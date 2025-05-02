from typing import List, Dict, Any, Set
import logging
import httpx
import os
from dotenv import load_dotenv
from app.research_lib.api.settings_utils import create_settings_snapshot
from app.research_lib.config.llm_config import get_llm as get_configured_llm
from app.research_lib.config.provider_router import provider_overrides_from_env
from app.utils.usage import record_usage
import asyncio
import math

load_dotenv()

logger = logging.getLogger(__name__)



SEARXNG_URL = os.getenv(
    "TEKK_SEARXNG_URL",
    os.getenv("SEARXNG_URL", "https://search.tekkscope.com"),
)
MAX_SEARCH_RESULTS = max(1, int(os.getenv("TEKK_SEARCH_MAX_RESULTS", "50")))
SEARXNG_PAGE_SIZE = max(1, int(os.getenv("TEKK_SEARXNG_PAGE_SIZE", "10")))
SEARXNG_TIMEOUT_SECONDS = max(
    0.5, float(os.getenv("TEKK_SEARXNG_TIMEOUT_SECONDS", "8"))
)

# You can add more configuration options here
# For example, you can add a timeout for the HTTP requests
# or a list of search engines to use
# For now, we will use the default settings

async def search_searxng(
    query: str,
    num_results: int = 10,
    timeout_seconds: float | None = None,
) -> List[Dict[str, Any]]:
    """
    Perform a search using SearXNG and return the results.

    Args:
        query: The search query.
        num_results: The number of results to return.

    Returns:
        A list of search results, where each result is a dictionary
        containing the title, url, and other metadata.
    """
    limit = max(1, min(int(num_results), MAX_SEARCH_RESULTS))
    request_timeout = max(
        0.5,
        float(timeout_seconds or SEARXNG_TIMEOUT_SECONDS),
    )
    page_count = max(1, math.ceil(limit / SEARXNG_PAGE_SIZE))

    async with httpx.AsyncClient(follow_redirects=True) as client:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; TekkscopeBot/1.0)"
        }

        async def fetch_page(page: int) -> List[Dict[str, Any]]:
            url = SEARXNG_URL
            if not url.endswith("/search"):
                url = f"{url.rstrip('/')}/search"
            try:
                response = await client.get(
                    url,
                    params={
                        "q": query,
                        "format": "json",
                        "language": "en",
                        "pageno": page,
                    },
                    timeout=request_timeout,
                    headers=headers,
                )
                response.raise_for_status()
                payload = response.json()
                return payload.get("results", []) if isinstance(payload, dict) else []
            except Exception as error:  # noqa: BLE001 - preserve partial page results
                logger.warning("SearXNG page %s failed for %r: %s", page, query, error)
                return []

        pages = await asyncio.gather(
            *(fetch_page(page) for page in range(1, page_count + 1))
        )
        results: List[Dict[str, Any]] = []
        seen_urls: Set[str] = set()
        for page_results in pages:
            for result in page_results:
                url = result.get("url") if isinstance(result, dict) else None
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                results.append(result)
                if len(results) >= limit:
                    return results
        return results


def get_llm():
    overrides = provider_overrides_from_env(
        max_tokens=int(os.getenv("TEKK_LLM_MAX_TOKENS", "8000")),
        temperature=0,
        search_tool="searxng",
        search_instance_url=SEARXNG_URL,
    )
    settings_snapshot = create_settings_snapshot(overrides=overrides)
    return get_configured_llm(settings_snapshot=settings_snapshot)


async def generate_lightweight_queries(
    prompt: str,
    n: int = 3,
    user_id: str | None = None,
    api_key_id: str | None = None,
) -> List[str]:
    try:
        llm = get_llm()
        template = (
            "Generate {n} diverse, short search queries (JSON array of strings) "
            "to cover different facets of: \"{prompt}\". Keep queries concise."
        )
        text = await llm.ainvoke(template.format(prompt=prompt, n=n))
        content = getattr(text, "content", str(text)) or "[]"

        await asyncio.to_thread(
            record_usage,
            user_id=user_id,
            api_key_id=api_key_id,
            service_used="search_query_generation",
            content=content,
            provider="GEMINI",
            model=os.getenv("LDR_LLM_MODEL", "gemini-2.0-flash"),
        )

        import json
        data = json.loads(content) if isinstance(content, str) else content
        if isinstance(data, list):
            queries = [str(q).strip() for q in data if str(q).strip()]
            return queries[:n] or [prompt]
    except Exception:
        pass
    return [prompt]


async def search_links(
    prompt: str,
    n_queries: int,
    num_results: int,
    enhanced_search: bool,
    user_id: str | None = None,
    api_key_id: str | None = None,
) -> List[Dict[str, Any]]:
    if enhanced_search:
        queries = await generate_lightweight_queries(prompt, n_queries, user_id, api_key_id)
    else:
        queries = [prompt]
    seen: Set[str] = set()
    out: List[Dict[str, Any]] = []
    requested_results = max(1, min(int(num_results), MAX_SEARCH_RESULTS))
    query_results = await asyncio.gather(
        *(search_searxng(q, requested_results) for q in queries),
        return_exceptions=True,
    )
    for q, results in zip(queries, query_results):
        if isinstance(results, Exception):
            logger.warning("Search query failed for %r: %s", q, results)
            continue
        for r in results:
            url = r.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            out.append({"title": r.get("title", ""), "url": url})
            if len(out) >= requested_results:
                return out
    return out
