# Connecting the InvGate MCP to Dynatrace — and verifying it

## 1. Prerequisites
- Dynatrace SaaS environment URL: `https://<env>.live.dynatrace.com`
- A Dynatrace API token with scopes: `openTelemetryTrace.ingest`,
  `metrics.ingest`, `logs.ingest` (Settings → Access Tokens → Generate).
- The server installed with the telemetry extra:
  `pip install "invgate-service-desk-mcp[telemetry]"`.

## 2. Configure (env)
```bash
export INVGATE_BASE_URL="https://<instance>.sd.cloud.invgate.net"
export INVGATE_API_TOKEN="<invgate-token>"

export INVGATE_TELEMETRY=1
export INVGATE_TELEMETRY_DETAIL=ids   # ids while validating; metadata for prod

export OTEL_EXPORTER_OTLP_ENDPOINT="https://<env>.live.dynatrace.com/api/v2/otlp"
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Api-Token <dt-token>"
export OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=delta
export OTEL_SERVICE_NAME=invgate-service-desk-mcp
```

### 2b. Associate metrics with the Dynatrace service (optional)

Dynatrace creates a service entity from the first traces it receives. To see
custom metrics (like `invgate.client.request.duration`) in the service screen,
add the entity ID to the resource attributes:

```bash
export OTEL_RESOURCE_ATTRIBUTES="dt.entity.service=SERVICE-XXXXXXXXXXXXXXXX"
```

To find the entity ID:
1. Open Dynatrace → **Services** → find `invgate-service-desk-mcp`
2. Copy the entity ID from the **Properties** section, or run:
   ```
   dtctl query 'fetch dt.entity.service | filter entity.name == "invgate-service-desk-mcp" | fields id'
   ```

The server prints a tip about this at startup when telemetry is enabled and the
attribute is not set.

## 3. Generate traffic
Run the server and exercise a tool (e.g. via the MCP client, or the live smoke
path). Each tool call produces one `execute_tool <tool>` span with a child
InvGate request span.

## 4. Verify in Dynatrace
- **Traces:** open **Distributed Tracing**, filter `service.name =
  invgate-service-desk-mcp`. You should see `execute_tool ...` spans with nested
  `GET incidents.by.agent`-style child spans, each with
  `http.response.status_code` and latency.
- **GenAI view:** **AI Observability** should list tool operations
  (`gen_ai.operation.name = execute_tool`, `gen_ai.tool.name = <tool>`).
- **Metrics (DQL notebook):**
  ```
  timeseries avg(mcp.tool.duration), by:{tool}
  timeseries avg(invgate.client.request.duration), by:{endpoint}
  ```
- **Privacy check:** open a span's attributes; confirm the InvGate token never
  appears. At `metadata` there are no ids; at `ids` you see `mcp.tool.argument.*`.
- **Logs:** open **Logs & Events**, filter `service.name == "invgate-service-desk-mcp"`.
  Tool failures appear as ERROR with the trace id; InvGate shape changes as WARNING.
- **Token-cost proxy:** `invgate.response.size` (chars) approximates how much context
  each call returns to the agent. It is NOT an LLM token count.

## 5. Troubleshooting
- Nothing arrives: verify the token scopes and that the endpoint path ends in
  `/api/v2/otlp`. Check the server's stderr for exporter errors.
- Metrics missing but traces present: confirm
  `OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE=delta`.
- Using `stdio`: confirm no console exporter is set (would corrupt the protocol).
