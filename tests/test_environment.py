import pytest

from agent_learn.shared.environment import get_required_environment_variable


def test_get_required_environment_variable_trims_value() -> None:
    environment = {"AGENT_MODEL": "  deepseek-v4-flash  "}

    assert get_required_environment_variable("AGENT_MODEL", environment) == "deepseek-v4-flash"


@pytest.mark.parametrize(
    ("variable_name", "environment"),
    [("", {}), ("DEEPSEEK_API_KEY", {}), ("DEEPSEEK_API_KEY", {"DEEPSEEK_API_KEY": " "})],
)
def test_get_required_environment_variable_rejects_missing_or_blank_value(
    variable_name: str, environment: dict[str, str]
) -> None:
    with pytest.raises(ValueError):
        get_required_environment_variable(variable_name, environment)
