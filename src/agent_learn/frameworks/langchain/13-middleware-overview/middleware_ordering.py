"""演示 middleware concern 的优先级排序与组合顺序原则。"""

from dataclasses import dataclass
from typing import Literal

MiddlewareConcern = Literal[
    "pii_redaction",
    "permission_guard",
    "tool_filter",
    "dynamic_prompt",
    "summarization",
    "logging",
    "retry",
    "human_in_the_loop",
]


DEFAULT_PRIORITY: dict[MiddlewareConcern, int] = {
    "pii_redaction": 10,
    "permission_guard": 20,
    "tool_filter": 30,
    "human_in_the_loop": 40,
    "dynamic_prompt": 50,
    "summarization": 60,
    "retry": 70,
    "logging": 80,
}


@dataclass(frozen=True, slots=True)
class MiddlewareSpec:
    """描述一个 middleware 的职责与优先级。"""

    name: str
    concern: MiddlewareConcern


def sort_middleware_by_priority(middlewares: list[MiddlewareSpec]) -> list[MiddlewareSpec]:
    """按 concern 优先级排序，数值越小越靠前执行。"""
    return sorted(middlewares, key=lambda item: DEFAULT_PRIORITY[item.concern])


def validate_logging_after_redaction(sorted_middlewares: list[MiddlewareSpec]) -> bool:
    """确认 PII 脱敏 middleware 排在 logging 之前。"""
    concern_positions = {
        item.concern: index for index, item in enumerate(sorted_middlewares)
    }
    if "pii_redaction" not in concern_positions or "logging" not in concern_positions:
        return True
    return concern_positions["pii_redaction"] < concern_positions["logging"]


def build_recommended_learning_stack() -> list[MiddlewareSpec]:
    """构造学习场景推荐的 middleware 组合示例。"""
    return [
        MiddlewareSpec(name="pii_guard", concern="pii_redaction"),
        MiddlewareSpec(name="permission_guard", concern="permission_guard"),
        MiddlewareSpec(name="tool_filter", concern="tool_filter"),
        MiddlewareSpec(name="hitl", concern="human_in_the_loop"),
        MiddlewareSpec(name="dynamic_prompt", concern="dynamic_prompt"),
        MiddlewareSpec(name="summarization", concern="summarization"),
        MiddlewareSpec(name="retry", concern="retry"),
        MiddlewareSpec(name="logging", concern="logging"),
    ]


def main() -> None:
    stack = sort_middleware_by_priority(build_recommended_learning_stack())
    print("推荐执行顺序：", [item.name for item in stack])
    print("脱敏早于日志：", validate_logging_after_redaction(stack))


if __name__ == "__main__":
    main()
