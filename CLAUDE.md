# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP (Model Context Protocol) server for the **InvGate Service Desk API**. The goal is to expose InvGate SD operations as MCP tools so that AI agents can interact with InvGate Service Desk programmatically.

## Knowledge Base

`base_conocimiento/api-spec.json` — Complete InvGate Service Desk API specification. This JSON maps endpoint keys (e.g. `incident`, `incidents.by.status`, `user`, `kb.articles`) to their HTTP methods, parameters, and descriptions. Key API domains:

- **Incidents** — CRUD, filtering by status/agent/customer/view/sentiment, attachments, comments, reassignment, approvals, tasks, linking CIs
- **Users & Groups** — user management, groups, companies, locations
- **Custom Fields** — field definitions, options (list/tree), fields by category
- **Knowledge Base** — articles CRUD, categories, keyword search
- **Workflows** — initial fields, deployment, process management
- **Assets/CIs** — asset lookup, linked assets
- **Breaking News** — announcements
- **Triggers** — automation rules and executions
- **Time Tracking** — time entries by category
- **Data Export** — bulk data extraction

## Architecture

Python-based MCP server using the Anthropic MCP SDK (`mcp` package, FastMCP). Modular by domain: each `src/invgate_service_desk_mcp/domains/*.py` module owns its tools and registers them via `register(mcp, client)`. 96 tools across 11 domains (63 read-only + 33 write opt-in). The API spec in `base_conocimiento/` was used to drive tool generation.

Writes are gated by `INVGATE_WRITE_PROFILE`: `none` (default, read-only), `support` (incidents + time tracking; KB stays read-only), or `full` (incidents + time tracking + Knowledge Base). Legacy `INVGATE_ENABLE_WRITES=1` still works and maps to `full`.

## InvGate SD API Notes

- Instance URL pattern: `https://{instance}.sd.cloud.invgate.net`
- Auth: API token via header
- Dates support `epoch` or `iso8601` format parameter
- Incidents are called "requests" in some API responses
- Custom fields are referenced by category and can be list, tree, or free-form types
- Views are predefined filters identified by numeric ID
