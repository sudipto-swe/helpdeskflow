"""Unit tests for KB ingestion, embeddings, and retrieval with Recall@5 acceptance check."""
import json
from pathlib import Path

import pytest

from apps.api.app.db.models import KBDocument
from apps.api.app.db.session import Base, SessionLocal, engine
from apps.api.app.rag.embeddings import embedder
from apps.api.app.rag.ingestion import ingest_kb
from apps.api.app.rag.retriever import HybridRetriever, format_citations

KB_FILE = Path("synth/data/knowledge_base.json")
GOLDEN_FILE = Path("eval/golden_tickets.jsonl")


@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Ingest KB
    ingest_kb(db, KB_FILE)
    yield db
    db.close()


def test_embedding_shape_and_normalization():
    vec = embedder.embed_text("bKash payment failed for customer")
    assert len(vec) == 128
    # L2 norm should be approximately 1.0
    norm = sum(x * x for x in vec) ** 0.5
    assert abs(norm - 1.0) < 1e-4


def test_kb_ingestion(db_session):
    count = db_session.query(KBDocument).count()
    assert count >= 40, f"Expected >= 40 docs ingested, got {count}"


def test_hybrid_retrieval_los_query(db_session):
    retriever = HybridRetriever(db_session)
    results = retriever.retrieve("red light blinking on LOS ONU", top_k=3)
    assert len(results) > 0
    top_doc_ids = [r["id"] for r in results]
    assert any("KB-TEC-001" in doc_id for doc_id in top_doc_ids)


def test_retrieval_recall_at_5(db_session):
    """Acceptance check: Verify Recall@5 across golden tickets is >= 70%."""
    retriever = HybridRetriever(db_session)

    with open(GOLDEN_FILE, "r", encoding="utf-8") as f:
        golden_items = [json.loads(line) for line in f if line.strip()]

    hits = 0
    evaluated = 0

    for item in golden_items:
        expected_kb = item.get("expected_kb_id")
        if not expected_kb:
            continue

        results = retriever.retrieve(item["text"], top_k=5)
        retrieved_ids = [r["id"] for r in results]

        # Check if expected KB doc ID is present in retrieved chunks
        if any(expected_kb in r_id for r_id in retrieved_ids):
            hits += 1
        evaluated += 1

    recall_at_5 = (hits / evaluated) if evaluated > 0 else 0.0
    print(f"\nRetrieval Recall@5: {recall_at_5:.2%} ({hits}/{evaluated})")
    assert recall_at_5 >= 0.70, f"Recall@5 {recall_at_5:.2%} is below 70% threshold"


def test_citation_formatting():
    chunks = [
        {"id": "KB-TEST-1", "title": "Refund Rules", "content": "Refunds are processed in 5 days."}
    ]
    formatted = format_citations(chunks)
    assert "[1] Source: KB-TEST-1 - Refund Rules" in formatted
    assert "Refunds are processed in 5 days." in formatted
