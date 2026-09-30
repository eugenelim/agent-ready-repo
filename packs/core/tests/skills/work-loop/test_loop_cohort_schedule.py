"""Unit tests for the wave-scheduled-supervisor scheduler in loop-cohort.py.

Covers the wave-scheduled supervisor:
  T1 — parse_depends_on + parse_plan
  T2 — topological order, cycle + forward-ref detection
  T4 — dispatch_decision gate

loop-cohort.py is a standalone hyphenated script; pure functions are loaded
via importlib here. CLI/exit-code behavior (the `schedule` verb) is exercised
by subprocess against the real file-path invocation elsewhere.
"""
from __future__ import annotations

import ast
import importlib.util
import inspect
import itertools
import json
import subprocess
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
LC_PATH = PACK_ROOT / ".apm/skills/work-loop/scripts/loop-cohort.py"


def _load():
    spec = importlib.util.spec_from_file_location("loop_cohort_under_test", LC_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lc = _load()

LOCAL = {f"T{i}" for i in range(1, 16)} | {"T1a", "T1b", "T1c"}


# ── T1: parse_depends_on ────────────────────────────────────────────────────

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


# ── T1: detect_unknown_deps ─────────────────────────────────────────────────

def test_detect_unknown_deps_names_the_absent_id():
    plan = "## T1: a\n**Depends on:** none\n\n## T2: b\n**Depends on:** T7\n"
    assert lc.detect_unknown_deps(plan) == [("T2", "T7")]


def test_detect_unknown_deps_names_all_pairs_sorted():
    # T1 declares unknown T9; T2 declares unknown T7 and T8.
    plan = (
        "## T1: a\n**Depends on:** T9\n\n"
        "## T2: b\n**Depends on:** T8, T7\n"
    )
    assert lc.detect_unknown_deps(plan) == [("T1", "T9"), ("T2", "T7"), ("T2", "T8")]


# Fixture plan for all legitimate-form cases: contains T1, T1a, T2, T3, T4.
# T4's Depends on: field is substituted per parametrize.
_CLEAN_PLAN_TEMPLATE = (
    "## T1: a\n**Depends on:** none\n\n"
    "## T1a: b\n**Depends on:** none\n\n"
    "## T2: c\n**Depends on:** none\n\n"
    "## T3: d\n**Depends on:** none\n\n"
    "## T4: e\n**Depends on:** {dep}\n"
)


@pytest.mark.parametrize("dep", [
    "none",
    "T1",                  # in-plan ID
    "T1a",                 # letter-suffix ID
    "T1-T3",               # in-plan range (T1, T2, T3 all present)
    "spec:other/T7",       # cross-spec marker
    "`other` T7",          # legacy cross-spec marker
    "T1 (trailing prose)",  # trailing parenthetical prose
])
def test_detect_unknown_deps_clean_forms(dep):
    plan = _CLEAN_PLAN_TEMPLATE.format(dep=dep)
    assert lc.detect_unknown_deps(plan) == []


def test_detect_unknown_deps_forward_ref_is_clean():
    # T1 depends on T2 which is authored later — but T2 is in the plan.
    plan = "## T1: a\n**Depends on:** T2\n\n## T2: b\n**Depends on:** none\n"
    assert lc.detect_unknown_deps(plan) == []


def test_detect_unknown_deps_range_spanning_absent_intermediate():
    # Plan holds T1 and T3; T3 declares T1-T3 so T2 is an absent intermediate.
    plan = (
        "## T1: a\n**Depends on:** none\n\n"
        "## T3: c\n**Depends on:** T1-T3\n"
    )
    assert lc.detect_unknown_deps(plan) == [("T3", "T2")]


def test_detect_unknown_deps_resolution_set_uses_full_plan():
    # RESOLUTION AXIS — discriminating case.
    # T3 declares dep on T1; scan set is {"T3"} (T1 and T2 are excluded from scan).
    # T1 IS in the resolution set (the full plan), so the dep is met, not unknown.
    # A mutant that derives the resolution set from scan_task_ids returns [("T3","T1")].
    plan = (
        "## T1: a\n**Depends on:** none\n\n"
        "## T2: b\n**Depends on:** none\n\n"
        "## T3: c\n**Depends on:** T1\n"
    )
    assert lc.detect_unknown_deps(plan, {"T3"}) == []


def test_detect_unknown_deps_scan_set_gates_which_tasks_are_read():
    # SCAN AXIS — one fixture, two calls, proven by difference.
    # T2 declares an unknown dep (T9); T1 and T3 are clean.
    plan = (
        "## T1: a\n**Depends on:** none\n\n"
        "## T2: b\n**Depends on:** T9\n\n"
        "## T3: c\n**Depends on:** none\n"
    )
    # T2 excluded from scan → no pair reported
    assert lc.detect_unknown_deps(plan, {"T1", "T3"}) == []
    # T2 included in scan → pair appears
    assert lc.detect_unknown_deps(plan, {"T1", "T2", "T3"}) == [("T2", "T9")]


# ── T2: topological order ───────────────────────────────────────────────────

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


# ── T2: cycle detection ─────────────────────────────────────────────────────

def test_detect_cycle():
    ordered, deps = lc.parse_plan(
        "### T1: a\n**Depends on:** T2\n### T2: b\n**Depends on:** T1\n"
    )
    cyc = lc.detect_cycles(ordered, deps)
    assert set(cyc) == {"T1", "T2"}


def test_no_cycle_on_dag():
    ordered, deps = lc.parse_plan(_PLAN)
    assert lc.detect_cycles(ordered, deps) == []


# ── T2: forward-ref detection — the two real cases, by shape ────────────────

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


# ── T4: dispatch_decision gate ──────────────────────────────────────────────

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


# ── T3: `schedule` verb — real file-path invocation via subprocess ──────────

def _seed_state(tmp_path):
    """Seed a minimal valid cohort state.json and return the run_id."""
    run_id = str(uuid.uuid4())
    (tmp_path / "state.json").write_text(
        json.dumps({
            "schema_version": lc.SCHEMA_VERSION,
            "run_id": run_id,
            "pending_transition": None,
            "transition_history": [],
        }),
        encoding="utf-8",
    )
    return run_id


def _schedule(tmp_path, plan_text):
    run_id = _seed_state(tmp_path)
    plan = tmp_path / "plan.md"
    plan.write_text(plan_text, encoding="utf-8", newline="\n")
    return subprocess.run(
        [
            sys.executable, str(LC_PATH), "schedule", str(tmp_path),
            "--plan", str(plan), "--expect-run-id", run_id,
        ],
        capture_output=True, text=True, cwd=str(tmp_path),
    )


def test_schedule_prints_topological_order(git_repo):
    r = _schedule(git_repo, _PLAN)
    assert r.returncode == 0, r.stderr
    assert "wave 1: T1" in r.stdout
    assert "wave 2: T2" in r.stdout


def test_schedule_exits_nonzero_on_cycle(git_repo):
    r = _schedule(
        git_repo,
        "### T1: a\n**Depends on:** T2\n### T2: b\n**Depends on:** T1\n",
    )
    assert r.returncode != 0
    assert "cycle" in r.stderr.lower()


def test_schedule_warns_but_reorders_on_forward_ref(git_repo):
    # a forward-ref is a valid acyclic edge: WARN (not fail) + reorder so the
    # dependency runs first. Cycles are the hard error (test above).
    r = _schedule(
        git_repo,
        "### T13: build\n**Depends on:** T15\n### T15: test\n**Depends on:** none\n",
    )
    assert r.returncode == 0, r.stderr
    assert "forward-reference" in r.stderr.lower()        # reported
    assert r.stdout.index("T15") < r.stdout.index("T13")  # reordered: T15 first


# ── T4: `dispatch-decision` verb — the gate as a runnable command ────────────


def _dispatch(*args):
    return subprocess.run(
        [sys.executable, str(LC_PATH), "dispatch-decision", *args],
        capture_output=True, text=True,
    )


def test_dispatch_decision_verb_safe_no_branches_parallel():
    # Phase 1: dispatch-decision is disabled — exits non-zero with clear message.
    r = _dispatch("--category", "cannot-collide", "--category", "typed-group-b")
    assert r.returncode != 0
    assert "disabled in Phase 1" in r.stderr


def test_dispatch_decision_verb_non_safe_serial():
    # Phase 1: dispatch-decision is disabled — exits non-zero with clear message.
    r = _dispatch("--category", "cannot-collide", "--category", "dangerous")
    assert r.returncode != 0
    assert "disabled in Phase 1" in r.stderr


# ── T7: cleared-gate surface rationale ──────────────────────────────────────
# Phase 1: _dispatch_rationale is removed alongside the dispatch-decision verb.
# The pure dispatch_decision() function (unit-testable) still exists.

def test_dispatch_decision_pure_function_still_exists():
    # Phase 1: the pure function remains for future use; only the CLI verb is disabled.
    assert lc.dispatch_decision(["cannot-collide"], merge_tree_clean=True) == "parallel"
    assert lc.dispatch_decision(["shared-state"], merge_tree_clean=True) == "serial"


def test_dispatch_decision_verb_parallel_emits_rationale_to_stderr():
    # Phase 1: dispatch-decision verb is disabled — exits non-zero.
    r = _dispatch("--category", "cannot-collide", "--category", "typed-group-b")
    assert r.returncode != 0
    assert "disabled in Phase 1" in r.stderr


# ── supervisor-auto-classify T1: classify_task ──────────────────────────────


def test_classify_all_added_is_cannot_collide():
    assert lc.classify_task([("A", "src/new_a.py"), ("A", "src/new_b.py")]) == "cannot-collide"


def test_classify_iff_reverse_single_non_added_flips_off():
    # Reverse direction: one M among adds → not cannot-collide.
    assert lc.classify_task([("A", "src/new.py"), ("M", "src/old.py")]) != "cannot-collide"


def test_classify_all_added_but_danger_path_is_not_cannot_collide():
    # Reverse: an added danger-path is still not cannot-collide.
    assert lc.classify_task([("A", "pkg/__init__.py")]) == "danger-path"


def test_classify_rename_copy_delete_are_move_or_delete():
    assert lc.classify_task([("R100", "old.py", "new.py")]) == "move-or-delete"
    assert lc.classify_task([("C", "a.py", "b.py")]) == "move-or-delete"
    assert lc.classify_task([("D", "gone.py")]) == "move-or-delete"


def test_classify_danger_paths_each_serialize():
    for path in [
        "poetry.lock", "pyproject.toml", "pkg/__init__.py", "web/index.ts",
        ".github/workflows/ci.yml", "Makefile", "marketplace.json",
        "a/b/migrations/0001_init.py",  # nested — anchoring
        "migrations/0001_init.py",      # top-level — Django/Alembic default
    ]:
        assert lc.classify_task([("M", path)]) == "danger-path", path


def test_classify_modified_existing_is_fail_closed_label():
    assert lc.classify_task([("M", "src/handler.py")]) == "modified-existing"


def test_classify_labels_outside_safe_categories_except_cannot_collide():
    # cannot-collide is the only auto label in SAFE_CATEGORIES; the rest serialize.
    assert "cannot-collide" in lc.SAFE_CATEGORIES
    for label in ("move-or-delete", "danger-path", "modified-existing", "cross-branch-symbol"):
        assert label not in lc.SAFE_CATEGORIES, label


# ── T1: added_paths_may_share_symbol (unit) ─────────────────────────────────
# Phase 1: added_paths_may_share_symbol is removed alongside dispatch-decision.
# The cross-branch symbol-collision check was only called from dispatch-decision.

def test_share_symbol_not_exposed_in_phase1():
    # Confirms the function is not accidentally retained in the Phase-1 surface.
    assert not hasattr(lc, "added_paths_may_share_symbol")


# ── supervisor-auto-classify T2: dispatch-decision auto-path ─────────────────


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def _mk_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "a@x")
    _git(repo, "config", "user.name", "a")
    (repo / "base.py").write_text("BASE = 1\n", encoding="utf-8", newline="\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    return repo


def _branch(repo, name, relpath, content="X = 1\n", *, modify=False):
    _git(repo, "checkout", "-q", "-b", name, "main")
    f = repo / relpath
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content, encoding="utf-8", newline="\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", name)
    _git(repo, "checkout", "-q", "main")


def _dispatch_in(repo, *args):
    return subprocess.run(
        [sys.executable, str(LC_PATH), "dispatch-decision", *args],
        cwd=repo, capture_output=True, text=True,
    )


def test_verb_auto_all_added_disjoint_is_parallel(tmp_path):
    # Phase 1: dispatch-decision --branch is disabled.
    repo = _mk_repo(tmp_path)
    _branch(repo, "p", "feat_p/p.py")
    _branch(repo, "q", "feat_q/q.py")
    r = _dispatch_in(repo, "--branch", "p", "--branch", "q")
    assert r.returncode != 0
    assert "disabled in Phase 1" in r.stderr


def test_verb_auto_modified_existing_is_serial(tmp_path):
    # Phase 1: dispatch-decision --branch is disabled.
    repo = _mk_repo(tmp_path)
    _branch(repo, "m", "base.py", "BASE = 2\n")
    _branch(repo, "p", "feat_p/p.py")
    r = _dispatch_in(repo, "--branch", "m", "--branch", "p")
    assert r.returncode != 0
    assert "disabled in Phase 1" in r.stderr


def test_verb_auto_cross_branch_shared_basename_is_serial(tmp_path):
    # Phase 1: dispatch-decision --branch is disabled.
    repo = _mk_repo(tmp_path)
    _branch(repo, "c1", "dirA/plugin.py")
    _branch(repo, "c2", "dirB/plugin.py")
    r = _dispatch_in(repo, "--branch", "c1", "--branch", "c2")
    assert r.returncode != 0
    assert "disabled in Phase 1" in r.stderr


def test_verb_auto_unresolvable_base_fails_closed(tmp_path):
    # Phase 1: dispatch-decision --branch is disabled (exits non-zero).
    repo = _mk_repo(tmp_path)
    _branch(repo, "p", "feat_p/p.py")
    _git(repo, "checkout", "-q", "--orphan", "orphan")
    (repo / "o.py").write_text("O = 1\n", encoding="utf-8", newline="\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "orphan")
    _git(repo, "checkout", "-q", "main")
    r = _dispatch_in(repo, "--branch", "p", "--branch", "orphan")
    assert r.returncode != 0
    assert "disabled in Phase 1" in r.stderr


def test_verb_category_override_takes_precedence(tmp_path):
    # Phase 1: dispatch-decision --category override is also disabled.
    repo = _mk_repo(tmp_path)
    _branch(repo, "p", "feat_p/p.py")
    r = _dispatch_in(repo, "--branch", "p", "--category", "typed-group-b")
    assert r.returncode != 0
    assert "disabled in Phase 1" in r.stderr


# ── supervisor-predict-disjointness PD-T1: parse Touches: ────────────────────


def test_parse_touches_comma_list():
    assert lc.parse_touches("src/api/*.py, docs/api.md") == {"src/api/*.py", "docs/api.md"}


def test_parse_touches_tolerates_prose():
    assert lc.parse_touches("src/*.py (the handlers)") == {"src/*.py"}


def test_parse_touches_by_task_maps_declared_only():
    plan = (
        "### T1: a\n**Depends on:** none\n**Touches:** src/a/*.py\n"
        "### T2: b\n**Depends on:** none\n"  # no Touches: line
        "### T3: c\n**Touches:** docs/c.md, src/c.py\n"
    )
    m = lc.parse_touches_by_task(plan)
    assert m["T1"] == {"src/a/*.py"}
    assert m["T3"] == {"docs/c.md", "src/c.py"}
    assert "T2" not in m            # optional: absent, not an empty-set key, no error


def test_parse_plan_signature_unchanged():
    # parse_plan must still return exactly (ordered, deps) — no arity change.
    ordered, deps = lc.parse_plan("### T1: a\n**Depends on:** none\n")
    assert ordered == ["T1"]


# ── PD-T2: globs_overlap — conservative, segment-wise ───────────────────────


def test_globs_overlap_literal_segment_mismatch_disjoint():
    assert lc.globs_overlap("src/a/*", "src/b/*") is False


def test_globs_overlap_different_depth_no_doublestar_disjoint():
    assert lc.globs_overlap("src/*", "src/api/x.py") is False  # * never crosses /


def test_globs_overlap_prefix_path_true():
    assert lc.globs_overlap("src/api/*", "src/api/x.py") is True


def test_globs_overlap_identical_true():
    assert lc.globs_overlap("src/api/x.py", "src/api/x.py") is True


def test_globs_overlap_wildcard_vs_wildcard_true():
    # the case a both-ways .match MISSES — both match src/api/handler.py
    assert lc.globs_overlap("src/api/*.py", "src/*/handler.py") is True
    assert lc.globs_overlap("a/*/x.py", "*/b/x.py") is True


def test_globs_overlap_doublestar_failsafe_true():
    assert lc.globs_overlap("**/*.py", "src/x.py") is True


def test_globs_overlap_distinct_dirs_disjoint():
    assert lc.globs_overlap("foo/*.py", "bar/*.py") is False


def test_globs_overlap_charclass_is_pattern_not_literal_true():
    # [abc].py is a PATTERN (not a pure literal); fnmatch("a.py","[abc].py") True
    assert lc.globs_overlap("[abc].py", "a.py") is True


# ── PD-T2: wave_touches_disjoint ────────────────────────────────────────────


def test_wave_touches_disjoint_all_disjoint_yes():
    assert lc.wave_touches_disjoint([{"src/a/*"}, {"src/b/*"}]) == "yes"


def test_wave_touches_disjoint_overlap_no():
    assert lc.wave_touches_disjoint([{"src/api/*"}, {"src/api/x.py"}]) == "no"


def test_wave_touches_disjoint_overlap_wins_over_missing():
    # two declared tasks overlap; a third omits Touches -> still "no"
    assert lc.wave_touches_disjoint([{"src/api/*"}, {"src/api/x.py"}, None]) == "no"


def test_wave_touches_disjoint_missing_blocks_yes_only():
    # no overlap found but a task is absent -> unknown (not yes)
    assert lc.wave_touches_disjoint([{"src/a/*"}, None]) == "unknown"


# ── PD-T3: schedule predicted-disjoint annotation + screen-only ──────────────


def test_schedule_predicts_no_on_overlapping_touches(git_repo):
    r = _schedule(
        git_repo,
        "### T1: a\n**Depends on:** none\n**Touches:** src/api/*\n"
        "### T2: b\n**Depends on:** none\n**Touches:** src/api/x.py\n",
    )
    assert r.returncode == 0, r.stderr
    assert "predicted-disjoint: no" in r.stdout


def test_schedule_predicts_yes_on_disjoint_touches(git_repo):
    r = _schedule(
        git_repo,
        "### T1: a\n**Depends on:** none\n**Touches:** src/a/*\n"
        "### T2: b\n**Depends on:** none\n**Touches:** src/b/*\n",
    )
    assert "predicted-disjoint: yes" in r.stdout


def test_schedule_predicts_unknown_when_a_task_omits_touches(git_repo):
    r = _schedule(
        git_repo,
        "### T1: a\n**Depends on:** none\n**Touches:** src/a/*\n"
        "### T2: b\n**Depends on:** none\n",  # no Touches:
    )
    assert "predicted-disjoint: unknown" in r.stdout


def test_schedule_no_annotation_on_single_task_wave(git_repo):
    r = _schedule(git_repo, "### T1: a\n**Depends on:** none\n**Touches:** src/a/*\n")
    assert r.returncode == 0, r.stderr
    assert "predicted-disjoint" not in r.stdout  # single-task wave → no annotation


def test_schedule_is_screen_only_no_gate_call(tmp_path):
    # Positive form: the predict path (cmd_schedule) shares no call with the
    # authoritative gate; and dispatch_decision's signature is unchanged.
    import inspect
    # the whole predict path (cmd_schedule -> wave_touches_disjoint ->
    # globs_overlap) must share no call with the gate path — guard all three so
    # a future refactor can't slip a gate call into a transitive helper.
    for fn in (lc.cmd_schedule, lc.wave_touches_disjoint, lc.globs_overlap):
        src = inspect.getsource(fn)
        assert "dispatch_decision" not in src, fn.__name__
        assert "wave_is_disjoint" not in src, fn.__name__
    # full signature string captures the `*` keyword-only marker, not just names
    assert str(inspect.signature(lc.dispatch_decision)) == "(categories, *, merge_tree_clean)"


# ── supervisor-auto-parallel AP-PT1: auto_parallel field + verb ─────────────

def _run_lc(*args, cwd: Path):
    return subprocess.run([sys.executable, str(LC_PATH), *args],
                          capture_output=True, text=True, cwd=str(cwd))


_WAVE_DECISION_PUBLIC_REFUSAL_DETAILS = {
    "unsupported-state-schema-version": "cohort state schema is unsupported",
    "state-unreadable": "cohort state could not be read",
    "no-schedule": "cohort has no scheduled wave",
    "state-malformed": "cohort state is malformed",
    "plan-missing": "scheduled plan could not be found",
    "plan-status-illegal": "scheduled plan status is illegal",
    "plan-hash-stale": "scheduled plan hash is stale",
    "wave-index-out-of-range": "requested wave index is out of range",
    "empty-wave": "selected wave has no unfinished work",
}


def _write_scheduled_state(
    spec_dir: Path,
    *,
    run_id: str | None = None,
    plan_hash: str = "0" * 64,
    schedule_waves: list[list[str]] | object | None = None,
    current_wave_index: object = 0,
    completed_task_ids: object | None = None,
    schema_version: object | None = None,
) -> str:
    if run_id is None:
        run_id = str(uuid.uuid4())
    state = {
        "schema_version": lc.SCHEMA_VERSION if schema_version is None else schema_version,
        "run_id": run_id,
        "pending_transition": None,
        "transition_history": [],
        "plan_hash": plan_hash,
        "schedule_waves": [["T1", "T2"]] if schedule_waves is None else schedule_waves,
        "current_wave_index": current_wave_index,
        "completed_task_ids": [] if completed_task_ids is None else completed_task_ids,
    }
    (spec_dir / "state.json").write_text(
        json.dumps(state, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return run_id


def _sha_plan(spec_dir: Path) -> str:
    return lc.sha256_canonical_contract(spec_dir / "plan.md")


def _write_plan(spec_dir: Path, plan_text: str) -> str:
    (spec_dir / "plan.md").write_text(plan_text, encoding="utf-8", newline="\n")
    return _sha_plan(spec_dir)


def _scheduled_fixture(
    spec_dir: Path,
    plan_text: str,
    *,
    schedule_waves: list[list[str]] | None = None,
    current_wave_index: object = 0,
    completed_task_ids: object | None = None,
) -> str:
    plan_hash = _write_plan(spec_dir, plan_text)
    return _write_scheduled_state(
        spec_dir,
        plan_hash=plan_hash,
        schedule_waves=schedule_waves,
        current_wave_index=current_wave_index,
        completed_task_ids=completed_task_ids,
    )


def _decision(spec_dir: Path, *args: str):
    before = (spec_dir / "state.json").read_bytes() if (spec_dir / "state.json").exists() else None
    result = _run_lc("wave-decision", str(spec_dir), *args, cwd=spec_dir)
    after = (spec_dir / "state.json").read_bytes() if (spec_dir / "state.json").exists() else None
    assert after == before
    return result


def _decision_payload(spec_dir: Path, *args: str) -> dict:
    result = _decision(spec_dir, *args, "--json")
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    return json.loads(result.stdout)


def _plan_from_touches(items: list[tuple[str, str | None]]) -> str:
    chunks = ["# Plan\n\n- **Status:** Executing\n\n"]
    for task_id, touches in items:
        chunks.append(f"### {task_id}: task {task_id}\n**Depends on:** none\n")
        if touches is not None:
            chunks.append(f"**Touches:** {touches}\n")
        chunks.append("\n")
    return "".join(chunks)


# STUB: AC-0001 — the real CLI emits one read-only decision envelope
def test_wave_decision_json_reports_scheduled_wave(git_repo):
    plan = (
        "# Plan\n\n- **Status:** Executing\n\n"
        "### T1: a\n**Depends on:** none\n**Touches:** src/a/*.py\n\n"
        "### T2: b\n**Depends on:** none\n**Touches:** src/b/*.py\n"
    )
    scheduled = _schedule(git_repo, plan)
    assert scheduled.returncode == 0, scheduled.stderr
    before = (git_repo / "state.json").read_bytes()

    result = _run_lc("wave-decision", str(git_repo), "--json", cwd=git_repo)

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["payload_version"] == 1
    assert payload["wave"] == ["T1", "T2"]
    assert payload["wave_disposition"] == "all-parallel-capable"
    assert payload["cohort"] == ["T1", "T2"]
    assert payload["admission_pending"] is True
    assert (git_repo / "state.json").read_bytes() == before


def test_wave_decision_uses_the_validated_schedule_snapshot(
    git_repo, monkeypatch, capsys
):
    initial_plan = _plan_from_touches([("T1", "src/initial.py")])
    _scheduled_fixture(git_repo, initial_plan, schedule_waves=[["T1"]])
    initial_state = json.loads((git_repo / "state.json").read_text(encoding="utf-8"))

    snapshot_plan = _plan_from_touches([
        ("T2", "src/snapshot/a.py"),
        ("T3", "src/snapshot/b.py"),
    ])
    snapshot_state = {
        **initial_state,
        "plan_hash": "1" * 64,
        "schedule_waves": [["T2", "T3"]],
        "current_wave_index": 0,
    }
    original_check = lc._g.check_schedule_current

    def checked_snapshot(spec_dir, *, include_snapshot=False):
        if include_snapshot:
            return lc._g.GuardResult(
                ok=True,
                message="schedule check-current OK",
                data={"state": snapshot_state, "plan_text": snapshot_plan},
            )
        return original_check(spec_dir)

    monkeypatch.setattr(lc, "_resolve_spec_dir", lambda _raw: git_repo)
    monkeypatch.setattr(lc, "read_state", lambda _spec_dir: initial_state)
    monkeypatch.setattr(
        lc._g,
        "check_identity",
        lambda _spec_dir, *, expect_run_id: lc._g.GuardResult(
            ok=True, message="identity OK"
        ),
    )
    monkeypatch.setattr(lc._g, "check_schedule_current", checked_snapshot)

    result = lc.cmd_wave_decision(
        SimpleNamespace(
            spec_dir=str(git_repo),
            wave=None,
            force_sequential=[],
            json=True,
        )
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["wave"] == ["T2", "T3"]
    assert payload["plan_hash"] == "1" * 64


def test_schedule_guard_returns_the_hash_checked_snapshot(git_repo):
    plan = _plan_from_touches([
        ("T1", "src/a.py"),
        ("T2", "src/b.py"),
    ])
    _scheduled_fixture(git_repo, plan)

    result = lc._g.check_schedule_current(git_repo, include_snapshot=True)

    assert result.ok, result.reason
    assert result.data == {
        "state": json.loads((git_repo / "state.json").read_text(encoding="utf-8")),
        "plan_text": plan,
    }


@pytest.mark.parametrize("json_mode", [True, False])
def test_wave_decision_late_state_read_refuses_state_unreadable(
    git_repo, monkeypatch, capsys, json_mode
):
    plan = _plan_from_touches([("T1", "src/a.py"), ("T2", "src/b.py")])
    _scheduled_fixture(git_repo, plan)
    before = (git_repo / "state.json").read_bytes()
    monkeypatch.setattr(lc, "_resolve_spec_dir", lambda _raw: git_repo)
    monkeypatch.setattr(
        lc._g,
        "check_schedule_current",
        lambda _spec_dir, *, include_snapshot=False: lc._g.GuardResult(
            ok=False,
            reason="state.json disappeared during schedule validation",
            data={"failure_kind": "state-unreadable"},
        ),
    )

    result = lc.cmd_wave_decision(
        SimpleNamespace(
            spec_dir=str(git_repo),
            wave=None,
            force_sequential=[],
            json=json_mode,
        )
    )

    captured = capsys.readouterr()
    assert result == 1
    if json_mode:
        assert captured.err == ""
        assert json.loads(captured.out) == {
            "payload_version": 1,
            "refusal": "state-unreadable",
            "detail": "cohort state could not be read",
        }
    else:
        assert captured.out == ""
        assert "state.json disappeared during schedule validation" in captured.err
    assert (git_repo / "state.json").read_bytes() == before


def test_schedule_guard_classifies_state_read_failure(git_repo):
    missing = git_repo / "late-state-missing"
    missing.mkdir()

    result = lc._g.check_schedule_current(missing, include_snapshot=True)

    assert not result.ok
    assert result.data == {"failure_kind": "state-unreadable"}


def test_wave_decision_json_refusal_detail_is_public_safe(git_repo):
    marker = "DO-NOT-ECHO"
    outside = git_repo.parent / marker

    result = _run_lc("wave-decision", str(outside), "--json", cwd=git_repo)

    assert result.returncode == 1
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload == {
        "payload_version": 1,
        "refusal": "state-unreadable",
        "detail": "cohort state could not be read",
    }
    assert marker not in result.stdout


@pytest.mark.parametrize("width", [1, 2, 3, 4, 5])
def test_wave_decision_pairs_match_combination_formula(git_repo, width):
    items = [(f"T{i}", f"src/{i}/*.py") for i in range(1, width + 1)]
    wave = [task_id for task_id, _touches in items]
    _scheduled_fixture(git_repo, _plan_from_touches(items), schedule_waves=[wave])

    payload = _decision_payload(git_repo)

    assert len(payload["pairs"]) == width * (width - 1) // 2
    assert [row["tasks"] for row in payload["pairs"]] == [
        list(pair) for pair in itertools.combinations(wave, 2)
    ]
    assert all("disposition" not in row and "admission" not in row for row in payload["pairs"])


def test_wave_decision_pair_relations_cover_disjoint_overlapping_unknown(git_repo):
    plan = _plan_from_touches([
        ("T1", "src/a/*"),
        ("T2", "src/b/*"),
        ("T3", "src/a/x.py"),
        ("T4", None),
    ])
    _scheduled_fixture(git_repo, plan, schedule_waves=[["T1", "T2", "T3", "T4"]])

    payload = _decision_payload(git_repo)

    relations = {tuple(row["tasks"]): row["touches_relation"] for row in payload["pairs"]}
    assert relations[("T1", "T2")] == "disjoint"
    assert relations[("T1", "T3")] == "overlapping"
    assert relations[("T1", "T4")] == "unknown"


def test_wave_decision_reason_codes_accumulate_and_overlap_short_circuits(git_repo):
    plan = _plan_from_touches([
        ("T1", "src/a/*"),
        ("T2", "src/a/x.py, src/a/y.py"),
        ("T3", None),
        ("T4", "db/migrations/0001.sql"),
        ("T5", "src/e/*"),
    ])
    _scheduled_fixture(git_repo, plan, schedule_waves=[["T1", "T2", "T3", "T4", "T5"]])

    payload = _decision_payload(git_repo, "--force-sequential", "T3")

    by_id = {row["task_id"]: row for row in payload["tasks"]}
    assert by_id["T1"]["disposition"] == "parallel-capable"
    assert by_id["T2"]["reasons"] == [
        {"code": "touches-overlap", "with": "T1", "globs": ["src/a/x.py", "src/a/*"]}
    ]
    assert by_id["T3"]["reasons"] == [
        {"code": "touches-undeclared"},
        {"code": "override-forced-sequential", "source": "cli"},
    ]
    assert by_id["T4"]["reasons"] == [
        {"code": "danger-path-declared", "glob": "db/migrations/0001.sql"}
    ]
    assert payload["cohort"] == ["T1", "T5"]
    assert payload["wave_disposition"] == "partially-parallel-capable"


def test_wave_decision_bare_force_sequential_applies_to_whole_wave(git_repo):
    plan = _plan_from_touches([("T1", "src/a/*"), ("T2", "src/b/*")])
    _scheduled_fixture(git_repo, plan)

    payload = _decision_payload(git_repo, "--force-sequential")

    assert payload["cohort"] == []
    assert payload["serialized"] == ["T1", "T2"]
    for row in payload["tasks"]:
        assert row["reasons"] == [{"code": "override-forced-sequential", "source": "cli"}]


def test_wave_decision_human_mode_succeeds_for_forced_verdict(git_repo):
    plan = _plan_from_touches([("T1", "src/a/*"), ("T2", "src/b/*")])
    _scheduled_fixture(git_repo, plan)

    result = _decision(git_repo, "--force-sequential", "T2")

    assert result.returncode == 0, result.stderr
    assert "wave_disposition:" in result.stdout
    assert "T2: sequential" in result.stdout
    assert result.stderr == ""


def test_wave_decision_overlap_short_circuits_on_first_admitted_peer(git_repo):
    plan = _plan_from_touches([
        ("T1", "src/a/*"),
        ("T2", "src/b/*"),
        ("T3", "src/a/x.py, src/b/x.py"),
    ])
    _scheduled_fixture(git_repo, plan, schedule_waves=[["T1", "T2", "T3"]])

    payload = _decision_payload(git_repo)

    task = {row["task_id"]: row for row in payload["tasks"]}["T3"]
    assert task["reasons"] == [
        {"code": "touches-overlap", "with": "T1", "globs": ["src/a/x.py", "src/a/*"]}
    ]


def test_wave_decision_overlap_accumulates_after_unary_reason(git_repo):
    plan = _plan_from_touches([
        ("T1", "src/a/*"),
        ("T2", "src/a/x.py"),
    ])
    _scheduled_fixture(git_repo, plan)

    payload = _decision_payload(git_repo, "--force-sequential", "T2")

    task = {row["task_id"]: row for row in payload["tasks"]}["T2"]
    assert task["reasons"] == [
        {"code": "override-forced-sequential", "source": "cli"},
        {
            "code": "touches-overlap",
            "with": "T1",
            "globs": ["src/a/x.py", "src/a/*"],
        },
    ]


@pytest.mark.parametrize(
    ("items", "expected_wave_disposition", "expected_cohort", "expected_serialized"),
    [
        ([("T1", "src/a/*")], "single-task", [], ["T1"]),
        ([("T1", "src/a/*"), ("T2", "src/b/*")], "all-parallel-capable", ["T1", "T2"], []),
        ([("T1", "src/a/*"), ("T2", "src/a/x.py"), ("T3", "src/b/*")], "partially-parallel-capable", ["T1", "T3"], ["T2"]),
        ([("T1", None), ("T2", "db/migrations/0001.sql")], "all-sequential", [], ["T1", "T2"]),
    ],
)
def test_wave_decision_disposition_shapes(
    git_repo, items, expected_wave_disposition, expected_cohort, expected_serialized
):
    wave = [task_id for task_id, _touches in items]
    _scheduled_fixture(git_repo, _plan_from_touches(items), schedule_waves=[wave])

    payload = _decision_payload(git_repo)

    assert payload["wave_disposition"] == expected_wave_disposition
    assert payload["cohort"] == expected_cohort
    assert payload["serialized"] == expected_serialized
    assert len(payload["cohort"]) != 1


def test_wave_decision_no_admitted_peer_reason(git_repo):
    plan = _plan_from_touches([("T1", "src/a/*"), ("T2", None)])
    _scheduled_fixture(git_repo, plan, schedule_waves=[["T1", "T2"]])

    payload = _decision_payload(git_repo)

    assert payload["cohort"] == []
    assert payload["tasks"][0]["reasons"] == [{"code": "no-admitted-peer"}]
    assert payload["tasks"][1]["reasons"] == [{"code": "touches-undeclared"}]


def test_wave_decision_wave_argument_and_completed_subtraction(git_repo):
    plan = _plan_from_touches([
        ("T1", "src/a/*"),
        ("T2", "src/b/*"),
        ("T3", "src/c/*"),
        ("T4", "src/d/*"),
    ])
    _scheduled_fixture(
        git_repo,
        plan,
        schedule_waves=[["T1", "T2"], ["T3", "T4"]],
        current_wave_index=1,
        completed_task_ids=["T3"],
    )

    default_payload = _decision_payload(git_repo)
    explicit_payload = _decision_payload(git_repo, "--wave", "0")

    assert default_payload["wave_index"] == 1
    assert default_payload["wave"] == ["T4"]
    assert default_payload["wave_disposition"] == "single-task"
    assert explicit_payload["wave_index"] == 0
    assert explicit_payload["wave"] == ["T1", "T2"]


def _assert_json_refusal(result: subprocess.CompletedProcess, code: str) -> dict:
    assert result.returncode == 1
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["payload_version"] == 1
    assert payload["refusal"] == code
    assert payload["detail"] == _WAVE_DECISION_PUBLIC_REFUSAL_DETAILS[code]
    assert 0 < len(payload["detail"]) <= 96
    assert "admission_pending" not in payload
    return payload


def _assert_human_refusal(result: subprocess.CompletedProcess, code_or_detail: str) -> None:
    assert result.returncode == 1
    assert result.stdout == ""
    assert "loop-cohort: stop" in result.stderr
    assert code_or_detail in result.stderr


def test_wave_decision_json_refusals_cover_closed_vocabulary(git_repo, tmp_path):
    cases: list[tuple[str, Path, str]] = []

    bad_schema = git_repo / "bad-schema"
    bad_schema.mkdir()
    _write_plan(bad_schema, _plan_from_touches([("T1", "src/a/*")]))
    _write_scheduled_state(bad_schema, schema_version=1)
    cases.append(("unsupported-state-schema-version", bad_schema, "schema_version=1"))

    missing_state = git_repo / "missing-state"
    missing_state.mkdir()
    cases.append(("state-unreadable", missing_state, "state.json"))

    no_schedule = git_repo / "no-schedule"
    no_schedule.mkdir()
    _write_scheduled_state(no_schedule, schedule_waves=[])
    cases.append(("no-schedule", no_schedule, "schedule_waves is absent or empty"))

    malformed = git_repo / "malformed"
    malformed.mkdir()
    _write_scheduled_state(malformed, schedule_waves=[["T1"]], current_wave_index="zero")
    cases.append(("state-malformed", malformed, "current_wave_index"))

    malformed_waves = git_repo / "malformed-waves"
    malformed_waves.mkdir()
    _write_scheduled_state(malformed_waves, schedule_waves="T1")
    cases.append(("state-malformed", malformed_waves, "schedule_waves"))

    malformed_completed = git_repo / "malformed-completed"
    malformed_completed.mkdir()
    _write_scheduled_state(
        malformed_completed,
        schedule_waves=[["T1"]],
        completed_task_ids="T1",
    )
    cases.append(("state-malformed", malformed_completed, "completed_task_ids"))

    missing_run_id = git_repo / "missing-run-id"
    missing_run_id.mkdir()
    _write_scheduled_state(missing_run_id, schedule_waves=[["T1"]])
    state = json.loads((missing_run_id / "state.json").read_text(encoding="utf-8"))
    state.pop("run_id")
    (missing_run_id / "state.json").write_text(
        json.dumps(state, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    cases.append(("state-malformed", missing_run_id, "run_id"))

    empty_run_id = git_repo / "empty-run-id"
    empty_run_id.mkdir()
    _write_scheduled_state(empty_run_id, run_id="", schedule_waves=[["T1"]])
    cases.append(("state-malformed", empty_run_id, "run_id"))

    plan_missing = git_repo / "plan-missing"
    plan_missing.mkdir()
    _write_scheduled_state(plan_missing)
    cases.append(("plan-missing", plan_missing, "plan.md not found"))

    illegal_status = git_repo / "illegal-status"
    illegal_status.mkdir()
    plan_hash = _write_plan(illegal_status, "# Plan\n\n- **Status:** Drafting\n\n### T1\n**Depends on:** none\n**Touches:** src/a/*\n")
    _write_scheduled_state(illegal_status, plan_hash=plan_hash, schedule_waves=[["T1"]])
    cases.append(("plan-status-illegal", illegal_status, "Drafting"))

    stale = git_repo / "stale"
    stale.mkdir()
    _write_plan(stale, _plan_from_touches([("T1", "src/a/*")]))
    _write_scheduled_state(stale, plan_hash="1" * 64, schedule_waves=[["T1"]])
    cases.append(("plan-hash-stale", stale, "plan.md no longer matches"))

    out_of_range = git_repo / "out-of-range"
    out_of_range.mkdir()
    _scheduled_fixture(out_of_range, _plan_from_touches([("T1", "src/a/*")]), schedule_waves=[["T1"]])
    cases.append(("wave-index-out-of-range", out_of_range, "wave_index=5"))

    empty = git_repo / "empty"
    empty.mkdir()
    _scheduled_fixture(
        empty,
        _plan_from_touches([("T1", "src/a/*")]),
        schedule_waves=[["T1"]],
        completed_task_ids=["T1"],
    )
    cases.append(("empty-wave", empty, "selected wave has no unfinished tasks"))

    outside = tmp_path / "outside"
    outside.mkdir()
    cases.append(("state-unreadable", outside, str(outside)))

    non_directory = git_repo / "not-a-directory"
    non_directory.write_text("not a spec dir\n", encoding="utf-8")
    cases.append(("state-unreadable", non_directory, "Not a directory"))

    invalid_state = git_repo / "invalid-state"
    invalid_state.mkdir()
    (invalid_state / "state.json").write_text("{not json\n", encoding="utf-8")
    cases.append(("state-unreadable", invalid_state, "state.json"))

    unreadable_state = git_repo / "unreadable-state"
    unreadable_state.mkdir()
    (unreadable_state / "state.json").mkdir()
    cases.append(("state-unreadable", unreadable_state, "state.json"))

    for code, spec_dir, detail in cases:
        args = ["--wave", "5"] if code == "wave-index-out-of-range" else []
        state_path = spec_dir / "state.json"
        before = state_path.read_bytes() if state_path.is_file() else None
        json_result = _run_lc("wave-decision", str(spec_dir), *args, "--json", cwd=git_repo)
        _assert_json_refusal(json_result, code)
        assert str(spec_dir) not in json_result.stdout
        if detail != _WAVE_DECISION_PUBLIC_REFUSAL_DETAILS[code]:
            assert detail not in json_result.stdout
        human_result = _run_lc("wave-decision", str(spec_dir), *args, cwd=git_repo)
        _assert_human_refusal(human_result, detail)
        after = state_path.read_bytes() if state_path.is_file() else None
        assert after == before


def test_wave_decision_state_malformed_folds_task_id_and_width_limits(git_repo):
    plan = _plan_from_touches([("T1", "src/a/*")])

    invalid_id = git_repo / "invalid-id"
    invalid_id.mkdir()
    _scheduled_fixture(invalid_id, plan, schedule_waves=[["T1", "BAD"]])
    _assert_json_refusal(_decision(invalid_id, "--json"), "state-malformed")

    overlong_id = git_repo / "overlong-id"
    overlong_id.mkdir()
    long_task = "T" + ("1" * 64)
    _scheduled_fixture(overlong_id, plan, schedule_waves=[["T1", long_task]])
    _assert_json_refusal(_decision(overlong_id, "--json"), "state-malformed")

    duplicate_id = git_repo / "duplicate-id"
    duplicate_id.mkdir()
    _scheduled_fixture(duplicate_id, plan, schedule_waves=[["T1", "T1"]])
    _assert_json_refusal(_decision(duplicate_id, "--json"), "state-malformed")

    ok64 = git_repo / "ok64"
    ok64.mkdir()
    ids64 = [f"T{i}" for i in range(1, 65)]
    _scheduled_fixture(ok64, _plan_from_touches([(task_id, f"src/{task_id}/*") for task_id in ids64]), schedule_waves=[ids64])
    payload64 = _decision_payload(ok64)
    assert len(payload64["pairs"]) == 2016
    assert [row["tasks"] for row in payload64["pairs"]] == [
        list(pair) for pair in itertools.combinations(ids64, 2)
    ]

    too_many = git_repo / "too-many"
    too_many.mkdir()
    ids65 = [f"T{i}" for i in range(1, 66)]
    _scheduled_fixture(too_many, _plan_from_touches([(task_id, f"src/{task_id}/*") for task_id in ids65]), schedule_waves=[ids65])
    _assert_json_refusal(_decision(too_many, "--json"), "state-malformed")


def _touch_items(count: int, *, prefix: str = "src") -> str:
    return ", ".join(f"{prefix}/g{i}.py" for i in range(count))


def test_wave_decision_touches_per_task_limit_is_folded_to_plan_status_illegal(git_repo):
    accepted = git_repo / "touches64"
    accepted.mkdir()
    _scheduled_fixture(
        accepted,
        _plan_from_touches([("T1", _touch_items(64)), ("T2", "other/x.py")]),
    )
    assert _decision(accepted, "--json").returncode == 0

    refused = git_repo / "touches65"
    refused.mkdir()
    _scheduled_fixture(
        refused,
        _plan_from_touches([("T1", _touch_items(65)), ("T2", "other/x.py")]),
    )

    _assert_json_refusal(_decision(refused, "--json"), "plan-status-illegal")
    _assert_human_refusal(_decision(refused), "maximum is 64")


def test_wave_decision_touches_per_wave_limit_is_folded_to_plan_status_illegal(git_repo):
    accepted = git_repo / "wave-touches256"
    accepted.mkdir()
    ids64 = [f"T{i}" for i in range(1, 65)]
    _scheduled_fixture(
        accepted,
        _plan_from_touches([
            (task_id, _touch_items(4, prefix=f"src/{task_id}"))
            for task_id in ids64
        ]),
        schedule_waves=[ids64],
    )
    assert _decision(accepted, "--json").returncode == 0

    refused = git_repo / "wave-touches257"
    refused.mkdir()
    ids = [f"T{i}" for i in range(1, 64)] + ["T64", "T65"]
    items = [
        (task_id, _touch_items(4, prefix=f"src/{task_id}"))
        for task_id in ids[:-1]
    ]
    items.append(("T65", "extra/one.py"))
    _scheduled_fixture(refused, _plan_from_touches(items), schedule_waves=[ids])

    _assert_json_refusal(_decision(refused, "--json"), "state-malformed")

    refused_total = git_repo / "wave-touches257-total"
    refused_total.mkdir()
    ids64_total = [f"T{i}" for i in range(1, 65)]
    items_total = [
        (task_id, _touch_items(4, prefix=f"src/{task_id}"))
        for task_id in ids64_total
    ]
    items_total[-1] = ("T64", _touch_items(5, prefix="src/T64"))
    _scheduled_fixture(refused_total, _plan_from_touches(items_total), schedule_waves=[ids64_total])
    _assert_json_refusal(_decision(refused_total, "--json"), "plan-status-illegal")
    _assert_human_refusal(_decision(refused_total), "maximum is 256")


def test_wave_decision_touch_glob_length_limit_is_folded_to_plan_status_illegal(git_repo):
    accepted = git_repo / "glob256"
    accepted.mkdir()
    glob256 = "a" * 253 + ".py"
    _scheduled_fixture(accepted, _plan_from_touches([("T1", glob256), ("T2", "b.py")]))
    assert _decision(accepted, "--json").returncode == 0

    refused = git_repo / "glob257"
    refused.mkdir()
    glob257 = "a" * 254 + ".py"
    _scheduled_fixture(refused, _plan_from_touches([("T1", glob257), ("T2", "b.py")]))

    _assert_json_refusal(_decision(refused, "--json"), "plan-status-illegal")
    _assert_human_refusal(_decision(refused), "longer than 256")


def test_wave_decision_reuses_admission_relations_for_pair_rows(monkeypatch):
    wave = ["T1", "T2", "T3", "T4"]
    touches = {
        task_id: [f"src/{task_id}/g{i}.py" for i in range(4)]
        for task_id in wave
    }
    calls = 0
    original = lc.globs_overlap

    def counted(left: str, right: str) -> bool:
        nonlocal calls
        calls += 1
        return original(left, right)

    monkeypatch.setattr(lc, "globs_overlap", counted)

    payload = lc._build_wave_decision(
        state={"schema_version": 2, "run_id": "run", "plan_hash": "hash"},
        touches=touches,
        wave_index=0,
        wave=wave,
        force_sequential=None,
    )

    assert payload["wave_disposition"] == "all-parallel-capable"
    assert calls == 6 * 4 * 4


def test_wave_decision_path_confinement_folds_escape_to_state_unreadable(git_repo, tmp_path):
    target = tmp_path / "outside-spec"
    target.mkdir()
    link = git_repo / "escape"
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")

    absolute_result = _run_lc("wave-decision", str(target), "--json", cwd=git_repo)
    dotdot_result = _run_lc("wave-decision", "subdir/../escape", "--json", cwd=git_repo)
    symlink_result = _run_lc("wave-decision", str(link), "--json", cwd=git_repo)

    _assert_json_refusal(absolute_result, "state-unreadable")
    _assert_json_refusal(dotdot_result, "state-unreadable")
    _assert_json_refusal(symlink_result, "state-unreadable")


@pytest.mark.parametrize(
    "resolution_failure",
    [OSError("symlink loop at private path"), RuntimeError("symlink loop at private path")],
)
def test_wave_decision_resolution_failures_use_json_refusal(
    monkeypatch, capsys, resolution_failure
):
    def fail_resolution(_raw):
        raise resolution_failure

    monkeypatch.setattr(lc, "_resolve_spec_dir", fail_resolution)
    args = SimpleNamespace(spec_dir="loop", json=True)

    assert lc.cmd_wave_decision(args) == 1
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {
        "payload_version": 1,
        "refusal": "state-unreadable",
        "detail": _WAVE_DECISION_PUBLIC_REFUSAL_DETAILS["state-unreadable"],
    }
    assert captured.err == ""
    assert "private path" not in captured.out


def test_wave_decision_does_not_touch_dispatch_gate_or_write_paths():
    source = LC_PATH.read_text(encoding="utf-8")
    parser_slice = source.split("# dispatch-decision (disabled)", 1)[1].split("# auto-parallel", 1)[0]
    assert "cmd_dispatch_decision" in parser_slice
    assert "wave-decision" not in parser_slice
    assert inspect.getsource(lc.cmd_dispatch_decision) == (
        "def cmd_dispatch_decision(args: argparse.Namespace) -> int:\n"
        "    return _disabled(\"dispatch-decision\")\n"
    )
    tree = ast.parse(source)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    reachable = set()
    pending = ["cmd_wave_decision"]
    called_symbols = set()
    string_constants = set()
    while pending:
        function_name = pending.pop()
        if function_name in reachable:
            continue
        reachable.add(function_name)
        for node in ast.walk(functions[function_name]):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_symbols.add(node.func.id)
                    if node.func.id in functions:
                        pending.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_symbols.add(node.func.attr)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                string_constants.add(node.value)

    forbidden_calls = {
        "dispatch_decision",
        "wave_is_disjoint",
        "write_state_atomic",
        "with_state_lock",
        "cmd_worktree",
    }
    assert forbidden_calls.isdisjoint(called_symbols)
    assert all("merge-tree" not in value for value in string_constants)


def test_init_state_has_auto_parallel_false(git_repo):
    spec = git_repo / "spec"
    spec.mkdir()
    run_id = str(uuid.uuid4())
    r = _run_lc("init", str(spec), "--run-id", run_id, cwd=git_repo)
    assert r.returncode == 0, r.stderr
    assert json.loads((spec / "state.json").read_text())["auto_parallel"] is False


def test_auto_parallel_verb_flips_both_ways(git_repo):
    # Phase 1: auto-parallel verb is disabled — exits non-zero.
    spec = git_repo / "spec"
    spec.mkdir()
    run_id = str(uuid.uuid4())
    _run_lc("init", str(spec), "--run-id", run_id, cwd=git_repo)
    r = _run_lc("auto-parallel", str(spec), cwd=git_repo)
    assert r.returncode != 0
    assert "disabled in Phase 1" in r.stderr


def test_auto_parallel_not_a_gate_input():
    import inspect
    assert "auto_parallel" not in str(inspect.signature(lc.dispatch_decision))


def test_merge_abort_backstop_free_of_auto_parallel():
    import inspect
    # The merge-abort backstop cannot be influenced by the flag.
    assert "auto_parallel" not in inspect.getsource(lc.cmd_worktree_merge)


def test_detect_unknown_deps_has_exactly_one_call_site():
    """The unknown-dependency refusal must keep exactly one call site.

    Its mutation proof works by deleting that call and watching both the CLI and
    the amendment suites go red. A second, defensive call anywhere else would
    still refuse on its own, so the deletion would leave every test green and the
    proof would pass for a guard that is no longer there. This check is what
    stops that happening silently: it reads the shipped module source and counts
    calls outside the definition.
    """
    source = LC_PATH.read_text(encoding="utf-8")
    call_lines = [
        line.strip()
        for line in source.splitlines()
        if "detect_unknown_deps(" in line and not line.lstrip().startswith("def ")
    ]
    assert len(call_lines) == 1, (
        "detect_unknown_deps must have exactly one call site; found "
        f"{len(call_lines)}: {call_lines}"
    )
    assert "scan_task_ids=" in call_lines[0], (
        "the scan set must be passed by keyword, so it cannot be mistaken for "
        f"the resolution set: {call_lines[0]}"
    )


# ── one owner for the task-section boundary walk ────────────────────────────

# Plans exercising every way the boundary walk can be got wrong: both heading
# levels, a task with no `Depends on:` line, the field on the final task, a
# `Depends on:` line in the preamble that belongs to no task, CRLF line
# endings, ranges, cross-spec markers, and parenthetical prose naming both a
# present and an absent ID.
AGREEMENT_PLANS = {
    "level-2 headings": """\
# Plan

## T1
**Depends on:** none

## T2
**Depends on:** T1

## T3
**Depends on:** T1, T2
""",
    "level-3 headings": """\
# Plan

### T1
**Depends on:** none

### T2
**Depends on:** T1
""",
    "task with no depends line": """\
# Plan

## T1
Some prose and no declaration at all.

## T2
**Depends on:** T1
""",
    # The case that makes a divergent boundary observable at all. T1 declares
    # nothing and T2 names an ID the plan does not contain, so a walk that
    # searched past T1's section end would hand T2's `Depends on:` line to T1
    # and report an unknown dependency against the wrong task. Without an
    # absent ID here the misattribution resolves to a known task and stays
    # invisible to the agreement property.
    "no depends line, next task names an absent id": """\
# Plan

## T1
Some prose and no declaration at all.

## T2
**Depends on:** T99
""",
    "field on the final task": """\
# Plan

## T1
**Depends on:** none

## T2
**Depends on:** T1
""",
    "preamble depends line owned by no task": """\
# Plan

**Depends on:** T99

## T1
**Depends on:** none
""",
    "crlf line endings": "# Plan\r\n\r\n## T1\r\n**Depends on:** none\r\n\r\n## T2\r\n**Depends on:** T1\r\n",
    "range and cross-spec marker": """\
# Plan

## T1
**Depends on:** none

## T2
**Depends on:** none

## T3
**Depends on:** T1-T2, spec:other-spec/T4
""",
    "parenthetical names a present id": """\
# Plan

## T1
**Depends on:** none

## T2
**Depends on:** none

## T3
**Depends on:** T1 (deliberately not ordered against T2)
""",
    "parenthetical names an absent id": """\
# Plan

## T1
**Depends on:** none

## T2
**Depends on:** T1 (supersedes the T77 approach)
""",
    "unknown dependency": """\
# Plan

## T1
**Depends on:** T42
""",
    "no tasks at all": "# Plan\n\nProse only.\n",
}


def test_boundary_walk_has_exactly_one_owner():
    """Only `walk_task_sections` may walk the task-heading matches.

    The registered defect was four functions each re-deriving which task owns a
    `Depends on:` line. Consolidation alone does not stay consolidated — the
    next caller that needs section boundaries can quietly add a fifth walk, and
    every behavioural test would still pass. This reads the shipped source and
    refuses a second `finditer` on the heading grammar.
    """
    source = LC_PATH.read_text(encoding="utf-8")
    walk_lines = [
        line.strip()
        for line in source.splitlines()
        if "TASK_HEADING_RE.finditer" in line
    ]
    assert len(walk_lines) == 1, (
        "TASK_HEADING_RE.finditer must appear exactly once, inside "
        f"walk_task_sections; found {len(walk_lines)}: {walk_lines}"
    )
    owner = source.split("def walk_task_sections")[1].split("\ndef ")[0]
    assert "TASK_HEADING_RE.finditer" in owner, (
        "the single heading walk moved out of walk_task_sections"
    )
    # The `Depends on:` field lookup is single-homed for the same reason.
    depends_lines = [
        line.strip()
        for line in source.splitlines()
        if "DEPENDS_LINE_RE.search" in line
    ]
    assert len(depends_lines) == 1, (
        "DEPENDS_LINE_RE.search must appear exactly once, inside "
        f"section_depends_field; found {len(depends_lines)}: {depends_lines}"
    )


def test_refusal_and_graph_agree_on_every_declared_id():
    """`detect_unknown_deps` and `parse_plan` partition the same field.

    This is the agreement the register entry asks for, stated as a property
    rather than an assertion about the code's shape: for each task, the IDs the
    field declares are exactly the edges the graph carries plus the IDs the
    refusal reports unknown. A boundary walk that attributed a line to the
    wrong task would move an ID out of one side without moving it into the
    other, and this fails.

    Scope: plans whose task IDs are unique. The property does not hold when a
    plan repeats a heading ID, because `parse_plan` keys its dependency map by
    task ID and the later section overwrites the earlier one. That is a real
    hazard rather than an artefact of this test — see
    `test_duplicate_task_heading_drops_the_earlier_sections_edges`.
    """
    for label, text in AGREEMENT_PLANS.items():
        ordered, deps = lc.parse_plan(text)
        unknown_by_task: dict[str, set[str]] = {}
        for task, dep in lc.detect_unknown_deps(text):
            unknown_by_task.setdefault(task, set()).add(dep)

        # Every task the refusal talks about is a task the graph knows.
        assert set(unknown_by_task) <= set(ordered), label

        for section in lc.walk_task_sections(text):
            field = lc.section_depends_field(text, section)
            declared = lc._local_dep_ids(field) if field is not None else set()
            carried = deps[section.task_id]
            reported = unknown_by_task.get(section.task_id, set())
            assert carried | reported == declared, (
                f"{label}: {section.task_id} declares {sorted(declared)} but the "
                f"graph carries {sorted(carried)} and the refusal reports "
                f"{sorted(reported)}"
            )
            # The two halves are disjoint: an ID is an edge or unknown, never both.
            assert not (carried & reported), f"{label}: {section.task_id}"


def test_every_boundary_consumer_agrees_on_the_task_set():
    """The four former walkers still see the same tasks in the same order."""
    for label, text in AGREEMENT_PLANS.items():
        ordered, _ = lc.parse_plan(text)
        walked = [s.task_id for s in lc.walk_task_sections(text)]
        assert walked == ordered, label
        assert list(lc._task_sections(text)) == ordered, label
        assert set(lc.parse_touches_by_task(text)) <= set(ordered), label


def test_preamble_depends_line_belongs_to_no_task():
    """A declaration above the first heading is owned by nobody.

    `T99` is in no task's section, so it is neither an edge nor an unknown-dep
    refusal. The field that carries this is `body_start`: a walk that opened the
    first task's body at the top of the file instead of just past its heading
    would hand this line to T1 and refuse the plan. (Rewinding `body_start` to
    the heading's own start is *not* enough to break it — the preamble sits
    above the heading either way, so only the first-section-opens-at-zero error
    shows up here.)
    """
    text = AGREEMENT_PLANS["preamble depends line owned by no task"]
    ordered, deps = lc.parse_plan(text)
    assert ordered == ["T1"]
    assert deps["T1"] == set()
    assert lc.detect_unknown_deps(text) == []


def test_parenthetical_ids_stay_commentary_after_consolidation():
    """The deliberate asymmetry survives: the field is read up to its first `(`.

    Both directions matter. An ID in parenthetical prose that names a real task
    must not become an edge, and one that names no task must not become an
    unknown-dependency refusal. Consolidating the walk must not widen either.
    """
    present = AGREEMENT_PLANS["parenthetical names a present id"]
    _, deps = lc.parse_plan(present)
    assert deps["T3"] == {"T1"}, "T2 sits after the '(' and is not an edge"
    assert lc.detect_unknown_deps(present) == []

    absent = AGREEMENT_PLANS["parenthetical names an absent id"]
    _, deps = lc.parse_plan(absent)
    assert deps["T2"] == {"T1"}
    assert lc.detect_unknown_deps(absent) == [], (
        "T77 sits after the '(' — commentary, so not reported unknown"
    )


def test_unknown_dependency_is_still_reported():
    """The refusal has not been widened away by the consolidation."""
    text = AGREEMENT_PLANS["unknown dependency"]
    assert lc.detect_unknown_deps(text) == [("T1", "T42")]


def test_task_section_text_opens_at_its_own_heading():
    """Each canonical section begins with its own heading, not the file's top.

    `_task_sections` feeds the amendment pins, so the section text is
    hash-sensitive. The `start` offset is what makes it exact, and nothing else
    in the suite reads it: with `start` forced to 0 for the first task, the
    whole pack suite stayed green while T1's pinned text silently absorbed the
    plan's preamble. This is the check that fails instead.
    """
    text = AGREEMENT_PLANS["preamble depends line owned by no task"]
    sections = lc._task_sections(text)
    assert set(sections) == {"T1"}
    assert sections["T1"].startswith("## T1"), sections["T1"]
    assert "# Plan" not in sections["T1"], "the preamble leaked into T1's section"

    multi = lc._task_sections(AGREEMENT_PLANS["level-2 headings"])
    for task_id, body in multi.items():
        assert body.startswith(f"## {task_id}"), (task_id, body)


_DUPLICATE_HEADING_PLAN = """\
# Plan

## T1
**Depends on:** none

## T2
**Depends on:** T1

## T2 evidence (observed output)

Prose recording what T2 produced. No declaration of its own.
"""


def test_duplicate_task_heading_drops_the_earlier_sections_edges():
    """Pins today's behaviour when one ID heads two sections: last section wins.

    `parse_plan` keys its dependency map by task ID, so the second `## T2`
    section — an evidence write-up with no `Depends on:` line — overwrites the
    real T2 section's edges, and T2 schedules as if it depended on nothing.
    Nothing refuses this on a fresh `schedule`: `_task_sections` does raise on
    the duplicate, but only `validate_completed_task_sections` calls it, and
    that returns early unless the run already has completed-task pins.

    This is pinned, not fixed. Making `schedule` refuse a duplicate heading
    changes a published guard's refusal set and needs its own specification;
    the check exists so the behaviour is visible and any change to it is
    deliberate.
    """
    ordered, deps = lc.parse_plan(_DUPLICATE_HEADING_PLAN)
    assert ordered == ["T1", "T2", "T2"]
    assert deps["T2"] == set(), "the evidence section's empty edge set wins"

    waves, _ = lc.topological_waves(ordered, deps)
    assert "T2" in waves[0], "T2 schedules beside the T1 it declared it needs"

    # The refusal path does catch it, but only once pins exist.
    with pytest.raises(ValueError, match="duplicate task section T2"):
        lc._task_sections(_DUPLICATE_HEADING_PLAN)
    assert lc.validate_completed_task_sections(_DUPLICATE_HEADING_PLAN, {}) is None


def test_agreement_property_holds_when_ids_are_unique():
    """The duplicate case is the only exception to the agreement property."""
    ordered, _ = lc.parse_plan(_DUPLICATE_HEADING_PLAN)
    assert len(ordered) != len(set(ordered)), "fixture must repeat an ID"
    for label, text in AGREEMENT_PLANS.items():
        ids = [s.task_id for s in lc.walk_task_sections(text)]
        assert len(ids) == len(set(ids)), f"{label}: corpus must keep IDs unique"


# ── the record lifecycle across `schedule` ─────────────────────────────────
#
# Contract: § The record
# lifecycle. `schedule` owns two of the three removal paths: a partition-
# changing re-schedule drops stale records, a partition-preserving one keeps
# them.

_LIFECYCLE_PLAN = """\
### T1: first
**Depends on:** none
### T2: second
**Depends on:** T1
"""


def _lifecycle_fixture(tmp_path: Path) -> str:
    """A scheduled cohort holding one receipt for T1 in wave 0."""
    run_id = _seed_state(tmp_path)
    (tmp_path / "plan.md").write_text(_LIFECYCLE_PLAN, encoding="utf-8", newline="\n")
    r = _run_lc("schedule", str(tmp_path), "--expect-run-id", run_id, cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    r = _run_lc(
        "dispatch-receipt", str(tmp_path), "--task", "T1", "--wave-index", "0",
        "--receipt", "--expect-run-id", run_id, cwd=tmp_path,
    )
    assert r.returncode == 0, r.stderr
    return run_id


def _state_of(tmp_path: Path) -> dict:
    return json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))


def test_schedule_creates_the_receipts_container_when_absent(git_repo):
    """`_seed_state` writes a two-key state, which is the pre-receipts shape."""
    r = _schedule(git_repo, _PLAN)
    assert r.returncode == 0, r.stderr
    state = _state_of(git_repo)
    assert lc.RECEIPTS_KEY in state, "schedule must leave the container present"
    assert state[lc.RECEIPTS_KEY] == {}


def test_schedule_keeps_a_record_when_the_partition_is_unchanged(git_repo):
    """`plan_hash` moves, the partition does not — so the record must survive.

    The intervening edit is what discriminates: without it a no-op re-schedule
    satisfies the assertion, and an implementation keyed on `plan_hash` rather
    than on the partition digest stays green.
    """
    run_id = _lifecycle_fixture(git_repo)
    before = _state_of(git_repo)
    edited = _LIFECYCLE_PLAN + "\nProse the contract hash must notice.\n"
    (git_repo / "plan.md").write_text(edited, encoding="utf-8", newline="\n")
    r = _run_lc("schedule", str(git_repo), "--expect-run-id", run_id, cwd=git_repo)
    assert r.returncode == 0, r.stderr
    after = _state_of(git_repo)
    assert after["plan_hash"] != before["plan_hash"], "the edit must move plan_hash"
    assert after["schedule_waves"] == before["schedule_waves"], "partition must hold"
    assert after[lc.RECEIPTS_KEY] == before[lc.RECEIPTS_KEY], (
        "a partition-preserving re-schedule must leave the record unchanged"
    )
    assert after[lc.RECEIPTS_KEY], "fixture must have written a record"


def test_schedule_drops_a_record_when_the_partition_changes(git_repo):
    run_id = _lifecycle_fixture(git_repo)
    superseded = next(iter(_state_of(git_repo)[lc.RECEIPTS_KEY]))
    (git_repo / "plan.md").write_text(
        _LIFECYCLE_PLAN + "### T3: third\n**Depends on:** T2\n",
        encoding="utf-8", newline="\n",
    )
    r = _run_lc("schedule", str(git_repo), "--expect-run-id", run_id, cwd=git_repo)
    assert r.returncode == 0, r.stderr
    after = _state_of(git_repo)
    assert len(after["schedule_waves"]) == 3, "the partition must have changed"
    assert superseded not in after[lc.RECEIPTS_KEY], (
        "no record may survive under the superseded partition digest"
    )
    assert after[lc.RECEIPTS_KEY] == {}
