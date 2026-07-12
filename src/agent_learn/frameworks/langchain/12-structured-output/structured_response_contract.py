"""演示为何应用应读取 `structured_response`，而不是解析最后一条自然语言。"""

from typing import Any


def extract_structured_response(final_state: dict[str, Any]) -> object | None:
    """从 Agent final state 中读取校验后的结构化结果。"""
    return final_state.get("structured_response")


def extract_last_message_text(final_state: dict[str, Any]) -> str | None:
    """读取最后一条 message 的文本内容，仅用于展示或调试。"""
    messages = final_state.get("messages")
    if not isinstance(messages, list) or not messages:
        return None
    last_message = messages[-1]
    content = getattr(last_message, "content", None)
    if content is None and isinstance(last_message, dict):
        content = last_message.get("content")
    return content if isinstance(content, str) else None


def should_prefer_structured_response(final_state: dict[str, Any]) -> bool:
    """当 `structured_response` 存在时，应用应优先消费它。"""
    structured = extract_structured_response(final_state)
    return structured is not None


def build_demo_final_state_with_structured_response() -> dict[str, Any]:
    """构造包含 `structured_response` 的演示 final state。"""
    return {
        "messages": [
            {"role": "user", "content": "张三，zhangsan@example.com"},
            {
                "role": "assistant",
                "content": "已提取联系人信息：张三，zhangsan@example.com。",
            },
        ],
        "structured_response": {
            "name": "张三",
            "email": "zhangsan@example.com",
            "phone": None,
        },
    }


def build_demo_final_state_without_structured_response() -> dict[str, Any]:
    """构造只有自然语言回答、没有结构化字段的演示 state。"""
    return {
        "messages": [
            {"role": "user", "content": "张三，zhangsan@example.com"},
            {
                "role": "assistant",
                "content": "联系人可能是张三，邮箱可能是 zhangsan@example.com。",
            },
        ],
    }


def main() -> None:
    with_structured = build_demo_final_state_with_structured_response()
    without_structured = build_demo_final_state_without_structured_response()

    print("应优先 structured_response：", should_prefer_structured_response(with_structured))
    print("structured_response：", extract_structured_response(with_structured))
    print("最后一条文本：", extract_last_message_text(without_structured))


if __name__ == "__main__":
    main()
