"""Triggers domain (Phase 6, read-only).

Thin, typed wrappers over the read-only automation-trigger endpoints: the list of
user-defined triggers and their execution history.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client import InvGateClient

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


async def list_triggers(client: InvGateClient, *, trigger_id: int | None = None) -> Any:
    """List the user-defined automation triggers, or one in particular by ID."""
    return await client.get("triggers", params={"trigger_id": trigger_id})


async def list_trigger_executions(client: InvGateClient, trigger_id: int) -> Any:
    """List each time a specific trigger was executed."""
    return await client.get("triggers.executions", params={"trigger_id": trigger_id})


def register(mcp: "FastMCP", client: InvGateClient) -> None:
    """Register the read-only trigger tools on the given MCP server."""

    @mcp.tool()
    async def list_triggers(trigger_id: int | None = None) -> Any:
        """List the automation triggers, or one in particular by ID."""
        return await list_triggers_fn(client, trigger_id=trigger_id)

    @mcp.tool()
    async def list_trigger_executions(trigger_id: int) -> Any:
        """List each time a specific trigger was executed."""
        return await list_trigger_executions_fn(client, trigger_id)


# Aliases so the tool wrappers above can call the module-level implementations.
list_triggers_fn = list_triggers
list_trigger_executions_fn = list_trigger_executions
