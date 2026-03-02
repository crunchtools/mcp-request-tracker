"""Mocked tool tests for all 16 RT tools."""

import pytest

from mcp_request_tracker_crunchtools.tools import __all__ as tools_all
from mcp_request_tracker_crunchtools.tools import (
    add_ticket_comment,
    add_time_worked,
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
)
from tests.conftest import _mock_rt_response, _patch_rt_client

TOOL_FUNCTIONS = [
    search_tickets,
    get_ticket,
    get_ticket_history,
    get_my_open_tickets,
    get_new_tickets,
    set_ticket_owner,
    set_ticket_status,
    resolve_ticket,
    open_ticket,
    take_ticket,
    set_time_worked,
    add_time_worked,
    add_ticket_comment,
    reply_to_ticket,
    create_ticket,
    complete_weekly_checklist,
]

EXPECTED_TOOL_COUNT = 16
EXPECTED_ALL_COUNT = 17  # 16 tools + close_client


def test_tool_count() -> None:
    """Verify expected number of exports in tools.__all__."""
    assert len(tools_all) == EXPECTED_ALL_COUNT


def test_imports() -> None:
    """Verify all tool functions are importable and callable."""
    assert len(TOOL_FUNCTIONS) == EXPECTED_TOOL_COUNT
    for func in TOOL_FUNCTIONS:
        assert callable(func)


class TestSearchTools:
    """Tests for search and view tools."""

    @pytest.mark.asyncio
    async def test_search_tickets(self) -> None:
        resp = _mock_rt_response(body="123: Test Ticket\n456: Another Ticket")
        async with _patch_rt_client(response=resp):
            result = await search_tickets("Status = 'new'")
            assert "Found 2 ticket(s)" in result
            assert "#123" in result
            assert "#456" in result

    @pytest.mark.asyncio
    async def test_search_tickets_no_results(self) -> None:
        resp = _mock_rt_response(body="")
        async with _patch_rt_client(response=resp):
            result = await search_tickets("Status = 'nonexistent'")
            assert "No tickets found" in result

    @pytest.mark.asyncio
    async def test_get_ticket(self) -> None:
        body = "id: 123\nSubject: Test Ticket\nStatus: open\nOwner: admin"
        resp = _mock_rt_response(body=body)
        async with _patch_rt_client(response=resp):
            result = await get_ticket(123)
            assert "Ticket #123 Details" in result
            assert "Subject: Test Ticket" in result
            assert "Status: open" in result

    @pytest.mark.asyncio
    async def test_get_ticket_history(self) -> None:
        body = "# 1/1 (id/1/total)\n\nType: Create\nCreator: admin"
        resp = _mock_rt_response(body=body)
        async with _patch_rt_client(response=resp):
            result = await get_ticket_history(123)
            assert "History for Ticket #123" in result
            assert "Create" in result

    @pytest.mark.asyncio
    async def test_get_my_open_tickets(self) -> None:
        resp = _mock_rt_response(body="100: My Ticket\n200: Another")
        async with _patch_rt_client(response=resp):
            result = await get_my_open_tickets("scott")
            assert "Open tickets for 'scott'" in result
            assert "#100" in result

    @pytest.mark.asyncio
    async def test_get_my_open_tickets_none(self) -> None:
        resp = _mock_rt_response(body="")
        async with _patch_rt_client(response=resp):
            result = await get_my_open_tickets("nobody")
            assert "No open tickets found" in result

    @pytest.mark.asyncio
    async def test_get_new_tickets(self) -> None:
        resp = _mock_rt_response(body="300: New Ticket")
        async with _patch_rt_client(response=resp):
            result = await get_new_tickets()
            assert "New tickets" in result
            assert "#300" in result

    @pytest.mark.asyncio
    async def test_get_new_tickets_with_queue(self) -> None:
        resp = _mock_rt_response(body="400: Queue Ticket")
        async with _patch_rt_client(response=resp):
            result = await get_new_tickets(queue="Professional")
            assert "#400" in result


class TestUpdateTools:
    """Tests for ticket update tools."""

    @pytest.mark.asyncio
    async def test_set_ticket_owner(self) -> None:
        resp = _mock_rt_response(body="Ticket 123 updated.")
        async with _patch_rt_client(response=resp):
            result = await set_ticket_owner(123, "scott")
            assert "owner set to 'scott'" in result

    @pytest.mark.asyncio
    async def test_set_ticket_status(self) -> None:
        resp = _mock_rt_response(body="Ticket 123 updated.")
        async with _patch_rt_client(response=resp):
            result = await set_ticket_status(123, "open")
            assert "status set to 'open'" in result

    @pytest.mark.asyncio
    async def test_resolve_ticket(self) -> None:
        resp = _mock_rt_response(body="Ticket 123 updated.")
        async with _patch_rt_client(response=resp):
            result = await resolve_ticket(123)
            assert "resolved" in result

    @pytest.mark.asyncio
    async def test_resolve_ticket_with_comment(self) -> None:
        resp = _mock_rt_response(body="Ticket 123 updated.")
        async with _patch_rt_client(response=resp):
            result = await resolve_ticket(123, comment="Done")
            assert "resolved" in result

    @pytest.mark.asyncio
    async def test_open_ticket(self) -> None:
        resp = _mock_rt_response(body="Ticket 123 updated.")
        async with _patch_rt_client(response=resp):
            result = await open_ticket(123)
            assert "opened" in result

    @pytest.mark.asyncio
    async def test_open_ticket_with_owner(self) -> None:
        resp = _mock_rt_response(body="Ticket 123 updated.")
        async with _patch_rt_client(response=resp):
            result = await open_ticket(123, owner="scott")
            assert "opened" in result

    @pytest.mark.asyncio
    async def test_take_ticket(self) -> None:
        resp = _mock_rt_response(body="Ticket 123 updated.")
        async with _patch_rt_client(response=resp):
            result = await take_ticket(123, "scott")
            assert "taken by 'scott'" in result


class TestTimeTools:
    """Tests for time tracking tools."""

    @pytest.mark.asyncio
    async def test_set_time_worked(self) -> None:
        resp = _mock_rt_response(body="Ticket 123 updated.")
        async with _patch_rt_client(response=resp):
            result = await set_time_worked(123, 30)
            assert "30 minutes" in result

    @pytest.mark.asyncio
    async def test_add_time_worked(self) -> None:
        update_resp = _mock_rt_response(body="Ticket 123 updated.")
        ticket_resp = _mock_rt_response(body="id: 123\nTimeWorked: 60")
        async with _patch_rt_client(side_effect=[update_resp, ticket_resp, ticket_resp]):
            result = await add_time_worked(123, 15)
            assert "Added 15 minutes" in result


class TestCommunicationTools:
    """Tests for communication tools."""

    @pytest.mark.asyncio
    async def test_add_ticket_comment(self) -> None:
        resp = _mock_rt_response(body="Message recorded.")
        async with _patch_rt_client(response=resp):
            result = await add_ticket_comment(123, "Internal note")
            assert "Comment added" in result

    @pytest.mark.asyncio
    async def test_reply_to_ticket(self) -> None:
        resp = _mock_rt_response(body="Message recorded.")
        async with _patch_rt_client(response=resp):
            result = await reply_to_ticket(123, "Hello requestor")
            assert "Reply added" in result


class TestCreationTools:
    """Tests for ticket creation tools."""

    @pytest.mark.asyncio
    async def test_create_ticket(self) -> None:
        resp = _mock_rt_response(body="# Ticket 999 created.")
        async with _patch_rt_client(response=resp):
            result = await create_ticket("General", "New ticket")
            assert "Ticket #999 created" in result

    @pytest.mark.asyncio
    async def test_create_ticket_with_options(self) -> None:
        resp = _mock_rt_response(body="# Ticket 1000 created.")
        async with _patch_rt_client(response=resp):
            result = await create_ticket(
                "Professional",
                "Full ticket",
                text="Description here",
                requestor="user@example.com",
                owner="scott",
                priority=50,
            )
            assert "Ticket #1000 created" in result


class TestWorkflowTools:
    """Tests for workflow tools."""

    @pytest.mark.asyncio
    async def test_complete_weekly_checklist(self) -> None:
        resp = _mock_rt_response(body="Ticket 500 updated.")
        async with _patch_rt_client(response=resp):
            result = await complete_weekly_checklist(
                ticket_id=500,
                owner="scott",
                checklist_results="All items checked",
                time_minutes=15,
            )
            assert "weekly checklist completed" in result
            assert "Owner set to 'scott'" in result
            assert "Ticket resolved" in result

    @pytest.mark.asyncio
    async def test_complete_weekly_checklist_no_time(self) -> None:
        resp = _mock_rt_response(body="Ticket 501 updated.")
        async with _patch_rt_client(response=resp):
            result = await complete_weekly_checklist(
                ticket_id=501,
                owner="scott",
                checklist_results="Done",
            )
            assert "weekly checklist completed" in result
            assert "minutes" not in result


class TestErrorHandling:
    """Tests for error handling in tools."""

    @pytest.mark.asyncio
    async def test_search_tickets_api_error(self) -> None:
        resp = _mock_rt_response(status=401, message="Credentials required")
        async with _patch_rt_client(response=resp):
            result = await search_tickets("Status = 'new'")
            assert "Error" in result

    @pytest.mark.asyncio
    async def test_get_ticket_api_error(self) -> None:
        resp = _mock_rt_response(status=404, message="Ticket not found")
        async with _patch_rt_client(response=resp):
            result = await get_ticket(99999)
            assert "Error" in result
