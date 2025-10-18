"""
Migration utility to move queued tasks from Database to Redis.
"""

from datetime import datetime, UTC
from loguru import logger
from sqlalchemy.orm import sessionmaker

from ...database.encrypted_db import db_manager
from ...database.models import QueuedResearch, ResearchHistory
from .redis_manager import redis_manager
from ...config.queue_config import QUEUE_TASK_TIMEOUT

def migrate_db_queue_to_redis(username: str, password: str) -> int:
    """
    Migrate queued tasks from DB to Redis for a specific user.
    
    Args:
        username: The username
        password: The user's password (needed to open DB)
        
    Returns:
        int: Number of tasks migrated
    """
    try:
        # Open database
        engine = db_manager.open_user_database(username, password)
        if not engine:
            logger.error(f"Could not open database for migration: {username}")
            return 0
            
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        migrated_count = 0
        expired_count = 0
        
        try:
            # Get all queued items from DB
            queued_items = (
                session.query(QueuedResearch)
                .filter_by(username=username, is_processing=False)
                .order_by(QueuedResearch.position)
                .all()
            )
            
            if not queued_items:
                return 0
                
            logger.info(f"Found {len(queued_items)} queued items in DB for {username} to migrate")
            
            now = datetime.now(UTC)
            
            for item in queued_items:
                # Check for expiration
                if item.created_at:
                    # Ensure item.created_at is timezone-aware or naive as needed
                    # Assuming stored as naive UTC or aware UTC
                    item_time = item.created_at
                    if item_time.tzinfo is None:
                        item_time = item_time.replace(tzinfo=UTC)
                        
                    age_seconds = (now - item_time).total_seconds()
                    
                    if age_seconds > QUEUE_TASK_TIMEOUT:
                        logger.info(f"Task {item.research_id} is expired (age: {age_seconds}s), marking as expired")
                        
                        # Update research history status
                        research = session.query(ResearchHistory).filter_by(id=item.research_id).first()
                        if research:
                            research.status = "error" # Or "expired" if supported, using error for now
                            # Add log entry
                            import json
                            log_entry = {
                                "time": now.isoformat(),
                                "message": "Task expired in queue due to inactivity",
                                "progress": 0,
                                "metadata": {"phase": "queue_expiration"}
                            }
                            if research.progress_log:
                                try:
                                    current_log = research.progress_log if isinstance(research.progress_log, list) else json.loads(research.progress_log)
                                except:
                                    current_log = []
                            else:
                                current_log = []
                            current_log.append(log_entry)
                            research.progress_log = current_log
                        
                        # Remove from queue DB
                        session.delete(item)
                        expired_count += 1
                        continue

                # Push to Redis
                success = redis_manager.enqueue_research(username, item.research_id, {
                    "query": item.query,
                    "mode": item.mode,
                    "settings": item.settings_snapshot,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "migrated": True
                })
                
                if success:
                    # Remove from DB
                    session.delete(item)
                    migrated_count += 1
            
            session.commit()
            logger.info(f"Migration for {username}: {migrated_count} migrated, {expired_count} expired")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error during queue migration for {username}: {e}")
            session.rollback()
            return 0
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Migration failed for {username}: {e}")
        return 0

def migrate_all_active_users():
    """
    Attempt to migrate queues for all active users.
    Note: This is tricky because we need passwords to open encrypted DBs.
    We can only migrate users who have active sessions or whose passwords we have.
    
    In this architecture, we might have to rely on lazy migration:
    Migrate when the user logs in or when we first access their queue.
    """
    # For now, we'll provide the function but it needs to be called with password.
    pass
