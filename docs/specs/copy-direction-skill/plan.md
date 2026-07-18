# Plan: copy-direction-skill

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Pure-markdown skill authoring, mirroring `aesthetic-direction`'s structure closely
to minimize novelty and make the discipline boundary legible by structural analogy.
The change lives under `packs/experience/.apm/skills/copy-direction/`, a one-line
edit to `packs/product-engineering/.apm/skills/voice-and-microcopy/SKILL.md`, a
`pack.toml` version bump, and two backlog entry updates.

**Cross-spec sequencing:** This plan depends on `content-design-skill` being
implemented (spec:content-design-skill). `copy-direction`'s hand-off step
references the `content-design` artifact; the pack.toml version bump (T7) must
come after both `content-design` and `copy-direction` are in the evals list. If
implementing both specs in a single PR, run `content-design-skill`'s tasks first.

The riskiest part is the SKILL.md 8-step procedure (T2): the procedure must mirror
`aesthetic-direction`'s rhythm closely enough that a user familiar with the visual
skill can orient immediately, while substituting the copy-specific interrogation
sequence. The `voice-and-microcopy` cross-reference (T6) carries the risk of
accidentally narrowing voice-and-microcopy's scope note — the note must be additive,
not restrictive.

Order of operations: scaffold (T1) → full SKILL.md authoring (T2) → references that
expand the procedure (T3) → asset template (T4) → evals (T5) → cross-reference note
(T6) → pack close-out: version bump, backlog updates, full lint (T7).

**Declined patterns:**
- Tempted to add a VoC research step to the procedure — declining per RFC-0062 OQ2:
  VoC is optional input, not produced; the skill takes the same posture as
  `aesthetic-direction` takes on persona.
- Tempted to fold copy-direction into aesthetic-direction (RFC-0062 Option B) —
  declining because that would overload a skill with a clear single visual job and
  there is no prior art for conflating visual and copy direction in one artifact.
- Tempted to write a combined plan with content-design-skill — declining because the
  RFC specifies two separate spec directories for independent tracking and review.
- Tempted to add a managed `copy-direction` → `voice-and-microcopy` trigger (a hook
  or runtime coupling) — declining per ADR-0024: no hooks, no engines; hand-off is
  a prose instruction in the procedure, not a runtime dependency.

## Constraints

- **RFC-0062** D1–D5 — `copy-direction` name (D1), `voice-and-microcopy` boundary
  via surface type (D4), SEO explicitly out of scope (D5).
- **ADR-0024** — Guardrails A and B; enforced by `tools/lint-experience-agnostic.py`.
- **RFC-0030** — `voice-and-microcopy`'s home stays in `product-engineering`;
  this spec adds a cross-reference note only, no home change.
- **RFC-0050** — experience pack design-thread; `copy-direction` artifact extends
  the discover-by-marker set alongside `content-brief`.
- **ADR-0028 / RFC-0037** — pack-activation-eval coverage shape.

## Construction tests

**Integration tests:**
- `tools/lint-experience-agnostic.py` exits 0 on `packs/experience/` after every
  new file lands.
- `grep "copy-direction" packs/product-engineering/.apm/skills/voice-and-microcopy/SKILL.md`
  returns a match after T6 completes.

**Manual verification:**
- Cold-prompt `copy-direction` with persona = "technical founders and their teams,"
  felt vibe = "direct but warm — we're the guide, not the expert." Confirm: ≥2
  named copy goals (short noun phrases), each grounded in ≥1 stable referent; a
  dominant goal named; ≥1 arbitration rule recorded; no copy strings or formula
  tables produced; artifact path named.
- Confirm the procedure degrades gracefully when no `content-design` output is
  present: elicits persona, surface type, and felt vibe inline without error.

## Tasks

### T1: Copy-direction skill directory scaffolded

**Depends on:** none

**Tests:**
- `find packs/experience/.apm/skills/copy-direction/ -type f | sort` returns
  `SKILL.md` and the four subdirectory placeholders
- `python3 tools/lint-experience-agnostic.py` exits 0

**Approach:**
- Create `packs/experience/.apm/skills/copy-direction/` with subdirectories
  `references/`, `assets/`, `evals/`
- Create `SKILL.md` stub: frontmatter `name: copy-direction`, `description:`
  placeholder; section heading stubs (When to invoke, Procedure, Anti-patterns)

**Done when:** Directory tree exists; lint exits 0 on empty stub.

---

### T2: SKILL.md fully authored (8-step procedure)

**Depends on:** T1

**Tests:**
- `python3 tools/lint-experience-agnostic.py` exits 0
- `awk '/^## Procedure/,/^## [^#]/' packs/experience/.apm/skills/copy-direction/SKILL.md | grep -c "^[0-9]\+\."` returns 8 (numbered steps scoped to Procedure section only)
- `grep "Anti-patterns" packs/experience/.apm/skills/copy-direction/SKILL.md` matches
- Manual cold-prompt confirms: ≥2 named copy goals with referents; dominant goal;
  ≥1 arbitration rule; no copy strings

**Approach:**
- `description:` — triggers on "what voice should our copy have", "write a
  copy-direction doc", "what should our headlines sound like", "how do we sound
  different from competitors", "copy vibe check"; explicitly does NOT use for UI
  microcopy states (use voice-and-microcopy), full brand identity specs (wider scope),
  or SEO content (deferred)
- **When to invoke** — four pre-conditions mirroring aesthetic-direction's gate:
  (1) real copy vibe to name, (2) no copy-direction doc already owns this surface,
  (3) naming direction not writing final copy, (4) persona or surface type known
  or elicitable
- **Procedure** — 8 steps:
  1. **Map the audience** — name each distinct reader type, write one copy JTBD
     sentence per type ("When {situation}, I want to {action}, so that {goal}"),
     rank them; load `references/copy-jtbd.md`
  2. **Run the interrogation** — felt vibe → named copy goals (short noun phrases:
     "direct," "warm-but-not-cute," "earned authority"); sharpen each against its
     opposite; load `references/interrogation-sequence.md`
  3. **Ground each goal** — take VoC findings as optional input: if provided, cite
     the audience's own language; if absent, elicit inline ("what words does your
     audience use when describing this problem?") and flag the resulting goals as
     "directional — not backed by VoC research." For each named goal, cite ≥1 stable
     referent: persona language, copy precedents (named examples — Stripe, Linear —
     as grounding; not as templates), persuasion standards (painkiller-first framing,
     tweet test, five-second evaluator scan); load `references/copy-grounding.md`
  4. **Rank the goals** — order so ties break; name the dominant goal
  5. **Record arbitration** — for each likely conflict (urgency vs. warmth;
     brevity vs. completeness), name which goal wins and why; load
     `references/copy-arbitration.md`
  6. **Capture the doc** — copy `assets/copy-direction-template.md` to
     `docs/design/copy/<slug>.md`; fill: reader map, named goals with referents,
     what each means and what would violate it, dominant goal, arbitration rules,
     open questions
  7. **Hold the plain-language floor** — verify direction against: no jargon the
     reader didn't bring, no idioms that don't translate, no assumptions about
     who the reader is
  8. **Hand off** — reference `voice-and-microcopy` for per-surface UI copy;
     reference `content-design` output as upstream context; note OQ1 scope
     extension for experience-reviewer deferred
- **Anti-patterns**: refuse naming goals without grounding them in a referent;
  refuse unranked goals; refuse reprinting copy precedents as templates; refuse
  producing SEO content or advertising copy briefs; refuse re-deriving copy
  direction mid-build (amend the doc deliberately, don't drift)

**Done when:** Manual cold-prompt produces output matching spec ACs; lint clean.

---

### T3: References directory authored

**Depends on:** T2

**Tests:**
- `ls packs/experience/.apm/skills/copy-direction/references/` shows ≥5 files
  (copy-jtbd.md, interrogation-sequence.md, copy-grounding.md, copy-arbitration.md,
  plain-language-floor.md)
- Each file cited in SKILL.md procedure exists; no dangling references
- `python3 tools/lint-experience-agnostic.py` exits 0

**Approach:**
- `references/copy-jtbd.md` — the copy JTBD sentence template and reader-type
  ranking method, mirroring `references/audience-jtbd.md` in aesthetic-direction;
  explains the difference between a copy JTBD (a "hire-this-copy-for" progress
  statement) and a generic persona description
- `references/plain-language-floor.md` — names the governing standards: GOV.UK
  Content Design plain-language guidance and the US Federal Plain Language
  Guidelines; defines the three step-7 checks (no jargon the reader didn't bring,
  no idioms that don't translate, no reader-identity assumptions); never reprints
  the standard text verbatim (ADR-0024 Guardrail A)
- `references/interrogation-sequence.md` — the interrogation question sequence for
  copy voice: what three words would describe this brand's copy? What would the
  corporate-bad version sound like? What does it feel like reading the headline in
  3 seconds? What would the over-friendly version get wrong?
- `references/copy-grounding.md` — the three referent types: (1) persona language
  (vocabulary the audience actually uses — mined from support tickets, sales calls,
  community posts); (2) copy precedents (named examples as quality anchors —
  Stripe "The new standard in online payments," Linear "The issue tracker you'll
  enjoy using"; named, not reprinted as formulas); (3) persuasion standards
  (painkiller-first framing, tweet test, five-second evaluator scan — each defined
  functionally, not as a reprint of the original framework)
- `references/copy-arbitration.md` — the common conflict types and arbitration
  structure: urgency vs. warmth, brevity vs. completeness, authority vs.
  approachability, specificity vs. universality; the dominant-goal arbitration rule;
  how to record a new conflict type

**Done when:** All referenced files exist; lint clean across all new files.

---

### T4: Copy-direction asset template authored

**Depends on:** T3

**Tests:**
- `ls packs/experience/.apm/skills/copy-direction/assets/` shows
  `copy-direction-template.md`
- `grep "type: copy-direction" packs/experience/.apm/skills/copy-direction/assets/copy-direction-template.md`
  matches
- `python3 tools/lint-experience-agnostic.py` exits 0

**Approach:**
- Mirror `aesthetic-direction-template.md` structure
- Frontmatter: `type: copy-direction`, `surface:`, `persona:`, `date:`
- Sections: Reader Map (table: reader type | JTBD sentence | rank), Named Copy
  Goals (table: goal | what it means | what would violate it | referent(s)), Dominant
  Goal, Copy Arbitration Rules (table: conflict | winner | reason), Plain-Language
  Floor Notes, Open Questions
- Placeholder text in square brackets `[…]`; no pre-written copy strings

**Done when:** Template exists with correct frontmatter; lint clean.

---

### T5: Evals authored; copy-direction added to pack.toml

**Depends on:** T2

**Tests:**
- `cat packs/experience/pack.toml | grep "copy-direction"` returns a match in
  `[pack.evals] skills`
- `ls packs/experience/.apm/skills/copy-direction/evals/` shows `eval_queries.json`
  and `evals.json`
- `python3 tools/lint-experience-agnostic.py` exits 0

**Approach:**
- `eval_queries.json`: trigger phrases — "what voice should our copy have", "write
  a copy direction doc", "how do we sound different from our competitors",
  "what should our hero headline feel like", "copy vibe check"
- `evals.json`: Tier-4 LLM-judge rubric; rubric checks: ≥2 named copy goals
  present as short noun phrases, each with ≥1 referent; dominant goal named;
  ≥1 arbitration rule recorded; no copy strings or formula tables produced
- Add `"copy-direction"` to `[pack.evals] skills` in `packs/experience/pack.toml`
  (do NOT bump version yet — version bump is T7, after both skills are in the list)

**Done when:** Lint clean; grep confirms pack.toml updated; both eval files present.

---

### T6: voice-and-microcopy cross-reference scope note added

**Depends on:** T2 (scope boundary language finalized in SKILL.md step 8)

**Tests:**
- `grep -c "copy-direction" packs/product-engineering/.apm/skills/voice-and-microcopy/SKILL.md`
  returns ≥1
- The note does not remove or qualify any existing voice-and-microcopy procedure
  text — additive only
- `python3 tools/lint-experience-agnostic.py` exits 0 (the experience lint doesn't
  scan product-engineering, but confirm the note itself contains no stack tokens)

**Approach:**
- Locate the preamble or "When to invoke" section in
  `packs/product-engineering/.apm/skills/voice-and-microcopy/SKILL.md`
- Add cross-reference scope note: "For marketing/acquisition copy voice and positioned
  copy (hero headlines, above-fold narrative, taglines) use the `experience` pack's
  `copy-direction` skill; `voice-and-microcopy` covers product UI copy states (error,
  empty state, button labels, form labels) — surface type is the boundary. **Onboarding
  tri-point:** onboarding narrative arc + structure → `content-design`; onboarding
  copy voice and register → `copy-direction`; onboarding UI-state strings
  (loading, error, empty) → `voice-and-microcopy`."
- Add as a blockquote or note callout consistent with the existing SKILL.md's style;
  do not edit existing procedure steps

**Done when:** Grep confirms note present; voice-and-microcopy procedure is unchanged
in behavior.

---

### T7: Pack version bumped to 0.5.0; backlog updated; full lint clean

**Depends on:** T1–T6, spec:content-design-skill/T5

**Tests:**
- `cat packs/experience/pack.toml | grep "^version"` returns `0.5.0`
- `grep '"version"' packs/experience/.claude-plugin/plugin.json` returns `0.5.0`
- `python3 tools/lint-experience-agnostic.py` exits 0 on the full `packs/experience/`
  tree (both new skills included)
- `grep "RFC-0062" docs/backlog.md` returns matches under both
  `copy-direction-skill-rfc` and `content-strategy-and-marketing-copy-lens` headings
- `grep "experience-reviewer-content-brief-scope" docs/backlog.md` returns a match

**Approach:**
- Bump `version` in `packs/experience/pack.toml` from `0.4.2` to `0.5.0`
- Bump `version` in `packs/experience/.claude-plugin/plugin.json` from `0.4.2` to
  `0.5.0` (both files must match; bumping only pack.toml drifts the plugin manifest)
- Run `make build-self` to re-aggregate `marketplace.json` with the updated version
- In `docs/backlog.md` under `### copy-direction-skill-rfc`: add "**In-progress:**
  RFC-0062 opened 2026-07-18. Implementing as `copy-direction` skill in the
  `experience` pack."
- In `docs/backlog.md` under `### content-strategy-and-marketing-copy-lens`:
  add "**In-progress (structural direction half):** RFC-0062 opened 2026-07-18.
  `content-design` skill implements the content-first / narrative-arc thread;
  SEO remains deferred per D5."
- In `docs/backlog.md` add `### experience-reviewer-content-brief-scope` entry:
  "**Deferred (RFC-0062 OQ1):** Extend `experience-reviewer`'s scope to include
  content briefs (`type: content-brief`) as a reviewable artifact type. The current
  skill produces the artifact; the reviewer's scope extension is a follow-on RFC.
  Decide-by: spec authoring for `content-design` skill. Owner: eugenelim."
- Run `python3 tools/lint-experience-agnostic.py` and verify clean exit on full tree

**Done when:** Version is 0.5.0; lint exits 0 on full tree; both backlog entries
reference RFC-0062.

## Rollout

Pure-markdown skill addition + a one-line informational edit to
`voice-and-microcopy`. No infrastructure, no data migration, no deployment
sequencing. Ships as a normal PR to main alongside the `content-design-skill`
implementation. Reversible: if `copy-direction`'s procedure violates ADR-0024
post-merge, the lint catches it in CI and a follow-up PR removes the violation;
the `voice-and-microcopy` scope note can be removed in the same PR.

## Risks

- **Procedure drifts from aesthetic-direction's rhythm** — making the two skills
  feel like different design disciplines rather than parallel methods. Mitigation:
  the 8-step structure is authoritative; step names are locked to the spec ACs;
  the manual cold-prompt gate checks structural symmetry before T2 is declared done.
- **voice-and-microcopy cross-reference note restricts rather than redirects** —
  accidentally narrowing voice-and-microcopy's scope. Mitigation: T6 test explicitly
  checks that no existing procedure text is removed or qualified; the note is additive.
- **Version bump ahead of content-design-skill** — pack ships at 0.5.0 with only
  one of the two skills. Mitigation: T7 has an explicit cross-spec dependency on
  spec:content-design-skill/T5; the bump cannot run until both evals entries are
  present.

## Changelog

- 2026-07-18: initial plan
