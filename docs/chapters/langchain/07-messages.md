# 第 7 章实践：LangChain Messages

## 来源与目标

- 教材来源：[07-langchain-messages.md](https://github.com/laiwang1999/agent-book-for-myself/blob/master/langchain/07-langchain-messages.md)
- 官方参考：[LangChain Messages](https://docs.langchain.com/oss/python/langchain/messages)

本章把 Message 当作 Agent 上下文的基本数据结构，而不是单纯的聊天文本。完成后，你应能构造稳定的 `SystemMessage`、`HumanMessage`、`AIMessage` 与 `ToolMessage`，并验证工具结果是否准确回写到对应的 tool call。

本章两个示例都只创建本地 Message 对象，不读取 API Key，也不会调用模型或网络服务。这样可以先把上下文契约、工具调用 ID 和消息顺序验证清楚，再接入真实 provider。

## 必须掌握

1. **角色、内容与元数据**：`SystemMessage` 放稳定行为边界，`HumanMessage` 表示用户输入，`AIMessage` 保存模型回答与运行信息。见 [message_basics.py](../../../src/agent_learn/frameworks/langchain/07-messages/message_basics.py)。
2. **消息历史是有序上下文**：Chat Model 通常是无状态的；每次调用都要传入需要保留的 message list。不要把权限、租户身份等可信服务端数据伪装成用户消息。
3. **工具调用闭环**：模型请求工具时，`AIMessage.tool_calls` 中的 `id` 必须由 `ToolMessage.tool_call_id` 原样回应。见 [tool_message_flow.py](../../../src/agent_learn/frameworks/langchain/07-messages/tool_message_flow.py)。
4. **`content` 与 `artifact` 的边界**：`ToolMessage.content` 是送回模型的紧凑结果；`artifact` 保存 UI、审计或调试需要而不应加入模型上下文的原始数据。
5. **消息元数据不可当作权限边界**：`name`、`id`、`response_metadata` 与 `usage_metadata` 有助于追踪和成本观测，但身份认证、授权与租户隔离必须由应用层或 middleware 保证。

## 消息关系

```text
SystemMessage + HumanMessage
          |
          v
 AIMessage.tool_calls[{id: "call_course_inventory_001"}]
          |
          v
 ToolMessage.tool_call_id == "call_course_inventory_001"
          |
          v
      后续 AIMessage 中文答复
```

`ToolMessage` 的 `tool_call_id` 不匹配时，模型无法可靠判断哪个结果对应哪个行动请求。多个 tool call 时尤其不能按数组位置“猜测”对应关系。

## 运行

在项目根目录执行：

```powershell
uv run python src/agent_learn/frameworks/langchain/07-messages/message_basics.py
uv run python src/agent_learn/frameworks/langchain/07-messages/tool_message_flow.py
uv run pytest tests/test_message_flow.py
```

第一个示例打印每条消息的 `type`、`id` 和文本内容；第二个示例打印完整的“用户请求 -> 模型工具请求 -> 工具结果 -> 中文答复”序列。它们不需要 `.env`，也不产生外部副作用。

接入真实模型时，使用第 6 章的 [chat_model_factory.py](../../../src/agent_learn/frameworks/langchain/chat_model_factory.py) 创建模型，并把本章构造的 message list 传给 `model.invoke(messages)`。模型提示词、用户问题和最终 AI 答复都应保持中文。

## 工程判断

| 场景 | 推荐做法 | 不应依赖 |
| --- | --- | --- |
| 一次性、无历史的简单请求 | 可以传字符串给 `model.invoke`。 | 把字符串方式扩展成复杂 Agent state。 |
| 多轮对话或 Agent | 显式维护 `list[BaseMessage]`。 | 只保存最终回答文本。 |
| 客户端执行业务工具 | 逐一执行 `AIMessage.tool_calls`，再按 ID 创建 `ToolMessage`。 | 用自然语言描述代替 `tool_call_id`。 |
| 工具返回大量原始数据 | 将模型所需摘要放入 `content`，将完整数据放入 `artifact` 或受控存储。 | 把完整内部记录无边界塞入上下文。 |
| 流式输出 | 累加 `AIMessageChunk`，等待工具参数完整后再执行。 | 假设单个 chunk 就是完整 JSON。 |
| 多模态或跨 provider | 优先读取 `content_blocks` 的标准化视图，并检查目标模型能力。 | 假设所有 provider 接受相同原始 `content` 格式。 |

## 常见失败模式

| 现象 | 原因 | 处理方式 |
| --- | --- | --- |
| 模型忽略工具结果或重复调用工具。 | `ToolMessage.tool_call_id` 与请求 ID 不匹配，或结果没有追加到原消息序列。 | 以 tool call 的 `id` 为唯一关联键；在发送下一次模型调用前做断言。 |
| 多轮对话表现突然失忆。 | 每轮只传入最新 `HumanMessage`，没有传入历史。 | 明确维护 history，或使用 Agent/short-term memory 的受控 state。 |
| 成本和延迟不断升高。 | history 与工具返回持续增长。 | 记录 `usage_metadata`，再设计 trimming、summarization 和 token 预算。 |
| 模型看到了不该看的内部数据。 | 将完整工具响应、权限信息或审计记录写进 `content`。 | 缩减 `content`；把非模型所需数据留在 `artifact`、context 或服务端存储。 |
| 切换 provider 后多模态解析失败。 | 直接依赖 provider-native `content` 格式。 | 检查 provider 文档，优先采用 LangChain 标准 `content_blocks`。 |

## 自检与练习

1. 先为 `has_matching_tool_result` 写一个“两个 tool call，只有一个结果”的测试，再实现对所有调用结果的完整性校验。
2. 为工具结果增加 `source` 和 `observed_at` 字段，讨论哪些字段应进入 `content`，哪些应仅保留在 `artifact`。
3. 将 `build_message_history` 接到第 6 章模型调用示例，观察 `AIMessage.usage_metadata` 的变化；不要在测试中发起真实模型请求。
4. 使用 `AIMessageChunk` 模拟三个片段，验证累加后文本顺序正确，并说明为何工具参数未完成时不能执行工具。

## 本章小结

Messages 是 LangChain Agent 的上下文契约。`SystemMessage` 定义稳定边界，`HumanMessage` 承载用户输入，`AIMessage` 记录模型回答和行动请求，`ToolMessage` 则以精确的 `tool_call_id` 回写工具执行结果。先把消息的角色、顺序和关联关系做成可测试的本地逻辑，后续的 tools、memory、streaming、middleware 和 tracing 才有可靠基础。
