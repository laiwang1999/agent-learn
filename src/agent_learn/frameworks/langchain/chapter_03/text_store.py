"""Deterministic text operations used by the research-agent tools."""

from dataclasses import dataclass, field
from hashlib import sha256


@dataclass(slots=True)
class TextStore:
    """Keep fetched documents outside the model context for exact text operations.

    This in-memory store is deliberately local to one example process. A production service
    should use a scoped, persistent store and enforce URL access policies.
    """

    _documents: dict[str, str] = field(default_factory=dict)

    def save(self, text: str) -> str:
        document_id = sha256(text.encode("utf-8")).hexdigest()[:12]
        self._documents[document_id] = text
        return document_id

    def get(self, document_id: str) -> str:
        try:
            return self._documents[document_id]
        except KeyError as error:
            raise ValueError(f"Unknown document_id: {document_id}") from error

    def matching_line_numbers(self, document_id: str, phrase: str) -> list[int]:
        needle = phrase.casefold()
        return [
            line_number
            for line_number, line in enumerate(self.get(document_id).splitlines(), start=1)
            if needle in line.casefold()
        ]

    def first_line_number(self, document_id: str, phrase: str) -> int | None:
        matches = self.matching_line_numbers(document_id, phrase)
        return matches[0] if matches else None
