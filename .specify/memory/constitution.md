# mcp-request-tracker-crunchtools Constitution

> **Version:** 1.1.0
> **Ratified:** 2026-03-02
> **Amended:** 2026-10-02
> **Status:** Active
> **Inherits:** [crunchtools/constitution](https://github.com/crunchtools/constitution) v1.21.0
> **Profile:** MCP Server

This file holds what is specific to mcp-request-tracker. The fleet rules and
the MCP Server profile (five-layer security model, two-layer tools,
distribution channels, transport modes, quality gates, Gourmand) apply at the
inherited version and are checked against this repo's files by
`constitution.yml`. They are not restated here.

## Security Model Specifics

- **Credentials:** `RT_URL`, `RT_USER` and `RT_PASS` are required;
  `RT_HTTP_USER` and `RT_HTTP_PASS` optionally add HTTP Basic Auth in front of
  RT. Both passwords are `SecretStr`, environment-only, never shown by
  `Config.__repr__`/`__str__`, and scrubbed from error messages by
  `RTError._sanitize()`. Tests cover the scrubbing of each.
- **Input limits:** ticket IDs are integers; priority is enforced to 0-99;
  queries and content are sanitized strings.
- **API:** RT REST 1.0. Authentication is a form-data POST, not a Bearer
  header. TLS certificates are always validated; requests time out after
  30s.
- **Surface:** the configured RT instance only, no filesystem access, shell
  execution or code evaluation.

## Single-Instance Design

The server talks to one RT instance, set by `RT_URL`. The URL is validated at
startup and held immutably in the `Config` singleton; no tool accepts a
dynamic URL.

## RT REST 1.0 Responses

RT REST 1.0 answers in text, not JSON. Parsing of that format (status line,
ticket bodies, search results) is tested directly, and mocks return text of
the form `RT/4.4.4 {status} {message}\n\n{body}`.

## Instance

| Context | Name |
|---------|------|
| GitHub repo | `crunchtools/mcp-request-tracker` |
| PyPI package | `mcp-request-tracker-crunchtools` |
| Python module | `mcp_request_tracker_crunchtools` |
| Container image | `quay.io/crunchtools/mcp-request-tracker` |
| systemd service | `mcp-request-tracker.service` |
| HTTP port | 8013 |

## History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial constitution |
| 1.0.1 | 2026-03-16 | Container Conventions section added |
| 1.1.0 | 2026-10-02 | Manifest under constitution v1.18.0: profile restatement removed, mcp-request-tracker specifics kept |
