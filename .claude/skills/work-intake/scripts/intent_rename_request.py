"""Validate a rename request for a repository intent.

A rename request names an existing live intent inside the intent directory
and a target namespace token from the allocator. This module decides
whether a request is well-formed and returns either a resolved request
object or one fixed refusal token.

The validator is total and side-effect free: it performs no writes and
returns a value for every input. The caller applies the rename; this
module only decides whether the rename is valid to attempt.

Refusal tokens, each naming the part at fault:
    ``root-unresolved``      — the repository root cannot be established.
    ``source-missing``       — the source path does not exist.
    ``source-outside-root``  — the source path escapes the intent directory.
    ``source-not-regular``   — the source path exists but is not a regular file.
    ``source-unreadable``    — the source cannot establish its own liveness.
    ``source-tombstone``     — the source carries a ``Tombstone:`` field.
    ``source-unregistered``  — the source has no workspace registry entry.
    ``registry-unparseable`` — the workspace registry is not valid TOML.
    ``registry-ambiguous``   — the workspace registry has more than one entry.
    ``token-unknown``        — the target token is not in the allocator namespace.
    ``path-dirty``           — the source path carries an uncommitted change.
"""

from __future__ import annotations

import importlib.util
import os
import re
import stat
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

# ── Sibling loader ────────────────────────────────────────────────────────────


def _load_sibling(name: str, module_name: str) -> object:
    """Load a sibling script by path under a pack-and-skill-qualified name.

    Skills are independent and several may ship a same-named script, so a
    bare ``import`` would bind whichever directory reached the path first
    and then cache it for every later importer. Loading by path under a
    unique name avoids that collision.

    The module is registered in ``sys.modules`` **before** ``exec_module``
    runs, so any frozen dataclass defined inside it can resolve its own
    ``__module__`` attribute correctly.
    """
    path = Path(__file__).resolve().parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot locate sibling module {name!r}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# Bytecode is a write; this module promises none. Save and restore the
# caller's value so sibling loading does not change process-wide behaviour
# for every later import in the host.
_prev_dont_write_bytecode = sys.dont_write_bytecode
sys.dont_write_bytecode = True
try:
    _shape = _load_sibling("intent_shape", "core_work_intake_intent_shape")
    _ordinal = _load_sibling("intent_ordinal", "core_work_intake_intent_ordinal")
    _transaction = _load_sibling(
        "intake_transaction", "core_work_intake_intake_transaction"
    )
    _file_safety = _load_sibling("file_safety", "core_work_intake_file_safety")
finally:
    sys.dont_write_bytecode = _prev_dont_write_bytecode

# ── Public constants ──────────────────────────────────────────────────────────

#: Repository-relative path of the intent directory.
INTENTS_PARENT = "docs/product/intents"

#: The two preamble fields that appear only on tombstones.  Their presence
#: without ``Tombstone:`` signals a structurally impossible live intent.
_POINTER_FIELDS: frozenset[str] = frozenset({"Reissued as", "Retired"})

#: Byte limit for the workspace registry read. 16 MiB comfortably exceeds
#: any workspace file this repository is expected to produce.
# The register's own reader recognises exactly this initiative-key shape.
# A table named like an initiative but outside it is not a registration
# there, so it must not be one here; a bare `ini-` prefix would count one.
_CANONICAL_INITIATIVE_RE = re.compile(r"^ini-\d{3}$")

_WORKSPACE_MAX_BYTES = 16 * 1024 * 1024

#: Byte limit for the source intent read.
_SOURCE_MAX_BYTES = 4 * 1024 * 1024


# ── Resolved request ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ResolvedRequest:
    """A validated rename request, ready for the caller to apply.

    All fields are guaranteed to satisfy the validator's checks: the source
    is a live, readable, registered intent inside the intent directory, the
    target token is in the allocator's namespace, and the source path
    carries no uncommitted change.
    """

    repository_root: Path
    """Resolved absolute repository root used for all path operations."""

    source: Path
    """Absolute path to the source intent file."""

    source_rel: str
    """Repository-relative path of the source, as supplied by the caller."""

    target_token: str
    """Target namespace token from the allocator."""


# ── Internal helpers ──────────────────────────────────────────────────────────


def _git_toplevel(cwd: Path) -> Path | None:
    """Return the git repository root, or ``None`` when the call fails.

    ``--no-optional-locks`` prevents the rev-parse from acquiring
    ``.git/index.lock``, keeping this call truly read-only. ``--literal-
    pathspecs`` is set for consistency with ``_is_dirty`` so both helpers
    share the same argv structure; rev-parse takes no pathspecs, but the
    flag is harmless and documents the intent.
    """
    try:
        result = subprocess.run(
            [
                "git",
                "--no-optional-locks",
                "--literal-pathspecs",
                "rev-parse",
                "--show-toplevel",
            ],
            cwd=os.fspath(cwd),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    line = result.stdout.decode("utf-8", errors="replace").strip()
    return Path(line) if line else None


def _is_dirty(repository_root: Path, source_rel: str) -> bool:
    """Return ``True`` when the source or workspace.toml carries any uncommitted change.

    Fails closed: any environmental failure — ``OSError``, ``TimeoutExpired``,
    or a nonzero exit code from either git invocation — reports dirty rather
    than letting the failure masquerade as a clean tree.

    Reports clean **only** when every guarded path is positively established
    as tracked in the index, not hidden from git's working-tree scan by the
    ``assume-unchanged`` or ``skip-worktree`` flags, and identical to HEAD.
    Absence of ``git status --porcelain`` output alone is not sufficient proof:
    ignored-and-untracked paths, and paths flagged ``assume-unchanged``
    (flag ``h``) or ``skip-worktree`` (flag ``S``), also produce no status
    output yet carry no guarantee of being clean.

    Both git invocations use ``--no-optional-locks`` so no index lock is
    acquired (keeping this function truly read-only), and ``--literal-
    pathspecs`` so a source filename containing glob characters is not
    interpreted as a pattern.
    """
    paths = [source_rel, "workspace.toml"]
    _GIT = ["git", "--no-optional-locks", "--literal-pathspecs"]

    # ── Step 1: verify tracked status and hidden-scan flags ───────────────────
    # ``git ls-files -v`` prints one line per tracked path in the form
    # ``<flag> <path>``.  Flag ``H`` is normal-tracked; ``h`` is
    # assume-unchanged; ``S`` is skip-worktree.  Either ``h`` or ``S`` hides
    # working-tree modifications from git's regular scan, so we treat them as
    # dirty regardless of whether the file is actually modified — the status
    # cannot be established positively.  A path absent from the output is
    # either untracked or ignored, which is also dirty.
    try:
        ls_result = subprocess.run(
            [*_GIT, "ls-files", "-v", "-z", "--", *paths],
            cwd=os.fspath(repository_root),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return True
    if ls_result.returncode != 0:
        return True

    # `-z` is load-bearing: without it git renders a path needing quoting in
    # its quoted, octal-escaped form, and a clean tracked file whose name
    # carries a non-ASCII character would never match the name we asked
    # about. NUL-separated records are byte-exact.
    tags: dict[str, list[str]] = {}
    ls_output = ls_result.stdout.decode("utf-8", errors="replace")
    for record in ls_output.split("\0"):
        if len(record) < 3:
            continue
        tags.setdefault(record[2:], []).append(record[0])

    # An allowlist, not a denylist. Only `H` — tracked, in the index, and not
    # hidden — proves a path is one git will report on. Every other tag is a
    # state that suppresses it from the scan below or leaves it unmerged, and
    # a denylist of the hidden ones has to be rediscovered each time git grows
    # a letter: `h`, `S` and `s` are all "assume-unchanged and/or
    # skip-worktree", and `s` is the combination.
    for p in paths:
        if tags.get(p) != ["H"]:
            return True

    # ── Step 2: check for staged or working-tree modifications ────────────────
    try:
        status_result = subprocess.run(
            [*_GIT, "status", "--porcelain", "--", *paths],
            cwd=os.fspath(repository_root),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return True
    if status_result.returncode != 0:
        return True
    return bool(status_result.stdout.strip())


def _count_registry_matches(data: object, target_path: str) -> int:
    """Count workspace entries whose ``path`` field equals ``target_path``.

    Registration is decided by **where** a path sits in the register, not by
    whether some table happens to carry a ``path`` key. Only two locations
    hold registrations: an initiative's work collections, and the shared
    backlog. A dict counts only when it is a direct element of one of those
    arrays.

    Position alone is not enough. Any array element anywhere would admit a
    decoy — an unrelated array of tables, or an ``open`` list under some
    other section — so the key path is matched as a whole rather than by its
    last segment.

    Nested structure inside an entry is never reached: an entry is compared
    and not traversed, so its ``needs`` edges and inline ``source`` table
    cannot contribute a second count for the same path.

    Complexity: O(n) in the number of nodes reachable from the two matched
    collection shapes, which is a small fraction of the document.
    """
    initiative_collections = {
        "work": ("queue", "active", "shipped"),
        "shaping_queue": ("active", "backlog"),
    }

    def _is_registry_collection(key_path: tuple[str, ...]) -> bool:
        """True for an initiative collection, or the shared backlog."""
        if len(key_path) == 3 and _CANONICAL_INITIATIVE_RE.fullmatch(key_path[0]):
            return key_path[2] in initiative_collections.get(key_path[1], ())
        return len(key_path) == 2 and key_path == ("backlog", "open")

    count = 0
    work: list[tuple[object, tuple[str, ...]]] = [(data, ())]
    while work:
        node, key_path = work.pop()
        if not isinstance(node, dict):
            continue
        for key, value in node.items():
            if not isinstance(key, str):
                continue
            child_path = key_path + (key,)
            if isinstance(value, list) and _is_registry_collection(child_path):
                for item in value:
                    if isinstance(item, dict):
                        entry_path = item.get("path")
                        if isinstance(entry_path, str) and entry_path == target_path:
                            count += 1
            elif isinstance(value, dict):
                work.append((value, child_path))
    return count


def _liveness_refusal(text: str) -> str | None:
    """Return a refusal token when liveness cannot be positively established.

    Liveness is established, not inferred from a field's absence.  A source
    whose preamble is ambiguous refuses rather than resolving to either side
    of the partition, because a best-effort read of an ambiguous preamble
    would let a retired name past the tombstone check.

    Returns one of ``source-unreadable`` or ``source-tombstone``, or
    ``None`` when the source is a live intent.
    """
    pairs = _shape.read_preamble(text)  # type: ignore[attr-defined]

    # No field parsed — liveness cannot be established.
    if not pairs:
        return "source-unreadable"

    names = {name for name, _ in pairs}

    # A parsed ``Tombstone:`` field identifies this as a tombstone.
    if "Tombstone" in names:
        return "source-tombstone"

    # A pointer field without ``Tombstone:`` is structurally impossible for a
    # live intent; refuse rather than resolving a structurally broken source.
    if names & _POINTER_FIELDS:
        return "source-unreadable"

    # Scan each visible preamble line for the ``tombstone`` token. Lines that
    # parse as any well-formed field are exempt regardless of their value, so
    # a ``Slug`` whose value is ``tombstone-migration`` or a field whose value
    # mentions tombstones in prose does not trigger this check. A visible line
    # that mentions ``tombstone`` but does NOT parse as any well-formed field
    # is a damaged marker — refuse rather than reading it as prose. A single
    # leading H1 title is exempt, so a live intent may name tombstone work in
    # its own title; only the first title is exempt, because a later one is
    # ordinary preamble. The accepted trade-off is that a tombstone marker
    # hand-damaged into an H1 heading is not caught here — reaching that state
    # requires editing a written marker into a heading, which no writer emits.
    inside_comment = False
    leading_content = True
    for line in text.splitlines():
        visible, inside_comment = _shape._visible_line_outside_comments(  # type: ignore[attr-defined]
            line, inside_comment
        )
        if visible.startswith("## "):
            break
        if visible.strip():
            # The exemption is for an H1 *title*, so the heading marker must
            # open the authored line. Testing the comment-stripped text alone
            # would also exempt a line whose ``# `` only surfaces once a
            # comment is removed — ``<!-- x --># Tombstone: …`` — which is a
            # token-bearing non-field line, not a title, and must still refuse.
            if (
                leading_content
                and line.lstrip().startswith("# ")
                and visible.startswith("# ")
            ):
                leading_content = False
                continue
            leading_content = False
        if "tombstone" not in visible.lower():
            continue
        # The line mentions ``tombstone``. Exempt it if it parses as any
        # well-formed field (any field name, any value).
        if _shape._FIELD_LINE.match(visible):  # type: ignore[attr-defined]
            continue
        # Does not parse as a well-formed field — treat as a damaged marker.
        return "source-unreadable"

    return None


# ── Public entry point ────────────────────────────────────────────────────────


def validate_rename_request(
    source_rel: str,
    target_token: str,
    *,
    repository_root: Path | None = None,
    _cwd: Path | None = None,
) -> ResolvedRequest | str:
    """Validate a rename request and return a resolved request or a refusal token.

    Args:
        source_rel: Repository-relative path of the source intent, e.g.
            ``"docs/product/intents/FEAT-0001-slug.md"``.
        target_token: Target namespace token from the allocator.
        repository_root: Repository root directory.  When ``None``, the root
            is discovered via ``git rev-parse --show-toplevel`` from ``_cwd``
            (or ``Path.cwd()`` when ``_cwd`` is also ``None``).  Supply a
            root to bypass git discovery, for example in callers that already
            hold a validated root.
        _cwd: Directory from which git discovery runs.  Ignored when
            ``repository_root`` is supplied.  Intended for tests that build
            their own git working tree under a temp path.

    Returns:
        A ``ResolvedRequest`` when every check passes, or one of the fixed
        refusal tokens when a check fails.  Exactly one token is returned
        per call; no exception escapes for expected failure modes.
    """
    # ── Step 1: resolve the repository root ──────────────────────────────────
    if repository_root is None:
        try:
            cwd = _cwd if _cwd is not None else Path.cwd()
        except OSError:
            return "root-unresolved"
        discovered = _git_toplevel(cwd)
        if discovered is None:
            return "root-unresolved"
        resolved_root = discovered
    else:
        try:
            resolved_root = repository_root.resolve(strict=True)
        except OSError:
            return "root-unresolved"

    # ── Step 2: confine the source path to the intent directory ──────────────
    try:
        _transaction.resolve_confined_target(  # type: ignore[attr-defined]
            repository_root=resolved_root,
            configured_parent=INTENTS_PARENT,
            artifact_target=source_rel,
        )
    except (ValueError, OSError):
        return "source-outside-root"

    # ── Step 3: check the source exists and is a regular file ────────────────
    original = resolved_root / source_rel
    try:
        st = original.lstat()
    except OSError:
        return "source-missing"

    if not stat.S_ISREG(st.st_mode):
        return "source-not-regular"

    # ── Step 4: read and check liveness ──────────────────────────────────────
    try:
        source_bytes = _file_safety.read_confined_regular_file(  # type: ignore[attr-defined]
            resolved_root, original, max_bytes=_SOURCE_MAX_BYTES
        )
        text = source_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError, ValueError):
        return "source-unreadable"

    refusal = _liveness_refusal(text)
    if refusal is not None:
        return refusal

    # ── Step 5: check the workspace registry ─────────────────────────────────
    workspace_path = resolved_root / "workspace.toml"
    try:
        workspace_bytes = _file_safety.read_confined_regular_file(  # type: ignore[attr-defined]
            resolved_root, workspace_path, max_bytes=_WORKSPACE_MAX_BYTES
        )
    except (OSError, ValueError):
        return "registry-unparseable"

    try:
        workspace_data = tomllib.loads(workspace_bytes.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError):
        return "registry-unparseable"

    match_count = _count_registry_matches(workspace_data, source_rel)
    if match_count == 0:
        return "source-unregistered"
    if match_count > 1:
        return "registry-ambiguous"

    # ── Step 6: check the target token ───────────────────────────────────────
    if target_token not in _ordinal.NAMESPACE_TOKENS:  # type: ignore[attr-defined]
        return "token-unknown"

    # ── Step 7: check for uncommitted changes ─────────────────────────────────
    if _is_dirty(resolved_root, source_rel):
        return "path-dirty"

    return ResolvedRequest(
        repository_root=resolved_root,
        source=original,
        source_rel=source_rel,
        target_token=target_token,
    )
