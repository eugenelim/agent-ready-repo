# Spec: intent-triad-execution-wiring

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0053 (governing — the no-engine coordinator contract, the typed sidecar, and the gate ladder this spec wires); ADR-0111 (intent-stage review is optional, emits `MALFORMED(<field>)` or nothing, and leaves `frame-intent` holding revision and status authority — this spec changes nothing about that review, and defers recording that one ran to the `shaping-review` follow-on)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A product engineer running `discovery-loop` gets the intent triad executed
rather than implied: `discovery-lead` names `frame-intent`, `de-risk-intent` and
`decompose-intent` at the gates they run at, and the G3 leaf handoff names the
invocation that continues the work on its Core-absent branch as well as its
negotiated one. Success is that a reader of `discovery-lead.md` alone can run
the ladder without reconstructing it from the skill's gate table, and that a
controller writing an `assumption-test` or `delivery-contract` slot has a
documented shape and starting classification to write against.

## What Changes

- Two blackboard slot types gain a documented shape and starting classification —
  `assumption-test` and `delivery-contract` — in
  `packs/product-engineering/.apm/skills/discovery-loop/references/sidecar-schema.md`.
- The gate-ladder walk names the triad — `packs/product-engineering/.apm/agents/discovery-lead.md`,
  "How you run the loop".
- The standalone-authoring exclusion stops reading as if the triad sits outside
  the loop — `discovery-loop/SKILL.md` frontmatter `description`.
- A `## Pick a route` section naming the three shaping sequences and the skill that opens each — `frame-intent/SKILL.md`, pointed at from `discovery-loop/SKILL.md`'s "When to invoke".
- The G3 Core-absent branch names `work-intake` as its next invocation, and the adjacent `only when ... advertises` restriction is rescoped in the same edit so it reads as bounding the object rather than the target —
  `discovery-loop/SKILL.md` "Capability-negotiated G3 handoff",
  `decompose-intent/SKILL.md` step 3, and
  `decompose-intent/references/recursive-decomposition.md`.

A skill's frontmatter `description` is not a restatement of the route menu. A
`description` states when to reach for that one skill and when not to; the menu
states which of three sequences a request belongs to. AC6 edits one such
exclusion clause and does not bring it under the menu's single-home rule.

This delivery does not change the `hands off to work-loop at G3` wording in
either frontmatter `description` or in `discovery-loop/SKILL.md`'s body. That
wording names the destination loop; the gate table's `work-intake` names the
route into it, and the two are compatible at different altitudes.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable; the sidecar schema is the contract consumers read for slot shape and handling | `packs/product-engineering/.apm/skills/discovery-loop/references/sidecar-schema.md` | pack maintainer | the two slot types appear in the field table with their field sets, and the classification section states both the starting level and that levels are assigned per instance at write time | a consumer can name each new slot's shape and starting classification from the schema alone, and cannot read a starting level as a fixed per-type value |
| Current product truth | Applicable; `discovery-lead.md` is the agent definition an adopter's harness loads | `packs/product-engineering/.apm/agents/discovery-lead.md` | pack maintainer | a pack test asserting the three skill names appear in the gate-ladder walk | the agent's walk and the skill's gate table name the same skills |
| Decision rationale | Not applicable | — | — | — | this spec follows ADR-0111 and RFC-0053 rather than deciding anything they left open; no new ADR is warranted |
| Release history | Applicable; `product-engineering` ships a consumer-visible schema and agent change | `packs/product-engineering/pack.toml`, `packs/product-engineering/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md` | pack maintainer | matching bumped versions, a regenerated `.claude-plugin/marketplace.json`, and one free-standing `##` entry with an explicit `Highlights` disposition | the four-step pipeline in `packs/AGENTS.local.md` § "Marketplace and release pipeline" is complete |
| Current product truth | Applicable; the route menu is the pack's front door and the answer to "which of these do I run" | `packs/product-engineering/.apm/skills/frame-intent/SKILL.md` | pack maintainer | a pack test reading the `## Pick a route` section's three routes and its `frame-situation` pointer | a reader arriving with an unshaped idea can pick a route from the skill alone |
| User-facing promise | Applicable; two guide passages state the G3 continuation and the gate walk this delivery changes | `guides/product-engineering/explanation/the-discovery-loop.md`, `guides/product-engineering/how-to/run-a-discovery.md` | maintainer | a read of each named passage against the shipped skill and agent | each named passage names the same G3 continuation *route* as the skill's gate-table G3 row, and neither states a gate walk the shipped agent contradicts |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Preserve the exact strings the roster and pack tests read: `"portable rendered"` and `"Core absence"` in `discovery-loop/SKILL.md`, and every string asserted by `packs/product-engineering/tests/pack/test_frame_intent_shaping_review.py` and `test_de_risk_intent_reviewer_boundary.py`.
- Keep every change a file edit under `packs/product-engineering/` plus its tests (CHARTER Principle 3 — no engine, scheduler, service, or solver).
- Give each of the two new slot types a row in the field table, a starting classification, and a stated field set, so no slot is documented on only one surface.
- Treat the blackboard `type` list as open — it ends in `…`. Documenting these two gives them a shape and a starting classification; it does not close the list, and no criterion here claims the list became exhaustive.
- Update each edited skill's `evals/` harness, or record in the verification ledger that the edit changes no eval-visible behavior and why (`packs/AGENTS.md` § authoring rules).

### Ask first

- Before changing the `normalized-intake.v1#handoff` envelope, its field set, or its digest — `tests/roster/test_shaping_handoff_pack_surface.py` digest-pins it against its projections.
- Before adding a slot type beyond the two named in `What Changes`.
- Before editing `packs/product-engineering/pack.toml` integration entries.

### Never do

- Never restate the route menu in a second skill; `frame-intent`'s intake step is its only home and every other surface points at it.
- Never enumerate the six-step sequence's steps, its entry rules, or its availability degrade in the menu. `frame-situation` owns all three — its own purpose statement, its "Recommend entry point" step, and its "Step 2 readiness" degrade. The menu names it and stops.
- Never add a slot type that stores text authored outside the loop. This delivery cut `shaping-review` for that reason; reintroducing it needs its own shaping pass, not a criterion here.
- Never move spec authoring into `decompose-intent`; `new-spec` keeps the spec and plan approval gates.
- Never add a new module, package, script, or top-level directory — this delivery changes Markdown and its tests only.

## Testing Strategy

Every behavior here is text in a shipped artifact that another surface reads, so
every criterion is verified by a **goal-based check**. No criterion carries a
compressible invariant, so TDD's red-green cycle would be ceremony over a string
comparison; none is user-invoked, so there is no manual-QA gesture to record.

The checks take two shapes, decided by what they must read. A criterion whose
subject lives inside `packs/product-engineering/` is a **shipped pack test**. A
criterion whose subject lives above the pack — the version files, `guides/`,
`docs/product/changelog.md` — is a **delivery-time check**, because a pack test
resolves `PACK_ROOT` and may not read above its own pack.

- Slot-type documentation (AC1-AC4): goal-based, exercised by a new pack test reading each schema surface separately — the field-table row, the per-slot field sets, the classification section's starting level, and the floor rule beneath its existing opening sentence. Reading the surfaces separately is what makes this more than a grep: a slot named in the field table but absent from the classification section is the drift the check exists to catch.
- AC3 is the guard, and it asks for one new sentence, not two. The section already opens with "Each slot carries — or the skill assigns at write time — a **data-classification level**"; AC3 anchors on that and requires only the floor rule beneath it, so the criterion cannot be half-satisfied by shipped text. The dangerous shape is a per-type constant, because it lets a higher-classified instance be read off a table instead of assessed; a criterion forbidding that shape would be an absence with no named subject, which no check can look for. Both slot types here are authored by the loop's own skills and carry the schema's own `internal` examples — product strategy and a scope boundary.
- Gate-ladder pairing (AC5): goal-based, exercised by a pack test that slices `discovery-lead.md` to `^## How you run the loop$` and asserts each skill sits beside its stated gate, so a bare mention elsewhere in the file - or an unpaired list inside the section - cannot satisfy it.
- Standalone-authoring description (AC6): goal-based, exercised by a pack test reading the frontmatter `description`, asserting both the two names that stay and the one that goes.
- Core-absent invocation (AC7-AC9): goal-based, exercised by a pack test that isolates one named sentence per surface before asserting - `portable rendered`, `If Core is absent`, `Otherwise render`. Scoping to the sentence is load-bearing: `work-intake` already appears on two of the three surfaces on the negotiated branch, so a file-scoped or section-scoped assertion is green with no edit made.
- Route menu (AC10-AC13): goal-based, exercised by a pack test that slices `frame-intent/SKILL.md` to its `## Pick a route` section before asserting, and reads `discovery-loop`'s "When to invoke" for the pointer. Slicing is load-bearing: `identify-opportunities` is named legitimately in `frame-intent`'s step 5 opportunity-scoring pointer, so a file-scoped absence assertion would red on shipped text this delivery must not touch.
- Version parity and bump (AC14): goal-based, a delivery-time read of the two version files against the base commit. It is deliberately not a shipped pack test: the baseline is a fact about this delivery, and a shipped assertion pinned to one version string asserts nothing after this PR merges.
- Guide reconciliation (AC15) and changelog placement (AC16): goal-based, delivery-time reads. Neither can be a pack test - `guides/` and `docs/product/changelog.md` sit above `packs/product-engineering/`, and a pack test resolves `PACK_ROOT` and reads only inside its pack.

## Acceptance Criteria

- [x] `sidecar-schema.md`'s blackboard `type` field row names `assumption-test` and `delivery-contract` among its listed artifact kinds.
- [x] `sidecar-schema.md`'s "Data classification & handling" section states that `internal` is the level a controller starts from for `assumption-test` and `delivery-contract`.
- [x] Beneath the "Data classification & handling" section's existing opening sentence — "Each slot carries — or the skill assigns at write time — a **data-classification level**" — `sidecar-schema.md` states that a starting level named for a slot type is a floor a write-time assessment may raise.
- [x] `sidecar-schema.md` states that an `assumption-test` slot carries the riskiest assumption, the predeclared kill condition, the prototype-approach, and the `validation_hook`; and that a `delivery-contract` slot carries the G3 leaf projection.
- [x] `discovery-lead.md`'s "How you run the loop" gate-ladder walk names `frame-intent` at G0, `de-risk-intent` at G1, and `decompose-intent` at both G1 and G3 — the two ladder positions the gate table gives it.
- [x] `discovery-loop/SKILL.md`'s frontmatter `description` standalone-authoring exclusion names `frame-domain` and `explore-options`, and does not name `frame-intent`.
- [x] The fallback sentence in `discovery-loop/SKILL.md`'s "Capability-negotiated G3 handoff" — the sentence containing `portable rendered` — names `work-intake` as the invocation that portable handoff is submitted to.
- [x] In `decompose-intent/SKILL.md`, the sentence beginning `If Core is absent` names `work-intake` as the invocation that branch submits to.
- [x] In `decompose-intent/references/recursive-decomposition.md`, the sentence beginning `Otherwise render` names `work-intake` as the invocation that branch submits to.
- [x] `frame-intent/SKILL.md` carries a `## Pick a route` section positioned between its `## When to invoke` and `## Procedure` sections. That section is the route menu, and it bounds AC11 and AC12.
- [x] The `## Pick a route` section names three routes, each with a one-line statement of the situation it fits: one naming `frame-intent`, `de-risk-intent` and `decompose-intent`; one naming `discovery-loop`; one naming `frame-situation`.
- [x] Within the `## Pick a route` section, `frame-situation` is the only skill of the six-step sequence named — the sequence's opening skill, and no later step of it. The section may not name `identify-opportunities`, `diverge-solutions`, `place-bet`, or `map-capabilities`.
- [x] `discovery-loop/SKILL.md`'s "When to invoke" section points at `frame-intent`'s `## Pick a route` section.
- [x] `packs/product-engineering/pack.toml` and `packs/product-engineering/.claude-plugin/plugin.json` carry the same version, and it orders after — by semantic-version comparison, not string comparison — the version in `pack.toml` at `git merge-base HEAD origin/main`. That merge-base is the canonical baseline for this criterion; the plan references it rather than restating it.
- [x] `guides/product-engineering/how-to/run-a-discovery.md`'s "When it hands off" section names the same G3 continuation *route* as `discovery-loop/SKILL.md`'s gate-table G3 row — the route, not the destination loop, which the skill separately and compatibly names as `work-loop`.
- [x] `docs/product/changelog.md` carries a free-standing `## [product-engineering][<version>] — <date>` heading whose version equals the bumped pack version, placed above every other pack release heading and not nested under `[Unreleased]`.

## Assumptions

none
