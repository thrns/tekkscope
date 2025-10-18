import os
import redis
import json
import time
from loguru import logger
from typing import Optional, Any, List, Dict, Generator

class RedisManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.client: Optional[redis.Redis] = None
        self.max_retries = 3
        self.retry_delay = 1
        self._connect()
        self._initialized = True
        
    def _connect(self):
        """Connect to Redis with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.client = redis.from_url(
                    self.redis_url, 
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                self.client.ping()
                logger.info(f"Connected to Redis at {self.redis_url}")
                return
            except Exception as e:
                logger.warning(f"Failed to connect to Redis (attempt {attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Could not connect to Redis after {self.max_retries} attempts")
                    self.client = None
            
    def get_client(self) -> Optional[redis.Redis]:
        """Get Redis client, attempting reconnect if needed"""
        if not self.client:
            self._connect()
        
        # Check if connection is still alive
        if self.client:
            try:
                self.client.ping()
            except Exception:
                logger.warning("Redis connection lost, reconnecting...")
                self._connect()
                
        return self.client
        
    def enqueue_research(self, username: str, research_id: str, data: dict) -> bool:
        """Add research task to Redis queue"""
        client = self.get_client()
        if not client:
            return False
            
        try:
            # Use a list for the queue
            queue_key = f"queue:research:{username}"
            
            # Store full task data
            task_data = {
                "username": username,
                "research_id": research_id,
                **data
            }
            
            # Push to right (end) of list
            client.rpush(queue_key, json.dumps(task_data))
            
            # Publish notification for real-time processing
            client.publish("research_tasks", json.dumps({"username": username, "research_id": research_id, "action": "queued"}))
            
            logger.info(f"Enqueued research {research_id} to Redis for user {username}")
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue research to Redis: {e}")
            return False

    def dequeue_research(self, username: str, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """
        Remove and return the next research task from the queue.
        Uses blpop for blocking wait if timeout > 0.
        """
        client = self.get_client()
        if not client:
            return None
            
        try:
            queue_key = f"queue:research:{username}"
            
            if timeout > 0:
                # Blocking pop
                result = client.blpop(queue_key, timeout=timeout)
                if result:
                    # blpop returns (key, value) tuple
                    return json.loads(result[1])
            else:
                # Non-blocking pop
                result = client.lpop(queue_key)
                if result:
                    return json.loads(result)
                    
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue research for {username}: {e}")
            return None

    def peek_queue(self, username: str) -> Optional[Dict[str, Any]]:
        """Look at the next item in queue without removing it"""
        client = self.get_client()
        if not client:
            return None
            
        try:
            queue_key = f"queue:research:{username}"
            items = client.lrange(queue_key, 0, 0)
            if items:
                return json.loads(items[0])
            return None
        except Exception as e:
            logger.error(f"Failed to peek queue for {username}: {e}")
            return None

    def remove_from_queue(self, username: str, research_id: str) -> bool:
        """Remove a specific research task from the queue by ID"""
        client = self.get_client()
        if not client:
            return False
            
        try:
            queue_key = f"queue:research:{username}"
            
            # We need to find the item with the matching research_id
            # Since Redis lists don't support removing by partial match,
            # we iterate through the list. For large queues this could be slow,
            # but user queues are typically small.
            
            items = client.lrange(queue_key, 0, -1)
            for item_str in items:
                try:
                    item = json.loads(item_str)
                    if item.get("research_id") == research_id:
                        # Found it, remove this specific string
                        # count=1 means remove first occurrence (should be unique anyway)
                        client.lrem(queue_key, 1, item_str)
                        logger.info(f"Removed research {research_id} from Redis queue")
                        return True
                except json.JSONDecodeError:
                    continue
                    
            return False
        except Exception as e:
            logger.error(f"Failed to remove research {research_id} from Redis: {e}")
            return False

    def get_all_queued_tasks(self, username: str) -> List[Dict[str, Any]]:
        """Get all queued tasks for a user"""
        client = self.get_client()
        if not client:
            return []
            
        try:
            queue_key = f"queue:research:{username}"
            items = client.lrange(queue_key, 0, -1)
            return [json.loads(item) for item in items]
        except Exception as e:
            logger.error(f"Failed to get queued tasks for {username}: {e}")
            return []

    def get_queue_length(self, username: str) -> int:
        client = self.get_client()
        if not client:
            return 0
        try:
            return client.llen(f"queue:research:{username}")
        except Exception:
            return 0
            
    def subscribe_to_tasks(self) -> Generator[Dict[str, Any], None, None]:
        """
        Subscribe to new task notifications
        
        Yields:
            Dict containing task info
        """
        try:
            client = self.get_client()
            pubsub = client.pubsub()
            pubsub.subscribe("research_tasks")
            
            for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        yield data
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in pubsub message: {message['data']}")
                        
        except Exception as e:
            logger.error(f"PubSub error: {e}")
            # Wait a bit before retrying to avoid tight loops on error
            import time
            time.sleep(5)

    def get_all_users_with_queues(self) -> list[str]:
        """
        Get all usernames that have active queues.
        Useful for maintenance tasks like cleanup.
        """
        try:
            client = self.get_client()
            # Scan for keys matching queue pattern
            # Pattern is "queue:{username}"
            cursor = '0'
            users = set()
            while cursor != 0:
                cursor, keys = client.scan(cursor=cursor, match="queue:research:*", count=100) # Changed match pattern to be more specific
                for key in keys:
                    # Extract username from key "queue:research:{username}"
                    # key is bytes, decode first
                    key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                    if key_str.startswith("queue:research:"):
                        username = key_str.split(":", 2)[2] # Split by 2 to get the third part
                        users.add(username)
            return list(users)
        except Exception as e:
            logger.error(f"Failed to scan for user queues: {e}")
            return []

redis_manager = RedisManager()
