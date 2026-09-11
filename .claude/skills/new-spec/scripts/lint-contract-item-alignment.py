#!/usr/bin/env python3
"""Check that a loop contract's items line up: identifiers, references, coverage.

Scope is deliberately narrow. This decides *item alignment* inside one spec
directory and owns no lifecycle question -- status vocabulary, ship transitions,
deferral anchors and contract traceability belong to the spec-status lint, and
duplicating them here would put two homes on one obligation.

Seven rules, all mechanical:

  1. every acceptance criterion carries a well-formed identifier
  2. identifiers are unique within the spec directory
  3. no identifier appears in the retired list
  4. every criterion-class reference in spec.md and plan.md resolves
  5. every criterion is named by at least one task *entry*
  6. every criterion appears in exactly one verification group
  7. a verification item's identifier is its own, not derived from what it serves

Rule 5 is scoped to task entries -- a task's ``Tests:`` and ``Done when:``
blocks -- and not to the whole document. The weaker form, "does this identifier
appear anywhere in plan.md", passes on a mention in prose, in a changelog, or in
another task's rationale; it went green on this repository's own contract while
a criterion had no implementing bullet at all.

Forward-only by construction: a spec whose criteria carry no identifiers is
skipped entirely, so introducing this check does not fail a corpus authored
before the convention existed.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CRITERION = re.compile(r"^- \[[ x]\] \*\*(AC-\d{4})\.\*\* ", re.M)
UNLABELLED = re.compile(r"^- \[[ x]\] (?!\*\*(?:AC|VI)-\d{4}\.\*\*)", re.M)
CRITERION_REF = re.compile(r"\bAC-\d{4}\b")
ITEM_REF = re.compile(r"\bVI-\d{4}\b")
MALFORMED = re.compile(r"\b(?:AC|VI)-(?!\d{4}\b)[A-Za-z0-9]+\b")
TASK = re.compile(r"^### (T\d+)\b(.*?)(?=^### T\d+\b|\Z)", re.M | re.S)
ENTRY = re.compile(r"\*\*(?:Tests|Done when):\*\*(.*?)(?=\n\*\*[A-Z]|\Z)", re.S)
GROUP_ITEM = re.compile(r"^- \*\*(.+?)\*\*", re.M | re.S)
RETIRED_HEADING = re.compile(r"^## Retired identifiers\s*$", re.M)
RETIRED_ENTRY = re.compile(r"^[-*]\s+`?((?:AC|VI)-\d{4})`?\s*$", re.M)


def _section(text: str, heading: str) -> str:
    """Return the body under a level-two heading, or "" when it is absent."""
    match = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def retired(spec: str) -> set[str]:
    """Identifiers recorded as retired.

    An absent heading is an empty list, not a finding: omitting it while nothing
    has been retired is the convention, so absence is the normal state.
    """
    if not RETIRED_HEADING.search(spec):
        return set()
    return set(RETIRED_ENTRY.findall(_section(spec, "Retired identifiers")))


def verification_groups(spec: str) -> dict[str, int]:
    """Count the Testing Strategy groups each criterion appears in.

    A group is a list item whose leading bold segment names its criteria in
    parentheses. Reading the whole section instead would count a criterion named
    in a group's explanatory prose as a second group.
    """
    counts: dict[str, int] = {}
    for lead in GROUP_ITEM.findall(_section(spec, "Testing Strategy")):
        for ident in set(CRITERION_REF.findall(lead)):
            counts[ident] = counts.get(ident, 0) + 1
    return counts


def task_entries(plan: str) -> dict[str, list[str]]:
    """Map each criterion to the tasks whose entries name it.

    Only ``Tests:`` and ``Done when:`` blocks count. ``Approach:`` is an
    instruction no completion gate reads, and prose elsewhere is not a claim that
    any task verifies the criterion.
    """
    named: dict[str, list[str]] = {}
    for task, body in TASK.findall(plan):
        scope = "".join(ENTRY.findall(body))
        for ident in set(CRITERION_REF.findall(scope)):
            named.setdefault(ident, []).append(task)
    return named


def check(spec_dir: Path) -> tuple[list[str], bool]:
    """Return findings for one spec directory, and whether the check ran.

    The second value distinguishes "no findings" from "not applicable". A caller
    that cannot tell them apart reads a skipped check as a clean one.
    """
    spec_path, plan_path = spec_dir / "spec.md", spec_dir / "plan.md"
    if not spec_path.is_file():
        return [f"{spec_dir}: no spec.md"], False
    spec = spec_path.read_text(encoding="utf-8")
    plan = plan_path.read_text(encoding="utf-8") if plan_path.is_file() else ""

    criteria = CRITERION.findall(spec)
    if not criteria:
        return [], False                      # forward-only: unlabelled specs are skipped

    findings: list[str] = []
    rel = spec_dir.as_posix()

    seen: set[str] = set()
    for ident in criteria:                                        # rules 1-3
        if ident in seen:
            findings.append(f"{rel}/spec.md: {ident} is assigned twice")
        seen.add(ident)
    for ident in sorted(seen & retired(spec)):
        findings.append(f"{rel}/spec.md: {ident} is retired and must not be reused")
    # Scoped to the section, not the document. A spec legitimately carries
    # checkboxes elsewhere -- a rollout step, a migration list -- and scanning
    # the whole file reported those as unlabelled criteria and failed a valid
    # spec. Line numbers are offset back to the file so the finding is locatable.
    section = _section(spec, "Acceptance Criteria")
    offset = spec[: spec.find(section)].count("\n") if section else 0
    for lineno, line in enumerate(section.splitlines(), 1):
        if UNLABELLED.match(line + "\n"):
            findings.append(
                f"{rel}/spec.md:{lineno + offset}: criterion carries no identifier"
            )

    for name, text in (("spec.md", spec), ("plan.md", plan)):     # rules 1 and 4
        for bad in sorted(set(MALFORMED.findall(text))):
            findings.append(f"{rel}/{name}: malformed identifier {bad}")
        for ref in sorted(set(CRITERION_REF.findall(text)) - seen):
            findings.append(f"{rel}/{name}: {ref} resolves to no criterion")

    if plan:                                                      # rule 5
        named = task_entries(plan)
        mentioned = set(CRITERION_REF.findall(plan))
        for ident in criteria:
            if ident not in named:
                hint = " (mentioned in plan, but not in a task entry)" if ident in mentioned else ""
                findings.append(f"{rel}/plan.md: {ident} is named by no task entry{hint}")

    groups = verification_groups(spec)                            # rule 6
    for ident in criteria:
        count = groups.get(ident, 0)
        if count != 1:
            where = "no verification group" if count == 0 else f"{count} verification groups"
            findings.append(f"{rel}/spec.md: {ident} appears in {where}")

    for item in sorted(set(ITEM_REF.findall(plan))):              # rule 7
        digits = item.split("-")[1]
        if f"AC-{digits}" in seen:
            findings.append(
                f"{rel}/plan.md: {item} mirrors AC-{digits}; a verification "
                f"item's identifier is its own, never derived from what it serves"
            )
    return findings, True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("spec_dir", nargs="*", type=Path)
    args = parser.parse_args(argv)

    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    root = args.root.resolve()
    targets = [d.resolve() for d in args.spec_dir] or sorted(
        p.parent for p in (root / "docs" / "specs").glob("*/spec.md")
    )

    findings, ran, skipped = [], 0, 0
    for target in targets:
        if root not in target.parents and target != root:
            print(f"lint-contract-item-alignment: refusing path outside root: {target}")
            return 2
        found, applied = check(target)
        findings.extend(found)
        ran += applied
        skipped += not applied

    for finding in findings:
        print(f"lint-contract-item-alignment: {finding}")
    print(
        f"lint-contract-item-alignment: {len(findings)} finding(s); "
        f"{ran} spec(s) checked, {skipped} skipped as unlabelled."
    )
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
