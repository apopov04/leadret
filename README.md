<p align="center">
  <img src="frontend/public/leadret-black.png" alt="LeadRet" width="120" />
</p>

<h1 align="center">LeadRet</h1>

<p align="center">
  <em>Leadrador Retriever — an AI-powered lead intelligence tool that fetches companies for you.</em>
</p>

LeadRet uses AI models with built-in web search (Google Gemini, Perplexity, or Grok) to find companies matching a description you write, extract structured data about each one, and present the results in a clean dashboard where you can rate, filter, and manage your leads.

---

## Setup Guide

Follow these steps to get LeadRet running on your machine. No prior coding experience needed — just follow along.

### Step 1: Install Prerequisites

You need three things installed:

| Tool | What it does | Download |
|------|-------------|----------|
| **Python 3.10+** | Runs the backend server | [python.org/downloads](https://www.python.org/downloads/) |
| **Node.js 18+** | Runs the frontend dashboard | [nodejs.org](https://nodejs.org/) (pick the LTS version) |
| **Git** | Downloads the project code | [git-scm.com](https://git-scm.com/downloads) |

To check if you already have them, open a terminal and run:

```bash
python --version
node --version
git --version
```

If each one prints a version number, you're good.

### Step 2: Download the Project

Open a terminal and run:

```bash
git clone https://github.com/apopov04/leadret.git
cd leadret
```

### Step 3: Install Python Dependencies

```bash
# Create a virtual environment
python -m venv venv

# Install packages — pick your OS:

# Windows (Git Bash or Command Prompt)
./venv/Scripts/python.exe -m pip install -r requirements.txt

# macOS / Linux
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### Step 5: Get an API Key

LeadRet needs an API key from at least one AI provider to search the web. Pick one:

| Provider | Where to get a key | Cost |
|----------|-------------------|------|
| **Gemini** (recommended) | [aistudio.google.com](https://aistudio.google.com) | Free tier available |
| **Perplexity** | [perplexity.ai](https://docs.perplexity.ai) | Pay-per-use |
| **Grok** | [console.x.ai](https://console.x.ai) | Pay-per-use |

### Step 6: Configure Your API Key

1. Copy the example config file:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` in any text editor and replace the placeholder with your real key:
   ```
   RESEARCH_PROVIDER=gemini
   GEMINI_API_KEY=your-actual-api-key-here
   ```
   Only fill in the key for the provider you chose. Leave the others as-is.

### Step 7: Start LeadRet

You need two terminal windows running at the same time:

**Terminal 1 — Backend:**
```bash
# Windows
./venv/Scripts/python.exe run_api.py

# macOS / Linux
python run_api.py
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open your browser and go to **[http://localhost:5173](http://localhost:5173)**. You should see the LeadRet dashboard.

---

## Features & How to Use

### Campaigns

Campaigns are saved research templates. Each campaign has a **name** and a **description** (the prompt that tells the AI what kind of companies to find).

- **Select a campaign** from the dropdown in the sidebar
- **Create a new campaign** by clicking the **+** button — give it a name and describe the companies you're looking for
- **Edit a campaign** by clicking the **pencil** icon — change the name or refine the prompt
- **Delete a campaign** by clicking the **trash** icon — you'll be asked to confirm before it's removed
- **Ad-hoc query** — select "AD-HOC QUERY" from the dropdown to run a one-off search without saving a campaign

### Running Research

1. Select a campaign (or write an ad-hoc query)
2. Choose a research provider from the **Execute** section (Gemini, Perplexity, or Grok)
3. Click **EXECUTE**
4. A progress bar shows the current phase (searching, processing, saving)
5. When done, new leads appear in the **Queue** tab

You can switch providers between runs — all results land in the same campaign regardless of which AI found them.

### Managing Leads

Leads appear in two tabs:

- **Queue** — New, unrated leads waiting for your review
- **Rated** — Leads you've already scored

For each lead in the **Queue**, you can:
- **Rate it 1-5 stars** — hover over the stars and click to rate (moves it to the Rated tab)
- **Delete it** — remove the lead permanently
- **Block the company** — adds the company to a blocklist so it never appears again

For each lead in the **Rated** tab, you can:
- **Back to Queue** — send it back for re-evaluation
- **Push to Salesforce** — placeholder button for future CRM integration

### Lead Cards

Each lead card shows:
- **Company name** and star rating
- **Sector**, **company type**, and **location** tags
- **Product name**, **tech stack** badges, and **funding stage**
- **Website link** (or a text input to manually add one if missing)
- **Source URL** — collapsible dropdown showing where the AI found the company
- **Summary** — a short description from the AI about what the company does

### Blocklist

The sidebar shows all blocked companies. Click the **X** next to any name to unblock it and allow that company to appear in future results.

### Themes

Click the **sun/moon icon** in the sidebar header to toggle between:
- **Clean theme** — light background with blue accents
- **Pip-Boy theme** — dark terminal-style theme with green accents (Fallout-inspired)

The favicon and sidebar logo change to match the active theme.

### CLI Pipeline

You can also run research from the command line without the dashboard:

```bash
# Using a saved campaign
python run_pipeline.py --campaign jetson

# Using a free-text prompt
python run_pipeline.py --prompt "Find robotics startups using ROS2"

# Override the default provider
python run_pipeline.py --campaign jetson --provider perplexity
```

The CLI version also verifies website URLs via HEAD requests and flags unreachable ones.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI + Uvicorn |
| Frontend | React + TypeScript + Vite + TanStack Query |
| Research | Gemini 2.5 Flash / Perplexity Sonar Pro / Grok 3 |
| Structured output | Pydantic models + JSON parsing |
| Database | SQLite with WAL mode |
| Styling | Tailwind CSS + CSS custom properties (dual theme) |
| Deduplication | Suffix-normalized company names (case-insensitive) |
| Retry logic | Tenacity (3x exponential backoff) |

## Coming Soon

**Flexible data model** — Campaigns now define their own custom fields instead of hardcoded ones. Sector is free-text instead of a fixed enum. New custom field editor in the sidebar with drag-and-drop reordering. Deleting a campaign cleans up its leads too.

**Bug fixes** — Fixed 7 bugs across frontend and backend: silent failures, bad URL validation, missing error states, and data integrity issues.

**Cleanup** — Removed the old Streamlit dashboard. Made API URLs and CORS configurable via env vars. Proper DB shutdown. Added accessibility labels.

**Stability** — Thread-safe research jobs, bounded job store, per-lead error handling so one bad result doesn't crash the whole run. Fixed a CSS ordering issue with Tailwind v4.

## License

MIT
