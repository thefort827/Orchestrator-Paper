from __future__ import annotations
from typing import TYPE_CHECKING

from protocols.task import Task
from protocols.message import Message

if TYPE_CHECKING:
    from core.memory import Memory
    from core.chat_room import ChatRoom


class TaskScheduler:
    def __init__(self, memory: Memory, chat_room: ChatRoom):
        self.memory = memory
        self.chat_room = chat_room
        self.tasks: dict[str, Task] = {}

    def create_task(self, title: str, description: str, assignee: str | None = None, dependencies: list[str] | None = None) -> str:
        task = Task(title=title, description=description, assignee=assignee, dependencies=dependencies)
        self.tasks[task.task_id] = task
        self.memory.add_shared({"role": "system", "content": f"[任务创建] {task.task_id}: {title} -> {assignee}"})
        return task.task_id

    def assign(self, task_id: str, agent_id: str):
        task = self.tasks.get(task_id)
        if not task:
            return
        task.assignee = agent_id
        task.status = "in_progress"

        context_lines = []
        for entry in self.memory.get_shared():
            content = entry.get("content", "")
            if content.startswith("[user]"):
                context_lines.append(content)
        context = "\n".join(context_lines[-3:])  # last 3 user messages
        extra = f"\n\n【原始需求】\n{context}" if context else ""

        msg = Message(
            sender="orchestrator",
            content=f"请完成任务: {task.title}\n描述: {task.description}{extra}",
            msg_type="task",
            recipients=[agent_id],
            task_id=task_id,
        )
        self.chat_room.send_to(msg, agent_id)

    def complete(self, task_id: str, deliverables: list[str] | None = None):
        task = self.tasks.get(task_id)
        if not task:
            return
        task.deliverables = deliverables
        self.memory.add_shared({"role": "system", "content": f"[任务完成] {task_id}: {task.title}"})

        try:
            from tools.validators import extract_deliverables, validate
            paths = deliverables or extract_deliverables(task.title, task.description)
            all_errors = []
            for path in paths:
                errs = validate(path)
                all_errors.extend(errs)
            if all_errors:
                task.status = "review_needed"
                task.validation_errors = all_errors
                error_text = "\n".join(all_errors)
                self.memory.add_shared({"role": "system",
                    "content": f"[产物校验] {task_id}: {len(all_errors)} 个问题\n{error_text}"})
                if task.assignee:
                    review_msg = Message(
            sender="orchestrator",
                        content=f"产物校验未通过，请修正以下问题:\n{error_text}",
                        msg_type="review",
                        recipients=[task.assignee],
                        task_id=task_id,
                    )
                    self.chat_room.send_to(review_msg, task.assignee)
                return
        except Exception as e:
            self.memory.add_shared({"role": "system",
                "content": f"[产物校验] {task_id}: 校验异常 {e}"})

        task.status = "completed"
        task.validation_errors = None

    def get_pending(self) -> list[Task]:
        return [t for t in self.tasks.values() if t.status == "pending"]

    def status_report(self) -> str:
        lines = ["任务状态报告:"]
        for t in self.tasks.values():
            label = t.status
            if t.validation_errors:
                label += f" ({len(t.validation_errors)} 问题)"
            lines.append(f"  [{label}] {t.title} -> {t.assignee or '未分配'}")
        return "\n".join(lines)
