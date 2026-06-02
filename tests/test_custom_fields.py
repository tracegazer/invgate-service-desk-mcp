import httpx
import pytest
import respx

from invgate_service_desk_mcp.client import InvGateClient
from invgate_service_desk_mcp.config import Config
from invgate_service_desk_mcp.domains import custom_fields as cf

BASE = "https://acme.sd.cloud.invgate.net"
API = f"{BASE}/api/v1"


@pytest.fixture
async def client():
    c = InvGateClient(Config(base_url=BASE, api_token="tok"))
    yield c
    await c.aclose()


@respx.mock
async def test_list_custom_fields_takes_no_params(client):
    payload = [{"uid": 1, "label": "Empresa", "type": 104, "is_required": True}]
    route = respx.get(f"{API}/cf.fields.all").mock(
        return_value=httpx.Response(200, json=payload)
    )

    result = await cf.list_custom_fields(client)

    assert result == payload
    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
async def test_list_shared_custom_fields_takes_no_params(client):
    route = respx.get(f"{API}/cf.fields.shared.all").mock(
        return_value=httpx.Response(200, json=[])
    )

    await cf.list_shared_custom_fields(client)

    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
async def test_list_custom_field_types_returns_code_map(client):
    payload = {"104": "Option List (Custom Keys)", "4": "Text Field (String)"}
    route = respx.get(f"{API}/cf.fields.types").mock(
        return_value=httpx.Response(200, json=payload)
    )

    result = await cf.list_custom_field_types(client)

    assert result == payload
    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
async def test_get_custom_field_config_passes_uid(client):
    payload = {"key-value": {"A": "Alpha"}}
    route = respx.get(f"{API}/cf.field.options").mock(
        return_value=httpx.Response(200, json=payload)
    )

    result = await cf.get_custom_field_config(client, uid=1)

    assert result == payload
    assert dict(route.calls.last.request.url.params) == {"uid": "1"}


@respx.mock
async def test_list_custom_fields_by_category_passes_category_id(client):
    route = respx.get(f"{API}/cf.fields.by.category").mock(
        return_value=httpx.Response(200, json=[{"328": "Customer"}])
    )

    await cf.list_custom_fields_by_category(client, category_id=163)

    assert dict(route.calls.last.request.url.params) == {"category_id": "163"}


@respx.mock
async def test_get_starting_fields_by_category_supports_language(client):
    route = respx.get(f"{API}/cf.starting.fields.by.category").mock(
        return_value=httpx.Response(200, json=[])
    )

    await cf.get_starting_fields_by_category(client, category_id=163, language="es")

    params = dict(route.calls.last.request.url.params)
    assert params == {"category_id": "163", "language": "es"}


@respx.mock
async def test_get_custom_field_list_options_passes_uid(client):
    payload = {"key-value": {"1": "Yes", "0": "No"}}
    route = respx.get(f"{API}/cf.field.options.list").mock(
        return_value=httpx.Response(200, json=payload)
    )

    result = await cf.get_custom_field_list_options(client, uid=7)

    assert result == payload
    assert dict(route.calls.last.request.url.params) == {"uid": "7"}


@respx.mock
async def test_get_custom_field_list_config_passes_uid(client):
    payload = {"count": 2, "configurations": {}}
    route = respx.get(f"{API}/cf.field.options.list.config").mock(
        return_value=httpx.Response(200, json=payload)
    )

    result = await cf.get_custom_field_list_config(client, uid=7)

    assert result == payload
    assert dict(route.calls.last.request.url.params) == {"uid": "7"}


@respx.mock
async def test_get_custom_field_tree_options_passes_uid(client):
    route = respx.get(f"{API}/cf.field.options.tree").mock(
        return_value=httpx.Response(200, json={"root": {}})
    )

    await cf.get_custom_field_tree_options(client, uid=9)

    assert dict(route.calls.last.request.url.params) == {"uid": "9"}
