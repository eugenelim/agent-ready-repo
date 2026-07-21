"""Kiro adapter — underlying JSON projection shared by kiro-cli and the kiro alias.

RFC-0022: the `kiro` contract adapter is a deprecated alias for `kiro-ide`.
This module (`kiro.py`) now serves as the shared implementation layer used by:
  - `kiro_cli.py` — CLI target, JSON agents with CLI short-name tool tokens.
  - `kiro_ide.py` — imports `_split_frontmatter`, `_apply_mapping`, and the
    direct-file helpers; overrides agent projection to emit `.md`.
  - `kiro` alias — deprecated alias that calls `kiro_ide.project`.

Per RFC-0005 § Build-pipeline ordering invariant, primitives project in
the fixed order **`hook-body` → `agent` → `hook-wiring` → `command` →
`skill`** within each pack. The order matters because Kiro's
`merge-into-agent-json` projection reads the agent JSON the agent
primitive's projection wrote — agents must land first.

When used directly (for the kiro alias / kiro-cli path), agents project as
`.kiro/agents/<name>.json`. The `kiro-ide-agent-frontmatter-v0.9` mapping
table (renamed from `kiro-agent-frontmatter-v0.9` in T1) is reinterpreted as
*frontmatter-key → JSON-field* rather than *frontmatter → frontmatter*.

Hook-wiring projection delegates to
`agentbundle.build.projections.merge_into_agent_json` per RFC-0005.
"""

from __future__ import annotations

import json
import shutil
import sys
import tomllib
from pathlib import Path
from typing import Any, Iterator

from agentbundle.build.projections.merge_into_agent_json import (
    project as merge_into_agent_json_project,
)
from agentbundle.build.projections.kiro_ide_hook import (
    project as kiro_ide_hook_project,
)


# Phase order from RFC-0005 § Build-pipeline ordering invariant.
# `agent` precedes `hook-wiring` so `merge-into-agent-json` finds the
# agent JSON in place. `command` and `skill` land last; their position
# relative to wiring is free (neither reads the agent JSON during
# projection), so the predictable trailing position keeps the phases
# uniform across adapters.
from agentbundle.build.phase_order import PHASE_ORDER as _PHASE_ORDER
from agentbundle.build.projections.direct_directory import sweep_orphans


def _iter_primitives(contract: dict) -> Iterator[str]:
    """Yield Kiro's projected primitive names in phase order.

    Walks both the legacy `[[adapter.kiro.projection]]` array (v0.2
    primitives that didn't migrate to the new shape) and the v0.3
    `[adapter.kiro.projections.<primitive>]` table form (hook-body and
    hook-wiring per RFC-0005). Skipped: primitives whose mode is
    `dropped` — they have no projection work.

    Returns an iterator in PHASE_ORDER so callers (project,
    test_pipeline_phase_order) get a deterministic sequence.
    """
    adapter_block = contract["adapter"]["kiro"]
    array_form = {entry["primitive"]: entry for entry in adapter_block.get("projection", [])}
    table_form = adapter_block.get("projections", {}) if isinstance(adapter_block.get("projections"), dict) else {}

    for primitive_name in _PHASE_ORDER:
        if primitive_name in array_form:
            mode = array_form[primitive_name].get("mode")
            if mode == "dropped":
                continue
            yield primitive_name
        elif primitive_name in table_form:
            rule = table_form[primitive_name]
            effective_mode = rule.get("mode")
            if isinstance(effective_mode, dict):
                effective_mode = effective_mode.get("repo")
            if effective_mode == "dropped":
                continue
            yield primitive_name


def project(pack_path: Path, contract: dict, output_root: Path) -> None:
    """Single-pack convenience wrapper. Delegates to `project_packs`."""
    project_packs([pack_path], contract, output_root)


def project_packs(pack_paths: list[Path], contract: dict, output_root: Path) -> None:
    """Project every pack in `pack_paths` in order, then run the
    shared orphan-sweep post-pass on the `skill` target directory.

    Same-name collision rule: pack source order as supplied here; the
    last pack's `<name>` overwrites earlier packs' (`_project_direct_directory`
    `rmtree`s the destination before `copytree`). The orphan sweep
    observes the union of source skill names across the call's pack
    list (not per-pack) so a pack shipping a subset can co-exist with
    another that ships the union complement.
    """
    for pack_path in pack_paths:
        _project_single(pack_path, contract, output_root)
    _sweep_skill_orphans(pack_paths, contract, output_root)


# Mirror of claude_code.py:_skill_direct_directory_target — keep in sync.
# A shared helper is barred by the spec's `Never do` boundary (no
# expansion of projections/direct_directory.py beyond `sweep_orphans`).
def _skill_direct_directory_target(contract: dict, output_root: Path) -> Path | None:
    adapter_block = contract["adapter"]["kiro"]
    for entry in adapter_block.get("projection", []):
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


def _project_single(pack_path: Path, contract: dict, output_root: Path) -> None:
    """Project *pack_path* into *output_root* per Kiro's contract rules.

    Iteration is phase-ordered (see `_iter_primitives`). For each
    primitive in the contract, dispatch on mode:

      - `direct-directory` → recursive copy
      - `direct-file` (agent) → markdown frontmatter + body → JSON
      - `direct-file` (other) → byte-for-byte file copy
      - `merge-into-agent-json` → delegate to the v0.3 projection module
      - `dropped` → no-op (filtered at iter time)
    """
    adapter_block = contract["adapter"]["kiro"]
    array_form = {entry["primitive"]: entry for entry in adapter_block.get("projection", [])}
    table_form = adapter_block.get("projections", {}) if isinstance(adapter_block.get("projections"), dict) else {}

    for primitive_name in _iter_primitives(contract):
        primitive = contract["primitive"][primitive_name]
        source_dir = pack_path / primitive["source-path"].rstrip("/")
        if not source_dir.exists():
            continue

        if primitive_name in array_form:
            rule = array_form[primitive_name]
            _dispatch_array_form(primitive_name, source_dir, output_root, rule, contract)
        else:
            rule = table_form[primitive_name]
            _dispatch_table_form(
                primitive_name, source_dir, output_root, rule, pack_path, contract,
            )


def _dispatch_array_form(
    primitive_name: str,
    source_dir: Path,
    output_root: Path,
    rule: dict,
    contract: dict,
) -> None:
    mode = rule["mode"]
    if mode == "direct-directory":
        _project_direct_directory(source_dir, output_root / rule["target-path"].rstrip("/"))
    elif mode == "direct-file":
        if primitive_name == "agent":
            _project_agent_as_json(source_dir, output_root, rule, contract)
        else:
            _project_direct_file(source_dir, output_root, rule["target-path"])
    else:
        raise ValueError(f"kiro: unhandled array-form mode {mode!r} for {primitive_name}")


def _dispatch_table_form(
    primitive_name: str,
    source_dir: Path,
    output_root: Path,
    rule: dict,
    pack_path: Path,
    contract: dict,
) -> None:
    mode = rule.get("mode")
    # `mode` may be a string or a scope-map per RFC-0005; at build time
    # we project the repo-scope shape (the user-scope path is resolved
    # at install time by T8b). For string-or-scope-map fields, prefer
    # the repo branch.
    effective_mode = mode["repo"] if isinstance(mode, dict) else mode

    if primitive_name == "hook-wiring" and effective_mode == "merge-into-agent-json":
        _project_hook_wiring_to_agent_json(source_dir, output_root, rule, pack_path)
    elif primitive_name == "hook-body" and effective_mode == "direct-file":
        # Resolve the scope-conditional target. The build pipeline
        # writes the repo-scope shape; user-scope projection is T8b's
        # install-time concern.
        target = rule.get("target")
        if isinstance(target, dict):
            target_template = target.get("repo")
        else:
            target_template = target
        if target_template:
            _project_direct_file_template(source_dir, output_root, target_template)
    elif primitive_name == "kiro-ide-hook" and effective_mode == "direct-file":
        # RFC-0005 v0.4 — IDE event hooks via the kiro-ide-hook primitive.
        # Delegate the file-walk, JSON-parse, and `${hook-body:<name>}`
        # expansion to the dedicated projection module so the wiring
        # here stays mechanical.
        _project_kiro_ide_hook(source_dir, output_root, rule, contract, pack_path)
    else:
        # Other table-form modes (or scope-only declarations the legacy
        # array still owns) — silent skip.
        return


# ---------------------------------------------------------------------------
# Agent .md → .json reform
# ---------------------------------------------------------------------------


def _project_agent_as_json(
    source_dir: Path,
    output_root: Path,
    rule: dict,
    contract: dict,
) -> None:
    """Read `.apm/agents/<name>.md` and emit `<output>/.kiro/agents/<name>.json`.

    Source layout: `.apm/agents/<name>.md` with YAML-style frontmatter
    (`---` fence) + markdown body. Output layout: JSON object with
    Kiro's documented fields per
    https://kiro.dev/docs/cli/custom-agents/configuration-reference/:

      - `name`: derived from the source filename (without `.md`),
        or overridden by a `name` frontmatter field if present.
      - `description`: frontmatter `description` (renamed per the
        contract's `kiro-ide-agent-frontmatter-v0.9` mapping).
      - `tools`: frontmatter `tools` normalized to a list.
      - `model`: frontmatter `model`, if declared.
      - `prompt`: the markdown body after the closing `---` fence.

    The mapping table on the contract retains its `rename` / `normalize`
    grammar; what changes from v0.2 is the *emission* — JSON instead
    of frontmatter-with-body markdown — which closes the spec/Kiro-docs
    drift RFC-0005's "observed-but-not-publicly-documented" drawback
    flagged.
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
        rewritten = _apply_mapping(frontmatter, mapping)
        agent_name = rewritten.get("name") or entry.stem
        agent_json: dict[str, Any] = {"name": agent_name}
        # Preserve any rewritten fields that aren't `name` (already
        # placed above). Iterate sorted for deterministic output.
        # An explicit `prompt` in frontmatter wins over the
        # body-derived prompt — pack authors writing Kiro JSON
        # directly may put the prompt there per the published
        # reference, and silently overwriting their value would be
        # data loss.
        for key in sorted(rewritten.keys()):
            if key == "name":
                continue
            agent_json[key] = rewritten[key]
        if "prompt" not in agent_json:
            # Body fallback: the markdown body becomes the agent's
            # prompt when frontmatter doesn't declare one.
            prompt = body.rstrip("\n")
            if prompt:
                agent_json["prompt"] = prompt
        # Skill-resources injection (RFC-0022 E4). The agent projection
        # declares `inject-resources` so custom agents reach the bundle's
        # skills — Kiro custom agents don't inherit the default agent's
        # `.kiro/skills` auto-discovery (kiro #6887/#6888). Author-declared
        # `resources` win: only inject when the agent set none. This function
        # handles the CLI (JSON) path; kiro-ide injects the same field in its
        # own `.md` projector (`_project_agent_as_md`).
        inject_resources = rule.get("inject-resources")
        if inject_resources and "resources" not in agent_json:
            agent_json["resources"] = list(inject_resources)
        destination = target_dir / (entry.stem + ".json")
        destination.write_text(
            json.dumps(agent_json, indent=2, sort_keys=False) + "\n",
            encoding="utf-8", newline="\n",
        )


# ---------------------------------------------------------------------------
# Hook-wiring → agent JSON merge
# ---------------------------------------------------------------------------


def _project_hook_wiring_to_agent_json(
    source_dir: Path,
    output_root: Path,
    rule: dict,
    pack_path: Path,
) -> None:
    """For each `.apm/hook-wiring/<name>.toml`, merge into the resolved
    agent JSON at `<output>/.kiro/agents/<attach-to-agent>.json`.

    The agent JSON is **guaranteed to exist** at this point — the
    phase-order invariant ensures agent projection ran first
    (`_iter_primitives` yields `agent` before `hook-wiring`). If the
    wiring TOML's `attach-to-agent` names an agent the pack didn't
    ship, the merge module refuses with the RFC-0005 `internal:` text.

    Pack-side validation already refused malformed wiring TOMLs at
    `validate` time (T2's `check_kiro_wiring`), so by the time we
    reach this code path, every wiring TOML has a same-pack agent
    target. Build-time defense-in-depth: re-check `attach-to-agent`
    against shipped agents and skip silently if the field is missing.
    """
    pack_name = pack_path.name

    target_template = rule.get("target")
    if isinstance(target_template, dict):
        target_template = target_template.get("repo")
    if not target_template:
        return

    # Group wiring TOMLs by their `attach-to-agent` so we can call
    # merge-into-agent-json once per agent. The merge module takes a
    # batch of `wiring_tomls` for one target file.
    wiring_by_agent: dict[str, dict[str, dict]] = {}
    for entry in sorted(source_dir.iterdir()):
        if not (entry.is_file() and entry.suffix == ".toml"):
            continue
        try:
            body = tomllib.loads(entry.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError:
            continue
        attach = body.get("attach-to-agent") if isinstance(body, dict) else None
        if not isinstance(attach, str):
            continue
        wiring_by_agent.setdefault(attach, {})[entry.stem] = body

    for attach_to_agent, wiring_tomls in wiring_by_agent.items():
        resolved = target_template.replace("<attach-to-agent>", attach_to_agent)
        target_path = output_root / resolved.lstrip("/")
        # Let AgentJsonRefusal propagate. RFC-0005 names the reachable
        # cases — missing agent (pipeline-ordering invariant violation),
        # unparseable JSON, wrong-shape `hooks` — all of which are bugs
        # at build time, not adopter-fixable conditions. Silently
        # swallowing them would let `make build` produce
        # silently-incomplete artifacts; the existing pipeline shape
        # is fail-fast, and that's the right shape here too.
        merge_into_agent_json_project(target_path, pack_name, wiring_tomls)


# ---------------------------------------------------------------------------
# Existing helpers (preserved from v0.2 with small adjustments)
# ---------------------------------------------------------------------------


def _ignore_symlinks(directory: str, names: list[str]) -> set[str]:
    """`shutil.copytree` ignore callback: skip every symlink member.

    Drops nested symlinks so they are never reproduced in the output
    tree. The top-level `is_symlink()` skip in `_project_direct_directory`
    covers the skill root; this covers the subtree.
    """
    base = Path(directory)
    return {name for name in names if (base / name).is_symlink()}


def _project_direct_directory(source_dir: Path, target_dir: Path) -> None:
    for entry in sorted(source_dir.iterdir()):
        # Defense-in-depth — `lint-packs` rejects packs that ship
        # symlinks, but a direct `project_packs` caller bypasses
        # that gate. A symlink at the skill-root level would be
        # dereferenced by `copytree`.
        if entry.is_symlink():
            continue
        if entry.is_dir():
            destination = target_dir / entry.name
            # Spec § Never do — `shutil.rmtree` is barred against
            # any entry whose `is_symlink()` is true. If a previous
            # run left a symlink at the destination path, unlink it.
            if destination.is_symlink():
                destination.unlink()
            elif destination.exists():
                shutil.rmtree(destination)
            # `ignore=_ignore_symlinks` drops nested symlinks so they are
            # never reproduced in the output tree.
            shutil.copytree(entry, destination, ignore=_ignore_symlinks)


def _project_direct_file(source_dir: Path, output_root: Path, target_prefix: str) -> None:
    target_dir = output_root / target_prefix.rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source_dir.iterdir()):
        if entry.is_file():
            destination = target_dir / entry.name
            shutil.copy2(entry, destination, follow_symlinks=False)


def _project_direct_file_template(
    source_dir: Path,
    output_root: Path,
    target_template: str,
) -> None:
    """Project each file under *source_dir* to a path derived from
    *target_template* by substituting `<name>` with the filename's
    basename.

    The v0.3 contract introduces `target = "tools/hooks/<name>.{sh,py}"`-
    style templates that preserve the source extension. The braces are
    illustrative; the actual output uses the source file's actual
    extension (`.sh` or `.py`)."""
    for entry in sorted(source_dir.iterdir()):
        if not entry.is_file():
            continue
        # Replace `<name>.{sh,py}` (or any `.{...}` choice block) with
        # the actual filename. The simplest substitution: replace the
        # whole `<name>.{...}` template with `<actual filename>`.
        resolved = target_template
        if "<name>" in resolved:
            # Strip everything from `<name>` onward and re-append the
            # source filename — the source's actual extension wins.
            prefix, _, _suffix = resolved.partition("<name>")
            resolved = prefix + entry.name
        target_path = output_root / resolved.lstrip("/")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(entry, target_path, follow_symlinks=False)


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


def _apply_mapping(frontmatter: dict[str, Any], mapping: dict) -> dict[str, Any]:
    """Apply the contract's `kiro-ide-agent-frontmatter-v0.9` rename /
    normalize / values / default rules. Interpreted as
    *markdown-frontmatter → JSON-field*.

    `normalize = "to-list"` on a string splits on commas, strips
    whitespace, and drops empties — the human-frontmatter convention
    pack authors use (`tools: Read, Grep, Glob, Bash`) that YAML
    itself parses as a single scalar.

    `values` translates a scalar source value through the declared
    alias map. A source value not in the map drops the field from
    the rewritten output (rather than emitting an unknown identifier
    the consumer would reject); a stderr line surfaces the drop at
    build time so a pack-author typo (`opsus` for `opus`) doesn't
    silently ship a default-model agent.

    `values` composes with `normalize = "to-list"`: `to-list` runs
    first, then `values` translates each element of the resulting list
    (collapsing duplicates, preserving order, dropping unmapped tokens
    with a warning). This is how the `tools` field maps Claude Code
    tool names (`Read`, `Grep`, `Bash`, …) onto Kiro tool ids
    (`read_file`, `grep_search`, `execute_bash`, …); the same `values`
    map still applies to a scalar field like `model`."""
    rewritten: dict[str, Any] = {}
    for source_key, value in frontmatter.items():
        rule = mapping.get(source_key, {})
        new_key = rule.get("rename", source_key)
        normalize = rule.get("normalize")
        if normalize == "to-list":
            if isinstance(value, list):
                pass
            elif isinstance(value, str):
                value = [item.strip() for item in value.split(",") if item.strip()]
            else:
                value = [value]
        values_map = rule.get("values")
        if isinstance(values_map, dict):
            if isinstance(value, list) and normalize == "to-list":
                # Per-element translation for a declared list field (`tools`
                # after `to-list`). Gated on `normalize == "to-list"` so a
                # scalar field that merely *parsed* as a list (e.g. a
                # malformed `model: [opus]`) still takes the scalar miss
                # branch and drops. Each source token maps through the values
                # map; an unmapped token drops with a stderr warning (it would
                # match no Kiro tool id/tag downstream and silently yield an
                # empty tool set). Order is preserved and duplicates collapse
                # — e.g. `Read, Grep, Glob` all map to the `read` tag, so the
                # output carries a single `read`.
                mapped: list = []
                for item in value:
                    if item in values_map:
                        translated = values_map[item]
                        if translated not in mapped:
                            mapped.append(translated)
                    else:
                        print(
                            f"kiro: dropping {new_key} entry {item!r} — not in "
                            f"contract values map for source key {source_key!r}",
                            file=sys.stderr,
                        )
                value = mapped
            elif isinstance(value, str) and value in values_map:
                value = values_map[value]
            else:
                print(
                    f"kiro: dropping {new_key}={value!r} — not in contract "
                    f"values map for source key {source_key!r}",
                    file=sys.stderr,
                )
                continue
        rewritten[new_key] = value
    for source_key, rule in mapping.items():
        default_value = rule.get("default")
        new_key = rule.get("rename", source_key)
        if new_key not in rewritten and default_value is not None:
            rewritten[new_key] = default_value
    return rewritten


# ---------------------------------------------------------------------------
# kiro-ide-hook dispatch (RFC-0005 v0.4)
# ---------------------------------------------------------------------------


def _project_kiro_ide_hook(
    source_dir: Path,
    output_root: Path,
    rule: dict,
    contract: dict,
    pack_path: Path,
) -> None:
    """Dispatch ``.apm/kiro-ide-hooks/`` through the dedicated projector.

    The kiro adapter holds onto the contract dict so the same-pack
    hook-body target directory can be looked up here (the projector
    needs it for ``${hook-body:<name>}`` resolution and shouldn't have
    to re-parse the contract itself). Pre-v0.4 contracts don't reach
    this code path — ``_iter_primitives`` won't yield
    ``kiro-ide-hook`` until the v0.4 contract declares it.
    """
    # Target template from the rule (.kiro/hooks/<pack>/<name>.kiro.hook
    # at v0.4 per the RFC's lean).
    target = rule.get("target")
    if isinstance(target, dict):
        target_template = target.get("repo")
    else:
        target_template = target
    if not target_template:
        return

    hook_body_target_dir = _resolve_kiro_hook_body_target_dir(contract)

    kiro_ide_hook_project(
        pack_path,
        output_root,
        target_template=target_template,
        hook_body_target_dir=hook_body_target_dir,
    )


def _resolve_kiro_hook_body_target_dir(contract: dict) -> str:
    """Resolve where same-pack hook-bodies project to under the kiro
    adapter, used for ``${hook-body:<name>}`` substitution.

    Prefers the legacy ``[[adapter.kiro.projection]]`` array entry per
    the v0.3 ``adapter.toml`` comment "the legacy entries remain
    authoritative". Falls back to the v0.3 table form's
    ``[adapter.kiro.projections.hook-body].target.repo`` if no array
    entry exists, stripping the trailing filename pattern (e.g.
    ``"tools/hooks/<name>.{sh,py}"`` → ``"tools/hooks"``). Final
    fallback: the documented default ``"tools/hooks"``.
    """
    adapter_block = contract.get("adapter", {}).get("kiro", {})
    array_form = {
        entry["primitive"]: entry
        for entry in adapter_block.get("projection", [])
        if isinstance(entry, dict)
    }
    if "hook-body" in array_form:
        return array_form["hook-body"].get("target-path", "tools/hooks/").rstrip("/")

    projections = adapter_block.get("projections", {})
    hook_body_rule = projections.get("hook-body", {}) if isinstance(projections, dict) else {}
    target = hook_body_rule.get("target")
    if isinstance(target, dict):
        target = target.get("repo", "")
    if isinstance(target, str) and "/" in target:
        return target.rsplit("/", 1)[0]
    return "tools/hooks"
