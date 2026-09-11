#!/usr/bin/env python3
"""Check that a loop contract's items line up: identifiers, references, coverage.

Scope is deliberately narrow. This decides *item alignment* inside one spec
directory and owns no lifecycle question -- status vocabulary, ship transitions,
deferral anchors and contract traceability belong to the spec-status lint, and
duplicating them here would put two homes on one obligation.

The rules, all mechanical:

  1. every acceptance criterion carries a well-formed identifier
  2. identifiers are unique within the spec directory
  3. no identifier appears in the retired list
  4. every criterion-class reference in spec.md and plan.md resolves
  5. every criterion is named by at least one task *entry*
  6. every criterion appears in exactly one verification group
  7. a verification item's identifier is its own, not derived from what it serves
  8. no task entry leaves a code span open, which is how a multi-site edit
     truncates a closing condition without making it look truncated
  9. given a base revision, no criterion was reworded while the assertion blocks
     naming it stayed put -- a criterion whose assertion did not follow it

Rule 5 is scoped to task entries -- a task's ``Tests:`` and ``Done when:``
blocks -- and not to the whole document. The weaker form, "does this identifier
appear anywhere in plan.md", passes on a mention in prose, in a changelog, or in
another task's rationale, so a criterion with no implementing bullet anywhere
reads as covered.

Forward-only by construction: a spec whose criteria carry no identifiers is
skipped entirely, so introducing this check does not fail a corpus authored
before the convention existed.

Exit codes: ``0`` no findings, or nothing to check; ``1`` at least one finding;
``2`` the check could not run -- a missing spec directory, or a path outside the
invocation root.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Every distinct finding this checker can emit, keyed by rule. The catalogue is
# here rather than in the suite so the two cannot drift: the messages below are
# formatted from these fragments, and the suite asserts that each fragment is
# exercised by some case. A rule whose fragment no test observes is a rule with
# no red case, so its suite is green for a reason unrelated to whether the rule
# works. It is a floor, not a derivation: a test could contain a fragment without
# asserting on it, and only running the case proves the branch is reachable.
FINDING_KINDS = {
    "unlabelled": "criterion carries no identifier",
    "duplicate": "is assigned twice",
    "retired": "is retired and must not be reused",
    "malformed": "malformed identifier",
    "unresolved": "resolves to no criterion",
    "no-task-entry": "is named by no task entry",
    "group-count": "appears in",
    "derived-item": "mirrors",
    "unconfined": "refusing path outside root",
    "capped": "more finding(s) in",
    "broken-entry": "entry has an unterminated code span",
    "stale-assertion": "was reworded with no changed assertion in",
}

# Findings are listed up to this many, then grouped by spec with an exact
# remainder. Uncapped, thirty bad specs produced 211 lines and 18KB -- and a
# checker's output lives in its caller's context for the rest of a session, so
# an error path that floods is a worse failure than the one it reports. The
# counts stay exact and `--verbose` restores the full list, following the
# repository's own convention for its spec-status lint.
FINDING_CAP = 20

# The rules that report no input when plan.md is absent. Rule 4 is deliberately
# not here: it reads both texts and still decides the spec half, so it is
# partially applied rather than unapplied, and listing it would claim a rule ran
# on nothing when half of it ran. A rule that silently runs on nothing is the
# partial-read-as-clean failure this module exists to detect in other artifacts.
PLAN_GATED = ("task-entry", "derived-item", "broken-entry")

CRITERION = re.compile(r"^- \[[ x]\] \*\*(AC-\d{4})\.\*\* ", re.M)
CRITERION_LINE = re.compile(r"- \[[ x]\] \*\*(AC-\d{4})\.\*\* ")
UNLABELLED = re.compile(r"^- \[[ x]\] (?!\*\*(?:AC|VI)-\d{4}\.\*\*)", re.M)
CRITERION_REF = re.compile(r"\bAC-\d{4}\b")
ITEM_REF = re.compile(r"\bVI-\d{4}\b")
MALFORMED = re.compile(r"\b(?:AC|VI)-(?!\d{4}\b)[A-Za-z0-9]+\b")
# A task body ends at the next task *or the next level-two heading*. Running it
# to end-of-file makes the last task's body swallow every section after it --
# Rollout, Risks, the Changelog -- so a criterion named in the changelog is
# credited to a task entry. That is the mention-anywhere form rule 5 exists to
# eliminate, reappearing inside rule 5.
TASK = re.compile(r"^### (T\d+)\b(.*?)(?=^### T\d+\b|^## |\Z)", re.M | re.S)
# A field block ends at the next *field label* -- bold, capitalised, colon --
# not at any bold capital. A bold identifier such as `**XX-0000.**` opens a case
# bullet, not a field, and treating it as a boundary truncated a task's Tests
# block at its first bullet.
ENTRY = re.compile(r"\*\*(?:Tests|Done when):\*\*(.*?)(?=\n\*\*[A-Z][A-Za-z ]*:\*\*|\Z)", re.S)
# Fenced blocks carry backticks whose count says nothing about the prose around
# them, so they come out before a span is matched.
FENCE = re.compile(r"^```.*?^```", re.M | re.S)
# A run of three or more written inline is a fence *token* quoted in prose, not a
# span delimiter: markup with no matching run of equal length renders it
# literally. Removing it before matching is what separates "this entry is
# broken" from "this entry mentions a fence".
INLINE_FENCE = re.compile(r"`{3,}")
RUN = re.compile(r"`+")
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
    # No heading check: `_section` returns "" for an absent heading and the entry
    # pattern finds nothing in it, so a guard here changes no outcome for any
    # input and no case can distinguish it.
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


def unterminated(entry: str) -> bool:
    """True when a code span in this entry is opened and never closed.

    Backtick *runs* are matched the way the markup delimits a span -- a span
    opens on a run of N and closes on the next run of exactly N -- rather than
    counted. A run of three written inline in prose ("a fenced ```python
    example") is the common case and is *not* a broken span: with no matching
    run of the same length the markup leaves it literal, so it renders exactly
    as written. Counting backticks reports it, and so did matching runs until an
    inline fence token was removed first.
    """
    return _spans_open(INLINE_FENCE.sub("", FENCE.sub("", entry)))


def _spans_open(text: str) -> bool:
    open_len = None
    for run in RUN.findall(text):
        if open_len is None:
            open_len = len(run)
        elif len(run) == open_len:
            open_len = None
    return open_len is not None


def _changed_lines(root: Path, ref: str, path: Path) -> set[int] | None:
    """New-file line numbers touched since ``ref``, or None when git cannot say.

    None is not an empty set. An unresolvable ref, a tree with no history and a
    missing git binary all mean "unknown", and reporting them as "nothing
    changed" would turn every one of them into a silent clean pass.
    """
    try:
        done = subprocess.run(
            ["git", "-C", str(root), "diff", "-U0", ref, "--", str(path)],
            capture_output=True, text=True, check=False, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    touched: set[int] = set()
    for hunk in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", done.stdout, re.M):
        start = int(hunk.group(1))
        touched.update(range(start, start + int(hunk.group(2) or 1)))
    return touched


def criterion_spans(spec: str) -> list[str | None]:
    """One entry per 1-indexed spec line, naming the criterion it falls under."""
    spans: list[str | None] = [None]      # index 0 unused; spans[n] is line n
    current: str | None = None
    for line in spec.splitlines():
        found = CRITERION_LINE.match(line)
        if found:
            current = found.group(1)
        elif line.startswith("## "):
            current = None
        spans.append(current)
    return spans


def _entry_lines(plan: str) -> set[int]:
    """The 1-indexed lines inside a task's ``Tests:`` or ``Done when:`` block.

    An assertion only ever lives in one of those two blocks. Crediting a change
    anywhere in the document reproduces the mention-anywhere defect rule 5 was
    scoped to eliminate: a changelog bullet naming a criterion silenced this
    rule for eight of them on the contract it was written for.
    """
    inside: set[int] = set()
    for task in TASK.finditer(plan):
        body, base = task.group(2), plan[: task.start(2)].count("\n") + 1
        for entry in ENTRY.finditer(body):
            first = base + body[: entry.start()].count("\n")
            inside.update(range(first, first + entry.group(0).count("\n") + 1))
    return inside


def _plan_owners(plan: str, changed: set[int]) -> set[str]:
    """Which criteria the changed assertion lines belong to.

    A changed line is credited to the criteria named by the bullet it sits
    under, not only to the criteria spelled on the line itself. An added
    constraint is normally written beneath the bullet that already names the
    identifier, so reading the line alone reports a criterion whose assertion
    did in fact follow -- the false alarm this rule cannot afford, since its
    whole value is that it never cries wolf. The scope is the assertion blocks,
    for the reason ``_entry_lines`` records.
    """
    owners: set[str] = set()
    current: set[str] = set()
    entries = _entry_lines(plan)
    for number, line in enumerate(plan.splitlines(), 1):
        stripped = line.lstrip()
        # Only a line-initial field label is a boundary. An *indented* bold
        # label is a constraint written inside a bullet -- exactly where a new
        # assertion lands -- and treating it as a boundary drops the bullet's
        # identifier, which is the same distinction the ENTRY pattern above
        # already had to make.
        if stripped.startswith("- ") or re.match(r"\*\*[A-Z][A-Za-z ]*:\*\*", line) \
                or line.startswith(("#", "|")):
            current = set(CRITERION_REF.findall(line))
        elif not stripped:
            current = set()
        if number in changed and number in entries:
            owners.update(current or CRITERION_REF.findall(line))
    return owners


def stale_assertions(spec_dir: Path, root: Path, ref: str,
                     spec: str, plan: str) -> list[str] | None:
    """Criteria reworded since ``ref`` whose plan lines did not change with them.

    The plan side reads only the task entries that carry assertions. Reading any
    line naming the identifier lets a changelog bullet or a rationale count as
    the assertion following, which is the mention-anywhere form rule 5 is scoped
    to eliminate; narrowing the scope also raised this rule's recall, because the
    wide form had been crediting exactly those non-assertion mentions.
    """
    spec_changed = _changed_lines(root, ref, spec_dir / "spec.md")
    plan_changed = _changed_lines(root, ref, spec_dir / "plan.md")
    if spec_changed is None or plan_changed is None:
        return None
    spans = criterion_spans(spec)
    reworded = {spans[n] for n in spec_changed if n < len(spans) and spans[n]}
    followed = _plan_owners(plan, plan_changed)
    return sorted(reworded - followed)


def check(spec_dir: Path, root: Path | None = None, since: str | None = None) -> tuple[list[str], bool, list[str]]:
    """Return findings, whether the check ran, and which rules could not.

    The second value distinguishes "no findings" from "not applicable"; the third
    distinguishes "no findings" from "some rules had no input". A caller that
    cannot tell those apart reads a partial check as a clean one, which is the
    failure this module exists to detect in other artifacts.
    """
    spec_path, plan_path = spec_dir / "spec.md", spec_dir / "plan.md"
    if not spec_path.is_file():
        return [f"{spec_dir}: no spec.md"], False, []
    spec = spec_path.read_text(encoding="utf-8")
    plan = plan_path.read_text(encoding="utf-8") if plan_path.is_file() else ""

    criteria = CRITERION.findall(spec)
    if not criteria:
        return [], False, []                  # forward-only: unlabelled specs are skipped

    findings: list[str] = []
    # Relative to the invocation root, not an absolute host path: a finding is
    # pasted into a review, a commit message and an issue, and an absolute path
    # is wrong in all three.
    try:
        rel = spec_dir.relative_to(root).as_posix() if root else spec_dir.as_posix()
    except ValueError:
        rel = spec_dir.as_posix()

    seen: set[str] = set()
    for ident in criteria:                                        # rules 1-3
        if ident in seen:
            findings.append(f"{rel}/spec.md: {ident} {FINDING_KINDS['duplicate']}")
        seen.add(ident)
    for ident in sorted(seen & retired(spec)):
        findings.append(f"{rel}/spec.md: {ident} {FINDING_KINDS['retired']}")
    # Scoped to the section, not the document. A spec legitimately carries
    # checkboxes elsewhere -- a rollout step, a migration list -- and scanning
    # the whole file reported those as unlabelled criteria and failed a valid
    # spec. Line numbers are offset back to the file so the finding is locatable.
    section = _section(spec, "Acceptance Criteria")
    offset = spec[: spec.find(section)].count("\n") if section else 0
    for lineno, line in enumerate(section.splitlines(), 1):
        if UNLABELLED.match(line + "\n"):
            findings.append(
                f"{rel}/spec.md:{lineno + offset}: {FINDING_KINDS['unlabelled']}"
            )

    # Rule 4 resolves against live criteria *and* the retired list. Without the
    # second half, retiring a criterion -- the one operation the retired list
    # exists for -- reports the retired identifier as unresolved and fails a
    # correctly retired spec.
    resolvable = seen | retired(spec)
    for name, text in (("spec.md", spec), ("plan.md", plan)):     # rules 1 and 4
        for bad in sorted(set(MALFORMED.findall(text))):
            findings.append(f"{rel}/{name}: {FINDING_KINDS['malformed']} {bad}")
        for ref in sorted(set(CRITERION_REF.findall(text)) - resolvable):
            findings.append(f"{rel}/{name}: {ref} {FINDING_KINDS['unresolved']}")

    unapplied: list[str] = [] if plan else list(PLAN_GATED)
    if plan:                                                      # rule 5
        named = task_entries(plan)
        mentioned = set(CRITERION_REF.findall(plan))
        for ident in criteria:
            if ident not in named:
                hint = " (mentioned in plan, but not in a task entry)" if ident in mentioned else ""
                findings.append(f"{rel}/plan.md: {ident} {FINDING_KINDS['no-task-entry']}{hint}")

    groups = verification_groups(spec)                            # rule 6
    for ident in criteria:
        count = groups.get(ident, 0)
        if count != 1:
            where = "no verification group" if count == 0 else f"{count} verification groups"
            findings.append(f"{rel}/spec.md: {ident} {FINDING_KINDS['group-count']} {where}")

    if plan:                                                      # rule 8
        for task, body in TASK.findall(plan):
            for entry in ENTRY.findall(body):
                if unterminated(entry):
                    findings.append(
                        f"{rel}/plan.md: {task} {FINDING_KINDS['broken-entry']}"
                    )
                    break     # one finding per task; a broken entry usually breaks one clause

    if since and plan:                                            # rule 9
        stale = stale_assertions(spec_dir, root or spec_dir, since, spec, plan)
        if stale is None:
            unapplied.append("stale-assertion")
        else:
            for ident in stale:
                findings.append(
                    f"{rel}/plan.md: {ident} {FINDING_KINDS['stale-assertion']} plan.md "
                    f"since {since}"
                )
    elif since:
        unapplied.append("stale-assertion")
    else:
        unapplied.append("stale-assertion (no --since)")

    for item in sorted(set(ITEM_REF.findall(plan))):              # rule 7
        digits = item.split("-")[1]
        if f"AC-{digits}" in seen:
            findings.append(
                f"{rel}/plan.md: {item} {FINDING_KINDS['derived-item']} AC-{digits}; a verification "
                f"item's identifier is its own, never derived from what it serves"
            )
    return findings, True, unapplied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--verbose", action="store_true",
                        help="list every finding instead of capping the listing")
    parser.add_argument("--since", metavar="REF",
                        help="base revision for the reworded-criterion rule; "
                             "skipped when absent or when the tree has no history")
    parser.add_argument("spec_dir", nargs="*", type=Path)
    args = parser.parse_args(argv)

    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    root = args.root.resolve()
    targets = [d.resolve() for d in args.spec_dir] or sorted(
        p.parent for p in (root / "docs" / "specs").glob("*/spec.md")
    )

    findings, ran, skipped, partial = [], 0, 0, []
    for target in targets:
        if root not in target.parents and target != root:
            print(f"lint-contract-item-alignment: {FINDING_KINDS['unconfined']}: {target}")
            return 2
        found, applied, unapplied = check(target, root, args.since)
        findings.extend(found)
        ran += applied
        skipped += not applied
        if unapplied:
            partial.append(f"{target.name}: {', '.join(unapplied)}")

    shown = findings if (args.verbose or len(findings) <= FINDING_CAP) else findings[:FINDING_CAP]
    for finding in shown:
        print(f"lint-contract-item-alignment: {finding}")
    if len(shown) < len(findings):
        # Grouped by spec rather than truncated mid-list: the reader needs to
        # know which specs are affected, which a flat cut-off hides.
        from collections import Counter
        rest = Counter(f.split(":", 1)[0] for f in findings[FINDING_CAP:])
        for spec, count in rest.most_common(10):
            print(f"lint-contract-item-alignment: {count} {FINDING_KINDS['capped']} {spec}")
        if len(rest) > 10:
            print(f"lint-contract-item-alignment: and {len(rest) - 10} further spec(s)")
        print(f"lint-contract-item-alignment: {len(findings) - len(shown)} finding(s) "
              f"not listed; re-run with --verbose for the full list")
    summary = (f"lint-contract-item-alignment: {len(findings)} finding(s); "
               f"{ran} spec(s) checked, {skipped} skipped as unlabelled")
    if partial:
        summary += f", {len(partial)} partial (rules with no input: {'; '.join(partial)})"
    print(summary + ".")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
