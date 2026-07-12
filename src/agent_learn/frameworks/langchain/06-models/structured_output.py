"""演示使用 Pydantic schema 获取可校验的结构化模型输出。"""

from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage, SystemMessage

from agent_learn.frameworks.langchain.chat_model_factory import create_chat_model


class ArticleSummary(BaseModel):
    """定义学习资料摘要所需的稳定字段。"""

    title: str = Field(description="资料的标题。")
    topic: str = Field(description="资料所属的 Agent 工程主题。")
    summary: str = Field(description="不超过三句话的中文摘要。")
    confidence: float = Field(ge=0, le=1, description="结论的可信度，取值范围为 0 到 1。")


SYSTEM_PROMPT = """你是一名 Agent 工程学习助手。
请从用户提供的资料中提取结构化摘要。所有字段值必须使用中文；无法确认时降低 confidence，且不要编造事实。"""


def create_structured_model():
    """创建返回 `ArticleSummary` 的模型包装器。"""
    # schema 描述会传给模型，因此字段描述使用中文以约束模型的生成语言。
    return create_chat_model(temperature=0.1, max_tokens=600).with_structured_output(ArticleSummary)


def main() -> None:
    model = create_structured_model()
    response = model.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content="资料标题：Agent 工具设计。内容：工具应定义清晰参数、失败边界和可验证返回值。"
            ),
        ]
    )
    print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
