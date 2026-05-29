"""Unit tests for the wave-scheduled-supervisor scheduler in loop-cohort.py.

Covers spec `docs/specs/wave-scheduled-supervisor/`:
  T1 — parse_depends_on + parse_plan (AC6)
  T2 — topological order, cycle + forward-ref detection (AC1/AC2/AC3)
  T4 — dispatch_decision gate (AC5)

loop-cohort.py is a standalone hyphenated script; pure functions are loaded
via importlib here. CLI/exit-code behavior (the `schedule` verb) is exercised
by subprocess against the real file-path invocation elsewhere.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
LC_PATH = REPO_ROOT / "packs/core/.apm/skills/work-loop/scripts/loop-cohort.py"


def _load():
    spec = importlib.util.spec_from_file_location("loop_cohort_under_test", LC_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lc = _load()

LOCAL = {f"T{i}" for i in range(1, 16)} | {"T1a", "T1b", "T1c"}


# ── T1: parse_depends_on (AC6) ──────────────────────────────────────────────

def test_parse_depends_on_none():
    assert lc.parse_depends_on("none", LOCAL) == (set(), [])


def test_parse_depends_on_strips_parenthetical_prose():
    # the prose names T13/T14 but they sit after "(" — only T11 is a real dep
    local, cross = lc.parse_depends_on(
        "T11 (must land after T11; not parallelizable with T13/T14)", LOCAL
    )
    assert local == {"T11"}
    assert cross == []


def test_parse_depends_on_letter_suffix_and_range():
    local, _ = lc.parse_depends_on("T1a, T1-T6", LOCAL)
    assert local == {"T1a", "T1", "T2", "T3", "T4", "T5", "T6"}


def test_parse_depends_on_cross_spec_marker_excluded():
    local, cross = lc.parse_depends_on("T2, spec:distribution-adapters/T7", LOCAL)
    assert local == {"T2"}                       # local T2 only
    assert ("distribution-adapters", "T7") in cross   # the cross-spec dep
    assert "T7" not in local                     # marker T7 is NOT a local edge


def test_parse_depends_on_legacy_backtick_cross_spec_no_collision():
    # self-hosting regression: `distribution-adapters` T7 must NOT collide with
    # self-hosting's own local T7.
    local, cross = lc.parse_depends_on("T2, `distribution-adapters` T7", LOCAL)
    assert "T7" not in local
    assert ("distribution-adapters", "T7") in cross


def test_parse_depends_on_backtick_local_id_not_dropped():
    # a backtick-quoted *local* task id adjacent to another id must NOT be
    # mis-read as a cross-spec dep and silently dropped (the silent-drop class
    # this spec exists to kill). `T1` T2 → both local, no cross-spec.
    local, cross = lc.parse_depends_on("`T1` T2", LOCAL)
    assert local == {"T1", "T2"}
    assert cross == []


# ── T1: parse_plan preserves authored order ─────────────────────────────────

_PLAN = """\
### T1: first
**Depends on:** none
### T2: second
**Depends on:** T1
### T3: third
**Depends on:** T1, T2
"""


def test_parse_plan_preserves_authored_order():
    ordered, deps = lc.parse_plan(_PLAN)
    assert ordered == ["T1", "T2", "T3"]      # file order, not sorted
    assert deps["T2"] == {"T1"}
    assert deps["T3"] == {"T1", "T2"}


# ── T2: topological order (AC1) ─────────────────────────────────────────────

def test_topological_waves_layers():
    ordered, deps = lc.parse_plan(_PLAN)
    waves, placed = lc.topological_waves(ordered, deps)
    assert placed == 3
    assert waves == [["T1"], ["T2"], ["T3"]]


def test_topological_independent_first_wave():
    ordered, deps = lc.parse_plan(
        "### T1: a\n**Depends on:** none\n### T2: b\n**Depends on:** none\n"
        "### T3: c\n**Depends on:** T1, T2\n"
    )
    waves, placed = lc.topological_waves(ordered, deps)
    assert sorted(waves[0]) == ["T1", "T2"]    # both independent → first wave
    assert waves[1] == ["T3"]


# ── T2: cycle detection (AC2) ───────────────────────────────────────────────

def test_detect_cycle():
    ordered, deps = lc.parse_plan(
        "### T1: a\n**Depends on:** T2\n### T2: b\n**Depends on:** T1\n"
    )
    cyc = lc.detect_cycles(ordered, deps)
    assert set(cyc) == {"T1", "T2"}


def test_no_cycle_on_dag():
    ordered, deps = lc.parse_plan(_PLAN)
    assert lc.detect_cycles(ordered, deps) == []


# ── T2: forward-ref detection (AC3) — the two real cases, by shape ──────────

def test_detect_forward_ref_agent_spec_cli_shape():
    # agent-spec-cli T13 (zipapp build) declares Depends on: ... T15 (authored later)
    ordered, deps = lc.parse_plan(
        "### T13: zipapp build\n**Depends on:** T2, T15\n"
        "### T14: qa\n**Depends on:** T13\n"
        "### T15: integration test\n**Depends on:** T4\n"
    )
    fwd = lc.detect_forward_refs(ordered, deps)
    assert ("T13", "T15") in fwd


def test_detect_forward_ref_incompatible_hook_shape():
    # incompatible-hook-event-drop T2 declares Depends on: T1, T3, T4 (T3/T4 later)
    ordered, deps = lc.parse_plan(
        "### T1: refactor\n**Depends on:** none\n"
        "### T2: swallow\n**Depends on:** T1, T3, T4\n"
        "### T3: enumerator\n**Depends on:** none\n"
        "### T4: formatter\n**Depends on:** none\n"
    )
    fwd = lc.detect_forward_refs(ordered, deps)
    assert ("T2", "T3") in fwd and ("T2", "T4") in fwd


def test_no_forward_ref_on_clean_plan():
    ordered, deps = lc.parse_plan(_PLAN)
    assert lc.detect_forward_refs(ordered, deps) == []


# ── T4: dispatch_decision gate (AC5) ────────────────────────────────────────

def test_dispatch_allows_safe_category_and_disjoint():
    # allow-path: all-safe categories + disjoint → parallel
    assert lc.dispatch_decision(
        ["cannot-collide", "typed-group-b"], merge_tree_clean=True
    ) == "parallel"


def test_dispatch_serializes_textual_loud_overlap():
    # serialize-on-fail, half (a): a textual-loud wave that OVERLAPS (merge
    # conflict) → serial, even though the category is "safe".
    assert lc.dispatch_decision(
        ["textual-loud", "textual-loud"], merge_tree_clean=False
    ) == "serial"


def test_dispatch_serializes_non_safe_category():
    # serialize-on-fail, half (b): a non-safe category serializes even when
    # merge-tree is clean.
    assert lc.dispatch_decision(
        ["cannot-collide", "dangerous"], merge_tree_clean=True
    ) == "serial"


def test_dispatch_fails_closed():
    # both conditions fail → serial.
    assert lc.dispatch_decision(["shared-state"], merge_tree_clean=False) == "serial"


# ── T3: `schedule` verb (AC4) — real file-path invocation via subprocess ────

import subprocess  # noqa: E402
import sys  # noqa: E402


def _schedule(tmp_path, plan_text):
    plan = tmp_path / "plan.md"
    plan.write_text(plan_text)
    return subprocess.run(
        [sys.executable, str(LC_PATH), "schedule", str(tmp_path), "--plan", str(plan)],
        capture_output=True, text=True,
    )


def test_schedule_prints_topological_order(tmp_path):
    r = _schedule(tmp_path, _PLAN)
    assert r.returncode == 0, r.stderr
    assert "wave 1: T1" in r.stdout
    assert "wave 2: T2" in r.stdout


def test_schedule_exits_nonzero_on_cycle(tmp_path):
    r = _schedule(
        tmp_path,
        "### T1: a\n**Depends on:** T2\n### T2: b\n**Depends on:** T1\n",
    )
    assert r.returncode != 0
    assert "cycle" in r.stderr.lower()


def test_schedule_warns_but_reorders_on_forward_ref(tmp_path):
    # a forward-ref is a valid acyclic edge: WARN (not fail) + reorder so the
    # dependency runs first. Cycles are the hard error (test above).
    r = _schedule(
        tmp_path,
        "### T13: build\n**Depends on:** T15\n### T15: test\n**Depends on:** none\n",
    )
    assert r.returncode == 0, r.stderr
    assert "forward-reference" in r.stderr.lower()        # reported
    assert r.stdout.index("T15") < r.stdout.index("T13")  # reordered: T15 first


# ── T4: `dispatch-decision` verb (AC5) — the gate as a runnable command ──────


def _dispatch(*args):
    return subprocess.run(
        [sys.executable, str(LC_PATH), "dispatch-decision", *args],
        capture_output=True, text=True,
    )


def test_dispatch_decision_verb_safe_no_branches_parallel():
    # all-safe categories, no branches to conflict (<2) → clean → parallel.
    r = _dispatch("--category", "cannot-collide", "--category", "typed-group-b")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "parallel"


def test_dispatch_decision_verb_non_safe_serial():
    # a non-safe category fails closed even with nothing to merge.
    r = _dispatch("--category", "cannot-collide", "--category", "dangerous")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "serial"


# ── T7: cleared-gate surface rationale (AC10) ───────────────────────────────


def test_dispatch_rationale_parallel_names_eligible_and_count():
    # parallel-eligible rationale names the wave as eligible + the task count.
    msg = lc._dispatch_rationale(
        ["cannot-collide", "typed-group-b"], merge_tree_clean=True, decision="parallel"
    )
    assert "parallel-eligible" in msg.lower()
    assert "2" in msg


def test_dispatch_rationale_serial_non_safe_names_category():
    msg = lc._dispatch_rationale(
        ["cannot-collide", "shared-state"], merge_tree_clean=True, decision="serial"
    )
    assert "non-safe" in msg.lower()
    assert "shared-state" in msg


def test_dispatch_rationale_serial_overlap_names_merge_tree():
    # branch overlap → name the git merge-tree conflict, not specific files.
    msg = lc._dispatch_rationale(
        ["cannot-collide"], merge_tree_clean=False, decision="serial"
    )
    assert "git merge-tree" in msg


def test_dispatch_rationale_both_fail_tiebreak_is_merge_tree():
    # both non-safe AND overlapping → merge-tree reason wins (short-circuit order).
    msg = lc._dispatch_rationale(
        ["shared-state"], merge_tree_clean=False, decision="serial"
    )
    assert "git merge-tree" in msg
    assert "shared-state" not in msg  # the category reason is NOT what's named


def test_decision_and_rationale_stay_coupled_on_both_fail():
    # AC10 tie-break correctness depends on dispatch_decision and
    # _dispatch_rationale sharing the merge_tree_clean-first short-circuit.
    # Drive BOTH from the same both-fail input so a future reorder of either
    # function trips this test (not just a stale docstring).
    cats, clean = ["shared-state"], False
    decision = lc.dispatch_decision(cats, merge_tree_clean=clean)
    assert decision == "serial"
    msg = lc._dispatch_rationale(cats, merge_tree_clean=clean, decision=decision)
    assert "git merge-tree" in msg          # the merge-tree half is named first
    assert "shared-state" not in msg        # not the category half


def test_dispatch_decision_verb_parallel_emits_rationale_to_stderr():
    # stdout stays the bare token; the human-facing rationale lands on stderr.
    r = _dispatch("--category", "cannot-collide", "--category", "typed-group-b")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "parallel"
    assert "parallel-eligible" in r.stderr.lower()


# ── supervisor-auto-classify T1: classify_task (AC1–AC4) ────────────────────


def test_classify_all_added_is_cannot_collide():
    assert lc.classify_task([("A", "src/new_a.py"), ("A", "src/new_b.py")]) == "cannot-collide"


def test_classify_iff_reverse_single_non_added_flips_off():
    # AC1 reverse direction: one M among adds → not cannot-collide.
    assert lc.classify_task([("A", "src/new.py"), ("M", "src/old.py")]) != "cannot-collide"


def test_classify_all_added_but_danger_path_is_not_cannot_collide():
    # AC1 reverse: an added danger-path is still not cannot-collide.
    assert lc.classify_task([("A", "pkg/__init__.py")]) == "danger-path"


def test_classify_rename_copy_delete_are_move_or_delete():
    assert lc.classify_task([("R100", "old.py", "new.py")]) == "move-or-delete"
    assert lc.classify_task([("C", "a.py", "b.py")]) == "move-or-delete"
    assert lc.classify_task([("D", "gone.py")]) == "move-or-delete"


def test_classify_danger_paths_each_serialize():
    for path in [
        "poetry.lock", "pyproject.toml", "pkg/__init__.py", "web/index.ts",
        ".github/workflows/ci.yml", "Makefile", "marketplace.json",
        "a/b/migrations/0001_init.py",  # nested — anchoring (AC3)
        "migrations/0001_init.py",      # top-level — Django/Alembic default (AC3)
    ]:
        assert lc.classify_task([("M", path)]) == "danger-path", path


def test_classify_modified_existing_is_fail_closed_label():
    assert lc.classify_task([("M", "src/handler.py")]) == "modified-existing"


def test_classify_labels_outside_safe_categories_except_cannot_collide():
    # cannot-collide is the only auto label in SAFE_CATEGORIES; the rest serialize.
    assert "cannot-collide" in lc.SAFE_CATEGORIES
    for label in ("move-or-delete", "danger-path", "modified-existing", "cross-branch-symbol"):
        assert label not in lc.SAFE_CATEGORIES, label


# ── T1: added_paths_may_share_symbol (AC8 unit) ─────────────────────────────


def test_share_symbol_shared_basename_true():
    assert lc.added_paths_may_share_symbol([{"x/plugin.py"}, {"y/plugin.py"}]) is True


def test_share_symbol_shared_parent_dir_true():
    assert lc.added_paths_may_share_symbol([{"plugins/a.py"}, {"plugins/b.py"}]) is True


def test_share_symbol_disjoint_false():
    assert lc.added_paths_may_share_symbol([{"x/a.py"}, {"y/b.py"}]) is False


def test_share_symbol_distinct_root_files_false():
    # two distinct-basename repo-root additions must NOT serialize (root "" is
    # excluded from the shared-dir match; a same-named root add is a merge-tree
    # conflict caught elsewhere). Pins the Concern-3 fix.
    assert lc.added_paths_may_share_symbol([{"README.md"}, {"LICENSE"}]) is False


# ── supervisor-auto-classify T2: dispatch-decision auto-path (AC5–AC10) ──────


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def _mk_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "a@x")
    _git(repo, "config", "user.name", "a")
    (repo / "base.py").write_text("BASE = 1\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    return repo


def _branch(repo, name, relpath, content="X = 1\n", *, modify=False):
    _git(repo, "checkout", "-q", "-b", name, "main")
    f = repo / relpath
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", name)
    _git(repo, "checkout", "-q", "main")


def _dispatch_in(repo, *args):
    return subprocess.run(
        [sys.executable, str(LC_PATH), "dispatch-decision", *args],
        cwd=repo, capture_output=True, text=True,
    )


def test_verb_auto_all_added_disjoint_is_parallel(tmp_path):
    repo = _mk_repo(tmp_path)
    _branch(repo, "p", "feat_p/p.py")
    _branch(repo, "q", "feat_q/q.py")
    r = _dispatch_in(repo, "--branch", "p", "--branch", "q")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "parallel"
    assert "auto-derived" in r.stderr.lower()          # AC7: auto, not human


def test_verb_auto_modified_existing_is_serial(tmp_path):
    repo = _mk_repo(tmp_path)
    _branch(repo, "m", "base.py", "BASE = 2\n")         # modifies existing
    _branch(repo, "p", "feat_p/p.py")
    r = _dispatch_in(repo, "--branch", "m", "--branch", "p")
    assert r.stdout.strip() == "serial"
    assert "modified-existing" in r.stderr             # AC7 names the signal


def test_verb_auto_cross_branch_shared_basename_is_serial(tmp_path):
    repo = _mk_repo(tmp_path)
    _branch(repo, "c1", "dirA/plugin.py")               # both add plugin.py
    _branch(repo, "c2", "dirB/plugin.py")
    r = _dispatch_in(repo, "--branch", "c1", "--branch", "c2")
    assert r.stdout.strip() == "serial"
    assert "cross-branch-symbol" in r.stderr            # AC8 integration


def test_verb_auto_unresolvable_base_fails_closed(tmp_path):
    repo = _mk_repo(tmp_path)
    _branch(repo, "p", "feat_p/p.py")
    _git(repo, "checkout", "-q", "--orphan", "orphan")  # no common ancestor
    (repo / "o.py").write_text("O = 1\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "orphan")
    _git(repo, "checkout", "-q", "main")
    r = _dispatch_in(repo, "--branch", "p", "--branch", "orphan")
    assert r.stdout.strip() == "serial"                 # AC9 fail-closed
    assert "base" in r.stderr.lower()


def test_verb_category_override_takes_precedence(tmp_path):
    repo = _mk_repo(tmp_path)
    _branch(repo, "p", "feat_p/p.py")
    r = _dispatch_in(repo, "--branch", "p", "--category", "typed-group-b")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "parallel"               # typed-group-b is safe
    assert "human-supplied" in r.stderr.lower()         # AC6 override path
