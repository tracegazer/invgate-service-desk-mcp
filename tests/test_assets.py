import httpx
import pytest
import respx

from invgate_service_desk_mcp.client import InvGateClient
from invgate_service_desk_mcp.config import Config
from invgate_service_desk_mcp.domains import assets
from invgate_service_desk_mcp.normalize import UnexpectedShapeError

BASE = "https://acme.sd.cloud.invgate.net"
API = f"{BASE}/api/v1"


@pytest.fixture
async def client():
    c = InvGateClient(Config(base_url=BASE, api_token="tok"))
    yield c
    await c.aclose()


@respx.mock
async def test_list_incidents_by_asset(client):
    route = respx.get(f"{API}/incidents.by.asset").mock(
        return_value=httpx.Response(200, json={"status": "OK", "requestIds": [1]})
    )

    result = await assets.list_incidents_by_asset(client, asset_id=5)

    # The {status, requestIds: [...]} envelope is flattened to a plain list.
    assert result == [1]
    assert dict(route.calls.last.request.url.params) == {"asset_id": "5"}


@respx.mock
async def test_list_requests_related_to_assets_encodes_ids(client):
    route = respx.get(f"{API}/assets").mock(return_value=httpx.Response(200, json=[]))

    await assets.list_requests_related_to_assets(
        client, assets_source_id=1, asset_ids=[10, 11]
    )

    params = route.calls.last.request.url.params
    assert params["assets_source_id"] == "1"
    assert params.get_list("assets_ids[]") == ["10", "11"]


@respx.mock
async def test_list_incidents_by_asset_raises_on_unexpected_shape(client):
    respx.get(f"{API}/incidents.by.asset").mock(
        return_value=httpx.Response(200, json={"status": "ERROR"})
    )

    with pytest.raises(UnexpectedShapeError, match="incidents.by.asset"):
        await assets.list_incidents_by_asset(client, asset_id=5)


@respx.mock
async def test_get_linked_assets_counters(client):
    route = respx.get(f"{API}/assets.linked.assets.counters.from").mock(
        return_value=httpx.Response(200, json={})
    )

    await assets.get_linked_assets_counters(client, assets_source_id=1, from_status="open")

    assert dict(route.calls.last.request.url.params) == {
        "assets_source_id": "1",
        "from": "open",
    }


@respx.mock
async def test_get_cis_by_id_encodes_internal_ids(client):
    route = respx.get(f"{API}/cis.by.id").mock(return_value=httpx.Response(200, json=[]))

    await assets.get_cis_by_id(client, ci_source_id=2, ci_internal_ids=[100, 200])

    params = route.calls.last.request.url.params
    assert params["ci_source_id"] == "2"
    assert params.get_list("ci_internal_ids[]") == ["100", "200"]


@respx.mock
async def test_list_incidents_by_cis(client):
    route = respx.get(f"{API}/incidents.by.cis").mock(
        return_value=httpx.Response(200, json={"status": "OK", "requestIds": [7, 8]})
    )

    result = await assets.list_incidents_by_cis(
        client, cis_source_id=2, ci_ids=[5], group="hw"
    )

    # The {status, requestIds: [...]} envelope is flattened to a plain list.
    assert result == [7, 8]
    params = route.calls.last.request.url.params
    assert params["cis_source_id"] == "2"
    assert params["group"] == "hw"
    assert params.get_list("ci_ids[]") == ["5"]


@respx.mock
async def test_get_linked_cis_counters(client):
    route = respx.get(f"{API}/incident.linked_cis.counters.from").mock(
        return_value=httpx.Response(200, json={})
    )

    await assets.get_linked_cis_counters(client, cis_source_id=2, from_status="open")

    assert dict(route.calls.last.request.url.params) == {
        "cis_source_id": "2",
        "from": "open",
    }
