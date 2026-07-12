# 第 14 章实践：LangChain Prebuilt Middleware

## 来源与目标

- 教材来源：[14-langchain-middleware-built-in.md](https://github.com/laiwang1999/agent-book-for-myself/blob/master/langchain/14-langchain-middleware-built-in.md)
- 官方参考：[LangChain Prebuilt middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in)

本章把 LangChain 内置 Middleware 按**工程职责**重新组织：上下文管理、人类监督、预算边界、可靠性、安全合规、工具选择、开发模拟与执行环境。完成后，你应能根据风险选型，而不是把 middleware 当作功能插件清单逐个堆砌。

离线示例提供选型地图与策略纯函数；真实 Agent 示例演示 `SummarizationMiddleware` 与 `ModelCallLimitMiddleware` 的组合用法。

## 必须掌握

1. **按职责分组选型**：先识别风险，再选控制层。见 [prebuilt_middleware_catalog.py](../../../src/agent_learn/frameworks/langchain/14-middleware-built-in/prebuilt_middleware_catalog.py)。
2. **上下文管理**：`SummarizationMiddleware` 摘要历史，`ContextEditingMiddleware` 清理旧工具结果。见第 9 章 trim 与 summarization 概念。
3. **预算边界**：`ModelCallLimitMiddleware`、`ToolCallLimitMiddleware` 防止循环与成本失控。见 [limit_budget_policy.py](../../../src/agent_learn/frameworks/langchain/14-middleware-built-in/limit_budget_policy.py)。
4. **安全合规**：`PIIMiddleware` 的 block/redact/mask/hash 策略。见 [pii_strategy_selector.py](../../../src/agent_learn/frameworks/langchain/14-middleware-built-in/pii_strategy_selector.py)。
5. **真实 prebuilt 组合**：摘要 + 模型调用上限。见 [live_prebuilt_middleware_agent.py](../../../src/agent_learn/frameworks/langchain/14-middleware-built-in/live_prebuilt_middleware_agent.py)。

## Prebuilt Middleware 分层

| 职责层 | 代表 Middleware | 主要解决问题 |
| --- | --- | --- |
| 上下文管理 | `SummarizationMiddleware`、`ContextEditingMiddleware` | 长对话与膨胀的工具结果 |
| 人类监督 | `HumanInTheLoopMiddleware` | 高风险工具执行前审批 |
| 预算边界 | `ModelCallLimitMiddleware`、`ToolCallLimitMiddleware` | 调用次数与成本上限 |
| 可靠性 | `ModelFallbackMiddleware`、`ToolRetryMiddleware` | 暂时失败与降级 |
| 安全合规 | `PIIMiddleware` | PII 检测与脱敏 |
| 工具选择 | `LLMToolSelectorMiddleware` | 工具过多时的 schema 负担 |
| 开发测试 | `LLMToolEmulator` | 模拟工具返回 |
| 执行环境 | `FilesystemMiddleware`、`ShellToolMiddleware` | 文件与命令（高风险） |

## 运行

### 离线验证（不需要 API Key）

```powershell
pip install -e ".[dev]"
python src/agent_learn/frameworks/langchain/14-middleware-built-in/prebuilt_middleware_catalog.py
python src/agent_learn/frameworks/langchain/14-middleware-built-in/limit_budget_policy.py
python src/agent_learn/frameworks/langchain/14-middleware-built-in/pii_strategy_selector.py
pytest tests/test_prebuilt_middleware.py
```

### 真实 Agent（需要 `.env`）

```powershell
pip install -e ".[dev,openai]"
python src/agent_learn/frameworks/langchain/14-middleware-built-in/live_prebuilt_middleware_agent.py
```

该示例在同一 `thread_id` 下多轮调用，并挂载 `SummarizationMiddleware` 与 `ModelCallLimitMiddleware`。环境变量与第 7 章相同。

扩展阅读：第 13 章 middleware 总览；第 5 章 `context_inventory_agent.py` 中的 checkpointer 与 HITL 前置知识。

## 工程判断

| 如果你的问题是 | 优先考虑 | 不应依赖 |
| --- | --- | --- |
| 对话和工具结果太长 | `SummarizationMiddleware`、`ContextEditingMiddleware` | 无限制累积 history |
| 高风险写操作 | `HumanInTheLoopMiddleware` + checkpointer | 只在 prompt 里写“请谨慎” |
| 成本或循环不可控 | `ModelCallLimitMiddleware`、`ToolCallLimitMiddleware` | 事后人工发现账单异常 |
| 外部服务偶发失败 | `ToolRetryMiddleware`（仅幂等读） | 对支付/发信工具盲目 retry |
| 敏感信息 | `PIIMiddleware` + `apply_to_output=True`（streaming） | 只在最终回复后脱敏 |
| 工具 schema 太重 | `LLMToolSelectorMiddleware` | 一次性暴露全部工具 |
| 开发期无真实 API | `LLMToolEmulator` | 用模拟结果代替全部 E2E 测试 |

## 常见失败模式

| 现象 | 原因 | 处理方式 |
| --- | --- | --- |
| HITL 无法恢复。 | 未配置 checkpointer 或 `thread_id`。 | 与第 9 章相同，启用持久化 checkpoint。 |
| 摘要后事实失真。 | summarization 遗漏细节。 | 关键原始记录保留在外部存储；调 `keep` 与 `trigger`。 |
| 工具 retry 造成重复副作用。 | 对非幂等写操作启用 `ToolRetryMiddleware`。 | 仅对只读或幂等工具 retry。 |
| PII 仍出现在 live stream。 | 未对 wire output 脱敏。 | `PIIMiddleware(..., apply_to_output=True)`。 |
| middleware 行为难以调试。 | 一次挂载过多层。 | 按风险逐个加入并用 trace 观察。 |
| Shell 泄露敏感信息。 | 误用 `HostExecutionPolicy`。 | 默认隔离；Shell 视为高风险工具。 |

## 自检与练习

1. 为 `recommend_model_call_limit` 增加“高风险工具较多时降低 run_limit”的测试。
2. 比较 `SummarizationMiddleware` 与第 9 章 `trim_messages_for_model` 的适用边界。
3. 设计 `interrupt_on` 配置：哪些工具 approve、哪些直接执行。
4. 说明 `LLMToolEmulator` 不能替代哪些端到端测试。
5. 列出你的 Agent 需要的 3 个 prebuilt middleware 及挂载顺序。

## 本章小结

Prebuilt Middleware 把常见横切需求做成可配置部件。业务 tools 回答“能做什么”；middleware 回答“何时能做、做多少次、失败后怎么办、哪些信息不能泄露、哪些动作必须有人确认”。应从明确风险倒推选型，逐个加入并验证，而不是一次性挂满所有内置能力。
