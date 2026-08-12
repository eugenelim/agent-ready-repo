"""Construction tests for ``tools/check-guide-index.py``.

The cases use in-memory inputs so the coverage contract stays testable in
restricted environments without a writable temporary directory.
"""

from __future__ import annotations

import importlib.util
import io
from contextlib import redirect_stdout
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "check_guide_index", _HERE / "check-guide-index.py"
)
assert _SPEC and _SPEC.loader
CHECKER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(CHECKER)


class _IndexText:
    """Small ``Path`` stand-in for parser tests."""

    def __init__(self, content: str) -> None:
        self.content = content

    def exists(self) -> bool:
        return True

    def read_text(self, *, encoding: str) -> str:
        assert encoding == "utf-8"
        return self.content


def test_extracts_only_direct_guide_home_links() -> None:
    index = _IndexText(
        "\n".join(
            [
                "[Core](core/)",
                "[Pack guide](architect/how-to/plan.md)",
                "[Site route](/packs/contracts/)",
                "[Parent route](../linear/)",
                "[Fragment](#product-engineering/)",
            ]
        )
    )

    assert CHECKER.extract_linked_packs(index) == {"core"}


def test_missing_pack_returns_failure() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        result = CHECKER.report_coverage(
            ["architect", "core"], {"core"}
        )

    assert result == 1
    assert "architect" in output.getvalue()


def test_complete_index_returns_success() -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        result = CHECKER.report_coverage(
            ["architect", "core"], {"architect", "core"}
        )

    assert result == 0
    assert "all 2 active packs" in output.getvalue()


if __name__ == "__main__":
    for name, function in sorted(globals().items()):
        if name.startswith("test_") and callable(function):
            function()
    print("test-check-guide-index: all cases passed.")
