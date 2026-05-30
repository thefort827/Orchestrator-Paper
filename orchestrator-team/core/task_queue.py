from __future__ import annotations
from typing import Callable
from collections import defaultdict

from protocols.task import Task


class TaskQueue:
    def __init__(self):
        self._pending: list[Task] = []
        self._subscriptions: dict[str, list[Callable]] = defaultdict(list)

    def publish(self, task: Task):
        self._pending.append(task)
        for callback in self._subscriptions.get(task.assignee or "*", []):
            callback(task)
        for callback in self._subscriptions.get("*", []):
            callback(task)

    def subscribe(self, agent_id: str, callback: Callable):
        self._subscriptions[agent_id].append(callback)

    def claim(self, agent_id: str, role_keywords: list[str] | None = None) -> Task | None:
        for i, task in enumerate(self._pending):
            if task.assignee == agent_id:
                self._pending.pop(i)
                return task
            if role_keywords and task.assignee is None:
                desc_lower = task.description.lower()
                if any(kw in desc_lower for kw in role_keywords):
                    task.assignee = agent_id
                    self._pending.pop(i)
                    return task
        return None
