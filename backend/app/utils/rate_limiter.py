from fastapi import HTTPException
from app.clients.supabase_client import supabase
import datetime
import os
import logging

# Plan Limits
# Format: (requests, window_seconds)
PLAN_LIMITS = {
    "free": {"requests": 30, "window": 86400}, # 30 per day
    "admin": {"requests": 0, "window": 0},     # ADMIN bypasses rate limits (unlimited)
    "small": {"requests": 10, "window": 60},   # 10 per minute
    "medium": {"requests": 50, "window": 60},  # 50 per minute
    "big": {"requests": 500, "window": 60},    # 500 per minute
}

async def check_rate_limit(api_key_id: str, user_id: str):
    """
    Check if the API key has exceeded its rate limit.
    ADMIN plan users bypass rate limits.
    """
    try:
        # 1. Get User Plan
        # Assuming 'plan' column exists in user_data. Default to 'free' if not found or error.
        plan = "free"
        try:
            user_res = supabase.table("user_data").select("plan").eq("uuid", user_id).execute()
            if user_res.data and len(user_res.data) > 0:
                plan = user_res.data[0].get("plan", "free").lower()
        except Exception as e:
            logging.warning(f"Failed to fetch user plan for {user_id}, defaulting to free. Error: {e}")

        if plan not in PLAN_LIMITS:
            plan = "free"

        # ADMIN plan bypasses rate limits
        if plan == "admin":
            logging.info(f"User {user_id} has ADMIN plan - bypassing rate limits")
            return

        limit_info = PLAN_LIMITS[plan]
        max_requests = limit_info["requests"]
        window_seconds = limit_info["window"]

        # 2. Calculate Window Start
        now = datetime.datetime.utcnow()
        window_start = now - datetime.timedelta(seconds=window_seconds)
        window_start_iso = window_start.isoformat() + "Z"

        # 3. Count Requests in Window
        # We count rows in 'usage' table for this api_token_id since window_start
        # Note: This count operation might be expensive on large tables without proper indexing.
        # Ensure 'api_token_id' and 'timestamp' are indexed.
        
        # Using count='exact', head=True to just get the count
        count_res = supabase.table("usage") \
            .select("id", count="exact", head=True) \
            .eq("api_token_id", api_key_id) \
            .gte("timestamp", window_start_iso) \
            .execute()
            
        current_usage = count_res.count if count_res.count is not None else 0

        if current_usage >= max_requests:
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded. Plan: {plan.capitalize()}. Limit: {max_requests} requests per {window_seconds} seconds."
            )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Rate limit check failed: {e}")
        # Fail open or closed? Usually fail open to avoid blocking users on system error, 
        # but for strict billing, might want to fail closed. 
        # Here we'll log and pass to avoid downtime.
        pass
