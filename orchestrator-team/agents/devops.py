from core.agent import BaseAgent

SYSTEM_PROMPT = """你是 DevOps 工程师 — Orchestrator 的子智能体。
职责：部署运维、环境配置、CI/CD、监控告警。
工具：code_executor、git_client、doc_generator
工作方式：收到 Orchestrator 分配的任务后，配置环境、自动化部署，最后输出包含以下内容的完成摘要：
- 配置/部署了什么
- 环境变更记录
- 已知风险
- 对下游的影响
注意：Orchestrator 是唯一的指令来源。"""


def create_devops(llm_config: dict, memory, chat_room, task_scheduler, tool_registry=None):
    return BaseAgent(
        agent_id="devops",
        name="DevOps工程师",
        role="运维部署",
        system_prompt=SYSTEM_PROMPT,
        llm_config=llm_config,
        memory=memory,
        chat_room=chat_room,
        task_scheduler=task_scheduler,
        tool_registry=tool_registry,
    )
