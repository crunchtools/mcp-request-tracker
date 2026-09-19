# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

Entries prior to 2026-09-19 are back-filled from GitHub Release notes (RT #1484).

## [Unreleased]

## [0.4.0] - 2026-03-10

Tagged twice, as both `0.4.0` and `v0.4.0`; the GitHub Release is on the
unprefixed `0.4.0`. Constitution II requires the `vX.Y.Z` form.

### Added
- **New tool: `update_ticket`** — update ticket fields (Subject, Priority, Queue)
  via a single tool call. All fields are optional, so any subset can be updated.
  Wraps the existing `client.update_ticket()` method that was previously only
  used internally. Tool count: 16 → 17. Closes #1.
- All 5 quality gates passed (ruff, mypy, 40/40 pytest, gourmand, container
  build).

## [0.3.0] - 2026-03-02

V2 architecture upgrade.

### Added
- **Two-layer tool pattern**: `server.py` wrappers delegate to pure async
  functions in `tools/tickets.py`.
- **Governance framework**: `.specify/` with constitution, baseline spec, and
  templates.
- **Gourmand quality gate**: zero AI slop violations enforced in CI.
- **Comprehensive tests**: 37 mocked tests covering all 16 tools (up from 10).
- **Pre-commit hooks**: ruff check + format.
- **GitHub issue templates**: bug reports and feature requests.
- 16 tools — Search/View (5): search, get ticket, get history, my open, new
  tickets; Update (5): set owner, set status, resolve, open, take; Time Tracking
  (2): set time, add time; Communication (2): comment (private), reply (visible);
  Creation (1): create ticket; Workflows (1): complete weekly checklist.

## [0.1.0] - 2026-02-15

Initial release of MCP Request Tracker CrunchTools — a secure MCP server for
Request Tracker (RT) ticket management.

### Added
- Full ticket management: search, create, update, resolve.
- Time tracking and workflow automation.
- Secure credential handling with SecretStr.
- Container image at `quay.io/crunchtools/mcp-request-tracker`.
