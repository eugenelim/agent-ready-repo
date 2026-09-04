#!/usr/bin/env python3
"""Measure whether the guide corpus lets a reader act.

Scores every guide under ``guides/`` for five affordances and every pack skill
for a documented invocation phrase, then prints summary tables. Pass
``--ledger`` to also write a JSON ledger recording the line behind every hit, so
any number in a report can be traced to the line that produced it.

The five affordances:

==  ==================  ====================================================
A   chat input          a literal, copy-pasteable thing the reader types
B   demonstrated input  a worked example of what the reader supplies in
C   sample output       an illustration of what the agent emits back
D   stated outcome      an explicit end state, outside the opening framing
E   job to be done      who this is for, or when to reach for it
==  ==================  ====================================================

Detectors are keyed to this repository's measured house conventions rather than
to open-ended prose, so a verdict is reproducible:

* ``**Use this when:**`` and ``## Before you start`` carry E.
* A bare ``text`` fence holding one plain sentence is the house form for A.
* An ``Output``/``Result`` heading, or an end-state phrase below the opening
  framing, carries D. An end-state phrase *inside* the framing states the
  reader's job, not an outcome, so the first 20 lines are excluded from D.

Detection proves an affordance is *present*, never that it is good. Treat the
counts as a lower bound on quality and as near-exact on presence.

Usage::

    python3 tools/audit-guide-affordances.py [--ledger PATH] [--guides-root DIR]
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- A: a literal chat input -------------------------------------------------
RE_SLASH = re.compile(r"(?:^|[\s`(])/[a-z][a-z0-9]+-[a-z0-9-]+")
RE_TYPED_PROMPT = re.compile(r"^\s*(?:>|[-*]|\|)?\s*[\"“][A-Z][^\"”]{12,}[\"”]")
RE_TYPE_CUE = re.compile(
    r"\b(?:you (?:say|type|ask|tell)|say to|type|paste this|prompt)\b"
    r"[^.\n]{0,30}[:\-]\s*[\"“`]",
    re.IGNORECASE,
)
# A_weak: the guide names the owning skill but never shows the input.
RE_SKILL_PROSE = re.compile(
    r"\b(?:run|invoke|use|call|ask)\b[^.\n]{0,25}`([a-z][a-z0-9]+(?:-[a-z0-9]+)+)`",
    re.IGNORECASE,
)
# A prose-sentence fence is the house form for "what you type". It is a chat
# input only if it reads as a sentence, not as a command, tree, table, or config.
RE_CMDISH = re.compile(
    r"(?:^\s*[$>#]\s|^\s*(?:agentbundle|git|apm|make|python|pip|npm|cd|ls|codex)\b"
    r"|\s--[a-z]|\||=|[{}]|─|│|├|└|▶|^\s*/plugin\b)"
)

# --- B: a demonstrated workflow input ---------------------------------------
RE_B = re.compile(
    r"\b(?:you (?:answer|reply|respond|supply|fill in|paste)"
    r"|your answer"
    r"|(?:example|sample|worked) (?:answer|answers|input|inputs|response"
    r"|responses|session|transcript|walkthrough)"
    r"|for example,? you (?:might|could|would) (?:say|answer|reply|write)"
    r"|it (?:asks|prompts|elicits)[^.\n]{0,40}(?:you|and you)"
    r"|answers? (?:might|could|look) like)",
    re.IGNORECASE,
)
RE_B_QA = re.compile(r"^\s*(?:\*\*)?(?:Q|Question|Agent asks|Prompt)(?:\*\*)?\s*[:.]")
RE_B_ANS = re.compile(r"^\s*(?:\*\*)?(?:A|Answer|You(?: say| answer| reply)?)(?:\*\*)?\s*[:.]")

# --- C: a sample chat output -------------------------------------------------
RE_C = re.compile(
    r"\b(?:the (?:agent|skill|loop|command) (?:responds|replies|returns|prints"
    r"|reports|surfaces|emits|outputs|writes back)"
    r"|(?:example|sample) output"
    r"|output looks like"
    r"|responds with"
    r"|you(?:'ll| will) (?:see|get) (?:a|an|the|something)"
    r"|the (?:emitted|generated|rendered|resulting) (?:file|artifact|brief|intent"
    r"|spec|report|record))",
    re.IGNORECASE,
)
OUTPUT_LANGS = frozenset({
    "",
    "text",
    "txt",
    "output",
    "markdown",
    "md",
    "toml",
    "yaml",
    "yml",
    "json",
    "mermaid",
})
CMD_LANGS = frozenset({"bash", "sh", "shell", "zsh", "console", "python", "py"})

# --- D: a stated outcome -----------------------------------------------------
RE_D_HEAD = re.compile(
    r"^#{2,4}\s+(?:outcome|outcomes|result|results|what you (?:have|get|end up with)"
    r"|what you'll have|done|you're done|deliverable|what this (?:gives|produces)"
    # "Verify the result" states an end state; a bare "Verify", "Verify and
    # continue", or "Verify the environment" is an instruction.
    r"|what changed|verify(?:ing)? the result)\b",
    re.IGNORECASE,
)
RE_D_PHRASE = re.compile(
    r"\b(?:you now have|you(?:'ll| will) have|the result is|you end up with"
    r"|leaves you with|at (?:the end|this point),? you|when you(?:'re| are) done,? you"
    r"|by the end,? you)\b",
    re.IGNORECASE,
)
# The opening framing states the reader's job; an end-state claim there is not
# an outcome. Twenty lines covers frontmatter, title, and Use-this-when.
FRAMING_LINES = 20

# --- E: a job to be done -----------------------------------------------------
RE_E = re.compile(
    r"(?:\*\*Use this when:\*\*"
    r"|^#{2,4}\s+(?:when to use|who (?:this|it)(?:'s| is) for|use (?:this|it) when"
    r"|before you start|prerequisites|audience|when this (?:applies|fits)"
    r"|is this the right)"
    r"|\buse this when\b|\breach for (?:this|it) when\b"
    r"|\bthis (?:guide|page|how-to|tutorial|reference) is for\b"
    r"|\bread this (?:if|when)\b"
    r"|\bdo not use (?:this|it) (?:for|when)\b|\bdon't use this\b)",
    re.IGNORECASE | re.MULTILINE,
)

# --- skill invocation phrasing -----------------------------------------------
RE_DESC = re.compile(r"^description:\s*(.*?)(?=^\w[\w-]*:|^---)", re.MULTILINE | re.DOTALL)
# Paired marks only. A straight apostrophe is a contraction far more often than
# a quote delimiter: matching it turned "who's authoritative — STORM's" into a
# fake example utterance in eight skill descriptions.
RE_QUOTED = re.compile(r"(?:\"([^\"\n]{8,120})\"|“([^”\n]{8,120})”|‘([^’\n]{8,120})’)")
RE_TRIGGERS_ON = re.compile(r"\bTriggers? on\b")

AFFORDANCES = ("A", "B", "C", "D", "E")
LABELS = {
    "A": "A chat input",
    "B": "B demonstrated input",
    "C": "C sample output",
    "D": "D stated outcome",
    "E": "E job to be done",
}


class Hit(NamedTuple):
    """One piece of evidence: the line it was found on, and the text."""

    line: int
    evidence: str


class GuideRow(NamedTuple):
    """One audited guide file and its per-affordance evidence."""

    path: str
    kind: str
    pack: str
    lines: int
    hits: dict[str, list[Hit]]

    def has(self, key: str) -> bool:
        """Report whether this guide carries the affordance."""
        return bool(self.hits[key])


class SkillRow(NamedTuple):
    """One skill and whether its description documents how to invoke it."""

    pack: str
    skill: str
    published: bool
    quoted: int
    triggers_on: bool
    example: str
    line: int
    """The 1-indexed line of the `description:` field, so a count is traceable."""


def _frontmatter(lines: list[str]) -> dict[str, str]:
    """Parse the leading YAML block as flat string pairs."""
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def _is_prompt_fence(lang: str, body: list[Hit]) -> bool:
    """Report whether a fenced block is a sentence the reader is meant to type."""
    if lang.lower() not in {"", "text", "txt"}:
        return False
    texts = [hit.evidence.strip() for hit in body if hit.evidence.strip()]
    if not 1 <= len(texts) <= 4:
        return False
    if any(RE_CMDISH.search(text) for text in texts):
        return False
    joined = " ".join(texts)
    return bool(re.match(r"^[A-Z“\"']", joined)) and len(joined.split()) >= 4


def _repo_relative(path: Path) -> str:
    """Render a path relative to the repository root when it sits inside it."""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def audit_guide(path: Path) -> GuideRow:
    """Score one guide file, recording a line number for every hit."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    fields = _frontmatter(lines)
    hits: dict[str, list[Hit]] = {key: [] for key in (*AFFORDANCES, "A_weak")}

    lang: str | None = None
    fence_start = 0
    body: list[Hit] = []

    def close_fence() -> None:
        """Classify a finished fence as a chat input, a sample output, or neither."""
        if lang is None:
            return
        low = lang.lower()
        for hit in body:
            if RE_SLASH.search(hit.evidence):
                hits["A"].append(Hit(hit.line, hit.evidence.strip()[:70]))
                return
        if low in OUTPUT_LANGS and low not in CMD_LANGS:
            for hit in body:
                if RE_TYPED_PROMPT.match(hit.evidence):
                    hits["A"].append(Hit(hit.line, hit.evidence.strip()[:70]))
                    return
        if _is_prompt_fence(lang, body):
            first = next(hit for hit in body if hit.evidence.strip())
            hits["A"].append(Hit(first.line, first.evidence.strip()[:70]))
            return
        joined = "\n".join(hit.evidence for hit in body)
        if low in OUTPUT_LANGS and low not in CMD_LANGS and len(body) >= 4 and len(joined) >= 120:
            hits["C"].append(Hit(fence_start, f"```{low or '(none)'} {len(body)}-line block"))

    for number, text in enumerate(lines, start=1):
        fence = re.match(r"^\s*```+\s*([A-Za-z0-9_+-]*)", text)
        if fence:
            if lang is None:
                lang, fence_start, body = fence.group(1), number, []
            else:
                close_fence()
                lang = None
            continue
        if lang is not None:
            body.append(Hit(number, text))
            continue

        # RE_TYPED_PROMPT is deliberately NOT applied to running prose: a
        # quoted sentence there is usually an illustration ("A managed
        # relational database …" is a requirement, not something you type).
        # Inside a fence, or after an explicit type cue, it is an input.
        if RE_SLASH.search(text) or RE_TYPE_CUE.search(text):
            hits["A"].append(Hit(number, text.strip()[:70]))
        else:
            named = RE_SKILL_PROSE.search(text)
            if named:
                hits["A_weak"].append(Hit(number, named.group(1)))

        if RE_B.search(text) or RE_B_QA.match(text) or RE_B_ANS.match(text):
            hits["B"].append(Hit(number, text.strip()[:70]))
        if RE_C.search(text):
            hits["C"].append(Hit(number, text.strip()[:70]))
        if RE_D_HEAD.match(text) or (number > FRAMING_LINES and RE_D_PHRASE.search(text)):
            hits["D"].append(Hit(number, text.strip()[:70]))
        if RE_E.search(text):
            hits["E"].append(Hit(number, text.strip()[:70]))

    if lang is not None:
        close_fence()

    return GuideRow(
        path=_repo_relative(path),
        kind=fields.get("kind", "-"),
        pack=fields.get("pack", "-"),
        lines=len(lines),
        hits=hits,
    )


def audit_skill(path: Path) -> SkillRow:
    """Report whether one skill's description documents how to invoke it."""
    text = path.read_text(encoding="utf-8", errors="replace")
    match = RE_DESC.search(text)
    line = text.count("\n", 0, match.start()) + 1 if match else 0
    description = " ".join(match.group(1).split()) if match else ""
    quoted = [text for groups in RE_QUOTED.findall(description) for text in groups if text]
    pack = path.parts[-5]
    return SkillRow(
        pack=pack,
        skill=path.parts[-2],
        # An underscore-prefixed slug is a reserved authoring asset, never a
        # published route member (agentbundle/build/main.py).
        published=not pack.startswith("_"),
        quoted=len(quoted),
        triggers_on=bool(RE_TRIGGERS_ON.search(description)),
        example=quoted[0] if quoted else "",
        line=line,
    )


def _rate(count: int, total: int) -> str:
    return f"{round(100 * count / total)}%" if total else "n/a"


def report(guides: list[GuideRow], skills: list[SkillRow]) -> None:
    """Print the summary tables."""
    total = len(guides)
    print(f"guide files audited: {total}\n")
    print("| affordance | present | missing | coverage |")
    print("| --- | --: | --: | --: |")
    for key in AFFORDANCES:
        count = sum(1 for row in guides if row.has(key))
        print(f"| {LABELS[key]} | {count} | {total - count} | {_rate(count, total)} |")

    weak = sum(1 for row in guides if row.has("A_weak") and not row.has("A"))
    every = sum(1 for row in guides if all(row.has(k) for k in AFFORDANCES))
    none = sum(1 for row in guides if not any(row.has(k) for k in AFFORDANCES))
    print(f"\nnames a skill in prose but never shows the input: {weak}")
    print(f"all five affordances: {every}   none: {none}")

    print("\n### by Diataxis kind")
    by_kind: dict[str, list[GuideRow]] = defaultdict(list)
    for row in guides:
        by_kind[row.kind].append(row)
    print("| kind | files | " + " | ".join(AFFORDANCES) + " |")
    print("| --- | --: |" + " --: |" * len(AFFORDANCES))
    for kind, rows in sorted(by_kind.items(), key=lambda item: -len(item[1])):
        cells = " | ".join(str(sum(1 for r in rows if r.has(k))) for k in AFFORDANCES)
        print(f"| {kind} | {len(rows)} | {cells} |")

    published = [row for row in skills if row.published]
    quoted = sum(1 for row in published if row.quoted)
    triggers = sum(1 for row in published if row.triggers_on)
    print("\n### skill invocation phrasing (published packs only)")
    print(f"published skills: {len(published)} of {len(skills)} in the repository tree")
    print(
        f"  description carries a quoted example utterance: {quoted}"
        f" ({_rate(quoted, len(published))})"
    )
    print(f"  description says 'Triggers on': {triggers} ({_rate(triggers, len(published))})")

    print("\n### harvestable: no chat input, but the named skill already has a phrase")
    phrases = {row.skill for row in skills if row.quoted}
    harvest: list[tuple[str, str, list[str]]] = []
    for row in guides:
        if row.has("A"):
            continue
        named = sorted({hit.evidence for hit in row.hits["A_weak"]} & phrases)
        if named:
            harvest.append((row.path, row.kind, named))
    distinct = len({name for _, _, names in harvest for name in names})
    print(f"{len(harvest)} guides; {distinct} distinct skills\n")
    print("| guide | kind | harvest from |")
    print("| --- | --- | --- |")
    for path, kind, named in sorted(harvest):
        print(f"| `{path}` | {kind} | " + ", ".join(f"`{name}`" for name in named) + " |")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guides-root", default=str(REPO_ROOT / "guides"))
    parser.add_argument("--packs-root", default=str(REPO_ROOT / "packs"))
    parser.add_argument("--ledger", help="write the per-file JSON ledger here")
    args = parser.parse_args()

    guides = [
        audit_guide(path)
        for path in sorted(Path(args.guides_root).rglob("*.md"))
        if path.name != "AGENTS.md"
    ]
    skills = [
        audit_skill(path)
        for path in sorted(Path(args.packs_root).glob("*/.apm/skills/*/SKILL.md"))
    ]
    report(guides, skills)

    if args.ledger:
        ledger = [
            {
                "path": row.path,
                "kind": row.kind,
                "lines": row.lines,
                **{key: [list(hit) for hit in row.hits[key]] for key in (*AFFORDANCES, "A_weak")},
            }
            for row in guides
        ]
        Path(args.ledger).write_text(
            json.dumps({"guides": ledger, "skills": [row._asdict() for row in skills]}, indent=1),
            encoding="utf-8",
        )
        print(f"\nledger written: {args.ledger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
