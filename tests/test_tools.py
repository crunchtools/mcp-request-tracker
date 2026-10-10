"""Mocked tool tests for all 17 RT tools."""

import pytest

from mcp_request_tracker_crunchtools.server import mcp
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
    update_ticket,
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
    update_ticket,
]

EXPECTED_TOOL_COUNT = 17
EXPECTED_ALL_COUNT = 18  # 17 tools + close_client


def test_tool_count() -> None:
    """Verify expected number of exports in tools.__all__."""
    assert len(tools_all) == EXPECTED_ALL_COUNT


def test_imports() -> None:
    """Verify all tool functions are importable and callable."""
    assert len(TOOL_FUNCTIONS) == EXPECTED_TOOL_COUNT
    for func in TOOL_FUNCTIONS:
        assert callable(func)


READ_ONLY = frozenset(
    {
        "search_tickets_tool",
        "get_ticket_tool",
        "get_ticket_history_tool",
        "get_my_open_tickets_tool",
        "get_new_tickets_tool",
    }
)
WRITES = frozenset(
    {
        "set_ticket_owner_tool",
        "set_ticket_status_tool",
        "update_ticket_tool",
        "resolve_ticket_tool",
        "open_ticket_tool",
        "take_ticket_tool",
        "set_time_worked_tool",
        "add_time_worked_tool",
        "add_ticket_comment_tool",
        "reply_to_ticket_tool",
        "create_ticket_tool",
        "complete_weekly_checklist_tool",
    }
)

# Arguments that satisfy each read-only tool's required parameters.
READ_ONLY_CALLS = {
    "search_tickets_tool": {"query": "Status = 'new'"},
    "get_ticket_tool": {"ticket_id": 123},
    "get_ticket_history_tool": {"ticket_id": 123},
    "get_my_open_tickets_tool": {"owner": "scott"},
    "get_new_tickets_tool": {"queue": "General"},
}


class TestReadOnlyAnnotation:
    """Every registered tool is classified, and the reads really only read."""

    @pytest.mark.asyncio
    async def test_every_tool_is_classified(self) -> None:
        tools = await mcp.list_tools()
        assert READ_ONLY.isdisjoint(WRITES)
        assert {tool.name for tool in tools} == READ_ONLY | WRITES
        annotated = {
            tool.name
            for tool in tools
            if tool.annotations is not None
            and tool.annotations.model_dump(by_alias=True).get("readOnlyHint") is True
        }
        assert annotated == READ_ONLY

    @pytest.mark.asyncio
    @pytest.mark.parametrize("name", sorted(READ_ONLY))
    async def test_read_only_tool_sends_no_content(self, name: str) -> None:
        """RT REST 1.0 is POST-only; a write is a POST carrying a `content` form."""
        async with _patch_rt_client(response=_mock_rt_response(body="123: Ticket")) as post:
            await mcp.call_tool(name, READ_ONLY_CALLS[name])
        assert post.await_count >= 1
        for call in post.await_args_list:
            assert "content" not in call.kwargs["data"]
            assert "/edit" not in call.args[0]
            assert "/comment" not in call.args[0]
            assert "/new" not in call.args[0]


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

    @pytest.mark.asyncio
    async def test_update_ticket_subject(self) -> None:
        resp = _mock_rt_response(body="Ticket 123 updated.")
        async with _patch_rt_client(response=resp):
            result = await update_ticket(123, subject="New Subject")
            assert "Ticket #123 updated" in result
            assert "Subject=New Subject" in result

    @pytest.mark.asyncio
    async def test_update_ticket_multiple_fields(self) -> None:
        resp = _mock_rt_response(body="Ticket 123 updated.")
        async with _patch_rt_client(response=resp):
            result = await update_ticket(123, subject="Title", priority=50, queue="Professional")
            assert "Ticket #123 updated" in result
            assert "Subject=Title" in result
            assert "Priority=50" in result
            assert "Queue=Professional" in result

    @pytest.mark.asyncio
    async def test_update_ticket_no_fields(self) -> None:
        async with _patch_rt_client():
            result = await update_ticket(123)
            assert "No fields provided" in result


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
