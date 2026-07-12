# 项目 AI 协作规则

本文件适用于所有读取、分析、编辑或生成本项目内容的 AI Agent。

## 首要规则：先读取 Skills

在理解项目、回答项目问题、修改代码、编辑 Markdown、调整依赖、运行验证或创建新文件之前，必须先执行以下步骤：

1. 枚举 `skills/` 目录中的所有 Skill 子目录。
2. 阅读每个 Skill 子目录中的 `SKILL.md`。
3. 根据当前任务读取该 Skill 在 `references/` 中明确要求的补充文件。
4. 只有完成上述读取后，才能检查或修改 `src/`、`docs/`、`tests/`、`pyproject.toml` 和其他项目文件。

不得因为任务看起来简单而跳过 Skills。Skills 是本项目的工作流、架构与内容质量的最高优先级本地约束；用户的明确指令和安全要求优先于 Skills。

## 当前 Skills

| Skill | 适用任务 | 必读补充内容 |
| --- | --- | --- |
| `skills/agent-learning/` | 新增或修订 Agent 学习章节、架构、LangChain、LangGraph、DeepAgents、tools、memory、workflow、observability | 修改架构或引入框架前，读取 `references/project-architecture.md`；新建章节前，读取 `references/chapter-template.md`。 |
| `skills/chinese-agent-learning/` | 编写或修改中文学习 Markdown、中文代码示例、tool、注释与 docstring | 编写或修改 tool 前，读取 `references/tool-docstring-template.md`。 |

当新增、删除或重命名 Skill 时，必须同步更新此表。

## 后续读取顺序

完成 Skills 读取后，按任务需要继续读取：

1. `docs/architecture.md`：任何会影响代码组织、框架边界、共享逻辑或依赖的任务。
2. 目标章节的 `docs/chapters/<framework>/` 文档：任何章节实现或学习材料任务。
3. 目标模块、相邻实现和对应测试：任何代码变更。
4. `pyproject.toml`：任何依赖、测试或运行方式变更。

## 修改约束

- 保持 `shared/` 框架无关；不要让 `langchain`、`langgraph`、`deepagents` 目录彼此直接导入。
- 新增章节时，同时交付可运行示例、中文重点文档与不依赖真实模型或网络的确定性测试；若章节核心能力依赖模型或 Agent 运行时行为，还必须提供至少一个通过环境变量配置的真实模型可运行示例，并在章节文档中写明离线验证与真实模型运行两套命令。
- 所有密钥、模型名、超时和 provider 配置必须从环境变量或配置读取；禁止写入真实密钥。
- 中文教材任务必须遵循 `chinese-agent-learning`：叙述内容、示例语义、输出、注释与 tool docstring 使用中文；框架 API、环境变量和其他技术字面量保持原样。
- tool 必须具有详尽 docstring，说明用途、参数、返回值、失败行为、副作用、使用边界与调用时机。
- 不覆盖、重置或删除与当前任务无关的用户改动。

## 完成前验证

修改后，执行与变更相称的验证：

1. 运行相关测试；纯逻辑优先使用不需要 API Key 的测试。
2. 运行静态检查或语法检查。
3. 回读 Markdown，确认中文内容、路径、链接和代码块可读。
4. 若无法进行真实模型调用，明确说明原因，不得伪造运行结果。
5. 若章节核心能力依赖真实模型或 Agent 运行时行为，完成前还应确认已提供真实模型示例路径、所需环境变量与运行命令；仅有离线模拟不足以视为该章完成。
