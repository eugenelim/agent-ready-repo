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
import importlib.util
import os
import re
import stat
import subprocess
import sys
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
DIAGNOSTIC_BYTE_LIMIT = 200

GIT_REDIRECT_VARIABLES = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
)
_ORIGIN_REF_PREFIX = "refs/remotes/origin/"

_LEVEL_RE = re.compile(r"^[a-z][a-z-]{0,63}$")
_TOKEN_ALTERNATION = "|".join(NAMESPACE_TOKENS)
# Two patterns, not three: the introducer decides in-or-out of the namespace and
# the owner's shape decides valid-or-malformed inside it. Deriving "malformed"
# as "introducer and not shape" is what makes the partition exhaustive.
_INTRODUCER = re.compile(rf"^(?:{_TOKEN_ALTERNATION})-")
_VALID = re.compile(rf"^({_TOKEN_ALTERNATION})-(\d{{4,}})-[^/]+\.md$")

RemoteView = collections.namedtuple("RemoteView", "names state")


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


def _git(directory: Path, arguments: list[str], deadline: float) -> str | None:
    """Run one git command, reading its output incrementally under a bound.

    ``Popen`` rather than ``run``: the byte bound has to hold while reading,
    and ``run`` buffers the whole result before anything can check it.
    """
    environment = os.environ.copy()
    for variable in GIT_REDIRECT_VARIABLES:
        environment.pop(variable, None)
    # An argument vector free of `fetch` does not prove no egress: ls-tree on a
    # partial clone resolves a missing object through the promisor remote. This
    # fails that closed on a git that honours it; the configuration check in
    # `remote_view` covers a git too old to.
    environment["GIT_NO_LAZY_FETCH"] = "1"
    environment["GIT_TERMINAL_PROMPT"] = "0"
    remaining = max(0.0, min(GIT_TIMEOUT_SECONDS, deadline - os.times().elapsed))
    try:
        child = subprocess.Popen(
            ["git", "--literal-pathspecs", *arguments],
            cwd=os.fspath(directory),
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
    except (OSError, ValueError):
        return None
    if child is None or getattr(child, "stdout", None) is None:
        return None
    chunks: list[bytes] = []
    total = 0
    try:
        while True:
            chunk = child.stdout.read(65_536)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_GIT_RESULT_BYTES:
                child.kill()
                raise _ScanRefused("bound-exceeded")
            chunks.append(chunk)
        child.wait(timeout=remaining or None)
    except _ScanRefused:
        raise
    except subprocess.TimeoutExpired:
        child.kill()
        return None
    except (OSError, ValueError):
        return None
    if child.returncode != 0:
        return None
    return b"".join(chunks).decode("utf-8", "surrogateescape")


def git_config_values(directory: Path) -> dict[str, str]:
    """Return git's effective configuration, or ``{}`` when it cannot be read."""
    output = _git(directory, ["config", "--list"], _deadline())
    if output is None:
        return {}
    values: dict[str, str] = {}
    for line in output.splitlines():
        key, separator, value = line.partition("=")
        if separator:
            values[key.strip()] = value.strip()
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
        and value.strip().lower() in {"true", "1", "yes", "on"}
        for key, value in folded.items()
    )


def _deadline() -> float:
    return os.times().elapsed + TOTAL_TIMEOUT_SECONDS


def remote_view(directory: Path) -> RemoteView:
    """Return the record names visible on ``origin`` and how complete they are.

    Three states, because "nothing there" and "could not look" are different
    instructions to a caller. ``absent`` means there is nothing to consult and
    the working tree is the whole available view. ``failed`` means there is
    something to consult and no way to read it, which refuses.
    """
    deadline = _deadline()
    # Before any object-reading command: a promisor designation means a read
    # could reach the network, and this check is observable independently of
    # GIT_NO_LAZY_FETCH precisely because it runs first.
    if _is_promisor(git_config_values(directory)):
        return RemoteView(frozenset(), "failed")

    toplevel = _git(directory, ["rev-parse", "--show-toplevel"], deadline)
    if toplevel is None or not toplevel.strip():
        return RemoteView(frozenset(), "absent")
    remotes = _git(directory, ["remote"], deadline)
    if remotes is None or "origin" not in remotes.split():
        return RemoteView(frozenset(), "absent")

    ref = _git(directory, ["symbolic-ref", "--quiet", _ORIGIN_REF_PREFIX + "HEAD"], deadline)
    if ref is None or not ref.strip().startswith(_ORIGIN_REF_PREFIX):
        # origin exists and its default branch cannot be established, so the
        # view is incomplete in an unknown way rather than empty.
        return RemoteView(frozenset(), "failed")

    root = Path(toplevel.strip())
    try:
        relative = directory.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return RemoteView(frozenset(), "absent")
    pathspec = f"{relative.as_posix()}/" if relative.parts else "."
    # -z: git renders a non-ASCII name in quoted C-string form otherwise, which
    # starts with a quote and so matches no introducer — the record would be
    # invisible and its ordinal handed out again. The mode is kept (no
    # --name-only) so a non-blob entry inside the namespace can fail closed.
    listing = _git(root, ["ls-tree", "-z", ref.strip(), "--", pathspec], deadline)
    if listing is None:
        return RemoteView(frozenset(), "failed")

    names: set[str] = set()
    for record in listing.split("\0"):
        if not record:
            continue
        meta, _, path = record.partition("\t")
        if not path:
            return RemoteView(frozenset(), "failed")
        name = Path(path).name
        if classify(name) == "outside":
            continue
        fields = meta.split()
        if len(fields) < 2 or fields[0] not in {"100644", "100755"}:
            # An in-namespace symlink, tree or gitlink on origin fails closed
            # exactly as a local non-regular entry does.
            return RemoteView(frozenset(), "failed")
        names.add(name)
        if len(names) > MAX_ENTRIES:
            return RemoteView(frozenset(), "failed")
    return RemoteView(frozenset(names), "ok")


def _local_names(directory: Path) -> set[str]:
    """Return in-namespace record names, refusing an incomplete scan."""
    names: set[str] = set()
    try:
        with os.scandir(directory) as entries:
            for count, entry in enumerate(entries, start=1):
                if count > MAX_ENTRIES:
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
    try:
        names = _local_names(directory)
        view = remote_view(directory)
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
    return (max(ordinals) + 1 if ordinals else 1), None


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
    for name in _local_names(directory):
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
