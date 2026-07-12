from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
from langchain_core.messages import ToolMessage


MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "agent_learn"
    / "frameworks"
    / "langchain"
    / "07-messages"
    / "tool_message_flow.py"
)


def load_tool_message_flow_module():
    """加载编号目录中的章节模块，避免目录连字符影响教学目录命名。"""
    spec = spec_from_file_location("tool_message_flow", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tool_message_uses_requested_tool_call_id() -> None:
    module = load_tool_message_flow_module()
    request = module.create_inventory_tool_call("course-001")
    result = module.lookup_lesson_inventory("course-001")

    tool_message = module.create_tool_result_message(request.tool_calls[0], result)

    assert tool_message.tool_call_id == "call_course_inventory_001"
    assert tool_message.name == "lookup_lesson_inventory"
    assert tool_message.artifact["raw_result"] == result
    assert module.has_matching_tool_result(request, tool_message)


def test_tool_message_rejects_missing_tool_call_id() -> None:
    module = load_tool_message_flow_module()

    with pytest.raises(ValueError, match="Tool call ID is required"):
        module.create_tool_result_message(
            {"name": "lookup_lesson_inventory"},
            {"status": "success", "data": {}},
        )


def test_tool_message_does_not_match_another_call_id() -> None:
    module = load_tool_message_flow_module()
    request = module.create_inventory_tool_call("course-001")
    unrelated_result = ToolMessage(
        content="{}",
        tool_call_id="call_other_tool",
        name="lookup_lesson_inventory",
    )

    assert not module.has_matching_tool_result(request, unrelated_result)
