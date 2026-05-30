import os
from dotenv import load_dotenv
from dataclasses import dataclass, field

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_API_KEY_HERE")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")


@dataclass
class LLMConfig:
    model: str = "mimo-v2.5-pro"
    api_key: str = DEEPSEEK_API_KEY
    base_url: str = DEEPSEEK_BASE_URL
    temperature: float = 0.3
    max_tokens: int = 4096


@dataclass
class AgentRoleConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    allowed_commands: list[str] | None = None
    denied_commands: list[str] | None = None
    allowed_paths: list[str] | None = None
    denied_paths: list[str] | None = None
    extra_tools: list[str] | None = None
    claim_keywords: list[str] | None = None


LLM_CONFIGS = {
    "orchestrator": LLMConfig(temperature=0.3, max_tokens=4096),
    "architect": LLMConfig(temperature=0.2, max_tokens=8192),
    "frontend_dev": LLMConfig(temperature=0.4, max_tokens=8192),
    "backend_dev": LLMConfig(temperature=0.3, max_tokens=8192),
    "qa_engineer": LLMConfig(temperature=0.2, max_tokens=4096),
    "devops": LLMConfig(temperature=0.3, max_tokens=4096),
}

AGENT_CONFIGS: dict[str, AgentRoleConfig] = {
    "orchestrator": AgentRoleConfig(
        llm=LLM_CONFIGS["orchestrator"],
        allowed_commands=["*"], denied_commands=[],
        allowed_paths=["*"], denied_paths=[],
    ),
    "architect": AgentRoleConfig(
        llm=LLM_CONFIGS["architect"],
        allowed_commands=["*"], denied_commands=[],
        allowed_paths=["*"], denied_paths=[],
        claim_keywords=["架构", "设计", "技术选型", "系统设计"],
    ),
    "frontend_dev": AgentRoleConfig(
        llm=LLM_CONFIGS["frontend_dev"],
        allowed_commands=["code_executor", "doc_generator"], denied_commands=["git_client"],
        allowed_paths=["workspace/"],
        denied_paths=["workspace/api/", "workspace/server/"],
        extra_tools=["code_executor", "test_runner"],
        claim_keywords=["前端", "ui", "界面", "组件", "样式", "html", "css"],
    ),
    "backend_dev": AgentRoleConfig(
        llm=LLM_CONFIGS["backend_dev"],
        allowed_commands=["code_executor", "doc_generator"], denied_commands=["git_client"],
        allowed_paths=["workspace/api/", "workspace/server/", "workspace/models/", "workspace/todo-app/"],
        denied_paths=["workspace/src/", "workspace/public/"],
        extra_tools=["code_executor"],
        claim_keywords=["后端", "api", "接口", "数据库", "数据模型"],
    ),
    "qa_engineer": AgentRoleConfig(
        llm=LLM_CONFIGS["qa_engineer"],
        allowed_commands=["code_executor", "test_runner", "doc_generator"], denied_commands=["git_client"],
        allowed_paths=["workspace/tests/", "workspace/src/", "workspace/api/"],
        denied_paths=[],
        extra_tools=["code_executor", "test_runner"],
        claim_keywords=["测试", "用例", "质量", "验证"],
    ),
    "devops": AgentRoleConfig(
        llm=LLM_CONFIGS["devops"],
        allowed_commands=["*"], denied_commands=[],
        allowed_paths=["*"], denied_paths=[],
        extra_tools=["code_executor", "git_client"],
        claim_keywords=["部署", "环境", "运维", "ci", "cd", "docker"],
    ),
}

SHARED_TOOLS = ["code_executor", "doc_generator", "git_client", "test_runner", "cline_runner"]
