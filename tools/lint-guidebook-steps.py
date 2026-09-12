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
    what_changes        **What changes:**
    prerequisite_cost   **What you need first:**  plus  *Skipping costs:*
    concept_resolved    **Concepts:**
    step_map            ## What you will run  then a table
    next_step           **Next:**
    go_deeper           **Go deeper:**  with a resolving link
    utterance           **You type:**  then a fenced block
    attributed_response **Agent returns:**  then a blockquote
    correction          **You push back:**  then a blockquote
    variability         **Output varies**
    decision            **You decide:**  or  **No decision gate at this step.**
    judgement_check     **Check (<kind>):**
    failure_path        **Watch out for:**
    artifact_location   **Where it lands:**  or  **Writes no artifact.**
    artifact_preview    **What it looks like:**  then a fenced excerpt

The nine per-skill obligations are declared inside a skill's own
``## Run `<skill>` `` block and nowhere else; the step-level ones appear
once on the page.

The page's ``##`` headings must be ``What you will run``, then one
``Run `<skill>` `` per skill in run order, then ``Where this leads`` — and
nothing else at that level.  That level is what the docs site builds its
in-page table of contents from, so a deeper heading publishes a page a reader
cannot navigate.

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
# One constant, so the suite builds its fixture at the level the lint reads.
# The fixture used to hardcode `#### Run`, which left nine per-skill checks
# reporting "no block declares it" and passing for the wrong reason.
RUN_HEADING_FORM = "## Run"
RUN_HEADING = re.compile(r"^" + RUN_HEADING_FORM + r" `([^`]+)`", re.M)
STEP_MAP_HEADING = "## What you will run"
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.M)


def _heading_name(text: str) -> str:
    """A heading reduced to its name, for comparison.

    Compares names, not decoration. An outline that reflowed a double space,
    or dropped a template-internal annotation like "(… — traceability)", is not
    drifting from its source; a renamed, missing or reordered heading is. So
    everything from the first parenthesis or em-dash is discarded, internal
    whitespace is collapsed, and case is ignored.
    """
    head = re.split(r"\s*[(—]", text, maxsplit=1)[0]
    return " ".join(head.split()).strip("`").casefold()


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


COMMENT = re.compile(r"^\s*<!--.*-->\s*$")


def _following_nonblank(lines: list[str], index: int) -> str | None:
    """The next line with content, skipping blanks and HTML comments.

    Comments are skipped because provenance is recorded in one — a rung comment
    sitting between a label and its blockquote must not break the structural
    rule that the blockquote follows the label.
    """
    for line in lines[index + 1 :]:
        if COMMENT.match(line):
            continue
        if line.strip():
            return line
    return None


def _rung(lines: list[str], index: int) -> str | None:
    """The provenance rung declared after an obligation's label, if any."""
    for line in lines[index + 1 :]:
        match = re.match(r"^\s*<!--\s*rung:\s*(.+?)\s*-->\s*$", line)
        if match:
            return match.group(1)
        if line.startswith("**"):
            break
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
    """The outline's declared source, from its rung comment.

    Provenance has one mechanism, not two. An earlier version looked for a
    separate `*Source:*` line and returned a deliberately unresolvable path
    when it found none — so an outline the contract permits to be *authored*
    was reported as having a broken source. The rung is now the only
    declaration: a repository-relative path is compared, `authored` is not, and
    an absent rung is its own finding under AC-0006.
    """
    rung = _rung(lines, index)
    if rung is None or rung.casefold().startswith("authored"):
        return None
    if not re.fullmatch(r"[A-Za-z0-9_./-]+\.[A-Za-z0-9]+", rung):
        # Prose, not a path — "the skill's asset template", or
        # "analytical-design SKILL.md", which names a file without locating it.
        # Only a bare path-shaped token is comparable; a rung with a space in
        # it is a description.
        return None
    resolved = step_path.resolve()
    for parent in resolved.parents:
        if parent.name == "guides":
            return (parent.parent / rung).resolve()
    # Outside a `guides/` tree — a fixture. Resolve beside the step itself.
    return (resolved.parent / rung).resolve()


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
        return [Finding(path, step, obligation, "no `## Run `<skill>` block declares it")]
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
        # `artifact_preview`'s "Writes no artifact." Those declare that the
        # obligation does not apply here, so the primary form's semantic check
        # must not then demand a path or an outline from them.
        # An explicit alternative declares that the obligation does not apply
        # here — `decision`'s "No decision gate at this step.", and
        # `artifact_location`/`artifact_preview`'s "Writes no artifact." The
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
        elif primary.startswith("**You push back:") and not (_following_nonblank(lines, index) or "").startswith(">"):
            # A step showing only a clean response teaches a reader to accept
            # the first draft. The correction turn is quoted like any other.
            findings.append(Finding(path, step, obligation, "must be followed by the corrected exchange as a blockquote"))
        elif primary.startswith("**Go deeper:") and not re.search(r"\]\([^)]+\)", line):
            # A backticked repository path was accepted before, which let a
            # reader-facing step close by naming a file only a maintainer can
            # open. Depth has to be reachable from the page.
            findings.append(Finding(path, step, obligation, "must carry a resolving link a reader can follow"))
        elif primary.startswith("**Check ("):
            match = re.match(r"^\*\*Check \(([^)]+)\):\*\*", line)
            if match is None:
                findings.append(Finding(path, step, obligation, "declares no judgement kind"))
            elif match.group(1) not in contract.judgement_kinds:
                findings.append(Finding(path, step, obligation, f"kind `{match.group(1)}` is not in the closed set"))
        elif primary.startswith("**Where it lands:") and not re.search(r"`[^`]+`", line):
            findings.append(Finding(path, step, obligation, "must name a backticked artifact path"))
        elif primary.startswith("**What it looks like:"):
            excerpt = _fenced_block(lines, index)
            source = _source_path(lines, index, path)
            if excerpt is None:
                findings.append(Finding(path, step, obligation, "shows no fenced excerpt of the artifact"))
            elif source is not None:
                if not source.is_file():
                    findings.append(Finding(path, step, obligation, "declared preview source does not resolve"))
                elif not _appears_verbatim_in(excerpt, source.read_text(encoding="utf-8")):
                    findings.append(Finding(path, step, obligation, "excerpt does not appear verbatim in its declared source"))
        elif primary.startswith("**Concepts:"):
            detail = _check_concepts(lines, index, path)
            if detail:
                findings.append(Finding(path, step, obligation, detail))
        elif primary.startswith("**Next:") and not re.search(r"\]\([^)]+\)", line):
            # A cold reader could not act on "continue with the build workflow".
            findings.append(Finding(path, step, obligation, "must carry a resolving link, not a prose promise"))
        elif primary.startswith("**You type:") and not (_following_nonblank(lines, index) or "").startswith("```"):
            # The site attaches its copy button to fenced blocks only, so an
            # inline utterance is the one value a reader must retype by hand.
            findings.append(Finding(path, step, obligation, "must be followed by a fenced block a reader can copy"))
        elif primary.startswith(STEP_MAP_HEADING):
            detail = _check_step_map(body)
            if detail:
                findings.append(Finding(path, step, obligation, detail))
    return findings


def _check_step_map(body: str) -> str | None:
    """The overview table must name every skill the step runs, and only those.

    Checked both ways on purpose. A row with no block sends a reader looking for
    a skill the step never explains; a block with no row leaves that skill with
    no statement of whether it is needed, which is the whole reason the table
    exists.
    """
    headings = {name for name, _ in _skill_blocks(body)}
    section = body.split(STEP_MAP_HEADING, 1)[1].split("\n## ", 1)[0]
    rows = {
        match.group(1)
        for line in section.splitlines()
        if line.startswith("|") and (match := re.match(r"^\|\s*`([a-z0-9-]+)`\s*\|", line))
    }
    if not rows:
        return "table names no skill"
    if missing := headings - rows:
        return f"table omits {', '.join('`' + name + '`' for name in sorted(missing))}"
    if extra := rows - headings:
        return f"table names {', '.join('`' + name + '`' for name in sorted(extra))} with no block"
    return None



def _outside_fences(body: str) -> str:
    """The body with fenced blocks blanked out, line count preserved.

    A preview of an artifact is fenced Markdown, and that artifact has its own
    headings. Reading them as page structure made every previewed `##` a
    skeleton finding -- the check was right to fire and wrong about where it
    was looking.
    """
    lines, inside, kept = body.splitlines(), False, []
    for line in lines:
        if line.lstrip().startswith("```"):
            inside = not inside
            kept.append("")
            continue
        kept.append("" if inside else line)
    return "\n".join(kept)


SKELETON_TAIL = "## Where this leads"


def check_page_skeleton(path: Path, step: str, body: str) -> list[Finding]:
    """The `##` headings must be the declared skeleton, in order.

    The level is what makes the in-page table of contents work, so a step that
    drifts back to a deeper level publishes a page a reader cannot navigate.
    """
    headings = re.findall(r"^## (.+?)\s*$", _outside_fences(body), re.M)
    if not headings:
        return [Finding(path, step, "skeleton", "carries no `##` heading, so the page has no in-page navigation")]
    expected_first, expected_last = STEP_MAP_HEADING[3:], SKELETON_TAIL[3:]
    findings: list[Finding] = []
    if headings[0] != expected_first:
        findings.append(Finding(path, step, "skeleton", f"first `##` is `{headings[0]}`, not `{expected_first}`"))
    if headings[-1] != expected_last:
        findings.append(Finding(path, step, "skeleton", f"last `##` is `{headings[-1]}`, not `{expected_last}`"))
    for name in headings[1:-1]:
        if not name.startswith("Run `"):
            findings.append(Finding(path, step, "skeleton", f"`{name}` is not a `Run` block and may not be a `##`"))
    # A trailing heading with nothing under it is worse than no heading: it
    # publishes a table-of-contents entry that leads a reader to an empty page
    # section. The onward pointers are what the section is for.
    if SKELETON_TAIL in body and "**Next:**" not in body.split(SKELETON_TAIL, 1)[1]:
        findings.append(Finding(path, step, "skeleton", f"`{expected_last}` carries no onward pointer"))
    return findings


def _fenced_block(lines: list[str], index: int) -> list[str] | None:
    """The lines inside the first fenced block after a label, or None."""
    opened = None
    for position in range(index + 1, len(lines)):
        line = lines[position]
        if opened is None:
            if line.startswith("```"):
                opened = position
            elif line.strip() and not COMMENT.match(line):
                return None
        elif line.startswith("```"):
            return lines[opened + 1 : position]
    return None


def _appears_verbatim_in(excerpt: list[str], source: str) -> bool:
    """True when the excerpt is a contiguous verbatim run of the source's lines.

    Contiguous rather than a prefix, because a template does not always *be* the
    artifact -- the screen brief opens with a page of rationale and carries the
    artifact in a nested block partway down, and a prefix rule would have shown
    a reader the rationale instead of the thing. Contiguity still catches every
    rename, reorder and reword inside the excerpted region, which is the drift
    the check exists for. Trailing whitespace is ignored: an editor strips it
    and that is not drift.
    """
    if not excerpt:
        return False
    actual = [line.rstrip() for line in source.splitlines()]
    wanted = [line.rstrip() for line in excerpt]
    return any(
        actual[start : start + len(wanted)] == wanted
        for start in range(len(actual) - len(wanted) + 1)
    )


PROVENANCE = re.compile(r"\*\(\s*Rung:", re.I)
PLACEHOLDER = re.compile(r"\[/[A-Za-z][A-Za-z-]*\]|\{\{[^}]*\}\}")


def _pack_skills(step_path: Path) -> set[str]:
    """The published skills of the pack that owns this guide page.

    Derived from the path — `guides/<pack>/...` — so a step cannot name a
    runnable from another pack, or one that does not exist at all. Returns an
    empty set when the pack ships no skills directory, which makes the runnable
    check inert rather than wrong for a guide outside a pack.
    """
    parts = step_path.resolve().parts
    if "guides" not in parts:
        return set()
    pack = parts[parts.index("guides") + 1]
    root = Path(*parts[: parts.index("guides")]) / "packs" / pack / ".apm" / "skills"
    if not root.is_dir():
        return set()
    return {child.name for child in root.iterdir() if (child / "SKILL.md").is_file()}


def check_page(path: Path, step: str, body: str, contract: Contract) -> list[Finding]:
    """Whole-page rules that belong to no single obligation.

    Each of these was found by a first-time reader of a real guidebook, and
    each is decidable, which is why it is gated here rather than argued over.
    """
    findings: list[Finding] = []
    if PROVENANCE.search(body):
        findings.append(Finding(path, step, "provenance", "records a rung in visible prose; use an HTML comment"))
    for bad in PLACEHOLDER.findall(body):
        findings.append(Finding(path, step, "placeholder", f"`{bad}` is not the declared `<segment>` form"))
    return findings


def check_named_runnables(path: Path, step: str, body: str, skills: set[str]) -> list[Finding]:
    """Every runnable a step names must be a published skill of its pack.

    Inert when the skill set is empty — a guide outside a pack, or a fixture.
    An earlier version reported every named runnable as unpublished in that
    case, which is a check being wrong rather than absent.
    """
    if not skills:
        return []
    findings: list[Finding] = []
    for name in sorted(set(re.findall(r"^" + RUN_HEADING_FORM + r" `([a-z0-9-]+)`", body, re.M))):
        if name not in skills:
            findings.append(Finding(path, step, "runnable", f"`{name}` is not a published skill of this pack"))
    for name in sorted(set(re.findall(r"[Rr]un `([a-z0-9-]+)`", body))):
        if name not in skills and not re.search(r"^" + RUN_HEADING_FORM + r" `" + re.escape(name), body, re.M):
            findings.append(Finding(path, step, "runnable", f"`{name}` is presented as a run but is not a published skill"))
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
    findings.extend(check_page(path, step, body, contract))
    findings.extend(check_page_skeleton(path, step, body))
    findings.extend(check_named_runnables(path, step, body, _pack_skills(path)))
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
