from collections import defaultdict, deque


class ShortTermMemory:
    def __init__(self, max_items: int = 20) -> None:
        self.max_items = max_items
        self._store: dict[str, deque[dict[str, str]]] = defaultdict(lambda: deque(maxlen=max_items))

    def add(self, session_id: str, role: str, content: str) -> None:
        self._store[session_id].append({"role": role, "content": content})

    def get(self, session_id: str) -> list[dict[str, str]]:
        return list(self._store[session_id])
