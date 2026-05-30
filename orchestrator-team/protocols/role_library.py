"""Dynamic role library — generates meeting participants based on task features."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class RoleDef:
    id: str
    name: str
    description: str
    triggers: list[str]  # keywords in task description that activate this role
    core: bool = False   # core member = included in specialist小组


ROLE_LIBRARY: list[RoleDef] = [
    RoleDef("architect", "架构师", "系统设计、技术选型、架构评审",
            triggers=["架构", "设计", "技术选型", "系统设计", "方案"], core=True),
    RoleDef("frontend_dev", "前端工程师", "HTML/CSS/JS 界面、交互实现",
            triggers=["前端", "界面", "UI", "组件", "样式", "html", "css", "交互"], core=True),
    RoleDef("backend_dev", "后端工程师", "API 开发、数据库、业务逻辑",
            triggers=["后端", "API", "接口", "数据库", "数据模型", "服务端"], core=True),
    RoleDef("qa_engineer", "测试工程师", "测试用例、质量验证、自动化测试",
            triggers=["测试", "质量", "验证", "自动化", "用例"], core=False),
    RoleDef("devops", "DevOps 工程师", "部署、CI/CD、监控、运维",
            triggers=["部署", "运维", "CI", "CD", "Docker", "环境"], core=False),
    RoleDef("security_auditor", "安全审计师", "安全审查、渗透测试、合规检查",
            triggers=["安全", "支付", "金融", "合规", "审计", "隐私"], core=False),
    RoleDef("mobile_expert", "移动端专家", "iOS/Android 开发、推送、离线存储",
            triggers=["移动端", "推送", "Android", "iOS", "APP", "手机"], core=False),
    RoleDef("product_manager", "产品经理", "需求分析、功能定义、用户故事",
            triggers=["产品", "需求", "功能", "用户故事", "PRD"], core=False),
]


def resolve_roles(task_description: str) -> list[RoleDef]:
    """Match task description against role triggers, returning matched roles."""
    text = task_description.lower()
    matched = []
    for role in ROLE_LIBRARY:
        if any(kw in text for kw in role.triggers):
            matched.append(role)
    # Always include architect for non-trivial tasks
    if not matched:
        matched = [r for r in ROLE_LIBRARY if r.id == "architect"]
    return matched


def split_meeting(matched_roles: list[RoleDef]) -> tuple[list[RoleDef], list[RoleDef]]:
    """Split into specialist小组 (core) and full评审 (all)."""
    core_team = [r for r in matched_roles if r.core]
    full_team = matched_roles
    return core_team, full_team
