# 第 9 章实践：LangChain Short-term Memory

## 来源与目标

- 教材来源：[09-langchain-short-term-memory.md](https://github.com/laiwang1999/agent-book-for-myself/blob/master/langchain/09-langchain-short-term-memory.md)
- 官方参考：[LangChain Short-term memory](https://docs.langchain.com/oss/python/langchain/short-term-memory)

本章解释 Agent 如何在**单个 thread** 内保持上下文：checkpointer 保存 state、`thread_id` 隔离不同会话、默认 `AgentState.messages` 承载对话历史，以及历史过长时的 trim、delete、summarize 策略。完成后，你应能区分 short-term memory 与 long-term memory 的边界，并在不调用模型的前提下验证 thread 隔离、消息裁剪与历史合法性。

本章示例使用进程内演示存储和纯函数，不读取 API Key，也不会调用模型或网络服务。需要观察完整 Agent + checkpointer 行为时，可结合第 5 章的 `context_inventory_agent.py`。

## 必须掌握

1. **Thread 是隔离单位**：同一 `thread_id` 共享 state，不同 thread 互不影响。见 [thread_memory_store.py](../../../src/agent_learn/frameworks/langchain/09-short-term-memory/thread_memory_store.py)。
2. **Checkpointer 持久化 thread state**：`InMemorySaver` 适合本地学习；生产应使用 Postgres 等数据库-backed checkpointer。见第 5 章 `context_inventory_agent.py`。
3. **默认 state 以 messages 为核心**：`AgentState.messages` 保存 System/Human/AI/Tool 消息序列，是短期记忆的主体。
4. **自定义 state 字段**：通过 `state_schema` 扩展 thread 级字段，例如任务阶段、表单进度或临时偏好。见 [custom_thread_state.py](../../../src/agent_learn/frameworks/langchain/09-short-term-memory/custom_thread_state.py)。
5. **历史管理策略**：trim 控制模型可见上下文，delete 永久移除 state 中的消息，summarize 用摘要替代早期历史；裁剪后必须保持 message 合法性。见 [message_trim_strategy.py](../../../src/agent_learn/frameworks/langchain/09-short-term-memory/message_trim_strategy.py) 与 [message_history_validator.py](../../../src/agent_learn/frameworks/langchain/09-short-term-memory/message_history_validator.py)。

## 短期记忆在系统中的位置

```text
thread_id 划定会话边界
checkpointer 在每个 step 读写 thread state
AgentState.messages 保存对话历史
middleware（before_model / after_model）在模型前后整理 memory
tools 通过 ToolRuntime.state 读取或 Command 写入 state
```

第 7 章讲 messages，第 8 章讲 tools。本章说明它们如何在同一 thread 中形成**连续状态**，而不是让模型“神秘地记住一切”。

## 运行

在项目根目录执行：

```powershell
pip install -e ".[dev]"
python src/agent_learn/frameworks/langchain/09-short-term-memory/thread_memory_store.py
python src/agent_learn/frameworks/langchain/09-short-term-memory/custom_thread_state.py
python src/agent_learn/frameworks/langchain/09-short-term-memory/message_trim_strategy.py
python src/agent_learn/frameworks/langchain/09-short-term-memory/message_history_validator.py
pytest tests/test_short_term_memory.py
```

以上命令不需要 `.env`，也不产生外部副作用。

接入真实 Agent 时，为 `create_agent` 传入 `checkpointer=InMemorySaver()`（或生产级 checkpointer），并在每次 `invoke` 时传入 `config={"configurable": {"thread_id": "..."}}`。

## 工程判断

| 场景 | 推荐做法 | 不应依赖 |
| --- | --- | --- |
| 本地学习与单元测试 | `InMemorySaver` + 明确 `thread_id`。 | 把它当作生产持久化方案。 |
| 生产多实例部署 | Postgres / SQLite 等持久化 checkpointer。 | 进程内字典或未共享的内存状态。 |
| 长对话成本控制 | trim 或 summarize + 保留近期原始消息。 | 无限制累积完整 history。 |
| 删除敏感消息 | `RemoveMessage` + 合法性校验。 | 随意删除 ToolMessage 却保留 tool_calls。 |
| 跨会话用户偏好 | long-term store 或数据库。 | 把所有长期信息塞进 short-term state。 |
| 工具读取当前任务进度 | `runtime.state` 自定义字段。 | 让模型在参数里自行提供 user_id。 |

## 常见失败模式

| 现象 | 原因 | 处理方式 |
| --- | --- | --- |
| 第二轮对话“失忆”。 | 未传 `checkpointer`，或 `thread_id` 每次不同。 | 创建 agent 时配置 checkpointer；同一会话复用 `thread_id`。 |
| 服务重启后会话丢失。 | 使用 `InMemorySaver` 且无外部持久化。 | 换成数据库-backed checkpointer。 |
| 不同用户看到彼此对话。 | `thread_id` 未按用户或会话隔离。 | 用认证后的会话标识生成 `thread_id`，并校验访问权限。 |
| trim 后模型报错或忽略工具结果。 | 删除了 ToolMessage 却保留对应 `AIMessage.tool_calls`。 | 裁剪后用 validator 检查配对关系；优先按 token 预算而非盲删条数。 |
| 摘要后事实逐渐失真。 | summarize 遗漏细节或引入偏差。 | 关键原始记录保留在外部存储，只把摘要放进模型上下文。 |
| state 越来越大、成本飙升。 | 工具返回大量原始数据写入 `messages`。 | 缩减 `ToolMessage.content`；完整数据放 artifact 或 store。 |

## 自检与练习

1. 为 `trim_messages_for_model` 写一个测试：历史超过阈值时保留首条 SystemMessage 和最近 N 条。
2. 构造“有 tool call 但缺少 ToolMessage”的历史，确认 `validate_message_history` 返回失败。
3. 比较 `thread-1` 与 `thread-2` 的 state，说明为何 Bob 的名字不会泄漏到另一个 thread。
4. 阅读第 5 章 `context_inventory_agent.py`，指出 `thread_id`、`checkpointer` 与 `RuntimeContext` 各自职责。
5. 设计一个 `task_stage` 自定义 state 字段，说明它应放在 short-term 还是 long-term memory。

## 本章小结

Short-term memory 让 LangChain Agent 在单个 thread 中保持上下文。启用方式是传入 checkpointer 与 `thread_id`；默认 `AgentState.messages` 保存对话历史，也可用 `state_schema` 扩展 thread 级字段。核心挑战是 history 会不断增长，带来成本、延迟、窗口溢出和注意力干扰，因此需要 trim、delete、summarize 或自定义策略，并始终保证 message 历史合法。工具通过 `ToolRuntime.state` 读取 memory，middleware 在模型调用前后整理 memory；跨 thread 的长期信息应使用 long-term store，而不是无限膨胀短期 state。
