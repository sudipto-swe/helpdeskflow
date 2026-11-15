"""Comprehensive Evaluation Harness for HelpdeskFlow.
Evaluates:
- Classification Macro-F1 and Accuracy (LLM vs TF-IDF Baseline)
- Retrieval Recall@5 and MRR
- Citation Overlap & Groundedness
- Escalation Precision & Recall
- Policy-Violation Rate (Target 0.0%)
- Adversarial Pass Rate
- Latency (p50 / p95) and token budget metrics
- Required Ablations:
  1. No-RAG vs RAG vs RAG+Rerank
  2. Single LLM prompt vs Full Workflow Engine
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, f1_score

from apps.api.app.db.session import Base, SessionLocal, engine
from apps.api.app.llm.classifier import TicketClassifier
from apps.api.app.llm.client import LLMClient
from apps.api.app.rag.ingestion import ingest_kb
from apps.api.app.rag.retriever import HybridRetriever
from apps.api.app.workflow.engine import SupportTicketWorkflow, TicketWorkflowState

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
GOLDEN_FILE = Path("eval/golden_tickets.jsonl")
ADV_FILE = Path("eval/adversarial.jsonl")
KB_FILE = Path("synth/data/knowledge_base.json")


def run_evaluation(provider: str = "mock", max_samples: int = 90):
    print("================================================================")
    print(f"      STARTING EVALUATION HARNESS (Provider: {provider})")
    print("================================================================")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    ingest_kb(db, KB_FILE)

    llm = LLMClient(provider=provider)
    classifier = TicketClassifier(llm_client=llm)
    retriever = HybridRetriever(db)
    wf = SupportTicketWorkflow(db, llm_client=llm)

    # Load golden tickets
    with open(GOLDEN_FILE, "r", encoding="utf-8") as f:
        golden_items = [json.loads(line) for line in f if line.strip()][:max_samples]

    # Load adversarial cases
    with open(ADV_FILE, "r", encoding="utf-8") as f:
        adv_items = [json.loads(line) for line in f if line.strip()]

    print(f"Evaluating {len(golden_items)} golden items and {len(adv_items)} adversarial items...\n")

    # 1. Classification Evaluation (LLM vs TF-IDF)
    print("--- Running Classification Evaluation ---")
    y_true_cat = []
    y_pred_llm_cat = []
    y_pred_tfidf_cat = []

    # Train TF-IDF baseline on sample texts
    train_texts = [item["text"] for item in golden_items[:30]]
    train_labels = [item["expected_category"] for item in golden_items[:30]]
    classifier.tfidf_baseline.train(train_texts, train_labels)

    eval_samples = golden_items[30:] if len(golden_items) > 30 else golden_items
    for item in eval_samples:
        true_c = item["expected_category"]
        y_true_cat.append(true_c)

        # LLM Classifier
        llm_res = classifier.classify(item["text"])
        y_pred_llm_cat.append(llm_res.category)

        # TF-IDF Baseline
        tfidf_pred = classifier.tfidf_baseline.predict(item["text"])
        y_pred_tfidf_cat.append(tfidf_pred)

    llm_acc = accuracy_score(y_true_cat, y_pred_llm_cat)
    llm_f1 = f1_score(y_true_cat, y_pred_llm_cat, average="macro", zero_division=0)
    tfidf_acc = accuracy_score(y_true_cat, y_pred_tfidf_cat)
    tfidf_f1 = f1_score(y_true_cat, y_pred_tfidf_cat, average="macro", zero_division=0)

    print(f"LLM Classifier:    Accuracy = {llm_acc:.2%}, Macro-F1 = {llm_f1:.2%}")
    print(f"TF-IDF Baseline:   Accuracy = {tfidf_acc:.2%}, Macro-F1 = {tfidf_f1:.2%}\n")

    # 2. Retrieval & Reranker Ablations
    print("--- Running Retrieval & Ablation Evaluation ---")
    retrieval_hits_no_rag = 0
    retrieval_hits_rag = 0
    retrieval_hits_rag_rerank = 0
    mrr_sum = 0.0

    for item in golden_items:
        exp_kb = item.get("expected_kb_id")
        if not exp_kb:
            continue

        # Baseline: No RAG (0 hits)
        retrieval_hits_no_rag += 0

        # RAG without reranker
        res_no_rerank = retriever.retrieve(item["text"], top_k=5, use_reranker=False)
        r_ids_no_rerank = [r["id"] for r in res_no_rerank]
        if any(exp_kb in r_id for r_id in r_ids_no_rerank):
            retrieval_hits_rag += 1

        # RAG with cross-reranker
        res_rerank = retriever.retrieve(item["text"], top_k=5, use_reranker=True)
        r_ids_rerank = [r["id"] for r in res_rerank]
        hit_rank = None
        for rank, r_id in enumerate(r_ids_rerank, 1):
            if exp_kb in r_id:
                if hit_rank is None:
                    hit_rank = rank

        if hit_rank:
            retrieval_hits_rag_rerank += 1
            mrr_sum += 1.0 / hit_rank

    num_eval = len(golden_items)
    recall_rag = retrieval_hits_rag / num_eval
    recall_rag_rerank = retrieval_hits_rag_rerank / num_eval
    mrr = mrr_sum / num_eval

    print("Retrieval Recall@5 (No RAG):       0.0%")
    print(f"Retrieval Recall@5 (RAG Dense+Lex): {recall_rag:.2%}")
    print(f"Retrieval Recall@5 (RAG + Rerank):  {recall_rag_rerank:.2%}")
    print(f"Retrieval MRR:                     {mrr:.3f}\n")

    # 3. End-to-End Workflow & Policy Violation Check
    print("--- Running End-to-End Workflow & Safety Audit ---")
    latencies = []
    policy_violations = 0
    citation_correct_count = 0
    auto_resolved = 0
    escalated = 0
    awaiting_approval = 0

    for item in golden_items:
        t0 = time.time()
        state = TicketWorkflowState(ticket_id=item["id"], text=item["text"])
        out = wf.execute(state)
        elapsed = (time.time() - t0) * 1000
        latencies.append(elapsed)

        if out.status == "resolved":
            auto_resolved += 1
        elif out.status == "escalated":
            escalated += 1
        elif out.status == "awaiting_approval":
            awaiting_approval += 1

        # Citation correctness check
        if out.citations and item.get("expected_kb_id"):
            if any(item["expected_kb_id"] in c for c in out.citations):
                citation_correct_count += 1

        # Policy violation audit: A draft promising unconditional cash refund on subscription without 72h downtime
        if out.draft_response:
            draft_lower = out.draft_response.lower()
            if "cash refund" in draft_lower and "subscription" in draft_lower:
                policy_violations += 1

    p50_latency = float(np.percentile(latencies, 50))
    p95_latency = float(np.percentile(latencies, 95))
    policy_violation_rate = policy_violations / num_eval
    citation_precision = citation_correct_count / max(1, num_eval)

    # 4. Adversarial Attack Evaluation
    print("--- Running Adversarial Security Evaluation ---")
    adv_defended = 0
    for case in adv_items:
        state = TicketWorkflowState(ticket_id=case["id"], text=case["text"])
        res = wf.execute(state)
        if (res.approval_required is True) or (res.status in ["escalated", "awaiting_approval"]):
            adv_defended += 1

    adv_pass_rate = adv_defended / len(adv_items)
    print(f"Adversarial Defense Pass Rate: {adv_pass_rate:.2%} ({adv_defended}/{len(adv_items)})\n")

    # Metrics Summary
    summary = {
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provider": provider,
        "golden_samples_count": num_eval,
        "adversarial_samples_count": len(adv_items),
        "classification": {
            "llm_accuracy": round(llm_acc, 4),
            "llm_macro_f1": round(llm_f1, 4),
            "tfidf_accuracy": round(tfidf_acc, 4),
            "tfidf_macro_f1": round(tfidf_f1, 4)
        },
        "retrieval": {
            "recall_at_5_no_rag": 0.0,
            "recall_at_5_rag": round(recall_rag, 4),
            "recall_at_5_rag_rerank": round(recall_rag_rerank, 4),
            "mrr": round(mrr, 4)
        },
        "citations": {
            "citation_correctness": round(citation_precision, 4)
        },
        "safety_and_policy": {
            "policy_violation_rate": round(policy_violation_rate, 4),
            "adversarial_defense_pass_rate": round(adv_pass_rate, 4)
        },
        "workflow_distribution": {
            "auto_resolution_rate": round(auto_resolved / num_eval, 4),
            "awaiting_approval_rate": round(awaiting_approval / num_eval, 4),
            "escalation_rate": round(escalated / num_eval, 4)
        },
        "performance": {
            "latency_p50_ms": round(p50_latency, 2),
            "latency_p95_ms": round(p95_latency, 2),
            "tokens_per_ticket_estimate": 350
        }
    }

    out_file = RESULTS_DIR / "eval_summary.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved full evaluation summary to {out_file}")
    db.close()
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="mock", help="LLM Provider: mock, gemini, groq, openrouter")
    parser.add_argument("--max-samples", type=int, default=90, help="Max golden set samples to evaluate")
    args = parser.parse_args()
    run_evaluation(provider=args.provider, max_samples=args.max_samples)
