"""演示如何消费 messages、tool_calls 与 values 等 typed projections。"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any


def _load_demo_event_run_module():
    """从同目录加载 demo 模块，避免连字符目录无法作为常规包导入。"""
    module_path = Path(__file__).with_name("demo_event_run.py")
    spec = spec_from_file_location("demo_event_run", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_demo = _load_demo_event_run_module()
DemoEventRun = _demo.DemoEventRun
ModelToolCallChunkEvent = _demo.ModelToolCallChunkEvent
TextDeltaEvent = _demo.TextDeltaEvent
ToolExecutionEvent = _demo.ToolExecutionEvent
build_demo_weather_run = _demo.build_demo_weather_run
build_failed_tool_run = _demo.build_failed_tool_run


def accumulate_text_deltas(deltas: list[str]) -> str:
    """把 `message.text` 增量拼接为完整文本。"""
    return "".join(deltas)


def consume_message_text_projection(events: list[TextDeltaEvent]) -> dict[str, Any]:
    """消费 messages projection 中的文本增量，并保留 node 分组信息。"""
    grouped_deltas: dict[str, list[str]] = {}
    for event in events:
        grouped_deltas.setdefault(event.node, []).append(event.delta)

    grouped_full_text = {
        node: accumulate_text_deltas(deltas) for node, deltas in grouped_deltas.items()
    }
    return {
        "grouped_full_text": grouped_full_text,
        "combined_text": accumulate_text_deltas([event.delta for event in events]),
        "delta_count": len(events),
    }


def finalize_model_tool_calls(chunks: list[ModelToolCallChunkEvent]) -> list[dict[str, Any]]:
    """把模型侧 tool call chunk 合并为最终 tool call 列表。"""
    grouped_chunks: dict[str, list[str]] = {}
    for chunk in chunks:
        grouped_chunks.setdefault(chunk.tool_name, []).append(chunk.argument_chunk)

    finalized_calls: list[dict[str, Any]] = []
    for tool_name, argument_chunks in grouped_chunks.items():
        finalized_calls.append(
            {
                "tool_name": tool_name,
                "arguments_json": "".join(argument_chunks),
            }
        )
    return finalized_calls


def consume_tool_execution_projection(
    events: list[ToolExecutionEvent],
) -> list[dict[str, Any]]:
    """消费 `stream.tool_calls` 生命周期事件，汇总每次工具执行结果。"""
    executions: dict[str, dict[str, Any]] = {}

    for event in events:
        current = executions.setdefault(
            event.tool_name,
            {
                "tool_name": event.tool_name,
                "input": None,
                "output_deltas": [],
                "output": None,
                "error": None,
                "status": "pending",
            },
        )

        if event.phase == "start":
            current["input"] = event.input_payload
            current["status"] = "running"
        elif event.phase == "output_delta" and event.output_delta:
            current["output_deltas"].append(event.output_delta)
            current["status"] = "running"
        elif event.phase == "complete":
            current["output"] = event.output
            current["status"] = "success"
        elif event.phase == "error":
            current["error"] = event.error_message
            current["status"] = "error"

    return list(executions.values())


def consume_values_projection(run: DemoEventRun) -> list[dict[str, Any]]:
    """把 state 快照 projection 转成可打印字典列表。"""
    return [
        {
            "message_count": snapshot.message_count,
            "task_stage": snapshot.task_stage,
        }
        for snapshot in run.state_snapshots
    ]


def summarize_demo_run(run: DemoEventRun) -> dict[str, Any]:
    """汇总一次模拟 run 的全部核心 projection 视图。"""
    return {
        "messages": consume_message_text_projection(run.message_text_deltas),
        "model_tool_calls": finalize_model_tool_calls(run.model_tool_call_chunks),
        "tool_executions": consume_tool_execution_projection(run.tool_execution_events),
        "values": consume_values_projection(run),
        "output": run.final_output,
    }


def main() -> None:
    success_summary = summarize_demo_run(build_demo_weather_run())
    failure_summary = summarize_demo_run(build_failed_tool_run())

    print("成功 run 合并文本：", success_summary["messages"]["combined_text"])
    print("成功 run 工具执行：", success_summary["tool_executions"])
    print("失败 run 工具执行：", failure_summary["tool_executions"])
    print("最终 output：", success_summary["output"]["task_stage"])


if __name__ == "__main__":
    main()
