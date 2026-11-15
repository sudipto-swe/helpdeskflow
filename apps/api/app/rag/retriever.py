"""Multilingual TF-IDF & Semantic Hybrid Retriever with cross-language query alignment.
Performs subword-aware, n-gram TF-IDF and dense hashing representations across English, Bangla, and Banglish.
"""
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.orm import Session

from apps.api.app.db.models import KBDocument
from apps.api.app.rag.embeddings import embedder

# Multilingual domain terms expansion
DOMAIN_EXPANSIONS = {
    # Speed issues
    "এমবিপিএস": "mbps speed slow buffer speedtest slow internet speed",
    "বাফারিং": "buffer youtube slow speed streaming",
    "স্পিড": "speed slow bandwidth",
    "speed": "mbps slow buffer speedtest",
    "slow": "speed slow buffer speedtest",
    # Outage / Fiber
    "ফাইবার": "fiber cut outage los red light downtime",
    "downtime": "outage downtime refund fiber cut 72 hours",
    "fiber": "fiber cut outage los patch cord",
    "red": "los red light blinking onu",
    "los": "red light blinking onu fiber",
    "বাতি": "light blinking red los onu",
    # Passwords / Wifi
    "পাসওয়ার্ড": "password wifi router reset admin 192.168.1.1",
    "ওয়াইফাই": "wifi router wireless password admin",
    "wifi": "wifi wireless router password admin 192.168.1.1",
    "password": "password router admin login reset",
    # Payments / bKash
    "বিকাশ": "bkash payment merchant trxid bill suspended",
    "bkash": "bkash payment merchant trxid bill suspended",
    "বিল": "bill invoice late fee due date payment",
    "bill": "bill invoice late fee due date payment",
    "ইনভয়েস": "invoice bill late fee payment 100 bdt",
    "trxid": "trxid bkash payment confirmation reconnection",
    # Orders / Products / Returns
    "রাউটার": "router tplink dlink delivery bazar order",
    "router": "router wifi onu tplink delivery order bazar",
    "পার্সেল": "parcel delivery tracking order bazar bengaldelivery",
    "delivery": "delivery timeline tracking courier order",
    "রিটার্ন": "return refund unopened 7 days packaging bazar",
    "রিফান্ড": "refund return money policy credit adjustment",
    "refund": "refund return money policy credit adjustment",
    "return": "return refund unopened 7 days packaging bazar",
    # Escalation / Legal / Dispute
    "বিটিআরসি": "btrc legal lawsuit dispute fraudulent supervisor escalation",
    "আইনি": "legal lawsuit btrc dispute court escalation",
    "btrc": "btrc legal lawsuit dispute fraudulent supervisor escalation",
    "fraudulent": "fraudulent cheat scam dispute escalation human legal",
    "fokirni": "fraudulent scam abusive escalation human supervisor",
    "churi": "fraudulent scam dispute overcharging escalation",
    # Cancellation
    "ক্যান্সেল": "cancel termination disconnect notice 7 days return onu",
    "cancel": "cancel termination disconnect notice 7 days return onu",
    "শহরে": "shifting moving cancel connection return onu"
}


def expand_text(text: str) -> str:
    lower = text.lower()
    additions = []
    for k, v in DOMAIN_EXPANSIONS.items():
        if k in lower:
            additions.append(v)
    return text + " " + " ".join(additions)


class HybridRetriever:
    """Hybrid TF-IDF + Dense Subword Retriever for Multilingual Helpdesk RAG."""

    def __init__(self, db: Session):
        self.db = db
        self.docs: List[KBDocument] = []
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix: Optional[np.ndarray] = None
        self._build_index()

    def _build_index(self):
        self.docs = self.db.query(KBDocument).all()
        if not self.docs:
            return

        corpus = []
        for d in self.docs:
            doc_text = f"{d.id} {d.title} {d.title} {' '.join(d.tags or [])} {d.content}"
            expanded = expand_text(doc_text)
            corpus.append(expanded)

        self.tfidf_vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=1,
            sublinear_tf=True
        )
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        use_reranker: bool = True
    ) -> List[Dict[str, Any]]:
        """Retrieve top_k documents using hybrid TF-IDF + Dense matching."""
        if not self.docs or self.tfidf_vectorizer is None or self.tfidf_matrix is None:
            self._build_index()

        if not self.docs or self.tfidf_vectorizer is None or self.tfidf_matrix is None:
            return []

        expanded_query = expand_text(query)
        q_vec = self.tfidf_vectorizer.transform([expanded_query])
        tfidf_scores = (self.tfidf_matrix * q_vec.T).toarray().flatten()

        dense_q = embedder.embed_text(query)
        dense_q_np = np.array(dense_q, dtype=np.float32)

        candidates: List[Dict[str, Any]] = []
        for idx, doc in enumerate(self.docs):
            tfidf_s = float(tfidf_scores[idx])

            # Dense score
            doc_dense = np.array(doc.embedding or [], dtype=np.float32)
            dense_s = 0.0
            if len(doc_dense) == len(dense_q_np):
                norm_d = np.linalg.norm(doc_dense)
                norm_q = np.linalg.norm(dense_q_np)
                if norm_d > 0 and norm_q > 0:
                    dense_s = float(np.dot(doc_dense, dense_q_np) / (norm_d * norm_q))

            hybrid_s = (0.75 * tfidf_s) + (0.25 * dense_s)

            candidates.append({
                "id": doc.id,
                "title": doc.title,
                "category": doc.category,
                "content": doc.content,
                "tags": doc.tags or [],
                "score": hybrid_s,
                "tfidf_score": tfidf_s,
                "dense_score": dense_s
            })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = candidates[: top_k * 2]

        if use_reranker and len(top_candidates) > 1:
            for item in top_candidates:
                boost = 0.0
                q_lower = query.lower()
                for t in item.get("tags", []):
                    if t.lower() in q_lower:
                        boost += 0.15
                item["final_score"] = item["score"] + boost
            top_candidates.sort(key=lambda x: x["final_score"], reverse=True)
        else:
            for item in top_candidates:
                item["final_score"] = item["score"]

        return top_candidates[:top_k]


def format_citations(retrieved_chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved documents with markdown citations."""
    if not retrieved_chunks:
        return "No relevant documentation found."
    lines = []
    for idx, chunk in enumerate(retrieved_chunks, 1):
        lines.append(f"[{idx}] Source: {chunk['id']} - {chunk['title']}\n{chunk['content']}\n")
    return "\n".join(lines)
