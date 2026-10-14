"""Slice 3 end-to-end conformance: delivery decisions ignore knowledge tooling (T3).

Mode: goal-based check through end-to-end conformance fixtures
(``docs/specs/delivery-knowledge-projection/plan.md``, task T3).  These
fixtures pin behavior that already holds, so there is no red phase; each one
carries a literal pre-slice expectation or a baseline-run comparison, and each
fails when its compared decision is deliberately changed (the mutation
observations are recorded in the spec's verification ledger).

Covers:

* AC-0007  a full work-loop pass makes the same spec, plan, review,
  acceptance, readiness, and closeout decisions with knowledge tooling absent,
  disabled, unavailable, timing out, refusing, and failing.
* AC-0012  with ``WORK_LOOP_SHADOW_SERVICES`` unset the pass produces the same
  files, state, and decisions as before this slice, and the feed returns the
  empty snapshot.
* AC-0004 and AC-0008  after every path the delivery-owned files hold no
  knowledge queue, cursor, retry, acknowledgement, skip log, admission,
  retention, or revocation record, no knowledge readiness transition, and the
  work-loop source holds no capture gate beyond the retained ones.

The engine never calls knowledge tooling, so each "knowledge tooling" variant
plants a stub the run would trip over if it did.  A stub appends to a log that
lives outside the repository; the log staying absent is the proof that delivery
never reached for knowledge, and a stub that sleeps would hang the run if it
did.
"""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

_SKILLS = Path(__file__).resolve().parents[3] / ".apm" / "skills"
SCRIPTS = _SKILLS / "work-loop" / "scripts"
ENGINE = SCRIPTS / "loop-engine.py"
COHORT = SCRIPTS / "loop-cohort.py"
SPEC_STATUS = SCRIPTS / "check-spec-status.py"
FEED = SCRIPTS / "delivery-fact-feed.py"
CANDIDATES = _SKILLS / "project-knowledge" / "scripts" / "project_knowledge.py"

FEATURE = "feature-one"
SPEC_REL = f"docs/specs/{FEATURE}"
SHADOW_ON = "1"
RUN_TIMEOUT = 120

_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?")

# Pre-slice literals.  The engine and cohort scripts are untouched by this
# slice, so these are what a run produced before it: the same eleven
# transitions, one file set, and a DONE run.
PRE_SLICE_FILES = frozenset({
    ".gitignore",
    ".loop-run/events.jsonl",
    f"{SPEC_REL}/engine-state.json",
    f"{SPEC_REL}/plan.md",
    f"{SPEC_REL}/spec.md",
    f"{SPEC_REL}/state.json",
})
SHADOW_PREFIX = f"{SPEC_REL}/.shadow-acceptance/"
SHADOW_REQUIRED = frozenset({SHADOW_PREFIX + ".gitignore", SHADOW_PREFIX + "shadow-evidence.log"})
PRE_SLICE_TRANSITIONS = (
    "spec-ready", "reviewers-clean", "spec-approved", "plan-approved", "plan-locked",
    "wave-complete", "wave-passed", "wave-complete", "gates-clean", "reviewers-clean",
    "done",
)

# Locations a knowledge stub is planted in, so no lookup order can miss one.
_STUB_DIRS = (
    ".claude/skills/project-knowledge/scripts",
    ".agents/skills/project-knowledge/scripts",
    "bin",
)
_STUB_NAMES = ("project_knowledge.py", "project-knowledge")
_STUB_SOURCES = {
    "timeout": "import time\ntime.sleep(3600)\n",
    "refusing": 'import sys\nsys.stderr.write(\'{"reason_code": "confinement"}\\n\')\nsys.exit(2)\n',
    "failing": 'raise RuntimeError("knowledge tooling failed")\n',
}
KNOWLEDGE_VARIANTS = ("absent", "disabled", "unavailable", "timeout", "refusing", "failing")


@dataclass
class Run:
    """The observable result of one full delivery pass."""

    root: Path
    transcript: list[tuple[str, int, str, str]] = field(default_factory=list)
    final: dict[str, str] = field(default_factory=dict)
    files: dict[str, str] = field(default_factory=dict)
    planted: dict[str, bytes] = field(default_factory=dict)
    stub_log: Path | None = None


# Identities the engine derives from the run id; content hashes (spec, plan) stay visible.
_RUN_DERIVED = re.compile(r'("(?:transition_id|operation_id|last_review_record_operation_id)": ")[0-9a-f]{64}"')
_HEX_IDENTITY = re.compile(r"[0-9a-f]{32,64}")
# Random per-run identifiers and wall-clock seconds; plan and spec hashes stay visible.
_RANDOM_ID = re.compile(r"\b(op|appr|rev|shadow|grant)-[0-9a-f]{16,32}\b")
_EVALUATION = re.compile(r'("(?:evaluation_fingerprint|correlation_id)": ")[0-9a-f]{32,64}"')
_PHASE_SECONDS = re.compile(r'("phase_s": )\d+')


def _mask(root: Path, text: str) -> str:
    """Mask the run root, run ids, and timestamps so two runs compare exactly."""
    text = text.replace(str(root.resolve()), "<ROOT>").replace(str(root), "<ROOT>")
    text = _RUN_DERIVED.sub(r'\1<DERIVED>"', text)
    text = _EVALUATION.sub(r'\1<DERIVED>"', _RANDOM_ID.sub(r"\1-<RANDOM>", text))
    text = _PHASE_SECONDS.sub(r'\1"<S>"', text)
    return _TIMESTAMP.sub("<TS>", _UUID.sub("<ID>", text))


def _plant_stub(root: Path, kind: str) -> None:
    source = "#!/usr/bin/env python3\n" + (
        "import os\n"
        "with open(os.environ['KNOWLEDGE_STUB_LOG'], 'a') as log:\n"
        "    log.write('invoked\\n')\n"
    ) + _STUB_SOURCES[kind]
    for directory in _STUB_DIRS:
        for name in _STUB_NAMES:
            path = root / directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")
            path.chmod(0o755)


def plant_knowledge_state(root: Path, variant: str) -> None:
    """Put the named knowledge-tooling condition into the repository tree."""
    knowledge = root / "docs" / "knowledge"
    if variant == "absent":
        return
    if variant == "disabled":
        # A repository that never activated project knowledge: a directory, no snapshot.
        knowledge.mkdir(parents=True)
        (knowledge / "README.md").write_text("# Knowledge\n", encoding="utf-8")
    elif variant == "unavailable":
        # The skill is present but cannot be run or read, and the store is not a directory.
        knowledge.parent.mkdir(parents=True, exist_ok=True)
        knowledge.write_text("not a store\n", encoding="utf-8")
        for directory in _STUB_DIRS:
            for name in _STUB_NAMES:
                path = root / directory / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(root / "missing-target")
    elif variant in _STUB_SOURCES:
        _plant_stub(root, variant)
        if variant == "failing":
            knowledge.mkdir(parents=True)
            (knowledge / "topics.index.json").write_bytes(b"{ not json")
            observations = knowledge / "observations" / "pattern"
            observations.mkdir(parents=True)
            (observations / "2026-10.jsonl").write_bytes(b'{"broken": \n')
    else:  # pragma: no cover - guards a misspelled variant name
        raise AssertionError(f"unknown variant {variant}")


def _planted_snapshot(root: Path) -> dict[str, bytes]:
    """Bytes (or link targets) of every planted knowledge-tooling path."""
    found: dict[str, bytes] = {}
    for top in ("docs/knowledge", ".claude", ".agents", "bin"):
        base = root / top
        if base.is_symlink() or base.is_file():
            found[top] = base.read_bytes() if base.is_file() else os.readlink(base).encode()
            continue
        for current, _dirs, names in os.walk(base):
            for name in names:
                path = Path(current) / name
                rel = path.relative_to(root).as_posix()
                found[rel] = (
                    os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
                )
    return found


def _is_planted(rel: str) -> bool:
    return rel.split("/", 1)[0] in {".claude", ".agents", "bin"} or rel.startswith("docs/knowledge")


def delivery_files(root: Path) -> dict[str, str]:
    """Every delivery-owned regular file (planted knowledge paths excluded), masked."""
    found: dict[str, str] = {}
    for current, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in names:
            path = Path(current) / name
            rel = path.relative_to(root).as_posix()
            if _is_planted(rel):
                continue
            text = _mask(root, path.read_text(encoding="utf-8"))
            if name == "shadow-evidence.log":
                # Frames carry run-derived receipt ids and checksums; keep their shape.
                text = _HEX_IDENTITY.sub("<HEX>", text)
            found[rel] = text
    return found


def delivery_env(
    root: Path, *, shadow: str | None, log: Path
) -> dict[str, str]:
    """The run environment: git identity, knowledge stubs first on PATH, shadow flag."""
    env = {k: v for k, v in os.environ.items() if k != "WORK_LOOP_SHADOW_SERVICES"}
    env.update({
        "GIT_AUTHOR_NAME": "Test Agent",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test Agent",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
        "KNOWLEDGE_STUB_LOG": str(log),
        "PATH": f"{root / 'bin'}{os.pathsep}{env.get('PATH', '')}",
    })
    if shadow is not None:
        env["WORK_LOOP_SHADOW_SERVICES"] = shadow
    return env


def run_delivery(base: Path, *, variant: str, shadow: str | None) -> Run:
    """Drive one full code-mode pass, init through done, in a fresh repository."""
    root = base / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    plant_knowledge_state(root, variant)
    run = Run(root=root, stub_log=base / "knowledge-calls.log")
    run.planted = _planted_snapshot(root)
    env = delivery_env(root, shadow=shadow, log=run.stub_log)
    spec_dir = root / "docs" / "specs" / FEATURE
    spec_dir.mkdir(parents=True)

    def call(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        done = subprocess.run(
            [sys.executable, str(script), *args], capture_output=True, text=True,
            encoding="utf-8", cwd=str(root), env=env, timeout=RUN_TIMEOUT, check=False,
        )
        label = f"{script.name} {' '.join(a for a in args if not a.startswith('/') and not _UUID.fullmatch(a))}"
        run.transcript.append((label, done.returncode, _mask(root, done.stdout), _mask(root, done.stderr)))
        return done

    def spec(status: str) -> None:
        (spec_dir / "spec.md").write_text(
            f"# Spec\n\n- **Status:** {status}\n\n## Acceptance Criteria\n\n- [ ] AC-001.\n",
            encoding="utf-8",
        )

    def engine(*args: str) -> subprocess.CompletedProcess[str]:
        return call(ENGINE, *args)

    def cohort(*args: str) -> subprocess.CompletedProcess[str]:
        return call(COHORT, *args)

    sd = str(spec_dir)
    spec("Draft")
    run_id = json.loads(engine("init", sd, "--mode", "code", "--json").stdout)["run_id"]
    cohort("init", sd, "--run-id", run_id)
    engine("transition", sd, "spec-ready")
    engine("transition", sd, "reviewers-clean")
    spec("Approved")
    engine("transition", sd, "spec-approved")
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n- **Status:** Approved\n\n### T1\n\n**Depends on:** none\n\n"
        "### T2\n\n**Depends on:** T1\n",
        encoding="utf-8",
    )
    engine("transition", sd, "plan-approved")
    cohort("approve-plan", sd, "--expect-run-id", run_id)
    cohort("schedule", sd, "--expect-run-id", run_id)
    engine("transition", sd, "plan-locked")
    cohort("dispatch-receipt", sd, "--task", "T1", "--wave-index", "0", "--receipt",
           "--expect-run-id", run_id)
    engine("transition", sd, "wave-complete")
    engine("transition", sd, "wave-passed", "--wave-index", "0")
    cohort("wave", "advance", sd, "--from-index", "0", "--expect-run-id", run_id)
    cohort("dispatch-receipt", sd, "--task", "T2", "--wave-index", "1",
           "--decline", "human-directed", "--expect-run-id", run_id)
    engine("transition", sd, "wave-complete")
    engine("transition", sd, "gates-clean")
    spec("Shipped")  # the code-review exit guard reads a shipped spec
    engine("transition", sd, "reviewers-clean", "--all-skipped")
    engine("transition", sd, "done")
    # Readiness and closeout decisions read after the pass.
    call(SPEC_STATUS, sd, "--expect", "Shipped")
    run.final["engine_status"] = _mask(root, engine("status", sd, "--json").stdout)
    run.final["cohort_status"] = _mask(root, cohort("status", sd, "--json").stdout)
    run.files = delivery_files(root)
    return run


def transitions(run: Run) -> list[str]:
    """The events the engine was asked to apply, in order."""
    return [
        label.split()[2] for label, *_ in run.transcript if label.startswith("loop-engine.py transition")
    ]


def decisions(run: Run) -> dict[str, object]:
    """Everything the delivery pass decided: step results, final state, and files."""
    return {"transcript": run.transcript, "final": run.final, "files": run.files}


@pytest.fixture(scope="module")
def runs(tmp_path_factory: pytest.TempPathFactory) -> dict[tuple[str, str | None], Run]:
    """One pass per (knowledge variant, shadow flag); computed once for the module."""
    results: dict[tuple[str, str | None], Run] = {}
    for variant in KNOWLEDGE_VARIANTS:
        for shadow in (None, SHADOW_ON):
            base = tmp_path_factory.mktemp(f"{variant}-{shadow or 'off'}")
            results[(variant, shadow)] = run_delivery(base, variant=variant, shadow=shadow)
    return results


# ── AC-0012: the pre-slice pass is pinned literally ─────────────────────────


def test_shadow_unset_pass_matches_the_pre_slice_run(runs: dict) -> None:
    """Shadow unset: eleven accepted transitions, DONE, and exactly the pre-slice file set."""
    run = runs[("absent", None)]
    assert transitions(run) == list(PRE_SLICE_TRANSITIONS)
    transition_results = [
        rc for label, rc, *_ in run.transcript if label.startswith("loop-engine.py transition")
    ]
    assert transition_results == [0] * len(PRE_SLICE_TRANSITIONS)
    assert json.loads(run.final["engine_status"])["state"] == "DONE"
    assert set(run.files) == PRE_SLICE_FILES
    cohort = json.loads(run.final["cohort_status"])
    assert cohort["plan_review_status"] == "approved"
    assert cohort["schedule_waves"] == [["T1"], ["T2"]]
    # Closeout readiness: the shipped spec satisfies the status guard.
    guard = [rc for label, rc, *_ in run.transcript if label.startswith("check-spec-status.py")]
    assert guard == [0]


def test_shadow_set_adds_only_the_shadow_files_and_keeps_every_decision(runs: dict) -> None:
    """Shadow set versus unset: same decisions, and only the shadow directory differs."""
    off, on = runs[("absent", None)], runs[("absent", SHADOW_ON)]
    added = set(on.files) - set(off.files)
    assert all(name.startswith(SHADOW_PREFIX) for name in added)
    assert added >= SHADOW_REQUIRED
    assert set(off.files) <= set(on.files)
    shared = {name: text for name, text in on.files.items() if not name.startswith(SHADOW_PREFIX)}
    assert shared == off.files
    assert on.transcript == off.transcript
    assert on.final == off.final


# ── AC-0007: knowledge tooling never changes a delivery decision ────────────


@pytest.mark.parametrize("shadow", [None, SHADOW_ON], ids=["shadow-unset", "shadow-set"])
@pytest.mark.parametrize("variant", KNOWLEDGE_VARIANTS[1:])
def test_knowledge_tooling_condition_leaves_every_decision_unchanged(
    runs: dict, variant: str, shadow: str | None
) -> None:
    """Spec, plan, review, acceptance, readiness, and closeout decisions match the baseline."""
    baseline, under_test = runs[("absent", shadow)], runs[(variant, shadow)]
    assert decisions(under_test) == decisions(baseline)
    assert transitions(under_test) == list(PRE_SLICE_TRANSITIONS)


@pytest.mark.parametrize("shadow", [None, SHADOW_ON], ids=["shadow-unset", "shadow-set"])
@pytest.mark.parametrize("variant", KNOWLEDGE_VARIANTS)
def test_delivery_never_reaches_for_knowledge_tooling(
    runs: dict, variant: str, shadow: str | None
) -> None:
    """No stub ran (a sleeping one would have hung the pass) and nothing planted changed."""
    run = runs[(variant, shadow)]
    assert run.stub_log is not None and not run.stub_log.exists()
    assert _planted_snapshot(run.root) == run.planted


@pytest.mark.parametrize(("variant", "expected"), [("refusing", 2), ("failing", 1)])
def test_a_planted_stub_would_have_been_visible_if_delivery_had_called_it(
    tmp_path: Path, variant: str, expected: int
) -> None:
    """Positive control: the stubs run, fail as named, and leave the log the isolation tests watch."""
    root, log = tmp_path / "repo", tmp_path / "calls.log"
    root.mkdir()
    plant_knowledge_state(root, variant)
    env = delivery_env(root, shadow=None, log=log)
    done = subprocess.run(
        [sys.executable, str(root / "bin" / "project-knowledge")],
        capture_output=True, text=True, env=env, timeout=RUN_TIMEOUT, check=False,
    )
    assert done.returncode == expected
    assert log.read_text(encoding="utf-8") == "invoked\n"


# ── AC-0004 and AC-0008: state inventory after every path ───────────────────

# Whole words (split on underscore, dash, dot) that mark a knowledge lifecycle record.
# "retry" is absent on purpose: the delivery review and implementation retry counters
# are listed in _DELIVERY_RETRY_KEYS, and a knowledge retry store would use a new key.
_FORBIDDEN_WORDS = frozenset({
    "queue", "queues", "cursor", "cursors", "ack", "acks", "acknowledgement",
    "acknowledgements", "skip", "skips", "admission", "admissions", "retention",
    "revocation", "revocations", "knowledge",
})


def _forbidden(name: str) -> bool:
    return bool(set(re.split(r"[_\-.]+", name.lower())) & _FORBIDDEN_WORDS)


# The retry counters are delivery-owned implementation and review retry state that
# predates knowledge and carries no knowledge meaning; the inventory names them
# so a new key cannot hide among them.
_DELIVERY_RETRY_KEYS = frozenset({
    "implementation_retry_count", "review_retry_count", "max_implementation_retries",
    "max_review_retries",
})


def _json_keys(value: object) -> set[str]:
    """Every object key in a JSON document, at any depth."""
    if isinstance(value, dict):
        keys = set(value)
        for child in value.values():
            keys |= _json_keys(child)
        return keys
    if isinstance(value, list):
        return set().union(*(_json_keys(item) for item in value)) if value else set()
    return set()


def inventory_violations(run: Run) -> list[str]:
    """Forbidden lifecycle state found in the delivery-owned files of *run*."""
    found: list[str] = []
    for name, text in run.files.items():
        if name.endswith(("engine-state.json", "state.json")):
            for key in _json_keys(json.loads(text)) - _DELIVERY_RETRY_KEYS:
                if _forbidden(key) or key.endswith("_retry_store"):
                    found.append(f"{name}: key {key}")
        if _forbidden(Path(name).stem) or "retry" in Path(name).stem.lower():
            found.append(f"{name}: file name")
        if name.endswith("events.jsonl"):
            for line in text.splitlines():
                event = json.loads(line)
                if any(_forbidden(key) for key in _json_keys(event)):
                    found.append(f"{name}: event key")
    return found


@pytest.mark.parametrize("shadow", [None, SHADOW_ON], ids=["shadow-unset", "shadow-set"])
@pytest.mark.parametrize("variant", KNOWLEDGE_VARIANTS)
def test_no_delivery_owned_knowledge_lifecycle_state_exists(
    runs: dict, variant: str, shadow: str | None
) -> None:
    """No queue, cursor, retry, ack, skip, admission, retention, revocation, or readiness key."""
    run = runs[(variant, shadow)]
    assert inventory_violations(run) == []
    assert {n for n in run.files if not n.startswith(SHADOW_PREFIX)} == PRE_SLICE_FILES
    shadow_files = {n for n in run.files if n.startswith(SHADOW_PREFIX)}
    assert (shadow_files >= SHADOW_REQUIRED) if shadow else not shadow_files
    # The legacy cohort state carries the review counters and nothing knowledge-shaped.
    cohort_keys = _json_keys(json.loads(run.final["cohort_status"]))
    assert not [k for k in cohort_keys if "knowledge" in k.lower()]
    # No knowledge transition: the engine applied only the pre-slice events.
    assert transitions(run) == list(PRE_SLICE_TRANSITIONS)
    events = run.files[".loop-run/events.jsonl"].splitlines()
    assert len(events) == len(PRE_SLICE_TRANSITIONS)


def test_the_inventory_catches_a_planted_lifecycle_record(runs: dict) -> None:
    """The inventory is not vacuous: each forbidden shape, once planted, is reported."""
    base = runs[("absent", None)]
    for key in ("knowledge_queue", "scan_cursor", "ack_log", "skip_log", "admission_log"):
        state = json.loads(base.files[f"{SPEC_REL}/state.json"])
        state[key] = []
        tampered = Run(root=base.root, files={**base.files, f"{SPEC_REL}/state.json": json.dumps(state)})
        assert inventory_violations(tampered), key
    stray = Run(root=base.root, files={**base.files, f"{SPEC_REL}/knowledge-cursor.json": "{}"})
    assert inventory_violations(stray)


# ── Pull scanning after the pass changes nothing ────────────────────────────


def _tool(script: Path, root: Path, *args: str, stdin: bytes = b"",
          shadow: str | None = None) -> subprocess.CompletedProcess[bytes]:
    env = {k: v for k, v in os.environ.items() if k != "WORK_LOOP_SHADOW_SERVICES"}
    if shadow is not None:
        env["WORK_LOOP_SHADOW_SERVICES"] = shadow
    return subprocess.run(
        [sys.executable, str(script), *args], input=stdin, capture_output=True,
        cwd=str(root), env=env, timeout=RUN_TIMEOUT, check=False,
    )


def _tree(root: Path) -> dict[str, bytes]:
    found: dict[str, bytes] = {}
    for current, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in names:
            path = Path(current) / name
            if not path.is_symlink():
                found[path.relative_to(root).as_posix()] = path.read_bytes()
    return found


def test_unset_shadow_scan_is_empty_and_feeding_the_candidate_mode_writes_nothing(
    runs: dict,
) -> None:
    """AC-0012 and AC-0004: an empty snapshot, an empty candidate frame, byte-identical tree."""
    run = runs[("failing", None)]
    before = _tree(run.root)
    page = _tool(FEED, run.root, "--root", str(run.root))
    assert page.returncode == 0, page.stderr
    parsed = json.loads(page.stdout)
    assert parsed["entries"] == [] and parsed["continuation"] is None
    assert parsed["shadow_services"] == "disabled"
    framed = _tool(CANDIDATES, run.root, "--candidates", stdin=page.stdout)
    assert framed.returncode == 0, framed.stderr
    assert b"<candidate " not in framed.stdout
    assert _tree(run.root) == before


def test_set_shadow_scan_of_the_pass_yields_no_candidate_and_writes_nothing(runs: dict) -> None:
    """A real shadow pass writes only engine-transition receipts, which are ineligible."""
    run = runs[("absent", SHADOW_ON)]
    before = _tree(run.root)
    page = _tool(FEED, run.root, "--root", str(run.root), shadow=SHADOW_ON)
    assert page.returncode == 0, page.stderr
    parsed = json.loads(page.stdout)
    facts = [e for e in parsed["entries"] if e["entry_kind"] == "fact"]
    assert facts, "the shadow pass must leave receipts for the scan to read"
    assert all(entry["observation"] is None for entry in facts)
    framed = _tool(CANDIDATES, run.root, "--candidates", stdin=page.stdout)
    assert framed.returncode == 0, framed.stderr
    assert b"<candidate " not in framed.stdout
    assert _tree(run.root) == before


def test_failing_scan_tooling_leaves_delivery_decisions_unchanged(runs: dict) -> None:
    """A refused feed, a refused candidate page, and a missing script change no delivery state."""
    run = runs[("failing", SHADOW_ON)]
    before = _tree(run.root)
    status = _tool(ENGINE, run.root, "status", str(run.root / SPEC_REL), "--json").stdout
    refused_feed = _tool(FEED, run.root, "--root", str(run.root / "missing"), shadow=SHADOW_ON)
    assert refused_feed.returncode == 2 and refused_feed.stdout == b""
    refused_page = _tool(CANDIDATES, run.root, "--candidates", stdin=b"not a page")
    assert refused_page.returncode != 0 and refused_page.stdout == b""
    assert _tool(ENGINE, run.root, "status", str(run.root / SPEC_REL), "--json").stdout == status
    assert _tree(run.root) == before


# ── AC-0008: source inventory ───────────────────────────────────────────────

_SOURCE_PROBE = re.compile(
    r"\bknowledge\b.{0,24}(queue|cursor|retry|acknowledg|skip|admission|retention|revocation)"
    r"|capture.{0,16}gate",
    re.IGNORECASE,
)
_SKILL_ROOTS = (_SKILLS / "work-loop", _SKILLS / "close-work")
# The one retained mention: the work-loop capture instruction for the existing gates.
RETAINED_PROBE_HITS = {
    ("work-loop/SKILL.md", "At each capture gate, admit only generalizable practice; dis"),
}
# Scripts that name the knowledge skill or store.  The engine, cohort, and shadow
# facade are deliberately absent: delivery never reaches for knowledge tooling.
KNOWLEDGE_AWARE_SCRIPTS = frozenset({
    "append-knowledge.py", "delivery-fact-feed.py", "lint-knowledge.py", "_delivery_feed.py",
    "_knowledge_projection.py",
})
_KNOWLEDGE_REFERENCE = re.compile(r"project[-_]knowledge|docs/knowledge|knowledge_store")


def _skill_files() -> list[Path]:
    found: list[Path] = []
    for root in _SKILL_ROOTS:
        for current, dirs, names in os.walk(root):
            dirs[:] = [d for d in dirs if d not in {"__pycache__"}]
            for name in names:
                path = Path(current) / name
                if stat.S_ISREG(os.lstat(path).st_mode) and path.suffix in {".md", ".py", ".json"}:
                    found.append(path)
    return found


def test_source_inventory_finds_only_the_retained_capture_gate_mention() -> None:
    """The plan's disconfirming probe finds no lifecycle store and no new capture gate."""
    hits: set[tuple[str, str]] = set()
    for path in _skill_files():
        for line in path.read_text(encoding="utf-8").splitlines():
            match = _SOURCE_PROBE.search(line)
            if match and "evals.json" not in path.name:
                rel = path.relative_to(_SKILLS).as_posix()
                hits.add((rel, line.strip().lstrip("- ")[:60]))
    assert hits == RETAINED_PROBE_HITS


def test_the_work_loop_names_only_the_retained_capture_gates() -> None:
    """spec-approved and plan-locked are the only gate names the skill hands to the producer."""
    text = (_SKILLS / "work-loop" / "SKILL.md").read_text(encoding="utf-8")
    section = text.split("### Project-knowledge integration", 1)[1].split("For durable work", 1)[0]
    assert "spec-approved" in section and "plan-locked" in section
    gates = set(re.findall(r"--semantic-gate[ =]([\w-]+)", text))
    assert gates <= {"spec-approved", "plan-locked"}


def test_no_delivery_runtime_script_references_knowledge_tooling() -> None:
    """Only the feed, projector, and legacy knowledge lint or retired writer name knowledge."""
    aware = {
        path.name
        for path in (_SKILLS / "work-loop" / "scripts").glob("*.py")
        if _KNOWLEDGE_REFERENCE.search(path.read_text(encoding="utf-8"))
    }
    assert aware <= KNOWLEDGE_AWARE_SCRIPTS, sorted(aware - KNOWLEDGE_AWARE_SCRIPTS)
    for runtime in ("loop-engine.py", "loop-cohort.py", "_compat_facade.py", "_acceptance.py"):
        assert runtime not in aware
