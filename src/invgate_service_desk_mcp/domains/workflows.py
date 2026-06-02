"""Workflows domain (Phase 6, read-only).

Thin, typed wrappers over the read-only workflow endpoints: the initial fields a
workflow needs to create a request, workflow process definitions with version
history, and current values of workflow list fields. Deploying workflows (write)
is deferred.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client import InvGateClient

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

DateFormat = str  # "iso8601" or "epoch"


async def get_workflow_initial_fields(client: InvGateClient, category_id: int) -> Any:
    """List the initial fields needed to create a request from a workflow category."""
    return await client.get(
        "wf.initialfields.by.category", params={"category_id": category_id}
    )


async def get_workflow_process(
    client: InvGateClient,
    *,
    process_id: int | None = None,
    date_format: DateFormat = "iso8601",
    page_key: str | None = None,
    limit: int | None = None,
) -> Any:
    """Get workflow process info with version history, or one process by ID."""
    return await client.get(
        "workflow.process",
        params={
            "id": process_id,
            "date_format": date_format,
            "page_key": page_key,
            "limit": limit,
        },
    )


async def get_workflow_field_list_values(
    client: InvGateClient, request_id: int, field_id: int
) -> Any:
    """Get current values of a list-type field in a workflow instance."""
    return await client.get(
        "workflow.field.list.values",
        params={"request_id": request_id, "field_id": field_id},
    )


def register(mcp: "FastMCP", client: InvGateClient) -> None:
    """Register the read-only workflow tools on the given MCP server."""

    @mcp.tool()
    async def get_workflow_initial_fields(category_id: int) -> Any:
        """List the initial fields needed to create a request from a workflow."""
        return await get_workflow_initial_fields_fn(client, category_id)

    @mcp.tool()
    async def get_workflow_process(
        process_id: int | None = None,
        date_format: DateFormat = "iso8601",
        page_key: str | None = None,
        limit: int | None = None,
    ) -> Any:
        """Get workflow process info with version history (or one by ID)."""
        return await get_workflow_process_fn(
            client,
            process_id=process_id,
            date_format=date_format,
            page_key=page_key,
            limit=limit,
        )

    @mcp.tool()
    async def get_workflow_field_list_values(request_id: int, field_id: int) -> Any:
        """Get current values of a list-type field in a workflow instance."""
        return await get_workflow_field_list_values_fn(client, request_id, field_id)


# Aliases so the tool wrappers above can call the module-level implementations.
get_workflow_initial_fields_fn = get_workflow_initial_fields
get_workflow_process_fn = get_workflow_process
get_workflow_field_list_values_fn = get_workflow_field_list_values
