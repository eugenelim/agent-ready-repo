"""Raw model-client fixture."""


def complete(question: str, context: list[str]) -> str:
    """Return a fixture action without policy metadata."""

    _ = (question, context)
    return "publish_summary"
