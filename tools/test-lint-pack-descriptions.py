#!/usr/bin/env python3
"""Self-test for ``lint-pack-descriptions.py``.

Matches the ``tools/test-lint-*.py`` convention: pure stdlib, no pytest, prints
a pass line and exits 0, or raises on the first failure.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "lint_pack_descriptions", _HERE / "lint-pack-descriptions.py"
)
assert _spec and _spec.loader
lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lint)

CEILING = lint.MAX_DESCRIPTION


def _pack(packs: Path, name: str, description: str | None) -> None:
    pack = packs / name
    pack.mkdir(parents=True)
    body = f'[pack]\nname = "{name}"\nversion = "0.0.1"\n'
    if description is not None:
        body += f"description = {json.dumps(description)}\n"
    (pack / "pack.toml").write_text(body, encoding="utf-8", newline="\n")


def test_over_ceiling_is_flagged() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        packs = Path(tmp) / "packs"
        _pack(packs, "chatty", "x" * (CEILING + 1))
        violations = lint.find_violations(packs)
    assert len(violations) == 1, violations
    assert "chatty" in violations[0]
    assert str(CEILING + 1) in violations[0]
    assert str(CEILING) in violations[0]


def test_at_ceiling_passes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        packs = Path(tmp) / "packs"
        _pack(packs, "exact", "x" * CEILING)
        assert lint.find_violations(packs) == []


def test_absent_description_is_ignored() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        packs = Path(tmp) / "packs"
        _pack(packs, "quiet", None)
        assert lint.find_violations(packs) == []


def test_malformed_pack_toml_is_not_a_crash() -> None:
    """Schema validation owns that defect; this lint must not double-report."""
    with tempfile.TemporaryDirectory() as tmp:
        packs = Path(tmp) / "packs"
        pack = packs / "broken"
        pack.mkdir(parents=True)
        (pack / "pack.toml").write_text("not toml [[[", encoding="utf-8")
        assert lint.find_violations(packs) == []


def test_directory_without_pack_toml_is_skipped() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        packs = Path(tmp) / "packs"
        (packs / "not-a-pack").mkdir(parents=True)
        assert lint.find_violations(packs) == []


def test_missing_packs_dir_is_not_a_crash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        assert lint.find_violations(Path(tmp) / "nope") == []


def test_ceiling_is_not_the_target_vocab_cap() -> None:
    """The editorial ceiling must stay independent of the ingest cap.

    `contracts/target-vocab.toml` caps skill/agent descriptions — text the model
    reads to decide activation. If this assert ever fails because someone set
    both to the same number, that is the coupling this lint exists to prevent.
    """
    assert CEILING != 1024
    vocab = _HERE.parent / "contracts" / "target-vocab.toml"
    if vocab.is_file():
        assert f"description-max-length = {CEILING}" not in vocab.read_text(
            encoding="utf-8"
        )


def test_real_packs_are_clean() -> None:
    """The in-tree catalogue must satisfy its own lint."""
    packs = _HERE.parent / "packs"
    if packs.is_dir():
        assert lint.find_violations(packs) == [], lint.find_violations(packs)


def test_exit_codes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _pack(root / "packs", "chatty", "x" * (CEILING + 1))
        assert lint.main(["--root", str(root)]) == 1
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _pack(root / "packs", "terse", "Short and useful.")
        assert lint.main(["--root", str(root)]) == 0


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("test-lint-pack-descriptions: all cases passed.")
    sys.exit(0)
