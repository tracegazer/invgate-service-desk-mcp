"""Breaking News domain (Phase 6, read-only).

Thin, typed wrappers over the read-only Breaking News (announcements) endpoints.
Creating/updating announcements (writes) is deferred to a later phase.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client import InvGateClient

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

DateFormat = str  # "iso8601" or "epoch"


async def get_breaking_news(
    client: InvGateClient,
    breaking_news_id: int,
    *,
    date_format: DateFormat = "iso8601",
) -> Any:
    """Get a single Breaking News announcement by ID."""
    return await client.get(
        "breakingnews", params={"id": breaking_news_id, "date_format": date_format}
    )


async def list_breaking_news(
    client: InvGateClient, *, date_format: DateFormat = "iso8601"
) -> Any:
    """List all Breaking News announcements."""
    return await client.get("breakingnews.all", params={"date_format": date_format})


async def get_breaking_news_status(
    client: InvGateClient,
    breaking_news_id: int,
    *,
    date_format: DateFormat = "iso8601",
) -> Any:
    """Get the updates of a Breaking News announcement."""
    return await client.get(
        "breakingnews.status",
        params={"id": breaking_news_id, "date_format": date_format},
    )


async def list_breaking_news_types(
    client: InvGateClient, *, type_id: int | None = None
) -> Any:
    """List the importance types of Breaking News, or one in particular by ID."""
    return await client.get("breakingnews.attributes.type", params={"id": type_id})


async def list_breaking_news_statuses(
    client: InvGateClient, *, status_id: int | None = None
) -> Any:
    """List the possible statuses of Breaking News, or one in particular by ID."""
    return await client.get("breakingnews.attributes.status", params={"id": status_id})


def register(mcp: FastMCP, client: InvGateClient) -> None:
    """Register the read-only Breaking News tools on the given MCP server."""

    @mcp.tool()
    async def get_breaking_news(
        breaking_news_id: int, date_format: DateFormat = "iso8601"
    ) -> Any:
        """Get a single Breaking News announcement by ID."""
        return await get_breaking_news_fn(
            client, breaking_news_id, date_format=date_format
        )

    @mcp.tool()
    async def list_breaking_news(date_format: DateFormat = "iso8601") -> Any:
        """List all Breaking News announcements."""
        return await list_breaking_news_fn(client, date_format=date_format)

    @mcp.tool()
    async def get_breaking_news_status(
        breaking_news_id: int, date_format: DateFormat = "iso8601"
    ) -> Any:
        """Get the updates of a Breaking News announcement."""
        return await get_breaking_news_status_fn(
            client, breaking_news_id, date_format=date_format
        )

    @mcp.tool()
    async def list_breaking_news_types(type_id: int | None = None) -> Any:
        """List the importance types of Breaking News (or one by ID)."""
        return await list_breaking_news_types_fn(client, type_id=type_id)

    @mcp.tool()
    async def list_breaking_news_statuses(status_id: int | None = None) -> Any:
        """List the possible statuses of Breaking News (or one by ID)."""
        return await list_breaking_news_statuses_fn(client, status_id=status_id)


# Aliases so the tool wrappers above can call the module-level implementations.
get_breaking_news_fn = get_breaking_news
list_breaking_news_fn = list_breaking_news
get_breaking_news_status_fn = get_breaking_news_status
list_breaking_news_types_fn = list_breaking_news_types
list_breaking_news_statuses_fn = list_breaking_news_statuses
