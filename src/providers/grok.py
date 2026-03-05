from __future__ import annotations

from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from src.config import GROK_API_KEY
from src.providers.base import ResearchProvider, ResearchBatch, _build_prompt, parse_json_response
from src.utils.logger import get_logger

logger = get_logger(__name__)

RESEARCH_MODEL = "grok-3"


def _is_retryable_openai(exc: BaseException) -> bool:
    """Return True if the exception is transient and worth retrying."""
    if isinstance(exc, (APIConnectionError, RateLimitError)):
        return True
    if isinstance(exc, APIStatusError) and exc.status_code >= 500:
        return True
    return False


class GrokProvider(ResearchProvider):
    """xAI Grok with web search tool."""

    def __init__(self):
        if not GROK_API_KEY:
            raise ValueError("GROK_API_KEY not set in environment")
        self.client = OpenAI(
            api_key=GROK_API_KEY,
            base_url="https://api.x.ai/v1",
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

        logger.info(f"Grok research call using {RESEARCH_MODEL} with web search...")

        response = self.client.chat.completions.create(
            model=RESEARCH_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a lead research analyst. Use web search to find companies and return structured JSON data. Return ONLY valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            tools=[{"type": "web_search"}],
            temperature=0.2,
        )

        text = response.choices[0].message.content or ""
        logger.info(f"Grok returned {len(text)} chars")

        return parse_json_response(text, "Grok")
