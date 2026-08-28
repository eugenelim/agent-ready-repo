#!/usr/bin/env python3
"""API ≡ CLI parity for every guard decision (T6).

The whole risk of putting one implementation behind two surfaces is that the two
drift: a CLI keeps its old behaviour while the engine gets new behaviour, or vice
versa, and every individual test still passes because each only ever looks at one
side. A parity table is the shape that catches it — one fixture, two callers, one
assertion that they agree.

Two independent comparisons per row, and both are needed:

  1. **Verdict parity.** `GuardResult.ok == (cli_returncode == 0)`. This is what
     stops the engine and the CLI disagreeing about whether a transition is legal.

  2. **Message fidelity against T0's goldens.** The CLI's normalized streams must
     equal what the PRE-CHANGE tool produced — not what the current API produces.
     Comparing the CLI to the API would be comparing the change against itself, the
     antipattern in `docs/knowledge/topics/
     a-test-that-moves-with-the-code-cannot-catch-the-code-being-wrong.json`.

Rows whose verdict this change intentionally alters carry a `change_reason` from
`golden_support.CHANGE_REASONS` and are asserted against their recorded `after`.
Every other row is asserted against `before`.

Scoped to decisions, not lifecycle walks: `test_loop_engine.py` and
`test_loop_cohort.py` already drive the walks, and duplicating them here would add
cost without adding drift protection.

Run with pytest.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import golden_support as gs
import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"
GUARDS = SCRIPTS / "_loop_guards.py"
COHORT = SCRIPTS / "loop-cohort.py"
CHECK_STATUS = SCRIPTS / "check-spec-status.py"

# Where the spec dir goes in an argv. `loop-cohort` takes its verb FIRST and the
# spec dir after it; `check-spec-status` takes the spec dir first. Writing the
# position explicitly, rather than inferring it per tool, is what stops the argv
# coming out inverted — which it did on the first attempt, and every cohort row
# failed with an argparse "invalid choice" that had nothing to do with parity.
SPEC = "<SPEC_DIR>"

RID = "11111111-2222-3333-4444-555555555555"
OTHER_RID = "99999999-8888-7777-6666-555555555555"

SPEC_MD = """# Spec: fixture

- **Status:** {status} <!-- Draft | Approved | Implementing | Shipped | Archived -->

## Acceptance Criteria

- [ ] AC1
"""
PLAN_MD = """# Plan: fixture

- **Status:** {status} <!-- Drafting | Approved | Executing | Done -->

## T1 First

**Depends on:** none

**Touches:** `a.py`
"""


@pytest.fixture(scope="module")
def guards():
    spec = importlib.util.spec_from_file_location("_loop_guards_parity", str(GUARDS))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def goldens() -> dict:
    data = json.loads(gs.GOLDEN_CLI_STREAMS.read_text(encoding="utf-8"))
    return {row["key"]: row for row in data["rows"]}


def _state(**over) -> dict:
    st = {
        "schema_version": 1, "run_id": RID, "feature": "fixture",
        "plan_review_status": "pending",
        "approved_spec_hash": None, "approved_plan_hash": None, "plan_hash": None,
        "schedule_waves": [], "current_wave_index": 0,
        "implementation_retry_count": 0, "review_round_count": 0,
        "review_retry_count": 0, "finding_fingerprints": [],
        "previous_finding_fingerprints": [],
        "max_implementation_retries": 5, "max_review_retries": 5,
    }
    st.update(over)
    return st


def build(guards, root: Path, name: str, *, spec_status="Approved", plan_status="Approved",
          approved=False, waves=None, no_state=False, no_spec=False, no_plan=False,
          spec_body=None, post=None, **over) -> Path:
    """ONE fixture builder, used by both halves of every row.

    That is the load-bearing detail: if the API and the CLI were given
    separately-constructed directories, a difference in the fixtures could masquerade
    as agreement — or as drift.

    `post` is a callable run AFTER the state file is written, mirroring how the
    generator built the drift and missing-artifact cases: the approved hashes must pin
    the clean body, and only then is the artifact drifted, deleted, or regressed. A
    kwarg that mutated before the pin would make the hash match the damage and the
    guard pass, so these cases cannot be expressed as pre-build kwargs.
    """
    d = root / name
    d.mkdir(parents=True)
    if not no_spec:
        (d / "spec.md").write_text(
            spec_body if spec_body is not None else SPEC_MD.format(status=spec_status),
            encoding="utf-8")
    if not no_plan:
        (d / "plan.md").write_text(PLAN_MD.format(status=plan_status), encoding="utf-8")
    if not no_state:
        if approved:
            over.setdefault("plan_review_status", "approved")
            over.setdefault("approved_spec_hash", guards.sha256_canonical_contract(d / "spec.md"))
            over.setdefault("approved_plan_hash", guards.sha256_canonical_contract(d / "plan.md"))
            over.setdefault("plan_hash", guards.sha256_canonical_contract(d / "plan.md"))
            over.setdefault("schedule_waves", waves if waves is not None else [["T1"], ["T2"]])
        (d / "state.json").write_text(json.dumps(_state(**over), indent=2), encoding="utf-8")
    if post is not None:
        post(d)
    return d


# ── post-build fixture mutations, matching the generator's construction ────

def _drift_spec(d: Path) -> None:
    (d / "spec.md").write_text(SPEC_MD.format(status="Approved") + "\ndrifted\n",
                               encoding="utf-8")


def _drift_plan(d: Path) -> None:
    (d / "plan.md").write_text(PLAN_MD.format(status="Approved") + "\ndrifted\n",
                               encoding="utf-8")


def _unlink_spec(d: Path) -> None:
    (d / "spec.md").unlink()


def _unlink_plan(d: Path) -> None:
    (d / "plan.md").unlink()


def _regress_spec_status(d: Path) -> None:
    (d / "spec.md").write_text(SPEC_MD.format(status="Draft"), encoding="utf-8")


def _nest_spec_md(d: Path) -> None:
    """A `--file sub/spec.md` target that really resolves inside `spec_dir`.

    The narrowing AC9 adds is about a multi-component path, not an escaping one — so
    the fixture has to put a genuine `spec.md` at `sub/spec.md`, or the refusal could
    be coming from confinement instead of the component rule.
    """
    sub = d / "sub"
    sub.mkdir()
    (sub / "spec.md").write_text(SPEC_MD.format(status="Approved"), encoding="utf-8")


def run_cli(script: Path, argv: list, cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(script), *[str(a) for a in argv]],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=False, cwd=str(cwd),
    )
    return proc.returncode, proc.stdout, proc.stderr


# ── the table ──────────────────────────────────────────────────────────────
#
# (golden key, fixture kwargs, api call, cli script, cli argv-after-spec-dir)
#
# The golden key ties each row to T0's pre-change capture, so a row that loses its
# key fails loudly rather than quietly asserting nothing.

def _rows():
    C, S = "cohort", "status"
    return [
        # ── run-ID identity ────────────────────────────────────────────────
        ("identity/ok", {},
         lambda g, d: g.check_identity(d, expect_run_id=RID),
         C, ["identity", SPEC, "--expect-run-id", RID]),
        ("identity/run-id-mismatch", {},
         lambda g, d: g.check_identity(d, expect_run_id=OTHER_RID),
         C, ["identity", SPEC, "--expect-run-id", OTHER_RID]),
        ("identity/unsupported-schema", {"schema_version": 99},
         lambda g, d: g.check_identity(d, expect_run_id=RID),
         C, ["identity", SPEC, "--expect-run-id", RID]),
        ("identity/absent-state", {"no_state": True},
         lambda g, d: g.check_identity(d, expect_run_id=RID),
         C, ["identity", SPEC, "--expect-run-id", RID]),

        # ── schedule currency ──────────────────────────────────────────────
        # `_dir_name` pins the fixture directory's basename for rows whose SUCCESS
        # message interpolates `spec_dir.name`. gs.normalize() rewrites paths and
        # digests but cannot touch a bare basename, and re-capturing the goldens to
        # match a new name is exactly what must never happen — so the table carries
        # the generator's name instead.
        ("schedule-check-current/ok", {"approved": True, "_dir_name": "sched-ok"},
         lambda g, d: g.check_schedule_current(d),
         C, ["schedule", "check-current", SPEC]),
        ("schedule-check-current/plan-hash-drift", {"approved": True, "plan_hash": "0" * 64},
         lambda g, d: g.check_schedule_current(d),
         C, ["schedule", "check-current", SPEC]),
        ("schedule-check-current/plan-status-illegal",
         {"approved": True, "plan_status_override": "Drafting"},
         lambda g, d: g.check_schedule_current(d),
         C, ["schedule", "check-current", SPEC]),
        ("schedule-check-current/absent-state", {"no_state": True},
         lambda g, d: g.check_schedule_current(d),
         C, ["schedule", "check-current", SPEC]),

        # ── plan currency, with and without --require-schedule ─────────────
        ("plan-check-current/pending", {},
         lambda g, d: g.check_plan_current(d),
         C, ["plan", "check-current", SPEC]),
        ("plan-check-current/ok", {"approved": True, "_dir_name": "plan-ok"},
         lambda g, d: g.check_plan_current(d),
         C, ["plan", "check-current", SPEC]),
        ("plan-check-current/ok-require-schedule",
         {"approved": True, "_dir_name": "plan-ok"},
         lambda g, d: g.check_plan_current(d, require_schedule=True),
         C, ["plan", "check-current", SPEC, "--require-schedule"]),
        ("plan-check-current/empty-waves-require-schedule", {"approved": True, "waves": []},
         lambda g, d: g.check_plan_current(d, require_schedule=True),
         C, ["plan", "check-current", SPEC, "--require-schedule"]),
        ("plan-check-current/wave-index-out-of-range",
         {"approved": True, "current_wave_index": 9},
         lambda g, d: g.check_plan_current(d, require_schedule=True),
         C, ["plan", "check-current", SPEC, "--require-schedule"]),
        ("plan-check-current/plan-hash-not-scheduled",
         {"approved": True, "plan_hash": "0" * 64},
         lambda g, d: g.check_plan_current(d, require_schedule=True),
         C, ["plan", "check-current", SPEC, "--require-schedule"]),

        # ── phase retry caps ───────────────────────────────────────────────
        ("check/implement-ok", {},
         lambda g, d: g.check_phase(d, phase="implement"),
         C, ["check", SPEC, "--phase", "implement"]),
        ("check/implement-absent-state", {"no_state": True},
         lambda g, d: g.check_phase(d, phase="implement"),
         C, ["check", SPEC, "--phase", "implement"]),
        ("check/review-under-cap", {"review_retry_count": 1},
         lambda g, d: g.check_phase(d, phase="review"),
         C, ["check", SPEC, "--phase", "review"]),
        ("check/review-at-cap", {"review_retry_count": 5},
         lambda g, d: g.check_phase(d, phase="review"),
         C, ["check", SPEC, "--phase", "review"]),
        ("check/gates-failed-under-cap", {"implementation_retry_count": 1},
         lambda g, d: g.check_phase(d, phase="gates-failed"),
         C, ["check", SPEC, "--phase", "gates-failed"]),
        ("check/gates-failed-at-cap", {"implementation_retry_count": 5},
         lambda g, d: g.check_phase(d, phase="gates-failed"),
         C, ["check", SPEC, "--phase", "gates-failed"]),
        ("check/unsupported-schema-non-implement", {"schema_version": 99},
         lambda g, d: g.check_phase(d, phase="review"),
         C, ["check", SPEC, "--phase", "review"]),
        # AC16: coercible counters that int() absorbed and AC8 now refuses.
        ("check/review-string-typed-count", {"review_retry_count": "1"},
         lambda g, d: g.check_phase(d, phase="review"),
         C, ["check", SPEC, "--phase", "review"]),
        ("check/review-float-typed-count", {"review_retry_count": 1.7},
         lambda g, d: g.check_phase(d, phase="review"),
         C, ["check", SPEC, "--phase", "review"]),
        ("check/review-negative-count", {"review_retry_count": -3},
         lambda g, d: g.check_phase(d, phase="review"),
         C, ["check", SPEC, "--phase", "review"]),

        # ── wave checks ────────────────────────────────────────────────────
        ("wave-check/more-ok", {"approved": True},
         lambda g, d: g.check_wave(d, expect="more"),
         C, ["wave", "check", SPEC, "--expect", "more"]),
        ("wave-check/more-ok-with-index", {"approved": True},
         lambda g, d: g.check_wave(d, expect="more", wave_index=0),
         C, ["wave", "check", SPEC, "--expect", "more", "--wave-index", "0"]),
        ("wave-check/last-not-last", {"approved": True},
         lambda g, d: g.check_wave(d, expect="last"),
         C, ["wave", "check", SPEC, "--expect", "last"]),
        ("wave-check/index-mismatch", {"approved": True},
         lambda g, d: g.check_wave(d, expect="more", wave_index=1),
         C, ["wave", "check", SPEC, "--expect", "more", "--wave-index", "1"]),
        ("wave-check/last-ok", {"approved": True, "current_wave_index": 1},
         lambda g, d: g.check_wave(d, expect="last"),
         C, ["wave", "check", SPEC, "--expect", "last"]),
        ("wave-check/more-no-more", {"approved": True, "current_wave_index": 1},
         lambda g, d: g.check_wave(d, expect="more"),
         C, ["wave", "check", SPEC, "--expect", "more"]),
        ("wave-check/absent-state", {"no_state": True},
         lambda g, d: g.check_wave(d, expect="last"),
         C, ["wave", "check", SPEC, "--expect", "last"]),

        # ── spec / plan status ─────────────────────────────────────────────
        ("check-spec-status/default-shipped-ok", {"spec_status": "Shipped"},
         lambda g, d: g.check_artifact_status(d, filename="spec.md", expect="Shipped"),
         S, [SPEC]),
        ("check-spec-status/default-draft-refuses", {"spec_status": "Draft"},
         lambda g, d: g.check_artifact_status(d, filename="spec.md", expect="Shipped"),
         S, [SPEC]),
        ("check-spec-status/expect-approved-ok", {"spec_status": "Approved"},
         lambda g, d: g.check_artifact_status(d, filename="spec.md", expect="Approved"),
         S, [SPEC, "--expect", "Approved"]),
        ("check-spec-status/expect-approved-plan-ok", {"spec_status": "Approved"},
         lambda g, d: g.check_artifact_status(d, filename="plan.md", expect="Approved"),
         S, [SPEC, "--expect", "Approved", "--file", "plan.md"]),
        ("check-spec-status/absent-spec", {"no_spec": True},
         lambda g, d: g.check_artifact_status(d, filename="spec.md", expect="Approved"),
         S, [SPEC, "--expect", "Approved"]),
        ("check-spec-status/no-status-line", {"spec_body": "# Spec\n\nno status here\n"},
         lambda g, d: g.check_artifact_status(d, filename="spec.md", expect="Shipped"),
         S, [SPEC]),
        ("check-spec-status/file-escapes-spec-dir", {},
         lambda g, d: g.check_artifact_status(d, filename="../outside.md", expect="Shipped"),
         S, [SPEC, "--file", "../outside.md"]),

        # ── AC9's `--file` narrowing, at the CLI boundary ───────────────────
        # A multi-component path that resolves INSIDE spec_dir. Previously accepted
        # (before.returncode == 0); now refused. Expressible declaratively, so it
        # belongs in the table rather than on the exemption list — it is a narrowing
        # of a shipped CLI's accepted inputs, which is exactly the kind of change
        # that needs its artifact at the CLI boundary.
        ("check-spec-status/file-multi-component-inside", {"post": _nest_spec_md},
         lambda g, d: g.check_artifact_status(d, filename="sub/spec.md", expect="Approved"),
         S, [SPEC, "--expect", "Approved", "--file", "sub/spec.md"]),

        # ── rows the golden set recorded but the table never compared ───────
        # Six of these are the highest-value messages in the tool: the two drift
        # reasons carry `_BOTH_CAUSES` plus two digests, which is the largest authored
        # string here and the most likely to be mangled by a relocation. The
        # `_dir_name` values match the generator's, because several messages
        # interpolate `spec_dir.name` and `normalize()` cannot rewrite a bare basename.
        ("identity/ok-json", {"_dir_name": "id-ok"},
         lambda g, d: g.check_identity(d, expect_run_id=RID),
         C, ["identity", SPEC, "--expect-run-id", RID, "--json"]),
        ("plan-check-current/spec-drift",
         {"approved": True, "_dir_name": "plan-specdrift", "post": _drift_spec},
         lambda g, d: g.check_plan_current(d),
         C, ["plan", "check-current", SPEC]),
        ("plan-check-current/plan-drift",
         {"approved": True, "_dir_name": "plan-plandrift", "post": _drift_plan},
         lambda g, d: g.check_plan_current(d),
         C, ["plan", "check-current", SPEC]),
        ("plan-check-current/missing-spec",
         {"approved": True, "_dir_name": "plan-nospec", "post": _unlink_spec},
         lambda g, d: g.check_plan_current(d),
         C, ["plan", "check-current", SPEC]),
        ("plan-check-current/missing-plan",
         {"approved": True, "_dir_name": "plan-noplan", "post": _unlink_plan},
         lambda g, d: g.check_plan_current(d),
         C, ["plan", "check-current", SPEC]),
        ("plan-check-current/status-regressed",
         {"approved": True, "_dir_name": "plan-statusregress", "post": _regress_spec_status},
         lambda g, d: g.check_plan_current(d),
         C, ["plan", "check-current", SPEC]),
        ("schedule-check-current/missing-plan",
         {"approved": True, "_dir_name": "sched-noplan", "post": _unlink_plan},
         lambda g, d: g.check_schedule_current(d),
         C, ["schedule", "check-current", SPEC]),
    ]


@pytest.mark.parametrize(
    "key,kwargs,api,tool,argv", _rows(), ids=[r[0] for r in _rows()]
)
def test_api_and_cli_agree(key, kwargs, api, tool, argv, guards, goldens, git_repo) -> None:
    golden = goldens.get(key)
    assert golden is not None, (
        f"{key} has no golden row. Every parity row must tie to T0's pre-change "
        "capture, or it asserts nothing about message fidelity."
    )

    # One fixture, built once, used by both halves.
    kwargs = dict(kwargs)
    plan_status = kwargs.pop("plan_status_override", "Approved")
    dir_name = kwargs.pop("_dir_name", "spec")
    spec_dir = build(guards, git_repo, dir_name, plan_status=plan_status, **kwargs)

    api_result = api(guards, spec_dir)
    script = COHORT if tool == "cohort" else CHECK_STATUS
    resolved_argv = [spec_dir if a == SPEC else a for a in argv]
    assert any(a is spec_dir for a in resolved_argv), (
        f"{key}: argv has no {SPEC} placeholder, so the CLI would never see the fixture"
    )
    rc, out, err = run_cli(script, resolved_argv, cwd=git_repo)

    # ── 1. verdict parity ──────────────────────────────────────────────────
    assert api_result.ok == (rc == 0), (
        f"{key}: the API and the CLI disagree on the verdict.\n"
        f"  API: ok={api_result.ok} reason={api_result.reason!r}\n"
        f"  CLI: rc={rc} stderr={err.strip()!r}\n"
        "This is the drift the shared implementation exists to prevent."
    )

    # ── 2. message fidelity against the PRE-CHANGE capture ─────────────────
    expected_rc = (golden["after"] if "after" in golden else golden["before"])["returncode"]
    assert rc == expected_rc, (
        f"{key}: exit code {rc}, golden expects {expected_rc}"
        + (f" (intentional change: {golden['change_reason']})" if "after" in golden else "")
    )

    if "after" not in golden:
        # Behaviour-preserving row: the streams must match byte-for-byte after
        # normalization. This is the assertion a substring check would have let slip.
        assert gs.normalize(err, spec_dir=spec_dir) == golden["before"]["stderr"], (
            f"{key}: stderr drifted from the pre-change capture.\n"
            f"  golden: {golden['before']['stderr']!r}\n"
            f"  actual: {gs.normalize(err, spec_dir=spec_dir)!r}"
        )
        assert gs.normalize(out, spec_dir=spec_dir) == golden["before"]["stdout"], (
            f"{key}: stdout drifted from the pre-change capture.\n"
            f"  golden: {golden['before']['stdout']!r}\n"
            f"  actual: {gs.normalize(out, spec_dir=spec_dir)!r}"
        )

    # ── 3. the CLI passes the shared reason through, rather than composing ──
    if not api_result.ok:
        assert err.strip(), f"{key}: refusal with an empty stderr"
        assert len(err.strip().split("\n")) == 1, f"{key}: stderr is not one line"
        assert "Traceback" not in err, f"{key}: traceback instead of a refusal"


def test_the_table_covers_every_guard(goldens) -> None:
    """Each of the six guards, and both outcomes for each.

    A table that only ever exercised refusals would still pass every assertion above
    while proving nothing about the success path, and vice versa.
    """
    seen: dict[str, set[bool]] = {}
    for key, _kwargs, _api, _tool, _argv in _rows():
        family = key.split("/")[0]
        golden = goldens[key]
        rc = (golden["after"] if "after" in golden else golden["before"])["returncode"]
        seen.setdefault(family, set()).add(rc == 0)
    expected = {
        "identity", "schedule-check-current", "plan-check-current",
        "check", "wave-check", "check-spec-status",
    }
    assert set(seen) == expected, f"missing guard families: {sorted(expected - set(seen))}"
    for family, outcomes in seen.items():
        assert outcomes == {True, False}, (
            f"{family}: only {'successes' if True in outcomes else 'refusals'} are "
            "covered; a guard needs both to pin its contract"
        )


# Golden rows this table cannot express, each mapped to the test that DOES cover it.
# A bare set of exempt keys is a promise with nothing behind it — the reviewer found
# two of the four covered nowhere at all. The mapping is machine-checked below: the
# named test must exist in the named module, so deleting or renaming it fails here
# instead of silently un-covering a ratified behaviour change.
#
# These three need a symlink or a sparse >8 MiB file, which the declarative fixture
# kwargs cannot express.
EXEMPT_ROWS = {
    "check-spec-status/symlinked-spec-md": (
        "test_loop_guards.py", "test_an_artifact_integrity_change_matches_its_golden"),
    "check-spec-status/oversized-spec-md": (
        "test_loop_guards.py", "test_an_artifact_integrity_change_matches_its_golden"),
    "plan-check-current/symlinked-plan-md": (
        "test_loop_guards.py", "test_an_artifact_integrity_change_matches_its_golden"),
}


# Sibling modules an EXEMPT_ROWS entry may name, mapped to LITERAL paths.
#
# Not `Path(__file__).parent / module_name`: `tools/lint-pack-test-boundary.py`'s
# `pack-tests-stay-in-pack` check requires a pack test's paths to be PROVABLY inside
# its own pack, and a join through a variable component is not — the linter cannot
# see where it lands. Literal components are provable, so they are what it accepts.
_SIBLING_MODULES = {
    "test_loop_guards.py": Path(__file__).resolve().parent / "test_loop_guards.py",
}


def test_every_intentional_change_is_exercised(goldens) -> None:
    """Every `change_reason` in the goldens appears in this table or in EXEMPT_ROWS."""
    declared = {k for k, r in goldens.items() if "change_reason" in r}
    covered = {key for key, *_ in _rows()}
    missing = declared - covered - set(EXEMPT_ROWS)
    assert not missing, f"intentional changes with no parity row: {sorted(missing)}"


def test_the_golden_set_is_fully_consumed(goldens) -> None:
    """No golden row may sit unread.

    The failure this closes: 11 of 49 captured rows were never compared against the
    live CLI, including both drift reasons — the largest authored strings in the tool.
    Nothing flagged it, because the table only ever asserted that its OWN rows had
    goldens, never that every golden had a row. Unused captures then accumulate
    silently and read as coverage they are not providing.
    """
    covered = {key for key, *_ in _rows()}
    unread = sorted(set(goldens) - covered - set(EXEMPT_ROWS))
    assert not unread, (
        f"{len(unread)} golden row(s) are never compared against the live CLI: "
        f"{unread}. Add a parity row, or add an EXEMPT_ROWS entry naming the test "
        "that covers it."
    )
    # And the exemptions must not name rows that no longer exist.
    stale = sorted(set(EXEMPT_ROWS) - set(goldens))
    assert not stale, f"EXEMPT_ROWS names golden rows that are gone: {stale}"


def test_every_exemption_names_a_test_that_exists() -> None:
    """The exemption list is a claim about other tests; verify the claim.

    Structural (AST), not a substring scan: a function name appearing in a comment or
    a docstring must not satisfy it.
    """
    import ast

    for key, (module_name, test_name) in sorted(EXEMPT_ROWS.items()):
        module_path = _SIBLING_MODULES.get(module_name)
        assert module_path is not None, (
            f"{key}: exemption names {module_name}, which is not in _SIBLING_MODULES — "
            "add a literal path entry for it"
        )
        assert module_path.is_file(), f"{key}: exemption names a missing module {module_name}"
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        names = {
            n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert test_name in names, (
            f"{key}: exemption claims {module_name}::{test_name} covers it, but no such "
            "test exists — the row is uncovered"
        )

        # Existence of the test is not coverage of THIS key. The named test is
        # parametrised over `_ARTIFACT_INTEGRITY_ROWS`, so the key must appear there;
        # otherwise deleting one entry silently un-covers a ratified behaviour change
        # while every assertion above still passes.
        table = next(
            (n for n in ast.walk(tree)
             if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == "_ARTIFACT_INTEGRITY_ROWS"
                     for t in n.targets)),
            None,
        )
        assert table is not None, (
            f"{key}: {module_name} has no _ARTIFACT_INTEGRITY_ROWS table to check "
            "the exemption against"
        )
        parametrised = {
            k.value for k in table.value.keys
            if isinstance(k, ast.Constant) and isinstance(k.value, str)
        }
        assert key in parametrised, (
            f"{key}: exempted, and {module_name}::{test_name} exists, but the key is "
            f"not in its _ARTIFACT_INTEGRITY_ROWS table {sorted(parametrised)} — so "
            "nothing actually drives it"
        )
