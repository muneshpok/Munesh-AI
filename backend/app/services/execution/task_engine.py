from dataclasses import dataclass
from uuid import uuid4


@dataclass(slots=True)
class TaskRecord:
    id: str
    status: str
    result: dict | None = None


class TaskExecutionEngine:
    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}

    def start_task(self) -> TaskRecord:
        task = TaskRecord(id=str(uuid4()), status="running")
        self._tasks[task.id] = task
        return task

    def complete_task(self, task_id: str, result: dict) -> None:
        task = self._tasks[task_id]
        task.status = "completed"
        task.result = result

    def get_task(self, task_id: str) -> TaskRecord:
        return self._tasks[task_id]
