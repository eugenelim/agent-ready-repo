#!/usr/bin/env python3
"""Guards the fixed, learnable structure of every web journey page.

Each file in web/src/content/journeys/ must carry:

  1. a `contract:` frontmatter object with all four keys — useItWhen,
     youProvide, youReceive, yourDecisions;
  2. a staged narrative whose stages use ONLY the fixed label set, in the
     fixed order, with `Output` always present:
       You provide  <  <Actor> does  <  You do  <  You decide  <  Output
     where <Actor> is one of the closed set {Agent, Reviewer, Loop};
  3. no surviving `## Stage N —`-format heading (a half-converted journey).

This freezes the consistency invariant the journey-template-revamp spec
introduces (docs/specs/journey-template-revamp/spec.md): structure never
varies, only content does. Prose wording quality stays a reviewer call —
this lint guards structure, not phrasing.

Exit 0 when every journey conforms; exit 1 on any violation.

Fixture mode (used by the paired self-test): set LJC_JOURNEY_DIR to point at
a fixture directory instead of the real tree.
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

CONTRACT_KEYS = ("useItWhen", "youProvide", "youReceive", "yourDecisions")

ACTORS = ("Agent", "Reviewer", "Loop")

# label -> rank (fixed order). Actor labels are handled separately.
FIXED_RANK = {
    "You provide": 0,
    "<Actor> does": 1,
    "You do": 2,
    "You decide": 3,
    "Output": 4,
}

# Stages are h3 (`### N.`), subordinate to the section's "The journey" h2.
_HEADING_NEW = re.compile(r"^###\s+(\d+)\.\s+\S")
# Old formats that must not survive: the `## Stage N —` prose narrative, and a
# stage left at h2 (`## N.`) before the h3 subordination fix.
_HEADING_OLD = re.compile(r"^##\s+(?:Stage\s+\d+|\d+\.)", re.IGNORECASE)
_LABEL = re.compile(r"^\s*-\s+\*\*(.+?):\*\*")
_ACTOR_DOES = re.compile(r"^(Agent|Reviewer|Loop) does$")


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
    """Return (frontmatter, body). Empty frontmatter if none present."""
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    fm = text[3:end]
    body = text[end + 4:]
    return fm, body


def _check_contract(fm: str) -> list[str]:
    """The frontmatter must carry a contract: block with all four keys."""
    lines = fm.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^contract:\s*$", line):
            start = i
            break
    if start is None:
        return ["missing `contract:` frontmatter block"]

    # Collect the indented block under `contract:`.
    block: list[str] = []
    for line in lines[start + 1:]:
        if line and not line[0].isspace():
            break
        block.append(line)

    missing = [
        key for key in CONTRACT_KEYS
        if not any(re.match(rf"\s+{key}:", b) for b in block)
    ]
    return [f"contract missing key `{k}`" for k in missing]


def _check_stages(body: str) -> list[str]:
    """Validate the staged narrative's fixed labels."""
    findings: list[str] = []
    lines = body.splitlines()

    # An old-format heading anywhere is a hard failure.
    for line in lines:
        if _HEADING_OLD.match(line):
            findings.append(
                f"surviving old-format heading: {line.strip()!r} "
                "(convert to `## N. <title>`)"
            )

    # Find new-format stage headings and the label lines in each section.
    stage_starts = [i for i, l in enumerate(lines) if _HEADING_NEW.match(l)]
    if not stage_starts:
        findings.append("no `## N.`-format stages found")
        return findings

    bounds = stage_starts + [len(lines)]
    for idx in range(len(stage_starts)):
        start = bounds[idx]
        end = bounds[idx + 1]
        heading = lines[start].strip()
        labels: list[str] = []
        for line in lines[start + 1:end]:
            if line.startswith("##"):
                break
            m = _LABEL.match(line)
            if m:
                labels.append(m.group(1).strip())

        if not labels:
            findings.append(f"stage {heading!r}: no fixed-label lines")
            continue

        ranks: list[int] = []
        for label in labels:
            if _ACTOR_DOES.match(label):
                ranks.append(FIXED_RANK["<Actor> does"])
            elif label in FIXED_RANK:
                ranks.append(FIXED_RANK[label])
            elif label.endswith(" does"):
                actor = label[:-5]
                findings.append(
                    f"stage {heading!r}: unknown actor {actor!r} "
                    f"(allowed: {', '.join(ACTORS)})"
                )
            else:
                findings.append(
                    f"stage {heading!r}: unknown label `{label}` "
                    "(not in the fixed set)"
                )

        if "Output" not in labels:
            findings.append(f"stage {heading!r}: missing `Output` label")

        if ranks != sorted(ranks):
            findings.append(
                f"stage {heading!r}: labels out of fixed order ({labels})"
            )

    return findings


def main() -> int:
    root = _repo_root()
    journey_dir = pathlib.Path(
        os.environ.get("LJC_JOURNEY_DIR", root / "web/src/content/journeys")
    )

    if not journey_dir.exists():
        print(
            f"lint-journey-contract: journey directory not found: {journey_dir}",
            file=sys.stderr,
        )
        return 1

    findings: list[str] = []
    checked = 0

    for jf in sorted(journey_dir.glob("*.md")):
        text = jf.read_text(encoding="utf-8")
        fm, body = _split_frontmatter(text)
        file_findings = _check_contract(fm) + _check_stages(body)
        checked += 1
        for f in file_findings:
            findings.append(f"  {jf.name}: {f}")

    if findings:
        print("lint-journey-contract: structural violations:", file=sys.stderr)
        for f in findings:
            print(f, file=sys.stderr)
        return 1

    print(f"lint-journey-contract: all {checked} journeys conform")
    return 0


if __name__ == "__main__":
    sys.exit(main())
