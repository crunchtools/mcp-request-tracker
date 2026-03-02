# Claude Code Instructions

Secure MCP server for Request Tracker (RT) ticket management. 16 tools across 6 categories.

## Quick Start

```bash
# uvx (recommended)
claude mcp add mcp-request-tracker-crunchtools \
    --env RT_URL=https://rt.example.com \
    --env RT_USER=your_username \
    --env RT_PASS=your_password \
    -- uvx mcp-request-tracker-crunchtools

# Container
claude mcp add mcp-request-tracker-crunchtools \
    --env RT_URL=https://rt.example.com \
    --env RT_USER=your_username \
    --env RT_PASS=your_password \
    -- podman run -i --rm -e RT_URL -e RT_USER -e RT_PASS quay.io/crunchtools/mcp-request-tracker

# Local development
cd ~/Projects/crunchtools/mcp-request-tracker
claude mcp add mcp-request-tracker-crunchtools \
    --env RT_URL=https://rt.example.com \
    --env RT_USER=your_username \
    --env RT_PASS=your_password \
    -- uv run mcp-request-tracker-crunchtools
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RT_URL` | Yes | — | Base URL of RT server |
| `RT_USER` | Yes | — | RT username for authentication |
| `RT_PASS` | Yes | — | RT password for authentication |
| `RT_HTTP_USER` | No | — | HTTP Basic Auth username (if RT behind basic auth) |
| `RT_HTTP_PASS` | No | — | HTTP Basic Auth password (if RT behind basic auth) |

## Available Tools (16)

| Category | Tools | Operations |
|----------|------:|------------|
| Search/View | 5 | search, get ticket, get history, my open, new tickets |
| Update | 5 | set owner, set status, resolve, open, take |
| Time Tracking | 2 | set time, add time |
| Communication | 2 | comment (private), reply (visible) |
| Creation | 1 | create ticket |
| Workflows | 1 | complete weekly checklist |

Full tool inventory with API endpoints: `.specify/specs/000-baseline/spec.md`

## Example Usage

```
Show me my open tickets
Search for tickets with "checklist" in the subject
Get details for ticket #1234
Take ownership of ticket #1234
Add 30 minutes to ticket #1234
Resolve ticket #1234 with comment "Fixed"
Create a new ticket in Professional queue
Complete the weekly checklist for ticket #500
```

## Development

```bash
uv sync --all-extras                                                    # Install dependencies
uv run ruff check src tests                                             # Lint
uv run mypy src                                                         # Type check
RT_URL=https://rt.example.com RT_USER=test RT_PASS=test uv run pytest -v  # Tests (mocked)
gourmand --full .                                                       # AI slop detection
```

Quality gates, testing standards, and architecture: `.specify/memory/constitution.md`
