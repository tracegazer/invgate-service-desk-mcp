#!/usr/bin/env bash
# Build the Smithery MCPB bundle (invgate-service-desk.mcpb).
#
# The version is taken from pyproject.toml at build time, so the bundle always
# matches the released package — there is no version to maintain in the manifest.
# Publish with:  smithery mcp publish ./invgate-service-desk.mcpb -n tracegazer/invgate-service-desk-mcp
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION=$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
echo "building MCPB bundle for v$VERSION"

BUILD=$(mktemp -d)
trap 'rm -rf "$BUILD"' EXIT

# Copy the manifest into a scratch dir and stamp the live version, leaving the
# committed bundle/manifest.json untouched (no spurious git diffs).
python3 - "$VERSION" "$BUILD/manifest.json" <<'PY'
import json, sys
m = json.load(open("bundle/manifest.json"))
m["version"] = sys.argv[1]
with open(sys.argv[2], "w") as fh:
    json.dump(m, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
PY

npx -y @anthropic-ai/mcpb validate "$BUILD/manifest.json"
( cd "$BUILD" && npx -y @anthropic-ai/mcpb pack . bundle.mcpb )
mv "$BUILD/bundle.mcpb" invgate-service-desk.mcpb
echo "built invgate-service-desk.mcpb (v$VERSION)"
