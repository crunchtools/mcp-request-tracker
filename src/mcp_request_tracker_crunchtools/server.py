"""MCP Server for Request Tracker.

This module provides a secure MCP server for interacting with Request Tracker.
All credentials are handled securely via SecretStr.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP

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
async def lifespan(mcp: FastMCP) -> AsyncIterator[None]:
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
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
