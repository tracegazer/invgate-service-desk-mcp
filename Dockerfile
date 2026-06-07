# Container image for Smithery (and anyone who wants to run the server in Docker).
# The server speaks MCP over stdio; Smithery builds this image and launches the
# console script, passing configuration as environment variables.
FROM python:3.12-slim

WORKDIR /app

# Install the package from source. Copying only what's needed keeps the layer small.
COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

# stdio transport is the default; no port is exposed.
ENTRYPOINT ["invgate-service-desk-mcp"]
