#!/usr/bin/env python3
"""Appends one entry to docs/knowledge/patterns.jsonl — the canonical writer.

The knowledge base is line-delimited JSON, and both `\\u2014` and a literal `—`
are valid JSON, so an author reaching for `json.dumps(entry)` (whose
`ensure_ascii` defaults to True) silently drifts the file's encoding while
passing every gate. This script is the one path that always writes raw UTF-8,
so the question never arises. `lint-knowledge.py` catches anything written by
another route.

Safety shape, in the order it happens — the order is the design:

  1. Resolve the repo root from git, with GIT_DIR / GIT_WORK_TREE /
     GIT_COMMON_DIR / GIT_CEILING_DIRECTORIES stripped from the child
     environment. Those variables relocate what `rev-parse` answers, and a
     confinement root an attacker can move is not a confinement root.
  2. Confine ``--file`` to ``<root>/docs/knowledge`` — expanduser, resolve,
     *then* verify the prefix. The order matters: checking before resolution
     accepts a symlink that escapes at its real location (CWE-73, the depth
     that a bare ``..``-strip misses). Same shape as the repo's blessed helper,
     ``tools/hooks/session-start.py:_safe_override_path``.
  3. Validate every field value *before* anything is opened. Entries are
     replayed verbatim into every future agent session by session-start, so
     this is a durable-instruction channel: no ``Cc`` controls (an ESC would
     be replayed as an ANSI sequence), no ``Cf`` formatting characters except
     ZWJ/ZWNJ (bidi overrides and the Unicode Tag block encode arbitrary text
     at zero visual width — invisible in a diff, live in every session), no
     U+0085/U+2028/U+2029 (they break ``str.splitlines()``, which is how both
     readers parse the file), no lone surrogates, and length caps.
  4. Take an exclusive lock for the rest of the run. Steps 5-7 are a
     read-modify-write; without the lock two concurrent appends both allocate
     the same id and the second replace discards the first entry, while both
     callers are told their learning was recorded.
  5. Pre-lint the existing file so a knowledge base that was *already* broken
     is reported as such, rather than the caller's entry taking the blame. A
     non-existent target is not a failure — it is an empty file to create.
     Linting precedes reading so a file that is not valid UTF-8 gets the
     designed message instead of a traceback.
  6. Allocate the next id as max(existing) + 1. Gaps are fine; the linter
     enforces uniqueness, not density.
  7. Write the full new content to a temp file beside the target, restore the
     target's mode onto it (``mkstemp`` creates 0600, and ``os.replace`` would
     otherwise narrow a committed world-readable file invisibly to git).
  8. Lint the *temp* file, and only ``os.replace`` it over the target on
     success. There is no window in which a rejected entry is live on disk, so
     there is nothing to roll back.

Usage:
    append-knowledge.py --kind gotcha --scope 'packs/core/**' \\
        --title '...' --body '...' --source 'PR#42' [--tier invariant]
        [--file <path under docs/knowledge>]
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

SCRIPT_DIR = Path(__file__).resolve().parent
LINTER = SCRIPT_DIR / "lint-knowledge.py"

# The confinement root, relative to the repo root.
KNOWLEDGE_DIR = ("docs", "knowledge")
DEFAULT_FILENAME = "patterns.jsonl"

# Field order as documented in docs/knowledge/README.md's field table.
FIELD_ORDER = ("id", "kind", "scope", "tier", "title", "body", "source")

TITLE_CAP = 120
BODY_CAP = 2000

# Environment that steers `git rev-parse --show-toplevel` away from the cwd.
_GIT_ENV_OVERRIDES = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_CEILING_DIRECTORIES",
)


def fail(reason: str, code: int = 1) -> int:
    print(f"append-knowledge: {reason}", file=sys.stderr)
    return code


class LockUnavailable(Exception):
    """Raised when the target's lock could not be acquired."""


def stale_name(lock_name: str, nonce: str) -> str:
    """The rename target used to break an abandoned lock.

    A named helper so a test can assert the shape without reaching into the
    lock loop: the lock's own token is `pid:nonce`, and `:` is reserved in
    Windows filenames, so using the token here would turn an abandoned lock
    permanently unbreakable on a platform this suite never runs on.
    """
    return f"{lock_name}.stale-{nonce}"


@contextlib.contextmanager
def exclusive(target: Path, timeout: float = 60.0, stale_after: float = 120.0):
    """Serialize the read-allocate-write window against the same target.

    Allocating `max(existing) + 1` and then replacing the whole file is a
    read-modify-write. Without this, two concurrent appends both read the same
    highest id, both write a full file, and the second replace silently
    discards the first entry — while *both* callers are told an id was
    recorded. That is worse than a crash: a learning is reported as captured
    and is not on disk.

    `O_CREAT | O_EXCL` rather than `fcntl.flock`, which Windows lacks; this
    repo's scripts are stdlib-only and cross-platform.

    `timeout` is a *wait* budget, not a hold budget: the critical section runs
    two lint subprocesses, so a holder legitimately takes about a second and a
    queue of six tips a 10s budget over. 60s tolerates realistic contention
    while still being bounded — the point is that it reports rather than
    spinning, not that it gives up quickly.

    Two rules make the takeover safe, and a first version of this got both
    wrong — it broke a lock once *the waiter* had waited `timeout`, and then
    unlinked whatever lock existed on the way out. Three processes ended up in
    the critical section at once, and the displaced holder's release deleted
    its successor's lock, cascading for the rest of the burst:

      - **Break on the lock's age, never on our own patience.** A holder that
        is merely slow still holds it. Only a lock older than `stale_after` —
        far longer than this critical section's two subprocess spawns — is
        treated as abandoned, and the acquire is retried rather than assumed
        to have won the unlink race.
      - **Release only what we still own.** The lock carries a unique token;
        if a stale-breaker took it over, its content no longer matches and we
        leave it alone.
    """
    lock = target.with_name(target.name + ".lock")
    nonce = uuid.uuid4().hex
    # `pid:nonce` identifies the holder in the lock *contents*; the rename
    # target uses the bare nonce, because `:` is reserved in Windows
    # filenames and a rejected rename turns an abandoned lock permanent.
    token = f"{os.getpid()}:{nonce}"
    deadline = time.monotonic() + timeout
    fd = None
    while fd is None:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            # Every path through here must reach the deadline check and the
            # sleep. A `continue` that skips them turns "bounded wait" into a
            # busy-spin — reachable with a dangling symlink at the lock path
            # (stat raises) or a directory there (unlink raises).
            try:
                age = time.time() - lock.stat().st_mtime
            except OSError:
                age = None  # vanished, or not stat-able
            else:
                # Stale in either direction, but only *grossly* so. A lock
                # whose mtime is far in the future is a bogus timestamp (clock
                # skew, NFS, a lock committed and checked out) and must not pin
                # the lock forever; a lock a few milliseconds "in the future"
                # is just timer granularity against a live holder, and treating
                # that as abandoned breaks the mutual exclusion outright —
                # it did, reintroducing the lost update this manager exists to
                # prevent.
                if age is not None and not -stale_after <= age <= stale_after:
                    # Break by rename, not unlink. Unlinking the path directly
                    # lets a second breaker delete a lock the *winner* has since
                    # created: B stats an abandoned lock, is descheduled, A
                    # breaks it and acquires, then B's unlink removes A's live
                    # lock and a third process enters. `os.replace` is atomic,
                    # so exactly one breaker moves the file it saw.
                    stale = lock.with_name(stale_name(lock.name, nonce))
                    try:
                        lock.replace(stale)
                    except FileNotFoundError:
                        pass  # another waiter won the break — just retry
                    except OSError as exc:
                        raise LockUnavailable(
                            f"{lock} looks abandoned ({age:.0f}s old) but cannot "
                            f"be moved aside: {exc}"
                        ) from None
                    else:
                        # The rename is what frees the path and what decides the
                        # race; clearing the renamed file is tidiness. It is
                        # gitignored, so failing here is not worth refusing over.
                        with contextlib.suppress(OSError):
                            if stale.is_dir():
                                stale.rmdir()
                            else:
                                stale.unlink()
            if time.monotonic() >= deadline:
                held = "could not be inspected" if age is None else f"held for {age:.0f}s"
                raise LockUnavailable(
                    f"{lock} ({held}) did not free within {timeout:.0f}s; "
                    "if no other append is running, remove it"
                ) from None
            time.sleep(0.05)
        except OSError as exc:
            raise LockUnavailable(f"cannot create {lock}: {exc}") from exc
    try:
        try:
            os.write(fd, token.encode())
        finally:
            os.close(fd)
    except BaseException:
        # An orphaned lock blocks every later append for `stale_after`.
        with contextlib.suppress(OSError):
            lock.unlink()
        raise
    try:
        yield
    finally:
        try:
            if lock.read_text(encoding="utf-8") == token:
                lock.unlink()
        except (OSError, ValueError):
            # ValueError catches UnicodeDecodeError, which is not an OSError: a
            # lock overwritten with binary made release raise *after*
            # `tmp.replace(target)` had installed the entry, so the caller saw a
            # traceback and never saw the id — the tool reporting wrongly about
            # what reached disk, which is the failure this lock exists to stop.
            pass


_linter_module = None


def _linter():
    """Cached handle on lint-knowledge.py — the single source for what is
    invisible, what kinds are legal, and how an entry is validated."""
    global _linter_module
    if _linter_module is None:
        _linter_module = _load_linter()
    return _linter_module


def _load_linter():
    """Import lint-knowledge.py for its enforced sets — one source of truth."""
    spec = importlib.util.spec_from_file_location("_lint_knowledge", str(LINTER))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {LINTER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def repo_root() -> Path | None:
    """The git top level for the cwd, immune to GIT_* relocation."""
    env = {k: v for k, v in os.environ.items() if k not in _GIT_ENV_OVERRIDES}
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False, env=env,
        )
    except (OSError, FileNotFoundError):
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    return Path(proc.stdout.strip())


def confine(raw: str, base: Path) -> Path | None:
    """Resolve *raw* and return it only if it stays under *base*.

    The containment check runs after ``resolve()``, so a symlink is validated
    at its real location rather than its lexical form.
    """
    try:
        resolved = Path(raw).expanduser().resolve()
        base_resolved = base.resolve()
    except (OSError, RuntimeError, ValueError):
        return None
    if not resolved.is_relative_to(base_resolved):
        return None
    return resolved


def validate_value(field: str, value: str) -> str | None:
    """Return an error string, or None when *value* is safe to write.

    The per-character rules live in `lint-knowledge.py` and are applied here to
    the same decoded value the gate will see, so the writer and the gate cannot
    disagree about what is refused. Only the field-shaped rules — emptiness and
    the length caps — are the writer's own.
    """
    lint = _linter()
    problems = lint.field_problems(value)
    if problems:
        return (f"{field} contains a {problems[0]}; entries are replayed "
                "verbatim into every future session, so these are refused")
    cap = {"title": TITLE_CAP, "body": BODY_CAP}.get(field)
    if cap is not None and len(value) > cap:
        return f"{field} is {len(value)} characters; the limit is {cap}"
    if not value.strip():
        return f"{field} must be a non-empty string"
    return None


def next_id(text: str) -> str:
    """max(existing) + 1, zero-padded. Gaps are fine — uniqueness is enforced."""
    highest = 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry_id = json.loads(line).get("id", "")
        except (json.JSONDecodeError, AttributeError):
            continue
        if isinstance(entry_id, str) and entry_id.startswith("K-"):
            try:
                highest = max(highest, int(entry_id[2:]))
            except ValueError:
                continue
    return f"K-{highest + 1:04d}"


def run_linter(target: Path) -> subprocess.CompletedProcess:
    """Lint *target* out of process.

    A subprocess, not an import: lint-knowledge.py chdirs to the repo root
    inside `main()`, so calling it in-process would relocate this process's
    relative paths. Importing the module is safe and is what `_load_linter()`
    does for the shared predicate and the enum sets. The
    absolute path is passed as the sole argument — no ``--`` separator, which
    that script (which has no argparse) would take as the target path.
    """
    return subprocess.run(
        [sys.executable, str(LINTER), str(target)],
        capture_output=True, text=True, encoding="utf-8", check=False,
    )


def main(argv: list[str] | None = None) -> int:
    linter = _load_linter()
    ap = argparse.ArgumentParser(
        prog="append-knowledge.py",
        description="Append one entry to the knowledge base, in raw UTF-8.",
    )
    ap.add_argument("--kind", required=True, choices=sorted(linter.ALLOWED_KINDS))
    ap.add_argument("--scope", required=True,
                    help="comma-separated path glob(s), e.g. 'packs/core/**'")
    ap.add_argument("--title", required=True, help=f"one line, <= {TITLE_CAP} chars")
    ap.add_argument("--body", required=True, help=f"the lesson, <= {BODY_CAP} chars")
    ap.add_argument("--source", required=True, help="provenance, e.g. PR#42")
    ap.add_argument("--tier", choices=sorted(linter.ALLOWED_TIERS), default=None)
    ap.add_argument("--file", default=None,
                    help="target path; must resolve under <repo>/docs/knowledge")
    args = ap.parse_args(argv)

    root = repo_root()
    if root is None:
        return fail(
            "not inside a git repository (or git is unavailable) — the "
            "confinement root cannot be established, so no write is attempted"
        )
    base = root.joinpath(*KNOWLEDGE_DIR)

    raw_target = args.file or str(base / DEFAULT_FILENAME)
    target = confine(raw_target, base)
    if target is None:
        return fail(
            f"refusing {raw_target!r}: the target must resolve inside {base} "
            "(checked after symlink resolution)"
        )

    if target.exists() and not target.is_file():
        return fail(f"{target} exists but is not a regular file")
    if not target.parent.is_dir():
        return fail(f"{target.parent} does not exist — create it first")

    fields = {"kind": args.kind, "scope": args.scope, "title": args.title,
              "body": args.body, "source": args.source}
    if args.tier:
        fields["tier"] = args.tier
    for field, value in fields.items():
        problem = validate_value(field, value)
        if problem is not None:
            return fail(problem)

    # Everything from here to the replace is one critical section: the id is
    # derived from the file's current contents, so a concurrent append between
    # the read and the replace would silently drop one entry.
    try:
        with exclusive(target):
            # A file that does not exist yet is an empty knowledge base, not a
            # broken one — pre-linting it would report "does not exist" and make a
            # fresh base uncreatable. Lint before reading, so a file that is not
            # even valid UTF-8 produces the designed message rather than a
            # traceback out of read_text.
            if target.is_file():
                pre = run_linter(target)
                if pre.returncode != 0:
                    return fail(
                        f"{target} already fails lint; fix it first — this append "
                        f"was not attempted.\n{pre.stdout}{pre.stderr}"
                    )
                try:
                    existing = target.read_text(encoding="utf-8")
                except UnicodeDecodeError as exc:
                    return fail(f"{target} is not valid UTF-8 ({exc.reason})")
            else:
                existing = ""

            entry = {"id": next_id(existing), **fields}
            ordered = {k: entry[k] for k in FIELD_ORDER if k in entry}
            line = json.dumps(ordered, ensure_ascii=False, allow_nan=False)

            if existing and not existing.endswith("\n"):
                existing += "\n"
            candidate = existing + line + "\n"

            fd, tmp_name = tempfile.mkstemp(
                prefix=".append-", suffix=".jsonl.tmp", dir=str(target.parent)
            )
            tmp = Path(tmp_name)
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(candidate)
                post = run_linter(tmp)
                if post.returncode != 0:
                    return fail(
                        f"the new entry does not lint; {target} is unchanged.\n"
                        f"{post.stdout}{post.stderr}"
                    )
                # mkstemp creates 0600, and os.replace carries that mode onto the
                # target — silently narrowing a committed, world-readable file.
                # Git tracks only the exec bit, so the change is invisible in a
                # diff and in CI.
                if target.is_file():
                    # perms only — never carry setuid/setgid/sticky onto a data file
                    tmp.chmod(target.stat().st_mode & 0o0777)
                else:
                    umask = os.umask(0)
                    os.umask(umask)
                    tmp.chmod(0o666 & ~umask)
                tmp.replace(target)
            finally:
                if tmp.exists():
                    tmp.unlink()
    except LockUnavailable as exc:
        return fail(str(exc))

    print(entry["id"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
