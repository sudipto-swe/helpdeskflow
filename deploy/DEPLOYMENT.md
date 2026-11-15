# Free Deployment Plan & Deployment Configurations

This directory contains manifests and instructions for deploying HelpdeskFlow completely free of charge without credit cards.

---

## 1. Architecture on Free-Tier Services

| Tier | Component | Free Provider | Free Tier Limits & Cold Starts |
|---|---|---|---|
| **Frontend** | React / Vite SPA | **Vercel** | Free Hobby tier, 100GB bandwidth, fast global edge CDN |
| **Backend API** | FastAPI Docker Container | **Hugging Face Spaces** or **Render** | HF Spaces: 2 vCPU, 16GB RAM free (no sleep if pinged), or Render: 512MB RAM (spins down after 15 min idle, 50s cold start) |
| **Database** | PostgreSQL + pgvector | **Neon** or **Supabase** | Neon: 0.5 GB storage, free pgvector extension, serverless pause |

---

## 2. Deployment Configurations

### A. Docker App on Hugging Face Spaces
Create a `Dockerfile` space on Hugging Face:
- Base: Docker
- SDK: Dockerfile located at `deploy/hf_spaces/Dockerfile`
- Expose Port: `7860` (or set `API_PORT=7860`)

### B. Vercel Configuration
File `deploy/vercel.json`:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite"
}
```

### C. Public Demo Notice
All public deployments display the amber banner:
`DEMO ENVIRONMENT: BengalNet & Bazar — Synthetic Data Only`
