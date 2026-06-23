#!/usr/bin/env python3
"""Pack activation-eval runner (pack-activation-evals spec, Tier A).

Measures — repeatably and empirically — whether each covered skill in a pack
*activates* on the prompts it should and stays quiet on the near-misses it
shouldn't, on **claude-code as the reference harness** (a proxy for the
byte-identical `description:` projected to every adapter).

For a pack, reads `packs/<pack>/pack.toml` `[pack.evals].skills` (an explicit
allowlist), projects the pack into an isolated temp directory so only that
pack's skills are discoverable, and for each query in each covered skill's
`evals/eval_queries.json` runs the convention's own headless detector:

    claude -p "<query>" --output-format stream-json --verbose --allowed-tools Skill

parsing the event stream for a `Skill` `tool_use` block (`.input.skill`) to
record whether the skill fired and which one. It runs each query `--runs`
times (default 3), computes a per-query `trigger_rate`, grades against the 0.5
threshold, and writes the runs + a bounded activation summary into a
gitignored, iteration-numbered eval-workspace.

Detection note: `--output-format json` returns a result-only envelope with no
tool_use events; `stream-json --verbose` is required to observe the activation
event. RFC-0037 / ADR-0028 / spec AC1 originally specified `json`; corrected by
an in-PR erratum (the activation event is not present in the `json` envelope on
claude 2.1.185).

Trust boundary: `--allowed-tools` is held to **`Skill` only** — the run
*observes* the activation event but the skill *body*'s tools (shell/file/
network) are never granted, so author-influenced query strings cannot drive
side effects. Query strings are always passed as an argv list, never via a
shell. The runner uses only the Python standard library + `tomllib` + the
already-installed `agentbundle` projection path + the `claude` CLI on PATH.

Report-only: an eval miss is not a non-zero exit. This is dev tooling that runs
in a scheduled / dispatch workflow, never on the PR critical path.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass, field

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
# Repo-relative, gitignored. Distinct from the ephemeral temp dir a pack is
# *projected* into for discovery — the eval-workspace persists across passes.
EVAL_WORKSPACE = ".eval-workspace"
DEFAULT_RUNS = 3
DEFAULT_TIMEOUT_S = 180
# The grading threshold (pack-activation-evals convention): a should_trigger
# query passes iff trigger_rate > 0.5; a should-not-trigger query passes iff
# trigger_rate < 0.5.
THRESHOLD = 0.5


# ── Pure functions (no live model; unit-tested against fixtures) ──────────


@dataclass
class ActivationResult:
    """The parsed outcome of one headless detector run.

    `skills_fired` lists every skill named by a `Skill` `tool_use` event in
    the stream, in order. `result` is the parsed `.result` field of the
    terminal `result` event (the model's final text) — never the raw stdout
    stream, stderr, the environment, or any secret.
    """

    skills_fired: list[str] = field(default_factory=list)
    result: str | None = None
    # Set when the run could not be measured (timeout, non-zero exit,
    # truncated stream) — a **harness failure**, distinct from a genuine
    # "skill did not fire". Surfaced as `error_count` in the summary so an
    # all-zero trigger_rate from a broken CLI is not misread as a regression.
    error: str | None = None

    @property
    def fired(self) -> bool:
        return bool(self.skills_fired)


def parse_activation(stdout: str) -> ActivationResult:
    """Parse a `claude -p --output-format stream-json --verbose` payload.

    The stream is JSON-lines. A skill activation appears as an `assistant`
    event whose `message.content[]` holds a block
    `{"type": "tool_use", "name": "Skill", "input": {"skill": "<name>", ...}}`.
    The stream ends with a `{"type": "result", ..., "result": "<text>"}` event.

    A line that is not valid JSON is skipped (resilience: a partial/garbled
    line must not crash the parse). Returns the skills fired and the terminal
    result text.
    """
    skills_fired: list[str] = []
    result_text: str | None = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        etype = event.get("type")
        if etype == "assistant":
            message = event.get("message") or {}
            for block in message.get("content") or []:
                if (
                    isinstance(block, dict)
                    and block.get("type") == "tool_use"
                    and block.get("name") == "Skill"
                ):
                    skill = (block.get("input") or {}).get("skill")
                    if isinstance(skill, str) and skill:
                        skills_fired.append(skill)
        elif etype == "result":
            res = event.get("result")
            if isinstance(res, str):
                result_text = res
    return ActivationResult(skills_fired=skills_fired, result=result_text)


def trigger_rate(target_fired: list[bool]) -> float:
    """Fraction of runs in which the target skill fired."""
    if not target_fired:
        return 0.0
    return sum(1 for f in target_fired if f) / len(target_fired)


def grade(rate: float, should_trigger: bool) -> bool:
    """A should_trigger query passes iff rate > 0.5; a should-not-trigger
    query passes iff rate < 0.5 (the pack-activation-evals convention)."""
    if should_trigger:
        return rate > THRESHOLD
    return rate < THRESHOLD


# ── Detector seam (adapter → headless detector) ───────────────────────────
#
# Only the `claude-code` detector ships in the first cut. Additional *headless*
# detectors (codex / copilot / cursor-agent / gemini) are additive behind this
# seam. GUI-only IDE adapters (kiro-ide, cursor) expose no headless surface and
# are rejected, not silently run (spec § Never do).


class ClaudeCodeDetector:
    """Projects a pack for the claude-code adapter and runs the headless
    `claude -p` detector, parsing the activation event."""

    adapter = "claude-code"

    def project(self, pack_path: pathlib.Path, output_root: pathlib.Path) -> None:
        # Lazy import so the pure functions above (and their unit tests) do
        # not require agentbundle to be importable.
        from agentbundle.build.adapters.claude_code import project
        from agentbundle.build.contract import load as load_contract

        contract = load_contract(REPO_ROOT / "docs" / "contracts" / "adapter.toml")
        project(pack_path, contract, output_root)

    def run_and_parse(
        self, query: str, cwd: pathlib.Path, timeout: int
    ) -> ActivationResult:
        # argv list (never shell=True); --allowed-tools held to Skill only.
        argv = [
            "claude",
            "-p",
            query,
            "--output-format",
            "stream-json",
            "--verbose",
            "--allowed-tools",
            "Skill",
        ]
        try:
            proc = subprocess.run(
                argv,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            # A timeout / spawn failure is a harness error, not a clean
            # non-activation. We never serialize the (possibly partial)
            # payload or the exception's stderr.
            kind = "timeout" if isinstance(exc, subprocess.TimeoutExpired) else "spawn-error"
            return ActivationResult(error=kind)
        res = parse_activation(proc.stdout)
        # A non-zero exit (auth failure, rate-limit) or a stream that never
        # reached a terminal `result` event **and** fired no skill (truncated /
        # format drift) means the run could not be measured — flag it so a
        # zeroed trigger_rate is distinguishable from a genuine miss. A run that
        # fired a skill but truncated before the result event is a real
        # activation, not a harness error, so it is deliberately not flagged.
        if proc.returncode != 0:
            res.error = f"exit-{proc.returncode}"
        elif res.result is None and not res.skills_fired:
            res.error = "no-result-event"
        return res


# Adapters with no headless prompt surface — rejected with a clear message
# rather than silently run (their shared byte-identical `description:` is
# covered by the claude-code reference-harness measurement).
_GUI_ONLY_ADAPTERS = {"kiro-ide", "cursor"}
_DETECTORS = {ClaudeCodeDetector.adapter: ClaudeCodeDetector}


def get_detector(adapter: str):
    """Return a detector instance for `adapter`, or raise ValueError for an
    unknown / non-headless adapter (the seam never silently runs one)."""
    detector_cls = _DETECTORS.get(adapter)
    if detector_cls is not None:
        return detector_cls()
    if adapter in _GUI_ONLY_ADAPTERS:
        raise ValueError(
            f"adapter {adapter!r} is a GUI-only IDE with no headless surface; "
            f"activation evals are headless-only (spec § Never do)"
        )
    raise ValueError(
        f"no headless detector registered for adapter {adapter!r}; "
        f"the first cut ships only {sorted(_DETECTORS)!r}"
    )


# ── Pack reading ──────────────────────────────────────────────────────────


def _safe_segment(label: str, name: str) -> str:
    """Reject a path segment that isn't a single, traversal-free name.

    `pack_name` (from `--pack`) and each skill name (from `[pack.evals].skills`)
    are interpolated into filesystem paths; confine them to a single component
    so `../…` or an absolute path can't escape the pack tree or the workspace.
    """
    # Reject both separators explicitly: `\` is not a separator on POSIX (so
    # `Path("a\\b").name` would pass there) but is on Windows — confine on all
    # platforms.
    if (
        not name
        or "/" in name
        or "\\" in name
        or name in (".", "..")
        or name == REPORT_ERROR  # reserved in-harness sentinel, not a skill name
        or name != pathlib.PurePosixPath(name).name
    ):
        raise ValueError(
            f"unsafe {label} {name!r}: must be a single path segment "
            f"(no '/', '\\', or '..')"
        )
    return name


def read_covered_skills(pack_dir: pathlib.Path) -> list[str]:
    """Return the `[pack.evals].skills` allowlist (empty if no block)."""
    manifest = tomllib.loads((pack_dir / "pack.toml").read_text(encoding="utf-8"))
    evals_cfg = manifest.get("pack", {}).get("evals") or {}
    skills = evals_cfg.get("skills", [])
    if not isinstance(skills, list):
        raise ValueError("[pack.evals].skills must be an array of strings")
    return [s for s in skills if isinstance(s, str) and s]


def read_eval_queries(pack_dir: pathlib.Path, skill: str) -> list[dict]:
    """Return the flat [{query, should_trigger}] array for one covered skill.

    Read from the source `.apm/skills/.../evals/` (author input), not the
    projected tree — the runner measures activation against the projection but
    the queries are authored, not a projected artifact (skill projection is a
    verbatim copytree today, so the two are byte-identical regardless)."""
    path = pack_dir / ".apm" / "skills" / skill / "evals" / "eval_queries.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path}: eval_queries.json must be a JSON array")
    return data


def read_output_evals(pack_dir: pathlib.Path, skill: str) -> list[dict]:
    """Return the `evals` list of a covered skill's evals/evals.json (the
    Tier-B output-quality source the B-lite behavior check runs against)."""
    path = pack_dir / ".apm" / "skills" / skill / "evals" / "evals.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    evals = data.get("evals") if isinstance(data, dict) else None
    if not isinstance(evals, list):
        raise ValueError(f"{path}: evals.json must have an 'evals' list")
    return evals


# ── Orchestration ──────────────────────────────────────────────────────────

# In-harness reports use this sentinel for a run whose dispatch failed (vs a
# legitimate `null`/None = "the sub-context activated no skill").
REPORT_ERROR = "__error__"


def _validate_reports(reports: object) -> None:
    """Validate the operator-supplied in-harness reports structure before it
    drives grading: `{skill: {query_id: [reported_skill | null | "__error__"]}}`.
    A malformed file must fail loud, not silently produce a wrong summary."""
    if not isinstance(reports, dict):
        raise ValueError("reports must be a JSON object {skill: {query_id: [...]}}")
    for skill, by_query in reports.items():
        if not isinstance(by_query, dict):
            raise ValueError(f"reports[{skill!r}] must be an object {{query_id: [...]}}")
        for query_id, runs in by_query.items():
            if not isinstance(runs, list):
                raise ValueError(
                    f"reports[{skill!r}][{query_id!r}] must be a list of run reports"
                )
            for entry in runs:
                if entry is not None and not isinstance(entry, str):
                    raise ValueError(
                        f"reports[{skill!r}][{query_id!r}] entries must be a skill "
                        f"name, null, or {REPORT_ERROR!r} (got {type(entry).__name__})"
                    )


def _pack_skills(pack_dir: pathlib.Path) -> set[str]:
    """Every skill dir in the pack — for intra-pack exclusivity."""
    skills_root = pack_dir / ".apm" / "skills"
    return (
        {p.name for p in skills_root.iterdir() if p.is_dir()}
        if skills_root.is_dir()
        else set()
    )


def _query_summary(
    query_id: str,
    query: str,
    should_trigger: bool,
    target_fired: list[bool],
    exclusivity: set[str],
    errored: int,
) -> tuple[dict, bool]:
    """Build one query's bounded summary record from its per-run outcomes.
    Shared by the headless orchestration and the in-harness grader so both
    emit an identical record shape. Returns (record, passed)."""
    rate = trigger_rate(target_fired)
    passed = grade(rate, should_trigger)
    return (
        {
            "query_id": query_id,
            "query": query,
            "should_trigger": should_trigger,
            "trigger_rate": rate,
            "passed": passed,
            "errored_runs": errored,
            "exclusivity_violations": sorted(exclusivity),
        },
        passed,
    )


def _next_iteration(pack_workspace: pathlib.Path) -> int:
    """One-based iteration number: max existing iteration-<N> + 1."""
    highest = 0
    if pack_workspace.is_dir():
        for child in pack_workspace.iterdir():
            if child.is_dir() and child.name.startswith("iteration-"):
                try:
                    highest = max(highest, int(child.name.split("-", 1)[1]))
                except ValueError:
                    continue
    return highest + 1


def run_eval(
    pack_name: str,
    *,
    runs: int = DEFAULT_RUNS,
    detector=None,
    timeout: int = DEFAULT_TIMEOUT_S,
    repo_root: pathlib.Path = REPO_ROOT,
    project_root: pathlib.Path | None = None,
) -> dict:
    """Run the activation eval for one pack and write one `iteration-<N>/`.

    Returns the bounded summary dict (also written as `summary.json`). The
    detector is injectable so the orchestration is testable without a live
    model; `project_root` lets a test point the projected pack at a prepared
    directory instead of invoking agentbundle.
    """
    if detector is None:
        detector = get_detector(ClaudeCodeDetector.adapter)
    _safe_segment("pack name", pack_name)
    pack_dir = repo_root / "packs" / pack_name
    covered = [_safe_segment("skill name", s) for s in read_covered_skills(pack_dir)]
    # Intra-pack exclusivity may name a non-covered skill; cross-*pack*
    # collisions are out of scope (the projection holds only this pack's skills).
    pack_skills = _pack_skills(pack_dir)

    pack_workspace = repo_root / EVAL_WORKSPACE / pack_name
    iteration = _next_iteration(pack_workspace)
    iter_dir = pack_workspace / f"iteration-{iteration}"

    # Project the pack into an isolated dir so only its skills are discoverable.
    if project_root is None:
        proj = iter_dir / ".projection"
        detector.project(pack_dir, proj)
        run_cwd = proj
    else:
        run_cwd = project_root

    summary: dict = {
        "pack": pack_name,
        "adapter": getattr(detector, "adapter", "claude-code"),
        "mode": "headless",
        # Headless observes the real `Skill` tool_use router event.
        "fidelity": "observed",
        "runs": runs,
        "iteration": iteration,
        "skills": {},
    }

    for skill in covered:
        queries = read_eval_queries(pack_dir, skill)
        skill_summary: dict = {
            "queries": [], "pass_count": 0, "total": len(queries), "error_count": 0,
        }
        if not queries:
            print(
                f"run-pack-evals: warning: {skill}: eval_queries.json is empty "
                f"— 0 queries measured.",
                file=sys.stderr,
            )
        for q_index, entry in enumerate(queries):
            query = entry.get("query", "")
            should_trigger = bool(entry.get("should_trigger", False))
            query_id = f"q{q_index:02d}"
            if not query:
                # The lint rejects this at source; guard the runner too rather
                # than measuring an empty prompt.
                print(
                    f"run-pack-evals: warning: {skill} {query_id}: empty query "
                    f"— skipped.",
                    file=sys.stderr,
                )
                continue
            target_fired: list[bool] = []
            exclusivity: set[str] = set()
            errored = 0
            for r in range(1, runs + 1):
                result = detector.run_and_parse(query, run_cwd, timeout)
                target_fired.append(skill in result.skills_fired)
                if result.error:
                    errored += 1
                # Intra-pack exclusivity: a *different* in-pack skill fired.
                for other in result.skills_fired:
                    if other != skill and other in pack_skills:
                        exclusivity.add(other)
                # Capture only the parsed .result field (the model's text),
                # never the raw stdout stream, stderr, env, or key.
                out_dir = (
                    iter_dir / skill / query_id / "with_skill" / f"run-{r}" / "outputs"
                )
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / "result.txt").write_text(
                    result.result or "", encoding="utf-8"
                )
            record, passed = _query_summary(
                query_id, query, should_trigger, target_fired, exclusivity, errored
            )
            if passed:
                skill_summary["pass_count"] += 1
            skill_summary["error_count"] += errored
            skill_summary["queries"].append(record)
        summary["skills"][skill] = skill_summary

    iter_dir.mkdir(parents=True, exist_ok=True)
    (iter_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def grade_reports(
    pack_name: str,
    reports: dict,
    *,
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict:
    """Grade **in-harness** (Phase 2, RFC-0037 § Errata E2) activation reports.

    `reports` is `{skill: {query_id: [reported_skill | null | "__error__", ...]}}`
    — collected by the catalogue-internal driver, which dispatches each query to
    a fresh, read-only host sub-context (supplied the covered skills'
    descriptions) and records which skill it **reports** it would activate.
    Reuses the Phase-1 `trigger_rate`/grading and the same eval-workspace +
    `summary.json` contract; labelled `mode: in-harness`, `fidelity: reported`
    so it is never conflated with the headless `observed` baseline. No model is
    invoked here — the dispatch is the driver's job; this is pure grading.
    """
    _validate_reports(reports)
    _safe_segment("pack name", pack_name)
    pack_dir = repo_root / "packs" / pack_name
    covered = [_safe_segment("skill name", s) for s in read_covered_skills(pack_dir)]
    pack_skills = _pack_skills(pack_dir)

    pack_workspace = repo_root / EVAL_WORKSPACE / pack_name
    iteration = _next_iteration(pack_workspace)
    iter_dir = pack_workspace / f"iteration-{iteration}"

    summary: dict = {
        "pack": pack_name,
        "adapter": "claude-code",
        "mode": "in-harness",
        # Reported (description-match judgement), not the observed router event —
        # a dispatched sub-context can't be skill-isolated (RFC-0037 § Errata E2).
        "fidelity": "reported",
        # The reports are collected by a hand-driven procedure, so the grade is
        # operator-attested, not tool-observed — a reader must not mistake this
        # for a measured headless run.
        "provenance": "operator-attested (driver-collected reports)",
        "runs": None,
        "iteration": iteration,
        "skills": {},
    }

    for skill in covered:
        queries = read_eval_queries(pack_dir, skill)
        skill_reports = reports.get(skill, {})
        skill_summary: dict = {
            "queries": [], "pass_count": 0, "total": len(queries), "error_count": 0,
        }
        for q_index, entry in enumerate(queries):
            query = entry.get("query", "")
            should_trigger = bool(entry.get("should_trigger", False))
            query_id = f"q{q_index:02d}"
            run_reports = skill_reports.get(query_id, [])
            target_fired = [r == skill for r in run_reports]
            errored = sum(1 for r in run_reports if r == REPORT_ERROR)
            if not run_reports:
                # A covered query the driver never dispatched is *unmeasured*,
                # not a clean non-activation — flag it so it can't read as a
                # real regression.
                errored = 1
                print(
                    f"run-pack-evals: warning: {skill} {query_id}: no in-harness "
                    f"reports — unmeasured, flagged as errored (not a miss).",
                    file=sys.stderr,
                )
            exclusivity = {
                r for r in run_reports
                if r and r not in (skill, REPORT_ERROR) and r in pack_skills
            }
            record, passed = _query_summary(
                query_id, query, should_trigger, target_fired, exclusivity, errored
            )
            if passed:
                skill_summary["pass_count"] += 1
            skill_summary["error_count"] += errored
            skill_summary["queries"].append(record)
            # Capture the bounded per-run reports (skill names only — no model
            # text, no host transcript) for traceability.
            cap = iter_dir / skill / query_id / "in_harness"
            cap.mkdir(parents=True, exist_ok=True)
            (cap / "reports.json").write_text(
                json.dumps(run_reports) + "\n", encoding="utf-8"
            )
        summary["skills"][skill] = skill_summary

    iter_dir.mkdir(parents=True, exist_ok=True)
    (iter_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


# The driver writes the skill run's output text here, inside the per-eval
# working dir, so the runner can re-derive output substring checks from a file
# it reads itself (not an operator-supplied string).
BEHAVIOR_OUTPUT_FILE = ".eval-output.txt"


def seed_workspace(skill_dir: pathlib.Path, files: list[str]) -> pathlib.Path:
    """Create an OS-temp working dir and copy the eval's `evals/files/` fixtures
    into it with path-confinement (every fixture resolved under the skill's
    `evals/` root; symlinks refused). Returns the working dir; the **driver**
    runs the skill there and is responsible for teardown in a `finally`.

    This is **not** a mechanical sandbox — a host agent running the skill keeps
    its full tool surface (RFC-0037 § Errata E3 / the spec-stage security pass).
    Containment is the procedure + the scope gate (only non-destructive,
    no-network/credential skills are eligible); this helper only confines what
    is seeded *in*.
    """
    evals_root = (skill_dir / "evals").resolve()
    ws = pathlib.Path(tempfile.mkdtemp(prefix="pack-eval-bx-"))
    for f in files or []:
        src = (skill_dir / f).resolve()
        try:
            src.relative_to(evals_root)
        except ValueError:
            shutil.rmtree(ws, ignore_errors=True)
            raise ValueError(f"fixture {f!r} resolves outside the skill's evals/ dir")
        if src.is_symlink() or not src.is_file():
            shutil.rmtree(ws, ignore_errors=True)
            raise ValueError(f"fixture {f!r} is not a regular file (symlinks refused)")
        shutil.copyfile(src, ws / pathlib.Path(f).name)
    return ws


def grade_behavior(
    pack_name: str,
    results: dict,
    *,
    workspaces: dict,
    repo_root: pathlib.Path = REPO_ROOT,
) -> dict:
    """Grade the **lightweight behavior/output check** (Phase 3, RFC-0037 §
    Errata E3). For each eval in a covered skill's `evals/evals.json`, the driver
    has run the skill in a per-eval working dir; this grades **without running
    anything**:

    - **deterministic post-conditions are re-derived here** from the working dir
      the runner reads — the eval's optional `expect.produces` files exist, and
      `expect.output_contains`/`output_excludes` substrings hold against the
      driver-captured `BEHAVIOR_OUTPUT_FILE` *inside* that dir. The runner does
      **not** trust operator `*_ok` booleans (security-reviewer Blocker 3).
    - only the semantic `assertions` verdicts are operator-**attested**.

    `results`: `{skill: {eval_id: {"assertions": [bool, ...], "errored": bool}}}`.
    `workspaces`: `{f"{skill}/{eval_id}": <working-dir path>}`. A missing
    workspace or malformed entry **fails closed** (graded errored, never a pass).
    """
    if not isinstance(results, dict):
        raise ValueError("results must be a JSON object {skill: {eval_id: {...}}}")
    _safe_segment("pack name", pack_name)
    pack_dir = repo_root / "packs" / pack_name

    pack_workspace = repo_root / EVAL_WORKSPACE / pack_name
    iteration = _next_iteration(pack_workspace)
    iter_dir = pack_workspace / f"iteration-{iteration}"

    summary: dict = {
        "pack": pack_name,
        "adapter": "claude-code",
        "mode": "in-harness",
        "tier": "B-lite",
        # Deterministic post-conditions are observed (runner-re-derived); the
        # semantic assertions are operator-attested.
        "fidelity": "observed+attested",
        "provenance": "operator-attested",
        "runs": None,
        "iteration": iteration,
        "skills": {},
    }

    for skill, by_eval in results.items():
        _safe_segment("skill name", skill)
        evals = read_output_evals(pack_dir, skill)
        skill_summary: dict = {
            "evals": [], "pass_count": 0, "total": len(evals), "error_count": 0,
        }
        for ev in evals:
            eid = str(ev.get("id"))
            attested = by_eval.get(eid, {})
            ws = workspaces.get(f"{skill}/{eid}")
            expect = ev.get("expect", {}) if isinstance(ev.get("expect"), dict) else {}

            errored = bool(attested.get("errored")) or ws is None
            produces_ok = output_ok = True
            wsp = pathlib.Path(ws) if ws is not None else None
            if not errored and not (wsp and wsp.is_dir()):
                errored = True  # fail closed: the driver never produced this dir
            if not errored:
                for f in expect.get("produces", []):
                    if not (wsp / f).is_file():
                        produces_ok = False
                out_txt = ""
                out_file = wsp / BEHAVIOR_OUTPUT_FILE
                if out_file.is_file():
                    out_txt = out_file.read_text(encoding="utf-8", errors="replace")
                for s in expect.get("output_contains", []):
                    if s not in out_txt:
                        output_ok = False
                for s in expect.get("output_excludes", []):
                    if s in out_txt:
                        output_ok = False

            attested_assertions = attested.get("assertions", [])
            declared_assertions = ev.get("assertions") or []
            if declared_assertions:
                # Declared-but-unattested fails closed; otherwise all must hold.
                if not attested_assertions:
                    assertions_ok = False
                    errored = True
                else:
                    assertions_ok = all(bool(a) for a in attested_assertions)
            else:
                assertions_ok = True  # no assertions to attest — deterministic only
            passed = not errored and produces_ok and output_ok and assertions_ok
            if passed:
                skill_summary["pass_count"] += 1
            if errored:
                skill_summary["error_count"] += 1
            skill_summary["evals"].append({
                "eval_id": eid,
                "produces_ok": produces_ok,
                "output_ok": output_ok,
                "assertions_ok": assertions_ok,
                "errored": errored,
                "passed": passed,
            })
        summary["skills"][skill] = skill_summary

    iter_dir.mkdir(parents=True, exist_ok=True)
    (iter_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def _print_report(summary: dict) -> None:
    runs = summary.get("runs")
    runs_note = f"runs={runs} " if runs is not None else ""
    prov = summary.get("provenance")
    prov_note = f"provenance={prov} " if prov else ""
    tier = summary.get("tier")
    tier_note = f"tier={tier} " if tier else ""
    print(
        f"pack={summary['pack']} adapter={summary['adapter']} "
        f"mode={summary.get('mode', 'headless')} "
        f"{tier_note}fidelity={summary.get('fidelity', 'observed')} "
        f"{prov_note}{runs_note}iteration={summary['iteration']}"
    )
    for skill, s in summary["skills"].items():
        errs = s.get("error_count", 0)
        # B-lite summaries carry `evals`; activation summaries carry `queries`.
        if "evals" in s:
            err_note = f"  ⚠ {errs} errored" if errs else ""
            print(f"  {skill}: {s['pass_count']}/{s['total']} evals passed{err_note}")
            for e in s["evals"]:
                mark = "ok " if e["passed"] else "FAIL"
                bits = []
                if not e["produces_ok"]:
                    bits.append("missing artifact")
                if not e["output_ok"]:
                    bits.append("output check")
                if not e["assertions_ok"]:
                    bits.append("assertion")
                if e["errored"]:
                    bits.append("errored")
                note = f"  ⚠ {', '.join(bits)}" if bits else ""
                print(f"    [{mark}] eval {e['eval_id']}{note}")
            continue
        err_note = (
            f"  ⚠ {errs} harness error(s) — trigger rates unreliable"
            if errs
            else ""
        )
        print(f"  {skill}: {s['pass_count']}/{s['total']} queries passed{err_note}")
        for q in s["queries"]:
            mark = "ok " if q["passed"] else "MISS"
            excl = (
                f"  ⚠ also fired: {', '.join(q['exclusivity_violations'])}"
                if q["exclusivity_violations"]
                else ""
            )
            errored = (
                f"  ⚠ {q['errored_runs']} errored run(s)"
                if q.get("errored_runs")
                else ""
            )
            print(
                f"    [{mark}] {q['query_id']} "
                f"should_trigger={q['should_trigger']} "
                f"trigger_rate={q['trigger_rate']:.2f}{excl}{errored}"
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run-pack-evals.py",
        description="Measure skill activation for a pack (Tier A, report-only).",
    )
    parser.add_argument("--pack", required=True, help="pack name under packs/")
    parser.add_argument(
        "--runs", type=int, default=DEFAULT_RUNS, help="runs per query (default 3)"
    )
    parser.add_argument(
        "--adapter",
        default=ClaudeCodeDetector.adapter,
        help="detector adapter (only claude-code ships in the first cut)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_S,
        help="per-run wall-clock timeout in seconds (default 180)",
    )
    parser.add_argument(
        "--mode",
        choices=("headless", "in-harness"),
        default="headless",
        help="headless (default; live claude -p) or in-harness (grade reports "
             "collected by the catalogue-internal driver — RFC-0037 § Errata E2)",
    )
    parser.add_argument(
        "--check",
        choices=("activation", "behavior"),
        default="activation",
        help="in-harness check: activation (Tier-A, default) or behavior "
             "(Tier-B-lite output/behavior — RFC-0037 § Errata E3)",
    )
    parser.add_argument(
        "--reports",
        help="path to the in-harness results JSON; with --check activation: "
             "{skill: {query_id: [reported|null|\"__error__\", ...]}}; with "
             "--check behavior: {skill: {eval_id: {assertions:[bool], errored, "
             "workspace}}}. Required with --mode in-harness",
    )
    args = parser.parse_args(argv)

    if args.mode == "in-harness":
        # In-harness grades results the driver already collected — no model call.
        if not args.reports:
            parser.error("--mode in-harness requires --reports <path>")
        try:
            payload = json.loads(
                pathlib.Path(args.reports).read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            parser.error(f"--reports {args.reports!r}: {exc}")
        if args.check == "behavior":
            # Split the driver's payload into attested verdicts + the per-eval
            # working dirs the runner re-derives deterministic checks from.
            if not isinstance(payload, dict):
                parser.error("--reports must be a JSON object for --check behavior")
            results: dict = {}
            workspaces: dict = {}
            for skill, by_eval in payload.items():
                results[skill] = {}
                for eid, entry in (by_eval or {}).items():
                    entry = dict(entry)
                    ws = entry.pop("workspace", None)
                    if ws is not None:
                        workspaces[f"{skill}/{eid}"] = ws
                    results[skill][eid] = entry
            summary = grade_behavior(args.pack, results, workspaces=workspaces)
        else:
            summary = grade_reports(args.pack, payload)
        _print_report(summary)
        return 0

    detector = get_detector(args.adapter)
    # `claude` is a hard prerequisite of the live run — fail fast (clear
    # message), not a per-query miss.
    if isinstance(detector, ClaudeCodeDetector) and shutil.which("claude") is None:
        print(
            "run-pack-evals: `claude` not found on PATH — it is required to run "
            "the activation detector.",
            file=sys.stderr,
        )
        return 1

    summary = run_eval(
        args.pack, runs=args.runs, detector=detector, timeout=args.timeout
    )
    _print_report(summary)
    return 0  # report-only: an eval miss is never a non-zero exit


if __name__ == "__main__":
    sys.exit(main())
