import os


# Keep imports deterministic in unit tests without requiring a real Supabase
# project, Redis instance, search service, or model provider.
os.environ.setdefault("SUPABASE_URL", "http://127.0.0.1:54321")
os.environ.setdefault("SUPABASE_API_KEY", "unit-test-key")
os.environ.setdefault("TEKK_REDIS_STREAM_ENABLED", "false")
