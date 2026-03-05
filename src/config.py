import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CAMPAIGNS_DIR = BASE_DIR / "campaigns"

_db_env = os.getenv("DATABASE_PATH", "")
DATABASE_PATH = Path(_db_env) if _db_env and Path(_db_env).is_absolute() else DATA_DIR / "lead_scout.db"

# Research provider: gemini, perplexity, or grok
RESEARCH_PROVIDER = os.getenv("RESEARCH_PROVIDER", "gemini")

# Provider API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
GROK_API_KEY = os.getenv("GROK_API_KEY", "")


def ensure_dirs() -> None:
    """Create required directories if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CAMPAIGNS_DIR.mkdir(parents=True, exist_ok=True)
