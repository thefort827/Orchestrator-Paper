"""产物校验器：在任务完成后自动检查生成文件的完整性"""
import ast
import os
import re


def validate_file_exists(filepath: str) -> list[str]:
    errors = []
    if not os.path.exists(filepath):
        errors.append(f"文件不存在: {filepath}")
    elif os.path.getsize(filepath) == 0:
        errors.append(f"文件为空: {filepath}")
    return errors


def validate_html(filepath: str) -> list[str]:
    errors = validate_file_exists(filepath)
    if errors:
        return errors
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if "<!DOCTYPE html" not in content.upper() and "<!doctype html" not in content.lower():
        errors.append("缺少 DOCTYPE 声明")
    if not re.search(r"<html[^>]*>", content, re.IGNORECASE):
        errors.append("缺少 <html> 标签")
    if not re.search(r"<body[^>]*>", content, re.IGNORECASE):
        errors.append("缺少 <body> 标签")
    if "</html>" not in content.lower():
        errors.append("缺少 </html> 闭合标签")
    if "</body>" not in content.lower():
        errors.append("缺少 </body> 闭合标签")
    script_matches = list(re.finditer(r"<script[^>]*>(.*?)</script>", content, re.DOTALL | re.IGNORECASE))
    for sm in script_matches:
        js_code = sm.group(1).strip()
        if js_code:
            try:
                compile(js_code, "<script>", "exec")
            except SyntaxError as e:
                errors.append(f"JavaScript 语法错误: {e}")
    return errors


def validate_python(filepath: str) -> list[str]:
    errors = validate_file_exists(filepath)
    if errors:
        return errors
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    try:
        ast.parse(content)
    except SyntaxError as e:
        errors.append(f"Python 语法错误: {e}")
    return errors


def validate(filepath: str) -> list[str]:
    ext = os.path.splitext(filepath)[1].lower()
    validators = {".html": validate_html, ".htm": validate_html, ".py": validate_python}
    validator = validators.get(ext, validate_file_exists)
    return validator(filepath)


def extract_deliverables(title: str, description: str) -> list[str]:
    """从任务描述中提取输出文件路径"""
    paths = []
    text = f"{title} {description}"
    for match in re.finditer(r'(?:workspace|output|输出到|生成)\s*[:=]?\s*([^\s,;\n]+(?:\.\w+)?)', text, re.IGNORECASE):
        path = match.group(1).strip().strip("'\"")
        if any(path.endswith(ext) for ext in (".html", ".htm", ".py", ".js", ".css", ".md", ".json", ".txt")):
            if not os.path.isabs(path):
                path = os.path.join(os.getcwd(), path)
            paths.append(path)
    if not paths:
        for match in re.finditer(r'([\w./\\-]+(?:\.html|\.htm|\.py|\.js|\.css))', text, re.ASCII):
            path = match.group(1).strip().strip("'\"")
            if not os.path.isabs(path):
                path = os.path.join(os.getcwd(), path)
            if os.path.exists(path):
                paths.append(path)
    return list(set(paths))
