"""Unit tests for Approval Gate, paused workflow persistence, and fake delivery providers."""
import pytest
from apps.api.app.db.session import SessionLocal, Base, engine
from apps.api.app.db.models import Ticket
from apps.api.app.workflow.engine import SupportTicketWorkflow, TicketWorkflowState
from apps.api.app.providers.delivery import fake_email, fake_slack


@pytest.fixture(scope="module")
def gate_setup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    wf = SupportTicketWorkflow(db)
    yield wf, db
    db.close()


def test_gate_pauses_sensitive_billing_dispute(gate_setup):
    wf, db = gate_setup
    state = TicketWorkflowState(
        ticket_id="TCK-GATE-01",
        text="Why was a 100 BDT late fee added to my invoice? I want this removed. [Customer: CUST-1008]"
    )
    result = wf.execute(state)
    assert result.status == "awaiting_approval"
    assert result.approval_required is True

    # Verify persisted in database
    db_ticket = db.query(Ticket).filter(Ticket.ticket_id == "TCK-GATE-01").first()
    assert db_ticket is not None
    assert db_ticket.status == "awaiting_approval"


def test_gate_escalates_and_posts_to_slack(gate_setup):
    wf, _ = gate_setup
    initial_slack_len = len(fake_slack.posted_messages)
    state = TicketWorkflowState(
        ticket_id="TCK-GATE-02",
        text="I am reporting your scam company to BTRC and consumer rights court!"
    )
    result = wf.execute(state)
    assert result.status == "escalated"
    assert len(fake_slack.posted_messages) > initial_slack_len
    last_msg = fake_slack.posted_messages[-1]
    assert "TCK-GATE-02" in last_msg["message"]


def test_resume_delivers_email_on_approval(gate_setup):
    wf, db = gate_setup
    state = TicketWorkflowState(
        ticket_id="TCK-GATE-03",
        text="I paid my bill via bKash 15 minutes ago. TrxID 9K8L23NM. [Customer: CUST-1002]"
    )
    wf.execute(state)

    initial_email_len = len(fake_email.sent_emails)
    updated = wf.resume_after_approval(
        ticket_id="TCK-GATE-03",
        approved=True,
        edited_draft="Your bKash transaction 9K8L23NM has been verified and line reactivated."
    )
    assert updated.status == "resolved"
    assert len(fake_email.sent_emails) > initial_email_len
    last_email = fake_email.sent_emails[-1]
    assert "9K8L23NM" in last_email["body"]
