import pytest

from agent_learn.frameworks.langchain.model_policy import select_generation_plan


def test_select_generation_plan_uses_default_for_short_conversation() -> None:
    assert select_generation_plan(10).temperature == 0.2
    assert select_generation_plan(10).max_tokens == 1200


def test_select_generation_plan_restricts_long_conversation() -> None:
    assert select_generation_plan(11).temperature == 0.1
    assert select_generation_plan(11).max_tokens == 800


def test_select_generation_plan_rejects_negative_message_count() -> None:
    with pytest.raises(ValueError):
        select_generation_plan(-1)
