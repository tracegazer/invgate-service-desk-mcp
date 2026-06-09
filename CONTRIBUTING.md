# Contributing

Thanks for your interest in improving `invgate-service-desk-mcp`.

## Development setup

This project uses [uv](https://docs.astral.sh/uv/). Do not activate the venv manually.

```bash
uv sync --extra dev
```

## Workflow

- **Tests first.** Add a test for every new tool or behavior change in `tests/`.
- **Run the suite:**
  ```bash
  uv run pytest -q          # expect: passing + live-smoke tests skipped
  ```
  Live-smoke tests run only when `INVGATE_LIVE_TEST` is set (they hit the real API).
- **Lint must be clean:**
  ```bash
  uv run ruff check src/ tests/
  ```
- **Build must succeed:**
  ```bash
  uv build
  ```

## Conventions

- [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`,
  `chore:`, `docs:`, `test:`, `refactor:`.
- Code in English; comments/docs in English or Spanish are both fine.
- Each domain lives in `src/invgate_service_desk_mcp/domains/*.py` and registers its
  tools via `register(mcp, client)`. Write tools register only for domains in the
  resolved write profile (`config.write_domains`) — see existing domains for the
  pattern.
- Never document or register a tool that does not exist. Keep the README accurate to
  the implemented state.
- Never construct or guess InvGate IDs; they are opaque values from the API.

## Releasing

When cutting a release, bump the version in **all** of these and keep them in sync:

1. `pyproject.toml` → `version`
2. `server.json` → top-level `version` **and** each package `version`
3. `CHANGELOG.md` → move `Unreleased` entries under the new version

`src/invgate_service_desk_mcp/__init__.py` derives `__version__` from package
metadata, so it does not need editing. `bundle/manifest.json` is stamped
automatically by `scripts/build-mcpb.sh`.

Then tag and push:

```bash
git tag vX.Y.Z && git push --tags
```

Pushing a `v*` tag triggers the **Release** workflow, which:

1. Builds the sdist + wheel and verifies the tag matches `pyproject.toml`.
2. Publishes to PyPI via Trusted Publishing (OIDC — no token).
3. Builds and pushes a multi-arch Docker image to
   `ghcr.io/tracegazer/invgate-service-desk-mcp` (`:X.Y.Z`, `:X.Y`, `:latest`).
4. Creates a GitHub release with the artifacts (including the `.mcpb` bundle).
5. Publishes the manifest to the official **MCP Registry**.
6. Builds the `.mcpb` bundle and publishes it to **Smithery** (only if the
   `SMITHERY_API_KEY` repo secret is set — otherwise the step warns and skips).

The registry step stamps `server.json` with the tag version automatically — both
the top-level `version` and the PyPI/OCI package versions (including the image
`:tag`) — so the registry can never lag the released package. It authenticates via
GitHub OIDC against the `io.github.tracegazer` namespace (matches the repo owner),
so no token is needed.

The Docker image must carry the `io.modelcontextprotocol.server.name` label
(set in the `Dockerfile`) — it is the registry's ownership proof for the OCI
package, and must match `name` in `server.json`.

> One-time setup on PyPI: register a Trusted Publisher for this project
> (PyPI → project → Publishing) pointing at owner `tracegazer`, repo
> `invgate-service-desk-mcp`, workflow `release.yml`, environment `pypi`. For the
> very first upload, use PyPI's "pending publisher" form.

> One-time setup for Smithery (optional): mint an **API key** at
> <https://smithery.ai/account/api-keys> (NOT a `smithery auth token` — those expire
> in <= 24h) and store it as the `SMITHERY_API_KEY` repo secret. The namespace
> `tracegazer/invgate-service-desk-mcp` must be one you own (claim it with
> `smithery namespace create tracegazer/invgate-service-desk-mcp` if needed). Without
> the secret, the release still succeeds and the Smithery step is skipped.

> One-time setup for GHCR: after the first release pushes the image, set the
> `invgate-service-desk-mcp` package visibility to **Public** (GitHub → Packages →
> package settings) so the MCP Registry can read its ownership label.
