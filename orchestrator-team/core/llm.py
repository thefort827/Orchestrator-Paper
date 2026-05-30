import re
import json
import uuid
from openai import OpenAI


def _parse_dsml(content: str) -> list[dict] | None:
    """Parse tool calls from content text (DeepSeek DSML or plain XML-like format)."""
    patterns = [
        r'<dsml>invoke name="([^"]+)">(.*?)</dsml>invoke>',
        r'<invoke name="([^"]+)">(.*?)(?:</invoke>|</tool_calls>|$)',
        r'^<invoke name="([^"]+)">(.*?)(?:</invoke>|$)',
    ]

    if not any(tag in content for tag in ("<invoke", "<dsml>invoke", "<tool_calls")):
        return None

    TOOL_PRIMARY_PARAM = {
        "code_executor": "code",
        "doc_generator": "content",
    }

    def _extract_params(body: str) -> dict[str, str]:
        args = {}
        for pm in re.finditer(
            r'<parameter name="([^"]+)"(?:\s+string="true")?>(.*?)(?:</parameter>|$)',
            body, re.DOTALL
        ):
            pname = pm.group(1)
            pval = pm.group(2).strip()
            if pval.startswith("'''") and pval.endswith("'''"):
                pval = pval[3:-3]
            elif pval.startswith('"""') and pval.endswith('"""'):
                pval = pval[3:-3]
            args[pname] = pval

        if args:
            return args

        stripped = body.strip()
        if not stripped:
            return args

        first_word = stripped.split()[0]
        if "=" in first_word:
            for kv in re.findall(r'(\w+)=(["\']?)([^"\']*?)\2(?:\s|$)', stripped):
                args[kv[0]] = kv[2]
        return args

    calls = []
    for pat in patterns:
        for match in re.finditer(pat, content, re.DOTALL):
            name = match.group(1)
            body = match.group(2)
            args = _extract_params(body)

            if not args:
                primary = TOOL_PRIMARY_PARAM.get(name)
                stripped = body.strip()
                if primary and stripped:
                    args[primary] = stripped
                elif primary:
                    args[primary] = ""

            if name not in {c["function"]["name"] for c in calls}:
                calls.append({
                    "id": f"call_{uuid.uuid4().hex[:8]}",
                    "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)},
                })
    return calls if calls else None


def _filter_valid_calls(calls: list[dict], tools_def: list[dict]) -> list[dict]:
    """Drop DSML calls whose required params are missing."""
    required_map: dict[str, list[str]] = {}
    for td in tools_def:
        fn = td.get("function", td)
        params = fn.get("parameters", {})
        required_map[fn["name"]] = params.get("required", [])

    valid = []
    for c in calls:
        name = c["function"]["name"]
        try:
            args = json.loads(c["function"]["arguments"])
        except (json.JSONDecodeError, TypeError):
            continue
        missing = [k for k in required_map.get(name, []) if k not in args or not args[k]]
        if missing:
            continue
        valid.append(c)
    return valid


class LLMClient:
    def __init__(self, model: str, api_key: str, base_url: str, temperature: float = 0.3, max_tokens: int = 4096):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.reset_usage()

    def reset_usage(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_calls = 0

    @property
    def total_tokens(self):
        return self.total_prompt_tokens + self.total_completion_tokens

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> tuple[str, list | None]:
        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        resp = self.client.chat.completions.create(**kwargs)
        self.total_calls += 1
        if hasattr(resp, "usage") and resp.usage:
            self.total_prompt_tokens += resp.usage.prompt_tokens or 0
            self.total_completion_tokens += resp.usage.completion_tokens or 0
        msg = resp.choices[0].message

        content = msg.content or ""

        if msg.tool_calls:
            tc_list = [
                {"id": tc.id, "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
            dsml_calls = _parse_dsml(content)
            if dsml_calls:
                for c in dsml_calls:
                    try:
                        json.loads(c["function"]["arguments"])
                    except json.JSONDecodeError:
                        c["function"]["arguments"] = "{}"
                dsml_map = {}
                for c in dsml_calls:
                    try:
                        dsml_map[c["function"]["name"]] = json.loads(c["function"]["arguments"])
                    except json.JSONDecodeError:
                        pass
                for tc in tc_list:
                    try:
                        tc_args = json.loads(tc["function"]["arguments"]) if tc["function"]["arguments"] else {}
                    except json.JSONDecodeError:
                        tc_args = {}
                    if not tc_args or tc_args == {}:
                        fn = tc["function"]["name"]
                        if fn in dsml_map:
                            tc["function"]["arguments"] = json.dumps(dsml_map[fn], ensure_ascii=False)
            validated = _filter_valid_calls(tc_list, tools or [])
            return content, validated if validated else None

        dsml_calls = _parse_dsml(content)
        if dsml_calls:
            validated = _filter_valid_calls(dsml_calls, tools or [])
            if validated:
                stripped = re.sub(r'<dsml>.*?</dsml>', "", content, flags=re.DOTALL).strip()
                return stripped, validated
            return content, None
        return content, None

    def chat_stream(self, messages: list[dict], tools: list[dict] | None = None):
        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        stream = self.client.chat.completions.create(**kwargs)
        collected_content = []
        tool_calls_data = {}

        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if not delta:
                continue

            if delta.content:
                collected_content.append(delta.content)
                print(delta.content, end="", flush=True)

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_data:
                        tool_calls_data[idx] = {"id": "", "function": {"name": "", "arguments": ""}}
                    if tc.id:
                        tool_calls_data[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls_data[idx]["function"]["name"] += tc.function.name
                        if tc.function.arguments:
                            tool_calls_data[idx]["function"]["arguments"] += tc.function.arguments

        print()
        content = "".join(collected_content)

        if tool_calls_data:
            return content, [
                {"id": d["id"], "function": {"name": d["function"]["name"], "arguments": d["function"]["arguments"]}}
                for d in sorted(tool_calls_data.values(), key=lambda x: list(tool_calls_data.keys())[0])
            ]
        return content, None
