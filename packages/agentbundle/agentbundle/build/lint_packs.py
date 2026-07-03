"""Pack-source lint — refuse packs whose content would break either
Windows portability or per-target metadata caps at projection time.

Three checks, applied to every pack under a `--packs-dir`:

  1. **No symlinks** — `Path.is_symlink()` against the entry. Windows
     symlink creation requires Developer Mode or admin privileges, and
     packs distributed via git/zip/zipapp lose symlink fidelity along
     the way.
  2. **No Windows-poisonous names** — every path is run through
     `safety.assert_portable_name`, which rejects reserved device names
     (CON/PRN/AUX/NUL/COM1-9/LPT1-9), trailing dots or spaces, and the
     `<>:"|?*` character set.
  3. **Per-target metadata caps** — for each pack's `.apm/skills/` and
     `.apm/agents/` source, refuse skill/agent names that don't match
     the strictest `name-pattern` across declared targets, names that
     exceed the strictest `name-max-length`, and descriptions that
     exceed the strictest `description-max-length`. Multi-line YAML
     descriptions (`>`, `|`, continuation lines) are refused outright
     rather than mis-parsed. Constraints come from
     `docs/contracts/target-vocab.toml` — see
     `docs/specs/lint-packs-target-vocab/spec.md`.

The lint is Python-only so it runs on every CI platform without
shelling out, and it is wired into `make build` / `make build-self` /
`make build-check` as a hard prerequisite.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from typing import NamedTuple, Pattern
from pathlib import Path

from agentbundle.pack_inventory import apm_entries
from agentbundle.safety import PathJailError, assert_portable_name

# Subtrees in a pack that ship to adopters. `seeds/` is the
# adopter-facing surface; `.apm/` is the primitives the APM adapter
# unpacks. Both must be portable. `pack.toml` and `.claude-plugin/`
# live outside the walk because their schemas already constrain
# their content.
_PACK_SUBTREES = ("seeds", ".apm")

# Path to the sibling vocab file, relative to a repo root. The loader
# walks up from a caller-supplied start until an ancestor contains
# this relative path.
_VOCAB_RELPATH = Path("docs/contracts/target-vocab.toml")

# Sentinel returned by `_extract_frontmatter_fields` when a key's
# value position is `>`, `|`, or empty (signaling a folded / nested
# block). The metadata checks translate this into an AC12 finding
# rather than try to parse the continuation.
_MULTILINE = object()


class Constraints(NamedTuple):
    """Strictest-cap snapshot of `docs/contracts/target-vocab.toml`.

    `binding_targets` keys (`"description_max"`, `"name_max"`,
    `"name_pattern"`) carry the ASCII-sorted list of targets enforcing
    the binding value. Findings render the list as
    `binding target: <comma-joined>`.
    """

    description_max: int
    name_pattern: Pattern[str]
    name_max: int
    binding_targets: dict[str, list[str]]


def _walk_up_for_vocab(start: Path) -> Path | None:
    cursor = start.resolve()
    while True:
        possible = cursor / _VOCAB_RELPATH
        if possible.is_file():
            return possible
        if cursor.parent == cursor:
            return None
        cursor = cursor.parent


def _load_target_vocab(start: Path) -> tuple[dict | None, str | None]:
    """Walk up from `start` looking for `docs/contracts/target-vocab.toml`;
    fall back to walking up from this module's own ancestor chain when
    the explicit walk fails. This keeps the gate working when an
    adopter points `--packs-dir` at a tmp tree outside the repo while
    still picking up the in-tree vocab. The legacy pre-PR
    `LintPackTests` rely on this fallback. Returns `(vocab_dict, None)`
    on success, `(None, err)` when **both** walks fail or the file is
    malformed."""
    candidate = _walk_up_for_vocab(start)
    if candidate is None:
        candidate = _walk_up_for_vocab(Path(__file__).parent)
    if candidate is None:
        return None, (
            "lint-packs: target-vocab.toml not found (walked up from "
            f"{start} and from this module's ancestor chain; expected "
            f"{_VOCAB_RELPATH.as_posix()})"
        )
    try:
        raw = tomllib.loads(candidate.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        return None, f"lint-packs: failed to parse {candidate}: {exc}"
    targets = raw.get("target")
    if not isinstance(targets, dict) or not targets:
        return None, (
            f"lint-packs: {candidate} has no [target.<name>] tables — "
            f"the metadata gate has no constraints to apply"
        )
    return raw, None


def _strictest_constraints(vocab: dict) -> tuple[Constraints | None, str | None]:
    """Collapse per-target caps into the strictest binding. Returns
    `(constraints, None)` on success, `(None, err)` if targets disagree
    on `name-pattern` (which would require regex intersection — not
    well-defined; the loader refuses rather than picking one)."""
    targets: dict[str, dict] = vocab["target"]

    # `name-pattern` must be byte-equal across every declared target —
    # regex intersection is not a defined operation, so disagreement
    # is refused (AC1 + AC11).
    pattern_per_target: dict[str, str] = {}
    for name, table in targets.items():
        if not isinstance(table, dict):
            continue
        pattern = table.get("name-pattern")
        if not isinstance(pattern, str):
            return None, (
                f"lint-packs: target {name!r} is missing `name-pattern` in "
                f"target-vocab.toml"
            )
        pattern_per_target[name] = pattern
    distinct_patterns = set(pattern_per_target.values())
    if len(distinct_patterns) != 1:
        # AC11 — name-pattern disagreement is refused. Report which
        # targets contributed which pattern so the file author can fix
        # the divergence without re-reading the loader source.
        groups: dict[str, list[str]] = {}
        for tgt, pat in sorted(pattern_per_target.items()):
            groups.setdefault(pat, []).append(tgt)
        rendered = "; ".join(
            f"{pat!r}: {', '.join(group)}" for pat, group in sorted(groups.items())
        )
        return None, (
            f"lint-packs: target-vocab.toml declares inconsistent "
            f"name-pattern values across targets ({rendered}) — every "
            f"declared target must share the same pattern (regex "
            f"intersection is not well-defined)"
        )
    compiled_pattern = re.compile(next(iter(distinct_patterns)))

    # Numeric caps — collect each target's value, find the minimum
    # (strictest binding), record which targets hit that minimum.
    desc_caps: dict[str, int] = {}
    name_caps: dict[str, int] = {}
    for name, table in targets.items():
        if not isinstance(table, dict):
            continue
        if isinstance(table.get("description-max-length"), int):
            desc_caps[name] = table["description-max-length"]
        if isinstance(table.get("name-max-length"), int):
            name_caps[name] = table["name-max-length"]

    if not desc_caps:
        return None, (
            "lint-packs: target-vocab.toml declares no "
            "`description-max-length` on any target — the metadata gate "
            "needs at least one target with a description cap"
        )
    if not name_caps:
        return None, (
            "lint-packs: target-vocab.toml declares no `name-max-length` "
            "on any target — the metadata gate needs at least one target "
            "with a name-length cap"
        )

    desc_min = min(desc_caps.values())
    name_min = min(name_caps.values())
    binding_targets = {
        "description_max": sorted(t for t, v in desc_caps.items() if v == desc_min),
        "name_max": sorted(t for t, v in name_caps.items() if v == name_min),
        "name_pattern": sorted(targets.keys()),
    }
    return (
        Constraints(
            description_max=desc_min,
            name_pattern=compiled_pattern,
            name_max=name_min,
            binding_targets=binding_targets,
        ),
        None,
    )


def _render_binding(constraints: Constraints, field: str) -> str:
    return ", ".join(constraints.binding_targets[field])


def _extract_frontmatter_fields(
    text: str, keys: set[str]
) -> dict[str, object]:
    """Return `{key: value}` for each requested key found in the
    `--- ... ---` frontmatter at the head of `text`.

    Values are either strings (single-line scalars, with balanced
    surrounding quotes stripped) or the `_MULTILINE` sentinel for keys
    whose value position is `>`, `|`, or empty (signalling a folded /
    nested block). Keys not present in the frontmatter are absent from
    the returned dict. Files without a `---` fence return `{}`.
    """
    # Strip a leading UTF-8 BOM so a SKILL.md saved by a Windows editor
    # still has its frontmatter recognised — without this, `lines[0]`
    # would carry the BOM and the parser would silently return `{}`,
    # letting an over-cap description slip through.
    text = text.lstrip("﻿")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}
    found: dict[str, object] = {}
    i = 1
    while i < end:
        raw = lines[i]
        if not raw.strip():
            i += 1
            continue
        # Only care about top-level keys; indented continuation lines
        # are handled below per-key.
        match = re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$", raw)
        if not match:
            i += 1
            continue
        key, value = match.group(1), match.group(2).strip()
        if key in keys:
            if value in ("", ">", "|") or value.startswith((">", "|")):
                # Folded / continuation block. Peek the next non-blank
                # line: if it's indented, this is a multi-line value
                # we refuse to parse; if it's a top-level key or the
                # closing fence, treat the value as an empty scalar
                # (also refused — empty descriptions are caught
                # downstream by description-presence checks).
                j = i + 1
                continuation = False
                while j < end:
                    nxt = lines[j]
                    if not nxt.strip():
                        j += 1
                        continue
                    indent = len(nxt) - len(nxt.lstrip())
                    if indent > 0:
                        continuation = True
                    break
                if continuation or value in (">", "|") or value.startswith((">", "|")):
                    found[key] = _MULTILINE
                else:
                    found[key] = ""
            else:
                if (
                    len(value) >= 2
                    and value[0] == value[-1]
                    and value[0] in ('"', "'")
                ):
                    value = value[1:-1]
                found[key] = value
        i += 1
    return found


def _check_skill_metadata(pack_dir: Path, constraints: Constraints) -> list[str]:
    findings: list[str] = []
    # Enumeration lives in one place (RFC-0060 AC9): the shared raw walk.
    # Lint keeps its own per-entry filtering (it lints SKILL.md-less dirs too,
    # which `show` excludes) — the walk is shared, the filter is not.
    for entry in apm_entries(pack_dir, "skills"):
        if not entry.is_dir():
            continue
        dir_name = entry.name
        skill_md = entry / "SKILL.md"
        relpath = (
            skill_md.relative_to(pack_dir).as_posix()
            if skill_md.is_file()
            else entry.relative_to(pack_dir).as_posix() + "/"
        )
        # On-disk name checks — pattern + length for the dir name.
        primary = _pattern_finding(
            pack_dir.name, "skill", dir_name, dir_name, constraints, relpath
        )
        if primary is not None:
            findings.append(primary)
        length = _length_finding(
            pack_dir.name, "skill", dir_name, constraints, relpath
        )
        if length is not None:
            findings.append(length)
        if not skill_md.is_file():
            continue
        text = skill_md.read_text(encoding="utf-8")
        findings.extend(
            _description_findings(
                pack_dir.name, "skill", dir_name, text, constraints, relpath
            )
        )
        # Frontmatter `name:` — multi-line refused (AC12); when
        # present and a single-line scalar that differs from the
        # dir, run the pattern check (AC2).
        fields = _extract_frontmatter_fields(text, {"name"})
        fm_name = fields.get("name")
        if fm_name is _MULTILINE:
            findings.append(
                f"{pack_dir.name}: skill/{dir_name}: name must be "
                f"a single-line value: {relpath}"
            )
        elif isinstance(fm_name, str) and fm_name and fm_name != dir_name:
            fm_finding = _pattern_finding(
                pack_dir.name, "skill", dir_name, fm_name, constraints, relpath
            )
            if fm_finding is not None:
                findings.append(fm_finding)
    return findings


def _check_agent_metadata(pack_dir: Path, constraints: Constraints) -> list[str]:
    findings: list[str] = []
    # Shared raw walk (RFC-0060 AC9); lint keeps its own .md-file filter.
    for entry in apm_entries(pack_dir, "agents"):
        if not entry.is_file() or entry.suffix != ".md":
            continue
        stem = entry.stem
        relpath = entry.relative_to(pack_dir).as_posix()
        primary = _pattern_finding(
            pack_dir.name, "agent", stem, stem, constraints, relpath
        )
        if primary is not None:
            findings.append(primary)
        length = _length_finding(
            pack_dir.name, "agent", stem, constraints, relpath
        )
        if length is not None:
            findings.append(length)
        text = entry.read_text(encoding="utf-8")
        findings.extend(
            _description_findings(
                pack_dir.name, "agent", stem, text, constraints, relpath
            )
        )
        fields = _extract_frontmatter_fields(text, {"name"})
        fm_name = fields.get("name")
        if fm_name is _MULTILINE:
            findings.append(
                f"{pack_dir.name}: agent/{stem}: name must be "
                f"a single-line value: {relpath}"
            )
        elif isinstance(fm_name, str) and fm_name and fm_name != stem:
            fm_finding = _pattern_finding(
                pack_dir.name, "agent", stem, fm_name, constraints, relpath
            )
            if fm_finding is not None:
                findings.append(fm_finding)
    return findings


def _pattern_finding(
    pack_name: str,
    primitive: str,
    display_name: str,
    candidate: str,
    constraints: Constraints,
    relpath: str,
) -> str | None:
    """Pattern-only check for one candidate name. Used by both the
    on-disk-name check (where `candidate == display_name`) and the
    frontmatter-`name:` mismatch check (where `candidate` is the
    frontmatter value). The finding embeds the candidate verbatim
    so the two cases are distinguishable by inspection."""
    if constraints.name_pattern.match(candidate):
        return None
    return (
        f"{pack_name}: {primitive}/{display_name}: "
        f"name does not match {constraints.name_pattern.pattern} "
        f"(got {candidate!r}; "
        f"binding target: {_render_binding(constraints, 'name_pattern')}): "
        f"{relpath}"
    )


def _length_finding(
    pack_name: str,
    primitive: str,
    display_name: str,
    constraints: Constraints,
    relpath: str,
) -> str | None:
    """Length check for the on-disk name only. The display_name slot
    IS the candidate; no separate frontmatter-name length finding —
    per spec AC3, projection risk for over-long frontmatter `name:`
    is not separately documented and the dir/stem length covers the
    operational case."""
    if len(display_name) <= constraints.name_max:
        return None
    return (
        f"{pack_name}: {primitive}/{display_name}: "
        f"name length exceeds {constraints.name_max} "
        f"(got {len(display_name)}; "
        f"binding target: {_render_binding(constraints, 'name_max')}): "
        f"{relpath}"
    )


def _description_findings(
    pack_name: str,
    primitive: str,
    display_name: str,
    text: str,
    constraints: Constraints,
    relpath: str,
) -> list[str]:
    out: list[str] = []
    fields = _extract_frontmatter_fields(text, {"description"})
    description = fields.get("description")
    if description is _MULTILINE:
        out.append(
            f"{pack_name}: {primitive}/{display_name}: description "
            f"must be a single-line value: {relpath}"
        )
        return out
    if not isinstance(description, str) or not description:
        return out
    if len(description) > constraints.description_max:
        out.append(
            f"{pack_name}: {primitive}/{display_name}: description length "
            f"exceeds {constraints.description_max} (got {len(description)}; "
            f"binding target: {_render_binding(constraints, 'description_max')}): "
            f"{relpath}"
        )
    return out


def lint_pack(pack_dir: Path, constraints: Constraints | None = None) -> list[str]:
    """Return a list of human-readable violation strings for one pack.

    Empty list ⇒ clean. Each string is suitable for stderr emission;
    callers decide how to format / exit.

    When `constraints` is supplied, the per-target metadata gate runs
    after the portability sweep and the combined findings are sorted
    by trailing relpath (the AC10 invariant). When omitted, behaviour
    matches the pre-vocab gate exactly.
    """
    findings: list[str] = []
    for subtree_name in _PACK_SUBTREES:
        subtree = pack_dir / subtree_name
        if not subtree.exists():
            continue
        # Walk via `rglob("*")` so directory entries are also checked;
        # a reserved-name *directory* (e.g. `seeds/NUL/`) is just as
        # poisonous as a reserved-name file.
        for entry in sorted(subtree.rglob("*")):
            relpath = entry.relative_to(pack_dir).as_posix()
            if entry.is_symlink():
                findings.append(
                    f"{pack_dir.name}: symlink not portable to Windows: {relpath}"
                )
                # Don't descend into symlinks — they may target outside
                # the pack and trigger spurious findings. The symlink
                # itself is already the violation.
                continue
            try:
                assert_portable_name(relpath)
            except PathJailError as exc:
                findings.append(f"{pack_dir.name}: {exc}")
    if constraints is not None:
        findings.extend(_check_skill_metadata(pack_dir, constraints))
        findings.extend(_check_agent_metadata(pack_dir, constraints))
    # Sort unconditionally so the trailing-relpath invariant holds in
    # both call modes — a portability-only caller with violations
    # spanning both subtrees gets the same deterministic ordering as
    # the gated path. Per-subtree `rglob` already returns entries
    # sorted, so for single-subtree fixtures the sort is a no-op.
    findings.sort(key=lambda f: f.rsplit(": ", 1)[-1])
    return findings


def lint_all_packs(
    packs_dir: Path,
    constraints: Constraints | None = None,
) -> dict[str, list[str]]:
    """Walk every immediate subdirectory of `packs_dir` that contains a
    `pack.toml`, return `{pack_name: [findings...]}`.

    Missing `packs_dir` returns an empty dict — caller decides whether
    that's an error in their context.
    """
    result: dict[str, list[str]] = {}
    if not packs_dir.exists():
        return result
    for entry in sorted(packs_dir.iterdir()):
        if not entry.is_dir():
            continue
        if not (entry / "pack.toml").exists():
            continue
        result[entry.name] = lint_pack(entry, constraints=constraints)
    return result


def cmd_lint_packs(args: argparse.Namespace) -> int:
    """argparse entrypoint. Exit code:
        0 — every pack clean
        1 — at least one finding, or vocab load failure
    """
    packs_dir = Path(args.packs_dir).resolve()
    if not packs_dir.exists():
        print(f"lint-packs: packs-dir not found: {packs_dir}", file=sys.stderr)
        return 1
    vocab, err = _load_target_vocab(packs_dir)
    if err is not None:
        print(err, file=sys.stderr)
        print(
            "lint-packs: configuration error — no packs were checked",
            file=sys.stderr,
        )
        return 1
    constraints, err = _strictest_constraints(vocab)
    if err is not None:
        print(err, file=sys.stderr)
        print(
            "lint-packs: configuration error — no packs were checked",
            file=sys.stderr,
        )
        return 1
    results = lint_all_packs(packs_dir, constraints=constraints)
    total = 0
    for _pack_name, findings in results.items():
        for finding in findings:
            print(finding, file=sys.stderr)
            total += 1
    if total:
        print(
            f"lint-packs: {total} violation(s) across "
            f"{sum(1 for f in results.values() if f)} pack(s)",
            file=sys.stderr,
        )
        return 1
    return 0
