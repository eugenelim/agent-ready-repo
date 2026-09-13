"""Red construction contract for selection-scoped workspace membership."""

from __future__ import annotations

import contextlib
import dataclasses
import importlib.util
import inspect
import io
import json
import sys
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_PATH = (
    REPO_ROOT
    / "packs"
    / "core"
    / ".apm"
    / "skills"
    / "workspace-status"
    / "scripts"
    / "workspace_status_engine.py"
)
CLI_PATH = ENGINE_PATH.with_name("workspace_status.py")
ENGINE_MODULE_NAME = "core_workspace_status_selection_membership"
SELECTED_MEMBERSHIP_ROUTE = "selected-membership"
SELECTOR_FLAG = "--spec-dir"


def _load_module(name: str, path: Path) -> ModuleType:
    """Load one skill-local module without changing the import path."""
    module_spec = importlib.util.spec_from_file_location(name, path)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[name] = module
    module_spec.loader.exec_module(module)
    return module


ENGINE = _load_module(ENGINE_MODULE_NAME, ENGINE_PATH)


@dataclasses.dataclass(frozen=True)
class RepositoryFixture:
    """A disposable repository and the selectors evaluated against it."""

    root: Path
    selectors: tuple[str, ...]


def _toml_value(value: object) -> str:
    """Render the small TOML value subset used by these fixtures."""
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        fields = ", ".join(
            f"{key} = {_toml_value(item)}" for key, item in value.items()
        )
        return "{ " + fields + " }"
    raise TypeError(f"unsupported fixture value: {type(value).__name__}")


def _canonical_target(slug: str, **changes: object) -> dict[str, object]:
    """Return one canonical target object, optionally made parse-invalid."""
    target: dict[str, object] = {
        "kind": "spec",
        "path": f"docs/specs/{slug}/spec.md",
        "source": {"mode": "repo-origin"},
        "summary": f"Fixture target {slug}",
        "needs": [],
    }
    target.update(changes)
    return target


def _legacy_backlog_spec(slug: str) -> dict[str, object]:
    """Return the exact accepted legacy backlog spec shape."""
    return {
        "slug": slug,
        "source": "fixture",
        "summary": f"Legacy fixture {slug}",
        "needs": [],
        "type": "spec",
    }


def _legacy_shaping(slug: str) -> dict[str, object]:
    """Return the live slug-shaped legacy shaping object."""
    return {"slug": slug, "type": "shape", "needs": []}


def _write_repository(
    root: Path,
    selectors: Iterable[str],
    *,
    backlog_open: Iterable[object] = (),
    initiatives: Mapping[str, Mapping[str, Iterable[object]]] | None = None,
    existing_specs: Iterable[str] = (),
) -> RepositoryFixture:
    """Write a deterministic workspace fixture and optional spec artifacts."""
    root.mkdir(parents=True, exist_ok=True)
    lines = [
        "[backlog]",
        f"open = {_toml_value(list(backlog_open))}",
        "closed = []",
    ]
    for initiative, collections in (initiatives or {}).items():
        lines.extend(
            [
                "",
                f'["{initiative}"]',
                f'name = "Fixture {initiative}"',
                'status = "active"',
                'milestone = "fixture"',
                f'["{initiative}".work]',
                f"queue = {_toml_value(list(collections.get('work.queue', ())))}",
                f"active = {_toml_value(list(collections.get('work.active', ())))}",
                f"shipped = {_toml_value(list(collections.get('work.shipped', ())))}",
                f'["{initiative}".shaping_queue]',
                f"backlog = {_toml_value(list(collections.get('shaping_queue.backlog', ())))}",
                f"active = {_toml_value(list(collections.get('shaping_queue.active', ())))}",
            ]
        )
    (root / "workspace.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for slug in existing_specs:
        spec_path = root / "docs" / "specs" / slug / "spec.md"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(
            f"# Spec: {slug}\n\n- **Status:** Approved\n", encoding="utf-8"
        )
    return RepositoryFixture(root=root, selectors=tuple(selectors))


def _engine_surface() -> Callable[[Path, list[str]], object]:
    """Resolve the implementation-discovered seam inside each test body."""
    surface = getattr(ENGINE, "selected_membership_status", None)
    assert callable(surface), "selected-membership engine surface is absent"
    return surface


def _payload(fixture: RepositoryFixture) -> dict[str, Any]:
    """Invoke the selected-membership engine and normalize its public payload."""
    value = _engine_surface()(fixture.root, list(fixture.selectors))
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        value = dataclasses.asdict(value)
    assert isinstance(value, dict)
    return value


def _results(fixture: RepositoryFixture) -> list[dict[str, Any]]:
    """Return the ordered selected-spec result list."""
    results = _payload(fixture)["results"]
    assert isinstance(results, list)
    assert all(isinstance(result, dict) for result in results)
    return results


def _result(fixture: RepositoryFixture, selector: str | None = None) -> dict[str, Any]:
    """Return one selected result by its supplied directory."""
    wanted = selector or fixture.selectors[0]
    matches = [
        result
        for result in _results(fixture)
        if result["selected_directory"] == wanted
    ]
    assert len(matches) == 1
    return matches[0]


def _tree_snapshot(root: Path) -> dict[str, bytes]:
    """Return every regular fixture file keyed by repository-relative path."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _invoke_cli(
    fixture: RepositoryFixture,
    selectors: Iterable[str],
    *,
    route: str = SELECTED_MEMBERSHIP_ROUTE,
) -> tuple[int, dict[str, Any], str]:
    """Invoke the real CLI function through one captured argument path."""
    cli = _load_module("core_workspace_status_selection_membership_cli", CLI_PATH)
    if route == SELECTED_MEMBERSHIP_ROUTE:
        assert route in cli._SUBCOMMANDS, "selected-membership CLI surface is absent"
    argv = [route, "--root", str(fixture.root)]
    for selector in selectors:
        argv.extend((SELECTOR_FLAG, selector))
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = cli.main(argv)
    except SystemExit as exc:
        exit_code = int(exc.code)
    output = stdout.getvalue()
    payload = json.loads(output) if output else {}
    return exit_code, payload, stderr.getvalue()


@pytest.fixture
def empty_selection(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(tmp_path / "empty-selection", ())


@pytest.fixture
def unknown_subcommand(tmp_path: Path) -> str:
    return "definitely-unknown-workspace-status-command"


@pytest.fixture
def selected_artifact_absent(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(tmp_path / "artifact-absent", ("docs/specs/absent",))


@pytest.fixture
def invalid_selectors(
    tmp_path: Path, selected_artifact_absent: RepositoryFixture
) -> tuple[RepositoryFixture, tuple[str, ...]]:
    root = selected_artifact_absent.root
    escaped = root / "docs" / "specs" / "escaped"
    escaped.parent.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    escaped.symlink_to(outside, target_is_directory=True)
    invalid = (
        "/docs/specs/absolute",
        "C:/docs/specs/drive",
        "docs\\specs\\backslash",
        "docs/specs/../dot-segment",
        "docs/specs/file/spec.md",
        "docs/specs/group/nested",
        "docs/specs/escaped",
    )
    return selected_artifact_absent, invalid


@pytest.fixture
def selected_and_unselected_memberships(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(
        tmp_path / "selected-and-unselected",
        ("docs/specs/selected",),
        backlog_open=(_canonical_target("selected"), _canonical_target("unselected")),
    )


@pytest.fixture
def canonical_membership(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(
        tmp_path / "canonical", ("docs/specs/canonical",),
        backlog_open=(_canonical_target("canonical"),),
    )


@pytest.fixture
def legacy_work_collection_matrix(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(
        tmp_path / "legacy-work-matrix",
        ("docs/specs/legacy-queue", "docs/specs/legacy-active", "docs/specs/legacy-shipped"),
        initiatives={
            "ini-001": {
                "work.queue": ("spec/legacy-queue",),
                "work.active": ("spec/legacy-active",),
                "work.shipped": ("spec/legacy-shipped",),
            }
        },
    )


@pytest.fixture
def legacy_backlog_membership(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(
        tmp_path / "legacy-backlog", ("docs/specs/legacy-backlog",),
        backlog_open=(_legacy_backlog_spec("legacy-backlog"),),
    )


@pytest.fixture
def legacy_shaping_membership(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(
        tmp_path / "legacy-shaping",
        ("docs/specs/shared-name", "docs/specs/known-present"),
        backlog_open=(_canonical_target("known-present"),),
        initiatives={
            "ini-002": {"shaping_queue.active": (_legacy_shaping("shared-name"),)}
        },
    )


@pytest.fixture
def duplicate_canonical_membership(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(
        tmp_path / "duplicate-canonical", ("docs/specs/duplicate",),
        backlog_open=(_canonical_target("duplicate"), _canonical_target("duplicate")),
    )


@pytest.fixture
def duplicate_mixed_membership(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(
        tmp_path / "duplicate-mixed", ("docs/specs/duplicate",),
        backlog_open=(_canonical_target("duplicate"),),
        initiatives={"ini-003": {"work.active": ("spec/duplicate",)}},
    )


@pytest.fixture
def near_match_memberships(tmp_path: Path) -> RepositoryFixture:
    entries = tuple(
        _canonical_target(slug)
        for slug in ("exact", "Exact", "exact-prefix", "prefix-exact", "exact-sibling")
    )
    return _write_repository(
        tmp_path / "near-matches", ("docs/specs/exact",), backlog_open=entries
    )


@pytest.fixture
def canonical_collection_matrix(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(
        tmp_path / "canonical-collections",
        (
            "docs/specs/top-level",
            "docs/specs/queued",
            "docs/specs/active",
            "docs/specs/shipped",
        ),
        backlog_open=(_canonical_target("top-level"),),
        initiatives={
            "ini-004": {
                "work.queue": (_canonical_target("queued"),),
                "work.active": (_canonical_target("active"),),
                "work.shipped": (_canonical_target("shipped"),),
            }
        },
    )


@pytest.fixture
def mixed_presence_selection(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(
        tmp_path / "mixed-presence",
        ("docs/specs/present", "docs/specs/absent"),
        backlog_open=(_canonical_target("present"),),
    )


@pytest.fixture
def absence_occurrence_class_matrix(tmp_path: Path) -> RepositoryFixture:
    invalid = _canonical_target("parse-blocked", summary=7)
    return _write_repository(
        tmp_path / "absence-classes",
        (
            "docs/specs/canonical",
            "docs/specs/legacy",
            "docs/specs/parse-blocked",
            "docs/specs/absent",
        ),
        backlog_open=(_canonical_target("canonical"), invalid),
        initiatives={"ini-005": {"work.queue": ("spec/legacy",)}},
    )


@pytest.fixture
def occurrence_provenance_matrix(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(
        tmp_path / "provenance",
        (
            "docs/specs/top-canonical",
            "docs/specs/top-legacy",
            "docs/specs/initiative-canonical",
            "docs/specs/initiative-legacy",
        ),
        backlog_open=(
            _canonical_target("top-canonical"),
            _legacy_backlog_spec("top-legacy"),
        ),
        initiatives={
            "ini-006": {
                "work.active": (
                    _canonical_target("initiative-canonical"),
                    "spec/initiative-legacy",
                )
            }
        },
    )


@pytest.fixture
def identity_preserving_variants(tmp_path: Path) -> tuple[RepositoryFixture, ...]:
    first = _write_repository(
        tmp_path / "identity-first",
        ("docs/specs/present", "docs/specs/absent"),
        backlog_open=(_canonical_target("present"), _canonical_target("other")),
    )
    changed = _canonical_target("present", summary="Changed non-identity summary")
    second = _write_repository(
        tmp_path / "identity-second",
        first.selectors,
        backlog_open=(_canonical_target("other"), changed),
    )
    return first, second


@pytest.fixture
def deterministic_output(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(
        tmp_path / "deterministic",
        ("docs/specs/present", "docs/specs/absent"),
        backlog_open=(_canonical_target("present"),),
    )


@pytest.fixture
def invalid_workspace(tmp_path: Path) -> dict[str, RepositoryFixture]:
    malformed_root = tmp_path / "malformed"
    malformed_root.mkdir()
    (malformed_root / "workspace.toml").write_text("[backlog\n", encoding="utf-8")
    malformed = RepositoryFixture(malformed_root, ("docs/specs/selected",))
    invalid_root = tmp_path / "invalid-lifecycle"
    invalid_root.mkdir()
    (invalid_root / "workspace.toml").write_text(
        '["ini-invalid"]\nstatus = "active"\n["ini-invalid".work]\nqueue = "bad"\n',
        encoding="utf-8",
    )
    invalid = RepositoryFixture(invalid_root, ("docs/specs/selected",))
    return {
        "malformed_toml": malformed,
        "invalid_lifecycle_collection": invalid,
    }


@pytest.fixture
def parse_blocked_selected_membership(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(
        tmp_path / "selected-parse-blocked",
        ("docs/specs/blocked",),
        backlog_open=(_canonical_target("blocked", summary=7),),
    )


@pytest.fixture
def unselected_parse_blocked_membership(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(
        tmp_path / "unselected-parse-blocked",
        ("docs/specs/selected",),
        backlog_open=(
            _canonical_target("selected"),
            _canonical_target("unselected", summary=7),
        ),
    )


@pytest.fixture
def nested_selector(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(
        tmp_path / "nested-selector", ("docs/specs/group/nested",)
    )


@pytest.fixture
def duplicate_legacy_membership(tmp_path: Path) -> RepositoryFixture:
    return _write_repository(
        tmp_path / "duplicate-legacy", ("docs/specs/duplicate",),
        backlog_open=(_legacy_backlog_spec("duplicate"),),
        initiatives={"ini-007": {"work.shipped": ("spec/duplicate",)}},
    )


@pytest.fixture
def read_only_snapshot(tmp_path: Path) -> RepositoryFixture:
    fixture = _write_repository(
        tmp_path / "read-only",
        ("docs/specs/present", "docs/specs/absent"),
        backlog_open=(_canonical_target("present"),),
        existing_specs=("present",),
    )
    (fixture.root / "unrelated.txt").write_text("unchanged\n", encoding="utf-8")
    return fixture


def test_engine_rejects_empty_selection(empty_selection: RepositoryFixture) -> None:
    payload = _engine_surface()(empty_selection.root, [])

    assert payload == {"error": {"code": "empty_selection"}}


def test_engine_validates_selector_grammar_and_confinement(
    invalid_selectors: tuple[RepositoryFixture, tuple[str, ...]],
) -> None:
    fixture, invalid = invalid_selectors

    assert _payload(fixture)["results"][0]["membership_present"] is False
    assert all(
        _engine_surface()(fixture.root, [selector])
        == {"error": {"code": "invalid_selector"}}
        for selector in invalid
    )


def test_engine_reuses_canonical_extraction_and_alias_resolution() -> None:
    source = inspect.getsource(ENGINE.selected_membership_status)

    assert "_extract_canonical_memberships(" in source
    assert "_legacy_canonical_alias(" in source
    assert "parse_workspace(" in source
    assert "tomllib.load" not in source


def test_membership_check_performs_no_writes(
    read_only_snapshot: RepositoryFixture,
) -> None:
    before = _tree_snapshot(read_only_snapshot.root)

    payload = _payload(read_only_snapshot)

    assert [result["membership_present"] for result in payload["results"]] == [
        True,
        False,
    ]
    assert _tree_snapshot(read_only_snapshot.root) == before


def test_empty_selection_is_rejected_by_recognized_route(
    empty_selection: RepositoryFixture, unknown_subcommand: str
) -> None:
    empty_code, empty_payload, _ = _invoke_cli(empty_selection, ())
    unknown_code, unknown_payload, _ = _invoke_cli(
        empty_selection, (), route=unknown_subcommand
    )

    assert empty_code == 2
    assert empty_payload["reason"] == "empty_selection"
    assert unknown_code == 2
    assert unknown_payload["reason"] == "unknown_subcommand"
    assert empty_payload != unknown_payload


def test_selector_grammar_and_confinement_with_valid_absent_artifact_control(
    invalid_selectors: tuple[RepositoryFixture, tuple[str, ...]],
) -> None:
    fixture, invalid = invalid_selectors
    valid_code, valid_payload, _ = _invoke_cli(fixture, fixture.selectors)
    invalid_payloads = [_invoke_cli(fixture, (selector,)) for selector in invalid]

    assert valid_code == 0
    assert valid_payload["results"][0]["membership_present"] is False
    assert all(code == 2 for code, _, _ in invalid_payloads)
    assert all(payload["reason"] == "invalid_selector" for _, payload, _ in invalid_payloads)


def test_missing_selected_artifact_still_has_membership_result(
    selected_artifact_absent: RepositoryFixture,
) -> None:
    result = _result(selected_artifact_absent)

    assert result["selected_directory"] == "docs/specs/absent"
    assert result["canonical_artifact_path"] == "docs/specs/absent/spec.md"
    assert result["membership_present"] is False
    assert result["occurrences"] == []


def test_unselected_memberships_are_out_of_scope(
    selected_and_unselected_memberships: RepositoryFixture,
) -> None:
    results = _results(selected_and_unselected_memberships)

    assert len(results) == 1
    assert results[0]["membership_present"] is True
    assert len(results[0]["occurrences"]) == 1


def test_canonical_membership_is_present(canonical_membership: RepositoryFixture) -> None:
    result = _result(canonical_membership)

    assert result["membership_present"] is True
    assert [item["form"] for item in result["occurrences"]] == ["canonical"]


def test_legacy_work_alias_is_present_in_all_work_collections(
    legacy_work_collection_matrix: RepositoryFixture,
) -> None:
    results = _results(legacy_work_collection_matrix)

    assert all(result["membership_present"] is True for result in results)
    assert [result["occurrences"][0]["collection"] for result in results] == [
        "work.queue",
        "work.active",
        "work.shipped",
    ]
    assert all(result["occurrences"][0]["form"] == "legacy" for result in results)


def test_exact_legacy_backlog_spec_object_is_present(
    legacy_backlog_membership: RepositoryFixture,
) -> None:
    result = _result(legacy_backlog_membership)

    assert result["membership_present"] is True
    assert result["occurrences"][0]["collection"] == "backlog.open"
    assert result["occurrences"][0]["form"] == "legacy"


def test_non_spec_legacy_slug_is_not_a_spec_membership(
    legacy_shaping_membership: RepositoryFixture,
) -> None:
    shaping = _result(legacy_shaping_membership, "docs/specs/shared-name")
    sentinel = _result(legacy_shaping_membership, "docs/specs/known-present")

    assert shaping["membership_present"] is False
    assert shaping["occurrences"] == []
    assert sentinel["membership_present"] is True
    assert len(sentinel["occurrences"]) == 1


def test_canonical_duplicate_occurrences_are_retained(
    duplicate_canonical_membership: RepositoryFixture,
) -> None:
    result = _result(duplicate_canonical_membership)

    assert result["membership_present"] is True
    assert len(result["occurrences"]) == 2
    assert [item["form"] for item in result["occurrences"]] == ["canonical", "canonical"]


def test_mixed_canonical_legacy_duplicates_are_retained(
    duplicate_mixed_membership: RepositoryFixture,
) -> None:
    result = _result(duplicate_mixed_membership)

    assert result["membership_present"] is True
    assert len(result["occurrences"]) == 2
    assert {item["form"] for item in result["occurrences"]} == {"canonical", "legacy"}


def test_membership_identity_matching_is_exact(
    near_match_memberships: RepositoryFixture,
) -> None:
    result = _result(near_match_memberships)

    assert result["membership_present"] is True
    assert len(result["occurrences"]) == 1
    assert result["occurrences"][0]["canonical_artifact_path"] == "docs/specs/exact/spec.md"


def test_four_canonical_spec_collections_participate(
    canonical_collection_matrix: RepositoryFixture,
) -> None:
    results = _results(canonical_collection_matrix)

    assert all(result["membership_present"] is True for result in results)
    assert [result["occurrences"][0]["collection"] for result in results] == [
        "backlog.open",
        "work.queue",
        "work.active",
        "work.shipped",
    ]


def test_one_ordered_result_per_selected_spec(
    mixed_presence_selection: RepositoryFixture,
) -> None:
    results = _results(mixed_presence_selection)

    assert [result["selected_directory"] for result in results] == list(
        mixed_presence_selection.selectors
    )
    assert len(results) == len(mixed_presence_selection.selectors)


def test_presence_is_equivalent_to_nonempty_occurrences(
    mixed_presence_selection: RepositoryFixture,
) -> None:
    results = _results(mixed_presence_selection)

    assert [len(result["occurrences"]) for result in results] == [1, 0]
    assert all(
        result["membership_present"] is bool(result["occurrences"])
        for result in results
    )


def test_absence_requires_zero_resolved_occurrences(
    absence_occurrence_class_matrix: RepositoryFixture,
) -> None:
    results = _results(absence_occurrence_class_matrix)

    assert [len(result["occurrences"]) for result in results] == [1, 1, 1, 0]
    assert [result["membership_present"] for result in results] == [True, True, True, False]


def test_result_and_occurrence_provenance_is_complete_and_repository_relative(
    occurrence_provenance_matrix: RepositoryFixture,
) -> None:
    results = _results(occurrence_provenance_matrix)
    occurrences = [result["occurrences"][0] for result in results]

    assert all(not Path(result["canonical_artifact_path"]).is_absolute() for result in results)
    assert all(not Path(item["canonical_artifact_path"]).is_absolute() for item in occurrences)
    assert all({"initiative", "collection", "entry_index", "form"} <= set(item) for item in occurrences)
    assert {item["initiative"] for item in occurrences} == {None, "ini-006"}
    assert {item["form"] for item in occurrences} == {"canonical", "legacy"}


def test_non_identity_edits_do_not_change_results(
    identity_preserving_variants: tuple[RepositoryFixture, ...],
) -> None:
    snapshots = [
        [
            (
                result["selected_directory"],
                result["membership_present"],
                len(result["occurrences"]),
            )
            for result in _results(fixture)
        ]
        for fixture in identity_preserving_variants
    ]

    assert snapshots == [
        [("docs/specs/present", True, 1), ("docs/specs/absent", False, 0)],
        [("docs/specs/present", True, 1), ("docs/specs/absent", False, 0)],
    ]


def test_selected_membership_output_is_deterministic(
    deterministic_output: RepositoryFixture,
) -> None:
    first = json.dumps(_payload(deterministic_output), sort_keys=True, separators=(",", ":"))
    second = json.dumps(_payload(deterministic_output), sort_keys=True, separators=(",", ":"))

    assert first.encode("utf-8") == second.encode("utf-8")
    assert [len(result["occurrences"]) for result in _results(deterministic_output)] == [1, 0]


def test_invalid_workspace_failure_classes_never_report_absence(
    invalid_workspace: dict[str, RepositoryFixture],
) -> None:
    payloads = {name: _payload(fixture) for name, fixture in invalid_workspace.items()}

    assert payloads["malformed_toml"]["error"]["code"] == "malformed_toml"
    assert payloads["invalid_lifecycle_collection"]["error"]["code"] == "invalid_workspace"
    assert payloads["malformed_toml"] != payloads["invalid_lifecycle_collection"]
    assert all("results" not in payload for payload in payloads.values())


def test_matching_parse_blocked_entry_prevents_absence(
    parse_blocked_selected_membership: RepositoryFixture,
) -> None:
    result = _result(parse_blocked_selected_membership)

    assert result["membership_present"] is True
    assert len(result["occurrences"]) == 1
    assert result["occurrences"][0]["form"] == "parse-blocked"


def test_unselected_parse_failure_does_not_widen_scope(
    unselected_parse_blocked_membership: RepositoryFixture,
) -> None:
    results = _results(unselected_parse_blocked_membership)

    assert len(results) == 1
    assert results[0]["membership_present"] is True
    assert len(results[0]["occurrences"]) == 1
    assert results[0]["occurrences"][0]["form"] == "canonical"


def test_nested_selector_is_rejected(nested_selector: RepositoryFixture) -> None:
    payload = _payload(nested_selector)

    assert payload["error"]["code"] == "invalid_selector"
    assert "results" not in payload


def test_legacy_duplicate_occurrences_are_retained(
    duplicate_legacy_membership: RepositoryFixture,
) -> None:
    result = _result(duplicate_legacy_membership)

    assert result["membership_present"] is True
    assert len(result["occurrences"]) == 2
    assert [item["form"] for item in result["occurrences"]] == ["legacy", "legacy"]
