"""Custom exceptions for MCP Request Tracker.

All exceptions are designed to be safe - they never expose
sensitive information like passwords or tokens.
"""

import os


class RTError(Exception):
    """Base exception for RT-related errors."""

    def __init__(self, message: str) -> None:
        sanitized_message = message
        for var in ("RT_PASS", "RT_HTTP_PASS"):
            value = os.environ.get(var, "")
            if value:
                sanitized_message = sanitized_message.replace(value, "***")
        super().__init__(sanitized_message)


class ConfigurationError(RTError):
    """Raised when configuration is invalid or missing."""


class AuthenticationError(RTError):
    """Raised when authentication fails."""


class TicketNotFoundError(RTError):
    """Raised when a ticket is not found."""


class PermissionError(RTError):
    """Raised when the user lacks permission for an operation."""


class RTApiError(RTError):
    """Raised when the RT API returns an error."""

    def __init__(self, status: int, message: str) -> None:
        self.status = status
        super().__init__(f"RT API error {status}: {message}")
