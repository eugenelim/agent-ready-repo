"""Tests for catalogue/sync_authoring_scaffold.py."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_SCAFFOLD = (
    REPO_ROOT
    / "packages"
    / "agentbundle"
    / "agentbundle"
    / "_data"
    / "catalogue-scaffold"
)


def _sync_pairs() -> list[tuple[Path, str]]:
    path = REPO_ROOT / "tools" / "catalogue" / "sync_authoring_scaffold.py"
    spec = importlib.util.spec_from_file_location("sync_authoring_scaffold", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._SYNC_PAIRS


def test_manifest_records_every_projected_file_digest() -> None:
    """`manifest.json` must record the sha256 of every projected file.

    The byte-equality check above compares repo copy to scaffold copy; this compares the
    scaffold copy to the digest install-time verification reads. A mismatch means a file
    this repo considers correct would be rejected on arrival, which byte-equality alone
    cannot see. Covers all `_SYNC_PAIRS`, not one file.
    """
    manifest = json.loads((DATA_SCAFFOLD / "manifest.json").read_text(encoding="utf-8"))
    recorded = manifest.get("files", {})
    wrong = []
    for _source, scaffold_rel in _sync_pairs():
        target = DATA_SCAFFOLD / scaffold_rel
        if not target.exists():
            continue  # byte-equality above owns the missing-file case
        expected = hashlib.sha256(target.read_bytes()).hexdigest()
        if recorded.get(scaffold_rel) != expected:
            wrong.append(scaffold_rel)
    assert not wrong, f"manifest.json digest does not match the projected file: {wrong}"


def test_claude_import_shims_are_projected_to_adopters() -> None:
    """`packs/CLAUDE.md` and `profiles/CLAUDE.md` reach an adopter catalogue.

    Deliberately hardcoded rather than derived from `_SYNC_PAIRS`. Every other
    assertion in this file reads that list, so deleting both pairs and
    regenerating the projection would leave the whole suite green while adopters
    silently stopped receiving the shims. These two paths are the outcome, so
    they are named here directly.

    Claude Code reads `CLAUDE.md`, never `AGENTS.md`, so without the shim an
    adopter's Claude session gets no scoped pack or profile instructions at all.
    The body must stay exactly the import directive: prose here would be a second
    copy of guidance `AGENTS.md` owns.
    """
    manifest = json.loads((DATA_SCAFFOLD / "manifest.json").read_text(encoding="utf-8"))
    for rel in ("packs/CLAUDE.md", "profiles/CLAUDE.md"):
        projected = DATA_SCAFFOLD / rel
        assert projected.is_file(), f"{rel} is not projected into the scaffold"
        assert projected.read_bytes() == b"@AGENTS.md\n", (
            f"{rel} must be exactly the `@AGENTS.md` import line"
        )
        assert rel in manifest.get("files", {}), (
            f"{rel} is on disk but absent from manifest.json, so `catalogue init` "
            "will not write it and `find_unexpected_files` will report it"
        )


def test_projection_byte_identical_to_repo_root() -> None:
    drifts = [
        scaffold_rel
        for source, scaffold_rel in _sync_pairs()
        if not (DATA_SCAFFOLD / scaffold_rel).exists()
        or source.read_bytes() != (DATA_SCAFFOLD / scaffold_rel).read_bytes()
    ]
    assert not drifts, f"scaffold projection is out of sync: {drifts}"
