#!/usr/bin/env python3
"""Check environment variables for LLM configuration"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=== Environment Variables Check ===\n")

# Check Gemini
gemini_key = os.getenv("LDR_LLM_GEMINI_API_KEY")
print(f"✓ LDR_LLM_GEMINI_API_KEY: {'SET' if gemini_key else 'NOT SET'}")
if gemini_key:
    print(f"  Value: {gemini_key[:20]}...{gemini_key[-4:]}")

# Check OpenAI (should NOT be set)
openai_keys = [
    "LDR_LLM_OPENAI_API_KEY",
    "OPENAI_API_KEY",
    "LDR_LLM_API_KEY",
]

print("\n=== OpenAI Keys (should be EMPTY) ===")
for key in openai_keys:
    value = os.getenv(key)
    if value:
        print(f"⚠️  {key}: {value[:20]}... (THIS SHOULD NOT BE SET!)")
    else:
        print(f"✓ {key}: Not set (good!)")

# Check Model config
print("\n=== Model Configuration ===")
print(f"LDR_LLM_MODEL: {os.getenv('LDR_LLM_MODEL', 'NOT SET')}")
print(f"LDR_LLM_MAX_TOKENS: {os.getenv('LDR_LLM_MAX_TOKENS', 'NOT SET')}")
print(f"USE_MODEL: {os.getenv('USE_MODEL', 'NOT SET')}")

print("\n=== Summary ===")
if gemini_key and not any(os.getenv(k) for k in openai_keys):
    print("✅ Configuration looks good! Using Gemini.")
elif gemini_key:
    print("⚠️  WARNING: OpenAI keys are set. These will override Gemini!")
    print("   Remove OpenAI keys from your .env file.")
else:
    print("❌ ERROR: No Gemini API key found!")
    print("   Set LDR_LLM_GEMINI_API_KEY in your .env file.")

