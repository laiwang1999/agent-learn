"""The smallest useful LangChain agent from the Quickstart chapter."""

from langchain.agents import create_agent

from .settings import AgentSettings


def get_weather(city: str) -> str:
    """Return demo weather for a city; replace this with a trusted weather API in production."""
    return f"The demo forecast for {city} is sunny."


def create_weather_agent(settings: AgentSettings):
    """Combine a model, tool, and system instruction into a runnable agent."""
    return create_agent(
        model=settings.model,
        tools=[get_weather],
        system_prompt=(
            "你是一名简洁的天气助手。回答天气问题时必须使用天气工具，"
            "并明确说明结果是演示用预报。"
        ),
    )


def main() -> None:
    settings = AgentSettings.from_env()
    agent = create_weather_agent(settings)
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What is the weather in Shanghai?"}]}
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
