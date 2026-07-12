from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


FRAMEWORK_ROOT = (
    Path(__file__).parents[1]
    / "src"
    / "agent_learn"
    / "frameworks"
    / "langchain"
    / "13-middleware-overview"
)


def load_chapter_module(filename: str):
    """加载编号目录中的章节模块，避免目录连字符影响教学目录命名。"""
    module_path = FRAMEWORK_ROOT / filename
    spec = spec_from_file_location(filename.removesuffix(".py"), module_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sort_middleware_puts_pii_before_logging() -> None:
    module = load_chapter_module("middleware_ordering.py")
    stack = module.sort_middleware_by_priority(module.build_recommended_learning_stack())

    assert stack[0].concern == "pii_redaction"
    assert module.validate_logging_after_redaction(stack) is True


def test_should_interrupt_tool_matches_exact_tool_name() -> None:
    module = load_chapter_module("hitl_tool_matching.py")
    interrupt_on = {"send_email": True}

    assert module.should_interrupt_tool("send_email", interrupt_on) is True
    assert module.should_interrupt_tool("send_notification", interrupt_on) is False


def test_find_unprotected_high_risk_tools() -> None:
    module = load_chapter_module("hitl_tool_matching.py")
    tools = [
        module.ToolDescriptor(name="send_email", is_high_risk=True),
        module.ToolDescriptor(name="read_inbox", is_high_risk=False),
    ]
    interrupt_on = {"read_inbox": True}

    unprotected = module.find_unprotected_high_risk_tools(tools, interrupt_on)

    assert unprotected == ["send_email"]


def test_build_role_aware_system_prompt_for_viewer() -> None:
    module = load_chapter_module("dynamic_prompt_builder.py")
    prompt = module.build_role_aware_system_prompt(
        module.RuntimeContext(
            user_role="viewer",
            tenant_name="learning-team",
            can_use_tools=True,
        )
    )

    assert "只读助手" in prompt
    assert "read_" in prompt


def test_build_role_aware_system_prompt_for_guest_without_tools() -> None:
    module = load_chapter_module("dynamic_prompt_builder.py")
    prompt = module.build_role_aware_system_prompt(
        module.RuntimeContext(
            user_role="guest",
            tenant_name="learning-team",
            can_use_tools=False,
        )
    )

    assert "没有工具调用权限" in prompt


def test_build_interrupt_policy_only_includes_high_risk_tools() -> None:
    module = load_chapter_module("hitl_tool_matching.py")
    tools = [
        module.ToolDescriptor(name="read_inbox"),
        module.ToolDescriptor(name="send_email", is_high_risk=True),
    ]

    policy = module.build_interrupt_policy(tools)

    assert policy == {"send_email": True}
