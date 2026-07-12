from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


FRAMEWORK_ROOT = (
    Path(__file__).parents[1]
    / "src"
    / "agent_learn"
    / "frameworks"
    / "langchain"
    / "11-streaming"
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


def test_summarize_stream_parts_counts_each_mode() -> None:
    router_module = load_chapter_module("stream_part_router.py")
    demo_module = load_chapter_module("demo_stream_chunks.py")
    parts = demo_module.build_demo_v2_stream_parts()

    summary = router_module.summarize_stream_parts(parts)

    assert summary.updates_count == 3
    assert summary.messages_count == 3
    assert summary.custom_count == 1
    assert "model" in summary.update_nodes
    assert "tools" in summary.update_nodes


def test_extract_update_node_names_preserves_order() -> None:
    demo_module = load_chapter_module("demo_stream_chunks.py")
    parts = demo_module.build_demo_v2_stream_parts()

    node_names = demo_module.extract_update_node_names(parts)

    assert node_names == ["model", "tools"]


def test_aggregate_tool_call_arguments_waits_for_last_chunk() -> None:
    module = load_chapter_module("tool_call_chunk_aggregator.py")
    chunks = module.build_demo_tool_call_chunks()

    ready_calls = module.aggregate_tool_call_arguments(chunks)

    assert len(ready_calls) == 1
    assert ready_calls[0].tool_name == "get_city_weather"
    parsed = module.parse_tool_call_arguments(ready_calls[0].arguments_json)
    assert parsed["city_name"] == "Shanghai"


def test_incomplete_tool_call_chunks_are_not_ready() -> None:
    module = load_chapter_module("tool_call_chunk_aggregator.py")
    chunks = module.build_incomplete_tool_call_chunks()

    ready_calls = module.aggregate_tool_call_arguments(chunks)

    assert ready_calls == []


def test_format_stream_part_for_custom_mode() -> None:
    router_module = load_chapter_module("stream_part_router.py")

    formatted = router_module.format_stream_part(
        router_module.StreamPart(type="custom", data="progress: 50%")
    )

    assert "[custom]" in formatted
    assert "50%" in formatted


def test_route_stream_part_appends_message_tokens() -> None:
    router_module = load_chapter_module("stream_part_router.py")
    demo_module = load_chapter_module("demo_stream_chunks.py")
    summary = router_module.StreamPartSummary()

    message_parts = [
        part for part in demo_module.build_demo_v2_stream_parts() if part.type == "messages"
    ]
    for part in message_parts:
        router_module.route_stream_part(part, summary)

    assert "".join(summary.message_tokens) == "我先查询天气。上海当前晴朗。"
