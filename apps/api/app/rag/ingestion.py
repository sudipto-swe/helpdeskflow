"""Knowledge Base ingestion, chunking, and storage."""
import json
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from apps.api.app.db.models import KBDocument
from apps.api.app.rag.embeddings import embedder


def chunk_document(doc: Dict[str, Any], max_chunk_size: int = 400) -> List[Dict[str, Any]]:
    """Split long content into semantic paragraphs or chunks while retaining metadata."""
    content = doc["content"]
    paragraphs = [p.strip() for p in content.split("\n") if p.strip()]

    chunks = []
    chunk_idx = 0

    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) > max_chunk_size and current_chunk:
            chunk_id = f"{doc['id']}-c{chunk_idx}"
            chunks.append({
                "id": chunk_id,
                "doc_id": doc["id"],
                "title": doc["title"],
                "category": doc["category"],
                "tags": doc.get("tags", []),
                "content": current_chunk.strip()
            })
            chunk_idx += 1
            current_chunk = para + " "
        else:
            current_chunk += para + " "

    if current_chunk:
        chunk_id = f"{doc['id']}-c{chunk_idx}" if chunk_idx > 0 else doc["id"]
        chunks.append({
            "id": chunk_id,
            "doc_id": doc["id"],
            "title": doc["title"],
            "category": doc["category"],
            "tags": doc.get("tags", []),
            "content": current_chunk.strip()
        })

    return chunks


def ingest_kb(db: Session, kb_path: Path) -> int:
    """Ingest Knowledge Base documents, compute embeddings, and persist to database."""
    with open(kb_path, "r", encoding="utf-8") as f:
        docs = json.load(f)

    inserted_count = 0
    for doc in docs:
        chunks = chunk_document(doc)
        for chunk in chunks:
            existing = db.query(KBDocument).filter(KBDocument.id == chunk["id"]).first()
            embedding = embedder.embed_text(chunk["title"] + " " + chunk["content"])
            if existing:
                existing.title = chunk["title"]  # type: ignore[assignment]
                existing.category = chunk["category"]  # type: ignore[assignment]
                existing.tags = chunk["tags"]  # type: ignore[assignment]
                existing.content = chunk["content"]  # type: ignore[assignment]
                existing.embedding = embedding  # type: ignore[assignment]
            else:
                kb_record = KBDocument(
                    id=chunk["id"],
                    title=chunk["title"],
                    category=chunk["category"],
                    tags=chunk["tags"],
                    content=chunk["content"],
                    embedding=embedding
                )
                db.add(kb_record)
                inserted_count += 1

    db.commit()
    return inserted_count
