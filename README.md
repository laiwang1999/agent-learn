# Agent Learning

一个以章节为单位的 Agent 工程学习项目。每个章节都包含可运行的示例、重点笔记和可验证的练习代码。

当前已实现的学习闭环：

- LangChain 第 3 章：Quickstart，从 weather agent 到带确定性文本工具的 research agent。
- 项目内 Skill：`skills/agent-learning/`，用于后续新增章节时保持架构和文档一致。

## 安装

```powershell
.venv\Scripts\Activate.ps1
pip install -e ".[dev,openai]"
```

需要比较 DeepAgents 时安装：

```powershell
pip install -e ".[dev,deepagents]"
```

设置模型密钥与可选模型名：

```powershell
$env:OPENAI_API_KEY = "..."
$env:AGENT_MODEL = "openai:gpt-5.5"
```

运行示例：

```powershell
python -m agent_learn.frameworks.langchain.chapter_03.weather_agent
python -m agent_learn.frameworks.langchain.chapter_03.research_agent
pytest
```

项目结构和新增章节规则见 [docs/architecture.md](docs/architecture.md) 与 [skills/agent-learning/SKILL.md](skills/agent-learning/SKILL.md)。
