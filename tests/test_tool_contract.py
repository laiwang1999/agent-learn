from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


FRAMEWORK_ROOT = Path(__file__).parents[1] / "src" / "agent_learn" / "frameworks" / "langchain" / "08-tools"


def load_chapter_module(filename: str):
    """加载编号目录中的章节模块，避免目录连字符影响教学目录命名。"""
    module_path = FRAMEWORK_ROOT / filename
    spec = spec_from_file_location(filename.removesuffix(".py"), module_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_search_lesson_catalog_returns_structured_results() -> None:
    module = load_chapter_module("basic_tool_definition.py")
    result = module.search_lesson_catalog.invoke({"query": "LangChain", "limit": 2})

    assert result["status"] == "success"
    assert result["data"]["query"] == "langchain"
    assert len(result["data"]["results"]) == 1
    assert result["data"]["results"][0]["product_id"] == "course-001"


def test_search_lesson_catalog_rejects_empty_query() -> None:
    module = load_chapter_module("basic_tool_definition.py")
    result = module.search_lesson_catalog.invoke({"query": "   ", "limit": 2})

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_input"


def test_runtime_is_hidden_from_tool_schema() -> None:
    basic_module = load_chapter_module("basic_tool_definition.py")
    state_module = load_chapter_module("tool_state_access.py")

    weather_schema = basic_module.get_city_weather.get_input_schema().model_json_schema()

    assert basic_module.runtime_is_hidden_from_schema(weather_schema) is True
    assert basic_module.runtime_is_hidden_from_tool_args(state_module.get_user_preference) is True
    assert "preference_name" in state_module.get_user_preference.args


def test_read_user_preference_from_demo_state() -> None:
    module = load_chapter_module("tool_state_access.py")
    demo_state = module.build_demo_state()

    result = module.read_user_preference(demo_state, "display_language")

    assert result["status"] == "success"
    assert result["data"]["preference_value"] == "zh-CN"


def test_get_last_human_message_text() -> None:
    module = load_chapter_module("tool_state_access.py")
    demo_state = module.build_demo_state()

    message_text = module.get_last_human_message_text(demo_state["messages"])

    assert message_text == "请根据我的语言偏好回答。"


def test_dynamic_tool_filter_for_guest_and_editor() -> None:
    module = load_chapter_module("dynamic_tool_filter.py")
    tools = module.build_demo_toolset()

    guest_tools = module.select_tools_for_request(
        tools,
        module.ToolAccessContext(is_authenticated=False, user_role="guest"),
    )
    editor_tools = module.select_tools_for_request(
        tools,
        module.ToolAccessContext(is_authenticated=True, user_role="editor"),
    )

    assert module.list_tool_names(guest_tools) == ["public_search_catalog"]
    assert module.list_tool_names(editor_tools) == [
        "public_search_catalog",
        "read_tenant_inventory",
        "write_inventory_adjustment",
    ]


def test_dynamic_tool_filter_viewer_cannot_write() -> None:
    module = load_chapter_module("dynamic_tool_filter.py")
    tools = module.build_demo_toolset()

    viewer_tools = module.select_tools_for_request(
        tools,
        module.ToolAccessContext(is_authenticated=True, user_role="viewer"),
    )

    assert "write_inventory_adjustment" not in module.list_tool_names(viewer_tools)


def test_weather_tool_rejects_empty_city_name() -> None:
    module = load_chapter_module("basic_tool_definition.py")
    result = module.get_city_weather.invoke(
        {"city_name": "  ", "units": "celsius", "include_forecast": False}
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "invalid_input"
