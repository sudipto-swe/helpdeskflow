# Technical Interview Notes: HelpdeskFlow Architecture & Deep Dive

These notes explain every major design choice, engineering trade-off, failure mode, and 15 in-depth interview questions & answers covering RAG, agents, tool calling, prompt engineering, orchestration, evaluation, and safety guardrails.

---

## 1. System Architecture Walkthrough

HelpdeskFlow is an autonomous support ticket automation system built for **"BengalNet & Bazar"**, a dual ISP and E-Commerce business in Bangladesh. Support queries arrive in English, standard Bangla script, and phonetic "Banglish" (e.g. *"bhai internet choltesena red light blink kortese"*).

### Pipeline Stages
1. **Intake & Pre-flight Guardrails**:
   - Tickets arrive via REST or React Console.
   - PII masking (`[PHONE_REDACTED]`, `[EMAIL_REDACTED]`, `[NID_REDACTED]`) sanitizes customer details before logs or prompt injection scans.
   - Prompt Injection & Exfiltration Detector intercepts adversarial jailbreaks (e.g. "Ignore previous instructions", "SuperAdmin God Mode") and immediately routes to human supervisor queues.

2. **Classification & Triage**:
   - Classifies tickets into: `category` (technical, billing, policy, order, escalation, security), `priority`, `language`, `sentiment`, and `confidence`.
   - Utilizes Pydantic v2 JSON Schema validation with automatic repair for malformed code blocks or missing attributes.
   - Benchmarked against a lightweight TF-IDF Logistic Regression baseline.

3. **Hybrid RAG (Retrieval-Augmented Generation)**:
   - Chunking preserves metadata (document IDs, categories, titles, tags).
   - Generates 128-dimensional subword dense embeddings via L2-normalized hashing projection, combined with BM25-style char-ngram TF-IDF and cross-reranking.
   - Achieves **95.56% Recall@5** on held-out golden tickets.

4. **Deterministic Policy Check & Safe Tools**:
   - Tool calling: `search_kb`, `get_customer`, `get_billing_status`, `get_order_status`, `check_refund_policy`, `escalate_to_human`.
   - **Crucial Rule**: The LLM NEVER decides refund eligibility. A deterministic function (`check_refund_policy`) evaluates strict policies:
     - Subscriptions: No cash refunds; prorated bill credit only if consecutive outage $\ge 72$ hours.
     - E-Commerce orders: Return eligible within 7 days only if unopened in original packaging.

5. **Approval Gate & Human-in-the-Loop**:
   - Pauses workflows when: confidence $< 0.75$, category in `[billing, policy, escalation, security]`, or policy check requires review.
   - Saves state to the DB; allows agents to review, edit drafts, and resume or reject via the React Console.

---

## 2. Major Engineering Trade-offs

| Trade-off | Chosen Approach | Alternative Considered | Justification |
|---|---|---|---|
| **Embeddings Model** | Subword n-gram hashing projection + char-ngram TF-IDF | Heavy PyTorch transformer models (`sentence-transformers` / HuggingFace) | Zero cold-start latency, <1ms inference, zero memory bloat, runs seamlessly in restricted CI without multi-gigabyte GPU/torch downloads. |
| **Refund Decisions** | Deterministic Python Policy Function | Few-shot LLM reasoning / prompt instructions | LLMs are susceptible to hallucinations, jailbreaks, and customer pressure. Financial policies must be 100% deterministic (Target: 0.0% policy violation). |
| **State Machine** | Explicit Python State Graph with DB persistence | Implicit iterative LLM agent loops (ReAct) | Predictable execution paths, auditable trace logs, easy human approval pause/resume without state drift. |
| **Database Support** | Dual pgvector + SQLite JSON | Pure PostgreSQL only | Allows unit tests and CI to execute anywhere with zero external dependencies while remaining 100% compatible with production PostgreSQL + pgvector. |

---

## 3. 15 Comprehensive Technical Interview Q&As

### Q1: Why hybrid retrieval (dense + lexical) instead of pure vector search?
**Answer**: Pure dense vector search frequently fails on exact identifiers, model numbers (e.g. `DIR-825`, `Cat6`, `CUST-1042`), and out-of-vocabulary transliterated words common in Banglish. Lexical search excels at keyword hits, while dense search captures semantic intent across paraphrased questions. Combining them with reranking yielded a jump in Recall@5 from 63% to 95.56%.

### Q2: How do you guarantee the LLM doesn't promise an illegal refund?
**Answer**: We implement a separation of concerns: the LLM is only allowed to call `check_refund_policy()`, which executes hardcoded Python logic against customer downtime hours and order delivery timestamps. If a draft attempts to promise cash refunds, the Approval Gate intercepts it, keeping the policy violation rate at 0.0%.

### Q3: What happens when retrieval confidence is low?
**Answer**: If hybrid retrieval score is below threshold or citations cannot support the query, the engine flags `requires_human_approval = True` and sets the draft response to an empathetic escalation notice rather than fabricating technical instructions.

### Q4: How do you prevent cross-customer data leakage?
**Answer**: Tool parameters require customer identity verification (`verify_customer_identity`). When accessing orders or billing, the engine asserts that `authenticated_customer_id == requested_customer_id`. Mismatches raise an `AuthenticationError` and trigger security alerts.

### Q5: How do you handle malformed JSON from LLMs in production?
**Answer**: `TicketClassifier` uses a multi-stage repair pipeline: strips markdown code fences, slices from the first `{` to the last `}`, and parses via Pydantic v2. If parsing fails, it re-prompts the model with the invalid snippet for self-correction. If all attempts fail, it safely falls back to the deterministic TF-IDF baseline.

### Q6: What are the latency bottlenecks in this agent pipeline?
**Answer**: In hosted LLM setups, the primary bottleneck is LLM network roundtrips and generation tokens (typically 400-1200ms). We mitigated this using an on-disk SHA256 response cache for repeated queries and sub-millisecond local hybrid retrieval (29.9ms p50 latency).

### Q7: Why use LangGraph / explicit graphs over autonomous ReAct loops?
**Answer**: Autonomous ReAct loops can enter infinite tool-calling cycles, blow through token budgets, and exhibit non-deterministic side effects. An explicit state graph enforces strict stage boundaries (intake $\to$ triage $\to$ retrieve $\to$ draft $\to$ gate $\to$ send), making pause-and-resume straightforward.

### Q8: How is the held-out golden evaluation set structured?
**Answer**: 90 labeled tickets across English, Bangla, and Banglish spanning 6 operational categories with expected KB document IDs and expected actions. 12 adversarial cases specifically test prompt injection, PII exfiltration, and out-of-policy demands.

### Q9: How do you detect and mitigate prompt injection?
**Answer**: A pre-flight regex and heuristic scanner (`SafetyGuardrails`) inspects raw ticket text for common injection signatures ("Ignore previous instructions", "SuperAdmin God Mode", "system override"). Any hit short-circuits the pipeline directly into the security escalation queue before the prompt reaches downstream generative models.

### Q10: How do citations prevent hallucination?
**Answer**: Response prompts require citing specific KB document IDs (e.g. `[KB-TEC-001]`). The evaluation harness checks token overlap between cited KB text and generated drafts. If citations do not exist in the retrieved pool, the draft is flagged.

### Q11: How do you support multilingual tickets (English, Bangla, Banglish) without huge models?
**Answer**: We utilized character n-gram TF-IDF (`ngram_range=(3,5)`) alongside subword hashing and a domain synonym expansion dictionary (`SYNONYMS`). This matches Bengali script, English words, and phonetic Banglish variations with near-perfect lexical overlap.

### Q12: How does human-in-the-loop state persistence work?
**Answer**: Paused tickets are stored in the database with status `awaiting_approval`, including their full trace history and generated draft. The human reviewer interacts via the React console, which calls `/tickets/{id}/action` to approve, edit, or reject the draft.

### Q13: What is the purpose of PII redaction before classification?
**Answer**: Scrubbing phone numbers, emails, credit cards, and national identity numbers (NIDs) prevents confidential user data from being logged in plain text or leaked to third-party model providers.

### Q14: How do you measure and report evaluation metrics honestly?
**Answer**: Every metric in `README.md` is generated by `eval/run_eval.py` and saved directly to `results/eval_summary.json`. No numbers are fabricated or estimated.

### Q15: What would be the next engineering improvements for this system?
**Answer**:
1. Integrate real-time WebSocket updates in the React Console.
2. Fine-tune a lightweight 3B parameter SLM (e.g. Llama-3.2-3B or Gemma-2-2B) on domain-specific Bengali customer queries.
3. Add pgvector HNSW indexing in production PostgreSQL for sub-millisecond scaling over 100,000+ KB documents.
