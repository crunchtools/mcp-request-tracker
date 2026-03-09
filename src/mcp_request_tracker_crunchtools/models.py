"""Pydantic input validation models for MCP Request Tracker.

These models validate tool inputs before they reach the API client,
enforcing field lengths, allowlists, and rejecting unexpected fields.
"""

from pydantic import BaseModel, ConfigDict, Field

# Field length and value constraints
MAX_SHORT_FIELD = 200  # Queue names, usernames, owner fields
MAX_SUBJECT = 500  # Ticket subject lines
MAX_TEXT = 50_000  # Large text fields (body, comments, checklists)
MAX_STATUS = 50  # Status field names
MAX_PRIORITY = 999  # RT priority range upper bound
MAX_MINUTES = 99_999  # Time tracking upper bound in minutes


class CreateTicketInput(BaseModel):
    """Validated input for creating a new RT ticket."""

    model_config = ConfigDict(extra="forbid")

    queue: str = Field(..., min_length=1, max_length=MAX_SHORT_FIELD)
    subject: str = Field(..., min_length=1, max_length=MAX_SUBJECT)
    text: str = Field(default="", max_length=MAX_TEXT)
    requestor: str = Field(default="", max_length=MAX_SHORT_FIELD)
    owner: str = Field(default="", max_length=MAX_SHORT_FIELD)
    priority: int = Field(default=0, ge=0, le=MAX_PRIORITY)


class TicketCommentInput(BaseModel):
    """Validated input for adding a comment or reply to a ticket."""

    model_config = ConfigDict(extra="forbid")

    ticket_id: int = Field(..., gt=0)
    content: str = Field(..., min_length=1, max_length=MAX_TEXT)


class SetTicketOwnerInput(BaseModel):
    """Validated input for changing ticket ownership."""

    model_config = ConfigDict(extra="forbid")

    ticket_id: int = Field(..., gt=0)
    owner: str = Field(..., min_length=1, max_length=MAX_SHORT_FIELD)


VALID_TICKET_STATUSES = {"new", "open", "stalled", "resolved", "rejected", "deleted"}


class SetTicketStatusInput(BaseModel):
    """Validated input for changing ticket status."""

    model_config = ConfigDict(extra="forbid")

    ticket_id: int = Field(..., gt=0)
    status: str = Field(..., min_length=1, max_length=MAX_STATUS)


class TimeWorkedInput(BaseModel):
    """Validated input for setting or adding time worked."""

    model_config = ConfigDict(extra="forbid")

    ticket_id: int = Field(..., gt=0)
    minutes: int = Field(..., gt=0, le=MAX_MINUTES)


class WeeklyChecklistInput(BaseModel):
    """Validated input for completing a weekly checklist."""

    model_config = ConfigDict(extra="forbid")

    ticket_id: int = Field(..., gt=0)
    owner: str = Field(..., min_length=1, max_length=MAX_SHORT_FIELD)
    checklist_results: str = Field(..., min_length=1, max_length=MAX_TEXT)
    time_minutes: int = Field(default=0, ge=0, le=MAX_MINUTES)
