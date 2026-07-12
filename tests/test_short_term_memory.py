from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


FRAMEWORK_ROOT = (
    Path(__file__).parents[1]
    / "src"
    / "agent_learn"
    / "frameworks"
    / "langchain"
    / "09-short-term-memory"
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


def test_thread_isolation_preserves_names_per_thread() -> None:
    module = load_chapter_module("thread_memory_store.py")
    result = module.demonstrate_thread_isolation()

    assert result["thread_one_name"] == "bob"
    assert result["thread_two_name"] is None
    assert result["thread_one_message_count"] == 2
    assert result["thread_two_message_count"] == 1


def test_build_thread_config_requires_non_empty_id() -> None:
    module = load_chapter_module("thread_memory_store.py")

    config = module.build_thread_config("session-001")

    assert config == {"configurable": {"thread_id": "session-001"}}


def test_custom_thread_state_merge_updates_stage_and_messages() -> None:
    module = load_chapter_module("custom_thread_state.py")
    initial_state = module.initialize_thread_state(
        messages=[{"role": "user", "content": "开始学习"}],
        user_id="learner-001",
        preferences={"display_language": "zh-CN"},
    )
    merged_state = module.merge_thread_state(
        initial_state,
        {
            "messages": [{"role": "user", "content": "下一章是什么？"}],
            "task_stage": "recommending_next_chapter",
            "preferences": {"theme": "dark"},
        },
    )

    assert len(merged_state.messages) == 2
    assert merged_state.task_stage == "recommending_next_chapter"
    assert merged_state.preferences["display_language"] == "zh-CN"
    assert merged_state.preferences["theme"] == "dark"


def test_trim_messages_keeps_first_and_recent_messages() -> None:
    module = load_chapter_module("message_trim_strategy.py")
    history = module.build_long_demo_history()

    trimmed = module.trim_messages_for_model(history, keep_recent_count=3)

    assert trimmed[0].type == "system"
    assert len(trimmed) < len(history)
    assert trimmed[-1].type == "ai"


def test_trim_by_token_budget_reduces_estimated_tokens() -> None:
    module = load_chapter_module("message_trim_strategy.py")
    history = module.build_long_demo_history()

    trimmed = module.trim_messages_by_token_budget(history, max_tokens=20, keep_recent_count=2)

    assert module.estimate_history_tokens(trimmed) <= module.estimate_history_tokens(history)


def test_validate_message_history_accepts_complete_tool_loop() -> None:
    module = load_chapter_module("message_history_validator.py")
    history = module.build_valid_tool_history()

    result = module.validate_message_history(history)

    assert result.is_valid is True


def test_validate_message_history_rejects_missing_tool_result() -> None:
    module = load_chapter_module("message_history_validator.py")
    history = module.build_invalid_tool_history_missing_result()

    result = module.validate_message_history(history)

    assert result.is_valid is False
    assert result.error_code == "orphan_tool_calls"


def test_delete_tool_messages_breaks_history_validity() -> None:
    module = load_chapter_module("message_history_validator.py")
    history = module.build_valid_tool_history()

    deleted_history = module.delete_messages_by_roles(history, roles_to_delete={"tool"})
    result = module.validate_message_history(deleted_history)

    assert result.is_valid is False
    assert result.error_code == "orphan_tool_calls"
