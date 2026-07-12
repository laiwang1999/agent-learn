"""演示 trim 或 delete 之后如何校验 message history 的合法性。"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """消息历史校验结果。"""

    is_valid: bool
    error_code: str | None = None
    error_message: str | None = None


def _extract_tool_call_ids(tool_calls: Any) -> set[str]:
    """从 AIMessage 的 tool_calls 中提取 ID 集合。"""
    if not isinstance(tool_calls, list):
        return set()

    call_ids: set[str] = set()
    for tool_call in tool_calls:
        if not isinstance(tool_call, dict):
            continue
        call_id = tool_call.get("id")
        if isinstance(call_id, str) and call_id:
            call_ids.add(call_id)
    return call_ids


def validate_message_history(messages: list[dict[str, Any]]) -> ValidationResult:
    """检查演示消息历史是否满足最小合法性约束。"""
    if not messages:
        return ValidationResult(
            is_valid=False,
            error_code="empty_history",
            error_message="Message history cannot be empty.",
        )

    first_role = messages[0].get("role")
    if first_role not in {"system", "user"}:
        return ValidationResult(
            is_valid=False,
            error_code="invalid_start_role",
            error_message="History should start with a system or user message.",
        )

    requested_tool_call_ids: set[str] = set()
    answered_tool_call_ids: set[str] = set()

    for message in messages:
        role = message.get("role")
        if role == "assistant":
            requested_tool_call_ids |= _extract_tool_call_ids(message.get("tool_calls"))
        if role == "tool":
            tool_call_id = message.get("tool_call_id")
            if isinstance(tool_call_id, str) and tool_call_id:
                answered_tool_call_ids.add(tool_call_id)

    orphan_tool_calls = requested_tool_call_ids - answered_tool_call_ids
    if orphan_tool_calls:
        return ValidationResult(
            is_valid=False,
            error_code="orphan_tool_calls",
            error_message="AIMessage tool_calls must have matching tool results.",
        )

    orphan_tool_results = answered_tool_call_ids - requested_tool_call_ids
    if orphan_tool_results:
        return ValidationResult(
            is_valid=False,
            error_code="orphan_tool_results",
            error_message="Tool results must reference an existing tool call.",
        )

    return ValidationResult(is_valid=True)


def delete_messages_by_roles(
    messages: list[dict[str, Any]],
    *,
    roles_to_delete: set[str],
) -> list[dict[str, Any]]:
    """按角色删除消息，用于演示 delete 策略及其风险。"""
    return [message for message in messages if message.get("role") not in roles_to_delete]


def build_valid_tool_history() -> list[dict[str, Any]]:
    """构造包含完整 tool call 闭环的合法历史。"""
    return [
        {"role": "system", "content": "你是库存助手。"},
        {"role": "user", "content": "查询 course-001 库存。"},
        {
            "role": "assistant",
            "content": "我先查询库存。",
            "tool_calls": [
                {
                    "name": "lookup_lesson_inventory",
                    "args": {"product_id": "course-001"},
                    "id": "call_course_inventory_001",
                }
            ],
        },
        {
            "role": "tool",
            "name": "lookup_lesson_inventory",
            "tool_call_id": "call_course_inventory_001",
            "content": '{"status": "success", "data": {"available_quantity": 8}}',
        },
        {"role": "assistant", "content": "course-001 当前可用数量为 8。"},
    ]


def build_invalid_tool_history_missing_result() -> list[dict[str, Any]]:
    """构造缺少 ToolMessage 的非法历史。"""
    history = build_valid_tool_history()
    return [message for message in history if message.get("role") != "tool"]


def main() -> None:
    valid_history = build_valid_tool_history()
    invalid_history = build_invalid_tool_history_missing_result()

    print("合法历史：", validate_message_history(valid_history))
    print("非法历史：", validate_message_history(invalid_history))

    deleted_history = delete_messages_by_roles(valid_history, roles_to_delete={"tool"})
    print("删除 tool 后：", validate_message_history(deleted_history))


if __name__ == "__main__":
    main()
