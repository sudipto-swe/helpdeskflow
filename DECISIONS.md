# DECISIONS: Architecture & Implementation Choices

| Decision ID | Area | Choice | Reason | Alternatives Considered | License |
|---|---|---|---|---|---|
| DEC-001 | Language & Core | Python 3.11+ (Python 3.14 in host environment), FastAPI, Pydantic v2 | Modern async standard, native pydantic v2 validation and fast schema serialization | Flask, Django | MIT / BSD |
| DEC-002 | Database & Storage | SQLAlchemy 2.0 with PostgreSQL + pgvector support; SQLite fallback for standalone zero-dependency testing | Enables robust pgvector in production/Docker while allowing tests to pass in environments where docker daemon or root postgres is unavailable | Pure SQLite (no native vector extension), MySQL | MIT / PostgreSQL |
| DEC-003 | LLM Client Interface | Single `LLMClient` with unified protocol supporting providers: `mock` (deterministic, zero-cost, CI), `ollama`, `gemini`, `groq`, `openrouter` with file-based disk cache and exponential backoff | Complies with Section B zero-budget rule and deterministic testing requirement | Calling SDKs directly in routes, vendor lock-in | Apache-2.0 / MIT |
| DEC-004 | Frontend Framework | React 18 / Vite / TypeScript + Tailwind CSS | Fast build, modern standard console UI, instant hot-reloading | Next.js, Vue, Plain HTML/JS | MIT |
| DEC-005 | Synthetic Domain | "BengalNet & Bazar" (Joint ISP & E-commerce support in Bangladesh) | Perfectly fits problem requirements: multilingual English/Bangla/Banglish support, delivery issues, internet outages, billing, strict refund rules | Generic generic SaaS helpdesk | Synthetic Data / CC0 |
