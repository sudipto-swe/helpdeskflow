"""Integration test suite verifying full ticket intake, listing, detail, and approval action endpoints."""
from fastapi.testclient import TestClient

from apps.api.app.main import app

client = TestClient(app)


def test_api_intake_and_workflow_execution():
    payload = {
        "text": "My router ONU is blinking red on LOS, please fix immediately [Customer: CUST-1002]",
        "customer_id": "CUST-1002"
    }
    response = client.post("/tickets/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "ticket_id" in data
    assert data["category"] == "technical"
    assert len(data["citations"]) > 0
    assert data["status"] in ["resolved", "awaiting_approval"]


def test_api_list_tickets_and_filtering():
    # Fetch list
    response = client.get("/tickets/")
    assert response.status_code == 200
    tickets = response.json()
    assert isinstance(tickets, list)
    assert len(tickets) > 0

    # Filter by resolved
    res_filtered = client.get("/tickets/?status=resolved")
    assert res_filtered.status_code == 200
    for t in res_filtered.json():
        assert t["status"] == "resolved"


def test_api_ticket_detail_and_approval_action():
    # Ingest a sensitive ticket that requires approval
    payload = {
        "text": "I was offline yesterday for 5 hours. Give me a full refund! [Customer: CUST-1005]",
        "customer_id": "CUST-1005"
    }
    resp = client.post("/tickets/", json=payload)
    assert resp.status_code == 200
    ticket_id = resp.json()["ticket_id"]

    # Check detail endpoint
    detail_resp = client.get(f"/tickets/{ticket_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["ticket_id"] == ticket_id
    assert "trace_steps" in detail
    assert "tool_calls" in detail

    # Execute approval action
    action_payload = {
        "approved": True,
        "edited_draft": "Your refund inquiry was reviewed under company policy."
    }
    action_resp = client.post(f"/tickets/{ticket_id}/action", json=action_payload)
    assert action_resp.status_code == 200
    assert action_resp.json()["status"] == "resolved"
    assert action_resp.json()["human_approved"] is True
