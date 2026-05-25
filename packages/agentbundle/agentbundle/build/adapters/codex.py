"""Codex adapter — projects skills as full `<name>/SKILL.md` trees under
`.agents/skills/`, projects hook bodies straight through, drops the rest.

Post-RFC-0009 (codex-native-skills): the `skill` primitive lands as
`direct-directory` mode (full body, byte-equal). Adopters upgrading
from the legacy `managed-block-inline` shape get a one-shot in-place
strip of the `<!-- agent-skills:start -->` / `<!-- agent-skills:end -->`
delimiter region from their existing `<output_root>/AGENTS.md`; the
strip is destructive by design and bound to the migration window
(removed together with `_splice_managed_block` in a follow-on release).
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator


# RFC-0005 § Build-pipeline ordering invariant — uniform across adapters.
from agentbundle.build.phase_order import PHASE_ORDER as _PHASE_ORDER
from agentbundle.build.projections.direct_directory import sweep_orphans


def _iter_primitives(contract: dict) -> Iterator[str]:
    """Yield Codex's projected primitive names in phase order."""
    adapter_block = contract["adapter"]["codex"]
    array_form = {entry["primitive"]: entry for entry in adapter_block.get("projection", [])}
    for primitive_name in _PHASE_ORDER:
        if primitive_name in array_form and array_form[primitive_name].get("mode") != "dropped":
            yield primitive_name


def project(pack_path: Path, contract: dict, output_root: Path) -> None:
    project_packs([pack_path], contract, output_root)


def project_packs(pack_paths: list[Path], contract: dict, output_root: Path) -> None:
    # One-shot migration strip on the project-root AGENTS.md. AC10:
    # in self-host, `_compose_agents_md` rewrites AGENTS.md from the
    # seed (which AC15 stripped of delimiters) just before this call,
    # so the strip is a documented no-op there. In adopter installs
    # against a pre-existing AGENTS.md carrying the legacy block, the
    # strip does real work. Both cases are correct.
    agents_md = output_root / "AGENTS.md"
    if agents_md.exists():
        original = agents_md.read_text(encoding="utf-8")
        stripped = _strip_legacy_skill_block(original)
        if stripped != original:
            # Destructive: any hand-edited prose between the legacy
            # delimiters is gone (RFC-0009 § Failure modes). Leave a
            # breadcrumb so an adopter who discovers missing notes
            # has a way to reconstruct what happened.
            print(
                f"codex: stripped legacy <!-- agent-skills:start --> region "
                f"from {agents_md} — see RFC-0009 § Migration path",
                file=sys.stderr,
            )
            # Atomic rewrite: a crash between truncate and write would
            # otherwise leave a zero-length AGENTS.md. write to a
            # sibling temp file, then `os.replace` for the swap.
            fd, tmp_path = tempfile.mkstemp(
                prefix=".AGENTS.md.strip.",
                suffix=".tmp",
                dir=str(agents_md.parent),
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(stripped)
                os.replace(tmp_path, agents_md)
            except BaseException:
                Path(tmp_path).unlink(missing_ok=True)
                raise

    adapter_block = contract["adapter"]["codex"]
    rules_by_primitive = {entry["primitive"]: entry for entry in adapter_block.get("projection", [])}

    for primitive_name in _iter_primitives(contract):
        rule = rules_by_primitive[primitive_name]
        mode = rule["mode"]
        primitive = contract["primitive"][primitive_name]
        source_dirs = [
            pack_path / primitive["source-path"].rstrip("/")
            for pack_path in pack_paths
        ]
        source_dirs = [source_dir for source_dir in source_dirs if source_dir.exists()]

        # The `skill` primitive's `direct-directory` projection runs
        # the orphan sweep uniformly across all three adapters, even
        # when no pack ships skills — matching claude_code / kiro
        # which sweep with an empty union (wiping leftover orphans).
        # See spec Objective invariant 4: "after every `project_packs`
        # call". Other primitives keep the early-skip.
        is_skill_direct_directory = (
            mode == "direct-directory" and primitive_name == "skill"
        )
        if not source_dirs and not is_skill_direct_directory:
            continue

        if mode == "direct-directory":
            target_dir = output_root / rule["target-path"].rstrip("/")
            target_dir.mkdir(parents=True, exist_ok=True)
            expected_names: set[str] = set()
            for source_dir in source_dirs:
                for entry in sorted(source_dir.iterdir()):
                    # Defense-in-depth — `lint-packs` already refuses
                    # packs that ship symlinks, but a caller invoking
                    # `project_packs` directly bypasses that gate. A
                    # symlink at the skill-root level would be
                    # dereferenced by `copytree` (the `symlinks=True`
                    # flag only governs symlinks *inside* the tree),
                    # exfiltrating the link target's contents.
                    if entry.is_symlink():
                        continue
                    if entry.is_dir():
                        expected_names.add(entry.name)
                        destination = target_dir / entry.name
                        # Spec § Never do — `shutil.rmtree` is barred
                        # against any entry whose `is_symlink()` is
                        # true. If a previous projection left a
                        # symlink at the destination path, unlink it
                        # (removes the link, not the target).
                        if destination.is_symlink():
                            destination.unlink()
                        elif destination.exists():
                            shutil.rmtree(destination)
                        # symlinks=True keeps source symlinks as
                        # symlinks — never dereferences. A malicious
                        # pack with a symlink to /etc/passwd cannot
                        # exfiltrate.
                        shutil.copytree(entry, destination, symlinks=True)
            # Bound to `skill` only per spec § Never do. Other
            # direct-directory primitives opt in explicitly.
            if primitive_name == "skill":
                sweep_orphans(target_dir, expected_names)
        elif mode == "direct-file":
            for source_dir in source_dirs:
                _project_direct_file(source_dir, output_root, rule["target-path"])
        else:
            raise ValueError(f"codex: unhandled mode {mode!r} for {primitive_name}")


def _project_direct_file(source_dir: Path, output_root: Path, target_prefix: str) -> None:
    target_dir = output_root / target_prefix.rstrip("/")
    target_dir.mkdir(parents=True, exist_ok=True)
    for entry in sorted(source_dir.iterdir()):
        if entry.is_file():
            shutil.copy2(entry, target_dir / entry.name, follow_symlinks=False)


def _splice_managed_block(
    existing: str,
    start_marker: str,
    end_marker: str,
    managed_block: str,
) -> str:
    if start_marker in existing and end_marker in existing:
        start_index = existing.index(start_marker)
        end_index = existing.index(end_marker) + len(end_marker)
        if end_index < len(existing) and existing[end_index] == "\n":
            end_index += 1
        return existing[:start_index] + managed_block + existing[end_index:]
    if existing and not existing.endswith("\n"):
        existing += "\n"
    return existing + managed_block


# Legacy delimiter literals, hardcoded for the migration window per
# RFC-0009 § Adapter implementation change. Removed in the post-strip
# release together with `_splice_managed_block`.
_LEGACY_SKILL_BLOCK_START = "<!-- agent-skills:start -->"
_LEGACY_SKILL_BLOCK_END = "<!-- agent-skills:end -->"


def _strip_legacy_skill_block(text: str) -> str:
    """Strip the legacy `agent-skills` managed block from an `AGENTS.md`.

    One-shot migration helper: if both delimiters are present, the
    splice removes everything from the start marker through the end
    marker (plus a trailing newline if present). If neither
    delimiter is present, the input is returned byte-equal — the
    strip is a no-op on a clean file. Idempotent.

    `_splice_managed_block` with an empty `managed_block` argument
    is sufficient on its own; its post-condition is that the
    delimiters and the region between them are gone from the result.
    The call goes through that helper so the AC23 retention test
    still observes the splice symbol being used (any future inlining
    that removes the symbol breaks the retention contract).
    """
    if _LEGACY_SKILL_BLOCK_START not in text or _LEGACY_SKILL_BLOCK_END not in text:
        return text
    # Splice helper indexes the first occurrence of each marker.
    # If `end` precedes `start` (an adopter who reordered the
    # delimiters) the splice would produce a result that still
    # contains both markers and is not idempotent. Refuse the
    # confused-deputy input rather than silently corrupt it.
    start_position = text.index(_LEGACY_SKILL_BLOCK_START)
    end_position = text.index(_LEGACY_SKILL_BLOCK_END)
    if end_position < start_position:
        raise ValueError(
            "codex: <!-- agent-skills:end --> appears before "
            "<!-- agent-skills:start --> in AGENTS.md — the migration "
            "strip refuses confused-deputy input. Restore the "
            "delimiter order or remove the block manually."
        )
    return _splice_managed_block(
        text,
        _LEGACY_SKILL_BLOCK_START,
        _LEGACY_SKILL_BLOCK_END,
        "",
    )
