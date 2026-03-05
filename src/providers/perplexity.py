from __future__ import annotations

from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from src.config import PERPLEXITY_API_KEY
from src.providers.base import ResearchProvider, ResearchBatch, _build_prompt, parse_json_response
from src.utils.logger import get_logger

logger = get_logger(__name__)

RESEARCH_MODEL = "sonar-pro"


def _is_retryable_openai(exc: BaseException) -> bool:
    """Return True if the exception is transient and worth retrying."""
    if isinstance(exc, (APIConnectionError, RateLimitError)):
        return True
    if isinstance(exc, APIStatusError) and exc.status_code >= 500:
        return True
    return False


class PerplexityProvider(ResearchProvider):
    """Perplexity Sonar — every call is automatically search-grounded."""

    def __init__(self):
        if not PERPLEXITY_API_KEY:
            raise ValueError("PERPLEXITY_API_KEY not set in environment")
        self.client = OpenAI(
            api_key=PERPLEXITY_API_KEY,
            base_url="https://api.perplexity.ai",
        )

    @retry(
        retry=retry_if_exception(_is_retryable_openai),
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=2, max=30),
    )
    def research(
        self,
        description: str,
        blocklist: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        existing_companies: list[str] | None = None,
    ) -> ResearchBatch:
        prompt = _build_prompt(description, blocklist, exclude_domains, existing_companies)

        logger.info(f"Perplexity research call using {RESEARCH_MODEL}...")

        response = self.client.chat.completions.create(
            model=RESEARCH_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a lead research analyst. Search the web and return structured JSON data about companies. Return ONLY valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        text = response.choices[0].message.content or ""
        logger.info(f"Perplexity returned {len(text)} chars")

        return parse_json_response(text, "Perplexity")
