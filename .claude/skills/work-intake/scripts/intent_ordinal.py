#!/usr/bin/env python3
"""Allocate a typed ordinal for a repository intent filename.

Usage: python3 intent_ordinal.py --dir <repo-relative dir> --token <TOKEN>
       python3 intent_ordinal.py --check <repo-relative dir>

Allocation mode prints ``<TOKEN>-NNNN`` on stdout and exits 0, or exits 1 with
one fixed diagnostic token on stderr. Exit 1 never means "do not admit": the
caller writes the intent at the unprefixed path and records the cause. Check
mode reports records sharing a type and an ordinal in one directory, and exits
1 rather than reporting clean for a directory it could not fully read.

`max + 1` is computed per type over the directory unioned with the records
visible on ``origin``. Allocation unions; check does not, because a remote-only
collision is already committed and needs a reissue rather than a refusal.

The allocator never returns a plausible answer. Where the untyped ADR/RFC
helper falls back to ``0001``, this one returns nothing: for a malformed name
inside the typed namespace, for a scan it could not complete, for a remote view
it could not read, and for a bound it would have to exceed.
"""
import argparse
import collections
import contextlib
import importlib.util
import os
import re
import stat
import subprocess
import sys
import time
from pathlib import Path

# ── The closed level-to-token table ───────────────────────────────────────────
# Transcribed from the owning product intent's Boundary, which is where the
# decision lives. Changing a token is a change to that artifact, not to this
# file; a repository-level test asserts this mapping still equals it.
LEVEL_TOKENS = {
    "product-vision": "VISION",
    "product-strategy": "STRAT",
    "capability": "CAP",
    "feature": "FEAT",
}
NAMESPACE_TOKENS = tuple(sorted(set(LEVEL_TOKENS.values())))

# Marker vocabulary. A caller records one of these tokens; it never composes a
# marker from input, because an intent is a durable file a later agent reads.
REFUSAL_CAUSES = (
    "unparsed-name",
    "incomplete-scan",
    "remote-unavailable",
    "bound-exceeded",
)

# ── Bounds, each with its origin ──────────────────────────────────────────────
GIT_TIMEOUT_SECONDS = 5          # inherited from the ADR/RFC helper
TOTAL_TIMEOUT_SECONDS = 10       # 170x the measured end-to-end cost
MAX_ENTRIES = 65_536             # ~295x this repository's largest directory
MAX_GIT_RESULT_BYTES = 8 * 1024 * 1024   # ~11x a whole-repository listing
# CPython refuses int() above 4300 digits, so an unbounded digit run would
# classify a name as valid and then raise instead of refusing. 12 is far above
# any ordinal this repository will reach.
MAX_ORDINAL_DIGITS = 12
DIAGNOSTIC_BYTE_LIMIT = 200

# The child's environment is built from an allowlist, not inherited and pruned.
# A denylist of `GIT_*` kept growing — the redirect set, then `GIT_CONFIG*`,
# then `GIT_TRACE*` which makes a read-only probe write files, then
# `GIT_CEILING_DIRECTORIES` which can fence discovery below the real root so
# `rev-parse` reports no repository. Each was a real hole and the next one is
# whichever variable nobody has thought of, so nothing inherited reaches git
# except the few names it needs to run at all.
GIT_ENVIRONMENT_ALLOWLIST = ("PATH", "HOME", "SystemRoot", "TMPDIR", "TEMP")
# Retained as the documented set the allowlist supersedes, so a reader who
# comes looking for the scrub finds why there is none.
GIT_REDIRECT_VARIABLES = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
)
_ORIGIN_REF_PREFIX = "refs/remotes/origin/"
# Git's *false* forms, which is the closed set. Everything else it reads as
# true — `2` and `-1` included — so an allowlist of true forms is the wrong
# shape: it fails open on every value nobody thought of.
_GIT_FALSE_VALUES = frozenset({"", "0", "no", "false", "off"})
# Git's own words for "there is no repository here", pinned to LC_ALL=C in the
# child. Exit 128 alone is not this statement: git uses it for every fatal
# error, so accepting the status would let an unrelated failure read as absence.
_NO_REPOSITORY_MESSAGE = "fatal: not a git repository"

_LEVEL_RE = re.compile(r"^[a-z][a-z-]{0,63}$")
_TOKEN_ALTERNATION = "|".join(NAMESPACE_TOKENS)
# Two patterns, not three: the introducer decides in-or-out of the namespace and
# the owner's shape decides valid-or-malformed inside it. Deriving "malformed"
# as "introducer and not shape" is what makes the partition exhaustive.
_INTRODUCER = re.compile(rf"^(?:{_TOKEN_ALTERNATION})-")
_VALID = re.compile(
    rf"^({_TOKEN_ALTERNATION})-(\d{{4,{MAX_ORDINAL_DIGITS}}})-[^/]+\.md$"
)

RemoteView = collections.namedtuple("RemoteView", "names state")
# `code` is git's exit status, or None when it could not be run to completion —
# launch failure, timeout, or a breached bound. The distinction matters: exit
# 128 from `rev-parse` is git positively saying "no repository", while None says
# nothing about the repository at all.
_GitResult = collections.namedtuple(
    "_GitResult", "output code diagnostic", defaults=("",)
)
_NOT_A_REPOSITORY = 128


class _ScanRefused(Exception):
    """Raised internally when no ordinal may be returned."""

    def __init__(self, cause: str) -> None:
        super().__init__(cause)
        self.cause = cause


# ── Shared confinement helper ─────────────────────────────────────────────────
# Loaded by path so scripts/ is never placed on sys.path: skills are
# independent and several may ship a module of the same name.
def _load_file_safety() -> object:
    previous = sys.dont_write_bytecode
    try:
        # Bytecode is a write, and this allocator promises to perform none.
        sys.dont_write_bytecode = True
        path = Path(__file__).resolve().parent / "file_safety.py"
        spec = importlib.util.spec_from_file_location(
            "core_work_intake_file_safety", path
        )
        if spec is None or spec.loader is None:
            raise _ScanRefused("incomplete-scan")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except _ScanRefused:
        raise
    except BaseException as error:
        raise _ScanRefused("incomplete-scan") from error
    finally:
        sys.dont_write_bytecode = previous


def classify(name: str) -> str:
    """Return ``valid``, ``malformed`` or ``outside`` for one entry name."""
    if not _INTRODUCER.match(name):
        return "outside"
    return "valid" if _VALID.match(name) else "malformed"


def token_for_level(level: str | None) -> str | None:
    """Return the token for *level*, or ``None`` when the table maps none.

    Exact match on a bare value. ``Level`` is an open field, so a decorated or
    differently-cased variant is simply unmapped, which is a normal outcome.
    """
    if not isinstance(level, str) or not _LEVEL_RE.match(level):
        return None
    return LEVEL_TOKENS.get(level)


def _git(
    directory: Path, arguments: list[str], deadline: float, *, capture_stderr: bool = False
) -> _GitResult:
    """Run one git command, reading its output incrementally under a bound.

    ``Popen`` rather than ``run``: the byte bound has to hold while reading,
    and ``run`` buffers the whole result before anything can check it. The
    deadline is enforced by polling the pipe rather than by blocking on a read,
    because an adopter-controlled config include can stall git with no output
    and a blocked ``read`` lets no deadline check run at all.
    """
    environment = {
        name: os.environ[name]
        for name in GIT_ENVIRONMENT_ALLOWLIST
        if name in os.environ
    }
    # An argument vector free of `fetch` does not prove no egress: ls-tree on a
    # partial clone resolves a missing object through the promisor remote. This
    # fails that closed on a git that honours it; the configuration check in
    # `remote_view` covers a git too old to.
    environment["GIT_NO_LAZY_FETCH"] = "1"
    environment["GIT_TERMINAL_PROMPT"] = "0"
    # Pins git's diagnostic wording, which the repository probe below matches
    # on. Without it the message is locale-dependent and the match is luck.
    environment["LC_ALL"] = "C"
    # A deadline already past is a refusal, not a zero-length wait.
    if min(GIT_TIMEOUT_SECONDS, deadline - time.monotonic()) <= 0:
        raise _ScanRefused("bound-exceeded")
    command_deadline = min(deadline, time.monotonic() + GIT_TIMEOUT_SECONDS)
    try:
        child = subprocess.Popen(
            ["git", "--literal-pathspecs", *arguments],
            cwd=os.fspath(directory),
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if capture_stderr else subprocess.DEVNULL,
            shell=False,
        )
    except (OSError, ValueError):
        return _GitResult(None, None)
    if child is None or getattr(child, "stdout", None) is None:
        return _GitResult(None, None)

    chunks: list[bytes] = []
    total = 0
    descriptor = child.stdout.fileno()
    try:
        # Non-blocking, then polled: one path on every platform, so the byte
        # bound is enforced while reading rather than after a buffered whole.
        # `communicate` was the earlier fallback and had to go — it allocates
        # the full result before any ceiling can apply to it.
        os.set_blocking(descriptor, False)
        while True:
            if time.monotonic() >= command_deadline:
                raise _ScanRefused("bound-exceeded")
            try:
                chunk = os.read(descriptor, 65_536)
            except BlockingIOError:
                time.sleep(0.005)
                continue
            except InterruptedError:
                continue
            except OSError:
                # Not EOF: accepting a truncated result here would hide a
                # promisor key or drop the highest remote ordinal while git
                # still exited zero.
                return _GitResult(None, None)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_GIT_RESULT_BYTES:
                raise _ScanRefused("bound-exceeded")
            chunks.append(chunk)
        child.wait(timeout=max(0.001, command_deadline - time.monotonic()))
    except _ScanRefused:
        raise
    except subprocess.TimeoutExpired:
        return _GitResult(None, None)
    except (OSError, ValueError):
        return _GitResult(None, None)
    finally:
        # Never leave a running or unreaped child behind, whichever way we left.
        if child.poll() is None:
            child.kill()
            with contextlib.suppress(subprocess.TimeoutExpired, OSError, ValueError):
                child.wait(timeout=1)
    diagnostic = ""
    if capture_stderr and child.stderr is not None:
        # Bounded and read only after the child has exited, so a large stderr
        # cannot deadlock against the stdout pipe. Used for one comparison and
        # never reflected anywhere.
        with contextlib.suppress(OSError, ValueError):
            diagnostic = child.stderr.read(4096).decode("utf-8", "replace")
    return _GitResult(
        b"".join(chunks).decode("utf-8", "surrogateescape"),
        child.returncode,
        diagnostic,
    )


def git_config_values(
    directory: Path, deadline: float | None = None
) -> dict[str, str] | None:
    """Return git's effective configuration, or ``None`` when it is unreadable.

    ``--list -z`` rather than ``--list``: the newline-delimited form cannot be
    parsed unambiguously, because a configuration *value* may itself contain a
    newline and would then forge a later key. An adopter controls that file, so
    the ambiguous form is an injection into the promisor check below. Each NUL
    record is ``key\nvalue``, or a bare key for a valueless one.
    """
    result = _git(
        directory, ["config", "--list", "-z"], deadline if deadline is not None else _deadline()
    )
    if result.output is None or result.code != 0:
        return None
    values: dict[str, str] = {}
    for record in result.output.split("\0"):
        if not record:
            continue
        key, separator, value = record.partition("\n")
        # A valueless key is git's own spelling of true — `[remote "origin"]`
        # with a bare `promisor` line reads as `true` to `--type=bool`. Mapping
        # it to the empty string would make it falsy here and bypass the check.
        values[key.strip()] = value if separator else "true"
    return values


def _is_promisor(config: dict[str, str]) -> bool:
    """Whether any of git's promisor designations is present.

    Two keys designate one, either sufficient on its own: a modern clone
    records only the per-remote key while the repository-level key alone is
    equally effective. A ``false`` value means that remote is not designated,
    never that transport is suppressed.
    """
    # Case-insensitively: git's own `config --list` lowercases a key, while the
    # documented spelling is `extensions.partialClone`, and a caller may hand
    # over either. Matching one spelling would leave the other designation open.
    folded = {key.lower(): value for key, value in config.items()}
    if folded.get("extensions.partialclone"):
        return True
    return any(
        key.startswith("remote.") and key.endswith(".promisor")
        and value.strip().lower() not in _GIT_FALSE_VALUES
        for key, value in folded.items()
    )


def _repository_root(directory: Path, deadline: float) -> tuple[str | None, str]:
    """Return ``(root, state)`` where state is ``ok``, ``absent`` or ``failed``.

    Only exit 128 means git positively determined there is no repository here.
    A launch failure, a timeout, an unsafe-ownership refusal or any other
    non-zero status says nothing about the repository, so it refuses: treating
    it as "no repository" is how a local-only ordinal collides with an existing
    record on ``origin``.
    """
    result = _git(
        directory, ["rev-parse", "--show-toplevel"], deadline, capture_stderr=True
    )
    if result.code == 0 and result.output and result.output.strip():
        return result.output.rstrip("\n"), "ok"
    if result.code == _NOT_A_REPOSITORY and result.diagnostic.startswith(
        _NO_REPOSITORY_MESSAGE
    ):
        # Git's own statement that there is nothing here, not merely a fatal
        # status. Every other fatal outcome says nothing about the repository.
        return None, "absent"
    return None, "failed"


def _deadline() -> float:
    """Monotonic wall-clock deadline for the whole invocation."""
    return time.monotonic() + TOTAL_TIMEOUT_SECONDS


def remote_view(directory: Path, deadline: float | None = None) -> RemoteView:
    """Return the record names visible on ``origin`` and how complete they are.

    Three states, because "nothing there" and "could not look" are different
    instructions to a caller. ``absent`` means there is nothing to consult and
    the working tree is the whole available view. ``failed`` means there is
    something to consult and no way to read it, which refuses.
    """
    if deadline is None:
        deadline = _deadline()
    # Before any object-reading command: a promisor designation means a read
    # could reach the network, and this check is observable independently of
    # GIT_NO_LAZY_FETCH precisely because it runs first.
    config = git_config_values(directory, deadline)
    if config is None or _is_promisor(config):
        # Unreadable configuration is not "no promisor": it is no answer, and
        # the next command would be the object read this check exists to precede.
        return RemoteView(frozenset(), "failed")

    # `absent` is a positive finding — git ran and reported nothing to consult.
    # A command that failed reports nothing *about* the view, so it refuses.
    toplevel, state = _repository_root(directory, deadline)
    if state != "ok":
        return RemoteView(frozenset(), state)
    remotes = _git(directory, ["remote"], deadline)
    if remotes.output is None or remotes.code != 0:
        return RemoteView(frozenset(), "failed")
    if "origin" not in remotes.output.split():
        return RemoteView(frozenset(), "absent")

    ref_result = _git(
        directory, ["symbolic-ref", "--quiet", _ORIGIN_REF_PREFIX + "HEAD"], deadline
    )
    ref = ref_result.output
    if ref_result.code != 0 or not ref or not ref.strip().startswith(_ORIGIN_REF_PREFIX):
        # origin exists and its default branch cannot be established, so the
        # view is incomplete in an unknown way rather than empty.
        return RemoteView(frozenset(), "failed")

    root = Path(toplevel)
    try:
        relative = directory.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        # The root would not resolve, or this directory is not under it. Either
        # way the pathspec cannot be built, which is no answer rather than none.
        return RemoteView(frozenset(), "failed")
    pathspec = f"{relative.as_posix()}/" if relative.parts else "."
    # -z: git renders a non-ASCII name in quoted C-string form otherwise, which
    # starts with a quote and so matches no introducer — the record would be
    # invisible and its ordinal handed out again. The mode is kept (no
    # --name-only) so a non-blob entry inside the namespace can fail closed.
    listing_result = _git(root, ["ls-tree", "-z", ref.strip(), "--", pathspec], deadline)
    if listing_result.code != 0 or listing_result.output is None:
        return RemoteView(frozenset(), "failed")
    listing = listing_result.output

    names: set[str] = set()
    consumed = 0
    for record in listing.split("\0"):
        if not record:
            continue
        # Counted per record consumed, not per name kept: a tree of names all
        # outside the namespace still costs the work the bound exists to cap.
        consumed += 1
        if consumed > MAX_ENTRIES:
            return RemoteView(frozenset(), "failed")
        meta, _, path = record.partition("\t")
        if not path:
            return RemoteView(frozenset(), "failed")
        # Git emits `/` on every platform, and a backslash inside a name is
        # filename data. `Path(path).name` would split on it under Windows and
        # read the wrong ordinal.
        name = path.rsplit("/", 1)[-1]
        if classify(name) == "outside":
            continue
        fields = meta.split()
        if len(fields) < 2 or fields[0] not in {"100644", "100755"}:
            # An in-namespace symlink, tree or gitlink on origin fails closed
            # exactly as a local non-regular entry does.
            return RemoteView(frozenset(), "failed")
        names.add(name)
    return RemoteView(frozenset(names), "ok")


def _local_names(directory: Path, deadline: float) -> set[str]:
    """Return in-namespace record names, refusing an incomplete scan."""
    names: set[str] = set()
    try:
        with os.scandir(directory) as entries:
            for count, entry in enumerate(entries, start=1):
                if count > MAX_ENTRIES:
                    raise _ScanRefused("bound-exceeded")
                # The whole-invocation deadline covers the local scan too: a
                # directory at the entry bound is 65,536 metadata inspections,
                # and a bound that starts only at the first git call is not the
                # bound this contract states.
                if time.monotonic() >= deadline:
                    raise _ScanRefused("bound-exceeded")
                kind = classify(entry.name)
                if kind == "outside":
                    # Skipped without a dereference, so an adopter's link in
                    # this directory cannot fail a scan it has no part in.
                    continue
                if kind == "malformed":
                    raise _ScanRefused("unparsed-name")
                # stat(follow_symlinks=False) rather than is_file(): that
                # returns False on any OSError, so an entry removed between
                # listing and classification would be dropped silently and the
                # scan would report a result it never saw.
                try:
                    inspected = entry.stat(follow_symlinks=False)
                except OSError as error:
                    raise _ScanRefused("incomplete-scan") from error
                if not stat.S_ISREG(inspected.st_mode):
                    raise _ScanRefused("incomplete-scan")
                names.add(entry.name)
    except _ScanRefused:
        raise
    except OSError as error:
        raise _ScanRefused("incomplete-scan") from error
    return names


def _ordinals(names: set[str], token: str) -> set[int]:
    found: set[int] = set()
    for name in names:
        match = _VALID.match(name)
        if match is None:
            raise _ScanRefused("unparsed-name")
        if match.group(1) == token:
            found.add(int(match.group(2)))
    return found


def allocate(directory: Path, token: str) -> tuple[int | None, str | None]:
    """Return ``(ordinal, None)`` or ``(None, cause)`` for one type."""
    if token not in NAMESPACE_TOKENS:
        return None, "unparsed-name"
    deadline = _deadline()
    try:
        names = _local_names(directory, deadline)
        view = remote_view(directory, deadline)
        if view.state == "failed":
            return None, "remote-unavailable"
        for name in view.names:
            if classify(name) == "malformed":
                raise _ScanRefused("unparsed-name")
        # Union by name, so a record present locally and on origin is one
        # record rather than two.
        ordinals = _ordinals(names | set(view.names), token)
    except _ScanRefused as refusal:
        return None, refusal.cause
    allocated = (max(ordinals) + 1) if ordinals else 1
    if len(str(allocated)) > MAX_ORDINAL_DIGITS:
        # The successor would not match the shape this allocator counts, so it
        # would be written once and refused as malformed on every later scan.
        return None, "bound-exceeded"
    return allocated, None


def next_typed_ordinal(directory: Path, token: str) -> int | None:
    """Return the next ordinal for *token*, or ``None`` when none may be given."""
    ordinal, _ = allocate(Path(directory), token)
    return ordinal


def duplicate_ordinals(directory: Path) -> dict[tuple[str, int], list[str]]:
    """Return records sharing a type and an ordinal in *directory* alone.

    Local only, as in the ADR/RFC helper: allocation unions the remote view and
    this does not, because a remote-only collision is already committed.
    """
    records: dict[tuple[str, int], list[str]] = {}
    for name in _local_names(directory, _deadline()):
        match = _VALID.match(name)
        if match is None:
            raise _ScanRefused("unparsed-name")
        records.setdefault((match.group(1), int(match.group(2))), []).append(name)
    return {key: sorted(value) for key, value in records.items() if len(value) > 1}


def _confined(argument: str) -> Path:
    """Resolve a repository-relative directory argument, refusing an escape."""
    if not argument or argument.startswith("-"):
        raise _ScanRefused("incomplete-scan")
    candidate = Path(argument)
    if candidate.is_absolute() or any(part in {"..", ""} for part in candidate.parts):
        raise _ScanRefused("incomplete-scan")
    root = Path.cwd()
    target = root / candidate
    safety = _load_file_safety()
    try:
        safety.validate_confined_directory(root, target)
    except Exception as error:  # UnsafeContentError and anything it wraps
        raise _ScanRefused("incomplete-scan") from error
    return target


def _fail(cause: str) -> int:
    """Emit one fixed, bounded diagnostic token and refuse.

    Selected from a closed set, never composed: no byte of an argument reaches
    stderr, because a caller records this and an intent is a durable file.
    """
    if cause not in REFUSAL_CAUSES:
        cause = "incomplete-scan"
    message = f"intent-ordinal: {cause}"
    assert len(message.encode("utf-8")) <= DIAGNOSTIC_BYTE_LIMIT
    print(message, file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    """Run allocation or the duplicate check."""
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--check", metavar="DIR")
    parser.add_argument("--dir", dest="directory", metavar="DIR")
    parser.add_argument("--token", metavar="TOKEN")
    try:
        arguments = parser.parse_args(argv)
    except SystemExit:
        return _fail("incomplete-scan")

    if arguments.check is not None:
        try:
            directory = _confined(arguments.check)
            duplicates = duplicate_ordinals(directory)
        except _ScanRefused as refusal:
            return _fail(refusal.cause)
        if not duplicates:
            # On stderr, never stdout: a caller capturing stdout still gets
            # nothing, while a log distinguishes this from never having run.
            print("intent-ordinal: no duplicate ordinals", file=sys.stderr)
            return 0
        for (token, ordinal), names in sorted(duplicates.items()):
            print(f"duplicate ordinal {token}-{ordinal:04d}: {len(names)} records",
                  file=sys.stderr)
        return 1

    if arguments.directory is None or arguments.token is None:
        return _fail("incomplete-scan")
    if arguments.token not in NAMESPACE_TOKENS:
        return _fail("unparsed-name")
    try:
        directory = _confined(arguments.directory)
    except _ScanRefused as refusal:
        return _fail(refusal.cause)
    ordinal, cause = allocate(directory, arguments.token)
    if ordinal is None:
        return _fail(cause or "incomplete-scan")
    print(f"{arguments.token}-{ordinal:04d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
