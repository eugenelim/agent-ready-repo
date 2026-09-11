#!/usr/bin/env python3
"""Lint the ordered Markdown steps in one or more guidebook directories.

Usage:
    python3 tools/lint-guidebook-steps.py [--contract PATH] GUIDEBOOK [GUIDEBOOK ...]

Each guide page with ``order:`` frontmatter is a step.  The contract at
``guides/AGENTS.md`` supplies the obligation identifiers, their labels, the
closed judgement kinds, and the prohibited vocabulary; this program
deliberately copies none of those lists.

Each obligation is declared by its label opening a line.  One per line here,
because a label wrapped across a newline stops being one token:

    position            **Step N of M — <title>**
    prerequisite_cost   **You need:**  plus  *Skipping costs:*
    concept_resolved    **Concepts:**
    next_step           **Next:**
    utterance           **You type:**
    attributed_response **Agent returns:**  then a blockquote
    variability         **Output varies**
    decision            **You decide:**  or  **No decision gate at this step.**
    judgement_check     **Check (<kind>):**
    failure_path        **If it fails:**
    artifact_location   **You now hold:**
    artifact_outline    **Expect these headings:**

The last three, plus ``utterance``, are per-skill: they are declared inside a
skill's own ``#### Run `<skill>` `` block and nowhere else.

``--contract`` selects the contract file (default: ``guides/AGENTS.md``).
The positional arguments select one or more guidebook directories.

Exit 0 means no findings.  Exit 1 means one or more step findings.  Exit 2
means usage or structural error, such as a missing directory or unreadable
contract.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
SECTION_HEADING = "## The guidebook step contract"
JUDGEMENT_HEADING = "### Judgement kinds"
VOCABULARY_HEADING = "### Prohibited vocabulary"
RUN_HEADING = re.compile(r"^#### Run `([^`]+)`\s*$", re.M)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.M)


@dataclass(frozen=True)
class Contract:
    """The guidebook contract parsed from its one authoritative source."""

    obligations: tuple[str, ...]
    labels: dict[str, str]
    scopes: dict[str, str]
    judgement_kinds: tuple[str, ...]
    prohibited_terms: tuple[str, ...]


@dataclass(frozen=True)
class Finding:
    """One actionable contract failure."""

    path: Path
    step: str
    obligation: str
    detail: str

    def render(self) -> str:
        return f"{self.path} (step {self.step}): {self.obligation}: {self.detail}"


def contract_section(text: str) -> str:
    """Return the contract section, stopping before the next level-two heading."""
    if SECTION_HEADING not in text:
        raise ValueError(f"contract carries no {SECTION_HEADING!r} section")
    return text.split(SECTION_HEADING, 1)[1].split("\n## ", 1)[0]


def obligation_ids_from_contract(text: str) -> tuple[str, ...]:
    """Read table identifiers from the preamble, not the later label table."""
    preamble = contract_section(text).split("\n### ", 1)[0]
    return tuple(re.findall(r"^\|\s*`([a-z_]+)`\s*\|", preamble, re.M))


def judgement_kinds_from_contract(text: str) -> tuple[str, ...]:
    """Read the closed set from list items only."""
    section = contract_section(text)
    if JUDGEMENT_HEADING not in section:
        return ()
    body = section.split(JUDGEMENT_HEADING, 1)[1].split("\n### ", 1)[0]
    return tuple(re.findall(r"^- `([a-z][a-z_-]+)`\s*$", body, re.M))


def prohibited_terms_from_contract(text: str) -> tuple[str, ...]:
    """Read lexical prohibited vocabulary from its dedicated subsection."""
    section = contract_section(text)
    if VOCABULARY_HEADING not in section:
        return ()
    body = section.split(VOCABULARY_HEADING, 1)[1].split("\n### ", 1)[0]
    return tuple(re.findall(r"`([a-z][a-z ]+)`", body))


def parse_contract(path: Path) -> Contract:
    """Parse contract identifiers, label forms, scopes, kinds, and vocabulary."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"cannot read contract {path}: {error}") from error
    section = contract_section(text)
    obligations = obligation_ids_from_contract(text)
    if not obligations or len(obligations) != len(set(obligations)):
        raise ValueError("contract obligation identifiers are missing or duplicate")
    label_area = section.split("### How a step is written", 1)
    if len(label_area) != 2:
        raise ValueError("contract carries no label table")
    label_area = label_area[1].split("### Judgement kinds", 1)[0]
    labels: dict[str, str] = {}
    scopes: dict[str, str] = {}
    for obligation, label, scope in re.findall(
        r"^\|\s*`([a-z_]+)`\s*\|\s*(.*?)\s*\|\s*(step|per skill)\s*\|",
        label_area,
        re.M,
    ):
        labels[obligation] = label
        scopes[obligation] = scope
    missing = set(obligations) - set(labels)
    if missing:
        raise ValueError(f"contract label table omits: {', '.join(sorted(missing))}")
    kinds = judgement_kinds_from_contract(text)
    if not kinds:
        raise ValueError("contract declares no judgement kinds")
    return Contract(obligations, labels, scopes, kinds, prohibited_terms_from_contract(text))


def _frontmatter_body(text: str) -> tuple[str, str]:
    """Return frontmatter and body, raising for a malformed guide step."""
    if not text.startswith("---\n"):
        raise ValueError("has no opening frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("has unclosed frontmatter")
    return text[4:end], text[end + 4 :]


def _has_order(frontmatter: str) -> bool:
    return bool(re.search(r"^order:\s*[^\s#]+", frontmatter, re.M))


def _label_variants(label: str) -> tuple[str, ...]:
    """Return the literal labels embedded in one contract table cell."""
    return tuple(re.findall(r"`([^`]+)`", label))


def _label_alternatives(label: str) -> tuple[str, ...]:
    """Return only the labels that are *alternatives* to the primary one.

    A label cell can hold two different relationships and expresses both the
    same way. `decision` offers an alternative — "or `**No decision gate at
    this step.**`" — while `prerequisite_cost` names a required companion —
    "plus `*Skipping costs:*`". Treating a companion as an alternative made a
    missing `**You need:**` pass by matching the companion line, which the
    AC-0003 omission fixture caught. Only the text after " or " is alternative.
    """
    if " or " not in label:
        return ()
    return tuple(re.findall(r"`([^`]+)`", label.split(" or ", 1)[1]))


def _line_with_label(lines: list[str], label: str) -> int | None:
    prefixes = _label_variants(label)
    for index, line in enumerate(lines):
        if any(line.startswith(prefix) for prefix in prefixes):
            return index
        if prefixes and prefixes[0].startswith("**Step N of M") and re.match(
            r"^\*\*Step \d+ of \d+ — .+\*\*$", line
        ):
            return index
        if prefixes and prefixes[0].startswith("**Check (") and re.match(
            r"^\*\*Check \([^)]+\):\*\*", line
        ):
            return index
        # A malformed judgement label is still a declared judgement check, so
        # report its missing kind rather than misclassifying it as absent.
        if prefixes and prefixes[0].startswith("**Check (") and line.startswith("**Check"):
            return index
    return None


def _skill_blocks(body: str) -> list[tuple[str, str]]:
    """Return each named skill and only the text inside its own Run block."""
    matches = list(RUN_HEADING.finditer(body))
    return [
        (match.group(1), body[match.end() : matches[index + 1].start() if index + 1 < len(matches) else len(body)])
        for index, match in enumerate(matches)
    ]


def _following_nonblank(lines: list[str], index: int) -> str | None:
    for line in lines[index + 1 :]:
        if line.strip():
            return line
    return None


def _outline_lines(lines: list[str], index: int) -> list[str]:
    """Return list items following the outline label, stopping at another label."""
    values: list[str] = []
    for line in lines[index + 1 :]:
        if line.startswith("**"):
            break
        if line.startswith("- "):
            values.append(line[2:].strip().strip("`"))
    return values


def _source_path(lines: list[str], index: int, step_path: Path) -> Path | None:
    """Resolve a declared local outline source, or None for authored outlines."""
    for line in lines[index + 1 :]:
        if line.startswith("**") and "Source:" not in line:
            break
        match = re.search(r"\*Source:\*\s*`([^`]+)`", line)
        if match:
            value = match.group(1)
            if value.casefold() == "authored":
                return None
            candidate = (step_path.parent / value).resolve()
            return candidate
    return Path("/missing-source")


def _check_concepts(lines: list[str], index: int, step_path: Path) -> str | None:
    """Require every named concept to link locally or carry a short explanation."""
    entries: list[str] = []
    for line in lines[index + 1 :]:
        if line.startswith("**"):
            break
        if line.startswith("- "):
            entries.append(line[2:].strip())
    if not entries:
        return "Concepts has no named concepts with a link or bounded explanation"
    for entry in entries:
        links = MARKDOWN_LINK.findall(entry)
        if links:
            for target in links:
                target = target.split("#", 1)[0]
                if not target or "://" in target or target.startswith("#"):
                    return f"concept link does not resolve within the repository: {entry}"
                candidate = (step_path.parent / target).resolve()
                if step_path.is_relative_to(REPO_ROOT) and not candidate.is_relative_to(REPO_ROOT):
                    return f"concept link escapes the repository: {entry}"
                if not candidate.is_file():
                    return f"concept link does not resolve: {entry}"
        elif ":" not in entry or len(entry) > 240:
            return f"concept resolves to neither a local link nor bounded explanation: {entry}"
    return None


def _check_obligation(
    contract: Contract, obligation: str, path: Path, step: str, body: str
) -> list[Finding]:
    """Check one contract row, using its parsed label and scope."""
    label = contract.labels[obligation]
    blocks = [("step", body)] if contract.scopes[obligation] == "step" else _skill_blocks(body)
    if contract.scopes[obligation] == "per skill" and not blocks:
        return [Finding(path, step, obligation, "no `#### Run `<skill>` block declares it")]
    findings: list[Finding] = []
    for skill, target in blocks:
        lines = target.splitlines()
        index = _line_with_label(lines, label)
        subject = "step" if skill == "step" else f"skill `{skill}`"
        if index is None:
            findings.append(Finding(path, step, obligation, f"missing on {subject}"))
            continue
        line = lines[index]
        variants = _label_variants(label)
        primary = variants[0] if variants else label
        # A label cell may offer an explicit alternative — `decision`'s "No
        # decision gate at this step.", and `artifact_location`/
        # `artifact_outline`'s "Writes no artifact." Those declare that the
        # obligation does not apply here, so the primary form's semantic check
        # must not then demand a path or an outline from them.
        # An explicit alternative declares that the obligation does not apply
        # here — `decision`'s "No decision gate at this step.", and
        # `artifact_location`/`artifact_outline`'s "Writes no artifact." The
        # primary form's semantic check must not then demand a path or an
        # outline. A *companion* label is not an alternative and is excluded by
        # `_label_alternatives`, or a missing primary label would pass by
        # matching its companion.
        if any(line.startswith(alt) for alt in _label_alternatives(label)):
            continue
        if primary.startswith("**Step") and not re.match(r"^\*\*Step \d+ of \d+ — .+\*\*$", line):
            findings.append(Finding(path, step, obligation, "position label is malformed"))
        elif any("Skipping costs:" in variant for variant in variants) and not any(item.startswith("*Skipping costs:*") for item in lines[index + 1 :]):
            findings.append(Finding(path, step, obligation, "missing `*Skipping costs:*`"))
        elif primary.startswith("**Agent returns:") and not (_following_nonblank(lines, index) or "").startswith(">"):
            findings.append(Finding(path, step, obligation, "must be followed by an attributed blockquote"))
        elif primary.startswith("**Check ("):
            match = re.match(r"^\*\*Check \(([^)]+)\):\*\*", line)
            if match is None:
                findings.append(Finding(path, step, obligation, "declares no judgement kind"))
            elif match.group(1) not in contract.judgement_kinds:
                findings.append(Finding(path, step, obligation, f"kind `{match.group(1)}` is not in the closed set"))
        elif primary.startswith("**You now hold:") and not re.search(r"`[^`]+`", line):
            findings.append(Finding(path, step, obligation, "must name a backticked artifact path"))
        elif primary.startswith("**Expect these headings:"):
            outline = _outline_lines(lines, index)
            source = _source_path(lines, index, path)
            if not outline:
                findings.append(Finding(path, step, obligation, "lists no expected headings"))
            elif source is not None:
                if not source.is_file():
                    findings.append(Finding(path, step, obligation, "declared outline source does not resolve"))
                else:
                    actual = [item.strip().strip("`") for item in HEADING.findall(source.read_text(encoding="utf-8"))]
                    if outline != actual:
                        findings.append(Finding(path, step, obligation, "expected headings diverge from declared source"))
        elif primary.startswith("**Concepts:"):
            detail = _check_concepts(lines, index, path)
            if detail:
                findings.append(Finding(path, step, obligation, detail))
    return findings


def registered_checks(
    contract: Contract,
) -> dict[str, Callable[[Path, str, str], list[Finding]]]:
    """Register one executable checker for each obligation in this contract."""
    return {
        obligation: (
            lambda path, step, body, obligation=obligation: _check_obligation(
                contract, obligation, path, step, body
            )
        )
        for obligation in contract.obligations
    }


def check_step(path: Path, contract: Contract) -> list[Finding]:
    """Return all contract findings for one ordered guide page."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return []
    frontmatter, body = _frontmatter_body(text)
    if not _has_order(frontmatter):
        return []
    step = path.stem
    findings = [
        finding
        for check in registered_checks(contract).values()
        for finding in check(path, step, body)
    ]
    lowered = body.casefold()
    for term in contract.prohibited_terms:
        if term.casefold() in lowered:
            findings.append(Finding(path, step, "prohibited vocabulary", f"contains `{term}`"))
    return findings


def lint(directories: list[Path], contract: Contract) -> list[Finding]:
    """Lint all ordered Markdown steps under the selected directories."""
    findings: list[Finding] = []
    for directory in directories:
        for path in sorted(directory.rglob("*.md")):
            findings.extend(check_step(path, contract))
    return findings


def main(argv: list[str] | None = None) -> int:
    """Run the guidebook step lint and return its documented exit status."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--contract", type=Path, default=REPO_ROOT / "guides" / "AGENTS.md")
    parser.add_argument("guidebooks", nargs="+", type=Path)
    args = parser.parse_args(argv)
    missing = [str(path) for path in args.guidebooks if not path.is_dir()]
    if missing:
        parser.error(f"guidebook directory does not exist: {', '.join(missing)}")
    try:
        contract = parse_contract(args.contract)
        findings = lint(args.guidebooks, contract)
    except (OSError, ValueError) as error:
        print(f"lint-guidebook-steps: structural error: {error}", file=sys.stderr)
        return 2
    for finding in findings:
        print(finding.render(), file=sys.stderr)
    if findings:
        return 1
    print(f"lint-guidebook-steps: OK ({len(args.guidebooks)} guidebook director{'y' if len(args.guidebooks) == 1 else 'ies'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
