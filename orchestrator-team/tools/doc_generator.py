import os

from tools.base import Tool, ToolResult


class DocGenerator(Tool):
    @property
    def name(self) -> str:
        return "doc_generator"

    @property
    def description(self) -> str:
        return "生成 Markdown 文档并保存到文件"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "文档文件名（如 README.md, api_docs.md）",
                },
                "content": {
                    "type": "string",
                    "description": "文档内容（Markdown 格式）",
                },
                "path": {
                    "type": "string",
                    "description": "保存路径，默认为 workspace",
                    "default": "workspace",
                },
            },
            "required": ["filename"],
        }

    def execute(self, filename: str, content: str = "", path: str = "workspace") -> ToolResult:
        full_dir = os.path.join(os.getcwd(), path)
        os.makedirs(full_dir, exist_ok=True)
        filepath = os.path.join(full_dir, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(success=True, output=f"文件已生成: {filepath} ({len(content)} bytes)")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
