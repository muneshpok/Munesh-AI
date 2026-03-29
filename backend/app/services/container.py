from app.services.agents.base import BaseAgent
from app.services.agents.lifecycle import AgentLifecycleManager
from app.services.agents.orchestrator import MultiAgentOrchestrator
from app.services.execution.task_engine import TaskExecutionEngine
from app.services.memory.long_term import LongTermMemory
from app.services.memory.short_term import ShortTermMemory
from app.services.tools.api_caller import APICallerTool
from app.services.tools.file_reader import FileReaderTool
from app.services.tools.registry import ToolRegistry
from app.services.tools.web_search import WebSearchTool


class ServiceContainer:
    def __init__(self) -> None:
        self.short_memory = ShortTermMemory()
        self.long_memory = LongTermMemory()
        self.tools = ToolRegistry()
        self.lifecycle = AgentLifecycleManager()
        self.engine = TaskExecutionEngine()
        self._register_tools()
        self._register_agents()
        self.orchestrator = MultiAgentOrchestrator(self.lifecycle, self.engine)

    def _register_tools(self) -> None:
        self.tools.register(WebSearchTool())
        self.tools.register(FileReaderTool())
        self.tools.register(APICallerTool())

    def _register_agents(self) -> None:
        general = BaseAgent("general", self.tools, self.short_memory, self.long_memory)
        research = BaseAgent("research", self.tools, self.short_memory, self.long_memory)
        planner = BaseAgent("planner", self.tools, self.short_memory, self.long_memory)
        for agent in (general, research, planner):
            self.lifecycle.register(agent)


container = ServiceContainer()
