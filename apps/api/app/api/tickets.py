"""FastAPI router for Tickets and Workflow management."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from apps.api.app.db.session import get_db
from apps.api.app.db.models import Ticket
from apps.api.app.workflow.engine import SupportTicketWorkflow, TicketWorkflowState

router = APIRouter(prefix="/tickets", tags=["tickets"])


class CreateTicketRequest(BaseModel):
    ticket_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    text: str = Field(min_length=5, description="Customer ticket inquiry text")


class ApprovalActionRequest(BaseModel):
    approved: bool
    edited_draft: Optional[str] = None


@router.post("/", response_model=dict)
def intake_ticket(req: CreateTicketRequest, db: Session = Depends(get_db)):
    """Ticket intake endpoint: immediately triggers workflow execution."""
    import uuid
    ticket_id = req.ticket_id or f"TCK-{str(uuid.uuid4())[:8].upper()}"

    wf = SupportTicketWorkflow(db)
    state = TicketWorkflowState(
        ticket_id=ticket_id,
        text=req.text,
        customer_id=req.customer_id,
        customer_name=req.customer_name
    )

    final_state = wf.execute(state)
    return {
        "ticket_id": final_state.ticket_id,
        "status": final_state.status,
        "category": final_state.category,
        "priority": final_state.priority,
        "language": final_state.language,
        "confidence": final_state.confidence,
        "draft_response": final_state.draft_response,
        "citations": final_state.citations,
        "approval_required": final_state.approval_required,
        "approval_reason": final_state.approval_reason
    }


@router.get("/", response_model=List[dict])
def list_tickets(status: Optional[str] = None, db: Session = Depends(get_db)):
    """List tickets with optional status filtering."""
    q = db.query(Ticket)
    if status:
        q = q.filter(Ticket.status == status)
    tickets = q.order_by(Ticket.created_at.desc()).limit(100).all()

    return [
        {
            "ticket_id": t.ticket_id,
            "customer_id": t.customer_id,
            "customer_name": t.customer_name,
            "text": t.text,
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "confidence": t.confidence,
            "draft_response": t.draft_response,
            "citations": t.citations,
            "approval_required": t.approval_required,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in tickets
    ]


@router.get("/{ticket_id}", response_model=dict)
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """Get full ticket details including trace and tool calls."""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {
        "ticket_id": ticket.ticket_id,
        "customer_id": ticket.customer_id,
        "customer_name": ticket.customer_name,
        "text": ticket.text,
        "category": ticket.category,
        "priority": ticket.priority,
        "sentiment": ticket.sentiment,
        "status": ticket.status,
        "confidence": ticket.confidence,
        "draft_response": ticket.draft_response,
        "citations": ticket.citations or [],
        "tool_calls": ticket.tool_calls or [],
        "trace_steps": ticket.trace_steps or [],
        "approval_required": ticket.approval_required,
        "human_approved": ticket.human_approved
    }


@router.post("/{ticket_id}/action", response_model=dict)
def review_ticket_action(
    ticket_id: str,
    action: ApprovalActionRequest,
    db: Session = Depends(get_db)
):
    """Approve, edit, or reject a paused ticket."""
    wf = SupportTicketWorkflow(db)
    try:
        updated = wf.resume_after_approval(
            ticket_id=ticket_id,
            approved=action.approved,
            edited_draft=action.edited_draft
        )
        return {
            "ticket_id": updated.ticket_id,
            "status": updated.status,
            "human_approved": updated.human_approved,
            "draft_response": updated.draft_response
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
