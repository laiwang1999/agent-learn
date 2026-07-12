"""演示 live event stream 在离开 run 前的 PII 脱敏。"""

import re
from typing import Any


EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def redact_email_addresses(text: str) -> str:
    """把文本中的邮箱地址替换为占位符。"""
    return EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)


def redact_stream_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """对单条 stream wire payload 做递归脱敏。

    `after_model` 等 state 级处理可能对 live reader 太晚；应在事件发出前处理。
    """
    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, str):
            redacted[key] = redact_email_addresses(value)
        elif isinstance(value, dict):
            redacted[key] = redact_stream_payload(value)
        elif isinstance(value, list):
            redacted[key] = [
                redact_stream_payload(item)
                if isinstance(item, dict)
                else redact_email_addresses(item)
                if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            redacted[key] = value
    return redacted


def contains_email_address(text: str) -> bool:
    """判断文本是否仍包含未脱敏邮箱。"""
    return EMAIL_PATTERN.search(text) is not None


def build_sensitive_tool_output_event() -> dict[str, Any]:
    """构造包含邮箱的模拟 tool output 事件。"""
    return {
        "projection": "tool_calls",
        "tool_name": "lookup_account_info",
        "phase": "complete",
        "output": {
            "status": "success",
            "data": {
                "user_name": "Alice",
                "contact_email": "alice@example.com",
            },
        },
    }


def main() -> None:
    raw_event = build_sensitive_tool_output_event()
    redacted_event = redact_stream_payload(raw_event)
    raw_email = raw_event["output"]["data"]["contact_email"]
    redacted_email = redacted_event["output"]["data"]["contact_email"]

    print("原始邮箱：", raw_email)
    print("脱敏后：", redacted_email)
    print("原始仍含邮箱：", contains_email_address(raw_email))
    print("脱敏后仍含邮箱：", contains_email_address(redacted_email))


if __name__ == "__main__":
    main()
