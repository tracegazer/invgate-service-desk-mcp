import httpx
import pytest
import respx

from invgate_service_desk_mcp.client import InvGateClient
from invgate_service_desk_mcp.config import Config
from invgate_service_desk_mcp.domains import organization as org

BASE = "https://acme.sd.cloud.invgate.net"
API = f"{BASE}/api/v1"


@pytest.fixture
async def client():
    c = InvGateClient(Config(base_url=BASE, api_token="tok"))
    yield c
    await c.aclose()


@respx.mock
async def test_list_helpdesks_filters(client):
    route = respx.get(f"{API}/helpdesks").mock(
        return_value=httpx.Response(200, json=[{"id": 2, "name": "IT"}])
    )

    result = await org.list_helpdesks(client, helpdesk_id=2, include_deleted=True)

    assert result == [{"id": 2, "name": "IT"}]
    assert dict(route.calls.last.request.url.params) == {"id": "2", "include_deleted": "true"}


@respx.mock
async def test_list_helpdesks_no_filter(client):
    route = respx.get(f"{API}/helpdesks").mock(return_value=httpx.Response(200, json=[]))

    await org.list_helpdesks(client)

    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
async def test_list_helpdesk_levels_by_id(client):
    route = respx.get(f"{API}/levels").mock(return_value=httpx.Response(200, json=[]))

    await org.list_helpdesk_levels(client, level_id=5)

    assert dict(route.calls.last.request.url.params) == {"id": "5"}


@respx.mock
async def test_list_helpdesks_and_levels_by_id(client):
    route = respx.get(f"{API}/helpdesksandlevels").mock(
        return_value=httpx.Response(200, json=[])
    )

    await org.list_helpdesks_and_levels(client, helpdesk_id=2)

    assert dict(route.calls.last.request.url.params) == {"id": "2"}


@respx.mock
async def test_list_helpdesk_observers_encodes_ids(client):
    route = respx.get(f"{API}/helpdesks.observers").mock(
        return_value=httpx.Response(200, json=[])
    )

    await org.list_helpdesk_observers(client, ids=[2, 3])

    assert route.calls.last.request.url.params.get_list("ids[]") == ["2", "3"]


@respx.mock
async def test_list_level_observers_no_filter(client):
    route = respx.get(f"{API}/levels.observers").mock(
        return_value=httpx.Response(200, json=[])
    )

    await org.list_level_observers(client)

    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
async def test_list_locations_by_id(client):
    route = respx.get(f"{API}/locations").mock(
        return_value=httpx.Response(200, json=[{"id": 108, "name": "HQ"}])
    )

    result = await org.list_locations(client, location_id=108)

    assert result == [{"id": 108, "name": "HQ"}]
    assert dict(route.calls.last.request.url.params) == {"id": "108"}


@respx.mock
async def test_list_location_members(client):
    route = respx.get(f"{API}/locations.users").mock(
        return_value=httpx.Response(200, json=[{"id": 5, "username": "ada"}])
    )

    await org.list_location_members(client, location_id=108, user_id=5)

    assert dict(route.calls.last.request.url.params) == {"id": "108", "user_id": "5"}


@respx.mock
async def test_list_location_observers_encodes_ids(client):
    route = respx.get(f"{API}/locations.observers").mock(
        return_value=httpx.Response(200, json=[])
    )

    await org.list_location_observers(client, ids=[1])

    assert route.calls.last.request.url.params.get_list("ids[]") == ["1"]


@respx.mock
async def test_list_company_members(client):
    route = respx.get(f"{API}/companies.users").mock(
        return_value=httpx.Response(200, json=[{"id": 5}])
    )

    await org.list_company_members(client, company_id=76, user_id=5)

    assert dict(route.calls.last.request.url.params) == {"id": "76", "user_id": "5"}


@respx.mock
async def test_list_company_groups(client):
    route = respx.get(f"{API}/companies.groups").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "name": "Support"}])
    )

    result = await org.list_company_groups(client, company_id=76)

    assert result == [{"id": 1, "name": "Support"}]
    assert dict(route.calls.last.request.url.params) == {"id": "76"}


@respx.mock
async def test_list_company_observers_no_filter(client):
    route = respx.get(f"{API}/companies.observers").mock(
        return_value=httpx.Response(200, json=[])
    )

    await org.list_company_observers(client)

    assert dict(route.calls.last.request.url.params) == {}
