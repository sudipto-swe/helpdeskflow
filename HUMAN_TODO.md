# HUMAN_TODO: Action Items Requiring Human Interaction

The autonomous agent handles implementation, testing, code generation, and local verification. The following steps require explicit external account access, credentials, or production clicks:

1. **Review Random Golden Items**
   - Action: Review 20 random items from `eval/golden_tickets.jsonl` to provide human validation stamps as documented in Section L.
   - Purpose: Ensure synthetic ground-truth tags match human evaluation criteria.

2. **External LLM Free-Tier API Keys (Optional for live provider testing)**
   - To run live models beyond the default deterministic `mock` provider:
     - Google Gemini API key: Get free API key from [Google AI Studio](https://aistudio.google.com/) -> add `GEMINI_API_KEY=...` in `.env`
     - Groq API key: Get free tier key from [Groq Console](https://console.groq.com/) -> add `GROQ_API_KEY=...` in `.env`
     - OpenRouter: [openrouter.ai](https://openrouter.ai/) free models -> add `OPENROUTER_API_KEY=...` in `.env`

3. **Deploy Free Hosted Database (Neon or Supabase)**
   - Neon: Go to [neon.tech](https://neon.tech), create free project, enable pgvector extension in SQL console: `CREATE EXTENSION IF NOT EXISTS vector;`.
   - Copy connection string to `DATABASE_URL`.

4. **Deploy Backend API (Hugging Face Spaces or Render Free Tier)**
   - Hugging Face Spaces: Create Docker Space (free CPU tier), set repository secret for `DATABASE_URL` and `LLM_PROVIDER`.
   - Render: Create Web Service from GitHub repo with Docker environment.

5. **Deploy Frontend Console (Vercel Free Tier)**
   - Connect GitHub repo to [Vercel](https://vercel.com), set root directory to `apps/web`, set `VITE_API_BASE_URL` to the deployed backend API URL.
