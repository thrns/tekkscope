from typing import Any, Dict, List, Optional
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from loguru import logger

from ...config.search_config import get_setting_from_snapshot
from ...web.services.socket_service import SocketIOService
from ..search_engine_base import BaseSearchEngine
from ..search_engine_factory import create_search_engine
from .search_engine_searxng import SearXNGSearchEngine


class MetaSearchEngine(BaseSearchEngine):
    """
    LLM-powered meta search engine that intelligently selects and uses
    the appropriate search engines based on query analysis
    """

    def __init__(
        self,
        llm,
        max_results: int = 10,
        use_api_key_services: bool = True,
        max_engines_to_try: int = 3,
        max_filtered_results: Optional[int] = None,
        engine_selection_callback=None,
        settings_snapshot: Optional[Dict[str, Any]] = None,
        programmatic_mode: bool = False,
        use_parallel_search: bool = True,
        max_parallel_engines: int = 3,
        parallel_search_threshold: int = 2,
        enable_news_detection: bool = True,
        enable_entity_detection: bool = True,
        **kwargs,
    ):
        """
        Initialize the meta search engine.

        Args:
            llm: Language model instance for query classification and relevance filtering
            max_results: Maximum number of search results to return
            use_api_key_services: Whether to include services that require API keys
            max_engines_to_try: Maximum number of engines to try before giving up
            max_filtered_results: Maximum number of results to keep after filtering
            settings_snapshot: Settings snapshot for thread context
            programmatic_mode: If True, disables database operations and metrics tracking
            use_parallel_search: Whether to use parallel execution when beneficial
            max_parallel_engines: Maximum number of engines to execute in parallel
            parallel_search_threshold: Minimum number of engines needed to use parallel mode
            enable_news_detection: Whether to detect and prioritize news queries
            enable_entity_detection: Whether to detect and prioritize entity queries
            **kwargs: Additional parameters (ignored but accepted for compatibility)
        """
        # Initialize the BaseSearchEngine with the LLM, max_filtered_results, and max_results
        super().__init__(
            llm=llm,
            max_filtered_results=max_filtered_results,
            max_results=max_results,
            settings_snapshot=settings_snapshot,
            programmatic_mode=programmatic_mode,
        )

        self.use_api_key_services = use_api_key_services
        self.max_engines_to_try = max_engines_to_try
        self.settings_snapshot = settings_snapshot
        self.use_parallel_search = use_parallel_search
        self.max_parallel_engines = max_parallel_engines
        self.parallel_search_threshold = parallel_search_threshold
        self.enable_news_detection = enable_news_detection
        self.enable_entity_detection = enable_entity_detection

        # Read parallel search preferences from settings if available
        if settings_snapshot:
            self.use_parallel_search = get_setting_from_snapshot(
                "search.engine.meta.use_parallel_search",
                self.use_parallel_search,
                settings_snapshot=settings_snapshot,
            )
            self.max_parallel_engines = int(get_setting_from_snapshot(
                "search.engine.meta.max_parallel_engines",
                self.max_parallel_engines,
                settings_snapshot=settings_snapshot,
            ))

        # Cache for engine instances
        self.engine_cache = {}
        
        # Track engines used in parallel searches
        self._parallel_engines_used = {}
        self._result_engine_mapping = {}  # Maps result URLs to their source engines

        # Get available engines (excluding 'meta' and 'auto')
        self.available_engines = self._get_available_engines()
        logger.info(
            f"Meta Search Engine initialized with {len(self.available_engines)} available engines: {', '.join(self.available_engines)}"
        )
        logger.info(
            f"Parallel search: {'enabled' if self.use_parallel_search else 'disabled'}, "
            f"max parallel engines: {self.max_parallel_engines}, threshold: {self.parallel_search_threshold}"
        )

        # Create a fallback engine in case everything else fails
        # Use SearXNG as the fallback engine instead of Wikipedia
        self.fallback_engine = SearXNGSearchEngine(
            max_results=self.max_results,
            llm=llm,
            max_filtered_results=max_filtered_results,
        )

    def _get_search_config(self) -> Dict[str, Any]:
        """Get search config from settings_snapshot or fallback to self._get_search_config()"""
        if self.settings_snapshot:
            # Extract search engine configs from settings snapshot
            config_data = {}
            for key, value in self.settings_snapshot.items():
                if key.startswith("search.engine.web."):
                    parts = key.split(".")
                    if len(parts) >= 4:
                        engine_name = parts[3]
                        if engine_name not in config_data:
                            config_data[engine_name] = {}
                        remaining_key = (
                            ".".join(parts[4:]) if len(parts) > 4 else ""
                        )
                        if remaining_key:
                            config_data[engine_name][remaining_key] = (
                                value.get("value")
                                if isinstance(value, dict)
                                else value
                            )

            # Also check for auto engine
            if "search.engine.auto.class_name" in self.settings_snapshot:
                config_data["auto"] = {}
                for key, value in self.settings_snapshot.items():
                    if key.startswith("search.engine.auto."):
                        remaining_key = key.replace("search.engine.auto.", "")
                        config_data["auto"][remaining_key] = (
                            value.get("value")
                            if isinstance(value, dict)
                            else value
                        )
            return config_data
        else:
            # Fallback to search_config if no snapshot
            return self._get_search_config()

    def _get_available_engines(self) -> List[str]:
        """
        Get list of available engines, excluding 'meta' and 'auto', based on user settings.
        Enhanced with better logging and error handling.
        
        Returns:
            List of available engine names
        """
        # Filter out 'meta' and 'auto' and check API key availability
        available = []
        skipped_reasons = {}

        # Get search config using helper method
        config_data = self._get_search_config()

        for name, config_ in config_data.items():
            if name in ["meta", "auto"]:
                continue

            # Determine if this is a local engine (starts with "local.")
            is_local_engine = name.startswith("local.")

            # Determine the appropriate setting path based on engine type
            if is_local_engine:
                # Format: search.engine.local.{engine_name}.use_in_auto_search
                local_name = name.replace("local.", "")
                auto_search_setting = (
                    f"search.engine.local.{local_name}.use_in_auto_search"
                )
            else:
                # Format: search.engine.web.{engine_name}.use_in_auto_search
                auto_search_setting = (
                    f"search.engine.web.{name}.use_in_auto_search"
                )

            # Get setting from database, default to False if not found
            use_in_auto_search = get_setting_from_snapshot(
                auto_search_setting,
                False,
                settings_snapshot=self.settings_snapshot,
            )

            # Skip engines that aren't enabled for auto search
            if not use_in_auto_search:
                skipped_reasons[name] = "not enabled for auto search"
                logger.debug(
                    f"Skipping {name} engine because it's not enabled for auto search"
                )
                continue

            # Skip engines that require API keys if we don't want to use them
            if (
                config_.get("requires_api_key", False)
                and not self.use_api_key_services
            ):
                skipped_reasons[name] = "API key services disabled"
                logger.debug(
                    f"Skipping {name} engine because API key services are disabled"
                )
                continue

            # Skip engines that require API keys if the key is not available
            if config_.get("requires_api_key", False):
                api_key = config_.get("api_key")
                if not api_key:
                    skipped_reasons[name] = "API key not available"
                    logger.debug(
                        f"Skipping {name} engine because API key is not available"
                    )
                    continue

            available.append(name)
            logger.debug(
                f"Engine {name} is available (reliability: {config_.get('reliability', 0.5):.2f}, "
                f"requires_api_key: {config_.get('requires_api_key', False)})"
            )

        # Log summary
        logger.info(
            f"Available engines: {len(available)} ({', '.join(available)})"
        )
        if skipped_reasons:
            logger.debug(
                f"Skipped engines: {len(skipped_reasons)} "
                f"({', '.join(f'{k}: {v}' for k, v in skipped_reasons.items())})"
            )

        # If no engines are available, raise an error instead of falling back silently
        if not available:
            error_msg = "No search engines enabled for auto search. Please enable at least one engine in settings."
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        return available

    def _detect_query_type(self, query: str) -> str:
        """
        Detect the primary query type to help with engine selection.
        
        Args:
            query: The search query
            
        Returns:
            Query type string: "news", "entity", "academic", "code", "medical", "historical", or "general"
        """
        if not query:
            return "general"
            
        query_lower = query.lower()
        
        # News detection
        if self.enable_news_detection:
            news_keywords = [
                "breaking news", "today", "latest", "current events", 
                "recent", "just happened", "this week", "this month",
                "breaking", "news", "headlines", "developments"
            ]
            if any(kw in query_lower for kw in news_keywords):
                logger.info("Query type detected: news")
                return "news"
        
        # Entity detection
        if self.enable_entity_detection:
            entity_patterns = [
                "who is", "what is", "identify", "name of", 
                "who was", "what was", "who are", "what are"
            ]
            if any(pattern in query_lower for pattern in entity_patterns):
                logger.info("Query type detected: entity")
                return "entity"
        
        # Academic detection
        academic_keywords = [
            "research", "paper", "study", "academic", "published",
            "journal", "publication", "scholarly", "peer-reviewed"
        ]
        if any(kw in query_lower for kw in academic_keywords):
            logger.info("Query type detected: academic")
            return "academic"
        
        # Code detection
        code_keywords = [
            "github", "repository", "code", "programming", "software",
            "library", "package", "module", "function", "api"
        ]
        if any(kw in query_lower for kw in code_keywords):
            logger.info("Query type detected: code")
            return "code"
        
        # Medical detection
        medical_keywords = [
            "medical", "clinical", "disease", "treatment", "diagnosis",
            "patient", "symptom", "medicine", "drug", "therapy"
        ]
        if any(kw in query_lower for kw in medical_keywords):
            logger.info("Query type detected: medical")
            return "medical"
        
        # Historical detection
        historical_keywords = [
            "history", "historical", "past", "ancient", "century",
            "decade", "era", "period"
        ]
        # Also check for date patterns
        import re
        date_pattern = r'\b(19|20)\d{2}\b|\b(january|february|march|april|may|june|july|august|september|october|november|december)\b'
        if any(kw in query_lower for kw in historical_keywords) or re.search(date_pattern, query_lower):
            logger.info("Query type detected: historical")
            return "historical"
        
        logger.info("Query type detected: general")
        return "general"

    def analyze_query(self, query: str) -> List[str]:
        """
        Analyze the query to determine the best search engines to use.
        Prioritizes SearXNG for general queries, but selects specialized engines
        for domain-specific queries (e.g., scientific papers, code).

        Args:
            query: The search query

        Returns:
            List of search engine names sorted by suitability
        """
        try:
            # Detect query type first
            query_type = self._detect_query_type(query)
            
            # First check if this is a specialized query that should use specific engines
            # First check if this is a specialized query that should use specific engines
            specialized_domains = {
                "scientific paper": ["searxng", "arxiv", "pubmed"],
                "medical research": ["searxng", "pubmed"],
                "clinical": ["searxng", "pubmed"],
                "github": ["searxng", "github"],
                "repository": ["searxng", "github"],
                "code": ["searxng", "github"],
                "programming": ["searxng", "github"],
                "news": ["searxng", "guardian"],
                "breaking news": ["searxng", "guardian"],
                "current events": ["searxng", "guardian"],
                "entity": ["searxng", "openalex", "wikipedia"],
                "who is": ["searxng", "openalex", "wikipedia"],
                "what is": ["searxng", "openalex", "wikipedia"],
            }

            # Quick heuristic check for specialized queries
            query_lower = query.lower()
            for term, engines in specialized_domains.items():
                if term in query_lower:
                    valid_engines = []
                    for engine in engines:
                        if engine in self.available_engines:
                            valid_engines.append(engine)

                    if valid_engines:
                        logger.info(
                            f"Detected specialized query type: {term}, using engines: {valid_engines}"
                        )
                        return valid_engines
            
            # Use query type detection for news and entity queries
            if query_type == "news":
                engines = ["searxng", "guardian"]
                valid_engines = [e for e in engines if e in self.available_engines]
                if valid_engines:
                    logger.info(f"News query detected, using engines: {valid_engines}")
                    return valid_engines
            
            if query_type == "entity":
                engines = ["searxng", "openalex", "wikipedia"]
                valid_engines = [e for e in engines if e in self.available_engines]
                if valid_engines:
                    logger.info(f"Entity query detected, using engines: {valid_engines}")
                    return valid_engines

            # For searches containing "arxiv", prioritize the arxiv engine
            if "arxiv" in query_lower and "arxiv" in self.available_engines:
                return ["arxiv"] + [
                    e for e in self.available_engines if e != "arxiv"
                ]

            # For searches containing "pubmed", prioritize the pubmed engine
            if "pubmed" in query_lower and "pubmed" in self.available_engines:
                return ["pubmed"] + [
                    e for e in self.available_engines if e != "pubmed"
                ]

            # Check if SearXNG is available and prioritize it for general queries
            if "searxng" in self.available_engines:
                # For general queries, return SearXNG first followed by reliability-ordered engines
                engines_without_searxng = [
                    e for e in self.available_engines if e != "searxng"
                ]
                reliability_sorted = sorted(
                    engines_without_searxng,
                    key=lambda x: self._get_search_config()
                    .get(x, {})
                    .get("reliability", 0),
                    reverse=True,
                )
                return ["searxng"] + reliability_sorted

            # If LLM is not available or SearXNG is not available, fall back to reliability
            if not self.llm or "searxng" not in self.available_engines:
                logger.warning(
                    "No LLM available or SearXNG not available, using reliability-based engines"
                )
                # Return engines sorted by reliability
                return sorted(
                    self.available_engines,
                    key=lambda x: self._get_search_config()
                    .get(x, {})
                    .get("reliability", 0),
                    reverse=True,
                )

            # Create a prompt that outlines the available search engines and their strengths
            engines_info = []
            config_data = self._get_search_config()
            for engine_name in self.available_engines:
                try:
                    engine_config = config_data.get(engine_name, {})
                    strengths = engine_config.get("strengths", "General search")
                    weaknesses = engine_config.get("weaknesses", "None specified")
                    description = engine_config.get("description", engine_name)
                    reliability = engine_config.get("reliability", 0.5)
                    requires_api_key = engine_config.get("requires_api_key", False)
                    
                    # Add specific descriptions for known engines
                    if engine_name == "guardian":
                        description = "The Guardian news API - News articles, current events, breaking news"
                        strengths = "News articles, current events, breaking news, recent developments"
                    elif engine_name == "openalex":
                        description = "OpenAlex academic database - Academic papers, entity data, research publications"
                        strengths = "Academic papers, entity data, research publications, scholarly information"
                    
                    info_parts = [
                        f"- {engine_name}: {description}",
                        f"  Strengths: {strengths}",
                        f"  Weaknesses: {weaknesses}",
                        f"  Reliability: {reliability:.2f}",
                    ]
                    if requires_api_key:
                        info_parts.append("  Requires API key: Yes")
                    
                    engines_info.append("\n".join(info_parts))
                except KeyError:
                    logger.exception(f"Missing key for engine {engine_name}")

            # Only proceed if we have engines available to choose from
            if not engines_info:
                logger.warning(
                    "No engine information available for prompt, using reliability-based sorting instead"
                )
                return sorted(
                    self.available_engines,
                    key=lambda x: self._get_search_config()
                    .get(x, {})
                    .get("reliability", 0),
                    reverse=True,
                )

            # Use a stronger prompt that emphasizes appropriate engine selection
            prompt = f"""You are a search query analyst. Consider this search query:

QUERY: {query}
QUERY TYPE: {query_type}

I have these search engines available:
{chr(10).join(engines_info)}

Determine which search engines would be most appropriate for answering this query.
First analyze the nature of the query: Is it factual, scientific, code-related, medical, news, entity-related, etc.?

IMPORTANT GUIDELINES:
- For NEWS queries (breaking news, current events, today's news), use SearXNG and Guardian (if available)
- For ENTITY queries (who is, what is, identify), use SearXNG, OpenAlex, and Wikipedia
- For ACADEMIC/SCIENTIFIC searches, use SearXNG, arXiv, and PubMed
- For MEDICAL research, use SearXNG and PubMed
- For CODE repositories and programming, use SearXNG and GitHub
- For GENERAL queries, ALWAYS use SearXNG as the primary engine
- Consider using multiple engines in parallel for comprehensive coverage when appropriate

Output ONLY a comma-separated list of 1-3 search engine names in order of most appropriate to least appropriate.
Example output: searxng,guardian or searxng,openalex,wikipedia"""

            # Get analysis from LLM
            response = self.llm.invoke(prompt)

            # Handle different response formats
            if hasattr(response, "content"):
                content = response.content.strip()
            else:
                content = str(response).strip()

            # Extract engine names
            valid_engines = []
            for engine_name in content.split(","):
                cleaned_name = engine_name.strip().lower()
                if cleaned_name in self.available_engines:
                    valid_engines.append(cleaned_name)

            # If SearXNG is available but not selected by the LLM, add it as a fallback
            if (
                "searxng" in self.available_engines
                and "searxng" not in valid_engines
            ):
                # Add it as the last option if the LLM selected others
                if valid_engines:
                    valid_engines.append("searxng")
                # Use it as the first option if no valid engines were selected
                else:
                    valid_engines = ["searxng"]

            # If still no valid engines, use reliability-based ordering
            if not valid_engines:
                valid_engines = sorted(
                    self.available_engines,
                    key=lambda x: self._get_search_config()
                    .get(x, {})
                    .get("reliability", 0),
                    reverse=True,
                )

            return valid_engines
        except Exception:
            logger.exception("Error analyzing query with LLM")
            # Fall back to SearXNG if available, then reliability-based ordering
            if "searxng" in self.available_engines:
                return ["searxng"] + sorted(
                    [e for e in self.available_engines if e != "searxng"],
                    key=lambda x: self._get_search_config()
                    .get(x, {})
                    .get("reliability", 0),
                    reverse=True,
                )
            else:
                return sorted(
                    self.available_engines,
                    key=lambda x: self._get_search_config()
                    .get(x, {})
                    .get("reliability", 0),
                    reverse=True,
                )

    def _merge_results(
        self, 
        all_results: List[Dict[str, Any]], 
        engine_results: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Merge and deduplicate results from multiple engines.
        
        Args:
            all_results: List of all results from all engines
            engine_results: Dictionary mapping engine names to their results
            
        Returns:
            Merged and deduplicated list of results, sorted by relevance score
        """
        if not all_results:
            return []
        
        # Normalize URLs for deduplication (case-insensitive, remove trailing slashes)
        def normalize_url(url: str) -> str:
            if not url:
                return ""
            url = url.lower().rstrip("/")
            # Remove common URL parameters that don't affect content
            if "?" in url:
                url = url.split("?")[0]
            return url
        
        # Track results by normalized URL
        url_to_result = {}
        url_to_engines = {}  # Track which engines found each URL
        url_to_positions = {}  # Track position in each engine's results
        
        config_data = self._get_search_config()
        
        # Process results from each engine
        for engine_name, results in engine_results.items():
            engine_reliability = config_data.get(engine_name, {}).get("reliability", 0.5)
            
            for position, result in enumerate(results):
                url = result.get("url", "")
                if not url:
                    continue
                
                normalized_url = normalize_url(url)
                
                # Track which engines found this URL
                if normalized_url not in url_to_engines:
                    url_to_engines[normalized_url] = []
                url_to_engines[normalized_url].append(engine_name)
                
                # Track position in each engine
                if normalized_url not in url_to_positions:
                    url_to_positions[normalized_url] = {}
                url_to_positions[normalized_url][engine_name] = position
                
                # If we haven't seen this URL before, store the result
                if normalized_url not in url_to_result:
                    url_to_result[normalized_url] = result.copy()
                    # Initialize metadata
                    url_to_result[normalized_url]["_meta"] = {
                        "source_engines": [engine_name],
                        "engine_count": 1,
                        "best_position": position,
                        "best_reliability": engine_reliability,
                    }
                else:
                    # Merge metadata from multiple engines
                    existing = url_to_result[normalized_url]
                    existing["_meta"]["source_engines"].append(engine_name)
                    existing["_meta"]["engine_count"] += 1
                    
                    # Update best position (lower is better)
                    if position < existing["_meta"]["best_position"]:
                        existing["_meta"]["best_position"] = position
                    
                    # Update best reliability
                    if engine_reliability > existing["_meta"]["best_reliability"]:
                        existing["_meta"]["best_reliability"] = engine_reliability
                    
                    # Combine snippets if available
                    if "snippet" in result and result["snippet"]:
                        existing_snippet = existing.get("snippet", "")
                        if existing_snippet and result["snippet"] not in existing_snippet:
                            existing["snippet"] = f"{existing_snippet} ... {result['snippet']}"
                        elif not existing_snippet:
                            existing["snippet"] = result["snippet"]
        
        # Calculate relevance scores and sort
        merged_results = list(url_to_result.values())
        
        for result in merged_results:
            meta = result.get("_meta", {})
            engine_count = meta.get("engine_count", 1)
            best_position = meta.get("best_position", 0)
            best_reliability = meta.get("best_reliability", 0.5)
            
            # Score calculation:
            # - Higher score for results found by multiple engines (diversity bonus)
            # - Higher score for better positions (lower position number = higher score)
            # - Higher score for more reliable engines
            # - Normalize position score (0-1 scale, assuming max 50 results)
            position_score = max(0, 1 - (best_position / 50))
            reliability_score = best_reliability
            diversity_bonus = min(0.3, (engine_count - 1) * 0.1)  # Bonus for multiple engines
            
            relevance_score = (position_score * 0.4) + (reliability_score * 0.4) + (diversity_bonus * 0.2)
            result["_relevance_score"] = relevance_score
        
        # Sort by relevance score (descending)
        merged_results.sort(key=lambda x: x.get("_relevance_score", 0), reverse=True)
        
        # Limit to max_results
        merged_results = merged_results[:self.max_results]
        
        logger.info(
            f"Merged {len(all_results)} results from {len(engine_results)} engines "
            f"into {len(merged_results)} unique results"
        )
        
        return merged_results

    def _get_previews_parallel(
        self, query: str, engine_names: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Execute searches in parallel across multiple engines.
        
        Args:
            query: The search query
            engine_names: List of engine names to use in parallel
            
        Returns:
            Merged and deduplicated list of results
        """
        if not engine_names:
            return []
        
        # Limit to max_parallel_engines
        engines_to_use = engine_names[:self.max_parallel_engines]
        logger.info(
            f"⚡ PARALLEL_SEARCH: Executing parallel search across {len(engines_to_use)} engines: {', '.join(engines_to_use)}"
        )
        
        start_time = time.time()
        all_results = []
        engine_results = {}
        engine_timings = {}
        
        def search_with_engine(engine_name: str) -> tuple:
            """Search function for parallel execution."""
            engine_start = time.time()
            try:
                engine = self._get_engine_instance(engine_name)
                if engine:
                    results = engine._get_previews(query)
                    engine_time = time.time() - engine_start
                    engine_timings[engine_name] = engine_time
                    logger.info(
                        f"✅ PARALLEL_SEARCH: {engine_name} completed in {engine_time:.2f}s with {len(results or [])} results"
                    )
                    return (engine_name, results or [], None)
                else:
                    return (engine_name, [], f"Failed to initialize {engine_name}")
            except Exception as e:
                engine_time = time.time() - engine_start
                engine_timings[engine_name] = engine_time
                logger.exception(f"Error in parallel search with {engine_name}")
                return (engine_name, [], str(e))
        
        # Execute searches in parallel
        with ThreadPoolExecutor(max_workers=len(engines_to_use)) as executor:
            futures = {
                executor.submit(search_with_engine, name): name 
                for name in engines_to_use
            }
            
            for future in as_completed(futures):
                engine_name, results, error = future.result()
                if error:
                    logger.warning(f"PARALLEL_SEARCH: {engine_name} failed: {error}")
                else:
                    engine_results[engine_name] = results
                    all_results.extend(results)
                    # Track which engine provided results
                    self._parallel_engines_used[engine_name] = len(results)
        
        # Merge and deduplicate results
        merged = self._merge_results(all_results, engine_results)
        
        total_time = time.time() - start_time
        logger.info(
            f"✅ PARALLEL_SEARCH: Completed in {total_time:.2f}s total. "
            f"Engines used: {list(engine_results.keys())} | Timings: {engine_timings} | Total results: {len(merged)}"
        )
        
        # Store result mapping for full content retrieval
        for result in merged:
            url = result.get("url", "")
            if url:
                meta = result.get("_meta", {})
                source_engines = meta.get("source_engines", [])
                if source_engines:
                    # Use the most reliable engine that found this result
                    config_data = self._get_search_config()
                    best_engine = max(
                        source_engines,
                        key=lambda e: config_data.get(e, {}).get("reliability", 0.5)
                    )
                    self._result_engine_mapping[url] = best_engine
        
        return merged

    def _should_use_parallel(
        self, query: str, ranked_engines: List[str], query_type: str
    ) -> bool:
        """
        Determine if parallel execution would be beneficial for this query.
        
        Args:
            query: The search query
            ranked_engines: List of ranked engine names
            query_type: Detected query type
            
        Returns:
            True if parallel execution should be used
        """
        if not self.use_parallel_search:
            return False
        
        if len(ranked_engines) < self.parallel_search_threshold:
            return False
        
        # Use parallel for queries that benefit from multiple perspectives
        parallel_beneficial_types = ["news", "general", "entity"]
        if query_type in parallel_beneficial_types:
            return True
        
        # Use parallel if multiple specialized engines are available
        if len(ranked_engines) >= 2:
            # Check if we have diverse engine types
            config_data = self._get_search_config()
            engine_types = set()
            for engine_name in ranked_engines[:3]:
                desc = config_data.get(engine_name, {}).get("description", "").lower()
                if "news" in desc or engine_name == "guardian":
                    engine_types.add("news")
                elif "academic" in desc or engine_name in ["arxiv", "pubmed", "openalex"]:
                    engine_types.add("academic")
                elif "code" in desc or engine_name == "github":
                    engine_types.add("code")
                else:
                    engine_types.add("general")
            
            # If we have diverse engine types, parallel is beneficial
            if len(engine_types) > 1:
                return True
        
        return False

    def _get_previews(self, query: str) -> List[Dict[str, Any]]:
        """
        Get preview information by selecting the best search engine(s) for this query.
        Can use parallel execution when beneficial.
        Logs which engines are selected and used.

        Args:
            query: The search query

        Returns:
            List of preview dictionaries
        """
        # Get ranked list of engines for this query
        ranked_engines = self.analyze_query(query)
        
        # Log engine selection at the start
        logger.info(f"🔍 SEARCH_ENGINE_SELECTION: Query='{query[:100]}...' | Ranked engines: {ranked_engines[:self.max_engines_to_try]}")

        if not ranked_engines:
            logger.warning(
                "No suitable search engines found for query, using fallback engine"
            )
            return self.fallback_engine._get_previews(query)

        # Detect query type for parallel decision
        query_type = self._detect_query_type(query)
        
        # Determine if parallel execution should be used
        use_parallel = self._should_use_parallel(query, ranked_engines, query_type)
        
        if use_parallel:
            # Use parallel execution
            engines_to_use = ranked_engines[:self.max_parallel_engines]
            logger.info(
                f"⚡ PARALLEL_SEARCH: Using parallel execution with {len(engines_to_use)} engines: {', '.join(engines_to_use)}"
            )
            
            try:
                results = self._get_previews_parallel(query, engines_to_use)
                
                if results and len(results) > 0:
                    logger.info(
                        f"PARALLEL_SEARCH: Successfully got {len(results)} merged results"
                    )
                    
                    # Store parallel engines info
                    self._selected_engines = engines_to_use
                    self._selected_engine_names = engines_to_use
                    
                    # Emit socket event for parallel search
                    if not self.programmatic_mode:
                        try:
                            SocketIOService().emit_socket_event(
                                "search_engine_selected",
                                {
                                    "engines": engines_to_use,
                                    "result_count": len(results),
                                    "mode": "parallel",
                                },
                            )
                        except (ValueError, Exception) as e:
                            logger.debug(f"Socket emit skipped: {e}")
                    
                    return results
                else:
                    logger.warning("Parallel search returned no results, falling back to sequential")
            except Exception as e:
                logger.exception(f"Parallel search failed: {e}, falling back to sequential")
                use_parallel = False
        
        # Use sequential execution (original logic)
        if not use_parallel:
            # Limit the number of engines to try
            engines_to_try = ranked_engines[: self.max_engines_to_try]
            logger.info(
                f"🔄 SEQUENTIAL_SEARCH: Will try engines in order: {', '.join(engines_to_try)}"
            )

            all_errors = []
            # Try each engine in order
            for engine_name in engines_to_try:
                logger.info(f"🔎 Trying search engine: {engine_name}")

                # Get or create the engine instance
                engine = self._get_engine_instance(engine_name)

                if not engine:
                    logger.warning(f"Failed to initialize {engine_name}, skipping")
                    all_errors.append(f"Failed to initialize {engine_name}")
                    continue

                try:
                    # Get previews from this engine
                    logger.info(f"🔎 Trying search engine: {engine_name}")
                    previews = engine._get_previews(query)

                    # If search was successful, return results
                    if previews and len(previews) > 0:
                        logger.info(f"✅ ENGINE_SELECTED: {engine_name} | Results: {len(previews)}")
                        logger.info(
                            f"Successfully got {len(previews)} preview results from {engine_name}"
                        )
                        # Store selected engine for later use
                        self._selected_engine = engine
                        self._selected_engine_name = engine_name

                        # Emit a socket event to inform about the selected engine
                        # Only emit if we're in a Flask context (not FastAPI/programmatic mode)
                        if not self.programmatic_mode:
                            try:
                                SocketIOService().emit_socket_event(
                                    "search_engine_selected",
                                    {
                                        "engine": engine_name,
                                        "result_count": len(previews),
                                        "mode": "sequential",
                                    },
                                )
                            except (ValueError, Exception) as e:
                                # Socket service not available (e.g., running in FastAPI context)
                                logger.debug(f"Socket emit skipped: {e}")

                        return previews

                    logger.info(f"{engine_name} returned no previews")
                    all_errors.append(f"{engine_name} returned no previews")

                except Exception as e:
                    error_msg = f"Error getting previews from {engine_name}: {e!s}"
                    logger.exception(error_msg)
                    all_errors.append(error_msg)

            # If we reach here, all engines failed, use fallback
            logger.warning(
                f"All engines failed or returned no preview results: {', '.join(all_errors)}"
            )
            logger.info("Using fallback Wikipedia engine for previews")
            self._selected_engine = self.fallback_engine
            self._selected_engine_name = "wikipedia"
            return self.fallback_engine._get_previews(query)

    def _get_full_content(
        self, relevant_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Get full content using the engine(s) that provided the previews.
        Handles both single engine (sequential) and multiple engines (parallel) scenarios.

        Args:
            relevant_items: List of relevant preview dictionaries

        Returns:
            List of result dictionaries with full content
        """
        # Check if we should get full content
        if get_setting_from_snapshot(
            "search.snippets_only",
            True,
            settings_snapshot=self.settings_snapshot,
        ):
            logger.info("Snippet-only mode, skipping full content retrieval")
            return relevant_items

        logger.info("Getting full content for relevant items")

        # Check if we used parallel search
        if hasattr(self, "_selected_engines") and self._selected_engines:
            # Parallel search was used - get full content from appropriate engines
            logger.info(
                f"Getting full content from parallel engines: {', '.join(self._selected_engines)}"
            )
            
            # Group items by their source engine
            items_by_engine = {}
            items_without_engine = []
            
            for item in relevant_items:
                url = item.get("url", "")
                # Check if we have engine mapping from parallel search
                if url in self._result_engine_mapping:
                    engine_name = self._result_engine_mapping[url]
                    if engine_name not in items_by_engine:
                        items_by_engine[engine_name] = []
                    items_by_engine[engine_name].append(item)
                else:
                    # Try to get from metadata
                    meta = item.get("_meta", {})
                    source_engines = meta.get("source_engines", [])
                    if source_engines:
                        # Use the most reliable engine
                        config_data = self._get_search_config()
                        best_engine = max(
                            source_engines,
                            key=lambda e: config_data.get(e, {}).get("reliability", 0.5)
                        )
                        if best_engine not in items_by_engine:
                            items_by_engine[best_engine] = []
                        items_by_engine[best_engine].append(item)
                    else:
                        items_without_engine.append(item)
            
            # Get full content from each engine
            all_full_content = []
            for engine_name, items in items_by_engine.items():
                try:
                    engine = self._get_engine_instance(engine_name)
                    if engine:
                        logger.info(
                            f"Getting full content for {len(items)} items from {engine_name}"
                        )
                        full_content = engine._get_full_content(items)
                        all_full_content.extend(full_content)
                    else:
                        logger.warning(f"Could not get engine instance for {engine_name}")
                        all_full_content.extend(items)  # Return as-is
                except Exception:
                    logger.exception(
                        f"Error getting full content from {engine_name}"
                    )
                    all_full_content.extend(items)  # Return as-is
            
            # Add items without engine mapping
            all_full_content.extend(items_without_engine)
            
            return all_full_content
        
        # Sequential search was used - use original logic
        elif hasattr(self, "_selected_engine"):
            try:
                logger.info(
                    f"Using {self._selected_engine_name} to get full content"
                )
                return self._selected_engine._get_full_content(relevant_items)
            except Exception:
                logger.exception(
                    f"Error getting full content from {self._selected_engine_name}"
                )
                # Fall back to returning relevant items without full content
                return relevant_items
        else:
            logger.warning(
                "No engine was selected during preview phase, returning relevant items as-is"
            )
            return relevant_items

    def _get_engine_instance(
        self, engine_name: str
    ) -> Optional[BaseSearchEngine]:
        """Get or create an instance of the specified search engine"""
        # Return cached instance if available
        if engine_name in self.engine_cache:
            return self.engine_cache[engine_name]

        # Create a new instance
        engine = None
        try:
            # Only pass parameters that all engines accept
            common_params = {"llm": self.llm, "max_results": self.max_results}

            # Add max_filtered_results if specified
            if self.max_filtered_results is not None:
                common_params["max_filtered_results"] = (
                    self.max_filtered_results
                )

            engine = create_search_engine(
                engine_name,
                settings_snapshot=self.settings_snapshot,
                programmatic_mode=self.programmatic_mode,
                **common_params,
            )
        except Exception:
            logger.exception(
                f"Error creating engine instance for {engine_name}"
            )
            return None

        if engine:
            # Cache the instance
            self.engine_cache[engine_name] = engine

        return engine

    def invoke(self, query: str) -> List[Dict[str, Any]]:
        """Compatibility method for LangChain tools"""
        return self.run(query)
