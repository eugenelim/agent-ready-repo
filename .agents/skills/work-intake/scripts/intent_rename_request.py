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
import stat
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

# Bytecode is a write; this module promises none.
sys.dont_write_bytecode = True


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


_shape = _load_sibling("intent_shape", "core_work_intake_intent_shape")
_ordinal = _load_sibling("intent_ordinal", "core_work_intake_intent_ordinal")
_transaction = _load_sibling(
    "intake_transaction", "core_work_intake_intake_transaction"
)

# ── Public constants ──────────────────────────────────────────────────────────

#: Repository-relative path of the intent directory.
INTENTS_PARENT = "docs/product/intents"

#: The two preamble fields that appear only on tombstones.  Their presence
#: without ``Tombstone:`` signals a structurally impossible live intent.
_POINTER_FIELDS: frozenset[str] = frozenset({"Reissued as", "Retired"})


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
    """Return the git repository root, or ``None`` when the call fails."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
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
    """Return ``True`` when the path carries any uncommitted change.

    Fails open on errors: if git is unavailable or the root is not a
    repository, the path is treated as clean rather than blocking the
    caller on an unrelated environmental failure.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--", source_rel],
            cwd=os.fspath(repository_root),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return bool(result.stdout.strip())


def _count_registry_matches(data: object, target_path: str) -> int:
    """Count workspace entries whose ``path`` field equals ``target_path``.

    Searches recursively through all TOML tables and arrays so entries
    nested under any initiative or queue key are found.
    """
    if isinstance(data, dict):
        count = 0
        p = data.get("path")
        if isinstance(p, str) and p == target_path:
            count += 1
        for value in data.values():
            count += _count_registry_matches(value, target_path)
        return count
    if isinstance(data, list):
        return sum(_count_registry_matches(item, target_path) for item in data)
    return 0


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

    # Scan each visible preamble line for the ``tombstone`` token.  A line
    # that contains the token but does not parse as a well-formed
    # ``Tombstone:`` field is a damaged marker — refuse rather than reading
    # it as prose.  Strictness is scoped to this marker; every other
    # unmatched line (H1 title, blanks, annotation bullets) is exempt.
    inside_comment = False
    for line in text.splitlines():
        visible, inside_comment = _shape._visible_line_outside_comments(  # type: ignore[attr-defined]
            line, inside_comment
        )
        if visible.startswith("## "):
            break
        if "tombstone" not in visible.lower():
            continue
        # The line mentions ``tombstone``.  Accept only a well-formed field.
        m = _shape._FIELD_LINE.match(visible)  # type: ignore[attr-defined]
        if not (m and m.group(1).strip() == "Tombstone"):
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
        cwd = _cwd if _cwd is not None else Path.cwd()
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
        text = original.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "source-unreadable"

    refusal = _liveness_refusal(text)
    if refusal is not None:
        return refusal

    # ── Step 5: check the workspace registry ─────────────────────────────────
    workspace_path = resolved_root / "workspace.toml"
    try:
        workspace_bytes = workspace_path.read_bytes()
    except OSError:
        return "source-unregistered"

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
