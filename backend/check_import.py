try:
    import ddgs
    print(f"Successfully imported ddgs. Version: {ddgs.__version__}")
except ImportError as e:
    print(f"Failed to import ddgs: {e}")

try:
    from duckduckgo_search import DDGS
    print("Successfully imported DDGS from duckduckgo_search")
except ImportError as e:
    print(f"Failed to import DDGS from duckduckgo_search: {e}")
