#!/usr/bin/env python3
"""Tests for `_loop_guards.py` — the shared read-only guard helpers.

Scope here is the module's *contract and safety*: how it loads, what it refuses,
and that it stays free of CLI concerns. The status guard, the managed readers, the
canonical contract hash, and the plan grammar are what remain; digest fidelity
across the relocation lives in `test_golden_fixtures.py`.

Run with pytest.
"""

from __future__ import annotations

import contextlib
import dataclasses
import importlib.util
import io
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest
import spawn_support as ss

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"
GUARDS = SCRIPTS / "_loop_guards.py"

# Every work-loop script these tests read, at a LITERAL path.
#
# `tools/lint-pack-test-boundary.py`'s `pack-tests-stay-in-pack` check requires a pack
# test's paths to be PROVABLY inside its own pack, and `SCRIPTS / <variable>` is not —
# the linter cannot see where a variable component lands. Literal components are
# provable. So a parametrised test that picks a script by name goes through this table
# rather than joining the name onto `SCRIPTS` itself.
_SCRIPT_PATHS = {
    "_loop_guards.py": SCRIPTS / "_loop_guards.py",
    "_statelock.py": SCRIPTS / "_statelock.py",
    "lint-spec-status.py": SCRIPTS / "lint-spec-status.py",
    "review-artifact.py": SCRIPTS / "review-artifact.py",
}


def _script(name: str) -> Path:
    """A work-loop script's path, by name, from the literal table above."""
    path = _SCRIPT_PATHS.get(name)
    assert path is not None, (
        f"{name} is not in _SCRIPT_PATHS — add a literal entry rather than joining "
        "the name onto SCRIPTS, which the pack-test boundary lint rejects"
    )
    return path


LINT_SPEC_STATUS = SCRIPTS / "lint-spec-status.py"

if not GUARDS.is_file():  # wrong parents[] depth after a move
    raise SystemExit(f"subject not found at {GUARDS} — check the parents[] depth")


# ── loading helpers ────────────────────────────────────────────────────────

def load_guards(path: Path = GUARDS, name: str = "_loop_guards_under_test"):
    """Load a copy of the module the way production does — unregistered, by path."""
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def g():
    return load_guards()


class Alarm:
    """Fail a blocking call instead of hanging the suite.

    NOT a performance assertion — the spec forbids those. It is a liveness guard: an
    unbounded read has no exit code to assert on, so the only way to distinguish
    "refused" from "blocked forever" is to interrupt it.
    """

    def __init__(self, seconds: int = 5):
        self.seconds = seconds

    def __enter__(self):
        self._old = signal.signal(signal.SIGALRM, self._raise)
        signal.alarm(self.seconds)
        return self

    def _raise(self, *_):
        raise TimeoutError("call blocked instead of refusing")

    def __exit__(self, *exc):
        signal.alarm(0)
        signal.signal(signal.SIGALRM, self._old)
        return False


# ── module load contract ───────────────────────────────────────────────────


def test_module_is_not_registered_in_sys_modules() -> None:
    """Unregistered, matching `_statelock.py`.

    Registration was specified in an earlier revision and withdrawn: `exec_module`
    does not remove a registered entry when the body raises, so a failed load would
    leave a half-executed module behind under a name whose `__file__` matches — and
    the next loader would accept it.
    """
    before = set(sys.modules)
    load_guards(name="_guards_registration_probe")
    assert "_guards_registration_probe" not in set(sys.modules) - before
    assert "_loop_guards" not in sys.modules


def test_frozen_dataclass_works_in_an_unregistered_module(g) -> None:
    """The regression test for omitting `from __future__ import annotations`.

    Under future-annotations, `dataclasses` resolves the defining module via
    `sys.modules.get(cls.__module__)` with no `None` guard, so creating a frozen
    dataclass in an unregistered `exec_module`'d module raises `AttributeError:
    'NoneType' object has no attribute '__dict__'`. Reintroducing that import turns
    this red — which is the only thing standing between a future tidy-up and a
    module that cannot load at all.
    """
    result = g.GuardResult(ok=True, message="fine")
    assert result.ok and result.reason is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.ok = False


def test_guardresult_invariant_raises_not_asserts(g) -> None:
    """`ok` and `reason` cannot disagree, and the check survives `-O`.

    The pre-existing engine convention was "None on success, a string on failure", so
    an adapter written `if result.reason:` would read `ok=False, reason=None` — the
    natural output of a containment bug — as success. `assert` would be stripped by
    `PYTHONOPTIMIZE`, so it raises `ValueError`.
    """
    with pytest.raises(ValueError):
        g.GuardResult(ok=True, reason="both set")
    with pytest.raises(ValueError):
        g.GuardResult(ok=False)
    probe = subprocess.run(
        [sys.executable, "-O", "-c",
         "import importlib.util,sys;"
         f"s=importlib.util.spec_from_file_location('g',{str(GUARDS)!r});"
         "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
         "\ntry:\n m.GuardResult(ok=True, reason='x')\n print('NOT_ENFORCED')\n"
         "except ValueError:\n print('ENFORCED')"],
        capture_output=True, text=True, check=False,
    )
    assert "ENFORCED" in probe.stdout, f"invariant lost under -O: {probe.stdout}{probe.stderr}"


def test_all_and_completeness_marker_agree(g) -> None:
    assert g._MODULE_COMPLETE is True
    missing = sorted(set(g.__all__) - set(dir(g)))
    assert not missing, f"__all__ names absent from the module: {missing}"


def test_module_complete_is_the_last_statement() -> None:
    """Position is the whole point — a truncation must remove it.

    If the marker sat anywhere but last, a file cut after it would still load, still
    pass the completeness check, and still be missing everything below.
    """
    import ast

    tree = ast.parse(GUARDS.read_text(encoding="utf-8"))
    last = tree.body[-1]
    assert isinstance(last, ast.Assign)
    assert [t.id for t in last.targets] == ["_MODULE_COMPLETE"]


# ── purity: no CLI concerns ────────────────────────────────────────────────

def test_module_has_no_cli_or_spawn_capability() -> None:
    """AST allowlist, so an added capability fails the gate rather than review.

    `subprocess` is the one that matters: this module is executed inside the process
    holding the engine-state lock, and the lock-hold budget's arithmetic depends on
    every under-lock subprocess being bounded and countable.
    """
    import ast

    tree = ast.parse(GUARDS.read_text(encoding="utf-8"))
    allowed = {
        "contextlib", "functools", "hashlib", "importlib", "io", "json", "os",
        "re", "stat", "sys", "collections", "dataclasses", "pathlib", "types",
    }
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= allowed, f"imports outside the allowlist: {sorted(imported - allowed)}"

    # Scanned over the AST, not the source text: the docstrings deliberately discuss
    # `subprocess`, `reconfigure` and `sys.exit` to explain why none of them appear
    # in the code, and a substring scan cannot tell prose from a call.
    # The `os.*` half comes from `spawn_support`, which the lock-hold scan and the
    # no-child-Python recorder also use. Restating a subset here is what let
    # `os.posix_spawn(...)` — and every `spawnl*`/`execl*`/`forkpty` variant — pass
    # this scan while failing the other two.
    banned_attrs = set(ss.OS_SPAWN_ATTRS) | {"exit", "argv", "reconfigure"}
    banned_roots = set(ss.SPAWN_MODULES) | {"urllib", "http", "argparse"}
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in banned_attrs:
            base = node.value
            root = base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
            if root in {"os", "sys"} or node.attr == "reconfigure":
                offenders.append(f"{root}.{node.attr} at line {node.lineno}")
        if isinstance(node, ast.Name) and node.id in banned_roots:
            offenders.append(f"{node.id} at line {node.lineno}")
    assert not offenders, f"forbidden capability reached in code: {offenders}"


def test_no_second_status_regex_in_the_guard_layer() -> None:
    """ADR-0061: one status parser. The allowlist admits `re`, so this needs saying.

    `canonical_contract` legitimately compiles heading and bold-lead patterns; what
    must not exist is a second `**Status:**` matcher competing with
    `lint-spec-status.py`'s.

    AC4 specifies an AST assertion, and the line-based form it replaces could not
    hold: `re.compile(` with its pattern on the following line evaded it entirely,
    which is the ordinary way a long pattern gets formatted. The walk inspects the
    pattern argument's constant value instead of the source line.
    """
    import ast as _ast

    tree = _ast.parse(GUARDS.read_text(encoding="utf-8"))
    offenders = []
    for node in _ast.walk(tree):
        if not (isinstance(node, _ast.Call) and isinstance(node.func, _ast.Attribute)
                and node.func.attr == "compile"
                and isinstance(node.func.value, _ast.Name)
                and node.func.value.id == "re"):
            continue
        if not node.args:
            continue
        pattern = node.args[0]
        # Joined string parts are inspected too — an f-string or implicit
        # concatenation is the other way a pattern hides from a source scan.
        parts = (
            [v.value for v in pattern.values if isinstance(v, _ast.Constant)]
            if isinstance(pattern, _ast.JoinedStr)
            else [pattern.value] if isinstance(pattern, _ast.Constant) else []
        )
        for part in parts:
            if isinstance(part, str) and "Status" in part:
                offenders.append(f"line {node.lineno}: re.compile({part!r})")

    assert not offenders, f"a second status regex: {offenders}"


def test_guards_work_under_a_stringio_stdout(g, tmp_path: Path) -> None:
    """The reverse hazard, which is the real one.

    `lint-spec-status.py` calls `sys.stdout.reconfigure(...)` at module scope, and
    `io.StringIO` has no `reconfigure`. Because the parser loads lazily inside a
    guard call, the first status read under a redirected stdout would raise
    `AttributeError` — surfacing as an `internal-error:` refusal of a legal document
    while the purity assertion above still saw zero bytes. The loader swaps in a
    throwaway `TextIOWrapper` for the exec, so this returns a real verdict.
    """
    art = tmp_path / "spec.md"
    art.write_text("# S\n\n- **Status:** Approved\n", encoding="utf-8")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        token = load_guards(name="_guards_stringio_probe").read_md_status(art)
    assert token == "Approved", f"parser load broke under a StringIO stdout: {token!r}"


def test_load_does_not_disturb_the_callers_streams(g, tmp_path: Path) -> None:
    """Verified on `encoding`/`errors` VALUES, not on object identity.

    `reconfigure` mutates the stream in place and never rebinds `sys.stdout`, so an
    identity assertion passes whether or not the loader does anything — it was the
    original form of this check and it was theatre.
    """
    art = tmp_path / "spec.md"
    art.write_text("# S\n\n- **Status:** Approved\n", encoding="utf-8")
    before = (sys.stdout.encoding, getattr(sys.stdout, "errors", None),
              sys.stderr.encoding, getattr(sys.stderr, "errors", None))
    load_guards(name="_guards_stream_probe").read_md_status(art)
    after = (sys.stdout.encoding, getattr(sys.stdout, "errors", None),
             sys.stderr.encoding, getattr(sys.stderr, "errors", None))
    assert before == after


# ── bounded reads: the property the child process used to supply ───────────

def _spec(tmp_path: Path, text: str = "# S\n\n- **Status:** Approved\n") -> Path:
    p = tmp_path / "spec.md"
    p.write_text(text, encoding="utf-8")
    return p


def test_fifo_artifact_refuses_instead_of_blocking(g, tmp_path: Path) -> None:
    """The finding both reviewers landed on, and the reason `O_NONBLOCK` is there.

    `read_text()` on a FIFO blocks forever, and so does `os.open` with
    `O_RDONLY | O_NOFOLLOW` — so the post-open `S_ISREG` re-check never runs. A child
    process bounded that with a 20 s subprocess timeout; in-process it would block
    inside the engine's critical section until the lock was judged stale and a second
    writer admitted, which is the lost update the lock exists to prevent.
    """
    fifo = tmp_path / "spec.md"
    os.mkfifo(fifo)
    with Alarm(5), pytest.raises(ValueError, match="regular file"):
        g.read_managed_text(fifo, "spec.md")


def test_directory_and_symlink_artifacts_refuse(g, tmp_path: Path) -> None:
    (tmp_path / "adir").mkdir()
    with pytest.raises(ValueError):
        g.read_managed_text(tmp_path / "adir", "adir")
    real = _spec(tmp_path)
    link = tmp_path / "link.md"
    try:
        link.symlink_to(real)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    with pytest.raises(ValueError):
        g.read_managed_text(link, "link.md")


def test_oversized_artifact_refuses(g, tmp_path: Path) -> None:
    """Sparse-extended, not 8 MiB of real bytes.

    The reader's size check reads `st_size` from the `lstat` *before* opening, so a
    sparse file trips it identically while occupying one block. Writing the bytes for
    real costs 8 MiB per run per fixture, and this suite already filled a temp
    filesystem once doing exactly that.
    """
    big = tmp_path / "plan.md"
    big.write_text("# P\n\n- **Status:** Approved\n", encoding="utf-8")
    os.truncate(big, 8 * 1024 * 1024 + 16)
    assert big.stat().st_blocks * 512 < 64 * 1024, "fixture is not sparse"
    with pytest.raises(ValueError, match="8 MiB"):
        g.read_managed_text(big, "plan.md")


def test_non_finite_json_refuses_rather_than_overflowing(g, tmp_path: Path) -> None:
    """`json.loads` accepts `Infinity`; `int(float("inf"))` then raises OverflowError.

    OverflowError is outside every exception set the guards convert, so an `Infinity`
    retry cap used to become a traceback rather than a refusal.
    """
    state = tmp_path / "data.json"
    state.write_text('{"schema_version": 1, "max_review_retries": Infinity}', encoding="utf-8")
    with pytest.raises(ValueError, match="non-finite"):
        g.read_managed_json(state, "data.json")
    state.write_text('{"schema_version": 1, "review_retry_count": NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="non-finite"):
        g.read_managed_json(state, "data.json")


def test_symlinked_ancestor_is_accepted(g, tmp_path: Path) -> None:
    """The false-refusal surface, which is the untested half.

    The symlink guard is leaf-scoped by design — every caller resolves the spec dir
    first — so a spec directory reached *through* a symlinked ancestor must still
    work. `pytest`'s `tmp_path` resolves through `/private/var` on macOS, so no
    existing test crosses one; the trap is recorded in
    `docs/knowledge/topics/pytest-tmp-path-hides-symlinked-ancestor-path-bugs.json`.
    """
    real_parent = tmp_path / "real"
    real_parent.mkdir()
    art = _spec(real_parent)
    linked_parent = tmp_path / "via-link"
    try:
        linked_parent.symlink_to(real_parent, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    assert g.sha256_canonical_contract(linked_parent / "spec.md") == \
        g.sha256_canonical_contract(art)


# ── containment ────────────────────────────────────────────────────────────

def test_contained_converts_exception_to_refusal(g) -> None:
    @g.contained
    def boom(_):
        raise RuntimeError("multi\nline\nboom")

    result = boom(1)
    assert result.ok is False
    assert result.reason.startswith(f"{g.INTERNAL_ERROR}: ")
    # The failing function is named. Six guards share this decorator, so without it an
    # operator cannot tell which decision failed to be made.
    assert "boom" in result.reason, f"reason does not name the guard: {result.reason!r}"
    assert "RuntimeError" in result.reason
    assert "\n" not in result.reason, "reason must be one line — it is a CLI contract"


def test_contained_passes_baseexception_through(g) -> None:
    """`Exception` only.

    Swallowing `KeyboardInterrupt` would make Ctrl-C look like a policy refusal, and
    swallowing a `SystemExit` — which a mis-set `__name__` on the parser load can
    produce, with code 0 — would report success from a guard that evaluated nothing.
    """
    @g.contained
    def interrupted(_):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        interrupted(1)

    @g.contained
    def exiting(_):
        raise SystemExit(0)

    with pytest.raises(SystemExit):
        exiting(1)


# The six guards, with one valid-shaped call each. Kept as data so the containment
# and purity checks below iterate the same set, and so adding a seventh guard without
# adding it here shows up as a coverage gap rather than passing silently — see
# `test_the_six_guard_table_matches_all`.
SIX_GUARDS = {
    "check_identity": {"expect_run_id": "11111111-2222-3333-4444-555555555555"},
    "check_plan_current": {},
    "check_schedule_current": {},
    "check_phase": {"phase": "implement"},
    "check_wave": {"expect": "more"},
    "check_artifact_status": {"filename": "spec.md", "expect": "Approved"},
}


def g_internal_error_marker() -> str:
    """`INTERNAL_ERROR`, read from the module rather than restated as a literal."""
    return load_guards(name="_guards_marker").INTERNAL_ERROR


@pytest.mark.parametrize("blank", ["", "   ", "\t\n"])
def test_a_blank_reason_is_rejected_at_construction(g, blank: str) -> None:
    """The fail-open the `ok`/`reason` invariant alone does not close.

    That invariant compares `reason is None`, so `GuardResult(ok=False, reason="")`
    constructed happily — and any adapter written `if result.reason:` reads such a
    refusal as SUCCESS. `test_no_adapter_branches_on_reason` closes the consumer side;
    this closes the producer side, and without it that test's docstring asserts in
    prose something the suite checked nowhere. Whitespace-only counts as blank, because
    `_one_line` collapses it to nothing.
    """
    with pytest.raises(ValueError, match="blank"):
        g.GuardResult(ok=False, reason=blank)

    # The legitimate shapes still construct.
    assert g.GuardResult(ok=True, reason=None).ok is True
    assert g.GuardResult(ok=False, reason="a real reason").ok is False


def test_reason_never_carries_raw_artifact_content(g, tmp_path: Path) -> None:
    """A refusal is printed to a stderr the agent captures and logs."""
    secret = "SENSITIVE-ARTIFACT-BODY-9f3c"
    state = tmp_path / "data.json"
    state.write_text('{"schema_version": 1, "run_id": "' + secret + '"}', encoding="utf-8")

    @g.contained
    def read_it(path):
        g.read_managed_json(path, "data.json")
        raise RuntimeError("failed after reading")

    assert secret not in (read_it(state).reason or "")


# ── AC12 — the widened except clauses on the lock-holding mutation verbs ───

RUN_ID = "11111111-2222-3333-4444-555555555555"


# `pre_approved` selects WHICH hash block inside `cmd_approve_plan` is exercised, and
# it is not cosmetic. With `plan_review_status: "pending"` the crash-window
# `_read_md_status` refuses first, so the two `sha256_canonical_contract` blocks are
# never reached — every approve-plan row passed while the `except` tuples they exist to
# cover were narrowed back. `"approved"` takes the idempotency branch, where the hash
# comparison runs BEFORE any status read.


# ── fail-closed status parsing ─────────────────────────────────────────────


# ── the loader's failure modes ─────────────────────────────────────────────


def test_loaded_parser_does_not_execute_its_main_block(g, tmp_path: Path) -> None:
    """`lint-spec-status.py` ends in `if __name__ == "__main__": sys.exit(main())`.

    A loader that gets `__name__` wrong runs it, and `SystemExit(0)` escaping a guard
    would report success from a transition that evaluated nothing — while holding the
    engine-state lock.
    """
    art = tmp_path / "spec.md"
    art.write_text("# S\n\n- **Status:** Approved\n", encoding="utf-8")
    assert g.read_md_status(art) == "Approved"
    parser = g._lint_spec_status()
    assert parser.__name__ != "__main__"


# ── the loader is duplicated on purpose; keep the copies identical ─────────


# ══ T1b: the six guard decisions ═══════════════════════════════════════════
#
# One case per branch each guard can take. The point is not coverage for its own
# sake: each of these branches is a refusal the FSM depends on, and the whole risk
# of moving the guards in-process is that one silently stops firing.

@pytest.fixture
def spec(tmp_path: Path):
    """A spec dir factory holding a spec and a plan with the given statuses."""
    def build(*, spec_status="Approved", plan_status="Approved", no_spec=False, no_plan=False) -> Path:
        d = tmp_path / f"spec{len(list(tmp_path.iterdir()))}"
        d.mkdir()
        if not no_spec:
            (d / "spec.md").write_text(SPEC_MD.format(s=spec_status), encoding="utf-8")
        if not no_plan:
            (d / "plan.md").write_text(PLAN_MD.format(s=plan_status), encoding="utf-8")
        return d
    return build


SPEC_MD = "# Spec\n\n- **Status:** {s}\n\n## Acceptance Criteria\n\n- [ ] AC1\n"
PLAN_MD = "# Plan\n\n- **Status:** {s}\n\n## T1 First\n\n**Depends on:** none\n"


# ── check_identity ─────────────────────────────────────────────────────────


# ── check_plan_current ─────────────────────────────────────────────────────


# ── check_schedule_current ─────────────────────────────────────────────────


# ── check_phase ────────────────────────────────────────────────────────────


# ── check_wave ─────────────────────────────────────────────────────────────


# ── check_artifact_status ──────────────────────────────────────────────────

def test_check_artifact_status_branches(g, spec) -> None:
    d = spec(spec_status="Shipped", plan_status="Done")
    ok = g.check_artifact_status(d, filename="spec.md", expect="Shipped")
    assert ok.ok and ok.data["status"] == "Shipped"
    assert g.check_artifact_status(d, filename="plan.md", expect="Done").ok

    r = g.check_artifact_status(d, filename="spec.md", expect="Approved")
    assert not r.ok and "Status is 'Shipped', expected 'Approved'" in r.reason

    missing = spec(no_spec=True)
    assert "not found" in g.check_artifact_status(missing, filename="spec.md", expect="X").reason

    nostatus = spec()
    (nostatus / "spec.md").write_text("# no status here\n", encoding="utf-8")
    r = g.check_artifact_status(nostatus, filename="spec.md", expect="Shipped")
    assert not r.ok and "no **Status:** line" in r.reason


@pytest.mark.parametrize(
    "status, expected_ok",
    [
        ("Implementing", True),
        ("Draft", False),
        ("Approved", False),
        ("Archived", False),
        ("Shipped", False),
    ],
)
def test_check_artifact_status_expect_implementing_is_exact(g, spec, status, expected_ok) -> None:
    """The existing API can enforce an intermediate review unit without widening it.

    Mutation proof: making ``check_artifact_status`` return success for a status
    mismatch flips each non-Implementing assertion.
    """
    result = g.check_artifact_status(
        spec(spec_status=status), filename="spec.md", expect="Implementing"
    )
    assert result.ok is expected_ok


def test_check_artifact_status_filename_is_one_component(g, spec) -> None:
    """AC9. A single component is what makes the confinement honest.

    `O_NOFOLLOW` rejects a symlink only at the FINAL component, so `sub/spec.md` with
    `sub` swapped after the prefix check would read outside the directory. And the
    charset alone admits every dot segment — the class `0cb5c213` fixed the day
    before this change — so dot-only names are rejected by segment equality, not by
    narrowing the charset, which would also reject legitimate leading-dot names.
    """
    d = spec()
    (d / "sub").mkdir()
    (d / "sub" / "spec.md").write_text(SPEC_MD.format(s="Approved"), encoding="utf-8")
    for bad in ("sub/spec.md", "..", ".", "...", "../spec.md", "a/b/c.md"):
        r = g.check_artifact_status(d, filename=bad, expect="Approved")
        assert not r.ok, f"{bad!r} was accepted"
        assert "single path component" in r.reason or "within spec-dir" in r.reason

    # A legitimate leading dot is still fine — the guard is segment equality.
    (d / ".hidden.md").write_text(SPEC_MD.format(s="Approved"), encoding="utf-8")
    assert g.check_artifact_status(d, filename=".hidden.md", expect="Approved").ok


def test_check_artifact_status_refuses_unsafe_targets(g, spec) -> None:
    d = spec()
    (d / "spec.md").unlink()
    os.mkfifo(d / "spec.md")
    with Alarm(5):
        r = g.check_artifact_status(d, filename="spec.md", expect="Approved")
    assert not r.ok and "regular file" in r.reason

    d2 = spec()
    real = d2 / "real.md"
    real.write_text(SPEC_MD.format(s="Approved"), encoding="utf-8")
    (d2 / "spec.md").unlink()
    try:
        (d2 / "spec.md").symlink_to(real)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    r = g.check_artifact_status(d2, filename="spec.md", expect="Approved")
    assert not r.ok, "a symlinked artifact was accepted"


# ── cross-guard properties ─────────────────────────────────────────────────


# ══ check --phase wave-exit: the verdict table ═════════════════════════════
#
# Contract: § The
# `check --phase wave-exit` verdict. The contract is that exactly one row
# applies to any cohort state and the rows jointly cover every cohort state, so
# branch order in the implementation is an optimisation rather than the thing
# that decides behaviour. These cases assert both halves: the per-row verdicts,
# and the partition over a generated domain.

_ABSENT = object()

# Row labels, matching the spec's order.
_ROWS = (
    "read-refuses", "schema-unsupported", "malformed", "container-absent",
    "pointer-invalid", "wave-malformed", "accounted", "unaccounted",
)

# Per row: the expected `ok`, and a substring the refusal or notice must carry.
# A partition walk alone cannot catch a row implemented with the wrong verdict —
# a wrong verdict is neither an overlap nor a gap — so the expected verdict is
# declared here and asserted for every state in the domain.
_ROW_VERDICTS = {
    "schema-unsupported": (True, ""),
    "malformed": (False, "malformed"),
    "container-absent": (True, "not enforced"),
    "pointer-invalid": (False, "current_wave_index"),
    "wave-malformed": (False, "malformed"),
    "accounted": (True, ""),
    "unaccounted": (False, "no dispatch receipt"),
}


# ── the read-refusal row, and the reader's refusal vocabulary ──────────────

# Every kind the guard's state acquisition can refuse with, read from
# `_loop_guards.py` and asserted complete by the survey below. The read axis of
# the partition is two-valued because no row discriminates among these kinds, and
# what licenses that collapse is the assertion that each one lands on the
# read-refusal row and nowhere else.
_ACQUISITION_REFUSALS = (
    "spec-dir cannot be examined: {exc}",
    "spec-dir is not a directory: {spec_dir}",
    "{label} cannot be examined: {exc}",
    "{label} must be a regular file",
    "{label} exceeds {_MAX_MANAGED_JSON_BYTES}-byte (8 MiB) limit",
    "{label} cannot be opened safely: {exc}",
    "{label} changed while being opened",
    "{label} could not be read safely: {exc}",
    "{label} changed while being read",
    "{label} contains the non-finite number {token}",
    "{label} contains the non-finite number {_scalar(token)}",
    "{label} is not valid UTF-8",
    "{label} malformed: {exc.msg} at line {exc.lineno}",
    "{label} is nested too deeply to parse",
    "{label} root must be an object",
)


# ── one declaration, not two copies ───────────────────────────────────────


# ── the repair-round verdict, and the superseded clause it rests on ────────
#
# Spec: docs/specs/repair-round-dispatch-assertion/spec.md.
#
# The clause lives inside `unaccounted_wave_tasks` rather than beside it because
# that predicate has two shipped consumers — the wave exit and `wave advance`'s
# advancing branch — and a round-scoping rule reaching one only is the defect
# this delivery exists to prevent from recurring in a new form.


# ── surviving module contract ──────────────────────────────────────────────

def test_import_performs_no_file_io() -> None:
    """Importing the module must not touch the filesystem.

    `io.open` is the load-bearing patch point (a `Path.read_text()` goes through it),
    and `os.open` is kept because the guard readers use it directly.
    """
    opened: list = []

    def _record(mod, attr):
        real = getattr(mod, attr)

        def spy(*a, **k):
            opened.append(f"{attr}:{a[0] if a else '?'}")
            return real(*a, **k)

        setattr(mod, attr, spy)
        return real

    real_os_open = _record(os, "open")
    real_io_open = _record(io, "open")
    try:
        mod = load_guards(name="_guards_io_probe")
    finally:
        os.open = real_os_open
        io.open = real_io_open

    assert not opened, f"import opened {len(opened)} file(s): {opened[:3]}"
    assert dict(mod.DEFAULTS) == {"max_implementation_retries": 5, "max_review_retries": 5}


def test_missing_artifact_raises_filenotfound_not_valueerror(g, tmp_path: Path) -> None:
    """Absence stays distinguishable from every integrity failure."""
    with pytest.raises(FileNotFoundError):
        g.read_managed_text(tmp_path / "nope.md", "nope.md")


def test_an_external_scalar_is_bounded_in_a_reason(g, spec) -> None:
    """The bound sits on the interpolation: a huge status token never reaches a reason whole."""
    d = spec()
    huge = "A" * 100_000
    (d / "spec.md").write_text(f"# Spec\n\n- **Status:** {huge}\n", encoding="utf-8")
    result = g.check_artifact_status(d, filename="spec.md", expect="Shipped")
    assert result.ok is False
    assert len(result.reason) < 500 and len(result.reason.splitlines()) == 1
    assert huge not in result.reason and "…" in result.reason


def test_a_control_character_cannot_reach_a_reason(g, spec) -> None:
    """ESC and its siblings are escaped, not passed through to a captured stream."""
    d = spec()
    (d / "spec.md").write_text(
        "# Spec\n\n- **Status:** Draft\x1b[2J\x1b[31mFAKE-OK\n", encoding="utf-8"
    )
    result = g.check_artifact_status(d, filename="spec.md", expect="Shipped")
    assert result.ok is False
    assert "\x1b" not in result.reason and "\\x1b" in result.reason


def test_a_crashing_guard_is_refused_not_raised(g, tmp_path: Path, monkeypatch) -> None:
    """`contained` converts an unexpected exception into a refusal that names the guard."""
    monkeypatch.setattr(g, "read_md_status", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")))
    d = tmp_path / "d"
    d.mkdir()
    (d / "spec.md").write_text("# Spec\n\n- **Status:** Draft\n", encoding="utf-8")
    result = g.check_artifact_status(d, filename="spec.md", expect="Draft")
    assert result.ok is False and g.INTERNAL_ERROR in result.reason
