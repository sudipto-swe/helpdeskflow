"""End-to-End Demo Script for HelpdeskFlow.
1. Seeds synthetic database if empty.
2. Ingests knowledge base documents.
3. Submits 5 representative tickets (Technical LOS, Slow Speed, bKash Billing, Return Request, Legal Threat).
4. Prints execution results, citations, tool calls, and approval gates.
"""
import time
from pathlib import Path

from apps.api.app.db.session import Base, SessionLocal, engine
from apps.api.app.rag.ingestion import ingest_kb
from apps.api.app.workflow.engine import SupportTicketWorkflow, TicketWorkflowState

SAMPLE_TICKETS = [
    {
        "id": "DEMO-TCK-001",
        "name": "Technical Fiber Cut (Bangla)",
        "customer": "CUST-1002",
        "text": "আমার ইন্টারনেট কাজ করছে না। ONU তে লাল বাতি জ্বলছে নিভছে (LOS)। অনুগ্রহ করে দ্রুত ঠিক করুন।"
    },
    {
        "id": "DEMO-TCK-002",
        "name": "Slow Speed Troubleshooting (Banglish)",
        "customer": "CUST-1015",
        "text": "speed khub kharap, 30mbps package neoar por o 5mbps pawa jacche na. youtube buffer kore."
    },
    {
        "id": "DEMO-TCK-003",
        "name": "Billing Reconnection (bKash)",
        "customer": "CUST-1024",
        "text": "I paid my bill 20 minutes ago via bKash but my internet line is still suspended. TrxID 9K8L23NM."
    },
    {
        "id": "DEMO-TCK-004",
        "name": "Out-of-Policy Refund Request (Policy Check)",
        "customer": "CUST-1033",
        "text": "I was offline for 6 hours yesterday. I want a 100% full cash refund right now to my bKash account."
    },
    {
        "id": "DEMO-TCK-005",
        "name": "Hostile Legal Dispute (Supervisor Escalation)",
        "customer": "CUST-1040",
        "text": "Your company is fraudulent! Overcharging me every month. I will report to BTRC and take legal action!"
    }
]


def run_demo():
    print("==================================================================")
    print("        HELPDESKFLOW END-TO-END DEMO EXECUTION")
    print("==================================================================")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    kb_file = Path("synth/data/knowledge_base.json")
    if kb_file.exists():
        ingest_kb(db, kb_file)

    wf = SupportTicketWorkflow(db)

    print(f"\nProcessing {len(SAMPLE_TICKETS)} representative sample tickets...\n")

    for item in SAMPLE_TICKETS:
        print("------------------------------------------------------------------")
        print(f"Ticket ID: {item['id']} | Category Test: {item['name']}")
        print(f"Customer:  {item['customer']}")
        print(f"Inquiry:   \"{item['text']}\"")

        start_time = time.time()
        state = TicketWorkflowState(
            ticket_id=item["id"],
            text=item["text"],
            customer_id=item["customer"]
        )
        result = wf.execute(state)
        elapsed = (time.time() - start_time) * 1000

        print(f"Result Status:    {result.status.upper()}")
        print(f"Classification:   Category={result.category} | Priority={result.priority} | Language={result.language}")
        print(f"Confidence:       {result.confidence:.2f}")
        print(f"Citations:        {result.citations}")
        print(f"Approval Needed:  {result.approval_required} (Reason: {result.approval_reason or 'None'})")
        print(f"Latency:          {elapsed:.1f}ms")
        print(f"Draft Response:\n  {result.draft_response}")
        print(f"Trace Steps:      {' -> '.join([s['step'] for s in result.trace_steps])}\n")

    print("==================================================================")
    print("                  DEMO COMPLETED SUCCESSFULLY")
    print("==================================================================")


if __name__ == "__main__":
    run_demo()
