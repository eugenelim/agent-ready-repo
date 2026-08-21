"""Retrieval fixture missing tenant and provenance fields."""


def retrieve(question: str) -> list[str]:
    """Return unscoped fixture chunks."""

    return [question]
