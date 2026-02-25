# MCP Request Tracker CrunchTools Container
# Built on Hummingbird Python image (Red Hat UBI-based) for enterprise security
#
# Build:
#   podman build -t quay.io/crunchtools/mcp-request-tracker .
#
# Run:
#   podman run -e RT_URL=... -e RT_USER=... -e RT_PASS=... quay.io/crunchtools/mcp-request-tracker
#
# With Claude Code:
#   claude mcp add mcp-request-tracker-crunchtools \
#     --env RT_URL=https://rt.example.com \
#     --env RT_USER=your_user \
#     --env RT_PASS=your_pass \
#     -- podman run -i --rm -e RT_URL -e RT_USER -e RT_PASS quay.io/crunchtools/mcp-request-tracker

# Use Hummingbird Python image (Red Hat UBI-based with Python pre-installed)
FROM quay.io/hummingbird/python:latest

# Labels for container metadata
LABEL name="mcp-request-tracker-crunchtools" \
      version="0.1.0" \
      summary="Secure MCP server for Request Tracker ticket management" \
      description="A security-focused MCP server for Request Tracker built on Red Hat UBI" \
      maintainer="crunchtools.com" \
      url="https://github.com/crunchtools/mcp-request-tracker" \
      io.k8s.display-name="MCP Request Tracker CrunchTools" \
      io.openshift.tags="mcp,request-tracker,rt,tickets"

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package and dependencies
RUN pip install --no-cache-dir .

# Verify installation
RUN python -c "from mcp_request_tracker_crunchtools import main; print('Installation verified')"

# Default: stdio transport (use -i with podman run)
# HTTP:    --transport streamable-http (use -d -p 8000:8000 with podman run)
EXPOSE 8000
ENTRYPOINT ["python", "-m", "mcp_request_tracker_crunchtools"]
