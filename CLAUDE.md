# Claude Code Instructions

This is a secure MCP server for Request Tracker (RT) ticket management.

## Quick Start

### Option 1: Using uvx (Recommended)

```bash
claude mcp add mcp-request-tracker-crunchtools \
    --env RT_URL=https://rt.example.com \
    --env RT_USER=your_username \
    --env RT_PASS=your_password \
    -- uvx mcp-request-tracker-crunchtools
```

### Option 2: Using Container

```bash
claude mcp add mcp-request-tracker-crunchtools \
    --env RT_URL=https://rt.example.com \
    --env RT_USER=your_username \
    --env RT_PASS=your_password \
    -- podman run -i --rm -e RT_URL -e RT_USER -e RT_PASS quay.io/crunchtools/mcp-request-tracker
```

### Option 3: Local Development

```bash
cd ~/Projects/crunchtools/mcp-request-tracker
claude mcp add mcp-request-tracker-crunchtools \
    --env RT_URL=https://rt.example.com \
    --env RT_USER=your_username \
    --env RT_PASS=your_password \
    -- uv run mcp-request-tracker-crunchtools
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `RT_URL` | Yes | Base URL of your RT server (e.g., `https://rt.example.com`) |
| `RT_USER` | Yes | RT username for authentication |
| `RT_PASS` | Yes | RT password for authentication |
| `RT_HTTP_USER` | No | HTTP Basic Auth username (if RT is behind basic auth) |
| `RT_HTTP_PASS` | No | HTTP Basic Auth password (if RT is behind basic auth) |

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
- `add_ticket_comment` - Add private comment
- `reply_to_ticket` - Add correspondence (visible to requestor)

### Creation
- `create_ticket` - Create a new ticket

### Workflows
- `complete_weekly_checklist` - Complete a weekly checklist ticket

## RT Query Syntax Examples

```
Status = 'new'
Status = 'open' AND Owner = 'scott'
Subject LIKE 'checklist'
Queue = 'Professional'
Created > '2025-01-01'
Owner = 'Nobody'
```

## Example Usage

```
User: Show me my open tickets
User: Search for tickets with "checklist" in the subject
User: Get details for ticket #1234
User: Take ownership of ticket #1234
User: Add 30 minutes to ticket #1234
User: Resolve ticket #1234 with comment "Fixed"
```

## Security Best Practices

- **Never commit credentials**: Use environment variables, not config files
- **Principle of least privilege**: Create an RT user with only needed permissions
- **Rotate passwords regularly**: Update RT_PASS periodically
- **Use HTTPS**: Ensure RT_URL uses https://

## Development

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Lint
uv run ruff check src tests

# Type check
uv run mypy src
```
