"""MCP Server for Request Tracker.

This module provides a secure MCP server for interacting with Request Tracker.
All credentials are handled securely via SecretStr.
"""

import argparse
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from .tools import register_tools
from .tools.tickets import close_client

# Configure logging to stderr (required for MCP stdio transport)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_mcp: FastMCP) -> AsyncIterator[None]:
    """Lifecycle manager for the MCP server."""
    logger.info("Starting MCP Request Tracker server")
    yield
    # Cleanup
    await close_client()
    logger.info("MCP Request Tracker server stopped")


# Initialize FastMCP server
mcp = FastMCP("request-tracker", lifespan=lifespan)

# Register all tools
register_tools(mcp)


def main() -> None:
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="MCP server for Request Tracker")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to for HTTP transports (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to for HTTP transports (default: 8000)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
