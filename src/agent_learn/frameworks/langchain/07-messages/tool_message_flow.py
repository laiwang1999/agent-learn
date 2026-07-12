"""演示 client-side tool call 如何通过 `ToolMessage` 回写到消息历史。"""

import json
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage


lesson_inventory = {
    "course-001": {"course_title": "LangChain 消息实践", "available_quantity": 8},
    "course-002": {"course_title": "LangGraph 状态实践", "available_quantity": 0},
}


def create_inventory_tool_call(product_id: str) -> AIMessage:
    """构造模型请求查询课程库存的 `AIMessage`。"""
    # tool call ID 是模型请求和工具结果之间的关联键，不能由调用方在回写时随意替换。
    normalized_product_id = product_id.strip()
    if not normalized_product_id:
        raise ValueError("Product ID cannot be empty.")

    return AIMessage(
        content="我将先查询课程库存，再给出中文答复。", 
        id="assistant_tool_request_001",
        tool_calls=[
            {
                "name": "lookup_lesson_inventory",
                "args": {"product_id": normalized_product_id},
                "id": "call_course_inventory_001",
            }
        ],
    )


def lookup_lesson_inventory(product_id: str) -> dict[str, object]:
    """返回本地演示课程库存，模拟确定性的工具执行结果。"""
    # 真实项目会在受权限控制的服务适配器中读取库存；本章保留为纯函数以便离线验证消息契约。
    normalized_product_id = product_id.strip()
    if not normalized_product_id:
        return {
            "status": "error",
            "error": {"code": "invalid_input", "message": "Product ID is required."},
        }

    product = lesson_inventory.get(normalized_product_id)
    if product is None:
        return {
            "status": "error",
            "error": {"code": "not_found", "message": "Product was not found."},
        }

    return {
        "status": "success",
        "data": {"product_id": normalized_product_id, **product},
    }


def create_tool_result_message(tool_call: dict[str, Any], result: dict[str, object]) -> ToolMessage:
    """把工具结果回写为与模型请求精确关联的 `ToolMessage`。"""
    # 先校验模型请求的最小字段；缺少 ID 时无法安全地把结果归属到某次工具调用。
    tool_call_id = tool_call.get("id")
    tool_name = tool_call.get("name")
    if not isinstance(tool_call_id, str) or not tool_call_id:
        raise ValueError("Tool call ID is required.")
    if not isinstance(tool_name, str) or not tool_name:
        raise ValueError("Tool name is required.")

    # content 会进入下一次模型上下文，因此只传递紧凑、可序列化的工具结果。
    # artifact 留给应用层保存原始返回值，不会作为此 ToolMessage 的模型文本内容。
    return ToolMessage(
        content=json.dumps(result, ensure_ascii=False),
        tool_call_id=tool_call_id,
        name=tool_name,
        artifact={"tool_call_id": tool_call_id, "raw_result": result},
    )


def has_matching_tool_result(ai_message: AIMessage, tool_message: ToolMessage) -> bool:
    """验证工具结果是否回应了给定 AI 消息中的任一工具调用。"""
    # 多个工具调用可能同时存在，必须按 ID 匹配，不能依赖消息或数组的排列位置。
    requested_call_ids = {tool_call["id"] for tool_call in ai_message.tool_calls}
    return tool_message.tool_call_id in requested_call_ids


def build_tool_message_history(product_id: str) -> list[BaseMessage]:
    """构造从用户请求到工具结果再到中文答复的完整消息序列。"""
    human_message = HumanMessage(
        content=f"请查询 {product_id} 的可用库存。", id="user_inventory_question_001"
    )
    tool_request = create_inventory_tool_call(product_id)
    tool_call = tool_request.tool_calls[0]

    # 工具执行与模型推理分离：Python 负责确定性查询，模型只根据回写结果组织最终语言答复。
    tool_result = lookup_lesson_inventory(tool_call["args"]["product_id"])
    tool_message = create_tool_result_message(tool_call, tool_result)

    if not has_matching_tool_result(tool_request, tool_message):
        raise ValueError("Tool result does not match the requested tool call.")

    final_answer = AIMessage(
        content="课程 course-001 当前可用数量为 8。",
        id="assistant_inventory_answer_001",
    )
    return [human_message, tool_request, tool_message, final_answer]


def main() -> None:
    messages = build_tool_message_history("course-001")
    for message in messages:
        print(f"{message.type}: {message.content}")

    tool_message = messages[2]
    assert isinstance(tool_message, ToolMessage)
    print(f"应用层 artifact：{tool_message.artifact}")


if __name__ == "__main__":
    main()
