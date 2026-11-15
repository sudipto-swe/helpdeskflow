"""Workflow state machine: intake -> classify -> retrieve -> draft -> policy_check -> approval_gate -> send/escalate.
Persists state to database and supports resumption on human approval.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from apps.api.app.db.models import Customer, Ticket
from apps.api.app.llm.classifier import TicketClassifier
from apps.api.app.llm.client import LLMClient
from apps.api.app.providers.delivery import fake_email, fake_slack
from apps.api.app.tools.support_tools import SupportTools


class TicketWorkflowState:
    """Represents the in-flight state of a ticket through the automation graph."""

    def __init__(
        self,
        ticket_id: str,
        text: str,
        customer_id: Optional[str] = None,
        customer_name: Optional[str] = None
    ):
        self.ticket_id = ticket_id
        self.text = text
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.category: Optional[str] = None
        self.priority: Optional[str] = None
        self.language: str = "en"
        self.sentiment: str = "neutral"
        self.confidence: float = 0.0
        self.retrieved_chunks: List[Dict[str, Any]] = []
        self.citations: List[str] = []
        self.tool_calls: List[Dict[str, Any]] = []
        self.draft_response: Optional[str] = None
        self.policy_check_passed: bool = True
        self.approval_required: bool = False
        self.approval_reason: Optional[str] = None
        self.status: str = "new"  # new, processing, awaiting_approval, resolved, escalated
        self.trace_steps: List[Dict[str, Any]] = []

    def log_step(self, step_name: str, details: Dict[str, Any]) -> None:
        self.trace_steps.append({
            "step": step_name,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        })


class SupportTicketWorkflow:
    """Graph workflow engine coordinating triage, RAG, tools, and human approval."""

    def __init__(self, db: Session, llm_client: Optional[LLMClient] = None):
        self.db = db
        self.llm = llm_client or LLMClient()
        self.classifier = TicketClassifier(llm_client=self.llm)
        self.tools = SupportTools(db)

    def execute(self, state: TicketWorkflowState) -> TicketWorkflowState:
        """Run workflow graph from intake to completion or approval pause."""
        state.status = "processing"
        state.log_step("intake", {"ticket_id": state.ticket_id, "text_len": len(state.text)})

        # 0. Safety Guardrail: Prompt Injection & Adversarial Check
        from apps.api.app.safety.guardrails import SafetyGuardrails
        is_inj, inj_reason = SafetyGuardrails.detect_prompt_injection(state.text)
        if is_inj:
            state.category = "security"
            state.priority = "urgent"
            state.status = "escalated"
            state.approval_required = True
            state.approval_reason = inj_reason
            state.draft_response = "Request flagged for security audit and escalated to human supervisor."
            self.tools.escalate_to_human(state.ticket_id, inj_reason, priority="urgent")
            state.log_step("guardrail_injection_intercept", {"reason": inj_reason})
            self._persist_ticket(state)
            return state
        triage = self.classifier.classify(state.text)
        state.category = triage.category
        state.priority = triage.priority
        state.language = triage.language
        state.sentiment = triage.sentiment
        state.confidence = triage.confidence

        if not state.customer_id and triage.detected_customer_id:
            state.customer_id = triage.detected_customer_id

        state.log_step("classify", {
            "category": state.category,
            "priority": state.priority,
            "confidence": state.confidence,
            "detected_cust": state.customer_id
        })

        # Check immediate escalation criteria
        if state.category in ["escalation", "security"] or state.sentiment == "hostile":
            state.approval_required = True
            state.approval_reason = f"High severity or sensitive category ({state.category})"
            state.status = "escalated"
            state.draft_response = (
                "Your request has been prioritized and routed to a senior human support manager "
                "who will review the matter promptly."
            )
            self.tools.escalate_to_human(state.ticket_id, state.approval_reason, state.priority or "urgent")
            fake_slack.post_alert("escalations", f"Ticket {state.ticket_id} escalated: {state.approval_reason}", {"ticket_id": state.ticket_id})
            state.log_step("escalate", {"reason": state.approval_reason})
            self._persist_ticket(state)
            return state

        # 2. Step: RAG Retrieval
        search_res = self.tools.search_kb(state.text, top_k=3)
        state.retrieved_chunks = search_res["results"]
        state.citations = search_res["citations"]
        state.tool_calls.append({"tool": "search_kb", "query": state.text, "citations": state.citations})
        state.log_step("retrieve", {"retrieved_count": len(state.retrieved_chunks), "citations": state.citations})

        # 3. Step: Tool Actions (if applicable)
        if state.category == "billing" and state.customer_id:
            try:
                billing_info = self.tools.get_billing_status(state.customer_id, authenticated=True)
                state.tool_calls.append({"tool": "get_billing_status", "result": billing_info})
                state.log_step("tool_call", {"tool": "get_billing_status", "customer_id": state.customer_id})
            except Exception as e:
                state.log_step("tool_error", {"tool": "get_billing_status", "error": str(e)})

        elif state.category == "policy" and ("refund" in state.text.lower() or "রিফান্ড" in state.text):
            # Deterministic policy check
            pol_res = self.tools.check_refund_policy(item_type="subscription", consecutive_downtime_hours=24)
            state.tool_calls.append({"tool": "check_refund_policy", "result": pol_res})
            if not pol_res["eligible"]:
                state.policy_check_passed = False
                state.approval_required = True
                state.approval_reason = pol_res["reason"]
            state.log_step("policy_check", pol_res)

        # 4. Step: Draft Response Generation
        cited_text = "\n\n".join([f"[{c['id']}] {c['title']}: {c['content']}" for c in state.retrieved_chunks])
        prompt = (
            f"Draft a polite, professional support answer for this customer inquiry using ONLY the provided KB articles.\n"
            f"Customer Ticket: \"{state.text}\"\n\n"
            f"Documentation:\n{cited_text}\n\n"
            f"Output JSON with reply_text, citations, action_taken, confidence, requires_human_approval."
        )

        draft_json = self.llm.generate_json(prompt, schema_name="draft")
        try:
            import json
            draft_data = json.loads(draft_json)
            state.draft_response = draft_data.get("reply_text")
            state.confidence = min(state.confidence, draft_data.get("confidence", 0.9))
        except Exception:
            state.draft_response = (
                "Thank you for contacting BengalNet & Bazar support. "
                "Our technical support team has noted your ticket and is addressing the issue according to company SLA."
            )

        state.log_step("draft", {"citations": state.citations, "confidence": state.confidence})

        # 5. Step: Approval Gate Check
        if (
            state.confidence < 0.75 or
            state.approval_required or
            not state.policy_check_passed or
            state.category in ["billing", "policy"]
        ):
            state.status = "awaiting_approval"
            state.approval_required = True
            if not state.approval_reason:
                state.approval_reason = "Requires supervisor review due to policy/billing category or confidence threshold."
            state.log_step("approval_gate", {"action": "paused_for_human", "reason": state.approval_reason})
            self._persist_ticket(state)
            return state

        # 6. Step: Send / Auto-Resolve
        state.status = "resolved"
        customer = None
        if state.customer_id:
            customer = self.db.query(Customer).filter(Customer.customer_id == state.customer_id).first()
        target_email = str(customer.email) if customer else "customer@example.com"
        fake_email.send_email(target_email, f"Support Ticket Update: {state.ticket_id}", state.draft_response or "")
        state.log_step("send_notification", {"to": target_email, "status": "resolved"})

        self._persist_ticket(state)
        return state

    def resume_after_approval(
        self,
        ticket_id: str,
        approved: bool,
        edited_draft: Optional[str] = None
    ) -> Ticket:
        """Resume paused workflow after a human reviewer approves, edits, or rejects."""
        ticket = self.db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")

        ticket.human_approved = approved  # type: ignore[assignment]
        if edited_draft:
            ticket.draft_response = edited_draft  # type: ignore[assignment]

        if approved:
            ticket.status = "resolved"  # type: ignore[assignment]
            target_email = "customer@example.com"
            if ticket.customer_id:
                cust = self.db.query(Customer).filter(Customer.customer_id == ticket.customer_id).first()
                if cust:
                    target_email = str(cust.email)
            fake_email.send_email(target_email, f"Support Update: {ticket.ticket_id}", str(ticket.draft_response or ""))
        else:
            ticket.status = "escalated"  # type: ignore[assignment]
            fake_slack.post_alert("supervisor-queue", f"Ticket {ticket_id} rejected by agent; escalated to senior manager.", {"ticket_id": ticket_id})

        self.db.commit()
        return ticket

    def _persist_ticket(self, state: TicketWorkflowState) -> Ticket:
        """Persist or update state in the database."""
        ticket = self.db.query(Ticket).filter(Ticket.ticket_id == state.ticket_id).first()
        if not ticket:
            ticket = Ticket(
                ticket_id=state.ticket_id,
                customer_id=state.customer_id,
                customer_name=state.customer_name,
                text=state.text
            )
            self.db.add(ticket)

        ticket.category = state.category  # type: ignore[assignment]
        ticket.priority = state.priority  # type: ignore[assignment]
        ticket.language = state.language  # type: ignore[assignment]
        ticket.sentiment = state.sentiment  # type: ignore[assignment]
        ticket.confidence = state.confidence  # type: ignore[assignment]
        ticket.status = state.status  # type: ignore[assignment]
        ticket.draft_response = state.draft_response  # type: ignore[assignment]
        ticket.citations = state.citations  # type: ignore[assignment]
        ticket.tool_calls = state.tool_calls  # type: ignore[assignment]
        ticket.trace_steps = state.trace_steps  # type: ignore[assignment]
        ticket.policy_check_passed = state.policy_check_passed  # type: ignore[assignment]
        ticket.approval_required = state.approval_required  # type: ignore[assignment]

        self.db.commit()
        self.db.refresh(ticket)
        return ticket
