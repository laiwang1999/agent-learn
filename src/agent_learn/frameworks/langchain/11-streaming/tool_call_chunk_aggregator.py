"""演示为何 tool call 参数必须以 chunk 聚合，而不能在 JSON 未完整时执行。"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ToolCallChunk:
    """模拟 `messages` mode 中的 tool call 参数片段。"""

    tool_name: str
    tool_call_id: str
    arguments_fragment: str
    chunk_position: str | None = None


@dataclass
class AggregatedToolCall:
    """聚合完成后的工具调用。"""

    tool_name: str
    tool_call_id: str
    arguments_json: str

    def is_ready_for_execution(self) -> bool:
        """参数 JSON 非空且以 `}` 结尾时，才视为可解析。"""
        normalized = self.arguments_json.strip()
        return bool(normalized) and normalized.endswith("}")


def aggregate_tool_call_arguments(chunks: list[ToolCallChunk]) -> list[AggregatedToolCall]:
    """把同一 tool call 的多个 argument fragment 合并为完整调用。

    只有出现 `chunk_position == \"last\"` 或参数 JSON 已闭合时，才返回可执行调用。
    """
    grouped: dict[str, AggregatedToolCall] = {}
    last_seen: dict[str, bool] = {}

    for chunk in chunks:
        current = grouped.setdefault(
            chunk.tool_call_id,
            AggregatedToolCall(
                tool_name=chunk.tool_name,
                tool_call_id=chunk.tool_call_id,
                arguments_json="",
            ),
        )
        current.arguments_json += chunk.arguments_fragment
        if chunk.chunk_position == "last":
            last_seen[chunk.tool_call_id] = True

    ready_calls: list[AggregatedToolCall] = []
    for tool_call_id, aggregated in grouped.items():
        if last_seen.get(tool_call_id) or aggregated.is_ready_for_execution():
            ready_calls.append(aggregated)
    return ready_calls


def parse_tool_call_arguments(arguments_json: str) -> dict[str, Any]:
    """把聚合后的 arguments JSON 解析为字典；不完整时抛出错误。"""
    import json

    normalized = arguments_json.strip()
    if not normalized:
        raise ValueError("Tool call arguments are empty.")
    return json.loads(normalized)


def build_demo_tool_call_chunks() -> list[ToolCallChunk]:
    """构造逐步流出 JSON 参数的演示 chunk 序列。"""
    return [
        ToolCallChunk(
            tool_name="get_city_weather",
            tool_call_id="call_weather_001",
            arguments_fragment='{"city_name": "',
            chunk_position=None,
        ),
        ToolCallChunk(
            tool_name="get_city_weather",
            tool_call_id="call_weather_001",
            arguments_fragment="Shanghai",
            chunk_position=None,
        ),
        ToolCallChunk(
            tool_name="get_city_weather",
            tool_call_id="call_weather_001",
            arguments_fragment='"}',
            chunk_position="last",
        ),
    ]


def build_incomplete_tool_call_chunks() -> list[ToolCallChunk]:
    """构造缺少结束信号的 chunk，用于演示不可 premature 执行。"""
    return [
        ToolCallChunk(
            tool_name="get_city_weather",
            tool_call_id="call_weather_002",
            arguments_fragment='{"city_name": "Shanghai"',
            chunk_position=None,
        ),
    ]


def main() -> None:
    complete_chunks = build_demo_tool_call_chunks()
    incomplete_chunks = build_incomplete_tool_call_chunks()

    ready_calls = aggregate_tool_call_arguments(complete_chunks)
    incomplete_calls = aggregate_tool_call_arguments(incomplete_chunks)

    print("完整 chunk 聚合结果：", ready_calls)
    if ready_calls:
        print("解析参数：", parse_tool_call_arguments(ready_calls[0].arguments_json))

    print("不完整 chunk 可执行调用数：", len(incomplete_calls))


if __name__ == "__main__":
    main()
