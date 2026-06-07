"""MCP server entrypoint for the InvGate Service Desk API.

Option B architecture: each domain module owns its tools and registers them via
``register(mcp, client)``. This keeps the server layer thin and lets each phase add
a domain without touching existing ones.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Literal

from .client import InvGateClient
from .config import Config
from .telemetry import InstrumentedFastMCP, Telemetry, build_telemetry
from .domains import (
    assets,
    breaking_news,
    catalog,
    custom_fields,
    incidents,
    kb,
    organization,
    timetracking,
    triggers,
    users,
    workflows,
)

INSTRUCTIONS = """\
Tools for the InvGate Service Desk API. 96 tools across 11 domains: incidents, \
catalog (reference data), users & groups, knowledge base, custom fields, \
organizational structure, assets & CIs, triggers, workflows, breaking news, \
and time tracking. Read-only by default; write tools are registered only when \
the operator sets INVGATE_ENABLE_WRITES. Incidents are called "requests" in \
some API responses.

DISCOVERY: Before creating or modifying a ticket, call list_priorities, \
list_statuses, list_incident_types, list_categories, and list_sources to \
obtain valid IDs. Use find_users to resolve names or emails to user IDs. \
Use list_helpdesks and list_helpdesk_levels to resolve help desk names to \
group IDs.

DISAMBIGUATION: When a search by name returns multiple results, NEVER choose \
on your own. Present ALL matching options to the user with their IDs and \
names, and ask the user to choose. This applies to users, help desks, \
categories, and any entity resolved by name.\
"""


def build_server(client: InvGateClient, telemetry: Telemetry | None = None) -> InstrumentedFastMCP:
    """Build the MCP server and register all enabled domain tools."""
    mcp = InstrumentedFastMCP(
        name="invgate-service-desk",
        instructions=INSTRUCTIONS,
        telemetry=telemetry or Telemetry(),
    )
    catalog.register(mcp, client)
    incidents.register(mcp, client)
    users.register(mcp, client)
    kb.register(mcp, client)
    custom_fields.register(mcp, client)
    organization.register(mcp, client)
    assets.register(mcp, client)
    triggers.register(mcp, client)
    workflows.register(mcp, client)
    breaking_news.register(mcp, client)
    timetracking.register(mcp, client)
    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(prog="invgate-service-desk-mcp")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport (default: stdio).",
    )
    args = parser.parse_args()

    warning = insecure_transport_warning(args.transport)
    if warning:
        print(warning, file=sys.stderr)

    config = Config.load(env=os.environ)
    print(write_profile_banner(config), file=sys.stderr)
    telemetry = build_telemetry(config)

    if config.telemetry_enabled:
        _telemetry_hints(telemetry)

    client = InvGateClient(config, telemetry=telemetry)
    mcp = build_server(client, telemetry=telemetry)
    try:
        mcp.run(transport=_transport(args.transport))
    finally:
        telemetry.shutdown()


def insecure_transport_warning(transport: str) -> str | None:
    """Warn when an HTTP transport is used: it exposes all data via the stored
    InvGate credential and ships no auth/binding controls of its own."""
    if transport == "stdio":
        return None
    return (
        f"WARNING: transport '{transport}' has no built-in auth. It exposes every "
        "InvGate operation through the server's stored credential. Bind it to "
        "loopback or run it behind an authenticated reverse proxy; never expose it "
        "directly to an untrusted network."
    )


def write_profile_banner(config: Config) -> str:
    """One-line summary of the resolved write profile for the startup log."""
    domains = ", ".join(sorted(config.write_domains)) or "read-only"
    return f"write profile: {config.write_profile} ({domains})"


def _telemetry_hints(telemetry: Telemetry) -> None:
    """Print helpful hints about telemetry configuration to stderr."""
    resource_attrs = os.environ.get("OTEL_RESOURCE_ATTRIBUTES", "")
    if "dt.entity.service" not in resource_attrs:
        print(
            "TIP: To associate metrics with your Dynatrace service entity, add:\n"
            '  OTEL_RESOURCE_ATTRIBUTES="dt.entity.service=<your-entity-id>"\n'
            "Find your entity ID in Dynatrace: Services → "
            f"{telemetry.resource_service_name()} → Properties",
            file=sys.stderr,
        )


def _transport(value: str) -> Literal["stdio", "sse", "streamable-http"]:
    return value  # type: ignore[return-value]


if __name__ == "__main__":
    main()
