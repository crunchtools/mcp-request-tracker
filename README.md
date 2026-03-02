# MCP Request Tracker CrunchTools

A secure MCP (Model Context Protocol) server for Request Tracker (RT) ticket management.

## Features

- **Secure Credential Handling**: Passwords stored as SecretStr, never logged
- **Full Ticket Management**: Search, view, create, update, and resolve tickets
- **Time Tracking**: Track time worked on tickets
- **Workflow Automation**: Pre-built workflows like checklist completion
- **Cross-Platform**: Works on Linux, macOS, and Windows

## Installation

### Option 1: Using uvx (Recommended)

```bash
uvx mcp-request-tracker-crunchtools
```

### Option 2: Using pip

```bash
pip install mcp-request-tracker-crunchtools
```

### Option 3: Using Container

```bash
podman run -e RT_URL=... -e RT_USER=... -e RT_PASS=... quay.io/crunchtools/mcp-request-tracker
```

## Configuration

Set the following environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `RT_URL` | Yes | Base URL of your RT server |
| `RT_USER` | Yes | RT username |
| `RT_PASS` | Yes | RT password |
| `RT_HTTP_USER` | No | HTTP Basic Auth username |
| `RT_HTTP_PASS` | No | HTTP Basic Auth password |

## Usage with Claude Code

### Using uvx

```bash
claude mcp add mcp-request-tracker-crunchtools \
    --env RT_URL=https://rt.example.com \
    --env RT_USER=your_username \
    --env RT_PASS=your_password \
    -- uvx mcp-request-tracker-crunchtools
```

### Using Container

```bash
claude mcp add mcp-request-tracker-crunchtools \
    --env RT_URL=https://rt.example.com \
    --env RT_USER=your_username \
    --env RT_PASS=your_password \
    -- podman run -i --rm -e RT_URL -e RT_USER -e RT_PASS quay.io/crunchtools/mcp-request-tracker
```

## Available Tools

### Search and View
- `search_tickets` - Search tickets using RT query syntax
- `get_ticket` - Get ticket details
- `get_ticket_history` - Get ticket history/changelog
- `get_my_open_tickets` - Get open tickets for a user
- `get_new_tickets` - Get new/unassigned tickets

### Update Tickets
- `set_ticket_owner` - Set ticket owner
- `set_ticket_status` - Set ticket status
- `open_ticket` - Open a ticket
- `resolve_ticket` - Resolve/close a ticket
- `take_ticket` - Take ownership and open

### Time Tracking
- `set_time_worked` - Set total time worked
- `add_time_worked` - Add time to existing time

### Communication
- `add_ticket_comment` - Add private comment (not visible to requestor)
- `reply_to_ticket` - Add correspondence (visible to requestor)

### Creation
- `create_ticket` - Create a new ticket

### Workflows
- `complete_weekly_checklist` - Complete a weekly checklist ticket with results

## RT Query Syntax Examples

```
Status = 'new'
Status = 'open' AND Owner = 'scott'
Subject LIKE 'checklist'
Queue = 'Professional'
Created > '2025-01-01'
Owner = 'Nobody'
```

## Security

This server is built with security in mind:

- **SecretStr**: Passwords are stored using Pydantic's SecretStr to prevent accidental logging
- **Error Sanitization**: Credentials are scrubbed from all error messages
- **No Filesystem Access**: The server never reads or writes files
- **No Shell Execution**: No subprocess or shell commands
- **Minimal Dependencies**: Only essential packages to reduce attack surface
- **Automated CVE Scanning**: Weekly security scans via GitHub Actions
- **Container Security**: Built on Hummingbird images with minimal CVE count

See [SECURITY.md](SECURITY.md) for the full security design document.

## Development

```bash
# Clone the repository
git clone https://github.com/crunchtools/mcp-request-tracker.git
cd mcp-request-tracker

# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Lint
uv run ruff check src tests

# Type check
uv run mypy src
```

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
See [LICENSE](LICENSE) for details.

<!-- mcp-name: io.github.crunchtools/request-tracker -->
