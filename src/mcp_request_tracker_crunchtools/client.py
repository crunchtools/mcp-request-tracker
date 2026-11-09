"""Request Tracker REST 1.0 API Client.

This module provides a secure async client for the RT REST 1.0 API.
All credentials are handled via the Config class using SecretStr.
"""

import logging
import re
from importlib.metadata import version
from typing import Any
from urllib.parse import quote, quote_plus

import httpx

from .config import Config
from .errors import RTApiError

logger = logging.getLogger(__name__)

# An RT ticket history with attachments is the biggest body here.
MAX_RESPONSE_SIZE = 10 * 1024 * 1024
BODY_SNIPPET_CHARS = 200
ELLIPSIS = "..."

# Identify this client by name. httpx otherwise sends `python-httpx/<version>`,
# which bot protection answers with an HTML challenge page instead of the API --
# the failure that cost an afternoon on mcp-wordpress (RT #1596). The version
# comes from installed package metadata so it cannot drift from pyproject.toml.
USER_AGENT = (
    f"mcp-request-tracker-crunchtools/{version('mcp-request-tracker-crunchtools')} "
    "(+https://github.com/crunchtools/mcp-request-tracker)"
)


def _snippet(text: str, truncated: bool = False) -> str:
    """A short, single-line excerpt of some text, for an error message."""
    collapsed = " ".join(text.split())
    if not collapsed:
        return "<empty body>"
    if len(collapsed) > BODY_SNIPPET_CHARS or truncated:
        return collapsed[: BODY_SNIPPET_CHARS - len(ELLIPSIS)] + ELLIPSIS
    return collapsed


def _body_snippet(body: bytes) -> str:
    """A short, single-line excerpt of a response body, for an error message."""
    prefix = body[: BODY_SNIPPET_CHARS * 4]
    return _snippet(prefix.decode("utf-8", errors="replace"), truncated=len(body) > len(prefix))


def _where(response: httpx.Response) -> str:
    """Which request a response answered, for an error message.

    The URL actually requested, which matters here because this client follows
    redirects: an RT behind Cloudflare Access answers from somewhere else
    entirely, and that is the case `raise_for_status()` could not describe.
    """
    return (
        f"{response.request.method} {response.request.url} "
        f"(HTTP {response.status_code}, {response.headers.get('content-type', 'no content-type')})"
    )


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
                headers={"User-Agent": USER_AGENT},
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
            RTApiError: On a transport failure, an oversized body, or an
                unsuccessful status -- naming the request in each case, since
                `raise_for_status()` could not say which URL answered.
        """
        client = await self._get_client()
        url = f"{self._config.api_base_url}/{endpoint}"

        form_data = {
            "user": self._config.username,
            "pass": self._config.password,
        }
        if data:
            form_data.update(data)

        if params:
            query_parts = [f"{k}={v}" for k, v in params.items()]
            if "?" in url:
                url = url + "&" + "&".join(query_parts)
            else:
                url = url + "?" + "&".join(query_parts)

        logger.debug("Making request to %s", endpoint)
        request = client.build_request("POST", url, data=form_data)
        try:
            response = await client.send(request, stream=True)
            try:
                body = await self._read_capped(response)
            finally:
                await response.aclose()
        # The URL is named here too, not only on an HTTP status: httpx's own
        # exception message does not reliably carry it, and a timeout with no
        # endpoint in it is the hardest failure of the three to place.
        except httpx.TimeoutException as e:
            raise RTApiError(0, f"Request timeout: POST {url}: {e}") from e
        except httpx.RequestError as e:
            raise RTApiError(0, f"Request failed: POST {url}: {e}") from e

        if not response.is_success:
            raise RTApiError(
                response.status_code,
                f"{_where(response)} returned {self._safe_snippet(body)}",
            )
        return body.decode("utf-8", errors="replace")

    def _safe_snippet(self, body: bytes) -> str:
        """A body excerpt with this client's own credentials taken out.

        RT REST 1.0 takes `user` and `pass` in the POST body, so a page that
        echoes the request back -- a proxy debug page, an SSO interstitial --
        reflects the password. `RTApiError` does not scrub, unlike some of the
        other servers in the fleet, so it is done here, where the body is first
        turned into a message (Layer 1).

        Two things this has to get right, both of which a redact-then-truncate
        or raw-string-only version gets wrong:

        * The echoed body is FORM-ENCODED, so a password with a reserved
          character in it comes back percent-encoded -- `a&b` as `a%26b`, a
          space as `+` or `%20` -- and a raw replace would walk straight past
          it. Every encoding of the secret is replaced, not just the one that
          was configured.
        * The redaction happens BEFORE the snippet is cut. Truncating first
          leaves the tail of a password that straddles the boundary.

        The whole body is decoded for this, which is why it is only on the
        error path: the body is already bounded, and a partially redacted
        credential is worse than the work.
        """
        text = body.decode("utf-8", errors="replace")
        for secret in (self._config.password, self._config.http_password):
            if not secret:
                continue
            for encoded in {secret, quote(secret, safe=""), quote_plus(secret)}:
                text = text.replace(encoded, "***")
        return _snippet(text)

    async def _read_capped(self, response: httpx.Response) -> bytes:
        """Read the body, aborting as soon as it would pass MAX_RESPONSE_SIZE.

        There was no limit here at all: a ticket history with attachments, or
        anything else answering on that URL, was read whole into the process.
        Measured before each chunk is copied in, because `aiter_bytes()`
        promises nothing about chunk size.
        """
        declared = response.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > MAX_RESPONSE_SIZE:
            raise RTApiError(
                response.status_code,
                f"{_where(response)} declared {declared} bytes, over the "
                f"{MAX_RESPONSE_SIZE} byte limit",
            )
        body = bytearray()
        async for chunk in response.aiter_bytes():
            if len(body) + len(chunk) > MAX_RESPONSE_SIZE:
                raise RTApiError(
                    response.status_code,
                    f"{_where(response)} sent over the {MAX_RESPONSE_SIZE} byte limit",
                )
            body += chunk
        return bytes(body)

    def _parse_response(self, text: str) -> tuple[int, str, str]:
        """Parse RT response into status code, message, and body."""
        lines = text.strip().split("\n")
        if not lines:
            return 500, "Empty response", ""

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
        fields: dict[str, Any] = {}
        current_key: str | None = None
        current_value: list[str] = []

        for line in text.split("\n"):
            if not line.strip():
                continue

            field_match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(.*)$", line)
            match field_match:
                case None if current_key and line.startswith(" "):
                    current_value.append(line.strip())
                case None:
                    pass
                case _:
                    if current_key:
                        fields[current_key] = "\n".join(current_value).strip()
                    current_key = field_match.group(1)
                    current_value = [field_match.group(2).strip()]

        if current_key:
            fields[current_key] = "\n".join(current_value).strip()

        return fields

    def _parse_search_results(self, text: str) -> list[dict[str, str]]:
        """Parse search results into list of tickets."""
        results: list[dict[str, str]] = []
        for raw_line in text.split("\n"):
            stripped = raw_line.strip()
            if not stripped:
                continue
            match = re.match(r"^(\d+): (.+)$", stripped)
            if match:
                results.append(
                    {
                        "id": match.group(1),
                        "Subject": match.group(2),
                    }
                )
        return results

    async def search_tickets(self, query: str, order_by: str = "-Created") -> list[dict[str, str]]:
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
        response = await self._request(f"ticket/{ticket_id}/history", params={"format": "l"})
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
        content_lines = []
        for key, value in fields.items():
            content_lines.append(f"{key}: {value}")

        content = "\n".join(content_lines)

        response = await self._request(f"ticket/{ticket_id}/edit", data={"content": content})
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
        formatted_lines = [lines[0]] + [" " + line for line in lines[1:]]
        return "\n".join(formatted_lines)

    async def correspond(self, ticket_id: int | str, text: str) -> str:
        """Add correspondence (reply) to ticket."""
        formatted_text = self._format_multiline_text(text)
        content = f"id: {ticket_id}\nAction: correspond\nText: {formatted_text}"
        response = await self._request(f"ticket/{ticket_id}/comment", data={"content": content})
        status, message, body = self._parse_response(response)

        if status != 200:
            raise RTApiError(status, f"{message} - {body}")

        return body

    async def comment(self, ticket_id: int | str, text: str) -> str:
        """Add comment (private note) to ticket."""
        formatted_text = self._format_multiline_text(text)
        content = f"id: {ticket_id}\nAction: comment\nText: {formatted_text}"
        response = await self._request(f"ticket/{ticket_id}/comment", data={"content": content})
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

        match = re.search(r"Ticket (\d+) created", body)
        if match:
            return match.group(1)

        if "Could not create ticket" in body or "No permission" in body:
            raise RTApiError(403, body.strip())

        return body.strip()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
