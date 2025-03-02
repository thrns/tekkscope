"""
Queue configuration settings.
"""

import os

# Queue mode configuration
QUEUE_MODE = os.environ.get(
    "TEKK_QUEUE_MODE", "direct"
).lower()  # "direct" or "queue"

# Maximum concurrent researches per user
MAX_CONCURRENT_PER_USER = int(os.environ.get("TEKK_MAX_CONCURRENT", "3"))

# Whether to use queue processor at all
USE_QUEUE_PROCESSOR = QUEUE_MODE == "queue"

# Queue check interval (seconds) - only used if queuing is enabled
QUEUE_CHECK_INTERVAL = int(os.environ.get("TEKK_QUEUE_INTERVAL", "10"))

# Redis Queue Configuration
USE_REDIS_QUEUE = os.environ.get("USE_REDIS_QUEUE", "true").lower() == "true"
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Task timeout in seconds (default: 1 hour)
QUEUE_TASK_TIMEOUT = int(os.environ.get("TEKK_QUEUE_TASK_TIMEOUT", "1800"))

# Cleanup interval in seconds (default: 15 minutes)
CLEANUP_INTERVAL = int(os.environ.get("TEKK_CLEANUP_INTERVAL", "900"))
