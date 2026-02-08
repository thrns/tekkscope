import os
import json
import logging

# Default rates (USD per 1M tokens)
# Key: (provider, model) -> Value: (input_price, output_price)
# Prices are in USD.
RATES: dict[tuple[str, str], tuple[float, float]] = {
    # OpenAI
    ("OPENAI", "gpt-4o-mini"): (0.15, 0.60),
    ("OPENAI", "gpt-4o"): (2.50, 10.00),
    
    # Gemini
    ("GEMINI", "gemini-2.0-flash"): (0.10, 0.40),
    ("GEMINI", "gemini-2.0-pro"): (0.10, 0.40), # Placeholder, verify if needed
    
    # Tekkscope Models (USD per 1M tokens)
    ("TEKKSCOPE", "lens"): (0.45, 1.34),
    ("TEKKSCOPE", "deeplens"): (1.00, 3.01),
    ("TEKKSCOPE", "reportlens"): (2.01, 4.46),
    ("TEKKSCOPE", "tek_pro"): (0.12, 0.48), # Tekk Chat Model
    
    # Scraper
    ("SCRAPER", "crawler"): (float(os.getenv("SCRAPER_PRICE_PER_1K", "0.001")) * 1000, 0.0), # Normalize to per 1M
}

def _load_overrides():
    """
    Load overrides from CREDIT_RATE_OVERRIDES environment variable.
    Expected format: JSON object with keys like "PROVIDER/MODEL" or "PROVIDER|MODEL".
    Value should be a list or tuple: [input_price, output_price]
    Example: '{"OPENAI/gpt-4o": [2.50, 10.00]}'
    """
    overrides_str = os.getenv("CREDIT_RATE_OVERRIDES")
    if overrides_str:
        try:
            overrides = json.loads(overrides_str)
            for key, value in overrides.items():
                provider: str | None = None
                model: str | None = None
                
                if "|" in key:
                    provider, model = key.split("|", 1)
                elif "/" in key:
                    provider, model = key.split("/", 1)
                elif ":" in key:
                    provider, model = key.split(":", 1)
                
                if provider and model:
                    if isinstance(value, (list, tuple)) and len(value) == 2:
                        RATES[(provider.upper(), model)] = (float(value[0]), float(value[1]))
                    else:
                        # Backwards compatibility for single float (assume symmetric or old style)
                        # Treating as input=value, output=value for safety, or just log warning
                        val = float(value)
                        RATES[(provider.upper(), model)] = (val, val)
        except Exception as e:
            logging.error(f"Failed to load CREDIT_RATE_OVERRIDES: {e}")

_load_overrides()

def get_rates(provider: str | None, model: str | None) -> tuple[float, float]:
    """
    Get the (input_rate, output_rate) for a given provider and model.
    Rates are in USD per 1M tokens.
    """
    default_rate = (0.10, 0.40) # Default to Flash rates
    
    if not provider:
        return default_rate

    prov_upper = provider.upper()
    
    # Check exact match
    if model and (prov_upper, model) in RATES:
        return RATES[(prov_upper, model)]
    
    # Check lowercased model
    if model and (prov_upper, model.lower()) in RATES:
        return RATES[(prov_upper, model.lower())]
        
    return default_rate

def compute_credits_used(input_tokens: int, output_tokens: int, provider: str | None, model: str | None) -> float:
    """
    Compute the credits used based on input/output tokens and rates.
    Returns cost in USD.
    """
    input_rate, output_rate = get_rates(provider, model)
    
    input_cost = (max(0, input_tokens) / 1_000_000) * input_rate
    output_cost = (max(0, output_tokens) / 1_000_000) * output_rate
    
    return round(input_cost + output_cost, 6)
