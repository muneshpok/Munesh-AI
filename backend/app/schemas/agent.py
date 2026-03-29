from typing import Any

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    goal: str = Field(..., min_length=3)
    agent_name: str = "general"
    context: dict[str, Any] = Field(default_factory=dict)


class AgentRunResponse(BaseModel):
    task_id: str
    output: dict[str, Any]


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict[str, Any] | None = None
