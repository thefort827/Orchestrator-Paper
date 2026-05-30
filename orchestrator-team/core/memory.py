from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.vector_memory import VectorMemory
    from protocols.handoff import Handoff


class Memory:
    def __init__(self):
        self._store: dict[str, list[dict]] = defaultdict(list)
        self._shared: list[dict] = []
        self._vector_memory: VectorMemory | None = None

    def attach_vector_memory(self, vm: "VectorMemory"):
        self._vector_memory = vm

    def add(self, agent_id: str, entry: dict):
        self._store[agent_id].append(entry)

    def add_shared(self, entry: dict):
        self._shared.append(entry)
        if self._vector_memory:
            content = entry.get("content", "")
            if content:
                speaker = entry.get("speaker", "unknown") or "unknown"
                self._vector_memory.add(content, speaker, "shared", {"role": entry.get("role", "user")})

    def get_history(self, agent_id: str, limit: int = 50) -> list[dict]:
        return self._store.get(agent_id, [])[-limit:]

    def get_shared(self, limit: int = 100) -> list[dict]:
        return self._shared[-limit:]

    def get_compressed_context(self, agent_id: str) -> tuple[list[dict], "Handoff"]:
        """Return (system_prompt_entries, compressed_handoff) instead of full history."""
        system = self._store.get("system", [])
        personal = self.get_history(agent_id, limit=20)
        shared = self.get_shared(limit=30)
        from core.context_compressor import compress_history
        handoff = compress_history(system + shared + personal, agent_id)
        return system, handoff

    def build_context(self, agent_id: str, query: str | None = None,
                      vector_fallback: bool = False, min_vector_results: int = 2) -> list[dict]:
        system = self._store.get("system", [])
        personal = self.get_history(agent_id)

        if vector_fallback and self._vector_memory and query:
            vector_results = self._vector_memory.search(query, top_k=10)
            if len(vector_results) >= min_vector_results:
                relevant = []
                for item in vector_results:
                    role = item.metadata.get("role", "user")
                    relevant.append({"role": role, "content": item.content})
                system_entries = []
                for e in system:
                    entry = dict(e)
                    entry.setdefault("role", "user")
                    system_entries.append(entry)
                personal_entries = []
                for e in personal:
                    entry = dict(e)
                    entry.setdefault("role", "user")
                    personal_entries.append(entry)
                return system_entries + relevant + personal_entries

        shared = self.get_shared()
        all_entries = system + shared + personal
        result = []
        for e in all_entries:
            entry = dict(e)
            entry.setdefault("role", "user")
            result.append(entry)
        return result
