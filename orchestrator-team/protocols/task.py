from __future__ import annotations
from dataclasses import dataclass, field
from uuid import uuid4
from datetime import datetime, timezone


@dataclass
class Task:
    title: str
    description: str
    assignee: str | None = None
    status: str = "pending"
    complexity: str = "simple"
    dependencies: list[str] | None = None
    deliverables: list[str] | None = None
    validation_errors: list[str] | None = None
    task_id: str = field(default_factory=lambda: uuid4().hex[:12])
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "assignee": self.assignee,
            "status": self.status,
            "dependencies": self.dependencies or [],
            "deliverables": self.deliverables or [],
            "validation_errors": self.validation_errors or [],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
