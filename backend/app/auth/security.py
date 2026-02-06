from typing import Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, APIKeyQuery

from app.auth.key_utils import key_prefix, verify_api_key
from app.clients.supabase_client import supabase

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
api_key_query = APIKeyQuery(name="token", auto_error=False)

def _lookup_api_key(api_key: str) -> Dict | None:
    """Resolve both migrated hashed keys and legacy plaintext keys.

    The legacy lookup keeps existing integrations working while deployments
    migrate the table to ``api_key_hash`` and ``api_key_prefix`` columns.
    """

    try:
        hashed_response = (
            supabase.table("api_keys")
            .select("id, user_id, api_key_hash, api_key_prefix")
            .eq("api_key_prefix", key_prefix(api_key))
            .execute()
        )
        for row in hashed_response.data or []:
            if verify_api_key(api_key, row.get("api_key_hash")):
                return {"sub": row["user_id"], "api_key_id": row["id"]}
    except Exception:
        # Older schemas do not have the migration columns yet. Fall through
        # to the legacy lookup rather than breaking existing API clients.
        pass

    legacy_response = (
        supabase.table("api_keys")
        .select("id, user_id, api_key")
        .eq("api_key", api_key)
        .execute()
    )
    if legacy_response.data:
        row = legacy_response.data[0]
        return {"sub": row["user_id"], "api_key_id": row["id"]}
    return None


def _parse_bearer_token(token: str | None) -> str:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, separator, api_key = token.partition(" ")
    if scheme.lower() != "bearer" or not separator or not api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Expected Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return api_key.strip()


def validate_token(token: str = Depends(api_key_header)) -> Dict:
    """
    Validate the Authorization header token and return user data.

    This function checks the token against the 'api_keys' table in the database.
    """
    try:
        api_key = _parse_bearer_token(token)
        key_data = _lookup_api_key(api_key)
        if key_data:
            return key_data

        # Fallback to users table if legacy tokens are stored there
        response = supabase.table("users").select("id, email").eq("api_key", api_key).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_data = response.data[0]
        return {"sub": user_data["id"], "email": user_data.get("email")}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable",
        ) from None


def validate_token_query(
    token: str | None = Depends(api_key_query),
    authorization: str | None = Depends(api_key_header),
) -> Dict:
    """Validate stream credentials from a header, with a legacy query fallback.

    Headers are preferred because query-string credentials can be copied into
    browser history, access logs, and referrer metadata. The query form remains
    available for existing EventSource clients.
    """

    try:
        candidate = token.strip() if token else None
        if authorization:
            candidate = _parse_bearer_token(authorization)
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization credentials are missing",
            )
        key_data = _lookup_api_key(candidate)
        if not key_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        return key_data
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable",
        ) from None
