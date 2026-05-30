"""Cline CLI wrapper — use cline as a sub-agent (MiMo API via cline auth)."""
from __future__ import annotations
import json
import os
import subprocess
import time
import shutil

from tools.base import Tool, ToolResult


def _find_cline() -> list[str]:
    """Return [executable, ...args] to invoke cline (via node if needed)."""
    # Use Node.js wrapper directly (the sh which returns a unix shell script on Windows)
    candidates = [
        os.path.expanduser("~/AppData/Roaming/npm/node_modules/cline/bin/cline"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return ["node", c]
    # fallback: try to find the actual binary via npm
    p = shutil.which("cline")
    if p:
        return ["node", p]
    raise RuntimeError(
        "Cline CLI not found. Install: npm install -g cline"
    )


def _parse_json_output(stdout: str) -> dict | None:
    """Extract run_result JSON from ndjson output."""
    if not stdout:
        return None
    for line in stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if data.get("type") == "run_result":
                return data
        except json.JSONDecodeError:
            continue
    return None


class ClineRunner(Tool):
    """Run Cline CLI as a sub-agent for complex coding tasks (MiMo API)."""

    @property
    def name(self) -> str:
        return "cline_runner"

    @property
    def description(self) -> str:
        return "使用 Cline AI 编码助手执行复杂的开发任务（适合大文件生成、多文件修改、需要深度上下文理解的任务）"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "要 Cline 执行的任务描述",
                },
                "cwd": {
                    "type": "string",
                    "description": "工作目录（默认当前目录）",
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时秒数（默认 120）",
                },
            },
            "required": ["prompt"],
        }

    def execute(self, prompt: str, cwd: str | None = None, timeout: int = 120) -> ToolResult:
        cline_cmd = _find_cline()
        workdir = os.path.abspath(cwd) if cwd else os.getcwd()
        env = os.environ.copy()

        cmd = cline_cmd + [
            "--json",
            "--auto-approve", "true",
            "-P", "openai-compatible",
            "--cwd", workdir,
            "--timeout", str(timeout),
            prompt,
        ]

        try:
            t0 = time.time()
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=workdir,
            )
            stdout_bytes, stderr_bytes = proc.communicate(timeout=timeout + 30)
            elapsed = time.time() - t0
        except subprocess.TimeoutExpired:
            proc.kill()
            return ToolResult(success=False, output="", error=f"Cline CLI 超时（{timeout}s）")
        except FileNotFoundError as e:
            return ToolResult(success=False, output="", error=f"Cline CLI 未找到: {e}")

        try:
            stdout_text = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
            stderr_text = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
        except Exception:
            stdout_text = ""
            stderr_text = ""

        run_data = _parse_json_output(stdout_text)

        if run_data:
            finish = run_data.get("finishReason", "")
            text = run_data.get("text", "")
            usage = run_data.get("usage", {})
            tokens = usage.get("inputTokens", 0) + usage.get("outputTokens", 0)
            if finish == "completed" and text:
                return ToolResult(
                    success=True,
                    output=f"[Cline] ({tokens} tokens, {elapsed:.0f}s)\n{text[:4000]}",
                )
            return ToolResult(
                success=False,
                output=text[:1000],
                error=f"finishReason={finish}, tokens={tokens}",
            )

        if proc.returncode != 0:
            return ToolResult(
                success=False, output=stdout_text[:1000], error=stderr_text[:1000]
            )

        return ToolResult(
            success=True,
            output=f"[Cline] ({elapsed:.0f}s)\n{stdout_text[:3000]}",
        )


class ClineSubAgent:
    """High-level API to use Cline as a sub-agent within an agent loop."""

    def __init__(self):
        pass

    def run(self, prompt: str, cwd: str | None = None, timeout: int = 120) -> str:
        result = ClineRunner().execute(prompt=prompt, cwd=cwd, timeout=timeout)
        if result.success:
            return result.output
        return f"[Cline 执行失败] {result.error}"
