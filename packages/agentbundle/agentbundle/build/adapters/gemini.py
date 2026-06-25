"""Gemini adapter — full-parity native adapter (RFC-0027 / ADR-0016).

Projects every catalogue primitive to Gemini CLI's native `.gemini/*` discovery
paths at both repo and user scope:

  - `skill`       → `direct-directory` → `.gemini/skills/<name>/`
  - `agent`       → `direct-file` + `gemini-agent-frontmatter` →
                    `.gemini/agents/<name>.md`. Unlike Cursor, Gemini has a real
                    per-agent tool allowlist, so `_project_agent_as_md` **keeps**
                    the source `tools` and name-maps each to a Gemini tool id
                    (dropping an unmapped token with a build-time log), and maps
                    `model` aliases to Gemini model ids (tier-preserving).
  - `hook-body`   → `direct-file` → `.gemini/hooks/<name>.{sh,py}` (the Cursor
                    model — under `.gemini/` so a single prefix fences it at both
                    scopes; the wiring command is path-rewritten to match).
  - `hook-wiring` → `merge-json` → an aggregated `.gemini/settings.json`.
                    `_project_settings_json` writes BOTH the `hooks` map
                    (event-remapped via the contract `hook-event-map`, FAIL-CLOSED
                    on an unmapped event — the copilot precedent) AND a static
                    `context.fileName` bridge (from the rule's `context-filenames`),
                    in one managed-merge that preserves adopter keys. Single-writer
                    (cursor model): written only when the pack ships hook-wiring, so
                    the `context` bridge rides in that write — `core` ships both the
                    wiring and `AGENTS.md`. (Repo-scope install writes merge-json
                    targets whole-file, so a per-pack settings.json would clobber
                    another pack's hooks.)
  - `command`     → `gemini-command-toml` → `.gemini/commands/<...>/<name>.toml`.
  - `kiro-ide-hook` → dropped (Kiro-only; declared in the contract's table form).

The adapter is scope-agnostic: it emits repo-relpaths (`.gemini/…`) at every scope.
Gemini's prefix is identical at repo and user scope (the claude-code/cursor pattern),
so the user-scope home is the generic user-rooting of the repo-relpath — there is no
Gemini-specific prefix rewrite. Distribution-only (not in SELF_HOST_ADAPTERS).
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
from agentbundle.build.projections.gemini_command_toml import (
    project_gemini_command_toml,
)

_ADAPTER = "gemini"

# The hook body lands under `.gemini/hooks/` (AC2), but the shipped hook-wiring
# command references it by its legacy `tools/hooks/` path. Rewrite the carried
# command so the emitted settings.json points where the body actually lands —
# the cursor.py `_rewrite_hook_body_path` precedent.
_LEGACY_HOOK_BODY_PREFIX = "tools/hooks/"
_GEMINI_HOOK_BODY_PREFIX = ".gemini/hooks/"


def project(pack_path: Path, contract: dict, output_root: Path) -> None:
    """Single-pack convenience wrapper. Delegates to `project_packs`."""
    project_packs([pack_path], contract, output_root)


def project_packs(pack_paths: list[Path], contract: dict, output_root: Path) -> None:
    """Project every pack, then run the shared post-passes: the skill orphan-sweep
    and the single `.gemini/settings.json` managed-merge (hooks + context)."""
    for pack_path in pack_paths:
        _project_single(pack_path, contract, output_root)
    _sweep_skill_orphans(pack_paths, contract, output_root)
    _project_settings_json(pack_paths, contract, output_root)


def _iter_primitives(contract: dict) -> Iterator[str]:
    """Yield gemini's projected primitive names in phase order (skipping dropped
    and `hook-wiring`, which the settings post-pass owns)."""
    adapter_block = contract["adapter"][_ADAPTER]
    array_form = {entry["primitive"]: entry for entry in adapter_block.get("projection", [])}
    table_form = adapter_block.get("projections", {})
    if not isinstance(table_form, dict):
        table_form = {}

    for primitive_name in _PHASE_ORDER:
        # hook-wiring is written by `_project_settings_json` as a post-pass, not
        # in the per-primitive loop (it must merge hooks + the static context key
        # in a single write).
        if primitive_name == "hook-wiring":
            continue
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
        elif mode == "gemini-command-toml":
            project_gemini_command_toml(source_dir, output_root, rule)
        else:
            raise ValueError(f"gemini: unhandled mode {mode!r} for {primitive_name}")


# ---------------------------------------------------------------------------
# skill / hook-body — direct copies (symlink-hardened, mirrors cursor.py)
# ---------------------------------------------------------------------------


def _ignore_symlinks(directory: str, names: list[str]) -> set[str]:
    """`shutil.copytree` ignore callback: skip every symlink member (drops nested
    symlinks so the install walker can't read through them to embed out-of-tree
    content). The cursor.py precedent."""
    base = Path(directory)
    return {name for name in names if (base / name).is_symlink()}


def _project_direct_directory(source_dir: Path, target_dir: Path) -> None:
    for entry in sorted(source_dir.iterdir()):
        if entry.is_symlink():
            continue
        if entry.is_dir():
            destination = target_dir / entry.name
            if destination.is_symlink():
                destination.unlink()
            elif destination.exists():
                shutil.rmtree(destination)
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
# agent .md → .md (tools KEPT + name-mapped, model tier-mapped)
# ---------------------------------------------------------------------------


def _project_agent_as_md(
    source_dir: Path,
    output_root: Path,
    rule: dict,
    contract: dict,
) -> None:
    """Read `.apm/agents/<name>.md` and emit `.gemini/agents/<name>.md`.

    Preserves the markdown body and rewrites the frontmatter to Gemini's subagent
    vocabulary via `gemini-agent-frontmatter`: `name`/`description` pass through
    (identity renames; `name` falls back to the filename), `tools` is name-mapped
    per element (unmapped token dropped with a build-time log; collisions
    de-duplicated), and `model` aliases map to Gemini model ids (an unmapped value
    is dropped). Only keys the mapping declares appear in the output.
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
        out_fm = _apply_mapping(frontmatter, mapping, entry.stem)
        output_text = _serialize_frontmatter_md(out_fm) + body
        (target_dir / entry.name).write_text(output_text, encoding="utf-8", newline="\n")


def _apply_mapping(
    frontmatter: dict[str, Any], mapping: dict[str, Any], filename_stem: str
) -> dict[str, Any]:
    """Apply the `gemini-agent-frontmatter` rename / normalize / values rules.

    Mapping order (tomllib-preserved) gives name → description → tools → model.
    A `to-list` `tools` rule splits comma strings, maps each token through
    `values` (dropping an unmapped token with a stderr log), and de-duplicates
    translated values. A scalar `model` maps through `values` (dropping an
    unmapped value entirely). `name` falls back to the filename stem.
    """
    out: dict[str, Any] = {}
    for source_key, key_rule in mapping.items():
        new_key = key_rule.get("rename", source_key)
        if source_key == "name":
            out[new_key] = frontmatter.get(source_key) or filename_stem
            continue
        if source_key not in frontmatter:
            continue
        value = frontmatter[source_key]
        normalize = key_rule.get("normalize")
        values_map = key_rule.get("values")
        if normalize == "to-list":
            if isinstance(value, list):
                tokens = [str(item).strip() for item in value if str(item).strip()]
            else:
                tokens = [item.strip() for item in str(value).split(",") if item.strip()]
            if isinstance(values_map, dict):
                mapped: list[str] = []
                for token in tokens:
                    if token in values_map:
                        translated = values_map[token]
                        if translated not in mapped:
                            mapped.append(translated)
                    else:
                        print(
                            f"gemini: dropping {new_key} entry {token!r} — not in "
                            f"contract values map for source key {source_key!r}",
                            file=sys.stderr,
                        )
                value = mapped
            else:
                value = tokens
            # Omit an empty `tools` rather than emit `tools: []`. An empty list
            # in Gemini's allowlist plausibly means "no tools permitted" (a silent
            # degrade); omitting the key lets Gemini apply its default — matching
            # the `model`-absent → omitted precedent (AC6). Fires only when every
            # declared tool was unmapped (each already logged above).
            if isinstance(value, list) and not value:
                continue
        elif isinstance(values_map, dict):
            if isinstance(value, str) and value in values_map:
                value = values_map[value]
            else:
                print(
                    f"gemini: dropping {new_key}={value!r} — not in contract values "
                    f"map for source key {source_key!r}",
                    file=sys.stderr,
                )
                continue
        out[new_key] = value
    return out


# ---------------------------------------------------------------------------
# hook-wiring + context bridge → single .gemini/settings.json managed-merge
# ---------------------------------------------------------------------------


def _hook_wiring_rule(contract: dict) -> dict | None:
    for entry in contract["adapter"][_ADAPTER].get("projection", []):
        if entry.get("primitive") == "hook-wiring":
            return entry
    return None


def _project_settings_json(
    pack_paths: list[Path], contract: dict, output_root: Path
) -> None:
    """Write the `hooks` wiring AND the static `context.fileName` bridge into one
    `.gemini/settings.json` in a single managed-merge (AC8).

    `hooks`: every `.apm/hook-wiring/<name>.toml` across all packs is aggregated;
    each source event is translated through the contract `hook-event-map`
    (FAIL-CLOSED — an unmapped event raises `ValueError`, never a silent drop),
    the carried command's `tools/hooks/` prefix is rewritten to `.gemini/hooks/`,
    and a source `matcher` passes through unchanged.

    `context`: `context.fileName` is set from the rule's `context-filenames`,
    written in this same single hook-wiring settings.json write (single-writer —
    see the `if not incoming: return` guard below). In the catalogue the base
    `core` pack ships both the wiring and `AGENTS.md`, so the bridge lands when the
    file it points at exists.

    The merge is managed-key-only: it preserves the adopter's other top-level keys
    and any unmanaged events / context sub-keys, replacing only what this adapter
    owns. Written once.
    """
    rule = _hook_wiring_rule(contract)
    if rule is None:
        return
    managed_key = rule.get("managed-key", "hooks")
    event_map = rule.get("hook-event-map", {})
    context_filenames = rule.get("context-filenames", [])
    primitive = contract["primitive"]["hook-wiring"]
    wiring_source = primitive["source-path"].rstrip("/")

    incoming: dict[str, list[dict]] = {}
    for pack_path in pack_paths:
        source_dir = pack_path / wiring_source
        if not source_dir.exists():
            continue
        for entry in sorted(source_dir.iterdir()):
            if not (entry.is_file() and entry.suffix == ".toml") or entry.is_symlink():
                continue
            payload = tomllib.loads(entry.read_text(encoding="utf-8"))
            events = payload.get(managed_key, {})
            for source_event in sorted(events):
                gemini_event = event_map.get(source_event)
                if gemini_event is None:
                    raise ValueError(
                        f"gemini: hook event {source_event!r} in {entry.name} has no "
                        f"entry in the contract hook-event-map "
                        f"({', '.join(sorted(event_map)) or 'empty'}); refusing to "
                        f"emit an unrecognised event (fail-closed)"
                    )
                for outer in events[source_event]:
                    out_entry = _translate_hook_entry(outer, source_event, entry.name)
                    incoming.setdefault(gemini_event, []).append(out_entry)

    # Write `.gemini/settings.json` only when this pack ships hook-wiring (the
    # cursor `_project_hooks_json` `if not incoming: return` model). Repo-scope
    # install writes merge-json targets **whole-file** (no install-time JSON
    # merge) and the adapter renders into an isolated tempdir, so a pack that
    # emits a settings.json would *overwrite* — not merge — any other pack's
    # settings.json, clobbering its hooks. Gating the write on hook-wiring
    # presence keeps `.gemini/settings.json` single-writer per install root
    # (exactly as `.cursor/hooks.json` / `.claude/settings.local.json` are), so
    # no cross-pack clobber. The `context.fileName` bridge rides in this same
    # write — in the catalogue the base `core` pack ships both the session-start
    # wiring AND `AGENTS.md` (as a seed), so the bridge lands precisely when the
    # `AGENTS.md` it points at exists.
    if not incoming:
        return

    target_path = output_root / rule["target-path"].lstrip("/")
    existing: dict[str, Any] = {}
    if target_path.exists():
        existing = json.loads(target_path.read_text(encoding="utf-8"))

    merged_hooks = dict(existing.get(managed_key, {}))
    merged_hooks.update(incoming)
    existing[managed_key] = merged_hooks

    # The context bridge is managed but additive: own `fileName`, preserve any
    # adopter-authored context sub-keys.
    context = dict(existing.get("context", {}))
    context["fileName"] = list(context_filenames)
    existing["context"] = context

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(existing, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n",
    )


def _translate_hook_entry(outer: dict, source_event: str, source_name: str) -> dict:
    """Translate one source hook entry to Gemini's shape: preserve a `matcher`
    (regex on BeforeTool/AfterTool) unchanged, rewrite each handler command's
    hook-body path. Fail-closed on a malformed handler (the copilot precedent)."""
    out_entry: dict[str, Any] = {}
    if "matcher" in outer:
        out_entry["matcher"] = outer["matcher"]
    handlers: list[dict] = []
    for handler in outer.get("hooks", []):
        handler_type = handler.get("type")
        command = handler.get("command")
        if handler_type != "command" or not isinstance(command, str):
            raise ValueError(
                f"gemini: {source_name}: hook handler for event {source_event!r} "
                f'must declare `type = "command"` and a string `command`; got '
                f"type={handler_type!r}, command={command!r}"
            )
        handlers.append(
            {"type": "command", "command": _rewrite_hook_body_path(command)}
        )
    out_entry["hooks"] = handlers
    return out_entry


def _rewrite_hook_body_path(command: str) -> str:
    return command.replace(_LEGACY_HOOK_BODY_PREFIX, _GEMINI_HOOK_BODY_PREFIX)


# ---------------------------------------------------------------------------
# frontmatter helpers — duplicated per the sibling-projection convention
# (do not reach across module privates).
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
    """Emit a YAML frontmatter block for a gemini `.md` agent file. Lists render
    as flow sequences; strings with YAML-special characters are double-quoted."""
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
