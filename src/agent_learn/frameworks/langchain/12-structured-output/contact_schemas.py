"""定义 Agent `response_format` 使用的 Pydantic schema。"""

from typing import Literal

from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    """从自由文本中抽取的联系人信息。"""

    name: str = Field(description="联系人姓名，必须是非空文本。")
    email: str = Field(description="电子邮箱地址。")
    phone: str | None = Field(
        default=None,
        description="电话号码；文本中未出现时应返回 null，不要编造。",
    )


class ProductRating(BaseModel):
    """产品评论的结构化评分与要点。"""

    rating: int | None = Field(
        default=None,
        description="1 到 5 的整数评分；无法判断时为 null。",
        ge=1,
        le=5,
    )
    sentiment: Literal["positive", "negative", "neutral"] = Field(
        description="评论情感倾向。"
    )
    key_points: list[str] = Field(
        default_factory=list,
        description="评论关键要点，每项使用简短中文短语。",
    )
    comment: str = Field(description="不超过两句话的中文评论摘要。")


def build_demo_contact_payload() -> dict[str, object]:
    """构造可通过校验的演示联系人 payload。"""
    return {
        "name": "Alice",
        "email": "alice@example.com",
        "phone": "13800138000",
    }


def build_demo_product_rating_payload() -> dict[str, object]:
    """构造可通过校验的演示产品评分 payload。"""
    return {
        "rating": 5,
        "sentiment": "positive",
        "key_points": ["续航优秀", "屏幕清晰"],
        "comment": "整体体验很好，适合日常办公。",
    }


def main() -> None:
    contact = ContactInfo.model_validate(build_demo_contact_payload())
    rating = ProductRating.model_validate(build_demo_product_rating_payload())
    print(contact.model_dump_json(indent=2, ensure_ascii=False))
    print(rating.model_dump_json(indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
