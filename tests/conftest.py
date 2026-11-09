"""Shared test fixtures for mcp-request-tracker tests."""

import os
from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import httpx
import pytest


@pytest.fixture(autouse=True)
def _reset_client_singleton() -> Generator[None, None, None]:
    """Reset the RT client and config singletons between tests."""
    import mcp_request_tracker_crunchtools.config as config_mod
    import mcp_request_tracker_crunchtools.tools.tickets as tickets_mod

    tickets_mod._rt_client = None
    config_mod._config = None
    yield
    tickets_mod._rt_client = None
    config_mod._config = None


def _mock_rt_response(status: int = 200, message: str = "Ok", body: str = "") -> httpx.Response:
    """Build a mock RT REST 1.0 response."""
    text = f"RT/4.4.4 {status} {message}\n\n{body}"
    return httpx.Response(
        200,
        text=text,
        request=httpx.Request("POST", "https://rt.example.com"),
    )


@asynccontextmanager
async def _patch_rt_client(
    response: httpx.Response | None = None,
    side_effect: list[httpx.Response] | None = None,
) -> AsyncIterator[AsyncMock]:
    """Patch the client to answer with mock RT responses.

    The client streams now: `build_request` then `send(..., stream=True)`. Only
    `send` is scripted; `build_request` is wrapped so it still builds a real
    request and records what the caller asked for, which is what the url and
    form assertions here are about.

    What a patch at this level cannot see is the client's own behaviour -- the
    User-Agent it adds and the bounded read it performs. Those are tested in
    `test_http_contract.py` over a `MockTransport` (constitution v1.36.0,
    Layer 3).
    """
    env = {
        "RT_URL": "https://rt.example.com",
        "RT_USER": "test_user",
        "RT_PASS": "test_pass",  # gatehouse: allow-secret
    }
    mock_send = AsyncMock()
    if side_effect is not None:
        mock_send.side_effect = side_effect
    elif response is not None:
        mock_send.return_value = response
    else:
        mock_send.return_value = _mock_rt_response()

    real_build = httpx.AsyncClient.build_request

    with (
        patch.dict(os.environ, env, clear=True),
        patch("httpx.AsyncClient.send", mock_send),
        patch.object(
            httpx.AsyncClient, "build_request", autospec=True, side_effect=real_build
        ) as mock_build,
    ):
        yield mock_build
