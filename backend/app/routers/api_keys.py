"""Authenticated API-key management endpoints.

The legacy ``/create`` and ``/list/{user_id}`` routes remain as aliases so
existing clients do not break, but ownership is always derived from the
authenticated token rather than trusted request input.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.key_utils import generate_api_key, hash_api_key, key_prefix, mask_api_key
from app.auth.security import validate_token
from app.clients.supabase_client import supabase


logger = logging.getLogger(__name__)
router = APIRouter()


class APIKeyData(BaseModel):
    # Kept optional for backward-compatible clients. The authenticated user is
    # authoritative and a mismatching value is rejected.
    user_id: str | None = None
    name: str = Field(default="", max_length=100)


def _assert_requested_owner(requested_user_id: str | None, user: dict) -> str:
    owner_id = user.get("sub")
    if not owner_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if requested_user_id and requested_user_id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User ownership mismatch")
    return owner_id


def _masked_record(row: dict) -> dict:
    raw_key = row.get("api_key")
    prefix = row.get("api_key_prefix") or (raw_key[:10] if raw_key else None)
    return {
        "id": row.get("id"),
        "api_key": mask_api_key(raw_key) if raw_key else prefix,
        "api_key_prefix": prefix,
        "api_key_name": row.get("api_key_name") or row.get("name"),
        "created_at": row.get("created_at"),
        "created_by": row.get("created_by"),
    }


@router.post("", summary="Create a new API key")
@router.post("/create", include_in_schema=False)
async def create_api_key(
    api_key_data: APIKeyData,
    user: dict = Depends(validate_token),
):
    owner_id = _assert_requested_owner(api_key_data.user_id, user)
    api_key = generate_api_key()
    name = api_key_data.name.strip() or "Untitled key"

    created_by = user.get("email") or owner_id
    try:
        user_response = (
            supabase.table("user_data")
            .select("uuid, name, email")
            .eq("uuid", owner_id)
            .execute()
        )
        if user_response.data:
            user_row = user_response.data[0]
            created_by = user_row.get("name") or user_row.get("email") or created_by
    except Exception:
        # API-key creation should still work for legacy users whose profile row
        # has not been synchronized yet.
        logger.info("Profile lookup unavailable while creating an API key")

    secure_payload = {
        "user_id": owner_id,
        "api_key_hash": hash_api_key(api_key),
        "api_key_prefix": key_prefix(api_key),
        "api_key_name": name,
        "created_by": created_by,
    }

    try:
        response = supabase.table("api_keys").insert(secure_payload).execute()
    except Exception:
        # Existing installations may not have the migration columns yet. Keep
        # the old route functional while emitting a migration signal; new
        # deployments should apply the migration and never use this fallback.
        logger.warning("API-key hash columns are unavailable; apply the API-key migration")
        legacy_payload = {
            "api_key": api_key,
            "user_id": owner_id,
            "api_key_name": name,
            "created_by": created_by,
        }
        response = supabase.table("api_keys").insert(legacy_payload).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create API key")

    # The plaintext key is intentionally returned only at creation time.
    return {"api_key": api_key, "id": response.data[0].get("id")}


@router.get("", summary="List the current user's API keys")
@router.get("/list/{user_id}", include_in_schema=False)
async def list_api_keys(
    user_id: str | None = None,
    user: dict = Depends(validate_token),
):
    owner_id = _assert_requested_owner(user_id, user)
    try:
        response = (
            supabase.table("api_keys")
            .select("id, api_key, api_key_prefix, api_key_name, created_at, created_by")
            .eq("user_id", owner_id)
            .execute()
        )
    except Exception:
        response = (
            supabase.table("api_keys")
            .select("id, api_key, created_at, created_by, api_key_name")
            .eq("user_id", owner_id)
            .execute()
        )
    return [_masked_record(row) for row in (response.data or [])]


@router.delete("/{api_key_id}", summary="Delete one of the current user's API keys")
@router.delete("/delete/{api_key_id}", include_in_schema=False)
async def delete_api_key(
    api_key_id: str,
    user: dict = Depends(validate_token),
):
    owner_id = _assert_requested_owner(None, user)
    response = (
        supabase.table("api_keys")
        .delete()
        .eq("id", api_key_id)
        .eq("user_id", owner_id)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key deleted successfully"}
