from protocols.message import Message
from tools.base import Tool, ToolResult


def _auto_match_assignee(title: str, description: str) -> str | None:
    """Match task text to best agent via claim_keywords."""
    text = f"{title} {description}".lower()
    from config import AGENT_CONFIGS

    best_agent = None
    best_score = 0
    for aid, cfg in AGENT_CONFIGS.items():
        if aid == "orchestrator" or not cfg.claim_keywords:
            continue
        score = sum(1 for kw in cfg.claim_keywords if kw.lower() in text)
        if score >= best_score:
            best_score = score
            best_agent = aid
    return best_agent if best_score > 0 else None


class TaskManager(Tool):
    def __init__(self, task_scheduler=None, task_queue=None, vector_memory=None, memory=None, chat_room=None):
        self._task_scheduler = task_scheduler
        self._task_queue = task_queue
        self._vector_memory = vector_memory
        self._memory = memory
        self._chat_room = chat_room

    @property
    def name(self) -> str:
        return "task_manager"

    @property
    def description(self) -> str:
        return "分配任务给团队成员（项目经理专用）"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["direct_assign", "create", "publish", "complete", "list"],
                    "description": "操作类型: direct_assign=直接分配给指定人, create=创建并分配, publish=发布到队列, complete=完成, list=查看列表",
                },
                "title": {
                    "type": "string",
                    "description": "任务标题（create/publish 时需要）",
                },
                "description": {
                    "type": "string",
                    "description": "任务描述",
                },
                "assignee": {
                    "type": "string",
                    "description": "负责人ID: architect / frontend_dev / backend_dev / qa_engineer / devops",
                },
                "keywords": {
                    "type": "string",
                    "description": "用于自动分配的逗号分隔关键词（publish 时使用）",
                },
                "task_id": {
                    "type": "string",
                    "description": "任务ID（complete 时需要）",
                },
            },
            "required": ["action"],
        }

    def execute(self, action: str, title: str = "", description: str = "",
                assignee: str = "", keywords: str = "", task_id: str = "") -> ToolResult:
        if action == "direct_assign":
            if not title:
                return ToolResult(success=False, output="", error="缺少 title")
            aid = assignee or _auto_match_assignee(title, description)
            if not aid:
                return ToolResult(success=False, output="", error="无法确定分配对象，请指定 assignee")
            tid = self._task_scheduler.create_task(title, description, aid)
            msg = Message(
                sender="orchestrator",
                content=f"请完成任务: {title}\n描述: {description}",
                msg_type="task",
                recipients=[aid],
                task_id=tid,
            )
            if self._chat_room:
                self._chat_room.send_to(msg, aid)
            if self._vector_memory:
                self._vector_memory.add(f"[任务分配] {title} -> {aid}", "pm", "task",
                                        {"task_id": tid, "assignee": aid})
            return ToolResult(success=True, output=f"已直接分配任务给 {aid}: {title} (ID: {tid})")

        if action == "create":
            if not title:
                return ToolResult(success=False, output="", error="缺少 title")
            aid = assignee or _auto_match_assignee(title, description)
            tid = self._task_scheduler.create_task(title, description, aid)
            if aid:
                self._task_scheduler.assign(tid, aid)
                if assignee and aid != assignee:
                    self._memory.add_shared({"role": "system",
                        "content": f"[路由修正] 任务 '{title}' 的负责人由 {assignee} 自动修正为 {aid}（基于关键词匹配）"})
            if self._vector_memory:
                self._vector_memory.add(f"[任务] {title}: {description}", "pm", "task",
                                        {"task_id": tid, "assignee": aid or "unassigned"})
            label = aid or "待分配"
            return ToolResult(success=True, output=f"任务已创建: {title} (ID: {tid}, 负责人: {label})")

        if action == "publish":
            if not title:
                return ToolResult(success=False, output="", error="缺少 title")
            from protocols.task import Task
            task = Task(title=title, description=description, assignee=assignee or None)
            self._task_scheduler.tasks[task.task_id] = task
            self._task_queue.publish(task)
            kw_list = [k.strip() for k in keywords.split(",")] if keywords else []
            if kw_list:
                for aid, cfg in __import__("config", fromlist=["AGENT_CONFIGS"]).AGENT_CONFIGS.items():
                    if cfg.claim_keywords and any(kw in cfg.claim_keywords for kw in kw_list):
                        self._task_queue.claim(aid, cfg.claim_keywords)
            if self._vector_memory:
                self._vector_memory.add(f"[任务发布] {title}: {description}", "pm", "task")
            return ToolResult(success=True, output=f"任务已发布到队列: {title} (关键词: {keywords or '无'})")

        if action == "complete":
            if not task_id:
                return ToolResult(success=False, output="", error="缺少 task_id")
            self._task_scheduler.complete(task_id)
            return ToolResult(success=True, output=f"任务已完成: {task_id}")

        if action == "list":
            report = self._task_scheduler.status_report()
            return ToolResult(success=True, output=report)

        return ToolResult(success=False, output="", error=f"不支持的操作: {action}")
