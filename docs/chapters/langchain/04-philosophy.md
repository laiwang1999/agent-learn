# 第 4 章实践：LangChain Philosophy

## 来源与学习目标

- 教材来源：[LangChain Philosophy](https://github.com/laiwang1999/agent-book-for-myself/blob/master/langchain/04-langchain-philosophy.md)
- 官方参考：[LangChain Philosophy](https://docs.langchain.com/oss/python/langchain/philosophy)

本章不学习某个单独 API，而是理解 LangChain 为什么从早期的 Chains 演进为今天以 `create_agent`、tools、LangGraph 和 LangSmith 为核心的生态。完成后应能解释每个框架层的职责，并为一个新任务选择合适的抽象层。

## 本章交付判断

本章只交付 Markdown，不创建代码目录或示例。原因是它讨论框架理念、历史演进和工程选型，没有需要通过运行代码验证的新行为。后续 Agents、Models、Tools、Memory、LangGraph 等章节会分别对这里提到的 API 和运行时能力提供可运行示例。

## 必须掌握

### 1. LangChain 的核心目标存在张力

LangChain 同时追求三件事：容易开始、保持灵活、能够生产使用。这三个目标不能只靠一个高级封装完成，因此形成了分层的生态。

| 目标 | 对开发者的含义 | 对应能力 |
| --- | --- | --- |
| 容易开始 | 用较少配置跑通 Agent。 | `create_agent`、统一模型接口、tools。 |
| 保持灵活 | 按业务控制工具、提示词、middleware 与状态。 | LangChain 的可组合 Agent harness。 |
| 生产可用 | 处理状态、恢复、观测、评估与人工介入。 | LangGraph、LangSmith。 |

不要把“容易上手”误解为“生产问题已经被框架自动解决”。Agent 的可靠性、权限和可观测性仍需要工程设计。

### 2. 模型标准化减少 Provider Lock-in，但不消除差异

不同 provider 在 message 格式、tool calling、streaming、多模态内容、reasoning blocks、上下文限制、价格与限流方面存在差异。LangChain 的标准接口降低迁移成本，让业务代码不必被某一个 provider 的输入输出形状锁定。

标准化不是抹平差异。更换模型前仍需验证：

- 是否支持所需的 tool calling 与 structured output。
- message content 的语义是否一致。
- timeout、rate limit、token 上限和成本是否满足任务。
- provider 特有的输出内容是否需要保留。

## 3. 模型负责决策，工具与工作流负责确定性执行

LangChain 的第二个重点是让模型能够编排外部数据和计算。模型适合根据上下文判断是否调用工具、选择工具和组织结果；精确计算、检索、数据写入、权限校验和不可逆动作应由 tools 或明确 workflow 承担。

这条分工能避免两类常见问题：

| 错误做法 | 风险 | 正确方向 |
| --- | --- | --- |
| 让模型猜测统计值、行号或数据库状态 | 输出流畅但不可验证。 | 提供确定性查询或计算工具。 |
| 把全部流程塞进一个 prompt | 难以控制分支、重试、状态和人工审核。 | 按复杂度引入 tools、middleware 或 LangGraph。 |

### 4. 从 Chains 到 Agent，再到 Graph

LangChain 的演进反映了 LLM 应用复杂度的变化：

```text
固定 Chains
  -> 模型决定工具调用的 Agents
  -> 需要状态、恢复、分支与人工介入的 LangGraph runtime
  -> 提供规划、文件系统与 subagents 默认能力的 Deep Agents
```

早期 Chains 适合固定顺序，例如“检索 -> 构造 prompt -> 生成回答”。当下一步需要依赖工具结果、需要循环或失败恢复时，固定链式流程就不够了。LangGraph 补充的是低层 orchestration，而不是与 LangChain 相互替代。

### 5. 四个层次的职责

| 层次 | 主要职责 | 适用信号 |
| --- | --- | --- |
| LangChain | Agent harness、模型、消息、tools、middleware。 | 需要快速构建且保留细粒度控制。 |
| LangGraph | 显式状态图、checkpoint、streaming、interrupt、持久执行。 | 流程有分支、循环、暂停恢复或人工审核。 |
| Deep Agents | planning、filesystem、sandbox、subagents、context management。 | 需要开箱即用的长任务或研究/编码能力。 |
| LangSmith | tracing、observability、evals。 | 需要解释 Agent 行为、评估质量、定位成本和延迟问题。 |

选择高层框架不是默认最优解。任务只需要一个受控工具调用时，先使用 LangChain；只有明确需要更复杂运行时或默认能力时，再下探 LangGraph 或使用 Deep Agents。

### 6. 历史中的关键工程变化

不必死记日期，但要理解以下变化带来的设计影响：

| 演进 | 解决的问题 | 今天的学习结论 |
| --- | --- | --- |
| string 输入输出变为 message list | 对话角色与 tool result 无法可靠地用字符串拼接表达。 | 将 messages 视为 Agent 状态的一部分。 |
| 文本 JSON 解析变为 provider 原生 tool calling | 模型生成的 JSON 容易格式错误。 | 依赖 typed tool schema，并处理 provider 差异。 |
| LangSmith 出现 | 行为偏差不能只靠异常栈定位。 | 从开发早期就观察 trace、工具参数、延迟与成本。 |
| LangGraph 出现 | 高层 Agent 不足以表达复杂状态和执行控制。 | 将持久化、恢复、分支和 HITL 视为运行时能力。 |
| integrations 拆包 | 核心包不应携带所有 provider SDK。 | 按使用场景安装 `langchain-openai` 等集成包。 |
| v1.0 收束高层 Agent abstraction | 旧 Chains 与 Agents 难以持续承载当前模型 API。 | 新项目优先学习 `create_agent` 和 LangGraph runtime。 |

## 架构决策清单

开始一个 Agent 任务前，依次回答：

1. 任务是固定步骤，还是模型需要根据结果动态决定下一步？
2. 是否存在必须由确定性代码完成的计算、校验或副作用？
3. 是否需要持久状态、分支、重试、暂停恢复或 human-in-the-loop？
4. 是否需要 planning、文件系统和 subagents 这类长任务默认能力？
5. 如何通过 tracing 和 evals 验证工具调用与最终结论？

前两个问题通常决定是否需要 Agent 和 tools；第三个问题决定是否需要 LangGraph；第四个问题决定是否评估 Deep Agents；第五个问题决定可观测性如何进入开发流程。

## 常见误区

| 误区 | 纠正 |
| --- | --- |
| LangChain 能屏蔽所有 provider 差异。 | 它只提供标准接口；能力、限制和成本仍需逐项验证。 |
| Agent 是普通聊天模型加一个很长的 prompt。 | Agent 还需要工具契约、状态、失败处理、权限与可观测性。 |
| LangGraph 是 LangChain 的替代品。 | LangChain 提供高层构建入口，LangGraph 提供低层 orchestration。 |
| Deep Agents 总比 LangChain 更适合。 | Deep Agents 提供更多默认能力，也带来更多默认行为；按任务需求选择。 |
| 能跑通 demo 就等于可以生产。 | 生产还需要 tracing、evals、权限边界、幂等、持久化和故障恢复。 |

## 自检与练习

1. 为一个“从知识库回答问题”的需求画出固定 workflow；再说明什么需求变化会使它需要 Agent。
2. 选择一个当前模型 provider，列出切换到另一 provider 前必须重新验证的四项能力。
3. 设计一个包含“发送邮件”的 tool，说明哪些控制属于 tool、LangGraph、human-in-the-loop 和 LangSmith。
4. 为一个长文档研究任务比较 LangChain、LangGraph 与 Deep Agents 的起步方案，并写出选择理由。

## 本章小结

LangChain 的核心方向是：降低构建 LLM 应用的起步成本，同时保留通向生产工程的控制力。它通过标准模型接口处理 provider 迁移，通过 tools 连接外部数据和计算，通过 LangGraph 管理复杂运行时，通过 LangSmith 观察和评估行为；Deep Agents 则提供更完整的长任务默认能力。

理解这套分层后，后续章节不应被看成零散 API：Models 解决模型接入，Tools 解决外部能力，Messages 解决状态表达，Memory 和 LangGraph 解决运行时，Observability 解决可靠性。
