"""构造模拟的 v3 event run，用于离线理解 typed projections 的数据形状。"""

from dataclasses import dataclass, field
from typing import Any, Literal


ProjectionName = Literal["messages", "tool_calls", "values", "output"]


@dataclass(frozen=True, slots=True)
class TextDeltaEvent:
    """模型文本增量事件，对应 `message.text` 中的一个 delta。"""

    node: str
    delta: str
    sequence: int


@dataclass(frozen=True, slots=True)
class ModelToolCallChunkEvent:
    """模型正在生成 tool call 参数时的 chunk，对应 `message.tool_calls`。"""

    node: str
    tool_name: str
    argument_chunk: str
    sequence: int


@dataclass(frozen=True, slots=True)
class ToolExecutionEvent:
    """工具执行生命周期事件，对应 `stream.tool_calls`。"""

    tool_name: str
    phase: Literal["start", "output_delta", "complete", "error"]
    input_payload: dict[str, Any] | None = None
    output_delta: str | None = None
    output: dict[str, Any] | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class StateSnapshotEvent:
    """Agent state 快照，对应 `stream.values` 中的一项。"""

    message_count: int
    task_stage: str


@dataclass
class DemoEventRun:
    """一次 Agent 运行的模拟 projection 数据集合。"""

    message_text_deltas: list[TextDeltaEvent] = field(default_factory=list)
    model_tool_call_chunks: list[ModelToolCallChunkEvent] = field(default_factory=list)
    tool_execution_events: list[ToolExecutionEvent] = field(default_factory=list)
    state_snapshots: list[StateSnapshotEvent] = field(default_factory=list)
    final_output: dict[str, Any] = field(default_factory=dict)


def build_demo_weather_run() -> DemoEventRun:
    """构造“查询旧金山天气”场景的模拟 event run。

    事件顺序体现典型 Agent 运行：
    1. 模型先流式输出思考文本；
    2. 模型生成 tool call 参数 chunk；
    3. 工具开始执行并输出增量；
    4. state 随 step 更新；
    5. 运行结束给出 final output。
    """
    return DemoEventRun(
        message_text_deltas=[
            TextDeltaEvent(node="model", delta="我先", sequence=1),
            TextDeltaEvent(node="model", delta="查询", sequence=2),
            TextDeltaEvent(node="model", delta="旧金山天气。", sequence=3),
            TextDeltaEvent(node="model", delta="旧金山当前晴朗。", sequence=4),
        ],
        model_tool_call_chunks=[
            ModelToolCallChunkEvent(
                node="model",
                tool_name="get_city_weather",
                argument_chunk='{"city_name": "San Francisco"',
                sequence=1,
            ),
            ModelToolCallChunkEvent(
                node="model",
                tool_name="get_city_weather",
                argument_chunk='}',
                sequence=2,
            ),
        ],
        tool_execution_events=[
            ToolExecutionEvent(
                tool_name="get_city_weather",
                phase="start",
                input_payload={"city_name": "San Francisco"},
            ),
            ToolExecutionEvent(
                tool_name="get_city_weather",
                phase="output_delta",
                output_delta="It's always sunny",
            ),
            ToolExecutionEvent(
                tool_name="get_city_weather",
                phase="complete",
                output={
                    "status": "success",
                    "data": {"city_name": "San Francisco", "conditions": "sunny"},
                },
            ),
        ],
        state_snapshots=[
            StateSnapshotEvent(message_count=1, task_stage="awaiting_model"),
            StateSnapshotEvent(message_count=3, task_stage="tool_running"),
            StateSnapshotEvent(message_count=5, task_stage="completed"),
        ],
        final_output={
            "messages": [
                {"role": "user", "content": "旧金山天气如何？"},
                {"role": "assistant", "content": "旧金山当前晴朗。"},
            ],
            "task_stage": "completed",
        },
    )


def build_failed_tool_run() -> DemoEventRun:
    """构造工具执行失败的模拟 run，用于观察 error projection。"""
    base_run = build_demo_weather_run()
    return DemoEventRun(
        message_text_deltas=base_run.message_text_deltas[:2],
        model_tool_call_chunks=base_run.model_tool_call_chunks,
        tool_execution_events=[
            ToolExecutionEvent(
                tool_name="get_city_weather",
                phase="start",
                input_payload={"city_name": "San Francisco"},
            ),
            ToolExecutionEvent(
                tool_name="get_city_weather",
                phase="error",
                error_message="external_service_error: weather API timeout",
            ),
        ],
        state_snapshots=base_run.state_snapshots[:2],
        final_output={
            "messages": [
                {"role": "user", "content": "旧金山天气如何？"},
                {"role": "assistant", "content": "天气服务暂时不可用，请稍后重试。"},
            ],
            "task_stage": "failed",
        },
    )


def list_projection_names() -> list[ProjectionName]:
    """列出本章演示涉及的 core projections。"""
    return ["messages", "tool_calls", "values", "output"]


def main() -> None:
    demo_run = build_demo_weather_run()
    print("文本增量条数：", len(demo_run.message_text_deltas))
    print("模型 tool call chunk 条数：", len(demo_run.model_tool_call_chunks))
    print("工具执行事件条数：", len(demo_run.tool_execution_events))
    print("state 快照条数：", len(demo_run.state_snapshots))
    print("最终输出 task_stage：", demo_run.final_output.get("task_stage"))


if __name__ == "__main__":
    main()
