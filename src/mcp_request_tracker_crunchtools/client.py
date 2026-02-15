"""Request Tracker REST 1.0 API Client.

This module provides a secure async client for the RT REST 1.0 API.
All credentials are handled via the Config class using SecretStr.
"""

import logging
import re
from typing import Any

import httpx

from .config import Config
from .errors import RTApiError

logger = logging.getLogger(__name__)


class RTClient:
    """Client for Request Tracker REST 1.0 API.

    This client handles authentication and provides methods for
    all common RT operations. Credentials are never logged.
    """

    def __init__(self, config: Config) -> None:
        """Initialize client with configuration.

        Args:
            config: Configuration object with credentials.
        """
        self._config = config
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with authentication."""
        if self._client is None:
            auth = None
            if self._config.http_user and self._config.http_password:
                auth = httpx.BasicAuth(self._config.http_user, self._config.http_password)

            self._client = httpx.AsyncClient(
                auth=auth,
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client

    async def _request(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> str:
        """Make authenticated request to RT API.

        Args:
            endpoint: API endpoint path.
            data: Form data to send.
            params: Query parameters.

        Returns:
            Response text from RT.

        Raises:
            httpx.HTTPError: On HTTP errors.
        """
        client = await self._get_client()
        url = f"{self._config.api_base_url}/{endpoint}"

        # RT REST 1.0 always needs login credentials in form data
        form_data = {
            "user": self._config.username,
            "pass": self._config.password,
        }
        if data:
            form_data.update(data)

        # RT REST 1.0 uses POST for authentication even on "GET" operations
        # The params become query string parameters
        if params:
            # Build query string manually
            query_parts = [f"{k}={v}" for k, v in params.items()]
            if "?" in url:
                url = url + "&" + "&".join(query_parts)
            else:
                url = url + "?" + "&".join(query_parts)

        logger.debug("Making request to %s", endpoint)
        response = await client.post(url, data=form_data)
        response.raise_for_status()
        return response.text

    def _parse_response(self, text: str) -> tuple[int, str, str]:
        """Parse RT response into status code, message, and body."""
        lines = text.strip().split("\n")
        if not lines:
            return 500, "Empty response", ""

        # First line is like "RT/4.4.4 200 Ok"
        first_line = lines[0]
        match = re.match(r"RT/[\d.]+ (\d+) (.+)", first_line)
        if match:
            status = int(match.group(1))
            message = match.group(2)
            body = "\n".join(lines[1:]).strip()
            return status, message, body

        return 500, "Invalid response format", text

    def _parse_ticket(self, text: str) -> dict[str, Any]:
        """Parse ticket show response into dictionary."""
        result: dict[str, Any] = {}
        current_key: str | None = None
        current_value: list[str] = []

        for line in text.split("\n"):
            if not line.strip():
                continue

            # Check for key: value pattern
            match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(.*)$", line)
            if match:
                # Save previous key if exists
                if current_key:
                    result[current_key] = "\n".join(current_value).strip()

                current_key = match.group(1)
                current_value = [match.group(2).strip()]
            elif current_key and line.startswith(" "):
                # Continuation of previous value
                current_value.append(line.strip())

        # Save last key
        if current_key:
            result[current_key] = "\n".join(current_value).strip()

        return result

    def _parse_search_results(self, text: str) -> list[dict[str, str]]:
        """Parse search results into list of tickets."""
        results: list[dict[str, str]] = []
        for raw_line in text.split("\n"):
            stripped = raw_line.strip()
            if not stripped:
                continue
            # Format: "123: Subject here"
            match = re.match(r"^(\d+): (.+)$", stripped)
            if match:
                results.append({
                    "id": match.group(1),
                    "Subject": match.group(2),
                })
        return results

    async def search_tickets(
        self, query: str, order_by: str = "-Created"
    ) -> list[dict[str, str]]:
        """Search for tickets using RT query syntax.

        Args:
            query: RT query string.
            order_by: Field to order by, prefix with - for descending.

        Returns:
            List of matching tickets with id and Subject.

        Raises:
            RTApiError: On API errors.
        """
        params = {
            "query": query,
            "orderby": order_by,
        }
        response = await self._request("search/ticket", params=params)
        status, message, body = self._parse_response(response)

        if status != 200:
            raise RTApiError(status, message)

        return self._parse_search_results(body)

    async def get_ticket(self, ticket_id: int | str) -> dict[str, Any]:
        """Get ticket details.

        Args:
            ticket_id: The ticket ID number.

        Returns:
            Dictionary of ticket fields.

        Raises:
            RTApiError: On API errors.
        """
        response = await self._request(f"ticket/{ticket_id}/show")
        status, message, body = self._parse_response(response)

        if status != 200:
            raise RTApiError(status, message)

        return self._parse_ticket(body)

    async def get_ticket_history(self, ticket_id: int | str) -> str:
        """Get ticket history.

        Args:
            ticket_id: The ticket ID number.

        Returns:
            Formatted history text.

        Raises:
            RTApiError: On API errors.
        """
        response = await self._request(
            f"ticket/{ticket_id}/history", params={"format": "l"}
        )
        status, message, body = self._parse_response(response)

        if status != 200:
            raise RTApiError(status, message)

        return body

    async def update_ticket(self, ticket_id: int | str, **fields: Any) -> str:
        """Update ticket fields.

        Args:
            ticket_id: The ticket ID number.
            **fields: Field name/value pairs to update.

        Returns:
            Response body from RT.

        Raises:
            RTApiError: On API errors.
        """
        # Build content in RT format
        content_lines = []
        for key, value in fields.items():
            content_lines.append(f"{key}: {value}")

        content = "\n".join(content_lines)

        response = await self._request(
            f"ticket/{ticket_id}/edit", data={"content": content}
        )
        status, message, body = self._parse_response(response)

        if status != 200:
            raise RTApiError(status, f"{message} - {body}")

        return body

    async def set_owner(self, ticket_id: int | str, owner: str) -> str:
        """Set ticket owner."""
        return await self.update_ticket(ticket_id, Owner=owner)

    async def set_status(self, ticket_id: int | str, status: str) -> str:
        """Set ticket status."""
        return await self.update_ticket(ticket_id, Status=status)

    async def set_time_worked(self, ticket_id: int | str, minutes: int) -> str:
        """Set time worked on ticket (in minutes)."""
        return await self.update_ticket(ticket_id, TimeWorked=str(minutes))

    async def add_time_worked(self, ticket_id: int | str, minutes: int) -> str:
        """Add time to time worked on ticket (in minutes)."""
        # Get current time worked
        ticket = await self.get_ticket(ticket_id)
        current = int(ticket.get("TimeWorked", "0") or "0")
        new_total = current + minutes
        return await self.update_ticket(ticket_id, TimeWorked=str(new_total))

    def _format_multiline_text(self, text: str) -> str:
        """Format multiline text for RT REST API.

        RT REST API 1.0 requires continuation lines to be prefixed with a space.
        """
        lines = text.split("\n")
        if len(lines) <= 1:
            return text
        # First line stays as-is, subsequent lines get prefixed with a space
        formatted_lines = [lines[0]] + [" " + line for line in lines[1:]]
        return "\n".join(formatted_lines)

    async def correspond(self, ticket_id: int | str, text: str) -> str:
        """Add correspondence (reply) to ticket."""
        formatted_text = self._format_multiline_text(text)
        content = f"id: {ticket_id}\nAction: correspond\nText: {formatted_text}"
        response = await self._request(
            f"ticket/{ticket_id}/comment", data={"content": content}
        )
        status, message, body = self._parse_response(response)

        if status != 200:
            raise RTApiError(status, f"{message} - {body}")

        return body

    async def comment(self, ticket_id: int | str, text: str) -> str:
        """Add comment (private note) to ticket."""
        formatted_text = self._format_multiline_text(text)
        content = f"id: {ticket_id}\nAction: comment\nText: {formatted_text}"
        response = await self._request(
            f"ticket/{ticket_id}/comment", data={"content": content}
        )
        status, message, body = self._parse_response(response)

        if status != 200:
            raise RTApiError(status, f"{message} - {body}")

        return body

    async def create_ticket(
        self,
        queue: str,
        subject: str,
        text: str = "",
        requestor: str = "",
        **extra_fields: Any,
    ) -> str:
        """Create a new ticket.

        Args:
            queue: Queue name.
            subject: Ticket subject.
            text: Initial ticket content.
            requestor: Email of the requestor.
            **extra_fields: Additional fields.

        Returns:
            Created ticket ID.

        Raises:
            RTApiError: On API errors.
        """
        content_lines = [
            f"Queue: {queue}",
            f"Subject: {subject}",
        ]
        if requestor:
            content_lines.append(f"Requestor: {requestor}")
        if text:
            formatted_text = self._format_multiline_text(text)
            content_lines.append(f"Text: {formatted_text}")

        for key, value in extra_fields.items():
            content_lines.append(f"{key}: {value}")

        content = "\n".join(content_lines)

        response = await self._request("ticket/new", data={"content": content})
        status, message, body = self._parse_response(response)

        if status != 200:
            raise RTApiError(status, f"{message} - {body}")

        # Parse ticket ID from response like "# Ticket 123 created."
        match = re.search(r"Ticket (\d+) created", body)
        if match:
            return match.group(1)

        # Check for error patterns in the body
        if "Could not create ticket" in body or "No permission" in body:
            raise RTApiError(403, body.strip())

        return body.strip()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
