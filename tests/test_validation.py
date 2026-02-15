"""Tests for input validation and configuration."""

import os
from unittest.mock import patch

import pytest


class TestConfig:
    """Tests for configuration handling."""

    def test_config_requires_url(self) -> None:
        """Test that RT_URL is required."""
        from mcp_request_tracker_crunchtools.config import Config
        from mcp_request_tracker_crunchtools.errors import ConfigurationError

        with patch.dict(os.environ, {}, clear=True), pytest.raises(
            ConfigurationError, match="RT_URL"
        ):
            Config()

    def test_config_requires_user(self) -> None:
        """Test that RT_USER is required."""
        from mcp_request_tracker_crunchtools.config import Config
        from mcp_request_tracker_crunchtools.errors import ConfigurationError

        with patch.dict(
            os.environ, {"RT_URL": "https://rt.example.com"}, clear=True
        ), pytest.raises(ConfigurationError, match="RT_USER"):
            Config()

    def test_config_requires_pass(self) -> None:
        """Test that RT_PASS is required."""
        from mcp_request_tracker_crunchtools.config import Config
        from mcp_request_tracker_crunchtools.errors import ConfigurationError

        env = {"RT_URL": "https://rt.example.com", "RT_USER": "test"}
        with patch.dict(os.environ, env, clear=True), pytest.raises(
            ConfigurationError, match="RT_PASS"
        ):
            Config()

    def test_config_valid(self) -> None:
        """Test valid configuration."""
        env = {
            "RT_URL": "https://rt.example.com",
            "RT_USER": "test",
            "RT_PASS": "secret",
        }
        with patch.dict(os.environ, env, clear=True):
            from mcp_request_tracker_crunchtools.config import Config

            config = Config()
            assert config.url == "https://rt.example.com"
            assert config.username == "test"
            assert config.password == "secret"

    def test_config_repr_hides_password(self) -> None:
        """Test that repr never exposes password."""
        env = {
            "RT_URL": "https://rt.example.com",
            "RT_USER": "test",
            "RT_PASS": "supersecret",
        }
        with patch.dict(os.environ, env, clear=True):
            from mcp_request_tracker_crunchtools.config import Config

            config = Config()
            repr_str = repr(config)
            assert "supersecret" not in repr_str
            assert "***" in repr_str


class TestErrors:
    """Tests for error handling."""

    def test_error_sanitizes_password(self) -> None:
        """Test that errors sanitize passwords from messages."""
        env = {"RT_PASS": "mysecretpassword"}
        with patch.dict(os.environ, env, clear=True):
            from mcp_request_tracker_crunchtools.errors import RTError

            error = RTError("Connection failed with password mysecretpassword")
            assert "mysecretpassword" not in str(error)
            assert "***" in str(error)

    def test_error_sanitizes_http_password(self) -> None:
        """Test that errors sanitize HTTP passwords."""
        env = {"RT_HTTP_PASS": "httppassword123"}
        with patch.dict(os.environ, env, clear=True):
            from mcp_request_tracker_crunchtools.errors import RTError

            error = RTError("Auth failed: httppassword123")
            assert "httppassword123" not in str(error)
            assert "***" in str(error)


class TestClient:
    """Tests for RT client."""

    def test_client_response_parsing(self) -> None:
        """Test RT response parsing."""
        env = {
            "RT_URL": "https://rt.example.com",
            "RT_USER": "test",
            "RT_PASS": "secret",
        }
        with patch.dict(os.environ, env, clear=True):
            from mcp_request_tracker_crunchtools.client import RTClient
            from mcp_request_tracker_crunchtools.config import Config

            config = Config()
            client = RTClient(config)

            # Test successful response parsing
            response = "RT/4.4.4 200 Ok\n\nid: 123\nSubject: Test"
            status, message, body = client._parse_response(response)
            assert status == 200
            assert message == "Ok"
            assert "id: 123" in body

    def test_client_ticket_parsing(self) -> None:
        """Test ticket data parsing."""
        env = {
            "RT_URL": "https://rt.example.com",
            "RT_USER": "test",
            "RT_PASS": "secret",
        }
        with patch.dict(os.environ, env, clear=True):
            from mcp_request_tracker_crunchtools.client import RTClient
            from mcp_request_tracker_crunchtools.config import Config

            config = Config()
            client = RTClient(config)

            ticket_text = """id: 123
Subject: Test Ticket
Status: open
Owner: admin"""
            ticket = client._parse_ticket(ticket_text)
            assert ticket["id"] == "123"
            assert ticket["Subject"] == "Test Ticket"
            assert ticket["Status"] == "open"
            assert ticket["Owner"] == "admin"

    def test_client_search_parsing(self) -> None:
        """Test search result parsing."""
        env = {
            "RT_URL": "https://rt.example.com",
            "RT_USER": "test",
            "RT_PASS": "secret",
        }
        with patch.dict(os.environ, env, clear=True):
            from mcp_request_tracker_crunchtools.client import RTClient
            from mcp_request_tracker_crunchtools.config import Config

            config = Config()
            client = RTClient(config)

            search_text = """123: First Ticket
456: Second Ticket
789: Third Ticket"""
            results = client._parse_search_results(search_text)
            assert len(results) == 3
            assert results[0]["id"] == "123"
            assert results[0]["Subject"] == "First Ticket"
            assert results[2]["id"] == "789"
