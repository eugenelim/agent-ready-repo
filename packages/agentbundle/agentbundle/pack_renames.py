"""Build the hint an adopter sees when a requested pack was renamed.

The builder is a pure function: it reads the reporting catalogue's rename map
and the candidate dependents' ``pack.toml`` files through
``file_safety.read_confined_regular_file`` and returns text. It has no write
path, makes no network call and reads no other catalogue.
"""

from __future__ import annotations

import os
import re
import stat
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from agentbundle.catalogue_tooling.diagnostics import escape_rendered_value
from agentbundle.catalogue_tooling.file_safety import read_confined_regular_file
from agentbundle.config import (
    State,
    canonicalize_source,
    source_is_credential_bearing,
)
from agentbundle.direct_source import recovery_command

MAP_RELPATH = Path("contracts") / "renames" / "pack-renames.toml"
MAX_BYTES = 65536
PLACEHOLDER = "<catalogue-source>"
_LEGACY_SOURCE = "agent-ready-repo"
_DIGEST_FRAGMENT_RE = re.compile(r"sha256=[0-9a-f]{64}")

PLACEHOLDER_SENTENCE = (
    "Edit this step to name a catalogue source before running it; "
    "leaving the source out sends this step to a different catalogue."
)
CREDENTIAL_SENTENCE = (
    "Upgrade cannot record this catalogue source, so each dependent keeps "
    "its old recorded source."
)


@dataclass(frozen=True)
class Installed:
    """The repo-scope installed state the hint reads.

    ``sources`` maps ``(pack, adapter)`` to the recorded source, or ``None``.
    """

    sources: dict[tuple[str, str], str | None] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> Installed:
        return cls({})

    @classmethod
    def from_state(cls, state: State) -> Installed:
        return cls({key: ps.source for key, ps in state.packs.items()})

    def adapters(self, pack: str) -> list[str]:
        return sorted(a for (p, a) in self.sources if p == pack)

    def names(self) -> list[str]:
        return sorted({p for (p, _a) in self.sources})


@dataclass(frozen=True)
class RenameHint:
    """Result: hint ``lines``, a ``refusal`` reason, or neither (no hint)."""

    lines: tuple[str, ...] = ()
    refusal: str | None = None


NO_HINT = RenameHint()


def _name_re() -> re.Pattern[str]:
    # Lazy: install imports this module's callers, so a top-level import cycles.
    from agentbundle.commands.install import _PACK_NAME_RE

    return _PACK_NAME_RE


def _shipped_adapters() -> tuple[str, ...]:
    from agentbundle.cli import _shipped_adapters_choices

    return _shipped_adapters_choices()


def _is_unsafe(value: str) -> bool:
    return escape_rendered_value(value) != value


def _is_unsafe_arg(value: str) -> bool:
    return _is_unsafe(value) or value.startswith("-")


def _lstat_kind(path: Path) -> str:
    """'absent', 'dir', or 'other' for *path*, never following a link."""
    try:
        mode = os.lstat(path).st_mode
    except FileNotFoundError:
        return "absent"
    return "dir" if stat.S_ISDIR(mode) else "other"


def _read_pack_toml(root: Path, relative: Path) -> bytes:
    return read_confined_regular_file(root, root / relative, max_bytes=MAX_BYTES)


def _load_map(root: Path, name: str) -> str | None:
    """Return the target *name* is renamed to, or ``None`` for no valid rename."""
    data = tomllib.loads(_read_pack_toml(root, MAP_RELPATH).decode("utf-8"))
    pattern = _name_re()
    renames = data.get("rename")
    schema = data.get("schema")
    if isinstance(schema, bool) or schema != 1 or not isinstance(renames, list):
        return None
    targets: list[str] = []
    for entry in renames:
        if not isinstance(entry, dict) or set(entry) != {"from", "to"}:
            return None
        old, new = entry["from"], entry["to"]
        if not (isinstance(old, str) and isinstance(new, str)):
            return None
        if not (pattern.fullmatch(old) and pattern.fullmatch(new)):
            return None
        if old == name:
            targets.append(new)
    if len(targets) != 1:
        return None
    return targets[0]


def _pack_toml_candidates(name: str) -> tuple[Path, Path]:
    """Pack directories in ``install._locate_pack`` order."""
    return Path("packs") / name, Path(name)


def _find_pack_toml(root: Path, name: str) -> Path | None:
    """The first ``pack.toml`` entry among the candidates, or ``None`` if absent.

    Raises ``ValueError`` when a candidate directory or its parent is a link or
    a non-directory (the Unchecked case).
    """
    if _lstat_kind(root / "packs") == "other":
        raise ValueError("packs is not a real directory")
    kinds = [_lstat_kind(root / c) for c in _pack_toml_candidates(name)]
    if "other" in kinds:
        raise ValueError("candidate pack directory is not a real directory")
    for candidate, kind in zip(_pack_toml_candidates(name), kinds, strict=False):
        if kind == "dir":
            try:
                os.lstat(root / candidate / "pack.toml")
            except FileNotFoundError:
                continue
            return candidate / "pack.toml"
    return None


def _target_is_pack(root: Path, target: str) -> bool:
    """True when *target* is a pack here, found as ``_locate_pack`` finds it.

    A candidate behind a link or non-directory is skipped, so it never counts.
    """
    packs_ok = _lstat_kind(root / "packs") != "other"
    for candidate in _pack_toml_candidates(target):
        if candidate.parts[0] == "packs" and not packs_ok:
            continue
        if _lstat_kind(root / candidate) != "dir":
            continue
        try:
            os.lstat(root / candidate / "pack.toml")
        except FileNotFoundError:
            continue
        _read_pack_toml(root, candidate / "pack.toml")
        return True
    return False


def _requires(pack_toml: object, target: str) -> bool:
    if not isinstance(pack_toml, dict):
        return False
    pack = pack_toml.get("pack")
    deps = pack.get("dependencies") if isinstance(pack, dict) else None
    required = deps.get("required") if isinstance(deps, dict) else None
    if not isinstance(required, list):
        return False
    return any(isinstance(e, dict) and e.get("pack") == target for e in required)


def _is_printable_source(source: str) -> bool:
    if not source or _is_unsafe(source) or "?" in source:
        return False
    try:
        parsed = urlsplit(source)
    except ValueError:
        return False
    if "@" in parsed.netloc:
        return False
    if "#" in source:
        return parsed.scheme == "archive+https" and bool(
            _DIGEST_FRAGMENT_RE.fullmatch(parsed.fragment)
        )
    return True


def _credential_free(source: str) -> str:
    """*source* without user-info, query and fragment, unsafe characters escaped."""
    text = source
    if "://" in source:
        try:
            parsed = urlsplit(source)
            netloc = parsed.netloc.rpartition("@")[2]
            text = parsed._replace(netloc=netloc, query="", fragment="").geturl()
        except ValueError:
            text = source.split("://", 1)[0] + "://"
    else:
        text = source.split("?", 1)[0].split("#", 1)[0]
    return escape_rendered_value(text)


def _no_recorded_source(recorded: str | None) -> bool:
    return not recorded or recorded == _LEGACY_SOURCE


def _source_sentence(pack: str, recorded: str | None, reporting: str) -> str | None:
    """The AC-0016, AC-0017 and AC-0028 sentence for one step, if any."""
    if _no_recorded_source(recorded):
        return f"Installed pack '{pack}' has no recorded source."
    assert recorded is not None
    canonical = canonicalize_source(recorded)
    if canonical is not None and canonical == canonicalize_source(reporting):
        return None
    return (
        f"This step is a move between catalogues: '{pack}' was installed "
        f"from {_credential_free(recorded)}."
    )


def build_rename_hint(
    name: str,
    *,
    catalogue_dir: Path,
    source: str,
    installed: Installed,
    command: str,
    target_root: str | None = None,
    explicit_adapter: str | None = None,
) -> RenameHint:
    """Return the rename hint for *name*, a refusal, or no hint.

    ``command`` is ``install`` or ``upgrade``. ``target_root`` is the ``--root``
    or ``--output`` value, and ``explicit_adapter`` the reporting ``install``'s
    ``--adapter``. Every failure to read the map yields no hint.
    """
    try:
        root = Path(catalogue_dir).resolve()
        if not _name_re().fullmatch(name):
            return NO_HINT
        target = _load_map(root, name)
        if target is None or not _target_is_pack(root, target):
            return NO_HINT
    except Exception:  # fail closed: any read, decode, parse or shape failure
        return NO_HINT

    shipped = _shipped_adapters()
    old_adapters = installed.adapters(name)
    if (
        not source
        or _is_unsafe_arg(source)
        or (target_root is not None and _is_unsafe_arg(target_root))
        or any(a not in shipped for a in old_adapters)
        or (explicit_adapter is not None and explicit_adapter not in shipped)
    ):
        return RenameHint(
            refusal=(
                f"{command}: the rename hint for '{name}' is withheld because "
                "the catalogue source, target root or an installed adapter "
                "name cannot be printed safely."
            )
        )

    printable = _is_printable_source(source)

    def step(
        sentences: list[str | None],
        *parts: str,
        root_flag: str,
        with_source: bool = True,
    ) -> list[str]:
        words = list(parts)
        if target_root is not None:
            words += [root_flag, target_root]
        lines = [s for s in sentences if s]
        if not with_source:
            return [*lines, recovery_command(*words)]
        if printable:
            return [*lines, recovery_command(*words, source)]
        return [*lines, PLACEHOLDER_SENTENCE, f"{recovery_command(*words)} {PLACEHOLDER}"]

    steps: list[list[str]] = []
    if old_adapters:
        for adapter in old_adapters:
            words = ["agentbundle", "uninstall", "--pack", name, "--scope", "repo"]
            if len(old_adapters) > 1:
                words += ["--adapter", adapter]
            steps.append(step([], *words, root_flag="--root", with_source=False))
        for adapter in old_adapters:
            sentence = _source_sentence(name, installed.sources[(name, adapter)], source)
            words = [
                "agentbundle", "install", "--pack", target, "--scope", "repo",
                "--adapter", adapter,
            ]
            steps.append(step([sentence], *words, root_flag="--output"))
    else:
        words = ["agentbundle", "install", "--pack", target, "--scope", "repo"]
        if explicit_adapter is not None:
            words += ["--adapter", explicit_adapter]
        steps.append(step([], *words, root_flag="--output"))

    notices: list[str] = []
    for pack in installed.names():
        if pack == name:
            continue
        escaped = escape_rendered_value(pack)
        try:
            if not _name_re().fullmatch(pack):
                raise ValueError("invalid pack name")
            relative = _find_pack_toml(root, pack)
            if relative is None:
                continue
            parsed = tomllib.loads(_read_pack_toml(root, relative).decode("utf-8"))
        except Exception:  # Unchecked: no step, one notice
            notices.append(
                f"Could not check installed pack '{escaped}' for a dependency "
                f"on '{target}'."
            )
            continue
        if not _requires(parsed, target):
            continue
        adapters = installed.adapters(pack)
        if any(a not in shipped for a in adapters):
            notices.append(
                f"Installed pack '{escaped}' has an adapter that is not a "
                "shipped adapter; upgrade it by hand."
            )
            continue
        for adapter in adapters:
            words = ["agentbundle", "upgrade", "--pack", pack, "--scope", "repo"]
            if len(adapters) > 1:
                words += ["--adapter", adapter]
            sentence = _source_sentence(pack, installed.sources[(pack, adapter)], source)
            steps.append(step([sentence], *words, root_flag="--root"))

    lines = [
        f"{command}: pack '{name}' was renamed to '{target}'.",
        "Run these steps to move to it:",
    ]
    if source_is_credential_bearing(source):
        lines.append(CREDENTIAL_SENTENCE)
    lines.extend(notices)
    for number, chunk in enumerate(steps, start=1):
        lines.extend(chunk[:-1])
        lines.append(f"  {number}. {chunk[-1]}")
    return RenameHint(lines=tuple(lines))


def hint_for_root(
    name: str,
    *,
    catalogue_dir: Path,
    source: str,
    root: Path,
    root_arg: str,
    command: str,
    explicit_adapter: str | None = None,
) -> RenameHint:
    """Build the hint reading the repo-scope state under *root*.

    ``root_arg`` is the raw ``--root`` or ``--output`` value. The default ``.``
    is not carried into the steps, because it names the working directory.
    An unreadable state yields no hint.
    """
    from agentbundle.config import ConfigError, load_state

    try:
        state = load_state(root / ".agentbundle-state.toml")
    except ConfigError:
        return NO_HINT
    return build_rename_hint(
        name,
        catalogue_dir=catalogue_dir,
        source=source,
        installed=Installed.from_state(state),
        command=command,
        target_root=None if root_arg == "." else root_arg,
        explicit_adapter=explicit_adapter,
    )


def print_not_found(message: str, hint: RenameHint) -> None:
    """Print the hint in place of *message*, or *message* then the refusal."""
    import sys

    if hint.lines:
        print("\n".join(hint.lines), file=sys.stderr)
        return
    print(message, file=sys.stderr)
    if hint.refusal:
        print(hint.refusal, file=sys.stderr)
