"""MCP tools for Request Tracker ticket operations."""

from fastmcp import FastMCP

from mcp_request_tracker_crunchtools.client import RTClient
from mcp_request_tracker_crunchtools.config import get_config
from mcp_request_tracker_crunchtools.errors import RTApiError

# Global RT client instance
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


def register_tools(mcp: FastMCP) -> None:
    """Register all ticket tools with the MCP server."""

    # ==========================================================================
    # Ticket Search and View Tools
    # ==========================================================================

    @mcp.tool()
    async def search_tickets(query: str, order_by: str = "-Created") -> str:
        """Search for tickets using RT query syntax.

        Args:
            query: RT query string (e.g., "Status = 'new'", "Subject LIKE 'checklist'",
                   "Owner = 'scott'", "Queue = 'Professional'")
            order_by: Field to order by, prefix with - for descending (default: -Created)

        Returns:
            List of matching tickets with ID and Subject
        """
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

    @mcp.tool()
    async def get_ticket(ticket_id: int) -> str:
        """Get details of a specific ticket.

        Args:
            ticket_id: The ticket ID number

        Returns:
            Ticket details including status, owner, subject, times, etc.
        """
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

    @mcp.tool()
    async def get_ticket_history(ticket_id: int) -> str:
        """Get the history/changelog of a ticket.

        Args:
            ticket_id: The ticket ID number

        Returns:
            Transaction history showing all changes made to the ticket
        """
        client = get_rt_client()
        try:
            history = await client.get_ticket_history(ticket_id)
            return f"History for Ticket #{ticket_id}:\n\n{history}"
        except RTApiError as e:
            return f"Error getting ticket history: {e}"

    # ==========================================================================
    # Ticket Update Tools
    # ==========================================================================

    @mcp.tool()
    async def set_ticket_owner(ticket_id: int, owner: str) -> str:
        """Set the owner of a ticket (take/assign ticket).

        Args:
            ticket_id: The ticket ID number
            owner: Username of the new owner

        Returns:
            Confirmation message
        """
        client = get_rt_client()
        try:
            result = await client.set_owner(ticket_id, owner)
            return f"Ticket #{ticket_id} owner set to '{owner}'.\n{result}"
        except RTApiError as e:
            return f"Error setting owner: {e}"

    @mcp.tool()
    async def set_ticket_status(ticket_id: int, status: str) -> str:
        """Set the status of a ticket.

        Args:
            ticket_id: The ticket ID number
            status: New status (e.g., 'new', 'open', 'stalled', 'resolved', 'rejected', 'deleted')

        Returns:
            Confirmation message
        """
        client = get_rt_client()
        try:
            result = await client.set_status(ticket_id, status)
            return f"Ticket #{ticket_id} status set to '{status}'.\n{result}"
        except RTApiError as e:
            return f"Error setting status: {e}"

    @mcp.tool()
    async def resolve_ticket(ticket_id: int, comment: str = "") -> str:
        """Resolve/close a ticket, optionally adding a comment.

        Args:
            ticket_id: The ticket ID number
            comment: Optional comment to add before resolving

        Returns:
            Confirmation message
        """
        client = get_rt_client()
        try:
            if comment:
                await client.comment(ticket_id, comment)

            result = await client.set_status(ticket_id, "resolved")
            return f"Ticket #{ticket_id} resolved.\n{result}"
        except RTApiError as e:
            return f"Error resolving ticket: {e}"

    @mcp.tool()
    async def open_ticket(ticket_id: int, owner: str = "") -> str:
        """Open a ticket (change status from new to open), optionally taking ownership.

        Args:
            ticket_id: The ticket ID number
            owner: Optional username to assign as owner

        Returns:
            Confirmation message
        """
        client = get_rt_client()
        try:
            if owner:
                await client.set_owner(ticket_id, owner)

            result = await client.set_status(ticket_id, "open")
            return f"Ticket #{ticket_id} opened.\n{result}"
        except RTApiError as e:
            return f"Error opening ticket: {e}"

    @mcp.tool()
    async def take_ticket(ticket_id: int, username: str) -> str:
        """Take ownership of a ticket and open it.

        Args:
            ticket_id: The ticket ID number
            username: Your username

        Returns:
            Confirmation message
        """
        client = get_rt_client()
        try:
            await client.set_owner(ticket_id, username)
            result = await client.set_status(ticket_id, "open")
            return f"Ticket #{ticket_id} taken by '{username}' and opened.\n{result}"
        except RTApiError as e:
            return f"Error taking ticket: {e}"

    # ==========================================================================
    # Time Tracking Tools
    # ==========================================================================

    @mcp.tool()
    async def set_time_worked(ticket_id: int, minutes: int) -> str:
        """Set the total time worked on a ticket.

        Args:
            ticket_id: The ticket ID number
            minutes: Total time worked in minutes

        Returns:
            Confirmation message
        """
        client = get_rt_client()
        try:
            result = await client.set_time_worked(ticket_id, minutes)
            return f"Ticket #{ticket_id} time worked set to {minutes} minutes.\n{result}"
        except RTApiError as e:
            return f"Error setting time worked: {e}"

    @mcp.tool()
    async def add_time_worked(ticket_id: int, minutes: int) -> str:
        """Add time to the time worked on a ticket.

        Args:
            ticket_id: The ticket ID number
            minutes: Additional time to add in minutes

        Returns:
            Confirmation message with new total
        """
        client = get_rt_client()
        try:
            result = await client.add_time_worked(ticket_id, minutes)
            ticket = await client.get_ticket(ticket_id)
            total = ticket.get("TimeWorked", "0")
            msg = f"Added {minutes} minutes to ticket #{ticket_id}. New total: {total} minutes."
            return f"{msg}\n{result}"
        except RTApiError as e:
            return f"Error adding time worked: {e}"

    # ==========================================================================
    # Communication Tools
    # ==========================================================================

    @mcp.tool()
    async def add_ticket_comment(ticket_id: int, comment: str) -> str:
        """Add a private comment/note to a ticket (not visible to requestor).

        Args:
            ticket_id: The ticket ID number
            comment: The comment text

        Returns:
            Confirmation message
        """
        client = get_rt_client()
        try:
            result = await client.comment(ticket_id, comment)
            return f"Comment added to ticket #{ticket_id}.\n{result}"
        except RTApiError as e:
            return f"Error adding comment: {e}"

    @mcp.tool()
    async def reply_to_ticket(ticket_id: int, message: str) -> str:
        """Reply to a ticket (correspondence visible to requestor).

        Args:
            ticket_id: The ticket ID number
            message: The reply message

        Returns:
            Confirmation message
        """
        client = get_rt_client()
        try:
            result = await client.correspond(ticket_id, message)
            return f"Reply added to ticket #{ticket_id}.\n{result}"
        except RTApiError as e:
            return f"Error replying to ticket: {e}"

    # ==========================================================================
    # Ticket Creation Tools
    # ==========================================================================

    @mcp.tool()
    async def create_ticket(
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
        client = get_rt_client()
        try:
            extra = {}
            if owner:
                extra["Owner"] = owner
            if priority:
                extra["Priority"] = str(priority)

            ticket_id = await client.create_ticket(queue, subject, text, requestor, **extra)
            return f"Ticket #{ticket_id} created in queue '{queue}'."
        except RTApiError as e:
            return f"Error creating ticket: {e}"

    # ==========================================================================
    # Bulk/Workflow Tools
    # ==========================================================================

    @mcp.tool()
    async def complete_weekly_checklist(
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
        client = get_rt_client()
        try:
            results = []

            # Take ownership and open
            await client.set_owner(ticket_id, owner)
            results.append(f"Owner set to '{owner}'")

            await client.set_status(ticket_id, "open")
            results.append("Status set to 'open'")

            # Add correspondence with results
            await client.correspond(ticket_id, checklist_results)
            results.append("Checklist results added")

            # Add time if specified
            if time_minutes > 0:
                await client.add_time_worked(ticket_id, time_minutes)
                results.append(f"Added {time_minutes} minutes")

            # Add completion comment and resolve
            await client.comment(ticket_id, "Completed")
            results.append("Completion comment added")

            await client.set_status(ticket_id, "resolved")
            results.append("Ticket resolved")

            return f"Ticket #{ticket_id} weekly checklist completed:\n" + "\n".join(
                f"  - {r}" for r in results
            )
        except RTApiError as e:
            return f"Error completing checklist: {e}"

    @mcp.tool()
    async def get_my_open_tickets(owner: str) -> str:
        """Get all open tickets assigned to a user.

        Args:
            owner: Username to search for

        Returns:
            List of open tickets owned by the user
        """
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

    @mcp.tool()
    async def get_new_tickets(queue: str = "") -> str:
        """Get all new (unassigned) tickets, optionally filtered by queue.

        Args:
            queue: Optional queue name to filter by

        Returns:
            List of new tickets
        """
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
