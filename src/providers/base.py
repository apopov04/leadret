from __future__ import annotations

import enum
import json
from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel, Field

from src.utils.logger import get_logger

_logger = get_logger(__name__)


class LeadResult(BaseModel):
    """What the LLM returns per lead."""
    company_name: str
    sector: str = "other"
    company_type: str = "unknown"
    funding_stage: Optional[str] = None
    product_name: str = ""
    location: Optional[str] = None
    website_url: str = ""
    source_url: str
    tech_stack: list[str] = Field(default_factory=list)
    jetson_usage: Optional[str] = None
    jetson_models: list[str] = Field(default_factory=list)
    jetson_confirmed: bool = False
    summary: str = ""


class ResearchBatch(BaseModel):
    """Wrapper around the LLM research results."""
    leads: list[LeadResult] = Field(default_factory=list)
    search_queries_used: list[str] = Field(default_factory=list)


class ResearchProvider(ABC):
    """Abstract base class for LLM-driven research providers."""

    @abstractmethod
    def research(
        self,
        description: str,
        blocklist: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        existing_companies: list[str] | None = None,
    ) -> ResearchBatch:
        ...


def _build_prompt(
    description: str,
    blocklist: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    existing_companies: list[str] | None = None,
) -> str:
    """Build the research prompt from campaign parameters."""
    parts = [
        "You are a lead research analyst. Your task is to search the web and find companies matching this brief:\n",
        description.strip(),
        "\n\nFor each company you find, extract structured data with these fields:",
        "- company_name: Official company name",
        "- sector: One of: robotics, autonomous_vehicles, industrial_automation, smart_cities, healthcare, agriculture, retail, defense, drones, edge_ai, computer_vision, other",
        "- company_type: One of: end_user, reseller, manufacturer, service_provider, distributor, unknown",
        "- funding_stage: e.g. 'Series A', 'Seed', 'Public', etc. (null if unknown)",
        "- product_name: Their main product or solution name",
        "- location: City, State/Country",
        "- website_url: Company website URL",
        "- source_url: The URL where you found information about this company (REQUIRED — must be a real, valid URL)",
        "- tech_stack: List of technologies they use",
        "- jetson_usage: Free text describing how they use Jetson (null if not applicable)",
        "- jetson_models: List of specific Jetson models (e.g. 'Orin NX', 'AGX Xavier')",
        "- jetson_confirmed: true if the company is confirmed to use NVIDIA Jetson",
        "- summary: 1-2 sentence summary of the company and why they're relevant",
    ]

    if blocklist:
        parts.append(f"\n\nDO NOT include these companies (blocklist): {', '.join(blocklist)}")

    if exclude_domains:
        parts.append(f"\nDO NOT use results from these domains: {', '.join(exclude_domains)}")

    if existing_companies:
        parts.append(f"\nSkip companies already found: {', '.join(existing_companies)}")

    parts.append(
        "\n\nReturn your results as a JSON object with two fields:"
        '\n- "leads": array of lead objects with the fields described above'
        '\n- "search_queries_used": array of search queries you used'
        "\n\nFind as many relevant companies as possible (aim for 10-20). "
        "Focus on real companies with real products, not press releases or listicles. "
        "Every lead MUST have a valid source_url where you found the information."
    )

    return "\n".join(parts)


def parse_json_response(text: str, provider_name: str) -> ResearchBatch:
    """Parse a JSON response from an LLM provider into a ResearchBatch.

    Shared by providers that return plain JSON (Perplexity, Grok).
    Strips markdown fences, parses the JSON, and validates each lead.

    Args:
        text: Raw text response from the LLM.
        provider_name: Name of the provider (used in log messages).

    Returns:
        A validated ResearchBatch.
    """
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        _logger.error(f"Failed to parse {provider_name} JSON response: {e}")
        return ResearchBatch()

    leads = []
    for item in data.get("leads", []):
        try:
            leads.append(LeadResult(**item))
        except Exception as e:
            _logger.warning(f"Skipping malformed lead: {e}")

    return ResearchBatch(
        leads=leads,
        search_queries_used=data.get("search_queries_used", []),
    )


def get_provider(name: str) -> ResearchProvider:
    """Factory function to get a research provider by name."""
    name = name.lower().strip()
    if name == "gemini":
        from src.providers.gemini import GeminiProvider
        return GeminiProvider()
    elif name == "perplexity":
        from src.providers.perplexity import PerplexityProvider
        return PerplexityProvider()
    elif name == "grok":
        from src.providers.grok import GrokProvider
        return GrokProvider()
    else:
        raise ValueError(f"Unknown research provider: {name}. Use 'gemini', 'perplexity', or 'grok'.")
