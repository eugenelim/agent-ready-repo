#!/usr/bin/env python3
"""One-shot: copy a frozen canonical-contract corpus into the pack's fixtures.

Run ONCE, against the pre-change tree, before T1a moves anything. Not shipped and
not re-run: from here the fixture IS the independent expectation.

Selection is driven by `canonical_contract`'s own comments, which name the shapes
that historically broke it. Three are near-unique in this repository (one
odd-fence file, two bold-lead-in specs, four checkbox-bearing plans), so a random
sample would miss them; two more (a lowercase-`c` heading, CRLF endings) do not
exist in the tree at all and are hand-authored here.
"""
from __future__ import annotations

import pathlib
import shutil
import sys

REPO = pathlib.Path(__file__).resolve().parents[4]
SRC = REPO / "docs" / "specs"
DEST = REPO / "packs" / "core" / "tests" / "skills" / "work-loop" / "fixtures" / "corpus"

# (slug, why it is in the corpus) — ordered; index becomes the NNN- prefix.
PICKS = [
    ("m2-frame-situation", "odd fence count (the only one in the tree)"),
    ("self-host-sweep-respects-state", "bold `**Acceptance Criteria**` lead-in, not a heading"),
    ("skills-rendering-directives", "second bold lead-in"),
    ("agentbundle-first-value-handoff", "plan carries progress checkboxes"),
    ("catalogue-wave1-contract-convergence", "plan carries progress checkboxes"),
    ("kiro-ide-hook", "plan carries progress checkboxes"),
    ("queue-add", "plan carries progress checkboxes"),
    ("adapter-support-accuracy", "multiline HTML comment in the preamble"),
    ("agentbundle-statelock-hardening", "multiline comment + lock-adjacent scope"),
    ("binder-publishing-gate-propagation", "multiline comment"),
    ("loop-cohort-state-lock", "the spec that introduced the state lock"),
    ("core-path-confinement", "path-confinement scope, many code refs"),
    ("adopter-clean-enforcement-gate", "checked ACs throughout"),
    ("build-check-single-verify", "short spec, all ACs checked"),
    ("agentbundle-wheel-release", "ordinary shipped spec"),
    ("bandit-nosec-form-lint", "ordinary shipped spec"),
    ("capture-evidence-repo-dot-segments", "the dot-segment precedent this spec cites"),
    ("nonjson-guard-all-read-paths", "guard-shaped spec"),
    ("local-scope-install-guards", "guard-shaped spec"),
    ("adopter-grounding-surface", "ordinary spec + plan"),
    ("apm-install-route-parity", "ordinary spec + plan"),
    ("architect-design-reviewer", "ordinary spec + plan"),
    ("author-brief-docs", "multiline comment"),
    ("agentbundle-engine-stragglers", "multiline comment"),
]

SYNTH_LOWERCASE = """# Spec: synthetic lowercase acceptance heading

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->

Hand-authored fixture. `canonical_contract`'s `_AC_HEADING_RE` is deliberately
case-insensitive because `lint-spec-status.py` matches `Acceptance Criteria`
exactly, so its own AC extraction returns nothing for a spec spelled with a
lowercase `c`. Inheriting that bug would break normalization for exactly those
specs. No spec in the live tree spells it this way, so the case cannot be
captured — only authored.

## Objective

Pin the lowercase-heading normalization path.

## acceptance criteria

- [x] The checked box above this line is normalized (bookkeeping).
- [ ] The unchecked box is normalized too.

## Boundaries

### Never do

- [ ] This checkbox sits OUTSIDE the AC section and must NOT be normalized —
      it is a `Never do` item, which is the scope the pin exists to protect.
"""

SYNTH_CRLF = (
    "# Spec: synthetic CRLF line endings\r\n"
    "\r\n"
    "- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped -->\r\n"
    "\r\n"
    "Hand-authored. `canonical_contract` normalizes CRLF and CR to LF as its first\r\n"
    "step; no file in the live tree uses CRLF, so this path is otherwise untested.\r\n"
    "\r\n"
    "## Acceptance Criteria\r\n"
    "\r\n"
    "- [x] CRLF is folded before hashing.\r\n"
    "- [ ] Trailing whitespace is stripped per line.   \r\n"
)

SYNTH_NO_STATUS = """# Plan: synthetic plan with no Status line

Hand-authored. `_read_md_status` returns None for a file with no `**Status:**`
line, and `_assert_status_legal` legitimately *skips* that case. Several real plan
fixtures have no status line, and AC14 turns only an unloadable parser into a
refusal — an absent token stays a skip. This fixture pins that distinction.

## T1: Do the thing

**Depends on:** none

- [ ] a progress checkbox, normalized file-wide because this is a plan
"""

SYNTH_STATUS_FREETEXT = """# Spec: synthetic status with appended free text

- **Status:** Implementing — scope now also covers the adjacent surface <!-- Draft | Approved -->

Hand-authored. Only the status *token* is spliced out; anything else on the line
stays pinned, so appending scope prose to the status line MUST move the digest.
`_STATUS_RE`'s whole group(1) span is deliberately not spliced.

## Acceptance Criteria

- [x] The token is replaced by the placeholder.
- [ ] The appended free text remains part of the digest.
"""


def main() -> int:
    if DEST.exists():
        print(f"refusing: {DEST} already exists — the corpus is frozen", file=sys.stderr)
        return 1
    DEST.mkdir(parents=True)
    n = 0
    for slug, why in PICKS:
        src = SRC / slug
        if not (src / "spec.md").is_file():
            print(f"  skip {slug} (no spec.md)", file=sys.stderr)
            continue
        n += 1
        out = DEST / f"{n:03d}-{slug}"
        out.mkdir()
        shutil.copy2(src / "spec.md", out / "spec.md")
        if (src / "plan.md").is_file():
            shutil.copy2(src / "plan.md", out / "plan.md")
        (out / "WHY").write_text(why + "\n", encoding="utf-8")
        print(f"  {out.name:52} {why}")

    for slug, spec_text, plan_text in (
        ("synthetic-lowercase-ac-heading", SYNTH_LOWERCASE, None),
        ("synthetic-crlf-endings", SYNTH_CRLF, None),
        ("synthetic-status-freetext", SYNTH_STATUS_FREETEXT, None),
        ("synthetic-plan-no-status", None, SYNTH_NO_STATUS),
    ):
        n += 1
        out = DEST / f"{n:03d}-{slug}"
        out.mkdir()
        if spec_text is not None:
            (out / "spec.md").write_text(spec_text, encoding="utf-8", newline="")
        if plan_text is not None:
            (out / "plan.md").write_text(plan_text, encoding="utf-8", newline="")
        (out / "WHY").write_text(
            "hand-authored: shape absent from the live tree\n", encoding="utf-8")
        print(f"  {out.name:52} hand-authored")

    files = sorted(p for p in DEST.glob("*/*.md"))
    print(f"\n{n} entries, {len(files)} artifacts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
