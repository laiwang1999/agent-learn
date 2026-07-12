---
name: chinese-agent-learning
description: Create or revise Chinese-first Agent learning Markdown and Python examples with Chinese semantic naming, explanatory comments, and comprehensive tool docstrings. Use when authoring Chinese LangChain, LangGraph, DeepAgents, tool, memory, workflow, or observability learning materials in this project.
---

# 中文 Agent 教材

## 目标

将来源资料转化为可学习、可运行、可验证的中文教材。面向读者和模型的 Markdown、代码注释、tool docstring、模型提示词、用户消息与 AI 答复使用中文；Python 标识符、文件名、测试名、技术运行时标识和结构化数据键使用英文。

## 写作流程

1. 阅读来源材料和项目的 `docs/architecture.md`。将章节目标写成读者能验证的中文能力，而不是来源内容的逐句翻译。
2. 新建或修改 Markdown 时，使用中文标题、段落、表格、图注、运行说明、练习和失败模式。保留 `create_agent`、`thread_id`、环境变量、命令和引用链接等原始技术字面量。
3. 编写两个层次的代码：一个最小示例解释核心 API；一个扩展示例解释真实工程边界，例如失败处理、状态、权限、观测或确定性计算。
4. 将示例中的 Python 文件名、模块名、类名、函数名、变量名、tool 名称、测试名、技术运行时标识和结构化数据键写成英文；文件名使用英文小写 `snake_case`。行内注释、块注释、tool docstring、模型提示词、用户消息和 AI 答复使用中文。
5. 为每个教学步骤加入解释性注释。注释说明设计意图、数据流、失败原因或工程权衡，不重复解释一眼可见的赋值和语法。
6. 为每个 tool 写完整 docstring。首句使用动词说明用户可见结果；其后必须依次包含 `Use when`、`Do not use when`、`Args`、`Returns`、`Side effects`、`Preconditions`、`Errors`、`Examples` 和 `Notes`。读取 [references/tool-docstring-template.md](references/tool-docstring-template.md) 后再实现 tool。
7. 为纯计算、解析与校验逻辑添加不依赖模型密钥和网络的测试；若章节核心教学目标包含模型调用、Agent loop、live streaming 或依赖模型的 middleware，还必须提供至少一个真实模型可运行示例，并在 Markdown 中分别写明离线命令与真实模型命令。运行测试和静态检查后，回读 Markdown，检查中文完整性。

## 中文约束

- Markdown 叙述、行内注释、块注释、tool docstring 的业务说明和模型提示词使用中文；必要英文术语首次出现时写成“中文（English）”。
- `system_prompt`、动态 prompt、prompt template、模型 messages 中的指令性内容必须使用中文，并明确要求 AI 最终答复使用中文。
- `messages[].content` 中的学习者提问和 AI 面向用户的答复必须使用中文。`thread_id`、配置键、环境变量、URL、JSON 键、错误码、日志与内部技术标识仍使用英文。
- 不将中文标点、中文变量名或中文输出混入 Python 标识符、JSON 键、环境变量、URL、`thread_id` 或其他技术运行时标识。
- Python 文件名、测试文件名和可执行脚本名必须使用英文小写 `snake_case`，例如 `minimal_inventory_agent.py` 和 `test_environment.py`；禁止使用中文文件名。
- 优先使用表达职责的英文名称，例如 `lookup_current_weather`、`count_matching_lines`、`document_store`；避免 `process_data`、`do_task` 等含糊名称。
- 代码示例中的用户问题、模型提示词和 AI 面向用户的答复使用中文；模拟数据标识、日志、异常码、技术错误消息和返回字段使用英文，确保协议可跨语言环境稳定运行。
- 中文注释应覆盖所有会影响理解的教学步骤，包括输入校验、边界判断、错误处理、状态保存和框架调用；不要加入“给变量赋值”一类无信息注释。

## Tool Docstring 要求

每个工具都必须使用参考模板中的固定结构。第一行以动词描述用户可见结果；随后完整填写 `Use when`、`Do not use when`、`Args`、`Returns`、`Side effects`、`Preconditions`、`Errors`、`Examples` 和 `Notes`。

`Returns` 必须说明成功时的 `{"status": "success", "data": ...}` 与失败时的 `{"status": "error", "error": {"code": "...", "message": "..."}}` 结构。`Errors` 至少说明 `invalid_input`、`not_found`、`permission_denied` 和 `external_service_error` 的适用性；不适用时必须明确写出原因。

工具详情模板和完整中文示例位于 [references/tool-docstring-template.md](references/tool-docstring-template.md)。

## 交付检查

- Markdown 的叙述性内容是中文，且包含学习目标、运行方式、失败模式和练习。
- 自定义代码示例使用英文语义命名、英文技术运行时标识和英文结构化数据键；所有模型提示词、用户消息、AI 面向用户的答复、tool docstring 与关键教学步骤注释使用中文。
- 每个 tool 具有完整 docstring，包含固定的九个段落标题、标准成功/失败返回结构和明确错误码。
- 测试不依赖真实 API Key、真实模型请求或不可逆副作用。
- 依赖真实模型的章节必须在 Markdown 中提供 `.env` 配置说明、真实模型运行命令，以及无法执行时的明确说明；不得伪造模型输出。
- 运行 `pytest`、`ruff check .` 和本 Skill 的校验器；记录无法进行的真实模型验证。
