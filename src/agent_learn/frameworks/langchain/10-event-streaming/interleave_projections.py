"""演示同步场景下如何交织消费多个 typed projections。"""

from typing import Any


def interleave_projection_streams(
    streams: dict[str, list[Any]],
    *,
    order: list[str],
) -> list[tuple[str, Any]]:
    """按 round-robin 交织多个 projection 流，模拟 `stream.interleave(...)` 行为。

    简单 CLI 或单通道日志可用这种模式；复杂前端通常改为分通道独立订阅。
    """
    if not order:
        raise ValueError("Projection order is required.")

    iterators = {name: iter(streams.get(name, [])) for name in order}
    interleaved: list[tuple[str, Any]] = []

    while iterators:
        exhausted: list[str] = []
        for name in order:
            iterator = iterators.get(name)
            if iterator is None:
                continue
            try:
                item = next(iterator)
            except StopIteration:
                exhausted.append(name)
                continue
            interleaved.append((name, item))

        for name in exhausted:
            iterators.pop(name, None)

    return interleaved


def build_demo_interleave_input() -> dict[str, list[Any]]:
    """构造可交织的演示 projection 数据。"""
    return {
        "messages": [
            {"delta": "我先"},
            {"delta": "查询"},
            {"delta": "天气。"},
        ],
        "tool_calls": [
            {"tool_name": "get_city_weather", "phase": "start"},
            {"tool_name": "get_city_weather", "phase": "complete"},
        ],
        "values": [
            {"message_count": 1, "task_stage": "awaiting_model"},
            {"message_count": 3, "task_stage": "completed"},
        ],
    }


def format_interleaved_item(projection_name: str, item: dict[str, Any]) -> str:
    """把交织后的事件格式化为 CLI 友好文本。"""
    if projection_name == "messages":
        return f"[messages] {item.get('delta', '')}"
    if projection_name == "tool_calls":
        return f"[tool_calls] {item.get('tool_name')}::{item.get('phase')}"
    if projection_name == "values":
        return (
            f"[values] messages={item.get('message_count')} "
            f"stage={item.get('task_stage')}"
        )
    return f"[{projection_name}] {item}"


def main() -> None:
    streams = build_demo_interleave_input()
    interleaved = interleave_projection_streams(
        streams,
        order=["messages", "tool_calls", "values"],
    )
    for projection_name, item in interleaved:
        print(format_interleaved_item(projection_name, item))


if __name__ == "__main__":
    main()
