"""A research agent that delegates exact text work to deterministic tools."""

import urllib.error
import urllib.request
from collections.abc import Sequence
from typing import Any

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import BaseTool, tool
from langgraph.checkpoint.memory import InMemorySaver

from .settings import AgentSettings
from .text_store import TextStore

SYSTEM_PROMPT = """你是一名文学数据助手。

关于文本的事实性结论必须使用文档工具验证，禁止猜测计数或行号。
无法从已获取文档验证时必须明确说明。回答应保持简洁，并为每个计数或行号标注文档 ID。
"""


def build_research_tools(store: TextStore) -> Sequence[BaseTool]:
    """Expose URL fetching and exact line analysis as a small, inspectable tool suite."""

    @tool
    def fetch_document(url: str) -> str:
        """Fetch a UTF-8 text document from an HTTPS URL and return its document ID and line count."""
        if not url.startswith("https://"):
            return "Fetch failed: only HTTPS URLs are accepted by this learning example."
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "agent-learn-research/0.1"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
                text = response.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as error:
            return f"Fetch failed: {error.reason}"

        document_id = store.save(text)
        return f"Fetched document_id={document_id}; line_count={len(text.splitlines())}."

    @tool
    def count_lines_containing(document_id: str, phrase: str) -> str:
        """Return the exact count and first matching 1-based line number for a saved document phrase."""
        try:
            matches = store.matching_line_numbers(document_id, phrase)
        except ValueError as error:
            return str(error)
        first_line = matches[0] if matches else None
        return f"phrase={phrase!r}; count={len(matches)}; first_line={first_line}"

    return [fetch_document, count_lines_containing]


def create_research_agent(settings: AgentSettings) -> tuple[Any, TextStore]:
    """Create an agent with short-term memory and its isolated document store."""
    store = TextStore()
    model = init_chat_model(
        settings.model,
        temperature=settings.temperature,
        timeout=settings.timeout_seconds,
        max_tokens=settings.max_tokens,
    )
    agent = create_agent(
        model=model,
        tools=build_research_tools(store),
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )
    return agent, store


def main() -> None:
    agent, _ = create_research_agent(AgentSettings.from_env())
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Fetch https://www.gutenberg.org/files/64317/64317-0.txt. "
                        "Count lines containing 'Gatsby' and give the first line containing 'Daisy'."
                    ),
                }
            ]
        },
        config={"configurable": {"thread_id": "great-gatsby-research"}},
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
