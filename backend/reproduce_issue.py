
import os
import sys
import logging
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="DEBUG")

# Add project root to path
sys.path.append(os.getcwd())

from app.research_lib.web_search_engines.search_engine_factory import create_search_engine
from app.research_lib.config.llm_config import get_llm

import json

def load_default_settings():
    with open("app/research_lib/defaults/default_settings.json", "r") as f:
        return json.load(f)

def test_meta_engine():
    logger.info("Starting test...")
    
    # Load default settings
    try:
        settings_snapshot = load_default_settings()
    except Exception as e:
        logger.error(f"Failed to load default settings: {e}")
        return

    # Override specific values
    if "search.tool" in settings_snapshot:
        settings_snapshot["search.tool"]["value"] = "auto"
    
    if "llm.gemini.api_key" in settings_snapshot:
        settings_snapshot["llm.gemini.api_key"]["value"] = os.getenv("TEKK_LLM_GEMINI_API_KEY", "dummy_key")
        
    # Ensure DDG is enabled in the snapshot (it should be from default_settings.json now)
    if "search.engine.web.duckduckgo.use_in_auto_search" in settings_snapshot:
        logger.info(f"DDG use_in_auto_search: {settings_snapshot['search.engine.web.duckduckgo.use_in_auto_search']['value']}")
    else:
        logger.warning("DDG settings not found in snapshot!")
        
    # Ensure Guardian settings are correct (they should be in default_settings.json now)
    # But just in case, we can log them
    logger.info(f"Guardian config: {settings_snapshot.get('search.engine.web.guardian.class_name')}")

    logger.info("Getting LLM...")
    try:
        llm = get_llm(model_name="gemini-2.0-flash", provider="gemini", settings_snapshot=settings_snapshot)
        logger.info(f"Got LLM: {llm}")
    except Exception as e:
        logger.error(f"Failed to get LLM: {e}")
        return

    logger.info("Creating MetaSearchEngine...")
    try:
        engine = create_search_engine(
            "auto",
            llm=llm,
            settings_snapshot=settings_snapshot
        )
        logger.info(f"Created engine: {engine}")
    except Exception as e:
        logger.exception(f"Failed to create engine: {e}")

if __name__ == "__main__":
    test_meta_engine()
