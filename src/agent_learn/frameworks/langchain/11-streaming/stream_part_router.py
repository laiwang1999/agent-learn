"""演示 v2 `StreamPart` 如何按 `type` 路由到 updates、messages 或 custom 处理逻辑。"""

from dataclasses import dataclass, field
from typing import Any, Literal

StreamModeType = Literal["updates", "messages", "custom"]


@dataclass(frozen=True, slots=True)
class StreamPart:
    """v2 streaming 的统一 chunk 结构。"""

    type: StreamModeType
    data: Any
    ns: tuple[str, ...] = ()


@dataclass
class StreamPartSummary:
    """统计一次模拟流中各 mode 的 chunk 数量与摘要。"""

    updates_count: int = 0
    messages_count: int = 0
    custom_count: int = 0
    update_nodes: list[str] = field(default_factory=list)
    message_tokens: list[str] = field(default_factory=list)
    custom_messages: list[str] = field(default_factory=list)


def route_stream_part(part: StreamPart, summary: StreamPartSummary) -> None:
    """根据 `part.type` 更新统计摘要，模拟多 mode 消费分发。"""
    if part.type == "updates":
        summary.updates_count += 1
        if isinstance(part.data, dict):
            for node_name in part.data:
                if node_name not in summary.update_nodes:
                    summary.update_nodes.append(node_name)
        return

    if part.type == "messages":
        summary.messages_count += 1
        token, _metadata = part.data if isinstance(part.data, tuple) and len(part.data) == 2 else (part.data, {})
        content = getattr(token, "content", token)
        if isinstance(content, str) and content:
            summary.message_tokens.append(content)
        return

    if part.type == "custom":
        summary.custom_count += 1
        if isinstance(part.data, str):
            summary.custom_messages.append(part.data)


def summarize_stream_parts(parts: list[StreamPart]) -> StreamPartSummary:
    """遍历 StreamPart 列表并汇总各 mode 信息。"""
    summary = StreamPartSummary()
    for part in parts:
        route_stream_part(part, summary)
    return summary


def format_stream_part(part: StreamPart) -> str:
    """把单个 StreamPart 格式化为 CLI 友好文本。"""
    if part.type == "updates":
        return f"[updates] nodes={list(part.data.keys()) if isinstance(part.data, dict) else part.data}"
    if part.type == "messages":
        token, metadata = part.data if isinstance(part.data, tuple) else (part.data, {})
        node = metadata.get("langgraph_node", "unknown") if isinstance(metadata, dict) else "unknown"
        content = getattr(token, "content", str(token))
        return f"[messages] node={node} token={content!r}"
    return f"[custom] {part.data!r}"


def main() -> None:
    from importlib.util import module_from_spec, spec_from_file_location
    from pathlib import Path

    module_path = Path(__file__).with_name("demo_stream_chunks.py")
    spec = spec_from_file_location("demo_stream_chunks", module_path)
    assert spec is not None
    assert spec.loader is not None
    demo_module = module_from_spec(spec)
    spec.loader.exec_module(demo_module)

    parts = demo_module.build_demo_v2_stream_parts()
    summary = summarize_stream_parts(parts)

    for part in parts:
        print(format_stream_part(part))

    print("updates 条数：", summary.updates_count)
    print("messages 条数：", summary.messages_count)
    print("custom 条数：", summary.custom_count)
    print("合并文本：", "".join(summary.message_tokens))


if __name__ == "__main__":
    main()
