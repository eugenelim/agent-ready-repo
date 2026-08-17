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
          spec_body=None, **over) -> Path:
    """ONE fixture builder, used by both halves of every row.

    That is the load-bearing detail: if the API and the CLI were given
    separately-constructed directories, a difference in the fixtures could masquerade
    as agreement — or as drift.
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
    return d


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
    ]


@pytest.mark.parametrize(
    "key,kwargs,api,tool,argv", _rows(), ids=[r[0] for r in _rows()]
)
def test_api_and_cli_agree(key, kwargs, api, tool, argv, guards, goldens, tmp_path) -> None:
    golden = goldens.get(key)
    assert golden is not None, (
        f"{key} has no golden row. Every parity row must tie to T0's pre-change "
        "capture, or it asserts nothing about message fidelity."
    )

    # One fixture, built once, used by both halves.
    kwargs = dict(kwargs)
    plan_status = kwargs.pop("plan_status_override", "Approved")
    dir_name = kwargs.pop("_dir_name", "spec")
    spec_dir = build(guards, tmp_path, dir_name, plan_status=plan_status, **kwargs)

    api_result = api(guards, spec_dir)
    script = COHORT if tool == "cohort" else CHECK_STATUS
    resolved_argv = [spec_dir if a == SPEC else a for a in argv]
    assert any(a is spec_dir for a in resolved_argv), (
        f"{key}: argv has no {SPEC} placeholder, so the CLI would never see the fixture"
    )
    rc, out, err = run_cli(script, resolved_argv, cwd=tmp_path)

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


def test_every_intentional_change_is_exercised(goldens) -> None:
    """Every `change_reason` in the goldens appears in this table.

    Otherwise a behaviour this change deliberately altered could regress with nothing
    watching — the golden would still record the intent, and no test would check it.
    """
    declared = {k for k, r in goldens.items() if "change_reason" in r}
    covered = {key for key, *_ in _rows()}
    # The artifact-integrity rows need a symlink or a sparse file, which the table's
    # declarative fixtures cannot express; they live in test_loop_guards.py instead.
    exempt = {
        "check-spec-status/symlinked-spec-md",
        "check-spec-status/oversized-spec-md",
        "plan-check-current/symlinked-plan-md",
        "check-spec-status/file-multi-component-inside",
    }
    missing = declared - covered - exempt
    assert not missing, f"intentional changes with no parity row: {sorted(missing)}"
