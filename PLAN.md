# PLAN: HelpdeskFlow (RAG + Tool-Calling Agent with Human Approval)

## Architecture Overview
HelpdeskFlow is an enterprise support-ticket workflow automation system featuring:
- Ticket intake (REST API & Web UI)
- Intelligent triage (Category, Priority, Language, Sentiment) with validated JSON schemas and fallback TF-IDF baseline
- Hybrid RAG (pgvector dense search + full-text lexical search + citation verification)
- Deterministic policy enforcement (`check_refund_policy`, identity authentication)
- Tool-calling agent (`search_kb`, `get_customer`, `get_billing_status`, `get_order_status`, `create_followup_task`, `escalate_to_human`, `schedule_callback`)
- State machine / Graph workflow with explicit approval gates for high-risk / low-confidence operations
- Guardrails: PII redaction, prompt injection defense, cross-customer isolation, token & tool budgets
- Agent Console: React + Vite + TypeScript dashboard for reviewing tickets, traces, approving drafts, and analytics
- Eval harness: Golden set (80+ tickets), Adversarial set (10+ tickets), ablations, policy violation tracking

---

## Milestones Tracker

- [x] **Milestone 1 [MVP]: Repo skeleton, Makefile, CI, docker-compose, health checks**
  - Acceptance checks:
    - Root and module structure matching specification
    - Makefile with common targets (`lint`, `test`, `type-check`, `run`, `demo`)
    - Docker Compose configuration for API and Postgres+pgvector (with local fallback support)
    - GitHub Actions CI workflow (`.github/workflows/ci.yml`)
    - API `/health` and `/ready` endpoints returning 200 OK with JSON status
    - Unit tests for health endpoints passing under `pytest`

- [x] **Milestone 2 [MVP]: Synthetic data generators & seed script**
  - Acceptance checks:
    - Fictional company: "BengalNet & Bazar" (ISP + E-commerce support)
    - `synth/generate_kb.py`: 40+ labeled synthetic markdown/json KB docs (refunds, billing, outages, escalation)
    - `synth/generate_customers.py`: 200+ customers with orders, subscriptions, bills
    - `synth/generate_tickets.py`: 150+ tickets (English, Bangla, Banglish with typos) + 80+ golden set tickets + 10+ adversarial tickets
    - Script `scripts/seed.py` creates and verifies data integrity

- [x] **Milestone 3 [MVP]: KB Ingestion, embeddings, retrieval with citations & Recall@5**
  - Acceptance checks:
    - Ingestion pipeline with chunking and metadata preservation
    - Embedding provider with local fast sentence embeddings / multilingual embedding support
    - Vector store / hybrid search implementation with pgvector (and SQLite/Numpy fallback for test environments without pgvector daemon)
    - Retrieval checks ensuring top-k chunks with explicit citations
    - Eval test verifying Recall@5 threshold on synthetic KB queries (achieved 95.56%)

- [ ] **Milestone 4 [MVP]: Classifier with schema validation & mock LLM**
  - Acceptance checks:
    - Pydantic v2 output schema for classification (`category`, `priority`, `language`, `sentiment`, `confidence`)
    - Retry & schema repair on invalid JSON
    - Unified `LLMClient` supporting `mock`, `gemini`, `groq`, `openrouter`, `ollama` with cache, retry, and token counters
    - Baseline TF-IDF classifier for latency & quality benchmark
    - Unit tests covering edge cases and malformed outputs

- [ ] **Milestone 5 [MVP]: Workflow graph end-to-end (mock + real LLM)**
  - Acceptance checks:
    - LangGraph / explicit state machine: intake -> classify -> retrieve -> draft -> policy_check -> approval_gate -> send/escalate
    - State persistence across restarts
    - Test executing full graph producing citation-backed draft from input ticket

- [ ] **Milestone 6 [MVP]: Minimal Agent Console & `make demo`**
  - Acceptance checks:
    - React + Vite + TypeScript frontend in `apps/web`
    - Ticket queue view, trace inspector (steps, chunks, tool calls), approval buttons
    - `make demo` runs automated end-to-end ticket batch processing
    - Headless browser/Playwright verification test taking screenshot

- [ ] **Milestone 7: Safe Tools & Identity Verification**
  - Acceptance checks:
    - `get_customer`, `get_billing_status`, `get_order_status` requiring customer identity match
    - `check_refund_policy`: 100% deterministic code logic (LLM cannot override)
    - `create_followup_task`, `escalate_to_human`, `schedule_callback`
    - Security tests asserting non-authenticated access and cross-customer queries fail

- [ ] **Milestone 8: Approval Gate, State Persistence & Fake Providers**
  - Acceptance checks:
    - Gate pauses on: low confidence, billing dispute, refund, account closure, legal threat, policy failure
    - Resuming paused workflows after admin approval / rejection / edit
    - Fake email & Slack delivery providers logging delivered payloads

- [ ] **Milestone 9: Guardrails & Security Testing**
  - Acceptance checks:
    - PII masking filter (emails, phone numbers, credit card numbers, national IDs)
    - Prompt injection detector & sandbox ignoring instruction overrides in ticket bodies
    - Hard budget enforcement: max tool calls (e.g. 5) and max tokens per ticket
    - Passing test suite over adversarial ticket dataset

- [ ] **Milestone 10: Evaluation Harness & Ablations**
  - Acceptance checks:
    - `eval/run_eval.py` executing over 80+ golden set and 10+ adversarial tickets
    - Metrics logged: Macro-F1, Accuracy, Recall@k, Citation Overlap, Groundedness, Policy-Violation Rate (target 0), Adversarial defense rate, p50/p95 latency
    - Ablation comparison: no-RAG vs RAG vs RAG+rerank; single-prompt vs graph workflow
    - Results committed to `results/`

- [ ] **Milestone 11: Analytics Dashboard & Feedback Loop**
  - Acceptance checks:
    - Analytics API & Console tab: auto-resolution rate, escalation rate, avg handling time, tokens/ticket
    - Human feedback recording (rating, corrected draft, audit trail)

- [ ] **Milestone 12: Documentation, Deployment Config & DoD Sign-off**
  - Acceptance checks:
    - `docs/INTERVIEW_NOTES.md` (15 in-depth interview questions & answers, architecture, trade-offs)
    - `docs/CV_BULLETS.md` (3 variants x 3 bullets backed strictly by `results/`)
    - Free tier deployment manifests (`deploy/` for Vercel, HuggingFace/Render, Neon/Supabase)
    - `HUMAN_TODO.md` with exact click-by-click instructions
    - `scripts/smoke.sh` passes end-to-end
