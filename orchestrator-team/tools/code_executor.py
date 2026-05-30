import os
import sys
import io
import textwrap
import traceback

from tools.base import Tool, ToolResult


def _make_safe_open(allowed_paths: list[str], denied_paths: list[str]):
    cwd = os.getcwd().replace("\\", "/") + "/"
    abs_allowed = []
    for a in (allowed_paths or ["*"]):
        if a == "*":
            abs_allowed.append("*")
        else:
            p = a.replace("\\", "/")
            abs_allowed.append(p if os.path.isabs(p) else cwd + p.lstrip("/"))
    abs_denied = []
    for d in (denied_paths or []):
        p = d.replace("\\", "/")
        abs_denied.append(p if os.path.isabs(p) else cwd + p.lstrip("/"))

    def safe_open(filepath: str, mode: str = "r", **kwargs):
        abs_path = os.path.abspath(filepath).replace("\\", "/")
        for d in abs_denied:
            if abs_path.startswith(d):
                raise PermissionError(f"[沙箱] 拒绝访问禁止路径: {filepath}")
        if "*" not in abs_allowed:
            ok = any(abs_path.startswith(a) for a in abs_allowed)
            if not ok:
                raise PermissionError(f"[沙箱] 拒绝访问: {filepath} (路径不在白名单)")
        return open(filepath, mode, **kwargs)
    return safe_open


class CodeExecutor(Tool):
    def __init__(self, allowed_paths: list[str] | None = None, denied_paths: list[str] | None = None):
        self._allowed = allowed_paths or ["*"]
        self._denied = denied_paths or []

    @property
    def name(self) -> str:
        return "code_executor"

    @property
    def description(self) -> str:
        return "在沙箱中执行 Python 代码并返回输出结果"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要执行的 Python 代码",
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（秒）",
                    "default": 30,
                },
            },
            "required": ["code"],
        }

    def execute(self, code: str, timeout: int = 30) -> ToolResult:
        safe_open = _make_safe_open(self._allowed, self._denied)
        safe_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "int": int,
                "float": float,
                "str": str,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "bool": bool,
                "True": True,
                "False": False,
                "None": None,
                "abs": abs,
                "all": all,
                "any": any,
                "enumerate": enumerate,
                "filter": filter,
                "map": map,
                "max": max,
                "min": min,
                "pow": pow,
                "reversed": reversed,
                "round": round,
                "sorted": sorted,
                "sum": sum,
                "zip": zip,
                "isinstance": isinstance,
                "type": type,
                "hasattr": hasattr,
                "getattr": getattr,
                "setattr": setattr,
                "open": safe_open,
                "__import__": __import__,
            }
        }
        stdout = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = stdout
        try:
            dedented = textwrap.dedent(code)
            exec(dedented, safe_globals)
            output = stdout.getvalue()
            return ToolResult(success=True, output=output or "代码执行成功（无输出）")
        except Exception:
            return ToolResult(success=False, output="", error=traceback.format_exc())
        finally:
            sys.stdout = old_stdout
