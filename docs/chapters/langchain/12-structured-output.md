# 第 12 章实践：LangChain Structured Output

## 来源与目标

- 教材来源：[12-langchain-structured-output.md](https://github.com/laiwang1999/agent-book-for-myself/blob/master/langchain/12-langchain-structured-output.md)
- 官方参考：[LangChain Structured output](https://docs.langchain.com/oss/python/langchain/structured-output)

本章聚焦 **Agent 场景**的结构化输出：`create_agent` 通过 `response_format` 让最终结果进入可验证的数据结构，并保存在 final state 的 `structured_response` 中。第 6 章已从模型角度讲解 `with_structured_output`；本章说明 Agent harness 如何选择 `ProviderStrategy` / `ToolStrategy`、如何处理 validation error，以及为何不应从最后一条自然语言中解析字段。

完成后，你应能设计 Pydantic schema、离线验证结构化 payload，并在真实 Agent 上读取 `structured_response`。

## 必须掌握

1. **`response_format` 是 Agent 结构化输出入口**：可直接传 schema，或由 LangChain 自动选择策略。见 [contact_schemas.py](../../../src/agent_learn/frameworks/langchain/12-structured-output/contact_schemas.py)。
2. **结果在 `structured_response`，不在自由文本里**：应用应读取校验后的对象，而不是解析 `AIMessage.text`。见 [structured_response_contract.py](../../../src/agent_learn/frameworks/langchain/12-structured-output/structured_response_contract.py)。
3. **Schema 设计决定稳定性**：字段描述、枚举、可空字段与 Pydantic 约束会直接影响抽取质量。见 [contact_schemas.py](../../../src/agent_learn/frameworks/langchain/12-structured-output/contact_schemas.py)。
4. **Validation error 是反馈边界**：格式错误可让模型重试；权限或业务规则错误不应依赖自动重试掩盖。见 [schema_validation.py](../../../src/agent_learn/frameworks/langchain/12-structured-output/schema_validation.py)。
5. **真实 Agent 结构化抽取**：`create_agent(..., response_format=ToolStrategy(ContactInfo))` 并读取 `result["structured_response"]`。DeepSeek thinking 模式不支持该策略强制使用的 `tool_choice="required"`，因此示例通过 `thinking_mode="disabled"` 显式关闭 thinking。见 [live_structured_agent.py](../../../src/agent_learn/frameworks/langchain/12-structured-output/live_structured_agent.py)。

## 结构化输出在系统中的位置

```text
第 6 章 Models：model.with_structured_output(schema)
第 8 章 Tools：业务动作的类型化接口
第 12 章 Agent：response_format → ProviderStrategy / ToolStrategy → structured_response
```

Structured output 与 tools 都使用 schema，但语义不同：tools 请求外部动作，structured output 把**最终结果**放进应用契约。

## 运行

### 离线验证（不需要 API Key）

```powershell
pip install -e ".[dev]"
python src/agent_learn/frameworks/langchain/12-structured-output/contact_schemas.py
python src/agent_learn/frameworks/langchain/12-structured-output/schema_validation.py
python src/agent_learn/frameworks/langchain/12-structured-output/structured_response_contract.py
pytest tests/test_structured_output.py
```

### 真实 Agent（需要 `.env`）

```powershell
pip install -e ".[dev,openai]"
python src/agent_learn/frameworks/langchain/12-structured-output/live_structured_agent.py
```

环境变量与第 7 章相同。该命令会从用户文本中抽取 `ContactInfo`，并打印 `structured_response`。示例会在请求参数中设置 `thinking={"type": "disabled"}`，避免 DeepSeek thinking 模式与 `ToolStrategy` 的强制 `tool_choice` 冲突。

## 工程判断

| 场景 | 推荐做法 | 不应依赖 |
| --- | --- | --- |
| Provider 支持 native structured output | 直接传 schema 或 `ProviderStrategy`。 | 从自然语言里正则抽字段。 |
| 仅支持 tool calling | `ToolStrategy(schema)` + `handle_errors`。 | 假设所有模型都有 native 支持。 |
| 与业务 tools 同时使用 | 确认 provider 支持二者并存，或拆两阶段 workflow。 | 无验证地叠加 tools 与 response_format。 |
| 字段可能缺失 | `str \| None` 与明确 description。 | 逼模型编造 phone、email。 |
| Union 多 schema | `ToolStrategy(Union[A, B])` 并处理多选错误。 | 强迫模型只选一个却输入混合信息。 |
| 高风险流程 | `handle_errors=False`，应用层处理。 | 让模型无限重试掩盖业务错误。 |

## 常见失败模式

| 现象 | 原因 | 处理方式 |
| --- | --- | --- |
| 字段经常漏填或乱填。 | schema 字段过多、描述含糊、无约束。 | 减少字段；写清 `Field(description=...)`；用 `Literal` / 范围约束。 |
| 应用读到的还是自然语言。 | 只看了 `messages[-1].content`。 | 读取 `structured_response`。 |
| validation 一直重试仍失败。 | 输入本身无法映射到 schema。 | 返回用户澄清问题，而不是无限重试。 |
| tools 与 structured output 冲突。 | provider 不支持同时启用。 | 拆成“先调工具收集证据，再结构化输出”两阶段。 |
| thinking 模式提示不支持 `tool_choice`。 | `ToolStrategy` 会强制 `tool_choice="required"`，但当前 DeepSeek thinking 模式不接受该值。 | 对该次结构化抽取显式设置 `thinking_mode="disabled"`；不要改用 DeepSeek 当前不支持的 `json_schema` response format。 |
| Union 同时返回多个结构。 | 输入同时含联系人与事件信息。 | 设计更完整 schema 或拆分任务。 |
| 流式过程中解析半截 JSON。 | 在 tool call chunk 未完成时解析。 | 等 final state 的 `structured_response`。 |

## 自检与练习

1. 为 `ProductRating` 增加 `rating=0` 的测试，确认 Pydantic 会拒绝。
2. 修改 `live_structured_agent.py` 的用户输入，使 phone 缺失，观察 `phone` 是否为 `None`。
3. 比较第 6 章 `structured_output.py` 与本章 Agent 路径，说明二者适用边界。
4. 设计一个包含 `contact` 与 `event` 两个可选字段的 schema，替代 `Union[ContactInfo, EventDetails]`。
5. 说明何时应设置 `ToolStrategy(handle_errors=False)`。

## 本章小结

LangChain Agent 通过 `response_format` 返回可验证的结构化结果，保存在 `structured_response` 中。ProviderStrategy 依赖 provider 原生能力，ToolStrategy 通过 tool calling 模拟并支持错误反馈。生产中应认真设计 schema 与错误处理：让模型修正可恢复的格式错误，但不要让自动重试掩盖权限或高风险业务流程错误。Structured output 的目标是让 Agent 最终结果成为应用契约，而不是“看起来像 JSON 的文本”。
