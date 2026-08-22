"""Model-only test fixture (not collected by the catalogue suite)."""

from model.client import complete


def check_completion() -> None:
    assert complete("question", ["context"]) == "publish_summary"
