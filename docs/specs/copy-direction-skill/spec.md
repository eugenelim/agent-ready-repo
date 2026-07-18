# Spec: copy-direction-skill

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0062 (D1–D5), ADR-0024 (guardrails A+B, framework-agnosticism), RFC-0050 (experience pack design-thread), RFC-0030 (voice-and-microcopy home stays in product-engineering)
- **Brief:** none
- **Contract:** none — pure-markdown skill + asset template; no API/event/RPC interface. The copy-direction doc is a markdown artifact template (skill `assets/`), not a versioned interface contract.
- **Shape:** integration — a new skill directory under `packs/experience/.apm/skills/`; a one-line cross-reference edit to `packs/product-engineering/.apm/skills/voice-and-microcopy/SKILL.md`; a pack version bump; method-authoring, not application code.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A `copy-direction` skill is added to the `experience` pack — the copy twin of
`aesthetic-direction`. Designers, copywriters, and solo builders use it to turn a
vague "copy vibe" into a small set of named, ranked copy goals grounded in stable
referents (persona language, copy precedents, persuasion standards), and to record
copy arbitration rules the rest of the build references when writing any copy for the
surface. The skill fills the second missing link in the experience pack's design
thread: it rides alongside `aesthetic-direction`, takes inputs from `content-design`
(or elicits inline), and feeds `voice-and-microcopy` when per-surface UI copy is
being written.

A scope-boundary cross-reference is added to `voice-and-microcopy` in the
product-engineering pack making the surface-type split explicit: `copy-direction` owns
marketing/acquisition copy voice and positioned copy (hero headlines, above-fold
narrative, taglines, announcement copy); `voice-and-microcopy` owns product UI copy
states (error messages, empty states, button labels, form labels). Surface type is the
boundary; both files carry the cross-reference.

Success means a designer can invoke `copy-direction` cold, answer an 8-step
interrogation sequence mirroring `aesthetic-direction`'s structure, and receive a
`copy-direction.md` doc the rest of the build references without re-litigating copy
voice. The experience pack version bumps to 0.5.0 to reflect two new public-interface
skills (this skill and `content-design` from its companion spec).

## Boundaries

### Always do

- Author `SKILL.md` + `references/` + `assets/` + `evals/` under
  `packs/experience/.apm/skills/copy-direction/`
- Mirror `aesthetic-direction`'s 8-step procedure structure applied to copy voice:
  audience map → interrogation → grounding → ranking → arbitration → capture →
  plain-language floor check → hand-off
- Keep every file pure-markdown per ADR-0024: name copy precedents and persuasion
  standards as references, never reprint them wholesale; produce named goals and
  arbitration rules, not a copy template or formula table
- Artifact path `docs/design/copy/<slug>.md` with `type: copy-direction`, resolved
  via RFC-0050 D6's three-tier layout contract; `copy-direction` extends the pack's
  discover-by-marker set
- Add `copy-direction` to `[pack.evals] skills` in `packs/experience/pack.toml`;
  ship `evals/eval_queries.json` + `evals/evals.json`
- Add a one-line cross-reference scope note to
  `packs/product-engineering/.apm/skills/voice-and-microcopy/SKILL.md` (scope note
  only — no behavior change to voice-and-microcopy)
- Bump `packs/experience/pack.toml` version from 0.4.2 → 0.5.0 when both
  `content-design` and `copy-direction` are in the evals list
- Mark `docs/backlog.md` entries `copy-direction-skill-rfc` and
  `content-strategy-and-marketing-copy-lens` as in-progress (RFC opened) with
  reference to RFC-0062
- Run `tools/lint-experience-agnostic.py` after every edit; keep it clean

### Ask first

- Any change to `voice-and-microcopy`'s procedure or behavior beyond the one-line
  cross-reference scope note
- Moving `voice-and-microcopy`'s home from `product-engineering` to `experience`
  (RFC-0030 constraint; confirmed as "Ask first" in the experience-pack spec Boundaries)
- Widening scope to include VoC research production — VoC findings are optional
  input, not produced by this skill
- Widening scope to include full brand identity documentation, advertising copy
  templates, or SEO content guidelines

### Never do

- Reprint copy precedents (Stripe, Linear, etc.) as prescriptive copy — name them
  as reference examples that ground a goal; never quote the headline and say
  "write copy like this"
- Produce a copy template, formula table, or pre-written copy strings
- Add hooks, engines, validators, or in-pack linters
- Edit `voice-and-microcopy`'s existing procedure steps — scope note only

## Testing Strategy

All verification is goal-based or manual QA — there is no testable runtime logic.

- **Goal-based:** `tools/lint-experience-agnostic.py` exits 0 on `packs/experience/`
  after the skill lands.
- **Goal-based:** `grep "copy-direction" packs/product-engineering/.apm/skills/voice-and-microcopy/SKILL.md`
  returns a match (cross-reference note present).
- **Goal-based:** `grep "not backed by VoC research" packs/experience/.apm/skills/copy-direction/SKILL.md`
  returns a match confirming the VoC-absent flag phrase is present in the procedure.
- **Goal-based:** `cat packs/experience/pack.toml | grep -E "^version|copy-direction"` confirms
  version 0.5.0 and `copy-direction` in the evals list.
- **Goal-based:** `grep -c "copy-direction-skill-rfc\|content-strategy-and-marketing-copy-lens" docs/backlog.md`
  combined with `grep "RFC-0062" docs/backlog.md` confirms both backlog entries reference RFC-0062.
- **Manual QA:** Cold-prompt `copy-direction` with persona = "technical founders and
  their teams" and felt copy vibe = "direct but warm — we're the guide, not the
  expert." Confirm output names ≥2 copy goals as short noun phrases, grounds each in
  ≥1 stable referent (persona language, a copy precedent, or a persuasion standard),
  records a dominant goal, and states ≥1 arbitration rule. Confirm no copy strings
  or formula tables are produced.

## Acceptance Criteria

- [x] `packs/experience/.apm/skills/copy-direction/SKILL.md` exists; frontmatter
  includes `name: copy-direction`; Procedure section has exactly 8 numbered steps
  (verified by counting within `## Procedure` only, not the full file); the step
  structure mirrors `aesthetic-direction`'s audience-map → interrogation → grounding
  → ranking → arbitration → capture → floor-check → hand-off; Anti-patterns section
  present.
- [x] Step 1 (audience map): maps each distinct reader type with a copy JTBD sentence
  and ranks them; feeds the ranked map into Step 2.
- [x] Step 2 (interrogation): converts felt vibe to named copy goals (short noun
  phrases); sharpens each against its opposite.
- [x] Step 3 (grounding): grounds each goal in ≥1 stable referent from: persona
  language (words the audience actually uses), copy precedents (cited as named
  examples, not reprinted), persuasion standards (painkiller-first framing, tweet
  test, five-second evaluator scan for above-fold copy).
- [x] Step 4 (ranking): orders goals so a tie can break; names the dominant goal.
- [x] Step 5 (arbitration): records which goal wins each named conflict type
  (urgency vs. warmth; brevity vs. completeness).
- [x] Step 7 (plain-language floor): verifies direction against named plain-language
  and inclusivity standards; a `references/plain-language-floor.md` file names the
  governing standards (GOV.UK Content Design plain-language guidance and the US
  Federal Plain Language Guidelines as the two stable named references) and defines
  the three specific checks the step applies: no jargon the reader didn't bring, no
  idioms that don't translate, no assumptions about the reader's identity.
- [x] VoC findings are taken as optional input: the SKILL.md procedure explicitly
  states that when VoC is absent the skill elicits audience language inline (a short
  "what words does your audience use?" prompt) and flags the resulting goals as
  "directional — not backed by VoC research" — consistent with `aesthetic-direction`'s
  posture on persona as optional input.
- [x] Artifact path `docs/design/copy/<slug>.md` with `type: copy-direction` is
  documented in SKILL.md; `copy-direction` is named as an extension to the pack's
  discover-by-marker set alongside `content-brief`.
- [x] One-line cross-reference scope note added to
  `packs/product-engineering/.apm/skills/voice-and-microcopy/SKILL.md`; note states
  the surface-type boundary: `copy-direction` owns marketing/acquisition copy voice
  and positioned copy (hero headlines, above-fold narrative, taglines);
  `voice-and-microcopy` owns product UI copy states (error, empty state, button
  labels, form labels). Onboarding is explicitly carved: the onboarding narrative
  arc and structure → `content-design`; the onboarding copy voice and register →
  `copy-direction`; onboarding UI-state strings → `voice-and-microcopy`.
- [x] `copy-direction` is listed in `[pack.evals] skills` in
  `packs/experience/pack.toml`; `evals/eval_queries.json` and `evals/evals.json`
  exist under `packs/experience/.apm/skills/copy-direction/evals/`.
- [x] `packs/experience/pack.toml` version is `0.5.0` (minor bump from 0.4.2,
  reflecting two new public-interface skills); `packs/experience/.claude-plugin/plugin.json`
  version is also `0.5.0`; `make build-self` has been run to re-aggregate
  `marketplace.json` with the updated version.
- [x] `tools/lint-experience-agnostic.py` exits 0 on `packs/experience/` with both
  new skills present.
- [x] `docs/backlog.md` entries `copy-direction-skill-rfc` and
  `content-strategy-and-marketing-copy-lens` carry an in-progress marker referencing
  RFC-0062.
- [x] SEO keyword targeting, advertising copy templates, and brand identity
  documentation production are explicitly listed as out of scope in the SKILL.md
  Anti-patterns or a clearly marked scope note (RFC-0062 D5 governs both skills).
- [x] The skill is standalone-useful: it elicits persona, surface type, and felt copy
  vibe inline when no `content-design` output is provided; no upstream artifact is
  required to invoke it.
- [x] `docs/backlog.md` has an entry under `### experience-reviewer-content-brief-scope`
  recording that experience-reviewer's scope extension to include content briefs is
  deferred (RFC-0062 OQ1), with a decide-by of "spec authoring for content-design."

## Assumptions

- **Technical:** `voice-and-microcopy` lives in `packs/product-engineering/.apm/skills/voice-and-microcopy/SKILL.md`
  and a one-line cross-reference addition does not require RFC-0030 approval —
  cross-reference scope notes are informational edits, not behavior changes.
  (source: experience-pack spec Boundaries "Ask first" confirms home change requires
  sign-off; adding a note does not)
- **Technical:** The experience pack version follows semver minor bumps for new
  public-interface additions (two new skills = 0.4.2 → 0.5.0). The major version
  (0.x) reflects pre-1.0 maturity, not a breaking change.
  (source: pack.toml version history inspection 2026-07-18)
- **Product:** RFC-0062 D4 (surface type as the `copy-direction` / `voice-and-microcopy`
  boundary) and OQ2 (VoC as optional input) are accepted as the binding decisions
  governing this spec's scope boundary and input posture.
  (source: RFC-0062 D4, OQ2 recommendations)
- **Product:** The `copy-direction-skill` spec depends on `content-design-skill` being
  implemented first in the same PR or a prior PR — copy-direction's hand-off step
  references the content-design artifact. If shipped separately, the hand-off step
  references the artifact path as a future upstream.
  (source: RFC-0062 skill chain diagram)
