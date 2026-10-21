"""Construction tests for the changed-artifact pointer check.

Drives the production CLI through ``main(argv)`` in disposable git
repositories. Expensive repositories are built once per module and copied.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / ".apm" / "skills" / "work-loop" / "scripts" / "lint-graph-pointers.py"
)


def _load() -> ModuleType:
    name = "core_work_loop_lint_graph_pointers"
    spec = importlib.util.spec_from_file_location(name, _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = prev
    return mod


lint = _load()

_GIT_ENV = {
    **{k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
}


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=T", "-c", "user.email=t@example.invalid",
         "-c", "commit.gpgsign=false", *args],
        check=True, capture_output=True, env=_GIT_ENV,
    )


def write(repo: Path, rel: str, content: str | bytes) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def doc(preamble: str, title: str = "Doc") -> str:
    return f"# {title}\n\n{preamble}\n\n## Body\n\ntext\n"


def run(repo: Path, capsys: pytest.CaptureFixture[str], base: str = "base") -> tuple[int, str, str]:
    capsys.readouterr()
    code = lint.main(["--root", str(repo), "--base-ref", base])
    out = capsys.readouterr()
    return code, out.out, out.err


def parse(out: str) -> dict[str, list[tuple[str, str]]]:
    found: dict[str, list[tuple[str, str]]] = {}
    for line in out.splitlines():
        if line.startswith("lint-graph-pointers:"):
            continue
        path, field, code = line.split(": ")
        found.setdefault(path, []).append((field, code))
    return found


BAD_PARENT = "- **Parent intent:** ../../etc/passwd"
INV = "intents"

TEMPLATE_FILES: dict[str, str | bytes] = {
    "docs/product/intents/outcome-a.md": doc("- **Slug:** svc-reliability\n- **Kind:** outcome"),
    "docs/product/intents/opp-a.md": doc("- **Slug:** opp-one\n- **Kind:** `opportunity` (x)"),
    "docs/product/intents/cap-a.md": doc("- **Slug:** cap-lvl\n- **Level:** capability"),
    "docs/product/intents/kind-wins.md": doc(
        "- **Slug:** kind-wins\n- **Kind:** outcome\n- **Level:** capability"),
    "docs/product/intents/plain.md": doc("- **Slug:** plain-one"),
    "docs/product/intents/old.md": doc("- **Slug:** old-one\n- **Tombstone:** superseded"),
    "docs/product/intents/twin-1.md": doc("- **Slug:** twin"),
    "docs/product/intents/twin-2.md": doc("- **Slug:** twin"),
    "docs/product/intents/_template.md": doc("- **Slug:** template-slug"),
    "docs/product/intents/untouched-bad.md": doc(f"- **Slug:** untouched-one\n{BAD_PARENT}"),
    "docs/product/briefs/b-one.md": doc("- **Slug:** b-one"),
    "docs/product/briefs/b-old.md": doc("- **Slug:** b-old\n- **Tombstone:** gone"),
    "docs/product/briefs/b-twin-1.md": doc("- **Slug:** b-twin"),
    "docs/product/briefs/b-twin-2.md": doc("- **Slug:** b-twin"),
    "docs/specs/tracked/spec.md": doc("- **Brief:** brief:b-one"),
    "docs/specs/old-name/spec.md": doc(f"{BAD_PARENT}"),
    "docs/specs/doomed/spec.md": b"\xff\xfe\x00bad",
}


@pytest.fixture(scope="module")
def template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    repo = tmp_path_factory.mktemp("template") / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    for rel, content in TEMPLATE_FILES.items():
        write(repo, rel, content)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    git(repo, "tag", "base")
    return repo


@pytest.fixture
def repo(template: Path, tmp_path: Path) -> Path:
    dest = tmp_path / "repo"
    shutil.copytree(template, dest, symlinks=True)
    return dest


# ---------------------------------------------------------------------------
# VI-1001: selection
# ---------------------------------------------------------------------------


def test_selection_covers_every_change_state(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = doc(BAD_PARENT)
    write(repo, "docs/specs/committed/spec.md", bad)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "c")
    write(repo, "docs/specs/staged/spec.md", bad)
    git(repo, "add", "docs/specs/staged/spec.md")
    write(repo, "docs/specs/tracked/spec.md", bad)  # unstaged edit of a tracked file
    write(repo, "docs/specs/untracked/spec.md", bad)
    code, out, _ = run(repo, capsys)
    assert code == 1
    assert sorted(parse(out)) == [
        "docs/specs/committed/spec.md",
        "docs/specs/staged/spec.md",
        "docs/specs/tracked/spec.md",
        "docs/specs/untracked/spec.md",
    ]


def test_rename_selects_destination_only(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (repo / "docs/specs/new-name").mkdir()
    git(repo, "mv", "docs/specs/old-name/spec.md", "docs/specs/new-name/spec.md")
    code, out, _ = run(repo, capsys)
    assert code == 1
    assert list(parse(out)) == ["docs/specs/new-name/spec.md"]


def test_deleted_artifacts_are_never_read(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (repo / "docs/specs/doomed/spec.md").unlink()
    (repo / "docs/specs/old-name/spec.md").unlink()
    code, out, err = run(repo, capsys)
    assert (code, err) == (0, "")
    assert "0 violation(s) in 0 selected" in out


def test_untouched_bad_artifact_not_reported_beside_changed_sibling(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write(repo, "docs/product/intents/sibling.md", doc("- **Slug:** sib\n- **Parent intent:** outcome:svc-reliability"))
    code, out, _ = run(repo, capsys)
    assert code == 0
    assert "0 violation(s) in 1 selected" in out
    assert "untouched-bad" not in out


def test_change_landed_on_base_branch_is_not_selected(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    git(repo, "checkout", "-q", "-b", "feat")
    write(repo, "docs/specs/feat-one/spec.md", doc("- **Brief:** brief:b-one"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "feat")
    git(repo, "checkout", "-q", "main")
    write(repo, "docs/specs/old-name/spec.md", doc("- **Brief:** none"))
    git(repo, "commit", "-q", "-am", "landed on main")
    git(repo, "checkout", "-q", "feat")
    code, out, _ = run(repo, capsys, base="main")
    assert code == 0
    assert "0 violation(s) in 1 selected" in out


def test_non_artifact_paths_are_ignored(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(repo, "docs/specs/_template/spec.md", doc(BAD_PARENT))
    write(repo, "docs/product/intents/_template.md", doc(BAD_PARENT))
    write(repo, "docs/product/intents/sub/deep.md", doc(BAD_PARENT))
    write(repo, "docs/specs/x/notes.md", doc(BAD_PARENT))
    write(repo, "README.md", doc(BAD_PARENT))
    code, out, _ = run(repo, capsys)
    assert code == 0
    assert "0 violation(s) in 0 selected" in out


# ---------------------------------------------------------------------------
# VI-1002: field rules (one invocation over many selected specs)
# ---------------------------------------------------------------------------

P = "Parent intent"
CASES: dict[str, tuple[str, list[tuple[str, str]]]] = {
    # passing
    "ok-outcome": (f"- **{P}:** outcome:svc-reliability", []),
    "ok-opportunity": (f"- **{P}:** opportunity:opp-one", []),
    "ok-capability-level": (f"- **{P}:** capability:cap-lvl", []),
    "ok-kind-beats-level": (f"- **{P}:** outcome:kind-wins", []),
    "ok-plain-intent": (f"- **{P}:** intent:plain-one", []),
    "ok-backticks": (f"- **{P}:** `intent:plain-one`", []),
    "ok-brief": ("- **Brief:** brief:b-one", []),
    "ok-absent": ("- **Slug:** nothing", []),
    "ok-blank": (f"- **{P}:**\n- **Brief:**   ", []),
    "ok-comment-only": (f"- **{P}:** <!-- {BAD_PARENT} -->", []),
    "ok-none": (f"- **{P}:** None\n- **Brief:** NONE (no brief yet)", []),
    "ok-commented-line": (f"<!--\n{BAD_PARENT}\n- **Brief:** nope\n-->", []),
    "ok-body-text": (f"- **Slug:** x\n\n## Body\n\n{BAD_PARENT}\n- **Brief:** nope\n", []),
    # failing
    "wrong-kind": (f"- **{P}:** outcome:plain-one", [(P, "parent-intent-wrong-kind")]),
    "wrong-kind-level": (f"- **{P}:** intent:cap-lvl", [(P, "parent-intent-wrong-kind")]),
    "typed-brief": (f"- **{P}:** brief:b-one", [(P, "parent-intent-wrong-kind")]),
    "missing": (f"- **{P}:** outcome:nowhere", [(P, "parent-intent-missing")]),
    "template-not-node": (f"- **{P}:** intent:template-slug", [(P, "parent-intent-missing")]),
    "retired": (f"- **{P}:** intent:old-one", [(P, "parent-intent-retired")]),
    "ambiguous": (f"- **{P}:** intent:twin", [(P, "parent-intent-ambiguous")]),
    "bare-slug": (f"- **{P}:** svc-reliability", [(P, "parent-intent-untyped")]),
    "repo-path": (f"- **{P}:** docs/product/intents/outcome-a.md", [(P, "parent-intent-untyped")]),
    "md-link": (f"- **{P}:** [x](docs/product/intents/outcome-a.md)", [(P, "parent-intent-untyped")]),
    "malformed-slug": (f"- **{P}:** outcome:Bad_Slug", [(P, "parent-intent-malformed")]),
    "malformed-trailing": (f"- **{P}:** outcome:svc-reliability extra", [(P, "parent-intent-malformed")]),
    "brief-untyped": ("- **Brief:** b-one", [("Brief", "brief-untyped")]),
    "brief-path": ("- **Brief:** docs/product/briefs/b-one.md", [("Brief", "brief-untyped")]),
    "brief-malformed": ("- **Brief:** brief:B_one", [("Brief", "brief-malformed")]),
    "brief-missing": ("- **Brief:** brief:nowhere", [("Brief", "brief-missing")]),
    "brief-retired": ("- **Brief:** brief:b-old", [("Brief", "brief-retired")]),
    "brief-ambiguous": ("- **Brief:** brief:b-twin", [("Brief", "brief-ambiguous")]),
    "repeated-second-bad": (
        f"- **{P}:** intent:plain-one\n- **{P}:** plain-one",
        [(P, "parent-intent-untyped")]),
    "both-fields": (
        f"- **{P}:** nope\n- **Brief:** nope",
        [("Brief", "brief-untyped"), (P, "parent-intent-untyped")]),
}


@pytest.fixture(scope="module")
def field_results(template: Path, tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    for label, wanted in (("pass", True), ("fail", False)):
        dest = tmp_path_factory.mktemp(f"fields-{label}") / "repo"
        shutil.copytree(template, dest, symlinks=True)
        for name, (preamble, expected) in CASES.items():
            if (not expected) == wanted:
                write(dest, f"docs/specs/{name}/spec.md", doc(preamble))
        buf, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            code = lint.main(["--root", str(dest), "--base-ref", "base"])
        results[label] = {"code": code, "out": buf.getvalue(), "err": err.getvalue()}
    return results


def test_passing_fields_exit_zero(field_results: dict[str, dict[str, object]]) -> None:
    res = field_results["pass"]
    assert res["code"] == 0
    assert res["err"] == ""
    assert "0 violation(s)" in str(res["out"])


def test_failing_fields_exit_one(field_results: dict[str, dict[str, object]]) -> None:
    assert field_results["fail"]["code"] == 1


@pytest.mark.parametrize("name", [n for n, (_, e) in CASES.items() if e])
def test_field_diagnostic(name: str, field_results: dict[str, dict[str, object]]) -> None:
    found = parse(str(field_results["fail"]["out"]))
    assert sorted(found[f"docs/specs/{name}/spec.md"]) == sorted(CASES[name][1])


def test_diagnostics_are_sorted_and_summarised(field_results: dict[str, dict[str, object]]) -> None:
    lines = str(field_results["fail"]["out"]).splitlines()
    body, summary = lines[:-1], lines[-1]
    assert body == sorted(body)
    n_expected = sum(len(e) for _, e in CASES.values())
    assert summary.startswith(f"lint-graph-pointers: {n_expected} violation(s) in ")


def test_body_only_edit_still_checks_preamble(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(repo, "docs/specs/old-name/spec.md", doc(BAD_PARENT).replace("text", "edited text"))
    code, out, _ = run(repo, capsys)
    assert code == 1
    assert parse(out) == {"docs/specs/old-name/spec.md": [(P, "parent-intent-untyped")]}


def test_field_rules_apply_in_intents_and_briefs(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(repo, "docs/product/intents/new.md", doc(f"- **Slug:** n1\n- **{P}:** n1"))
    write(repo, "docs/product/briefs/new.md", doc(f"- **Slug:** nb\n- **{P}:** outcome:svc-reliability\n- **Brief:** x"))
    code, out, _ = run(repo, capsys)
    assert code == 1
    assert parse(out) == {
        "docs/product/briefs/new.md": [("Brief", "brief-untyped")],
        "docs/product/intents/new.md": [(P, "parent-intent-untyped")],
    }


# ---------------------------------------------------------------------------
# VI-1003: boundaries
# ---------------------------------------------------------------------------


def _select_one(repo: Path) -> None:
    write(repo, "docs/specs/probe/spec.md", doc("- **Brief:** brief:b-one"))


@pytest.mark.parametrize("ref", ["no-such-ref", "bad ref", "--foo", "", "x\x00y", "a\nb"])
def test_unavailable_or_hostile_base_ref_refuses(
    ref: str, repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _select_one(repo)
    capsys.readouterr()
    code = lint.main(["--root", str(repo), f"--base-ref={ref}"])
    out = capsys.readouterr()
    assert code == 2
    assert out.out == ""
    assert out.err.strip() == "lint-graph-pointers: base-unavailable"


def test_non_directory_root_refuses(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, _, err = run(tmp_path / "missing", capsys)
    assert code == 2
    assert err.strip() == "lint-graph-pointers: root-invalid"


def test_non_repository_root_refuses(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, _, err = run(tmp_path, capsys)
    assert code == 2
    assert "base-unavailable" in err


def test_symlinked_intent_file_refuses(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _select_one(repo)
    (repo / "docs/product/intents/link.md").symlink_to(repo / "docs/product/intents/plain.md")
    code, out, err = run(repo, capsys)
    assert (code, out) == (2, "")
    assert err.strip().startswith("lint-graph-pointers: unsafe-artifact")


def test_symlinked_collection_root_refuses(
    repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _select_one(repo)
    elsewhere = tmp_path / "elsewhere"
    shutil.move(str(repo / "docs/product/briefs"), elsewhere)
    (repo / "docs/product/briefs").symlink_to(elsewhere)
    code, out, err = run(repo, capsys)
    assert (code, out) == (2, "")
    assert err.strip() == "lint-graph-pointers: unsafe-artifact docs/product/briefs"


def test_missing_collections_are_empty(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    shutil.rmtree(repo / "docs/product")
    write(repo, "docs/specs/probe/spec.md", doc("- **Brief:** brief:b-one"))
    code, out, _ = run(repo, capsys)
    assert code == 1
    assert parse(out) == {"docs/specs/probe/spec.md": [("Brief", "brief-missing")]}


def test_invalid_utf8_in_target_file_refuses(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _select_one(repo)
    write(repo, "docs/product/intents/broken.md", b"- **Slug:** \xff\xfe\n")
    code, out, err = run(repo, capsys)
    assert (code, out) == (2, "")
    assert err.strip() == "lint-graph-pointers: invalid-utf8 docs/product/intents/broken.md"


def test_invalid_utf8_in_selected_spec_refuses(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(repo, "docs/specs/probe/spec.md", b"- **Brief:** \xff\n")
    code, out, err = run(repo, capsys)
    assert (code, out) == (2, "")
    assert err.strip() == "lint-graph-pointers: invalid-utf8 docs/specs/probe/spec.md"


def test_oversized_target_refuses(
    repo: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _select_one(repo)
    monkeypatch.setattr(lint, "MAX_ARTIFACT_BYTES", 10)
    code, _, err = run(repo, capsys)
    assert code == 2
    assert err.startswith("lint-graph-pointers: resource-limit")


def test_no_change_repository_is_clean(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out, err = run(repo, capsys)
    assert (code, err) == (0, "")
    assert out.strip() == "lint-graph-pointers: 0 violation(s) in 0 selected artifact(s)"


def test_unexpected_exception_is_sanitised(
    repo: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(*_a: object) -> int:
        raise RuntimeError(str(repo))

    monkeypatch.setattr(lint, "_run", boom)
    code, out, err = run(repo, capsys)
    assert (code, out) == (2, "")
    assert err.strip() == "lint-graph-pointers: internal-error"


def test_output_never_echoes_values_or_host_paths(
    repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write(repo, "docs/specs/hostile/spec.md", doc(
        f"- **{P}:** ../../etc/passwd\x1b[31m\n- **Brief:** \x1b]0;title\x07evil"))
    write(repo, "docs/specs/probe/spec.md", b"\xff")
    code, out, err = run(repo, capsys)
    assert code == 2
    capsys.readouterr()
    (repo / "docs/specs/probe/spec.md").unlink()
    code, out, err = run(repo, capsys)
    assert code == 1
    for stream in (out, err):
        assert "passwd" not in stream
        assert "evil" not in stream
        assert "\x1b" not in stream
        assert str(tmp_path) not in stream
        assert "Traceback" not in stream


def _snapshot(repo: Path) -> dict[str, bytes]:
    return {
        p.relative_to(repo).as_posix(): p.read_bytes()
        for p in sorted(repo.rglob("*"))
        if p.is_file() and not p.is_symlink()
    }


def test_invocation_does_not_modify_the_repository(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write(repo, "docs/specs/tracked/spec.md", doc(BAD_PARENT))
    write(repo, "docs/specs/fresh/spec.md", doc("- **Brief:** brief:b-one"))
    before = _snapshot(repo)
    code, _, _ = run(repo, capsys)
    assert code == 1
    assert _snapshot(repo) == before


# ---------------------------------------------------------------------------
# VI-2001: the `Discovery:` rule (changed specs only)
# ---------------------------------------------------------------------------

D = "Discovery"
DISCOVERY_CASES: dict[str, tuple[str, list[tuple[str, str]]]] = {
    # passing
    "d-ok-outcome": (f"- **{D}:** outcome:svc-reliability", []),
    "d-ok-opportunity": (f"- **{D}:** opportunity:opp-one", []),
    "d-ok-capability": (f"- **{D}:** capability:cap-lvl", []),
    "d-ok-intent": (f"- **{D}:** intent:plain-one", []),
    "d-ok-backticks": (f"- **{D}:** `intent:plain-one`", []),
    "d-ok-bare-nonlive": (f"- **{D}:** not-an-intent", []),
    "d-ok-bare-retired": (f"- **{D}:** old-one", []),
    "d-ok-research": (f"- **{D}:** docs/research/topic.md", []),
    "d-ok-notes": (f"- **{D}:** docs/specs/other/notes/discovery.md", []),
    "d-ok-research-link": (f"- **{D}:** [r](../../research/topic.md)", []),
    "d-ok-scheme-link": (
        f"- **{D}:** [x](https://example.invalid/docs/product/./intents/a.md)", []),
    "d-ok-brief": (f"- **{D}:** brief:b-one", []),
    "d-ok-spec": (f"- **{D}:** spec:tracked", []),
    "d-ok-url": (f"- **{D}:** https://example.invalid/page", []),
    "d-ok-free-text": (f"- **{D}:** talked to the team", []),
    "d-ok-absent": ("- **Slug:** nothing", []),
    "d-ok-blank": (f"- **{D}:**   ", []),
    "d-ok-comment-only": (f"- **{D}:** <!-- docs/product/intents/outcome-a.md -->", []),
    "d-ok-none": (f"- **{D}:** None", []),
    "d-ok-none-reason": (f"- **{D}:** None — docs/product/intents/outcome-a.md", []),
    "d-ok-commented-line": (f"<!--\n- **{D}:** docs/product/intents/outcome-a.md\n-->", []),
    "d-ok-body-text": (
        f"- **Slug:** x\n\n## Body\n\n- **{D}:** docs/product/intents/outcome-a.md\n", []),
    # failing
    "d-wrong-kind": (f"- **{D}:** outcome:plain-one", [(D, "discovery-wrong-kind")]),
    "d-wrong-kind-level": (f"- **{D}:** intent:cap-lvl", [(D, "discovery-wrong-kind")]),
    "d-malformed": (f"- **{D}:** outcome:Bad_Slug", [(D, "discovery-malformed")]),
    "d-malformed-trailing": (
        f"- **{D}:** outcome:svc-reliability extra", [(D, "discovery-malformed")]),
    "d-malformed-empty": (f"- **{D}:** intent:", [(D, "discovery-malformed")]),
    "d-missing": (f"- **{D}:** outcome:nowhere", [(D, "discovery-missing")]),
    "d-retired": (f"- **{D}:** intent:old-one", [(D, "discovery-retired")]),
    "d-ambiguous": (f"- **{D}:** intent:twin", [(D, "discovery-ambiguous")]),
    "d-repo-path": (f"- **{D}:** docs/product/intents/outcome-a.md", [(D, "discovery-untyped")]),
    "d-repo-path-missing": (f"- **{D}:** docs/product/intents/ghost.md", [(D, "discovery-untyped")]),
    "d-rel-link": (
        f"- **{D}:** [x](../../product/intents/outcome-a.md)", [(D, "discovery-untyped")]),
    "d-rel-link-fragment": (
        f"- **{D}:** [x](../../product/intents/outcome-a.md#top)", [(D, "discovery-untyped")]),
    "d-slash-link": (
        f"- **{D}:** [x](/docs/product/intents/outcome-a.md)", [(D, "discovery-untyped")]),
    "d-spec-relative-link": (
        f"- **{D}:** [x](docs/product/intents/outcome-a.md)", [(D, "discovery-untyped")]),
    "d-escaping-link": (
        f"- **{D}:** [r](../../../../product/intents/x.md)", [(D, "discovery-untyped")]),
    "d-normalized-link": (
        f"- **{D}:** [x](../../product/./intents/outcome-a.md)", [(D, "discovery-untyped")]),
    "d-bare-live": (f"- **{D}:** svc-reliability", [(D, "discovery-untyped")]),
    "d-repeated-second-bad": (
        f"- **{D}:** intent:plain-one\n- **{D}:** plain-one", [(D, "discovery-untyped")]),
}


@pytest.fixture(scope="module")
def discovery_results(
    template: Path, tmp_path_factory: pytest.TempPathFactory
) -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    for label, wanted in (("pass", True), ("fail", False)):
        dest = tmp_path_factory.mktemp(f"discovery-{label}") / "repo"
        shutil.copytree(template, dest, symlinks=True)
        for name, (preamble, expected) in DISCOVERY_CASES.items():
            if (not expected) == wanted:
                write(dest, f"docs/specs/{name}/spec.md", doc(preamble))
        buf, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            code = lint.main(["--root", str(dest), "--base-ref", "base"])
        results[label] = {"code": code, "out": buf.getvalue(), "err": err.getvalue()}
    return results


def test_discovery_passing_cases_exit_zero(
    discovery_results: dict[str, dict[str, object]]
) -> None:
    res = discovery_results["pass"]
    assert res["code"] == 0
    assert res["err"] == ""
    assert "0 violation(s)" in str(res["out"])


def test_discovery_failing_cases_exit_one(
    discovery_results: dict[str, dict[str, object]]
) -> None:
    assert discovery_results["fail"]["code"] == 1


@pytest.mark.parametrize("name", [n for n, (_, e) in DISCOVERY_CASES.items() if e])
def test_discovery_diagnostic(
    name: str, discovery_results: dict[str, dict[str, object]]
) -> None:
    found = parse(str(discovery_results["fail"]["out"]))
    assert sorted(found[f"docs/specs/{name}/spec.md"]) == sorted(DISCOVERY_CASES[name][1])


def test_discovery_untouched_legacy_spec_produces_nothing(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write(repo, "docs/specs/legacy/spec.md", doc(f"- **{D}:** docs/product/intents/outcome-a.md"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "legacy")
    git(repo, "tag", "-f", "base")
    write(repo, "docs/specs/other/spec.md", doc(f"- **{D}:** outcome:svc-reliability"))
    code, out, _ = run(repo, capsys)
    assert code == 0
    assert "0 violation(s) in 1 selected" in out


def test_discovery_body_only_edit_still_checks_preamble(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    legacy = doc(f"- **{D}:** docs/product/intents/outcome-a.md")
    write(repo, "docs/specs/legacy/spec.md", legacy)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "legacy")
    git(repo, "tag", "-f", "base")
    write(repo, "docs/specs/legacy/spec.md", legacy.replace("text", "edited text"))
    code, out, _ = run(repo, capsys)
    assert code == 1
    assert parse(out) == {"docs/specs/legacy/spec.md": [(D, "discovery-untyped")]}


def test_discovery_does_not_apply_to_intents_or_briefs(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    legacy = f"- **{D}:** docs/product/intents/outcome-a.md"
    write(repo, "docs/product/intents/new.md", doc(f"- **Slug:** n1\n{legacy}"))
    write(repo, "docs/product/briefs/new.md", doc(f"- **Slug:** nb\n{legacy}"))
    code, out, _ = run(repo, capsys)
    assert code == 0
    assert "0 violation(s) in 2 selected" in out


# ---------------------------------------------------------------------------
# VI-2002: the real CLI on the Discovery field
# ---------------------------------------------------------------------------


def _cli(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--root", str(repo), "--base-ref", "base"],
        capture_output=True, text=True, env=_GIT_ENV, check=False,
    )


def test_discovery_cli_valid_fixture_exits_zero_and_changes_nothing(repo: Path) -> None:
    write(repo, "docs/specs/ok/spec.md", doc(f"- **{D}:** outcome:svc-reliability"))
    before = _snapshot(repo)
    proc = _cli(repo)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines()[-1] == (
        "lint-graph-pointers: 0 violation(s) in 1 selected artifact(s)")
    assert proc.stderr == ""
    assert _snapshot(repo) == before


def test_discovery_cli_invalid_fixture_names_code_without_value(repo: Path) -> None:
    raw = "docs/product/intents/outcome-a.md"
    write(repo, "docs/specs/bad/spec.md", doc(f"- **{D}:** {raw}"))
    before = _snapshot(repo)
    proc = _cli(repo)
    assert proc.returncode == 1
    assert proc.stdout.splitlines()[0] == "docs/specs/bad/spec.md: Discovery: discovery-untyped"
    assert "outcome-a" not in proc.stdout + proc.stderr
    assert _snapshot(repo) == before


@pytest.mark.parametrize("unit", ["[", "[](", "[](<"])
def test_discovery_link_scan_is_linear_on_hostile_values(unit: str) -> None:
    import time

    value = unit * (1_000_000 // len(unit))
    started = time.monotonic()
    lint._check_discovery(value, lint._Index(), "docs/specs/x")
    assert time.monotonic() - started < 2.0


def test_intent_kinds_match_the_resolver_kinds() -> None:
    path = _SCRIPT.parent / "intent_delivery_relations.py"
    name = "core_work_loop_intent_delivery_relations_kinds"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = prev
    assert set(lint._INTENT_KINDS) == set(mod._PARENT_INTENT_KINDS)
