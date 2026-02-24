import os
import sys
import logging
from app.research_lib.web_search_engines.engines.search_engine_searxng import SearXNGSearchEngine

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_searxng():
    print("Testing SearXNGSearchEngine...")
    
    # Use the hosted URL
    instance_url = "https://search.tekkscope.com"
    
    try:
        # Test with float max_results as seen in logs
        engine = SearXNGSearchEngine(
            instance_url=instance_url,
            max_results=50.0  # Passing float to test if this causes issues
        )
        
        queries = [
            "Atheeb Hussain career and achievements",
            "Atheeb Hussain biography and background"
        ]
        
        for query in queries:
            print(f"\nRunning search for: '{query}'")
            results = engine.run(query)
            print(f"Results found: {len(results)}")
            if not results:
                print("WARNING: No results found!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_searxng()
