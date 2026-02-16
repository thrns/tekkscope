import pytest

from app.mcp_server import ToolInputError, _validate_http_url, _validate_url_list


def test_mcp_accepts_absolute_http_urls():
    assert _validate_http_url("https://1.1.1.1/research") == "https://1.1.1.1/research"
    assert _validate_url_list(["http://1.1.1.1", "https://9.9.9.9"])[1].startswith("https://")


@pytest.mark.parametrize(
    "value",
    ["example.com", "file:///etc/passwd", "javascript:alert(1)", ""],
)
def test_mcp_rejects_non_http_urls(value):
    with pytest.raises(ToolInputError):
        _validate_http_url(value)


@pytest.mark.parametrize("value", ["http://localhost:8000", "http://127.0.0.1:8000"])
def test_mcp_rejects_private_targets(value):
    with pytest.raises(ToolInputError, match="public host"):
        _validate_http_url(value)


def test_mcp_caps_url_batches():
    with pytest.raises(ToolInputError, match="more than 50"):
        _validate_url_list(["https://example.com"] * 51)
