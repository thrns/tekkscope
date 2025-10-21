"""
Queue processor v2 - uses encrypted user databases instead of service.db
Supports both direct execution and queue modes.
"""

import threading
import time
from typing import Set, Dict, Any

from loguru import logger

from ...database.encrypted_db import db_manager
from ...database.models import (
    QueuedResearch,
    ResearchHistory,
    UserActiveResearch,
)
from ...database.queue_service import UserQueueService
from ...database.session_context import get_user_db_session
from ...database.session_passwords import session_password_store
from ..routes.globals import active_research, termination_flags
from ..services.research_service import (
    run_research_process,
    start_research_process,
)
from .redis_manager import redis_manager
from ...config.queue_config import (
    MAX_CONCURRENT_PER_USER,
    QUEUE_CHECK_INTERVAL,
    USE_REDIS_QUEUE,
    QUEUE_TASK_TIMEOUT,
    CLEANUP_INTERVAL
)
from datetime import datetime, UTC


class QueueProcessorV2:
    """
    Processes queued researches using encrypted user databases.
    This replaces the service.db approach.
    Now supports Redis as the primary queue.
    """

    def __init__(self, check_interval=10):
        """
        Initialize the queue processor.

        Args:
            check_interval: How often to check for work (seconds)
        """
        self.check_interval = check_interval
        self.running = False
        self.thread = None

        # In the new per-user encrypted database architecture,
        # there's no system database for global settings.
        # Use defaults for queue processor configuration.
        self.max_concurrent_per_user = 3
        self.direct_mode = True

        # Log configuration
        logger.info(
            "Queue processor using default configuration "
            "(per-user encrypted databases don't have system-wide settings)"
        )

        # Track which users we should check
        self._users_to_check: Set[str] = set()
        self._users_lock = threading.Lock()

    def start(self):
        """Start the queue processor thread."""
        if self.running:
            logger.warning("Queue processor already running")
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._process_queue_loop, daemon=True
        )
        self.thread.start()
        
        # Also start Redis subscriber for real-time updates
        self.subscriber_thread.start()
        
        # Start cleanup loop
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop, daemon=True
        )
        self._cleanup_thread.start()
        
        logger.info(f"Queue processor v2 started (Interval: {self.check_interval}s, Cleanup: {CLEANUP_INTERVAL}s)")

    def stop(self):
        """Stop the queue processor thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("Queue processor v2 stopped")

    def notify_user_activity(self, username: str, session_id: str):
        """
        Notify that a user has activity and their queue should be checked.

        Args:
            username: The username
            session_id: The Flask session ID (for password access)
        """
        with self._users_lock:
            self._users_to_check.add(f"{username}:{session_id}")
            logger.debug(f"User {username} added to queue check list")

    def notify_research_queued(self, username: str, research_id: str, **kwargs):
        """
        Notify that a research was queued.
        In direct mode, this immediately starts the research if slots are available.
        In queue mode, it adds to the queue.

        Args:
            username: The username
            research_id: The research ID
            **kwargs: Additional parameters for direct execution (query, mode, etc.)
        """
        if self.direct_mode and kwargs:
            # Direct mode with all required parameters - try to start immediately
            session_id = kwargs.get("session_id")
            if session_id:
                # Check if we can start it directly
                password = session_password_store.get_session_password(
                    username, session_id
                )
                if password:
                    try:
                        # Open database and check active count
                        engine = db_manager.open_user_database(
                            username, password
                        )
                        if engine:
                            with get_user_db_session(username) as db_session:
                                # Count active researches
                                active_count = (
                                    db_session.query(UserActiveResearch)
                                    .filter_by(
                                        username=username, status="in_progress"
                                    )
                                    .count()
                                )

                                if active_count < self.max_concurrent_per_user:
                                    # We have slots - start directly!
                                    logger.info(
                                        f"Direct mode: Starting research {research_id} immediately "
                                        f"(active: {active_count}/{self.max_concurrent_per_user})"
                                    )

                                    # Start the research directly
                                    self._start_research_directly(
                                        username,
                                        research_id,
                                        password,
                                        **kwargs,
                                    )
                                    return
                                else:
                                    logger.info(
                                        f"Direct mode: Max concurrent reached ({active_count}/"
                                        f"{self.max_concurrent_per_user}), queueing {research_id}"
                                    )
                    except Exception:
                        logger.exception(
                            f"Error in direct execution for {username}"
                        )

        # Fall back to queue mode (or if direct mode failed)
        # Note: QueueManager should have already pushed to Redis
        # We just log here
        logger.info(f"Research {research_id} queued for user {username}")

    def _start_research_directly(
        self, username: str, research_id: str, password: str, **kwargs
    ):
        """
        Start a research directly without queueing.

        Args:
            username: The username
            research_id: The research ID
            password: The user's password
            **kwargs: Research parameters (query, mode, settings, etc.)
        """
        query = kwargs.get("query")
        mode = kwargs.get("mode")
        settings_snapshot = kwargs.get("settings_snapshot", {})

        # Create active research record
        try:
            with get_user_db_session(username) as db_session:
                active_record = UserActiveResearch(
                    username=username,
                    research_id=research_id,
                    status="in_progress",
                    thread_id="pending",
                    settings_snapshot=settings_snapshot,
                )
                db_session.add(active_record)
                db_session.commit()

                # Update task status if it exists
                queue_service = UserQueueService(db_session)
                queue_service.update_task_status(research_id, "processing")
        except Exception:
            logger.exception(
                f"Failed to create active research record for {research_id}"
            )
            return

        # Extract parameters from kwargs
        model_provider = kwargs.get("model_provider")
        model = kwargs.get("model")
        custom_endpoint = kwargs.get("custom_endpoint")
        search_engine = kwargs.get("search_engine")

        # Start the research process
        try:
            research_thread = start_research_process(
                research_id,
                query,
                mode,
                active_research,
                termination_flags,
                run_research_process,
                username=username,
                user_password=password,
                model_provider=model_provider,
                model=model,
                custom_endpoint=custom_endpoint,
                search_engine=search_engine,
                max_results=kwargs.get("max_results"),
                time_period=kwargs.get("time_period"),
                iterations=kwargs.get("iterations"),
                questions_per_iteration=kwargs.get("questions_per_iteration"),
                strategy=kwargs.get("strategy", "source-based"),
                settings_snapshot=settings_snapshot,
            )

            # Update thread ID
            try:
                with get_user_db_session(username) as db_session:
                    active_record = (
                        db_session.query(UserActiveResearch)
                        .filter_by(username=username, research_id=research_id)
                        .first()
                    )
                    if active_record:
                        active_record.thread_id = str(research_thread.ident)
                        db_session.commit()
            except Exception:
                logger.exception(
                    f"Failed to update thread ID for {research_id}"
                )

            logger.info(
                f"Direct execution: Started research {research_id} for user {username} "
                f"in thread {research_thread.ident}"
            )

        except Exception:
            logger.exception(f"Failed to start research {research_id} directly")
            # Clean up the active record
            try:
                with get_user_db_session(username) as db_session:
                    active_record = (
                        db_session.query(UserActiveResearch)
                        .filter_by(username=username, research_id=research_id)
                        .first()
                    )
                    if active_record:
                        db_session.delete(active_record)
                        db_session.commit()
            except Exception:
                pass

    def notify_research_completed(self, username: str, research_id: str):
        """
        Notify that a research completed.
        Updates the user's queue status in their database.
        """
        try:
            with get_user_db_session(username) as session:
                queue_service = UserQueueService(session)
                queue_service.update_task_status(research_id, "completed")
                logger.info(
                    f"Research {research_id} completed for user {username}"
                )
        except Exception:
            logger.exception(
                f"Failed to update completion status for {username}"
            )

    def _redis_subscriber_loop(self):
        """Listen for Redis pub/sub notifications"""
        logger.info("Starting Redis subscriber loop")
        for message in redis_manager.subscribe_to_tasks():
            if not self.running:
                break
            
            username = message.get("username")
            if username:
                # We need a session ID to process the queue.
                # This is a limitation: we can only process if we have a cached password.
                # We'll try to find any active session for this user.
                # For now, we'll rely on the periodic check or the user's next request
                # to pick up the task if we can't find a session.
                
                # However, if we have active users in our check list, we can trigger them.
                with self._users_lock:
                    # Check if we have any session for this user in our check list
                    for user_session in self._users_to_check:
                        if user_session.startswith(f"{username}:"):
                            # Already scheduled to check
                            break
                    else:
                        # Not scheduled. We can't easily schedule without session ID.
                        # But we can log it.
                        logger.debug(f"Received Redis notification for {username}")

    def _process_queue_loop(self):
        """Main loop that processes the queue."""
        while self.running:
            try:
                # Get list of users to check
                with self._users_lock:
                    users_to_check = list(self._users_to_check)
                    # Don't clear immediately, only clear those we successfully process?
                    # Or clear and re-add if needed.
                    self._users_to_check.clear()

                # Process each user's queue
                for user_session in users_to_check:
                    try:
                        username, session_id = user_session.split(":", 1)
                        self._process_user_queue(username, session_id)
                    except Exception:
                        logger.exception(
                            f"Error processing queue for {user_session}"
                        )
                        
                # Re-add users who still have active tasks or queued items?
                # For now, we rely on them being re-added by activity or polling.

            except Exception:
                logger.exception("Error in queue processor loop")

            time.sleep(self.check_interval)

    def _process_user_queue(self, username: str, session_id: str):
        """
        Process the queue for a specific user.

        Args:
            username: The username
            session_id: The Flask session ID
        """
        # Get the user's password from session store
        password = session_password_store.get_session_password(
            username, session_id
        )
        if not password:
            logger.debug(
                f"No password available for user {username}, skipping queue check"
            )
            return

        # Open the user's encrypted database
        try:
            # First ensure the database is open
            engine = db_manager.open_user_database(username, password)
            if not engine:
                logger.error(f"Failed to open database for user {username}")
                return

            # Get a session and process the queue
            with get_user_db_session(username) as db_session:
                queue_service = UserQueueService(db_session)

                # Get queue status (active tasks)
                # We only care about active tasks to know if we have slots
                active_count = (
                    db_session.query(UserActiveResearch)
                    .filter_by(username=username, status="in_progress")
                    .count()
                )

                # Calculate available slots
                available_slots = (
                    self.max_concurrent_per_user - active_count
                )

                if available_slots <= 0:
                    return

                # Check Redis queue first
                redis_count = redis_manager.get_queue_length(username)
                
                # Check DB queue (fallback)
                db_queued_count = (
                    db_session.query(QueuedResearch)
                    .filter_by(username=username, is_processing=False)
                    .count()
                )

                if redis_count == 0 and db_queued_count == 0:
                    return

                logger.info(
                    f"Processing queue for {username}: "
                    f"{active_count} active, "
                    f"{redis_count} in Redis, {db_queued_count} in DB, "
                    f"{available_slots} slots available"
                )

                # Process queued researches
                self._start_queued_researches(
                    db_session,
                    queue_service,
                    username,
                    password,
                    available_slots,
                )
                
                # If we processed tasks, we should check this user again soon
                # to keep the pipeline full
                self.notify_user_activity(username, session_id)

        except Exception:
            logger.exception(f"Error processing queue for user {username}")

    def _start_queued_researches(
        self,
        db_session,
        queue_service: UserQueueService,
        username: str,
        password: str,
        available_slots: int,
    ):
        """Start queued researches up to available slots."""
        
        slots_used = 0
        
        # 1. Try Redis first
        while slots_used < available_slots:
            task = redis_manager.dequeue_research(username)
            if not task:
                break
                
            try:
                self._start_redis_task(db_session, username, password, task)
                slots_used += 1
            except Exception:
                logger.exception(f"Failed to start Redis task for {username}")
                # Don't increment slots_used so we try next one
        
        # 2. Fallback to DB if we still have slots
        if slots_used < available_slots:
            remaining_slots = available_slots - slots_used
            
            queued = (
                db_session.query(QueuedResearch)
                .filter_by(username=username, is_processing=False)
                .order_by(QueuedResearch.position)
                .limit(remaining_slots)
                .all()
            )

            for queued_research in queued:
                try:
                    # Mark as processing
                    queued_research.is_processing = True
                    db_session.commit()

                    # Update task status
                    queue_service.update_task_status(
                        queued_research.research_id, "processing"
                    )

                    # Start the research
                    self._start_research(
                        db_session,
                        username,
                        password,
                        queued_research,
                    )

                    # Remove from queue
                    db_session.delete(queued_research)
                    db_session.commit()

                    logger.info(
                        f"Started DB queued research {queued_research.research_id} "
                        f"for user {username}"
                    )
                    slots_used += 1

                except Exception:
                    logger.exception(
                        f"Error starting queued research {queued_research.research_id}"
                    )
                    # Reset processing flag
                    queued_research.is_processing = False
                    db_session.commit()

                    # Update task status
                    queue_service.update_task_status(
                        queued_research.research_id,
                        "failed",
                        error_message="Failed to start research",
                    )

    def _start_redis_task(self, db_session, username, password, task):
        """Start a task dequeued from Redis"""
        research_id = task.get("research_id")
        logger.info(f"Starting Redis task {research_id} for {username}")
        
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
        
        # Extract settings
        settings = task.get("settings", {})
        # Handle nested settings if present
        if "submission" in settings:
            submission_params = settings["submission"]
            complete_settings = settings.get("settings_snapshot", {})
        else:
            submission_params = settings
            complete_settings = {}
            
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
            model_provider=submission_params.get("model_provider"),
            model=submission_params.get("model"),
            custom_endpoint=submission_params.get("custom_endpoint"),
            search_engine=submission_params.get("search_engine"),
            max_results=submission_params.get("max_results"),
            time_period=submission_params.get("time_period"),
            iterations=submission_params.get("iterations"),
            questions_per_iteration=submission_params.get("questions_per_iteration"),
            strategy=submission_params.get("strategy", "source-based"),
            settings_snapshot=complete_settings,
        )
        
        # Update thread ID
        active_record.thread_id = str(research_thread.ident)
        db_session.commit()
        
        # Update status in DB if record exists (it should)
        try:
            queue_service = UserQueueService(db_session)
            queue_service.update_task_status(research_id, "processing")
        except Exception:
            pass

    def _start_research(
        self,
        db_session,
        username: str,
        password: str,
        queued_research,
    ):
        """Start a queued research (from DB)."""
        # Update research status
        research = (
            db_session.query(ResearchHistory)
            .filter_by(id=queued_research.research_id)
            .first()
        )

        if not research:
            raise ValueError(
                f"Research {queued_research.research_id} not found"
            )

        research.status = "in_progress"
        db_session.commit()

        # Create active research record
        active_record = UserActiveResearch(
            username=username,
            research_id=queued_research.research_id,
            status="in_progress",
            thread_id="pending",
            settings_snapshot=queued_research.settings_snapshot,
        )
        db_session.add(active_record)
        db_session.commit()

        # Extract settings
        settings_snapshot = queued_research.settings_snapshot or {}

        # Handle new vs legacy structure
        if (
            isinstance(settings_snapshot, dict)
            and "submission" in settings_snapshot
        ):
            submission_params = settings_snapshot.get("submission", {})
            complete_settings = settings_snapshot.get("settings_snapshot", {})
        else:
            submission_params = settings_snapshot
            complete_settings = {}

        # Start the research process with password
        research_thread = start_research_process(
            queued_research.research_id,
            queued_research.query,
            queued_research.mode,
            active_research,
            termination_flags,
            run_research_process,
            username=username,
            user_password=password,  # Pass password for metrics
            model_provider=submission_params.get("model_provider"),
            model=submission_params.get("model"),
            custom_endpoint=submission_params.get("custom_endpoint"),
            search_engine=submission_params.get("search_engine"),
            max_results=submission_params.get("max_results"),
            time_period=submission_params.get("time_period"),
            iterations=submission_params.get("iterations"),
            questions_per_iteration=submission_params.get(
                "questions_per_iteration"
            ),
            strategy=submission_params.get("strategy", "source-based"),
            settings_snapshot=complete_settings,
        )

        # Update thread ID
        active_record.thread_id = str(research_thread.ident)
        db_session.commit()

    def process_user_request(self, username: str, session_id: str) -> int:
        """
        Process queue for a user during their request.
        This is called from request context to check and start queued items.

        Returns:
            Number of researches started
        """
        try:
            # Add user to check list
            self.notify_user_activity(username, session_id)

            # Force immediate check (don't wait for loop)
            password = session_password_store.get_session_password(
                username, session_id
            )
            if password:
                # Open database and check queue
                engine = db_manager.open_user_database(username, password)
                if engine:
                    with get_user_db_session(username) as db_session:
                        queue_service = UserQueueService(db_session)
                        
                        # Check Redis first
                        redis_count = redis_manager.get_queue_length(username)
                        if redis_count > 0:
                            # Trigger processing
                            self._process_user_queue(username, session_id)
                            return redis_count
                            
                        # Check DB
                        status = queue_service.get_queue_status()
                        if status and status["queued_tasks"] > 0:
                            logger.info(
                                f"User {username} has {status['queued_tasks']} "
                                f"queued tasks, triggering immediate processing"
                            )
                            # Process will happen in background thread
                            return status["queued_tasks"]

            return 0

        except Exception:
            logger.exception(f"Error in process_user_request for {username}")
            return 0


    def _cleanup_loop(self):
        """
        Background loop to clean up stale tasks from Redis queues.
        Runs every CLEANUP_INTERVAL seconds.
        """
        logger.info("Starting queue cleanup loop")
        
        while self.running:
            try:
                if not USE_REDIS_QUEUE:
                    time.sleep(CLEANUP_INTERVAL)
                    continue
                    
                logger.debug("Running queue cleanup scan...")
                
                # Get all users with queues
                users = redis_manager.get_all_users_with_queues()
                
                now = datetime.now(UTC)
                removed_count = 0
                
                for username in users:
                    try:
                        # Get all tasks for user
                        tasks = redis_manager.get_all_queued_tasks(username)
                        
                        for task in tasks:
                            created_at_str = task.get("created_at")
                            if not created_at_str:
                                continue
                                
                            try:
                                created_at = datetime.fromisoformat(created_at_str)
                                if created_at.tzinfo is None:
                                    created_at = created_at.replace(tzinfo=UTC)
                                    
                                age_seconds = (now - created_at).total_seconds()
                                
                                if age_seconds > QUEUE_TASK_TIMEOUT:
                                    research_id = task.get("research_id")
                                    logger.info(f"Removing stale task {research_id} for {username} (age: {age_seconds}s)")
                                    
                                    # Remove from Redis
                                    redis_manager.remove_from_queue(username, research_id)
                                    removed_count += 1
                                    
                                    # NOTE: We cannot easily clean up the database record here because
                                    # the user's database is encrypted and we might not have their password
                                    # (session_id) available in this background thread context.
                                    #
                                    # The "Lazy Migration" logic in _process_user_queue will handle
                                    # marking DB records as expired when the user eventually logs in
                                    # and their queue is processed.
                                    
                            except ValueError:
                                logger.warning(f"Invalid timestamp in task: {created_at_str}")
                                
                    except Exception as e:
                        logger.error(f"Error cleaning queue for {username}: {e}")
                
                if removed_count > 0:
                    logger.info(f"Cleanup scan complete. Removed {removed_count} stale tasks.")
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
            
            # Sleep for cleanup interval
            time.sleep(CLEANUP_INTERVAL)

# Global queue processor instance
queue_processor = QueueProcessorV2()
