import pytest
from pydantic import ValidationError

from app.models.api_models import LensRequest, SearchRequest


def test_search_request_has_safe_bounds():
    request = SearchRequest(query="machine learning", num_results=20, n_queries=2)

    assert request.num_results == 20
    assert request.n_queries == 2


@pytest.mark.parametrize(
    "payload",
    [
        {"query": ""},
        {"query": "ok", "num_results": 0},
        {"query": "ok", "num_results": 101},
        {"query": "ok", "unexpected": True},
    ],
)
def test_search_request_rejects_invalid_input(payload):
    with pytest.raises(ValidationError):
        SearchRequest.model_validate(payload)


def test_nested_research_settings_are_validated():
    request = LensRequest.model_validate(
        {"query": "an evidence-backed question", "settings": {"max_results": 10}}
    )

    assert request.settings.max_results == 10
