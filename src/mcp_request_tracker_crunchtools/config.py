"""Secure configuration handling.

This module handles all configuration including sensitive credentials.
Passwords are stored as SecretStr to prevent accidental logging.
"""

import logging
import os

from pydantic import SecretStr

from .errors import ConfigurationError

logger = logging.getLogger(__name__)


class Config:
    """Secure configuration handling.

    Passwords are stored as SecretStr and should only be accessed
    via properties when actually needed for API calls.
    """

    def __init__(self) -> None:
        """Initialize configuration from environment variables.

        Raises:
            ConfigurationError: If required environment variables are missing.
        """
        url = os.environ.get("RT_URL")
        if not url:
            raise ConfigurationError(
                "RT_URL environment variable required. "
                "Set it to your Request Tracker server URL."
            )

        username = os.environ.get("RT_USER")
        if not username:
            raise ConfigurationError(
                "RT_USER environment variable required. "
                "Set it to your Request Tracker username."
            )

        password = os.environ.get("RT_PASS")
        if not password:
            raise ConfigurationError(
                "RT_PASS environment variable required. "
                "Set it to your Request Tracker password."
            )

        self._url = url.rstrip("/")
        self._username = username
        # Store password as SecretStr to prevent accidental logging
        self._password = SecretStr(password)

        # Optional HTTP Basic Auth (if RT is behind basic auth)
        http_user = os.environ.get("RT_HTTP_USER")
        http_pass = os.environ.get("RT_HTTP_PASS")
        self._http_user = http_user
        self._http_password = SecretStr(http_pass) if http_pass else None

        logger.info("Configuration loaded successfully")

    @property
    def url(self) -> str:
        """Get RT server URL."""
        return self._url

    @property
    def username(self) -> str:
        """Get RT username."""
        return self._username

    @property
    def password(self) -> str:
        """Get password value for API calls.

        Use sparingly - only when making actual API calls.
        """
        return self._password.get_secret_value()

    @property
    def http_user(self) -> str | None:
        """Get HTTP Basic Auth username."""
        return self._http_user

    @property
    def http_password(self) -> str | None:
        """Get HTTP Basic Auth password for API calls.

        Use sparingly - only when making actual API calls.
        """
        if self._http_password is None:
            return None
        return self._http_password.get_secret_value()

    @property
    def api_base_url(self) -> str:
        """Get the REST API base URL.

        The endpoint path is appended to the configured RT URL.
        """
        return f"{self._url}/REST/1.0"

    def __repr__(self) -> str:
        """Safe repr that never exposes credentials."""
        return f"Config(url={self._url!r}, user={self._username!r}, password=***)"

    def __str__(self) -> str:
        """Safe str that never exposes credentials."""
        return f"Config(url={self._url!r}, user={self._username!r}, password=***)"


# Global configuration instance - initialized on first import
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance.

    This function lazily initializes the configuration on first call.
    Subsequent calls return the same instance.

    Returns:
        The global Config instance.

    Raises:
        ConfigurationError: If configuration is invalid.
    """
    global _config
    if _config is None:
        _config = Config()
    return _config
