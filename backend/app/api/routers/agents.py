from fastapi import APIRouter, HTTPException

from app.schemas.agent import AgentRunRequest, AgentRunResponse, TaskStatusResponse
from app.services.container import container

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[str])
def list_agents() -> list[str]:
    return container.lifecycle.all()


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(payload: AgentRunRequest) -> AgentRunResponse:
    if payload.agent_name not in container.lifecycle.all():
        raise HTTPException(status_code=404, detail="agent not found")
    task_id, output = await container.orchestrator.run(payload.agent_name, payload.goal, payload.context)
    return AgentRunResponse(task_id=task_id, output=output)


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def task_status(task_id: str) -> TaskStatusResponse:
    try:
        task = container.engine.get_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="task not found") from exc
    return TaskStatusResponse(task_id=task.id, status=task.status, result=task.result)
