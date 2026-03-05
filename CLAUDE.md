# CLAUDE.md

## Project Overview

LeadRet (Leadrador Retriever) — LLM-driven lead intelligence system. Uses AI models with built-in web search (Gemini, Perplexity, or Grok) to find companies matching a campaign description, extract structured data, and present results in a React + FastAPI dashboard.

## Development Commands

### Setup
```bash
cd leadret

# Backend
python -m venv venv
./venv/Scripts/python.exe -m pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

**Windows Git Bash Note:** Never use `source venv/Scripts/activate`. Instead, invoke the venv Python directly:
```bash
./venv/Scripts/python.exe -m pip install -r requirements.txt
```

### Run the App (two terminals)

**Terminal 1 — Backend:**
```bash
./venv/Scripts/python.exe run_api.py
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Backend at http://localhost:8000, frontend at http://localhost:5173.

### Run Pipeline (CLI)
```bash
./venv/Scripts/python.exe run_pipeline.py --campaign jetson                         # YAML campaign
./venv/Scripts/python.exe run_pipeline.py --prompt "Find robotics startups using ROS2"  # Ad-hoc
./venv/Scripts/python.exe run_pipeline.py --campaign jetson --provider perplexity    # Override provider
```

### Environment
Copy `.env.example` to `.env` and set `RESEARCH_PROVIDER` and the corresponding API key (`GEMINI_API_KEY`, `PERPLEXITY_API_KEY`, or `GROK_API_KEY`). Only one provider key is needed. Gemini is the default and has a free tier.

## Architecture

### LLM-Driven Research

One prompt, one call, structured output:
1. Campaign YAML (or ad-hoc prompt) defines what to search for
2. `ResearchProvider.research()` sends the description to an AI with web search
3. AI searches the web, extracts structured `LeadResult[]`
4. Results are deduped against DB and saved to SQLite
5. React dashboard shows leads in a feed (newest first) with rating/feedback

### Research Providers

- **Gemini** (`gemini-2.5-flash`) — Google Gemini with Search grounding. Two-step: grounded search → structured extraction.
- **Perplexity** (`sonar-pro`) — Every call is automatically search-grounded. OpenAI-compatible API.
- **Grok** (`grok-3`) — xAI Grok with `web_search` tool. OpenAI-compatible API.

Provider is just the search engine — the campaign is the bucket. Switching providers mid-campaign is safe.

### Campaign System

Campaigns are YAML files in `campaigns/`. Can also be created/edited/deleted from the dashboard UI.
- `name` — Display name
- `description` — Natural language research brief (the prompt sent to the AI)
- `blocklist` — Known companies to skip
- `exclude_domains` — Domains to ignore

### Storage
- **SQLite** with WAL mode, shared connection + threading lock
- Tables: `leads`, `blocked_companies`
- All data in `data/lead_scout.db`
- Case-insensitive dedup via `COLLATE NOCASE` unique index

### Dashboard
- **React + TypeScript + Vite** frontend with **FastAPI** backend
- Sidebar: campaign CRUD (+/edit/delete), provider selector, execute button, blocklist
- Lead cards with interactive star rating (1-5), delete, block company
- Queue (unrated) and Rated tab views
- Stats bar: total leads, rated, queue count
- Dual theme support (clean light / Pip-Boy terminal green)
- Theme-aware favicon and logo (dog icon)

### Key Backend Patterns
- Background research jobs run in threads with thread-safe status updates
- Job store bounded to 100 entries with LRU eviction
- `_lead_result_to_lead` catches errors per-lead (skips bad data, doesn't crash the job)
- Tenacity retry with predicates: only retries transient errors (connection, rate limit, 5xx)
- SSRF protection in CLI pipeline via private IP range blocking

## Project Structure

```
lead-scout/
  .env.example
  requirements.txt
  CLAUDE.md
  run_api.py              # FastAPI backend launcher
  run_pipeline.py         # CLI pipeline entry point
  run_dashboard.py        # Legacy Streamlit dashboard launcher
  backend/
    main.py               # FastAPI app + CORS
    schemas.py            # Pydantic request/response models
    routes/               # API route modules (leads, campaigns, blocked, research, stats)
    services/
      research_runner.py  # Background job manager with thread-safe updates
  frontend/
    public/               # Static assets (dog logos: green, blue, black)
    src/
      App.tsx             # Main React app
      api/                # API client functions
      components/         # React components (sidebar, leads, stats, common)
      context/            # Theme context with localStorage persistence
      hooks/              # TanStack Query hooks (useLeads, useResearch, useStats)
      types/              # TypeScript interfaces
    index.html
  campaigns/
    jetson.yaml           # Default campaign config
  data/                   # SQLite DB (gitignored)
  src/
    config.py             # Settings from .env
    models/
      lead.py             # Lead, Sector, CompanyType
      campaign.py         # Campaign + YAML loader
    storage/
      database.py         # SQLite schema + shared connection with lock
      lead_store.py       # All CRUD operations
    providers/
      base.py             # LeadResult, ResearchBatch, ResearchProvider ABC
      gemini.py           # Google Gemini provider
      perplexity.py       # Perplexity Sonar provider
      grok.py             # xAI Grok provider
    utils/
      logger.py           # Rich-based logging
  dashboard/
    app.py                # Legacy Streamlit dashboard
```
