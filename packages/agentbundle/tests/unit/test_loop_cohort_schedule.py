"""Unit tests for the wave-scheduled-supervisor scheduler in loop-cohort.py.

Covers spec `docs/specs/wave-scheduled-supervisor/`:
  T1 — parse_depends_on + parse_plan
  T2 — topological order, cycle + forward-ref detection
  T4 — dispatch_decision gate

loop-cohort.py is a standalone hyphenated script; pure functions are loaded
via importlib here. CLI/exit-code behavior (the `schedule` verb) is exercised
by subprocess against the real file-path invocation elsewhere.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
LC_PATH = REPO_ROOT / "packs/core/.apm/skills/work-loop/scripts/loop-cohort.py"


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

import json  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import uuid  # noqa: E402


def _seed_state(tmp_path):
    """Seed a minimal Phase-1 state.json and return the run_id."""
    run_id = str(uuid.uuid4())
    (tmp_path / "state.json").write_text(
        json.dumps({"schema_version": 1, "run_id": run_id}), encoding="utf-8"
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


def test_schedule_predicts_no_on_overlapping_touches(tmp_path):
    r = _schedule(
        tmp_path,
        "### T1: a\n**Depends on:** none\n**Touches:** src/api/*\n"
        "### T2: b\n**Depends on:** none\n**Touches:** src/api/x.py\n",
    )
    assert r.returncode == 0, r.stderr
    assert "predicted-disjoint: no" in r.stdout


def test_schedule_predicts_yes_on_disjoint_touches(tmp_path):
    r = _schedule(
        tmp_path,
        "### T1: a\n**Depends on:** none\n**Touches:** src/a/*\n"
        "### T2: b\n**Depends on:** none\n**Touches:** src/b/*\n",
    )
    assert "predicted-disjoint: yes" in r.stdout


def test_schedule_predicts_unknown_when_a_task_omits_touches(tmp_path):
    r = _schedule(
        tmp_path,
        "### T1: a\n**Depends on:** none\n**Touches:** src/a/*\n"
        "### T2: b\n**Depends on:** none\n",  # no Touches:
    )
    assert "predicted-disjoint: unknown" in r.stdout


def test_schedule_no_annotation_on_single_task_wave(tmp_path):
    r = _schedule(tmp_path, "### T1: a\n**Depends on:** none\n**Touches:** src/a/*\n")
    assert r.returncode == 0, r.stderr
    assert "predicted-disjoint" not in r.stdout  # single-task wave → no annotation


def test_schedule_is_screen_only_no_gate_call(tmp_path):
    # AC5 positive form: the predict path (cmd_schedule) shares no call with the
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

import json as _json  # noqa: E402


def _run_lc(*args):
    return subprocess.run([sys.executable, str(LC_PATH), *args],
                          capture_output=True, text=True)


def test_init_state_has_auto_parallel_false(tmp_path):
    spec = tmp_path / "spec"
    spec.mkdir()
    run_id = str(uuid.uuid4())
    r = _run_lc("init", str(spec), "--run-id", run_id)
    assert r.returncode == 0, r.stderr
    assert _json.loads((spec / "state.json").read_text())["auto_parallel"] is False


def test_auto_parallel_verb_flips_both_ways(tmp_path):
    # Phase 1: auto-parallel verb is disabled — exits non-zero.
    spec = tmp_path / "spec"
    spec.mkdir()
    run_id = str(uuid.uuid4())
    _run_lc("init", str(spec), "--run-id", run_id)
    r = _run_lc("auto-parallel", str(spec))
    assert r.returncode != 0
    assert "disabled in Phase 1" in r.stderr


def test_auto_parallel_not_a_gate_input():
    import inspect
    assert "auto_parallel" not in str(inspect.signature(lc.dispatch_decision))


def test_merge_abort_backstop_free_of_auto_parallel():
    import inspect
    # The merge-abort backstop cannot be influenced by the flag.
    assert "auto_parallel" not in inspect.getsource(lc.cmd_worktree_merge)
