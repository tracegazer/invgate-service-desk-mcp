"""Time tracking domain (Phase 8).

Thin, typed wrappers over the InvGate time tracking endpoints: read the logged
entries (by request or by date interval) and the cost categories; write tools
(log/delete) are deferred behind explicit opt-in.

API date asymmetry to be aware of: the GET filter takes ``from``/``to`` as
ISO-8601 strings (``date_format`` controls the response shape), while the POST
logs ``from``/``to`` as **epoch timestamps** (INTEGER). Note the category id is
``category_id`` on the POST but surfaces as ``timetracking_category_id`` in GET
responses.

There is no update verb. ``delete_time_entry`` is implemented to spec and kept
for completeness, but be warned: logged entries are effectively permanent.
Verified live against the Mainsoft instance (2026-06-03) that a correctly-formed
delete (existing entry, matching author) returns the same ``{"status": "ERROR"}``
as deleting a nonexistent id, and such entries cannot be removed from the UI
either. Treat ``log_time`` as irreversible.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..client import InvGateClient

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


async def list_time_tracking(
    client: InvGateClient,
    *,
    request_id: int | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    date_format: str | None = None,
) -> Any:
    """List time tracking entries for a request or within a date interval.

    Provide either ``request_id`` or ``from_date`` (ISO-8601). ``to_date``
    defaults to now. ``date_format`` is 'iso8601noT' (default) or 'iso8601'.
    """
    if request_id is None and from_date is None:
        raise ValueError("Provide either request_id or from_date.")
    return await client.get(
        "timetracking",
        params={
            "request_id": request_id,
            "from": from_date,
            "to": to_date,
            "date_format": date_format,
        },
    )


async def list_time_tracking_categories(
    client: InvGateClient, category_id: int | None = None
) -> Any:
    """List time tracking categories (or one by ID). Includes ``cost_per_hour``."""
    return await client.get(
        "timetracking.attributes.category", params={"id": category_id}
    )


# --- Write operations (registered only when the operator opts in) ------------


async def log_time(
    client: InvGateClient,
    *,
    request_id: int,
    user_id: int,
    to_timestamp: int,
    from_timestamp: int | None = None,
    category_id: int | None = None,
    comment: str | None = None,
) -> Any:
    """Log time on a request. ``from``/``to`` are epoch timestamps (``from``
    defaults to now). To set ``category_id``, first call
    ``list_time_tracking_categories`` and pass the matching numeric id (do not
    guess it). Returns ``{"status": ..., "timetracking_id": <id>}``."""
    return await client.post(
        "timetracking",
        data={
            "request_id": request_id,
            "user_id": user_id,
            "to": to_timestamp,
            "from": from_timestamp,
            "category_id": category_id,
            "comment": comment,
        },
    )


async def delete_time_entry(
    client: InvGateClient,
    *,
    request_id: int,
    timetracking_id: int,
    user_id: int,
) -> Any:
    """Delete a time tracking entry from a request."""
    return await client.delete(
        "timetracking",
        params={
            "request_id": request_id,
            "timetracking_id": timetracking_id,
            "user_id": user_id,
        },
    )


def register(mcp: "FastMCP", client: InvGateClient) -> None:
    """Register the read-only time tracking tools on the given MCP server."""

    @mcp.tool()
    async def list_time_tracking(
        request_id: int | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        date_format: str | None = None,
    ) -> Any:
        """List time tracking entries for a request or within a date interval
        (provide request_id or from_date; dates are ISO-8601)."""
        return await list_time_tracking_fn(
            client,
            request_id=request_id,
            from_date=from_date,
            to_date=to_date,
            date_format=date_format,
        )

    @mcp.tool()
    async def list_time_tracking_categories(category_id: int | None = None) -> Any:
        """List time tracking categories (or one by ID), including cost_per_hour."""
        return await list_time_tracking_categories_fn(client, category_id)

    # Write tools are registered only when the operator has opted in.
    if client.writes_enabled_for("timetracking"):
        _register_writes(mcp, client)


def _register_writes(mcp: "FastMCP", client: InvGateClient) -> None:
    """Register the time tracking write tools. Called only when writes are enabled."""

    @mcp.tool()
    async def log_time(
        request_id: int,
        user_id: int,
        to_timestamp: int,
        from_timestamp: int | None = None,
        category_id: int | None = None,
        comment: str | None = None,
    ) -> Any:
        """Log time on a request (from/to are epoch timestamps; from defaults to
        now). For category_id, first call list_time_tracking_categories and use
        the matching numeric id rather than guessing."""
        return await log_time_fn(
            client,
            request_id=request_id,
            user_id=user_id,
            to_timestamp=to_timestamp,
            from_timestamp=from_timestamp,
            category_id=category_id,
            comment=comment,
        )

    @mcp.tool()
    async def delete_time_entry(
        request_id: int, timetracking_id: int, user_id: int
    ) -> Any:
        """Delete a time tracking entry from a request."""
        return await delete_time_entry_fn(
            client,
            request_id=request_id,
            timetracking_id=timetracking_id,
            user_id=user_id,
        )


# Aliases so the tool wrappers above can call the module-level implementations
# without shadowing them by the same in-scope tool names.
list_time_tracking_fn = list_time_tracking
list_time_tracking_categories_fn = list_time_tracking_categories
log_time_fn = log_time
delete_time_entry_fn = delete_time_entry
