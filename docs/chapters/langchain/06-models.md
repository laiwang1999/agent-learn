# 第 6 章实践：LangChain Models

## 来源与目标

- 教材来源：[LangChain Models 章节](https://github.com/laiwang1999/agent-book-for-myself/blob/master/langchain/06-langchain-models.md)
- 官方参考：[LangChain Models](https://docs.langchain.com/oss/python/langchain/models)

模型是 Agent 的推理引擎：它理解消息、决定是否请求 tool、解释 tool result 并组织最终答复。完成本章后，应能用统一模型接口进行调用，理解 provider 差异，并为结构化输出、成本、重试和模型选择设计明确边界。

## 本章代码

本章目录为 `src/agent_learn/frameworks/langchain/06-models/`。

| 示例 | 学习重点 |
| --- | --- |
| `model_invocation.py` | `ChatOpenAI` 兼容模型初始化、`invoke`、中文消息与按对话长度选择参数。 |
| `structured_output.py` | 使用 Pydantic schema 与 `with_structured_output` 获取可校验的中文结构化结果。 |
| `src/agent_learn/frameworks/langchain/model_policy.py` | 被多个 LangChain 章节复用的纯参数策略，演示如何把可测试决策与 provider 调用分开。 |

运行真实模型示例：

```powershell
pip install -e ".[dev,openai]"
python src/agent_learn/frameworks/langchain/06-models/model_invocation.py
python src/agent_learn/frameworks/langchain/06-models/structured_output.py
```

示例会从根目录 `.env` 读取模型配置。它们会发送真实模型请求；纯策略测试不发送网络请求：

```powershell
pytest
```

## 必须掌握

### 1. 标准接口降低迁移成本，不消除 Provider 差异

LangChain 可以使用 `init_chat_model` 的 `"provider:model"` 形式快速初始化，也可以使用 `ChatOpenAI` 等 provider-specific class 显式传入 `base_url`、`api_key` 与其他参数。

| 方式 | 适合场景 | 注意点 |
| --- | --- | --- |
| `init_chat_model` | 快速试验、可配置模型选择。 | provider 名称与集成包必须正确。 |
| Provider-specific class | 需要 `base_url`、代理、provider 专有参数或兼容接口。 | 业务代码更了解 provider 细节。 |

本项目使用 `ChatOpenAI` 对接 DeepSeek 的 OpenAI-compatible API，并把构造逻辑放入 `chat_model_factory.py`，供第 5、6 章共同调用。统一接口只降低切换成本；context window、tool calling、structured output、streaming、限流和费用仍必须按 provider 实测。

### 2. `invoke`、`stream` 与 `batch` 分别解决不同问题

| 方法 | 返回方式 | 使用条件 |
| --- | --- | --- |
| `invoke` | 一次返回完整 `AIMessage`。 | 下游必须等待完整结果。 |
| `stream` | 逐步返回 `AIMessageChunk`。 | 需要尽快展示生成进度。 |
| `batch` | 并发处理多个独立输入。 | 输入之间没有状态依赖。 |
| `batch_as_completed` | 按完成顺序返回带 index 的结果。 | 需要优先处理先完成的任务。 |

不要把 streaming 当成纯界面功能。它会改变下游如何处理 chunk、tool call chunk 和中间状态。不要把 `batch` 当成 provider 离线 batch API；它通常是客户端并发，仍受 rate limit 和成本限制。

### 3. 参数是任务策略的一部分

| 参数 | 工程含义 |
| --- | --- |
| `temperature` | 控制随机性；抽取、分类和结构化输出通常应较低。 |
| `max_tokens` | 限制输出长度与成本。 |
| `timeout` | 限制单次等待时间。 |
| `max_retries` | 处理临时网络、429 和 5xx 错误；不应重试权限或参数错误。 |
| `max_concurrency` | 限制 `batch` 并发，避免触发 provider 限流。 |

`model_policy.py` 让长对话使用更低随机性和更短输出。这是教学策略，不是通用真理；真实系统还应结合任务类型、模型能力、token 预算和 SLA。

### 4. Tool binding 与 Agent loop 的边界

`model.bind_tools([...])` 只让模型能够请求 tool call。单独调用模型时，应用仍要执行 tool、把 `ToolMessage` 写回 messages、处理多轮循环和失败。

`create_agent` 则提供 harness，负责模型-tool loop、状态、middleware、streaming 和观测。以下关系必须清晰：

```text
bind_tools -> 模型可以提出工具请求
手写循环    -> 应用负责执行与回写工具结果
create_agent -> harness 负责循环，模型负责决策，tool 负责执行
```

### 5. Structured Output 约束输出边界

`with_structured_output(ArticleSummary)` 将 schema 交给模型包装器，并把响应解析为 Pydantic 对象。它适合 API、UI、抽取和下游自动处理。

结构化输出不是事实校验器：schema 能保证字段形状，却不能证明内容真实。仍要处理解析失败、重试、来源验证和低 `confidence` 的降级路径。

### 6. 模型能力、路由与可观测性

Model profiles 可以描述 context window、多模态、reasoning 和 tool calling 等能力，但它们可能缺失或过期，不能当作绝对契约。

动态模型选择应依据可信的 state 或 context，例如消息长度、租户预算、数据合规要求或任务等级。不要让用户通过 message 任意指定昂贵模型。每次模型调用都应在 tracing 中记录模型名、参数、token usage、延迟、重试与路由原因。

## 常见失败模式

| 现象 | 原因 | 处理方式 |
| --- | --- | --- |
| 更换模型后 tool calling 失效。 | 新模型或 provider 不支持等价的 tool calling。 | 先验证模型 profile 与集成能力，再做端到端测试。 |
| `batch` 触发大量 429。 | 并发度超过 provider 限额。 | 设置 `max_concurrency`，并加入 rate limiter 与退避策略。 |
| schema 通过但回答不真实。 | 结构化输出只校验形状，不验证事实。 | 使用 tool、来源引用、业务校验和 evals。 |
| 长对话成本和延迟失控。 | messages 与 tool result 持续累积。 | 使用 summarization、token 预算和模型路由策略。 |
| 重试造成重复外部动作。 | 将模型重试误用于带副作用 tool。 | 模型与 tool 分开设计重试；写操作需要幂等键和审批。 |
| `base_url` 能连通但部分能力异常。 | 兼容接口没有完整实现 provider 特性。 | 使用 provider 专用 integration，或限制只使用已验证能力。 |

## 自检与练习

1. 为 `select_generation_plan` 加入成本预算参数，并先写测试说明临界值行为。
2. 为 `ArticleSummary` 增加来源字段，讨论 schema 校验为何仍不能替代事实验证。
3. 使用 `stream` 改写 `model_invocation.py`，说明 UI 如何增量拼接 `AIMessageChunk`。
4. 对三个独立问题使用 `batch`，设置 `max_concurrency=2`，并记录每项输入的完成顺序。
5. 在真实 provider 上验证 `with_structured_output` 的解析失败行为，再为失败设计重试与 fallback。

## 本章小结

LangChain Models 提供了统一的模型调用表面：初始化、`invoke`、`stream`、`batch`、tool binding 与 structured output。模型是 Agent 的推理引擎，但可靠系统还需要正确的参数策略、provider 能力验证、token 与限流管理、可观测性，以及与 tools、Agent harness 和 LangGraph runtime 的明确分工。
