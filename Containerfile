# MCP Request Tracker CrunchTools Container
# Built on Hummingbird Python image (Red Hat UBI-based) for enterprise security

# Stage 1: Builder (has a shell, dnf and build tools)
FROM quay.io/hummingbird/python:latest-builder AS builder
USER 0
WORKDIR /app
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

# Stage 2: Runtime (distroless -- no shell, no package manager)
FROM quay.io/hummingbird/python:latest

LABEL name="mcp-request-tracker-crunchtools" \
      version="0.4.0" \
      summary="Secure MCP server for Request Tracker ticket management" \
      description="A security-focused MCP server for Request Tracker built on Red Hat UBI" \
      maintainer="crunchtools.com" \
      url="https://github.com/crunchtools/mcp-request-tracker" \
      io.k8s.display-name="MCP Request Tracker CrunchTools" \
      io.openshift.tags="mcp,request-tracker,rt,tickets" \
      org.opencontainers.image.source="https://github.com/crunchtools/mcp-request-tracker" \
      org.opencontainers.image.description="Secure MCP server for Request Tracker ticket management" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later"

WORKDIR /app

COPY --from=builder /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Verify the install. Exec form: this stage has no /bin/sh for RUN's shell form.
RUN ["python3", "-c", "from mcp_request_tracker_crunchtools import main; print('Installation verified')"]

EXPOSE 8013
ENTRYPOINT ["python", "-m", "mcp_request_tracker_crunchtools"]
