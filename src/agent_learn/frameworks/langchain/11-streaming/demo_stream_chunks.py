"""构造模拟的 v2 StreamPart 序列，用于离线理解多 mode streaming。"""

from dataclasses import dataclass
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_stream_part_router_module():
    """从同目录加载 StreamPart 定义，避免连字符目录无法作为常规包导入。"""
    module_path = Path(__file__).with_name("stream_part_router.py")
    spec = spec_from_file_location("stream_part_router", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


StreamPart = _load_stream_part_router_module().StreamPart


@dataclass
class DemoToken:
    """轻量 token 对象，模拟 messages mode 中的 message chunk。"""

    content: str


def build_demo_v2_stream_parts() -> list:
    """构造包含 updates、messages、custom 的演示流。"""
    return [
        StreamPart(
            type="updates",
            data={"model": {"messages": [{"role": "assistant", "tool_calls": ["pending"]}]}},
            ns=(),
        ),
        StreamPart(
            type="messages",
            data=(DemoToken(content="我先"), {"langgraph_node": "model"}),
            ns=(),
        ),
        StreamPart(
            type="messages",
            data=(DemoToken(content="查询天气。"), {"langgraph_node": "model"}),
            ns=(),
        ),
        StreamPart(
            type="custom",
            data="Looking up data for city: Shanghai",
            ns=(),
        ),
        StreamPart(
            type="updates",
            data={"tools": {"messages": [{"role": "tool", "name": "get_city_weather"}]}},
            ns=(),
        ),
        StreamPart(
            type="messages",
            data=(DemoToken(content="上海当前晴朗。"), {"langgraph_node": "model"}),
            ns=(),
        ),
        StreamPart(
            type="updates",
            data={"model": {"messages": [{"role": "assistant", "content": "上海当前晴朗。"}]}},
            ns=(),
        ),
    ]


def extract_update_node_names(parts: list) -> list[str]:
    """从 updates chunk 中提取出现过的 node 名称。"""
    node_names: list[str] = []
    for part in parts:
        if part.type != "updates" or not isinstance(part.data, dict):
            continue
        for node_name in part.data:
            if node_name not in node_names:
                node_names.append(node_name)
    return node_names


def main() -> None:
    parts = build_demo_v2_stream_parts()
    print("演示流 chunk 数：", len(parts))
    print("updates 节点序列：", extract_update_node_names(parts))


if __name__ == "__main__":
    main()
