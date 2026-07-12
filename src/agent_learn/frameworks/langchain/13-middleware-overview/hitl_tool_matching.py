"""演示 HumanInTheLoopMiddleware 如何按 tool `.name` 匹配审批目标。"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToolDescriptor:
    """描述一个可供 Agent 调用的工具名。"""

    name: str
    is_high_risk: bool = False


def should_interrupt_tool(
    tool_name: str,
    interrupt_on: dict[str, bool],
) -> bool:
    """判断指定工具是否应被 HITL middleware 拦截。

    `interrupt_on` 的 key 必须与 `@tool` 暴露给模型的 `.name` 完全一致。
    """
    normalized_name = tool_name.strip()
    if not normalized_name:
        return False
    return interrupt_on.get(normalized_name, False) is True


def build_interrupt_policy(tools: list[ToolDescriptor]) -> dict[str, bool]:
    """为所有高风险工具生成 `interrupt_on` 配置。"""
    return {tool.name: True for tool in tools if tool.is_high_risk}


def find_unprotected_high_risk_tools(
    tools: list[ToolDescriptor],
    interrupt_on: dict[str, bool],
) -> list[str]:
    """找出标记为高风险但未配置 interrupt 的工具名。"""
    unprotected: list[str] = []
    for tool in tools:
        if tool.is_high_risk and not interrupt_on.get(tool.name, False):
            unprotected.append(tool.name)
    return unprotected


def main() -> None:
    tools = [
        ToolDescriptor(name="read_inbox", is_high_risk=False),
        ToolDescriptor(name="send_email", is_high_risk=True),
        ToolDescriptor(name="send_notification", is_high_risk=True),
    ]
    interrupt_on = build_interrupt_policy(tools)

    print("interrupt_on：", interrupt_on)
    print("send_email 需审批：", should_interrupt_tool("send_email", interrupt_on))
    print("read_inbox 需审批：", should_interrupt_tool("read_inbox", interrupt_on))
    print("未保护的高风险工具：", find_unprotected_high_risk_tools(tools, interrupt_on))


if __name__ == "__main__":
    main()
