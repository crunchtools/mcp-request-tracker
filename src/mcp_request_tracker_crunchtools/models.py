"""Pydantic input validation models for MCP Request Tracker.

These models validate tool inputs before they reach the API client,
enforcing field lengths, allowlists, and rejecting unexpected fields.
"""

from pydantic import BaseModel, ConfigDict, Field


class CreateTicketInput(BaseModel):
    """Validated input for creating a new RT ticket."""

    model_config = ConfigDict(extra="forbid")

    queue: str = Field(..., min_length=1, max_length=200)
    subject: str = Field(..., min_length=1, max_length=500)
    text: str = Field(default="", max_length=50000)
    requestor: str = Field(default="", max_length=200)
    owner: str = Field(default="", max_length=200)
    priority: int = Field(default=0, ge=0, le=999)


class TicketCommentInput(BaseModel):
    """Validated input for adding a comment or reply to a ticket."""

    model_config = ConfigDict(extra="forbid")

    ticket_id: int = Field(..., gt=0)
    content: str = Field(..., min_length=1, max_length=50000)


class SetTicketOwnerInput(BaseModel):
    """Validated input for changing ticket ownership."""

    model_config = ConfigDict(extra="forbid")

    ticket_id: int = Field(..., gt=0)
    owner: str = Field(..., min_length=1, max_length=200)


VALID_TICKET_STATUSES = {"new", "open", "stalled", "resolved", "rejected", "deleted"}


class SetTicketStatusInput(BaseModel):
    """Validated input for changing ticket status."""

    model_config = ConfigDict(extra="forbid")

    ticket_id: int = Field(..., gt=0)
    status: str = Field(..., min_length=1, max_length=50)


class TimeWorkedInput(BaseModel):
    """Validated input for setting or adding time worked."""

    model_config = ConfigDict(extra="forbid")

    ticket_id: int = Field(..., gt=0)
    minutes: int = Field(..., gt=0, le=99999)


class WeeklyChecklistInput(BaseModel):
    """Validated input for completing a weekly checklist."""

    model_config = ConfigDict(extra="forbid")

    ticket_id: int = Field(..., gt=0)
    owner: str = Field(..., min_length=1, max_length=200)
    checklist_results: str = Field(..., min_length=1, max_length=50000)
    time_minutes: int = Field(default=0, ge=0, le=99999)
