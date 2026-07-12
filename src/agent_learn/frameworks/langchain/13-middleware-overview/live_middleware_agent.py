"""演示 `@dynamic_prompt` 与 `@wrap_tool_call` 组合的真实 Agent middleware。"""

from collections.abc import Callable
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, dynamic_prompt, wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools import tool
from langchain.tools.tool_node import ToolCallRequest

from agent_learn.frameworks.langchain.chat_model_factory import create_chat_model


def _load_dynamic_prompt_builder_module():
    """从同目录加载 prompt 构建逻辑，避免连字符目录无法作为常规包导入。"""
    module_path = Path(__file__).with_name("dynamic_prompt_builder.py")
    spec = spec_from_file_location("dynamic_prompt_builder", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_prompt_builder = _load_dynamic_prompt_builder_module()
RuntimeContext = _prompt_builder.RuntimeContext
build_role_aware_system_prompt = _prompt_builder.build_role_aware_system_prompt


lesson_notes = {
    "course-001": {"course_title": "LangChain Middleware 实践", "lesson_count": 9},
}


@tool
def read_lesson_outline(course_id: str) -> dict[str, object]:
    """读取指定课程的大纲信息。

    Use when:
    - 用户询问具有明确课程编号的目录或章节信息。
    - 需要返回可验证的结构化课程事实。

    Do not use when:
    - 课程编号不明确，或请求修改课程内容；应先补充信息或转入审批流程。

    Args:
        course_id: 课程编号，例如 `course-001`。必须是非空文本。

    Returns:
        成功时: {"status": "success", "data": {"course_id": "...", "course_title": "...", "lesson_count": 0}}
        失败时: {"status": "error", "error": {"code": "...", "message": "..."}}

    Side effects:
    - 无。本工具只读取进程内演示数据。

    Preconditions:
    - `course_id` 必须是非空文本。

    Errors:
    - invalid_input: `course_id` 为空。
    - not_found: 演示数据中不存在目标课程。
    - permission_denied: 不适用；权限由 middleware 与 context 控制。
    - external_service_error: 不适用。

    Examples:
        read_lesson_outline(course_id="course-001")

    Notes:
    - 工具名以 `read_` 前缀标识只读能力，便于与 dynamic prompt 策略配合。
    """
    normalized_course_id = course_id.strip()
    if not normalized_course_id:
        return {
            "status": "error",
            "error": {"code": "invalid_input", "message": "Course ID is required."},
        }

    course = lesson_notes.get(normalized_course_id)
    if course is None:
        return {
            "status": "error",
            "error": {"code": "not_found", "message": "Course was not found."},
        }

    return {
        "status": "success",
        "data": {"course_id": normalized_course_id, **course},
    }


@dynamic_prompt
def build_learning_prompt(request: ModelRequest[RuntimeContext]) -> str:
    """根据 runtime context 动态生成 system prompt。"""
    context = request.runtime.context
    if context is None:
        return "你是学习助手。当前缺少可信运行时上下文，不得调用工具。最终答复必须使用中文。"
    return build_role_aware_system_prompt(context)


@wrap_tool_call
def convert_tool_errors_to_messages(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage],
) -> ToolMessage:
    """把工具异常转换为模型可恢复的 ToolMessage。"""
    try:
        return handler(request)
    except Exception as error:
        return ToolMessage(
            content=(
                "Tool error: Please check your input and try again. "
                f"({error})"
            ),
            tool_call_id=request.tool_call["id"],
        )


def create_learning_middleware_agent():
    """创建组合 dynamic prompt 与 tool error middleware 的学习 Agent。"""
    return create_agent(
        model=create_chat_model(),
        tools=[read_lesson_outline],
        context_schema=RuntimeContext,
        middleware=[build_learning_prompt, convert_tool_errors_to_messages],
        name="learning_middleware_agent",
    )


def main() -> None:
    agent = create_learning_middleware_agent()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "请介绍 course-001 的课程大纲。"}]},
        context=RuntimeContext(
            user_role="viewer",
            tenant_name="learning-team",
            can_use_tools=True,
        ),
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
