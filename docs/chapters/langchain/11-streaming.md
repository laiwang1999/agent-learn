# 第 11 章实践：LangChain Streaming

## 来源与目标

- 教材来源：[11-langchain-streaming.md](https://github.com/laiwang1999/agent-book-for-myself/blob/master/langchain/11-langchain-streaming.md)
- 官方参考：[LangChain Streaming](https://docs.langchain.com/oss/python/langchain/streaming)

本章解释 Agent 运行时的**底层 stream modes**：`updates`、`messages` 与 `custom`。第 10 章的 Event Streaming 是应用层首选接口；本章帮助理解 projection 背后的运行时语义、v2 统一 `StreamPart` 格式，以及何时仍需要直接使用 `agent.stream(...)`。

完成后，你应能区分三种 mode 的职责、在参数 JSON 未完整前不执行工具，并在真实 Agent 上观察 `stream_mode=["updates", "messages"]` 的输出。

## 必须掌握

1. **三种核心 mode**：`updates` 看 Agent step 进度，`messages` 看 LLM token 与 metadata，`custom` 看工具或节点发出的业务进度。见 [stream_part_router.py](../../../src/agent_learn/frameworks/langchain/11-streaming/stream_part_router.py)。
2. **v2 统一 chunk 结构**：`{"type": "...", "ns": ..., "data": ...}`，多 mode 时按 `type` 分发。见 [stream_part_router.py](../../../src/agent_learn/frameworks/langchain/11-streaming/stream_part_router.py)。
3. **Tool call chunk 需聚合**：参数 JSON 逐步流出，不能在 chunk 未完整时执行工具。见 [tool_call_chunk_aggregator.py](../../../src/agent_learn/frameworks/langchain/11-streaming/tool_call_chunk_aggregator.py)。
4. **与 Event Streaming 的分工**：新 UI 优先 `stream_events(version="v3")`；调试 graph、兼容旧代码、组合多 mode 时理解本章。见第 10 章。
5. **真实底层 streaming**：`agent.stream(..., stream_mode=..., version="v2")` 观察 updates 与 messages。见 [live_stream_modes_agent.py](../../../src/agent_learn/frameworks/langchain/11-streaming/live_stream_modes_agent.py)。

## Streaming 在系统中的位置

```text
第 10 章 Event Streaming：应用层 typed projections（首选）
第 11 章 Streaming：底层 stream modes（updates / messages / custom）
agent.stream(version="v2") → StreamPart → 按 type 分发到 UI / 日志 / 调试面板
```

## 运行

### 离线验证（不需要 API Key）

```powershell
pip install -e ".[dev]"
python src/agent_learn/frameworks/langchain/11-streaming/stream_part_router.py
python src/agent_learn/frameworks/langchain/11-streaming/tool_call_chunk_aggregator.py
python src/agent_learn/frameworks/langchain/11-streaming/demo_stream_chunks.py
pytest tests/test_streaming_modes.py
```

### 真实 Agent streaming（需要 `.env`）

```powershell
pip install -e ".[dev,openai]"
python src/agent_learn/frameworks/langchain/11-streaming/live_stream_modes_agent.py
```

环境变量与第 7 章相同：`DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`AGENT_MODEL`、`AGENT_TEMPERATURE`、`AGENT_TIMEOUT_SECONDS`、`AGENT_MAX_TOKENS`。

该命令使用 `agent.stream(..., stream_mode=["updates", "messages"], version="v2")`，打印 step 更新与模型文本增量。

## 工程判断

| 场景 | 推荐做法 | 不应依赖 |
| --- | --- | --- |
| 新前端 Agent UI | Event Streaming `stream_events(v3)`。 | 只解析底层 tuple 或手写拆包。 |
| 调试每个 Agent step | `stream_mode="updates"`。 | 只等最终 `invoke` 结果。 |
| 打字机文本 | `stream_mode="messages"` 或 v3 `stream.messages`。 | 假设 chunk 一定是纯字符串。 |
| 工具内部进度 | `get_stream_writer()` + `stream_mode="custom"`。 | 把所有进度塞进最终文本回答。 |
| 同时看 step 与 token | `stream_mode=["updates", "messages"]` + v2。 | 混在一个 handler 里不区分 type。 |
| 工具参数未完成 | 聚合 chunk 或等 completed message。 | 见到第一个 `tool_call_chunk` 就执行工具。 |
| 内部模型不展示 | `streaming=False` 或 `disable_streaming=True`。 | 所有模型默认流出 token。 |

## 常见失败模式

| 现象 | 原因 | 处理方式 |
| --- | --- | --- |
| 工具执行参数解析失败。 | 在 JSON 未完整时执行 tool call。 | 等 `chunk_position == "last"` 或从 `updates` 读 completed message。 |
| 前端只看到 token，不知道执行到哪一步。 | 只用了 `messages`，没用 `updates`。 | 组合 `["updates", "messages"]` 或改用 Event Streaming。 |
| custom 进度从未出现。 | 未传 `stream_mode="custom"`，或工具不在 graph 上下文执行。 | 在 `agent.stream` 中包含 `custom`；工具内用 `get_stream_writer()`。 |
| 多 Agent 输出混在一起。 | 未设置 `name` 或未开 `subgraphs=True`。 | 为每个 `create_agent` 命名，读 metadata 中的 agent 名。 |
| HITL 无法恢复。 | 无 checkpointer 或 `thread_id`。 | 与第 9 章一样配置 checkpointer + thread config。 |
| 新旧代码 chunk 形状不一致。 | 混用 v1 tuple 与 v2 StreamPart。 | 新代码统一 `version="v2"` 或直接用 v3 Event Streaming。 |

## 自检与练习

1. 为 `aggregate_tool_call_arguments` 增加“缺少 last chunk 时不返回完整调用”的测试。
2. 修改 `build_demo_stream_parts`，加入 `custom` chunk，确认 router 能单独统计 custom 条数。
3. 对比本章 `live_stream_modes_agent.py` 与第 10 章 `live_stream_events_agent.py`，各适合什么 UI 场景。
4. 说明为何 `updates` 适合观察 tool 执行完成，而 `messages` 适合观察 tool call 参数生成过程。
5. 阅读官方 Streaming 文档，列出你的项目应禁用 streaming 的内部模型类型。

## 本章小结

LangChain Streaming 页面讲的是底层 modes：`updates` 用于 Agent step 进度，`messages` 用于 LLM token 与 metadata，`custom` 用于业务进度。v2 把它们统一成 `StreamPart` dict。新应用优先 Event Streaming；理解本章有助于调试 graph、聚合 tool call chunk、组合多 mode、处理 HITL interrupt 与多 Agent 输出。Streaming 不只是打字机效果，而是运行时状态、控制流与用户体验之间的桥梁。
