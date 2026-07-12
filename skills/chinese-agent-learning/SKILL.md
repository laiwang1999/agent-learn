---
name: chinese-agent-learning
description: Create or revise Chinese-first Agent learning Markdown and Python examples with Chinese semantic naming, explanatory comments, and comprehensive tool docstrings. Use when authoring Chinese LangChain, LangGraph, DeepAgents, tool, memory, workflow, or observability learning materials in this project.
---

# 中文 Agent 教材

## 目标

将来源资料转化为可学习、可运行、可验证的中文教材。保留 API、类名、配置键和命令等不可翻译的技术字面量；其余面向读者的 Markdown、代码示例语义、注释与 docstring 都使用中文。

## 写作流程

1. 阅读来源材料和项目的 `docs/architecture.md`。将章节目标写成读者能验证的中文能力，而不是来源内容的逐句翻译。
2. 新建或修改 Markdown 时，使用中文标题、段落、表格、图注、运行说明、练习和失败模式。保留 `create_agent`、`thread_id`、环境变量、命令和引用链接等原始技术字面量。
3. 编写两个层次的代码：一个最小示例解释核心 API；一个扩展示例解释真实工程边界，例如失败处理、状态、权限、观测或确定性计算。
4. 将示例中的自定义模块名、函数名、变量名、工具名和输出文字写成中文。第三方库导入、标准库名称、框架 API、环境变量和文件系统约定可保持原样。
5. 为每个教学步骤加入解释性注释。注释说明设计意图、数据流、失败原因或工程权衡，不重复解释一眼可见的赋值和语法。
6. 为每个 tool 写完整中文 docstring，并按“用途、参数、返回值、错误或失败结果、副作用、使用边界、何时调用”说明。读取 [references/tool-docstring-template.md](references/tool-docstring-template.md) 后再实现 tool。
7. 为纯计算、解析与校验逻辑添加不依赖模型密钥和网络的测试。运行测试和静态检查后，回读 Markdown，检查中文完整性。

## 中文约束

- 不使用英文句子替代中文解释；必要英文术语首次出现时写成“中文（English）”。
- 不将中文标点、中文变量名或中文输出混入必须由框架解析的标识符、JSON 键、环境变量或 URL。
- 优先使用表达职责的中文名称，例如 `获取当前天气`、`统计匹配行号`、`文档存储库`；避免“处理数据”“执行任务”等含糊名称。
- 代码示例的用户问题、模拟数据、日志与异常提示均使用中文，确保读者无需自行翻译就能理解运行结果。
- 注释应覆盖所有会影响理解的教学步骤，包括输入校验、边界判断、错误处理、状态保存和框架调用；不要加入“给变量赋值”一类无信息注释。

## Tool Docstring 要求

每个工具都必须说明：

1. 工具解决的具体问题，以及不应解决的问题。
2. 每个参数的格式、单位、允许范围或来源。
3. 返回结果的结构、字段含义和可验证性。
4. 异常、超时、空结果和降级时返回什么。
5. 是否读写外部系统，是否有费用、权限或幂等性要求。
6. Agent 在什么条件下应该调用它，以及何时应拒绝或请求更多信息。

工具详情模板和完整中文示例位于 [references/tool-docstring-template.md](references/tool-docstring-template.md)。

## 交付检查

- Markdown 的叙述性内容是中文，且包含学习目标、运行方式、失败模式和练习。
- 自定义代码示例使用中文语义命名，并为关键教学步骤提供中文注释。
- 每个 tool 具有完整中文 docstring，覆盖用途、参数、返回、失败、副作用与边界。
- 测试不依赖真实 API Key、真实模型请求或不可逆副作用。
- 运行 `pytest`、`ruff check .` 和本 Skill 的校验器；记录无法进行的真实模型验证。
