"""``agentbundle show <pack>`` subcommand.

Answers "what skills and agents does pack X contain?" by walking the pack's
``.apm/`` source tree **live** on each call (ADR-0049 / RFC-0060): nothing is
persisted and no manifest is touched, so the answer cannot drift from what the
pack actually ships.

Two honest, state-differentiated sources:

  - **Primary — catalogue.** Resolve the pack in the active catalogue, walk
    ``.apm/skills/`` and ``.apm/agents/``, and print the pack's ``pack.toml``
    metadata alongside its full, sorted skill + agent inventory
    (``source: catalogue``).
  - **Degrade — install state.** When the catalogue is unresolvable, an
    *installed* pack still yields its inventory from the install-state file —
    the union of skill/agent names across every adapter row in both the user
    and repo scope (``source: installed-state``) — while a *not-installed* pack
    fails with a one-line error, because there is no source to read.

``--format json`` emits the same as a single stable object for programmatic
consumers. The inventory is never filtered (``show`` reports what *exists*, not
what a user can invoke), and it is the full, untagged set — every skill under
``.apm/skills/``, not the ``[pack.evals].skills`` subset.

Exit codes:
  0  — success (catalogue path or installed-state fallback).
  1  — unknown pack, or unresolvable-catalogue-and-not-installed (one-line
       stderr, empty stdout — including under ``--format json``).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

    from agentbundle.config import State


def run(args: "argparse.Namespace") -> int:
    """Entry point for ``agentbundle show``."""
    from agentbundle.catalogue import CatalogueError, resolve_catalogue
    from agentbundle.commands._common import resolve_catalogue_uri
    from agentbundle.pack_inventory import agent_names, skill_names

    pack_name: str = args.pack
    fmt: str = getattr(args, "format", "table")

    # ── Resolve the catalogue (authoritative primary source) ──────────────────
    try:
        catalogue_dir = resolve_catalogue(resolve_catalogue_uri(args))
    except CatalogueError:
        # Honest, state-differentiated degrade (ADR-0049).
        return _degrade(args, pack_name, fmt)

    # ── Name-match the pack in the catalogue ──────────────────────────────────
    match = _find_pack_dir(catalogue_dir, pack_name)
    if match is None:
        print(f"show: pack {pack_name!r} not found in catalogue", file=sys.stderr)
        return 1

    pack_dir, toml = match
    pack = toml.get("pack", {})
    _emit(
        fmt,
        name=pack.get("name") or pack_dir.name,
        # Pass metadata through as-is: an *absent* key is null; a present
        # (even empty) value is not coerced, so "declared empty" and "absent"
        # stay distinguishable on the authoritative catalogue path.
        version=pack.get("version"),
        description=pack.get("description"),
        skills=skill_names(pack_dir),
        agents=agent_names(pack_dir),
        source="catalogue",
    )
    return 0


# ---------------------------------------------------------------------------
# Primary path — catalogue lookup
# ---------------------------------------------------------------------------


def _find_pack_dir(catalogue_dir: Path, pack_name: str) -> tuple[Path, dict] | None:
    """Return ``(pack_dir, parsed pack.toml)`` for *pack_name*, or None.

    Reuses ``list-packs``' ``_discover_pack_dirs`` so the accepted catalogue
    layouts stay identical, then matches on the pack's declared ``[pack].name``
    (falling back to the directory name) — the step the AC5 "unknown pack" path
    depends on.
    """
    from agentbundle.commands.list_packs import _discover_pack_dirs
    from agentbundle.config import ConfigError, load_pack_toml

    for pack_dir in _discover_pack_dirs(catalogue_dir):
        try:
            toml = load_pack_toml(pack_dir / "pack.toml")
        except ConfigError:
            continue
        # A declared ``[pack].name`` is authoritative (list-packs keys display
        # on it); fall back to the directory name only when it is absent, so a
        # coincidental dir-name match never shadows a pack declaring a different
        # name.
        name = toml.get("pack", {}).get("name") or pack_dir.name
        if name == pack_name:
            return pack_dir, toml
    return None


# ---------------------------------------------------------------------------
# Degrade path — install-state fallback
# ---------------------------------------------------------------------------


def _degrade(args: "argparse.Namespace", pack_name: str, fmt: str) -> int:
    """Recover the inventory from the install state when the catalogue is gone.

    Reads both the user and repo scope (mirroring ``list-installed``). An
    *installed* pack yields the union of skill/agent names across every adapter
    row in both scopes, deduped + sorted (``source: installed-state``, metadata
    null); a *not-installed* pack errors and exits non-zero.
    """
    states = _load_states(args)
    if not any(state.has_pack(pack_name) for state in states):
        print(
            f"show: catalogue unavailable and pack {pack_name!r} is not installed",
            file=sys.stderr,
        )
        return 1

    skills: set[str] = set()
    agents: set[str] = set()
    for state in states:
        for pack_state in state.rows_for_pack(pack_name).values():
            for relpath in pack_state.files:
                skill = _skill_from_relpath(relpath)
                if skill:
                    skills.add(skill)
                agent = _agent_from_relpath(relpath)
                if agent:
                    agents.add(agent)

    _emit(
        fmt,
        name=pack_name,  # the argument passed to `show`; state has no pack name
        version=None,  # inventory-only fallback — never fabricated from state
        description=None,
        skills=sorted(skills),
        agents=sorted(agents),
        source="installed-state",
    )
    return 0


def _load_states(args: "argparse.Namespace") -> list["State"]:
    """Load the user- and repo-scope install-state files, read-only.

    Mirrors ``list-installed``'s two-scope gather: user
    (``~/.agentbundle/state.toml`` via ``scope.resolve_user_root``) and repo
    (``<--root>/.agentbundle-state.toml``). An unresolvable user home is skipped;
    an absent state file loads as an empty ``State``; a legacy/incompatible file
    (``StateFileLegacy`` — a ``ConfigError``) is skipped, not fatal.
    """
    from agentbundle import scope as scope_mod
    from agentbundle.config import ConfigError, load_state

    candidates: list[tuple[str, Path]] = []
    try:
        user_root = scope_mod.resolve_user_root()
    except scope_mod.UserScopeUnresolvable:
        pass
    else:
        candidates.append(("user", user_root / ".agentbundle" / "state.toml"))
    repo_root = Path(getattr(args, "root", ".") or ".").resolve()
    candidates.append(("repo", repo_root / ".agentbundle-state.toml"))

    states: list["State"] = []
    for scope_name, path in candidates:
        try:
            states.append(load_state(path))
        except ConfigError as exc:
            # Mirror `list-installed`: a legacy/incompatible state file is
            # warned-and-skipped, not silently dropped — otherwise an installed
            # pack whose only row lives there would masquerade as not-installed
            # on this degrade path with no hint why.
            print(f"show: skipping {scope_name} scope: {exc}", file=sys.stderr)
    return states


def _skill_from_relpath(relpath: str) -> str | None:
    """Skill name = the path segment immediately after a ``skills/`` component.

    Layout-agnostic across ``.claude/skills/``, the shared ``.agents/skills/``
    (codex/copilot/cursor/gemini), and ``.kiro/skills/``. Any projected file
    under ``skills/<name>/`` maps to ``<name>``; the caller dedupes.
    """
    parts = Path(relpath).parts
    for i, part in enumerate(parts):
        if part == "skills" and i + 1 < len(parts):
            return parts[i + 1]
    return None


def _agent_from_relpath(relpath: str) -> str | None:
    """Agent name = the filename directly under an ``agents/`` component, with
    its extension stripped by an **extension-agnostic** rule.

    Strip a trailing ``.agent.md`` (copilot's double-suffix) if present, else
    ``Path.stem`` (the single final extension). Recovers ``<n>`` uniformly from
    ``.claude/agents/<n>.md``, ``.codex/agents/<n>.toml``,
    ``.kiro/agents/<n>.json``, and ``.github/agents/<n>.agent.md`` — so
    co-installed adapter rows dedupe to one entry.
    """
    path = Path(relpath)
    parts = path.parts
    # A top-level ``agents/`` component only — never an ``agents/`` dir nested
    # inside a skill's payload (``.../skills/<n>/agents/helper.md``), which would
    # surface a phantom agent.
    if len(parts) >= 2 and parts[-2] == "agents" and "skills" not in parts:
        name = path.name
        if name.endswith(".agent.md"):
            return name[: -len(".agent.md")]
        return path.stem
    return None


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _emit(
    fmt: str,
    *,
    name: str,
    version: str | None,
    description: str | None,
    skills: list[str],
    agents: list[str],
    source: str,
) -> None:
    """Render the inventory as a table block or a single JSON object."""
    if fmt == "json":
        import json

        obj = {
            "name": name,
            "version": version,
            "description": description,
            "skills": skills,
            "agents": agents,
            "source": source,
        }
        print(json.dumps(obj))
        return

    from agentbundle.commands._common import render_table

    rows: list[list[str]] = [["name", name]]
    # Fallback (installed-state) omits version/description — the state has neither.
    if version is not None:
        rows.append(["version", version])
    if description is not None:
        rows.append(["description", description])
    rows.append(["skills", ", ".join(skills) if skills else "-"])
    rows.append(["agents", ", ".join(agents) if agents else "-"])
    render_table(["FIELD", "VALUE"], rows, wrap_col=1)
    if source != "catalogue":
        print(f"source: {source} (catalogue unavailable)")
