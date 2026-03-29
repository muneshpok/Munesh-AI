from app.services.agents.base import BaseAgent


class AgentLifecycleManager:
    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> BaseAgent:
        return self._agents[name]

    def all(self) -> list[str]:
        return list(self._agents.keys())
