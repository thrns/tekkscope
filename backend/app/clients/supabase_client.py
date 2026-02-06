import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_API_KEY")

if not url or not key:
    raise ValueError("Supabase URL and Key must be set in the environment variables.")

supabase: Client = create_client(url, key)

def decrement_credits(user_id: str | None, amount: float | int) -> None:
    try:
        if not user_id:
            return
        sel = supabase.table("credits").select("balance").eq("user_id", user_id).execute()
        data = (sel.data or [])
        bal = 0.0
        if isinstance(data, list) and data:
            item = data[0]
            bal = float(item.get("balance") or 0)
        new_balance = max(0.0, bal - float(amount or 0))
        now = datetime.utcnow().isoformat()+"Z"
        upd = supabase.table("credits").update({"balance": new_balance, "last_updated": now}).eq("user_id", user_id).execute()
        if not upd.data:
            supabase.table("credits").insert({"user_id": user_id, "balance": new_balance, "last_updated": now}).execute()
    except Exception:
        pass