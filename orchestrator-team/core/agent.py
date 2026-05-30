from __future__ import annotations
import json
import asyncio
from collections import Counter
from typing import TYPE_CHECKING

from core.llm import LLMClient
from core.error_handler import logger
from protocols.message import Message

if TYPE_CHECKING:
    from core.memory import Memory
    from core.chat_room import ChatRoom
    from core.task_scheduler import TaskScheduler
    from tools.registry import ToolRegistry


class BaseAgent:
    MAX_ROUNDS = 15

    def __init__(self, agent_id: str, name: str, role: str, system_prompt: str,
                 llm_config: dict, memory: Memory, chat_room: ChatRoom | None = None,
                 task_scheduler: TaskScheduler | None = None,
                 tool_registry: ToolRegistry | None = None,
                 use_compressed_context: bool = True):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm = LLMClient(**llm_config)
        self.memory = memory
        self.chat_room = chat_room
        self.task_scheduler = task_scheduler
        self.tool_registry = tool_registry
        self._inbox: list[Message] = []
        self.use_compressed_context = use_compressed_context

    def receive(self, msg: Message):
        self._inbox.append(msg)
        entry = {"role": "user", "content": f"[{msg.sender}] {msg.content}"}
        self.memory.add(self.agent_id, entry)
        if msg.sender == "user":
            self.memory.add_shared(entry)

    def respond(self) -> str | None:
        if not self._inbox:
            return None
        msg = self._inbox.pop(0)
        return self._process(msg)

    async def respond_async(self) -> str | None:
        if not self._inbox:
            return None
        msg = self._inbox.pop(0)
        return await self._process_async(msg)

    def _process(self, msg: Message) -> str:
        messages = self._build_messages(msg)
        tools_def = self.tool_registry.to_openai_tools() if self.tool_registry else None
        consecutive_failures: Counter = Counter()

        for _ in range(self.MAX_ROUNDS):
            try:
                reply, tool_calls = self.llm.chat(messages, tools=tools_def)
            except Exception as e:
                logger.error(f"Agent {self.agent_id} LLM 调用失败: {e}")
                return f"抱歉，处理时出错: {e}"

            if not tool_calls:
                if msg.task_id and self.task_scheduler:
                    self.task_scheduler.complete(msg.task_id)
                return reply

            self._append_tool_calls(messages, reply, tool_calls)
            results = self._execute_tools(messages, tool_calls)
            self._track_failures(messages, results, consecutive_failures)

        final = self._final_llm_call(messages)
        if msg.task_id and self.task_scheduler:
            self.task_scheduler.complete(msg.task_id)
        return final

    async def _process_async(self, msg: Message) -> str:
        messages = self._build_messages(msg)
        tools_def = self.tool_registry.to_openai_tools() if self.tool_registry else None
        consecutive_failures: Counter = Counter()

        for _ in range(self.MAX_ROUNDS):
            try:
                reply, tool_calls = (
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.llm.chat, messages, tools_def
                    )
                )
            except Exception as e:
                logger.error(f"Agent {self.agent_id} async LLM 失败: {e}")
                return f"抱歉，处理时出错: {e}"

            if not tool_calls:
                if msg.task_id and self.task_scheduler:
                    self.task_scheduler.complete(msg.task_id)
                print(f"\n  [{self.agent_id}] {reply}")
                return reply

            self._append_tool_calls(messages, reply, tool_calls)
            results = self._execute_tools(messages, tool_calls)
            self._track_failures(messages, results, consecutive_failures)

        final = self._final_llm_call(messages)
        if msg.task_id and self.task_scheduler:
            self.task_scheduler.complete(msg.task_id)
        return final

    def _build_messages(self, msg: Message) -> list[dict]:
        if self.use_compressed_context:
            system_entries, handoff = self.memory.get_compressed_context(self.agent_id)
            handoff_note = {"role": "system", "content": f"[上下文摘要]\n{handoff.to_markdown()}"}
            return [
                {"role": "system", "content": self.system_prompt},
                handoff_note,
                *system_entries,
                {"role": "user", "content": msg.content},
            ]
        return [
            {"role": "system", "content": self.system_prompt},
            *self.memory.build_context(self.agent_id),
            {"role": "user", "content": msg.content},
        ]

    def _append_tool_calls(self, messages: list[dict], reply: str, tool_calls: list):
        tc_msg = {"role": "assistant", "content": reply, "tool_calls": [
            {"id": tc["id"], "type": "function", "function": tc["function"]}
            for tc in tool_calls
        ]}
        messages.append(tc_msg)
        self.memory.add(self.agent_id, tc_msg)

    def _execute_tools(self, messages: list[dict], tool_calls: list) -> list[tuple[str, bool]]:
        results: list[tuple[str, bool]] = []
        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            try:
                fn_args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                fn_args = {}
            try:
                result = self.tool_registry.execute(fn_name, **fn_args)
                success = True
            except Exception as e:
                result = f"工具执行异常: {e}"
                success = False
                logger.error(f"Agent {self.agent_id} 工具 {fn_name} 异常: {e}")
            self.memory.add(self.agent_id, {"role": "tool", "tool_call_id": tc["id"], "content": f"[工具 {fn_name}] 返回:\n{result}"})
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
            results.append((fn_name, success))
        return results

    def _track_failures(self, messages: list[dict], results: list[tuple[str, bool]], consecutive_failures: Counter):
        any_failure = False
        for fn_name, success in results:
            if not success:
                any_failure = True
                consecutive_failures[fn_name] += 1
            else:
                consecutive_failures[fn_name] = 0

        if not any_failure:
            return

        if consecutive_failures.total() >= 6:
            hint = (
                "[系统提示] 工具调用已连续失败多次，请立即停止使用工具，"
                "直接用文字回复当前结果或错误信息。"
            )
            messages.append({"role": "system", "content": hint})
            return

        for fn_name, count in consecutive_failures.items():
            if count == 3:
                hint = (
                    f"[系统提示] 工具 {fn_name} 已连续失败 {count} 次。"
                    "请立即停止使用此工具，尝试以下替代方案："
                    "1) 使用其他可用工具完成相同目标；"
                    "2) 将大任务拆分为多个小步骤；"
                    "3) 直接用文字回复结果。"
                )
                messages.append({"role": "system", "content": hint})
            elif count == 5:
                hint = (
                    f"[系统提示] 工具 {fn_name} 已连续失败 {count} 次。"
                    "请立即放弃使用工具，直接用文字回复。"
                )
                messages.append({"role": "system", "content": hint})

    def _final_llm_call(self, messages: list[dict]) -> str:
        try:
            final, _ = self.llm.chat(messages)
            return final
        except Exception as e:
            return f"超出最大工具调用轮次，最后错误: {e}"

    def say(self, content: str, recipients: list[str] | None = None):
        msg = Message(sender=self.agent_id, content=content, recipients=recipients)
        if recipients and len(recipients) == 1:
            self.chat_room.send_to(msg, recipients[0])
        else:
            self.chat_room.broadcast(msg)

    async def respond_async_silent(self) -> str | None:
        """静默执行：不打印输出，供并行调用。"""
        if not self._inbox:
            return None
        msg = self._inbox.pop(0)
        return await self._process_async_silent(msg)

    async def _process_async_silent(self, msg: Message) -> str:
        messages = self._build_messages(msg)
        tools_def = self.tool_registry.to_openai_tools() if self.tool_registry else None
        consecutive_failures: Counter = Counter()

        for _ in range(self.MAX_ROUNDS):
            try:
                reply, tool_calls = (
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.llm.chat, messages, tools_def
                    )
                )
            except Exception as e:
                return f"LLM error: {e}"

            if not tool_calls:
                if msg.task_id and self.task_scheduler:
                    self.task_scheduler.complete(msg.task_id)
                return reply

            self._append_tool_calls(messages, reply, tool_calls)
            results = self._execute_tools(messages, tool_calls)
            self._track_failures(messages, results, consecutive_failures)

        final = self._final_llm_call(messages)
        if msg.task_id and self.task_scheduler:
            self.task_scheduler.complete(msg.task_id)
        return final


async def run_parallel(agents: list[BaseAgent]) -> dict[str, str]:
    """并行执行多个 agent 的 inbox 任务，返回 {agent_id: reply}。"""
    tasks = {}
    for agent in agents:
        if agent._inbox:
            tasks[agent.agent_id] = agent.respond_async_silent()

    if not tasks:
        return {}

    results = await asyncio.gather(
        *[coro for coro in tasks.values()],
        return_exceptions=True,
    )
    return {
        aid: (str(r) if not isinstance(r, Exception) else f"ERROR: {r}")
        for aid, r in zip(tasks.keys(), results)
    }
