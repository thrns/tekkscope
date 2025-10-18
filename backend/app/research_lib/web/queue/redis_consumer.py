"""
Redis Queue Consumer
Consumes research tasks from Redis queue and processes them.
"""

import threading
import time
import json
from typing import Dict, Any, Optional
from loguru import logger

from .redis_manager import redis_manager
from ...database.encrypted_db import db_manager
from ...database.session_context import get_user_db_session
from ...database.session_passwords import session_password_store
from ...database.models import UserActiveResearch, ResearchHistory
from ...database.queue_service import UserQueueService
from ..routes.globals import active_research, termination_flags
from ..services.research_service import (
    run_research_process,
    start_research_process,
)

class RedisQueueConsumer:
    """
    Consumes tasks from Redis queue and processes them.
    Works alongside QueueProcessorV2 but focuses on Redis consumption.
    """
    
    def __init__(self, check_interval: int = 2):
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        self.active_users = set()
        self.lock = threading.Lock()
        
    def start(self):
        """Start the consumer thread"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._consumption_loop, daemon=True)
        self.thread.start()
        logger.info("Redis Queue Consumer started")
        
    def stop(self):
        """Stop the consumer thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Redis Queue Consumer stopped")
        
    def notify_user_active(self, username: str):
        """Add user to active set to check their queue"""
        with self.lock:
            self.active_users.add(username)
            
    def _consumption_loop(self):
        """Main consumption loop"""
        while self.running:
            try:
                # Get snapshot of active users
                with self.lock:
                    users_to_check = list(self.active_users)
                
                # If no active users, wait for pub/sub notification or timeout
                if not users_to_check:
                    time.sleep(self.check_interval)
                    continue
                    
                for username in users_to_check:
                    self._process_user_queue(username)
                    
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in Redis consumption loop: {e}")
                time.sleep(5)
                
    def _process_user_queue(self, username: str):
        """Process queue for a specific user"""
        try:
            # Check if we can process more tasks for this user
            # We need to know the user's max concurrent limit and current active tasks
            # This requires DB access, so we need a session/password
            
            # Note: In this architecture, we might not have the password readily available
            # if it's not in the session store. If we can't get the password, we can't
            # process the queue for this user.
            
            # Try to find any active session for this user to get password
            # This is a limitation - we rely on user being logged in or having a cached password
            password = self._get_user_password(username)
            if not password:
                # Can't access DB without password
                return

            # Open DB and check capacity
            engine = db_manager.open_user_database(username, password)
            if not engine:
                return
                
            with get_user_db_session(username) as db_session:
                # Check active count
                active_count = (
                    db_session.query(UserActiveResearch)
                    .filter_by(username=username, status="in_progress")
                    .count()
                )
                
                # Default limit if not specified
                max_concurrent = 3 
                
                if active_count >= max_concurrent:
                    return
                    
                # We have slots! Try to dequeue from Redis
                task = redis_manager.dequeue_research(username)
                if task:
                    self._start_task(username, password, task, db_session)
                    
        except Exception as e:
            logger.error(f"Error processing Redis queue for {username}: {e}")

    def _get_user_password(self, username: str) -> Optional[str]:
        """
        Try to retrieve user password from session store.
        This is a best-effort approach since we don't store passwords permanently.
        """
        # We need to iterate through sessions or have a way to look up by username
        # session_password_store stores by (username, session_id)
        # We'll need to modify session_password_store to support this or iterate
        
        # For now, we'll rely on the fact that QueueProcessorV2 passes session_id
        # But here we are independent.
        
        # TODO: Improve password retrieval mechanism for background workers
        return None 

    def _start_task(self, username: str, password: str, task: Dict[str, Any], db_session):
        """Start a dequeued task"""
        research_id = task.get("research_id")
        if not research_id:
            return
            
        logger.info(f"Starting Redis task {research_id} for {username}")
        
        try:
            # Create active record
            active_record = UserActiveResearch(
                username=username,
                research_id=research_id,
                status="in_progress",
                thread_id="pending",
                settings_snapshot=task.get("settings", {})
            )
            db_session.add(active_record)
            db_session.commit()
            
            # Start process
            research_thread = start_research_process(
                research_id,
                task.get("query"),
                task.get("mode"),
                active_research,
                termination_flags,
                run_research_process,
                username=username,
                user_password=password,
                # Extract other params from task/settings
                **self._extract_params(task)
            )
            
            # Update thread ID
            active_record.thread_id = str(research_thread.ident)
            db_session.commit()
            
        except Exception as e:
            logger.error(f"Failed to start Redis task {research_id}: {e}")
            # Should probably re-enqueue or mark as failed in DB if possible

    def _extract_params(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Extract research parameters from task data"""
        settings = task.get("settings", {})
        # Handle nested settings if present
        if "submission" in settings:
            settings = settings["submission"]
            
        return {
            "model_provider": settings.get("model_provider"),
            "model": settings.get("model"),
            "custom_endpoint": settings.get("custom_endpoint"),
            "search_engine": settings.get("search_engine"),
            "max_results": settings.get("max_results"),
            "time_period": settings.get("time_period"),
            "iterations": settings.get("iterations"),
            "questions_per_iteration": settings.get("questions_per_iteration"),
            "strategy": settings.get("strategy", "source-based"),
            "settings_snapshot": task.get("settings", {})
        }

redis_consumer = RedisQueueConsumer()
