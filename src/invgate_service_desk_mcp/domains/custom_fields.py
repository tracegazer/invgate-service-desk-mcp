"""Custom Fields domain (Phase 4, read-only).

Thin, typed wrappers over the read-only custom-field endpoints. These let an AI
agent discover which custom fields exist, their types, their selectable options
(list/tree), and which apply to a category — the prerequisite for ever filling
field values on a request. Writing field options (instance configuration) and
setting field values on a request are deferred to a later write phase.

Two distinct concepts in InvGate: a field DEFINITION (instance-level, identified
by ``uid``, with a numeric ``type``) versus a field VALUE on a request (lives on
the ticket). This domain only reads definitions/options.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client import InvGateClient

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


async def list_custom_fields(client: InvGateClient) -> Any:
    """List all active custom field definitions."""
    return await client.get("cf.fields.all")


async def list_shared_custom_fields(client: InvGateClient) -> Any:
    """List all active shared custom field definitions."""
    return await client.get("cf.fields.shared.all")


async def list_custom_field_types(client: InvGateClient) -> Any:
    """List supported custom field types (a map of type code to description)."""
    return await client.get("cf.fields.types")


async def get_custom_field_config(client: InvGateClient, uid: int) -> Any:
    """Get the configuration of a custom field by UID (legacy; prefer the
    list/tree option endpoints for list/tree fields)."""
    return await client.get("cf.field.options", params={"uid": uid})


async def list_custom_fields_by_category(client: InvGateClient, category_id: int) -> Any:
    """List the custom fields related to a category."""
    return await client.get("cf.fields.by.category", params={"category_id": category_id})


async def get_starting_fields_by_category(
    client: InvGateClient,
    category_id: int,
    *,
    language: str | None = None,
) -> Any:
    """List the custom fields applicable to a category at request creation."""
    return await client.get(
        "cf.starting.fields.by.category",
        params={"category_id": category_id, "language": language},
    )


async def get_custom_field_list_options(client: InvGateClient, uid: int) -> Any:
    """Get the options of a list-type custom field."""
    return await client.get("cf.field.options.list", params={"uid": uid})


async def get_custom_field_list_config(client: InvGateClient, uid: int) -> Any:
    """Get the configuration of a list-type custom field."""
    return await client.get("cf.field.options.list.config", params={"uid": uid})


async def get_custom_field_tree_options(client: InvGateClient, uid: int) -> Any:
    """Get the options structure of a tree-type custom field."""
    return await client.get("cf.field.options.tree", params={"uid": uid})


def register(mcp: FastMCP, client: InvGateClient) -> None:
    """Register the read-only custom-field tools on the given MCP server."""

    @mcp.tool()
    async def list_custom_fields() -> Any:
        """List all active custom field definitions."""
        return await list_custom_fields_fn(client)

    @mcp.tool()
    async def list_shared_custom_fields() -> Any:
        """List all active shared custom field definitions."""
        return await list_shared_custom_fields_fn(client)

    @mcp.tool()
    async def list_custom_field_types() -> Any:
        """List supported custom field types (type code -> description)."""
        return await list_custom_field_types_fn(client)

    @mcp.tool()
    async def get_custom_field_config(uid: int) -> Any:
        """Get the configuration of a custom field by UID."""
        return await get_custom_field_config_fn(client, uid)

    @mcp.tool()
    async def list_custom_fields_by_category(category_id: int) -> Any:
        """List the custom fields related to a category."""
        return await list_custom_fields_by_category_fn(client, category_id)

    @mcp.tool()
    async def get_starting_fields_by_category(
        category_id: int,
        language: str | None = None,
    ) -> Any:
        """List the custom fields applicable to a category at request creation."""
        return await get_starting_fields_by_category_fn(
            client, category_id, language=language
        )

    @mcp.tool()
    async def get_custom_field_list_options(uid: int) -> Any:
        """Get the options of a list-type custom field."""
        return await get_custom_field_list_options_fn(client, uid)

    @mcp.tool()
    async def get_custom_field_list_config(uid: int) -> Any:
        """Get the configuration of a list-type custom field."""
        return await get_custom_field_list_config_fn(client, uid)

    @mcp.tool()
    async def get_custom_field_tree_options(uid: int) -> Any:
        """Get the options structure of a tree-type custom field."""
        return await get_custom_field_tree_options_fn(client, uid)


# Aliases so the tool wrappers above can call the module-level implementations
# without shadowing them by the same in-scope tool names.
list_custom_fields_fn = list_custom_fields
list_shared_custom_fields_fn = list_shared_custom_fields
list_custom_field_types_fn = list_custom_field_types
get_custom_field_config_fn = get_custom_field_config
list_custom_fields_by_category_fn = list_custom_fields_by_category
get_starting_fields_by_category_fn = get_starting_fields_by_category
get_custom_field_list_options_fn = get_custom_field_list_options
get_custom_field_list_config_fn = get_custom_field_list_config
get_custom_field_tree_options_fn = get_custom_field_tree_options
