# STUB: AC-0001, AC-0018
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = PACK_ROOT / ".apm/skills/work-intake/scripts/intent_rename.py"
SOURCE = "docs/product/intents/FEAT-0001-source.md"
SUCCESSOR = "docs/product/intents/STRAT-0001-source.md"
TOMBSTONE_DATE = date(2026, 9, 29)
LEDGER = "/".join(
    ("docs", "specs", "intent-rename-transaction", "notes", "verification-ledger.md")
)


def _load() -> Any:
    spec = importlib.util.spec_from_file_location("core_work_intake_intent_rename_citations", SCRIPT)
    assert spec and spec.loader, SCRIPT
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rename = _load()


def _init_index(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)


def _commit(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test Runner"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "fixture"],
        cwd=root,
        check=True,
        capture_output=True,
    )


def _rename_fixture(root: Path, extras: dict[str, str] | None = None) -> None:
    source = root / SOURCE
    source.parent.mkdir(parents=True)
    source.write_text(
        "# Source\n\n"
        "- **Slug:** `source`\n"
        "- **Status:** Draft\n"
        "- **Level:** feature\n"
        "- **Owner:** test-owner\n\n"
        f"Self: {SOURCE}\n",
        encoding="utf-8",
    )
    (root / "citation.md").write_text(f"See {SOURCE}.\n", encoding="utf-8")
    (root / "workspace.toml").write_text(
        "[backlog]\n"
        f'open = [{{path = "{SOURCE}", kind = "intent", '
        'source = {mode = "repo-origin"}, summary = "rename", needs = []}]\n',
        encoding="utf-8",
    )
    for relative, text in (extras or {}).items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    _commit(root)


def _interrupt_after_successor(checkpoint: str) -> None:
    if checkpoint == "after-successor":
        raise rename.InjectedInterruption(checkpoint)


def test_ac_0001_and_ac_0018_public_rename_repoints_every_citation_and_nothing_else(
    tmp_path: Path,
) -> None:
    """Through the public rename: no stale path remains, and citers change only by substitution."""
    extras = {
        "inline.md": f"[source]({SOURCE})\n",
        "header.md": f"- **Discovery:** {SOURCE}\n",
        "config.toml": f'path = "{SOURCE}"\n',
        "fence.md": f"```text\n{SOURCE}\n```\ntwice: {SOURCE}\n",
        LEDGER: f"measured against {SOURCE}\n",
        "docs/specs/example/notes/verification-ledger.md": f"{SOURCE}\n",
        "unrelated.md": "No citation here.\n",
    }
    _rename_fixture(tmp_path, extras)

    def tree() -> dict[str, bytes]:
        return {
            path.relative_to(tmp_path).as_posix(): path.read_bytes()
            for path in tmp_path.rglob("*")
            if path.is_file() and ".git" not in path.relative_to(tmp_path).parts
        }

    before = tree()

    result = rename.run_intent_rename(
        SOURCE, "STRAT", repository_root=tmp_path, _today=lambda: TOMBSTONE_DATE
    )

    assert result.status is rename.RenameStatus.COMMITTED, result
    after = tree()
    stale = {
        relative for relative, data in after.items() if SOURCE.encode() in data
    }
    assert stale == {LEDGER}
    assert after[SUCCESSOR] == before[SOURCE].replace(SOURCE.encode(), SUCCESSOR.encode())
    assert set(after) == set(before) | {SUCCESSOR}
    for relative, data in before.items():
        if relative in {SOURCE, LEDGER}:
            continue
        assert after[relative] == data.replace(SOURCE.encode(), SUCCESSOR.encode()), relative
    assert after[LEDGER] == before[LEDGER]


def test_ac_0001_and_ac_0018_derived_set_equals_independent_string_search(
    tmp_path: Path,
) -> None:
    intents = tmp_path / "docs/product/intents"
    intents.mkdir(parents=True)
    fixtures = {
        SOURCE: f"# Source\n\n- **Slug:** `source`\n\nSelf: {SOURCE}\n",
        "inline.md": f"[source]({SOURCE})\n",
        "header.md": f"- **Discovery:** {SOURCE}\n",
        "config.toml": f'path = "{SOURCE}"\n',
        "fence.md": f"```text\n{SOURCE}\n```\n",
        LEDGER: SOURCE,
        "notes/verification-ledger.md": SOURCE,
        "docs/specs/example/verification-ledger.md": SOURCE,
        "docs/specs/example/notes/verification-ledger.md": SOURCE,
        "docs/specs/example/notes/other-ledger.md": SOURCE,
    }
    for relative, text in fixtures.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    _init_index(tmp_path)

    actual = set(
        rename.derive_citing_paths(
            SOURCE, SUCCESSOR, repository_root=tmp_path, created_paths=(SUCCESSOR,)
        )
    )
    expected = {
        relative
        for relative, text in fixtures.items()
        if SOURCE in text and relative not in {SOURCE, LEDGER}
    }

    assert actual == expected
    assert LEDGER not in actual
    for relative in actual:
        before = (tmp_path / relative).read_bytes()
        after = rename.repoint_citation_bytes(before, SOURCE, SUCCESSOR)
        assert after == before.replace(SOURCE.encode(), SUCCESSOR.encode())


def test_spec_verification_ledger_is_excluded_from_derived_writes(
    tmp_path: Path,
) -> None:
    ledger_before = f"before {SOURCE} middle {SOURCE} after\n"
    _rename_fixture(tmp_path, {LEDGER: ledger_before})

    derived = rename._derive(
        tmp_path,
        operation_id="0" * 32,
        base_commit=rename._head(tmp_path),
        source=SOURCE,
        target_token="STRAT",
        date=TOMBSTONE_DATE.isoformat(),
        successor=SUCCESSOR,
    )
    writes = {item.path: item for item in derived.writes}

    assert LEDGER not in writes
    assert (tmp_path / LEDGER).read_text(encoding="utf-8") == ledger_before


def test_derivation_uses_bounded_literal_git_parent_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "inline.md").write_text(f"See {SOURCE}.\n", encoding="utf-8")
    _init_index(tmp_path)
    calls: list[list[str]] = []
    original = rename._git

    def recording_git(root: Path, arguments: list[str], *, max_bytes: int) -> bytes:
        calls.append(arguments)
        return original(root, arguments, max_bytes=max_bytes)

    monkeypatch.setattr(rename, "_git", recording_git)

    assert rename.derive_citing_paths(SOURCE, repository_root=tmp_path) == ("inline.md",)
    assert ["ls-files", "-z", "--"] in calls


@pytest.mark.parametrize(
    ("source_rel", "projection_rel"),
    (
        (
            "packs/core/.apm/skills/work-intake/SKILL.md",
            ".agents/skills/work-intake/SKILL.md",
        ),
        (
            "packs/core/.apm/skills/work-intake/SKILL.md",
            ".claude/skills/work-intake/SKILL.md",
        ),
        (
            "packs/core/.apm/agents/implementer.md",
            ".claude/agents/implementer.md",
        ),
        (
            "packs/core/.apm/commands/conventions-check.md",
            ".claude/commands/conventions-check.md",
        ),
        (
            "packs/core/.apm/agents/implementer.md",
            ".codex/agents/implementer.toml",
        ),
        (
            "packs/core/.apm/hooks/pre-tool.py",
            "tools/hooks/pre-tool.py",
        ),
    ),
)
def test_direct_self_host_projection_maps_to_unique_tracked_apm_source(
    tmp_path: Path, source_rel: str, projection_rel: str
) -> None:
    source = tmp_path / source_rel
    projection = tmp_path / projection_rel
    source.parent.mkdir(parents=True)
    projection.parent.mkdir(parents=True)
    source.write_text(f"Source cites {SOURCE}.\n", encoding="utf-8")
    projection.write_text(f"Projection cites {SOURCE}.\n", encoding="utf-8")
    _init_index(tmp_path)

    assert rename.derive_citing_paths(SOURCE, repository_root=tmp_path) == (
        source_rel,
    )


@pytest.mark.parametrize(
    "projection_rel", (".claude/settings.local.json", ".codex/hooks.json")
)
def test_merged_self_host_projection_maps_to_unique_citing_hook_wiring_source(
    tmp_path: Path, projection_rel: str
) -> None:
    source_rel = "packs/core/.apm/hook-wiring/work-intake.toml"
    source = tmp_path / source_rel
    projection = tmp_path / projection_rel
    source.parent.mkdir(parents=True)
    projection.parent.mkdir(parents=True)
    source.write_text(f'path = "{SOURCE}"\n', encoding="utf-8")
    projection.write_text(f'{{"path":"{SOURCE}"}}\n', encoding="utf-8")
    _init_index(tmp_path)

    assert rename.derive_citing_paths(SOURCE, repository_root=tmp_path) == (
        source_rel,
    )


def test_projection_source_is_repointed_exactly_without_staging_projection(
    tmp_path: Path,
) -> None:
    source_rel = "packs/core/.apm/skills/work-intake/SKILL.md"
    projection_rel = ".agents/skills/work-intake/SKILL.md"
    source_before = f"before {SOURCE} middle {SOURCE} after\n"
    projection_before = f"generated {SOURCE}\n"
    _rename_fixture(
        tmp_path,
        {source_rel: source_before, projection_rel: projection_before},
    )

    derived = rename._derive(
        tmp_path,
        operation_id="0" * 32,
        base_commit=rename._head(tmp_path),
        source=SOURCE,
        target_token="STRAT",
        date=TOMBSTONE_DATE.isoformat(),
        successor=SUCCESSOR,
    )
    writes = {item.path: item for item in derived.writes}

    assert projection_rel not in writes
    assert writes[source_rel].preimage == source_before.encode()
    assert writes[source_rel].postimage == source_before.replace(
        SOURCE, SUCCESSOR
    ).encode()
    assert (tmp_path / projection_rel).read_text(encoding="utf-8") == projection_before


@pytest.mark.parametrize(
    ("guarded_rel", "extras"),
    (
        ("citation.md", {}),
        (
            "packs/core/.apm/skills/work-intake/SKILL.md",
            {
                "packs/core/.apm/skills/work-intake/SKILL.md": f"Source cites {SOURCE}.\n",
                ".agents/skills/work-intake/SKILL.md": f"Projection cites {SOURCE}.\n",
            },
        ),
    ),
)
def test_index_only_change_to_derived_target_refuses_before_staging(
    tmp_path: Path, guarded_rel: str, extras: dict[str, str]
) -> None:
    """A clean worktree cannot hide a different staged citation postimage."""
    _rename_fixture(tmp_path, extras)
    guarded = tmp_path / guarded_rel
    original = guarded.read_bytes()
    guarded.write_bytes(b"index-only replacement\n")
    subprocess.run(["git", "add", "--", guarded_rel], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "restore", "--source=HEAD", "--worktree", "--", guarded_rel],
        cwd=tmp_path,
        check=True,
    )
    index_before = subprocess.run(
        ["git", "diff", "--cached", "--binary", "--", guarded_rel],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    ).stdout
    assert index_before
    assert guarded.read_bytes() == original

    result = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _today=lambda: TOMBSTONE_DATE,
    )

    assert result.status is rename.RenameStatus.REFUSED
    assert result.code == "path-dirty"
    assert guarded.read_bytes() == original
    assert not (tmp_path / SUCCESSOR).exists()
    assert not list((tmp_path / "docs/product/intents").glob(".intent-rename-*"))
    assert (
        subprocess.run(
            ["git", "diff", "--cached", "--binary", "--", guarded_rel],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        ).stdout
        == index_before
    )


def test_hidden_derived_citation_refuses_before_staging(tmp_path: Path) -> None:
    """An assume-unchanged bit is not positive proof that a citation is clean."""
    _rename_fixture(tmp_path)
    subprocess.run(
        ["git", "update-index", "--assume-unchanged", "citation.md"],
        cwd=tmp_path,
        check=True,
    )
    before = (tmp_path / "citation.md").read_bytes()

    result = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _today=lambda: TOMBSTONE_DATE,
    )

    assert result.status is rename.RenameStatus.REFUSED
    assert result.code == "path-dirty"
    assert (tmp_path / "citation.md").read_bytes() == before
    assert not (tmp_path / SUCCESSOR).exists()
    assert not list((tmp_path / "docs/product/intents").glob(".intent-rename-*"))


def test_derived_citation_probe_failure_refuses_before_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed Git proof for a derived target has the fixed dirty refusal."""
    _rename_fixture(tmp_path)
    original_git = rename._git

    # The dirty proof runs through the operation's own bounded `_git`.
    def fail_citation_probe(root: Path, arguments: list[str], *, max_bytes: int) -> bytes:
        if "ls-files" in arguments and "citation.md" in arguments:
            raise subprocess.TimeoutExpired(arguments, 10)
        return original_git(root, arguments, max_bytes=max_bytes)

    monkeypatch.setattr(rename, "_git", fail_citation_probe)
    before = (tmp_path / "citation.md").read_bytes()

    result = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _today=lambda: TOMBSTONE_DATE,
    )

    assert result.status is rename.RenameStatus.REFUSED
    assert result.code == "path-dirty"
    assert (tmp_path / "citation.md").read_bytes() == before
    assert not (tmp_path / SUCCESSOR).exists()
    assert not list((tmp_path / "docs/product/intents").glob(".intent-rename-*"))


def test_direct_projection_with_ambiguous_pack_sources_refuses(tmp_path: Path) -> None:
    projection = tmp_path / ".agents/skills/work-intake/SKILL.md"
    projection.parent.mkdir(parents=True)
    projection.write_text(f"Projection cites {SOURCE}.\n", encoding="utf-8")
    for pack in ("core", "other"):
        source = tmp_path / f"packs/{pack}/.apm/skills/work-intake/SKILL.md"
        source.parent.mkdir(parents=True)
        source.write_text(f"Source cites {SOURCE}.\n", encoding="utf-8")
    _init_index(tmp_path)

    with pytest.raises(ValueError, match="projection-source-ambiguous"):
        rename.derive_citing_paths(SOURCE, repository_root=tmp_path)


def test_merged_projection_with_ambiguous_citing_sources_refuses(tmp_path: Path) -> None:
    projection = tmp_path / ".codex/hooks.json"
    projection.parent.mkdir(parents=True)
    projection.write_text(f'{{"path":"{SOURCE}"}}\n', encoding="utf-8")
    for pack in ("core", "other"):
        source = tmp_path / f"packs/{pack}/.apm/hook-wiring/hooks.toml"
        source.parent.mkdir(parents=True)
        source.write_text(f'path = "{SOURCE}"\n', encoding="utf-8")
    _init_index(tmp_path)

    with pytest.raises(ValueError, match="projection-source-ambiguous"):
        rename.derive_citing_paths(SOURCE, repository_root=tmp_path)


def test_projection_without_tracked_citing_source_refuses(tmp_path: Path) -> None:
    projection = tmp_path / ".claude/commands/conventions-check.md"
    projection.parent.mkdir(parents=True)
    projection.write_text(f"Projection cites {SOURCE}.\n", encoding="utf-8")
    _init_index(tmp_path)

    with pytest.raises(ValueError, match="projection-source-missing"):
        rename.derive_citing_paths(SOURCE, repository_root=tmp_path)


def test_untracked_created_successor_participates_in_search(tmp_path: Path) -> None:
    (tmp_path / "inline.md").write_text("No old path here.\n", encoding="utf-8")
    _init_index(tmp_path)
    successor = tmp_path / SUCCESSOR
    successor.parent.mkdir(parents=True)
    successor.write_text(f"Created bytes still cite {SOURCE}.\n", encoding="utf-8")

    assert rename.derive_citing_paths(
        SOURCE, SUCCESSOR, repository_root=tmp_path, created_paths=(SUCCESSOR,)
    ) == (SUCCESSOR,)


def test_non_utf8_citing_file_refuses(tmp_path: Path) -> None:
    (tmp_path / "binary.md").write_bytes(b"\xff" + SOURCE.encode("utf-8"))
    _init_index(tmp_path)

    with pytest.raises(ValueError, match="citation-not-text"):
        rename.derive_citing_paths(SOURCE, repository_root=tmp_path)


def test_tracked_file_and_byte_budgets_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "one.md").write_text(f"{SOURCE}\n", encoding="utf-8")
    (tmp_path / "two.md").write_text("other\n", encoding="utf-8")
    _init_index(tmp_path)

    monkeypatch.setattr(rename, "_MAX_TRACKED_FILES", 1)
    with pytest.raises(ValueError, match="tracked-file-bound"):
        rename.derive_citing_paths(SOURCE, repository_root=tmp_path)

    monkeypatch.setattr(rename, "_MAX_TRACKED_FILES", 100)
    monkeypatch.setattr(rename, "_MAX_CITING_BYTES", len(SOURCE) - 1)
    with pytest.raises(ValueError, match="citation-bound"):
        rename.derive_citing_paths(SOURCE, repository_root=tmp_path)


def test_dirty_tracked_file_citing_source_only_live_refuses_the_rename(
    tmp_path: Path,
) -> None:
    """A citation present only in a dirty working copy cannot escape the sweep."""
    _rename_fixture(tmp_path, {"notes.md": "No citation committed here.\n"})
    (tmp_path / "notes.md").write_text(f"Now cites {SOURCE}.\n", encoding="utf-8")
    before = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(tmp_path).parts
    }

    result = rename.run_intent_rename(SOURCE, "STRAT", repository_root=tmp_path)

    assert result.status is rename.RenameStatus.REFUSED
    assert result.code == "path-dirty"
    after = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(tmp_path).parts
    }
    assert after == before
    assert not list((tmp_path / "docs/product/intents").glob(".intent-rename-*"))


def test_unrelated_staged_add_does_not_disturb_the_pinned_derivation(
    tmp_path: Path,
) -> None:
    """An index-only file absent from the pinned commit is outside the snapshot."""
    _rename_fixture(tmp_path)
    (tmp_path / "staged-only.md").write_text("Unrelated.\n", encoding="utf-8")
    subprocess.run(["git", "add", "staged-only.md"], cwd=tmp_path, check=True)

    result = rename.run_intent_rename(SOURCE, "STRAT", repository_root=tmp_path)

    assert result.status is rename.RenameStatus.COMMITTED, result
    assert (tmp_path / "citation.md").read_text(encoding="utf-8") == f"See {SUCCESSOR}.\n"


def test_git_reads_refuse_once_output_exceeds_their_byte_budget(
    tmp_path: Path,
) -> None:
    """Git output is bounded while consumed, not after it is fully buffered."""
    (tmp_path / "large.md").write_bytes(b"x" * 300_000)
    _commit(tmp_path)

    assert len(rename._git_file(tmp_path, "HEAD", "large.md", max_bytes=300_000)) == 300_000
    with pytest.raises(ValueError, match="git-output-bound"):
        rename._git_file(tmp_path, "HEAD", "large.md", max_bytes=299_999)
    with pytest.raises(ValueError, match="git-output-bound"):
        rename._git(tmp_path, ["ls-files", "-z", "--"], max_bytes=3)


def test_recovery_refuses_forward_and_back_when_citation_set_record_changes(
    tmp_path: Path,
) -> None:
    for direction in ("forward", "back"):
        root = tmp_path / direction
        root.mkdir()
        _rename_fixture(root)
        partial = rename.run_intent_rename(
            SOURCE,
            "STRAT",
            repository_root=root,
            _checkpoint=_interrupt_after_successor,
            _today=lambda: TOMBSTONE_DATE,
        )
        assert partial.status is rename.RenameStatus.PARTIAL
        stage = next((root / "docs/product/intents").glob(".intent-rename-*"))
        record_path = stage / "record.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["writes"] = [
            item for item in record["writes"] if item["path"] != "citation.md"
        ]
        record_path.write_bytes(rename._canonical_json(record))
        before_source = (root / SOURCE).read_bytes()
        before_citation = (root / "citation.md").read_bytes()

        result = rename.recover_intent_rename(
            direction,
            SOURCE,
            "STRAT",
            TOMBSTONE_DATE.isoformat(),
            repository_root=root,
        )

        assert result.status is rename.RenameStatus.REFUSED
        assert result.code == "record-mismatch"
        assert (root / SOURCE).read_bytes() == before_source
        assert (root / "citation.md").read_bytes() == before_citation
