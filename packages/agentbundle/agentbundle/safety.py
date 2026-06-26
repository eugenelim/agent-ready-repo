"""Tier-1/2/3 file-safety primitives, path-jail enforcement, content hashing.

The Tier contract is owned by the sibling `distribution-adapters` spec.
Here we implement it:

  - Tier-1 — adapter-contract-projected; SHA in state matches on-disk.
            The CLI may write or overwrite.
  - Tier-2 — adapter-contract-projected; on-disk SHA differs from state
            (adopter has edited the file since install). The CLI never
            overwrites; it drops a `<stem>.upstream.<ext>` companion next
            to the original instead.
  - Tier-3 — every path the state file does not record under any pack.
            Read-only to the CLI.

`write_jailed` is the only sanctioned write call. Every command that
writes routes through it so the path-jail check (refusal of any
`../`-style escape from the configured root) is non-optional.
"""

from __future__ import annotations

import enum
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterable

from agentbundle.config import State


class Tier(enum.Enum):
    TIER_1 = "tier-1"
    TIER_2 = "tier-2"
    TIER_3 = "tier-3"


class PathJailError(ValueError):
    """Raised when a write would land outside the configured root."""


class WriteError(OSError):
    """Raised when an otherwise-jailed write fails due to OS errors —
    typically `PermissionError` on a read-only filesystem, `OSError` on
    a full disk, or `NotADirectoryError` when a parent exists as a file.

    Distinct from `PathJailError` so callers can render different one-line
    stderr messages: jail violations indicate a malicious or buggy pack,
    write errors indicate environment problems on the adopter side.
    """


# ---------------------------------------------------------------------------
# Content hashing
# ---------------------------------------------------------------------------


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Tier classification
# ---------------------------------------------------------------------------


def classify(relpath: str, root: Path, state: State) -> Tier:
    """Classify `relpath` (relative to `root`) per the Tier contract.

    Resolution:
      1. If `relpath` is in `state.projected_paths()`:
         - If the file is absent on disk → treat as Tier-1 (about to write).
         - If on-disk SHA == state SHA  → Tier-1.
         - Else                        → Tier-2 (adopter has edited).
      2. Otherwise → Tier-3.

    The "absent on disk → Tier-1" rule is important for `install` and
    `render` after a Tier-1 file was deleted by the adopter — re-installing
    rewrites it (it's adapter-contract space; the bundle owns it).

    **Carve-out for first-install paths:** `commands/install._classify_for_install`
    deliberately bypasses this function for the install command's own walk
    because step 2 here ("not in state → Tier-3") would mark every path
    in a fresh projection as Tier-3 on a first install, suppressing every
    write. The install command's contract is different — every path in
    its incoming projection is adapter-contract space, and the classifier
    only decides overwrite-vs-companion. Do not "fix" this function to do
    what install needs; install's contract differs.
    """
    if relpath not in state.projected_paths():
        return Tier.TIER_3

    on_disk = root / relpath
    if not on_disk.exists():
        return Tier.TIER_1

    # Multi-row resolution (RFC-0052 / ADR-0039): a path may be co-owned by
    # several adapter rows. We no longer take the *first* owner via a
    # `break` — instead the file is Tier-1 when its on-disk SHA matches
    # **any** owner-row's recorded SHA. Co-owned rows hold an identical SHA
    # by construction (the install gate refuses a same-path/different-SHA
    # collision), so this normally compares against a single value; the
    # set form is robust if a future corruption leaves rows disagreeing.
    expected_shas = state.shas_for(relpath)
    if not expected_shas:
        # Path recorded under a pack table but without a sha entry; we
        # can't prove tier-1 vs tier-2 — be conservative.
        return Tier.TIER_2

    return Tier.TIER_1 if sha256_file(on_disk) in expected_shas else Tier.TIER_2


# ---------------------------------------------------------------------------
# .upstream.<ext> companion paths
# ---------------------------------------------------------------------------


def companion_path(path: Path) -> Path:
    """Compute the `.upstream.<ext>` companion path for `path`.

    Rules (from the sibling spec § companion semantics):
      - `AGENTS.md`        → `AGENTS.upstream.md`
      - `docs/CHARTER.md`  → `docs/CHARTER.upstream.md`
      - `Makefile`         → `Makefile.upstream`  (no extension)
      - `foo.tar.gz`       → `foo.tar.upstream.gz`  (only the final suffix
                                                     is treated as the ext)
    """
    suffix = path.suffix  # always includes the leading "."; empty if none
    if suffix:
        return path.with_name(path.stem + ".upstream" + suffix)
    return path.with_name(path.name + ".upstream")


# ---------------------------------------------------------------------------
# Path-jail
# ---------------------------------------------------------------------------


def assert_under(root: Path, target: Path) -> None:
    """Refuse if `target.resolve()` would escape `root.resolve()`.

    Used by `write_jailed` and by recipe-loading sites that synthesise
    target paths from untrusted data (catalogue URIs, fixture packs).
    The resolved comparison foils `..` traversal and symlink escape.
    """
    root_resolved = root.resolve()
    target_resolved = target.resolve()
    try:
        target_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise PathJailError(
            f"refusing to write outside repo root: {target_resolved} not under {root_resolved}"
        ) from exc


# ---------------------------------------------------------------------------
# Windows-portability guard
# ---------------------------------------------------------------------------

# Windows reserves these device names regardless of extension — `CON.txt`
# is the same as `CON`. The set is case-insensitive and applies at every
# path segment, so `foo/NUL.log` is also poisonous. We check on every OS
# because pack content authored on macOS still ships to Windows adopters.
_WINDOWS_RESERVED_NAMES = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + [f"COM{i}" for i in range(1, 10)]
    + [f"LPT{i}" for i in range(1, 10)]
)

# Characters Windows refuses in filenames. The forward slash is the path
# separator on both POSIX and Windows so it is excluded; the backslash
# is excluded because we treat it as a separator (callers normalise at
# the CLI boundary, and `_split_segments` below splits on both).
_WINDOWS_FORBIDDEN_CHARS = frozenset('<>:"|?*')


def _split_segments(relpath: str) -> list[str]:
    """Split a relpath into segments, treating `/` and `\\` as separators.

    Empty segments (from leading/trailing/double separators) are dropped
    so we don't flag the empty stem as "trailing space" or "reserved."

    Defense-in-depth: even though `cli.py:_normalise_path_separators`
    rewrites backslashes at the CLI boundary, this helper accepts both
    separators so a library caller that bypasses the CLI (a test, a
    Python harness) still gets the guard applied correctly. Callers
    should not assume the relpath is pre-normalised.
    """
    out: list[str] = []
    buf: list[str] = []
    for ch in relpath:
        if ch in ("/", "\\"):
            if buf:
                out.append("".join(buf))
                buf = []
        else:
            buf.append(ch)
    if buf:
        out.append("".join(buf))
    return out


def assert_portable_name(relpath: str) -> None:
    """Refuse if any path segment is a Windows-poisonous name.

    Checks three classes (all OSes, because pack content travels):
      1. Reserved device names (CON/PRN/AUX/NUL/COM1-9/LPT1-9), case-
         insensitive, matched on the segment **before** any extension —
         Windows treats `CON.txt` and `NUL.tar.gz` the same as the bare
         device name.
      2. Segments ending in `.` or ` ` — Windows silently strips both
         from filenames at the API layer, so a pack file named `foo. `
         disappears on extract.
      3. Segments containing `<>:"|?*` — illegal in Windows filenames.

    Raises `PathJailError` with a one-line message naming the segment.
    """
    for segment in _split_segments(relpath):
        if not segment:
            continue
        # `.` and `..` are traversal markers — `assert_under` handles
        # escape attempts via path resolution. Skip them here so a
        # `../malicious` write reports the jail violation rather than
        # the "trailing dot" guard.
        if segment in (".", ".."):
            continue
        # Class 3: forbidden characters (check first — cheap, no
        # tokenisation needed and gives the most actionable message).
        for ch in segment:
            if ch in _WINDOWS_FORBIDDEN_CHARS:
                raise PathJailError(
                    f"refusing path with forbidden character {ch!r} in segment "
                    f"{segment!r} (Windows-incompatible): {relpath}"
                )
        # Class 2: trailing dot or space.
        if segment.endswith(".") or segment.endswith(" "):
            raise PathJailError(
                f"refusing path with trailing dot or space in segment "
                f"{segment!r} (Windows strips both silently): {relpath}"
            )
        # Class 1: reserved device name on the pre-extension stem.
        # Windows treats every `<reserved>.<anything>` as the device,
        # so split on the *first* dot rather than the last.
        stem = segment.split(".", 1)[0]
        if stem.upper() in _WINDOWS_RESERVED_NAMES:
            raise PathJailError(
                f"refusing path with Windows-reserved device name "
                f"{stem!r} in segment {segment!r}: {relpath}"
            )


# ---------------------------------------------------------------------------
# Atomic, jailed writes
# ---------------------------------------------------------------------------


def write_jailed(
    root: Path,
    relpath: str,
    content: bytes | str,
    *,
    mode: int | None = None,
    scope: str = "repo",
    allowed_prefixes: list[str] | None = None,
) -> Path:
    """Write `content` to `root / relpath` atomically; refuse outside-root.

    Atomic: writes to a sibling tmpfile then `os.replace`s into place. The
    rename is atomic on POSIX within a filesystem; we ensure same-fs by
    putting the tmpfile next to the target.

    Returns the final on-disk path (resolved). Raises `PathJailError` if
    the resolved target escapes `root`. Caller is responsible for any
    write_atomic backups / Tier-2 companion logic — `write_jailed` is the
    primitive, not the policy.

    RFC-0004 extensions, generalised at repo scope by RFC-0012:
      ``scope`` — the resolved path must additionally lie under one of
      the entries in ``allowed_prefixes`` (each relative to ``root``).
      The two-layer jail (under the root, under a declared prefix)
      stops a buggy projection rule from passing the basic `..`-escape
      check. **Both scopes** consult ``allowed_prefixes`` now —
      RFC-0012 extends the user-scope rail to repo-scope per-IDE
      projection at the same shape.

      ``allowed_prefixes`` — the spec's declared list (e.g.
      ``[".claude/", ".agentbundle/"]`` for Claude Code). Each entry
      must end in ``/``; the function compares against the
      relpath-from-root with a directory-boundary check so
      ``allowed-prefixes = [".claude/"]`` rejects a write to a top-
      level file named ``.claudefoo``.

      When ``allowed_prefixes`` is ``None`` at either scope, the
      per-prefix check is skipped (the bare jail-under-root still
      applies). Passing ``scope="user"`` with ``allowed_prefixes=None``
      remains a programming error — every adopter-facing user-scope
      write must declare its prefix list, so the assertion is the
      forcing function that catches a callsite that forgot.
    """
    if scope == "user" and allowed_prefixes is None:
        # Programming error in CLI code (not adopter-facing). The rail
        # must never silently degrade — surfacing forces the caller to
        # pass the declared prefix list from the adapter's [scope]
        # block. Documented in the spec.
        raise TypeError(
            "allowed_prefixes is required when scope='user'"
        )

    assert_portable_name(relpath)
    target = root / relpath
    assert_under(root, target)

    if allowed_prefixes is not None:
        # Check the resolved target is under one of the declared
        # prefixes relative to root. Use directory-boundary matching:
        # the prefix's trailing slash is mandatory, so ``.claude/``
        # admits ``.claude/skills/foo`` but rejects a top-level
        # ``.claude`` file (which would otherwise let a pack replace
        # the directory with a file).
        prefixes = allowed_prefixes
        # Defense-in-depth: the adapter contract schema enforces a
        # trailing slash on every `allowed-prefixes` entry; assert it
        # at runtime so a future caller that bypasses the schema
        # (e.g. constructing the list in code) cannot silently widen
        # the jail. A `.claude` (no slash) prefix would otherwise
        # admit `.claudefoo` — exactly the bug the equality-clause
        # removal was meant to fix.
        if not all(p.endswith("/") for p in prefixes):
            raise PathJailError(
                f"refusing to write at scope {scope!r}: allowed_prefixes "
                f"must each end with '/'; got {prefixes!r}"
            )
        target_relpath = target.resolve().relative_to(root.resolve()).as_posix()
        if not any(target_relpath.startswith(p) for p in prefixes):
            raise PathJailError(
                f"refusing to write outside allowed prefixes for scope "
                f"{scope!r}: {target.resolve()}"
            )
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise WriteError(
            f"cannot create parent directory {target.parent}: {exc}"
        ) from exc

    if isinstance(content, str):
        data = content.encode("utf-8")
    else:
        data = content

    try:
        fd, tmp_str = tempfile.mkstemp(
            prefix=target.name + ".",
            suffix=".tmp",
            dir=str(target.parent),
        )
    except OSError as exc:
        raise WriteError(
            f"cannot write under {target.parent}: {exc}"
        ) from exc
    tmp = Path(tmp_str)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        if mode is not None:
            os.chmod(tmp, mode)
        os.replace(tmp, target)
    except OSError as exc:
        tmp.unlink(missing_ok=True)
        raise WriteError(
            f"cannot write {target}: {exc}"
        ) from exc
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return target.resolve()


_PACK_PRIMITIVE_TYPES: tuple[str, ...] = (
    "skills", "agents", "hooks", "hook-wiring", "commands",
    "shared-libs", "adapter-root-bins", "user-libs",
)
"""The primitive-type directories under ``<pack>/.apm/`` that the build
pipeline projects. Used by :func:`_collect_pack_owned_names` to walk a
pack's source and build the per-pack scan filter.

Source of truth is ``_data/adapter.toml``'s ``[primitive.*]`` tables
(eight entries today: five originals + ``shared-libs`` and
``adapter-root-bins`` introduced by RFC-0013, + ``user-libs`` introduced
by credbroker-user-scope T3). A contract bump that adds a new primitive
type must extend this tuple, or the per-pack scan will silently miss the
new type's orphans at install start — catalogue-broker packs (e.g.
``credential-brokers``) project load-bearing artifacts under
``adapter-root-bins/`` and ``user-libs/``."""


def _collect_pack_owned_names(
    pack_dir: Path, pack_name: str
) -> tuple[set[str], str]:
    """Return ``(primitive_names, copilot_stem)`` for per-pack scoping.

    Walks each ``<pack_dir>/.apm/<type>/`` directory (for the five
    canonical primitive types) and collects the basenames of immediate
    children — these are the per-skill / per-agent / per-command
    segments that show up in the on-disk projection. For files (e.g.
    ``agents/foo.md``) the stem is collected (``foo``) so a
    file-shape projection matches; for directories (``skills/foo/``)
    the directory name is collected. Dunder / dotfile children
    (``__pycache__``, ``.DS_Store``) are skipped — they aren't pack
    primitives and would needlessly widen the matched-name set.

    The two return values are scoped to different positions in the
    relative path under an adapter prefix:

      - ``primitive_names`` — matched against any **path segment** of
        the relative-to-prefix path. Drives claude-code / kiro /
        codex matching.
      - ``copilot_stem`` (equals ``pack_name``) — matched against the
        **file stem** only when ``len(rel.parts) == 1`` (i.e., the
        Copilot single-file projection at ``<prefix>/<pack>.md``).

    Splitting the two avoids the cross-pack-name-collision false
    positive: if pack A ships a hook named after pack B's pack name,
    its projection at ``.claude/hooks/<pack-B>.py`` would otherwise
    match pack B's scan via a bare segment-equals-pack-name check.
    The structural restriction (segment for primitives; stem-at-
    depth-1 for Copilot) eliminates this without requiring a new
    catalogue lint.
    """
    primitive_names: set[str] = set()
    apm = pack_dir / ".apm"
    if not apm.is_dir():
        return primitive_names, pack_name
    for ptype in _PACK_PRIMITIVE_TYPES:
        sub = apm / ptype
        if not sub.is_dir():
            continue
        for child in sub.iterdir():
            if child.name.startswith(("_", ".")):
                continue
            primitive_names.add(child.stem if child.is_file() else child.name)
    return primitive_names, pack_name


def scan_for_pack_artifacts(
    root: Path,
    allowed_prefixes: list[str],
    *,
    pack_dir: Path | None = None,
    pack_name: str | None = None,
) -> list[Path]:
    """Return on-disk files under ``<root>/<prefix>/`` for each prefix.

    Read-only; walks every ``<root>/<prefix>/`` and returns the files
    found. No state mutation. Used by RFC-0012 § *Reliability* — the
    orphan-projection refusal at install start compares this list
    against ``state.toml``; a non-empty result with no state row for
    the pack means a prior install crashed mid-write.

    **Per-pack scoping (preferred).** When ``pack_dir`` and
    ``pack_name`` are both provided, the result is narrowed via a
    heuristic stand-in for full render-driven ownership: a file's
    relative-to-prefix path is matched against names walked from the
    pack's source. Specifically:

      - ``claude-code`` / ``kiro``: ``<prefix>/<type>/<primitive>/<file>``
        — the ``<primitive>`` path segment is matched against
        primitive names walked from ``<pack_dir>/.apm/<type>/``.
      - ``codex``: ``<prefix>/<primitive>/<file>`` (prefix ends in
        ``skills/``) — same segment match.
      - ``copilot``: ``<prefix>/<pack>.md`` — the **file stem** is
        matched against ``pack_name``, but only when the relative
        path is a single segment (``len(rel.parts) == 1``); this
        scopes the stem rule to Copilot's flat projection and avoids
        a cross-pack-name-collision false positive at other adapters.

    The heuristic admits a narrow residual false-positive surface:
    if a foreign pack ships a primitive whose stem matches a primitive
    name in this pack, the foreign file matches via case (b). The
    path-jail enforces prefix containment (not primitive-name
    uniqueness across packs); two packs landing files at the same
    on-disk path would conflict at install-time write, but the scan
    runs *before* that point. The depth-1 restriction on case (c)
    closes the larger cross-pack-name-collision surface (foreign
    primitive named after this pack's pack-name); the remaining
    stem-in-primitives risk is bounded by catalogue conventions
    around per-pack-unique primitive naming.

    **Legacy mode.** When ``pack_dir``/``pack_name`` are omitted, the
    helper preserves its pre-2026-05-26 adapter-prefix-only scoping
    for any external caller that didn't migrate.

    Each ``prefix`` is expected to end in ``/`` (matching the
    contract's `allowed-prefixes.<scope>` convention). Missing prefix
    directories are skipped silently — a greenfield install has no
    on-disk artifacts and that's the expected case, not an error.

    Results are sorted by path for stable test comparison and stable
    stderr ordering when callers print the list.
    """
    primitive_names: set[str] | None = None
    copilot_stem: str | None = None
    if pack_dir is not None and pack_name is not None:
        primitive_names, copilot_stem = _collect_pack_owned_names(
            pack_dir, pack_name
        )

    out: list[Path] = []
    for prefix in allowed_prefixes:
        base = root / prefix
        if not base.exists():
            continue
        for entry in base.rglob("*"):
            if not entry.is_file():
                continue
            if primitive_names is not None:
                rel = entry.relative_to(base)
                # Segment match: any path component matches a primitive
                # directory name. File-shape primitives (e.g.
                # ``agents/foo.md``) need stem-vs-primitive-names too —
                # the path part is ``foo.md`` but the collected name is
                # ``foo``.
                primitive_hit = (
                    bool(set(rel.parts) & primitive_names)
                    or entry.stem in primitive_names
                )
                # Copilot single-file projection only — scoped to the
                # depth-1 case so a cross-pack primitive named after
                # another pack's pack-name doesn't match here.
                copilot_hit = (
                    copilot_stem is not None
                    and len(rel.parts) == 1
                    and entry.stem == copilot_stem
                )
                if not (primitive_hit or copilot_hit):
                    continue
            out.append(entry)
    return sorted(out)


def write_companion(root: Path, relpath: str, content: bytes | str) -> Path:
    """Write a `<stem>.upstream.<ext>` companion next to `relpath`."""
    companion = companion_path(Path(relpath))
    return write_jailed(root, str(companion), content)


def copy_jailed(root: Path, source: Path, relpath: str) -> Path:
    """Copy a file into the jailed root, preserving mode (mirrors shutil.copy2)."""
    assert_portable_name(relpath)
    target = root / relpath
    assert_under(root, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target, follow_symlinks=False)
    return target.resolve()


# ---------------------------------------------------------------------------
# Helpers used by commands that walk projections
# ---------------------------------------------------------------------------


def projected_files_in_state(state: State, pack_name: str) -> Iterable[str]:
    # A pack may have several adapter rows (v0.4); the union of their
    # footprints is the set of paths the pack projects at this scope.
    out: set[str] = set()
    for ps in state.rows_for_pack(pack_name).values():
        out.update(ps.files.keys())
    return tuple(sorted(out))


# ---------------------------------------------------------------------------
# User-scope artifact root (RFC-0004)
# ---------------------------------------------------------------------------


def user_state_path(home: Path | None = None) -> Path:
    """Return the user-scope state file path: `~/.agentbundle/state.toml`.

    Per RFC-0004 § *State file per scope*, user-scope artifacts live inside
    the namespaced `~/.agentbundle/` dot-directory — not as bare dotfiles
    in `$HOME`. The dot-directory is the future home for
    `.adapt-discovery.toml`, `.adapt-pending.md`, and `.upstream.<ext>`
    companions at user scope; pinning the location here keeps every
    caller agreeing on the layout.

    Creates the dot-directory with mode `0o700` if it does not exist. The
    mode mirrors `ssh`'s `~/.ssh/` — user-readable only — because state
    contains paths the CLI knows are present under the user's home, which
    is sensitive enough to keep out of other accounts on shared hosts.
    Existing directories are left alone (no chmod) so adopters who chose
    a more permissive mode on purpose keep their choice.

    The `home` argument exists for testing — production callers omit it
    and the helper reads `~` via `pathlib.Path.home()`.

    Race-safety: previously this used ``if not base.exists():`` followed
    by ``mkdir(exist_ok=False)`` — a TOCTOU window where another
    process could insert a hostile entry (symlink, regular file)
    between the check and the create. The current shape is
    ``mkdir(exist_ok=True)`` plus a symlink / regular-directory probe
    via ``lstat``; an attacker who pre-creates the path as a symlink
    or a non-directory file is detected at the probe rather than
    silently honoured.
    """
    import os
    import stat as _stat

    base = (home if home is not None else Path.home()) / ".agentbundle"
    try:
        base.mkdir(parents=True, exist_ok=True, mode=0o700)
    except OSError as exc:
        raise OSError(
            f"cannot create user-scope state directory {base}: {exc}"
        ) from exc
    # Refuse a pre-existing entry that is not a regular directory
    # (e.g. a symlink to an attacker-controlled location, or a stray
    # file). Existing real directories are honoured even if their mode
    # is more permissive than 0o700 — the doc-comment promises not to
    # chmod existing dirs.
    try:
        st = os.lstat(base)
    except OSError as exc:
        raise OSError(f"cannot stat user-scope state directory {base}: {exc}") from exc
    if _stat.S_ISLNK(st.st_mode) or not _stat.S_ISDIR(st.st_mode):
        raise OSError(
            f"user-scope state directory {base} is not a regular directory; "
            f"refusing to use it"
        )
    return base / "state.toml"
