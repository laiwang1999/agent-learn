# 第 10 章实践：LangChain Event Streaming

## 来源与目标

- 教材来源：[10-langchain-event-streaming.md](https://github.com/laiwang1999/agent-book-for-myself/blob/master/langchain/10-langchain-event-streaming.md)
- 官方参考：[LangChain Event streaming](https://docs.langchain.com/oss/python/langchain/event-streaming)

本章解释 Agent 运行时如何把执行过程暴露给应用和前端：`stream_events(..., version="v3")` 返回 run object，并通过 typed projections 分别提供 messages、tool_calls、values、output、subagents 等视图。完成后，你应能区分**模型生成 tool call** 与**工具实际执行**两条流，并在不调用模型的前提下验证文本增量累积、多 projection 交织消费与流式脱敏。

本章示例用本地模拟事件序列代替真实 `stream_events` 调用，不读取 API Key，也不会调用模型或网络服务。需要观察完整 Agent 流式运行时，请在本章理解 projection 语义后，再对真实 agent 使用 `agent.stream_events(input, version="v3")`。

## 必须掌握

1. **Projection 是同一事件流的不同视图**：`stream.messages` 看模型输出，`stream.tool_calls` 看工具执行生命周期，`stream.values` 看 state 快照。见 [demo_event_run.py](../../../src/agent_learn/frameworks/langchain/10-event-streaming/demo_event_run.py)。
2. **文本增量与最终状态分离**：`message.text` 提供打字机效果，`stream.output` 提供运行结束后的最终 state。见 [projection_consumers.py](../../../src/agent_learn/frameworks/langchain/10-event-streaming/projection_consumers.py)。
3. **两条 tool 相关 projection**：`message.tool_calls` 表示模型正在生成调用参数；`stream.tool_calls` 表示系统实际执行与结果。见 [projection_consumers.py](../../../src/agent_learn/frameworks/langchain/10-event-streaming/projection_consumers.py)。
4. **多视图同时消费**：异步可用 `asyncio.gather`；同步可用 `interleave` 合并顺序流。见 [interleave_projections.py](../../../src/agent_learn/frameworks/langchain/10-event-streaming/interleave_projections.py)。
5. **流式脱敏必须在事件离开 run 前完成**：`after_model` _state 级清理对 live reader 可能太晚。见 [stream_redaction.py](../../../src/agent_learn/frameworks/langchain/10-event-streaming/stream_redaction.py)。

## Event Streaming 在系统中的位置

```text
Agent 运行产生底层 protocol events
stream_events(version="v3") 暴露 typed projections
前端/日志/监控分别消费 messages、tool_calls、values、output
自定义 transformer 通过 stream.extensions 扩展业务事件
PII guardrail 在 wire output 前脱敏
```

第 9 章讲 thread state 如何保存；本章讲运行过程中如何**实时观察** state、messages、tool calls 与嵌套 runs。

## 运行

在项目根目录执行：

```powershell
pip install -e ".[dev]"
python src/agent_learn/frameworks/langchain/10-event-streaming/demo_event_run.py
python src/agent_learn/frameworks/langchain/10-event-streaming/projection_consumers.py
python src/agent_learn/frameworks/langchain/10-event-streaming/interleave_projections.py
python src/agent_learn/frameworks/langchain/10-event-streaming/stream_redaction.py
pytest tests/test_event_streaming.py
```

以上命令不需要 `.env`，也不产生外部副作用。

接入真实 Agent 时的最小模式：

```python
stream = agent.stream_events(
    {"messages": [{"role": "user", "content": "旧金山天气如何？"}]},
    version="v3",
)
for message in stream.messages:
    for delta in message.text:
        print(delta, end="", flush=True)
final_state = stream.output
```

## 工程判断

| 场景 | 推荐做法 | 不应依赖 |
| --- | --- | --- |
| 聊天 UI 打字机效果 | `stream.messages` + `message.text`。 | 只等最终 `invoke` 结果。 |
| 工具步骤面板 | 同时消费 `message.tool_calls` 与 `stream.tool_calls`。 | 从最终自然语言里猜工具动作。 |
| 调试 state 增长 | `stream.values`（内部面板）。 | 无脱敏地直接暴露给终端用户。 |
| 子 Agent UI | 命名 `create_agent(name=...)`，读 `stream.subagents`。 | 把所有 token 混成一条流。 |
| 多区域前端 | 各 projection 独立消费。 | 强行只解析 raw protocol events。 |
| 含 PII 的 live stream | wire output 前 redact。 | 只在 `after_model` 或事后日志里清理。 |

## 常见失败模式

| 现象 | 原因 | 处理方式 |
| --- | --- | --- |
| 前端只看到最后一句回答。 | 只读取 `stream.output`，未消费增量 projection。 | 为 UI 单独订阅 `stream.messages` 与 `stream.tool_calls`。 |
| 工具面板与模型请求不同步。 | 只观察 `message.tool_calls` 或只观察 `stream.tool_calls`。 | 两条 projection 分别展示“模型想调用什么”和“系统执行了什么”。 |
| 调试面板泄露邮箱、手机号。 | 直接转发 `stream.values` 或 tool output。 | 在事件离开 run 前做 PII redaction。 |
| 子 Agent 输出难以归属。 | 未给子 Agent 设置 `name`，或未使用 `stream.subagents`。 | 为每个 `create_agent` 命名并单独消费子流。 |
| 自定义业务进度只能打日志。 | 未使用 stream transformer / `stream.extensions`。 | 把检索、上传等步骤注册为 typed extension。 |
| 多 projection 消费顺序混乱。 | 手写轮询多个迭代器。 | 简单 CLI 用 `interleave`；复杂前端分通道订阅。 |

## 自检与练习

1. 为 `accumulate_text_deltas` 增加空列表与单字符增量的测试。
2. 修改 `build_demo_weather_run`，让工具执行失败，观察 `tool_execution` projection 如何表达 `error`。
3. 用 `interleave_projection_streams` 打印 messages 与 tool_calls 的交错顺序，说明为何 UI 常分通道而不是单通道。
4. 比较 `redact_stream_payload` 处理前后的 tool output，说明为何 live streaming 需要 wire-level guardrail。
5. 阅读官方 Event streaming 文档，列出你的前端需要哪三个 projection，并说明各自展示区域。

## 本章小结

LangChain Event Streaming 推荐 `stream_events(..., version="v3")`，通过 typed projections 把 Agent 运行拆成可消费视图：`messages` 承载模型文本与 reasoning，`message.tool_calls` 与 `stream.tool_calls` 分别对应模型请求与工具执行，`values` 与 `output` 承载 state 快照与最终结果，`subagents` / `subgraphs` 承载嵌套运行，`extensions` 承载自定义业务事件。它的价值是让应用不必解析底层 stream tuple，同时提醒生产环境：tool output 与 state snapshots 可能含敏感信息，必须在事件离开 run 前脱敏。
