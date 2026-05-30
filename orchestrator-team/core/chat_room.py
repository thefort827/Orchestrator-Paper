from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING

from protocols.message import Message

if TYPE_CHECKING:
    from core.agent import BaseAgent
    from core.memory import Memory


ORCHESTRATOR_ID = "orchestrator"


class ChatRoom:
    def __init__(self, memory: Memory):
        self.memory = memory
        self.participants: dict[str, BaseAgent] = {}
        self._round = 0
        self._meeting_mode = False

    @property
    def meeting_mode(self) -> bool:
        return self._meeting_mode

    @meeting_mode.setter
    def meeting_mode(self, value: bool):
        self._meeting_mode = value

    def _can_send(self, sender: str, target_id: str) -> bool:
        """Only PM can send to non-PM agents outside meeting mode."""
        if sender == target_id:
            return True
        if self._meeting_mode:
            return True
        if sender == ORCHESTRATOR_ID:
            return True
        if target_id == ORCHESTRATOR_ID:
            return True
        return False

    def register(self, agent: BaseAgent):
        self.participants[agent.agent_id] = agent

    def broadcast(self, msg: Message):
        self.memory.add_shared({"role": "system", "content": f"[{msg.sender}] {msg.content}"})
        print(f"\n  [{msg.sender}] {msg.content}\n")
        for pid, agent in self.participants.items():
            if pid != msg.sender and self._can_send(msg.sender, pid):
                agent.receive(msg)

    def send_to(self, msg: Message, target_id: str):
        if not self._can_send(msg.sender, target_id):
            print(f"\n  [!] 路由阻止: {msg.sender} 不能直接发送给 {target_id}（仅项目经理可分配任务）")
            return
        self.memory.add_shared({"role": "system", "content": f"[{msg.sender}->{target_id}] {msg.content}"})
        print(f"\n  [{msg.sender}->{target_id}] {msg.content}\n")
        if target_id in self.participants:
            self.participants[target_id].receive(msg)

    def broadcast_msg(self, sender: str, content: str):
        """Convenience: create a Message and broadcast it."""
        msg = Message(sender=sender, content=content, msg_type="system")
        self.broadcast(msg)

    def create_message(self, sender: str, content: str, recipients: list[str] | None = None) -> Message:
        return Message(sender=sender, content=content, recipients=recipients, msg_type="system")

    async def broadcast_async(self, msg: Message):
        self.memory.add_shared({"role": "system", "content": f"[{msg.sender}] {msg.content}"})
        print(f"\n  [{msg.sender}] {msg.content}\n")
        tasks = []
        for pid, agent in self.participants.items():
            if pid != msg.sender and self._can_send(msg.sender, pid):
                agent.receive(msg)
        for pid, agent in self.participants.items():
            if pid != msg.sender and self._can_send(msg.sender, pid):
                tasks.append(asyncio.create_task(agent.respond_async()))
        if tasks:
            await asyncio.gather(*tasks)

    async def discuss_async(self, topic: str, initiator: str, rounds: int = 2) -> list[str]:
        msg = Message(sender=initiator, content=f"【讨论启动】{topic}", msg_type="discussion")
        self.memory.add_shared({"role": "user", "content": f"[{initiator}] 发起讨论: {topic}"})
        for pid in self.participants:
            if pid != initiator:
                self.participants[pid].receive(msg)

        pm = self.participants.get(initiator)
        round_replies = {}

        for i in range(rounds):
            tasks = {}
            for pid, agent in self.participants.items():
                tasks[pid] = asyncio.create_task(agent.respond_async())
            round_replies = {}
            for pid, task in tasks.items():
                reply = await task
                if reply:
                    round_replies[pid] = reply

            feedback_msgs = []
            for pid, reply in round_replies.items():
                line = f"[{pid}]: {reply}"
                feedback_msgs.append(line)
                self.memory.add_shared({"role": "user", "content": line})
                print(f"  {line}")

            if i < rounds - 1:
                digest = "\n".join(feedback_msgs)
                digest_msg = Message(
                    sender="system",
                    content=f"[第{i+1}轮讨论摘要]\n{digest}\n\n请参考以上意见，如有不同看法可以提出辩论。",
                    msg_type="discussion_feedback",
                )
                for pid, agent in self.participants.items():
                    agent.receive(digest_msg)

        if pm and round_replies:
            summary_msg = Message(
                sender="system",
                content="请总结本轮讨论，归纳共识和分歧点，并给出最终结论。",
                msg_type="discussion_summary",
            )
            pm.receive(summary_msg)
            summary = await pm.respond_async() or ""
            print(f"\n  [讨论总结] {summary}")
            self.memory.add_shared({"role": "user", "content": f"[讨论总结] {summary}"})

        return [f"[{pid}]: {reply}" for pid, reply in round_replies.items()]

    def discuss(self, topic: str, initiator: str, rounds: int = 3) -> str:
        pm = self.participants.get(initiator)
        if pm:
            pm.say(f"发起讨论: {topic}")
        conclusions = []

        for i in range(rounds):
            for pid, agent in self.participants.items():
                reply = agent.respond()
                if reply:
                    conclusions.append(f"[{pid}]: {reply}")
                    self.memory.add_shared({"role": "user", "content": f"[{pid}]: {reply}"})

            if i < rounds - 1:
                for pid, agent in self.participants.items():
                    agent.receive(Message(
                        sender="system",
                        content=f"请参考其他成员在第{i+1}轮的意见，如有不同看法可以提出辩论。",
                        msg_type="discussion_feedback",
                    ))

        return "\n".join(conclusions) if conclusions else f"讨论完成: {topic}"
