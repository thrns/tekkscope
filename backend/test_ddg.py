import os
import sys
from loguru import logger

# Add the current directory to sys.path
sys.path.append(os.getcwd())

from app.research_lib.web_search_engines.engines.search_engine_ddg import DuckDuckGoSearchEngine

def test_ddg():
    logger.info("Testing DuckDuckGo Search Engine...")
    try:
        engine = DuckDuckGoSearchEngine(max_results=5)
        logger.info("Engine initialized successfully.")
        
        results = engine.run("test query")
        logger.info(f"Search results: {len(results)}")
        for res in results:
            logger.info(f" - {res.get('title', 'No Title')}: {res.get('link', 'No Link')}")
            
    except Exception as e:
        logger.exception(f"DuckDuckGo test failed: {e}")

if __name__ == "__main__":
    test_ddg()
