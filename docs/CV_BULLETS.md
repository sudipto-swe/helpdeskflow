# CV Bullets: HelpdeskFlow Applied AI Engineer

All numbers below are extracted directly from committed evaluation runs recorded in [`results/eval_summary.json`](../results/eval_summary.json).

---

### Variant 1: Applied AI & LLM Systems Focus
- Architected an autonomous support ticket automation system with **hybrid RAG** (dense vector search + character n-gram TF-IDF) achieving **95.56% Recall@5** and **0.841 MRR** across English, Bengali, and Banglish customer queries.
- Engineered safe tool-calling agent workflows with **deterministic policy enforcement**, reducing financial policy violation rates to **0.0%** and defending against **100.0%** of adversarial prompt-injection attacks.
- Built a human-in-the-loop approval gate and React console that automated **56.7%** of routine support tickets with a **29.9ms p50 latency** while pausing sensitive billing and refund queries for human review.

---

### Variant 2: Backend & Distributed Workflow Focus
- Designed and deployed a resilient ticket triage pipeline using **FastAPI, SQLAlchemy, and explicit state-machine orchestration**, handling **160+ synthetic production tickets** with persistent paused-workflow resumption.
- Implemented **Pydantic v2 JSON schema validation with automated self-repair**, achieving **74.36% Macro-F1** classification across 6 categories, outperforming a baseline TF-IDF model by **+38.35% F1**.
- Integrated enterprise guardrails featuring **automated PII redaction** (phone, email, NID, cards) and per-ticket token and tool execution budgets to prevent cross-customer data leakage.

---

### Variant 3: Full-Stack & Evaluation Rigor Focus
- Developed an end-to-end AI support console (React, Vite, TypeScript, Tailwind CSS) displaying real-time agent execution traces, tool call inspections, and citation-backed response drafts.
- Built a comprehensive evaluation harness evaluating **90 held-out golden tickets** and **12 adversarial security scenarios**, benchmarking retrieval ablations, citation correctness (**87.78%**), and latency distributions.
- Containerized the full system with **Docker Compose**, multi-stage build images, structured JSON request logging, and 100% green local and GitHub Actions CI pipelines.
