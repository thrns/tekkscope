import asyncio
from typing import List, Dict, Any
import logging
import os
from bs4 import BeautifulSoup
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext
from crawlee.storage_clients import MemoryStorageClient
from urllib.parse import urljoin, urlparse
from app.streaming import manager
from app.clients.search import search_links
from dotenv import load_dotenv
from app.utils.usage import record_usage


load_dotenv()

logger = logging.getLogger(__name__)

MAX_SCRAPE_SOURCES = max(1, int(os.getenv("TEKK_SCRAPE_MAX_SOURCES", "50")))
SCRAPE_TIMEOUT_SECONDS = max(
    0.5, float(os.getenv("TEKK_SCRAPE_TIMEOUT_SECONDS", "8"))
)
SCRAPE_CONCURRENCY = max(1, int(os.getenv("TEKK_SCRAPE_CONCURRENCY", "20")))


def _source_limit(requested: int) -> int:
    try:
        requested_limit = int(requested)
    except (TypeError, ValueError):
        requested_limit = MAX_SCRAPE_SOURCES
    return max(1, min(requested_limit, MAX_SCRAPE_SOURCES))


def _create_crawler() -> PlaywrightCrawler:
    """Create a concurrent crawler while remaining compatible with old Crawlee."""
    try:
        return PlaywrightCrawler(
            storage_client=MemoryStorageClient(),
            max_concurrency=SCRAPE_CONCURRENCY,
        )
    except TypeError:
        # Older Crawlee releases accepted the storage client but not the
        # concurrency keyword. They still manage request scheduling internally.
        return PlaywrightCrawler(storage_client=MemoryStorageClient())


async def _run_crawler(crawler: PlaywrightCrawler, urls: List[str], timeout: float) -> None:
    await asyncio.wait_for(crawler.run(urls), timeout=max(0.1, timeout))

async def extract_content(
    urls: List[str], timeout_seconds: float | None = None
) -> Dict[str, str]:
    """
    Extract the content from a list of URLs using Crawlee.

    Args:
        urls: A list of URLs to extract content from.

    Returns:
        A dictionary where the keys are the URLs and the values are the
        extracted content.
    """
    extracted_data = {}

    crawler = _create_crawler()

    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        content = await context.page.evaluate("() => document.body.innerText")
        extracted_data[context.request.url] = content
        await context.push_data({"url": context.request.url, "content": content})

    try:
        await _run_crawler(
            crawler,
            urls[:MAX_SCRAPE_SOURCES],
            timeout_seconds if timeout_seconds is not None else SCRAPE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning(
            "Content extraction reached the %ss deadline", SCRAPE_TIMEOUT_SECONDS
        )
    return extracted_data

async def search_and_extract(
    query: str, num_results: int = MAX_SCRAPE_SOURCES
) -> Dict[str, str]:
    """
    Perform a search and extract the content from the search results.

    Args:
        query: The search query.
        num_results: The number of results to process.

    Returns:
        A dictionary where the keys are the URLs and the values are the
        extracted content.
    """
    started_at = asyncio.get_running_loop().time()
    try:
        search_results = await asyncio.wait_for(
            search_links(query, 1, _source_limit(num_results), False),
            timeout=SCRAPE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning(
            "Search exceeded the %ss scrape deadline", SCRAPE_TIMEOUT_SECONDS
        )
        return {}
    urls = [result["url"] for result in search_results]
    if not urls:
        return {}

    remaining = SCRAPE_TIMEOUT_SECONDS - (
        asyncio.get_running_loop().time() - started_at
    )
    if remaining <= 0:
        return {}
    return await extract_content(urls, timeout_seconds=remaining)


async def extract_content_from_url(url: str) -> dict:
    """Extracts content from a given URL using crawlee and Playwright."""
    logging.info(f"Extracting content from URL: {url}")

    # Set the storage directory for crawlee to a temporary directory
    crawler = _create_crawler()

    @crawler.router.default_handler
    async def handler(context: PlaywrightCrawlingContext) -> None:
        # Extract the page content.
        page_content = await context.page.content()
        soup = BeautifulSoup(page_content, "html.parser")

        # Extract clean content
        for script in soup(["script", "style"]):
            script.decompose()
        content = soup.get_text()
        lines = (line.strip() for line in content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        content = "\n".join(chunk for chunk in chunks if chunk)

        # Extract metadata
        font = soup.body.get("style", "").split("font-family:")[-1].split(";")[0].strip()
        colors = [element.get("style", "").split("color:")[-1].split(";")[0].strip() for element in soup.find_all(style=lambda value: value and "color:" in value)]
        metadata = {"font": font, "colors": list(set(colors))}

        # Extract links
        internal_links = []
        external_links = []
        for a in soup.find_all("a", href=True):
            link_text = a.get_text(strip=True)
            link_url = a["href"]
            absolute_url = urljoin(url, link_url)
            if urlparse(absolute_url).netloc == urlparse(url).netloc:
                internal_links.append({"text": link_text, "url": absolute_url})
            else:
                external_links.append({"text": link_text, "url": absolute_url})

        # Push the extracted content to the dataset.
        await context.push_data({
            'content': content,
            'method': 'crawlee',
            'metadata': metadata,
            'internal_links': internal_links,
            'external_links': external_links
        })

    await _run_crawler(crawler, [url], SCRAPE_TIMEOUT_SECONDS)

    # Retrieve the extracted data.
    dataset = await crawler.get_dataset()
    data = await dataset.get_data()

    if data and data.items:
        return data.items[0]
    return {}


async def extract_content_from_links(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    semaphore = asyncio.Semaphore(SCRAPE_CONCURRENCY)

    async def enrich(result: Dict[str, Any]) -> Dict[str, Any]:
        url = result.get("url")
        if not url:
            return result
        async with semaphore:
            try:
                result.update(await extract_content_from_url(url))
            except asyncio.TimeoutError:
                logger.warning("Content extraction timed out for %s", url)
            except Exception as error:  # noqa: BLE001 - preserve other results
                logger.warning("Content extraction failed for %s: %s", url, error)
        return result

    await asyncio.gather(*(enrich(result) for result in results))
    return results


async def stream_search_content(
    query: str,
    n_queries: int,
    num_results: int,
    enhanced_search: bool,
    client_id: str,
    emit_end: bool = True,
    return_results: bool = False,
    api_key_id: str | None = None,
) -> List[Dict[str, Any]] | None:
    source_limit = _source_limit(num_results)
    started_at = asyncio.get_running_loop().time()
    await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "search", "query": query}})
    try:
        results = await asyncio.wait_for(
            search_links(
                query,
                n_queries,
                source_limit,
                enhanced_search,
                user_id=client_id,
                api_key_id=api_key_id,
            ),
            timeout=SCRAPE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        results = []
        await manager.send_to_client(
            client_id,
            {
                "type": "error",
                "content": f"Search exceeded the {SCRAPE_TIMEOUT_SECONDS:g}s deadline",
            },
        )
    urls = list(dict.fromkeys(r.get("url") for r in results if r.get("url")))[:source_limit]
    await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "urls", "count": len(urls), "urls": urls[:5]}})
    enriched: List[Dict[str, Any]] = []
    total = len(urls)
    if urls:
        crawler = _create_crawler()

        @crawler.router.default_handler
        async def handler(context: PlaywrightCrawlingContext) -> None:
            url = context.request.url
            await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "visiting", "url": url}})
            page_content = await context.page.content()
            soup = BeautifulSoup(page_content, "html.parser")
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = "\n".join(chunk for chunk in chunks if chunk)

            font = soup.body.get("style", "").split("font-family:")[-1].split(";")[0].strip() if soup.body else ""
            colors = [element.get("style", "").split("color:")[-1].split(";")[0].strip() for element in soup.find_all(style=lambda value: value and "color:" in value)]
            metadata = {"font": font, "colors": list(set(colors))}

            internal_links: List[Dict[str, str]] = []
            external_links: List[Dict[str, str]] = []
            from urllib.parse import urljoin, urlparse
            for a in soup.find_all("a", href=True):
                link_text = a.get_text(strip=True)
                link_url = a["href"]
                absolute_url = urljoin(url, link_url)
                if urlparse(absolute_url).netloc == urlparse(url).netloc:
                    internal_links.append({"text": link_text, "url": absolute_url})
                else:
                    external_links.append({"text": link_text, "url": absolute_url})

            base = next((r for r in results if r.get("url") == url), {"title": "", "url": url})
            enriched.append({
                "title": base.get("title", ""),
                "url": url,
                "content": clean_text,
                "method": "crawlee",
                "metadata": metadata,
                "internal_links": internal_links,
                "external_links": external_links,
            })
            completed = len(enriched)
            await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "progress", "completed": completed, "total": total}})
            await manager.send_to_client(client_id, {"type": "thinking", "content": {"phase": "scraped", "url": url}})

        remaining = SCRAPE_TIMEOUT_SECONDS - (
            asyncio.get_running_loop().time() - started_at
        )
        if remaining > 0:
            try:
                await _run_crawler(crawler, urls, remaining)
            except asyncio.TimeoutError:
                await manager.send_to_client(
                    client_id,
                    {
                        "type": "thinking",
                        "content": {
                            "phase": "scrape_timeout",
                            "message": f"Scraping stopped at the {SCRAPE_TIMEOUT_SECONDS:g}s deadline",
                            "completed": len(enriched),
                            "total": total,
                        },
                    },
                )
        else:
            await manager.send_to_client(
                client_id,
                {
                    "type": "thinking",
                    "content": {
                        "phase": "scrape_timeout",
                        "message": "No scrape time remained after search",
                        "completed": 0,
                        "total": total,
                    },
                },
            )

    await manager.send_to_client(client_id, {"type": "response", "content": {"results": enriched or results}})
    try:
        total_text = "\n".join([r.get("content", "") for r in (enriched or [])])
        await asyncio.to_thread(
            record_usage,
            user_id=client_id,
            api_key_id=api_key_id,
            service_used="scraper",
            content=total_text,
            provider="SCRAPER",
            model="crawler",
            input_ratio=0.8,
        )
    except Exception:
        pass
    if emit_end:
        await manager.send_to_client(client_id, {"type": "response", "content": "[END_OF_STREAM]"})
        await manager.send_to_client(client_id, "[END_OF_STREAM]")
    return (enriched or results) if return_results else None
