# Spec: design-critique-marketing-clarity

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0042 (agent additions keyed to loop/work-type); backlog item `design-critique-marketing-clarity-criterion`
- **Brief:** none
- **Contract:** none
- **Shape:** n/a — methodology/prose change (`design-critique` SKILL.md edit); no application LLD

`Mode: full (governance + public-interface change — shipped skill method change with frontmatter description update)`

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Agents running `design-critique` on a marketing page or landing page get a
**marketing clarity pass** that the current skill omits. Today the skill walks
Nielsen's 10 usability heuristics and checks the quality floor — both are
usability lenses, not copy/conversion lenses. A reviewer applying the skill to
the Ottawa site's homepage would not flag "hero subtitle describes features not
outcomes" or "zero social proof above the fold" because those are not usability
failures. The three missing criteria are the tweet test, the five-second scan,
and painkiller-first structure. Success is: (P1) a new mode 3 (marketing clarity
pass) is added to the skill, running when the artifact includes above-fold
marketing copy; (P2) the frontmatter description is updated to include
copy/marketing trigger phrases; (P3) the four modes are clearly ordered and the
source mode label on findings distinguishes `marketing` from `floor` / `heuristic`
/ `taste`; (P4) severity guidance applies to marketing clarity findings using the
existing 0–4 rubric.

## Boundaries

### Always do
- Edit the **source** `packs/experience/.apm/skills/design-critique/SKILL.md`.
  Run `make build-self` after to regenerate projections.
- Keep the three existing passes intact (quality-floor, heuristics, taste) —
  marketing clarity is an additive fourth mode.
- Marketing clarity runs as **mode 3**, between heuristics (mode 2) and taste
  (mode 4). Renumber accordingly.
- Bump experience pack to 0.4.0: `packs/experience/pack.toml` **and**
  `packs/experience/.claude-plugin/plugin.json` (marketplace.json aggregates
  version from plugin.json, not pack.toml — both must match).
- Add a `docs/product/changelog.md` `[Unreleased]` entry.

### Ask first
- Adding a new `references/` file for marketing clarity depth — the three
  criteria fit inline in the SKILL.md; only add a reference if the criteria
  require more than a paragraph each.
- Changing when the quality-floor or heuristics passes run.

### Never do
- Touch the risk-triggers block in `packs/core/.apm/skills/work-loop/SKILL.md`.
- Create a new `marketing-critique` skill; this is a bounded amendment.
- Add normative stack-specific implementation guidance (no "use a hero section
  with H1 + subtitle" — express as design intent only).

## Acceptance Criteria

- [x] **AC1.** `design-critique` SKILL.md lists four modes, numbered 1–4:
  quality-floor, heuristic evaluation, marketing clarity, taste critique.
- [x] **AC2.** Marketing clarity mode specifies its trigger condition: runs
  "when the artifact includes above-fold marketing copy (hero, tagline, CTA
  section) with a persuasion/conversion goal" — and explicitly does NOT fire for
  internal tools, forms, settings screens, or content pages with no conversion goal.
- [x] **AC3.** Tweet test criterion: headline stands alone as a conviction
  statement (shareable without context).
- [x] **AC4.** Five-second scan criterion: above-fold answers what / who / should
  I care within 5 seconds.
- [x] **AC5.** Painkiller-first criterion: copy leads with the reader's
  problem/desired outcome, not the author's feature list.
- [x] **AC6.** Each marketing clarity finding maps to the criterion it violates
  and carries a severity (0–4) with the `marketing` source mode label. Severity
  reuses the frequency × impact × persistence rubric from `heuristics.md`, with
  "impact" meaning conversion/persuasion cost (how badly the miss hurts the
  reader's ability to determine fit and take the intended action); the SKILL.md
  states this mapping explicitly so reviewers know it is a deliberate application
  of the rubric, not a fresh opinion scale.
- [x] **AC7.** Frontmatter description includes copy/marketing trigger phrases
  (e.g., "is this copy compelling", "does this headline work", "tweet test",
  "does this page convert").
- [x] **AC8.** All existing prose references to the mode count ("three modes") and
  to taste-as-mode-3 in `SKILL.md` are updated consistently: the intro list
  (current line 10), the "always run in this order" sentence, the procedure step
  numbering (steps 5 → 6 for taste, insert 5 for marketing clarity), the
  "Mode:" source label set in the findings-output sentence, and any "all three
  modes" references. Verified by reading the amended file and confirming no
  orphaned "three" / "mode 3 = taste" reference survives.
- [x] **AC9.** The existing anti-patterns list is unchanged (no new anti-patterns
  added that would contradict the new mode).
- [x] **AC10.** `make lint-packs` passes clean.
- [x] **AC11.** `make build-self` completes without error and
  `grep '"version"' marketplace.json` returns `"0.4.0"` for the experience pack.

## Testing Strategy

Verification mode: **Visual / manual QA** — this is a prose skill document;
correctness is demonstrated by reading the amended skill and confirming it would
surface marketing clarity findings on a sample scenario.

**Scenario A (positive):** apply the amended `design-critique` skill to a landing page
whose above-fold copy reads "Agent-ready-repo: A monorepo template for multi-adapter
AI coding agents." Expected outcome: marketing clarity pass fires; tweet test finding
raised (headline describes what it is but doesn't communicate why a developer should
care — no conviction); five-second scan finding raised (reader can answer "what is
this" but not "should I care"); painkiller-first finding raised (copy leads with the
author's feature list, not the reader's pain).

**Scenario B (negative):** apply the amended skill to a settings screen with four
input fields and a Save button. Expected outcome: marketing clarity pass does NOT
fire; only quality-floor, heuristics, and (if a grounded reference exists) taste
passes run. No "marketing" source-label findings in output.

**No unit tests** — skill is pure prose; correctness is by human + reviewer judgment.

## Assumptions

1. **Verified:** The existing three modes are correct and complete for
   usability/taste review — no changes to quality-floor, heuristics, or taste passes.
2. **Decided:** Marketing clarity criteria are bounded and stable enough to inline;
   no dedicated `references/` file is added (the "Ask first" boundary commits to
   this; reversed only if criteria expand beyond a paragraph).
3. **Verified:** The experience pack has no existing "marketing" or "conversion"
   criterion in any reference file (grep confirms: no match on "tweet test" or
   "painkiller" in `packs/experience/`).
