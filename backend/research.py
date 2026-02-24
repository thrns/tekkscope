import os
from pathlib import Path
from typing import Optional, Dict, Any

from local_deep_research import api as ldr_api


def load_env():
    """Load environment variables from .env into process env using python-dotenv."""
    env_file = Path(__file__).parent / ".env"
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_file, override=False)
    except Exception:
        pass


def run_research(query: str, mode: str = "quick", iterations: Optional[int] = None) -> Dict[str, Any]:
    """Run Local Deep Research using Python API, configured via environment vars.
    Returns a result dictionary (e.g., contains 'summary', 'citations', etc.).
    """
    load_env()

    provider = os.getenv("LDR_LLM_PROVIDER", "openai")
    model = os.getenv("LDR_LLM_MODEL")  
    openai_key = os.getenv("LDR_LLM_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    searxng_url = os.getenv("LDR_SEARXNG_URL", "http://127.0.0.1:8080")

    if provider.lower() in {"openai", "anthropic", "openai_endpoint"} and not openai_key:
        raise RuntimeError("Missing API key. Set LDR_LLM_OPENAI_API_KEY or OPENAI_API_KEY in .env.")

    settings_override: Dict[str, Any] = {}
    if iterations is not None:
        settings_override["search.iterations"] = int(iterations)

    if searxng_url:
        settings_override.setdefault("search.tool", None)

    max_tokens_env = os.getenv("LDR_LLM_MAX_TOKENS")
    try:
        max_tokens = int(max_tokens_env) if max_tokens_env else 8000
        settings_override["llm.max_tokens"] = max_tokens
    except (TypeError, ValueError):
        settings_override["llm.max_tokens"] = 8000

    mode_norm = (mode or "quick").lower()
    if mode_norm in {"quick", "summary", "quick_summary"}:
        result = ldr_api.quick_summary(
            query=query,
            provider=provider,
            api_key=openai_key,
            settings_override=settings_override or None,
        )
    elif mode_norm in {"report", "detailed", "detailed_research"}:
        result = ldr_api.detailed_research(
            query=query,
            retrievers=None,
            llms=None,
        )
    else:
        result = ldr_api.quick_summary(
            query=query,
            provider=provider,
            api_key=openai_key,
            settings_override=settings_override or None,
        )

    if not isinstance(result, dict):
        raise RuntimeError(f"Unexpected LDR result type: {type(result)}")
    return result