# 第 3 章实践：LangChain Quickstart

## 来源与目标

- 教材来源：[LangChain Quickstart 章节](https://github.com/laiwang1999/agent-book-for-myself/blob/master/langchain/03-langchain-quickstart.md)
- 官方参考：[LangChain Quickstart](https://docs.langchain.com/oss/python/langchain/quickstart)

本章目标是跑通一个最小 Agent，并理解它如何通过模型、工具、system prompt 和短期 memory 形成闭环。随后将同一思路扩展为 research agent，用确定性工具处理计数与行号。

## 必须掌握

### 1. `create_agent` 的三个核心输入

| 输入 | 要掌握的结论 |
| --- | --- |
| `model` | 决定模型 provider 与推理能力；模型名和参数必须可配置。 |
| `tools` | 决定 Agent 的外部动作边界；函数名、类型标注和 docstring 都是工具契约。 |
| `system_prompt` | 规定角色、约束、失败策略与输出要求；它不是普通说明文字。 |

对应代码：[weather_agent.py](../../../src/agent_learn/frameworks/langchain/chapter_03/weather_agent.py)。

### 2. 工具负责确定性工作

LLM 适合理解问题、选择工具和组织回答，不应凭生成能力给出精确计数、行号或文件检索结果。本项目的 research 示例将文档保存在 `TextStore`，并由 `count_lines_containing` 计算可复查结果。这样模型只需编排，计算仍由确定性 Python 代码完成。

对应代码：[research_agent.py](../../../src/agent_learn/frameworks/langchain/chapter_03/research_agent.py) 与 [text_store.py](../../../src/agent_learn/frameworks/langchain/chapter_03/text_store.py)。

### 3. Memory 的作用域

`InMemorySaver` 结合 `thread_id` 保存同一会话的短期状态。它适合本地学习，但服务重启会丢失数据，也不能跨实例共享。进入生产环境前应替换为持久化 checkpointer，并明确 thread 的租户和访问边界。

### 4. LangChain、LangGraph 与 DeepAgents 的选择

| 需求 | 首选 |
| --- | --- |
| 需要细粒度定义模型、工具、middleware | LangChain |
| 需要显式状态图、暂停恢复、分支或持久化 | LangGraph |
| 需要开箱即用的 planning、文件系统和 subagents | DeepAgents |

选择框架是能力边界决策，不是功能越多越好。先实现最小可验证 Agent，再引入更高层运行时。

## 运行

```powershell
pip install -e ".[dev,openai]"
$env:OPENAI_API_KEY = "..."
$env:AGENT_MODEL = "openai:gpt-5.5"
python -m agent_learn.frameworks.langchain.chapter_03.weather_agent
python -m agent_learn.frameworks.langchain.chapter_03.research_agent
```

research 示例只接受 HTTPS 文本 URL，并设置超时。它是学习代码，不是生产级 URL 下载服务；生产环境还需要域名白名单、大小限制、内容类型校验、持久化存储和审计。

## 自检与练习

1. 将 weather 工具替换为真实 API 前，列出超时、重试、认证、缓存和限流策略。
2. 为 `TextStore` 增加一个返回匹配行上下文的纯函数，并先为它写测试。
3. 将 research agent 的 `InMemorySaver` 替换为持久化 checkpointer，说明 thread 隔离方案。
4. 使用 tracing 检查模型是否调用了正确工具、是否传入了正确参数、工具结果是否支持最终结论。

## 常见失败模式

| 现象 | 原因 | 处理方式 |
| --- | --- | --- |
| 模型直接编造行号 | prompt 未要求验证，或缺少确定性工具 | 明确禁止猜测，并提供查询工具。 |
| 工具没有被调用 | 工具名或 docstring 不清楚 | 用动作导向的名称和准确参数描述。 |
| 多轮对话丢失上下文 | 未配置 checkpointer 或重复使用错误的 thread | 设置 checkpointer，并为每个会话传入稳定的 `thread_id`。 |
| 示例在重启后失效 | 使用内存 store/checkpointer | 在生产实现中改用持久化、隔离的存储。 |
