"""FastMCP server setup for Request Tracker MCP."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from .tools import (
    add_ticket_comment,
    add_time_worked,
    close_client,
    complete_weekly_checklist,
    create_ticket,
    get_my_open_tickets,
    get_new_tickets,
    get_ticket,
    get_ticket_history,
    open_ticket,
    reply_to_ticket,
    resolve_ticket,
    search_tickets,
    set_ticket_owner,
    set_ticket_status,
    set_time_worked,
    take_ticket,
    update_ticket,
)

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
    await close_client()
    logger.info("MCP Request Tracker server stopped")


mcp = FastMCP(
    name="mcp-request-tracker-crunchtools",
    version="0.4.0",
    lifespan=lifespan,
    instructions=(
        "Secure MCP server for Request Tracker (RT) ticket management. "
        "Provides search, view, update, time tracking, communication, creation, "
        "and workflow tools for RT tickets via the REST 1.0 API."
    ),
)


@mcp.tool()
async def search_tickets_tool(query: str, order_by: str = "-Created") -> str:
    """Search for tickets using RT query syntax.

    Args:
        query: RT query string (e.g., "Status = 'new'", "Subject LIKE 'checklist'",
               "Owner = 'scott'", "Queue = 'Professional'")
        order_by: Field to order by, prefix with - for descending (default: -Created)

    Returns:
        List of matching tickets with ID and Subject
    """
    return await search_tickets(query, order_by)


@mcp.tool()
async def get_ticket_tool(ticket_id: int) -> str:
    """Get details of a specific ticket.

    Args:
        ticket_id: The ticket ID number

    Returns:
        Ticket details including status, owner, subject, times, etc.
    """
    return await get_ticket(ticket_id)


@mcp.tool()
async def get_ticket_history_tool(ticket_id: int) -> str:
    """Get the history/changelog of a ticket.

    Args:
        ticket_id: The ticket ID number

    Returns:
        Transaction history showing all changes made to the ticket
    """
    return await get_ticket_history(ticket_id)


@mcp.tool()
async def get_my_open_tickets_tool(owner: str) -> str:
    """Get all open tickets assigned to a user.

    Args:
        owner: Username to search for

    Returns:
        List of open tickets owned by the user
    """
    return await get_my_open_tickets(owner)


@mcp.tool()
async def get_new_tickets_tool(queue: str = "") -> str:
    """Get all new (unassigned) tickets, optionally filtered by queue.

    Args:
        queue: Optional queue name to filter by

    Returns:
        List of new tickets
    """
    return await get_new_tickets(queue)


@mcp.tool()
async def set_ticket_owner_tool(ticket_id: int, owner: str) -> str:
    """Set the owner of a ticket (take/assign ticket).

    Args:
        ticket_id: The ticket ID number
        owner: Username of the new owner

    Returns:
        Confirmation message
    """
    return await set_ticket_owner(ticket_id, owner)


@mcp.tool()
async def set_ticket_status_tool(ticket_id: int, status: str) -> str:
    """Set the status of a ticket.

    Args:
        ticket_id: The ticket ID number
        status: New status (e.g., 'new', 'open', 'stalled', 'resolved', 'rejected', 'deleted')

    Returns:
        Confirmation message
    """
    return await set_ticket_status(ticket_id, status)


@mcp.tool()
async def update_ticket_tool(
    ticket_id: int,
    subject: str = "",
    priority: int | None = None,
    queue: str = "",
) -> str:
    """Update ticket fields (subject, priority, queue). All fields are optional.

    Args:
        ticket_id: The ticket ID number
        subject: New subject/title for the ticket
        priority: New priority (0-99)
        queue: New queue name (e.g., 'General', 'Professional')

    Returns:
        Confirmation of updated fields
    """
    return await update_ticket(ticket_id, subject, priority, queue)


@mcp.tool()
async def resolve_ticket_tool(ticket_id: int, comment: str = "") -> str:
    """Resolve/close a ticket, optionally adding a comment.

    Args:
        ticket_id: The ticket ID number
        comment: Optional comment to add before resolving

    Returns:
        Confirmation message
    """
    return await resolve_ticket(ticket_id, comment)


@mcp.tool()
async def open_ticket_tool(ticket_id: int, owner: str = "") -> str:
    """Open a ticket (change status from new to open), optionally taking ownership.

    Args:
        ticket_id: The ticket ID number
        owner: Optional username to assign as owner

    Returns:
        Confirmation message
    """
    return await open_ticket(ticket_id, owner)


@mcp.tool()
async def take_ticket_tool(ticket_id: int, username: str) -> str:
    """Take ownership of a ticket and open it.

    Args:
        ticket_id: The ticket ID number
        username: Your username

    Returns:
        Confirmation message
    """
    return await take_ticket(ticket_id, username)


@mcp.tool()
async def set_time_worked_tool(ticket_id: int, minutes: int) -> str:
    """Set the total time worked on a ticket.

    Args:
        ticket_id: The ticket ID number
        minutes: Total time worked in minutes

    Returns:
        Confirmation message
    """
    return await set_time_worked(ticket_id, minutes)


@mcp.tool()
async def add_time_worked_tool(ticket_id: int, minutes: int) -> str:
    """Add time to the time worked on a ticket.

    Args:
        ticket_id: The ticket ID number
        minutes: Additional time to add in minutes

    Returns:
        Confirmation message with new total
    """
    return await add_time_worked(ticket_id, minutes)


@mcp.tool()
async def add_ticket_comment_tool(ticket_id: int, comment: str) -> str:
    """Add a private comment/note to a ticket (not visible to requestor).

    Args:
        ticket_id: The ticket ID number
        comment: The comment text

    Returns:
        Confirmation message
    """
    return await add_ticket_comment(ticket_id, comment)


@mcp.tool()
async def reply_to_ticket_tool(ticket_id: int, message: str) -> str:
    """Reply to a ticket (correspondence visible to requestor).

    Args:
        ticket_id: The ticket ID number
        message: The reply message

    Returns:
        Confirmation message
    """
    return await reply_to_ticket(ticket_id, message)


@mcp.tool()
async def create_ticket_tool(
    queue: str,
    subject: str,
    text: str = "",
    requestor: str = "",
    owner: str = "",
    priority: int = 0,
) -> str:
    """Create a new ticket.

    Args:
        queue: Queue name (e.g., 'General', 'Professional')
        subject: Ticket subject/title
        text: Initial ticket content/description
        requestor: Email of the requestor
        owner: Username to assign as owner
        priority: Ticket priority (0-99)

    Returns:
        Created ticket ID and confirmation
    """
    return await create_ticket(queue, subject, text, requestor, owner, priority)


@mcp.tool()
async def complete_weekly_checklist_tool(
    ticket_id: int,
    owner: str,
    checklist_results: str,
    time_minutes: int = 0,
) -> str:
    """Complete a weekly checklist ticket with results.

    This is a workflow shortcut that:
    1. Takes ownership of the ticket
    2. Opens the ticket
    3. Adds correspondence with checklist results
    4. Adds time worked (if specified)
    5. Adds a "Completed" comment
    6. Resolves the ticket

    Args:
        ticket_id: The ticket ID number
        owner: Username taking the ticket
        checklist_results: The checklist completion results
        time_minutes: Time spent on checklist (optional)

    Returns:
        Confirmation of all actions taken
    """
    return await complete_weekly_checklist(ticket_id, owner, checklist_results, time_minutes)
