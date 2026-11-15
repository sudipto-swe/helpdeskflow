"""Unit tests for synthetic data integrity and seed verification."""
import json
from pathlib import Path

from apps.api.app.db.models import Customer, Order, Subscription, Ticket
from apps.api.app.db.session import SessionLocal

DATA_DIR = Path("synth/data")
EVAL_DIR = Path("eval")


def test_synthetic_files_exist():
    assert (DATA_DIR / "knowledge_base.json").exists()
    assert (DATA_DIR / "customers.json").exists()
    assert (DATA_DIR / "tickets.json").exists()
    assert (EVAL_DIR / "golden_tickets.jsonl").exists()
    assert (EVAL_DIR / "adversarial.jsonl").exists()


def test_kb_documents_count_and_schema():
    with open(DATA_DIR / "knowledge_base.json", "r", encoding="utf-8") as f:
        kb = json.load(f)
    assert len(kb) >= 40, f"Expected at least 40 KB documents, got {len(kb)}"
    for doc in kb:
        assert "id" in doc
        assert "title" in doc
        assert "category" in doc
        assert "content" in doc
        assert len(doc["content"]) > 20


def test_customers_count_and_schema():
    with open(DATA_DIR / "customers.json", "r", encoding="utf-8") as f:
        customers = json.load(f)
    assert len(customers) >= 200, f"Expected at least 200 customers, got {len(customers)}"
    sample = customers[0]
    assert "customer_id" in sample
    assert "phone" in sample
    assert "subscription" in sample
    assert sample["is_synthetic"] is True


def test_tickets_and_golden_eval_count():
    with open(DATA_DIR / "tickets.json", "r", encoding="utf-8") as f:
        tickets = json.load(f)
    assert len(tickets) >= 150

    with open(EVAL_DIR / "golden_tickets.jsonl", "r", encoding="utf-8") as f:
        golden = [json.loads(line) for line in f if line.strip()]
    assert len(golden) >= 80

    with open(EVAL_DIR / "adversarial.jsonl", "r", encoding="utf-8") as f:
        adversarial = [json.loads(line) for line in f if line.strip()]
    assert len(adversarial) >= 10


def test_db_seeding_integrity():
    db = SessionLocal()
    try:
        assert db.query(Customer).count() >= 200
        assert db.query(Subscription).count() >= 200
        assert db.query(Order).count() > 0
        assert db.query(Ticket).count() >= 150
    finally:
        db.close()
