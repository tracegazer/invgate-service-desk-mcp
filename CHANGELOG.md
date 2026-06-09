# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-06-08

### Added
- Wheel `force-include` for the `py.typed` marker so downstream consumers get
  type information from an installed wheel.
- CI jobs for packaging (`uv build` + import smoke) and dependency auditing
  (`pip-audit`), plus `uv` caching across all CI jobs.
- Release workflow: on `v*` tag, builds and publishes to PyPI via Trusted
  Publishing (OIDC) and creates a GitHub release with artifacts.
- Release workflow also publishes the manifest to the official MCP Registry
  (GitHub OIDC, no token), stamping `server.json` with the tag version so the
  registry never lags the released package.
- Multi-arch Docker image (`linux/amd64`, `linux/arm64`) published to
  `ghcr.io/tracegazer/invgate-service-desk-mcp` on every release, and exposed as
  an `oci` package in `server.json` so container users are discoverable via the
  registry.
- Release workflow publishes the `.mcpb` bundle to Smithery on each tag
  (gated on a `SMITHERY_API_KEY` secret; skipped with a warning if unset).
- The `.mcpb` bundle is attached as an asset to every GitHub Release (same
  artifact used for Smithery), enabling one-click install into Claude Desktop.
  Documented prominently near the top of the README.
- Standalone `workflow_dispatch` workflows to republish to the MCP Registry and
  to Smithery without cutting a new release.
- Dependabot configuration for Python deps and GitHub Actions.
- `SECURITY.md`, `CONTRIBUTING.md` (with a release checklist), `CHANGELOG.md`,
  issue forms, and a pull-request template.

### Changed
- `__version__` is now derived from package metadata instead of a hardcoded
  string, removing version drift between `__init__.py` and `pyproject.toml`.
- Expanded Ruff lint rule set (`E`, `F`, `I`, `UP`, `B`, `SIM`, `RUF`) and applied
  fixes.
- Package maturity bumped from Alpha to Beta.

## [0.1.3] - 2026-06-07

### Added
- Smithery MCPB bundle (`bundle/manifest.json` + `scripts/build-mcpb.sh`).
- MCP registry metadata (official registry / Glama / Smithery).

### Removed
- Obsolete container-deploy files.

## [0.1.2] - 2026-06-07

### Added
- Granular write profiles (`none` / `support` / `full`) via
  `INVGATE_WRITE_PROFILE`, with `INVGATE_ENABLE_WRITES` kept as a legacy alias
  for `full`.

## [0.1.1] - 2026-06-04

### Added
- Initial release: 96 tools across 11 InvGate Service Desk domains, read-only by
  default with opt-in write tools, and optional OpenTelemetry observability.

[Unreleased]: https://github.com/tracegazer/invgate-service-desk-mcp/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/tracegazer/invgate-service-desk-mcp/compare/v0.1.3...v0.2.0
[0.1.3]: https://github.com/tracegazer/invgate-service-desk-mcp/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/tracegazer/invgate-service-desk-mcp/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/tracegazer/invgate-service-desk-mcp/releases/tag/v0.1.1
