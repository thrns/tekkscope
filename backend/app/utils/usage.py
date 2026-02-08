"""Best-effort usage accounting shared by search and scraping paths."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from app.clients.supabase_client import decrement_credits, supabase
from app.config.credit_rates import compute_credits_used

logger = logging.getLogger(__name__)


def estimate_token_split(text: str, input_ratio: float = 0.7) -> tuple[int, int]:
    """Estimate input/output tokens when a provider does not return counts."""

    total_tokens = max(1, round(len(text or "") / 4))
    bounded_ratio = min(0.95, max(0.05, input_ratio))
    input_tokens = max(1, round(total_tokens * bounded_ratio))
    output_tokens = max(1, total_tokens - input_tokens)
    return input_tokens, output_tokens


def record_usage(
    *,
    user_id: str | None,
    api_key_id: str | None,
    service_used: str,
    content: str,
    provider: str,
    model: str,
    input_ratio: float = 0.7,
) -> float:
    """Persist one usage event and decrement credits without breaking a request.

    Current provider integrations expose text rather than authoritative token
    counts, so the record is explicitly estimated. Once a provider response
    includes usage metadata, callers can replace the estimate with exact counts.
    """

    if not user_id:
        return 0.0

    input_tokens, output_tokens = estimate_token_split(content, input_ratio)
    credits_used = compute_credits_used(input_tokens, output_tokens, provider, model)
    research_id = str(uuid.uuid4())
    payload = {
        "user_id": user_id,
        "service_used": service_used,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "credits_used": credits_used,
        "research_id": research_id,
        "api_token_id": api_key_id,
        "provider": provider,
        "model": model,
        "token_count_estimated": True,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    try:
        try:
            supabase.table("usage").insert(payload).execute()
        except Exception:
            # Older projects may not have provider/model estimate columns yet.
            # Keep billing telemetry compatible until the additive migration is
            # applied, while retaining the richer payload for new schemas.
            legacy_payload = {
                key: payload[key]
                for key in (
                    "user_id",
                    "service_used",
                    "input_tokens",
                    "output_tokens",
                    "credits_used",
                    "research_id",
                    "api_token_id",
                    "timestamp",
                )
            }
            supabase.table("usage").insert(legacy_payload).execute()
        decrement_credits(user_id, credits_used)
    except Exception:  # noqa: BLE001 - telemetry must not break user requests
        logger.exception("Failed to persist usage event for %s", service_used)
    return credits_used
