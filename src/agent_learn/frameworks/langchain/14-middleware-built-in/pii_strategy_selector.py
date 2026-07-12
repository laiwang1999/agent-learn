"""演示 PIIMiddleware 策略选型：block、redact、mask、hash。"""

from typing import Literal

PIIStrategy = Literal["block", "redact", "mask", "hash"]
DataSensitivity = Literal["public", "internal", "restricted", "regulated"]


def select_pii_strategy(
    *,
    sensitivity: DataSensitivity,
    needs_referential_identity: bool,
    is_streaming_output: bool,
) -> PIIStrategy:
    """根据数据敏感度与是否需保留关联性选择 PII 策略。

    - regulated：严格场景优先 block
    - 需要同一实体可关联但不暴露原文：hash
    - 需要局部识别（如卡号尾号）：mask
    - 一般日志/对话脱敏：redact

    streaming 场景仍应配合 apply_to_output；本函数只负责策略选择。
    """
    if sensitivity == "regulated":
        return "block"
    if needs_referential_identity:
        return "hash"
    if sensitivity == "restricted":
        return "mask"
    if is_streaming_output:
        return "redact"
    return "redact"


def build_pii_middleware_config(
    pii_type: str,
  *,
  sensitivity: DataSensitivity,
  needs_referential_identity: bool = False,
  is_streaming_output: bool = False,
) -> dict[str, object]:
    """构造 PIIMiddleware 初始化参数的演示配置。"""
    strategy = select_pii_strategy(
        sensitivity=sensitivity,
        needs_referential_identity=needs_referential_identity,
        is_streaming_output=is_streaming_output,
    )
    return {
        "pii_type": pii_type,
        "strategy": strategy,
        "apply_to_input": True,
        "apply_to_output": is_streaming_output,
    }


def main() -> None:
    print("regulated email：", build_pii_middleware_config("email", sensitivity="regulated"))
    print(
        "streaming internal：",
        build_pii_middleware_config(
            "email",
            sensitivity="internal",
            is_streaming_output=True,
        ),
    )


if __name__ == "__main__":
    main()
