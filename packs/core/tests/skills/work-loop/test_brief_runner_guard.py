"""Run grant, integration: the ``guard`` verb over real commit pairs.

Each case builds a small repository, commits a base and a head, and runs the runner's
``guard`` as a child process, as the build-check step does.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

RUNNER = Path(__file__).resolve().parents[3] / ".apm/skills/work-loop/scripts/brief-runner.py"
GIT_ENV = {
    "PATH": os.environ.get("PATH", ""),
    "HOME": "/nonexistent",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.invalid",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.invalid",
}
BRIEF = "docs/product/briefs/b.md"
GRANT = "docs/product/run-grants/b.toml"
RECORD = "- **Run grant:** required (confirmed 2026-01-01T00:00:00Z)\n"


def brief(status: str = "Ready", rows: tuple[str, ...] = ("alpha",), extra: str = "") -> str:
    body = "\n".join(f"| `{r}` | <auto> |" for r in rows)
    return (
        f"# Brief\n\n- **Status:** {status}\n{extra}\n## Spec map\n\n| Spec | Status |\n"
        f"| --- | --- |\n{body}\n\nProse.\n"
    )


def spec(status: str) -> str:
    return f"# Spec\n\n- **Status:** {status}\n"


def git(root: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(root), *args], env=GIT_ENV, capture_output=True, check=True, text=True
    )
    return done.stdout.strip()


def put(root: Path, files: dict[str, str | None]) -> None:
    for name, text in files.items():
        path = root / name
        if text is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")


def commit(root: Path, files: dict[str, str | None]) -> str:
    put(root, files)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "c")
    return git(root, "rev-parse", "HEAD")


def run_guard(root: Path, base: str, head: str) -> tuple[int, dict[str, Any]]:
    done = subprocess.run(
        [sys.executable, "-I", str(RUNNER), "guard", "--from", base, "--to", head,
         "--root", str(root)],
        env=GIT_ENV, capture_output=True, text=True, check=False,
    )  # fmt: skip
    return done.returncode, json.loads(done.stdout)


def pair(
    tmp_path: Path, before: dict[str, str | None], after: dict[str, str | None]
) -> tuple[Path, str, str]:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    base = commit(root, {"README.md": "x\n", **before})
    return root, base, commit(root, after)


def kinds(answer: dict[str, Any]) -> dict[str, str]:
    return {c["path"]: c["kind"] for c in answer["grant_changes"]}


def test_a_grant_file_alone_passes(tmp_path: Path) -> None:
    root, a, b = pair(tmp_path, {}, {GRANT: "x = 1\n"})
    code, out = run_guard(root, a, b)
    assert code == 0 and out["verdict"] == "pass" and "refusal" not in out
    assert kinds(out) == {GRANT: "grant-file"} and out["other_paths"] == 0


def test_standing_orders_alone_pass(tmp_path: Path) -> None:
    path = "docs/product/standing-orders/b.md"
    root, a, b = pair(tmp_path, {}, {path: "1. x\n"})
    code, out = run_guard(root, a, b)
    assert code == 0 and kinds(out) == {path: "standing-orders"}


def test_a_brief_made_ready_alone_passes(tmp_path: Path) -> None:
    root, a, b = pair(tmp_path, {BRIEF: brief("Draft")}, {BRIEF: brief("Ready")})
    code, out = run_guard(root, a, b)
    assert code == 0 and kinds(out) == {BRIEF: "brief-made-runnable"}


def test_a_new_brief_committed_ready_is_a_grant_change(tmp_path: Path) -> None:
    root, a, b = pair(tmp_path, {}, {BRIEF: brief("Ready")})
    assert kinds(run_guard(root, a, b)[1]) == {BRIEF: "brief-made-runnable"}


@pytest.mark.parametrize(
    "extra",
    [
        {"src/code.py": "x = 1\n"},
        {"docs/knowledge/n.md": "note\n"},
        {".github/workflows/w.yml": "name: w\n"},
    ],
)
@pytest.mark.parametrize("change", ["grant", "orders", "ready"])
def test_each_grant_change_mixed_with_another_path_fails(
    tmp_path: Path, change: str, extra: dict[str, str | None]
) -> None:
    before = {BRIEF: brief("Draft")}
    grant = {
        "grant": {GRANT: "x = 1\n"},
        "orders": {"docs/product/standing-orders/b.md": "1. x\n"},
        "ready": {BRIEF: brief("Ready")},
    }[change]
    root, a, b = pair(tmp_path, before, {**grant, **extra})
    code, out = run_guard(root, a, b)
    assert code == 1 and out["verdict"] == "fail" and out["other_paths"] == 1
    assert out["refusal"] == {
        "code": "grant-change-mixed",
        "detail": "grant changes are mixed with other paths",
    }


def test_the_guard_surface_is_listed_and_counts_as_another_path(tmp_path: Path) -> None:
    runner = "packs/core/.apm/skills/work-loop/scripts/brief-runner.py"
    root, a, b = pair(tmp_path, {}, {GRANT: "x = 1\n", runner: "#\n"})
    code, out = run_guard(root, a, b)
    assert code == 1 and out["guard_surface"] == [runner] and out["other_paths"] == 1


def test_a_ready_to_executing_edit_is_not_a_grant_change(tmp_path: Path) -> None:
    root, a, b = pair(
        tmp_path, {BRIEF: brief("Ready")}, {BRIEF: brief("Executing"), "src/c.py": "1\n"}
    )
    code, out = run_guard(root, a, b)
    assert code == 0 and out["grant_changes"] == [] and out["other_paths"] == 2


def test_a_prose_edit_to_a_no_grant_ready_brief_is_not_one(tmp_path: Path) -> None:
    root, a, b = pair(
        tmp_path, {BRIEF: brief("Ready")}, {BRIEF: brief("Ready") + "More.\n", "x.py": "1\n"}
    )
    assert run_guard(root, a, b)[1]["grant_changes"] == []


def test_a_draft_brief_edit_is_not_one(tmp_path: Path) -> None:
    root, a, b = pair(
        tmp_path, {BRIEF: brief("Draft")}, {BRIEF: brief("Draft") + "More.\n", "x.py": "1\n"}
    )
    code, out = run_guard(root, a, b)
    assert code == 0 and out["grant_changes"] == []


def test_a_prose_edit_to_a_granted_brief_is_brief_granted(tmp_path: Path) -> None:
    granted = brief("Ready", extra=RECORD)
    root, a, b = pair(tmp_path, {BRIEF: granted}, {BRIEF: granted + "More.\n"})
    assert kinds(run_guard(root, a, b)[1]) == {BRIEF: "brief-granted"}


def test_a_grant_file_beside_a_brief_counts_as_evidence(tmp_path: Path) -> None:
    root, a, b = pair(
        tmp_path, {BRIEF: brief("Ready"), GRANT: "x = 1\n"}, {BRIEF: brief("Ready") + "More.\n"}
    )
    assert kinds(run_guard(root, a, b)[1]) == {BRIEF: "brief-granted"}


def test_added_trailing_text_on_a_granted_status_line_is_brief_granted(tmp_path: Path) -> None:
    granted = brief("Ready", extra=RECORD)
    edited = granted.replace("- **Status:** Ready", "- **Status:** Ready (and then some)")
    root, a, b = pair(tmp_path, {BRIEF: granted}, {BRIEF: edited})
    assert kinds(run_guard(root, a, b)[1]) == {BRIEF: "brief-granted"}


def test_a_granted_brief_closed_to_shipped_is_not_a_grant_change(tmp_path: Path) -> None:
    granted = brief("Executing", extra=RECORD)
    root, a, b = pair(
        tmp_path,
        {BRIEF: granted},
        {
            BRIEF: brief("Shipped", extra=RECORD) + "Cut-closed: done.\n",
            "docs/product/briefs/other.md": "x\n",
            "src/c.py": "1\n",
        },
    )
    code, out = run_guard(root, a, b)
    assert code == 0 and out["grant_changes"] == []


def test_a_spec_map_edit_on_a_ready_brief_allows_the_added_rows_new_drafts(
    tmp_path: Path,
) -> None:
    drafts = {
        "docs/specs/beta/spec.md": spec("Draft"),
        "docs/specs/beta/plan.md": "# Plan\n\n- **Status:** Drafting\n",
    }
    root, a, b = pair(
        tmp_path, {BRIEF: brief("Ready")}, {BRIEF: brief("Ready", ("alpha", "beta")), **drafts}
    )
    code, out = run_guard(root, a, b)
    assert code == 0 and kinds(out) == {BRIEF: "brief-spec-map"}
    assert out["companions"] == sorted(drafts) and out["other_paths"] == 0


@pytest.mark.parametrize(
    "extra",
    [
        {"docs/knowledge/n.md": "note\n"},
        {"docs/specs/beta/delivery/r.md": "record\n"},
        {"docs/specs/beta/spec.md": spec("Approved")},
        {"docs/adr/0001-x.md": "adr\n"},
        {"docs/specs/gamma/spec.md": spec("Draft")},
    ],
)
def test_a_spec_map_edit_fails_beside_anything_but_the_new_drafts(
    tmp_path: Path, extra: dict[str, str | None]
) -> None:
    files = {
        "docs/specs/beta/spec.md": spec("Draft"),
        "docs/specs/beta/plan.md": "# Plan\n\n- **Status:** Drafting\n",
        **extra,
    }
    root, a, b = pair(
        tmp_path, {BRIEF: brief("Ready")}, {BRIEF: brief("Ready", ("alpha", "beta")), **files}
    )
    code, out = run_guard(root, a, b)
    assert code == 1 and out["refusal"]["code"] == "grant-change-mixed"
    assert out["other_paths"] >= 1


def test_an_existing_spec_is_not_a_companion(tmp_path: Path) -> None:
    root, a, b = pair(
        tmp_path,
        {BRIEF: brief("Ready"), "docs/specs/beta/spec.md": spec("Draft")},
        {BRIEF: brief("Ready", ("alpha", "beta")), "docs/specs/beta/spec.md": spec("Draft") + "x\n"},
    )
    code, out = run_guard(root, a, b)
    assert code == 1 and out["companions"] == []


def test_the_two_change_route_fails_on_its_first_change(tmp_path: Path) -> None:
    root, a, b = pair(
        tmp_path,
        {BRIEF: brief("Ready")},
        {BRIEF: brief("Draft", ("alpha", "beta")), "src/c.py": "1\n"},
    )
    code, out = run_guard(root, a, b)
    assert code == 1 and kinds(out) == {BRIEF: "brief-spec-map"}


def test_a_deleted_grant_file_is_a_grant_change(tmp_path: Path) -> None:
    root, a, b = pair(tmp_path, {GRANT: "x = 1\n"}, {GRANT: None, "src/c.py": "1\n"})
    code, out = run_guard(root, a, b)
    assert code == 1 and kinds(out) == {GRANT: "grant-file"}


def test_a_renamed_grant_file_lists_both_sides(tmp_path: Path) -> None:
    new = "docs/product/run-grants/c.toml"
    root, a, b = pair(tmp_path, {GRANT: "x = 1\n"}, {GRANT: None, new: "x = 1\n"})
    out = run_guard(root, a, b)[1]
    assert kinds(out) == {GRANT: "grant-file", new: "grant-file"}


def test_an_unsafe_path_prints_withheld(tmp_path: Path) -> None:
    bad = "docs/product/run-grants/a‮b.toml"
    root, a, b = pair(tmp_path, {}, {bad: "x = 1\n"})
    out = run_guard(root, a, b)[1]
    assert out["grant_changes"] == [{"path": "withheld", "kind": "grant-file"}]


def test_an_unknown_revision_refuses(tmp_path: Path) -> None:
    root, a, _ = pair(tmp_path, {}, {"x.py": "1\n"})
    for argv in ((a, "0" * 40), ("nonesuch", a)):
        code, out = run_guard(root, *argv)
        assert code == 1
        assert set(out) == {"refusal"} and out["refusal"]["code"] == "unknown-revision"


def test_unrelated_histories_refuse_for_want_of_a_merge_base(tmp_path: Path) -> None:
    root, a, _ = pair(tmp_path, {}, {"x.py": "1\n"})
    git(root, "checkout", "-q", "--orphan", "other")
    other = commit(root, {"y.py": "1\n"})
    code, out = run_guard(root, a, other)
    assert code == 1 and out["refusal"]["code"] == "unknown-revision"


def test_the_output_keys_are_exactly_the_contract(tmp_path: Path) -> None:
    root, a, b = pair(tmp_path, {}, {GRANT: "x = 1\n"})
    out = run_guard(root, a, b)[1]
    assert list(out) == [
        "companions", "grant_changes", "guard_surface", "merge_base", "other_paths", "to",
        "verdict",
    ]  # fmt: skip
    assert out["merge_base"] == a and out["to"] == b


def test_guard_writes_nothing(tmp_path: Path) -> None:
    root, a, b = pair(tmp_path, {}, {GRANT: "x = 1\n", "src/c.py": "1\n"})
    snapshot: Callable[[], tuple[str, ...]] = lambda: (  # noqa: E731
        git(root, "status", "--porcelain", "--ignored"),
        git(root, "for-each-ref"),
        git(root, "count-objects", "-v"),
        ",".join(sorted(str(p.relative_to(root)) for p in root.rglob("*") if ".git" not in p.parts)),
    )
    before = snapshot()
    run_guard(root, a, b)
    assert snapshot() == before
