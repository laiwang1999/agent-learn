"""演示 `thread_id` 如何隔离短期记忆，以及 checkpointer 概念的本地等价实现。"""

from copy import deepcopy
from typing import Any


def build_thread_config(thread_id: str) -> dict[str, dict[str, str]]:
    """构造 LangChain Agent 调用时使用的 thread 配置。"""
    normalized_thread_id = thread_id.strip()
    if not normalized_thread_id:
        raise ValueError("Thread ID is required.")
    return {"configurable": {"thread_id": normalized_thread_id}}


class ThreadMemoryStore:
    """进程内 thread state 存储，用于离线演示 checkpointer 的隔离语义。

    生产环境应使用 Postgres 等持久化 checkpointer，而不是此类演示存储。
    """

    def __init__(self) -> None:
        self._states: dict[str, dict[str, Any]] = {}

    def save_state(self, thread_id: str, state: dict[str, Any]) -> None:
        """保存指定 thread 的完整 state 快照。"""
        normalized_thread_id = thread_id.strip()
        if not normalized_thread_id:
            raise ValueError("Thread ID is required.")
        # 深拷贝避免调用方后续修改影响已保存快照。
        self._states[normalized_thread_id] = deepcopy(state)

    def load_state(self, thread_id: str) -> dict[str, Any] | None:
        """读取指定 thread 的 state；不存在时返回 None。"""
        normalized_thread_id = thread_id.strip()
        if not normalized_thread_id:
            raise ValueError("Thread ID is required.")
        stored_state = self._states.get(normalized_thread_id)
        if stored_state is None:
            return None
        return deepcopy(stored_state)

    def append_messages(self, thread_id: str, new_messages: list[dict[str, str]]) -> dict[str, Any]:
        """向已有 thread 追加 messages，模拟同 thread 的第二次 invoke。"""
        current_state = self.load_state(thread_id) or {"messages": []}
        messages = list(current_state.get("messages", []))
        messages.extend(new_messages)
        updated_state = {**current_state, "messages": messages}
        self.save_state(thread_id, updated_state)
        return updated_state

    def list_thread_ids(self) -> list[str]:
        """列出当前存储中的所有 thread 标识。"""
        return sorted(self._states.keys())


def extract_display_name_from_messages(messages: list[dict[str, str]]) -> str | None:
    """从演示消息列表中提取用户自我介绍的名字。"""
    prefix = "my name is "
    for message in messages:
        if message.get("role") != "user":
            continue
        content = message.get("content", "").strip().lower()
        if prefix in content:
            return content.split(prefix, maxsplit=1)[1].strip().rstrip(".")
    return None


def demonstrate_thread_isolation() -> dict[str, object]:
    """演示同一信息只保存在对应 thread，不会泄漏到其他 thread。"""
    store = ThreadMemoryStore()

    # thread-1：用户先自我介绍，再询问名字。
    store.append_messages(
        "thread-1",
        [{"role": "user", "content": "Hi! My name is Bob."}],
    )
    store.append_messages(
        "thread-1",
        [{"role": "user", "content": "What's my name?"}],
    )

    # thread-2：新会话中没有前文，无法知道 Bob。
    store.append_messages(
        "thread-2",
        [{"role": "user", "content": "What's my name?"}],
    )

    thread_one_state = store.load_state("thread-1")
    thread_two_state = store.load_state("thread-2")
    assert thread_one_state is not None
    assert thread_two_state is not None

    return {
        "thread_one_name": extract_display_name_from_messages(thread_one_state["messages"]),
        "thread_two_name": extract_display_name_from_messages(thread_two_state["messages"]),
        "thread_one_message_count": len(thread_one_state["messages"]),
        "thread_two_message_count": len(thread_two_state["messages"]),
    }


def main() -> None:
    result = demonstrate_thread_isolation()
    print("thread-1 可回忆的名字：", result["thread_one_name"])
    print("thread-2 可回忆的名字：", result["thread_two_name"])
    print("thread-1 消息数：", result["thread_one_message_count"])
    print("thread-2 消息数：", result["thread_two_message_count"])
    print("thread 配置示例：", build_thread_config("learning-session-001"))


if __name__ == "__main__":
    main()
