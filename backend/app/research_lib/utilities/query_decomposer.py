"""
Query decomposition utilities for breaking down complex queries into searchable sub-queries.
"""

from typing import List, Optional
from loguru import logger

from ..advanced_search_system.questions.standard_question import StandardQuestionGenerator


def is_query_search_ready(query: str, max_length: int = 200) -> bool:
    """
    Check if a query is suitable for direct search without decomposition.
    
    Args:
        query: The query to check
        max_length: Maximum character length for a search-ready query (default: 200)
        
    Returns:
        True if query is search-ready, False if it needs decomposition
    """
    if not query or not query.strip():
        return False
    
    query = query.strip()
    
    # Length check
    if len(query) > max_length:
        logger.debug(f"Query too long ({len(query)} chars), needs decomposition")
        return False
    
    # Sentence count check (more than 2 sentences suggests complexity)
    sentences = [s.strip() for s in query.split('.') if s.strip()]
    if len(sentences) > 2:
        logger.debug(f"Query has {len(sentences)} sentences, needs decomposition")
        return False
    
    # Instruction pattern check (queries with AI instructions need decomposition)
    instruction_patterns = [
        "you are a", "your task is", "provide a", "generate a",
        "conduct a", "analyze", "extract", "identify and analyze",
        "specializing in", "so we can understand", "your task",
        "systematic search", "multiple platforms"
    ]
    query_lower = query.lower()
    if any(pattern in query_lower for pattern in instruction_patterns):
        logger.debug(f"Query contains instruction patterns, needs decomposition")
        return False
    
    # Check for multiple distinct topics (indicated by multiple periods and varied content)
    if len(sentences) > 1:
        # Check if sentences are very different in length/content (suggests multiple topics)
        sentence_lengths = [len(s.split()) for s in sentences]
        if max(sentence_lengths) > 2 * min(sentence_lengths) and len(sentences) >= 2:
            logger.debug("Query appears to have multiple distinct topics, needs decomposition")
            return False
    
    return True


def decompose_query(
    query: str,
    llm,
    max_sub_queries: int = 5,
    context: str = ""
) -> List[str]:
    """
    Decompose a complex query into multiple focused, searchable sub-queries.
    
    Args:
        query: The complex query to decompose
        llm: Language model instance for decomposition
        max_sub_queries: Maximum number of sub-queries to generate (default: 5)
        context: Optional context to help with decomposition
        
    Returns:
        List of focused, searchable sub-queries
    """
    if not query or not query.strip():
        return []
    
    logger.info(f"Decomposing query into searchable sub-queries: {query[:100]}...")
    
    try:
        # Use StandardQuestionGenerator's generate_sub_questions method
        question_generator = StandardQuestionGenerator(llm)
        sub_queries = question_generator.generate_sub_questions(query, context)
        
        # Limit to max_sub_queries
        sub_queries = sub_queries[:max_sub_queries]
        
        # Filter out any queries that are too short or too long
        filtered_queries = []
        for q in sub_queries:
            q = q.strip()
            # Skip queries that are too short (< 5 words) or too long (> 100 words)
            word_count = len(q.split())
            if 5 <= word_count <= 100:
                filtered_queries.append(q)
            else:
                logger.debug(f"Filtered out query (word count: {word_count}): {q[:50]}...")
        
        if not filtered_queries:
            # Fallback: if decomposition failed, try to extract key phrases
            logger.warning("Decomposition returned no valid queries, using fallback")
            filtered_queries = _fallback_decomposition(query)
        
        logger.info(f"Decomposed query into {len(filtered_queries)} sub-queries")
        return filtered_queries
        
    except Exception as e:
        logger.exception(f"Error decomposing query: {e}")
        # Fallback to simple decomposition
        return _fallback_decomposition(query)


def _fallback_decomposition(query: str) -> List[str]:
    """
    Fallback decomposition method when LLM decomposition fails.
    Uses simple heuristics to break down the query.
    
    Args:
        query: The query to decompose
        
    Returns:
        List of sub-queries
    """
    # Split by sentences and create queries from each
    sentences = [s.strip() for s in query.split('.') if s.strip() and len(s.strip()) > 10]
    
    # If we have multiple sentences, use them as separate queries
    if len(sentences) >= 2:
        return sentences[:5]
    
    # If single sentence but long, try to split by conjunctions
    if len(query.split()) > 30:
        # Split by common conjunctions
        for delimiter in [' and ', ' or ', ' but ', ';', ' - ']:
            if delimiter in query:
                parts = [p.strip() for p in query.split(delimiter) if p.strip()]
                if len(parts) >= 2:
                    return parts[:5]
    
    # Last resort: return the original query
    return [query]

