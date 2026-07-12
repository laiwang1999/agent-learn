from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


FRAMEWORK_ROOT = (
    Path(__file__).parents[1]
    / "src"
    / "agent_learn"
    / "frameworks"
    / "langchain"
    / "14-middleware-built-in"
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


def test_recommend_for_runaway_cost_problem() -> None:
    module = load_chapter_module("prebuilt_middleware_catalog.py")
    recommendation = module.recommend_for_problem("runaway_cost")

    assert recommendation is not None
    assert "ModelCallLimitMiddleware" in recommendation.middleware_names


def test_list_all_middleware_names_is_unique() -> None:
    module = load_chapter_module("prebuilt_middleware_catalog.py")
    names = module.list_all_middleware_names()

    assert len(names) == len(set(names))
    assert "SummarizationMiddleware" in names


def test_recommend_model_call_limit_lowers_for_high_risk_tools() -> None:
    module = load_chapter_module("limit_budget_policy.py")
    safe_profile = module.AgentWorkloadProfile(
        tool_count=6,
        high_risk_tool_count=0,
        expected_turns=4,
    )
    risky_profile = module.AgentWorkloadProfile(
        tool_count=6,
        high_risk_tool_count=3,
        expected_turns=4,
    )

    safe_run, _ = module.recommend_model_call_limit(safe_profile)
    risky_run, _ = module.recommend_model_call_limit(risky_profile)

    assert risky_run < safe_run


def test_recommend_tool_call_limit_for_write_high() -> None:
    module = load_chapter_module("limit_budget_policy.py")

    tool_run, tool_thread = module.recommend_tool_call_limit(
        module.AgentWorkloadProfile(tool_count=5, high_risk_tool_count=1, expected_turns=3),
        default_tool_risk="write_high",
    )

    assert tool_run == 2
    assert tool_thread == 6


def test_select_pii_strategy_for_regulated_data() -> None:
    module = load_chapter_module("pii_strategy_selector.py")

    strategy = module.select_pii_strategy(
        sensitivity="regulated",
        needs_referential_identity=False,
        is_streaming_output=True,
    )

    assert strategy == "block"


def test_build_pii_middleware_config_enables_output_redaction_for_streaming() -> None:
    module = load_chapter_module("pii_strategy_selector.py")

    config = module.build_pii_middleware_config(
        "email",
        sensitivity="internal",
        is_streaming_output=True,
    )

    assert config["apply_to_output"] is True
    assert config["strategy"] == "redact"
