from core.agent import BaseAgent

SYSTEM_PROMPT = """你是测试工程师 (QA Engineer) — Orchestrator 的子智能体。
职责：测试用例设计、自动化测试、质量保证。
工具：code_executor、test_runner、doc_generator
工作方式：收到 Orchestrator 分配的任务后，设计并执行测试，最后输出包含以下内容的完成摘要：
- 测试了什么、发现了什么缺陷
- 测试覆盖率
- 已知风险
- 对发布的影响
注意：Orchestrator 是唯一的指令来源。"""


def create_qa_engineer(llm_config: dict, memory, chat_room, task_scheduler, tool_registry=None):
    return BaseAgent(
        agent_id="qa_engineer",
        name="测试工程师",
        role="质量保证",
        system_prompt=SYSTEM_PROMPT,
        llm_config=llm_config,
        memory=memory,
        chat_room=chat_room,
        task_scheduler=task_scheduler,
        tool_registry=tool_registry,
    )
