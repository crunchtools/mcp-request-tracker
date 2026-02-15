# Security Design Document

This document describes the security architecture of mcp-request-tracker-crunchtools.

## 1. Threat Model

### 1.1 Assets to Protect

| Asset | Sensitivity | Impact if Compromised |
|-------|-------------|----------------------|
| RT Password | Critical | Full account access, ticket manipulation |
| RT Username | High | Account identification for attacks |
| HTTP Basic Auth | Critical | Bypass authentication layer |
| Ticket Data | High | Sensitive business information exposure |

### 1.2 Threat Actors

| Actor | Capability | Motivation |
|-------|------------|------------|
| Malicious AI Agent | Can craft tool inputs | Data exfiltration, privilege escalation |
| Local Attacker | Access to filesystem | Credential theft, configuration tampering |
| Network Attacker | Man-in-the-middle | Credential interception (mitigated by TLS) |

### 1.3 Attack Vectors

| Vector | Description | Mitigation |
|--------|-------------|------------|
| **Credential Leakage** | Password exposed in logs, errors, or outputs | SecretStr, scrubbed error messages |
| **Input Injection** | Malicious ticket queries | Input validation, parameterized queries |
| **SSRF** | Redirect API calls to internal services | URL validation on RT_URL |
| **Supply Chain** | Compromised dependencies | Automated CVE scanning |

## 2. Security Architecture

### 2.1 Defense in Depth Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Input Validation                                    │
│ - Pydantic types for all tool inputs                        │
│ - Integer validation for ticket IDs                         │
│ - String sanitization for queries                           │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Credential Handling                                 │
│ - Environment variables only (never file, never arg)        │
│ - SecretStr prevents accidental logging                     │
│ - Never include credentials in error messages               │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: API Client Hardening                               │
│ - Configured RT URL only (no dynamic URLs)                  │
│ - TLS certificate validation (default in httpx)            │
│ - Request timeout enforcement (30s)                         │
├─────────────────────────────────────────────────────────────┤
│ Layer 4: Output Sanitization                                │
│ - Redact credentials from any error messages                │
│ - Structured errors without internal details                │
├─────────────────────────────────────────────────────────────┤
│ Layer 5: Runtime Protection                                 │
│ - No filesystem access                                      │
│ - No shell execution (subprocess)                           │
│ - No dynamic code evaluation (eval/exec)                    │
│ - Type-safe with Pydantic                                   │
├─────────────────────────────────────────────────────────────┤
│ Layer 6: Supply Chain Security                              │
│ - Automated CVE scanning via GitHub Actions                 │
│ - Dependabot alerts enabled                                 │
│ - Weekly dependency audits                                  │
│ - Container built on Hummingbird for minimal CVEs           │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Credential Security

Credentials are handled with multiple protections:

```python
from pydantic import SecretStr

class Config:
    def __init__(self) -> None:
        password = os.environ.get("RT_PASS")
        if not password:
            raise ConfigurationError("RT_PASS required")

        # Store as SecretStr to prevent accidental logging
        self._password = SecretStr(password)

    @property
    def password(self) -> str:
        """Get password value - use sparingly."""
        return self._password.get_secret_value()

    def __repr__(self) -> str:
        return "Config(url=..., user=..., password=***)"
```

### 2.3 Error Handling

Errors are sanitized before being returned:

```python
class RTError(Exception):
    def __init__(self, message: str) -> None:
        # Sanitize message to remove any credential references
        safe_message = self._sanitize(message)
        super().__init__(safe_message)

    def _sanitize(self, message: str) -> str:
        """Remove any credential values from error messages."""
        sensitive_vars = ["RT_PASS", "RT_HTTP_PASS"]
        result = message
        for var in sensitive_vars:
            value = os.environ.get(var, "")
            if value:
                result = result.replace(value, "***")
        return result
```

## 3. Required Permissions

### 3.1 RT User Permissions

The RT user account should have the minimum permissions needed:

**Read-Only Operations:**
- SeeTicket
- ShowTicket
- ShowTicketComments

**Full Management:**
- SeeTicket
- ShowTicket
- ShowTicketComments
- CreateTicket
- ModifyTicket
- CommentOnTicket
- ReplyToTicket
- OwnTicket
- TakeTicket

## 4. Supply Chain Security

### 4.1 Automated CVE Scanning

This project uses GitHub Actions to automatically scan for CVEs:

1. **Weekly Scheduled Scans**: Every Monday at 9 AM UTC
2. **PR Checks**: Every pull request is scanned before merge
3. **Automatic Issues**: When CVEs are found, an issue is created
4. **Dependabot**: Enabled for automatic security updates

### 4.2 Container Security

The container image is built on **Hummingbird Python** from Project Hummingbird:

| Advantage | Description |
|-----------|-------------|
| **Minimal CVE Count** | Dramatically reduced attack surface |
| **Rapid Security Updates** | Security patches applied promptly |
| **Non-Root Default** | Runs as non-root user |
| **Production Ready** | Proper signal handling |

## 5. Security Checklist

Before each release:

- [ ] All inputs validated through Pydantic types
- [ ] No credential exposure in logs or errors
- [ ] No filesystem operations
- [ ] No shell execution
- [ ] No eval/exec
- [ ] Error messages don't leak internals
- [ ] Dependencies scanned for CVEs
- [ ] Container rebuilt with latest Hummingbird base

## 6. Reporting Security Issues

Please report security issues to security@crunchtools.com or open a private security advisory on GitHub.

Do NOT open public issues for security vulnerabilities.
