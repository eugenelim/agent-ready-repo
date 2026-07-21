"""Cursor adapter — full-parity native adapter (RFC-0026 / ADR-0015).

Projects every catalogue primitive to Cursor's native `.cursor/*` discovery
paths. Cursor's CLI and IDE share one `.cursor/` layout, so a single adapter
covers both. No new projection mode and no `adapter.schema.json` change: each
primitive reuses an already-enumerated mode, with two Cursor-specific inline
helpers for the parts a declarative mode can't express.

  - `skill`       → `direct-directory` → `.cursor/skills/<name>/`
  - `agent`       → `direct-file` + `cursor-agent-frontmatter-v0.11` →
                    `.cursor/agents/<name>.md`. Cursor subagents have no
                    per-agent tool allowlist, so `_project_agent_as_md` drops
                    the source `tools` and derives a `readonly` flag for
                    non-mutating agents (documented degradation, the ADR-0013
                    Copilot shape).
  - `hook-body`   → `direct-file` → `.cursor/hooks/<name>.{sh,py}`
  - `hook-wiring` → `merge-json` → an aggregated `.cursor/hooks.json`.
                    `_project_hooks_json` remaps each source event via the
                    contract `hook-event-map`, rewrites the hook-body path in
                    the command (`tools/hooks/`→`.cursor/hooks/`, where the
                    body actually lands), and adds the `version` key Cursor's
                    schema wants.
  - `command`     → `direct-file` → `.cursor/commands/<name>.md`
  - `kiro-ide-hook` → dropped (Kiro-only; declared in the contract's table form).

The adapter is scope-agnostic: it emits repo-relpaths (`.cursor/…`) at every
scope. Cursor's prefix is identical at repo and user scope (the claude-code/
codex pattern), so the user-scope home is the generic user-rooting of the
repo-relpath — there is no Cursor-specific prefix rewrite (unlike Copilot's
`.github/`→`.copilot/` divergence).
"""

from __future__ import annotations

import json
import shutil
import sys
import tomllib
from pathlib import Path
from typing import Any, Iterator

# RFC-0005 § Build-pipeline ordering invariant — uniform across adapters.
from agentbundle.build.phase_order import PHASE_ORDER as _PHASE_ORDER
from agentbundle.build.projections.direct_directory import sweep_orphans

_ADAPTER = "cursor"

# Cursor subagents inherit all parent tools; a `readonly: true` flag is the
# only way to restrict one. An agent is read-only when its declared tool set
# contains none of these mutating tools (RFC-0026 Open Q2 / spec AC9). `Bash`
# is deliberately not here — the `core` reviewers declare it and must stay
# read-only.
_MUTATING_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

# Copilot's hook-body retarget precedent: the source hook-wiring command
# references the body by its legacy `tools/hooks/` path, but cursor projects
# the body to `.cursor/hooks/` (`hook-body` direct-file). Rewrite the carried
# command so the emitted `hooks.json` references the script where it lands.
_LEGACY_HOOK_BODY_PREFIX = "tools/hooks/"
_CURSOR_HOOK_BODY_PREFIX = ".cursor/hooks/"


def project(pack_path: Path, contract: dict, output_root: Path) -> None:
    """Single-pack convenience wrapper. Delegates to `project_packs`."""
    project_packs([pack_path], contract, output_root)


def project_packs(pack_paths: list[Path], contract: dict, output_root: Path) -> None:
    """Project every pack in `pack_paths`, then run the shared orphan-sweep
    post-pass on the `skill` target (mirrors kiro_ide/claude_code)."""
    for pack_path in pack_paths:
        _project_single(pack_path, contract, output_root)
    _sweep_skill_orphans(pack_paths, contract, output_root)


def _iter_primitives(contract: dict) -> Iterator[str]:
    """Yield cursor's projected primitive names in phase order.

    Walks the `[[adapter.cursor.projection]]` array (the five standard
    primitives) and the `[adapter.cursor.projections.<primitive>]` table
    form (`kiro-ide-hook`). Skips any entry whose mode is `dropped`.
    """
    adapter_block = contract["adapter"][_ADAPTER]
    array_form = {entry["primitive"]: entry for entry in adapter_block.get("projection", [])}
    table_form = adapter_block.get("projections", {})
    if not isinstance(table_form, dict):
        table_form = {}

    for primitive_name in _PHASE_ORDER:
        if primitive_name in array_form:
            if array_form[primitive_name].get("mode") == "dropped":
                continue
            yield primitive_name
        elif primitive_name in table_form:
            rule = table_form[primitive_name]
            mode = rule.get("mode")
            if isinstance(mode, dict):
                mode = mode.get("repo")
            if mode == "dropped":
                continue
            yield primitive_name


def _project_single(pack_path: Path, contract: dict, output_root: Path) -> None:
    adapter_block = contract["adapter"][_ADAPTER]
    array_form = {entry["primitive"]: entry for entry in adapter_block.get("projection", [])}

    for primitive_name in _iter_primitives(contract):
        # All projected cursor primitives live in the array form; the only
        # table-form entry (kiro-ide-hook) is `dropped` and filtered above.
        rule = array_form[primitive_name]
        primitive = contract["primitive"][primitive_name]
        source_dir = pack_path / primitive["source-path"].rstrip("/")
        if not source_dir.exists():
            continue

        mode = rule["mode"]
        if mode == "direct-directory":
            _project_direct_directory(source_dir, output_root / rule["target-path"].rstrip("/"))
        elif mode == "direct-file":
            if primitive_name == "agent":
                _project_agent_as_md(source_dir, output_root, rule, contract)
            else:
                _project_direct_file(source_dir, output_root, rule["target-path"])
        elif mode == "merge-json":
            _project_hooks_json(source_dir, output_root, rule)
        else:
            raise ValueError(f"cursor: unhandled mode {mode!r} for {primitive_name}")


# ---------------------------------------------------------------------------
# skill / command / hook-body — direct copies
# ---------------------------------------------------------------------------


def _ignore_symlinks(directory: str, names: list[str]) -> set[str]:
    """`shutil.copytree` ignore callback: skip every symlink member.

    Drops **nested** symlinks during the copy so they are never reproduced in
    the output tree. Without this, a symlink inside a skill subdir would be
    copied as a symlink (`symlinks=True`) and later dereferenced by the
    install walker's `read_bytes()`, embedding out-of-tree content (e.g. a
    secret the symlink points at) into the projection. The top-level
    `is_symlink()` skip in `_project_direct_directory` only covers the skill
    root; this covers the subtree. (Build runs on trusted `packs/`; this is
    the install-from-untrusted-catalogue defense — mirrored in all five
    direct-directory adapters.)
    """
    base = Path(directory)
    return {name for name in names if (base / name).is_symlink()}


def _project_direct_directory(source_dir: Path, target_dir: Path) -> None:
    for entry in sorted(source_dir.iterdir()):
        # Defense-in-depth: `lint-packs` rejects symlink-bearing packs, but a
        # direct `project_packs` caller bypasses that gate.
        if entry.is_symlink():
            continue
        if entry.is_dir():
            destination = target_dir / entry.name
            if destination.is_symlink():
                destination.unlink()
            elif destination.exists():
                shutil.rmtree(destination)
            # `ignore=_ignore_symlinks` drops nested symlinks (see above);
            # `symlinks` is then moot since none survive the filter.
            shutil.copytree(entry, destination, ignore=_ignore_symlinks)


def _project_direct_file(source_dir: Path, output_root: Path, target_prefix: str) -> None:
    target_dir = output_root / target_prefix.rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source_dir.iterdir()):
        if entry.is_file():
            shutil.copy2(entry, target_dir / entry.name, follow_symlinks=False)


def _skill_direct_directory_target(contract: dict, output_root: Path) -> Path | None:
    for entry in contract["adapter"][_ADAPTER].get("projection", []):
        if entry.get("primitive") == "skill" and entry.get("mode") == "direct-directory":
            return output_root / entry["target-path"].rstrip("/")
    return None


def _sweep_skill_orphans(pack_paths: list[Path], contract: dict, output_root: Path) -> None:
    target_dir = _skill_direct_directory_target(contract, output_root)
    if target_dir is None:
        return
    skill_source_path = contract["primitive"]["skill"]["source-path"].rstrip("/")
    expected_names: set[str] = set()
    for pack_path in pack_paths:
        source_dir = pack_path / skill_source_path
        if not source_dir.exists():
            continue
        for entry in source_dir.iterdir():
            if entry.is_dir():
                expected_names.add(entry.name)
    sweep_orphans(target_dir, expected_names)


# ---------------------------------------------------------------------------
# agent .md → .md (tools dropped, readonly derived)
# ---------------------------------------------------------------------------


def _project_agent_as_md(
    source_dir: Path,
    output_root: Path,
    rule: dict,
    contract: dict,
) -> None:
    """Read `.apm/agents/<name>.md` and emit `.cursor/agents/<name>.md`.

    The output preserves the markdown body and rewrites the frontmatter to
    Cursor's subagent vocabulary: `name` / `description` / `model` pass
    through (identity renames from the `cursor-agent-frontmatter-v0.11`
    mapping; `name` falls back to the filename), the source `tools` is dropped,
    and a `readonly: true` flag is emitted for non-mutating agents. No
    Claude/Kiro/Copilot-only key (`tools`, `is_background`, `hooks`, …)
    appears in the output.
    """
    target_dir = output_root / rule["target-path"].rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)

    mapping_name = rule.get("frontmatter-mapping")
    mapping = (
        contract.get("frontmatter-mapping", {}).get(mapping_name, {})
        if mapping_name
        else {}
    )

    for entry in sorted(source_dir.iterdir()):
        if not (entry.is_file() and entry.suffix == ".md"):
            continue
        frontmatter, body = _split_frontmatter(entry.read_text(encoding="utf-8"))

        out_fm: dict[str, Any] = {}
        # Emit only the keys the mapping declares (name/description/model for
        # cursor) — a whitelist that drops `tools` and anything else not in
        # Cursor's frontmatter vocabulary. Mapping order (tomllib-preserved)
        # gives name → description → model.
        for source_key, key_rule in mapping.items():
            new_key = key_rule.get("rename", source_key)
            if source_key == "name":
                out_fm[new_key] = frontmatter.get(source_key) or entry.stem
            elif source_key in frontmatter:
                out_fm[new_key] = frontmatter[source_key]

        readonly = _derive_readonly(frontmatter)
        if readonly is not None:
            out_fm["readonly"] = readonly

        output_text = _serialize_frontmatter_md(out_fm) + body
        (target_dir / entry.name).write_text(output_text, encoding="utf-8", newline="\n")


def _derive_readonly(frontmatter: dict[str, Any]) -> bool | None:
    """Return `True` to emit `readonly: true`, or `None` to omit the flag.

    `True` — a `tools:` list is declared and contains no mutating tool: the
             agent is read-only and Cursor must be told so.
    `None` — every other case (a `tools:` list with a mutating tool, or no
             `tools:` list at all): the agent inherits all tools and is
             writable, which is Cursor's default — so the flag is omitted
             rather than emitted as `readonly: false` (RFC-0026: derive
             read-only for non-mutating agents, "otherwise inherit-all").
             Emitting `readonly: true` for a writable agent would wrongly
             restrict it; emitting `readonly: false` is redundant noise.
    """
    raw = frontmatter.get("tools")
    if raw is None:
        return None
    if isinstance(raw, list):
        tools = {str(item).strip() for item in raw if str(item).strip()}
    else:
        tools = {item.strip() for item in str(raw).split(",") if item.strip()}
    if tools & _MUTATING_TOOLS:
        return None
    return True


# ---------------------------------------------------------------------------
# hook-wiring → aggregated .cursor/hooks.json (event-remapped, version-keyed)
# ---------------------------------------------------------------------------


def _project_hooks_json(source_dir: Path, output_root: Path, rule: dict) -> None:
    """Merge every `.apm/hook-wiring/<name>.toml` into `.cursor/hooks.json`.

    Cursor's shape is `{"version": 1, "hooks": {<cursorEvent>: [{"command":
    …}]}}`. The shared `merge_json` projection can't produce it (no event
    remap, no `version` key), so this Cursor-specific helper does both:

      - Source events use Claude-native PascalCase (`SessionStart`, …) and are
        translated through the contract `hook-event-map`; a source event with
        no entry is dropped with a build-time log line (fail-open — the
        no-silent-caps rule, deliberately unlike copilot's fail-closed map).
      - The carried command's legacy `tools/hooks/` hook-body prefix is
        rewritten to `.cursor/hooks/`, where the body actually lands.

    The merge is managed-key-only: it preserves the adopter's other top-level
    keys in an existing `hooks.json` and any unmanaged events under the
    managed key, replacing only the events this wiring owns.
    """
    target_path = output_root / rule["target-path"].lstrip("/")
    managed_key = rule.get("managed-key", "hooks")
    event_map = rule.get("hook-event-map", {})

    incoming: dict[str, list[dict]] = {}
    for entry in sorted(source_dir.iterdir()):
        if not (entry.is_file() and entry.suffix == ".toml"):
            continue
        payload = tomllib.loads(entry.read_text(encoding="utf-8"))
        events = payload.get(managed_key, {})
        for source_event in sorted(events):
            cursor_event = event_map.get(source_event)
            if cursor_event is None:
                print(
                    f"cursor: dropping hook event {source_event!r} — no entry in "
                    f"hook-event-map ({', '.join(sorted(event_map)) or 'empty'}); "
                    f"source file {entry.name}",
                    file=sys.stderr,
                )
                continue
            handlers = incoming.setdefault(cursor_event, [])
            for outer in events[source_event]:
                for handler in outer.get("hooks", []):
                    handler_type = handler.get("type")
                    command = handler.get("command")
                    if handler_type != "command" or not isinstance(command, str):
                        # Drop with a build-time log rather than silently — the
                        # same no-silent-caps stance as the unmapped-event drop
                        # above (copilot fails closed here; cursor stays fail-open
                        # with a log, consistent with decision 4's event handling).
                        print(
                            f"cursor: dropping malformed hook handler for event "
                            f"{source_event!r} in {entry.name} — expected "
                            f'`type = "command"` + string `command`, got '
                            f"type={handler_type!r}, command={command!r}",
                            file=sys.stderr,
                        )
                        continue
                    handlers.append({"command": _rewrite_hook_body_path(command)})

    if not incoming:
        return

    existing: dict[str, Any] = {}
    if target_path.exists():
        existing = json.loads(target_path.read_text(encoding="utf-8"))

    merged = dict(existing.get(managed_key, {}))
    merged.update(incoming)
    existing[managed_key] = merged
    existing.setdefault("version", 1)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(existing, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n",
    )


def _rewrite_hook_body_path(command: str) -> str:
    return command.replace(_LEGACY_HOOK_BODY_PREFIX, _CURSOR_HOOK_BODY_PREFIX)


# ---------------------------------------------------------------------------
# frontmatter helpers — duplicated from kiro.py per the sibling-projection
# convention (do not reach across module privates).
# ---------------------------------------------------------------------------


def _split_frontmatter(text: str) -> tuple[dict, str]:
    lines = text.splitlines(keepends=True)
    if not lines or not lines[0].startswith("---"):
        return {}, text
    end_index = None
    for index in range(1, len(lines)):
        if lines[index].startswith("---"):
            end_index = index
            break
    if end_index is None:
        return {}, text
    frontmatter_lines = lines[1:end_index]
    body = "".join(lines[end_index + 1 :])
    return _parse_frontmatter(frontmatter_lines), body


def _parse_frontmatter(lines: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line in lines:
        stripped = line.rstrip("\n")
        if not stripped.strip() or stripped.lstrip().startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [item.strip() for item in value[1:-1].split(",") if item.strip()]
            result[key.strip()] = items
        else:
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            result[key.strip()] = value
    return result


def _serialize_frontmatter_md(fields: dict[str, Any]) -> str:
    """Emit a YAML frontmatter block for a cursor `.md` agent file.

    Booleans render lower-cased (`readonly: true`, not Python's `True`) so the
    output is valid YAML/JSON — the kiro_ide serializer this borrows has no
    bool branch and its `else` would render `True`. Strings with YAML-special
    characters are double-quoted; lists render as flow sequences.
    """
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, list):
            items = ", ".join(str(item) for item in value)
            lines.append(f"{key}: [{items}]")
        elif isinstance(value, str):
            if any(char in value for char in ":#{}[]|>&*!,'\""):
                escaped = value.replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'{key}: "{escaped}"')
            else:
                lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"
