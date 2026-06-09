# Security Policy

## Supported versions

Only the latest released version of `invgate-service-desk-mcp` receives security fixes.

| Version | Supported |
| ------- | --------- |
| latest  | ✅        |
| older   | ❌        |

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

Report privately via GitHub's [private vulnerability reporting](https://github.com/tracegazer/invgate-service-desk-mcp/security/advisories/new)
(Security → Report a vulnerability). You should receive an acknowledgement within a
few days. If a fix is warranted, it will be released and credited (unless you prefer
to remain anonymous).

## Handling of credentials

`invgate-service-desk-mcp` authenticates to the InvGate Service Desk API with HTTP
Basic auth: a username (`api` by default) and an API token used as the password.

- The token is read from `INVGATE_API_TOKEN` (env) or a local `config.toml` and is
  never written back to disk.
- The API token is redacted from error messages and from all OpenTelemetry spans,
  metrics, and logs before export.
- Treat your InvGate API token like a password: scope it to the minimum access you
  need and run the server in read-only mode (`INVGATE_WRITE_PROFILE=none`, the
  default) unless you explicitly require write tools.
- Always use an `https://` base URL in production — a plain `http://` URL sends
  credentials in cleartext (the server warns when it detects this).
