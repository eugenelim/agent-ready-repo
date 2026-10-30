"""_loop_guards — the work-loop's shared read-only guard helpers.

What lives here: the bounded, symlink-safe readers; the canonical contract hash of
`spec.md` and `plan.md`; the status-token parse; the artifact-status guard that
`lint-spec-status.py` and `lint-traceability.py` call; and the plan grammar the
supervisor's projector shares (the task-section walk and the `Depends on:` parse).

Contract — every public guard in this module:

  * takes explicit typed arguments and returns a `GuardResult`;
  * prints NOTHING to stdout or stderr, and carries no CLI prefix in `reason`
    or `message` — each adapter adds its own, so the layer cannot double it;
  * parses no arguments, reads no `sys.argv`, never calls `sys.exit`;
  * mutates no state file and creates no file anywhere;
  * never spawns a process and never opens a socket.

`spec_dir` precondition: callers pass an absolute, already-resolved,
already-confined `Path`. Confinement stays with the caller that owns it. What a
callee can actually check, it does: that `spec_dir` exists and is a directory.

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
from collections import namedtuple
from collections.abc import Container
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

__all__ = [
    # result type
    "GuardResult",
    # bounded, symlink-safe readers
    "ManagedContentError",
    "read_managed_json",
    "read_managed_text",
    # canonical contract hashing
    "canonical_contract",
    "sha256_canonical_contract",
    # status parsing + legality
    "UnreadableArtifact",
    "read_md_status",
    "contained",
    "contained_reason",
    "DEFAULTS",
    "check_artifact_status",
]

SCRIPT_DIR = Path(__file__).resolve().parent
# Each standalone CLI retains a local declaration so its schema validation gains no
# new load dependency.


# ── result type ───────────────────────────────────────────────────────────


# Marker prefix distinguishing a crash-refusal from a policy refusal. An operator
# reading `internal-error:` knows the guard could not decide, rather than that it
# decided against them.
INTERNAL_ERROR = "internal-error"

# Bound on ONE interpolated external scalar, not on the whole reason. Several
# authored reasons may be deliberately long, and capping the assembled string
# clipped it mid-sentence, losing the
# steps an operator needs. So the bound sits where untrusted length actually
# enters: `_scalar()`, at each interpolation of state-file or argv data.
_MAX_SCALAR_CHARS = 120

# Backstop, and load-bearing rather than theoretical: the audit that introduced
# `_scalar` MISSED a success message, where a 100 KB value
# reached stdout at exactly this cap. Treat it as what holds when a site is
# missed, not as evidence that none is. Set well above the longest
# authored reason so it cannot truncate legitimate text.
_MAX_REASON_CHARS = 4000


class ManagedContentError(ValueError):
    """The file was read safely, but its BYTES are unusable.

    Distinct from the structural failures sharing the same `ValueError` vocabulary
    (unopenable, non-regular, replaced mid-read), and the distinction is load-bearing
    rather than cosmetic: `the phase engine's _recover_pending` DELETES `events.pending` — a
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
    argument. A 100 KB `run_id` in a state file otherwise becomes a 100 KB
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
# in a state file otherwise emits a real screen-clear and colour change into that
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
    matters because the pre-existing convention in the phase engine was "None on
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
        # filename), and a 100 KB `run_id` in a state file produced a 100,055-character
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
    a contained call; `the cohort writer's with_state_lock`'s own handler remains its only
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


# ── DEFAULTS ────────────────────────────────────────────────────────────

# The two retry caps a guard falls back to when the caller supplies none. They were
# read from a bundled template; the template is gone, so the values live here.
DEFAULTS = MappingProxyType({"max_implementation_retries": 5, "max_review_retries": 5})


# ── state paths + managed JSON read ─────────────────────────────────────


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

# Hashed into every approved digest, so its bytes never change.
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
    # section; a checkbox under `## Agent Rules` (`## Boundaries` before the
    # rename) is a `Never do` item, which is
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
    return _sha256_canonical_text(
        read_managed_text(path, path.name),
        artifact_name=path.name,
    )


def _sha256_canonical_text(text: str, *, artifact_name: str) -> str:
    """Hash already-read contract text without reopening its artifact."""
    try:
        canonical = canonical_contract(
            text,
            ac_section_only=(artifact_name != "plan.md"),
        )
    except ImportError as exc:
        raise ValueError(
            f"{artifact_name}: canonical status parser unavailable: {exc}"
        ) from exc
    return _sha256_bytes(canonical.encode("utf-8"))


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


# ── artifact status guard ──────────────────────────────────────────────────
#
# Reads the file it needs at call time. Reasons carry no CLI prefix: each caller
# adds its own.


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


_FILENAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


@contained
def check_artifact_status(spec_dir: Path, *, filename: str, expect: str) -> GuardResult:
    """A spec or plan artifact carries the expected `**Status:**` value.

    Reasons here are PREFIX-FREE, like every other guard's. the status checker
    prints its own `status-check: ` prefix, and the engine composes its own —
    so embedding one in the reason produced `status-check: status-check:
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


# ── plan grammar ──────────────────────────────────────────────────────────
# The loop engine and the execution supervisor's projector share the task-section
# walk and the `Depends on:` value parse. Only the engine uses
# `section_depends_field`; the projector finds that line with its own field reader.
# These names sit above the completeness marker, so the loaders that check the
# marker refuse a file truncated before them, and they stay out of `__all__`,
# which pins the guard surface.

# Accepts both '## T<n>' (level-2) and '### T<n>' (level-3) headings for
# backward compatibility with existing plans that predate the Phase-1 spec.
TASK_HEADING_RE = re.compile(r"^#{2,3}\s+(T\d+[a-z]?)\b", re.MULTILINE)
DEPENDS_LINE_RE = re.compile(r"^\*\*Depends on:\*\*\s*(.+)$", re.MULTILINE)
_RANGE_RE = re.compile(r"(T\d+)\s*-\s*(T\d+)")
TASK_ID_RE = re.compile(r"T\d+[a-z]?")
_CROSS_MARKER_RE = re.compile(r"spec:([A-Za-z0-9._-]+)/(T\d+[a-z]?)")
_CROSS_LEGACY_RE = re.compile(r"`(?!T\d+[a-z]?`)([A-Za-z0-9._-]+)`\s*(T\d+[a-z]?)")


def local_dep_ids(field: str) -> set[str]:
    """Local task IDs a `Depends on:` field names ahead of its first `(`.

    Trailing parenthetical prose is authored commentary, not declaration, so the
    field is truncated there. An ID written after that `(` is therefore not a
    declared dependency for any caller: it is neither scheduled as an edge nor
    reported as unknown. That is deliberate — widening it would change what
    counts as a dependency for every caller of this helper, not just the
    unknown-dependency check.
    """
    head = field.split("(")[0]
    cleaned = _CROSS_MARKER_RE.sub("", head)
    cleaned = _CROSS_LEGACY_RE.sub("", cleaned)
    if not cleaned.strip() or re.fullmatch(r"\s*none\s*", cleaned, re.IGNORECASE):
        return set()
    ids: set[str] = set()
    for lo, hi in _RANGE_RE.findall(cleaned):
        ids.update(f"T{i}" for i in range(int(lo[1:]), int(hi[1:]) + 1))
    ids.update(TASK_ID_RE.findall(cleaned))
    return ids


def parse_depends_on(
    field: str, local_task_ids: Container[str]
) -> tuple[set[str], list[tuple[str, str]]]:
    """Parse a 'Depends on:' field value into local task IDs and cross-spec markers."""
    head = field.split("(")[0]
    cross = _CROSS_MARKER_RE.findall(head) + _CROSS_LEGACY_RE.findall(head)
    return {t for t in local_dep_ids(field) if t in local_task_ids}, cross


# One plan task's boundaries, as offsets into the plan text: `start` opens the
# heading, `body_start` is just past it, and `end` is where the next task heading
# begins, or the end of the text for the final task.
TaskSection = namedtuple("TaskSection", ["task_id", "start", "body_start", "end"])


def walk_task_sections(text: str) -> list[TaskSection]:
    """Sole owner of the plan's task-section boundaries.

    Every caller that needs to know which task owns a line resolves it here.
    That is the point of the function rather than a convenience: the
    unknown-dependency refusal in `detect_unknown_deps` must attribute a
    `Depends on:` line to exactly the task `parse_plan` attributes it to. Were
    the two to walk the boundaries separately and ever disagree, `schedule`
    would refuse a plan it would otherwise have scheduled, or accept one whose
    edges it then reads differently. Sharing the walk makes that agreement
    structural instead of a coincidence maintained by hand.
    """
    matches = list(TASK_HEADING_RE.finditer(text))
    return [
        TaskSection(
            task_id=m.group(1),
            start=m.start(),
            body_start=m.end(),
            end=matches[i + 1].start() if i + 1 < len(matches) else len(text),
        )
        for i, m in enumerate(matches)
    ]


def section_depends_field(text: str, section: TaskSection) -> str | None:
    """The raw `Depends on:` field value a task declares, or None.

    Single-homed for the same reason as the walk above: the refusal and the
    graph must read the same field text for the same task.
    """
    dm = DEPENDS_LINE_RE.search(text[section.body_start:section.end])
    return dm.group(1) if dm else None


# Last statement in the file, on purpose. A module truncated at a clean statement
# boundary — an interrupted `make build-self`, a half-finished checkout — loads
# WITHOUT raising and returns a handle missing everything after the cut. The
# loaders require this to be truthy and `set(__all__) <= set(dir(module))`, so a
# truncation anywhere above becomes a load failure rather than a live handle
# serving a half-configured guard. Detects accidental truncation only; tampering is
# the accepted write-access residual documented in the spec.
_MODULE_COMPLETE = True
