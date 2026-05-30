from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class CompletionSummary:
    """Sub-agent structured completion report — replaces raw conversation history."""
    agent_id: str
    task_id: str
    task_title: str
    status: str  # "completed" | "failed" | "partial"
    files_modified: list[str] = field(default_factory=list)
    key_decisions: list[str] = field(default_factory=list)
    known_limitations: list[str] = field(default_factory=list)
    downstream_impact: str = ""
    summary: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_markdown(self) -> str:
        lines = [
            f"## 完成摘要: {self.task_title}",
            f"**状态**: {self.status}",
            f"**负责人**: {self.agent_id}",
            f"**简述**: {self.summary}",
        ]
        if self.files_modified:
            lines.append("\n**修改的文件**:")
            for f in self.files_modified:
                lines.append(f"- {f}")
        if self.key_decisions:
            lines.append("\n**关键决策**:")
            for d in self.key_decisions:
                lines.append(f"- {d}")
        if self.known_limitations:
            lines.append("\n**已知限制**:")
            for l in self.known_limitations:
                lines.append(f"- {l}")
        if self.downstream_impact:
            lines.append(f"\n**下游影响**: {self.downstream_impact}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "task_title": self.task_title,
            "status": self.status,
            "files_modified": self.files_modified,
            "key_decisions": self.key_decisions,
            "known_limitations": self.known_limitations,
            "downstream_impact": self.downstream_impact,
            "summary": self.summary,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> CompletionSummary:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
