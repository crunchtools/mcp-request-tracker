# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/) and this project adheres to
[Semantic Versioning](https://semver.org/).

Entries prior to 2026-09-19 are back-filled from GitHub Release notes (RT #1484).

## [Unreleased]

## [0.5.0] - 2026-10-10

### Added
- The five tools that only read (`search_tickets`, `get_ticket`,
  `get_ticket_history`, `get_my_open_tickets`, `get_new_tickets`) publish
  `readOnlyHint: true`. A gateway uses it to decide whether an invalid optional
  argument may be dropped or must refuse the call (crunchtools/constitution#35).
- Tests pin every registered tool into `READ_ONLY` or `WRITES`, and check that
  no read-only tool sends RT a `content` form, which is how REST 1.0 writes.

### Changed
- Inherits constitution v1.22.0; the workflow pins and the pre-commit hook rev
  move with it.

### Fixed
- `server.json` said 0.3.0 through the 0.4.0 release; it carries the release
  version again.

### Changed
- Constitution is now a v1.18.0 manifest: only repo-specific facts remain;
  fleet and profile rules apply by reference.
- Constitution validation is pinned via `.github/workflows/constitution.yml`.
- Dependabot auto-merges GitHub Actions minor and patch updates.

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
