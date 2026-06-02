import httpx
import pytest
import respx

from invgate_service_desk_mcp.client import InvGateClient
from invgate_service_desk_mcp.config import Config
from invgate_service_desk_mcp.server import build_server
from invgate_service_desk_mcp.telemetry import InstrumentedFastMCP, Telemetry

BASE = "https://acme.sd.cloud.invgate.net"
API = f"{BASE}/api/v1"


@pytest.fixture
async def client():
    c = InvGateClient(Config(base_url=BASE, api_token="tok"))
    yield c
    await c.aclose()


def test_insecure_transport_warning_for_http_transports():
    from invgate_service_desk_mcp.server import insecure_transport_warning

    assert insecure_transport_warning("stdio") is None
    for transport in ("sse", "streamable-http"):
        warning = insecure_transport_warning(transport)
        assert warning is not None
        assert "auth" in warning.lower()


async def test_registers_incident_read_tools(client):
    mcp = build_server(client)

    tools = await mcp.list_tools()
    names = {t.name for t in tools}

    assert {
        "get_incident",
        "get_incident_comments",
        "list_incidents_by_status",
        "list_incidents_by_agent",
        "list_incidents_by_customer",
    } <= names


async def test_registers_user_and_group_read_tools(client):
    mcp = build_server(client)

    tools = await mcp.list_tools()
    names = {t.name for t in tools}

    assert {
        "get_user",
        "list_users",
        "find_users",
        "get_user_groups",
        "list_groups",
        "list_group_members",
        "list_companies",
    } <= names


async def test_registers_knowledge_base_read_tools(client):
    mcp = build_server(client)

    tools = await mcp.list_tools()
    names = {t.name for t in tools}

    assert {
        "search_kb_articles",
        "list_kb_articles",
        "get_kb_articles_by_ids",
        "list_kb_articles_by_category",
        "get_kb_article_attachments",
        "list_kb_categories",
        "get_kb_categories_by_ids",
    } <= names


async def test_registers_custom_field_read_tools(client):
    mcp = build_server(client)

    names = {t.name for t in await mcp.list_tools()}

    assert {
        "list_custom_fields",
        "list_shared_custom_fields",
        "list_custom_field_types",
        "get_custom_field_config",
        "list_custom_fields_by_category",
        "get_starting_fields_by_category",
        "get_custom_field_list_options",
        "get_custom_field_list_config",
        "get_custom_field_tree_options",
    } <= names


async def test_registers_organization_read_tools(client):
    mcp = build_server(client)

    names = {t.name for t in await mcp.list_tools()}

    assert {
        "list_helpdesks",
        "list_helpdesk_levels",
        "list_helpdesks_and_levels",
        "list_helpdesk_observers",
        "list_level_observers",
        "list_locations",
        "list_location_members",
        "list_location_observers",
        "list_company_members",
        "list_company_groups",
        "list_company_observers",
        "list_incidents_by_helpdesk",
    } <= names


async def test_registers_phase6_complementary_read_tools(client):
    mcp = build_server(client)

    names = {t.name for t in await mcp.list_tools()}

    assert {
        # Breaking News
        "get_breaking_news",
        "list_breaking_news",
        "get_breaking_news_status",
        "list_breaking_news_types",
        "list_breaking_news_statuses",
        # Triggers
        "list_triggers",
        "list_trigger_executions",
        # Workflows
        "get_workflow_initial_fields",
        "get_workflow_process",
        "get_workflow_field_list_values",
        # Assets / CIs
        "list_incidents_by_asset",
        "list_requests_related_to_assets",
        "get_linked_assets_counters",
        "get_cis_by_id",
        "list_incidents_by_cis",
        "get_linked_cis_counters",
    } <= names


async def test_registers_time_tracking_read_tools(client):
    mcp = build_server(client)

    names = {t.name for t in await mcp.list_tools()}

    assert {
        "list_time_tracking",
        "list_time_tracking_categories",
    } <= names


async def test_time_tracking_write_tools_registered_when_writes_enabled():
    client = InvGateClient(Config(base_url=BASE, api_token="tok", enable_writes=True))
    try:
        mcp = build_server(client)
        names = {t.name for t in await mcp.list_tools()}
    finally:
        await client.aclose()

    assert {"log_time", "delete_time_entry"} <= names


async def test_time_tracking_write_tools_absent_by_default(client):
    mcp = build_server(client)
    names = {t.name for t in await mcp.list_tools()}

    assert "log_time" not in names
    assert "delete_time_entry" not in names


async def test_no_write_tools_by_default(client):
    mcp = build_server(client)

    tools = await mcp.list_tools()

    # Writes are opt-in: with the default config no write verb may be exposed.
    forbidden = ("create", "update", "delete", "reassign", "reopen", "close", "reject")
    offenders = [t.name for t in tools if t.name.startswith(forbidden)]
    assert offenders == [], f"write tools leaked without opt-in: {offenders}"


async def test_kb_write_tools_registered_when_writes_enabled():
    from invgate_service_desk_mcp.client import InvGateClient

    client = InvGateClient(Config(base_url=BASE, api_token="tok", enable_writes=True))
    try:
        mcp = build_server(client)
        names = {t.name for t in await mcp.list_tools()}
    finally:
        await client.aclose()

    assert {"create_kb_article", "update_kb_article", "delete_kb_article"} <= names


async def test_incident_write_tools_registered_when_writes_enabled():
    from invgate_service_desk_mcp.client import InvGateClient

    client = InvGateClient(Config(base_url=BASE, api_token="tok", enable_writes=True))
    try:
        mcp = build_server(client)
        names = {t.name for t in await mcp.list_tools()}
    finally:
        await client.aclose()

    assert {
        "create_incident",
        "update_incident",
        "reassign_incident",
        "add_incident_comment",
        "cancel_incident",
        "set_incident_custom_field",
        "delete_incident_custom_field",
        "accept_incident_solution",
    } <= names


async def test_incident_write_tools_absent_by_default(client):
    mcp = build_server(client)
    names = {t.name for t in await mcp.list_tools()}

    assert "create_incident" not in names
    assert "reassign_incident" not in names


@respx.mock
async def test_get_user_groups_tool_routes_to_api(client):
    route = respx.get(f"{API}/users.groups").mock(
        return_value=httpx.Response(200, json=[{"id": 1, "groups": []}])
    )
    mcp = build_server(client)

    await mcp.call_tool("get_user_groups", {"user_ids": [1, 2]})

    assert route.called
    assert route.calls.last.request.url.params.get_list("ids[]") == ["1", "2"]


@respx.mock
async def test_get_incident_tool_routes_to_api(client):
    route = respx.get(f"{API}/incident").mock(
        return_value=httpx.Response(200, json={"id": 42, "title": "Printer down"})
    )
    mcp = build_server(client)

    result = await mcp.call_tool("get_incident", {"incident_id": 42})

    assert route.called
    assert route.calls.last.request.url.params["id"] == "42"
    # FastMCP returns (content_blocks, structured) — the structured payload carries the data.
    structured = result[1] if isinstance(result, tuple) else result
    assert "Printer down" in str(structured)


async def test_build_server_uses_instrumented_fastmcp_when_telemetry_passed():
    client = InvGateClient(Config(base_url="https://x.net", api_token="t"))
    mcp = build_server(client, telemetry=Telemetry())
    assert isinstance(mcp, InstrumentedFastMCP)
