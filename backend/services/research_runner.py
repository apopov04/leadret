"""Background research job manager."""
from __future__ import annotations

import collections
import threading
import uuid
from datetime import datetime, timezone

from src.models.campaign import Campaign, load_campaign
from src.models.lead import Lead, Sector, CompanyType
from src.providers.base import LeadResult, get_provider
from src.storage.database import init_db
from src.storage.lead_store import (
    save_leads,
    get_existing_company_names,
    get_blocked_company_names,
)
from src.utils.logger import get_logger

logger = get_logger("research_runner")

# In-memory job store (bounded to last 100 jobs)
_MAX_JOBS = 100
_jobs: collections.OrderedDict[str, dict] = collections.OrderedDict()
_jobs_lock = threading.Lock()


def get_job(job_id: str) -> dict | None:
    with _jobs_lock:
        return _jobs.get(job_id)


def _lead_result_to_lead(result: LeadResult) -> Lead | None:
    """Convert a LeadResult to a Lead. Returns None if conversion fails."""
    try:
        try:
            sector = Sector(result.sector)
        except (ValueError, KeyError):
            sector = Sector.OTHER
        try:
            company_type = CompanyType(result.company_type)
        except (ValueError, KeyError):
            company_type = CompanyType.UNKNOWN

        return Lead(
            company_name=result.company_name,
            sector=sector,
            company_type=company_type,
            funding_stage=result.funding_stage,
            product_name=result.product_name,
            location=result.location,
            website_url=result.website_url if result.website_url.startswith("http") else "",
            source_url=result.source_url if result.source_url.startswith("http") else "",
            source_type="web_search",
            tech_stack=result.tech_stack,
            jetson_usage=result.jetson_usage,
            jetson_models=result.jetson_models,
            jetson_confirmed=result.jetson_confirmed,
            summary=result.summary,
            discovered_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        logger.warning(f"Failed to convert lead '{result.company_name}': {e}")
        return None


def _update_job(job_id: str, **fields):
    """Thread-safe job update."""
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job:
            job.update(fields)


def _run_job(job_id: str, campaign: Campaign, provider_name: str):
    try:
        _update_job(job_id, status="running", phase="INITIALIZING", progress=0.1)

        init_db()
        existing = get_existing_company_names(campaign.name)
        blocked = get_blocked_company_names()
        full_blocklist = list(set(campaign.blocklist + blocked))

        _update_job(job_id, phase="SEARCHING WEB", progress=0.3)

        provider = get_provider(provider_name)
        batch = provider.research(
            description=campaign.description,
            blocklist=full_blocklist,
            exclude_domains=campaign.exclude_domains,
            existing_companies=existing,
        )

        _update_job(job_id, phase="PROCESSING RESULTS", progress=0.7)

        leads = []
        for result in batch.leads:
            lead = _lead_result_to_lead(result)
            if lead:
                leads.append(lead)

        _update_job(job_id, phase="SAVING TO DATABASE", progress=0.9)

        stats = {"saved": 0, "skipped": 0}
        if leads:
            stats = save_leads(leads, campaign.name)

        # Set result before status so clients never see completed + null result
        _update_job(job_id, result=stats, progress=1.0, phase="COMPLETE", status="completed")
        logger.info(f"Job {job_id} completed: {stats}")

    except Exception as e:
        _update_job(job_id, error=str(e), progress=1.0, status="failed")
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)


def start_research(
    campaign_name: str | None = None,
    prompt: str | None = None,
    provider: str = "gemini",
) -> str:
    """Start a research job in background. Returns job_id."""
    if campaign_name:
        campaign = load_campaign(campaign_name)
    elif prompt:
        campaign = Campaign.from_adhoc(prompt)
    else:
        raise ValueError("Provide either campaign or prompt")

    job_id = str(uuid.uuid4())[:12]

    with _jobs_lock:
        # Evict oldest jobs if at capacity
        while len(_jobs) >= _MAX_JOBS:
            _jobs.popitem(last=False)
        _jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "progress": 0.0,
            "phase": "QUEUED",
            "result": None,
            "error": None,
        }

    thread = threading.Thread(target=_run_job, args=(job_id, campaign, provider), daemon=True)
    thread.start()

    return job_id
