"""Custom exceptions for MCP Request Tracker.

All exceptions are designed to be safe - they never expose
sensitive information like passwords or tokens.
"""

import os


class RTError(Exception):
    """Base exception for RT-related errors."""

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


class ConfigurationError(RTError):
    """Raised when configuration is invalid or missing."""

    pass


class AuthenticationError(RTError):
    """Raised when authentication fails."""

    pass


class TicketNotFoundError(RTError):
    """Raised when a ticket is not found."""

    pass


class PermissionError(RTError):
    """Raised when the user lacks permission for an operation."""

    pass


class RTApiError(RTError):
    """Raised when the RT API returns an error."""

    def __init__(self, status: int, message: str) -> None:
        self.status = status
        super().__init__(f"RT API error {status}: {message}")
