"""
Query preprocessing utilities that combine decomposition and enhancement.
"""

from typing import Dict, Any, List, Optional
from loguru import logger

from .query_decomposer import is_query_search_ready, decompose_query
from .prompt_enhancer import (
    enhance_lens_prompt,
    enhance_deeplens_prompt,
    enhance_reportlens_prompt,
)


def preprocess_query_for_research(
    raw_query: str,
    llm,
    mode: str = "deeplens",
    max_sub_queries: int = 5
) -> Dict[str, Any]:
    """
    Preprocess a query for research by checking if it needs decomposition
    and enhancing it for synthesis.
    
    Args:
        raw_query: The original user query
        llm: Language model instance for decomposition
        mode: Research mode ("lens", "deeplens", or "reportlens")
        max_sub_queries: Maximum number of sub-queries to generate
        
    Returns:
        Dictionary containing:
        - search_queries: List of queries to use for searching
        - synthesis_prompt: Enhanced prompt for LLM synthesis
        - original_query: Original user query
        - was_decomposed: Boolean indicating if decomposition occurred
    """
    if not raw_query or not raw_query.strip():
        raise ValueError("Query cannot be empty")
    
    raw_query = raw_query.strip()
    logger.info(f"Preprocessing query for {mode} mode: {raw_query[:100]}...")
    
    # Check if query is search-ready
    search_ready = is_query_search_ready(raw_query)
    
    if search_ready:
        logger.info("Query is search-ready, using as-is")
        # Query is good for direct search
        search_queries = [raw_query]
        was_decomposed = False
    else:
        logger.info("Query needs decomposition")
        # Decompose the query into searchable sub-queries
        search_queries = decompose_query(raw_query, llm, max_sub_queries)
        
        if not search_queries:
            # Fallback: use original query if decomposition failed
            logger.warning("Decomposition failed, using original query")
            search_queries = [raw_query]
            was_decomposed = False
        else:
            was_decomposed = True
            logger.info(f"Decomposed into {len(search_queries)} search queries")
    
    # Enhance the original query for synthesis (not the decomposed queries)
    synthesis_prompt = _get_enhanced_prompt(raw_query, mode)
    
    return {
        "search_queries": search_queries,
        "synthesis_prompt": synthesis_prompt,
        "original_query": raw_query,
        "was_decomposed": was_decomposed
    }


def _get_enhanced_prompt(query: str, mode: str) -> str:
    """
    Get the enhanced prompt for a given mode.
    
    Args:
        query: The original query
        mode: Research mode ("lens", "deeplens", or "reportlens")
        
    Returns:
        Enhanced prompt string
    """
    if mode == "lens":
        return enhance_lens_prompt(query)
    elif mode == "deeplens":
        return enhance_deeplens_prompt(query)
    elif mode == "reportlens":
        return enhance_reportlens_prompt(query)
    else:
        # Default to deeplens
        logger.warning(f"Unknown mode {mode}, using deeplens enhancement")
        return enhance_deeplens_prompt(query)

