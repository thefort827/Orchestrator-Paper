from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4
from datetime import datetime, timezone


@dataclass
class Message:
    sender: str
    content: str
    msg_type: str = "text"
    recipients: list[str] | None = None
    task_id: str | None = None
    priority: str = "medium"
    message_id: str = field(default_factory=lambda: uuid4().hex[:12])
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipients": self.recipients,
            "type": self.msg_type,
            "content": self.content,
            "task_id": self.task_id,
            "priority": self.priority,
            "timestamp": self.timestamp,
        }
