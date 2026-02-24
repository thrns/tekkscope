import sys
import os

# Add project root to path
sys.path.append("/Users/atheebhusssain/Desktop/TEKKSCOPE_MONO/tekkscope")

try:
    import app.routers.tek
    print("Successfully imported app.routers.tek")
except Exception as e:
    print(f"Error importing app.routers.tek: {e}")


try:
    import app.routers.deeplens
    print("Successfully imported app.routers.deeplens")
except Exception as e:
    print(f"Error importing app.routers.deeplens: {e}")

try:
    import app.routers.lens
    print("Successfully imported app.routers.lens")
except Exception as e:
    print(f"Error importing app.routers.lens: {e}")

try:
    import app.routers.reportlens
    print("Successfully imported app.routers.reportlens")
except Exception as e:
    print(f"Error importing app.routers.reportlens: {e}")

try:
    import app.clients.scraper
    print("Successfully imported app.clients.scraper")
except Exception as e:
    print(f"Error importing app.clients.scraper: {e}")

try:
    import app.clients.tek_client
    print("Successfully imported app.clients.tek_client")
except Exception as e:
    print(f"Error importing app.clients.tek_client: {e}")
