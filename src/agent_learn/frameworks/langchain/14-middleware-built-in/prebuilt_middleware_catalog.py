"""按工程职责索引 Prebuilt Middleware，用于离线选型。"""

from dataclasses import dataclass
from typing import Literal

ProblemCategory = Literal[
    "long_context",
    "high_risk_tools",
    "runaway_cost",
    "transient_failures",
    "sensitive_data",
    "too_many_tools",
    "dev_without_api",
    "filesystem_work",
]


@dataclass(frozen=True, slots=True)
class MiddlewareRecommendation:
    """针对一类问题的 middleware 推荐。"""

    problem: ProblemCategory
    middleware_names: tuple[str, ...]
    notes: str


PREBUILT_CATALOG: tuple[MiddlewareRecommendation, ...] = (
    MiddlewareRecommendation(
        problem="long_context",
        middleware_names=("SummarizationMiddleware", "ContextEditingMiddleware"),
        notes="摘要历史或清理旧工具结果，控制 context window。",
    ),
    MiddlewareRecommendation(
        problem="high_risk_tools",
        middleware_names=("HumanInTheLoopMiddleware",),
        notes="需要 checkpointer；interrupt_on 的 key 必须与 tool.name 一致。",
    ),
    MiddlewareRecommendation(
        problem="runaway_cost",
        middleware_names=("ModelCallLimitMiddleware", "ToolCallLimitMiddleware"),
        notes="限制单次 run 与 thread 累计调用次数。",
    ),
    MiddlewareRecommendation(
        problem="transient_failures",
        middleware_names=(
            "ToolRetryMiddleware",
            "ModelRetryMiddleware",
            "ModelFallbackMiddleware",
        ),
        notes="仅对可恢复、幂等或只读失败启用 retry。",
    ),
    MiddlewareRecommendation(
        problem="sensitive_data",
        middleware_names=("PIIMiddleware",),
        notes="streaming 场景应对 wire output 脱敏（apply_to_output）。",
    ),
    MiddlewareRecommendation(
        problem="too_many_tools",
        middleware_names=(
            "LLMToolSelectorMiddleware",
            "ProviderToolSearchMiddleware",
        ),
        notes="减少进入主模型上下文的 tool schema 体积。",
    ),
    MiddlewareRecommendation(
        problem="dev_without_api",
        middleware_names=("LLMToolEmulator",),
        notes="加速开发，但不能替代真实 E2E 测试。",
    ),
    MiddlewareRecommendation(
        problem="filesystem_work",
        middleware_names=(
            "FilesystemFileSearchMiddleware",
            "FilesystemMiddleware",
            "ShellToolMiddleware",
        ),
        notes="Shell 与写文件属于高风险能力，需隔离与审批。",
    ),
)


def recommend_for_problem(problem: ProblemCategory) -> MiddlewareRecommendation | None:
    """根据问题类别返回推荐条目。"""
    for item in PREBUILT_CATALOG:
        if item.problem == problem:
            return item
    return None


def list_all_middleware_names() -> list[str]:
    """列出目录中提到的全部 middleware 名称（去重）。"""
    names: list[str] = []
    for item in PREBUILT_CATALOG:
        for name in item.middleware_names:
            if name not in names:
                names.append(name)
    return names


def main() -> None:
    recommendation = recommend_for_problem("runaway_cost")
    assert recommendation is not None
    print("问题：", recommendation.problem)
    print("推荐：", recommendation.middleware_names)
    print("全部内置名称：", list_all_middleware_names())


if __name__ == "__main__":
    main()
