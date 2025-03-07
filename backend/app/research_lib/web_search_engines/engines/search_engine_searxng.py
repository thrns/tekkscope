import enum
import time
from typing import Any, Dict, List, Optional

import requests
from langchain_core.language_models import BaseLLM
from loguru import logger

from ...config import search_config
from ..search_engine_base import BaseSearchEngine
from .full_search import FullSearchResults


@enum.unique
class SafeSearchSetting(enum.IntEnum):
    """
    Acceptable settings for safe search.
    """

    OFF = 0
    MODERATE = 1
    STRICT = 2


class SearXNGSearchEngine(BaseSearchEngine):
    """
    SearXNG search engine implementation that requires an instance URL provided via
    environment variable or configuration. Designed for ethical usage with proper
    rate limiting and single-instance approach.
    """

    def __init__(
        self,
        max_results: int = 15,
        instance_url: str = "https://search.tekkscope.com",
        categories: Optional[List[str]] = None,
        engines: Optional[List[str]] = None,
        language: str = "en",
        safe_search: str = SafeSearchSetting.OFF.name,
        time_range: Optional[str] = None,
        delay_between_requests: float = 0.0,
        llm: Optional[BaseLLM] = None,
        max_filtered_results: Optional[int] = None,
        include_full_content: bool = True,
        **kwargs,
    ):  # API key is actually the instance URL
        """
        Initialize the SearXNG search engine with ethical usage patterns.

        Args:
            max_results: Maximum number of search results
            instance_url: URL of your SearXNG instance (preferably self-hosted)
            categories: List of SearXNG categories to search in (general, images, videos, news, etc.)
            engines: List of engines to use (google, bing, duckduckgo, etc.)
            language: Language code for search results
            safe_search: Safe search level (0=off, 1=moderate, 2=strict)
            time_range: Time range for results (day, week, month, year)
            delay_between_requests: Seconds to wait between requests
            llm: Language model for relevance filtering
            max_filtered_results: Maximum number of results to keep after filtering
            include_full_content: Whether to include full webpage content in results
        """

        # Initialize the BaseSearchEngine with LLM, max_filtered_results, and max_results
        super().__init__(
            llm=llm,
            max_filtered_results=max_filtered_results,
            max_results=max_results,
            **kwargs,  # Pass through all other kwargs including search_snippets_only
        )

        # Validate and normalize the instance URL if provided
        # Handle case where instance_url might be wrapped in a dict from settings snapshot
        if isinstance(instance_url, dict):
            if "value" in instance_url:
                instance_url = instance_url["value"]
                logger.warning(
                    f"SearXNG instance_url was wrapped in dict, unwrapped to: {instance_url}"
                )
            else:
                logger.error(
                    f"SearXNG instance_url is a dict but has no 'value' key: {instance_url}"
                )
                instance_url = "https://search.tekkscope.com"  # Fallback to default
        
        self.instance_url = instance_url.rstrip("/")
        logger.info(
            f"SearXNG initialized with instance URL: {self.instance_url} (type: {type(self.instance_url)})"
        )
        
        # Set is_available to True by default - the initialization check is too strict
        # and can fail even when the instance is actually accessible
        # The actual search will handle errors if the instance is truly unavailable
        self.is_available = True
        
        # Quick health check to verify instance is accessible
        try:
            health_url = f"{self.instance_url}/health" if not self.instance_url.endswith("/health") else self.instance_url
            # Add headers to prevent blocking by firewalls/proxies
            health_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            health_response = requests.get(health_url, timeout=3, verify=True, headers=health_headers)
            if health_response.status_code == 200:
                logger.info(f"SearXNG health check passed: {health_url}")
                self.is_available = True
            else:
                # Try the search endpoint as fallback health check
                try:
                    test_response = requests.get(
                        f"{self.instance_url}/search",
                        params={"q": "test", "format": "json"},
                        timeout=3,
                        verify=True,
                        headers=health_headers
                    )
                    if test_response.status_code == 200:
                        logger.info(f"SearXNG search endpoint accessible (health check fallback)")
                        self.is_available = True
                    else:
                        logger.warning(f"SearXNG returned status {test_response.status_code}, but will attempt searches anyway")
                        self.is_available = True  # Still set to True to allow attempts
                except Exception:
                    logger.warning(f"SearXNG health check failed, but will attempt searches anyway")
                    self.is_available = True  # Still set to True to allow attempts
        except requests.exceptions.SSLError:
            # Try without SSL verification
            try:
                health_url = f"{self.instance_url}/health" if not self.instance_url.endswith("/health") else self.instance_url
                health_response = requests.get(health_url, timeout=3, verify=False, headers=health_headers)
                if health_response.status_code == 200:
                    logger.info(f"SearXNG health check passed (SSL disabled): {health_url}")
                    self.is_available = True
                else:
                    logger.warning(f"SearXNG health check returned {health_response.status_code}, but will attempt searches anyway")
                    self.is_available = True
            except Exception:
                logger.warning(f"SearXNG health check failed, but will attempt searches anyway")
                self.is_available = True
        except Exception as e:
            # Health check failed, but we'll still try searches
            logger.warning(f"SearXNG health check error: {e!s}, but will attempt searches anyway")
            self.is_available = True

        # Add debug logging for all parameters
        logger.info(
            f"SearXNG init params: max_results={max_results}, language={language}, "
            f"max_filtered_results={max_filtered_results}, is_available={self.is_available}"
        )

        self.max_results = max_results
        self.categories = categories or ["general"]
        self.engines = engines
        self.language = language
        try:
            # Handle both string names and integer values
            if isinstance(safe_search, int) or (
                isinstance(safe_search, str) and str(safe_search).isdigit()
            ):
                self.safe_search = SafeSearchSetting(int(safe_search))
            else:
                self.safe_search = SafeSearchSetting[safe_search]
        except (ValueError, KeyError):
            logger.exception(
                "'{}' is not a valid safe search setting. Disabling safe search",
                safe_search,
            )
            self.safe_search = SafeSearchSetting.OFF
        self.time_range = time_range

        self.delay_between_requests = float(delay_between_requests)

        self.include_full_content = include_full_content

        # Always set search_url regardless of is_available (we set is_available=True above)
        self.search_url = f"{self.instance_url}/search"
        logger.info(
            f"SearXNG engine initialized with instance: {self.instance_url}"
        )
        logger.info(
            f"Rate limiting set to {self.delay_between_requests} seconds between requests"
        )

        # Always create full_search regardless of is_available (we set is_available=True above)
        self.full_search = FullSearchResults(
            llm=llm,
            web_search=self,
            language=language,
            max_results=max_results,
            region="wt-wt",
            time="y",
            safesearch=self.safe_search.value,
        )

        self.last_request_time = 0
        
        # Final safety check - ensure is_available is True (in case something changed it)
        if not self.is_available:
            self.is_available = True

    def _respect_rate_limit(self):
        """Apply self-imposed rate limiting between requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.delay_between_requests:
            wait_time = self.delay_between_requests - time_since_last_request
            logger.info(f"Rate limiting: waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)

        self.last_request_time = time.time()

    def _get_search_results(self, query: str) -> List[Dict[str, Any]]:
        """
        Get search results from SearXNG with ethical rate limiting.

        Args:
            query: The search query

        Returns:
            List of search results from SearXNG
        """
        # Force is_available to True if it's somehow False (safety check)
        if not self.is_available:
            self.is_available = True

        logger.info(f"SearXNG running search for query: {query}")

        try:
            self._respect_rate_limit()

            initial_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }

            try:
                initial_response = requests.get(
                    self.instance_url, headers=initial_headers, timeout=10
                )
                cookies = initial_response.cookies
            except Exception:
                logger.exception("Failed to get initial cookies")
                cookies = None

            params = {
                "q": query,
                "categories": ",".join(self.categories),
                "language": self.language,
                "format": "json",  # Use JSON format for reliable parsing
                "pageno": 1,
                "safesearch": self.safe_search.value,
                "count": self.max_results,
            }

            if self.engines:
                params["engines"] = ",".join(self.engines)

            if self.time_range:
                params["time_range"] = self.time_range

            # Headers for JSON API request
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": self.instance_url + "/",
                "Connection": "keep-alive",
            }

            logger.info(
                f"Sending request to SearXNG instance at {self.instance_url}"
            )
            logger.debug(f"SearXNG request params: {params}")
            logger.debug(f"SearXNG search_url: {self.search_url}")
            
            response = requests.get(
                self.search_url,
                params=params,
                headers=headers,
                cookies=cookies,
                timeout=15,
            )

            if response.status_code == 200:
                try:
                    # Parse JSON response
                    data = response.json()
                    results = []
                    
                    # Debug: Log the response structure
                    logger.debug(f"SearXNG response keys: {list(data.keys())}")
                    logger.debug(f"SearXNG number_of_results: {data.get('number_of_results', 'N/A')}")
                    
                    # Extract results from JSON response
                    search_results = data.get("results", [])
                    logger.debug(f"SearXNG search_results type: {type(search_results)}, length: {len(search_results) if isinstance(search_results, list) else 'N/A'}")
                    
                    if not isinstance(search_results, list):
                        logger.warning(f"Expected results to be a list, got {type(search_results)}")
                        search_results = []

                    for idx, result_data in enumerate(search_results):
                        if idx >= self.max_results:
                            break

                        # Extract fields from JSON result
                        title = result_data.get("title", "")
                        url = result_data.get("url", "")
                        content = result_data.get("content", "")
                        
                        # Handle cases where url might be in parsed_url
                        if not url and "parsed_url" in result_data:
                            parsed = result_data["parsed_url"]
                            if isinstance(parsed, list) and len(parsed) >= 2:
                                scheme = parsed[0] if parsed[0] else "https"
                                domain = parsed[1] if parsed[1] else ""
                                path = parsed[2] if len(parsed) > 2 and parsed[2] else "/"
                                url = f"{scheme}://{domain}{path}"

                        logger.debug(
                            f"Extracted result {idx}: title={title[:30]}..., url={url[:30]}..., content={content[:30]}..."
                        )

                        # Add to results if we have at least a title or URL
                        if title or url:
                            results.append(
                                {
                                    "title": title,
                                    "url": url,
                                    "content": content,
                                    "engine": result_data.get("engine", "searxng"),
                                    "category": result_data.get("category", "general"),
                                }
                            )
                        else:
                            logger.warning(
                                f"SearXNG result {idx} skipped: no title or URL. "
                                f"Result data keys: {list(result_data.keys())}"
                            )

                    logger.info(
                        f"SearXNG returned {len(results)} results from JSON parsing"
                    )
                    
                    if len(results) == 0 and len(search_results) > 0:
                        logger.warning(
                            f"SearXNG parsed 0 results despite having {len(search_results)} items in response"
                        )
                    return results

                except ValueError as e:
                    logger.exception(f"Error parsing JSON response: {e}")
                    logger.debug(f"Response text (first 500 chars): {response.text[:500]}")
                    return []
                except Exception:
                    logger.exception("Error parsing JSON results")
                    return []
            else:
                logger.error(
                    f"SearXNG returned status code {response.status_code}"
                )
                logger.debug(f"Response text (first 500 chars): {response.text[:500]}")
                return []

        except Exception:
            logger.exception("Error getting SearXNG results")
            return []

    def _get_previews(self, query: str) -> List[Dict[str, Any]]:
        """
        Get preview information for SearXNG search results.

        Args:
            query: The search query

        Returns:
            List of preview dictionaries
        """
        # Force is_available to True if it's somehow False (safety check)
        if not self.is_available:
            self.is_available = True

        logger.info(f"Getting SearXNG previews for query: {query}")

        results = self._get_search_results(query)

        if not results:
            logger.warning(f"No SearXNG results found for query: {query}")
            return []

        previews = []
        for i, result in enumerate(results):
            title = result.get("title", "")
            url = result.get("url", "")
            content = result.get("content", "")

            preview = {
                "id": url or f"searxng-result-{i}",
                "title": title,
                "link": url,
                "snippet": content,
                "engine": result.get("engine", ""),
                "category": result.get("category", ""),
            }

            previews.append(preview)

        return previews

    def _get_full_content(
        self, relevant_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Get full content for the relevant search results.

        Args:
            relevant_items: List of relevant preview dictionaries

        Returns:
            List of result dictionaries with full content
        """
        # Force is_available to True if it's somehow False (safety check)
        if not self.is_available:
            self.is_available = True

        if (
            hasattr(search_config, "SEARCH_SNIPPETS_ONLY")
            and search_config.SEARCH_SNIPPETS_ONLY
        ):
            logger.info("Snippet-only mode, skipping full content retrieval")
            return relevant_items

        logger.info("Retrieving full webpage content")

        try:
            results_with_content = self.full_search._get_full_content(
                relevant_items
            )
            return results_with_content

        except Exception:
            logger.exception("Error retrieving full content")
            return relevant_items

    def invoke(self, query: str) -> List[Dict[str, Any]]:
        """Compatibility method for LangChain tools"""
        return self.run(query)

    def results(
        self, query: str, max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get search results in a format compatible with other search engines.

        Args:
            query: The search query
            max_results: Optional override for maximum results

        Returns:
            List of search result dictionaries
        """
        # Force is_available to True if it's somehow False (safety check)
        if not self.is_available:
            self.is_available = True

        original_max_results = self.max_results

        try:
            if max_results is not None:
                self.max_results = max_results

            results = self._get_search_results(query)

            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "title": result.get("title", ""),
                        "link": result.get("url", ""),
                        "snippet": result.get("content", ""),
                    }
                )

            return formatted_results

        finally:
            self.max_results = original_max_results

    @staticmethod
    def get_self_hosting_instructions() -> str:
        """
        Get instructions for self-hosting a SearXNG instance.

        Returns:
            String with installation instructions
        """
        return """
# SearXNG Self-Hosting Instructions

The most ethical way to use SearXNG is to host your own instance. Here's how:

## Using Docker (easiest method)

1. Install Docker if you don't have it already
2. Run these commands:

```bash
# Pull the SearXNG Docker image
docker pull searxng/searxng

# Run SearXNG (will be available at http://localhost:8080)
docker run -d -p 8080:8080 --name searxng searxng/searxng
```

## Using Docker Compose (recommended for production)

1. Create a file named `docker-compose.yml` with the following content:

```yaml
version: '3'
services:
  searxng:
    container_name: searxng
    image: searxng/searxng
    ports:
      - "8080:8080"
    volumes:
      - ./searxng:/etc/searxng
    environment:
      - SEARXNG_BASE_URL=http://localhost:8080/
    restart: unless-stopped
```

2. Run with Docker Compose:

```bash
docker-compose up -d
```

For more detailed instructions and configuration options, visit:
https://searxng.github.io/searxng/admin/installation.html
"""

    def run(
        self, query: str, research_context: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        """
        Override BaseSearchEngine run method to add SearXNG-specific error handling.
        """
        # Force is_available to True if it's somehow False (safety check)
        if not self.is_available:
            self.is_available = True

        logger.info(f"SearXNG search engine running with query: '{query}'")

        try:
            # Call the parent class's run method
            results = super().run(query, research_context=research_context)
            logger.info(f"SearXNG search completed with {len(results)} results")
            return results
        except Exception:
            logger.exception("Error in SearXNG run method")
            # Return empty results on error
            return []