from app.services.agents.base import AgentContext
from app.services.agents.lifecycle import AgentLifecycleManager
from app.services.execution.task_engine import TaskExecutionEngine


class MultiAgentOrchestrator:
    def __init__(self, lifecycle: AgentLifecycleManager, engine: TaskExecutionEngine) -> None:
        self.lifecycle = lifecycle
        self.engine = engine

    async def run(self, agent_name: str, goal: str, metadata: dict | None = None) -> tuple[str, dict]:
        task = self.engine.start_task()
        agent = self.lifecycle.get(agent_name)
        context = AgentContext(session_id=task.id, goal=goal, metadata=metadata or {})
        result = await agent.execute(context)
        self.engine.complete_task(task.id, result)
        return task.id, result
