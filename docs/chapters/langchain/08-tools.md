# 第 8 章实践：LangChain Tools

## 来源与目标

- 教材来源：[08-langchain-tools.md](https://github.com/laiwang1999/agent-book-for-myself/blob/master/langchain/08-langchain-tools.md)
- 官方参考：[LangChain Tools](https://docs.langchain.com/oss/python/langchain/tools)

本章把 Tool 当作 Agent 采取行动的类型化接口，而不是普通 Python helper。完成后，你应能定义模型可见的 tool schema、用 `ToolRuntime` 读取服务端注入的 state 与 context，并观察真实 Agent 如何根据 schema 选择工具。

离线示例用于验证 schema、权限过滤与 state 读取；真实 Agent 示例用于观察模型如何实际调用本章工具。

## 必须掌握

1. **Schema 与实现分离**：模型只看到工具名、描述和参数 schema；实现细节由你的 Python 代码执行。见 [basic_tool_definition.py](../../../src/agent_learn/frameworks/langchain/08-tools/basic_tool_definition.py)。
2. **`@tool` 与高级 schema**：type hints 与 docstring 生成模型可见契约；复杂参数用 Pydantic `args_schema` 约束枚举、默认值与字段描述。
3. **保留参数名**：`config` 与 `runtime` 不能作为模型填写的业务参数；`ToolRuntime` 由框架注入并对模型隐藏。见 [tool_state_access.py](../../../src/agent_learn/frameworks/langchain/08-tools/tool_state_access.py)。
4. **返回值语义**：string 适合人类可读摘要，object 适合结构化推理，`Command` 用于更新 Agent state，`return_direct=True` 可在结果已完整时跳过下一次模型调用。
5. **真实 Agent 工具选择**：模型根据 tool schema 决定调用时机与参数。见 [live_catalog_agent.py](../../../src/agent_learn/frameworks/langchain/08-tools/live_catalog_agent.py)。

## 工具在 Agent 中的位置

```text
messages 提供上下文
model 读取上下文并请求行动
tools 执行外部动作（schema 对模型可见，runtime 由系统注入）
agent harness 管理循环、状态、middleware 与错误恢复
```

第 5 章讲 Agent loop，第 6 章讲模型，第 7 章讲 messages。本章进入能力边界中最关键的一层：模型根据 tool schema 决定何时行动，你的应用负责执行、权限、状态更新与错误处理。

## 运行

### 离线验证（不需要 API Key）

```powershell
pip install -e ".[dev]"
python src/agent_learn/frameworks/langchain/08-tools/basic_tool_definition.py
python src/agent_learn/frameworks/langchain/08-tools/tool_state_access.py
python src/agent_learn/frameworks/langchain/08-tools/dynamic_tool_filter.py
pytest tests/test_tool_contract.py
```

### 真实 Agent（需要 `.env`）

```powershell
pip install -e ".[dev,openai]"
python src/agent_learn/frameworks/langchain/08-tools/live_catalog_agent.py
```

该命令会创建真实 Agent，并让模型根据 tool schema 调用 `search_lesson_catalog` 与 `get_city_weather`。环境变量要求与第 7 章相同。若无法执行真实模型调用，请明确说明缺失的配置，不要伪造工具调用结果。

## 工程判断

| 场景 | 推荐做法 | 不应依赖 |
| --- | --- | --- |
| 参数少于两个、结构简单 | `@tool` + type hints + 中文 docstring。 | 让模型从自由文本猜参数格式。 |
| 参数有枚举、嵌套或业务默认值 | Pydantic `args_schema` 与字段级描述。 | 仅靠函数签名中的裸类型。 |
| 读取当前对话短期记忆 | `runtime.state` 读取 messages 或自定义字段。 | 把长期用户画像混进单次 state。 |
| 跨会话偏好或账户设置 | `runtime.store` 与持久化后端。 | 学习示例中的 `InMemoryStore` 直接上生产。 |
| 更新 Agent state | 返回 `Command(update=...)` 并附带 `ToolMessage`。 | 在工具里直接改全局变量却不通知模型。 |
| 工具失败 | middleware 统一转成可恢复的 `ToolMessage`。 | 无差别吞掉权限错误或支付失败。 |
| 工具过多或权限分级 | `wrap_model_call` 动态过滤工具集合。 | 把所有写操作工具一直暴露给模型。 |

## 常见失败模式

| 现象 | 原因 | 处理方式 |
| --- | --- | --- |
| 模型从不调用工具或参数总填错。 | 工具名含糊、docstring 未说明使用时机、schema 不完整。 | 用 `snake_case` 命名；在 docstring 中写清 `Use when` / `Do not use when`；复杂参数改用 Pydantic。 |
| 模型尝试填写 `runtime` 或 `user_id`。 | 把系统参数暴露进 tool schema。 | 用 `ToolRuntime` 和 `context` 注入；schema 只保留业务输入。 |
| 工具更新了 state，但模型不知道结果。 | 返回 `Command` 时未附带 `ToolMessage`。 | 在 `update["messages"]` 中加入带 `runtime.tool_call_id` 的 `ToolMessage`。 |
| 并发工具写同一 state 字段后结果混乱。 | 未定义 reducer。 | 为会被并行更新的字段定义合并语义。 |
| 动态 MCP 工具可见但无法执行。 | 只在 `wrap_model_call` 注册 schema，未在 `wrap_tool_call` 提供执行路径。 | 两个 hook 成对治理来源、权限与 sandbox。 |
| 生产重启后长期记忆丢失。 | 使用进程内 `InMemoryStore` 保存跨会话数据。 | 换成 Postgres 等持久化 store，并明确 namespace 隔离。 |

## 自检与练习

1. 为 `runtime_is_hidden_from_schema` 增加一个测试：schema 中出现 `runtime` 或 `config` 时应失败。
2. 给 `get_city_weather` 增加 `units` 非法枚举值测试，确认 Pydantic schema 能拦截错误输入。
3. 实现 `filter_tools_by_feature_flag`，只允许购买了 `premium_search` 的用户看到 `premium_web_search`。
4. 阅读第 5 章 `lookup_tenant_inventory`，说明哪些输入来自模型、哪些来自 `runtime.context`。
5. 设计一个返回 `Command` 的 `set_display_name` 工具草图，写出需要附带的 `ToolMessage` 字段。

## 本章小结

LangChain tools 是 Agent 采取行动的类型化接口。`@tool` 用函数名、type hints 和 docstring 生成模型可见 schema；`ToolRuntime` 统一访问 state、context、store 与 `tool_call_id`；返回值可以是 string、object、multimodal content 或 `Command`，也可以用 `return_direct=True` 直接结束 loop。生产设计的重点不只是“能被模型调用”，而是名称清晰、权限由服务端注入、错误可恢复、动态暴露可控。工具设计决定 Agent 能做什么，也决定它可能造成什么风险。
