"""_loop_guards — the work-loop's shared read-only guard API.

`loop-engine.py transition` used to shell out to `loop-cohort.py` and
`check-spec-status.py` for every read-only FSM guard, costing up to three extra
Python interpreters per transition. The guard *decisions* live here now, so the
engine and those CLIs call one implementation and cannot drift into disagreeing
about whether a transition is legal.

Contract — every public function in this module:

  * takes explicit typed arguments and returns a `GuardResult`;
  * prints NOTHING to stdout or stderr, and carries no CLI prefix in `reason`
    or `message` — each adapter adds its own, so the layer cannot double it
    (which it did once, caught by the golden capture);
  * parses no arguments, reads no `sys.argv`, never calls `sys.exit`;
  * mutates no state file and creates no file anywhere;
  * never spawns a process and never opens a socket.

Two named exceptions to the first bullet, kept because their six mutation-verb
callers consume a reason string directly and rewriting those call sites is out of
scope: `validate_run_id` and `assert_status_legal` return `str | None`.

`spec_dir` precondition: callers pass an absolute, already-resolved,
already-confined `Path`. Confinement stays with the caller that owns it —
`loop-engine._resolve_spec_dir` and `loop-cohort._resolve_spec_dir` (both
repo-root anchored), and `check-spec-status.py`'s bare `resolve()`, which is the
weakest of the three and stays that way under its frozen argument surface. What a
callee can actually check, it does: that `spec_dir` exists and is a directory.
Re-testing "absolute, no `..`" would be dead code, because every caller resolves
first.

NOTE ON `from __future__ import annotations` — deliberately absent, unlike every
sibling script. `GuardResult` is a frozen dataclass, and under future-annotations
`dataclasses` resolves the defining module via `sys.modules.get(cls.__module__)`
with no `None` guard — so class creation raises `AttributeError` in a module loaded
by `exec_module` without being registered in `sys.modules`. Registering instead
would mean hand-rolling the failed-load cleanup that `import` does for free, and
would make this module a session-global singleton whose memoised parser leaks
across tests. PEP 604 unions evaluate natively above the 3.11 floor, so the import
buys nothing here. Probe-verified in both directions.

Every file read goes through `read_managed_json` / `read_managed_text`, which
`lstat`, require a regular file, open `O_RDONLY | O_NOFOLLOW | O_NONBLOCK`, re-check
type and dev/ino on the descriptor, and cap the read. `O_NONBLOCK` is load-bearing,
not defensive: the type pre-check is path-based and racy, and `os.open` on a FIFO
without it blocks forever — which, in-process, would block inside the engine's
critical section until the lock went stale and a second writer was admitted.

Python 3.11+ standard library only. No third-party imports, no packaging, no
installation.
"""

import contextlib
import functools
import hashlib
import importlib.util
import io
import json
import os
import re
import stat
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    # result type
    "GuardResult",
    # bounded, symlink-safe readers
    "ManagedContentError",
    "read_managed_json",
    "read_managed_text",
    "read_state",
    "state_path_for",
    # canonical contract hashing
    "canonical_contract",
    "sha256_canonical_contract",
    # status parsing + legality
    "UnreadableArtifact",
    "read_md_status",
    "assert_status_legal",
    "validate_run_id",
    "contained",
    "contained_reason",
    # retry caps
    "DEFAULTS",
    # the six read-only guards
    "check_identity",
    "check_plan_current",
    "check_schedule_current",
    "check_phase",
    "check_wave",
    "check_artifact_status",
]

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "assets" / "state.json"


# ── result type ───────────────────────────────────────────────────────────


# Marker prefix distinguishing a crash-refusal from a policy refusal. An operator
# reading `internal-error:` knows the guard could not decide, rather than that it
# decided against them.
INTERNAL_ERROR = "internal-error"

# Bound on ONE interpolated external scalar, not on the whole reason. Several
# authored reasons are deliberately long \u2014 `_BOTH_CAUSES` is a ~900-char recovery
# runbook \u2014 and capping the assembled string clipped it mid-sentence, losing the
# steps an operator needs. So the bound sits where untrusted length actually
# enters: `_scalar()`, at each interpolation of state-file or argv data.
_MAX_SCALAR_CHARS = 120

# Backstop, and load-bearing rather than theoretical: the audit that introduced
# `_scalar` MISSED `check_identity`'s success message, where a 100 KB `run_id`
# reached stdout at exactly this cap. Treat it as what holds when a site is
# missed, not as evidence that none is. Set well above the longest
# authored reason (`_BOTH_CAUSES` plus two digests, ~1050 chars) so it cannot
# truncate legitimate text \u2014 `test_the_longest_authored_reason_survives_intact`
# pins that separation.
_MAX_REASON_CHARS = 4000


class ManagedContentError(ValueError):
    """The file was read safely, but its BYTES are unusable.

    Distinct from the structural failures sharing the same `ValueError` vocabulary
    (unopenable, non-regular, replaced mid-read), and the distinction is load-bearing
    rather than cosmetic: `loop-engine._recover_pending` DELETES `events.pending` — a
    durable audit record — only when its content is invalid, and must keep it when the
    read merely failed. That decision was previously made by substring-matching
    `str(exc)` against a hand-listed set of message fragments, duplicated at two call
    sites: the source-substring gate antipattern this repo records, applied to the
    audit trail. The list had already fallen behind — it omitted the
    non-finite-number message, so a `NaN` in `events.pending` was retained forever and
    re-warned on every transition.

    Subclasses `ValueError` so every existing `except (OSError, UnicodeDecodeError,
    ValueError, ImportError)` clause keeps catching it unchanged.
    """


def _scalar(value: object) -> str:
    """`repr(value)` bounded to one interpolation's worth.

    Use at every site that interpolates data the tool did not author \u2014 a run-id
    from argv, a `schema_version` or status token from a state file, a `--file`
    argument. A 100 KB `run_id` in `state.json` otherwise becomes a 100 KB
    "one-line" stderr message.
    """
    text = repr(value)
    if len(text) > _MAX_SCALAR_CHARS:
        text = text[: _MAX_SCALAR_CHARS - 1] + "\u2026"
    return text


# Every remaining C0 control character plus DEL, escaped rather than passed through.
# `str.split()` already consumes the whitespace ones; what survives is the dangerous
# half, most importantly ESC. Reasons and messages are printed to a stream a
# supervising agent captures and logs, so a `run_id` of "aaa\x1b[2J\x1b[31mFAKE-OK"
# in state.json otherwise emits a real screen-clear and colour change into that
# transcript. Collapsing whitespace alone does not stop it.
_CONTROL_ESCAPES = str.maketrans({c: f"\\x{c:02x}" for c in [*range(32), 127]})


def _bounded(value: object) -> str:
    """`str(value)` bounded, WITHOUT `repr`'s quoting.

    For the one place the output format is pinned by a golden capture:
    `check_identity`'s success message prints `run_id=<value>` unquoted, and
    substituting `_scalar` there changed a shipped CLI's stdout to `run_id='<value>'`
    — caught by the parity table, which is what it is for.

    Control characters are not this function's job: `_one_line` escapes them at the
    `GuardResult` chokepoint, so every reason and message is covered whether or not
    its site remembered a helper. What is left here is the length bound.
    """
    text = str(value)
    if len(text) > _MAX_SCALAR_CHARS:
        text = text[: _MAX_SCALAR_CHARS - 1] + "…"
    return text


def _one_line(text: str) -> str:
    """Collapse whitespace, neutralise control characters, and cap length.

    All three parts are the same one-line CLI contract from different angles:
    collapsing whitespace stops a newline in interpolated data from forging a second
    stderr line, escaping the remaining control characters stops it forging terminal
    output, and the cap is the length backstop (see `_MAX_REASON_CHARS`).
    """
    collapsed = " ".join(str(text).split()).translate(_CONTROL_ESCAPES)
    if len(collapsed) > _MAX_REASON_CHARS:
        collapsed = collapsed[: _MAX_REASON_CHARS - 1] + "\u2026"
    return collapsed


def contained_reason(fn):
    """Containment for the two `None`-means-proceed helpers on the mutation path.

    `validate_run_id` and `assert_status_legal` return `str | None`, where `None`
    means "legal, proceed". They therefore cannot use `contained`: a `GuardResult`
    would be read as a failure by every caller, and — far worse — any containment
    that resolved to `None` would be `approve-plan` sailing past a check that never
    ran. That is the fail-open shape AC14 removes from the status parser, and it must
    not be reintroduced on the write side.

    So this wrapper converts an escaping `Exception` into a **non-empty reason**,
    never `None`. Leaving them unwrapped is not equivalent: the known failure classes
    are already handled inside, but an unexpected one would propagate as a traceback
    out of a lock-holding mutation verb, which is precisely what the child process
    used to prevent.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            result = fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 — the containment boundary itself
            return _one_line(f"{INTERNAL_ERROR}: {type(exc).__name__}: {exc}")
        if result is None:
            return None
        if not str(result).strip():
            # A blank reason would read as a refusal with no cause. Never emit one.
            return f"{INTERNAL_ERROR}: {fn.__name__} produced an empty reason"
        # The NORMAL return needs the same hygiene as the except arm above. It used to
        # be returned raw, so the module's "every reason is whitespace-collapsed and
        # length-capped" claim held only by the accident that every current
        # interpolation site calls `_scalar`. A newline in interpolated data forges a
        # second stderr line, which is a one-line CLI contract violation.
        return _one_line(result)

    return wrapper


@dataclass(frozen=True)
class GuardResult:
    """The outcome of one read-only guard.

    `ok` and `reason` cannot disagree: `__post_init__` raises when they do. That
    matters because the pre-existing convention in `loop-engine.py` was "None on
    success, a non-empty string on failure", so an adapter written `if
    result.reason:` would read an `ok=False, reason=None` result — the natural
    output of a containment bug or a missed branch — as success. Adapters branch on
    `ok`.

    `ValueError`, not `assert`: `-O` / `PYTHONOPTIMIZE` strips assertions, and this
    is the invariant the no-silent-success guarantee rests on.
    """

    ok: bool
    reason: str | None = None
    message: str | None = None
    data: dict | None = None

    def __post_init__(self):
        if self.ok != (self.reason is None):
            raise ValueError(
                "GuardResult invariant violated: ok must be True exactly when "
                f"reason is None (ok={self.ok!r}, reason={self.reason!r})"
            )
        # Reason hygiene belongs HERE, at the one chokepoint every refusal passes
        # through — not only in `contained`'s except arm, which is where it lived
        # and which covers just the crash path. Policy refusals interpolate
        # attacker-influenceable values (`stored={run_id!r}`, a status token, a
        # filename), and a 100 KB `run_id` in state.json produced a 100,055-character
        # reason on the agent-captured stderr. For an agentic surface that is a
        # context flood and a carrier into the supervising agent's window.
        if self.reason is not None:
            cleaned = _one_line(self.reason)
            if not cleaned:
                # A blank-but-not-None reason is a FAIL-OPEN, not a cosmetic defect.
                # The invariant above only compares `reason is None`, so
                # `GuardResult(ok=False, reason="")` constructs happily — and any
                # adapter written as `if result.reason:` then reads a refusal as
                # success. `contained_reason` already refuses to produce one on the
                # mutation path; this closes the same hole on the result type.
                raise ValueError(
                    "GuardResult invariant violated: reason is blank, which reads as "
                    f"success to any truthiness check (reason={self.reason!r})"
                )
            if cleaned != self.reason:
                object.__setattr__(self, "reason", cleaned)  # frozen dataclass
        if self.message is not None:
            cleaned = _one_line(self.message)
            if cleaned != self.message:
                object.__setattr__(self, "message", cleaned)


def contained(fn):
    """Turn any escaping `Exception` into a refusal.

    This restores what the child-process boundary used to provide for free: its exit
    code converted every unexpected exception into a refusal, so nothing reached the
    caller as a traceback. In-process there is no such boundary, and an
    `OverflowError` from `int(float("inf"))` on a malformed retry cap would surface
    out of a process holding the engine-state lock.

    `Exception` only. `BaseException` — `KeyboardInterrupt`, `SystemExit` — passes
    through untouched. Lock-integrity exceptions need no clause here: this module
    never acquires a lock, so `_statelock`'s `StateLockLost` cannot originate inside
    a contained call; `loop-cohort.with_state_lock`'s own handler remains its only
    one. Naming the class would force this layer to import the lock module, which
    its import allowlist forbids.

    The reason never carries raw artifact content — only an exception type and a
    message — because a refusal is printed to a stderr the agent captures. It DOES
    name the failing guard: six guards share this decorator and their reasons are
    otherwise indistinguishable, so an operator reading `internal-error: RuntimeError:
    ...` could not tell which decision failed to be made.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 — the containment boundary itself
            return GuardResult(
                ok=False,
                reason=_one_line(
                    f"{INTERNAL_ERROR}: {fn.__name__}: {type(exc).__name__}: {exc}"
                ),
            )

    return wrapper


# ── managed-read cap ────────────────────────────────────────────────────

_MAX_MANAGED_JSON_BYTES = 8 * 1024 * 1024


# ── template readers + DEFAULTS ─────────────────────────────────────────

def _template_retry_cap(field: str, fallback: int) -> int:
    """Read one retry cap from the bundled `assets/state.json` template.

    The cap is single-sourced in the template — the adopter-visible knob — so this
    reads it rather than hard-coding a duplicate. The `fallback` default is the one
    sanctioned duplicate, and `test_loop_cohort_max_iter_single_source.py` polices it
    against the template.

    `FileNotFoundError` ONLY falls back. The original caught
    `(FileNotFoundError, OSError, KeyError, TypeError, ValueError)`, and routing this
    read through the bounded reader would have folded every integrity failure —
    oversized, non-regular, symlinked, replaced mid-read — into that same silent
    5/5 default. That is the identical fail-open shape as the parser's old
    `except ImportError: return None`, so it refuses instead. A genuinely absent
    template (an adopter tree that ships none) still falls back.
    """
    try:
        raw = read_managed_json(TEMPLATE_PATH, "assets/state.json")
    except FileNotFoundError:
        return fallback
    try:
        return int(raw[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"assets/state.json has no usable {field}: {exc}"
        ) from exc


def _template_max_implementation_retries(fallback: int = 5) -> int:
    """Read max_implementation_retries from the bundled state.json template."""
    return _template_retry_cap("max_implementation_retries", fallback)


def _template_max_review_retries(fallback: int = 5) -> int:
    """Read max_review_retries from the bundled state.json template."""
    return _template_retry_cap("max_review_retries", fallback)


class _LazyDefaults(Mapping):
    """Eagerly BOUND, lazily POPULATED.

    Both properties are required and they pull against each other. Eager binding:
    `test_loop_cohort_max_iter_single_source.py` does `mod.DEFAULTS[...]` immediately
    after `exec_module`, with no verb invoked, so a plain function or
    `cached_property` breaks it. Lazy population: importing this module must perform
    no file I/O, because the first guard call happens inside the engine's critical
    section and an uncapped template read there is exactly the unbounded hold this
    change exists to remove.

    A `Mapping` rather than a dict subclass so there is no way to end up with a
    half-populated dict that reads as complete.
    """

    _KEYS = ("max_implementation_retries", "max_review_retries")

    def __init__(self):
        self._values: dict | None = None

    def _load(self) -> dict:
        if self._values is None:
            self._values = {
                "max_implementation_retries": _template_max_implementation_retries(),
                "max_review_retries": _template_max_review_retries(),
            }
        return self._values

    def __getitem__(self, key):
        return self._load()[key]

    def __iter__(self):
        return iter(self._KEYS)

    def __len__(self):
        return len(self._KEYS)

    def __repr__(self):
        return f"_LazyDefaults({self._values!r})" if self._values else "_LazyDefaults(unloaded)"


DEFAULTS = _LazyDefaults()


# ── state paths + managed JSON read ─────────────────────────────────────

def state_path_for(spec_dir: Path) -> Path:
    return spec_dir / "state.json"


def _read_managed_bytes(path: Path, label: str) -> bytes:
    """Read a bounded regular file's bytes without following or racing a symlink.

    The shared descriptor discipline behind both public readers, so JSON state files
    and Markdown artifacts cannot drift apart on safety. Unchanged from the original
    apart from `O_NONBLOCK` below: lstat, require S_ISREG, open, re-check type and
    dev/ino on the descriptor, cap the read, and re-verify identity afterwards so a
    file replaced mid-read is refused rather than silently half-read.
    """
    try:
        before = os.lstat(path)
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise ValueError(f"{label} cannot be examined: {exc}") from exc
    if not stat.S_ISREG(before.st_mode):
        raise ValueError(f"{label} must be a regular file")
    if before.st_size > _MAX_MANAGED_JSON_BYTES:
        raise ManagedContentError(
            f"{label} exceeds {_MAX_MANAGED_JSON_BYTES}-byte (8 MiB) limit"
        )
    # O_NONBLOCK is load-bearing, not defensive. The S_ISREG check above is
    # path-based and therefore racy: swap the regular file for a FIFO between
    # the lstat and this open, and `os.open` blocks forever waiting for a
    # writer, so the post-open type re-check below never runs. In-process that
    # block sits inside the engine's critical section until the lock is judged
    # stale and a second writer is admitted — the lost update the lock exists
    # to prevent. With O_NONBLOCK the open returns immediately and the fstat
    # rejects it. Verified: no-op for regular files, immediate for a FIFO.
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise ValueError(f"{label} cannot be opened safely: {exc}") from exc
    try:
        try:
            opened = os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode):
                raise ValueError(f"{label} must be a regular file")
            identity = (before.st_dev, before.st_ino)
            if (opened.st_dev, opened.st_ino) != identity:
                raise ValueError(f"{label} changed while being opened")
            chunks: list[bytes] = []
            remaining = _MAX_MANAGED_JSON_BYTES + 1
            while remaining:
                chunk = os.read(fd, min(64 * 1024, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            raw = b"".join(chunks)
            after_fd = os.fstat(fd)
        except OSError as exc:
            raise ValueError(f"{label} could not be read safely: {exc}") from exc
    finally:
        os.close(fd)
    # BOTH halves are deliberate, and the `after_fd` one was briefly deleted as
    # "tautological" during review. It is not removable: a descriptor's dev/ino cannot
    # change under a real kernel, so this comparison indeed cannot fire from an
    # ordinary filesystem race — but "the reader verifies descriptor identity twice"
    # is a pinned contract with two pre-existing tests asserting the second `fstat`
    # happens (`test_cohort_state_reader_rejects_identity_change` and its engine twin
    # both fail with "did not verify descriptor identity twice"). Removing it broke
    # both. The path half below catches the case that CAN fire — the path re-pointed
    # at a different inode mid-read, which the `O_NOFOLLOW` open cannot see alone.
    try:
        after_path = os.lstat(path)
    except OSError as exc:
        raise ValueError(f"{label} changed while being read") from exc
    if (
        (after_fd.st_dev, after_fd.st_ino) != identity
        or (after_path.st_dev, after_path.st_ino) != identity
    ):
        raise ValueError(f"{label} changed while being read")
    if len(raw) > _MAX_MANAGED_JSON_BYTES:
        raise ManagedContentError(
            f"{label} exceeds {_MAX_MANAGED_JSON_BYTES}-byte (8 MiB) limit"
        )
    return raw


def read_managed_json(path: Path, label: str) -> dict:
    """Read a bounded regular JSON object without following or racing a symlink."""
    raw = _read_managed_bytes(path, label)

    def _reject_non_finite(token: str):
        # The three non-standard LITERALS json accepts: NaN, Infinity, -Infinity.
        raise ManagedContentError(f"{label} contains the non-finite number {token}")

    def _reject_float(token: str):
        # And the OVERFLOW route, which `parse_constant` does NOT cover: `1e400`
        # parses as an ordinary float and json.loads returns `inf` without ever
        # consulting parse_constant (verified). That `inf` then reached arithmetic
        # as a traceback out of a lock-holding mutation verb, which is exactly what
        # the literal check above was added to prevent.
        #
        # Scoped to the NON-FINITE result only. Rejecting every float here was
        # over-broad and regressed a preserved verdict: `non_negative_int` already
        # refuses any non-`int` counter by `isinstance` — including every finite
        # float — with its own message, and never calls `int()`, so there is no
        # overflow path for a finite value to reach. Widening this to all floats
        # merely stole that refusal and changed its wording.
        value = float(token)
        if value in (float("inf"), float("-inf")) or value != value:
            raise ManagedContentError(
                f"{label} contains the non-finite number {_scalar(token)}"
            )
        return value

    try:
        data = json.loads(
            raw.decode("utf-8"),
            parse_constant=_reject_non_finite,
            parse_float=_reject_float,
        )
    except UnicodeDecodeError as exc:
        raise ManagedContentError(f"{label} is not valid UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ManagedContentError(
            f"{label} malformed: {exc.msg} at line {exc.lineno}"
        ) from exc
    except RecursionError as exc:
        # `json.loads` raises this — NOT a `ValueError` — on a deeply nested document,
        # so it escaped every reader-vocabulary handler and reached a lock holder as a
        # traceback. It is unambiguously invalid content: the bytes parsed nowhere and
        # no amount of retrying helps. Classifying it structurally instead would leave
        # a planted `.engine-state-*.json.tmp` in place, re-warning on every
        # transition forever.
        raise ManagedContentError(f"{label} is nested too deeply to parse") from exc
    if not isinstance(data, dict):
        raise ManagedContentError(f"{label} root must be an object")
    return data


def read_managed_text(path: Path, label: str) -> str:
    """Read a bounded, regular, non-symlinked Markdown artifact as text.

    Same descriptor discipline as `read_managed_json` — that is the point: `spec.md`
    and `plan.md` were read with a plain `path.read_text()`, which follows symlinks,
    has no size cap, and blocks forever on a FIFO. That was survivable only because
    the read happened in a child process bounded by a subprocess timeout. In-process
    there is no such bound, so it gets the same treatment as the state files.

    Decoding note: `read_text()` folds CR and CRLF to LF via universal newlines,
    which made `canonical_contract`'s own fold redundant. Reading bytes here removes
    that free normalization, so the fold becomes the control that keeps a
    CR-authored artifact hashing identically — mutation-verified in T0. Decoded
    strictly, because a malformed artifact must refuse rather than silently differ.
    """
    raw = _read_managed_bytes(path, label)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ManagedContentError(f"{label} is not valid UTF-8") from exc


def read_state(spec_dir: Path) -> dict:
    path = state_path_for(spec_dir)
    try:
        return read_managed_json(path, "state.json")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"state.json missing at {path}") from exc


# ── parser loader + sha helper ──────────────────────────────────────────

_lint_module: object | None = None


_PARSER_SYMBOLS = (
    "parse_status", "extract_status_token", "_STATUS_RE",
    "_SECTION_HEADING_RE", "_HTML_COMMENT_RE", "_AC_DONE_RE",
)


def _lint_spec_status():
    """Load `lint-spec-status.py` — the ONE canonical Markdown status parser.

    Four controls the sibling `_statelock` loader lacks, and one reason each:

    1. `lstat` + `S_ISREG` on the module path. A symlink there is followed silently
       by `exec_module`, and this module is executed inside the lock-holding engine.
    2. `sys.dont_write_bytecode` saved, set, and restored to its PRIOR value. Not to
       `False`: these loaders nest under a host interpreter that may have been
       started with `-B`, and clobbering that would be a side effect on unrelated
       imports. Suppressing the write keeps a stale or poisoned `.pyc` from being
       created here; a pre-existing one remains the accepted residual.
    3. Stream swap. `lint-spec-status.py` calls `sys.stdout.reconfigure(...)` at
       module scope. That mutates the stream in place — it does NOT rebind
       `sys.stdout` — so snapshotting the reference would restore nothing. The real
       hazard is the reverse: a caller whose `sys.stdout` lacks `reconfigure` (an
       `io.StringIO`, which is how this pack's own tests capture output) makes that
       line raise. Swapping in a throwaway `TextIOWrapper` keeps the caller's stream
       untouched and always provides `reconfigure`. Deliberately not
       `sys.__stdout__`: that is `None` under pythonw, embedded, and detached-stdio
       contexts, which would turn a working environment into a refusing one.
    4. Completeness. A module truncated at a clean statement boundary loads without
       raising; requiring the symbols the guard path actually uses turns that into a
       load failure instead of a parser missing `parse_status`.

    Every failure is re-raised as `ImportError` so the callers' existing
    `except (ImportError, OSError)` refusal clauses cover it — including
    `SyntaxError`, which derives from `Exception`, not from `ValueError`, and would
    otherwise escape as a traceback.
    """
    global _lint_module
    if _lint_module is not None:
        return _lint_module

    lint_path = Path(__file__).resolve().parent / "lint-spec-status.py"
    try:
        info = os.lstat(lint_path)
    except OSError as exc:
        raise ImportError(
            f"cannot load {lint_path}: {exc}. Restore the file or re-run "
            "`make build-self` to regenerate the projection."
        ) from exc
    if not stat.S_ISREG(info.st_mode):
        raise ImportError(
            f"cannot load {lint_path}: not a regular file (symlink or device). "
            "Restore the file or re-run `make build-self`."
        )

    previous_dont_write = sys.dont_write_bytecode
    real_stdout, real_stderr = sys.stdout, sys.stderr
    sink_out = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    sink_err = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    try:
        sys.dont_write_bytecode = True
        sys.stdout, sys.stderr = sink_out, sink_err
        spec = importlib.util.spec_from_file_location("_lint_spec_status", str(lint_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {lint_path}: no import spec")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except ImportError:
        raise
    except BaseException as exc:
        # BaseException, not Exception: a mis-set `__name__` would run the module's
        # `if __name__ == "__main__": sys.exit(main())`, and SystemExit(0) escaping
        # from here would report success from a guard that evaluated nothing.
        raise ImportError(
            f"cannot load {lint_path}: {type(exc).__name__}: {exc}. Restore the "
            "file or re-run `make build-self`."
        ) from exc
    finally:
        sys.dont_write_bytecode = previous_dont_write
        sys.stdout, sys.stderr = real_stdout, real_stderr
        with contextlib.suppress(Exception):
            sink_out.close()
            sink_err.close()

    missing = [name for name in _PARSER_SYMBOLS if not hasattr(module, name)]
    if missing:
        raise ImportError(
            f"cannot load {lint_path}: incomplete module, missing {missing}. The "
            "file is truncated — restore it or re-run `make build-self`."
        )
    _lint_module = module
    return _lint_module


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ── canonical contract ──────────────────────────────────────────────────

_STATUS_PLACEHOLDER = "<loop-cohort:status>"
# A heading, or the bold prose lead-in two specs here use instead. Missing the
# latter would leave those specs with no normalization at all — i.e. AC5
# failing for them by construction, the defect this spec exists to fix.
_AC_HEADING_RE = re.compile(
    r"^ {0,3}(?:#{2,3}\s+|\*\*)Acceptance\s+Criteria\b", re.IGNORECASE
)
# A region closes on the next heading at its own depth or shallower — a sibling
# or an ancestor — and never on a deeper one. That single rule replaces the
# hand-cased pair it grew out of: H3 subheadings sit inside H2-opened AC
# sections all over this repo and must not close them, while an H3-opened
# section is closed by the next H3, which a fixed `#{1,2}` test missed entirely.
# A bold lead-in has no depth, so it takes _BOLD_DEPTH — deeper than any
# heading, so every heading closes it — and also closes on the next bold lead-in,
# without which it would run to EOF and un-pin every later checkbox, including a
# `Never do` item, which is the scope the pin exists to protect.
_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})[ \t]")
_BOLD_LEAD_RE = re.compile(r"^ {0,3}\*\*")
_BOLD_DEPTH = 7

# AC10: a mismatch has two possible causes and the verb cannot tell them apart,
# so it names both rather than asserting the one that is usually wrong.
_BOTH_CAUSES = (
    "either the approved scope changed, or this baseline was pinned before "
    "canonical hashing landed. For the second case, recover the cohort only: "
    "(1) restore `Status: Approved` in BOTH spec.md and plan.md — approve-plan "
    "refuses unless both read Approved; (2) `loop-cohort reset <spec-dir>`; "
    "(3) `loop-cohort init <spec-dir> --run-id <run_id>`, taking run_id from "
    "`loop-engine status <spec-dir> --json`; (4) `loop-cohort approve-plan "
    "<spec-dir> --expect-run-id <run_id>` then `loop-cohort schedule <spec-dir> "
    "--expect-run-id <run_id>`; "
    "(5) restore the Status you were on. Do NOT run `loop-engine reset` — "
    "`plan-locked` is legal only from SPEC-PLAN-APPROVED and the engine has no "
    "state-setting verb, so resetting it strands the run. Note the reset clears "
    "the retry counters and the stasis baseline, and re-running approve-plan "
    "re-pins whatever is on disk, so it is a re-approval in substance"
)


def canonical_contract(text: str, *, ac_section_only: bool = True) -> str:
    """Canonical form of spec.md / plan.md for approval pinning.

    Normalizes exactly four things: CRLF/CR → LF; per-line trailing whitespace;
    the preamble status *token*; and the bracket contents of a checkbox.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    lint = _lint_spec_status()
    # Newline-preserving comment strip. `parse_status` uses a plain sub() with
    # re.DOTALL, which collapses a multiline comment to nothing and shifts every
    # later line index — fine when you only want the token, wrong here, where
    # the index has to map back to the raw line being rewritten.
    cleaned = lint._HTML_COMMENT_RE.sub(
        lambda m: "\n" * m.group(0).count("\n"), text
    ).split("\n")

    for i, cleaned_line in enumerate(cleaned):
        if lint._SECTION_HEADING_RE.match(cleaned_line):
            break  # preamble ends at the first section heading
        if cleaned_line.lstrip().startswith("#"):
            continue
        if not lint._STATUS_RE.search(cleaned_line):
            continue
        # Rewrite the *raw* line, not the comment-stripped one.
        raw = lines[i]
        m = lint._STATUS_RE.search(raw)
        if m is None:
            break
        token = lint.extract_status_token(m.group(1))
        if token:
            # Span-bounded splice of the token only. A str.replace would also
            # rewrite the token where it recurs inside the trailing vocabulary
            # comment (`<!-- Draft | Approved | Implementing | ... -->`) that
            # every spec and plan the template emits carries — making each
            # status normalize differently. Splicing _STATUS_RE's whole group(1) span
            # would swallow appended free text and defeat the pin.
            start = m.start(1)
            lines[i] = raw[:start] + _STATUS_PLACEHOLDER + raw[start + len(token):]
        break

    # Which checkboxes count as bookkeeping depends on the artifact, so the
    # caller says. A spec's progress marks live in its Acceptance Criteria
    # section; a checkbox under `## Boundaries` is a `Never do` item, which is
    # precisely the scope the pin protects. This is a forward invariant: no
    # spec carries such a checkbox today.
    # A plan has no such section: every checkbox in it is task progress, and
    # four plans here carry them, so a plan is normalized file-wide.
    #
    # Case-insensitive on purpose: `lint-spec-status.py` matches `Acceptance
    # Criteria` exactly, so its own AC extraction silently returns nothing for
    # the specs that spell it with a lowercase `c`. Inheriting that bug here
    # would break this normalization for exactly those specs. Tracked as
    # `spec-ac-heading-casing-silent-gate`.
    in_ac = not ac_section_only
    opened_depth = _BOLD_DEPTH
    fence_char = fence_len = None
    for i, line in enumerate(lines):
        # CommonMark fence semantics, not a toggle. A toggle desyncs on a
        # nested fence — a ```toml inside a ```markdown example flips the state
        # back — and one real plan in this tree has an odd fence count, which
        # left the tracker stuck open and disabled normalization for the rest of
        # the file. Only a bare run of the opening character, at least as long,
        # closes; a line carrying an info string always opens.
        stripped = line.lstrip()
        marker = stripped[:1]
        if marker in ("`", "~"):
            run = len(stripped) - len(stripped.lstrip(marker))
            info = stripped[run:].strip()
            if fence_char is None:
                if run >= 3:
                    fence_char, fence_len = marker, run
                    continue
            elif marker == fence_char and run >= fence_len and not info:
                fence_char = fence_len = None
                continue
        if fence_char is not None:
            continue
        if ac_section_only and _AC_HEADING_RE.match(line):
            in_ac = True
            opener = _HEADING_RE.match(line)
            opened_depth = len(opener.group(1)) if opener else _BOLD_DEPTH
            continue
        if ac_section_only and in_ac:
            closer = _HEADING_RE.match(line)
            if (closer and len(closer.group(1)) <= opened_depth) or (
                opened_depth == _BOLD_DEPTH and _BOLD_LEAD_RE.match(line)
            ):
                in_ac = False
        if in_ac and lint._AC_DONE_RE.match(line):
            # Bracket contents only — leading whitespace and the bullet run stay
            # byte-for-byte, so re-indenting a criterion still moves the digest.
            j = line.index("[")
            lines[i] = line[:j + 1] + " " + line[j + 2:]

    return "\n".join(line.rstrip() for line in lines)


def sha256_canonical_contract(path: Path) -> str:
    """SHA-256 of canonical_contract(<spec.md | plan.md>).

    `canonical_contract` loads the canonical status parser, so this can raise
    `ImportError` for a reason that has nothing to do with `path`. The guards see it
    through `@contained`, but the cohort's mutation verbs call this DIRECTLY and
    their `except` tuples were widened for the reader's `ValueError` only — so an
    unloadable parser surfaced as a traceback out of `approve-plan` and `schedule`,
    both of which hold the cohort state lock. Converting here means every caller
    inherits the fix rather than each having to remember it.
    """
    try:
        canonical = canonical_contract(
            read_managed_text(path, path.name),
            ac_section_only=(path.name != "plan.md"),
        )
    except ImportError as exc:
        raise ValueError(
            f"{path.name}: canonical status parser unavailable: {exc}"
        ) from exc
    return _sha256_bytes(canonical.encode("utf-8"))


# ── run-id validation ───────────────────────────────────────────────────

@contained_reason
def validate_run_id(state: dict, expect_run_id: str, *, verb: str) -> str | None:
    """Return None when the run-id pairing is legal, else a one-line reason.

    `None` means "proceed", so this uses `contained_reason` rather than `contained`:
    a `GuardResult` would be read as a failure by every caller, and a containment
    that resolved to `None` would be `approve-plan` proceeding past a check that
    never ran. Callers convert the reason; the six mutation verbs that use this keep
    their `stop(...)` mapping in `loop-cohort.py`.

    Distinct from `check_identity`'s messages on purpose — two different decisions
    with two different message sets, which must not be merged.
    """
    sv = state.get("schema_version")
    if sv != 1:
        return (
            f"{verb}: unsupported schema_version={_scalar(sv)} (expected 1); run reset pair"
        )
    stored = state.get("run_id")
    if stored != expect_run_id:
        return (
            f"{verb}: --expect-run-id mismatch (stored={_scalar(stored)}, "
            f"supplied={_scalar(expect_run_id)})"
        )
    return None


# ── status legality ─────────────────────────────────────────────────────

class UnreadableArtifact(Exception):
    """The artifact exists but could not be read as UTF-8 markdown."""


def read_md_status(path: Path) -> str | None:
    """Return the canonical status token, or None when the file has none.

    None means "no status line", which callers legitimately skip. A file that
    cannot be *read* is a different thing and must not be silently skipped —
    it raises, so the caller stops with a reason instead of proceeding on a
    guard that quietly did nothing.
    """
    try:
        text = read_managed_text(path, path.name)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        # ValueError is new, and it is the bounded reader's whole failure vocabulary
        # (oversized, non-regular, symlinked, replaced mid-read, bad UTF-8). Without
        # it here, an unsafe artifact would raise past `assert_status_legal`'s
        # handler and out of a lock-holding mutation verb as a traceback.
        # No `{path.name}: ` prefix here, deliberately — and note the asymmetry with
        # the parser branch below. `read_managed_text` is called with `path.name` as
        # its label, so every message in its failure vocabulary already opens with the
        # filename; prefixing again produced `spec.md: spec.md cannot be opened
        # safely: …`. The parser branch DOES prefix, because an `ImportError` carries
        # no filename of its own and no caller supplies one.
        raise UnreadableArtifact(str(exc)) from exc
    try:
        return _lint_spec_status().parse_status(text)
    except ImportError as exc:
        # NOT `return None`. That is what None means here — "no status line" — which
        # `assert_status_legal` legitimately SKIPS. So an unloadable canonical parser
        # used to make the post-approval status-regression guard silently pass: a
        # security control defaulting to allow on error. A broken parser is now
        # indistinguishable from an unreadable artifact, which is a refusal.
        raise UnreadableArtifact(
            f"{path.name}: canonical status parser unavailable: {exc}"
        ) from exc


# Normalizing the status token out of the hash also removed the incidental
# detection of a *regressed* status: an approved run whose spec.md went back to
# Draft used to trip the byte compare. Assert it directly instead, at every verb
# that reads a pinned artifact — a compensating control that covers one of three
# call sites is not a compensating control.
#
# An absent or unparseable token is skipped, not stopped: plan fixtures
# legitimately carry no status line, and this must not become a new way for a
# CODE-* pre-guard to go red.
_LEGAL_AFTER_APPROVAL = {
    "spec.md": ("Approved", "Implementing", "Shipped"),
    "plan.md": ("Approved", "Executing", "Done"),
}


@contained_reason
def assert_status_legal(verb: str, *paths: Path) -> str | None:
    """Return None when every pinned artifact's status is legal, else a reason.

    Same `None`-means-proceed shape as `validate_run_id`, and wrapped with
    `contained_reason` for the same reason.

    An artifact that does not exist is skipped, as before — but note the asymmetry
    this preserves: `Path.exists()` is False for a broken symlink, so a dangling link
    is skipped here and caught by the reader when the artifact is actually needed.
    """
    for path in paths:
        allowed = _LEGAL_AFTER_APPROVAL.get(path.name)
        if allowed is None or not path.exists():
            continue
        try:
            token = read_md_status(path)
        except UnreadableArtifact as exc:
            return f"{verb}: {exc}"
        # `extract_status_token` returns "" — not None — when the value is only
        # an HTML comment, so `is not None` would stop on it. AC9's promise is
        # that an absent *or unparseable* token is skipped, and that promise is
        # the whole safety argument for wiring this into a CODE-* pre-guard.
        if token and token not in allowed:
            return (
                f"{verb}: {path.name} Status is {_scalar(token)}; expected one of "
                f"{list(allowed)} after approval"
            )
    return None


# ── the six read-only guards ───────────────────────────────────────────────
#
# One implementation each, called by `loop-engine.py` in-process, by the matching
# `loop-cohort.py` / `check-spec-status.py` CLI verb, and by tests. Every reason and
# success string is the verb's existing text verbatim, minus the CLI's own prefix —
# the adapters add that back, and T0's goldens hold the pre-change literals.
#
# Each guard reads the files it needs at call time. Three guards in one transition
# therefore perform three fresh bounded reads, exactly as three child processes did.
# A shared snapshot is the one change that could alter behaviour under concurrent
# cohort mutation, so it is deliberately absent.


def _require_spec_dir(spec_dir: Path) -> str | None:
    """Validate the one thing a callee can: that `spec_dir` is a directory.

    Confinement belongs to the caller (see the module docstring). Re-testing
    "absolute, no `..`" here would be dead code — every caller resolves first — so
    this checks existence and type instead, which can actually fail.
    """
    try:
        info = os.lstat(spec_dir)
    except OSError as exc:
        return f"spec-dir cannot be examined: {exc}"
    if not stat.S_ISDIR(info.st_mode):
        return f"spec-dir is not a directory: {spec_dir}"
    return None


def _state_or_reason(spec_dir: Path) -> tuple[dict | None, str | None]:
    """Read `state.json`, mapping its failure vocabulary to a reason."""
    problem = _require_spec_dir(spec_dir)
    if problem is not None:
        return None, problem
    try:
        return read_state(spec_dir), None
    except (FileNotFoundError, ValueError) as exc:
        return None, str(exc)


@contained
def check_identity(spec_dir: Path, *, expect_run_id: str | None) -> GuardResult:
    """Engine/cohort run-ID pairing, plus the cohort schema version."""
    state, reason = _state_or_reason(spec_dir)
    if reason is not None:
        return GuardResult(ok=False, reason=reason)
    if state.get("schema_version") != 1:
        sv = state.get("schema_version")
        return GuardResult(
            ok=False,
            reason=f"identity: unsupported schema_version={_scalar(sv)} (expected 1)",
        )
    stored = state.get("run_id")
    if expect_run_id is not None and stored != expect_run_id:
        return GuardResult(
            ok=False,
            reason=(
                f"identity: run_id mismatch (stored={_scalar(stored)}, "
                f"expected={_scalar(expect_run_id)})"
            ),
        )
    return GuardResult(
        ok=True,
        message=(
            f"run_id={_bounded(stored)} "
            f"schema_version={_bounded(state.get('schema_version'))}"
        ),
        data={"run_id": stored, "schema_version": state.get("schema_version")},
    )


@contained
def check_plan_current(spec_dir: Path, *, require_schedule: bool = False) -> GuardResult:
    """Approved spec and plan baselines still match what is on disk."""
    state, reason = _state_or_reason(spec_dir)
    if reason is not None:
        return GuardResult(ok=False, reason=reason)

    if state.get("plan_review_status") != "approved":
        # Deliberately unprefixed, as it has always been. The engine reads exit
        # status, and the skill documents this exact string as the cue to run
        # pre-EXECUTE review rather than as a termination signal.
        return GuardResult(ok=False, reason="plan_review_status: pending")

    spec_path = spec_dir / "spec.md"
    plan_path = spec_dir / "plan.md"
    if not spec_path.exists():
        return GuardResult(
            ok=False, reason=f"plan check-current: spec.md not found at {spec_path}"
        )
    if not plan_path.exists():
        return GuardResult(
            ok=False, reason=f"plan check-current: plan.md not found at {plan_path}"
        )

    legality = assert_status_legal("plan check-current", spec_path, plan_path)
    if legality is not None:
        return GuardResult(ok=False, reason=legality)

    current_spec_hash = sha256_canonical_contract(spec_path)
    if state.get("approved_spec_hash") != current_spec_hash:
        return GuardResult(
            ok=False,
            reason=(
                "plan check-current: spec.md no longer matches the approved baseline — "
                + _BOTH_CAUSES
                + f" (approved={_scalar(state.get('approved_spec_hash', 'null'))} "
                f"current={current_spec_hash!r})"
            ),
        )

    current_plan_hash = sha256_canonical_contract(plan_path)
    if state.get("approved_plan_hash") != current_plan_hash:
        return GuardResult(
            ok=False,
            reason=(
                "plan check-current: plan.md no longer matches the approved baseline — "
                + _BOTH_CAUSES
                + f" (approved={_scalar(state.get('approved_plan_hash', 'null'))} "
                f"current={current_plan_hash!r})"
            ),
        )

    if require_schedule:
        if state.get("plan_hash") != state.get("approved_plan_hash"):
            return GuardResult(
                ok=False,
                reason=(
                    "plan check-current: plan_hash != approved_plan_hash "
                    "(schedule not run or run on a different plan version); "
                    + _BOTH_CAUSES
                ),
            )
        waves = state.get("schedule_waves", [])
        if not waves:
            return GuardResult(
                ok=False,
                reason="plan check-current: schedule_waves is empty (run schedule first)",
            )
        idx = non_negative_int(state, "current_wave_index", 0)
        if isinstance(idx, str):
            return GuardResult(ok=False, reason=f"plan check-current: {idx}")
        if not (0 <= idx < len(waves)):
            return GuardResult(
                ok=False,
                reason=(
                    f"plan check-current: current_wave_index={_scalar(idx)} out of range "
                    f"[0, {len(waves)})"
                ),
            )

    return GuardResult(
        ok=True, message=f"plan check-current OK for {spec_dir.name}"
    )


@contained
def check_schedule_current(spec_dir: Path) -> GuardResult:
    """The scheduled plan is still the plan on disk."""
    state, reason = _state_or_reason(spec_dir)
    if reason is not None:
        return GuardResult(ok=False, reason=reason)
    plan_path = spec_dir / "plan.md"
    if not plan_path.exists():
        return GuardResult(
            ok=False,
            reason=f"schedule check-current: plan.md not found at {plan_path}",
        )
    legality = assert_status_legal("schedule check-current", plan_path)
    if legality is not None:
        return GuardResult(ok=False, reason=legality)
    current = sha256_canonical_contract(plan_path)
    stored = state.get("plan_hash")
    if stored != current:
        return GuardResult(
            ok=False,
            reason=(
                "schedule check-current: plan.md no longer matches the scheduled "
                "baseline — " + _BOTH_CAUSES
                + f" (stored={_scalar(stored)} current={current!r})"
            ),
        )
    return GuardResult(
        ok=True, message=f"schedule check-current OK for {spec_dir.name}"
    )


def non_negative_int(state: dict, field: str, default):
    """Validate a counter as a non-negative int, or return a reason string.

    `int()` coerced `"3"`, `3.7` and `-1` alike, so a malformed counter changed the
    retry-cap arithmetic silently — and `Infinity` raised `OverflowError` out of the
    guard entirely. The non-finite case is refused earlier, at the JSON boundary;
    this catches the rest. Returns a `str` on failure so callers can prefix it with
    their own verb name, matching the existing message shapes.
    """
    raw = state.get(field, default)
    if isinstance(raw, bool) or not isinstance(raw, int):
        return f"{field} must be a non-negative integer, got {type(raw).__name__}"
    if raw < 0:
        return f"{field} must be a non-negative integer, got {_scalar(raw)}"
    return raw


@contained
def check_phase(spec_dir: Path, *, phase: str,
                allow_review_retry_cap_override: bool = False) -> GuardResult:
    """Implementation and review retry caps.

    Reads state FIRST, for every phase including `implement`. `cmd_check` has always
    called `read_state` before reaching the `implement` stub, so `check --phase
    implement` is not a total no-op: it refuses on a missing or malformed
    `state.json`. Returning `ok` unconditionally for `implement` would drop a live
    refusal that the `wave-complete` guard depends on.

    `allow_review_retry_cap_override` waives the **review** cap only, and only for
    a caller that asked for it. It is named for that one cap rather than for both
    because only `findings-remain` plumbs it through: `review record` has the
    matching flag, and a human going past the review cap has to clear the
    transition and the recording together or the two halves desync. The
    implementation cap at `gates-failed` has no such pair and no way to set this,
    so it is deliberately not consulted here.
    """
    state, reason = _state_or_reason(spec_dir)
    if reason is not None:
        return GuardResult(ok=False, reason=reason)

    # The `implement` phase skips schema validation so pre-Phase-1 state files do not
    # break the hook; phases that actually evaluate counters reject incompatible state.
    if phase != "implement" and state.get("schema_version") != 1:
        sv = state.get("schema_version")
        return GuardResult(
            ok=False,
            reason=f"check: unsupported schema_version={_scalar(sv)} (expected 1); run reset pair",
        )

    if phase == "implement":
        # Phase-1 compatibility stub: exits 0 for any readable Phase-1 state.
        return GuardResult(ok=True, message="")

    if phase == "gates-failed":
        count = non_negative_int(state, "implementation_retry_count", 0)
        cap = non_negative_int(state, "max_implementation_retries",
                                DEFAULTS["max_implementation_retries"])
        for value in (count, cap):
            if isinstance(value, str):
                return GuardResult(ok=False, reason=f"check: {value}")
        if count >= cap:
            return GuardResult(
                ok=False,
                reason=(
                    f"implementation retry cap reached ({_scalar(count)}/{_scalar(cap)}); "
                    "reset and start a new run"
                ),
            )
        return GuardResult(ok=True, message="")

    if phase == "review":
        count = non_negative_int(state, "review_retry_count", 0)
        cap = non_negative_int(state, "max_review_retries",
                                DEFAULTS["max_review_retries"])
        for value in (count, cap):
            if isinstance(value, str):
                return GuardResult(ok=False, reason=f"check: {value}")
        if count >= cap and not allow_review_retry_cap_override:
            # Wording unchanged, deliberately. This reason is printed by
            # `loop-cohort check --phase review`, which accepts no override, as
            # well as by the `findings-remain` transition, which does -- so the
            # shared text names no flag and each adapter appends its own remedy.
            return GuardResult(
                ok=False,
                reason=(
                    f"review retry cap reached ({_scalar(count)}/{_scalar(cap)}); "
                    "reset and start a new run"
                ),
            )
        return GuardResult(ok=True, message="")

    return GuardResult(ok=False, reason=f"unknown phase {_scalar(phase)}")


@contained
def check_wave(spec_dir: Path, *, expect: str, wave_index: int | None = None) -> GuardResult:
    """Current wave index, and whether more waves remain."""
    state, reason = _state_or_reason(spec_dir)
    if reason is not None:
        return GuardResult(ok=False, reason=reason)

    waves = state.get("schedule_waves", [])
    idx = non_negative_int(state, "current_wave_index", 0)
    if isinstance(idx, str):
        return GuardResult(ok=False, reason=f"wave check: {idx}")
    total = len(waves)

    if wave_index is not None and idx != wave_index:
        return GuardResult(
            ok=False,
            reason=(
                f"wave check: current_wave_index={_scalar(idx)} does not match "
                f"--wave-index {_scalar(wave_index)}"
            ),
        )

    if expect == "more":
        if idx < total - 1:
            return GuardResult(
                ok=True,
                message=(
                    f"wave check more — wave_index={_scalar(idx)} has more waves "
                    f"(total={_scalar(total)})"
                ),
            )
        return GuardResult(
            ok=False,
            reason=(
                f"wave check more: no more waves "
                f"(current={_scalar(idx)}, total={_scalar(total)})"
            ),
        )

    if expect == "last":
        if idx == total - 1:
            return GuardResult(
                ok=True,
                message=(
                    f"wave check last — wave_index={_scalar(idx)} is the last wave "
                    f"(total={_scalar(total)})"
                ),
            )
        return GuardResult(
            ok=False,
            reason=(
                f"wave check last: not the last wave "
                f"(current={_scalar(idx)}, total={_scalar(total)})"
            ),
        )

    return GuardResult(ok=False, reason=f"wave check: unknown --expect value {_scalar(expect)}")


_FILENAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


@contained
def check_artifact_status(spec_dir: Path, *, filename: str, expect: str) -> GuardResult:
    """A spec or plan artifact carries the expected `**Status:**` value.

    Reasons here are PREFIX-FREE, like every other guard's. `check-spec-status.py`
    prints its own `check-spec-status: ` prefix, and the engine composes its own —
    so embedding one in the reason produced `check-spec-status: check-spec-status:
    …`, which the pre-change goldens caught immediately. A CLI prefix inside the
    guard layer is exactly the CLI concern this layer is supposed to be free of.

    Check ORDER is load-bearing, and also golden-caught. Confinement runs BEFORE the
    single-component rule, so `--file ../outside.md` keeps its existing
    "must be within spec-dir" message rather than being re-diagnosed as a component
    problem. The component rule then catches the genuinely new case: a
    multi-component path that resolves *inside* `spec_dir`, which used to be
    accepted.

    Why single-component matters at all: `O_NOFOLLOW` rejects a symlink only at the
    FINAL component, so `sub/spec.md` with `sub` swapped after the prefix check would
    read outside the directory. And the charset alone admits every dot segment — the
    class `0cb5c213` fixed the day before this change — so dot-only names are
    rejected by segment equality rather than by narrowing the charset, which would
    also reject legitimate leading-dot filenames.
    """
    problem = _require_spec_dir(spec_dir)
    if problem is not None:
        return GuardResult(ok=False, reason=problem)

    # TWO paths, deliberately. Confinement needs the canonical one — resolve first,
    # then verify the prefix, which is the CWE-73 depth rather than the shallower
    # `..`-strip. But the READ must use the UNRESOLVED path, because `resolve()`
    # dereferences a symlink at the final component, so handing the resolved path to
    # the reader means `O_NOFOLLOW` never sees the link and a symlinked `spec.md`
    # sails through. Found by test, not by reading.
    unresolved = spec_dir / filename
    try:
        target = unresolved.resolve()
        inside = target.is_relative_to(spec_dir.resolve())
    except (OSError, RuntimeError) as exc:
        # RuntimeError: `Path.resolve()` on a symlink loop under the 3.11/3.12 floor.
        return GuardResult(ok=False, reason=f"cannot resolve {filename}: {exc}")
    if not inside:
        return GuardResult(ok=False, reason="--file must be within spec-dir")

    if not _FILENAME_RE.fullmatch(filename) or set(filename) == {"."}:
        return GuardResult(
            ok=False, reason=f"--file must be a single path component: {_scalar(filename)}"
        )

    if not target.exists():
        return GuardResult(ok=False, reason=f"{filename} not found at {target}")

    try:
        token = read_md_status(unresolved)
    except UnreadableArtifact as exc:
        return GuardResult(ok=False, reason=f"cannot read {target}: {exc}")

    if token is None:
        return GuardResult(ok=False, reason=f"no **Status:** line found in {target}")
    if token != expect:
        return GuardResult(
            ok=False, reason=f"{filename} Status is {_scalar(token)}, expected {_scalar(expect)}"
        )
    return GuardResult(
        ok=True,
        message=f"OK — Status: {expect} at {target}",
        data={"path": str(target), "status": token},
    )


# Last statement in the file, on purpose. A module truncated at a clean statement
# boundary — an interrupted `make build-self`, a half-finished checkout — loads
# WITHOUT raising and returns a handle missing everything after the cut. The
# loaders require this to be truthy and `set(__all__) <= set(dir(module))`, so a
# truncation anywhere above becomes a load failure rather than a live handle
# serving a half-configured guard. Detects accidental truncation only; tampering is
# the accepted write-access residual documented in the spec.
_MODULE_COMPLETE = True
