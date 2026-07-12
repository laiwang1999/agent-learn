"""演示 short-term memory 过长时的 trim 策略（模型调用前的上下文裁剪）。"""

from typing import Any, Protocol


class MessageLike(Protocol):
    """trim 逻辑所需的最小消息接口。"""

    @property
    def type(self) -> str: ...

    @property
    def content(self) -> str: ...


def estimate_message_tokens(message: MessageLike) -> int:
    """用字符数近似估算单条消息的 token 开销。

    教学示例采用 `len(content) // 4` 的粗估；生产应使用真实 tokenizer。
    """
    content = message.content
    if not isinstance(content, str):
        return 0
    return max(1, len(content) // 4)


def estimate_history_tokens(messages: list[MessageLike]) -> int:
    """估算整段 message history 的近似 token 总数。"""
    return sum(estimate_message_tokens(message) for message in messages)


def trim_messages_for_model(
    messages: list[MessageLike],
    *,
    keep_recent_count: int = 3,
) -> list[MessageLike]:
    """保留首条消息与最近 N 条消息，模拟 `@before_model` trim middleware 的核心行为。

    首条消息通常承载 system instruction 或初始上下文；最近几条保留当前对话连贯性。
    """
    if keep_recent_count <= 0:
        raise ValueError("keep_recent_count must be positive.")
    if len(messages) <= keep_recent_count + 1:
        return list(messages)

    first_message = messages[0]
    # 与官方示例一致：根据总条数奇偶性决定保留最近 3 或 4 条。
    recent_slice_size = keep_recent_count if len(messages) % 2 == 0 else keep_recent_count + 1
    recent_messages = messages[-recent_slice_size:]
    return [first_message, *recent_messages]


def trim_messages_by_token_budget(
    messages: list[MessageLike],
    *,
    max_tokens: int,
    keep_recent_count: int = 2,
) -> list[MessageLike]:
    """在 token 预算内优先保留首条消息和最近消息。"""
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive.")
    if not messages:
        return []

    first_message = messages[0]
    recent_messages = list(messages[-keep_recent_count:]) if keep_recent_count > 0 else []
    candidate_messages = [first_message, *recent_messages]

    while candidate_messages and estimate_history_tokens(candidate_messages) > max_tokens:
        if len(candidate_messages) <= 1:
            break
        # 从最早的可丢弃消息开始缩减，但始终保留首条消息。
        candidate_messages.pop(1)

    return candidate_messages


def trim_state_update(
    messages: list[MessageLike],
    *,
    keep_recent_count: int = 3,
) -> dict[str, Any]:
    """返回 trim 后的消息列表，供 middleware 或教学断言使用。"""
    trimmed_messages = trim_messages_for_model(messages, keep_recent_count=keep_recent_count)
    return {
        "original_count": len(messages),
        "trimmed_count": len(trimmed_messages),
        "messages": trimmed_messages,
        "estimated_tokens_before": estimate_history_tokens(messages),
        "estimated_tokens_after": estimate_history_tokens(trimmed_messages),
    }


class DemoMessage:
    """用于离线 trim 演示的轻量消息对象。"""

    def __init__(self, message_type: str, content: str) -> None:
        self.type = message_type
        self.content = content


def build_long_demo_history() -> list[DemoMessage]:
    """构造一段足够长的演示对话历史。"""
    history = [DemoMessage("system", "你是一名学习助手。最终答复必须使用中文。")]
    for index in range(1, 8):
        history.append(DemoMessage("human", f"这是第 {index} 轮用户问题。"))
        history.append(DemoMessage("ai", f"这是第 {index} 轮助手答复。"))
    return history


def main() -> None:
    history = build_long_demo_history()
    update = trim_state_update(history, keep_recent_count=3)
    print("裁剪前消息数：", update["original_count"])
    print("裁剪后消息数：", update["trimmed_count"])
    print("裁剪前近似 tokens：", update["estimated_tokens_before"])
    print("裁剪后近似 tokens：", update["estimated_tokens_after"])
    print("保留的消息类型序列：", [message.type for message in update["messages"]])


if __name__ == "__main__":
    main()
