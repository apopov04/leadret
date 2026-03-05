"""Research trigger and status endpoints."""
from fastapi import APIRouter, HTTPException

from backend.schemas import ResearchRequest, ResearchJobStatus, ProviderInfo
from backend.services.research_runner import start_research, get_job
from src.config import GEMINI_API_KEY, PERPLEXITY_API_KEY, GROK_API_KEY

router = APIRouter(tags=["research"])

_PROVIDER_KEYS = {
    "gemini": GEMINI_API_KEY,
    "perplexity": PERPLEXITY_API_KEY,
    "grok": GROK_API_KEY,
}


@router.post("/research")
def trigger_research(body: ResearchRequest):
    if not body.campaign and not body.prompt:
        raise HTTPException(status_code=400, detail="Provide either campaign or prompt")

    if not _PROVIDER_KEYS.get(body.provider):
        raise HTTPException(status_code=400, detail=f"No API key configured for {body.provider}")

    try:
        job_id = start_research(
            campaign_name=body.campaign,
            prompt=body.prompt,
            provider=body.provider,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Campaign '{body.campaign}' not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"job_id": job_id}


@router.get("/research/{job_id}")
def research_status(job_id: str) -> ResearchJobStatus:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return ResearchJobStatus(**job)


@router.get("/config/providers")
def list_providers() -> list[ProviderInfo]:
    return [
        ProviderInfo(name=name, has_key=bool(key))
        for name, key in _PROVIDER_KEYS.items()
    ]
