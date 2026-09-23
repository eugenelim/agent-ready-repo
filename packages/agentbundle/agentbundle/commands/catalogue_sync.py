"""``agentbundle catalogue sync`` handler — dry-run and check for a derived catalogue.

Neither ``--dry-run`` nor ``--check`` writes. Both resolve the upstream
source, replay the recorded derivation in memory through
``initialise_self_hosted.replay_derivation(..., interactive=False)``, and
print a plan or an answer. This phase's write path is exactly none — see
``docs/specs/catalogue-sync-dry-run/spec.md`` § Boundaries.

``resolve_catalogue`` and ``fetch_catalogue_archive_with_provenance`` are
imported at module scope (rather than lazily per call) so a caller can
monkeypatch them by attribute name on this module without reaching into
``agentbundle.catalogue`` / ``agentbundle.https_catalogue`` directly.
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterable

from agentbundle.catalogue import CatalogueError, resolve_catalogue, resolve_git_ref
from agentbundle.catalogue_tooling.file_safety import (
    UnsafeContentError,
    read_confined_regular_file,
    sha256_confined_regular_file,
)
from agentbundle.catalogue_tooling.initialise_self_hosted import (
    _OWNERSHIP_STATE_FILE,
    ReplayError,
    SelfHostedInitConfig,
    SelfHostOwnershipState,
    SelfHostPin,
    SelfHostRecipe,
    _is_attributed,
    _is_safe_recipe_text,
    _load_ownership_state,
    _load_self_host_recipe,
    _migrate_managed_paths,
    _plan_stale_owned_paths,
    _write_ownership_state,
    replay_derivation,
)
from agentbundle.commands._common import check_spec_version_gate, confirm_or_refuse
from agentbundle.config import PackState, State
from agentbundle.https_catalogue import fetch_catalogue_archive_with_provenance
from agentbundle.safety import (
    Publish,
    Tier,
    classify,
    companion_path,
    write_companion,
    write_jailed,
)

if TYPE_CHECKING:
    import argparse

# Exit codes — spec AC-0013's ordered, total table. `run()` and its two
# `--check` helpers implement every row as a sequence of first-match-wins
# predicates; see each function's docstring for the rows it owns.
_SUCCESS = 0
_DIFFERENCE = 1
_MALFORMED = 2
_CANNOT_ANSWER = 3
_APPLY_FAILED = 4

# The two digest-bearing schemes fetch_catalogue_archive_with_provenance
# handles; every other URI (local path or git+https://) goes through
# resolve_catalogue instead. Whose digest each form verifies differs — see
# docs/specs/catalogue-sync-dry-run/notes/grounding/probe-digest-provenance.py —
# which is why the two get distinct fidelity tokens rather than one shared
# "verified-digest" token.
_DIGEST_BEARING_PREFIXES = ("archive+https://", "catalogue+https://")

# `_plan_stale_owned_paths` decline tokens spec AC-0017 marks undecided — the
# confinement refusal and the unreadable entry. Every other decline reason is
# decided (compared) even though it declines removal. See that function's
# docstring for the full reason set.
_UNDECIDED_DECLINE_TOKENS = frozenset(
    {"path-confinement-refused", "recorded-entry-unreadable"}
)

# spec AC-0013's `--check` (no `--compare-tree`) rows: the recorded pin's
# `archive_sha256` must be exactly a 64-character lowercase hex string, or it
# is treated as absent/malformed and the row reads cannot-answer.
_HEX64 = re.compile(r"[0-9a-f]{64}")

# spec AC-0043 — `--guides` names the whole `guides/_shared/` subtree.
_GUIDES_SCOPE_PREFIX = "guides/_shared/"

# spec AC-0033 clause 5 / AC-0063 — the whole vendored tooling root, not only
# its `agentbundle/` subdirectory: the engine and the vendored
# `catalogue-curation` copy are installed as a pair, so phase 4 owns both
# under one extent. Compared as a prefix, like the pack scope below, so
# every path under either root is caught regardless of depth.
_DEFERRED_PACKAGE_PREFIXES = ("packages/credbroker/", ".agentbundle/tooling/")


def _is_deferred_package_path(path: str) -> bool:
    """AC-0033 clause 5 — ``True`` when *path* belongs to a `--package`
    subtree phase 4, not this phase, owns.
    """
    return path.startswith(_DEFERRED_PACKAGE_PREFIXES)


def _scope_subtrees(
    pack_names: list[str], profile_names: list[str], guides: bool
) -> tuple[frozenset[str], frozenset[str]] | None:
    """Return AC-0043's scope as ``(dir_prefixes, exact_paths)``.

    ``dir_prefixes`` each carry their trailing separator — comparing without
    it would let ``--pack core`` also admit the sibling
    ``packs/core-extras/``, which shares the prefix ``"packs/core"`` but not
    ``"packs/core/"``. ``--profile <name>`` names one exact file rather than
    a directory, so it is matched in ``exact_paths`` instead of as a prefix.

    Returns ``None`` when no scoping flag was supplied at all — AC-0043's
    "the scope is every path", which AC-0042 uses to assert clause 4 excludes
    nothing.
    """
    if not pack_names and not profile_names and not guides:
        return None
    dir_prefixes = {f"packs/{name}/" for name in pack_names}
    if guides:
        dir_prefixes.add(_GUIDES_SCOPE_PREFIX)
    exact_paths = {f"profiles/{name}.toml" for name in profile_names}
    return frozenset(dir_prefixes), frozenset(exact_paths)


def _in_scope(
    path: str, scope: tuple[frozenset[str], frozenset[str]] | None
) -> bool:
    """AC-0033 clause 4 — ``True`` when *path* is inside the scope AC-0043
    fixes. ``scope is None`` means no scoping flag was supplied, which admits
    every path.
    """
    if scope is None:
        return True
    dir_prefixes, exact_paths = scope
    if path in exact_paths:
        return True
    return any(path.startswith(prefix) for prefix in dir_prefixes)


def select_write_set(
    planned_paths: Iterable[str],
    *,
    pack_names: list[str],
    profile_names: list[str],
    guides: bool,
) -> tuple[set[str], int]:
    """AC-0033 clauses 4 and 5 — narrow *planned_paths* to the write set.

    *planned_paths* is the full replayed set (e.g. ``set(replay.file_bytes)``)
    — AC-0033 clause 3's admission, never narrowed by this function. See
    plan.md § Design decisions "The scope filter selects what is written,
    never what is replayed": narrowing the replay itself would mark the rest
    of the adopter's tree stale.

    Returns ``(admitted, deferred_package)``. ``deferred_package`` is AC-0066's
    count, computed over *planned_paths* exactly as given rather than over
    the scope-narrowed subset — AC-0066 fixes that this count "stay[s]
    computed over the full replayed selection" regardless of which scoping
    flags this run supplies, so a `--pack` run still reports how many
    deferred paths the *full* replay carries.
    """
    scope = _scope_subtrees(pack_names, profile_names, guides)
    deferred = 0
    admitted: set[str] = set()
    for path in planned_paths:
        if _is_deferred_package_path(path):
            deferred += 1
            continue
        if _in_scope(path, scope):
            admitted.add(path)
    return admitted, deferred


def build_pin(
    source_uri: str,
    *,
    archive_sha256: str | None,
    source_revision: str | None,
    attributed: bool,
    synced_at: str,
) -> dict[str, Any]:
    """AC-0037 — the recorded pin row for *source_uri*'s source form.

    Reuses ``SelfHostPin`` (``init``'s own pin record) rather than a second
    dict shape, so "``source_uri`` present only under ``attributed``" stays
    one implementation. *archive_sha256* and *source_revision* are the
    values ``_resolve_source`` already returns for the two digest-bearing
    forms — ``archive_sha256`` absent and ``source_revision`` absent for
    ``archive+https://``, ``source_revision`` the descriptor's value or
    absent for ``catalogue+https://`` — and *pass through unchanged* for
    those two forms and for a local path.

    A ``git+https://`` URI is the one row phase 2's resolver can't supply:
    ``_resolve_source`` computes the ref only to fetch against it and
    discards the value (plan.md § Interfaces & contracts). This function
    reads the same ref through :func:`agentbundle.catalogue.resolve_git_ref`
    — the one parse T1 exported — rather than re-deriving it, so the fetch
    and the pin can never disagree. *source_revision* is ignored for this
    one form.
    """
    revision = (
        resolve_git_ref(source_uri)
        if source_uri.startswith("git+https://")
        else source_revision
    )
    pin = SelfHostPin(
        source_uri=source_uri if attributed else None,
        source_revision=revision,
        archive_sha256=archive_sha256,
        synced_at=synced_at,
    )
    return pin.to_dict()


def merge_ownership_state(
    old_state: dict[str, Any],
    *,
    recorded: dict[str, str | None],
    written: dict[str, str],
    removed: Iterable[str],
    pack_names: list[str],
    profile_names: list[str],
    pin: dict[str, Any],
) -> dict[str, Any]:
    """AC-0059/AC-0036/AC-0033 clause 1/AC-0044/AC-0045 — the post-run state.

    Touches no filesystem: every value comes from an argument, never from a
    read of *target*. Callers (T4's write phase, T6's ``_run_apply``) own
    building each argument from what they actually did.

    ``recorded`` is the pre-run ``path -> sha256`` mapping (``None`` for a
    schema-1 null-sha entry) — the same shape ``_classify_planned_paths``
    already builds from ``managed_paths``. ``written`` is ``path ->
    sha256`` for exactly the paths this run wrote *to their recorded
    identity* — a ``would-update`` path, or a path admitted only because it
    belongs to a pack or profile this run introduced (AC-0033 clause 3's
    last admission). A ``would-companion`` path's original path is not in
    ``written`` (its digest does not change — that is what keeps it
    classified Tier-2 next time) and its *companion destination* is never a
    key in either mapping, so the merged path set excludes Tier-3 and
    companion paths structurally: the merge has no argument through which
    either could ever arrive, rather than a runtime filter over one that
    could.

    The merged set is ``(recorded - removed) | written`` exactly — clause
    ordering matters: ``written`` is applied last so a path both stale (no
    longer planned) and freshly written (e.g. re-admitted this run) lands
    on its new digest, never its pre-run one.

    ``pack_names``/``profile_names`` are AC-0033 clause 1's already-resolved
    effective selection; T6 owns resolving them and AC-0068's validity
    domain. Every other recipe field — ``name``, ``display_name``,
    ``guides``, ``attribution``, ``tooling``, and the rest — is carried
    forward from ``old_state`` unchanged: AC-0033's write-set definition
    reaches no state-file field, so nothing here has a mandate to update
    one, and carrying every field forward unconditionally is what keeps a
    scoped run's recorded identity untouched (AC-0044) without a second,
    scope-aware code path.
    """
    removed_set = set(removed)
    merged_paths: dict[str, str | None] = {
        path: sha for path, sha in recorded.items() if path not in removed_set
    }
    merged_paths.update(written)

    old_recipe = old_state.get("recipe")
    recipe: dict[str, Any] = dict(old_recipe) if isinstance(old_recipe, dict) else {}
    recipe["packs"] = list(pack_names)
    recipe["profiles"] = list(profile_names)

    new_state = dict(old_state)
    new_state["managed_paths"] = [
        {"path": path, "sha256": sha} for path, sha in merged_paths.items()
    ]
    new_state["recipe"] = recipe
    new_state["pin"] = pin
    return new_state


# ---------------------------------------------------------------------------
# T4: the write sequence applies a plan or restores the tree.
#
# Composes T2's `select_write_set` (scope + deferred-package exclusion) and
# T3's `merge_ownership_state`/`build_pin` rather than duplicating either.
# `apply_write_sequence` is the one entry point T6's `_run_apply` calls after
# consent; every other function here is one of its independently testable
# pieces (plan.md § Component decomposition names the rollback snapshot as
# this task's own named seam — the rest is what "applies a plan or restores
# the tree" requires alongside it).
# ---------------------------------------------------------------------------

# spec AC-0076 — a chosen ceiling, not a measurement (plan.md's Design
# decisions "Rollback holds the prior walk tuple in memory").
_SNAPSHOT_BOUND_BYTES = 256 * 1024 * 1024
_SNAPSHOT_CHUNK_BYTES = 1024 * 1024


class SnapshotBoundExceeded(Exception):
    """AC-0076 — the write-set paths that exist hold more than the bound."""

    def __init__(self, *, bound: int, measured: int) -> None:
        super().__init__(
            f"write-set paths hold {measured} byte(s), which exceeds the "
            f"{bound}-byte bound"
        )
        self.bound = bound
        self.measured = measured


class SnapshotUnreadableError(Exception):
    """A write-set path's pre-run state could not be read while building the
    rollback snapshot (an AC-0039 `3 — cannot-answer` row)."""

    def __init__(self, path: str) -> None:
        super().__init__(f"cannot read pre-run state of {path!r}")
        self.path = path


@dataclass(frozen=True)
class WalkEntry:
    """One path's pre-run state — the same tuple AC-0041 compares: entry
    kind, mode, symlink target, and bytes (regular files only).
    """

    kind: str  # "absent" | "file" | "dir" | "symlink" | "other"
    mode: int | None
    symlink_target: str | None
    content: bytes | None


_ABSENT_ENTRY = WalkEntry(kind="absent", mode=None, symlink_target=None, content=None)


def _read_bounded_chunks(path: Path) -> Iterable[bytes]:
    """Yield *path*'s bytes in fixed-size chunks.

    Split out so a test can force a chunked read to yield more than the
    file's own ``st_size`` predicted — simulating a path that grew between
    the pre-prompt ``st_size`` sum and this read, which is the race
    AC-0076's as-built bound exists to catch (plan.md T4 § Tests).
    """
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(_SNAPSHOT_CHUNK_BYTES)
            if not chunk:
                return
            yield chunk


def _lstat_entry(path: Path) -> WalkEntry:
    """Non-dereferencing read of *path*'s kind, mode and symlink target.

    Never reads file content — :func:`snapshot_write_set` does that itself,
    incrementally, so the byte bound holds over bytes actually read.
    """
    try:
        st = path.lstat()
    except OSError:
        return _ABSENT_ENTRY
    if stat.S_ISLNK(st.st_mode):
        try:
            target = str(path.readlink())
        except OSError:
            target = None
        return WalkEntry(kind="symlink", mode=stat.S_IMODE(st.st_mode),
                          symlink_target=target, content=None)
    if stat.S_ISDIR(st.st_mode):
        return WalkEntry(kind="dir", mode=stat.S_IMODE(st.st_mode),
                          symlink_target=None, content=None)
    if stat.S_ISREG(st.st_mode):
        return WalkEntry(kind="file", mode=stat.S_IMODE(st.st_mode),
                          symlink_target=None, content=None)
    return WalkEntry(kind="other", mode=stat.S_IMODE(st.st_mode),
                      symlink_target=None, content=None)


def _ancestor_relpaths(relpath: str) -> list[str]:
    """Return *relpath*'s ancestor directories, root-first, as posix strings.

    Excludes the root itself (``"."``) and *relpath* itself.
    """
    parts = Path(relpath).parts[:-1]
    return [
        "/".join(parts[: i + 1]) for i in range(len(parts))
    ]


def snapshot_write_set(
    target: Path,
    paths: Iterable[str],
    *,
    bound: int = _SNAPSHOT_BOUND_BYTES,
) -> dict[str, WalkEntry]:
    """AC-0038/AC-0076 — the pre-run walk tuple for every *paths* entry and
    its ancestor directories, taken before the consent prompt.

    Two passes, per AC-0076: first, a fast ``st_size`` sum over every
    existing path with no content read at all, refusing before any byte is
    read when the sum alone exceeds *bound* (naming it and the measured
    sum). Second, the actual snapshot is built, reading each file's bytes in
    bounded chunks and re-checking the running total as it reads — a bound
    checked only against a per-file finished total would still read one
    path that grew past the first pass's sum in full before it could trip
    (plan.md T4 § Tests, AC-0076's as-built half).

    Raises :class:`SnapshotUnreadableError` when a path that exists cannot
    be read at all (spec AC-0039's own row for this).
    """
    unique_paths = sorted(set(paths))

    total = 0
    for relpath in unique_paths:
        entry = _lstat_entry(target / relpath)
        if entry.kind == "file":
            try:
                total += (target / relpath).stat().st_size
            except OSError as exc:
                raise SnapshotUnreadableError(relpath) from exc
    if total > bound:
        raise SnapshotBoundExceeded(bound=bound, measured=total)

    snapshot: dict[str, WalkEntry] = {}
    running = 0
    for relpath in unique_paths:
        for ancestor in _ancestor_relpaths(relpath):
            if ancestor in snapshot:
                continue
            snapshot[ancestor] = _lstat_entry(target / ancestor)

        full = target / relpath
        entry = _lstat_entry(full)
        if entry.kind == "file":
            buffer = bytearray()
            try:
                for chunk in _read_bounded_chunks(full):
                    buffer.extend(chunk)
                    running += len(chunk)
                    if running > bound:
                        raise SnapshotBoundExceeded(bound=bound, measured=running)
            except SnapshotBoundExceeded:
                raise
            except OSError as exc:
                raise SnapshotUnreadableError(relpath) from exc
            entry = dataclasses.replace(entry, content=bytes(buffer))
        snapshot[relpath] = entry
    return snapshot


def restore_from_snapshot(
    target: Path,
    snapshot: dict[str, WalkEntry],
    acted_paths: Iterable[str],
) -> list[str]:
    """AC-0038 — restore every path in *acted_paths* to its *snapshot* state.

    Scoped to *acted_paths* — what the run actually wrote, created or
    removed — never to the whole snapshot: restoring a path the run never
    reached would rewrite an adopter edit made at that path during the run
    (plan.md's Design decisions, "Rollback holds the prior walk tuple in
    memory"). Best-effort: every path is attempted regardless of an earlier
    failure, and every path that could not be restored is returned rather
    than raised (spec AC-0058).

    File content is restored through :func:`agentbundle.safety.write_jailed`
    — every target-tree write goes through the jailed primitive, restore
    included (plan.md § Constraints). A directory the run created and the
    snapshot shows absent is removed once it is empty; a directory removal
    left non-empty by an unrestorable child is itself reported unrestored.
    """
    unrestored: list[str] = []
    scope: set[str] = set()
    for relpath in acted_paths:
        scope.add(relpath)
        scope.update(_ancestor_relpaths(relpath))
    # Deepest paths first so a directory's children are gone (or reported
    # unrestored) before the directory itself is considered for removal.
    ordered = sorted(scope, key=lambda p: p.count("/"), reverse=True)
    for relpath in ordered:
        entry = snapshot.get(relpath, _ABSENT_ENTRY)
        full = target / relpath
        try:
            if entry.kind == "absent":
                current = _lstat_entry(full)
                if current.kind in ("file", "symlink"):
                    full.unlink()
                elif current.kind == "dir":
                    # Only ever empty if every child this run created under
                    # it was itself already restored (deepest-first order);
                    # an OSError here (non-empty) is reported, not raised
                    # past this loop, matching every other restore failure.
                    full.rmdir()
                # already absent: nothing to do.
            elif entry.kind == "file":
                write_jailed(target, relpath, entry.content or b"", mode=entry.mode)
            else:
                # A pre-existing ancestor directory: still a directory is a
                # no-op restore.
                pass
        except OSError:
            unrestored.append(relpath)
    return unrestored


def _write_group(path: str) -> int:
    """AC-0032 — the order group *path*'s destination sorts into: packs,
    profiles, guides, then everything else (the derivation-wide paths)."""
    if path.startswith("packs/"):
        return 0
    if path.startswith("profiles/"):
        return 1
    if path.startswith(_GUIDES_SCOPE_PREFIX):
        return 2
    return 3


def write_order(paths: Iterable[str]) -> list[str]:
    """AC-0032 — *paths* ordered packs, profiles, guides, derivation-wide.

    The ownership state (AC-0033 clause 6) is never passed here — it is
    always written after every path this returns, by construction of the
    caller.
    """
    return sorted(set(paths), key=lambda p: (_write_group(p), p))


def gate_recheck(target: Path, expected: dict[str, str | None]) -> list[str]:
    """AC-0077's gate recheck — *expected* maps a `would-update` destination
    to the digest (``None`` for "classification found no entry") its row was
    classified against. Returns every path whose on-disk state has since
    diverged — a changed digest, a changed entry kind, or an entry found
    where none was expected.

    Runs once, after consent and before the write phase opens, over every
    write-set destination that carries a classified row — never over the
    ownership state, which has none. An ordinary confined read; needs no
    change to the write helpers (plan.md § Constraints).
    """
    diverged: list[str] = []
    for path in sorted(expected):
        full = target / path
        try:
            full.lstat()
            exists = True
        except OSError:
            exists = False

        expected_sha = expected[path]
        if not exists:
            if expected_sha is not None:
                diverged.append(path)
            continue
        if expected_sha is None:
            diverged.append(path)
            continue
        try:
            actual = sha256_confined_regular_file(target, full)
        except UnsafeContentError:
            diverged.append(path)
            continue
        if actual != expected_sha:
            diverged.append(path)
    return diverged


def _staged_sibling_name(directory: Path, destination_name: str) -> str | None:
    """Find a staged temp file of this command's own staging shape.

    Mirrors ``safety.write_jailed``'s staging pattern:
    ``tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=...)``.
    """
    prefix = destination_name + "."
    try:
        candidates = sorted(
            entry.name for entry in directory.iterdir()
            if entry.name.startswith(prefix) and entry.name.endswith(".tmp")
        )
    except OSError:
        return None
    return candidates[0] if candidates else None


def classify_companion_destinations(
    target: Path, companions: dict[str, str]
) -> tuple[dict[str, str], dict[str, str], dict[str, str | None]]:
    """AC-0070's admission check — classify every computed companion
    destination in *companions* (``original path -> companion path``).

    Returns ``(admitted, occupied, residue)``. ``admitted`` and ``occupied``
    map ``original -> companion``; ``residue`` maps ``original -> sibling``
    (``None`` when no staged sibling of this command's own staging shape is
    found). A destination absent on disk is admitted. A present destination
    with a link count of one is an ordinary occupant. A present destination
    with a link count above one is the crash residue AC-0070's third outcome
    names, reported separately from an occupant.

    A plain ``lstat`` — never an attempted link — decides admission: the
    non-replacing publish's own atomic mechanism (not this check) is what
    actually protects against a destination that appears *after* this run
    (spec AC-0070's admission race), so this function never itself writes.
    """
    admitted: dict[str, str] = {}
    occupied: dict[str, str] = {}
    residue: dict[str, str | None] = {}
    for original in sorted(companions):
        companion = companions[original]
        full = target / companion
        try:
            st = full.lstat()
        except OSError:
            admitted[original] = companion
            continue
        if st.st_nlink > 1:
            residue[original] = _staged_sibling_name(full.parent, full.name)
        else:
            occupied[original] = companion
    return admitted, occupied, residue


def detect_companion_collisions(
    companions: dict[str, str], planned_paths: set[str]
) -> dict[str, str]:
    """AC-0071 — every ``original -> companion`` pair whose companion
    destination the replayed source itself plans, refusing the whole run.
    """
    return {
        original: companion
        for original, companion in companions.items()
        if companion in planned_paths
    }


def _resolves_within(target: Path, path: str, protected_prefixes: tuple[str, ...]) -> bool:
    """AC-0069's spelling clause — True when *path* resolves, by directory
    identity rather than a string prefix, inside one of *protected_prefixes*.

    A string prefix comparison is defeated by a traversal
    (``packs/../.agentbundle/tooling/x``) and, on a case-insensitive
    filesystem, by a differing-case spelling
    (``.agentbundle/Tooling/x``) — both resolve to the same on-disk entry a
    plain prefix comparison misses. ``os.path.samestat`` compares the
    resolved ancestor's device/inode against each protected directory's own,
    which the OS itself folds case on when the filesystem does.
    """
    try:
        resolved = (target / path).resolve(strict=True)
    except OSError:
        return False
    protected_stats = []
    for prefix in protected_prefixes:
        try:
            protected_stats.append((target / prefix).stat())
        except OSError:
            continue
    if not protected_stats:
        return False
    try:
        root_resolved = target.resolve(strict=True)
    except OSError:
        return False
    current = resolved.parent
    while True:
        try:
            current_stat = current.stat()
        except OSError:
            break
        if any(os.path.samestat(current_stat, ps) for ps in protected_stats):
            return True
        if current == root_resolved or current.parent == current:
            break
        current = current.parent
    return False


def _in_coverage(
    target: Path,
    path: str,
    *,
    pack_names: list[str],
    profile_names: list[str],
    guides_mode: str,
    scope: tuple[frozenset[str], frozenset[str]] | None,
) -> bool:
    """AC-0069 — True when *path* lies inside this run's coverage.

    Coverage is a positive set (this run's resolved packs/profiles, guides
    under a selecting mode, and every path the scope AC-0043 fixes admits),
    narrowed by the exclusions AC-0069 names — never the exclusions alone,
    which would re-admit every axis nobody enumerated.
    """
    if _resolves_within(target, path, _DEFERRED_PACKAGE_PREFIXES):
        return False
    if guides_mode == "none" and path.startswith(_GUIDES_SCOPE_PREFIX):
        return False
    if not _in_scope(path, scope):
        return False
    if path.startswith("packs/"):
        return any(path.startswith(f"packs/{name}/") for name in pack_names)
    if path.startswith("profiles/"):
        return any(path == f"profiles/{name}.toml" for name in profile_names)
    return True


def select_removal_set(
    target: Path,
    old_state: dict[str, Any],
    full_replayed_paths: set[str],
    *,
    pack_names: list[str],
    profile_names: list[str],
    guides_mode: str,
    scope: tuple[frozenset[str], frozenset[str]] | None,
) -> tuple[set[str], set[str]]:
    """AC-0035/AC-0064/AC-0069 — the paths this run actually removes, and the
    recorded-but-protected paths reported as ``out_of_coverage``.

    The keep-set passed to the shipped removal guard is *full_replayed_paths*
    unconditionally — never scope-narrowed, per plan.md's Design decisions
    ("The removal set needs its own filter, and it is not the keep-set").
    Coverage narrows the guard's *returned* removable list instead, which is
    the § Never do boundary: passing a narrowed keep-set into
    ``_plan_stale_owned_paths`` would mark every out-of-scope recipe path
    stale.
    """
    removable, _reasons = _plan_stale_owned_paths(
        target, old_state, full_replayed_paths
    )
    removal_set: set[str] = set()
    out_of_coverage: set[str] = set()
    for path in removable:
        if _in_coverage(
            target, path,
            pack_names=pack_names, profile_names=profile_names,
            guides_mode=guides_mode, scope=scope,
        ):
            removal_set.add(path)
        else:
            out_of_coverage.add(path)
    return removal_set, out_of_coverage


def _confined_unlink(target: Path, path: str) -> bool:
    """AC-0073 — remove *path*, refusing at the unlink (not only at the plan)
    if it is no longer a confined, non-link-like regular file.

    Reuses the exact confinement helper the removal planner itself applies
    (``_plan_stale_owned_paths``'s own sha guard), so "the same confinement"
    is one implementation rather than a second copy.
    """
    full = target / path
    try:
        sha256_confined_regular_file(target, full)
    except (UnsafeContentError, OSError):
        return False
    try:
        full.unlink()
    except OSError:
        return False
    return True


def _dataclass_from_dict(cls: type, data: dict[str, Any]) -> Any:
    """Build *cls* from *data*, dropping any key *cls* does not declare."""
    field_names = {f.name for f in dataclasses.fields(cls)}
    return cls(**{k: v for k, v in data.items() if k in field_names})


def write_merged_state(target: Path, merged_state: dict[str, Any]) -> None:
    """AC-0033 clause 6 — persist *merged_state* through ``init``'s own state
    writer, so its symlink refusal and random ``O_EXCL`` staging name stay
    one implementation (plan.md § Constraints) rather than a second one.
    """
    state = SelfHostOwnershipState(
        schema_version=merged_state.get("schema_version", "3"),
        managed_paths=merged_state.get("managed_paths", []),
        adapters=merged_state.get("adapters", []),
        managed_target_path=merged_state.get("managed_target_path", ""),
        source_pack_identity=merged_state.get("source_pack_identity", ""),
        source_root_kind=merged_state.get("source_root_kind", "self-hosted-source"),
        recipe=_dataclass_from_dict(SelfHostRecipe, merged_state.get("recipe") or {}),
        pin=_dataclass_from_dict(SelfHostPin, merged_state.get("pin") or {}),
    )
    _write_ownership_state(target, state)


@dataclass
class WriteSequenceResult:
    """T6's own material for mapping onto AC-0039's rows and for building
    :func:`merge_ownership_state`'s arguments. At most one failure field is
    ever populated; ``ok`` says which shape this is.
    """

    ok: bool
    written: dict[str, str] = field(default_factory=dict)
    removed: set[str] = field(default_factory=set)
    out_of_coverage: set[str] = field(default_factory=set)
    companion_occupied: dict[str, str] = field(default_factory=dict)
    companion_residue: dict[str, str | None] = field(default_factory=dict)
    companion_collision: dict[str, str] | None = None
    snapshot_bound_exceeded: tuple[int, int] | None = None
    snapshot_unreadable: str | None = None
    gate_diverged: list[str] | None = None
    write_failed_path: str | None = None
    restored: bool | None = None
    unrestored: list[str] = field(default_factory=list)
    removal_failed: bool = False
    state_write_failed: bool = False


def apply_write_sequence(
    target: Path,
    *,
    old_state: dict[str, Any] | None,
    verdict_rows: list[tuple[str, str, str | None]],
    file_bytes: dict[str, bytes],
    planned_paths: set[str],
    pack_names: list[str],
    profile_names: list[str],
    scope_packs: Iterable[str] = (),
    scope_profiles: Iterable[str] = (),
    guides_scope: bool = False,
    guides_mode: str,
    pin: dict[str, Any],
    snapshot_bound_bytes: int = _SNAPSHOT_BOUND_BYTES,
) -> WriteSequenceResult:
    """AC-0032/AC-0033/AC-0034/AC-0035/AC-0038/AC-0058/AC-0059/AC-0070/
    AC-0071/AC-0073/AC-0076/AC-0077 — apply the plan *verdict_rows* classified
    (spec AC-0033 clauses 3-6), or restore the tree.

    *pack_names*/*profile_names* are AC-0033 clause 1's already-resolved
    effective selection (the recorded recipe unioned with any name a scoping
    flag introduces) — used for introduced-pack/profile detection and for
    AC-0069's coverage selection axis. *scope_packs*/*scope_profiles*/
    *guides_scope* are the raw scoping **flags** AC-0043 names — a narrower,
    usually-empty list distinct from the resolved selection, forwarded to
    T2's `select_write_set` unchanged; conflating the two would scope every
    write to only the flag's own names even on an unscoped run, since the
    resolved selection is never empty in practice.

    Removal after every write, and the state after removal, because a crash
    between the two must leave a recorded state that under-claims rather
    than over-claims what it owns (plan.md T4 § Approach): only a write-phase
    failure is rolled back (AC-0038); a removal or state-write failure after
    every write has landed leaves those writes and any completed removal in
    place, reporting `4 — apply-failed` (spec AC-0039/AC-0041's own rows for
    each).
    """
    old_state = old_state or {}
    old_recipe = old_state.get("recipe")
    old_packs = set(old_recipe.get("packs", []) or []) if isinstance(old_recipe, dict) else set()
    old_profiles = (
        set(old_recipe.get("profiles", []) or []) if isinstance(old_recipe, dict) else set()
    )
    introduced_packs = set(pack_names) - old_packs
    introduced_profiles = set(profile_names) - old_profiles

    recorded: dict[str, str | None] = {}
    for entry in _migrate_managed_paths(old_state):
        path = entry.get("path", "")
        if path:
            sha = entry.get("sha256")
            recorded[path] = sha if isinstance(sha, str) else None

    would_update: set[str] = set()
    companions: dict[str, str] = {}
    admitted_new: set[str] = set()
    for path, verdict, companion in verdict_rows:
        if verdict == "would-update":
            would_update.add(path)
        elif verdict == "would-companion" and companion:
            companions[path] = companion
        elif verdict == "untouched":
            introduced_pack_path = any(
                path.startswith(f"packs/{name}/") for name in introduced_packs
            )
            introduced_profile_path = any(
                path == f"profiles/{name}.toml" for name in introduced_profiles
            )
            if introduced_pack_path or introduced_profile_path:
                admitted_new.add(path)

    collisions = detect_companion_collisions(companions, planned_paths)
    if collisions:
        return WriteSequenceResult(ok=False, companion_collision=collisions)

    admitted_companions, occupied, residue = classify_companion_destinations(
        target, companions
    )

    scope_packs = list(scope_packs)
    scope_profiles = list(scope_profiles)
    scope = _scope_subtrees(scope_packs, scope_profiles, guides_scope)
    raw_admitted = would_update | set(admitted_companions.values()) | admitted_new
    admitted, _deferred = select_write_set(
        raw_admitted, pack_names=scope_packs, profile_names=scope_profiles,
        guides=guides_scope,
    )
    would_update_admitted = would_update & admitted
    companion_destination_to_original = {
        companion: original for original, companion in admitted_companions.items()
        if companion in admitted
    }

    try:
        snapshot = snapshot_write_set(target, admitted, bound=snapshot_bound_bytes)
    except SnapshotBoundExceeded as exc:
        return WriteSequenceResult(
            ok=False, snapshot_bound_exceeded=(exc.bound, exc.measured),
            companion_occupied=occupied, companion_residue=residue,
        )
    except SnapshotUnreadableError as exc:
        return WriteSequenceResult(
            ok=False, snapshot_unreadable=exc.path,
            companion_occupied=occupied, companion_residue=residue,
        )

    expected_would_update: dict[str, str | None] = {
        path: (
            hashlib.sha256(snapshot[path].content).hexdigest()
            if snapshot[path].kind == "file" else None
        )
        for path in would_update_admitted
    }
    diverged = gate_recheck(target, expected_would_update)
    if diverged:
        return WriteSequenceResult(
            ok=False, gate_diverged=sorted(diverged),
            companion_occupied=occupied, companion_residue=residue,
        )

    ordered = write_order(admitted)
    written: dict[str, str] = {}
    acted: list[str] = []
    write_failed_path: str | None = None
    for path in ordered:
        is_companion = path in companion_destination_to_original
        try:
            if is_companion:
                original = companion_destination_to_original[path]
                content = file_bytes[original]
                # `write_companion` computes the `.upstream.<ext>` suffix
                # itself from *original* — passing the already-suffixed
                # destination here would suffix it a second time.
                write_companion(target, original, content, publish=Publish.NEVER_REPLACE)
            elif path in would_update_admitted:
                content = file_bytes[path]
                write_jailed(
                    target, path, content,
                    publish=Publish.REPLACE_IF_UNCHANGED,
                    expected_sha256=expected_would_update[path],
                )
            else:
                content = file_bytes[path]
                write_jailed(target, path, content)
        except Exception:
            write_failed_path = path
            break
        acted.append(path)
        # A companion destination is never a key in `written` — its
        # *original* path's digest does not change (AC-0034), and AC-0059
        # keeps the companion path itself out of the recorded state; T3's
        # `merge_ownership_state` has no argument through which either could
        # arrive, and this is the one seam that must not hand it one.
        if not is_companion:
            written[path] = hashlib.sha256(content).hexdigest()

    if write_failed_path is not None:
        # `write_jailed`/`write_companion` create the destination's parent
        # directory before the write that then fails, so the failed path's
        # own ancestor is a restore candidate too — but never the failed
        # path's own content: it was never actually written (a divergence
        # refuses before the rename, every other failure cleans up its own
        # staged tempfile), so whatever is at that path is either untouched
        # or another writer's edit, and AC-0041 requires either to be left
        # exactly as found rather than restored to the pre-run snapshot.
        restore_scope = [*acted, *_ancestor_relpaths(write_failed_path)]
        unrestored = restore_from_snapshot(target, snapshot, restore_scope)
        return WriteSequenceResult(
            ok=False,
            write_failed_path=write_failed_path,
            restored=not unrestored,
            unrestored=unrestored,
            companion_occupied=occupied,
            companion_residue=residue,
        )

    removal_set, out_of_coverage = select_removal_set(
        target, old_state, planned_paths,
        pack_names=pack_names, profile_names=profile_names,
        guides_mode=guides_mode, scope=scope,
    )
    removed: set[str] = set()
    removal_failed = False
    for path in sorted(removal_set):
        if _confined_unlink(target, path):
            removed.add(path)
        else:
            removal_failed = True

    if removal_failed:
        return WriteSequenceResult(
            ok=False, removal_failed=True,
            written=written, removed=removed, out_of_coverage=out_of_coverage,
            companion_occupied=occupied, companion_residue=residue,
        )

    merged = merge_ownership_state(
        old_state, recorded=recorded, written=written, removed=removed,
        pack_names=pack_names, profile_names=profile_names, pin=pin,
    )
    try:
        write_merged_state(target, merged)
    except Exception:
        return WriteSequenceResult(
            ok=False, state_write_failed=True,
            written=written, removed=removed, out_of_coverage=out_of_coverage,
            companion_occupied=occupied, companion_residue=residue,
        )

    return WriteSequenceResult(
        ok=True, written=written, removed=removed, out_of_coverage=out_of_coverage,
        companion_occupied=occupied, companion_residue=residue,
    )


def _synthesize_state(recorded: dict[str, str | None]) -> State:
    """Build the one-row ``State`` :func:`safety.classify` reads.

    A null-sha entry is recorded with the ``"sha"`` key omitted rather than
    present-and-``None`` — see plan.md's Design decisions: ``dict[str, str]``
    carrying ``None`` is a type lie that survives only through
    ``no_strict_optional`` and an ``Any`` hole.
    """
    files: dict[str, dict[str, str]] = {
        path: ({"sha": sha} if sha is not None else {})
        for path, sha in recorded.items()
    }
    return State(packs={("sync", "sync"): PackState(installed_version="0", files=files)})


def _safe_scalar(field: str, value: str | None, rejections: list[str]) -> str | None:
    """Return *value* when it passes the bounded terminal-safe scalar check.

    Spec AC-0012: every value this command renders that it did not itself
    author, whatever its origin, is routed through this gate before it
    reaches stdout, stderr, or the ``--format json`` document. A rejection
    names the field and the reason and never reproduces the value — so
    ``rejections`` accumulates a fixed message, not *value* itself.

    ``value=None`` is not a hostile value (an absent pin is reported as
    "absent", not rejected), so it passes through unchanged.
    """
    if value is None:
        return None
    if _is_safe_recipe_text(value):
        return value
    rejections.append(
        f"rejected {field}: value failed the terminal-safe scalar check"
    )
    return None


def _parse_decline_reason(reason: str) -> tuple[str, str] | None:
    """Recover ``(path, token)`` from one ``_plan_stale_owned_paths`` reason.

    Mirrors that function's fixed ``f"skipped removal of {rel_path!r}:
    {token}"`` shape. Parsing failure returns ``None`` so the caller fails
    closed to "uncompared" rather than misreporting a decided verdict.
    """
    prefix = "skipped removal of "
    if not reason.startswith(prefix) or ": " not in reason:
        return None
    path_repr, _, token = reason[len(prefix) :].rpartition(": ")
    if not path_repr:
        return None
    try:
        path = ast.literal_eval(path_repr)
    except (ValueError, SyntaxError):
        return None
    return (path, token) if isinstance(path, str) else None


def _screen_recorded_path(target: Path, path: str) -> bool:
    """Screen a recorded-and-planned *path* before it reaches `safety.classify`.

    Security finding 2 / adversarial finding 2: `classify`'s own on-disk read
    (`safety.sha256_file`) is a raw `path.open("rb")` — it follows a symlink
    to its destination's bytes, hashes a hard link, and raises
    `IsADirectoryError` when a directory sits where a recorded regular file
    is expected. Screening through the declared `file_safety` confinement
    helper first, rather than reimplementing any part of the Tier contract,
    keeps `safety.classify` the single Tier implementation (§ Always do,
    § Never do) while refusing every one of those shapes before it is ever
    reached.

    A path with **no** on-disk entry at all is not screened here and always
    passes: `classify`'s own "absent on disk -> Tier-1 (about to write)"
    resolution depends on being able to tell a truly absent path apart from
    a present-but-unsafe one, and only a present entry can be unsafe. A
    dangling symlink is a *present* entry (its own `lstat` succeeds) even
    though `Path.exists()` reports it absent, so it is screened and refused
    like every other symlink rather than silently read as "absent".
    """
    full = target / path
    try:
        full.lstat()
    except OSError:
        return True
    try:
        sha256_confined_regular_file(target, full)
    except UnsafeContentError:
        return False
    return True


def _underivable_condition(target: Path, source: Path) -> str | None:
    """Return spec AC-0009's underivable-selection condition, or ``None``.

    Every condition AC-0009 enumerates is checked here, before any call that
    would resolve an absent or discarded selection to the source's full
    contents (``select_packs``/``_select_profiles`` widen to "every pack"
    when passed ``None`` — exactly the widening AC-0009 forbids).
    """
    state_path = target / _OWNERSHIP_STATE_FILE
    if not state_path.exists() and not state_path.is_symlink():
        return "no state file at the target"

    diagnostics: list[str] = []
    raw_state = _load_ownership_state(target, diagnostics)
    if raw_state is None:
        return "the ownership-state loader could not return a state object"

    if "recipe" not in raw_state:
        return "the recorded state has no recipe key"

    raw_recipe = raw_state["recipe"]
    if not isinstance(raw_recipe, dict):
        return "the recorded recipe is not a JSON object"

    recipe = _load_self_host_recipe(raw_state, source, diagnostics)
    if recipe is None:
        # Every condition under which _load_self_host_recipe itself returns
        # None (raw_state is None, no "recipe" key, recipe not a dict) is
        # already handled above; reached only if that contract changes.
        return "the recorded recipe could not be read"

    if recipe.packs is None and recipe.profiles is None:
        if "packs" in raw_recipe or "profiles" in raw_recipe:
            return "the recorded packs or profiles selection was discarded"
        return "the recorded recipe carries neither packs nor profiles"

    return None


def _classify_planned_paths(
    target: Path,
    old_state: dict[str, Any] | None,
    planned_paths: set[str],
    rejections: list[str],
) -> tuple[dict[str, int], list[tuple[str, str, str | None]]]:
    """Classify every recorded and planned path, reconciling the seven counts.

    Walks the raw ``managed_paths`` array exactly once: every entry lands in
    exactly one bucket, so a silently dropped entry breaks the
    ``compared + uncompared`` identity rather than passing it by
    construction (spec AC-0016).

    Spec AC-0012: a recorded path (``managed_paths``) and a source-tree entry
    name (``planned_paths`` — a path the replay planned from the *source*,
    not the recorded state) are both unauthored input, so both are routed
    through the terminal-safe check before they can reach a printed row;
    a rejection is appended to *rejections* by field name only.
    """
    counts: dict[str, int] = {
        "would_update": 0,
        "would_companion": 0,
        "untouched": 0,
        "would_remove": 0,
        "schema_1_inert": 0,
        "compared": 0,
        "uncompared": 0,
    }
    rows: list[tuple[str, str, str | None]] = []

    managed_paths_raw = (old_state or {}).get("managed_paths", [])
    if not isinstance(managed_paths_raw, list):
        managed_paths_raw = []

    migrated = _migrate_managed_paths(old_state or {})
    # Entries _migrate_managed_paths drops outright (not a dict/str, or a
    # dict with no "path" key) never reach either bucket below.
    counts["uncompared"] += len(managed_paths_raw) - len(migrated)

    recorded: dict[str, str | None] = {}
    for entry in migrated:
        path = entry.get("path", "")
        sha = entry.get("sha256")
        if not _is_safe_recipe_text(path):
            counts["uncompared"] += 1
            rejections.append(
                "rejected managed_paths: entry failed the terminal-safe "
                "scalar check"
            )
            continue
        if path in recorded:
            counts["uncompared"] += 1
            continue
        recorded[path] = sha if isinstance(sha, str) else None

    # `planned_paths` names come from the replayed *source* tree, not the
    # recorded state — a source-tree entry name is unauthored input too
    # (spec AC-0012), so it is filtered the same way before it can reach a
    # printed row.
    safe_planned_paths: set[str] = set()
    for path in planned_paths:
        if _is_safe_recipe_text(path):
            safe_planned_paths.add(path)
        else:
            rejections.append(
                "rejected planned_paths: entry failed the terminal-safe "
                "scalar check"
            )
    planned_paths = safe_planned_paths

    state = _synthesize_state(recorded)
    stale_paths = [path for path in recorded if path not in planned_paths]

    for path in sorted(planned_paths):
        # Screen only when `path` is recorded — that is exactly when
        # `classify` would otherwise touch the filesystem (a path outside
        # `state.projected_paths()` returns Tier-3 with no on-disk read at
        # all, so screening it would only manufacture a false
        # `path-confinement-refused` for an ordinary untouched entry).
        if path in recorded and not _screen_recorded_path(target, path):
            counts["uncompared"] += 1
            continue
        tier = classify(path, target, state)
        if tier is Tier.TIER_3:
            counts["untouched"] += 1
            rows.append((path, "untouched", None))
            continue
        counts["compared"] += 1
        if tier is Tier.TIER_1:
            counts["would_update"] += 1
            rows.append((path, "would-update", None))
        elif recorded.get(path) is None:
            counts["schema_1_inert"] += 1
            rows.append((path, "schema-1-inert", None))
        else:
            # `safety.companion_path` is a computed value derived from an
            # already-checked *path*, but spec AC-0012 is origin-agnostic —
            # it is routed through the same gate at its own render site
            # rather than trusted because its input already passed.
            companion = _safe_scalar(
                "companion_path", str(companion_path(Path(path))), rejections
            )
            counts["would_companion"] += 1
            rows.append((path, "would-companion", companion))

    if stale_paths:
        removable, reasons = _plan_stale_owned_paths(
            target, old_state or {}, planned_paths
        )
        removable_set = set(removable)
        decline_tokens: dict[str, str] = {}
        for reason in reasons:
            parsed = _parse_decline_reason(reason)
            if parsed is not None:
                decline_tokens[parsed[0]] = parsed[1]
        for path in stale_paths:
            if path in removable_set:
                counts["compared"] += 1
                counts["would_remove"] += 1
                rows.append((path, "would-remove", None))
                continue
            token = decline_tokens.get(path)
            if token is None or token in _UNDECIDED_DECLINE_TOKENS:
                counts["uncompared"] += 1
            else:
                counts["compared"] += 1

    return counts, rows


def _pack_toml_from_replay(name: str, file_bytes: dict[str, bytes]) -> dict[str, Any] | None:
    """Parse the source's planned ``pack.toml`` for *name*, or ``None``.

    ``file_bytes`` is the replay's already-confined read (see
    ``_collect_bytes`` in ``initialise_self_hosted.py``); this parses it
    without a second filesystem read.
    """
    content = file_bytes.get(f"packs/{name}/pack.toml")
    if content is None:
        return None
    try:
        return tomllib.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None


def check_adapter_contract_gate(
    pack_names: list[str], file_bytes: dict[str, bytes]
) -> int | None:
    """Refuse when a selected pack's adapter-contract major differs from the
    CLI's own (spec AC-0019).

    Reuses ``check_spec_version_gate`` — the existing uniform-refusal gate
    every other pack-manifest consumer calls — rather than re-implementing
    the major-version comparison. Returns the gate's refusal code, or
    ``None`` when every selected pack's major agrees (or declares none).
    """
    for name in pack_names:
        pack_toml = _pack_toml_from_replay(name, file_bytes)
        if pack_toml is None:
            continue
        gate = check_spec_version_gate(pack_toml)
        if gate is not None:
            return gate
    return None


def _read_baseline_pack_toml(target: Path, name: str) -> dict[str, Any] | None:
    """Read the derived tree's own copy of *name*'s manifest, or ``None``.

    Goes through the declared ``file_safety`` confinement helper rather than
    an inline path check (spec AC-0020) — a new pack the derived tree does
    not yet carry has no baseline to compare, which reads the same as any
    other confinement refusal: no signal.
    """
    baseline_path = target / "packs" / name / "pack.toml"
    try:
        baseline_bytes = read_confined_regular_file(target, baseline_path)
    except UnsafeContentError:
        return None
    try:
        return tomllib.loads(baseline_bytes.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None


def compatibility_warnings(
    target: Path,
    pack_names: list[str],
    file_bytes: dict[str, bytes],
    rejections: list[str],
) -> list[str]:
    """Advisory rows for spec AC-0018 — warn-only, never change the exit code.

    Compares each selected pack's ``[pack] version`` and
    ``[pack.adapter-contract] version`` against the derived tree's own copy
    of that pack's manifest (read through :func:`_read_baseline_pack_toml`),
    and evaluates ``[pack.dependencies]`` ``required``/``conflicts`` edges
    against the replay's resolved selection. One row per signal; a signal
    that is absent contributes nothing.

    Every compared value here is unauthored — a source or baseline
    manifest's own text (spec AC-0012) — so a hostile one is reported to
    *rejections* by field name rather than embedded in an advisory line.
    """
    selected = set(pack_names)
    warnings: list[str] = []
    source_tomls: dict[str, dict[str, Any]] = {}

    for name in pack_names:
        source_toml = _pack_toml_from_replay(name, file_bytes)
        if source_toml is None:
            continue
        source_tomls[name] = source_toml

        baseline_toml = _read_baseline_pack_toml(target, name)
        if baseline_toml is None:
            continue

        source_pack = source_toml.get("pack", {})
        baseline_pack = baseline_toml.get("pack", {})
        if not isinstance(source_pack, dict) or not isinstance(baseline_pack, dict):
            continue

        source_version = source_pack.get("version")
        baseline_version = baseline_pack.get("version")
        if isinstance(source_version, str) and isinstance(baseline_version, str):
            safe_source_version = _safe_scalar(
                "pack_version", source_version, rejections
            )
            safe_baseline_version = _safe_scalar(
                "pack_version", baseline_version, rejections
            )
            if (
                safe_source_version is not None
                and safe_baseline_version is not None
                and safe_source_version != safe_baseline_version
            ):
                warnings.append(
                    f"advisory: pack version differs for {name!r} — derived "
                    f"tree carries {safe_baseline_version!r}, source "
                    f"declares {safe_source_version!r}"
                )

        source_contract = source_pack.get("adapter-contract", {})
        baseline_contract = baseline_pack.get("adapter-contract", {})
        source_contract_version = (
            source_contract.get("version") if isinstance(source_contract, dict) else None
        )
        baseline_contract_version = (
            baseline_contract.get("version")
            if isinstance(baseline_contract, dict)
            else None
        )
        safe_source_contract_version = (
            _safe_scalar("adapter_contract_version", source_contract_version, rejections)
            if isinstance(source_contract_version, str)
            else None
        )
        safe_baseline_contract_version = (
            _safe_scalar("adapter_contract_version", baseline_contract_version, rejections)
            if isinstance(baseline_contract_version, str)
            else None
        )
        source_contract_hostile = (
            isinstance(source_contract_version, str)
            and safe_source_contract_version is None
        )
        baseline_contract_hostile = (
            isinstance(baseline_contract_version, str)
            and safe_baseline_contract_version is None
        )
        # Either side may omit `[pack.adapter-contract]` entirely — the field
        # is optional (unlike `[pack] version`), so "differs" has to compare
        # against an absent baseline too, not only a baseline that also
        # declares one. A hostile value on either side is already reported
        # to *rejections* above; the comparison itself is skipped rather
        # than risking a display built from a value that failed the check.
        if (
            not source_contract_hostile
            and not baseline_contract_hostile
            and safe_source_contract_version != safe_baseline_contract_version
            and (
                isinstance(safe_source_contract_version, str)
                or isinstance(safe_baseline_contract_version, str)
            )
        ):
            baseline_display = (
                safe_baseline_contract_version
                if isinstance(safe_baseline_contract_version, str)
                else "absent"
            )
            source_display = (
                safe_source_contract_version
                if isinstance(safe_source_contract_version, str)
                else "absent"
            )
            warnings.append(
                f"advisory: adapter-contract version differs for {name!r} — "
                f"derived tree carries {baseline_display!r}, source "
                f"declares {source_display!r}"
            )

    for name, source_toml in source_tomls.items():
        deps = source_toml.get("pack", {}).get("dependencies", {})
        if not isinstance(deps, dict):
            continue

        # Security finding 5: `required`/`conflicts` is a valid TOML scalar
        # (e.g. `required = 1`) as well as an array. Iterating an
        # unguarded non-list container raises `TypeError` — an uncaught
        # exception AC-0014 forbids deciding the process exit status. A
        # malformed container is reported by field name into *rejections*
        # and contributes no warning row; it must never refuse the run
        # (AC-0013's dry-run success row) or move the exit code (AC-0018).
        required = deps.get("required")
        if required is not None and not isinstance(required, list):
            rejections.append(
                "rejected dependency_required: value is not an array"
            )
            required = []
        for entry in required or []:
            if not isinstance(entry, dict):
                continue
            dep_name = entry.get("pack")
            if not isinstance(dep_name, str):
                continue
            safe_dep_name = _safe_scalar("dependency_edge_name", dep_name, rejections)
            if safe_dep_name is not None and safe_dep_name not in selected:
                warnings.append(
                    f"advisory: pack {name!r} declares a required dependency on "
                    f"{safe_dep_name!r}, which the resolved selection does not include"
                )

        conflicts = deps.get("conflicts")
        if conflicts is not None and not isinstance(conflicts, list):
            rejections.append(
                "rejected dependency_conflicts: value is not an array"
            )
            conflicts = []
        for entry in conflicts or []:
            if not isinstance(entry, dict):
                continue
            dep_name = entry.get("pack")
            if not isinstance(dep_name, str):
                continue
            safe_dep_name = _safe_scalar("dependency_edge_name", dep_name, rejections)
            if safe_dep_name is not None and safe_dep_name in selected:
                warnings.append(
                    f"advisory: pack {name!r} declares a conflict with "
                    f"{safe_dep_name!r}, which the resolved selection includes"
                )

    return warnings


def _compare_recorded_entry(target: Path, entry: object) -> bool | None:
    """One `--check --compare-tree` comparison for a single raw ``managed_paths``
    entry. Returns ``True`` when the on-disk content differs from the
    recorded digest, ``False`` when it matches, and ``None`` when the entry
    could not be compared at all — spec AC-0013's "any recorded path could
    not be compared" reads this ``None``.

    Every malformed shape (not a dict, no ``path``, no ``sha256``, a hostile
    path) and every confinement failure (escaping, hard-linked, non-regular,
    a reparse point, or simply absent) is folded into the same ``None`` —
    compare-tree's table row does not distinguish *why* an entry could not be
    compared, only that it could not.
    """
    if not isinstance(entry, dict):
        return None
    rel_path = entry.get("path")
    recorded_sha = entry.get("sha256")
    if (
        not isinstance(rel_path, str)
        or not rel_path
        or not _is_safe_recipe_text(rel_path)
        or not isinstance(recorded_sha, str)
        or not recorded_sha
    ):
        return None
    try:
        on_disk_sha = sha256_confined_regular_file(target, target / rel_path)
    except UnsafeContentError:
        return None
    return on_disk_sha != recorded_sha


def _report_check_result(
    result: str,
    *,
    attributed: bool,
    source_raw: str,
    fmt: str,
    code: int,
) -> int:
    """Report a `--check` answer that is not a refusal: "current" or "differs".

    Mirrors `_refuse`'s shape — the source is named only under `attributed`,
    and only after the same terminal-safe check every other unauthored value
    passes (spec AC-0002, AC-0012) — so a `--check` answer carries the same
    guarantees as every other output this command renders.
    """
    rejections: list[str] = []
    safe_source = _safe_scalar("source", source_raw, rejections) if attributed else None
    if fmt == "json":
        doc: dict[str, Any] = {"ok": True, "result": result}
        if attributed:
            if safe_source is not None:
                doc["source"] = safe_source
            else:
                doc["rejections"] = rejections
        print(json.dumps(doc, indent=2))
    else:
        print(f"check: {result}")
        if attributed:
            if safe_source is not None:
                print(f"  source: {safe_source}")
            else:
                for line in rejections:
                    print(f"  {line}")
    return code


def _check_digest_only(
    target: Path,
    *,
    resolved_archive_sha256: str | None,
    attributed: bool,
    source_raw: str,
    fmt: str,
) -> int:
    """Spec AC-0013's `--check`, no `--compare-tree`, rows: compare the
    recorded pin's `archive_sha256` against the resolved source's own
    verified digest. A local-path or `git+https://` source never affords one,
    so it cannot-answers before the recorded pin is even read.
    """
    if resolved_archive_sha256 is None:
        return _refuse(
            "the resolved source affords no verified archive_sha256",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_CANNOT_ANSWER,
        )

    diagnostics: list[str] = []
    raw_state = _load_ownership_state(target, diagnostics)
    pin = raw_state.get("pin") if isinstance(raw_state, dict) else None
    recorded = pin.get("archive_sha256") if isinstance(pin, dict) else None

    if not isinstance(recorded, str) or _HEX64.fullmatch(recorded) is None:
        return _refuse(
            "the recorded archive_sha256 is absent, or is not a "
            "64-character lowercase hex string",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_CANNOT_ANSWER,
        )

    if recorded == resolved_archive_sha256:
        return _report_check_result(
            "current",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_SUCCESS,
        )
    return _report_check_result(
        "differs",
        attributed=attributed,
        source_raw=source_raw,
        fmt=fmt,
        code=_DIFFERENCE,
    )


def _check_compare_tree(
    target: Path,
    *,
    attributed: bool,
    source_raw: str,
    fmt: str,
) -> int:
    """Spec AC-0013's `--check --compare-tree` rows, plus this mode's share of
    the recorded-path-container-not-an-array row. The resolved source is
    never read here — see plan.md's Follow-ons: `--check --compare-tree`
    answers entirely from the recorded state and the target tree.
    """
    diagnostics: list[str] = []
    raw_state = _load_ownership_state(target, diagnostics)
    container: object = (
        raw_state.get("managed_paths", []) if isinstance(raw_state, dict) else []
    )

    if not isinstance(container, list):
        return _refuse(
            "the recorded-path container is not an array",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_CANNOT_ANSWER,
        )
    if not container:
        return _refuse(
            "the recorded path set is empty",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_CANNOT_ANSWER,
        )

    any_differs = False
    for entry in container:
        outcome = _compare_recorded_entry(target, entry)
        if outcome is None:
            return _refuse(
                "a recorded path could not be compared",
                attributed=attributed,
                source_raw=source_raw,
                fmt=fmt,
                code=_CANNOT_ANSWER,
            )
        any_differs = any_differs or outcome

    return _report_check_result(
        "differs" if any_differs else "current",
        attributed=attributed,
        source_raw=source_raw,
        fmt=fmt,
        code=_DIFFERENCE if any_differs else _SUCCESS,
    )


def _resolve_source(
    source_uri: str,
) -> tuple[Path, str, str | None, str | None, Callable[[], None] | None]:
    """Dispatch *source_uri* to its resolver.

    Returns ``(path, fidelity_token, archive_sha256, source_revision,
    cleanup)``. ``cleanup`` is a zero-argument callable that removes the
    extracted archive directory a digest-bearing fetch handed this caller
    ownership of, or ``None`` when there is nothing to clean up (a local
    path is never extracted; a ``git+https://`` fetch self-cleans via
    ``atexit`` inside ``resolve_catalogue``, so this caller owns no
    directory for that form either).
    """
    if source_uri.startswith(_DIGEST_BEARING_PREFIXES):
        result = fetch_catalogue_archive_with_provenance(source_uri)
        token = (
            "digest-publisher-asserted"
            if source_uri.startswith("catalogue+https://")
            else "digest-adopter-pinned"
        )
        extracted = result.path

        def _cleanup() -> None:
            shutil.rmtree(str(extracted), ignore_errors=True)

        return extracted, token, result.archive_sha256, result.source_revision, _cleanup

    path = resolve_catalogue(source_uri)
    token = "git-tls" if source_uri.startswith("git+https://") else "local-path"
    return path, token, None, None, None


def _plan_document(
    *,
    target: Path,
    dry_run: bool,
    check: bool,
    fidelity_token: str,
    archive_sha256: str | None,
    source_revision: str | None,
    attribution: str,
    tooling: str,
    guides: str,
    source_raw: str,
    attributed: bool,
    pack_names: list[str],
    profile_names: list[str],
    summary: dict[str, int],
    verdict_rows: list[tuple[str, str, str | None]],
    compatibility: list[str],
    violations: int,
    rejections: list[str],
) -> dict[str, Any]:
    """Build the plan document, following ``upgrade._build_json_doc``'s
    ``summary``-carrying shape and vocabulary.

    Spec AC-0012: ``archive_sha256``, ``source_revision``, ``target``, every
    ``pack_names``/``profile_names`` entry, and — under ``attributed`` — the
    source URI are all unauthored (resolved from a remote document, the
    replayed source tree, or the adopter's own ``--target``/``--source``
    flags rather than written by this command), so each is routed through
    the terminal-safe check here, at the one place they are assembled for
    rendering.

    Spec AC-0005: ``violations`` (the identity leak check's count) is
    carried into the document so both this table and the ``--format json``
    surface report it, not only the exit code it also selects.
    """
    safe_archive_sha256 = _safe_scalar("archive_sha256", archive_sha256, rejections)
    safe_source_revision = _safe_scalar("source_revision", source_revision, rejections)
    safe_target = _safe_scalar("target", str(target), rejections)
    safe_pack_names = [
        name for name in pack_names
        if _safe_scalar("packs", name, rejections) is not None
    ]
    safe_profile_names = [
        name for name in profile_names
        if _safe_scalar("profiles", name, rejections) is not None
    ]
    doc: dict[str, Any] = {
        "command": "catalogue sync",
        "target": safe_target,
        "dry_run": dry_run,
        "check": check,
        "fidelity": fidelity_token,
        "pin": {
            "archive_sha256": safe_archive_sha256,
            "source_revision": safe_source_revision,
        },
        "modes": {
            "attribution": attribution,
            "tooling": tooling,
            "guides": guides,
            "provenance": "flags-and-defaults",
        },
        "packs": safe_pack_names,
        "profiles": safe_profile_names,
        "summary": summary,
        "violations": violations,
        "compatibility": compatibility,
        "verdicts": [
            {
                "path": path,
                "verdict": verdict,
                **({"companion": companion} if companion else {}),
            }
            for path, verdict, companion in verdict_rows
        ],
    }
    if attributed:
        safe_source = _safe_scalar("source", source_raw, rejections)
        if safe_source is not None:
            doc["source"] = safe_source
    doc["rejections"] = list(rejections)
    return doc


def _render_plan(doc: dict[str, Any], *, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(doc, indent=2))
        return

    modes = doc["modes"]
    lines = [
        f"fidelity: {doc['fidelity']}",
        "modes: attribution={attribution} tooling={tooling} guides={guides} "
        "(from {provenance})".format(**modes),
        f"archive_sha256: {doc['pin']['archive_sha256'] or 'absent'}",
        f"source_revision: {doc['pin']['source_revision'] or 'absent'}",
    ]
    if "source" in doc:
        lines.append(f"source: {doc['source']}")
    lines.append(f"violations: {doc['violations']}")
    lines.append("packs: " + (", ".join(doc["packs"]) or "(none)"))
    lines.append("profiles: " + (", ".join(doc["profiles"]) or "(none)"))
    for line in doc.get("rejections", []):
        lines.append(line)
    for line in doc.get("compatibility", []):
        lines.append(line)
    for row in doc["verdicts"]:
        line = f"{row['verdict']}: {row['path']}"
        if "companion" in row:
            line += f" -> companion {row['companion']}"
        lines.append(line)
    counts = doc["summary"]
    lines.append(
        "counts: would-update={would_update} would-companion={would_companion} "
        "untouched={untouched} would-remove={would_remove} "
        "schema-1-inert={schema_1_inert} compared={compared} "
        "uncompared={uncompared}".format(**counts)
    )
    print("\n".join(lines))


def _refuse(
    reason: str,
    *,
    attributed: bool,
    source_raw: str,
    fmt: str,
    code: int,
) -> int:
    """Report a resolution or verification refusal.

    Never reproduces the underlying exception text: it may embed the raw
    source value (a local path is, after all, its own URI), which spec
    AC-0002 forbids surfacing outside ``attributed`` mode. Only a fixed
    reason and, when attributed, the source itself are ever printed — and
    even then only once it passes AC-0012's terminal-safe check, same as
    every other unauthored value this command renders.
    """
    rejections: list[str] = []
    safe_source = _safe_scalar("source", source_raw, rejections) if attributed else None
    if fmt == "json":
        doc: dict[str, Any] = {"ok": False, "error": reason}
        if attributed:
            if safe_source is not None:
                doc["source"] = safe_source
            else:
                doc["rejections"] = rejections
        print(json.dumps(doc, indent=2))
    else:
        print(f"error: {reason}", file=sys.stderr)
        if attributed:
            if safe_source is not None:
                print(f"  source: {safe_source}", file=sys.stderr)
            else:
                for line in rejections:
                    print(f"  {line}", file=sys.stderr)
    return code


def _consent_gate(
    *,
    yes: bool,
    attributed: bool,
    source_raw: str,
    fidelity_token: str,
) -> bool:
    """AC-0031 — ask an operator for consent before the apply path's first write.

    Composes ``commands._common.confirm_or_refuse`` — the shared
    confirm/refuse/``--yes`` mechanics ``uninstall``, ``install --force`` and
    ``upgrade`` already share (plan.md's Cut-before-adding search: an adequate
    repository solution for the yes/terminal/EOF mechanics already exists, so
    this function adds only the two prompt obligations apply introduces) —
    with what the prompt itself must and must not say: AC-0072 names the
    source fidelity on every prompt, and AC-0050 forbids naming the source URI
    outside ``attributed`` mode. *source_raw* is unauthored input, so AC-0049
    routes it through the terminal-safe check first; a value that fails is
    reported by field name and reason, never reproduced.

    Returns ``True`` on an affirmative reply or *yes*. Returns ``False`` on a
    negative reply, an end-of-input, or an absent terminal with no *yes* —
    ``confirm_or_refuse``'s non-TTY branch refuses before ever calling
    ``input()``, so "end-of-input" and "no terminal" reach the same decision
    without a separate branch here.

    Reads only *yes* and the terminal — never a recorded value. Passing one in
    is the seam plan.md's "Consent drift" risk names: it would reopen phase
    2's modes-from-flags invariant (AC-0048), so this function takes no state
    argument at all.
    """
    rejections: list[str] = []
    safe_source = (
        _safe_scalar("source", source_raw, rejections) if attributed else None
    )
    lines = [f"fidelity: {fidelity_token}"]
    if attributed:
        if safe_source is not None:
            lines.append(f"source: {safe_source}")
        else:
            lines.extend(rejections)
    lines.append("Apply this plan? [y/N] ")
    return confirm_or_refuse(
        yes=yes,
        question="\n".join(lines),
        refuse_message=(
            "catalogue sync: refusing to apply without a terminal; use --yes"
        ),
        abort_message="catalogue sync: aborted; no changes made",
    )


def _run_dry_run(
    *,
    target: Path,
    source_path: Path,
    fidelity_token: str,
    archive_sha256: str | None,
    source_revision: str | None,
    attribution: str,
    tooling: str,
    guides: str,
    dry_run: bool,
    attributed: bool,
    source_raw: str,
    fmt: str,
) -> int:
    """Spec AC-0013's `--dry-run` rows: no recorded selection derivable, the
    recorded-path container not an array, source verification failure, the
    identity leak check, the adapter-contract gate, and — reaching none of
    those — a printed plan and the success or difference code.
    """
    cfg = SelfHostedInitConfig(
        target=target,
        source=source_path,
        tooling=tooling,
        attribution=attribution,
        guides=guides,
        dry_run=dry_run,
    )

    condition = _underivable_condition(target, source_path)
    if condition is not None:
        return _refuse(
            f"no recorded selection is derivable: {condition}",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_CANNOT_ANSWER,
        )

    # Spec AC-0013/AC-0014: a recorded `managed_paths` that is not an array
    # cannot be interpreted at all — distinct from a malformed *entry* inside
    # an otherwise-array container, which AC-0016 routes to "uncompared".
    # Checked here, before any plan can be printed, rather than left to
    # `_classify_planned_paths`'s own defensive coercion to an empty list.
    diagnostics: list[str] = []
    raw_state = _load_ownership_state(target, diagnostics)
    managed_paths_container: object = (
        raw_state.get("managed_paths", []) if isinstance(raw_state, dict) else []
    )
    if not isinstance(managed_paths_container, list):
        return _refuse(
            "the recorded-path container is not an array",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_CANNOT_ANSWER,
        )

    try:
        replay = replay_derivation(cfg, interactive=False)
    except ReplayError:
        return _refuse(
            "source could not be verified",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_CANNOT_ANSWER,
        )

    # Spec AC-0019 — a selected pack's adapter-contract major differing from
    # the CLI's own refuses uniformly, via the same gate every other pack-
    # manifest consumer calls. Unlike AC-0018's warnings below, this changes
    # the exit code and prints no plan.
    gate_code = check_adapter_contract_gate(replay.pack_names, replay.file_bytes)
    if gate_code is not None:
        return gate_code

    resolved_cfg = replay.config
    planned_paths = set(replay.file_bytes.keys())
    # One shared rejections list: every value this command did not itself
    # author — a recorded path, a source-tree entry name, a manifest's own
    # version string, the resolved digest/revision, and the source URI
    # itself — is routed through the terminal-safe check before it can
    # reach any output surface (spec AC-0012), and every rejection lands
    # here regardless of which stage produced it.
    rejections: list[str] = []
    summary_counts, verdict_rows = _classify_planned_paths(
        target, replay.old_state, planned_paths, rejections
    )
    compatibility = compatibility_warnings(
        target, replay.pack_names, replay.file_bytes, rejections
    )
    doc = _plan_document(
        target=target,
        dry_run=dry_run,
        check=False,
        fidelity_token=fidelity_token,
        archive_sha256=archive_sha256,
        source_revision=source_revision,
        attribution=resolved_cfg.attribution,
        tooling=resolved_cfg.tooling,
        guides=resolved_cfg.guides,
        source_raw=source_raw,
        attributed=attributed,
        pack_names=replay.pack_names,
        profile_names=replay.profile_names,
        summary=summary_counts,
        verdict_rows=verdict_rows,
        compatibility=compatibility,
        violations=len(replay.violations),
        rejections=rejections,
    )
    _render_plan(doc, fmt=fmt)
    return _DIFFERENCE if replay.violations else _SUCCESS


def run(args: argparse.Namespace) -> int:
    target_raw: str = args.target
    source_raw: str = args.source
    dry_run = bool(args.dry_run)
    check = bool(args.check)
    compare_tree = bool(args.compare_tree)
    attribution: str = args.attribution or "white-label"
    tooling: str = args.tooling or "external"
    guides: str = args.guides_mode or "selected"
    fmt: str = args.format
    # Security finding 1 (owner decision 2026-09-17): `_is_attributed` is the
    # single attribution gate. A second, independently-shaped check (e.g. an
    # inline `attribution == "attributed"` equality) is a defect even when it
    # currently agrees with this one, because nothing then constrains the two
    # to keep agreeing as either side changes. `target`/`source` are the only
    # required fields; the ones this decision actually reads —
    # `attribution` — are flag-derived, never the recorded recipe (AC-0003).
    attribution_cfg = SelfHostedInitConfig(
        target=Path(target_raw),
        source=Path(source_raw),
        tooling=tooling,
        attribution=attribution,
        guides=guides,
        dry_run=dry_run,
    )
    attributed = _is_attributed(attribution_cfg)

    # Rendering is bounded on all three channels (stdout, stderr, and the
    # `--format json` document) from the first refusal onward — every
    # branch below reaches `_refuse`, never a bespoke print, so a malformed
    # invocation gets the same JSON-aware shape as every other refusal.
    #
    # An omitted `--source`, and neither or both of `--dry-run`/`--check`,
    # never reach this function at all: both are `argparse` requirements
    # (`--source` is `required=True`; the two flags form a `required=True`
    # mutually exclusive group), so `argparse` itself exits 2 — spec
    # AC-0013's malformed code — before `run()` is ever called.
    target_path = Path(target_raw)
    if target_path.is_symlink():
        return _refuse(
            "rejected target: value is a symlink. Provide a direct path.",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_MALFORMED,
        )
    target = target_path.resolve()

    if compare_tree and not check:
        return _refuse(
            "--compare-tree requires --check",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_MALFORMED,
        )

    cleanup: Callable[[], None] | None = None
    try:
        source_path, fidelity_token, archive_sha256, source_revision, cleanup = (
            _resolve_source(source_raw)
        )
    except CatalogueError:
        return _refuse(
            "source could not be resolved",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_CANNOT_ANSWER,
        )
    except Exception:
        # Spec AC-0014: a resolver exception is a named row too — never an
        # uncaught traceback deciding the process exit status. Every
        # resolver-specific failure this module knows about is already
        # `CatalogueError`; anything else is still "could not be resolved"
        # from this command's point of view.
        return _refuse(
            "source could not be resolved",
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
            code=_CANNOT_ANSWER,
        )

    try:
        if check:
            if compare_tree:
                return _check_compare_tree(
                    target,
                    attributed=attributed,
                    source_raw=source_raw,
                    fmt=fmt,
                )
            return _check_digest_only(
                target,
                resolved_archive_sha256=archive_sha256,
                attributed=attributed,
                source_raw=source_raw,
                fmt=fmt,
            )
        return _run_dry_run(
            target=target,
            source_path=source_path,
            fidelity_token=fidelity_token,
            archive_sha256=archive_sha256,
            source_revision=source_revision,
            attribution=attribution,
            tooling=tooling,
            guides=guides,
            dry_run=dry_run,
            attributed=attributed,
            source_raw=source_raw,
            fmt=fmt,
        )
    finally:
        if cleanup is not None:
            cleanup()
