"""LeadRet — LLM-Driven Research Pipeline

Runs a single LLM research step: give an AI with built-in web search
a campaign description, and let it find and extract structured lead data.

Usage:
    python run_pipeline.py --campaign jetson           # Run with YAML campaign
    python run_pipeline.py --prompt "Find robotics startups using ROS2"  # Ad-hoc
"""
import argparse
import sys
import time
import ipaddress
import socket
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

from src.config import DATABASE_PATH, RESEARCH_PROVIDER
from src.models.campaign import Campaign, load_campaign, list_campaigns
from src.models.lead import Lead, Sector, CompanyType
from src.providers.base import LeadResult, get_provider
from src.storage.database import init_db
from src.storage.lead_store import save_leads, get_existing_company_names, get_blocked_company_names, count_leads
from src.utils.logger import get_logger

logger = get_logger("pipeline")


_PRIVATE_NETWORKS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
)


def _is_private_url(url: str) -> bool:
    """Return True if the URL resolves to a private/internal IP address (SSRF guard)."""
    try:
        hostname = urlparse(url).hostname
        if not hostname:
            return True
        for family, _type, _proto, _canonname, sockaddr in socket.getaddrinfo(
            hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM
        ):
            addr = ipaddress.ip_address(sockaddr[0])
            if any(addr in net for net in _PRIVATE_NETWORKS):
                return True
    except (socket.gaierror, ValueError, OSError):
        return True
    return False


def _url_reachable(url: str, timeout: int = 5) -> bool:
    """Check if a URL resolves with a HEAD request (falls back to GET)."""
    if not url or not url.startswith("http"):
        return False
    if _is_private_url(url):
        return False
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        if resp.status_code < 400:
            return True
        # Some servers reject HEAD, try GET
        resp = requests.get(url, timeout=timeout, allow_redirects=True, stream=True)
        return resp.status_code < 400
    except Exception:
        return False


def _lead_result_to_lead(result: LeadResult) -> Lead | None:
    """Convert a LeadResult from the provider into a Lead model. Returns None if invalid."""
    # Normalize missing URLs to empty string
    if result.source_url and not result.source_url.startswith("http"):
        result.source_url = ""
    if result.website_url and not result.website_url.startswith("http"):
        result.website_url = ""

    # Verify URLs — flag bad ones but keep the lead
    if result.website_url and not _url_reachable(result.website_url):
        logger.warning(f"website_url does not resolve for {result.company_name}: {result.website_url}")
        result.website_url = ""

    if not _url_reachable(result.source_url):
        logger.warning(f"source_url does not resolve for {result.company_name}: {result.source_url}")
        if result.website_url:
            result.source_url = result.website_url
        else:
            result.source_url = ""

    # Safe enum parsing
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
        website_url=result.website_url,
        source_url=result.source_url,
        source_type="web_search",
        tech_stack=result.tech_stack,
        jetson_usage=result.jetson_usage,
        jetson_models=result.jetson_models,
        jetson_confirmed=result.jetson_confirmed,
        summary=result.summary,
        discovered_at=datetime.now(timezone.utc),
    )


def main():
    parser = argparse.ArgumentParser(description="LeadRet — LLM Research Pipeline")
    parser.add_argument("--campaign", help="Campaign name (filename without .yaml)")
    parser.add_argument("--prompt", help="Free-text research prompt (creates ad-hoc campaign)")
    parser.add_argument("--provider", help=f"Research provider override (default: {RESEARCH_PROVIDER})")
    args = parser.parse_args()

    if not args.campaign and not args.prompt:
        parser.error("Provide either --campaign or --prompt")

    # Load or create campaign
    if args.campaign:
        try:
            campaign = load_campaign(args.campaign)
        except FileNotFoundError:
            available = list_campaigns()
            logger.error(f"Campaign '{args.campaign}' not found. Available: {available}")
            sys.exit(1)
    else:
        campaign = Campaign.from_adhoc(args.prompt)

    provider_name = args.provider or RESEARCH_PROVIDER

    logger.info(f"LeadRet Research — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Campaign: {campaign.name}")
    logger.info(f"Provider: {provider_name}")
    logger.info(f"Database: {DATABASE_PATH}")

    init_db()
    start = time.time()

    try:
        # Get dedup hints
        existing = get_existing_company_names(campaign.name)
        blocked = get_blocked_company_names()
        full_blocklist = list(set(campaign.blocklist + blocked))

        if existing:
            logger.info(f"Existing companies in DB: {len(existing)}")
        if full_blocklist:
            logger.info(f"Blocklist: {len(full_blocklist)} companies")

        # Run research
        provider = get_provider(provider_name)
        logger.info("Starting research...")
        batch = provider.research(
            description=campaign.description,
            blocklist=full_blocklist,
            exclude_domains=campaign.exclude_domains,
            existing_companies=existing,
        )

        logger.info(f"Provider returned {len(batch.leads)} leads")
        if batch.search_queries_used:
            logger.info(f"Queries used: {batch.search_queries_used}")

        # Convert and filter
        leads = []
        for result in batch.leads:
            lead = _lead_result_to_lead(result)
            if lead:
                leads.append(lead)

        logger.info(f"Valid leads after filtering: {len(leads)}")

        # Save
        if leads:
            stats = save_leads(leads, campaign.name)
            logger.info(f"Save results: {stats}")

    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        sys.exit(1)

    elapsed = time.time() - start
    logger.info(f"Research completed in {elapsed:.1f}s")
    logger.info(f"Total leads in DB for '{campaign.name}': {count_leads(campaign.name)}")


if __name__ == "__main__":
    main()
