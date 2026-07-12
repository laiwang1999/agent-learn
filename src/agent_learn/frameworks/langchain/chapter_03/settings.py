"""Runtime configuration for the Quickstart examples."""

from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True, slots=True)
class AgentSettings:
    """Keep model settings explicit and configurable outside source code."""

    model: str
    temperature: float
    timeout_seconds: int
    max_tokens: int

    @classmethod
    def from_env(cls) -> "AgentSettings":
        return cls(
            model=getenv("AGENT_MODEL", "openai:gpt-5.5"),
            temperature=float(getenv("AGENT_TEMPERATURE", "0.2")),
            timeout_seconds=int(getenv("AGENT_TIMEOUT_SECONDS", "120")),
            max_tokens=int(getenv("AGENT_MAX_TOKENS", "4000")),
        )
