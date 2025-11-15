import os
from pathlib import Path
from typing import Optional, Dict, Any

from app.research_lib import api as ldr_api
from app.research_lib.api.settings_utils import create_settings_snapshot
from app.research_lib.config.provider_router import (
    get_provider_order,
    normalize_provider_name,
    provider_model,
    provider_overrides_from_env,
)


def load_env():
    """Load environment variables from .env into process env using python-dotenv."""
    env_file = Path(__file__).parent / ".env"
    try:
        from dotenv import load_dotenv
        # load_dotenv returns True if the .env is found and loaded; False otherwise
        load_dotenv(dotenv_path=env_file, override=False)
    except Exception:
        # If dotenv is not installed or any error occurs, continue without failing
        pass


def run_research(query: str, mode: str = "quick", iterations: Optional[int] = None) -> Dict[str, Any]:
    """Run Local Deep Research using Python API, configured via environment vars.

    Returns a result dictionary from LDR (e.g., contains 'summary', 'citations', etc.).
    """
    load_env()

    # Read from process environment (populated by dotenv) and apply sensible defaults
    provider = normalize_provider_name(
        os.getenv("TEKK_LLM_PROVIDER")
        or os.getenv("LDR_LLM_PROVIDER")
        or os.getenv("USE_MODEL", "openai")
    )
    model = os.getenv("TEKK_LLM_MODEL") or os.getenv("LDR_LLM_MODEL")
    searxng_url = os.getenv("TEKK_SEARXNG_URL", "https://search.tekkscope.com")

    # Optional: override settings (e.g., iterations, search tool). Keys based on LDR settings schema.
    settings_override: Dict[str, Any] = {}
    if iterations is not None:
        settings_override["search.iterations"] = int(iterations)

    settings_override["search.tool"] = "searxng"
    settings_override[
        "search.engine.web.searxng.default_params.instance_url"
    ] = searxng_url

    # Clamp max tokens to a safe value for cloud models
    max_tokens_env = os.getenv("LDR_LLM_MAX_TOKENS")
    try:
        max_tokens = int(max_tokens_env) if max_tokens_env else 8000
        settings_override["llm.max_tokens"] = max_tokens
    except (TypeError, ValueError):
        settings_override["llm.max_tokens"] = 8000

    provider_overrides = provider_overrides_from_env(
        max_tokens=settings_override["llm.max_tokens"],
        temperature=0.7,
        search_tool="searxng",
        search_instance_url=searxng_url,
    )
    provider_overrides["llm.provider"] = provider
    provider_overrides["llm.model"] = provider_model(provider, model)
    provider_overrides["llm.failover_providers"] = ",".join(
        get_provider_order(provider)[1:]
    )
    provider_overrides.update(settings_override)
    settings_snapshot = create_settings_snapshot(overrides=provider_overrides)

    # Choose API function based on mode
    mode_norm = (mode or "quick").lower()
    if mode_norm in {"quick", "summary", "quick_summary"}:
        result = ldr_api.quick_summary(
            query=query,
            settings_snapshot=settings_snapshot,
            programmatic_mode=True,
        )
    elif mode_norm in {"report", "detailed", "detailed_research"}:
        result = ldr_api.detailed_research(
            query=query,
            retrievers=None,
            llms=None,
            iterations=iterations or 1,
            settings_snapshot=settings_snapshot,
            search_tool="searxng",
        )
    else:
        # Fallback to quick_summary
        result = ldr_api.quick_summary(
            query=query,
            settings_snapshot=settings_snapshot,
            programmatic_mode=True,
        )

    if not isinstance(result, dict):
        raise RuntimeError(f"Unexpected LDR result type: {type(result)}")
    return result
