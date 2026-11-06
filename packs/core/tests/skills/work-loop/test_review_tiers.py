"""The review-tier classifier over real Git repositories (review-obligation-policy T3).

AC-0002: each ``full`` predicate. AC-0003, AC-0004: the ``wording-only`` path and
line rules. AC-0006: ``rebase`` by verbatim patch id. AC-0008: the ``minor-fix``
line limit, measured from the anchor result. AC-0011: a changed selection.
AC-0012 (forcing half): ``review_tier: full``.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_HELPER = Path(__file__).resolve().parent / "supervisor_harness.py"


def _harness() -> ModuleType:
    alias = "core_work_loop_supervisor_harness"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER)
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


h = _harness()
tiers = h.cli._supervisor("_review_tiers.py")
commit_mod = h.cli._supervisor("_supervisor_commit.py")
RULES: dict[str, Any] = h.cli._supervisor("_supervisor_review.py").load_rules()
PROSE = "docs/guide.md"
CODE = "src/app.py"


@dataclass
class Repo:
    """A throwaway repository with a commit helper and a supervisor Git port."""

    root: Path
    port: Any = None
    base: str = ""
    history: list[str] = field(default_factory=list)

    def git(self, *args: str, stdin: bytes | None = None) -> str:
        done = subprocess.run(
            ["git", "-C", str(self.root), *args],
            input=stdin,
            capture_output=True,
            check=True,
            env={**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"},
        )
        return done.stdout.decode().strip()

    def write(self, files: dict[str, str | bytes | None]) -> str:
        """Write *files* (None deletes), commit, and return the commit id."""
        for name, body in files.items():
            path = self.root / name
            if body is None:
                path.unlink()
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(body, bytes):
                path.write_bytes(body)
            else:
                path.write_text(body, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", "step")
        sha = self.git("rev-parse", "HEAD")
        self.history.append(sha)
        return sha

    def symlink(self, name: str, target: str) -> str:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_symlink() or path.exists():
            path.unlink()
        path.symlink_to(target)
        return self.write({})


@pytest.fixture
def repo(tmp_path: Path) -> Iterator[Repo]:
    root = tmp_path / "repo"
    root.mkdir()
    made = Repo(root)
    made.git("init", "-q", "-b", "main")
    made.git("config", "user.email", "tests@example.invalid")
    made.git("config", "user.name", "tests")
    made.git("config", "core.symlinks", "true")
    made.base = made.write(
        {PROSE: "# Guide\n\nThe tool reads the file once.\n", CODE: "x = 1\n", "README.md": "x\n"}
    )
    made.port = commit_mod.GitPort(root, "docs/specs/calc", clock=lambda: "2026-11-05T00:00:00Z")
    yield made


def _anchor(repo: Repo, result: str, changed: set[str], with_ids: bool = True) -> Any:
    ids = (
        {p: repo.port.patch_id(repo.base, result, p) for p in sorted(changed)} if with_ids else None
    )
    return tiers.AnchorFacts(result, repo.base, frozenset(changed), ids)


def _classify(repo: Repo, anchor: Any, current: str, changed: set[str], **over: Any) -> Any:
    args: dict[str, Any] = {
        "current": current,
        "changed": changed,
        "run_base": repo.base,
        "open_findings": False,
        "adopted_reanchor": False,
        "spec_dir_changed": False,
        "selection_changed": False,
        "review_tier": None,
    }
    args.update(over)
    return tiers.classify(repo.port, RULES, anchor, **args)


def _prose_change(repo: Repo, before: str, after: str, path: str = PROSE) -> tuple[Any, str]:
    anchor_sha = repo.write({path: before})
    anchor = _anchor(repo, anchor_sha, {path})
    return anchor, repo.write({path: after})


# ── AC-0002: full predicates ────────────────────────────────────────────────


def test_ac0002_no_anchor_facts_is_full(repo: Repo) -> None:
    current = repo.write({CODE: "x = 2\n"})
    assert _classify(repo, None, current, {CODE}).name == "full"


def test_ac0002_an_added_path_is_full(repo: Repo) -> None:
    anchor_sha = repo.write({CODE: "x = 2\n"})
    current = repo.write({"docs/new.md": "New text.\n"})
    tier = _classify(repo, _anchor(repo, anchor_sha, {CODE}), current, {CODE, "docs/new.md"})
    assert tier.name == "full"


def test_ac0002_a_deleted_run_added_file_is_full(repo: Repo) -> None:
    anchor_sha = repo.write({"docs/added.md": "Added.\n"})
    current = repo.write({"docs/added.md": None})
    anchor = _anchor(repo, anchor_sha, {"docs/added.md"})
    assert _classify(repo, anchor, current, {"docs/added.md"}).name == "full"


def test_ac0002_a_mode_change_is_full(repo: Repo) -> None:
    anchor_sha = repo.write({CODE: "x = 2\n"})
    (repo.root / CODE).chmod(0o755)
    current = repo.write({})
    tier = _classify(repo, _anchor(repo, anchor_sha, {CODE}), current, {CODE}, open_findings=True)
    assert tier.name == "full"


def test_ac0002_a_retargeted_symlink_is_full(repo: Repo) -> None:
    repo.write({"docs/a.md": "A.\n", "docs/b.md": "B.\n"})
    anchor_sha = repo.symlink("docs/link.md", "a.md")
    current = repo.symlink("docs/link.md", "b.md")
    anchor = _anchor(repo, anchor_sha, {"docs/link.md"})
    assert _classify(repo, anchor, current, {"docs/link.md"}).name == "full"


def test_ac0002_a_submodule_bump_is_full(repo: Repo) -> None:
    def gitlink(sha: str) -> str:
        repo.git("update-index", "--add", "--cacheinfo", f"160000,{sha},vendor/lib")
        repo.git("commit", "-q", "-m", "bump")
        return repo.git("rev-parse", "HEAD")

    anchor_sha = gitlink(repo.base)
    other = repo.write({CODE: "x = 3\n"})
    current = gitlink(other)
    anchor = _anchor(repo, anchor_sha, {"vendor/lib"}, with_ids=False)
    assert _classify(repo, anchor, current, {"vendor/lib"}, open_findings=True).name == "full"


def test_ac0002_an_attribute_cannot_make_a_nul_blob_text(repo: Repo) -> None:
    anchor_sha = repo.write({".gitattributes": "*.md diff\n", PROSE: b"Plain.\x00a\n"})
    current = repo.write({PROSE: b"Plain.\x00b\n"})
    anchor = _anchor(repo, anchor_sha, {PROSE})
    assert _classify(repo, anchor, current, {PROSE}).name == "full"


def test_ac0002_a_non_utf8_blob_is_full(repo: Repo) -> None:
    anchor, current = _prose_change(repo, "Café.\n", "x")
    repo.write({PROSE: b"Caf\xe9.\n"})
    current = repo.history[-1]
    assert _classify(repo, anchor, current, {PROSE}).name == "full"


def test_ac0002_an_oversized_blob_is_full(repo: Repo) -> None:
    big = "word " * (tiers.READ_LIMIT // 5 + 10) + "\n"
    anchor, current = _prose_change(repo, "Short.\n", big)
    assert _classify(repo, anchor, current, {PROSE}).name == "full"


def test_ac0002_a_missing_anchor_commit_is_full(repo: Repo) -> None:
    current = repo.write({PROSE: "Changed prose.\n"})
    anchor = tiers.AnchorFacts("0" * 40, repo.base, frozenset({PROSE}), None)
    assert _classify(repo, anchor, current, {PROSE}).name == "full"


def test_ac0002_a_classifier_error_is_full(repo: Repo) -> None:
    class Broken:
        def __getattr__(self, name: str) -> Any:
            raise RuntimeError("boom")

    anchor, current = _prose_change(repo, "One.\n", "Two.\n")
    tier = tiers.classify(
        Broken(), RULES, anchor, current=current, changed={PROSE}, run_base=repo.base,
        open_findings=False, adopted_reanchor=False, spec_dir_changed=False,
        selection_changed=False, review_tier=None,
    )
    assert tier.name == "full"


def test_a_path_reverted_to_base_is_a_delta_path(repo: Repo) -> None:
    anchor_sha = repo.write({CODE: "x = 1\ny = 2\n"})
    current = repo.write({CODE: "x = 1\n"})
    tier = _classify(repo, _anchor(repo, anchor_sha, {CODE}), current, {CODE}, open_findings=True)
    assert tier.name == "minor-fix" and "1 changed lines" in tier.reason


# ── AC-0003, AC-0004: wording-only ──────────────────────────────────────────


def test_ac0003_a_plain_prose_edit_is_wording_only(repo: Repo) -> None:
    anchor, current = _prose_change(
        repo, "# Guide\n\nThe tool reads the file once.\n", "# Guide\n\nThe tool reads each file once.\n"
    )
    assert _classify(repo, anchor, current, {PROSE}).name == "wording-only"


def test_ac0003_an_open_finding_blocks_wording_only(repo: Repo) -> None:
    anchor, current = _prose_change(repo, "Reads once.\n", "Reads each file once.\n")
    assert _classify(repo, anchor, current, {PROSE}, open_findings=True).name == "minor-fix"


@pytest.mark.parametrize(
    "path",
    [
        "src/notes.md",
        "docs/specs/feature/spec.md",
        "docs/adr/0001-x.md",
        "docs/guides/agents.md",
        "docs/guides/AGENTS.local.md",
        "docs/guides/SKILL.md",
    ],
)
def test_ac0003_a_path_off_the_allowlist_or_instruction_named_is_not_wording_only(
    repo: Repo, path: str
) -> None:
    anchor, current = _prose_change(repo, "Plain words here.\n", "Plain wording here.\n", path)
    assert _classify(repo, anchor, current, {path}).name == "full"


def test_ac0003_an_inline_reference_makes_the_file_instruction_reached(repo: Repo) -> None:
    repo.write({"CLAUDE.md": "Read the house rules. See @docs/guide.md for more.\n"})
    anchor, current = _prose_change(repo, "Plain words here.\n", "Plain wording here.\n")
    assert _classify(repo, anchor, current, {PROSE}).name == "full"


def test_ac0003_a_two_hop_reference_is_instruction_reached(repo: Repo) -> None:
    repo.write({"AGENTS.md": "@docs/index.md\n", "docs/index.md": "Also @guide.md\n"})
    anchor, current = _prose_change(repo, "Plain words here.\n", "Plain wording here.\n")
    assert _classify(repo, anchor, current, {PROSE}).name == "full"


def test_ac0003_an_escaping_reference_is_full(repo: Repo) -> None:
    repo.write({"AGENTS.md": "Rules live in @../outside.md\n"})
    anchor, current = _prose_change(repo, "Plain words here.\n", "Plain wording here.\n")
    assert _classify(repo, anchor, current, {PROSE}).name == "full"


def test_ac0003_a_reference_through_a_symlinked_directory_is_full(repo: Repo) -> None:
    repo.symlink("linked", "docs")
    repo.write({"AGENTS.md": "See @linked/other.md\n"})
    anchor, current = _prose_change(repo, "Plain words here.\n", "Plain wording here.\n")
    assert _classify(repo, anchor, current, {PROSE}).name == "full"


def test_ac0003_a_six_hop_chain_is_full(repo: Repo) -> None:
    chain = {"AGENTS.md": "@docs/h1.md\n"}
    for hop in range(1, 7):
        chain[f"docs/h{hop}.md"] = f"@h{hop + 1}.md\n"
    repo.write(chain)
    anchor, current = _prose_change(repo, "Plain words here.\n", "Plain wording here.\n")
    assert _classify(repo, anchor, current, {PROSE}).name == "full"


def test_ac0003_an_instruction_named_symlink_is_read_at_its_target(repo: Repo) -> None:
    repo.write({"docs/rules.md": "See @guide.md\n"})
    repo.symlink("CLAUDE.md", "docs/rules.md")
    anchor, current = _prose_change(repo, "Plain words here.\n", "Plain wording here.\n")
    assert _classify(repo, anchor, current, {PROSE}).name == "full"


def test_a_handle_or_email_is_not_a_reference(repo: Repo) -> None:
    repo.write({"AGENTS.md": "Ask @maintainers or mail team@example.invalid.\n"})
    anchor, current = _prose_change(repo, "Plain words here.\n", "Plain wording here.\n")
    assert _classify(repo, anchor, current, {PROSE}).name == "wording-only"


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("```\ncode a\n```\n", "```\ncode b\n```\n"),
        ("```\n" + "x\n" * 10 + "code a\n```\n", "```\n" + "x\n" * 10 + "code b\n```\n"),
        ("Text.\n\n    indented a\n", "Text.\n\n    indented b\n"),
        ("Use `a` here.\n", "Use `b` here.\n"),
        ("See [docs](a.md).\n", "See [docs](b.md).\n"),
        ("[ref]: https://a.example\n", "[ref]: https://b.example\n"),
        ("Visit <https://a.example>.\n", "Visit <https://b.example>.\n"),
        ("# Title a\n", "# Title b\n"),
        ("<!-- note a -->\n", "<!-- note b -->\n"),
        ("<div>a</div>\n", "<div>b</div>\n"),
        ("| a | b |\n", "| a | c |\n"),
        ("---\ntitle: a\n---\nBody.\n", "---\ntitle: b\n---\nBody.\n"),
        ("Plain line.\nNext.\n", "Plain line.\n```\nNext.\n"),
        # A pipe table with no leading pipe is still a table.
        ("a | b\n--- | ---\n1 | 2\n", "a | b\n--- | ---\n1 | 3\n"),
        ("Intro.\n\nname | role\n-----|-----\nann | dev\n", "Intro.\n\nname | role\n-----|-----\nann | ops\n"),
        # A setext heading and its underline are both markup.
        ("Title a\n=======\n", "Title b\n=======\n"),
        ("Title a\n-------\n", "Title b\n-------\n"),
        ("Intro text.\n\nSection a\nmore\n---\n", "Intro text.\n\nSection b\nmore\n---\n"),
        ("Text.\n\n---\n\nAfter.\n", "Text.\n\n- - -\n\nAfter.\n"),
        # Code after a shorter inner fence stays inside the longer fence.
        ("````\n```\ncode a\n````\n", "````\n```\ncode b\n````\n"),
        ("~~~~\n~~~\ncode a\n~~~~\n", "~~~~\n~~~\ncode b\n~~~~\n"),
        # A fence of the other character does not close it.
        ("~~~\n```\ncode a\n~~~\n", "~~~\n```\ncode b\n~~~\n"),
    ],
)
def test_ac0004_a_changed_line_outside_plain_prose_is_not_wording_only(
    repo: Repo, before: str, after: str
) -> None:
    anchor, current = _prose_change(repo, before, after)
    assert _classify(repo, anchor, current, {PROSE}).name == "full"


def test_ac0004_the_scan_marks_the_constructs_the_fixtures_edit() -> None:
    assert tiers.scan_markdown("a | b\n--- | ---\n1 | 2") == ["markup"] * 3
    assert tiers.scan_markdown("Title\nsecond line\n=====\nBody.") == [
        "markup", "markup", "markup", "prose",
    ]
    assert tiers.scan_markdown("````\n```\ncode\n```\n````\nAfter.") == [
        "fence", "fence", "fence", "fence", "fence", "prose",
    ]
    assert tiers.scan_markdown("````\ncode\n```\nStill code.\n`````\nProse.") == [
        "fence", "fence", "fence", "fence", "fence", "prose",
    ]
    assert tiers.scan_markdown("Escaped \\| pipe is plain.") == ["prose"]


# ── AC-0006: rebase ─────────────────────────────────────────────────────────


def _rebased(repo: Repo, change: str, upstream: dict[str, str]) -> tuple[Any, str, str]:
    """An anchor on the base, then the same change replayed on an upstream commit."""
    anchor_sha = repo.write({CODE: change})
    anchor = _anchor(repo, anchor_sha, {CODE})
    repo.git("checkout", "-q", repo.base)
    new_base = repo.write(upstream)
    current = repo.write({CODE: change})
    return anchor, new_base, current


def test_ac0006_an_unchanged_patch_after_a_reanchor_is_rebase(repo: Repo) -> None:
    repo.write({CODE: "\n".join(f"line{i}" for i in range(30)) + "\n"})
    repo.base = repo.history[-1]
    lines = [f"line{i}" for i in range(30)]
    changed = lines.copy()
    changed[2] = "LINE2"
    anchor, new_base, current = _rebased(
        repo, "\n".join(changed) + "\n", {"other.txt": "upstream\n"}
    )
    tier = _classify(repo, anchor, current, {CODE}, run_base=new_base, adopted_reanchor=True)
    assert tier.name == "rebase"


def test_ac0006_a_reindent_is_not_rebase(repo: Repo) -> None:
    anchor_sha = repo.write({CODE: "def f():\n    return 2\n"})
    anchor = _anchor(repo, anchor_sha, {CODE})
    repo.git("checkout", "-q", repo.base)
    new_base = repo.write({"other.txt": "upstream\n"})
    current = repo.write({CODE: "def f():\n  return 2\n"})
    tier = _classify(repo, anchor, current, {CODE}, run_base=new_base, adopted_reanchor=True)
    assert tier.name != "rebase"


def test_ac0006_an_old_git_never_classifies_rebase(repo: Repo, monkeypatch: pytest.MonkeyPatch) -> None:
    anchor, new_base, current = _rebased(repo, "x = 2\n", {"other.txt": "upstream\n"})
    monkeypatch.setattr(repo.port, "git_version", lambda: (2, 38))
    tier = _classify(repo, anchor, current, {CODE}, run_base=new_base, adopted_reanchor=True)
    assert tier.name != "rebase"


def test_ac0006_an_open_finding_or_spec_change_blocks_rebase(repo: Repo) -> None:
    anchor, new_base, current = _rebased(repo, "x = 2\n", {"other.txt": "upstream\n"})
    common = {"run_base": new_base, "adopted_reanchor": True}
    assert _classify(repo, anchor, current, {CODE}, open_findings=True, **common).name != "rebase"
    assert _classify(repo, anchor, current, {CODE}, spec_dir_changed=True, **common).name != "rebase"


@pytest.mark.parametrize(
    "condition",
    [
        "old-git",
        "no-patch-ids",
        "no-run-base",
        "changed-paths-differ",
        "spec-dir-changed",
        "open-finding",
        "patch-changed",
    ],
)
def test_ac0006_an_adopted_reanchor_that_fails_a_rebase_condition_is_full(
    repo: Repo, monkeypatch: pytest.MonkeyPatch, condition: str
) -> None:
    """The delta path union is byte-identical after a reanchor, so only ``full`` is safe."""
    anchor, new_base, current = _rebased(repo, "x = 2\n", {"other.txt": "upstream\n"})
    args: dict[str, Any] = {"run_base": new_base, "adopted_reanchor": True}
    changed = {CODE}
    if condition == "old-git":
        monkeypatch.setattr(repo.port, "git_version", lambda: (2, 38))
        why = "older than 2.39"
    elif condition == "no-patch-ids":
        anchor = tiers.AnchorFacts(anchor.anchor_result, anchor.run_base, anchor.changed_paths, None)
        why = "no patch ids"
    elif condition == "no-run-base":
        args["run_base"] = None
        why = "run base is undefined"
    elif condition == "changed-paths-differ":
        changed = {CODE, "other.txt"}
        why = "changed paths differ"
    elif condition == "spec-dir-changed":
        args["spec_dir_changed"] = True
        why = "spec directory"
    elif condition == "open-finding":
        args["open_findings"] = True
        why = "finding is open"
    else:
        repo.write({CODE: "x = 3\n"})
        current = repo.history[-1]
        why = f"patch for {CODE} changed"
    tier = _classify(repo, anchor, current, changed, **args)
    assert tier.name == "full"
    assert "adopted reanchor" in tier.reason and why in tier.reason, tier.reason


def test_ac0006_a_wording_only_edit_after_a_refused_reanchor_is_full(repo: Repo) -> None:
    """The wording-only path would otherwise pass vacuously over an identical path union."""
    anchor, current = _prose_change(repo, "Plain words here.\n", "Plain wording here.\n")
    assert _classify(repo, anchor, current, {PROSE}).name == "wording-only"
    refused = _classify(repo, anchor, current, {PROSE}, adopted_reanchor=True, run_base=None)
    assert refused.name == "full" and "run base is undefined" in refused.reason


# ── AC-0002: every Git read is bounded ──────────────────────────────────────


def _spy(repo: Repo) -> list[tuple[tuple[str, ...], int, int | None]]:
    """Record each hardened Git call as ``(args, stdout size, limit)``."""
    seen: list[tuple[tuple[str, ...], int, int | None]] = []
    real = repo.port.hardened.run

    def run(*args: str, **kwargs: Any) -> bytes:
        out: bytes = real(*args, **kwargs)
        seen.append((args, len(out), kwargs.get("limit")))
        return out

    repo.port.hardened.run = run
    return seen


def test_ac0002_the_tree_is_read_only_for_the_paths_and_instruction_names_it_needs(
    repo: Repo,
) -> None:
    """A repository whose whole listing passes the read limit still classifies, in small reads."""
    bulk = {f"bulk/{'n' * 120}{i:05d}.txt": "x\n" for i in range(7000)}
    repo.write({"AGENTS.md": "House rules. See @docs/other.md.\n", "docs/other.md": "Other.\n", **bulk})
    anchor, current = _prose_change(repo, "Plain words here.\n", "Plain wording here.\n")
    listing = repo.git("ls-tree", "-r", "--full-tree", current)
    assert len(listing.encode()) > tiers.READ_LIMIT
    seen = _spy(repo)
    tier = _classify(repo, anchor, current, {PROSE})
    assert tier.name == "wording-only", tier.reason
    reads = [call for call in seen if call[0][0] in ("ls-tree", "diff-tree", "diff", "rev-list")]
    assert reads
    assert all(limit == tiers.READ_LIMIT for _, _, limit in reads)
    assert not any("-r" in args for args, _, _ in seen if args[0] == "ls-tree")
    assert max(size for _, size, _ in seen) < tiers.READ_LIMIT // 4


def test_ac0002_an_oversized_tree_read_is_full_with_the_git_code(
    repo: Repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    anchor_sha = repo.write({CODE: "x = 2\n"})
    current = repo.write({CODE: "x = 3\n"})
    anchor = _anchor(repo, anchor_sha, {CODE})
    monkeypatch.setattr(commit_mod, "_READ_LIMIT", 20)
    tier = _classify(repo, anchor, current, {CODE}, open_findings=True)
    assert tier.name == "full" and "denied-git-output-too-large" in tier.reason, tier.reason


def test_ac0002_an_oversized_rev_list_read_is_refused_by_code(repo: Repo) -> None:
    for number in range(6):
        repo.write({CODE: f"x = {number}\n"})
    with pytest.raises(commit_mod.SupervisorGitError) as refused:
        repo.port.rev_list(repo.base, repo.history[-1], limit=100)
    assert refused.value.code == "denied-git-output-too-large"
    assert len(repo.port.rev_list(repo.base, repo.history[-1], limit=tiers.READ_LIMIT)) == 6


# ── AC-0002, AC-0008: the line comparison is bounded ────────────────────────


def test_ac0008_a_file_past_the_line_limit_is_full_and_never_compared(repo: Repo) -> None:
    long = "same line\n" * (tiers.MAX_DIFF_LINES + 5)
    anchor, current = _prose_change(repo, long, long + "one more\n")
    tier = _classify(repo, anchor, current, {PROSE})
    assert tier.name == "full" and "too long to compare" in tier.reason, tier.reason


def test_ac0008_a_large_repetitive_file_under_the_limit_finishes_quickly(repo: Repo) -> None:
    count = tiers.MAX_DIFF_LINES - 5
    old = "".join("same line\n" for _ in range(count))
    new = old[: -len("same line\n")] + "last line differs\n"
    anchor_sha = repo.write({CODE: old})
    current = repo.write({CODE: new})
    anchor = _anchor(repo, anchor_sha, {CODE})
    started = time.monotonic()
    tier = _classify(repo, anchor, current, {CODE}, open_findings=True)
    assert time.monotonic() - started < 20
    assert tier.name == "minor-fix"


def test_ac0008_the_changed_line_count_stops_once_it_passes_the_ceiling() -> None:
    old = "".join(f"common{i}\nold{i}\n" for i in range(500))
    new = "".join(f"common{i}\nnew{i}\n" for i in range(500))
    assert tiers._changed_line_count(old, new, 10) == 12  # six two-line hunks, then it stops
    assert tiers._changed_line_count("a\nb\n", "a\nc\n", 10) == 2


# ── AC-0003: references reach every entry they could name ───────────────────


@pytest.mark.parametrize(
    "reference",
    [
        "@docs/GUIDE.md",
        "@Docs/Guide.MD",
        "@docs/guide.md#install",
        "**@docs/guide.md**",
        "_@docs/guide.md_",
        "@docs/guide.md*",
        "@docs/guide.md).",
        "@./docs/guide.md",
        "@docs/../docs/guide.md",
    ],
    ids=lambda text: text,
)
def test_ac0003_a_reference_that_could_name_the_file_under_folding_or_markup_reaches_it(
    repo: Repo, reference: str
) -> None:
    repo.write({"AGENTS.md": f"Start with {reference} before coding.\n"})
    anchor, current = _prose_change(repo, "Plain words here.\n", "Plain wording here.\n")
    tier = _classify(repo, anchor, current, {PROSE})
    assert tier.name == "full", reference


def test_ac0003_a_non_ascii_reference_could_name_any_normalisation_and_is_full(
    repo: Repo,
) -> None:
    repo.write({"AGENTS.md": "Start with @docs/guide\u00e9.md before coding.\n"})
    anchor, current = _prose_change(repo, "Plain words here.\n", "Plain wording here.\n")
    tier = _classify(repo, anchor, current, {PROSE})
    assert tier.name == "full" and "non-ASCII" in tier.reason


def test_ac0003_a_reference_to_some_other_file_leaves_the_prose_edit_wording_only(
    repo: Repo,
) -> None:
    repo.write({"AGENTS.md": "Start with @docs/elsewhere.md and **@docs/other.md**.\n"})
    anchor, current = _prose_change(repo, "Plain words here.\n", "Plain wording here.\n")
    assert _classify(repo, anchor, current, {PROSE}).name == "wording-only"


def test_ac0003_a_reference_that_resolves_to_a_symlink_is_full(repo: Repo) -> None:
    repo.write({"docs/other.md": "Other.\n"})
    repo.symlink("docs/link.md", "other.md")
    repo.write({"AGENTS.md": "Start with @docs/link.md before coding.\n"})
    anchor, current = _prose_change(repo, "Plain words here.\n", "Plain wording here.\n")
    tier = _classify(repo, anchor, current, {PROSE})
    assert tier.name == "full" and "symlink" in tier.reason, tier.reason


# ── AC-0008: minor-fix ──────────────────────────────────────────────────────


def _lines(count: int, tag: str) -> str:
    return "".join(f"{tag}{i} = {i}\n" for i in range(count))


def test_ac0008_forty_lines_from_the_anchor_is_minor_fix(repo: Repo) -> None:
    anchor_sha = repo.write({CODE: _lines(20, "a")})
    current = repo.write({CODE: _lines(20, "b")})
    tier = _classify(repo, _anchor(repo, anchor_sha, {CODE}), current, {CODE}, open_findings=True)
    assert tier.name == "minor-fix"


def test_ac0008_forty_one_lines_over_two_repairs_is_full(repo: Repo) -> None:
    anchor_sha = repo.write({CODE: _lines(20, "a")})
    anchor = _anchor(repo, anchor_sha, {CODE})
    repo.write({CODE: _lines(10, "b") + _lines(20, "a")[len(_lines(10, "a")):]})
    current = repo.write({CODE: _lines(20, "b") + "extra = 1\n"})
    assert _classify(repo, anchor, current, {CODE}, open_findings=True).name == "full"


def test_ac0008_a_path_outside_the_anchor_set_is_full(repo: Repo) -> None:
    anchor_sha = repo.write({CODE: "x = 2\n"})
    current = repo.write({"README.md": "y\n"})
    tier = _classify(
        repo, _anchor(repo, anchor_sha, {CODE}), current, {CODE, "README.md"}, open_findings=True
    )
    assert tier.name == "full"


# ── AC-0011, AC-0012 ────────────────────────────────────────────────────────


def test_ac0011_a_changed_selection_is_full(repo: Repo) -> None:
    anchor, current = _prose_change(repo, "One.\n", "Two.\n")
    assert _classify(repo, anchor, current, {PROSE}, selection_changed=True).name == "full"


def test_ac0012_review_tier_full_overrides_a_lower_tier(repo: Repo) -> None:
    anchor_sha = repo.write({CODE: "x = 2\n"})
    current = repo.write({CODE: "x = 3\n"})
    anchor = _anchor(repo, anchor_sha, {CODE})
    assert _classify(repo, anchor, current, {CODE}, open_findings=True).name == "minor-fix"
    forced = _classify(repo, anchor, current, {CODE}, open_findings=True, review_tier="full")
    assert forced.name == "full"


def test_glob_match_keeps_star_within_a_segment() -> None:
    assert tiers.glob_match("docs/*.md", "docs/a.md")
    assert not tiers.glob_match("docs/*.md", "docs/specs/a.md")
    assert tiers.glob_match("docs/guides/**/*.md", "docs/guides/x/a.md")


# ── round-2 review repairs (T9) ─────────────────────────────────────────────


@pytest.mark.parametrize("indent", ["    ", "     ", "\t"])
def test_ac0004_an_indented_line_never_closes_a_fence(repo: Repo, indent: str) -> None:
    """AC-0004: a fence line indented four or more columns stays inside the code block."""
    before = f"Intro.\n\n```markdown\nExample:\n{indent}```\nrun the old command\n```\n\nEnd.\n"
    after = before.replace("old command", "new command")
    kinds = tiers.scan_markdown(before)
    assert kinds[5] == "fence", kinds
    anchor, current = _prose_change(repo, before, after)
    assert _classify(repo, anchor, current, {PROSE}).name == "full"


def test_ac0004_a_closing_fence_indented_up_to_three_spaces_still_closes() -> None:
    """AC-0004: CommonMark lets a closing fence carry up to three spaces of indent."""
    kinds = tiers.scan_markdown("```\ncode\n   ```\nAfter the block.\n")
    assert kinds == ["fence", "fence", "fence", "prose", "blank"]


def test_ac0008_the_line_matcher_bounds_its_cost_with_autojunk() -> None:
    """AC-0008: the matcher drops over-repeated lines, so a hostile file cannot go quadratic.

    Reverting to ``autojunk=False`` turns this red: the popular-line set stays empty.
    """
    text = "same line\n" * 400
    matcher = tiers._line_matcher(text, text + "tail\n")
    assert matcher.autojunk is True
    assert "same line" in matcher.bpopular


# ── T10: any fence-looking line keeps a file out of wording-only ────────────


@pytest.mark.parametrize(
    "before",
    [
        "Intro.\n\n```\nExample:\n ```\nrun the old command\n```\n\nEnd.\n",
        "Intro.\n\n```\nExample:\n\x0c```\nrun the old command\n```\n\nEnd.\n",
        "Intro.\n\n```\nExample:\n\x0b```\nrun the old command\n```\n\nEnd.\n",
        "Intro.\n\n```\nExample:\n ```\nrun the old command\n```\n\nEnd.\n",
        "Intro\n    ```\nmore intro\n```\nrun the old command\n```\n",
        "Intro\n    ```\nmore intro\n```\nrun the old command\n```\n",
    ],
    ids=["nbsp-close", "formfeed-close", "vtab-close", "emspace-close", "4sp-open", "nbsp-open"],
)
def test_ac0004_a_file_with_a_fence_like_line_is_never_wording_only(repo: Repo, before: str) -> None:
    """AC-0004: the six reproduced inputs classify full, whatever the fence whitespace."""
    after = before.replace("old command", "new command")
    assert not tiers._wording_only_file(before, after)
    anchor, current = _prose_change(repo, before, after)
    assert _classify(repo, anchor, current, {PROSE}).name == "full"


def test_ac0004_a_prose_edit_without_fences_stays_wording_only(repo: Repo) -> None:
    """AC-0004: the fence rule leaves an ordinary prose edit wording-only."""
    anchor, current = _prose_change(repo, "Intro text here.\n\nMore words.\n", "Intro text there.\n\nMore words.\n")
    assert _classify(repo, anchor, current, {PROSE}).name == "wording-only"
