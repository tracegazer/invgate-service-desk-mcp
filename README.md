# invgate-service-desk-mcp

<!-- mcp-name: io.github.tracegazer/invgate-service-desk-mcp -->

> A [Model Context Protocol](https://modelcontextprotocol.io) server for **InvGate Service Desk / Service Management**.

Give your AI assistant full access to your InvGate Service Desk — query incidents, look up users, search the knowledge base, check assets, and manage tickets — all through natural language.

**96 tools** across 11 domains. Read-only by default, with optional write operations behind explicit opt-in.

## What can it do?

| Domain | Tools | Examples |
|--------|------:|---------|
| **Catalog** | 5 | List priorities, statuses, incident types, categories (with search), sources |
| **Incidents** | 34 | Get ticket details, list by status/agent/customer, create & update tickets, reassign, comment, manage approvals |
| **Users & Groups** | 7 | Look up users, find by email/phone, list group members |
| **Knowledge Base** | 10 | Search articles, browse categories, create & update articles |
| **Custom Fields** | 9 | List field definitions, get options (list/tree), fields by category |
| **Organization** | 11 | Helpdesks, levels, locations, company structure |
| **Assets / CIs** | 6 | Find assets linked to incidents, CI relationships |
| **Time Tracking** | 4 | View logged hours, log new time entries |
| **Triggers** | 2 | List automation rules and their executions |
| **Workflows** | 3 | Inspect workflow fields, processes, and field values |
| **Breaking News** | 5 | View announcements, statuses, types |

> **63 read-only tools** work out of the box. **33 write tools** (incidents, KB, time tracking) activate only when you explicitly opt in.

## Quick start

### 1. Install

```bash
pip install invgate-service-desk-mcp
```

Or run without installing (requires [uv](https://docs.astral.sh/uv/)):

```bash
uvx invgate-service-desk-mcp
```

### 2. Connect to Claude Desktop

Add this to your `claude_desktop_config.json`:

```jsonc
{
  "mcpServers": {
    "invgate": {
      "command": "uvx",
      "args": ["invgate-service-desk-mcp"],
      "env": {
        "INVGATE_BASE_URL": "https://acme.sd.cloud.invgate.net",
        "INVGATE_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

Restart Claude Desktop. That's it — start asking about your tickets.

<details>
<summary>Using pip install instead of uvx</summary>

```jsonc
{
  "mcpServers": {
    "invgate": {
      "command": "invgate-service-desk-mcp",
      "env": {
        "INVGATE_BASE_URL": "https://acme.sd.cloud.invgate.net",
        "INVGATE_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

</details>

<details>
<summary>Enabling write operations</summary>

By default the server is **read-only**. Opt into writes with `INVGATE_WRITE_PROFILE`:

| Profile          | Reads      | Writes                                                            |
|------------------|------------|-------------------------------------------------------------------|
| `none` (default) | everything | nothing                                                           |
| `support`        | everything | incidents (tickets, comments, reassign, approve) + time tracking  |
| `full`           | everything | incidents + time tracking + Knowledge Base                        |

```jsonc
{
  "mcpServers": {
    "invgate": {
      "command": "uvx",
      "args": ["invgate-service-desk-mcp"],
      "env": {
        "INVGATE_BASE_URL": "https://acme.sd.cloud.invgate.net",
        "INVGATE_API_TOKEN": "your-api-token",
        "INVGATE_WRITE_PROFILE": "support"
      }
    }
  }
}
```

> **Compatibility:** the legacy `INVGATE_ENABLE_WRITES=1` still works and maps to `full`.
> If both are set, the profile wins and a warning is printed to stderr. Note: `support`
> deliberately keeps the Knowledge Base read-only. An invalid profile name fails fast at startup.

> **Warning:** write mode lets the connected agent create, modify, and delete real content through your InvGate credential. There is no API to delete a ticket — created tickets can only be cancelled, not removed.

</details>

### 3. Get your API token

In your InvGate Service Desk instance: **Settings > Integrations > API** (or ask your admin). The server authenticates via HTTP Basic with username `api` and your token as the password.

## Configuration

Configuration resolves in this order (highest priority first):

1. **Environment variables** (always win)
2. **TOML config** at `~/.config/invgate-service-desk-mcp/config.toml`

| Env var | TOML key | Description |
|---------|----------|-------------|
| `INVGATE_BASE_URL` | `base_url` | Instance URL, e.g. `https://acme.sd.cloud.invgate.net` |
| `INVGATE_API_TOKEN` | `api_token` | API token (HTTP Basic password) |
| `INVGATE_API_USERNAME` | `api_username` | HTTP Basic username (optional, defaults to `api`) |
| `INVGATE_WRITE_PROFILE` | `write_profile` | Write access profile: `none` (default), `support`, or `full` |
| `INVGATE_TELEMETRY` | `telemetry_enabled` | Enable OpenTelemetry (default: `false`) |
| `INVGATE_TELEMETRY_DETAIL` | `telemetry_detail` | Span detail: `metadata` (default), `ids`, or `full` |

```toml
# ~/.config/invgate-service-desk-mcp/config.toml
base_url = "https://acme.sd.cloud.invgate.net"
api_token = "..."
# api_username = "api"
# write_profile = "none"  # "none" (default) | "support" | "full"
# telemetry_enabled = false
# telemetry_detail = "metadata"
```

> **Tip:** create the config directory first: `mkdir -p ~/.config/invgate-service-desk-mcp`

See [`config.toml.example`](config.toml.example) for a copy-paste template.

## Running the server

```bash
invgate-service-desk-mcp                 # STDIO transport (default)
invgate-service-desk-mcp --transport sse # SSE/HTTP transport
```

> **Security note:** STDIO (the default) keeps everything local. The `sse` and `streamable-http` transports have no built-in authentication — only use them bound to loopback or behind an authenticated reverse proxy.

## Observability (optional)

The server can emit OpenTelemetry traces, metrics, and logs — completely opt-in and vendor-neutral. Export to any OTLP-compatible backend (Dynatrace, Grafana, Datadog, Jaeger, etc.).

```bash
pip install "invgate-service-desk-mcp[telemetry]"

export INVGATE_TELEMETRY=1
```

OTLP endpoint and headers are configured via standard OpenTelemetry env vars (not in the TOML file):

<details>
<summary>Dynatrace setup</summary>

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="https://<your-env>.live.dynatrace.com/api/v2/otlp"
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Api-Token <YOUR_DT_TOKEN>"
export OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=delta
export OTEL_SERVICE_NAME=invgate-service-desk-mcp
```

Token scopes needed: `openTelemetryTrace.ingest`, `metrics.ingest`, `logs.ingest`.
See [`docs/observability-dynatrace.md`](docs/observability-dynatrace.md) for a detailed guide.

</details>

<details>
<summary>Generic OTLP collector</summary>

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
export OTEL_SERVICE_NAME=invgate-service-desk-mcp
```

</details>

**Signals emitted:**

- **Traces** — tool execution spans (GenAI semantic conventions) + InvGate API request spans with response size and item count
- **Metrics** — `mcp.tool.duration`, `invgate.client.request.duration`, `mcp.tool.errors`, `invgate.response.item_count`, `invgate.response.size`
- **Logs** — tool errors and unexpected API response shapes, correlated to traces (OTLP only, never stdout)

## Development

```bash
git clone https://github.com/tracegazer/invgate-service-desk-mcp.git
cd invgate-service-desk-mcp
uv venv && uv pip install -e ".[dev]"
pytest
```

## License

[MIT](LICENSE)
