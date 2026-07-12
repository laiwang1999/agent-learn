"""演示 structured output 的 schema 校验与 validation error 消息构造。"""

from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError


def _load_contact_schemas_module():
    """从同目录加载 schema 定义，避免连字符目录无法作为常规包导入。"""
    module_path = Path(__file__).with_name("contact_schemas.py")
    spec = spec_from_file_location("contact_schemas", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_schemas = _load_contact_schemas_module()
ContactInfo = _schemas.ContactInfo
ProductRating = _schemas.ProductRating


@dataclass(frozen=True, slots=True)
class ValidationOutcome:
    """结构化 payload 的校验结果。"""

    is_valid: bool
    model: BaseModel | None = None
    error_code: str | None = None
    error_message: str | None = None


def validate_structured_payload(
    schema: type[BaseModel],
    payload: dict[str, Any],
) -> ValidationOutcome:
    """用 Pydantic 校验结构化 payload，模拟 Agent 侧的 validation 边界。"""
    try:
        validated = schema.model_validate(payload)
    except ValidationError as error:
        return ValidationOutcome(
            is_valid=False,
            error_code="structured_output_validation_error",
            error_message=format_validation_error(error),
        )
    return ValidationOutcome(is_valid=True, model=validated)


def format_validation_error(error: ValidationError) -> str:
    """把 Pydantic 校验错误格式化为可反馈给模型的简短消息。"""
    messages = [issue["msg"] for issue in error.errors()]
    return "; ".join(messages)


def build_model_retry_hint(error_message: str) -> str:
    """构造类似 ToolStrategy 默认反馈的重试提示。"""
    return (
        "Structured output validation failed. "
        f"Please fix your mistakes: {error_message}"
    )


def main() -> None:
    valid_contact = validate_structured_payload(
        ContactInfo,
        {"name": "Bob", "email": "bob@example.com", "phone": None},
    )
    invalid_rating = validate_structured_payload(
        ProductRating,
        {
            "rating": 10,
            "sentiment": "positive",
            "key_points": ["很好"],
            "comment": "超出范围的评分示例。",
        },
    )

    print("合法联系人：", valid_contact)
    if invalid_rating.error_message:
        print("重试提示：", build_model_retry_hint(invalid_rating.error_message))


if __name__ == "__main__":
    main()
