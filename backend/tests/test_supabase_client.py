import httpx
import pytest

from app.data.supabase_client import SupabaseDataApi, SupabaseDataError


def test_transport_failures_are_exposed_as_repository_errors() -> None:
    def fail(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline")

    api = SupabaseDataApi("https://example.supabase.co", "test-secret")
    api._client.close()
    api._client = httpx.Client(transport=httpx.MockTransport(fail))

    with pytest.raises(SupabaseDataError, match="could not be reached") as caught:
        api.select("clinics")

    assert caught.value.status_code == 503
