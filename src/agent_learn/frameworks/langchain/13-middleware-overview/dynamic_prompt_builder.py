"""演示 `@dynamic_prompt` 背后的纯函数 prompt 构建逻辑（可离线测试）。"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    """描述本次请求的角色与权限。"""

    user_role: str
    tenant_name: str
    can_use_tools: bool


def build_role_aware_system_prompt(context: RuntimeContext) -> str:
    """根据 runtime context 生成中文 system prompt，供 `@dynamic_prompt` 使用。"""
    if not context.can_use_tools:
        return (
            f"你是租户 {context.tenant_name} 的学习助手。"
            "当前身份没有工具调用权限，只能基于已有上下文回答。"
            "最终答复必须使用中文。"
        )

    if context.user_role == "viewer":
        return (
            f"你是租户 {context.tenant_name} 的只读助手。"
            "你只能调用以 read_ 开头的工具，禁止执行写操作。"
            "最终答复必须使用中文。"
        )

    return (
        f"你是租户 {context.tenant_name} 的编辑助手。"
        "你可以调用读写工具完成任务，但高风险写操作必须先获得审批。" 
        "最终答复必须使用中文。"
    )


def main() -> None:
    viewer_prompt = build_role_aware_system_prompt(
        RuntimeContext(user_role="viewer", tenant_name="learning-team", can_use_tools=True)
    )
    guest_prompt = build_role_aware_system_prompt(
        RuntimeContext(user_role="guest", tenant_name="learning-team", can_use_tools=False)
    )
    print("viewer prompt：", viewer_prompt)
    print("guest prompt：", guest_prompt)


if __name__ == "__main__":
    main()
