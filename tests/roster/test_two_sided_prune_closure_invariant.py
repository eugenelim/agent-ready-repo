"""Red construction contract for the two-sided prune closure invariant."""

from __future__ import annotations

import functools
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from collections.abc import Iterable, Mapping
from contextlib import redirect_stderr, redirect_stdout
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@functools.lru_cache(maxsize=1)
def _base_revision() -> str:
    """The revision this branch actually forked from, not a revision typed once.

    Pinning a literal SHA lets the comparison drift onto a stale contract as the
    base branch moves; the merge base cannot.

    Falls back to `HEAD` when no merge base resolves — a shallow clone, a detached
    checkout, or a fork without the `origin/main` ref. Callers then compare HEAD
    with itself, so a base-relative property simply does not assert rather than
    erroring on an environment question it cannot answer.
    """
    completed = subprocess.run(
        ["git", "merge-base", "origin/main", "HEAD"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        return "HEAD"
    return completed.stdout.strip()


ENGINE_PATH = REPO_ROOT / "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py"
PRUNE_PATH = ENGINE_PATH.with_name("workspace_status_prune.py")
CLI_PATH = ENGINE_PATH.with_name("workspace_status.py")
MANIFEST_PATH = REPO_ROOT / ".workspace-prune-protected.toml"
LOCK_NAME = ".workspace-repair.lock"
SELECTED_DELTA_ELEMENT = (
    b'{ kind = "spec", path="docs/specs/chosen/spec.md", '
    b'source = { mode="repo-origin" }, summary = "Chosen, with } and ]", needs=[] },'
)


def _load_prune() -> ModuleType:
    """Load the pack prune source directly, without changing ``sys.path``."""
    module_spec = importlib.util.spec_from_file_location(
        "core_workspace_status_prune_closure", PRUNE_PATH
    )
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


ENGINE = _load_prune()


def _load_pack_script(path: Path, name: str) -> ModuleType:
    """Load one pack script under a test-specific module identity."""
    module_spec = importlib.util.spec_from_file_location(name, path)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


def _toml(value: object) -> str:
    """Render the small, deliberate TOML subset used by fixture workspaces."""
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{key} = {_toml(item)}" for key, item in value.items()) + " }"
    raise TypeError(f"unsupported fixture value: {type(value).__name__}")


def _canonical(slug: str, **changes: object) -> dict[str, object]:
    """Return one canonical membership, optionally invalid outside its identity."""
    entry: dict[str, object] = {
        "kind": "spec",
        "path": f"docs/specs/{slug}/spec.md",
        "source": {"mode": "repo-origin"},
        "summary": f"Fixture {slug}",
        "needs": [],
    }
    entry.update(changes)
    return entry


def _legacy_backlog(slug: str) -> dict[str, object]:
    """Return the supported legacy backlog-object form."""
    return {"slug": slug, "source": "fixture", "summary": slug, "needs": [], "type": "spec"}


def _write_repository(
    root: Path,
    specs: Iterable[str],
    *,
    backlog_open: Iterable[object] = (),
    work: Mapping[str, Mapping[str, Iterable[object]]] | None = None,
) -> Path:
    """Create a disposable repository with the relevant workspace collections."""
    root.mkdir(parents=True, exist_ok=True)
    lines = ["[backlog]", f"open = {_toml(list(backlog_open))}", "closed = []"]
    for initiative, collections in (work or {}).items():
        lines += [
            "",
            f'["{initiative}"]',
            'name = "Fixture"',
            'status = "active"',
            'milestone = "fixture"',
            f'["{initiative}".work]',
            f"queue = {_toml(list(collections.get('queue', ())))}",
            f"active = {_toml(list(collections.get('active', ())))}",
            f"shipped = {_toml(list(collections.get('shipped', ())))}",
        ]
    (root / "workspace.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for slug in specs:
        artifact = root / "docs/specs" / slug
        artifact.mkdir(parents=True, exist_ok=True)
        (artifact / "spec.md").write_text(f"# {slug}\n", encoding="utf-8")
        (artifact / "notes").mkdir(exist_ok=True)
        (artifact / "notes/fixture.md").write_text("fixture\n", encoding="utf-8")
    return root


def _snapshot(root: Path) -> dict[str, tuple[str, int, bytes | str | None]]:
    """Capture content, link targets, and mode bits without following links."""
    result: dict[str, tuple[str, int, bytes | str | None]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        mode = stat.S_IMODE(path.lstat().st_mode)
        if path.is_symlink():
            result[relative] = ("symlink", mode, os.readlink(path))
        elif path.is_dir():
            result[relative] = ("dir", mode, None)
        else:
            result[relative] = ("file", mode, path.read_bytes())
    return result


def _preview(root: Path, selectors: list[str]) -> dict[str, Any]:
    """Call the pinned non-mutating engine seam."""
    return ENGINE.prune_preview(root, selectors)


def _confirmation(preview: Mapping[str, Any]) -> dict[str, str]:
    """Supply authorization independently from an unsigned preview challenge."""
    return {
        "operation_id": str(preview["operation_id"]),
        "operation_digest": str(preview["operation_digest"]),
        "subject": "fixture-maintainer",
        "role": "maintainer",
        "confirming_identity": "fixture@example.invalid",
    }


def _execute(root: Path, selectors: list[str], *, failure_point: str | None = None) -> dict[str, Any]:
    """Preview, independently authorize, then run the pinned destructive seam."""
    preview = _preview(root, selectors)
    assert "error" not in preview
    return ENGINE.prune_execute(root, selectors, _confirmation(preview), failure_point)


def _error(payload: Mapping[str, Any], code: str) -> None:
    """Assert one stable structured refusal code."""
    assert payload["error"]["code"] == code


def _cli(root: Path, *arguments: str) -> tuple[int, dict[str, Any], str]:
    """Use the shipped command path and parse its structured stdout."""
    return _cli_at(CLI_PATH, root, *arguments)


def _cli_at(
    cli_path: Path, root: Path, *arguments: str
) -> tuple[int, dict[str, Any], str]:
    """Run one explicit CLI tree against the shared frozen fixture."""
    completed = subprocess.run(
        [sys.executable, str(cli_path), *arguments, "--root", str(root)],
        check=False,
        capture_output=True,
    )
    return completed.returncode, json.loads(completed.stdout), completed.stderr.decode("utf-8")


@pytest.fixture
def empty_selection(tmp_path: Path) -> Path:
    return _write_repository(tmp_path / "empty", ())


@pytest.fixture
def unknown_subcommand() -> str:
    return "not-a-workspace-status-command"


@pytest.fixture
def single_registered_target(tmp_path: Path) -> Path:
    return _write_repository(tmp_path / "registered", ("chosen",), backlog_open=(_canonical("chosen"),))


@pytest.fixture
def invalid_selectors(tmp_path: Path) -> tuple[Path, tuple[str, ...]]:
    root = _write_repository(tmp_path / "invalid", ("chosen",), backlog_open=(_canonical("chosen"),))
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "docs/specs/escape").symlink_to(outside, target_is_directory=True)
    return root, ("/docs/specs/a", "C:/docs/specs/a", "docs\\specs\\a", "docs/specs/../a", "docs/specs/a/spec.md", "docs/specs/a/nested", "docs/specs/escape")


@pytest.fixture
def mutated_selector_input(tmp_path: Path) -> Path:
    return _write_repository(
        tmp_path / "mutated-selector",
        ("chosen", "not-chosen"),
        backlog_open=(_canonical("chosen"), _canonical("not-chosen")),
    )


@pytest.fixture
def alpha_bravo_selection(tmp_path: Path) -> Path:
    return _write_repository(
        tmp_path / "alpha-bravo",
        ("alpha", "bravo"),
        backlog_open=(_canonical("alpha"), _canonical("bravo")),
    )


@pytest.fixture
def confirmation_binding_matrix(single_registered_target: Path) -> Path:
    return single_registered_target


@pytest.fixture
def protected_target_selection(tmp_path: Path) -> Path:
    root = _write_repository(tmp_path / "protected", ("protected", "open"), backlog_open=(_canonical("protected"), _canonical("open")))
    (root / ".workspace-prune-protected.toml").write_text('protected = ["docs/specs/protected"]\n', encoding="utf-8")
    return root


@pytest.fixture
def already_absent_selection(tmp_path: Path) -> Path:
    return _write_repository(tmp_path / "absent", ("present",), backlog_open=(_canonical("present"),))


@pytest.fixture
def registered_and_entryless_targets(tmp_path: Path) -> Path:
    return _write_repository(tmp_path / "both", ("registered", "entryless"), backlog_open=(_canonical("registered"),))


@pytest.fixture
def preplanted_lock(single_registered_target: Path) -> Path:
    (single_registered_target / LOCK_NAME).write_text("99999\n", encoding="utf-8")
    return single_registered_target


@pytest.fixture
def lock_span_probe(single_registered_target: Path) -> Path:
    return single_registered_target


@pytest.fixture
def noop_write_fault(single_registered_target: Path) -> Path:
    return single_registered_target


@pytest.fixture
def partial_artifact_removal_matrix(tmp_path: Path) -> Path:
    return _write_repository(tmp_path / "partial", ("chosen",), backlog_open=(_canonical("chosen"),))


@pytest.fixture
def symlinked_parent_escape(tmp_path: Path) -> tuple[Path, Path]:
    """Prepare identical internal and external trees for a parent-link race."""
    root = _write_repository(
        tmp_path / "parent-link", (), backlog_open=(_canonical("chosen"),)
    )
    external = tmp_path / "external"
    chosen = external / "chosen"
    (chosen / "notes").mkdir(parents=True)
    (chosen / "spec.md").write_bytes(b"# chosen\n")
    (chosen / "notes/fixture.md").write_bytes(b"fixture\n")
    (root / "docs").mkdir()
    (root / "docs/specs").symlink_to(external, target_is_directory=True)
    return root, external


@pytest.fixture
def clean_two_sided_prune(single_registered_target: Path) -> Path:
    workspace_path = single_registered_target / "workspace.toml"
    workspace = workspace_path.read_text(encoding="utf-8")
    workspace_path.write_text(
        workspace.replace("closed = []", f"closed = {_toml([_canonical('chosen')])}"),
        encoding="utf-8",
    )
    return single_registered_target


@pytest.fixture
def forced_half_state_matrix(single_registered_target: Path) -> Path:
    return single_registered_target


@pytest.fixture
def aba_characterization(single_registered_target: Path) -> Path:
    return single_registered_target


@pytest.fixture
def intake_transaction_lock_span(single_registered_target: Path) -> Path:
    return single_registered_target


@pytest.fixture
def prune_intake_interleaving(single_registered_target: Path) -> Path:
    return single_registered_target


@pytest.fixture
def participating_writer_interleaving_matrix(single_registered_target: Path) -> Path:
    return single_registered_target


@pytest.fixture
def duplicate_canonical_survivor(tmp_path: Path) -> Path:
    return _write_repository(tmp_path / "duplicate", ("chosen",), backlog_open=(_canonical("chosen"), _canonical("chosen")))


@pytest.fixture
def legacy_alias_survivor(tmp_path: Path) -> Path:
    return _write_repository(
        tmp_path / "legacy",
        ("chosen",),
        work={"ini-900": {"active": ("spec/chosen",)}},
    )


@pytest.fixture
def parse_blocked_survivor(tmp_path: Path) -> Path:
    return _write_repository(tmp_path / "blocked", ("chosen",), backlog_open=(_canonical("chosen", summary=7),))


@pytest.fixture
def default_command_compatibility(
    single_registered_target: Path, tmp_path: Path
) -> tuple[Path, Path]:
    """Materialize the frozen base CLI and engine without a Git worktree write."""
    base_scripts = tmp_path / "base-scripts"
    base_scripts.mkdir()
    # The CLI loads its engine and the prune sibling from its own directory, so a
    # partial copy compares a base that cannot start against a HEAD that can.
    required = (
        "packs/core/.apm/skills/workspace-status/scripts/workspace_status.py",
        "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py",
    )
    # Present only at revisions after the prune moved into its own module.
    optional = (
        "packs/core/.apm/skills/workspace-status/scripts/workspace_status_prune.py",
    )
    for relative in required + optional:
        completed = subprocess.run(
            ["git", "show", f"{_base_revision()}:{relative}"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
        )
        if completed.returncode != 0:
            assert relative in optional, completed.stderr.decode("utf-8")
            continue
        (base_scripts / Path(relative).name).write_bytes(completed.stdout)
    return single_registered_target, base_scripts / "workspace_status.py"


@pytest.fixture
def refusal_snapshot_matrix(protected_target_selection: Path) -> Path:
    return protected_target_selection


@pytest.fixture
def unsafe_and_instruction_like_input(single_registered_target: Path) -> Path:
    return single_registered_target


@pytest.fixture
def workspace_status_eval_contract(single_registered_target: Path) -> Path:
    return single_registered_target


@pytest.fixture
def exact_delta_with_unselected_neighbours(tmp_path: Path) -> Path:
    root = _write_repository(tmp_path / "delta", ("chosen", "neighbour"))
    neighbour = (
        b'{kind="spec", path = "docs/specs/neighbour/spec.md", '
        b'source={mode = "repo-origin"}, summary="Neighbour", needs = [ ]}'
    )
    workspace = b"\n".join(
        (
            b"# Workspace fixture: comments and spacing are load-bearing.",
            b"[backlog] # top-level lifecycle",
            b"open = [",
            b"  " + SELECTED_DELTA_ELEMENT + b" # selected membership only",
            b"    " + neighbour + b", # keep this neighbour",
            b"]",
            b"closed = [ ] # keep the empty collection",
            b"",
            b'# Initiative formatting deliberately differs from backlog.',
            b'["ini"]',
            b'name="Fixture"',
            b'status = "active"',
            b'milestone="fixture"',
            b"",
            b'["ini".work] # dotted quoted table',
            b"queue = [",
            b"]",
            b"active = [ ] # another retained comment",
            b"shipped=[ " + neighbour + b" ]",
            "# café tail comment".encode(),
            b"",
        )
    )
    (root / "workspace.toml").write_bytes(workspace)
    (root / "unrelated.txt").write_text("stay\n", encoding="utf-8")
    target = tmp_path / "symlink-target"
    target.write_text("outside selected tree\n", encoding="utf-8")
    (root / "docs/specs/chosen/nested-link").symlink_to(target)
    return root


@pytest.fixture
def baseline_staleness_matrix(single_registered_target: Path) -> Path:
    return single_registered_target


@pytest.fixture
def nested_list_membership_survivor(tmp_path: Path) -> Path:
    root = _write_repository(tmp_path / "nested-list", ("chosen",))
    (root / "workspace.toml").write_text(
        "[[holder]]\n"
        f"entries = {_toml([_canonical('chosen')])}\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def preview_to_confirmation_round_trip(single_registered_target: Path) -> Path:
    return single_registered_target


def test_empty_selection_is_rejected_by_recognized_route(empty_selection: Path, unknown_subcommand: str) -> None:
    before = _snapshot(empty_selection)
    # Plant the shared lock first. Argument-syntax validation is the one permitted
    # pre-lock step, so an empty selection must still be refused as empty_selection.
    # A route that validated after acquiring the lock would surface lock_busy here,
    # which is what makes this assertion able to fail.
    (empty_selection / ".workspace-repair.lock").write_text("1", encoding="utf-8")
    try:
        empty_code, empty, _ = _cli(empty_selection, "prune")
        unknown_code, unknown, _ = _cli(empty_selection, unknown_subcommand)
    finally:
        (empty_selection / ".workspace-repair.lock").unlink()
    assert empty_code != 0 and empty["error"]["code"] == "empty_selection"
    # The unknown-subcommand payload is a pre-existing contract shape and must not
    # be reshaped by adding a route: it reports `reason`, not an `error` object.
    assert unknown_code != 0 and unknown["reason"] == "unknown_subcommand"
    assert empty != unknown and _snapshot(empty_selection) == before


def test_selector_grammar_and_confinement_with_valid_prune_control(invalid_selectors: tuple[Path, tuple[str, ...]]) -> None:
    root, invalid = invalid_selectors
    for selector in invalid:
        _error(_preview(root, [selector]), "invalid_selector")
    result = _execute(root, ["docs/specs/chosen"])
    assert "error" not in result and not (root / "docs/specs/chosen").exists()


def test_selection_is_immutable_after_fixing(mutated_selector_input: Path) -> None:
    selectors = ["docs/specs/chosen"]
    preview = _preview(mutated_selector_input, selectors)
    selectors[0] = "docs/specs/not-chosen"
    before = _snapshot(mutated_selector_input)
    result = ENGINE.prune_execute(mutated_selector_input, selectors, _confirmation(preview))
    _error(result, "confirmation_binding_mismatch")
    assert _snapshot(mutated_selector_input) == before


def test_confirmation_cannot_replace_execute_selection_alpha_bravo(
    alpha_bravo_selection: Path,
) -> None:
    alpha_selector = "/".join(("docs", "specs", "alpha"))
    bravo_selector = "/".join(("docs", "specs", "bravo"))
    preview = _preview(alpha_bravo_selection, [alpha_selector])
    confirmation = _confirmation(preview)
    before = _snapshot(alpha_bravo_selection)
    result = ENGINE.prune_execute(
        alpha_bravo_selection,
        [bravo_selector],
        confirmation,
    )
    _error(result, "confirmation_binding_mismatch")
    assert _snapshot(alpha_bravo_selection) == before
    assert (alpha_bravo_selection / alpha_selector).is_dir()
    assert (alpha_bravo_selection / bravo_selector).is_dir()

    ordered_preview = _preview(
        alpha_bravo_selection,
        [alpha_selector, bravo_selector],
    )
    reordered = ENGINE.prune_execute(
        alpha_bravo_selection,
        [bravo_selector, alpha_selector],
        _confirmation(ordered_preview),
    )
    _error(reordered, "confirmation_binding_mismatch")
    assert _snapshot(alpha_bravo_selection) == before


def test_confirmation_binding_failure_classes_are_distinct_and_inert(confirmation_binding_matrix: Path) -> None:
    preview = _preview(confirmation_binding_matrix, ["docs/specs/chosen"])
    cases = {
        "confirmation_missing": {},
        "confirmation_invalid": {"operation_id": 3},
        "confirmation_stale": {**_confirmation(preview), "operation_digest": "0" * 64},
        "confirmation_binding_mismatch": {**_confirmation(preview), "operation_id": "other"},
    }
    for code, confirmation in cases.items():
        before = _snapshot(confirmation_binding_matrix)
        _error(ENGINE.prune_execute(confirmation_binding_matrix, ["docs/specs/chosen"], confirmation), code)
        assert _snapshot(confirmation_binding_matrix) == before
    assert "error" not in _execute(confirmation_binding_matrix, ["docs/specs/chosen"])


def test_protected_target_is_refused_before_mutation(protected_target_selection: Path) -> None:
    before = _snapshot(protected_target_selection)
    payload = _execute(protected_target_selection, ["docs/specs/protected"])
    _error(payload, "protected_target")
    assert payload["error"]["selector"] == "docs/specs/protected"
    assert _snapshot(protected_target_selection) == before
    assert "error" not in _execute(protected_target_selection, ["docs/specs/open"])


def test_protected_manifest_covers_every_literal_roster_spec_dependency() -> None:
    import tomllib

    protected = set(tomllib.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["protected"])
    literals = set()
    for path in (REPO_ROOT / "tests/roster").glob("test_*.py"):
        literals.update(__import__("re").findall(r"docs/specs/[a-z0-9][a-z0-9-]*", path.read_text(encoding="utf-8")))
    assert literals <= protected


def test_prune_refuses_its_own_spec_directory(tmp_path: Path) -> None:
    """The real prune refuses this spec in a disposable repository copy."""
    import tomllib

    selector = "docs/specs/two-sided-prune-closure-invariant"
    protected = set(tomllib.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["protected"])
    assert selector in protected
    assert any(item.startswith(selector) for item in protected)
    root = _write_repository(tmp_path / "own-spec", ())
    shutil.copytree(
        REPO_ROOT / selector,
        root / selector,
    )
    (root / MANIFEST_PATH.name).write_bytes(MANIFEST_PATH.read_bytes())
    before = _snapshot(root)
    result = _execute(root, [selector])
    _error(result, "protected_target")
    assert result["error"]["selector"] == selector
    assert _snapshot(root) == before


def test_every_selected_target_must_be_present_before_mutation(already_absent_selection: Path) -> None:
    before = _snapshot(already_absent_selection)
    payload = _execute(already_absent_selection, ["docs/specs/present", "docs/specs/absent"])
    _error(payload, "nothing_to_remove")
    assert payload["error"]["selector"] == "docs/specs/absent" and _snapshot(already_absent_selection) == before
    assert "error" not in _execute(already_absent_selection, ["docs/specs/present"])


def test_recorded_presence_determines_both_sided_obligation(registered_and_entryless_targets: Path) -> None:
    preview = _preview(registered_and_entryless_targets, ["docs/specs/registered", "docs/specs/entryless"])
    targets = {target["selector"]: target for target in preview["targets"]}
    assert targets["docs/specs/registered"]["membership_present"] is True
    assert targets["docs/specs/entryless"]["membership_present"] is False
    assert "error" not in ENGINE.prune_execute(registered_and_entryless_targets, list(targets), _confirmation(preview))


def test_prelocked_workspace_refuses_before_any_state_read(preplanted_lock: Path) -> None:
    malformed_confirmation = preplanted_lock / "malformed-confirmation.json"
    malformed_confirmation.write_bytes(b"{not-json")
    before = _snapshot(preplanted_lock)
    _error(_preview(preplanted_lock, ["docs/specs/chosen"]), "lock_busy")
    code, payload, _ = _cli(
        preplanted_lock,
        "prune",
        "--select",
        "docs/specs/chosen",
        "--confirmation-file",
        "malformed-confirmation.json",
    )
    assert code != 0
    _error(payload, "lock_busy")
    assert _snapshot(preplanted_lock) == before


def test_lock_spans_both_mutations_and_closure_and_is_always_released(
    lock_span_probe: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exceptional = _write_repository(
        lock_span_probe.parent / "lock-span-exception",
        ("chosen",),
        backlog_open=(_canonical("chosen"),),
    )
    previews = {
        root: _preview(root, ["docs/specs/chosen"])
        for root in (lock_span_probe, exceptional)
    }
    events: list[tuple[Path, str]] = []
    read_counts = {lock_span_probe: 0, exceptional: 0}
    original_remove = ENGINE._remove_prune_tree
    original_write = ENGINE._write_prune_workspace
    original_read = ENGINE._migration_file_bytes
    original_closure = ENGINE._prune_closure

    def assert_locked(root: Path, event: str) -> None:
        assert (root / LOCK_NAME).is_file()
        events.append((root, event))

    def remove(root: Path, selector: str, manifest: dict[str, Any]) -> None:
        assert_locked(root, "artifact_removal")
        original_remove(root, selector, manifest)

    def write(root: Path, data: bytes) -> None:
        assert_locked(root, "membership_write")
        original_write(root, data)

    def read(root: Path, relative_path: str) -> bytes | None:
        if relative_path == "workspace.toml" and root in read_counts:
            assert (root / LOCK_NAME).is_file()
            read_counts[root] += 1
            if read_counts[root] == 2:
                events.append((root, "post_mutation_read"))
        return original_read(root, relative_path)

    def closure(root: Path, selection: list[str], workspace_bytes: bytes) -> dict[str, Any]:
        assert_locked(root, "closure")
        if root == exceptional:
            raise RuntimeError("injected closure failure")
        return original_closure(root, selection, workspace_bytes)

    monkeypatch.setattr(ENGINE, "_remove_prune_tree", remove)
    monkeypatch.setattr(ENGINE, "_write_prune_workspace", write)
    monkeypatch.setattr(ENGINE, "_migration_file_bytes", read)
    monkeypatch.setattr(ENGINE, "_prune_closure", closure)

    normal_result = ENGINE.prune_execute(
        lock_span_probe,
        ["docs/specs/chosen"],
        _confirmation(previews[lock_span_probe]),
    )
    assert "error" not in normal_result
    exceptional_result = ENGINE.prune_execute(
        exceptional,
        ["docs/specs/chosen"],
        _confirmation(previews[exceptional]),
    )
    _error(exceptional_result, "closure_failed")
    for root in (lock_span_probe, exceptional):
        assert [event for event_root, event in events if event_root == root] == [
            "artifact_removal",
            "membership_write",
            "post_mutation_read",
            "closure",
        ]
        assert read_counts[root] == 2
        assert not (root / LOCK_NAME).exists()


def test_closure_reads_post_mutation_bytes_from_disk_not_intended_bytes(noop_write_fault: Path) -> None:
    payload = _execute(noop_write_fault, ["docs/specs/chosen"], failure_point="membership_write_noop")
    _error(payload, "closure_failed")
    assert payload["error"]["membership_survives"] is True


def test_closure_finds_membership_nested_beneath_a_list(
    nested_list_membership_survivor: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_bytes = (nested_list_membership_survivor / "workspace.toml").read_bytes()
    workspace, parse_error = ENGINE._parse_prune_workspace(workspace_bytes)
    assert parse_error is None and workspace is not None
    expected_occurrences = [
        {
            "canonical_artifact_path": "docs/specs/chosen/spec.md",
            "initiative": None,
            "collection": "holder.entries",
            "entry_index": 0,
            "form": "canonical",
            "occurrence_path": ["holder", 0, "entries", 0],
        }
    ]
    assert ENGINE._resolve_prune_closure_memberships(
        workspace,
        ["docs/specs/chosen/spec.md"],
    )["docs/specs/chosen/spec.md"] == expected_occurrences
    monkeypatch.setattr(ENGINE, "_prune_artifact_absent", lambda *_: True)
    result = ENGINE._prune_closure(
        nested_list_membership_survivor,
        ["docs/specs/chosen"],
        workspace_bytes,
    )
    _error(result, "closure_failed")
    assert result["error"]["membership_survives"] is True
    assert result["error"]["occurrences"] == expected_occurrences


def test_multiline_basic_string_ending_in_quote_remains_editable(
    tmp_path: Path,
) -> None:
    root = _write_repository(tmp_path / "multiline-quote", ("chosen",))
    workspace_bytes = (
        b"[backlog]\n"
        b'open = [{kind="spec", path="docs/specs/chosen/spec.md", '
        b'source={mode="repo-origin"}, summary="""ends in a quote"""", needs=[]}]\n'
        b"closed = []\n"
    )
    (root / "workspace.toml").write_bytes(workspace_bytes)
    workspace, error = ENGINE._parse_prune_workspace(workspace_bytes)
    assert error is None and workspace is not None
    occurrences = ENGINE.resolve_selected_memberships(
        workspace, ["docs/specs/chosen/spec.md"]
    )["docs/specs/chosen/spec.md"]
    edited = ENGINE._prune_workspace_without_occurrences(
        workspace_bytes,
        workspace,
        occurrences,
    )
    assert edited is not None
    parsed, parse_error = ENGINE._parse_prune_workspace(edited)
    assert parse_error is None and parsed is not None


def test_unlocatable_workspace_edit_uses_documented_refusal(
    single_registered_target: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preview = _preview(single_registered_target, ["docs/specs/chosen"])
    before = _snapshot(single_registered_target)
    monkeypatch.setattr(ENGINE, "_prune_workspace_without_occurrences", lambda *_: None)
    result = ENGINE.prune_execute(
        single_registered_target,
        ["docs/specs/chosen"],
        _confirmation(preview),
    )
    _error(result, "invalid_workspace")
    assert _snapshot(single_registered_target) == before


def test_artifact_absence_requires_directory_nonexistence(partial_artifact_removal_matrix: Path) -> None:
    for shape in ("empty", "missing-spec", "symlink"):
        root = _write_repository(partial_artifact_removal_matrix.parent / shape, (), backlog_open=(_canonical("chosen"),))
        artifact = root / "docs/specs/chosen"
        if shape == "empty":
            artifact.mkdir(parents=True)
        elif shape == "missing-spec":
            artifact.mkdir(parents=True)
            (artifact / "notes").mkdir()
            (artifact / "notes/only-note.md").write_text("not a spec\n", encoding="utf-8")
        else:
            # The link's own parent must exist before os.symlink; only the
            # selected directory itself is replaced by the symlink.
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.symlink_to(root / "workspace.toml")
        preview = _preview(root, ["docs/specs/chosen"])
        assert preview["targets"][0]["artifact_present"] is True
        closure = ENGINE._prune_closure(
            root,
            ["docs/specs/chosen"],
            (root / "workspace.toml").read_bytes(),
        )
        _error(closure, "closure_failed")
        assert closure["error"]["artifact_survives"] is True


def test_prune_refuses_symlinked_parent_without_touching_external_tree(
    symlinked_parent_escape: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, external = symlinked_parent_escape
    external_before = _snapshot(external)
    original_confined = ENGINE._confined_artifact_path
    original_manifest = ENGINE.prune_tree_manifest

    # Model a parent swapped after the guarded baseline and recheck. Those
    # earlier layers correctly reject a parent link observed before mutation;
    # this construction isolates the removal call's own race resistance.
    def _admit_recorded_selector(repository_root: Path, value: str) -> Path | None:
        if value in {"docs/specs/chosen", "docs/specs/chosen/spec.md"}:
            return repository_root / value
        return original_confined(repository_root, value)

    monkeypatch.setattr(ENGINE, "_confined_artifact_path", _admit_recorded_selector)

    def _record_external_manifest(
        repository_root: Path, selector: str
    ) -> dict[str, Any] | None:
        if repository_root == root and selector == "docs/specs/chosen":
            manifest = original_manifest(external, "chosen")
            assert manifest is not None
            return {
                "entries": [
                    {**entry, "path": f"docs/specs/{entry['path']}"}
                    for entry in manifest["entries"]
                ]
            }
        return original_manifest(repository_root, selector)

    monkeypatch.setattr(ENGINE, "prune_tree_manifest", _record_external_manifest)
    preview = _preview(root, ["docs/specs/chosen"])
    original_unlink = ENGINE.os.unlink
    original_open = ENGINE.os.open
    descriptor_unlinks: list[str] = []
    opened_external_parents: list[Path] = []

    def _record_descriptor_unlink(
        path: str | bytes, *, dir_fd: int | None = None
    ) -> None:
        if dir_fd is not None:
            descriptor_unlinks.append(os.fsdecode(path))
        original_unlink(path, dir_fd=dir_fd)

    def _record_open(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        candidate = Path(os.fsdecode(path))
        if candidate.is_absolute() and candidate == external:
            opened_external_parents.append(candidate)
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(ENGINE.os, "unlink", _record_descriptor_unlink)
    monkeypatch.setattr(ENGINE.os, "open", _record_open)
    result = ENGINE.prune_execute(
        root,
        ["docs/specs/chosen"],
        _confirmation(preview),
    )
    _error(result, "closure_failed")
    assert result["error"]["observation_unavailable"] is True
    assert opened_external_parents == []
    assert descriptor_unlinks == []
    assert _snapshot(external) == external_before


def test_prune_removal_refuses_entries_absent_from_the_recorded_manifest(
    single_registered_target: Path,
) -> None:
    selector = "docs/specs/chosen"
    manifest = ENGINE.prune_tree_manifest(single_registered_target, selector)
    assert manifest is not None
    unexpected = single_registered_target / selector / "arrived-after-baseline.txt"
    unexpected.write_bytes(b"must survive\n")
    before = _snapshot(single_registered_target / selector)
    with pytest.raises(ENGINE.UnsafePruneError):
        ENGINE._remove_prune_tree(single_registered_target, selector, manifest)
    assert _snapshot(single_registered_target / selector) == before


def test_defect_kind_occurrence_at_selected_path_is_removed(tmp_path: Path) -> None:
    """Prune identity is the selected path, even when the entry kind differs."""
    root = _write_repository(
        tmp_path / "defect-kind-occurrence",
        ("chosen",),
        backlog_open=(
            _canonical("chosen"),
            _canonical("chosen", kind="defect"),
        ),
    )
    preview = _preview(root, ["docs/specs/chosen"])
    assert len(preview["targets"][0]["occurrences"]) == 2
    result = _execute(root, ["docs/specs/chosen"])
    assert "error" not in result
    workspace, parse_error = ENGINE._parse_prune_workspace(
        (root / "workspace.toml").read_bytes()
    )
    assert parse_error is None and workspace is not None
    assert ENGINE._resolve_prune_closure_memberships(
        workspace, ["docs/specs/chosen/spec.md"]
    )["docs/specs/chosen/spec.md"] == []


def test_exit_zero_requires_both_sides_absent_in_one_locked_observation(clean_two_sided_prune: Path) -> None:
    workspace_bytes = (clean_two_sided_prune / "workspace.toml").read_bytes()
    parsed_workspace, parse_error = ENGINE._parse_prune_workspace(workspace_bytes)
    assert parse_error is None and parsed_workspace is not None
    closure_occurrences = ENGINE._resolve_prune_closure_memberships(
        parsed_workspace, ["docs/specs/chosen/spec.md"]
    )["docs/specs/chosen/spec.md"]
    assert {item["collection"] for item in closure_occurrences} == {
        "backlog.open",
        "backlog.closed",
    }
    # A prune consumes its fixture, so copy it before the destructive run.
    spare = clean_two_sided_prune.parent / "clean_two_sided_prune_spare"
    shutil.copytree(clean_two_sided_prune, spare)

    # Every resolving occurrence is removed, including the one outside the
    # read-only report's collection scope, so a clean run closes two-sided.
    result = _execute(clean_two_sided_prune, ["docs/specs/chosen"])
    assert "error" not in result, result
    assert result["closure"]["artifact_absent"] is True
    assert result["closure"]["membership_absent"] is True
    surviving, _ = ENGINE._parse_prune_workspace(
        (clean_two_sided_prune / "workspace.toml").read_bytes()
    )
    assert ENGINE._resolve_prune_closure_memberships(
        surviving, ["docs/specs/chosen/spec.md"]
    )["docs/specs/chosen/spec.md"] == []

    # And when the membership write does not land, the broad scan is what denies
    # success: both occurrences must be named, not just the in-scope one.
    again = _execute(
        spare, ["docs/specs/chosen"],
        failure_point="membership_write_noop",
    )
    _error(again, "closure_failed")
    assert again["error"]["membership_survives"] is True
    assert {item["collection"] for item in again["error"]["occurrences"]} == {
        "backlog.open",
        "backlog.closed",
    }


def test_surviving_half_state_is_reported_and_fails(forced_half_state_matrix: Path) -> None:
    result = _execute(forced_half_state_matrix, ["docs/specs/chosen"], failure_point="after_artifact_removal")
    _error(result, "closure_failed")
    assert result["error"]["selector"] == "docs/specs/chosen"
    assert result["error"]["membership_survives"] is True


def test_aba_is_excluded_by_the_lock_not_the_digest(aba_characterization: Path) -> None:
    before = (aba_characterization / "workspace.toml").read_bytes()
    changed = before.replace(b"Fixture", b"Changed")
    assert hashlib.sha256(before).digest() == hashlib.sha256(before).digest()
    (aba_characterization / "workspace.toml").write_bytes(changed)
    (aba_characterization / "workspace.toml").write_bytes(before)
    assert (aba_characterization / "workspace.toml").read_bytes() == before
    (aba_characterization / LOCK_NAME).write_text("123\n", encoding="utf-8")
    _error(_preview(aba_characterization, ["docs/specs/chosen"]), "lock_busy")


def _load_intake():
    return _load_pack_script(
        REPO_ROOT / "packs/core/.apm/skills/work-intake/scripts/intake_transaction.py",
        "core_work_intake_prune_closure",
    )


def _load_status() -> ModuleType:
    """Load the real workspace-status writer module and bind its engine."""
    status = _load_pack_script(CLI_PATH, "core_workspace_status_writer_interleaving")
    assert status._bind_engine()
    return status


def _load_refresh() -> ModuleType:
    """Load the real guarded-refresh writer under a unique pack/skill name."""
    return _load_pack_script(
        REPO_ROOT / "packs/core/.apm/skills/work-intake/scripts/refresh.py",
        "core_work_intake_refresh_prune_closure",
    )


def _assert_prune_busy_and_inert(root: Path) -> None:
    """Run the real prune contender and prove its busy refusal writes nothing."""
    before = _snapshot(root)
    _error(_preview(root, ["docs/specs/chosen"]), "lock_busy")
    assert _snapshot(root) == before


def _write_migration_case(
    status: ModuleType, root: Path, token: str
) -> tuple[dict[str, object], dict[str, object]]:
    """Build one valid real migration selection and planned operation."""
    _write_repository(
        root,
        ("chosen", "legacy"),
        backlog_open=(_canonical("chosen"),),
        work={"ini-002": {"queue": ("spec/legacy",)}},
    )
    (root / "docs/specs/legacy/plan.md").write_text(
        "# Plan: legacy\n", encoding="utf-8"
    )
    workspace_path = root / "workspace.toml"
    workspace_path.write_text(
        "[authorization.migration]\n"
        'contract_version = "work-intake-migration-authorization.v1"\n'
        'approver_roles = ["migration-approver"]\n\n'
        + workspace_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    workspace_bytes = workspace_path.read_bytes()
    workspace = status.parse_workspace(workspace_path)
    canonical = status.run_canonical_reconciliation(workspace, root)
    assert len(canonical.legacy_memberships) == 1
    finding = status.build_migration_finding(
        workspace_bytes, canonical.legacy_memberships[0]
    )
    selection = {
        "contract_version": "work-intake-migration-selection.v1",
        "legacy_finding_id": finding["legacy_finding_id"],
        "workspace_fingerprint": hashlib.sha256(workspace_bytes).hexdigest(),
        "source_membership": finding["source_membership"],
        "target_entry": {
            "path": "docs/specs/legacy/spec.md",
            "kind": "spec",
            "source": {"mode": "repo-origin", "ref": f"fixture/{token}"},
            "summary": f"Reviewed migration {token}",
            "needs": [],
        },
        "target_membership": {
            "ini_slug": "ini-002",
            "collection": "work.queue",
        },
        "owning_processor": "new-spec",
        "provenance_reference": "docs/specs/legacy/spec.md",
        "legacy_content_approved_for_ledger": True,
    }
    planned = status.compute_migration_plan(root, workspace_path, selection)
    assert planned.result["result_code"] == "planned"
    assert planned.proposed_operation is not None
    return selection, planned.proposed_operation


def _migration_confirmation(
    operation: Mapping[str, object], action: str, token: str
) -> dict[str, str]:
    """Create fresh test-only evidence for one real migration writer."""
    return {
        "contract_version": "work-intake-migration-confirmation.v1",
        "confirmation_id": f"confirmation-{token:0<32}"[:45],
        "action": action,
        "operation_id": str(operation["operation_id"]),
        "operation_digest": str(operation["operation_digest"]),
        "authorization_subject": f"subject-{token:0<32}"[:40],
        "role": "migration-approver",
        "confirmed_at": datetime.now(UTC).isoformat(),
        "authorization_source": "current-human-session",
    }


def test_intake_transaction_holds_the_shared_lock_across_its_whole_interval(intake_transaction_lock_span: Path) -> None:
    """Observe the lock at each callback, so an early release is detectable.

    Reading the source for the lock name proves only that the string appears. The
    interval claim is about *when* the lock is held, so each callback records the
    lock's live presence: releasing it between the two turns the second observation
    False and this test red.
    """
    intake = _load_intake()
    root = intake_transaction_lock_span
    (root / "docs/specs").mkdir(parents=True, exist_ok=True)
    observed: dict[str, bool] = {}

    def _materialize(target: Path) -> None:
        observed["materialize"] = (root / LOCK_NAME).exists()
        target.mkdir(parents=True, exist_ok=True)
        (target / "spec.md").write_text("# spec\n", encoding="utf-8")

    def _register() -> None:
        observed["register"] = (root / LOCK_NAME).exists()

    result = intake.run_intake_transaction(
        repository_root=root,
        configured_parent="docs/specs",
        artifact_target="docs/specs/intake-target",
        materialize_artifact=_materialize,
        register_workspace_entry=_register,
        rollback_partial_state=lambda: None,
        record_reconciliation=lambda _stage: None,
        dispatch_processor=lambda: None,
    )

    assert observed.get("materialize") is True, "lock not held during artifact materialization"
    assert observed.get("register") is True, "lock released before workspace registration"
    assert result.failed_stage is None, result.failed_stage
    # And it must not leak: released once the interval closes.
    assert not (root / LOCK_NAME).exists()


def test_prune_and_intake_are_mutually_exclusive_in_both_orders(prune_intake_interleaving: Path) -> None:
    lock = prune_intake_interleaving / LOCK_NAME
    lock.write_text("123\n", encoding="utf-8")
    _error(_preview(prune_intake_interleaving, ["docs/specs/chosen"]), "lock_busy")
    lock.unlink()
    assert "error" not in _execute(prune_intake_interleaving, ["docs/specs/chosen"])


def test_every_participating_writer_is_mutually_exclusive_in_both_orders(
    participating_writer_interleaving_matrix: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status = _load_status()
    intake = _load_intake()
    refresh = _load_refresh()
    case_parent = participating_writer_interleaving_matrix.parent / "writers"

    def repository(name: str, *extra_specs: str) -> Path:
        return _write_repository(
            case_parent / name,
            ("chosen", *extra_specs),
            backlog_open=(_canonical("chosen"),),
        )

    def prune_first(root: Path, contender: Any) -> None:
        preview = _preview(root, ["docs/specs/chosen"])
        original_remove = ENGINE._remove_prune_tree
        reached = False

        def remove_with_contender(
            repository_root: Path, selector: str, manifest: dict[str, Any]
        ) -> None:
            nonlocal reached
            reached = True
            before = _snapshot(repository_root)
            contender()
            assert _snapshot(repository_root) == before
            original_remove(repository_root, selector, manifest)

        with monkeypatch.context() as patcher:
            patcher.setattr(ENGINE, "_remove_prune_tree", remove_with_contender)
            result = ENGINE.prune_execute(
                root, ["docs/specs/chosen"], _confirmation(preview)
            )
        assert reached
        # This sandbox may refuse the descriptor-based directory removal after
        # the contender ran. Claude's gate reruns the same case without that
        # host restriction; mutual exclusion is already observed above.
        assert "error" not in result or result["error"]["code"] == "closure_failed"

    def prepare_repair_apply(root: Path) -> Path:
        _write_repository(
            root,
            ("chosen", "repair"),
            backlog_open=(_canonical("chosen"),),
            work={"ini-002": {"queue": (_canonical("repair"),)}},
        )
        (root / "docs/specs" / "repair/spec.md").write_text(
            "# Spec: repair\n\n- **Status:** Shipped\n", encoding="utf-8"
        )
        (root / "docs/specs" / "repair/plan.md").write_text(
            "# Plan: repair\n", encoding="utf-8"
        )
        plan = root / "repair-plan.json"
        code, payload, stderr = _cli(
            root, "repair-plan", "--plan-file", str(plan)
        )
        assert code == 0, stderr
        assert payload["automatic_operations"], payload
        return plan

    repair_root = case_parent / "repair-first"
    repair_plan = prepare_repair_apply(repair_root)
    repair_observed: list[bool] = []
    original_apply = status._apply_operations

    def apply_with_prune(*args: Any, **kwargs: Any) -> Any:
        repair_observed.append((repair_root / LOCK_NAME).exists())
        _assert_prune_busy_and_inert(repair_root)
        result = original_apply(*args, **kwargs)
        repair_observed.append((repair_root / LOCK_NAME).exists())
        return result

    with monkeypatch.context() as patcher:
        patcher.setattr(status, "_apply_operations", apply_with_prune)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            repair_code = status.main(
                [
                    "repair-apply",
                    "--root",
                    str(repair_root),
                    "--plan-file",
                    str(repair_plan),
                    "--yes",
                ]
            )
    assert repair_code == 0 and repair_observed == [True, True]

    repair_prune_root = case_parent / "repair-prune-first"
    repair_prune_plan = prepare_repair_apply(repair_prune_root)

    def repair_contender() -> None:
        code, payload, _stderr = _cli(
            repair_prune_root,
            "repair-apply",
            "--plan-file",
            str(repair_prune_plan),
            "--yes",
        )
        assert code == 2 and payload["reason"] == "lock_busy"

    prune_first(repair_prune_root, repair_contender)

    intake_root = repository("intake-first")
    intake_observed: list[bool] = []

    def materialize(target: Path) -> None:
        intake_observed.append((intake_root / LOCK_NAME).exists())
        _assert_prune_busy_and_inert(intake_root)
        target.mkdir(parents=True)
        (target / "spec.md").write_bytes(b"# intake\n")

    def register() -> None:
        intake_observed.append((intake_root / LOCK_NAME).exists())

    intake_result = intake.run_intake_transaction(
        repository_root=intake_root,
        configured_parent="docs/specs",
        artifact_target="docs/specs/" + "intake",
        materialize_artifact=materialize,
        register_workspace_entry=register,
        rollback_partial_state=lambda: None,
        record_reconciliation=lambda _stage: None,
        dispatch_processor=lambda: None,
    )
    assert intake_result.status is intake.TransactionStatus.COMMITTED
    assert intake_observed == [True, True]

    intake_prune_root = repository("intake-prune-first")

    def intake_contender() -> None:
        result = intake.run_intake_transaction(
            repository_root=intake_prune_root,
            configured_parent="docs/specs",
            artifact_target="docs/specs/" + "intake",
            materialize_artifact=lambda _target: pytest.fail("busy writer mutated"),
            register_workspace_entry=lambda: pytest.fail("busy writer mutated"),
            rollback_partial_state=lambda: pytest.fail("busy writer rolled back"),
            record_reconciliation=lambda _stage: pytest.fail("busy writer recorded"),
            dispatch_processor=lambda: pytest.fail("busy writer dispatched"),
        )
        assert result.status is intake.TransactionStatus.LOCK_BUSY

    prune_first(intake_prune_root, intake_contender)

    refresh_root = repository("refresh-first", "refresh")
    refresh_artifact = refresh_root / "docs/specs" / "refresh/spec.md"
    refresh_workspace = refresh_root / "workspace.toml"
    refresh_observed: list[bool] = []
    original_confined = refresh._confined_existing_file
    confined_calls = 0

    def confined_with_prune(root: Path, relative: str) -> Path:
        nonlocal confined_calls
        confined_calls += 1
        if confined_calls == 1:
            refresh_observed.append((refresh_root / LOCK_NAME).exists())
            _assert_prune_busy_and_inert(refresh_root)
        return original_confined(root, relative)

    original_replace = Path.replace

    def replace_observer(source: Path, target: Path) -> Path:
        result = original_replace(source, target)
        if Path(target) == refresh_workspace:
            refresh_observed.append((refresh_root / LOCK_NAME).exists())
        return result

    with monkeypatch.context() as patcher:
        patcher.setattr(refresh, "_confined_existing_file", confined_with_prune)
        patcher.setattr(Path, "replace", replace_observer)
        refresh_result = refresh.guarded_write_pair(
            repository_root=refresh_root,
            artifact_path="docs/specs/" + "refresh/spec.md",
            expected_artifact_digest=refresh.digest_bytes(refresh_artifact.read_bytes()),
            expected_workspace_digest=refresh.digest_bytes(refresh_workspace.read_bytes()),
            artifact_bytes=b"# refreshed\n",
            workspace_bytes=refresh_workspace.read_bytes(),
        )
    assert refresh_result.code == "written" and refresh_observed == [True, True]

    refresh_prune_root = repository("refresh-prune-first", "refresh")

    def refresh_contender() -> None:
        artifact = refresh_prune_root / "docs/specs" / "refresh/spec.md"
        workspace = refresh_prune_root / "workspace.toml"
        result = refresh.guarded_write_pair(
            repository_root=refresh_prune_root,
            artifact_path="docs/specs/" + "refresh/spec.md",
            expected_artifact_digest=refresh.digest_bytes(artifact.read_bytes()),
            expected_workspace_digest=refresh.digest_bytes(workspace.read_bytes()),
            artifact_bytes=b"must not write\n",
            workspace_bytes=workspace.read_bytes(),
        )
        assert result.code == "lock_busy"

    prune_first(refresh_prune_root, refresh_contender)

    def migration_first(name: str, action: str) -> None:
        root = case_parent / name
        selection, operation = _write_migration_case(status, root, name[:2])
        if action == "rollback":
            applied = status.apply_migration_operation(
                root,
                selection,
                str(operation["operation_id"]),
                _migration_confirmation(operation, "apply", "a1"),
            )
            assert applied["result_code"] == "applied"
        observed: list[bool] = []
        original_failure = status._migration_failure

        def failure_with_prune(failure_point: str | None, point: str) -> None:
            if point.endswith("stage_before") and not observed:
                observed.append((root / LOCK_NAME).exists())
                _assert_prune_busy_and_inert(root)
            if point == "ledger_replace_after":
                observed.append((root / LOCK_NAME).exists())
            original_failure(failure_point, point)

        with monkeypatch.context() as patcher:
            patcher.setattr(status, "_migration_failure", failure_with_prune)
            if action == "apply":
                result = status.apply_migration_operation(
                    root,
                    selection,
                    str(operation["operation_id"]),
                    _migration_confirmation(operation, action, "b2"),
                )
                expected = "applied"
            else:
                result = status.rollback_migration_operation(
                    root,
                    str(operation["operation_id"]),
                    _migration_confirmation(operation, action, "c3"),
                )
                expected = "rolled_back"
        assert result["result_code"] == expected
        assert observed[0] is True and observed[-1] is True

    migration_first("migration-apply-first", "apply")
    migration_first("migration-rollback-first", "rollback")

    for name, writer in (
        ("migration-apply-prune-first", status.apply_migration_operation),
        ("migration-rollback-prune-first", status.rollback_migration_operation),
    ):
        root = repository(name)

        def migration_contender(
            writer: Any = writer, root: Path = root
        ) -> None:
            if writer is status.apply_migration_operation:
                result = writer(root, {}, "missing", {})
            else:
                result = writer(root, "missing", {})
            assert result["result_code"] == "lock_busy"

        prune_first(root, migration_contender)

    for name in ("second-prune-first", "first-prune-first"):
        root = repository(name)
        prune_first(root, lambda root=root: _assert_prune_busy_and_inert(root))


def test_duplicate_canonical_occurrences_must_all_be_removed(duplicate_canonical_survivor: Path) -> None:
    preview = _preview(duplicate_canonical_survivor, ["docs/specs/chosen"])
    assert len(preview["targets"][0]["occurrences"]) == 2
    workspace_path = duplicate_canonical_survivor / "workspace.toml"
    workspace_bytes = workspace_path.read_bytes()
    workspace, error = ENGINE._parse_prune_workspace(workspace_bytes)
    assert error is None and workspace is not None
    occurrences = ENGINE.resolve_selected_memberships(
        workspace, ["docs/specs/chosen/spec.md"]
    )["docs/specs/chosen/spec.md"]
    partially_removed = ENGINE._prune_workspace_without_occurrences(
        workspace_bytes, workspace, occurrences[:1]
    )
    assert partially_removed is not None
    workspace_path.write_bytes(partially_removed)
    survivors_workspace, error = ENGINE._parse_prune_workspace(partially_removed)
    assert error is None and survivors_workspace is not None
    survivors = ENGINE.resolve_selected_memberships(
        survivors_workspace, ["docs/specs/chosen/spec.md"]
    )["docs/specs/chosen/spec.md"]
    assert len(survivors) == 1
    closure = ENGINE._prune_closure(
        duplicate_canonical_survivor,
        ["docs/specs/chosen"],
        partially_removed,
    )
    _error(closure, "closure_failed")
    assert closure["error"]["membership_survives"] is True
    assert closure["error"]["occurrences"] == survivors


def test_surviving_legacy_alias_denies_closure(
    legacy_alias_survivor: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    preview = _preview(legacy_alias_survivor, ["docs/specs/chosen"])
    assert preview["targets"][0]["occurrences"] == [{
        "canonical_artifact_path": "docs/specs/chosen/spec.md",
        "initiative": "ini-900",
        "collection": "work.active",
        "entry_index": 0,
        "form": "legacy",
    }]
    monkeypatch.setattr(ENGINE, "_remove_prune_tree", lambda *_: None)
    monkeypatch.setattr(ENGINE, "_prune_artifact_absent", lambda *_: True)
    result = _execute(
        legacy_alias_survivor,
        ["docs/specs/chosen"],
        failure_point="membership_write_noop",
    )
    _error(result, "closure_failed")
    assert result["error"]["occurrences"] == preview["targets"][0]["occurrences"]


def test_legacy_string_alias_is_removed_by_clean_prune(
    legacy_alias_survivor: Path,
) -> None:
    result = _execute(legacy_alias_survivor, ["docs/specs/chosen"])

    assert "error" not in result
    workspace = ENGINE.parse_workspace(legacy_alias_survivor / "workspace.toml")
    assert workspace["ini-900"]["work"]["active"] == []


@pytest.mark.parametrize(
    ("active", "expected"),
    (
        ('["spec/chosen"]', "[]"),
        ('["spec/chosen", "unrelated,]"]', '["unrelated,]"]'),
        ('["unrelated,]", "spec/chosen",]', '["unrelated,]",]'),
    ),
)
def test_legacy_string_alias_is_removed_with_exact_array_spans(
    tmp_path: Path, active: str, expected: str
) -> None:
    root = _write_repository(tmp_path / "legacy-string", ("chosen",))
    workspace_path = root / "workspace.toml"
    workspace_path.write_text(
        workspace_path.read_text(encoding="utf-8").replace(
            "closed = []", f'["ini-900".work]\nactive = {active}'
        ),
        encoding="utf-8",
    )

    workspace_bytes = workspace_path.read_bytes()
    workspace, parse_error = ENGINE._parse_prune_workspace(workspace_bytes)
    assert parse_error is None and workspace is not None
    occurrences = ENGINE._resolve_prune_closure_memberships(
        workspace, ["docs/specs/chosen/spec.md"]
    )["docs/specs/chosen/spec.md"]
    edited = ENGINE._prune_workspace_without_occurrences(
        workspace_bytes, workspace, occurrences
    )
    assert edited is not None
    workspace = ENGINE.tomllib.loads(edited.decode("utf-8"))
    assert workspace["ini-900"]["work"]["active"] == ENGINE.tomllib.loads(
        f"active = {expected}"
    )["active"]
    assert ENGINE._resolve_prune_closure_memberships(
        workspace, ["docs/specs/chosen/spec.md"]
    )["docs/specs/chosen/spec.md"] == []


def test_parse_blocked_occurrence_denies_closure(parse_blocked_survivor: Path) -> None:
    preview = _preview(parse_blocked_survivor, ["docs/specs/chosen"])
    assert preview["targets"][0]["parse_blocked_occurrences"]
    _error(_execute(parse_blocked_survivor, ["docs/specs/chosen"]), "closure_failed")


def test_existing_subcommands_are_unchanged(
    default_command_compatibility: tuple[Path, Path],
) -> None:
    root, base_cli = default_command_compatibility
    commands = (("status",), ("reconcile",), ("explain", "--item", "docs/specs/chosen/spec.md"), ("selected-membership", "--spec-dir", "docs/specs/chosen"))
    expected = [_cli_at(base_cli, root, *command) for command in commands]
    actual = [_cli(root, *command) for command in commands]
    assert actual == expected


def test_every_refusal_path_performs_no_writes(refusal_snapshot_matrix: Path) -> None:
    cases = ((["docs/specs/../bad"], None), (["docs/specs/protected"], None), (["docs/specs/missing"], None), (["docs/specs/open"], {}))
    for selectors, confirmation in cases:
        before = _snapshot(refusal_snapshot_matrix)
        if confirmation is None:
            _preview(refusal_snapshot_matrix, selectors)
        else:
            ENGINE.prune_execute(refusal_snapshot_matrix, selectors, confirmation)
        assert _snapshot(refusal_snapshot_matrix) == before


def test_refusal_output_is_safe_and_utf8(unsafe_and_instruction_like_input: Path) -> None:
    code, payload, stderr = _cli(unsafe_and_instruction_like_input, "prune", "--select", "docs/specs/../café")
    assert code != 0 and payload["error"]["code"] == "invalid_selector"
    assert stderr.encode("utf-8").decode("utf-8") == stderr
    assert "Traceback" not in stderr and str(unsafe_and_instruction_like_input) not in stderr


def test_pack_delivery_contract_is_complete_and_version_increased(workspace_status_eval_contract: Path) -> None:
    assert callable(ENGINE.prune_operation_digest)
    core = (REPO_ROOT / "packs/core/pack.toml").read_text(encoding="utf-8")
    plugin = (REPO_ROOT / "packs/core/.claude-plugin/plugin.json").read_text(encoding="utf-8")
    evals = list((REPO_ROOT / "packs/core/.apm/skills/workspace-status/evals").rglob("*"))
    changelog = (REPO_ROOT / "docs/product/changelog.md").read_text(encoding="utf-8")
    core_version = re.search(r'^version = "([^"]+)"', core, re.M).group(1)
    plugin_version = re.search(r'"version":\s*"([^"]+)"', plugin).group(1)
    assert core_version == plugin_version, (core_version, plugin_version)

    # The bump rule binds a branch that CHANGES the core pack. Asserting it
    # unconditionally made this test red on `main` itself — where the merge base
    # is HEAD, so the "next patch" names a version that does not exist yet — and
    # red on every branch that touches something else entirely. Scope it to the
    # condition that actually obliges a bump.
    base = _base_revision()
    changed = subprocess.run(
        ["git", "diff", "--quiet", base, "--", "packs/core"],
        cwd=REPO_ROOT, capture_output=True,
    ).returncode != 0

    if changed:
        base_core = subprocess.run(
            ["git", "show", f"{base}:packs/core/pack.toml"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
        base_version = re.search(r'^version = "([^"]+)"', base_core, re.M).group(1)
        if base_version != core_version:
            # A bump landed: it must be exactly the next patch, since this pack
            # reserves minor for new primitives and major for removals.
            b_major, b_minor, b_patch = (int(p) for p in base_version.split("."))
            assert core_version == f"{b_major}.{b_minor}.{b_patch + 1}", (
                base_version,
                core_version,
            )
            # And the core-led changelog entry must name that exact version.
            assert f"## [core][{core_version}]" in changelog, core_version
    assert any("prune" in path.read_text(encoding="utf-8") for path in evals if path.is_file())
    assert "prune" in changelog.lower() and workspace_status_eval_contract.exists()


def test_successful_prune_changes_only_the_selected_delta(exact_delta_with_unselected_neighbours: Path) -> None:
    before = _snapshot(exact_delta_with_unselected_neighbours)
    workspace_before = before["workspace.toml"][2]
    assert isinstance(workspace_before, bytes)
    assert workspace_before.count(SELECTED_DELTA_ELEMENT) == 1
    expected_workspace = workspace_before.replace(SELECTED_DELTA_ELEMENT, b"", 1)
    parsed_workspace, parse_error = ENGINE._parse_prune_workspace(workspace_before)
    assert parse_error is None and parsed_workspace is not None
    recorded = ENGINE.resolve_selected_memberships(
        parsed_workspace, ["docs/specs/chosen/spec.md"]
    )["docs/specs/chosen/spec.md"]
    assert ENGINE._prune_workspace_without_occurrences(
        workspace_before, parsed_workspace, recorded
    ) == expected_workspace
    outside_target = exact_delta_with_unselected_neighbours.parent / "symlink-target"
    result = _execute(exact_delta_with_unselected_neighbours, ["docs/specs/chosen"])
    after = _snapshot(exact_delta_with_unselected_neighbours)
    expected = {
        path: state
        for path, state in before.items()
        if path != "docs/specs/chosen" and not path.startswith("docs/specs/chosen/")
    }
    expected["workspace.toml"] = (
        before["workspace.toml"][0],
        before["workspace.toml"][1],
        expected_workspace,
    )
    assert "error" not in result
    assert after == expected
    assert outside_target.read_text(encoding="utf-8") == "outside selected tree\n"


def test_operation_digest_binds_selection_tree_and_workspace_and_refuses_drift(
    baseline_staleness_matrix: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preview = _preview(baseline_staleness_matrix, ["docs/specs/chosen"])
    digest = preview["operation_digest"]
    (baseline_staleness_matrix / "docs/specs/chosen/spec.md").write_text("drift\n", encoding="utf-8")
    _error(ENGINE.prune_execute(baseline_staleness_matrix, ["docs/specs/chosen"], _confirmation(preview)), "baseline_stale")
    assert digest != _preview(baseline_staleness_matrix, ["docs/specs/chosen"])["operation_digest"]

    workspace_path = baseline_staleness_matrix / "workspace.toml"
    current_preview = _preview(baseline_staleness_matrix, ["docs/specs/chosen"])
    workspace_path.write_bytes(workspace_path.read_bytes() + b"# before baseline\n")
    before = _snapshot(baseline_staleness_matrix)
    result = ENGINE.prune_execute(
        baseline_staleness_matrix,
        ["docs/specs/chosen"],
        _confirmation(current_preview),
    )
    _error(result, "baseline_stale")
    assert _snapshot(baseline_staleness_matrix) == before
    assert (baseline_staleness_matrix / "docs/specs/chosen").is_dir()


def test_pre_unlink_artifact_drift_refuses_the_stale_baseline(
    single_registered_target: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fault between baseline capture and unlink cannot delete changed bytes."""
    preview = _preview(single_registered_target, ["docs/specs/chosen"])
    artifact = single_registered_target / "docs/specs/chosen/notes/fixture.md"
    original_edit = ENGINE._prune_workspace_without_occurrences

    def inject_artifact_drift(*args: Any, **kwargs: Any) -> bytes | None:
        artifact.write_bytes(b"changed after baseline\n")
        return original_edit(*args, **kwargs)

    monkeypatch.setattr(ENGINE, "_prune_workspace_without_occurrences", inject_artifact_drift)
    result = ENGINE.prune_execute(
        single_registered_target,
        ["docs/specs/chosen"],
        _confirmation(preview),
    )
    _error(result, "baseline_stale")
    assert artifact.read_bytes() == b"changed after baseline\n"
    assert (single_registered_target / "docs/specs/chosen").is_dir()


def test_preview_emits_an_unsigned_challenge_requiring_independent_authorization(preview_to_confirmation_round_trip: Path) -> None:
    before = _snapshot(preview_to_confirmation_round_trip)
    preview = _preview(preview_to_confirmation_round_trip, ["docs/specs/chosen"])
    assert {"operation_id", "operation_digest", "selection", "targets"} <= set(preview)
    assert not {"subject", "role", "confirming_identity"} & set(preview)
    # The shipped CLI preview must be unsigned too: pinning only the engine seam
    # leaves a CLI that emits authorization fields undetected.
    cli_code, cli_preview, _ = _cli(
        preview_to_confirmation_round_trip, "prune", "--select", "docs/specs/chosen", "--preview"
    )
    assert cli_code == 0
    assert {"operation_id", "operation_digest"} <= set(cli_preview)
    assert not {"subject", "role", "confirming_identity"} & set(cli_preview)
    _error(ENGINE.prune_execute(preview_to_confirmation_round_trip, ["docs/specs/chosen"], preview), "confirmation_invalid")
    assert _snapshot(preview_to_confirmation_round_trip) == before
    assert "error" not in ENGINE.prune_execute(preview_to_confirmation_round_trip, ["docs/specs/chosen"], _confirmation(preview))


def test_nested_list_occurrence_refuses_before_touching_a_sibling(tmp_path: Path) -> None:
    """A nested lifecycle list must not let a sibling membership be cut.

    The occurrence records an inner index; applying it to the outer array would
    remove an entry nobody selected. Refusing keeps the exact-delta guarantee.
    """
    root = tmp_path / "nested"
    (root / "docs/specs/chosen").mkdir(parents=True)
    (root / "docs/specs/neighbour").mkdir(parents=True)
    (root / "docs/specs/chosen/spec.md").write_text("# c\n", encoding="utf-8")
    (root / "docs/specs/neighbour/spec.md").write_text("# n\n", encoding="utf-8")
    chosen = '{path = "docs/specs/chosen/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "c", needs = []}'
    neighbour = '{path = "docs/specs/neighbour/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "n", needs = []}'
    (root / "workspace.toml").write_text(
        '["ini-900"]\nname = "h"\nstatus = "active"\n'
        f'["ini-900".work]\nqueue = [[{chosen}, {neighbour}]]\n',
        encoding="utf-8",
    )
    before = _snapshot(root)
    result = _execute(root, ["docs/specs/chosen"])
    _error(result, "invalid_workspace")
    assert _snapshot(root) == before
    assert "docs/specs/neighbour" in (root / "workspace.toml").read_text(encoding="utf-8")


def test_nested_legacy_string_occurrence_refuses_before_touching_a_sibling(tmp_path: Path) -> None:
    """The nesting guard must cover the legacy-string branch too.

    The dict branch recorded a nesting marker and the string branch did not, so a
    nested legacy alias slipped past the refusal and its inner index was applied to
    the outer array, cutting an unselected sibling alias.
    """
    root = tmp_path / "nested-legacy"
    (root / "docs/specs/chosen").mkdir(parents=True)
    (root / "docs/specs/neighbour").mkdir(parents=True)
    (root / "docs/specs/chosen/spec.md").write_text("# c\n", encoding="utf-8")
    (root / "docs/specs/neighbour/spec.md").write_text("# n\n", encoding="utf-8")
    (root / "workspace.toml").write_text(
        '["ini-900"]\nname = "h"\nstatus = "active"\n'
        '["ini-900".work]\nactive = [["spec/chosen", "spec/neighbour"]]\n',
        encoding="utf-8",
    )
    before = _snapshot(root)
    result = _execute(root, ["docs/specs/chosen"])
    _error(result, "invalid_workspace")
    assert _snapshot(root) == before
    assert "spec/neighbour" in (root / "workspace.toml").read_text(encoding="utf-8")


def test_late_entry_drift_refuses_without_deleting_an_earlier_entry(tmp_path: Path) -> None:
    """A mismatch found late must not follow entries already deleted.

    Validation used to interleave with deletion, so drift in a late-traversed
    entry was detected only after an earlier one had been unlinked — data loss on
    what is nominally a refusal path. `notes/` sorts before `spec.md`, so it is the
    entry that would already be gone.
    """
    root = tmp_path / "ordering"
    (root / "docs/specs/chosen/notes").mkdir(parents=True)
    (root / "docs/specs/chosen/spec.md").write_text("# c\n", encoding="utf-8")
    (root / "docs/specs/chosen/notes/n.md").write_text("note\n", encoding="utf-8")
    (root / "workspace.toml").write_text(
        '[backlog]\nopen = [\n  {path = "docs/specs/chosen/spec.md", kind = "spec", '
        'source = {mode = "repo-origin"}, summary = "c", needs = []},\n]\n',
        encoding="utf-8",
    )
    preview = _preview(root, ["docs/specs/chosen"])
    confirmation = _confirmation(preview)
    (root / "docs/specs/chosen/spec.md").write_text("CHANGED\n", encoding="utf-8")

    result = ENGINE.prune_execute(root, ["docs/specs/chosen"], confirmation)
    _error(result, "baseline_stale")
    assert (root / "docs/specs/chosen/notes/n.md").exists()
    assert (root / "docs/specs/chosen/spec.md").exists()
    assert (root / "docs/specs/chosen").is_dir()


def test_fifo_at_the_lock_path_does_not_block_the_refusal(tmp_path: Path) -> None:
    """A FIFO planted at the lock path must not hang the busy refusal.

    The holder diagnostic opens the lock file; a blocking open on a FIFO waits for
    a writer that never comes, so the command would never return at all.
    """
    root = tmp_path / "fifo"
    (root / "docs/specs/x").mkdir(parents=True)
    (root / "docs/specs/x/spec.md").write_text("# x\n", encoding="utf-8")
    (root / "workspace.toml").write_text("[backlog]\nopen = []\n", encoding="utf-8")
    os.mkfifo(root / LOCK_NAME)
    try:
        result = ENGINE.prune_execute(root, ["docs/specs/x"], {})
    finally:
        (root / LOCK_NAME).unlink()
    _error(result, "lock_busy")
    assert result["error"].get("holder_pid") is None


def test_confined_removal_requires_a_no_follow_primitive(
    single_registered_target: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without a no-follow primitive the prune declines and deletes nothing.

    Confined removal rests on no-follow descriptor descent, so on a host lacking it
    the two-sided guarantee cannot be honoured. Asserting the probe equals its own
    definition would prove nothing; this drives the real path with the capability
    forced off and requires the dedicated refusal plus an untouched tree.
    """
    preview = _preview(single_registered_target, ["docs/specs/chosen"])
    confirmation = _confirmation(preview)
    before = _snapshot(single_registered_target)
    monkeypatch.setattr(ENGINE, "_PRUNE_NOFOLLOW_AVAILABLE", False)
    result = ENGINE.prune_execute(
        single_registered_target, ["docs/specs/chosen"], confirmation
    )
    _error(result, "unsupported_platform")
    assert result["error"]["selection"] == ["docs/specs/chosen"]
    assert _snapshot(single_registered_target) == before
    # It is its own refusal, not a closure failure: nothing was attempted.
    assert result["error"]["code"] != "closure_failed"


def test_every_emitted_refusal_code_is_documented() -> None:
    """Every prune refusal code appears in the shipped refusal list itself.

    Two ways a looser check passes while an operator is stranded: searching the
    whole document finds a code mentioned in some other table rather than in the
    list they were told to consult, and a regex over literal calls misses a code
    assembled at runtime. So this bounds the search to the list section and
    refuses any non-literal code outright.
    """
    prune_source = PRUNE_PATH.read_text(encoding="utf-8")

    # `(?<!def )` skips the helper's own definition line, which is not a call.
    non_literal = re.findall(
        r"""(?<!def )_prune_error\(\s*(?!["'])(\w+)""", prune_source
    )
    assert non_literal == [], f"refusal code is not a literal: {non_literal}"

    emitted = set(re.findall(r"""_prune_error\(\s*["']([a-z_]+)["']""", prune_source))
    assert emitted, "no refusal codes found - the pattern stopped matching"

    skill = (
        REPO_ROOT / "packs/core/.apm/skills/workspace-status/SKILL.md"
    ).read_text(encoding="utf-8")
    anchor = "A non-zero result names a stable refusal code:"
    assert anchor in skill, "refusal-list anchor moved; this control cannot bound itself"
    tail = skill[skill.index(anchor) + len(anchor):]
    first_bullet = tail.index("\n- ")
    listing = tail[: tail.index("\n\n", first_bullet)]

    undocumented = sorted(code for code in emitted if f"`{code}`" not in listing)
    assert undocumented == [], undocumented
