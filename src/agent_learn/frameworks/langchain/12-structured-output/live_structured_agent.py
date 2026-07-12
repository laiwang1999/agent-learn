"""演示真实 Agent 如何通过 `response_format` 返回 `structured_response`。"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from langchain.agents import create_agent

from agent_learn.frameworks.langchain.chat_model_factory import create_chat_model


def _load_contact_schemas_module():
    """从同章节目录加载 schema 定义。"""
    module_path = Path(__file__).with_name("contact_schemas.py")
    spec = spec_from_file_location("contact_schemas", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ContactInfo = _load_contact_schemas_module().ContactInfo


def create_contact_extraction_agent():
    """创建带 `response_format` 的联系人抽取 Agent。"""
    return create_agent(
        model=create_chat_model(temperature=0.1, max_tokens=600),
        tools=[],
        response_format=ContactInfo,
        system_prompt=(
            "你是信息抽取助手。从用户文本中提取联系人姓名、邮箱和电话。"
            "文本中未出现的字段必须返回 null，禁止编造。最终自然语言答复必须使用中文。"
        ),
        name="contact_extraction_agent",
    )


def main() -> None:
    agent = create_contact_extraction_agent()
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "联系人：李四，邮箱 lisi@example.com，没有提供电话。",
                }
            ]
        }
    )

    structured_response = result.get("structured_response")
    print("structured_response：", structured_response)
    if hasattr(structured_response, "model_dump"):
        print(structured_response.model_dump_json(indent=2, ensure_ascii=False))
    print("最后一条消息：", result["messages"][-1].content)


if __name__ == "__main__":
    main()
