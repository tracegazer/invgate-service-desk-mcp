"""Generate sustained telemetry traffic for Dynatrace dashboards.

Runs read-only MCP tool calls via the real MCP protocol every N minutes.
Usage:
    INVGATE_BASE_URL=... INVGATE_API_TOKEN=... INVGATE_TELEMETRY=1 \
    OTEL_EXPORTER_OTLP_ENDPOINT=... OTEL_EXPORTER_OTLP_HEADERS=... \
    OTEL_SERVICE_NAME=invgate-service-desk-mcp \
    python scripts/generate_telemetry.py [--interval 600] [--rounds 12]
"""

import argparse
import asyncio
import json
import os
import random
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# Read-only tool calls with varying complexity
TOOL_CALLS = [
    ("list_priorities", {}),
    ("list_statuses", {}),
    ("list_incident_types", {}),
    ("list_sources", {}),
    ("list_categories", {"page_size": 10}),
    ("list_categories", {"search": "red"}),
    ("get_incident", {"incident_id": 1}),
    ("get_incident", {"incident_id": 100}),
    ("get_incident_comments", {"request_id": 1}),
    ("list_incidents_by_status", {"status_id": 2, "limit": 10}),
    ("list_groups", {}),
    ("list_companies", {}),
    ("list_helpdesks", {}),
    ("list_locations", {}),
    ("search_kb_articles", {"keywords": "VPN"}),
    ("search_kb_articles", {"keywords": "password reset"}),
    ("list_kb_categories", {}),
    ("list_triggers", {}),
    ("list_breaking_news_types", {}),
    ("list_breaking_news_statuses", {}),
    ("list_time_tracking_categories", {}),
]


async def run_round(round_num: int, total: int):
    """Run one round of tool calls via MCP stdio protocol."""
    # Pick a random subset (10-15 calls) to vary the traffic pattern
    calls = random.sample(TOOL_CALLS, k=min(random.randint(10, 15), len(TOOL_CALLS)))

    server = StdioServerParameters(
        command="uv",
        args=["run", "invgate-service-desk-mcp"],
        env={**os.environ},
    )

    t0 = time.time()
    ok = 0
    err = 0

    try:
        async with stdio_client(server) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                for name, args in calls:
                    try:
                        result = await session.call_tool(name, arguments=args)
                        data = json.loads(result.content[0].text) if result.content else []
                        size = len(data) if isinstance(data, list) else 1
                        ok += 1
                    except Exception as e:
                        print(f"    ERR {name}: {e}", file=sys.stderr)
                        err += 1
    except Exception as e:
        print(f"  Round {round_num} session error: {e}", file=sys.stderr)
        return

    elapsed = time.time() - t0
    print(
        f"  Round {round_num}/{total}: {ok} ok, {err} err, "
        f"{len(calls)} calls in {elapsed:.1f}s"
    )


async def main():
    parser = argparse.ArgumentParser(description="Generate MCP telemetry traffic")
    parser.add_argument(
        "--interval", type=int, default=600, help="Seconds between rounds (default: 600)"
    )
    parser.add_argument(
        "--rounds", type=int, default=12, help="Number of rounds (default: 12 = 2h at 10m)"
    )
    args = parser.parse_args()

    print(
        f"Generating telemetry: {args.rounds} rounds, "
        f"{args.interval}s interval ({args.rounds * args.interval / 60:.0f} min total)"
    )

    for i in range(1, args.rounds + 1):
        await run_round(i, args.rounds)
        if i < args.rounds:
            print(f"  Sleeping {args.interval}s until round {i + 1}...")
            await asyncio.sleep(args.interval)

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
