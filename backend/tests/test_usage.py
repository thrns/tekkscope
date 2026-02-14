from app.utils import usage


class _FakeTable:
    def insert(self, payload):
        self.payload = payload
        return self

    def execute(self):
        return type("Response", (), {"data": [self.payload]})()


class _FakeSupabase:
    def __init__(self):
        self.table_client = _FakeTable()

    def table(self, name):
        assert name == "usage"
        return self.table_client


def test_usage_records_estimated_tokens_and_credit_metadata(monkeypatch):
    fake = _FakeSupabase()
    debits = []
    monkeypatch.setattr(usage, "supabase", fake)
    monkeypatch.setattr(usage, "decrement_credits", lambda user_id, amount: debits.append((user_id, amount)))

    credits = usage.record_usage(
        user_id="user-1",
        api_key_id="key-1",
        service_used="scraper",
        content="A sourced response with useful text.",
        provider="SCRAPER",
        model="crawler",
        input_ratio=0.8,
    )

    payload = fake.table_client.payload
    assert credits > 0
    assert payload["user_id"] == "user-1"
    assert payload["api_token_id"] == "key-1"
    assert payload["token_count_estimated"] is True
    assert payload["input_tokens"] + payload["output_tokens"] >= 1
    assert debits == [("user-1", credits)]
