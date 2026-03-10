"""Pure async functions for Request Tracker ticket operations.

These functions handle RT API interactions and are called by the
@mcp.tool() wrappers in server.py.
"""

from mcp_request_tracker_crunchtools.client import RTClient
from mcp_request_tracker_crunchtools.config import get_config
from mcp_request_tracker_crunchtools.errors import RTApiError

_rt_client: RTClient | None = None


def get_rt_client() -> RTClient:
    """Get the RT client instance."""
    global _rt_client
    if _rt_client is None:
        config = get_config()
        _rt_client = RTClient(config)
    return _rt_client


async def close_client() -> None:
    """Close the RT client."""
    global _rt_client
    if _rt_client:
        await _rt_client.close()
        _rt_client = None


async def search_tickets(query: str, order_by: str = "-Created") -> str:
    """Search for tickets using RT query syntax."""
    client = get_rt_client()
    try:
        results = await client.search_tickets(query, order_by)
        if not results:
            return "No tickets found matching the query."

        lines = [f"Found {len(results)} ticket(s):\n"]
        for ticket in results:
            lines.append(f"  #{ticket['id']}: {ticket['Subject']}")

        return "\n".join(lines)
    except RTApiError as e:
        return f"Error searching tickets: {e}"


async def get_ticket(ticket_id: int) -> str:
    """Get details of a specific ticket."""
    client = get_rt_client()
    try:
        ticket = await client.get_ticket(ticket_id)
        if not ticket:
            return f"Ticket #{ticket_id} not found."

        lines = [f"Ticket #{ticket_id} Details:\n"]
        for key, value in ticket.items():
            if value and value != "Not set":
                lines.append(f"  {key}: {value}")

        return "\n".join(lines)
    except RTApiError as e:
        return f"Error getting ticket: {e}"


async def get_ticket_history(ticket_id: int) -> str:
    """Get the history/changelog of a ticket."""
    client = get_rt_client()
    try:
        history = await client.get_ticket_history(ticket_id)
        return f"History for Ticket #{ticket_id}:\n\n{history}"
    except RTApiError as e:
        return f"Error getting ticket history: {e}"


async def set_ticket_owner(ticket_id: int, owner: str) -> str:
    """Set the owner of a ticket."""
    client = get_rt_client()
    try:
        result = await client.set_owner(ticket_id, owner)
        return f"Ticket #{ticket_id} owner set to '{owner}'.\n{result}"
    except RTApiError as e:
        return f"Error setting owner: {e}"


async def set_ticket_status(ticket_id: int, status: str) -> str:
    """Set the status of a ticket."""
    client = get_rt_client()
    try:
        result = await client.set_status(ticket_id, status)
        return f"Ticket #{ticket_id} status set to '{status}'.\n{result}"
    except RTApiError as e:
        return f"Error setting status: {e}"


async def resolve_ticket(ticket_id: int, comment: str = "") -> str:
    """Resolve/close a ticket, optionally adding a comment."""
    client = get_rt_client()
    try:
        if comment:
            await client.comment(ticket_id, comment)

        result = await client.set_status(ticket_id, "resolved")
        return f"Ticket #{ticket_id} resolved.\n{result}"
    except RTApiError as e:
        return f"Error resolving ticket: {e}"


async def open_ticket(ticket_id: int, owner: str = "") -> str:
    """Open a ticket, optionally taking ownership."""
    client = get_rt_client()
    try:
        if owner:
            await client.set_owner(ticket_id, owner)

        result = await client.set_status(ticket_id, "open")
        return f"Ticket #{ticket_id} opened.\n{result}"
    except RTApiError as e:
        return f"Error opening ticket: {e}"


async def take_ticket(ticket_id: int, username: str) -> str:
    """Take ownership of a ticket and open it."""
    client = get_rt_client()
    try:
        await client.set_owner(ticket_id, username)
        result = await client.set_status(ticket_id, "open")
        return f"Ticket #{ticket_id} taken by '{username}' and opened.\n{result}"
    except RTApiError as e:
        return f"Error taking ticket: {e}"


async def set_time_worked(ticket_id: int, minutes: int) -> str:
    """Set the total time worked on a ticket."""
    client = get_rt_client()
    try:
        result = await client.set_time_worked(ticket_id, minutes)
        return f"Ticket #{ticket_id} time worked set to {minutes} minutes.\n{result}"
    except RTApiError as e:
        return f"Error setting time worked: {e}"


async def add_time_worked(ticket_id: int, minutes: int) -> str:
    """Add time to the time worked on a ticket."""
    client = get_rt_client()
    try:
        result = await client.add_time_worked(ticket_id, minutes)
        ticket = await client.get_ticket(ticket_id)
        total = ticket.get("TimeWorked", "0")
        msg = f"Added {minutes} minutes to ticket #{ticket_id}. New total: {total} minutes."
        return f"{msg}\n{result}"
    except RTApiError as e:
        return f"Error adding time worked: {e}"


async def add_ticket_comment(ticket_id: int, comment: str) -> str:
    """Add a private comment/note to a ticket (not visible to requestor)."""
    client = get_rt_client()
    try:
        result = await client.comment(ticket_id, comment)
        return f"Comment added to ticket #{ticket_id}.\n{result}"
    except RTApiError as e:
        return f"Error adding comment: {e}"


async def reply_to_ticket(ticket_id: int, message: str) -> str:
    """Reply to a ticket (correspondence visible to requestor)."""
    client = get_rt_client()
    try:
        result = await client.correspond(ticket_id, message)
        return f"Reply added to ticket #{ticket_id}.\n{result}"
    except RTApiError as e:
        return f"Error replying to ticket: {e}"


async def create_ticket(
    queue: str,
    subject: str,
    text: str = "",
    requestor: str = "",
    owner: str = "",
    priority: int = 0,
) -> str:
    """Create a new ticket."""
    client = get_rt_client()
    try:
        extra: dict[str, str] = {}
        if owner:
            extra["Owner"] = owner
        if priority:
            extra["Priority"] = str(priority)

        created_id = await client.create_ticket(queue, subject, text, requestor, **extra)
        return f"Ticket #{created_id} created in queue '{queue}'."
    except RTApiError as e:
        return f"Error creating ticket: {e}"


async def complete_weekly_checklist(
    ticket_id: int,
    owner: str,
    checklist_results: str,
    time_minutes: int = 0,
) -> str:
    """Complete a weekly checklist ticket with results.

    Workflow: take ownership, open, add results, add time, comment, resolve.
    """
    client = get_rt_client()
    try:
        results = []

        await client.set_owner(ticket_id, owner)
        results.append(f"Owner set to '{owner}'")

        await client.set_status(ticket_id, "open")
        results.append("Status set to 'open'")

        await client.correspond(ticket_id, checklist_results)
        results.append("Checklist results added")

        if time_minutes > 0:
            await client.add_time_worked(ticket_id, time_minutes)
            results.append(f"Added {time_minutes} minutes")

        await client.comment(ticket_id, "Completed")
        results.append("Completion comment added")

        await client.set_status(ticket_id, "resolved")
        results.append("Ticket resolved")

        return f"Ticket #{ticket_id} weekly checklist completed:\n" + "\n".join(
            f"  - {r}" for r in results
        )
    except RTApiError as e:
        return f"Error completing checklist: {e}"


async def update_ticket(
    ticket_id: int,
    subject: str = "",
    priority: int | None = None,
    queue: str = "",
) -> str:
    """Update ticket fields (subject, priority, queue)."""
    client = get_rt_client()
    try:
        fields: dict[str, str] = {}
        if subject:
            fields["Subject"] = subject
        if priority is not None:
            fields["Priority"] = str(priority)
        if queue:
            fields["Queue"] = queue

        if not fields:
            return "No fields provided to update."

        result = await client.update_ticket(ticket_id, **fields)
        updated = ", ".join(f"{k}={v}" for k, v in fields.items())
        return f"Ticket #{ticket_id} updated ({updated}).\n{result}"
    except RTApiError as e:
        return f"Error updating ticket: {e}"


async def get_my_open_tickets(owner: str) -> str:
    """Get all open tickets assigned to a user."""
    client = get_rt_client()
    try:
        query = f"Owner = '{owner}' AND (Status = 'new' OR Status = 'open')"
        results = await client.search_tickets(query, "-Created")

        if not results:
            return f"No open tickets found for '{owner}'."

        lines = [f"Open tickets for '{owner}' ({len(results)} total):\n"]
        for ticket in results:
            lines.append(f"  #{ticket['id']}: {ticket['Subject']}")

        return "\n".join(lines)
    except RTApiError as e:
        return f"Error searching tickets: {e}"


async def get_new_tickets(queue: str = "") -> str:
    """Get all new (unassigned) tickets, optionally filtered by queue."""
    client = get_rt_client()
    try:
        query = f"Status = 'new' AND Queue = '{queue}'" if queue else "Status = 'new'"
        results = await client.search_tickets(query, "-Created")

        if not results:
            return "No new tickets found."

        lines = [f"New tickets ({len(results)} total):\n"]
        for ticket in results:
            lines.append(f"  #{ticket['id']}: {ticket['Subject']}")

        return "\n".join(lines)
    except RTApiError as e:
        return f"Error searching tickets: {e}"


__all__ = [
    "add_ticket_comment",
    "add_time_worked",
    "close_client",
    "complete_weekly_checklist",
    "create_ticket",
    "get_my_open_tickets",
    "get_new_tickets",
    "get_rt_client",
    "get_ticket",
    "get_ticket_history",
    "open_ticket",
    "reply_to_ticket",
    "resolve_ticket",
    "search_tickets",
    "set_ticket_owner",
    "set_ticket_status",
    "set_time_worked",
    "take_ticket",
    "update_ticket",
]
