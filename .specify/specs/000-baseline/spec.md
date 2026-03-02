# Specification: Baseline

> **Spec ID:** 000-baseline
> **Status:** Implemented
> **Version:** 0.3.0
> **Author:** crunchtools.com
> **Date:** 2026-03-02

## Overview

Baseline specification for mcp-request-tracker-crunchtools v0.3.0, documenting all 16 tools across 6 categories that provide secure access to the Request Tracker REST 1.0 API.

---

## Tools (16)

### Search/View Tools (5)

| Tool | RT API Endpoint | Description |
|------|-----------------|-------------|
| `search_tickets` | `GET search/ticket` | Search tickets using RT query syntax |
| `get_ticket` | `GET ticket/{id}/show` | Get ticket details |
| `get_ticket_history` | `GET ticket/{id}/history` | Get ticket history/changelog |
| `get_my_open_tickets` | `GET search/ticket` | Get open tickets for a user |
| `get_new_tickets` | `GET search/ticket` | Get new/unassigned tickets |

### Update Tools (5)

| Tool | RT API Endpoint | Description |
|------|-----------------|-------------|
| `set_ticket_owner` | `POST ticket/{id}/edit` | Set ticket owner |
| `set_ticket_status` | `POST ticket/{id}/edit` | Set ticket status |
| `resolve_ticket` | `POST ticket/{id}/edit` | Resolve/close a ticket with optional comment |
| `open_ticket` | `POST ticket/{id}/edit` | Open a ticket with optional owner |
| `take_ticket` | `POST ticket/{id}/edit` | Take ownership and open |

### Time Tracking Tools (2)

| Tool | RT API Endpoint | Description |
|------|-----------------|-------------|
| `set_time_worked` | `POST ticket/{id}/edit` | Set total time worked |
| `add_time_worked` | `POST ticket/{id}/edit` | Add time to existing total |

### Communication Tools (2)

| Tool | RT API Endpoint | Description |
|------|-----------------|-------------|
| `add_ticket_comment` | `POST ticket/{id}/comment` | Add private comment (not visible to requestor) |
| `reply_to_ticket` | `POST ticket/{id}/comment` | Add correspondence (visible to requestor) |

### Creation Tools (1)

| Tool | RT API Endpoint | Description |
|------|-----------------|-------------|
| `create_ticket` | `POST ticket/new` | Create a new ticket |

### Workflow Tools (1)

| Tool | RT API Endpoint | Description |
|------|-----------------|-------------|
| `complete_weekly_checklist` | Multiple | Take, open, correspond, time, comment, resolve |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RT_URL` | Yes | — | Base URL of RT server |
| `RT_USER` | Yes | — | RT username for authentication |
| `RT_PASS` | Yes | — | RT password for authentication |
| `RT_HTTP_USER` | No | — | HTTP Basic Auth username (if RT behind basic auth) |
| `RT_HTTP_PASS` | No | — | HTTP Basic Auth password (if RT behind basic auth) |

---

## Error Hierarchy

```
RTError
├── ConfigurationError
├── AuthenticationError
├── TicketNotFoundError
├── PermissionError
└── RTApiError
```

---

## Module Structure

```
src/mcp_request_tracker_crunchtools/
├── __init__.py          # Entry point, version, CLI args
├── __main__.py          # python -m support
├── server.py            # FastMCP server, @mcp.tool() wrappers
├── client.py            # httpx async client, RT REST 1.0 API
├── config.py            # SecretStr credentials, API base URL
├── errors.py            # RTError hierarchy with credential scrubbing
└── tools/
    ├── __init__.py      # Re-exports all 16 tool functions
    └── tickets.py       # Pure async functions for all ticket operations
```

---

## Test Coverage

| Test File | Tests | What It Covers |
|-----------|------:|----------------|
| `test_tools.py` | 18+ | Tool count, imports, mocked API (search, view, update, time, communication, creation, workflow) |
| `test_validation.py` | 10 | Config required vars, password hiding, error sanitization, response parsing |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 0.3.0 | 2026-03-02 | Two-layer refactor, gourmand, spec-kit, mocked tests, pre-commit, issue templates |
| 0.1.1 | 2026-02-28 | MCP Registry publication, dual container push |
| 0.1.0 | 2026-02-27 | Initial release with 16 tools |
