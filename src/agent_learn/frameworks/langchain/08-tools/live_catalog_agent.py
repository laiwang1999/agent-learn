"""演示真实 Agent 如何根据 tool schema 选择并调用本章定义的工具。"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from langchain.agents import create_agent

from agent_learn.frameworks.langchain.chat_model_factory import create_chat_model


def _load_basic_tool_definition_module():
    """从同章节目录加载工具定义，避免连字符目录无法作为常规包导入。"""
    module_path = Path(__file__).with_name("basic_tool_definition.py")
    spec = spec_from_file_location("basic_tool_definition", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_tools = _load_basic_tool_definition_module()
search_lesson_catalog = _tools.search_lesson_catalog
get_city_weather = _tools.get_city_weather


def create_catalog_agent():
    """创建绑定本章课程搜索与天气工具的学习 Agent。"""
    return create_agent(
        model=create_chat_model(),
        tools=[search_lesson_catalog, get_city_weather],
        system_prompt=(
            "你是课程学习助手。查询课程目录时必须调用 search_lesson_catalog，"
            "查询天气时必须调用 get_city_weather，禁止编造工具结果。"
            "最终答复必须使用中文。"
        ),
        name="catalog_tools_agent",
    )


def main() -> None:
    agent = create_catalog_agent()
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "请搜索标题包含 LangChain 的课程，并告诉我上海当前天气。",
                }
            ]
        }
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
