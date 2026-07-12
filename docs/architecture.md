# 项目架构

## 目标

本项目以“一个教材章节对应一个可运行的学习切片”为基本单位。每个切片都应让读者能够阅读重点、运行代码、修改行为并通过测试验证，不将教程代码直接当作生产实现。

## 目录边界

```text
agent_learn/
├── docs/                         # 学习文档、章节重点和架构决策
│   └── chapters/<framework>/      # 与教材章节一一对应的笔记
├── skills/agent-learning/         # 项目内 Skill，规定新增章节的工作流
├── src/agent_learn/
│   ├── shared/                    # 框架无关的领域逻辑、数据契约和测试夹具
│   └── frameworks/
│       ├── langchain/             # LangChain harness、tools、middleware 示例
│       ├── langgraph/             # 未来的 StateGraph、persistence、streaming 示例
│       └── deepagents/            # 未来的 planning、filesystem、subagents 示例
└── tests/                         # 不依赖真实模型密钥的确定性测试
```

`shared/` 是跨章节共用组件的唯一位置，只允许依赖 Python 标准库或明确的领域库，不能导入 LangChain、LangGraph 或 DeepAgents。先检查此目录，再在章节内新增 helper；当组件被两个或更多章节使用，或它本身是项目级契约时，应放入 `shared/`。每个 `frameworks/<framework>/<nn>-<topic-slug>/` 是独立的学习切片，负责将 shared 逻辑接到对应框架的 API 上。

## 框架分工

| 层 | 适用内容 | 不应承担的职责 |
| --- | --- | --- |
| `shared` | 文本处理、领域模型、数据校验、纯函数、测试数据 | 模型调用、框架对象或 provider 配置 |
| `langchain` | 单 Agent、模型、tools、middleware、结构化输出 | 多节点执行图的底层实现 |
| `langgraph` | 显式状态、分支、checkpoint、interrupt、streaming | 隐藏在图节点中的大型业务逻辑 |
| `deepagents` | 长任务 planning、文件系统、subagents、权限边界 | 替代所有可用单 Agent 完成的简单任务 |

LangChain 与 DeepAgents 可使用 LangGraph 提供的运行时能力，但本项目中禁止一个框架目录直接导入另一个框架目录。章节可以导入 `shared/`，但 `shared/` 不能反向导入任何 framework；要复用逻辑时，先下沉到 `shared`。

## 新增章节的最小交付

每个新增章节至少提交以下内容：

1. `docs/chapters/<framework>/<nn>-<slug>.md`：来源、学习目标、重点、运行说明、失败模式和练习。
2. 仅当章节有可观察的运行行为时，才添加 `src/agent_learn/frameworks/<framework>/<nn>-<topic-slug>/` 下的示例；纯概念章节只交付 Markdown。
3. `tests/`：覆盖不需要模型或网络的确定性逻辑，尤其是 shared 组件。
4. 依赖变更：仅在章节实际使用时加入，并优先放在可选依赖组。
5. 若章节核心能力依赖真实模型或 Agent 运行时行为：至少提供一个通过环境变量配置的真实模型可运行示例，并在章节文档中写明离线验证与真实模型运行两套命令。

每个需要 API Key 的示例必须通过环境变量读取密钥和模型配置；密钥、用户数据和真实外部副作用不得写入示例代码或测试。
