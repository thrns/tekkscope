"""
Database encryption and performance settings.

NOTE:# Database settings
# These can be overridden by TEKK_DB_* environment variables only,
as they cannot be changed after database creation.

Environment variables:
- LDR_DB_JOURNAL_MODE: Journal mode (default: WAL)
- LDR_DB_SYNCHRONOUS: Synchronous mode (default: NORMAL)
- LDR_DB_HMAC_ALGORITHM: HMAC algorithm (default: HMAC_SHA512)
- LDR_DB_KDF_ALGORITHM: KDF algorithm (default: PBKDF2_HMAC_SHA512)
"""

# Empty list since all database settings are now environment-only
database_settings = []
