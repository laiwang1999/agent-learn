from agent_learn.frameworks.langchain.chapter_03.text_store import TextStore


def test_text_store_returns_one_based_case_insensitive_matches() -> None:
    store = TextStore()
    document_id = store.save("Daisy meets Gatsby.\nNo match.\nGATSBY leaves.")

    assert store.matching_line_numbers(document_id, "gatsby") == [1, 3]
    assert store.first_line_number(document_id, "daisy") == 1


def test_text_store_returns_none_when_phrase_is_absent() -> None:
    store = TextStore()
    document_id = store.save("A short document.")

    assert store.first_line_number(document_id, "missing") is None
