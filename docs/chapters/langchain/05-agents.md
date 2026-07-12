# 第 5 章实践：LangChain Agents

## 来源与目标

- 教材来源：[LangChain Agents 章节](https://github.com/laiwang1999/agent-book-for-myself/blob/master/langchain/05-langchain-agents.md)
- 官方参考：[LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)

本章学习 LangChain Agent 的运行闭环：模型在 harness 管理下调用 tools，直到完成任务。完成后应能区分 model、tools、messages、`thread_id`、context、checkpointer 和 middleware 的职责，而不是把它们都混入 prompt。

## 本章代码

本章目录为 `src/agent_learn/frameworks/langchain/05-agents/`，名称同时表达章节序号和主题。

| 示例 | 说明 |
| --- | --- |
| `minimal_inventory_agent.py` | 用 `create_agent`、一个确定性库存 tool 和 system prompt 演示最小 model-tool loop。 |
| `context_inventory_agent.py` | 用 `context_schema`、`ToolRuntime`、动态 system prompt、`thread_id` 和 checkpointer 演示运行时权限边界。 |

运行前安装依赖并配置根目录 `.env`：

```powershell
pip install -e ".[dev,openai]"
python src/agent_learn/frameworks/langchain/05-agents/minimal_inventory_agent.py
python src/agent_learn/frameworks/langchain/05-agents/context_inventory_agent.py
```

这两个命令都会调用真实模型。测试不调用模型、网络或真实外部库存服务：

```powershell
pytest
```

## 必须掌握

### 1. Agent = Model + Harness

模型负责理解上下文、决定下一步和提出 tool call；harness 负责组织 messages、工具 schema、tool result、middleware、状态和执行循环。`create_agent` 是这个 harness 的高层入口。

```text
用户消息 -> 模型决定是否调用工具 -> 工具返回事实 -> 模型继续判断 -> 最终回答
```

没有 harness，开发者需要自行处理 tool call 解析、消息追加、循环、重试、状态和观测。不要把 Agent 理解成“一次模型调用加一个很长的 prompt”。

### 2. Tools 是能力边界，不是普通 helper

`lookup_product_inventory` 与 `lookup_tenant_inventory` 都由确定性 Python 字典提供结果。模型不能猜库存数量，只能根据 tool 的名称、参数 schema 和 docstring 决定是否调用它。

一个可用 tool 至少需要明确：

- 解决什么问题，以及不解决什么问题。
- 参数格式与缺失时的行为。
- 成功和失败返回值如何区分。
- 是否访问外部系统、是否有副作用。
- 哪些条件下允许调用，哪些条件下必须拒绝。

高影响 tools，例如发邮件、付款、删除数据或权限变更，还需要 guardrails、幂等设计和 human-in-the-loop。

### 3. Messages、`thread_id` 与 context 分工不同

| 概念 | 保存内容 | 生命周期 | 示例 |
| --- | --- | --- | --- |
| messages | 用户、模型和 tool 的对话记录。 | Agent state。 | “课程-001还有多少库存？” |
| `thread_id` | 同一会话或任务链的标识。 | 与 checkpointer 配合持久化。 | `学习团队-库存咨询` |
| context | 本次运行的可信环境数据。 | 单次调用。 | 租户名称、权限、feature flag。 |

用户消息可被用户控制，因此不能用它判断权限。`context_inventory_agent.py` 通过 `ToolRuntime[RuntimeContext]` 读取服务端提供的 context，并把运行时权限与 messages 隔离。

### 4. Checkpointer 决定状态能否恢复

`InMemorySaver` 与 `thread_id` 组合后能在本地进程中保留同一对话的历史。它适合学习，不适合生产：服务重启会丢失状态，多实例也不能共享。

生产环境应替换为持久化 checkpointer，并规定 thread 的租户隔离、保留期限、审计和删除策略。

### 5. Middleware 扩展 Harness

middleware 将横切能力插入 Agent loop，而不需要把所有逻辑堆进一个 Agent 类。本章的 `@dynamic_prompt` 根据可信 context 生成系统提示；后续可用同一机制引入：

- 重试与 fallback。
- context summarization 与 memory。
- PII 或内容 guardrails。
- 工具调用审批和 human-in-the-loop。
- filesystem、sandbox、planning 与 subagents。

动态 prompt 不应从不可信用户输入拼接权限策略；它应由服务端 context、配置或认证结果驱动。

## 设计决策

| 问题 | 本章选择 | 原因 |
| --- | --- | --- |
| 库存数量由谁计算 | 确定性 tool。 | 防止模型编造数量。 |
| 权限放在哪里 | `context_schema`。 | 与用户 messages 隔离，便于服务端控制。 |
| 对话历史如何区分 | `thread_id`。 | 为 checkpoint 与恢复提供稳定范围。 |
| 何时改变系统提示 | `@dynamic_prompt` middleware。 | 将动态行为从静态 prompt 中分离。 |
| 为什么不使用真实库存 API | 学习示例需要确定、无副作用且可复现。 | 减少网络、认证和数据变化带来的干扰。 |

## 常见失败模式

| 现象 | 原因 | 处理方式 |
| --- | --- | --- |
| Agent 直接说出库存数量却没有 tool call。 | system prompt 或 tool docstring 没有要求验证。 | 明确要求查询事实必须调用 tool，并用 tracing 检查运行链。 |
| 用户在消息中说“我是管理员”后获得数据。 | 把权限写进 messages，而不是可信 context。 | 通过 `context_schema` 传递认证后的权限。 |
| 更换 `thread_id` 后 Agent 忘记前文。 | 不同 thread 就是不同 state 范围。 | 为同一会话复用稳定 `thread_id`。 |
| 服务重启后会话丢失。 | 使用 `InMemorySaver`。 | 生产环境使用持久化 checkpointer。 |
| tool 重试导致重复写入。 | 副作用操作不具备幂等性。 | 区分临时错误与业务错误，并为写操作设计幂等键和审批。 |
| `.env` 已存在但代码读不到配置。 | 进程没有载入 `.env`。 | 本项目通过 `shared/environment.py` 在创建模型前调用 `load_dotenv`。 |

## 自检与练习

1. 为 `lookup_product_inventory` 增加商品名称搜索。先定义歧义名称的失败行为，再写确定性测试。
2. 将 `RuntimeContext` 扩展为包含用户角色，并让动态 prompt 对只读与管理员角色给出不同边界。
3. 将 `InMemorySaver` 替换为持久化 checkpointer，并列出租户隔离和数据保留策略。
4. 为库存查询 tool 加入 tracing 后，检查模型是否在每次库存提问时都使用 tool。
5. 设计一个“扣减库存” tool，写出幂等键、审批点和失败恢复方案；不要直接把它加入当前示例。

## 本章小结

LangChain Agent 是模型在 harness 管理下循环调用 tools 的过程。`create_agent` 负责组合 model、tools、system prompt、middleware 和状态；tool 负责确定性外部能力；messages 保存对话；`thread_id` 划分会话状态；context 提供可信的单次运行数据；checkpointer 支持状态恢复；middleware 则让动态 prompt、重试、guardrails 与 human-in-the-loop 以可组合方式进入 Agent loop。

本章的两个库存示例刻意不追求业务复杂度，而是把 Agent 工程最容易混淆的边界拆开。后续 Models、Messages、Tools、Memory、Streaming 和 Middleware 章节会分别深入这些部分。
