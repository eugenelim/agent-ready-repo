# Plan: well-architected-cloud

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Pure-markdown skill content in `packs/architect/`. The bulk is new **reference** files
(the well-architected substance + the convergence-loop procedure); the `SKILL.md` edits are
thin routing because every `SKILL.md` sits near the pack's <100-line ceiling. The riskiest
parts are not the content — they are honoring four pack principles that pull against the
obvious approach: (1) **no shared references** — common substance is duplicated per-skill
with a note, never centralized; (2) the **<100-line ceiling** — `architect-diagram` (96) and
`architect-review` (92) have almost no headroom, so SKILL.md gains only routing lines and all
depth goes to `references/`; (3) **no required composition** — `architect-design`'s loop must
degrade to its own rubric when `architect-review` is absent; (4) **no subagents / no script** —
the convergence loop is prose the agent follows in-conversation, never `loop-cohort` and never
a state file.

Order: author the reference set + the loop procedure on the design side (T1), wire the
design-side SKILL.md stage + loop (T2), duplicate the set into review with the
mechanical/judgment finding tag + WA rubric + risk-register asset (T3), wire the review
SKILL.md mode while preserving review-only (T4), add the diagram-side primitives parity ref
(T5), do the version/changelog/marketplace/README housekeeping (T6), then author the dogfood
fixtures and run manual QA (T7). Testing is goal-based structural greps for the invariants
plus manual-QA dogfooding for skill + loop behavior (no code → no TDD).

## Constraints

- No ADR/RFC governs this — in-charter for the `architect` pack (README defers the
  EA-platform layer, not cloud well-architected).
- Binding pack principles: skill autonomy over DRY (duplicate, don't share); <100-line
  SKILL.md; mode detection inside the skill; inline-first; Mermaid-only; no required
  configuration; **no subagents** (README:72-73); no required composition (README:50-54).
- Distribution model projects content to a scope-specific *path*, not different content per
  scope — confirming the loop must live inline in `architect-design`, not in a scope-gated or
  separate pack (`scope.py`, `commands/install.py`).
- Optional composition with the user-scope `research` skill (`applied`/`deep`) powers the
  leading-edge path; it is never required — `architect-design` degrades to first-principles +
  flagged-novelty + lowered-confidence when `research` is absent (no-required-composition).

## Construction tests

**Integration tests:** none beyond per-task tests (no code; skills are markdown).
**Manual verification:** the dogfood runs in T7 are the cross-cutting behavioral check —
they exercise the full design → review → resolve loop end to end against committed brief
fixtures and are the only verification of prose-skill + loop behavior.

## Design (LLD)

Shape is `mixed` but the work is skill-content, so only two sub-sections earn their place.

### Design decisions

- **Loop lives inside `architect-design`, not a pack.** The distribution model can't ship
  different content per scope, and the loop needs no subagents; a separate `architect-loop`
  pack would buy nothing. *Rejected:* repo-scope `architect-loop` + subagents. Traces to:
  AC "convergence loop", Boundaries "no new pack / no subagents".
- **Loop is pure prose, no script, no `loop-cohort`.** Single artifact, single agent, no
  waves/parallelism → none of `loop-cohort`'s machinery applies; a script forfeits the
  pure-markdown property. *Rejected:* project `loop-cohort`; write a simpler loop script.
  Traces to: AC "convergence-loop … no script, no state file".
- **Reviewer independence via the harness's native facility, cold-read floor.** Honors
  `architect-review`'s "no marking own homework" anti-pattern without shipping an agent
  primitive. *Rejected:* mandate fresh context (unportable) / same-context self-review
  (biased). Traces to: AC "reviewer independence".
- **Mechanical-vs-judgment finding tag in `architect-review`.** The signal the loop consumes
  to decide auto-resolve vs escalate. Traces to: AC "every WA-mode finding carries a
  mechanical vs judgment tag".
- **Concept-first as a *stage*, duplicate-not-share refs, generic `cloud-primitives`, WA as
  an orthogonal *mode* of review, GenAI/agentic lens distinct from the managed-platform
  diagram refs** — as previously decided (see spec ACs). *Rejected:* new skills; shared refs
  dir; `cloud-hetzner.md`; a new review skill.

### Component / module decomposition

New / changed files (all under `packs/architect/`):

- `.apm/skills/architect-design/references/` — **new:** `well-architected-pillars.md`
  (spine + distillation), `quality-attribute-scenarios.md`, `tradeoffs-and-sensitivity.md`,
  `cloud-primitives.md` (generic + gaps checklist + Hetzner exemplar), `local-dev.md` (local-first
  provider-class: local→production delta + graduation path, no toolchain prescription),
  `cross-cutting-questions.md`,
  `lens-genai-agentic.md`, **`convergence-loop.md`** (pure-prose loop: review → auto-resolve
  mechanical → re-review → surface judgment; reviewer independence; pass cap; stasis escape;
  no-`architect-review` degradation), **`leading-edge-domains.md`** (the *method* for novel
  domains: detect → compose with `research` applied/deep → ad-hoc lens → carry source+confidence
  → degrade when `research` absent; ships method, never domain content). Existing
  `nfr-checklist.md` + `design-doc-rubric.md` stay.
- `.apm/skills/architect-design/SKILL.md` — **edit:** Stage-0 concept + by-construction pass +
  loop routing (points at `convergence-loop.md`) + the anti-pattern non-collision note. Thin.
- `.apm/skills/architect-design/assets/` — **new:** `concept.md` — the light one-page concept
  template (arc42 Architecture-Communication-Canvas spirit), sibling to the existing heavy
  `design-doc.md`; the Stage-0 concept is drafted from it.
- `.apm/skills/architect-review/references/` — **new (duplicated from design, each with the
  pack's duplication note):** the seven provider/WA references (well-architected-pillars,
  quality-attribute-scenarios, tradeoffs-and-sensitivity, cloud-primitives, **local-dev**,
  cross-cutting-questions, lens-genai-agentic), **plus** `rubric-well-architected.md` (the
  WA-mode rubric; defines the mechanical-vs-judgment finding-tag taxonomy). (`convergence-loop`
  and `leading-edge-domains` stay design-side — review neither loops nor synthesizes.)
- `.apm/skills/architect-review/assets/` — **new:** `risk-register.md` (severity- *and*
  mechanical/judgment-tagged findings + improvement plan + risk-acceptance + non-risks).
- `.apm/skills/architect-review/SKILL.md` — **edit:** WA/lens mode routing (orthogonal to
  artifact-type) + finding-tag instruction; **review-only mode preserved**. Very thin (92→).
- `.apm/skills/architect-diagram/references/cloud-primitives.md` — **new:** generic primitives
  *diagram* vocab, parity with `cloud-{aws,azure,gcp}.md`.
- `pack.toml`, `.claude-plugin/plugin.json` — 0.1.0 → 0.2.0; `README.md` skill table refresh;
  `.claude-plugin/marketplace.json` regenerated via `make build-self`; `docs/product/changelog.md`
  `[Unreleased]` entry.
- `docs/specs/well-architected-cloud/fixtures/` — **new:** five dogfood brief fixtures
  (`brief-agentic-hetzner.md`, `brief-enterprise-brain.md`, `brief-local-first.md`,
  `brief-hyperscaler.md`, `brief-non-cloud.md`).

> **Rollout & deployment** — see [`## Rollout`](#rollout). No infra; ships as pack content.

## Tasks

### T1: WA reference set + convergence-loop procedure authored on the design side

**Depends on:** none
**Touches:** packs/architect/.apm/skills/architect-design/references/*

**Tests:**
- `ls` shows the nine new references under `architect-design/references/` (AC "shared reference content", AC "convergence-loop reference", AC "leading-edge-domains reference", AC "local-dev reference").
- `cloud-primitives.md` and `local-dev.md` are distinct: primitives = real production hosting lacking managed services ("gaps you must fill"); local-dev = the local-first on-ramp ("local→production delta" + graduation path), neither prescribing a toolchain (AC "local-dev reference", Boundary "no local toolchain").
- `leading-edge-domains.md` describes the method (detect novelty → optionally compose with `research` applied/deep for grey-lit + GRADE confidence → synthesize ad-hoc lens → carry source+confidence → degrade when `research` absent) and states it ships method-only, never domain content (AC "leading-edge-domains reference", Boundary "never ship leading-edge domain content").
- No load-bearing cross-skill link: `grep -rE 'load|see|include' <refs>` finds no directive pointing into another skill's `references/` dir; the prose duplication note (names a sibling file) is exempt and is the only permitted mention (AC "no inter-skill sharing").
- `cloud-primitives.md` has a "capability gaps you must fill" section enumerating gap *categories* (managed data tier, edge/CDN, managed identity, serverless) with ≥1 concrete gap (AC "gaps checklist"). Specific gaps are illustrative here, not pinned in the spec.
- `quality-attribute-scenarios.md` carries the six-part template (source/stimulus/artifact/environment/response/response-measure) (AC "scenario-anchored").
- `lens-genai-agentic.md` covers prompt-injection, tool-use authz, data-egress-to-LLM, evals/observability, token cost, and notes it is distinct from the managed-platform agentic diagram refs (AC "GenAI/agentic lens distinct").
- `cross-cutting-questions.md` includes the third-party-attestation / restricted-scope-data question naming **CASA/ASVS as a downstream gate, referenced not reproduced**, and routing control verification to `security-reviewer`/`security-checklists`; `well-architected-pillars.md`'s Security content carries the same pointer (AC "cross-cutting question bank", Boundary "never reproduce ASVS/CASA checklists").
- `convergence-loop.md` describes the loop as pure prose (no script/state file), the review→auto-resolve-mechanical→re-review→surface-judgment cycle, reviewer independence (fresh-context-preferred / cold-read floor; seed artifact+concept+constraints), the pass cap, the stasis escape, and the no-`architect-review` degradation (AC "convergence-loop reference", AC "reviewer independence", AC "loop terminates").

**Approach:**
- Author each reference from `.context/architect-pack-enterprise-modes-research.md` (PARTS A, E, F), process stripped per Boundaries.
- Keep each reference focused and load-on-demand; no SKILL.md edits here.

**Done when:** the nine references exist, are self-contained, and the greps above pass.

### T2: `architect-design` SKILL.md — concept-first + by-construction + loop routing

**Depends on:** T1
**Touches:** packs/architect/.apm/skills/architect-design/SKILL.md, packs/architect/.apm/skills/architect-design/assets/concept.md

**Line budget:** current 76 lines, ceiling 100 → **≤ 24 lines of headroom** for *all* of:
Stage-0 concept step, by-construction sub-step, loop routing, degradation note, anti-pattern
clarification. The loop *procedure* lives in `convergence-loop.md`; SKILL.md carries only
pointers. **Fallback if the budget is breached:** move the by-construction prose into a
reference and leave a one-line pointer, exactly as the loop detail already is.

**Tests:**
- `wc -l SKILL.md` < 100 (AC "SKILL.md under ceiling").
- SKILL.md describes a Stage-0 concept (problem+constraints, 1–2 shapes, provider/class, top 2–3 QAs) preceding the full doc and awaiting acknowledgement (AC "Stage-0 first").
- SKILL.md distinguishes concept *shaping* from the refused "just write the proposal section" (AC "anti-pattern non-collision").
- SKILL.md routes to `well-architected-pillars.md` / `cloud-primitives.md` / `tradeoffs-and-sensitivity.md` when a provider is named, and degrades gracefully when no provider is in play (AC "pillar achievement", AC "tradeoff/sensitivity", AC "graceful degradation").
- SKILL.md routes the post-draft loop to `convergence-loop.md`, states the loop auto-resolves mechanical findings without asking but never judgment findings, and degrades to the embedded rubric self-check when `architect-review` is absent (AC "convergence loop", AC "never auto-resolve judgment", AC "review not installed").
- `assets/concept.md` exists, sibling to `assets/design-doc.md`, carrying the light one-page concept fields (problem & context, constraints, 1–2 shapes, provider/class + by-construction note, top 2–3 prioritized QAs with *why*, key tradeoff/open decision, optional open questions). **Primary check:** `grep` confirms it carries **none** of the design doc's heavy sections (no full proposal, alternatives-with-rejection, risks table, rollout). `wc -l` materially-shorter-than-`design-doc.md` is corroboration only (AC "light concept template asset", Boundary "concept stays one-page").
- SKILL.md routes the concept stage to the leading-edge path (`leading-edge-domains.md`) when no shipped pillar/lens/provider covers the domain, composing with `research` when available and degrading otherwise (AC "leading-edge path", AC "leading-edge claims carry source+confidence").

**Approach:**
- Author `assets/concept.md` from the arc42 Architecture-Communication-Canvas spirit (travel-light), distinct from `design-doc.md`.
- Insert the concept stage between "Frame the problem" and "Draft inline" (drafting the concept from `assets/concept.md`); add the by-construction sub-step; add a post-draft "Converge" step pointing at `convergence-loop.md`.
- Add one anti-pattern clarification distinguishing shaping from partial advocacy.

**Done when:** SKILL.md < 100 lines; a manual read confirms the stage, the loop routing, the non-collision wording; T7 dogfood ACs for design + loop pass.

### T3: Duplicate WA refs into `architect-review` + WA rubric (finding tags) + risk-register asset

**Depends on:** T1
**Touches:** packs/architect/.apm/skills/architect-review/references/*, packs/architect/.apm/skills/architect-review/assets/*

**Tests:**
- The seven provider/WA references (incl. `local-dev.md`) exist under `architect-review/references/`, each carrying the pack's one-line duplication note (AC "duplicated per skill", AC "local-dev reference").
- No load-bearing cross-skill link (same grep as T1; duplication note exempt) (AC "no inter-skill sharing").
- `rubric-well-architected.md` exists, anchors checks to the pillar spine + lenses, and defines the **mechanical-vs-judgment finding-tag taxonomy as a decidable test** — mechanical = fix fully determined by the pillar spine / a stated constraint with no business-value or risk-acceptance choice; judgment = requires choosing between defensible options (tradeoff / risk-acceptance / low-confidence or leading-edge assumption) — applicable to a novel finding, not just examples (AC "finding tag", AC "mechanical-vs-judgment operationally defined").
- `assets/risk-register.md` carries the output shape: findings tagged severity *and* mechanical/judgment + improvement plan + risk-acceptance + non-risks (AC "WA-mode output shape", AC "finding tag").

**Approach:**
- Copy the six references from T1, prepend the duplication note used elsewhere in the pack.
- Author the WA rubric (genre = a design under WA lenses, with the finding-tag taxonomy) and the risk-register output asset reusing the existing verdict + severity vocabulary.

**Done when:** files exist with duplication notes, greps pass, and the asset names all output elements + the finding tag.

### T4: `architect-review` SKILL.md — WA/lens mode + finding tags; review-only preserved

**Depends on:** T3
**Touches:** packs/architect/.apm/skills/architect-review/SKILL.md

**Line budget:** current 92 lines, ceiling 100 → **≤ 8 lines of headroom** — extremely tight.
The WA-mode branch must be a few routing lines pointing at `rubric-well-architected.md` +
`assets/risk-register.md`; all depth stays in references. **Fallback (bounded):** if 8 lines
won't hold it, relocate **only the passage the WA-mode edit sits adjacent to** (a same-concern
ride-along) into a reference — not a general SKILL.md refactor; the review-only-mode prose stays
untouched.

**Tests:**
- `wc -l SKILL.md` < 100 (AC "SKILL.md under ceiling").
- SKILL.md adds a WA/lens mode detected **orthogonally** to artifact-type routing, selectable by concern-lens and/or workload-class lens incl. GenAI/agentic (AC "WA mode orthogonal", AC "lens selection").
- SKILL.md instructs every WA finding to carry a mechanical-vs-judgment tag and a quality-attribute scenario where measurable (AC "finding tag", AC "scenario-anchored").
- SKILL.md points the WA mode at `rubric-well-architected.md` + `assets/risk-register.md`, reusing the existing verdict/severity tags (AC "WA-mode output shape").
- The existing review-only mode (external artifact: findings + verdict, no auto-fix) is preserved and explicitly distinguished from the loop's use (AC "review-only preserved").

**Approach:**
- Add a short WA-mode branch to the artifact-routing section; keep depth in references; leave the review-only path intact.

**Done when:** SKILL.md < 100 lines; manual read confirms the orthogonal mode, the tag instruction, and the preserved review-only path; T7 dogfood AC for review passes.

### T5: `architect-diagram` cloud-primitives diagram reference (parity)

**Depends on:** none
**Touches:** packs/architect/.apm/skills/architect-diagram/references/cloud-primitives.md, packs/architect/.apm/skills/architect-diagram/SKILL.md

**Line budget:** current 96 lines, ceiling 100 → **≤ 4 lines** — at most a single inline
mention (the existing "Cloud-aware AWS/Azure/GCP" line gains "/primitives", net ~0 new lines);
the reference loads on demand by name-match. **Fallback:** add the reference with no SKILL.md
line if the budget can't absorb one.

**Tests:**
- `cloud-primitives.md` exists alongside `cloud-{aws,azure,gcp}.md` with generic VPS/primitives diagram vocab (AC "diagram parity").
- `wc -l SKILL.md` < 100 (AC "SKILL.md under ceiling").

**Approach:**
- Mirror `cloud-aws.md`'s structure for a generic primitives provider (servers, LB, object storage, private network, firewall; Hetzner exemplar shorthands); add at most one inline routing token.

**Done when:** the reference exists and SKILL.md stays under the ceiling.

### T6: Version bump, changelog, marketplace regen, README refresh

**Depends on:** T2, T4, T5
**Touches:** packs/architect/pack.toml, packs/architect/.claude-plugin/plugin.json, packs/architect/README.md, .claude-plugin/marketplace.json, docs/product/changelog.md

**Tests:**
- `pack.toml` and `plugin.json` both read `version = "0.2.0"` and are consistent (AC "version bumped & consistent").
- `make build-self` regenerates `.claude-plugin/marketplace.json` and the architect entry reflects 0.2.0; `git status` shows only the expected regeneration (AC "marketplace regenerated").
- `make lint-packs` and `python tools/lint-skill-spec.py` green (AC "lints green").
- `docs/product/changelog.md` has a new `[Unreleased]` entry naming the WA + loop capability (AC "changelog entry").
- README skill table mentions the well-architected / lens + convergence-loop capability.

**Approach:**
- Bump both version files; run `make build-self` to regenerate `.claude-plugin/marketplace.json`; add the changelog entry; refresh the README table lines for the two skills.

**Done when:** all gate greps/targets above pass on a clean tree.

### T7: Dogfood fixtures + manual QA on five briefs

**Depends on:** T2, T4

**Approach:**
- Author five committed fixtures under `docs/specs/well-architected-cloud/fixtures/`:
  `brief-agentic-hetzner.md` (the A2UI-agents-on-Hetzner pressure-test brief, planting **two**
  findings — (a) a cleanly-fixable mechanical gap, e.g. an unlabeled trust boundary, to exercise
  auto-resolve; (b) a mechanical finding the rubric **cannot determinately fix**, to exercise the
  **stasis escape**), `brief-enterprise-brain.md` (a leading-edge domain with no shipped
  reference — enterprise brain / living ontologies), `brief-local-first.md` (a founder starting
  local), `brief-hyperscaler.md`, `brief-non-cloud.md`.

**Tests (manual QA):**
- `fixtures/brief-agentic-hetzner.md` → `architect-design` concept names the primitives class + data-tier + edge/CDN gaps, prioritizes Security (agentic) + Performance, surfaces the self-host-inference-vs-external-LLM tradeoff as a sensitivity point (AC "dogfood design").
- Same brief → the loop **auto-resolves** the cleanly-fixable mechanical gap across iterations, **stasis-escalates** the non-determinate mechanical finding to the human, and **surfaces** (never auto-resolves) the self-host-vs-external decision as a judgment finding (AC "dogfood loop", AC "loop terminates", AC "never auto-resolve judgment").
- Same brief → `architect-review` WA mode under GenAI/agentic + security lenses produces a risk register naming the internal-data→external-LLM egress boundary and the A2UI surface-authority risk, each finding mechanical/judgment-tagged (AC "dogfood review", AC "finding tag").
- `fixtures/brief-enterprise-brain.md` → `architect-design` takes the **leading-edge path**: flags novelty, composes with `research` (`applied`/`deep`) when installed (else degrades + flags + lowers confidence), synthesizes an ad-hoc enterprise-brain lens (memory types / knowledge stratums / provenance / governance), and surfaces the centralized-vs-federated-ontology decision as a judgment finding carrying source + confidence (AC "leading-edge path", AC "leading-edge claims carry source+confidence").
- `fixtures/brief-local-first.md` → `architect-design` concept treats local-first as a legitimate starting topology, names the local→production delta + a graduation path to a provider class, and prescribes **no** local toolchain (AC "local-first provider-class", AC "dogfood local-first").
- `fixtures/brief-hyperscaler.md` → `architect-design` concept names provider-managed-service pillar achievement and does **not** apply the primitives "gaps" framing (AC "dogfood hyperscaler").
- `fixtures/brief-non-cloud.md` → `architect-design`'s Stage-0 concept degrades gracefully — shapes problem/constraints/choice/QAs without forcing provider or pillar scaffolding (AC "graceful degradation").

**Done when:** all seven gestures produce the named observables.

## Rollout

- **Delivery:** big-bang pack content; reversible (revert the PR). Nothing irreversible — no
  data, no published events. Adopters pick it up on next pack install/update.
- **Infrastructure:** none.
- **External-system integration:** none beyond regenerating `.claude-plugin/marketplace.json`
  via `make build-self` so the bumped version is consistent across the catalogue.
- **Deployment sequencing:** version/changelog/marketplace housekeeping (T6) lands after the
  content tasks; no other ordering constraint.

## Risks

- **SKILL.md line-ceiling breach** — `architect-review` (92) and `architect-diagram` (96) are
  extremely tight; `architect-design` (76) takes the largest content addition. Mitigation:
  per-task line budgets (T2/T4/T5) + the explicit relocate-to-reference fallbacks; depth lives
  in references, SKILL.md carries pointers.
- **Loop non-termination / over-resolution** — a prose loop could spin or auto-"fix" a real
  judgment call. Mitigation: pass cap + stasis escape + the hard Boundary "never auto-resolve
  a judgment finding"; the dogfood loop gesture verifies escalation.
- **Self-review bias** — same-context review marks its own homework. Mitigation: reviewer-
  independence boundary (fresh-context-preferred / cold-read floor; seed concept+constraints
  not authoring narrative).
- **Marketplace.json drift red-failing build-check** — bumping a user-scope-default pack drifts
  the all-packs aggregation. Mitigation: T6 runs `make build-self` in the same PR.
- **Duplication drift** — duplicated references can diverge. Mitigation: the duplication note
  flags the twin; accepted per the pack's explicit "duplication is the principle" stance.
- **Framework-prescription creep** — the agentic/A2UI material tempts naming frameworks.
  Mitigation: Boundary "never prescribe frameworks"; reviewer check.

## Changelog

- 2026-06-12: initial plan.
- 2026-06-12: expanded `architect-design` to carry the convergence loop (review →
  auto-resolve mechanical → surface judgment) after the user chose loop-in-design over an
  `architect-loop` pack; added the mechanical/judgment finding tag + review-only preservation
  in `architect-review`, the `convergence-loop.md` reference, reviewer-independence handling,
  and the "no script / no loop-cohort" boundary. Folded in adversarial-review fixes
  (cross-link grep wording, per-task line budgets, pinned dogfood fixtures, marketplace path).
- 2026-06-12: added a **local-first provider-class** (`local-dev.md` — local→production delta +
  graduation path, architecture-altitude, no toolchain prescription) as the founder on-ramp
  (concept stage, not a new mode) + a `brief-local-first.md` dogfood fixture.
- 2026-06-12: added the **leading-edge / novel-domain path** (`leading-edge-domains.md` —
  detect novelty → optionally compose with the `research` skill applied/deep → ad-hoc lens →
  carry source+confidence → degrade when absent; ships method not domain content) after the
  enterprise-brain pressure-test; added the CASA/ASVS downstream-assessability pointer + the
  light `assets/concept.md` template. Folded in second-pass adversarial fixes (operationally-
  defined mechanical/judgment discriminator, stasis + never-auto-resolve fixture coverage,
  reviewer-independence scoped to the documentable surface, split compound AC, bounded T4
  fallback, concept absence-of-sections as primary check).
