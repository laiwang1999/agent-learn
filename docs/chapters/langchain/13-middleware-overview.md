# 第 13 章实践：LangChain Middleware Overview

## 来源与目标

- 教材来源：[13-langchain-middleware-overview.md](https://github.com/laiwang1999/agent-book-for-myself/blob/master/langchain/13-langchain-middleware-overview.md)
- 官方参考：[LangChain Middleware overview](https://docs.langchain.com/oss/python/langchain/middleware/overview)

本章是 Middleware 章节的入口：Middleware 是在 Agent loop 关键位置插入的**横切控制层**，用于 logging、动态 prompt、工具过滤、重试、guardrails、PII 脱敏与 human-in-the-loop 等。完成后，你应能说明 middleware 在 loop 中的位置、为何顺序很重要，以及 HITL 如何按 tool `.name` 匹配。

离线示例验证 concern 排序与工具名匹配；真实 Agent 示例演示 `@dynamic_prompt` 与 `@wrap_tool_call` 的组合用法。

## 必须掌握

1. **Middleware 是 harness 横切层**：不替代 model/tools/messages，而是在它们之间的路径上施加策略。见 [middleware_ordering.py](../../../src/agent_learn/frameworks/langchain/13-middleware-overview/middleware_ordering.py)。
2. **通过列表组合**：`create_agent(..., middleware=[...])`；顺序会影响安全与观测结果。见 [middleware_ordering.py](../../../src/agent_learn/frameworks/langchain/13-middleware-overview/middleware_ordering.py)。
3. **编译进 LangGraph**：middleware 运行在 `create_agent` 返回的 compiled graph 内，不是外层 wrapper。见第 5 章 `context_inventory_agent.py`。
4. **HITL 按 tool 名匹配**：`interrupt_on={"send_email": True}` 必须与 `@tool` 的 `.name` 一致。见 [hitl_tool_matching.py](../../../src/agent_learn/frameworks/langchain/13-middleware-overview/hitl_tool_matching.py)。
5. **真实 middleware 组合**：`@dynamic_prompt` 改写系统提示，`@wrap_tool_call` 统一处理工具错误。见 [live_middleware_agent.py](../../../src/agent_learn/frameworks/langchain/13-middleware-overview/live_middleware_agent.py)。

## Middleware 在 Agent Loop 中的位置

```text
准备上下文 → [before_model / dynamic_prompt] → 调用模型
  → [wrap_model_call] → 工具选择
  → [wrap_tool_call / HITL] → 执行工具 → 写回 messages
  → [after_model] → 再次调用模型 → 直到结束
```

## 运行

### 离线验证（不需要 API Key）

```powershell
pip install -e ".[dev]"
python src/agent_learn/frameworks/langchain/13-middleware-overview/middleware_ordering.py
python src/agent_learn/frameworks/langchain/13-middleware-overview/hitl_tool_matching.py
python src/agent_learn/frameworks/langchain/13-middleware-overview/dynamic_prompt_builder.py
pytest tests/test_middleware_overview.py
```

### 真实 Agent（需要 `.env`）

```powershell
pip install -e ".[dev,openai]"
python src/agent_learn/frameworks/langchain/13-middleware-overview/live_middleware_agent.py
```

环境变量与第 7 章相同。该示例会根据 `RuntimeContext` 动态生成 system prompt，并用 `wrap_tool_call` 把工具异常转成可恢复的 `ToolMessage`。

扩展阅读：第 5 章 [`context_inventory_agent.py`](../../../src/agent_learn/frameworks/langchain/05-agents/context_inventory_agent.py) 演示 `context_schema` + `@dynamic_prompt` + checkpointer 的完整权限边界。

## 工程判断

| 场景 | 推荐做法 | 不应依赖 |
| --- | --- | --- |
| 权限与 PII | 安全类 middleware 靠前；脱敏早于日志外发。 | 只在 system prompt 里写“不要泄露数据”。 |
| 动态 system prompt | `@dynamic_prompt` 读取 `runtime.context`。 | 把租户身份写进用户消息。 |
| 工具错误恢复 | `@wrap_tool_call` 返回 `ToolMessage`。 | 在每个 tool 里重复 try/except。 |
| HITL 审批 | `HumanInTheLoopMiddleware(interrupt_on={tool_name: True})`。 | 用与 `.name` 不一致的字符串。 |
| 嵌入更大 StateGraph | 整个 agent（含 middleware）作为 node/subgraph。 | 剥掉 middleware 再塞进 graph。 |
| 一个巨大 middleware | 每个 middleware 只处理一个 concern。 | 把日志、权限、重试、脱敏写进同一个类。 |

## 常见失败模式

| 现象 | 原因 | 处理方式 |
| --- | --- | --- |
| HITL 未拦截高风险工具。 | `interrupt_on` 的 key 与 tool `.name` 不一致。 | 用 `tool.name` 做 key；为高风险工具写测试。 |
| 日志里出现明文 PII。 | 先写日志后脱敏。 | 调整 middleware 顺序，脱敏早于外发。 |
| 无权限用户仍能调用写操作工具。 | 只靠 prompt 约束。 | 用 tool filtering 或 `wrap_tool_call` 确定性拒绝。 |
| 子 Agent 记忆混乱。 | subgraph checkpoint scope 未明确。 | 区分 per-invocation 与 per-thread。 |
| middleware 行为难以解释。 | 缺少 trace 或步骤日志。 | 为关键 middleware 增加可观测事件。 |

## 自检与练习

1. 为 `sort_middleware_by_priority` 增加一个测试：PII redaction 必须排在 logging 之前。
2. 构造自定义 `@tool("send_notification")` 名称，验证 `should_interrupt_tool` 的匹配逻辑。
3. 阅读第 5 章 `build_permission_prompt`，说明它为何属于 middleware 而不是普通 helper。
4. 设计一个仅包含 `SummarizationMiddleware` 与 `HumanInTheLoopMiddleware` 的 middleware 列表，并解释顺序影响。
5. 说明何时应把 agent 嵌入更大的 `StateGraph`，而不是扩展单个 agent 的 prompt。

## 本章小结

Middleware 是在 Agent loop 中控制和定制执行过程的机制，编译进 `create_agent` 返回的 LangGraph。它可组合用于 prompt 变换、工具选择、错误处理、guardrails、PII 与 HITL；顺序要明确，安全策略应确定性执行。Agent 可作为 node 嵌入更大 workflow 时，middleware 会随 agent 一起运行。Middleware 是从“能跑的 Agent”走向“可控的 Agent”的关键步骤。
