"""创建供多个 LangChain 章节复用的 OpenAI-compatible 对话模型。"""

from langchain_openai import ChatOpenAI

from agent_learn.shared.environment import (
    get_required_environment_variable,
    load_project_environment,
)


def create_chat_model(*, temperature: float | None = None, max_tokens: int | None = None) -> ChatOpenAI:
    """根据项目环境变量创建 DeepSeek OpenAI-compatible 对话模型。"""
    # 在读取配置前载入本地 .env，同时保留部署环境变量的优先级。
    load_project_environment()
    return ChatOpenAI(
        model=get_required_environment_variable("AGENT_MODEL"),
        api_key=get_required_environment_variable("DEEPSEEK_API_KEY"),
        base_url=get_required_environment_variable("DEEPSEEK_BASE_URL"),
        temperature=(
            float(get_required_environment_variable("AGENT_TEMPERATURE"))
            if temperature is None
            else temperature
        ),
        timeout=int(get_required_environment_variable("AGENT_TIMEOUT_SECONDS")),
        max_tokens=(
            int(get_required_environment_variable("AGENT_MAX_TOKENS"))
            if max_tokens is None
            else max_tokens
        ),
    )
