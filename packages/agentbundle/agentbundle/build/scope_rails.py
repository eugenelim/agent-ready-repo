"""Contract-level user-scope refusal rails (RFC-0004 Rails A/B/C).

The three rails fire **only when a pack declares `"user" ∈
allowed-scopes`**. Repo-only packs are not inspected. The whole point
of the rails is to keep content that would not survive the
user-scope projection out of user-scope packs in the first place.

Each rail returns `None` when the pack passes, or a string describing
the first offending path when the rail refuses. The string carries
enough context for the caller (`validate` or `install`) to format the
spec's stderr text — `<pack>: <rail message>` — without per-rail
formatting code at each call site.

Rails:

  - **Rail A — seeds/.** A pack containing a non-empty `seeds/` directory
    cannot declare `"user" ∈ allowed-scopes` (seeds project to nonsense
    paths under `~`). The detection is filesystem-shaped: any descendant
    file under `<pack>/seeds/` triggers the rail.

  - **Rail B — hook-shaped primitives.** A pack whose source tree
    contains a non-empty `.apm/hooks/` or `.apm/hook-wiring/` directory
    cannot declare `"user" ∈ allowed-scopes` until the user-scope hook-
    wiring merge story is designed in a follow-up RFC.

  - **Rail C — `<adapt:NAME>` markers.** A pack declaring `"user" ∈
    allowed-scopes` cannot carry either the legacy UPPER_SNAKE marker
    form `<adapt:[A-Z_][A-Z0-9_]*>` *or* the canonical lowercase-hyphen
    form `<adapt:[a-z][a-z0-9-]*>` in any file under `.apm/skills/`,
    `.apm/agents/`, or `.apm/commands/`. Both casings are recognised
    per `adapt-to-project` spec AC14 (canonical syntax) and AC21
    (cross-spec widening) so a user-scope pack carrying lowercase-
    hyphen markers cannot bypass the rail. The rail walks those
    directories in `sorted(os.walk(...))` order so the first-offending-
    path stderr message is deterministic across runs and platforms.
    Non-UTF-8 (binary) files are skipped silently — they cannot contain
    a textual marker by definition, and forcing them through decoding
    would surface spurious errors on legitimate binaries (icons,
    images, archives).

The rails are run by `agentbundle validate <pack>` (pre-publish) and
re-run by `agentbundle install --scope user` against the resolved pack
content. Re-running at install time closes the widen-after-publish gap:
a pack published as `["repo"]` and later flipped to include `"user"`
cannot install at user scope without passing every rail at install
time.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable


# Both legacy UPPER_SNAKE and canonical lowercase-hyphen marker forms
# are recognised per adapt-to-project spec AC14 + AC21. The canonical
# form is what self_host.resolve_markers writes; the legacy form is
# tolerated with a one-shot per-file warning during the migration
# window. Rail C refuses either form in user-scope packs because both
# would survive into a user-scope projection and bypass the contract.
_MARKER_REGEX = re.compile(rb"<adapt:(?:[A-Z_][A-Z0-9_]*|[a-z][a-z0-9-]*)>")

# The three primitive source directories Rail C walks. `.apm/hooks/` and
# `.apm/hook-wiring/` are already user-scope-refused by Rail B, so a
# marker check on them is unreachable. `seeds/` is already
# user-scope-refused by Rail A, so the marker rail's input never
# includes `seeds/`. Spec § *Install-scope dimension* pins the list.
_MARKER_RAIL_DIRS = (".apm/skills", ".apm/agents", ".apm/commands")

# Cap per-file inspection size to keep Rail C bounded. A primitive file
# is human-authored content (SKILL.md, agent body, command); an outsize
# input under one of the rail directories is either an accident or a
# DoS attempt against the validate / install path. Files larger than
# the cap are reported and refused as if they had matched — the rail's
# job is "decide whether this pack is safe at user scope", and an
# unreviewable blob in primitive territory is not safe by default.
_MARKER_RAIL_FILE_CAP_BYTES = 4 * 1024 * 1024  # 4 MiB


def _allows_user(allowed_scopes: Iterable[str]) -> bool:
    """Return True if the pack's allowed-scopes includes `"user"`."""
    return "user" in set(allowed_scopes or ())


def check_seeds(pack_path: Path, allowed_scopes: Iterable[str]) -> str | None:
    """Rail A. Return None on accept; refusal string on refuse.

    A pack containing a non-empty `seeds/` directory cannot declare
    `"user" ∈ allowed-scopes`.
    """
    if not _allows_user(allowed_scopes):
        return None
    seeds_dir = pack_path / "seeds"
    if not seeds_dir.exists():
        return None
    # followlinks=False so a symlink loop or symlink to outside the
    # pack tree can't extend the rail's reach; consistency with Rail C.
    for root, _dirs, files in os.walk(seeds_dir, followlinks=False):
        if files:
            # Name the first file in sorted order so the message is
            # deterministic across runs (Rail C uses the same rule).
            first = sorted(files)[0]
            rel = Path(root, first).relative_to(pack_path)
            return (
                f"pack carries non-empty seeds/ but declares "
                f'"user" ∈ allowed-scopes; first offender: {rel.as_posix()}'
            )
    return None


def check_hooks(pack_path: Path, allowed_scopes: Iterable[str]) -> str | None:
    """Rail B. Return None on accept; refusal string on refuse.

    A pack containing a non-empty `.apm/hooks/` or `.apm/hook-wiring/`
    directory cannot declare `"user" ∈ allowed-scopes`.
    """
    if not _allows_user(allowed_scopes):
        return None
    for hook_subdir in (".apm/hooks", ".apm/hook-wiring"):
        candidate = pack_path / hook_subdir
        if not candidate.exists():
            continue
        # followlinks=False — consistent with Rails A and C.
        for root, _dirs, files in os.walk(candidate, followlinks=False):
            if files:
                first = sorted(files)[0]
                rel = Path(root, first).relative_to(pack_path)
                return (
                    f"pack carries hook-shaped primitives at {hook_subdir}/ but "
                    f'declares "user" ∈ allowed-scopes; first offender: '
                    f"{rel.as_posix()}"
                )
    return None


def check_markers(pack_path: Path, allowed_scopes: Iterable[str]) -> str | None:
    """Rail C. Return None on accept; refusal string on refuse.

    A pack declaring `"user" ∈ allowed-scopes` cannot carry
    `<adapt:NAME>` markers in any file under `.apm/skills/`,
    `.apm/agents/`, or `.apm/commands/`. Walks in deterministic
    `sorted(os.walk(...))` order. Binary files are skipped silently —
    a marker is by construction a UTF-8 byte sequence, and forcing
    binaries through decoding would create spurious failures.
    """
    if not _allows_user(allowed_scopes):
        return None
    for rail_subdir in _MARKER_RAIL_DIRS:
        root_dir = pack_path / rail_subdir
        if not root_dir.exists():
            continue
        for root, dirs, files in os.walk(root_dir, followlinks=False):
            dirs.sort()
            for fname in sorted(files):
                fpath = Path(root, fname)
                try:
                    # lstat (not stat) so a `*.md → /dev/zero` symlink
                    # surfaces as a symlink at this rail rather than a
                    # zero-byte file. Symlinks under `.apm/skills/`,
                    # `.apm/agents/`, `.apm/commands/` are not a
                    # legitimate primitive shape — refuse them out
                    # right so the size cap below can't be defeated by
                    # `read_bytes()` traversing the symlink target.
                    st = os.lstat(fpath)
                except OSError:
                    continue
                from stat import S_ISLNK

                if S_ISLNK(st.st_mode):
                    rel = fpath.relative_to(pack_path)
                    return (
                        f"pack declares \"user\" ∈ allowed-scopes but "
                        f"a primitive entry is a symlink (not a regular "
                        f"file); first offender: {rel.as_posix()}"
                    )
                size = st.st_size
                if size > _MARKER_RAIL_FILE_CAP_BYTES:
                    rel = fpath.relative_to(pack_path)
                    return (
                        f"pack declares \"user\" ∈ allowed-scopes but "
                        f"a primitive file exceeds the marker-rail size cap "
                        f"({_MARKER_RAIL_FILE_CAP_BYTES // (1024 * 1024)} MiB); "
                        f"first offender: {rel.as_posix()}"
                    )
                # Close the lstat→read TOCTOU window with O_NOFOLLOW so
                # the kernel refuses if the entry was swapped for a
                # symlink between the lstat above and this read. The
                # platform check (`hasattr(os, "O_NOFOLLOW")`) is
                # defensive — POSIX always has it; Windows doesn't, but
                # the stdlib-only commitment defers Windows anyway.
                try:
                    if hasattr(os, "O_NOFOLLOW"):
                        fd = os.open(str(fpath), os.O_RDONLY | os.O_NOFOLLOW)
                        try:
                            data = os.read(fd, size)
                            # Drain any residual bytes appended after lstat.
                            while True:
                                chunk = os.read(fd, 65536)
                                if not chunk:
                                    break
                                if len(data) + len(chunk) > _MARKER_RAIL_FILE_CAP_BYTES:
                                    rel = fpath.relative_to(pack_path)
                                    return (
                                        f"pack declares \"user\" ∈ allowed-scopes "
                                        f"but a primitive file grew past the "
                                        f"marker-rail size cap during read; "
                                        f"first offender: {rel.as_posix()}"
                                    )
                                data += chunk
                        finally:
                            os.close(fd)
                    else:
                        data = fpath.read_bytes()
                except OSError:
                    # Unreadable file — defer to validate's caller for
                    # filesystem-permission errors; don't refuse here.
                    continue
                if _is_binary(data):
                    continue
                if _MARKER_REGEX.search(data) is not None:
                    rel = fpath.relative_to(pack_path)
                    return (
                        f"pack declares \"user\" ∈ allowed-scopes but "
                        f"a primitive file carries <adapt:NAME> markers; "
                        f"first offender: {rel.as_posix()}"
                    )
    return None


def _is_binary(data: bytes) -> bool:
    """Heuristic: a UTF-8 decode that fails marks the file as binary.

    The strict-grep contract pins decoding via `errors='strict'` and
    catching `UnicodeDecodeError` — a file that fails to decode cannot
    carry a textual marker. Empty files decode trivially and are not
    binary.
    """
    if not data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def run_all(
    pack_path: Path,
    allowed_scopes: Iterable[str],
) -> str | None:
    """Run Rails A → B → C in spec order; return first refusal or None.

    The spec orders them A → B → C so the seeds rail fires before the
    marker rail's input is even computed (the marker rail never sees
    `seeds/` content — Rail A already refused the pack if `seeds/` was
    populated). Use this helper from the CLI's `install` and
    `validate` surfaces to keep the message order consistent.
    """
    for rail in (check_seeds, check_hooks, check_markers):
        result = rail(pack_path, allowed_scopes)
        if result is not None:
            return result
    return None


# ---------------------------------------------------------------------------
# T2 (RFC-0005): kiro `attach-to-agent` validate rail.
#
# Pure-function shape so unit tests can drive it with in-memory pack-shaped
# dicts (per the T2 plan's testing approach — no on-disk fixtures). The CLI
# `validate` command's filesystem-based wrapper lives in `check_kiro_wiring`
# below; it loads the on-disk pack and dispatches to this in-memory helper.
# ---------------------------------------------------------------------------


def check_kiro_attach_to_agent(
    pack_name: str,
    wiring_tomls: dict[str, dict],
    agent_basenames: set[str],
    target_adapters: Iterable[str],
) -> str | None:
    """In-memory rail. Return refusal string on the first offender, or None.

    Fires only when ``"kiro" in target_adapters``. For each wiring TOML:
      - missing ``attach-to-agent`` field → refuse,
      - ``attach-to-agent`` value naming an agent the pack does not ship
        (no ``.apm/agents/<value>.md``) → refuse.

    Refusal text is RFC-0005 § Repo-scope Kiro promotion verbatim:
    ``pack <P>'s hook-wiring <name>.toml does not declare 'attach-to-agent'
    (or names an unknown agent); required for kiro projection``.

    Arguments:
      pack_name: pack name (substituted into the refusal text).
      wiring_tomls: map of wiring TOML basename (without ``.toml``) → parsed
        TOML body. Iteration order is preserved; the first offender wins.
      agent_basenames: set of agent file basenames (without ``.md``) the
        pack ships under ``.apm/agents/``.
      target_adapters: iterable of adapter names the pack is being
        validated against. No-op when ``kiro`` is absent.
    """
    if "kiro" not in set(target_adapters or ()):
        return None
    for wiring_name, body in wiring_tomls.items():
        attach = body.get("attach-to-agent") if isinstance(body, dict) else None
        if not isinstance(attach, str) or attach not in agent_basenames:
            return (
                f"pack {pack_name}'s hook-wiring {wiring_name}.toml "
                f"does not declare 'attach-to-agent' (or names an unknown "
                f"agent); required for kiro projection"
            )
    return None


def check_kiro_wiring(
    pack_path: Path,
    pack_name: str,
    target_adapters: Iterable[str],
) -> str | None:
    """Filesystem wrapper around ``check_kiro_attach_to_agent``.

    Reads ``.apm/hook-wiring/*.toml`` and ``.apm/agents/*.md`` from
    ``pack_path``, parses each wiring TOML with ``tomllib``, and
    dispatches to the in-memory rail. A wiring TOML that fails to parse
    counts as a refusal on its own (a malformed pack-side declaration).
    """
    if "kiro" not in set(target_adapters or ()):
        return None

    wiring_dir = pack_path / ".apm" / "hook-wiring"
    if not wiring_dir.exists():
        return None

    import tomllib

    wiring_tomls: dict[str, dict] = {}
    for entry in sorted(wiring_dir.iterdir()):
        if not entry.is_file() or entry.suffix != ".toml":
            continue
        try:
            wiring_tomls[entry.stem] = tomllib.loads(entry.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError) as exc:
            return (
                f"pack {pack_name}'s hook-wiring {entry.stem}.toml "
                f"failed to parse: {exc}"
            )

    agents_dir = pack_path / ".apm" / "agents"
    agent_basenames: set[str] = set()
    if agents_dir.exists():
        for entry in sorted(agents_dir.iterdir()):
            if entry.is_file() and entry.suffix == ".md":
                agent_basenames.add(entry.stem)

    return check_kiro_attach_to_agent(
        pack_name,
        wiring_tomls,
        agent_basenames,
        target_adapters,
    )
