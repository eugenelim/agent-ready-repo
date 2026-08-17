#!/usr/bin/env python3
"""Tests for `_loop_guards.py` — the shared read-only guard API (T1a).

Scope here is the module's *contract and safety*: how it loads, what it refuses,
and that it stays free of the CLI concerns the engine cannot afford to inherit.
The six guard decisions themselves arrive in T1b; digest fidelity across the
relocation lives in `test_golden_fixtures.py`, which asserts against goldens
captured before anything moved.

The organising idea: deleting the child process removed two properties nobody had
written down — a subprocess timeout bounding every artifact read, and an exit code
converting every unexpected exception into a refusal. Most of what follows is
those two properties, re-established explicitly and tested where they can fail.

Run with pytest.
"""

from __future__ import annotations

import contextlib
import dataclasses
import importlib.util
import io
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"
GUARDS = SCRIPTS / "_loop_guards.py"
COHORT = SCRIPTS / "loop-cohort.py"
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


def run_cohort(*args, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(COHORT), *[str(a) for a in args]],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=False, cwd=str(cwd) if cwd else None,
    )


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

def test_import_performs_no_file_io() -> None:
    """Importing the module must not touch the filesystem.

    The first guard call happens inside the engine's critical section. `DEFAULTS`
    used to be a module-level dict computed from two uncapped
    `TEMPLATE_PATH.read_text()` calls, so importing the module there would have
    performed an unbounded read while holding the lock.

    `io.open` is the load-bearing patch point, and patching `os.open` alone made this
    test unable to fail. Probe-verified, on this interpreter, in both directions:

        Path.read_text() observed by   os.open -> False   io.open -> True
                                  builtins.open -> False  io.open_code -> False
        exec_module's own source read trips io.open -> False

    So `os.open` — the regression's actual shape is a `read_text()` — was invisible,
    while `io.open` sees it and does *not* false-positive on the loader reading the
    module's own source. `os.open` is kept because the guard readers use it directly,
    so a module-level `read_managed_*` call is caught by that half.
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

    # The observable, independent of which primitive a future edit reaches for:
    # `DEFAULTS` is bound but unpopulated until first subscript.
    assert mod.DEFAULTS._values is None, (
        "DEFAULTS was populated during import — it must stay lazy"
    )
    assert mod.DEFAULTS["max_review_retries"] is not None
    assert mod.DEFAULTS._values is not None, "first subscript did not populate DEFAULTS"


def test_defaults_is_bound_eagerly_and_populated_lazily(g) -> None:
    """Both properties are required, and they pull against each other.

    `test_loop_cohort_max_iter_single_source.py` subscripts `mod.DEFAULTS` straight
    after `exec_module` with no verb invoked, so a plain function or `cached_property`
    breaks it — while eager *population* is the file I/O the previous test forbids.
    """
    template = json.loads(
        (SCRIPTS.parent / "assets" / "state.json").read_text(encoding="utf-8")
    )
    assert g.DEFAULTS["max_implementation_retries"] == template["max_implementation_retries"]
    assert g.DEFAULTS["max_review_retries"] == template["max_review_retries"]
    assert set(g.DEFAULTS) == {"max_implementation_retries", "max_review_retries"}


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


def test_load_writes_no_bytecode() -> None:
    """No `.pyc` for the guard module, measured across a real CLI invocation."""
    cache = SCRIPTS / "__pycache__"
    before = {p.name for p in cache.glob("_loop_guards*.pyc")} if cache.is_dir() else set()
    run = run_cohort("--help")
    assert run.returncode == 0
    after = {p.name for p in cache.glob("_loop_guards*.pyc")} if cache.is_dir() else set()
    assert after == before, f"a load wrote bytecode: {sorted(after - before)}"


@pytest.mark.parametrize("preset", [True, False])
@pytest.mark.parametrize("outcome", ["success", "failure"])
def test_load_restores_dont_write_bytecode_to_its_prior_value(
    preset: bool, outcome: str, tmp_path: Path,
) -> None:
    """AC13: restored to its PRIOR value, after both a successful and a failed load.

    The previous form asserted `sys.dont_write_bytecode is previous` where `previous`
    was read in this process and the load happened in a subprocess — comparing the
    test process's untouched flag to itself, which cannot fail in either direction.
    Both directions matter: restoring to a hardcoded `False` would silently defeat a
    host interpreter started with `-B`.

    Run in-process, with the flag pre-set both ways, and over a load that raises as
    well as one that succeeds — the restore is in a `finally`, and only the failing
    case proves it.
    """
    sandbox = tmp_path / "scripts"
    sandbox.mkdir()
    (sandbox / "loop-cohort.py").write_bytes((SCRIPTS / "loop-cohort.py").read_bytes())
    if outcome == "success":
        (sandbox / "_loop_guards.py").write_bytes(GUARDS.read_bytes())
        (sandbox.parent / "assets").mkdir()
        (sandbox.parent / "assets" / "state.json").write_bytes(
            (SCRIPTS.parent / "assets" / "state.json").read_bytes()
        )
    else:
        (sandbox / "_loop_guards.py").write_text("def broken(  # truncated\n",
                                                 encoding="utf-8")

    cohort = load_guards(path=sandbox / "loop-cohort.py",
                         name=f"_cohort_flag_{preset}_{outcome}")

    original = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = preset
        if outcome == "success":
            cohort.load_guards()
        else:
            with pytest.raises(cohort.GuardsUnavailable):
                cohort.load_guards()
        assert sys.dont_write_bytecode is preset, (
            f"after a {outcome} load with the flag pre-set to {preset}, it is "
            f"{sys.dont_write_bytecode} — the prior value was not restored"
        )
    finally:
        sys.dont_write_bytecode = original


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
        "re", "stat", "sys", "collections", "dataclasses", "pathlib",
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
    banned_attrs = {
        "system", "popen", "fork", "execv", "execve", "execvp", "execvpe",
        "spawnv", "spawnve", "exit", "argv", "reconfigure",
    }
    banned_roots = {"subprocess", "multiprocessing", "socket", "urllib", "argparse"}
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


def test_guards_print_nothing(g, spec, tmp_path: Path) -> None:
    """Zero bytes on both streams, and the verdict is asserted too.

    An empty-stream assertion alone passes on a guard that refused for an unrelated
    reason — including the specific case where capturing through an `io.StringIO`
    makes the lazily-loaded parser's module-scope `reconfigure` raise. So each call
    asserts its real result.

    Two corrections against AC6's wording. It says "calling any guard produces zero
    bytes", and the helpers alone are not the six `GuardResult` guards — so all six
    are now driven inside the captured block, each with its verdict asserted. And the
    capture is a `TextIOWrapper` over a `BytesIO` rather than a `StringIO`, as AC6
    specifies: a `StringIO` has no `buffer`, so a stream-mutating callee behaves
    differently under it than under a real redirected stdout, and the whole point is
    to measure bytes on something stream-shaped.
    """
    art = tmp_path / "spec.md"
    art.write_text("# S\n\n- **Status:** Shipped\n\n## Acceptance Criteria\n\n- [x] a\n",
                   encoding="utf-8")
    d = spec(approved=True)

    out_raw, err_raw = io.BytesIO(), io.BytesIO()
    out = io.TextIOWrapper(out_raw, encoding="utf-8", write_through=True)
    err = io.TextIOWrapper(err_raw, encoding="utf-8", write_through=True)
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        digest = g.sha256_canonical_contract(art)
        token = g.read_md_status(art)
        legal = g.assert_status_legal("probe", art)
        run_id = g.validate_run_id({"schema_version": 1, "run_id": "a"}, "a", verb="probe")
        verdicts = {
            "check_identity": g.check_identity(d, expect_run_id="run-1"),
            "check_plan_current": g.check_plan_current(d, require_schedule=True),
            "check_schedule_current": g.check_schedule_current(d),
            "check_phase": g.check_phase(d, phase="review"),
            "check_wave": g.check_wave(d, expect="more"),
            "check_artifact_status": g.check_artifact_status(
                d, filename="spec.md", expect="Approved"),
        }
        out.flush()
        err.flush()

    assert len(digest) == 64
    assert token == "Shipped"
    assert legal is None and run_id is None
    # Each guard's real result, so an empty stream cannot be the side effect of a
    # guard that refused early for an unrelated reason.
    assert set(verdicts) == set(SIX_GUARDS), "not every guard ran inside the capture"
    for name, verdict in verdicts.items():
        assert isinstance(verdict, g.GuardResult), f"{name} returned no GuardResult"
        assert verdict.ok, f"{name} refused inside the capture: {verdict.reason}"

    assert out_raw.getvalue() == b"" and err_raw.getvalue() == b"", (
        f"a guard wrote to a stream: stdout={out_raw.getvalue()!r} "
        f"stderr={err_raw.getvalue()!r}"
    )


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


def test_missing_artifact_raises_filenotfound_not_valueerror(g, tmp_path: Path) -> None:
    """The one case that must stay distinguishable.

    `_template_retry_cap` falls back only on `FileNotFoundError` — an adopter tree
    that ships no template — and refuses on every integrity failure. Folding absence
    into `ValueError` would silently restore the 5/5 fail-open.
    """
    with pytest.raises(FileNotFoundError):
        g.read_managed_text(tmp_path / "nope.md", "nope.md")


def test_non_finite_json_refuses_rather_than_overflowing(g, tmp_path: Path) -> None:
    """`json.loads` accepts `Infinity`; `int(float("inf"))` then raises OverflowError.

    OverflowError is outside every exception set the guards convert, so an `Infinity`
    retry cap used to become a traceback rather than a refusal.
    """
    state = tmp_path / "state.json"
    state.write_text('{"schema_version": 1, "max_review_retries": Infinity}', encoding="utf-8")
    with pytest.raises(ValueError, match="non-finite"):
        g.read_managed_json(state, "state.json")
    state.write_text('{"schema_version": 1, "review_retry_count": NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="non-finite"):
        g.read_managed_json(state, "state.json")


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


def test_the_six_guard_table_matches_all(g) -> None:
    """`SIX_GUARDS` must stay the full set, or the tests below silently under-cover."""
    exported = {n for n in g.__all__ if n.startswith("check_")}
    assert set(SIX_GUARDS) == exported, (
        f"SIX_GUARDS and __all__'s guards disagree: "
        f"only-in-table={sorted(set(SIX_GUARDS) - exported)}, "
        f"only-in-__all__={sorted(exported - set(SIX_GUARDS))}"
    )


@pytest.mark.parametrize("guard_name", sorted(SIX_GUARDS))
def test_every_guard_contains_an_unexpected_exception(guard_name, tmp_path) -> None:
    """AC10, per guard. Removing `@contained` from any one of the six must fail here.

    The existing containment tests decorate ad-hoc local functions, which proves the
    decorator works and nothing about whether the guards carry it. All six do today,
    so this is purely a regression net — and it is the mutation that was not run: with
    only the local-function tests, deleting `@contained` from `check_phase` left the
    suite green while restoring a traceback out of a process holding the state lock.

    The injection targets the two module-level entry helpers every guard funnels
    through (`_state_or_reason` for five, `_require_spec_dir` for
    `check_artifact_status`), so the exception originates *inside* the guard body
    rather than being handed to it as an argument.
    """
    g = load_guards(name=f"_guards_contain_{guard_name}")
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()

    def boom(*_a, **_k):
        raise RuntimeError("injected\nmulti-line\nfailure")

    g._state_or_reason = boom
    g._require_spec_dir = boom

    result = getattr(g, guard_name)(spec_dir, **SIX_GUARDS[guard_name])

    assert isinstance(result, g.GuardResult), (
        f"{guard_name} returned {type(result).__name__}, not a GuardResult — "
        "@contained is missing, so the exception escaped"
    )
    assert result.ok is False
    assert result.reason.startswith(g.INTERNAL_ERROR), (
        f"{guard_name} refused without the internal-error marker: {result.reason!r}"
    )
    assert guard_name in result.reason, (
        f"the reason does not name the failing guard: {result.reason!r}"
    )
    assert "RuntimeError" in result.reason
    assert "\n" not in result.reason, "a reason is a one-line CLI contract"


def test_a_crashing_guard_is_a_nonzero_exit_with_no_traceback(tmp_path: Path) -> None:
    """AC10's other half: the containment holds at the CLI boundary too.

    In-process containment is necessary but not sufficient — the adapter still has to
    map a crash-refusal onto a non-zero exit and a single stderr line. Driven through
    `check-spec-status.py`, whose one guard is `check_artifact_status`, with the
    sandbox's guard module edited to raise from inside that guard.
    """
    sandbox = tmp_path / "scripts"
    sandbox.mkdir()
    for name in ("_loop_guards.py", "lint-spec-status.py", "check-spec-status.py"):
        (sandbox / name).write_bytes((SCRIPTS / name).read_bytes())
    (sandbox.parent / "assets").mkdir()
    (sandbox.parent / "assets" / "state.json").write_bytes(
        (SCRIPTS.parent / "assets" / "state.json").read_bytes()
    )

    # Inject at the guard's first statement, so the raise happens inside the body
    # that `@contained` wraps.
    guard_src = (sandbox / "_loop_guards.py").read_text(encoding="utf-8")
    anchor = "def _require_spec_dir("
    assert anchor in guard_src, "injection anchor moved — update this test"
    head, _, tail = guard_src.partition(anchor)
    body_start = tail.index("\n", tail.index('"""', tail.index('"""') + 3)) + 1
    guard_src = (
        head + anchor + tail[:body_start]
        + '    raise RuntimeError("injected crash")\n' + tail[body_start:]
    )
    (sandbox / "_loop_guards.py").write_text(guard_src, encoding="utf-8")

    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    (spec_dir / "spec.md").write_text("# S\n\n- **Status:** Approved\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(sandbox / "check-spec-status.py"), str(spec_dir),
         "--expect", "Approved"],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode != 0, "a crashing guard reported success"
    assert "Traceback" not in proc.stderr, (
        f"the crash escaped as a traceback:\n{proc.stderr}"
    )
    assert len(proc.stderr.strip().splitlines()) == 1, (
        f"expected one stderr line, got:\n{proc.stderr}"
    )
    assert g_internal_error_marker() in proc.stderr, (
        f"the refusal is not marked as an internal error: {proc.stderr!r}"
    )


def g_internal_error_marker() -> str:
    """`INTERNAL_ERROR`, read from the module rather than restated as a literal."""
    return load_guards(name="_guards_marker").INTERNAL_ERROR


def test_contained_reason_never_returns_none_on_failure(g) -> None:
    """The mutation-path helpers, where `None` means "proceed".

    A containment that resolved to `None` here would be `approve-plan` sailing past a
    check that never ran — the same fail-open shape as the status parser's old
    `except ImportError: return None`, on the write side.
    """
    assert g.validate_run_id(None, "a", verb="probe") is not None
    assert g.validate_run_id(None, "a", verb="probe").startswith("internal-error")

    @g.contained_reason
    def blank(_):
        return "   "

    assert blank(1).startswith("internal-error")


def test_reason_never_carries_raw_artifact_content(g, tmp_path: Path) -> None:
    """A refusal is printed to a stderr the agent captures and logs."""
    secret = "SENSITIVE-ARTIFACT-BODY-9f3c"
    state = tmp_path / "state.json"
    state.write_text('{"schema_version": 1, "run_id": "' + secret + '"}', encoding="utf-8")

    @g.contained
    def read_it(path):
        g.read_managed_json(path, "state.json")
        raise RuntimeError("failed after reading")

    assert secret not in (read_it(state).reason or "")


def test_an_external_scalar_is_bounded_in_a_reason(g) -> None:
    """The bound sits on the interpolation, not on the assembled reason.

    A 100 KB `run_id` in `state.json` is attacker-influenceable length reaching a
    stderr line the agent captures and logs. Both guards that echo it are covered,
    because they carry two independent message sets by design.
    """
    huge = "A" * 100_000
    reason = g.validate_run_id(
        {"schema_version": 1, "run_id": huge}, "expected-id", verb="approve-plan"
    )
    assert reason is not None
    assert len(reason) < 500 and len(reason.splitlines()) == 1
    assert huge not in reason
    # And the truncation is visible rather than silent.
    assert "…" in reason


def test_the_longest_authored_reason_survives_intact(g) -> None:
    """The backstop must never clip the tool's own text.

    Capping the assembled reason at 400 chars regressed exactly this: the
    `_BOTH_CAUSES` recovery runbook is ~900 chars of numbered steps an operator
    follows to repair a stale baseline, and it was being cut off mid-sentence at
    step 3. This pins the separation the `_MAX_REASON_CHARS` comment claims.
    """
    longest = max(
        (v for k, v in vars(g).items() if isinstance(v, str) and k.isupper()),
        key=len,
    )
    assert len(longest) > 500, "expected a long authored constant to guard"
    assert g._one_line(longest) == " ".join(longest.split()), (
        "the backstop truncated an authored constant"
    )
    assert len(longest) + 200 < g._MAX_REASON_CHARS, (
        f"_MAX_REASON_CHARS={g._MAX_REASON_CHARS} leaves no headroom over the "
        f"longest authored constant ({len(longest)} chars) plus its interpolations"
    )


# ── AC12 — the widened except clauses on the lock-holding mutation verbs ───

RUN_ID = "11111111-2222-3333-4444-555555555555"


def _cohort_fixture(root: Path, *, approved: bool) -> Path:
    """A spec dir with a valid cohort `state.json`, inside a real git repo."""
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    spec_dir = root / "docs" / "specs" / "ac12"
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_text("# S\n\n- **Status:** Approved\n", encoding="utf-8")
    (spec_dir / "plan.md").write_text(
        "# P\n\n- **Status:** Approved\n\n## T1 a\n\n**Depends on:** none\n",
        encoding="utf-8",
    )
    zero = "0" * 64
    state = {
        "schema_version": 1, "run_id": RUN_ID, "feature": "ac12",
        "plan_review_status": "approved" if approved else "pending",
        "approved_spec_hash": zero, "approved_plan_hash": zero, "plan_hash": zero,
        "schedule_waves": [["T1"]], "current_wave_index": 0,
        "implementation_retry_count": 0, "review_round_count": 0,
        "review_retry_count": 0, "finding_fingerprints": [],
        "previous_finding_fingerprints": [],
        "max_implementation_retries": 5, "max_review_retries": 5,
    }
    (spec_dir / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    return spec_dir


# `pre_approved` selects WHICH hash block inside `cmd_approve_plan` is exercised, and
# it is not cosmetic. With `plan_review_status: "pending"` the crash-window
# `_read_md_status` refuses first, so the two `sha256_canonical_contract` blocks are
# never reached — every approve-plan row passed while the `except` tuples they exist to
# cover were narrowed back. `"approved"` takes the idempotency branch, where the hash
# comparison runs BEFORE any status read.
@pytest.mark.parametrize("verb,pre_approved", [
    ("approve-plan", False),   # crash-window status read refuses
    ("approve-plan", True),    # idempotency branch: reaches the hash comparison
    ("schedule", True),
], ids=["approve-plan-pending", "approve-plan-already-approved", "schedule"])
@pytest.mark.parametrize("breakage", ["symlinked", "oversized"])
def test_a_lock_holding_verb_refuses_an_unsafe_artifact_without_writing(
    verb: str, pre_approved: bool, breakage: str, tmp_path: Path,
) -> None:
    """The four widened `except` tuples, at the two verbs that hold the cohort lock.

    `ValueError` is the bounded reader's whole failure vocabulary and was not in these
    handlers; `ImportError` reaches them through the canonical parser. Both would
    otherwise leave a lock-holding verb as a traceback — and `cmd_approve_plan`
    *writes what it computes*, so an escape partway through is the dangerous shape.

    The byte-comparison is the load-bearing assertion. A one-line refusal that had
    already written half its result would satisfy an exit-code check.

    Coverage limit, stated rather than implied: of `cmd_approve_plan`'s two
    `sha256_canonical_contract` blocks, only the idempotency one is reachable by
    breaking an artifact. The pending branch's block — the one that WRITES what it
    computes — sits after `_read_md_status`, and both read the same file through the
    same bounded reader, so any breakage that would trip the hash trips the status read
    first. Its `except` is therefore a guard against the artifact becoming unsafe
    BETWEEN those two reads: a genuine TOCTOU, covered by
    `test_the_write_block_refuses_a_mid_verb_swap_without_writing` below rather than
    here.
    """
    spec_dir = _cohort_fixture(tmp_path, approved=pre_approved)
    target = spec_dir / "plan.md"

    if breakage == "symlinked":
        real = spec_dir / "plan.real.md"
        target.rename(real)
        target.symlink_to(real)
    else:
        # Sparse-extend past the reader's 8 MiB cap. `os.truncate` trips the
        # `st_size` pre-check while allocating one block, not 8 MiB — writing for
        # real exhausted the volume mid-suite once already.
        with Path(target).open("r+b") as fh:
            os.truncate(fh.fileno(), 9 * 1024 * 1024)

    state_file = spec_dir / "state.json"
    before = state_file.read_bytes()

    proc = run_cohort(verb, spec_dir, "--expect-run-id", RUN_ID, cwd=tmp_path)

    assert proc.returncode != 0, f"{verb}/{breakage}/pre_approved={pre_approved} reported success on an unsafe artifact"
    assert "Traceback" not in proc.stderr, (
        f"{verb}/{breakage}/pre_approved={pre_approved} escaped as a traceback:\n{proc.stderr}"
    )
    assert len(proc.stderr.strip().splitlines()) == 1, (
        f"{verb}/{breakage}/pre_approved={pre_approved} expected one stderr line, got:\n{proc.stderr}"
    )
    assert state_file.read_bytes() == before, (
        f"{verb}/{breakage}/pre_approved={pre_approved} mutated state.json while refusing — a partial write from "
        "a lock holder is the failure this criterion exists to prevent"
    )


def test_the_write_block_refuses_a_mid_verb_swap_without_writing(tmp_path: Path) -> None:
    """`cmd_approve_plan`'s WRITE block: the artifact goes unsafe after the status read.

    This is the block AC12 singles out — "entirely unguarded and wrote its result".
    It cannot be reached by breaking the artifact up front, because `_read_md_status`
    reads the same file through the same reader and refuses first. So the failure it
    guards is a TOCTOU: `Status: Approved` is read successfully, and the file becomes
    non-regular before `sha256_canonical_contract` runs.

    Simulated in a sandbox by making the guard module's `read_managed_text` succeed for
    the status read and then fail, which is what a swap between the two reads looks
    like from inside the verb. Without the `except`, that is a traceback out of a
    process holding the cohort lock; with a returning stub, it stores a non-digest as
    the approved baseline.
    """
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("loop-cohort.py", "_statelock.py", "lint-spec-status.py"):
        (scripts / name).write_bytes((SCRIPTS / name).read_bytes())
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "state.json").write_bytes(
        (SCRIPTS.parent / "assets" / "state.json").read_bytes()
    )

    # A guard module whose reader fails only AFTER the first two successful reads
    # (spec.md and plan.md status), i.e. exactly when the hashing block runs.
    guard_src = GUARDS.read_text(encoding="utf-8")
    anchor = "def read_managed_text(path: Path, label: str) -> str:"
    assert anchor in guard_src, "injection anchor moved — update this test"
    injected = anchor + """
    global _SWAP_READS
    try:
        _SWAP_READS += 1
    except NameError:
        _SWAP_READS = 1
    if _SWAP_READS > 2:
        raise ValueError(f"{label} must be a regular file")
"""
    (scripts / "_loop_guards.py").write_text(
        guard_src.replace(anchor, injected, 1), encoding="utf-8"
    )

    repo = tmp_path / "repo"
    spec_dir = _cohort_fixture(repo, approved=False)   # pending -> the write branch
    state_file = spec_dir / "state.json"
    before = state_file.read_bytes()

    proc = subprocess.run(
        [sys.executable, str(scripts / "loop-cohort.py"), "approve-plan",
         str(spec_dir), "--expect-run-id", RUN_ID],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=False, cwd=str(repo), timeout=60,
    )

    assert proc.returncode != 0, (
        f"approve-plan reported success after the artifact went unsafe mid-verb:\n"
        f"{proc.stdout}{proc.stderr}"
    )
    assert "Traceback" not in proc.stderr, (
        f"the write block escaped as a traceback:\n{proc.stderr}"
    )
    assert len(proc.stderr.strip().splitlines()) == 1, (
        f"expected one stderr line, got:\n{proc.stderr}"
    )
    assert "cannot pin the approved artifacts" in proc.stderr, (
        f"refused, but not from the write block: {proc.stderr.strip()[:200]!r}"
    )
    assert state_file.read_bytes() == before, (
        "approve-plan wrote state.json after failing to hash — the baseline would "
        "record a half-applied approval"
    )


@pytest.mark.parametrize("verb", ["approve-plan", "schedule"])
def test_a_lock_holding_verb_refuses_an_unloadable_parser_without_writing(
    verb: str, tmp_path: Path,
) -> None:
    """A corrupt canonical parser must also be a clean refusal from a lock holder.

    Split from the artifact cases because it arrives by a different route: an unsafe
    *artifact* raises `ValueError` from the bounded reader, while an unloadable
    *canonical parser* raises `ImportError` from `_lint_spec_status()`.

    Honest scope note: this does NOT discriminate the `ImportError` term in the four
    `except` tuples. Both parser-touching entry points — `read_md_status` and
    `sha256_canonical_contract` — convert `ImportError` into the reader's `ValueError`
    vocabulary at the boundary, so nothing reaches those tuples as an `ImportError`
    today (mutation-checked: removing the term keeps every case green). The term is
    kept as a backstop because `canonical_contract` itself does not convert, so a
    future direct call from a locked verb would need it. What this test pins is the
    end-to-end property the criterion is actually about: no traceback, one line, and
    no write.

    Needs a sandbox rather than the real scripts, because the breakage is a corrupt
    `lint-spec-status.py`, which is a shipped file.
    """
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("loop-cohort.py", "_loop_guards.py", "_statelock.py"):
        (scripts / name).write_bytes((SCRIPTS / name).read_bytes())
    (scripts / "lint-spec-status.py").write_text(
        "def parse_status(  # truncated mid-signature\n", encoding="utf-8"
    )
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "state.json").write_bytes(
        (SCRIPTS.parent / "assets" / "state.json").read_bytes()
    )

    repo = tmp_path / "repo"
    spec_dir = _cohort_fixture(repo, approved=(verb == "schedule"))
    state_file = spec_dir / "state.json"
    before = state_file.read_bytes()

    proc = subprocess.run(
        [sys.executable, str(scripts / "loop-cohort.py"), verb, str(spec_dir),
         "--expect-run-id", RUN_ID],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=False, cwd=str(repo), timeout=60,
    )

    assert proc.returncode != 0, f"{verb} succeeded with no canonical status parser"
    assert "Traceback" not in proc.stderr, f"{verb} tracebacked:\n{proc.stderr}"
    assert len(proc.stderr.strip().splitlines()) == 1, (
        f"{verb} expected one stderr line, got:\n{proc.stderr}"
    )
    assert state_file.read_bytes() == before, (
        f"{verb} mutated state.json while refusing on an unloadable parser"
    )


# ── AC15/AC16 — the artifact-integrity rows the parity table cannot express ─
#
# `test_loop_guards_parity.EXEMPT_ROWS` names this test as the one that covers them,
# and asserts by AST that it exists. Keep the name in sync with that mapping.

_ARTIFACT_INTEGRITY_ROWS = {
    # golden key -> (script, argv-after-spec-dir, how to break the artifact)
    "check-spec-status/symlinked-spec-md": (
        "check-spec-status.py", ["--expect", "Approved"], "symlink-spec"),
    "check-spec-status/oversized-spec-md": (
        "check-spec-status.py", ["--expect", "Approved"], "oversize-spec"),
    "plan-check-current/symlinked-plan-md": (
        "loop-cohort.py", None, "symlink-plan"),
}


def _golden_rows() -> dict:
    raw = json.loads(
        (Path(__file__).resolve().parent / "fixtures" / "golden_cli_streams.json")
        .read_text(encoding="utf-8")
    )
    return {r["key"]: r for r in raw["rows"]}


@pytest.mark.parametrize("key", sorted(_ARTIFACT_INTEGRITY_ROWS))
def test_an_artifact_integrity_change_matches_its_golden(key: str, tmp_path: Path) -> None:
    """The three ratified `artifact-integrity` changes, driven through the real CLI.

    Each was captured pre-change as a SUCCESS (`before.returncode == 0`): the old
    unbounded `read_text` followed a symlink and accepted a 9 MiB file. The bounded
    reader refuses both, which is a deliberate change recorded with a `change_reason`
    — and until now it was asserted nowhere, in either the parity table or here.

    The recorded `after` carries only `returncode`, so that is what is compared
    against; the one-line/no-traceback contract is asserted alongside it. The
    before/after inequality is the non-vacuity check — a row whose verdict did not
    actually change does not belong on the exemption list.
    """
    script_name, extra_argv, breakage = _ARTIFACT_INTEGRITY_ROWS[key]
    golden = _golden_rows()[key]
    assert golden.get("change_reason") == "artifact-integrity", (
        f"{key} is no longer an artifact-integrity row — update this test's table"
    )

    repo = tmp_path / "repo"
    spec_dir = _cohort_fixture(repo, approved=True)

    if breakage == "symlink-spec":
        real = spec_dir / "real-spec.md"
        (spec_dir / "spec.md").rename(real)
        (spec_dir / "spec.md").symlink_to(real)
    elif breakage == "symlink-plan":
        real = spec_dir / "real-plan.md"
        (spec_dir / "plan.md").rename(real)
        (spec_dir / "plan.md").symlink_to(real)
    elif breakage == "oversize-spec":
        # Sparse. `os.truncate` trips the reader's `st_size` pre-check while
        # allocating one block; writing 9 MiB for real exhausted the volume once.
        with Path(spec_dir / "spec.md").open("r+b") as fh:
            os.truncate(fh.fileno(), 9 * 1024 * 1024)
    else:  # pragma: no cover - table and branches are edited together
        raise AssertionError(f"unknown breakage {breakage!r}")

    argv = ([str(spec_dir), *extra_argv] if extra_argv is not None
            else ["plan", "check-current", str(spec_dir)])
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / script_name), *argv],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=False, cwd=str(repo), timeout=60,
    )

    expected_rc = golden["after"]["returncode"]
    assert proc.returncode == expected_rc, (
        f"{key}: expected returncode {expected_rc} (the recorded `after`), got "
        f"{proc.returncode}.\nstdout={proc.stdout!r}\nstderr={proc.stderr!r}"
    )
    # Non-vacuity: this row only earns its `change_reason` if the verdict moved.
    assert golden["before"]["returncode"] != expected_rc, (
        f"{key}: before and after agree, so nothing changed and the row should not "
        "carry a change_reason"
    )
    assert "Traceback" not in proc.stderr, f"{key} tracebacked:\n{proc.stderr}"
    assert len(proc.stderr.strip().splitlines()) == 1, (
        f"{key}: expected one stderr line, got:\n{proc.stderr}"
    )


# ── fail-closed status parsing ─────────────────────────────────────────────

def test_unloadable_parser_refuses_instead_of_skipping(tmp_path: Path) -> None:
    """The fail-open this change removes.

    `read_md_status` returned `None` when the parser could not be imported, and
    `None` is exactly what `assert_status_legal` legitimately SKIPS — so a broken
    canonical parser made the post-approval status-regression guard silently pass.
    A security control defaulting to allow on error.
    """
    sandbox = tmp_path / "scripts"
    sandbox.mkdir()
    for name in ("_loop_guards.py", "lint-spec-status.py"):
        (sandbox / name).write_bytes((SCRIPTS / name).read_bytes())
    (sandbox.parent / "assets").mkdir()
    (sandbox.parent / "assets" / "state.json").write_bytes(
        (SCRIPTS.parent / "assets" / "state.json").read_bytes()
    )
    (sandbox / "lint-spec-status.py").write_text("def parse_status(  # truncated\n",
                                                 encoding="utf-8")
    mod = load_guards(sandbox / "_loop_guards.py", "_guards_broken_parser")

    art = tmp_path / "spec.md"
    art.write_text("# S\n\n- **Status:** Draft\n", encoding="utf-8")
    with pytest.raises(mod.UnreadableArtifact):
        mod.read_md_status(art)
    # And the legality check refuses rather than reporting "legal".
    reason = mod.assert_status_legal("probe", art)
    assert reason is not None and "spec.md" in reason


def test_absent_status_token_is_still_skipped(g, tmp_path: Path) -> None:
    """Only an *unloadable parser* became a refusal; an absent token stays a skip.

    Several real plan fixtures carry no status line, and AC14 must not turn those
    into refusals — that would break `plan check-current` for them by construction.
    """
    art = tmp_path / "plan.md"
    art.write_text("# Plan\n\nno status line here\n", encoding="utf-8")
    assert g.read_md_status(art) is None
    assert g.assert_status_legal("probe", art) is None


def test_regressed_status_is_refused(g, tmp_path: Path) -> None:
    art = tmp_path / "spec.md"
    art.write_text("# S\n\n- **Status:** Draft\n", encoding="utf-8")
    reason = g.assert_status_legal("probe", art)
    assert reason is not None and "Draft" in reason


# ── the loader's failure modes ─────────────────────────────────────────────

# AC13: "Every case runs against BOTH loaders, since both now carry the four
# controls." The second loader is `_lint_spec_status()`, inside `_loop_guards.py`,
# which loads `lint-spec-status.py`. It previously had exactly one case — a syntax
# error — so the non-regular, symlinked, permission-denied and clean-truncation
# controls were unverified on it.
#
# loader -> (target filename, argv that reaches it, clean-truncation cut anchor)
_LOADERS = {
    # `identity` needs no parser, so it isolates the guard-module loader.
    "guards": ("_loop_guards.py", ["identity"], "def read_state("),
    # `plan check-current` reads a status token, which is the only route to the
    # parser loader. Truncating before `parse_status` leaves `__all__`-equivalent
    # symbols missing, which is what `_PARSER_SYMBOLS` exists to catch.
    "parser": ("lint-spec-status.py", ["plan", "check-current"], "def parse_status("),
}


@pytest.mark.parametrize(
    "mode",
    ["missing", "unreadable", "non-regular", "symlinked", "syntax-error",
     "truncated-mid-statement", "truncated-clean", "no-completeness-marker"],
)
@pytest.mark.parametrize("loader", sorted(_LOADERS))
def test_load_failure_is_a_one_line_refusal(
    loader: str, mode: str, tmp_path: Path,
) -> None:
    """Every way either module can fail to load produces a refusal, never a traceback.

    `truncated-clean` is the one that motivated the completeness marker: a file cut at
    a statement boundary loads *without raising* and returns a handle missing
    everything below the cut, so exception handling alone cannot see it.
    """
    target_name, verb, cut_anchor = _LOADERS[loader]

    sandbox = tmp_path / "scripts"
    sandbox.mkdir()
    (sandbox.parent / "assets").mkdir()
    (sandbox.parent / "assets" / "state.json").write_bytes(
        (SCRIPTS.parent / "assets" / "state.json").read_bytes()
    )
    # Everything except the file under test, which each branch below writes.
    for name in ("loop-cohort.py", "lint-spec-status.py", "_statelock.py",
                 "_loop_guards.py"):
        if name != target_name:
            (sandbox / name).write_bytes((SCRIPTS / name).read_bytes())
    target = sandbox / target_name
    original = (SCRIPTS / target_name).read_text(encoding="utf-8")

    if mode == "missing":
        pass
    elif mode == "unreadable":
        target.write_text(original, encoding="utf-8")
        target.chmod(0o000)
        if os.access(target, os.R_OK):  # running as root
            pytest.skip("cannot make a file unreadable as this user")
    elif mode == "non-regular":
        os.mkfifo(target)
    elif mode == "symlinked":
        real = sandbox / f"real_{target_name}"
        real.write_text(original, encoding="utf-8")
        try:
            target.symlink_to(real)
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation unavailable")
    elif mode == "syntax-error":
        target.write_text("def broken(:\n", encoding="utf-8")
    elif mode == "truncated-mid-statement":
        target.write_text(original[: len(original) // 2], encoding="utf-8")
    elif mode == "truncated-clean":
        cut = original.index(cut_anchor)
        target.write_text(original[:cut], encoding="utf-8")
    elif mode == "no-completeness-marker":
        if loader == "parser":
            # `lint-spec-status.py` carries no `_MODULE_COMPLETE`; its completeness
            # gate is the `_PARSER_SYMBOLS` check. Remove a required symbol instead —
            # the same class of failure (module loads, contract unmet).
            marker = "def extract_status_token("
            assert marker in original, "parser symbol anchor moved — update this test"
            target.write_text(original.replace(marker, "def _renamed_away("),
                              encoding="utf-8")
        else:
            target.write_text(original.replace("_MODULE_COMPLETE = True", ""),
                              encoding="utf-8")

    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    if loader == "parser":
        # The parser is only reached once there is a status to read, so the fixture
        # has to be complete enough to get past the state and artifact checks.
        (spec_dir / "spec.md").write_text("# S\n\n- **Status:** Approved\n",
                                          encoding="utf-8")
        (spec_dir / "plan.md").write_text(
            "# P\n\n- **Status:** Approved\n\n## T1 a\n\n**Depends on:** none\n",
            encoding="utf-8")
        (spec_dir / "state.json").write_text(
            json.dumps(cohort_state(plan_review_status="approved")), encoding="utf-8")

    # The SANDBOX copy — pointing at the real script would load the real, intact
    # module and report a missing state.json instead of the load failure under test.
    run = subprocess.run(
        [sys.executable, str(sandbox / "loop-cohort.py"), *verb, str(spec_dir)],
        capture_output=True, text=True, check=False, cwd=str(tmp_path),
    )
    combined = run.stdout + run.stderr
    try:
        assert run.returncode != 0, f"{mode}: expected a refusal, got 0 ({combined!r})"
        assert "Traceback" not in combined, f"{mode}: traceback instead of a refusal:\n{combined}"
        assert len(run.stderr.strip().split("\n")) == 1, \
            f"{mode}: stderr is not one line:\n{run.stderr}"
        assert target_name in combined, (
            f"{loader}/{mode}: refusal does not name {target_name}: {combined!r}"
        )
        assert "build-self" in combined or "Restore" in combined, \
            f"{mode}: refusal does not name a remedy: {run.stderr!r}"
    finally:
        if mode == "unreadable" and target.exists():
            target.chmod(0o644)


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


def test_every_cohort_verb_refuses_when_the_module_is_unavailable(tmp_path: Path) -> None:
    """The sentinel is checked at one chokepoint, so this covers every verb at once.

    The alternative — a check copied into each of ~20 verb entries — is exactly the
    shape where one gets missed, and a missed one would run on the fallback stubs.
    """
    sandbox = tmp_path / "scripts"
    sandbox.mkdir()
    (sandbox.parent / "assets").mkdir()
    (sandbox.parent / "assets" / "state.json").write_bytes(
        (SCRIPTS.parent / "assets" / "state.json").read_bytes()
    )
    for name in ("loop-cohort.py", "lint-spec-status.py", "_statelock.py"):
        (sandbox / name).write_bytes((SCRIPTS / name).read_bytes())
    # _loop_guards.py deliberately absent.
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()

    verbs = [
        ["identity", spec_dir],
        ["status", spec_dir],
        ["check", spec_dir, "--phase", "implement"],
        ["plan", "check-current", spec_dir],
        ["schedule", "check-current", spec_dir],
        ["wave", "check", spec_dir, "--expect", "last"],
        ["init", spec_dir, "--run-id", "11111111-2222-3333-4444-555555555555"],
        ["reset", spec_dir],
    ]
    for argv in verbs:
        run = subprocess.run(
            [sys.executable, str(sandbox / "loop-cohort.py"), *[str(a) for a in argv]],
            capture_output=True, text=True, check=False, cwd=str(tmp_path),
        )
        combined = run.stdout + run.stderr
        assert run.returncode != 0, f"{argv[0]}: proceeded without the guard module"
        assert "Traceback" not in combined, f"{argv[0]}: traceback:\n{combined}"
        assert "_loop_guards.py" in combined, f"{argv[0]}: refusal does not name the path"


# ── the loader is duplicated on purpose; keep the copies identical ─────────

def test_loader_copies_are_structurally_identical() -> None:
    """Three copies is a decision — the loader cannot live in the module it loads.

    The comparison is over the AST of the function body with the docstring dropped,
    and it needs no normalization at all: once the CLI prefixes moved out of the guard
    layer into the adapters, the three bodies became identical as written. That is
    strictly better than a normalized comparison, because there is no substitution
    left that could be loosened until the test passes vacuously. (An earlier revision
    substituted the tool names and claimed in its docstring to assert that the
    prefixes really differed; it did not make that assertion, and the substitution is
    now provably a no-op — asserted below, so reintroducing a tool-specific literal
    fails here rather than being silently absorbed.)

    All three copies must resolve. Skipping when fewer were found is how this test
    would quietly stop covering a renamed copy — it is the failure mode, not a
    tolerance.
    """
    import ast
    import re as _re

    wanted = {
        "loop-cohort.py": "load_guards",
        "loop-engine.py": "_guards",
        "check-spec-status.py": "load_guards",
    }
    bodies: dict[str, str] = {}
    for filename, funcname in wanted.items():
        path = SCRIPTS / filename
        assert path.is_file(), f"loader copy {filename} is missing"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        fn = next((n for n in tree.body
                   if isinstance(n, ast.FunctionDef) and n.name == funcname), None)
        assert fn is not None, (
            f"{filename} has no top-level {funcname}() — if the loader was renamed, "
            "update `wanted` so this check keeps covering all three copies"
        )
        body = fn.body[1:] if (fn.body and isinstance(fn.body[0], ast.Expr)
                               and isinstance(fn.body[0].value, ast.Constant)) else fn.body
        bodies[filename] = "\n".join(ast.dump(node) for node in body)

    assert len(bodies) == 3, f"expected 3 loader copies, compared {len(bodies)}"
    assert len(set(bodies.values())) == 1, (
        "the loader copies have drifted:\n"
        + "\n".join(f"  {f}: {len(b)} chars" for f, b in sorted(bodies.items()))
    )
    # No tool-specific literal may reappear in a body, which is what made the old
    # normalization necessary and what would make this comparison meaningless again.
    for filename, body in bodies.items():
        leaked = _re.findall(r"loop-cohort|loop-engine|check-spec-status", body)
        assert not leaked, (
            f"{filename}'s loader body names a specific tool ({sorted(set(leaked))}). "
            "The three copies are identical as written; keep tool-specific text in the "
            "caller, not in the shared loader body."
        )


# ══ T1b: the six guard decisions ═══════════════════════════════════════════
#
# One case per branch each guard can take. The point is not coverage for its own
# sake: each of these branches is a refusal the FSM depends on, and the whole risk
# of moving the guards in-process is that one silently stops firing.

SPEC_MD = "# Spec\n\n- **Status:** {s}\n\n## Acceptance Criteria\n\n- [ ] AC1\n"
PLAN_MD = "# Plan\n\n- **Status:** {s}\n\n## T1 First\n\n**Depends on:** none\n"


def cohort_state(**over) -> dict:
    st = {
        "schema_version": 1, "run_id": "run-1", "feature": "f",
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


@pytest.fixture
def spec(g, tmp_path: Path):
    """A spec dir factory. `approved=True` pins REAL hashes so drift is meaningful."""
    def build(*, spec_status="Approved", plan_status="Approved", approved=False,
              waves=None, no_state=False, no_spec=False, no_plan=False, **over) -> Path:
        d = tmp_path / f"spec{len(list(tmp_path.iterdir()))}"
        d.mkdir()
        if not no_spec:
            (d / "spec.md").write_text(SPEC_MD.format(s=spec_status), encoding="utf-8")
        if not no_plan:
            (d / "plan.md").write_text(PLAN_MD.format(s=plan_status), encoding="utf-8")
        if no_state:
            return d
        if approved:
            over.setdefault("plan_review_status", "approved")
            over.setdefault("approved_spec_hash", g.sha256_canonical_contract(d / "spec.md"))
            over.setdefault("approved_plan_hash", g.sha256_canonical_contract(d / "plan.md"))
            over.setdefault("plan_hash", g.sha256_canonical_contract(d / "plan.md"))
            over.setdefault("schedule_waves", waves if waves is not None else [["T1"], ["T2"]])
        (d / "state.json").write_text(json.dumps(cohort_state(**over)), encoding="utf-8")
        return d
    return build


# ── check_identity ─────────────────────────────────────────────────────────

def test_check_identity_branches(g, spec) -> None:
    d = spec()
    ok = g.check_identity(d, expect_run_id="run-1")
    assert ok.ok and ok.data == {"run_id": "run-1", "schema_version": 1}

    bad = g.check_identity(d, expect_run_id="other")
    assert not bad.ok and "run_id mismatch" in bad.reason

    # expect_run_id=None means "just tell me", which the CLI allows.
    assert g.check_identity(d, expect_run_id=None).ok

    assert not g.check_identity(spec(schema_version=99), expect_run_id="run-1").ok
    assert not g.check_identity(spec(no_state=True), expect_run_id="run-1").ok


# ── check_plan_current ─────────────────────────────────────────────────────

def test_check_plan_current_refuses_pending_without_a_verb_prefix(g, spec) -> None:
    """The one refusal with no verb prefix, and it must stay that way.

    `SKILL.md` documents this exact string as the cue to run pre-EXECUTE review
    rather than as a termination signal, so re-prefixing it would change how the
    loop reads a normal PLAN-stage state.
    """
    result = g.check_plan_current(spec())
    assert not result.ok
    assert result.reason == "plan_review_status: pending"


def test_check_plan_current_branches(g, spec) -> None:
    assert g.check_plan_current(spec(approved=True)).ok

    drifted = spec(approved=True)
    (drifted / "spec.md").write_text(SPEC_MD.format(s="Approved") + "\ndrift\n", encoding="utf-8")
    r = g.check_plan_current(drifted)
    assert not r.ok and "spec.md no longer matches the approved baseline" in r.reason

    drifted = spec(approved=True)
    (drifted / "plan.md").write_text(PLAN_MD.format(s="Approved") + "\ndrift\n", encoding="utf-8")
    r = g.check_plan_current(drifted)
    assert not r.ok and "plan.md no longer matches the approved baseline" in r.reason

    missing = spec(approved=True)
    (missing / "spec.md").unlink()
    assert "spec.md not found" in g.check_plan_current(missing).reason

    missing = spec(approved=True)
    (missing / "plan.md").unlink()
    assert "plan.md not found" in g.check_plan_current(missing).reason

    regressed = spec(approved=True)
    (regressed / "spec.md").write_text(SPEC_MD.format(s="Draft"), encoding="utf-8")
    r = g.check_plan_current(regressed)
    assert not r.ok and "Status is 'Draft'" in r.reason


def test_check_plan_current_require_schedule_branches(g, spec) -> None:
    assert g.check_plan_current(spec(approved=True), require_schedule=True).ok

    r = g.check_plan_current(spec(approved=True, waves=[]), require_schedule=True)
    assert not r.ok and "schedule_waves is empty" in r.reason

    r = g.check_plan_current(spec(approved=True, current_wave_index=9), require_schedule=True)
    assert not r.ok and "out of range" in r.reason

    r = g.check_plan_current(spec(approved=True, plan_hash="0" * 64), require_schedule=True)
    assert not r.ok and "plan_hash != approved_plan_hash" in r.reason

    # Without --require-schedule the same states are fine: the flag is the difference.
    assert g.check_plan_current(spec(approved=True, waves=[])).ok


# ── check_schedule_current ─────────────────────────────────────────────────

def test_check_schedule_current_branches(g, spec) -> None:
    assert g.check_schedule_current(spec(approved=True)).ok

    r = g.check_schedule_current(spec(approved=True, plan_hash="0" * 64))
    assert not r.ok and "no longer matches the scheduled baseline" in r.reason

    missing = spec(approved=True)
    (missing / "plan.md").unlink()
    assert "plan.md not found" in g.check_schedule_current(missing).reason

    bad_status = spec(approved=True)
    (bad_status / "plan.md").write_text(PLAN_MD.format(s="Drafting"), encoding="utf-8")
    assert not g.check_schedule_current(bad_status).ok

    # The missing-state refusal, which the CLI has always performed here.
    assert not g.check_schedule_current(spec(no_state=True)).ok


# ── check_phase ────────────────────────────────────────────────────────────

def test_check_phase_reads_state_even_for_implement(g, spec) -> None:
    """`implement` is a stub, but NOT a total no-op.

    `cmd_check` has always called `read_state` before reaching it, so a missing or
    malformed `state.json` refuses. The engine's `wave-complete` guard is this check,
    so returning ok unconditionally would drop a live refusal.
    """
    assert g.check_phase(spec(), phase="implement").ok
    assert not g.check_phase(spec(no_state=True), phase="implement").ok

    corrupt = spec()
    (corrupt / "state.json").write_text("{not json", encoding="utf-8")
    assert not g.check_phase(corrupt, phase="implement").ok

    # ...but `implement` still skips schema validation, so a pre-Phase-1 state file
    # does not break the hook — that asymmetry is deliberate and load-bearing.
    assert g.check_phase(spec(schema_version=99), phase="implement").ok
    assert not g.check_phase(spec(schema_version=99), phase="review").ok


def test_check_phase_retry_caps(g, spec) -> None:
    assert g.check_phase(spec(review_retry_count=4), phase="review").ok
    r = g.check_phase(spec(review_retry_count=5), phase="review")
    assert not r.ok and "review retry cap reached (5/5)" in r.reason

    assert g.check_phase(spec(implementation_retry_count=4), phase="gates-failed").ok
    r = g.check_phase(spec(implementation_retry_count=5), phase="gates-failed")
    assert not r.ok and "implementation retry cap reached (5/5)" in r.reason

    assert not g.check_phase(spec(), phase="nonsense").ok


def test_check_phase_validates_counter_types(g, spec) -> None:
    """`int()` coerced these silently, changing the cap arithmetic.

    `"3"` and `3.7` both became 3; `-1` passed every comparison; `Infinity` raised
    OverflowError straight out of the guard. The non-finite case is refused earlier at
    the JSON boundary — this covers the rest.
    """
    for value in ("4", 4.7, -1, True):
        r = g.check_phase(spec(review_retry_count=value), phase="review")
        assert not r.ok, f"{value!r} was accepted as a counter"
        assert "non-negative integer" in r.reason
    r = g.check_phase(spec(max_review_retries="5"), phase="review")
    assert not r.ok and "non-negative integer" in r.reason


# ── check_wave ─────────────────────────────────────────────────────────────

def test_check_wave_branches(g, spec) -> None:
    first = spec(approved=True, waves=[["T1"], ["T2"], ["T3"]], current_wave_index=0)
    mid = spec(approved=True, waves=[["T1"], ["T2"], ["T3"]], current_wave_index=1)
    last = spec(approved=True, waves=[["T1"], ["T2"], ["T3"]], current_wave_index=2)

    assert g.check_wave(first, expect="more").ok
    assert g.check_wave(mid, expect="more").ok
    r = g.check_wave(last, expect="more")
    assert not r.ok and "no more waves" in r.reason

    assert g.check_wave(last, expect="last").ok
    r = g.check_wave(first, expect="last")
    assert not r.ok and "not the last wave" in r.reason

    # The optional index check the `wave-passed` guard relies on.
    assert g.check_wave(mid, expect="more", wave_index=1).ok
    r = g.check_wave(mid, expect="more", wave_index=0)
    assert not r.ok and "does not match --wave-index 0" in r.reason

    assert not g.check_wave(first, expect="sideways").ok
    assert not g.check_wave(spec(no_state=True), expect="last").ok


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

def test_spec_dir_must_be_a_directory(g, tmp_path: Path) -> None:
    afile = tmp_path / "not-a-dir"
    afile.write_text("x", encoding="utf-8")
    for call in (
        lambda p: g.check_identity(p, expect_run_id=None),
        lambda p: g.check_plan_current(p),
        lambda p: g.check_schedule_current(p),
        lambda p: g.check_phase(p, phase="review"),
        lambda p: g.check_wave(p, expect="last"),
        lambda p: g.check_artifact_status(p, filename="spec.md", expect="X"),
    ):
        assert not call(afile).ok
        assert not call(tmp_path / "absent").ok


def test_each_guard_reads_state_afresh(g, spec, monkeypatch) -> None:
    """No cross-guard snapshot: three guards mean three reads.

    A shared snapshot is the one change that could alter behaviour under concurrent
    cohort mutation, which is why the spec forbids it. Three separately-invoked child
    processes read three times; this proves the in-process path still does.
    """
    d = spec(approved=True)
    reads: list[str] = []
    real = g.read_managed_json

    def counting(path, label):
        reads.append(label)
        return real(path, label)

    monkeypatch.setattr(g, "read_managed_json", counting)
    g.check_identity(d, expect_run_id="run-1")
    g.check_schedule_current(d)
    g.check_wave(d, expect="more")
    assert reads.count("state.json") == 3, f"expected 3 fresh reads, saw {reads}"


def test_guards_create_and_mutate_nothing(g, spec) -> None:
    """Directory-level, not a six-file byte compare.

    `_recover_engine_state_tmp` globs `.engine-state-*.json.tmp` and PROMOTES the
    first valid match over `engine-state.json`, so a stray temp file left by a guard
    would silently become engine state — which a named-file comparison cannot see.
    A `state.json.lock` would likewise be invisible, and it is the observable half of
    "no guard acquires the cohort mutation lock".
    """
    d = spec(approved=True)
    (d / "engine-state.json").write_text('{"state": "CODE-IMPLEMENTATION"}', encoding="utf-8")

    # AC18 covers the repo-root `.loop-run/` as well as the spec dir. It is a second
    # place the engine writes — `_LOOP_RUN_DIR_NAME` in `loop-engine.py` — so a guard
    # dropping a pending-event or lock file there would be invisible to a spec-dir
    # snapshot. Seeded with a file so the comparison cannot pass empty-to-empty.
    loop_run = d.parent / ".loop-run"
    loop_run.mkdir()
    (loop_run / "pending.json").write_text('{"seeded": true}', encoding="utf-8")

    roots = {"spec": d, "loop-run": loop_run}

    def snapshot():
        # Both directories must exist AT SNAPSHOT TIME. Without this the whole
        # assertion degrades to comparing {} with {} the moment a fixture changes.
        for label, root in roots.items():
            assert root.is_dir(), (
                f"{label} directory {root} is absent — the comparison would pass "
                "vacuously, which AC18 explicitly forbids"
            )
        return {
            f"{label}/{p.relative_to(root).as_posix()}": p.read_bytes()
            for label, root in roots.items()
            for p in sorted(root.rglob("*")) if p.is_file()
        }

    before = snapshot()
    assert before, "fixture is empty — the assertion would pass vacuously"
    assert any(k.startswith("loop-run/") for k in before), (
        "the .loop-run half of the snapshot is empty — seed it or the guard writes "
        "this test exists to catch would be invisible"
    )

    g.check_identity(d, expect_run_id="run-1")
    g.check_plan_current(d, require_schedule=True)
    g.check_schedule_current(d)
    g.check_phase(d, phase="review")
    g.check_wave(d, expect="more")
    g.check_artifact_status(d, filename="spec.md", expect="Approved")

    after = snapshot()
    assert after == before, (
        "guards changed a watched directory: "
        f"{sorted(set(after) ^ set(before)) or 'contents differ'}"
    )
    for root in roots.values():
        assert not list(root.glob(".engine-state-*.json.tmp"))
        assert not list(root.glob("*.lock"))


def test_all_is_pinned_to_the_declared_surface(g) -> None:
    """`__all__` is the loaders' completeness contract, so it is pinned explicitly.

    AC13 makes `set(__all__) <= set(dir(module))` the check that turns a
    cleanly-truncated file into a load failure. That check is only as good as
    `__all__` is complete: a name dropped from the list stops being covered, and the
    loader would happily hand back a module missing it.

    Pinning it here rather than deriving it from the module is deliberate — a derived
    expectation would move with the code, which is the antipattern this spec has been
    tripping over since T0.
    """
    expected = {
        # result type + containment
        "GuardResult", "contained", "contained_reason",
        # bounded, symlink-safe readers
        "read_managed_json", "read_managed_text", "read_state", "state_path_for",
        # canonical contract hashing
        "canonical_contract", "sha256_canonical_contract",
        # status parsing, legality, validation
        "UnreadableArtifact", "read_md_status", "assert_status_legal",
        "validate_run_id", "non_negative_int",
        # retry caps
        "DEFAULTS",
        # the six read-only guards
        "check_identity", "check_plan_current", "check_schedule_current",
        "check_phase", "check_wave", "check_artifact_status",
    }
    actual = set(g.__all__)
    assert actual == expected, (
        "the guard module's public surface changed.\n"
        f"  added:   {sorted(actual - expected)}\n"
        f"  removed: {sorted(expected - actual)}\n"
        "If this is intentional, update both this list and the loaders' required-symbol "
        "expectations — the completeness check is only as strong as __all__ is complete."
    )
    assert len(g.__all__) == len(set(g.__all__)), "__all__ contains a duplicate"
    # Every guard the FSM dispatches must be exported, or the engine cannot reach it.
    assert {"check_identity", "check_plan_current", "check_schedule_current",
            "check_phase", "check_wave", "check_artifact_status"} <= actual


def test_every_loader_derives_completeness_from_all_not_an_enumeration() -> None:
    """AC13's completeness check reads the module's own `__all__`; no loader restates it.

    An enumerated required-symbol list has to be repeated in all three loader copies,
    and it drifted on day one: the cohort copy listed `non_negative_int` and the other
    two did not, while `check-spec-status.py` omitted `check_artifact_status` — the
    only function it calls. Deriving from `__all__` makes the module the single
    source, so this asserts both halves: the derivation is present, and the form that
    drifts is absent.

    Structural, not substring-on-source: the assertion walks each loader's AST for the
    `__all__` read, so a comment mentioning `__all__` cannot satisfy it.
    """
    import ast as _ast

    # Declared, not discovered. The engine's copy is `_guards`; the other two are
    # `load_guards`. Searching for one name would silently drop a copy and pass —
    # so the mapping is data, and an unresolvable entry fails rather than skips.
    loaders = {
        "loop-cohort.py": "load_guards",
        "loop-engine.py": "_guards",
        "check-spec-status.py": "load_guards",
    }

    for filename, funcname in loaders.items():
        src = (SCRIPTS / filename).read_text(encoding="utf-8")
        tree = _ast.parse(src)

        assert "_GUARDS_REQUIRED" not in {
            node.id for node in _ast.walk(tree) if isinstance(node, _ast.Name)
        }, f"{filename} reintroduced the enumerated required-symbol list"

        loader = next(
            (n for n in _ast.walk(tree)
             if isinstance(n, _ast.FunctionDef) and n.name == funcname),
            None,
        )
        assert loader is not None, (
            f"{filename} has no {funcname}() — if the loader was renamed, update the "
            "`loaders` map above so this check keeps covering all three copies"
        )

        reads_all = any(
            isinstance(n, _ast.Constant) and n.value == "__all__"
            for n in _ast.walk(loader)
        )
        assert reads_all, (
            f"{filename}'s load_guards does not derive completeness from __all__"
        )

        calls_dir = any(
            isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name)
            and n.func.id == "dir"
            for n in _ast.walk(loader)
        )
        assert calls_dir, (
            f"{filename}'s load_guards reads __all__ but never compares it against "
            "dir(module) — a truncated module declares __all__ without defining it"
        )
