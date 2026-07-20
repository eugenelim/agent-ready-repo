# Plan: spec-D-pack-workflow-guide

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Three documentation writes: (1) the new explanation guide, (2) the CONTRIBUTING.md step 0 addition, and (3) confirming the author-a-skill.md intro link (which is Spec A's AC8 — verify Spec A has not already shipped this change before T3 runs). All three are independent — they can be done in any order and landed in one PR.

The riskiest part is the guide itself: it must be written at archetype level (no individual skill name enumeration beyond examples), use the session-arc vocabulary consistently, and cover all five arc-design decisions without becoming a catalogue reference page. The ADR-0054 archetypes and verb taxonomy are the normative source for sections 2, 3, and 7.

CONTRIBUTING.md step numbering: the existing steps must be renumbered (current "step 1" becomes "step 2", etc.) if the file uses numbered steps — or the step 0 is inserted as "Step 0:" if the file uses headers. Verify the file's numbering scheme before editing.

## Constraints

- RFC-0067 §D1: seven sections normative; section content described per RFC.
- RFC-0067 §D2: step 0 paragraph verbatim (or equivalent); step 1 amendment sentence.
- ADR-0054: four-type classification and verb taxonomy are normative content for sections 2 and 3.
- No governance citations in the guide body: adopter-surface convention.
- Spec A owns AC7 (`## Naming your skill`) and AC8 (intro link) in `author-a-skill.md`. This spec does not touch those; it authors the guide that the intro link points to.

## Construction tests

**Integration tests:** none.

**Manual QA (cross-cutting, runs at T4):** A hypothetical new pack — e.g., a `ticketing` pack that manages issues across sessions — can be classified through the decision tree (Step 1), arc-mapped (Step 2), named (Step 3), and registered (Step 5) using only the guide. No reviewer consultation needed.

## Tasks

### T1: Author `pack-workflow-design.md`

**Depends on:** none
**Touches:** docs/guides/_shared/explanation/pack-workflow-design.md

**Tests:**
- Goal-based (AC1): file exists at the specified path.
- Goal-based (AC2): all seven sections present with correct headings.
- Goal-based (AC3): decision tree in section 2 leads to one of the four ADR-0054 types.
- Goal-based (AC4): section 3 walks all five arc stages with guiding questions.
- Goal-based (AC5): section 4 references verb taxonomy + banned labels; cross-links to author-a-skill.md.
- Goal-based (AC6): section 5 covers single `output_dir` + subdirectories + cites journey-mapping.
- Goal-based (AC7): section 6 covers `shaping_queue` type + routing + fallback.
- Goal-based (AC8): section 7 has three worked archetypes (Episodic — product-strategy; Sustained-project — desk-research; Sustained-derived — experience-design) plus a stateless reserved-category note (no current catalogue member); no pack incorrectly labelled as stateless.
- Goal-based (AC11): no RFC/ADR/spec citations in the guide body.

**Approach:**

Author the guide with the following structure:

```
# Pack workflow design

## What a pack is
[One paragraph on cohesive skill set for a role's work. Session-arc vocabulary:
Arrive → Orient → Work → Persist → Collaborate.]

## Step 1 — Characterize your workflow type
[Decision tree: Does the pack create durable files? → Does it own those files
or derive from them? → Is work episodic or ongoing? → Which of four types?]

| Type | Description |
| episodic | ... |
| sustained-project | ... |
| sustained-derived | ... |
| stateless | ... |

## Step 2 — Map the arc for your pack
[For each arc stage, guiding questions:
- Arrive: how does a user start a session with this pack?
- Orient: does this pack need a *-status skill?
- Work: which skills drive the core workflow?
- Persist: does this pack accumulate a project directory across sessions? Where?
- Collaborate: how do artifacts from this pack feed other packs?]

## Step 3 — Name your skills
[Reference to verb taxonomy; banned labels; description-driven activation;
cross-link to author-a-skill.md for the full table.]

## Step 4 — Decide your vault-path shape
[If your pack maintains a persistent project directory across sessions: single output_dir base per pack (configured via
agentbundle-layout.toml). Skill-specific subdirectories under the base.
Canonical example: journey-mapping writes to <output_dir>/journeys/.]

## Step 5 — Register with workspace-status
[shaping_queue type for your pack's shaping items. Routing contract:
workspace-status routes {type = "<your-type>"} to your pack's *-status skill.
Fallback if pack not installed.]

## Reference: worked archetypes
[Three real examples per ADR-0054:
1. Episodic — product-strategy: each skill invocation standalone; no status skill needed.
   (converters and architect also Episodic — noted as additional examples.)
2. Sustained-project — desk-research: project-start → check → digest → synthesize; status skill reads overview.md.
3. Sustained-derived — experience-design: reads journeys/screens/blueprints; experience-status.
Stateless: reserved category per ADR-0054; no current catalogue pack fits — guide notes it exists for future hypothetical packs with pure-transformation shape.]
```

**Done when:** AC1–AC8 + AC11 hold.

---

### T2: Add step 0 to `CONTRIBUTING.md`

**Depends on:** none
**Touches:** CONTRIBUTING.md

**Tests:**
- Goal-based (AC9): CONTRIBUTING.md gains step 0 before the current step 1 in the "Adding a new pack" section.
- Goal-based (AC10): step 1 (now step 2, or step 1 if the file uses a different scheme) gains the arc-mapping sentence.

**Approach:**
- Read `CONTRIBUTING.md` to find the "Adding a new pack" section and its current step structure.
- Insert step 0 before the current step 1 with the RFC-0067 §D2 paragraph content (adapted to the file's voice and formatting convention):
  > **0. Design the pack's workflow arc first.** A pack is a set of cohesive workflows for a role's work — not a list of features. Before writing any SKILL.md, work through the pack workflow design framework at `docs/guides/_shared/explanation/pack-workflow-design.md`. It takes you through: characterizing whether your pack is episodic, sustained-project, or sustained-derived; mapping the Arrive → Orient → Work → Persist → Collaborate arc to your pack's skill set; naming your skills against the verb taxonomy; and deciding whether your pack needs a status skill, a `*-project-start` skill, and config-driven output paths. The RFC reviewers will ask these questions; answering them before you write the skill bodies saves a review cycle.
- Add to the "Open an RFC" step: "The RFC should include your arc mapping from step 0 — which skills cover which arc stages, and why."
- If the file uses numbered steps, renumber existing steps (step 1 → step 2, etc.) for consistency.

**Done when:** AC9 + AC10 hold.

---

### T3: Confirm author-a-skill.md intro link exists (read-only precondition check)

**Depends on:** none
**Touches:** docs/guides/_shared/how-to/author-a-skill.md (read-only)

**Tests:**
- Coordination check: verify that Spec A has landed its AC8 (the intro link to `../explanation/pack-workflow-design.md` in `author-a-skill.md`). If Spec A is not yet shipped, this spec's PR should be sequenced after it, or Spec A and this spec ship in the same PR with Spec A owning the `author-a-skill.md` edit.

**Approach:**
- Read `docs/guides/_shared/how-to/author-a-skill.md`.
- If the intro-link sentence is present: task is complete — Spec A has delivered AC8.
- If absent: do NOT add it here — it is Spec A's AC8. Note in the PR description that Spec A must ship before or with this PR for the link to resolve.
- This spec does NOT modify `author-a-skill.md`.

**Done when:** The intro link exists (by Spec A's delivery). If Spec D ships before Spec A, the link is a dangling reference until Spec A lands — document this sequencing requirement in the PR.

---

### T4: Gates and adversarial review

**Depends on:** T1, T2, T3

**Tests:**
- Goal-based (AC12): `.claude/skills/work-loop/scripts/lint-spec-status.py --root .` exits 0; `git status` clean except intended files.

**Approach:**
- Run `.claude/skills/work-loop/scripts/lint-spec-status.py --root .` on this spec.
- Verify all ACs hold by re-reading the authored files.
- Run adversarial review; address any Blockers.

**Done when:** AC12 holds; adversarial-reviewer returns `Clean — ready to commit.`

## Design (LLD)

### Behavior & rules

**Guide tone:** second-person, imperative ("Decide", "Map", "Name"), not passive. Each step produces one concrete output (a type classification, an arc map, a skill name list, a config decision, a registration entry) so the reader can check their work.

**Decision tree (Step 1) structure:**

```
Does the pack maintain a work-in-progress thread across sessions —
tracking phases, a growing project, or cumulative state?
  No → Does each invocation produce a standalone artifact?
        Yes → Episodic
        No  → Stateless
  Yes → Does this pack create and own the project thread,
        or derive from a thread another pack owns?
         Own    → Sustained-project (creates and manages the project)
         Derive → Sustained-derived (reads and extends the project)
```

Note: an episodic pack *can* write a per-invocation artifact (e.g., a strategy document); the distinguishing question is whether it accumulates shared project state across sessions, not whether it writes any file at all.

**Arc-mapping questions (Step 2):**
- Arrive: "What does a user type to open this pack's first session?"
- Orient: "When a user returns after a break, what do they need to know? → If the answer is non-trivial, the pack needs a `*-status` skill."
- Work: "Which one or two skills are the core workflows this pack enables?"
- Persist: "Does the pack accumulate a project directory across sessions? → vault-path design if yes; episodic packs that write standalone per-invocation artifacts skip Step 4."
- Collaborate: "What does the next pack in the user's workflow consume from this one?"

## Rollout

Pure documentation write; no pack manifest changes; no projected-tree rebuild needed. Can be merged independently of Specs A, B, and C. The CONTRIBUTING.md step 0 takes effect as soon as the PR merges — any new pack RFC opened after merge should include the arc mapping.

## Risks

- CONTRIBUTING.md may not have a structured "Adding a new pack" section with numbered steps. Mitigation: T2 reads the file first and adapts the step 0 insertion to the file's existing structure.
- The guide's archetype examples reference specific pack names (product-strategy, desk-research, experience-design, converters) that may change in the future. Mitigation: the guide's archetype section labels by type name, not pack name; pack examples are illustrative ("e.g., product-strategy"), not normative.

## Changelog

- 2026-07-20: initial plan, authored alongside the spec for RFC-0067 spec/plan/ADR follow-on work.
- 2026-07-20: corrected decision tree first question from "creates durable files" to "maintains work-in-progress thread across sessions" — the original wording would misroute episodic packs that write standalone artifacts (e.g., product-strategy) to the sustained-project branch; the distinguishing criterion is cross-session accumulated project state, not file creation.
