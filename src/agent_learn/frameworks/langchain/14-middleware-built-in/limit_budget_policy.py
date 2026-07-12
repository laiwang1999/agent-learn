"""演示如何为 Agent 推荐模型与工具调用预算上限。"""

from dataclasses import dataclass
from typing import Literal

ToolRiskLevel = Literal["read_only", "write_low", "write_high"]


@dataclass(frozen=True, slots=True)
class AgentWorkloadProfile:
    """描述 Agent  workload 的风险与规模特征。"""

    tool_count: int
    high_risk_tool_count: int
    expected_turns: int


@dataclass(frozen=True, slots=True)
class CallLimitRecommendation:
    """模型与工具调用上限建议。"""

    model_run_limit: int
    model_thread_limit: int
    tool_run_limit: int
    tool_thread_limit: int


def recommend_model_call_limit(profile: AgentWorkloadProfile) -> tuple[int, int]:
    """根据 workload 推荐 model run/thread 上限。"""
    base_run = 8
    if profile.high_risk_tool_count > 0:
        base_run = max(5, base_run - profile.high_risk_tool_count)
    if profile.tool_count > 10:
        base_run = max(4, base_run - 2)

    thread_limit = max(base_run * 2, profile.expected_turns + 4)
    return base_run, thread_limit


def recommend_tool_call_limit(
    profile: AgentWorkloadProfile,
    *,
    default_tool_risk: ToolRiskLevel = "read_only",
) -> tuple[int, int]:
    """根据工具风险推荐 tool run/thread 上限。"""
    if default_tool_risk == "write_high":
        return 2, 6
    if default_tool_risk == "write_low":
        return 5, 12
    base_run = 12
    if profile.tool_count > 8:
        base_run = 8
    return base_run, base_run * 2


def recommend_call_limits(profile: AgentWorkloadProfile) -> CallLimitRecommendation:
    """组合模型与工具调用预算建议。"""
    model_run, model_thread = recommend_model_call_limit(profile)
    tool_run, tool_thread = recommend_tool_call_limit(profile)
    return CallLimitRecommendation(
        model_run_limit=model_run,
        model_thread_limit=model_thread,
        tool_run_limit=tool_run,
        tool_thread_limit=tool_thread,
    )


def main() -> None:
    profile = AgentWorkloadProfile(
        tool_count=12,
        high_risk_tool_count=2,
        expected_turns=6,
    )
    limits = recommend_call_limits(profile)
    print("推荐上限：", limits)


if __name__ == "__main__":
    main()
