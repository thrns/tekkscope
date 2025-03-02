"""Provider ordering and request-time LLM failover helpers.

The application already exposes provider-specific LangChain clients. This
module keeps the routing policy small so it can wrap those clients without
changing the research pipeline's invocation API.
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Iterable, Optional, Sequence

from langchain_core.runnables import Runnable
from loguru import logger


CLOUD_PROVIDERS = ("gemini", "openai", "anthropic")
PROVIDER_ALIASES = {"google": "gemini"}
DEFAULT_MODELS = {
    "gemini": "gemini-2.0-flash",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-latest",
}


def _first_env(*names: str) -> Optional[str]:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def _first_secret_env(*names: str) -> Optional[str]:
    placeholders = {name.upper() for name in names}
    for name in names:
        value = os.getenv(name)
        if value and value.strip().upper() not in placeholders:
            return value
    return None


def _configured_fallback_env() -> Optional[str]:
    names = (
        "TEKK_LLM_FALLBACK_PROVIDERS",
        "TEKK_LLM_FAILOVER_PROVIDERS",
        "LDR_LLM_FALLBACK_PROVIDERS",
        "LDR_LLM_FAILOVER_PROVIDERS",
    )
    for name in names:
        if name in os.environ:
            return os.environ[name]
    return None


def normalize_provider_name(value: Optional[str]) -> str:
    name = (value or "gemini").strip().strip("\"'").lower()
    return PROVIDER_ALIASES.get(name, name)


def provider_model(provider: str, requested_model: Optional[str] = None) -> str:
    """Return a model valid for a provider, honoring provider-specific env vars."""

    normalized = normalize_provider_name(provider)
    env_prefix = normalized.upper()
    configured = _first_env(
        f"TEKK_LLM_{env_prefix}_MODEL",
        f"LDR_LLM_{env_prefix}_MODEL",
    )
    if configured:
        return configured
    if requested_model:
        return requested_model
    return DEFAULT_MODELS.get(normalized, requested_model or "gemma:latest")


def _as_provider_names(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = value.replace(";", ",").split(",")
    elif isinstance(value, Iterable):
        values = value
    else:
        values = [value]

    result: list[str] = []
    for item in values:
        if item is None:
            continue
        raw_name = str(item).strip().strip("\"'")
        if not raw_name:
            continue
        name = normalize_provider_name(raw_name)
        if name and name not in result:
            result.append(name)
    return result


def get_provider_order(
    primary: Optional[str] = None,
    configured_fallbacks: Any = None,
) -> tuple[str, ...]:
    """Return the primary provider followed by configured fallbacks.

    Cloud providers default to the other two cloud providers when their keys
    are present. Local/custom providers retain their existing single-provider
    behavior unless an explicit fallback list is configured.
    """

    primary_name = normalize_provider_name(
        primary
        or os.getenv("TEKK_LLM_PROVIDER")
        or os.getenv("LDR_LLM_PROVIDER")
        or os.getenv("USE_MODEL")
    )
    configured = configured_fallbacks
    if configured is None:
        configured = _configured_fallback_env()

    if configured is None and primary_name in CLOUD_PROVIDERS:
        configured = [provider for provider in CLOUD_PROVIDERS if provider != primary_name]

    order = [primary_name]
    for provider in _as_provider_names(configured):
        if provider != primary_name and provider not in order:
            order.append(provider)
    return tuple(order)


def provider_overrides_from_env(
    *,
    max_tokens: int,
    temperature: float,
    search_tool: str,
    search_instance_url: str,
) -> dict[str, Any]:
    """Build a complete provider-aware settings override map for API clients."""

    primary = normalize_provider_name(
        _first_env("TEKK_LLM_PROVIDER", "LDR_LLM_PROVIDER", "USE_MODEL")
    )
    model = provider_model(
        primary,
        _first_env("TEKK_LLM_MODEL", "LDR_LLM_MODEL"),
    )
    keys = {
        "gemini": _first_secret_env(
            "TEKK_LLM_GEMINI_API_KEY",
            "LDR_LLM_GEMINI_API_KEY",
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
        ),
        "openai": _first_secret_env(
            "TEKK_LLM_OPENAI_API_KEY",
            "LDR_LLM_OPENAI_API_KEY",
            "OPENAI_API_KEY",
        ),
        "anthropic": _first_secret_env(
            "TEKK_LLM_ANTHROPIC_API_KEY",
            "LDR_LLM_ANTHROPIC_API_KEY",
            "ANTHROPIC_API_KEY",
        ),
        "openai_endpoint": _first_secret_env(
            "TEKK_LLM_OPENAI_ENDPOINT_API_KEY",
            "LDR_LLM_OPENAI_ENDPOINT_API_KEY",
            "OPENROUTER_API_KEY",
        ),
    }
    fallback_value = _configured_fallback_env()
    if fallback_value is None and primary in CLOUD_PROVIDERS:
        fallback_value = ",".join(
            provider for provider in CLOUD_PROVIDERS if provider != primary
        )

    return {
        "llm.provider": primary,
        "llm.model": model,
        "llm.api_key": keys.get(primary),
        "llm.gemini.api_key": keys["gemini"],
        "llm.openai.api_key": keys["openai"],
        "llm.anthropic.api_key": keys["anthropic"],
        "llm.openai_endpoint.api_key": keys["openai_endpoint"],
        "llm.failover_providers": fallback_value or "",
        "llm.max_tokens": max_tokens,
        "llm.temperature": temperature,
        "search.tool": search_tool,
        "search.engine.web.searxng.default_params.instance_url": search_instance_url,
    }


class ProviderFailoverError(RuntimeError):
    """Raised when every configured provider fails a request."""

    def __init__(self, errors: Sequence[tuple[str, Exception]]):
        self.errors = tuple(errors)
        details = "; ".join(
            f"{provider}: {type(error).__name__}: {error}"
            for provider, error in self.errors
        )
        super().__init__(f"All configured LLM providers failed ({details})")


class ProviderFailoverLLM(Runnable[Any, Any]):
    """Small invoke/ainvoke-compatible wrapper with ordered provider failover."""

    def __init__(self, providers: Sequence[tuple[str, Any]]):
        if not providers:
            raise ValueError("ProviderFailoverLLM requires at least one provider")
        self.providers = tuple(providers)
        self.provider_order = tuple(name for name, _ in self.providers)
        self.active_provider: Optional[str] = None
        self.last_errors: dict[str, Exception] = {}

    def _record_success(self, provider: str, started: float) -> None:
        self.active_provider = provider
        logger.info(
            "LLM provider succeeded: provider={} elapsed_ms={:.0f}",
            provider,
            (time.monotonic() - started) * 1000,
        )

    def invoke(self, *args: Any, **kwargs: Any) -> Any:
        self.last_errors = {}
        errors: list[tuple[str, Exception]] = []
        for provider, llm in self.providers:
            started = time.monotonic()
            try:
                response = llm.invoke(*args, **kwargs)
                self._record_success(provider, started)
                return response
            except Exception as error:  # noqa: BLE001 - failover must handle provider errors
                self.last_errors[provider] = error
                errors.append((provider, error))
                logger.warning(
                    "LLM provider failed; trying next provider: provider={} error={}",
                    provider,
                    error,
                )
        raise ProviderFailoverError(errors)

    async def ainvoke(self, *args: Any, **kwargs: Any) -> Any:
        self.last_errors = {}
        errors: list[tuple[str, Exception]] = []
        for provider, llm in self.providers:
            started = time.monotonic()
            try:
                ainvoke = getattr(llm, "ainvoke", None)
                if ainvoke is None:
                    response = await asyncio.to_thread(llm.invoke, *args, **kwargs)
                else:
                    response = await ainvoke(*args, **kwargs)
                self._record_success(provider, started)
                return response
            except Exception as error:  # noqa: BLE001 - failover must handle provider errors
                self.last_errors[provider] = error
                errors.append((provider, error))
                logger.warning(
                    "Async LLM provider failed; trying next provider: provider={} error={}",
                    provider,
                    error,
                )
        raise ProviderFailoverError(errors)

    def bind_tools(self, *args: Any, **kwargs: Any) -> "ProviderFailoverLLM":
        """Keep failover active when an agent binds tools to the chat model."""

        bound_providers = []
        for provider, llm in self.providers:
            bind_tools = getattr(llm, "bind_tools", None)
            if bind_tools is None:
                raise AttributeError(f"Provider {provider} does not support bind_tools")
            bound_providers.append((provider, bind_tools(*args, **kwargs)))
        return ProviderFailoverLLM(bound_providers)

    def __call__(self, input: Any, *args: Any, **kwargs: Any) -> Any:
        """Allow LangChain expression pipelines to coerce this wrapper."""

        return self.invoke(input, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        # Preserve model/callback attributes expected by existing wrappers.
        return getattr(self.providers[0][1], name)

    def __repr__(self) -> str:
        return f"ProviderFailoverLLM(providers={self.provider_order!r})"
