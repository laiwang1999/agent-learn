from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


FRAMEWORK_ROOT = (
    Path(__file__).parents[1]
    / "src"
    / "agent_learn"
    / "frameworks"
    / "langchain"
    / "10-event-streaming"
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


def test_accumulate_text_deltas_joins_chunks() -> None:
    module = load_chapter_module("projection_consumers.py")

    assert module.accumulate_text_deltas(["旧", "金", "山"]) == "旧金山"


def test_consume_message_text_projection_groups_by_node() -> None:
    demo_module = load_chapter_module("demo_event_run.py")
    consumer_module = load_chapter_module("projection_consumers.py")
    demo_run = demo_module.build_demo_weather_run()

    result = consumer_module.consume_message_text_projection(demo_run.message_text_deltas)

    assert result["delta_count"] == 4
    assert "旧金山当前晴朗。" in result["combined_text"]
    assert result["grouped_full_text"]["model"].startswith("我先")


def test_finalize_model_tool_calls_merges_argument_chunks() -> None:
    demo_module = load_chapter_module("demo_event_run.py")
    consumer_module = load_chapter_module("projection_consumers.py")
    demo_run = demo_module.build_demo_weather_run()

    finalized = consumer_module.finalize_model_tool_calls(demo_run.model_tool_call_chunks)

    assert len(finalized) == 1
    assert finalized[0]["tool_name"] == "get_city_weather"
    assert '"city_name": "San Francisco"' in finalized[0]["arguments_json"]


def test_consume_tool_execution_projection_reports_success() -> None:
    demo_module = load_chapter_module("demo_event_run.py")
    consumer_module = load_chapter_module("projection_consumers.py")
    demo_run = demo_module.build_demo_weather_run()

    executions = consumer_module.consume_tool_execution_projection(demo_run.tool_execution_events)

    assert executions[0]["status"] == "success"
    assert executions[0]["output"]["data"]["conditions"] == "sunny"
    assert executions[0]["output_deltas"] == ["It's always sunny"]


def test_failed_tool_run_reports_error_projection() -> None:
    demo_module = load_chapter_module("demo_event_run.py")
    consumer_module = load_chapter_module("projection_consumers.py")
    failed_run = demo_module.build_failed_tool_run()

    executions = consumer_module.consume_tool_execution_projection(failed_run.tool_execution_events)

    assert executions[0]["status"] == "error"
    assert "timeout" in executions[0]["error"]


def test_interleave_projection_streams_round_robin() -> None:
    module = load_chapter_module("interleave_projections.py")
    streams = module.build_demo_interleave_input()

    interleaved = module.interleave_projection_streams(
        streams,
        order=["messages", "tool_calls", "values"],
    )

    assert [name for name, _ in interleaved] == [
        "messages",
        "tool_calls",
        "values",
        "messages",
        "tool_calls",
        "values",
        "messages",
    ]


def test_redact_stream_payload_masks_email() -> None:
    module = load_chapter_module("stream_redaction.py")
    raw_event = module.build_sensitive_tool_output_event()

    redacted = module.redact_stream_payload(raw_event)
    email = redacted["output"]["data"]["contact_email"]

    assert email == "[REDACTED_EMAIL]"
    assert not module.contains_email_address(email)


def test_summarize_demo_run_includes_output_projection() -> None:
    demo_module = load_chapter_module("demo_event_run.py")
    consumer_module = load_chapter_module("projection_consumers.py")
    summary = consumer_module.summarize_demo_run(demo_module.build_demo_weather_run())

    assert summary["output"]["task_stage"] == "completed"
    assert len(summary["values"]) == 3
