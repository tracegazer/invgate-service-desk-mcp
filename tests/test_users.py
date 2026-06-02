import httpx
import pytest
import respx

from invgate_service_desk_mcp.client import InvGateClient
from invgate_service_desk_mcp.config import Config
from invgate_service_desk_mcp.domains import users

BASE = "https://acme.sd.cloud.invgate.net"
API = f"{BASE}/api/v1"


@pytest.fixture
async def client():
    c = InvGateClient(Config(base_url=BASE, api_token="tok"))
    yield c
    await c.aclose()


@respx.mock
async def test_get_user_requests_by_id(client):
    route = respx.get(f"{API}/user").mock(
        return_value=httpx.Response(200, json={"id": 7, "name": "Ada"})
    )

    result = await users.get_user(client, user_id=7)

    assert result == {"id": 7, "name": "Ada"}
    assert dict(route.calls.last.request.url.params) == {"id": "7"}


@respx.mock
async def test_get_user_can_include_disabled(client):
    route = respx.get(f"{API}/user").mock(return_value=httpx.Response(200, json={}))

    await users.get_user(client, user_id=7, include_disabled=True)

    params = dict(route.calls.last.request.url.params)
    assert params == {"id": "7", "include_disabled": "true"}


@respx.mock
async def test_list_users_passes_ids_array(client):
    route = respx.get(f"{API}/users").mock(
        return_value=httpx.Response(200, json=[{"id": 1}, {"id": 2}])
    )

    result = await users.list_users(client, ids=[1, 2])

    assert result == [{"id": 1}, {"id": 2}]
    assert route.calls.last.request.url.params.get_list("ids[]") == ["1", "2"]


@respx.mock
async def test_list_users_without_ids_lists_all(client):
    route = respx.get(f"{API}/users").mock(return_value=httpx.Response(200, json=[]))

    await users.list_users(client)

    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
async def test_find_users_searches_by_email(client):
    # users.by returns a paginated map: {next_page_key, data: {"<id>": {...}}}.
    payload = {"next_page_key": None, "data": {"9": {"id": 9, "email": "ada@acme.com"}}}
    route = respx.get(f"{API}/users.by").mock(return_value=httpx.Response(200, json=payload))

    result = await users.find_users(client, email="ada@acme.com")

    assert result == payload
    assert dict(route.calls.last.request.url.params) == {"email": "ada@acme.com"}


@respx.mock
async def test_find_users_maps_phone_to_phones_and_exact_match(client):
    route = respx.get(f"{API}/users.by").mock(return_value=httpx.Response(200, json=[]))

    await users.find_users(client, phone="+5491155550000", exact_match=True)

    params = dict(route.calls.last.request.url.params)
    assert params == {"phones": "+5491155550000", "exact_match": "true"}


@respx.mock
async def test_find_users_searches_by_employee_number(client):
    payload = {"next_page_key": None, "data": {"11": {"id": 11}}}
    route = respx.get(f"{API}/users.by").mock(return_value=httpx.Response(200, json=payload))

    result = await users.find_users(client, employee_number="E-42")

    assert result == payload
    assert dict(route.calls.last.request.url.params) == {"employee_number": "E-42"}


async def test_find_users_requires_a_search_criterion(client):
    with pytest.raises(ValueError, match="username, email, phone or employee"):
        await users.find_users(client)


@respx.mock
async def test_list_users_include_disabled(client):
    route = respx.get(f"{API}/users").mock(return_value=httpx.Response(200, json=[]))

    await users.list_users(client, include_disabled=True)

    assert dict(route.calls.last.request.url.params) == {"include_disabled": "true"}


@respx.mock
async def test_get_user_groups_passes_user_ids_array(client):
    route = respx.get(f"{API}/users.groups").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "groups": []}])
    )

    result = await users.get_user_groups(client, user_ids=[1, 2])

    assert result == [{"id": 1, "groups": []}]
    assert route.calls.last.request.url.params.get_list("ids[]") == ["1", "2"]


async def test_get_user_groups_requires_user_ids(client):
    with pytest.raises(ValueError, match="user_ids"):
        await users.get_user_groups(client, user_ids=[])


@respx.mock
async def test_list_groups_without_filter_lists_all(client):
    route = respx.get(f"{API}/groups").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "name": "Support"}])
    )

    result = await users.list_groups(client)

    assert result == [{"id": 1, "name": "Support"}]
    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
async def test_list_groups_filters_by_name(client):
    route = respx.get(f"{API}/groups").mock(return_value=httpx.Response(200, json=[]))

    await users.list_groups(client, name="Support")

    assert dict(route.calls.last.request.url.params) == {"name": "Support"}


@respx.mock
async def test_list_group_members_requires_group_id(client):
    route = respx.get(f"{API}/groups.users").mock(
        return_value=httpx.Response(200, json=[{"id": 3, "username": "ada"}])
    )

    result = await users.list_group_members(client, group_id=5)

    assert result == [{"id": 3, "username": "ada"}]
    assert dict(route.calls.last.request.url.params) == {"id": "5"}


@respx.mock
async def test_list_group_members_can_filter_by_user(client):
    route = respx.get(f"{API}/groups.users").mock(
        return_value=httpx.Response(200, json=[])
    )

    await users.list_group_members(client, group_id=5, user_id=3)

    assert dict(route.calls.last.request.url.params) == {"id": "5", "user_id": "3"}


@respx.mock
async def test_list_companies_filters_by_external_id(client):
    route = respx.get(f"{API}/companies").mock(
        return_value=httpx.Response(200, json=[{"id": 2, "name": "Acme"}])
    )

    result = await users.list_companies(client, external_id="EXT-1")

    assert result == [{"id": 2, "name": "Acme"}]
    assert dict(route.calls.last.request.url.params) == {"external_id": "EXT-1"}
