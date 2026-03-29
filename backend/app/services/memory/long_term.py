from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class MemoryRecord:
    id: str
    text: str
    vector: np.ndarray


class LongTermMemory:
    def __init__(self) -> None:
        self._records: list[MemoryRecord] = []

    @staticmethod
    def _embed(text: str) -> np.ndarray:
        arr = np.zeros(64, dtype=np.float32)
        for i, token in enumerate(text.lower().split()[:64]):
            arr[i] = (sum(ord(c) for c in token) % 997) / 997
        norm = np.linalg.norm(arr)
        return arr / norm if norm else arr

    def add(self, record_id: str, text: str) -> None:
        self._records.append(MemoryRecord(id=record_id, text=text, vector=self._embed(text)))

    def search(self, query: str, limit: int = 3) -> list[dict[str, str]]:
        if not self._records:
            return []
        q_vec = self._embed(query)
        scored = sorted(
            self._records,
            key=lambda record: float(np.dot(q_vec, record.vector)),
            reverse=True,
        )
        return [{"id": r.id, "text": r.text} for r in scored[:limit]]
