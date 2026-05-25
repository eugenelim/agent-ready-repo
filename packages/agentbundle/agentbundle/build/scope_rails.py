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


def check_hooks(
    pack_path: Path,
    allowed_scopes: Iterable[str],
    user_scope_hooks: bool = False,
) -> str | None:
    """Rail B. Return None on accept; refusal string on refuse.

    A pack containing a non-empty ``.apm/hooks/`` or
    ``.apm/hook-wiring/`` directory cannot declare ``"user" ∈
    allowed-scopes`` **unless** it explicitly opts in via
    ``[pack.install] user-scope-hooks = true`` (RFC-0005 § Rail B —
    user-scope lift). The opt-in is the consent gesture: "yes, my
    hooks land on the adopter's machine outside per-project isolation".

    The lift here is the validate-side half — T8b threads the same
    flag through install/uninstall so the rail's behaviour stays
    consistent between the two surfaces.
    """
    if not _allows_user(allowed_scopes):
        return None
    if user_scope_hooks:
        # Pack-author opted in — RFC-0005 says the rail lifts. The
        # adapter-side gate (hook-wiring mode declares user-scope
        # capability) is checked later in the projection pipeline
        # (T5/T6); the rail's job is the consent-gesture check.
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
    user_scope_hooks: bool = False,
) -> str | None:
    """Run Rails A → B → C in spec order; return first refusal or None.

    The spec orders them A → B → C so the seeds rail fires before the
    marker rail's input is even computed (the marker rail never sees
    ``seeds/`` content — Rail A already refused the pack if ``seeds/``
    was populated). Use this helper from the CLI's ``install`` and
    ``validate`` surfaces to keep the message order consistent.

    ``user_scope_hooks`` propagates to Rail B's conditional lift
    (RFC-0005 § Rail B — user-scope lift). Rails A and C ignore it.
    """
    if (result := check_seeds(pack_path, allowed_scopes)) is not None:
        return result
    if (result := check_hooks(pack_path, allowed_scopes, user_scope_hooks)) is not None:
        return result
    if (result := check_markers(pack_path, allowed_scopes)) is not None:
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


def check_kiro_event_vocabulary(
    pack_name: str,
    wiring_tomls: dict[str, dict],
    vocabulary: list[str] | None,
    target_adapters: Iterable[str],
    adapter_name: str,
) -> str | None:
    """T6 (RFC-0005): per-adapter event-vocabulary refusal.

    AC17 and AC17b: a wiring TOML naming an event outside the resolved
    target adapter's declared ``agent-event-vocabulary`` is refused at
    ``validate`` time with the RFC-0005 verbatim text
    ``pack <P>'s hook-wiring <name>.toml uses event '<E>'; not in
    adapter '<adapter>' agent-event-vocabulary``.

    The check fires only when:
      - the resolved target adapter is in ``target_adapters``, AND
      - that adapter declares ``vocabulary`` (the projection's
        ``agent-event-vocabulary`` field is present).

    Claude Code's projection does not declare ``agent-event-vocabulary``,
    so a wiring TOML with arbitrary event names projected against
    Claude Code passes ``validate``. The vocabulary refusal is
    per-adapter, not per-RFC (AC17b).

    Arguments:
      pack_name: substituted into the refusal text.
      wiring_tomls: map of basename → parsed TOML body. First offender
        wins.
      vocabulary: the adapter's declared event-name list, or None when
        the adapter has no such declaration (rail is a no-op).
      target_adapters: iterable of adapter names the pack is being
        validated against.
      adapter_name: the adapter the vocabulary belongs to (substituted
        into the refusal text).
    """
    if adapter_name not in set(target_adapters or ()):
        return None
    if vocabulary is None:
        return None
    allowed = set(vocabulary)
    for wiring_name, body in wiring_tomls.items():
        hooks = body.get("hooks", {}) if isinstance(body, dict) else {}
        if not isinstance(hooks, dict):
            continue
        for event in hooks.keys():
            if event not in allowed:
                return (
                    f"pack {pack_name}'s hook-wiring {wiring_name}.toml "
                    f"uses event '{event}'; not in adapter '{adapter_name}' "
                    f"agent-event-vocabulary"
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
    dispatches to the in-memory rail. Mirrors rail C's symlink
    discipline: a symlink under either directory is refused — a
    legitimate primitive is a regular file, and following a symlink
    would let a pack reach outside its source tree. A wiring TOML that
    fails to parse counts as a refusal on its own.
    """
    if "kiro" not in set(target_adapters or ()):
        return None

    wiring_dir = pack_path / ".apm" / "hook-wiring"
    if not wiring_dir.exists():
        return None

    import tomllib
    from stat import S_ISLNK

    wiring_tomls: dict[str, dict] = {}
    for entry in sorted(wiring_dir.iterdir()):
        if entry.suffix != ".toml":
            continue
        try:
            st = os.lstat(entry)
        except OSError:
            continue
        if S_ISLNK(st.st_mode):
            rel = entry.relative_to(pack_path)
            return (
                f"pack {pack_name}'s hook-wiring entry is a symlink "
                f"(not a regular file); first offender: {rel.as_posix()}"
            )
        if not entry.is_file():
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
            if entry.suffix != ".md":
                continue
            try:
                st = os.lstat(entry)
            except OSError:
                continue
            if S_ISLNK(st.st_mode):
                rel = entry.relative_to(pack_path)
                return (
                    f"pack {pack_name}'s agent entry is a symlink "
                    f"(not a regular file); first offender: {rel.as_posix()}"
                )
            if entry.is_file():
                agent_basenames.add(entry.stem)

    return check_kiro_attach_to_agent(
        pack_name,
        wiring_tomls,
        agent_basenames,
        target_adapters,
    )


# ---------------------------------------------------------------------------
# T-C2 (RFC-0005): kiro-ide-hook validate rail.
#
# Five refusal paths covering the RFC's "validate rail" subsection
# under § *Kiro IDE event hooks — new `kiro-ide-hook` primitive*:
#
#   1. Missing required field (`name`, `version`, `when.type`,
#      `then.type`).
#   2. `when.type` outside the adapter's declared
#      `ide-event-vocabulary`.
#   3. `then.type` outside the adapter's declared
#      `ide-action-vocabulary`.
#   4. Malformed placeholder in `then.command` — any `${...}` that
#      does not match `\$\{hook-body:[a-zA-Z0-9_-]+\}` exactly.
#   5. Unresolvable placeholder — well-formed `${hook-body:<name>}`
#      whose `<name>` is not a same-pack `.apm/hooks/<name>.<ext>`.
#
# RFC § Substitution rules clause 1 fences the placeholder scan to
# `then.command` only; placeholder-shaped text in `then.prompt`
# (askAgent), `name`, `description`, `when.patterns`, or any other
# field passes through verbatim.
#
# Vocabularies arrive as parameters from the caller — same pattern
# as `check_kiro_event_vocabulary`. The caller (`commands/validate.py`)
# loads them from the v0.4 adapter contract once and threads them in;
# rail-side caching would couple the rail to contract-file location.
# ---------------------------------------------------------------------------


# Strict placeholder grammar — RFC § Substitution rules clause 4.
# Closing brace required; inner name matches `[a-zA-Z0-9_-]+` only,
# so whitespace, slashes, dots, and `..` are all forbidden by
# construction.
_HOOK_BODY_PLACEHOLDER_RE = re.compile(r"\$\{hook-body:([a-zA-Z0-9_-]+)\}")

# Loose `${...}` matcher used to find anything placeholder-shaped that
# fails the strict grammar above; an offender that matches this but
# not the strict regex is a malformed placeholder. We deliberately
# don't try to match `${...` without a closing brace — that's literal
# text per shell-syntax convention.
_ANY_PLACEHOLDER_RE = re.compile(r"\$\{[^}]*\}")


def check_kiro_ide_hook(
    pack_path: Path,
    pack_name: str,
    target_adapters: Iterable[str],
    ide_event_vocabulary: list[str] | None = None,
    ide_action_vocabulary: list[str] | None = None,
) -> str | None:
    """T-C2 filesystem rail for the kiro-ide-hook primitive.

    Walks ``<pack_path>/.apm/kiro-ide-hooks/*.kiro.hook`` in sorted
    order and applies the five refusal paths above. The first
    offender wins; subsequent files are not inspected (matches the
    other Kiro rails' first-offender discipline).

    Returns:
      ``None`` when every hook passes, or when ``kiro`` is not in
      ``target_adapters``, or when the pack ships no
      ``.apm/kiro-ide-hooks/`` directory.

      A refusal string in RFC-0005 § *validate rail* verbatim form
      otherwise. The string carries enough context for the caller to
      format the spec's stderr line — ``validate: <pack>: <message>``
      — without per-rail formatting code at each call site.

    Arguments:
      pack_path: absolute path to the pack root.
      pack_name: pack name (substituted into the refusal text).
      target_adapters: iterable of adapter names the pack is being
        validated against. Rail is a no-op when ``"kiro"`` is absent.
      ide_event_vocabulary: the kiro adapter's declared
        ``ide-event-vocabulary`` from
        ``[adapter.kiro.projections.kiro-ide-hook]``. ``None`` skips
        check 2 (rail becomes a no-op for that field — same shape as
        ``check_kiro_event_vocabulary`` when the adapter declares no
        vocabulary).
      ide_action_vocabulary: same shape, for ``then.type``.
    """
    if "kiro" not in set(target_adapters or ()):
        return None

    import json
    from stat import S_ISLNK

    hooks_dir = pack_path / ".apm" / "kiro-ide-hooks"
    if not hooks_dir.exists():
        return None

    # Same-pack hook-body basenames — set up once so check 5 (unresolvable
    # placeholder) can verify a referenced name against shipped files.
    # An empty set is fine — every placeholder will fail check 5, which
    # is the correct semantics (a pack with no hook-bodies cannot
    # reference one).
    hook_body_basenames: set[str] = set()
    hook_body_dir = pack_path / ".apm" / "hooks"
    if hook_body_dir.exists():
        for entry in sorted(hook_body_dir.iterdir()):
            try:
                st = os.lstat(entry)
            except OSError:
                continue
            if S_ISLNK(st.st_mode):
                # Symlinks under .apm/hooks/ are out of scope for this
                # rail; check_hooks (Rail B) is the gate for that
                # surface and it doesn't fire for repo-only packs.
                continue
            if entry.is_file():
                hook_body_basenames.add(entry.stem)

    allowed_events = set(ide_event_vocabulary) if ide_event_vocabulary is not None else None
    allowed_actions = set(ide_action_vocabulary) if ide_action_vocabulary is not None else None

    for entry in sorted(hooks_dir.iterdir()):
        if not entry.name.endswith(".kiro.hook"):
            # Other files in .kiro-ide-hooks/ aren't this primitive's
            # responsibility — silently skipped (matches the
            # `*.kiro.hook` filter assumption from RFC Q6).
            continue
        if entry.name == ".kiro.hook":
            # A file named exactly `.kiro.hook` has no bare name to
            # substitute into the projection target — refuse rather
            # than emit a `.kiro/hooks/<pack>/.kiro.hook` whose
            # filename collides with anything else a pack ships.
            return (
                f"pack {pack_name}'s kiro-ide-hook entry has an "
                f"empty bare name; expected <name>.kiro.hook with "
                f"<name> non-empty"
            )
        try:
            st = os.lstat(entry)
        except OSError:
            continue
        if S_ISLNK(st.st_mode):
            rel = entry.relative_to(pack_path)
            return (
                f"pack {pack_name}'s kiro-ide-hook entry is a symlink "
                f"(not a regular file); first offender: {rel.as_posix()}"
            )
        if not entry.is_file():
            continue

        try:
            body = json.loads(entry.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return (
                f"pack {pack_name}'s kiro-ide-hook {entry.name} "
                f"failed to parse: {exc}"
            )
        if not isinstance(body, dict):
            return (
                f"pack {pack_name}'s kiro-ide-hook {entry.name} "
                f"is not a JSON object"
            )

        # Check 1 — required fields. Order: name → version → when → then →
        # when.type → then.type so the most-likely-missing top-level
        # field surfaces first.
        for required in ("name", "version", "when", "then"):
            if required not in body:
                return (
                    f"pack {pack_name}'s kiro-ide-hook {entry.name} "
                    f"is missing required field {required}"
                )
        when = body.get("when")
        then = body.get("then")
        if not isinstance(when, dict) or "type" not in when:
            return (
                f"pack {pack_name}'s kiro-ide-hook {entry.name} "
                f"is missing required field when.type"
            )
        if not isinstance(then, dict) or "type" not in then:
            return (
                f"pack {pack_name}'s kiro-ide-hook {entry.name} "
                f"is missing required field then.type"
            )

        when_type = when["type"]
        then_type = then["type"]

        # Check 2 — when.type vocabulary.
        if allowed_events is not None and when_type not in allowed_events:
            return (
                f"pack {pack_name}'s kiro-ide-hook {entry.name} "
                f"uses event '{when_type}'; not in adapter 'kiro' "
                f"ide-event-vocabulary"
            )

        # Check 3 — then.type vocabulary.
        if allowed_actions is not None and then_type not in allowed_actions:
            return (
                f"pack {pack_name}'s kiro-ide-hook {entry.name} "
                f"uses action '{then_type}'; not in adapter 'kiro' "
                f"ide-action-vocabulary"
            )

        # Checks 4 + 5 — placeholder scan. RFC § Substitution rules
        # clause 1 fences this to `then.command` only.
        command = then.get("command")
        if isinstance(command, str):
            # First pass: any `${...}` that doesn't match the strict
            # grammar is malformed (check 4).
            for match in _ANY_PLACEHOLDER_RE.finditer(command):
                literal = match.group(0)
                if not _HOOK_BODY_PLACEHOLDER_RE.fullmatch(literal):
                    return (
                        f"pack {pack_name}'s kiro-ide-hook {entry.name} "
                        f"contains malformed placeholder '{literal}'; "
                        f"expected ${{hook-body:<name>}} with name "
                        f"matching [a-zA-Z0-9_-]+"
                    )
            # Second pass: well-formed placeholders must resolve to a
            # same-pack hook-body (check 5).
            for match in _HOOK_BODY_PLACEHOLDER_RE.finditer(command):
                name = match.group(1)
                if name not in hook_body_basenames:
                    return (
                        f"pack {pack_name}'s kiro-ide-hook {entry.name} "
                        f"references unknown hook-body "
                        f"'${{hook-body:{name}}}'; no such hook-body "
                        f"in pack"
                    )

    return None
