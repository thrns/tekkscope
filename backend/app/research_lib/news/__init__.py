"""
LDR News - AI-powered news aggregation and analysis module.
"""

# Try to import database models, fallback to None if not available
try:
    from ..database.models import (
        NewsSubscription as BaseSubscription,
        SubscriptionFolder,
        UserPreference,
        UserRating as Rating,
    )
    _DATABASE_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    _DATABASE_AVAILABLE = False
    # Create placeholder classes
    BaseSubscription = None
    SubscriptionFolder = None
    UserPreference = None
    Rating = None

try:
    from .subscription_manager.scheduler import NewsScheduler, get_news_scheduler
    from .folder_manager import FolderManager
    from .subscription_manager import SearchSubscription, TopicSubscription

    # Import API functions
    from .api import (
        get_news_feed,
        research_news_item,
        save_news_preferences,
        get_news_categories,
    )
except (ImportError, ModuleNotFoundError) as e:
    # If news module dependencies fail, set to None
    NewsScheduler = None
    get_news_scheduler = None
    FolderManager = None
    SearchSubscription = None
    TopicSubscription = None
    get_news_feed = None
    research_news_item = None
    save_news_preferences = None
    get_news_categories = None

__all__ = [
    # Core classes
    "BaseSubscription",
    "SubscriptionFolder",
    "UserPreference",
    "Rating",
    "NewsScheduler",
    "get_news_scheduler",
    "FolderManager",
    "SearchSubscription",
    "TopicSubscription",
    # API functions
    "get_news_feed",
    "research_news_item",
    "save_news_preferences",
    "get_news_categories",
]
