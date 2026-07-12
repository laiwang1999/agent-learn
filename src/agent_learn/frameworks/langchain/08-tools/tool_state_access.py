"""演示工具如何通过 `ToolRuntime` 读取 state，并把核心逻辑做成可测试纯函数。"""

from typing import Any

from langchain.messages import HumanMessage
from langchain.tools import ToolRuntime, tool


def get_last_human_message_text(messages: list[Any]) -> str:
    """从消息列表中提取最近一条用户消息文本。"""
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content
            if isinstance(content, str) and content.strip():
                return content.strip()
    return "No user messages found"


def read_user_preference(state: dict[str, Any], preference_name: str) -> dict[str, object]:
    """从 Agent state 中读取用户偏好字段。"""
    normalized_name = preference_name.strip()
    if not normalized_name:
        return {
            "status": "error",
            "error": {"code": "invalid_input", "message": "Preference name is required."},
        }

    preferences = state.get("user_preferences", {})
    if not isinstance(preferences, dict):
        return {
            "status": "error",
            "error": {"code": "invalid_input", "message": "User preferences must be a mapping."},
        }

    value = preferences.get(normalized_name)
    if value is None:
        return {
            "status": "error",
            "error": {"code": "not_found", "message": "Preference was not set."},
        }

    return {
        "status": "success",
        "data": {"preference_name": normalized_name, "preference_value": value},
    }


@tool
def get_last_user_message(runtime: ToolRuntime) -> str:
    """获取当前对话中最近一条用户消息文本。

    Use when:
    - 需要引用用户刚刚提出的要求，而模型上下文可能已被截断或摘要。
    - 当前对话 state 中仍保留完整 messages 历史。

    Do not use when:
    - 需要跨会话长期记忆；应改用 store 或持久化用户画像服务。
    - 用户消息已被 middleware 清洗或替换；应直接读取受控业务字段。

    Args:
        runtime: 由 LangChain 注入的运行时对象，不会出现在模型可见 schema 中。

    Returns:
        返回最近一条非空 `HumanMessage` 的文本；若不存在则返回固定英文提示。

    Side effects:
    - 无。本工具只读取当前 state，不修改消息或外部资源。

    Preconditions:
    - `runtime.state` 必须包含 `messages` 列表。

    Errors:
    - invalid_input: 不适用；缺失消息时返回固定提示文本，不抛异常。
    - not_found: 不适用；无用户消息时返回 `"No user messages found"`。
    - permission_denied: 不适用；本示例不实现权限系统。
    - external_service_error: 不适用；本示例不调用外部服务。

    Examples:
        get_last_user_message(runtime=runtime)

    Notes:
    - `runtime` 由框架注入，模型不会在 tool schema 中看到该参数。
    - 生产实现应限制读取范围，避免把敏感审计字段无边界暴露给模型。
    """
    messages = runtime.state.get("messages", [])
    return get_last_human_message_text(messages)


@tool
def get_user_preference(preference_name: str, runtime: ToolRuntime) -> dict[str, object]:
    """读取当前对话 state 中的用户偏好值。

    Use when:
    - 需要根据用户在当前会话中保存的显示语言、主题或其他短期偏好作答。
    - 偏好已经通过受控流程写入 `user_preferences` 字段。

    Do not use when:
    - 需要跨会话账户级设置；应读取 store 或用户配置服务。
    - 偏好名称不明确或可能触发高成本外部查询；应先澄清名称。

    Args:
        preference_name: 偏好字段名，例如 `display_language`。
        runtime: 由 LangChain 注入的运行时对象，提供当前 state。

    Returns:
        返回包含 `status` 的字典及其关键字段含义。
        成功时: {"status": "success", "data": {"preference_name": "...", "preference_value": "..."}}
        失败时: {"status": "error", "error": {"code": "...", "message": "..."}}

    Side effects:
    - 无。本工具只读取 state，不修改偏好或外部资源。

    Preconditions:
    - `runtime.state` 必须存在，且 `user_preferences` 为映射类型。

    Errors:
    - invalid_input: `preference_name` 为空，或 `user_preferences` 不是映射。
    - not_found: state 中不存在目标偏好。
    - permission_denied: 不适用；本示例不实现权限系统。
    - external_service_error: 不适用；本示例不调用外部服务。

    Examples:
        get_user_preference(preference_name="display_language", runtime=runtime)

    Notes:
    - state 表示当前对话短期记忆，不等于长期用户画像。
    - 需要更新偏好时应返回 `Command`，并在 update 中附带 `ToolMessage` 通知模型。
    """
    return read_user_preference(runtime.state, preference_name)


def build_demo_state() -> dict[str, Any]:
    """构造带 messages 与自定义偏好字段的演示 state。"""
    return {
        "messages": [
            HumanMessage(content="请根据我的语言偏好回答。", id="human_pref_question_001"),
        ],
        "user_preferences": {
            "display_language": "zh-CN",
            "theme": "light",
        },
    }


def main() -> None:
    demo_state = build_demo_state()
    print("最近用户消息：", get_last_human_message_text(demo_state["messages"]))
    print(
        "语言偏好：",
        read_user_preference(demo_state, "display_language"),
    )

    assert "runtime" not in get_user_preference.args
    assert "preference_name" in get_user_preference.args


if __name__ == "__main__":
    main()
