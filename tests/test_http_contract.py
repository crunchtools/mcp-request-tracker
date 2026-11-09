"""The outbound HTTP contract (constitution v1.36.0, MCP Server profile Layer 3).

A real `httpx.AsyncClient` over a `MockTransport`: the agent string is a header
the client adds and the ceiling is enforced while the client reads, so the
`_patch_rt_client` helper -- which replaces `send` -- cannot see either.
"""

import os
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import contextmanager
from importlib.metadata import version
from typing import Any
from unittest.mock import patch

import httpx
import pytest

from mcp_request_tracker_crunchtools import client as client_mod
from mcp_request_tracker_crunchtools.config import Config
from mcp_request_tracker_crunchtools.errors import RTApiError

Handler = Callable[[httpx.Request], httpx.Response]
RT_PASS = "s3cret-rt-password"  # gatehouse: allow-secret


async def _chunks(chunk: bytes, times: int) -> AsyncIterator[bytes]:
    """A chunked body, which carries no content-length -- what a header check misses."""
    for _ in range(times):
        yield chunk


@contextmanager
def _serving(handler: Handler) -> Iterator[client_mod.RTClient]:
    """Hand back a client whose own `_get_client` rides a mock transport."""
    env = {"RT_URL": "https://rt.example.com", "RT_USER": "test_user", "RT_PASS": RT_PASS}
    real = httpx.AsyncClient

    def factory(**kwargs: Any) -> httpx.AsyncClient:
        kwargs.pop("transport", None)
        return real(transport=httpx.MockTransport(handler), **kwargs)

    with (
        patch.dict(os.environ, env, clear=True),
        patch.object(httpx, "AsyncClient", factory),
    ):
        yield client_mod.RTClient(Config())


class TestUserAgent:
    """A request says what it is, and the version cannot drift from the release."""

    @pytest.mark.asyncio
    async def test_outgoing_request_names_the_product_and_version(self) -> None:
        seen: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.headers["User-Agent"])
            return httpx.Response(200, text="RT/5.0.0 200 Ok\n\n")

        with _serving(handler) as rt:
            await rt._request("ticket/1/show")

        expected = (
            f"mcp-request-tracker-crunchtools/{version('mcp-request-tracker-crunchtools')} "
            "(+https://github.com/crunchtools/mcp-request-tracker)"
        )
        assert seen == [expected]
        assert "python-httpx" not in seen[0]


class TestResponseCeiling:
    """There was no limit here at all before this."""

    @pytest.mark.asyncio
    async def test_chunked_body_over_the_cap_is_refused(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(client_mod, "MAX_RESPONSE_SIZE", 4096)

        def handler(_request: httpx.Request) -> httpx.Response:
            response = httpx.Response(
                200, headers={"content-type": "text/plain"}, content=_chunks(b"x" * 1024, 16)
            )
            assert "content-length" not in response.headers
            return response

        with _serving(handler) as rt, pytest.raises(RTApiError) as caught:
            await rt._request("ticket/1/history")

        message = str(caught.value)
        assert "over the 4096 byte limit" in message
        assert "ticket/1/history" in message

    @pytest.mark.asyncio
    async def test_a_single_oversized_chunk_is_refused_before_it_is_copied(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(client_mod, "MAX_RESPONSE_SIZE", 1024)

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, headers={"content-type": "text/plain"}, content=_chunks(b"x" * 8192, 1)
            )

        with _serving(handler) as rt, pytest.raises(RTApiError) as caught:
            await rt._request("ticket/1/show")

        assert "over the 1024 byte limit" in str(caught.value)


class TestErrorNamesTheSite:
    """`raise_for_status()` could not say which URL answered."""

    @pytest.mark.asyncio
    async def test_an_access_page_is_quoted_with_the_request(self) -> None:
        """This client follows redirects, so the body can come from elsewhere."""

        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                403,
                headers={"content-type": "text/html"},
                text="<title>Cloudflare Access</title>",
            )

        with _serving(handler) as rt, pytest.raises(RTApiError) as caught:
            await rt._request("ticket/1/show")

        message = str(caught.value)
        assert "Cloudflare Access" in message
        assert "text/html" in message
        assert "HTTP 403" in message


class TestSnippetCarriesNoCredential:
    """RT REST 1.0 takes the password in the POST body, so a reflection leaks it."""

    @pytest.mark.asyncio
    async def test_a_body_reflecting_the_password_is_scrubbed(self) -> None:
        """A proxy debug page echoing the form back is the case this covers.

        `RTApiError` does not scrub, unlike some of the fleet's error types, so
        the redaction happens where the body becomes a message.
        """

        def handler(request: httpx.Request) -> httpx.Response:
            echoed = request.content.decode()
            return httpx.Response(
                400, headers={"content-type": "text/html"}, text=f"<pre>{echoed}</pre>"
            )

        with _serving(handler) as rt, pytest.raises(RTApiError) as caught:
            await rt._request("ticket/1/show")

        message = str(caught.value)
        assert RT_PASS not in message
        assert "***" in message
