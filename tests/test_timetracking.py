"""Tests for the time tracking domain (Phase 8).

Read tools list entries (by request or by interval) and categories. Write tools
(log/delete) are gated behind opt-in. Note the API's date asymmetry: the GET
filter uses ISO-8601 strings, but the POST logs ``from``/``to`` as epoch
timestamps (INTEGER).
"""

import httpx
import pytest
import respx

from invgate_service_desk_mcp.client import InvGateClient
from invgate_service_desk_mcp.config import Config
from invgate_service_desk_mcp.domains import timetracking

BASE = "https://acme.sd.cloud.invgate.net"
API = f"{BASE}/api/v1"


@pytest.fixture
async def client():
    c = InvGateClient(Config(base_url=BASE, api_token="tok"))
    yield c
    await c.aclose()


def form(route):
    return bytes(route.calls.last.request.content).decode()


# --- Read operations --------------------------------------------------------


@respx.mock
async def test_list_time_tracking_by_request_id(client):
    payload = [{"timetracking_id": 1, "incident": 100, "total": "3600"}]
    route = respx.get(f"{API}/timetracking").mock(
        return_value=httpx.Response(200, json=payload)
    )

    result = await timetracking.list_time_tracking(client, request_id=100)

    assert result == payload
    assert dict(route.calls.last.request.url.params) == {"request_id": "100"}


@respx.mock
async def test_list_time_tracking_by_interval(client):
    route = respx.get(f"{API}/timetracking").mock(
        return_value=httpx.Response(200, json=[])
    )

    await timetracking.list_time_tracking(
        client,
        from_date="2026-06-01 00:00",
        to_date="2026-06-02 00:00",
        date_format="iso8601",
    )

    params = dict(route.calls.last.request.url.params)
    assert params == {
        "from": "2026-06-01 00:00",
        "to": "2026-06-02 00:00",
        "date_format": "iso8601",
    }


async def test_list_time_tracking_requires_request_or_from(client):
    with pytest.raises(ValueError, match="request_id"):
        await timetracking.list_time_tracking(client)


@respx.mock
async def test_list_time_tracking_categories_takes_no_params(client):
    payload = [{"id": 1, "name": "Support", "cost_per_hour": 50.0}]
    route = respx.get(f"{API}/timetracking.attributes.category").mock(
        return_value=httpx.Response(200, json=payload)
    )

    result = await timetracking.list_time_tracking_categories(client)

    assert result == payload
    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
async def test_list_time_tracking_categories_by_id(client):
    route = respx.get(f"{API}/timetracking.attributes.category").mock(
        return_value=httpx.Response(200, json=[{"id": 7}])
    )

    await timetracking.list_time_tracking_categories(client, category_id=7)

    assert dict(route.calls.last.request.url.params) == {"id": "7"}


# --- Write operations (opt-in) ----------------------------------------------


@respx.mock
async def test_log_time_posts_form_with_mapped_dates(client):
    route = respx.post(f"{API}/timetracking").mock(
        return_value=httpx.Response(200, json={"status": "OK", "timetracking_id": 55})
    )

    result = await timetracking.log_time(
        client,
        request_id=100,
        user_id=18,
        to_timestamp=1780000000,
        from_timestamp=1779996400,
        category_id=3,
        comment="on call",
    )

    assert result == {"status": "OK", "timetracking_id": 55}
    body = form(route)
    for token in (
        "request_id=100",
        "user_id=18",
        "to=1780000000",
        "from=1779996400",
        "category_id=3",
        "comment=on+call",
    ):
        assert token in body


@respx.mock
async def test_log_time_minimal_required_only(client):
    route = respx.post(f"{API}/timetracking").mock(
        return_value=httpx.Response(200, json={"status": "OK", "timetracking_id": 56})
    )

    await timetracking.log_time(client, request_id=100, user_id=18, to_timestamp=1780000000)

    body = form(route)
    assert "request_id=100" in body and "user_id=18" in body and "to=1780000000" in body
    # Optional params omitted entirely (client drops None values).
    assert "category_id" not in body and "from=" not in body and "comment" not in body


@respx.mock
async def test_delete_time_entry_uses_query_params(client):
    route = respx.delete(f"{API}/timetracking").mock(
        return_value=httpx.Response(200, json={"status": "OK"})
    )

    result = await timetracking.delete_time_entry(
        client, request_id=100, timetracking_id=55, user_id=18
    )

    assert result == {"status": "OK"}
    assert dict(route.calls.last.request.url.params) == {
        "request_id": "100",
        "timetracking_id": "55",
        "user_id": "18",
    }
