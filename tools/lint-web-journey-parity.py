#!/usr/bin/env python3
"""Guards every web journey page against skill-count drift from its pack.

Each file in web/src/content/journeys/ carries a `skills:` list in its YAML
frontmatter. The `pack:` field names the pack it describes. The count of
entries in the `skills:` list must match the count of skill directories in
packs/<pack>/.apm/skills/.

Invariant:
  For every journey file, len(skills) == len(packs/<pack>/.apm/skills/*)

A skill added to a pack without a corresponding journey update trips the
invariant; a journey entry added without a matching skill directory also trips
it. Either way the author is forced to reconcile.

Exit 0 when every journey is in parity; exit 1 on any drift.

Fixture mode (used by the paired self-test): set WJP_JOURNEY_DIR and
WJP_PACKS_DIR to point to fixture directories instead of the real tree.
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys


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


def _parse_frontmatter(text: str) -> tuple[str | None, int]:
    """Return (pack_name, skill_count) from YAML frontmatter.

    Parses just enough YAML to extract the `pack:` scalar and count
    `- name:` entries under the `skills:` mapping key. No external
    dependency — avoids PyYAML not being installed.
    """
    if not text.startswith("---"):
        return None, 0
    end = text.find("\n---", 3)
    if end == -1:
        return None, 0
    fm = text[3:end]

    pack: str | None = None
    skill_count = 0
    in_skills = False

    for line in fm.splitlines():
        m = re.match(r'^pack:\s+"?([^"\s]+)"?', line)
        if m:
            pack = m.group(1)
            continue
        if re.match(r"^skills:\s*$", line):
            in_skills = True
            continue
        if in_skills:
            if re.match(r"\s+- name:", line):
                skill_count += 1
            elif line and not line[0].isspace():
                in_skills = False

    return pack, skill_count


def main() -> int:
    root = _repo_root()
    journey_dir = pathlib.Path(
        os.environ.get("WJP_JOURNEY_DIR", root / "web/src/content/journeys")
    )
    packs_dir = pathlib.Path(
        os.environ.get("WJP_PACKS_DIR", root / "packs")
    )

    if not journey_dir.exists():
        print(
            f"lint-web-journey-parity: journey directory not found: {journey_dir}",
            file=sys.stderr,
        )
        return 1

    findings: list[str] = []
    checked = 0

    for journey_file in sorted(journey_dir.glob("*.md")):
        text = journey_file.read_text(encoding="utf-8")
        pack, journey_count = _parse_frontmatter(text)

        if pack is None:
            findings.append(f"  {journey_file.name}: no `pack:` field in frontmatter")
            continue

        skills_dir = packs_dir / pack / ".apm" / "skills"
        if not skills_dir.exists():
            findings.append(
                f"  {journey_file.name}: pack `{pack}` has no .apm/skills/ directory"
            )
            continue

        actual_count = sum(1 for d in skills_dir.iterdir() if d.is_dir())
        checked += 1

        if journey_count != actual_count:
            diff = actual_count - journey_count
            action = "add" if diff > 0 else "remove"
            findings.append(
                f"  {journey_file.name} (pack: {pack}): "
                f"journey lists {journey_count} skill(s), "
                f"pack has {actual_count} — "
                f"{action} {abs(diff)} from the journey's `skills:` list"
            )

    if findings:
        print("lint-web-journey-parity: skill-count drift detected:", file=sys.stderr)
        for f in findings:
            print(f, file=sys.stderr)
        return 1

    print(f"lint-web-journey-parity: all {checked} journeys in parity")
    return 0


if __name__ == "__main__":
    sys.exit(main())
