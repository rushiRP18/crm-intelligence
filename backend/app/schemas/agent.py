"""Pydantic schemas for agent runs and dry-run responses."""
from datetime import datetime
from pydantic import BaseModel
from typing import Any


class ToolCall(BaseModel):
    tool_name: str
    input: Any
    output: Any
    duration_ms: float | None = None


class AgentRunResponse(BaseModel):
    id: int
    email_id: int
    reasoning_trace: str | None
    tool_calls: list[ToolCall] | None
    decision: str | None
    draft_reply: str | None
    final_action: str | None
    run_duration_ms: float | None
    dry_run: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DryRunRequest(BaseModel):
    email_id: int
