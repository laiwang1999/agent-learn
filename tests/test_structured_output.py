from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


FRAMEWORK_ROOT = (
    Path(__file__).parents[1]
    / "src"
    / "agent_learn"
    / "frameworks"
    / "langchain"
    / "12-structured-output"
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


def test_contact_info_accepts_missing_phone() -> None:
    module = load_chapter_module("contact_schemas.py")
    contact = module.ContactInfo.model_validate(
        {"name": "Alice", "email": "alice@example.com", "phone": None}
    )

    assert contact.phone is None
    assert contact.name == "Alice"


def test_product_rating_rejects_out_of_range_score() -> None:
    module = load_chapter_module("contact_schemas.py")
    validation_module = load_chapter_module("schema_validation.py")

    outcome = validation_module.validate_structured_payload(
        module.ProductRating,
        {
            "rating": 10,
            "sentiment": "positive",
            "key_points": ["很好"],
            "comment": "评分超出范围。",
        },
    )

    assert outcome.is_valid is False
    assert outcome.error_code == "structured_output_validation_error"


def test_validate_structured_payload_accepts_demo_contact() -> None:
    schema_module = load_chapter_module("contact_schemas.py")
    validation_module = load_chapter_module("schema_validation.py")

    outcome = validation_module.validate_structured_payload(
        schema_module.ContactInfo,
        schema_module.build_demo_contact_payload(),
    )

    assert outcome.is_valid is True
    assert outcome.model is not None
    assert outcome.model.email == "alice@example.com"


def test_should_prefer_structured_response_when_present() -> None:
    module = load_chapter_module("structured_response_contract.py")
    final_state = module.build_demo_final_state_with_structured_response()

    assert module.should_prefer_structured_response(final_state) is True
    assert module.extract_structured_response(final_state)["name"] == "张三"


def test_extract_structured_response_returns_none_without_field() -> None:
    module = load_chapter_module("structured_response_contract.py")
    final_state = module.build_demo_final_state_without_structured_response()

    assert module.extract_structured_response(final_state) is None
    assert module.should_prefer_structured_response(final_state) is False


def test_build_model_retry_hint_includes_validation_message() -> None:
    module = load_chapter_module("schema_validation.py")
    hint = module.build_model_retry_hint("rating must be <= 5")

    assert "validation failed" in hint.lower()
    assert "rating must be <= 5" in hint
