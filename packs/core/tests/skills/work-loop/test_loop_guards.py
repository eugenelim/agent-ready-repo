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
    """
    opened: list = []
    real_open = os.open
    os.open = lambda *a, **k: (opened.append(a[0]), real_open(*a, **k))[1]
    try:
        load_guards(name="_guards_io_probe")
    finally:
        os.open = real_open
    assert not opened, f"import opened {len(opened)} file(s): {opened[:3]}"


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


def test_load_writes_no_bytecode_and_restores_the_flag() -> None:
    previous = sys.dont_write_bytecode
    cache = SCRIPTS / "__pycache__"
    before = {p.name for p in cache.glob("_loop_guards*.pyc")} if cache.is_dir() else set()
    run = run_cohort("--help")
    assert run.returncode == 0
    after = {p.name for p in cache.glob("_loop_guards*.pyc")} if cache.is_dir() else set()
    assert after == before, f"a load wrote bytecode: {sorted(after - before)}"
    assert sys.dont_write_bytecode is previous


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
    """
    src = GUARDS.read_text(encoding="utf-8")
    offenders = [
        line.strip() for line in src.split("\n")
        if "re.compile" in line and "Status" in line
    ]
    assert not offenders, f"a second status regex: {offenders}"


def test_guards_print_nothing(g, tmp_path: Path) -> None:
    """Zero bytes on both streams, and the verdict is asserted too.

    An empty-stream assertion alone passes on a guard that refused for an unrelated
    reason — including the specific case where capturing through an `io.StringIO`
    makes the lazily-loaded parser's module-scope `reconfigure` raise. So each call
    asserts its real result.
    """
    art = tmp_path / "spec.md"
    art.write_text("# S\n\n- **Status:** Shipped\n\n## Acceptance Criteria\n\n- [x] a\n",
                   encoding="utf-8")
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        digest = g.sha256_canonical_contract(art)
        token = g.read_md_status(art)
        legal = g.assert_status_legal("probe", art)
        run_id = g.validate_run_id({"schema_version": 1, "run_id": "a"}, "a", verb="probe")
    assert len(digest) == 64
    assert token == "Shipped"
    assert legal is None and run_id is None
    assert out.getvalue() == "" and err.getvalue() == ""


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
    assert result.reason.startswith("internal-error: RuntimeError")
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

@pytest.mark.parametrize(
    "mode",
    ["missing", "unreadable", "non-regular", "symlinked", "syntax-error",
     "truncated-mid-statement", "truncated-clean", "no-completeness-marker"],
)
def test_load_failure_is_a_one_line_refusal(mode: str, tmp_path: Path) -> None:
    """Every way the module can fail to load produces a refusal, never a traceback.

    `truncated-clean` is the one that motivated the completeness marker: a file cut at
    a statement boundary loads *without raising* and returns a handle missing
    everything below the cut, so exception handling alone cannot see it.
    """
    sandbox = tmp_path / "scripts"
    sandbox.mkdir()
    (sandbox.parent / "assets").mkdir()
    (sandbox.parent / "assets" / "state.json").write_bytes(
        (SCRIPTS.parent / "assets" / "state.json").read_bytes()
    )
    for name in ("loop-cohort.py", "lint-spec-status.py", "_statelock.py"):
        (sandbox / name).write_bytes((SCRIPTS / name).read_bytes())
    target = sandbox / "_loop_guards.py"
    original = GUARDS.read_text(encoding="utf-8")

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
        real = sandbox / "real_guards.py"
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
        cut = original.index("def read_state(")
        target.write_text(original[:cut], encoding="utf-8")
    elif mode == "no-completeness-marker":
        target.write_text(original.replace("_MODULE_COMPLETE = True", ""), encoding="utf-8")

    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    # The SANDBOX copy — pointing at the real script would load the real, intact
    # module and report a missing state.json instead of the load failure under test.
    run = subprocess.run(
        [sys.executable, str(sandbox / "loop-cohort.py"), "identity", str(spec_dir)],
        capture_output=True, text=True, check=False, cwd=str(tmp_path),
    )
    combined = run.stdout + run.stderr
    try:
        assert run.returncode != 0, f"{mode}: expected a refusal, got 0 ({combined!r})"
        assert "Traceback" not in combined, f"{mode}: traceback instead of a refusal:\n{combined}"
        assert len(run.stderr.strip().split("\n")) == 1, \
            f"{mode}: stderr is not one line:\n{run.stderr}"
        assert "_loop_guards.py" in combined, f"{mode}: refusal does not name the path"
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

    Byte-identity is impossible: each copy differs in function name and in the tool
    prefix on its messages. So the comparison is over the normalized AST of the
    function body, and the test additionally asserts the prefixes really do differ,
    which stops the normalization being loosened until it passes vacuously.

    Copies land across T1a/T2/T3, so absent ones are reported rather than failed.
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
        if not path.is_file():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        fn = next((n for n in tree.body
                   if isinstance(n, ast.FunctionDef) and n.name == funcname), None)
        if fn is None:
            continue
        # Drop the docstring, then normalize the tool-specific literals away.
        body = fn.body[1:] if (fn.body and isinstance(fn.body[0], ast.Expr)
                               and isinstance(fn.body[0].value, ast.Constant)) else fn.body
        dumped = "\n".join(ast.dump(node) for node in body)
        dumped = _re.sub(r"loop-cohort|loop-engine|check-spec-status", "<TOOL>", dumped)
        bodies[filename] = dumped

    if len(bodies) < 2:
        pytest.skip(f"only {len(bodies)} loader copy present so far: {sorted(bodies)}")
    distinct = set(bodies.values())
    assert len(distinct) == 1, (
        "the loader copies have drifted; present: " + ", ".join(sorted(bodies))
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

    def snapshot():
        return {
            p.relative_to(d).as_posix(): p.read_bytes()
            for p in sorted(d.rglob("*")) if p.is_file()
        }

    before = snapshot()
    assert before, "fixture is empty — the assertion would pass vacuously"
    g.check_identity(d, expect_run_id="run-1")
    g.check_plan_current(d, require_schedule=True)
    g.check_schedule_current(d)
    g.check_phase(d, phase="review")
    g.check_wave(d, expect="more")
    g.check_artifact_status(d, filename="spec.md", expect="Approved")
    after = snapshot()
    assert after == before, (
        "guards changed the spec directory: "
        f"{sorted(set(after) ^ set(before)) or 'contents differ'}"
    )
    assert not list(d.glob(".engine-state-*.json.tmp"))
    assert not list(d.glob("*.lock"))
