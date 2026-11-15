"""Unit tests for the complete workflow graph end-to-end."""
from pathlib import Path

import pytest

from apps.api.app.db.session import Base, SessionLocal, engine
from apps.api.app.llm.client import LLMClient
from apps.api.app.rag.ingestion import ingest_kb
from apps.api.app.workflow.engine import SupportTicketWorkflow, TicketWorkflowState

KB_FILE = Path("synth/data/knowledge_base.json")


@pytest.fixture(scope="module")
def workflow_setup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    ingest_kb(db, KB_FILE)
    client = LLMClient(provider="mock")
    wf = SupportTicketWorkflow(db, llm_client=client)
    yield wf, db
    db.close()


def test_workflow_technical_ticket(workflow_setup):
    wf, db = workflow_setup
    state = TicketWorkflowState(
        ticket_id="TEST-TCK-001",
        text="My router ONU has a red light blinking on LOS. Please fix."
    )
    final_state = wf.execute(state)

    assert final_state.category == "technical"
    assert len(final_state.citations) > 0
    assert any("KB-TEC-001" in c for c in final_state.citations)
    assert final_state.draft_response is not None
    assert final_state.status in ["resolved", "awaiting_approval"]
    assert len(final_state.trace_steps) >= 3


def test_workflow_legal_escalation(workflow_setup):
    wf, db = workflow_setup
    state = TicketWorkflowState(
        ticket_id="TEST-TCK-002",
        text="This is fraudulent! I will take legal action and report to BTRC!"
    )
    final_state = wf.execute(state)

    assert final_state.category == "escalation"
    assert final_state.status == "escalated"
    assert final_state.approval_required is True


def test_workflow_approval_resumption(workflow_setup):
    wf, db = workflow_setup
    state = TicketWorkflowState(
        ticket_id="TEST-TCK-003",
        text="I want a refund for the 4 days downtime on my subscription [Customer: CUST-1005]"
    )
    final_state = wf.execute(state)
    assert final_state.status == "awaiting_approval"

    # Human approves with edited draft
    approved_ticket = wf.resume_after_approval(
        ticket_id="TEST-TCK-003",
        approved=True,
        edited_draft="We have approved a prorated credit adjustment for your account."
    )
    assert approved_ticket.status == "resolved"
    assert approved_ticket.human_approved is True
    assert "prorated credit" in (approved_ticket.draft_response or "")
