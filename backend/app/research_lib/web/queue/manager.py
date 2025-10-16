"""Queue manager for handling research queue operations"""

from datetime import datetime
from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

from ...database.encrypted_db import db_manager
from ...database.models import QueuedResearch, ResearchHistory
from .processor_v2 import queue_processor
from .redis_manager import redis_manager


class QueueManager:
    """Manages the research queue operations"""

    @staticmethod
    def add_to_queue(username, research_id, query, mode, settings):
        """
        Add a research to the queue

        Args:
            username: User who owns the research
            research_id: UUID of the research
            query: Research query
            mode: Research mode
            settings: Research settings dictionary

        Returns:
            int: Queue position
        """
        # Try Redis first
        try:
            # Get current length for position estimate
            current_len = redis_manager.get_queue_length(username)
            
            success = redis_manager.enqueue_research(username, research_id, {
                "query": query,
                "mode": mode,
                "settings": settings,
                "created_at": datetime.now().isoformat() # Approximate timestamp
            })
            
            if success:
                # Notify processor (it might be listening on pub/sub, but explicit notify doesn't hurt)
                # queue_processor.notify_research_queued(username, research_id)
                return current_len + 1
                
        except Exception as e:
            logger.error(f"Failed to enqueue to Redis, falling back to DB: {e}")

        # Fallback to Database
        engine = db_manager.connections.get(username)
        if not engine:
            # If we can't connect to DB and Redis failed, we're in trouble
            # But we might not have a DB connection if user not logged in? 
            # Usually this is called from a request where DB is available.
            raise ValueError(f"No database connection for user {username}")

        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        try:
            # Get the next position in queue for this user
            max_position = (
                session.query(func.max(QueuedResearch.position))
                .filter_by(username=username)
                .scalar()
                or 0
            )

            queued_record = QueuedResearch(
                username=username,
                research_id=research_id,
                query=query,
                mode=mode,
                settings_snapshot=settings,
                position=max_position + 1,
            )
            session.add(queued_record)
            session.commit()

            logger.info(
                f"Added research {research_id} to DB queue at position {max_position + 1}"
            )

            # Notify queue processor
            queue_processor.notify_research_queued(username, research_id)

            return max_position + 1

        finally:
            session.close()

    @staticmethod
    def get_queue_position(username, research_id):
        """
        Get the current queue position for a research

        Args:
            username: User who owns the research
            research_id: UUID of the research

        Returns:
            int: Current queue position or None if not in queue
        """
        # Check Redis first
        try:
            tasks = redis_manager.get_all_queued_tasks(username)
            for i, task in enumerate(tasks):
                if task.get("research_id") == research_id:
                    return i + 1
        except Exception as e:
            logger.warning(f"Failed to check Redis queue position: {e}")

        # Check DB
        engine = db_manager.connections.get(username)
        if not engine:
            return None

        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        try:
            queued = (
                session.query(QueuedResearch)
                .filter_by(username=username, research_id=research_id)
                .first()
            )

            if not queued:
                return None

            # Count how many are ahead in queue
            ahead_count = (
                session.query(QueuedResearch)
                .filter(
                    QueuedResearch.username == username,
                    QueuedResearch.position < queued.position,
                )
                .count()
            )
            
            # Add Redis count if we have mixed queues?
            # For simplicity, if it's in DB, we assume it's behind all Redis tasks
            # unless we migrated them.
            redis_count = redis_manager.get_queue_length(username)

            return redis_count + ahead_count + 1

        finally:
            session.close()

    @staticmethod
    def remove_from_queue(username, research_id):
        """
        Remove a research from the queue

        Args:
            username: User who owns the research
            research_id: UUID of the research

        Returns:
            bool: True if removed, False if not found
        """
        # Try Redis
        removed_redis = redis_manager.remove_from_queue(username, research_id)
        if removed_redis:
            return True

        # Try DB
        engine = db_manager.connections.get(username)
        if not engine:
            return False

        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        try:
            queued = (
                session.query(QueuedResearch)
                .filter_by(username=username, research_id=research_id)
                .first()
            )

            if not queued:
                return False

            position = queued.position
            session.delete(queued)

            # Update positions of items behind in queue
            session.query(QueuedResearch).filter(
                QueuedResearch.username == username,
                QueuedResearch.position > position,
            ).update({QueuedResearch.position: QueuedResearch.position - 1})

            session.commit()
            logger.info(f"Removed research {research_id} from DB queue")
            return True

        finally:
            session.close()

    @staticmethod
    def get_user_queue(username):
        """
        Get all queued researches for a user

        Args:
            username: User to get queue for

        Returns:
            list: List of queued research info
        """
        result = []
        
        # Get from Redis
        try:
            redis_tasks = redis_manager.get_all_queued_tasks(username)
            for i, task in enumerate(redis_tasks):
                result.append({
                    "research_id": task.get("research_id"),
                    "query": task.get("query"),
                    "mode": task.get("mode"),
                    "position": i + 1,
                    "created_at": task.get("created_at"),
                    "is_processing": False,
                    "source": "redis"
                })
        except Exception as e:
            logger.error(f"Failed to get Redis queue for {username}: {e}")

        # Get from DB
        engine = db_manager.connections.get(username)
        if not engine:
            return result

        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        try:
            queued_items = (
                session.query(QueuedResearch)
                .filter_by(username=username)
                .order_by(QueuedResearch.position)
                .all()
            )

            redis_count = len(result)
            
            for item in queued_items:
                # Get research info
                research = (
                    session.query(ResearchHistory)
                    .filter_by(id=item.research_id)
                    .first()
                )

                if research:
                    result.append(
                        {
                            "research_id": item.research_id,
                            "query": item.query,
                            "mode": item.mode,
                            "position": redis_count + item.position,
                            "created_at": item.created_at.isoformat()
                            if item.created_at
                            else None,
                            "is_processing": item.is_processing,
                            "source": "database"
                        }
                    )

            return result

        finally:
            session.close()

