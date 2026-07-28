#!/usr/bin/env python3
"""Validates pack-local JOURNEY.md files.

Each JOURNEY.md in packs/<pack>/JOURNEY.md must:
  - carry a unique journey_id
  - reference only skills that exist in packs/<pack>/.apm/skills/<name>/
  - list exactly as many skills as the pack has .apm/skills/ directories
  - use only STATE_VOCAB values for **State:**, start_state, and end_state
  - include **You decide:** in any stage whose state is in WRITE_STATES
  - include **Output:** in every stage
  - not share a canonical source with a non-generated central journey file

Fixture mode: set LPJ_PACKS_DIR and LPJ_JOURNEY_DIR env vars to point at
fixture directories instead of the real tree.

Exit 0 when all JOURNEY.md files validate; exit 1 on any violation.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

STATE_VOCAB: frozenset[str] = frozenset({
    "read-only",
    "draft",
    "proposed-write",
    "confirmed-write",
    "publish",
    "destructive",
    "no-action-required",
    "decision-required",
    "blocked",
})

WRITE_STATES: frozenset[str] = frozenset({
    "proposed-write",
    "confirmed-write",
    "publish",
    "destructive",
    "decision-required",
})

_HEADING_NEW = re.compile(r"^###\s+\d+\.\s+\S")
_LABEL_VALUE = re.compile(r"^\s*-\s+\*\*(.+?):\*\*\s*(.*)")


def _repo_root() -> pathlib.Path:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return pathlib.Path(r.stdout.strip())
    except FileNotFoundError:
        pass
    return pathlib.Path.cwd()


def _split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    return text[3:end], text[end + 4:]


def _get_scalar(fm: str, key: str) -> str | None:
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", fm, re.MULTILINE)
    return m.group(1).strip() if m else None


def _get_skill_names(fm: str) -> list[str]:
    lines = fm.splitlines()
    in_skills = False
    names: list[str] = []
    for line in lines:
        if re.match(r"^skills:\s*$", line):
            in_skills = True
            continue
        if in_skills:
            if line and not line[0].isspace():
                break
            m = re.match(r"\s+- name:\s+(.+)$", line)
            if m:
                names.append(m.group(1).strip())
    return names


def _check_stages(body: str) -> list[str]:
    findings: list[str] = []
    lines = body.splitlines()
    stage_starts = [i for i, ln in enumerate(lines) if _HEADING_NEW.match(ln)]
    if not stage_starts:
        return findings

    bounds = stage_starts + [len(lines)]
    for idx in range(len(stage_starts)):
        start = bounds[idx]
        end = bounds[idx + 1]
        heading = lines[start].strip()

        label_values: dict[str, str] = {}
        for line in lines[start + 1:end]:
            if line.startswith("##"):
                break
            m = _LABEL_VALUE.match(line)
            if m:
                label_values[m.group(1).strip()] = m.group(2).strip()

        if "Output" not in label_values:
            findings.append(f"stage {heading!r}: missing **Output:** label")

        if "State" not in label_values:
            findings.append(
                f"stage {heading!r}: missing **State:** label"
                " (required in pack-local JOURNEY.md stages)"
            )

        state_val = label_values.get("State")
        if state_val is not None:
            if state_val not in STATE_VOCAB:
                findings.append(
                    f"stage {heading!r}: **State:** value {state_val!r} not in STATE_VOCAB"
                )
            elif state_val in WRITE_STATES and "You decide" not in label_values:
                findings.append(
                    f"stage {heading!r}: state {state_val!r} requires **You decide:** label"
                )

    return findings


def _validate_journey(
    path: pathlib.Path,
    pack_dir: pathlib.Path,
    central_files: dict[str, tuple[str, str]],
) -> list[str]:
    """Return error strings for one JOURNEY.md.

    central_files maps central file stem -> (pack field, generated field).
    """
    text = path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text)
    findings: list[str] = []

    journey_id = _get_scalar(fm, "journey_id")
    if not journey_id:
        findings.append(f"{path}: missing required journey_id")
        return findings

    pack_field = _get_scalar(fm, "pack")
    if pack_field and pack_field != pack_dir.name:
        findings.append(
            f"{path}: pack field {pack_field!r} does not match "
            f"directory name {pack_dir.name!r}"
        )

    for key in ("start_state", "end_state"):
        val = _get_scalar(fm, key)
        if val is not None and val not in STATE_VOCAB:
            findings.append(
                f"{path}: {key} {val!r} is not a valid STATE_VOCAB value"
            )

    skill_names = _get_skill_names(fm)
    skills_dir = pack_dir / ".apm" / "skills"
    pack_skill_dirs = (
        sorted(d.name for d in skills_dir.iterdir() if d.is_dir())
        if skills_dir.exists()
        else []
    )

    if len(skill_names) != len(pack_skill_dirs):
        findings.append(
            f"{path}: skill count mismatch — "
            f"JOURNEY.md lists {len(skill_names)}, "
            f"pack has {len(pack_skill_dirs)}"
        )

    for name in skill_names:
        if name not in pack_skill_dirs:
            findings.append(
                f"{path}: skill {name!r} not found in {skills_dir}"
            )

    pack_name = pack_dir.name
    for stem, (cf_pack, cf_generated) in central_files.items():
        if cf_generated == "true":
            continue
        if stem == journey_id:
            findings.append(
                f"{path}: dual canonical ownership — "
                f"non-generated central file '{stem}.md' has same slug as journey_id"
            )
        elif cf_pack == pack_name:
            findings.append(
                f"{path}: dual canonical ownership — "
                f"non-generated central file '{stem}.md' claims same pack"
            )

    findings.extend(_check_stages(body))
    return findings


def main() -> int:
    root = _repo_root()
    packs_dir = pathlib.Path(
        os.environ.get("LPJ_PACKS_DIR", root / "packs")
    )
    journey_dir = pathlib.Path(
        os.environ.get("LPJ_JOURNEY_DIR", root / "web/src/content/journeys")
    )

    journey_files = sorted(packs_dir.glob("*/JOURNEY.md"))

    if not journey_files:
        print("lint-pack-journeys: no JOURNEY.md files found — nothing to validate")
        return 0

    central_files: dict[str, tuple[str, str]] = {}
    if journey_dir.exists():
        for jf in journey_dir.glob("*.md"):
            text = jf.read_text(encoding="utf-8")
            cfm, _ = _split_frontmatter(text)
            central_files[jf.stem] = (
                _get_scalar(cfm, "pack") or "",
                _get_scalar(cfm, "generated") or "",
            )

    id_to_paths: dict[str, list[pathlib.Path]] = {}
    for jf in journey_files:
        text = jf.read_text(encoding="utf-8")
        fm, _ = _split_frontmatter(text)
        jid = _get_scalar(fm, "journey_id")
        if jid:
            id_to_paths.setdefault(jid, []).append(jf)

    all_findings: list[str] = []

    for jid, paths in id_to_paths.items():
        if len(paths) > 1:
            all_findings.append(
                f"duplicate journey_id {jid!r} found in: "
                + ", ".join(str(p) for p in paths)
            )

    for jf in journey_files:
        all_findings.extend(_validate_journey(jf, jf.parent, central_files))

    if all_findings:
        print("lint-pack-journeys: violations found:", file=sys.stderr)
        for f in all_findings:
            print(f"  {f}", file=sys.stderr)
        return 1

    print(f"lint-pack-journeys: all {len(journey_files)} JOURNEY.md files valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
