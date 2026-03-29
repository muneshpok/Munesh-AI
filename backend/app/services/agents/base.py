from dataclasses import dataclass, field
from typing import Any

from app.services.memory.long_term import LongTermMemory
from app.services.memory.short_term import ShortTermMemory
from app.services.tools.registry import ToolRegistry


@dataclass(slots=True)
class AgentContext:
    session_id: str
    goal: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent:
    def __init__(self, name: str, tools: ToolRegistry, short_memory: ShortTermMemory, long_memory: LongTermMemory) -> None:
        self.name = name
        self.tools = tools
        self.short_memory = short_memory
        self.long_memory = long_memory

    async def execute(self, context: AgentContext) -> dict[str, Any]:
        self.short_memory.add(context.session_id, "user", context.goal)
        relevant = self.long_memory.search(context.goal)
        tool_snapshot = self.tools.list_tools()
        response = {
            "agent": self.name,
            "goal": context.goal,
            "tools": tool_snapshot,
            "relevant_memories": relevant,
            "message": "Goal accepted and queued for decomposition.",
        }
        self.short_memory.add(context.session_id, "assistant", response["message"])
        self.long_memory.add(context.session_id, context.goal)
        return response
