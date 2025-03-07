from typing import Any, Dict, List, Optional

from duckduckgo_search import DDGS
from langchain_core.language_models import BaseLLM
from loguru import logger

from ..rate_limiting import RateLimitError
from ..search_engine_base import BaseSearchEngine
from .full_search import FullSearchResults


class DuckDuckGoSearchEngine(BaseSearchEngine):
    """DuckDuckGo search engine implementation with two-phase retrieval"""

    def __init__(
        self,
        max_results: int = 10,
        region: str = "us-en",
        safe_search: bool = True,
        llm: Optional[BaseLLM] = None,
        language: str = "en",
        include_full_content: bool = False,
        max_filtered_results=5,
    ):
        """
        Initialize the DuckDuckGo search engine.

        Args:
            max_results: Maximum number of search results
            region: Region code for search results (e.g. "us-en")
            safe_search: Whether to enable safe search
            llm: Language model for relevance filtering
            language: Language for content processing
            include_full_content: Whether to include full webpage content in results
        """
        super().__init__(
            llm=llm,
            max_filtered_results=max_filtered_results,
            max_results=max_results,
        )
        self.region = region
        self.safe_search = safe_search
        self.language = language
        self.include_full_content = include_full_content
        
        # We don't need to initialize DDGS here as it's usually used as a context manager
        # or instantiated per request, but we can keep a reference if needed.
        # For thread safety, it's often better to instantiate per request.

        if include_full_content and llm:
            # We need to create a wrapper that mimics the interface expected by FullSearchResults
            # or just pass self if we implement the necessary methods.
            # For now, we'll pass self as the web_search engine, but FullSearchResults might expect
            # a langchain wrapper. Let's see if we can make it work.
            # Actually, FullSearchResults expects an object with a `results` method.
            self.full_search = FullSearchResults(
                llm=llm,
                web_search=self, # Pass self as it has the results method
                language=language,
                max_results=max_results,
                region=region,
                time="y",
                safesearch="Moderate" if safe_search else "Off",
            )

    def run(
        self, query: str, research_context: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a search using DuckDuckGo with the two-phase approach.
        """
        logger.info("---Execute a search using DuckDuckGo (Direct)---")
        return super().run(query, research_context=research_context)

    def results(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Direct results method compatible with Langchain wrapper interface.
        """
        if max_results is None:
            max_results = self.max_results
            
        try:
            with DDGS() as ddgs:
                # DDGS text search
                ddg_results = list(ddgs.text(
                    keywords=query,
                    region=self.region,
                    safesearch="moderate" if self.safe_search else "off",
                    max_results=max_results,
                ))
                return ddg_results
        except Exception as e:
            logger.error(f"DDGS search failed: {e}")
            return []

    def _get_previews(self, query: str) -> List[Dict[str, Any]]:
        """
        Get preview information (titles and snippets) for initial search results.
        """
        try:
            # Get search results from DuckDuckGo
            results = self.results(query, max_results=self.max_results)

            if not results:
                return []

            # Process results to get previews
            previews = []
            for i, result in enumerate(results):
                # DDGS returns: {'title': ..., 'href': ..., 'body': ...}
                link = result.get("href") or result.get("link")
                title = result.get("title", "")
                snippet = result.get("body") or result.get("snippet", "")
                
                preview = {
                    "id": link,
                    "title": title,
                    "snippet": snippet,
                    "link": link,
                }

                previews.append(preview)

            return previews

        except Exception as e:
            error_msg = str(e)
            logger.exception(f"Error getting DuckDuckGo previews: {error_msg}")
            
            # Re-raise rate limit errors if detected
            if "202 Ratelimit" in error_msg or "ratelimit" in error_msg.lower():
                raise RateLimitError(f"DuckDuckGo rate limit hit: {error_msg}")
            
            return []

    def _get_full_content(
        self, relevant_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Get full content for the relevant items by using FullSearchResults.
        """
        if hasattr(self, "full_search"):
            return self.full_search._get_full_content(relevant_items)
        return relevant_items
