from app.auth.key_utils import (
    generate_api_key,
    hash_api_key,
    key_prefix,
    mask_api_key,
    verify_api_key,
)


def test_generated_keys_keep_the_public_format():
    key = generate_api_key()

    assert key.startswith("ts_")
    assert len(key) == 35
    assert key_prefix(key) == key[:10]


def test_hashes_verify_without_exposing_the_plaintext():
    key = generate_api_key()
    digest = hash_api_key(key)

    assert digest != key
    assert verify_api_key(key, digest)
    assert not verify_api_key("ts_wrong", digest)
    assert mask_api_key(key).startswith("ts_")
    assert mask_api_key(key).endswith(f"...{key[-4:]}")
