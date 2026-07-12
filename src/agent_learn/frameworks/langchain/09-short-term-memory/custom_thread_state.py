"""演示自定义 AgentState 字段如何与 messages 共同构成短期记忆。"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CustomThreadState:
    """扩展默认 messages 之外的 thread 级结构化状态。"""

    messages: list[dict[str, str]] = field(default_factory=list)
    user_id: str = ""
    preferences: dict[str, str] = field(default_factory=dict)
    task_stage: str = "collecting_requirements"


def initialize_thread_state(
    messages: list[dict[str, str]],
    user_id: str,
    preferences: dict[str, str] | None = None,
    task_stage: str = "collecting_requirements",
) -> CustomThreadState:
    """构造带自定义字段的初始 thread state。"""
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        raise ValueError("User ID is required.")

    return CustomThreadState(
        messages=list(messages),
        user_id=normalized_user_id,
        preferences=dict(preferences or {}),
        task_stage=task_stage.strip() or "collecting_requirements",
    )


def merge_thread_state(existing: CustomThreadState, incoming: dict[str, Any]) -> CustomThreadState:
    """把新一轮 invoke 的增量更新合并进已有 thread state。"""
    merged_messages = list(existing.messages)
    incoming_messages = incoming.get("messages")
    if isinstance(incoming_messages, list):
        merged_messages.extend(incoming_messages)

    merged_preferences = dict(existing.preferences)
    incoming_preferences = incoming.get("preferences")
    if isinstance(incoming_preferences, dict):
        merged_preferences.update(
            {str(key): str(value) for key, value in incoming_preferences.items()}
        )

    merged_user_id = str(incoming.get("user_id", existing.user_id)).strip() or existing.user_id
    merged_task_stage = str(incoming.get("task_stage", existing.task_stage)).strip() or existing.task_stage

    return CustomThreadState(
        messages=merged_messages,
        user_id=merged_user_id,
        preferences=merged_preferences,
        task_stage=merged_task_stage,
    )


def read_task_stage(state: CustomThreadState) -> str:
    """读取当前 thread 的任务阶段。"""
    return state.task_stage


def update_task_stage(state: CustomThreadState, new_stage: str) -> CustomThreadState:
    """更新 thread 内任务阶段，模拟工具或 middleware 写入 state。"""
    normalized_stage = new_stage.strip()
    if not normalized_stage:
        raise ValueError("Task stage is required.")
    return CustomThreadState(
        messages=list(state.messages),
        user_id=state.user_id,
        preferences=dict(state.preferences),
        task_stage=normalized_stage,
    )


def state_to_checkpoint_payload(state: CustomThreadState) -> dict[str, Any]:
    """把自定义 state 序列化为可存入 checkpointer 的字典。"""
    return {
        "messages": list(state.messages),
        "user_id": state.user_id,
        "preferences": dict(state.preferences),
        "task_stage": state.task_stage,
    }


def main() -> None:
    initial_state = initialize_thread_state(
        messages=[{"role": "user", "content": "我想开始学习 Agent。"}],
        user_id="learner-001",
        preferences={"display_language": "zh-CN", "theme": "light"},
    )
    merged_state = merge_thread_state(
        initial_state,
        {
            "messages": [{"role": "user", "content": "请继续推荐下一章。"}],
            "task_stage": "recommending_next_chapter",
        },
    )
    print("初始 task_stage：", read_task_stage(initial_state))
    print("合并后 task_stage：", read_task_stage(merged_state))
    print("合并后消息数：", len(merged_state.messages))
    print("checkpoint 载荷：", state_to_checkpoint_payload(merged_state))


if __name__ == "__main__":
    main()
