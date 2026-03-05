from __future__ import annotations

import json
import re
from urllib.parse import urlparse

from google import genai
from google.genai import types
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from src.config import GEMINI_API_KEY
from src.providers.base import ResearchProvider, ResearchBatch, LeadResult, _build_prompt
from src.utils.logger import get_logger

logger = get_logger(__name__)

RESEARCH_MODEL = "gemini-2.5-flash"

# Pattern to strip Gemini citation markers like [cite: 1], [cite: 25, 26], etc.
CITE_PATTERN = re.compile(r"\[cite:\s*[\d,\s]*(?:in previous turn)?\s*\]", re.IGNORECASE)

# Google grounding redirect URLs are not real source URLs
GROUNDING_URL_PREFIX = "https://vertexaisearch.cloud.google.com"


def _clean_citations(text: str) -> str:
    """Remove Gemini citation markers from text."""
    return CITE_PATTERN.sub("", text).strip()


def _is_grounding_url(url: str) -> bool:
    """Check if a URL is a Gemini grounding redirect (not a real URL)."""
    return url.startswith(GROUNDING_URL_PREFIX)


def _url_domain(url: str) -> str:
    """Extract domain from URL for comparison."""
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def _is_retryable_gemini(exc: BaseException) -> bool:
    """Return True if the exception is transient and worth retrying."""
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return True
    status = getattr(exc, "status_code", None)
    if status is not None and (status >= 500 or status == 429):
        return True
    return False


class GeminiProvider(ResearchProvider):
    """Google Gemini with Search grounding."""

    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set in environment")
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    @retry(
        retry=retry_if_exception(_is_retryable_gemini),
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

        logger.info(f"Gemini research call using {RESEARCH_MODEL} with grounding...")

        # Step 1: Grounded search call (cap thinking to keep it fast)
        search_response = self.client.models.generate_content(
            model=RESEARCH_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.2,
                thinking_config=types.ThinkingConfig(thinking_budget=1024),
            ),
        )

        grounded_text = search_response.text

        # Extract grounding data: real URLs and text-to-URL mappings
        chunk_urls, text_url_map = self._extract_grounding_data(search_response)

        # Clean citation markers from the grounded text
        grounded_text = _clean_citations(grounded_text)
        logger.info(
            f"Grounded search returned {len(grounded_text)} chars, "
            f"{len(chunk_urls)} source URLs, {len(text_url_map)} text-URL mappings"
        )

        # Step 2: Extract structured data from grounded response
        url_list = ""
        if chunk_urls:
            url_list = (
                "\n\nSource URLs from this search session (these are the real, permanent URLs "
                "where information was found — use these for source_url):\n"
                + "\n".join(f"- {u}" for u in chunk_urls[:30])
            )

        extraction_prompt = (
            "Extract the company leads from this research into a JSON object.\n\n"
            "Research results:\n" + grounded_text + "\n\n"
            + url_list + "\n\n"
            "IMPORTANT:\n"
            "- website_url = the company's own homepage (e.g. https://company.com)\n"
            "- source_url = the EXACT URL where the information about this company was found. "
            "Pick from the source URLs listed above. This is typically a news article, blog post, "
            "case study, or press release — NOT the company's own homepage.\n"
            "- NEVER use vertexaisearch.cloud.google.com URLs.\n"
            "- NEVER set source_url equal to website_url unless the info literally came from the company's site.\n"
            "- Do NOT include citation markers like [cite: N] in any field.\n\n"
            "Return a JSON object with two fields:\n"
            '- "leads": array of objects, each with: company_name, sector, company_type, '
            "funding_stage, product_name, location, website_url, source_url, tech_stack, "
            "jetson_usage, jetson_models, jetson_confirmed, summary\n"
            '- "search_queries_used": array of search queries used\n\n'
            "Return ONLY valid JSON, no markdown fences."
        )

        extract_response = self.client.models.generate_content(
            model=RESEARCH_MODEL,
            contents=extraction_prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )

        return self._parse_response(extract_response.text, chunk_urls, text_url_map)

    def _extract_grounding_data(self, response) -> tuple[list[str], dict[str, list[str]]]:
        """Extract real source URLs and text-to-URL mappings from grounding metadata.

        Returns:
            chunk_urls: deduplicated list of real source URLs
            text_url_map: dict mapping text snippets to their source URLs
        """
        chunk_urls_list: list[str] = []  # ordered list, index matches grounding_chunk_indices
        chunk_url_set: dict[str, None] = {}  # dedup preserving order
        text_url_map: dict[str, list[str]] = {}

        try:
            candidates = response.candidates or []
            for candidate in candidates:
                metadata = getattr(candidate, "grounding_metadata", None)
                if not metadata:
                    continue

                # Build ordered chunk URL list (index matters for mapping)
                chunks = getattr(metadata, "grounding_chunks", None) or []
                for chunk in chunks:
                    web = getattr(chunk, "web", None)
                    url = ""
                    if web and hasattr(web, "uri") and web.uri:
                        if not _is_grounding_url(web.uri):
                            url = web.uri
                            chunk_url_set[url] = None
                    chunk_urls_list.append(url)

                # Map text segments to their source URLs via chunk indices
                supports = getattr(metadata, "grounding_supports", None) or []
                for support in supports:
                    segment = getattr(support, "segment", None)
                    indices = getattr(support, "grounding_chunk_indices", None) or []
                    if not segment:
                        continue
                    text = getattr(segment, "text", "") or ""
                    text = text.strip()
                    if not text or len(text) < 5:
                        continue
                    # Resolve chunk indices to real URLs
                    urls_for_segment = []
                    for idx in indices:
                        if idx < len(chunk_urls_list) and chunk_urls_list[idx]:
                            urls_for_segment.append(chunk_urls_list[idx])
                    if urls_for_segment:
                        text_url_map[text] = urls_for_segment

        except Exception as e:
            logger.debug(f"Could not extract grounding data: {e}")

        return list(chunk_url_set.keys()), text_url_map

    def _find_source_for_company(
        self,
        company_name: str,
        chunk_urls: list[str],
        text_url_map: dict[str, list[str]],
        website_url: str = "",
    ) -> str | None:
        """Try to find the real source URL for a company using grounding text-URL mappings."""
        if not company_name:
            return None

        name_lower = company_name.lower()
        company_domain = _url_domain(website_url) if website_url else ""

        # Search text-URL mappings for mentions of this company
        for text_snippet, urls in text_url_map.items():
            if name_lower in text_snippet.lower():
                # Return the first non-company-website URL that mentions this company
                for url in urls:
                    url_domain = _url_domain(url)
                    # Skip if this URL is the company's own site
                    if company_domain and url_domain == company_domain:
                        continue
                    return url
                # If all URLs are the company's own site, still return one
                if urls:
                    return urls[0]

        return None

    def _parse_response(
        self,
        text: str,
        chunk_urls: list[str] | None = None,
        text_url_map: dict[str, list[str]] | None = None,
    ) -> ResearchBatch:
        """Parse the JSON response into a ResearchBatch."""
        chunk_urls = chunk_urls or []
        text_url_map = text_url_map or {}

        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON response: {e}")
            return ResearchBatch()

        leads = []
        for item in data.get("leads", []):
            try:
                # Clean citation markers from all string fields
                for key, val in item.items():
                    if isinstance(val, str):
                        item[key] = _clean_citations(val)

                company_name = item.get("company_name", "")
                source = item.get("source_url", "")
                website = item.get("website_url", "")

                # Fix grounding redirect URLs
                if _is_grounding_url(source):
                    item["source_url"] = ""
                    source = ""
                if _is_grounding_url(website):
                    item["website_url"] = ""
                    website = ""

                # If source_url is missing or same as website, try to find real source
                source_is_bad = (
                    not source
                    or source == website
                    or _url_domain(source) == _url_domain(website)
                )
                if source_is_bad:
                    real_source = self._find_source_for_company(
                        company_name, chunk_urls, text_url_map, website_url=website
                    )
                    if real_source:
                        item["source_url"] = real_source
                        logger.debug(f"Mapped {company_name} -> {real_source}")

                # Final fallback: if still no source_url, use website
                if not item.get("source_url"):
                    if website:
                        item["source_url"] = website
                        logger.debug(f"Fell back to website_url for {company_name}")
                    else:
                        logger.warning(f"No URL at all for {company_name}, skipping")
                        continue

                leads.append(LeadResult(**item))
            except Exception as e:
                logger.warning(f"Skipping malformed lead: {e}")

        return ResearchBatch(
            leads=leads,
            search_queries_used=data.get("search_queries_used", []),
        )
