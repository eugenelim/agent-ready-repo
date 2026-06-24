# Spec: product-rung

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0033, RFC-0043 (D1–D6 + open-question defaults OQ1/OQ2; OQ3 deferred to post-ship review, not settled here); ADR-0019 (the recursive level-tagged `intent` ontology this refines — its part 1 `Level` enum only; parts 2–3 are preserved and out of scope); RFC-0030 (the `product-engineering` pack's founding RFC)
- **Contract:** none <!-- prompt-only markdown skill content; no API/event/RPC surface -->
- **Shape:** n/a — skill prose + template/reference authoring across the three `product-engineering` skills plus one `core` `init-project` seam; no application LLD

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A user shaping a **greenfield product concept** (or a multi-feature bet) with the `product-engineering` pack can frame it at a **product altitude** — `product-vision` (the existence bet: why this product should exist, for whom, through what wedge) or `product-strategy` (the path: the central challenge, guiding policy, coherent actions, and problem/segment sequence) — instead of being coerced to a `feature` intent by the old Scale→Level stamp. `Level` is an **open** field carrying a **recognized set** (`product-vision` › `product-strategy` › `capability` › `feature`); `Scale` *suggests* a starting altitude but never silently stamps one, and keeps its load-bearing leaf-projection role. Either rung is authorable directly; **skipping is allowed but observable** — a sibling-spawn detector offers to frame the product parent when a concept won't reduce to one shippable slice, and a retroactive-parent affordance back-links orphaned siblings at an inferred altitude. The product-existence bet is de-risked **once at the top** as `market-existence` (market desirability + viability), a kind categorically distinct from feature-level `desirability`. The greenfield product loop connects to core's `init-project` as a recognized discovery source. Everything is **prompt-only**: no engine, hook, new skill, or new artifact type.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep every change **prompt-only** — enum widening, prompt edits, two seeded level-conditional field blocks, one de-risk-kind row, tracker-projection rows, and one by-reference seam doc. No engine, hook, new skill, or new artifact type.
- Keep `Level` **open-valued**; document the recognized set `product-vision › product-strategy › capability › feature` as the seeded/prompted altitudes, not a closed enum.
- Preserve `Scale`'s **leaf-projection** role unchanged (`app` → a same-repo `core` brief; `business-unit` → per-component slices); only the Scale→Level **stamp** becomes a suggested starting altitude.
- Give the product-existence bet a **distinct de-risk token** (`market-existence`); never reuse the word `desirability`. Reuse the existing pre-PMF qualitative-bar in `kill-condition.md` — add no new de-risk mechanism.
- Make either rung **authorable directly** and skipping **safe-but-observable** — the sibling-spawn detector *offers*, never blocks; the retroactive parent's altitude is *inferred and confirmable*, never assumed.
- Bump `product-engineering` `0.5.1 → 0.6.0` (`pack.toml` + `.claude-plugin/plugin.json`) and re-aggregate `marketplace.json`; bump `core` (patch/minor) for the seam and run `make build-self` (the `core` `init-project` skill **is** self-host-projected).
- Add a `[Unreleased] → Added` changelog entry (`docs/product/changelog.md`) in the implementing PR.

### Ask first

- Any change to `Scale`'s leaf-projection role, or to `receive-brief`'s level-agnostic contract / the brief's no-`level:`-field shape (these are ADR-0019 part 2 — preserved and out of scope to redesign).
- Renaming either rung away from `product-vision` / `product-strategy` (the RFC-0043-Accepted tokens).
- Mandating either rung, or turning the sibling-spawn detector into a gate rather than an offer.

### Never do

- Cite `RFC-0043`, any ADR/RFC number, `docs/rfc/…` paths, or a `docs/backlog.md` anchor in any **shipped `.apm/**`** content (the seeded field sets, prompts, references) — the `AGENTS.local.md` adopter-clean rule. Provenance lives in this spec and ADR-0033, never in shipped prose.
- Edit the **immutable** ADR-0019 body or the **frozen** RFC-0043 body.
- Import `product-engineering` code into core's `init-project` — the seam is **by reference only**, and `init-project` still performs no discovery itself.
- Ship a new artifact type (`vision.md` / `strategy.md`), a fixed N-deep `Level` ladder, write-time hooks, or a heavyweight fixed-type ontology.

## Testing Strategy

This is a skill-prose / template / reference change; verification is **goal-based** and **manual QA**, with no TDD-mode logic:

- **Enum widening, recognized-set doc, Scale→Level suggestion, leaf-projection preserved, both field blocks present + level-conditional, `market-existence` row, tracker rows, the `init-project` seam, version bump, changelog, guide touch-up, adopter-clean** — *goal-based*: a `grep` / `diff` / build one-liner verifies each outcome. (The adopter-clean grep and the both-blocks-present check are cross-cutting — see `plan.md` Construction tests.)
- **The rungs route correctly end-to-end** — *manual QA, exercised end-to-end*: run `frame-intent` on a greenfield product concept and confirm it **offers `product-vision`** (not a silent `feature` stamp); run `de-risk-intent` on a `product-vision` intent and confirm it picks **`market-existence`** (not `desirability`); drive the sibling-spawn path and confirm it **offers** the product parent rather than emitting orphaned siblings. A passing grep alone does not satisfy this — the built skills, run as a user would, must produce the right behaviour.

## Acceptance Criteria

- [ ] **`Level` is open with a recognized set.** `intent-model.md` and `intent-template.md` document the recognized set `product-vision › product-strategy › capability › feature` and state the field stays **open-valued** (an adopter may name an intervening altitude); the `intent-template.md:11` `Level:` comment is widened from `<capability | feature>` to show the recognized set without closing it.
- [ ] **The two rungs are the same recursive `intent` at a higher `Level`** — no new artifact type, file layout, discovery wiring, or hook is introduced; the `intent` template, recursion, de-risk loop, and decomposition boundary are reused unchanged in shape.
- [ ] **`product-vision` and `product-strategy` semantics are documented.** `intent-model.md` (and the guide, per the guide AC) state that `product-vision` is the *existence bet* (why this product should exist, for whom, through what wedge) and `product-strategy` is the *path* (central challenge, guiding policy, coherent actions, problem/segment sequence), with vision sitting above strategy and both above `capability`.
- [ ] **The Scale→Level stamp becomes a suggestion.** `scale-intake.md`'s "default level" role and `frame-intent` SKILL.md step 3 no longer hard-stamp / hard-nudge an altitude from Scale; they offer a *suggested starting altitude* (`app` greenfield concept → `product-vision`; `app` known feature → `feature`; `business-unit` → `product-strategy` or `capability`) that the user overrides in one word.
- [ ] **`Scale`'s leaf-projection role is preserved unchanged.** `scale-intake.md`'s leaf-projection sentence and the intake table's "Leaf lands as" column still map `app` → a same-repo `core` brief and `business-unit` → per-component slices; no edit weakens or removes this.
- [ ] **`frame-intent` asks the altitude explicitly for concept-shaped / greenfield input** rather than defaulting to `feature`; for a clearly-scoped feature it still proceeds at `feature` without ceremony.
- [ ] **The `product-vision` field block is seeded** (level-conditional, filled only at that rung) in `intent-template.md`: customer-shaped pitch · the change (what's different for the customer) · the job + struggling moment · who, by circumstance (early adopter, not demographic) · existing alternatives (what they do today, badly) · narrowest wedge (smallest version someone pays for now) · demand evidence (behaviour/payment, not stated interest) · open assumptions tiered (`must-test-before-shipping` / `accept-as-bet` / `will-monitor-post-ship`) · counter-metrics.
- [ ] **The `product-strategy` field block is seeded** (level-conditional): central challenge (diagnosis) · guiding policy · coherent actions (3–5) · problem/segment sequence (which, in what order, why now) · horizon.
- [ ] **The field blocks are prose / short-field and live in the single `intent-template.md` markdown file** — no new per-rung template, layout, or schema; an empty heading remains a prompt, not an error (the pack's template-not-schema posture holds).
- [ ] **`market-existence` is added as a distinct de-risk kind.** `de-risk-intent` SKILL.md and `intent-model.md`'s level→kind mapping gain a row: `product-vision` / `product-strategy` → `market-existence`. The seeded gloss **names both halves explicitly** — will-anyone-want-this-at-all (market desirability) **and** can-this-be-a-business (viability) — so the Cagan/SVPG viability gap is visibly closed, not just the token renamed. The prose states it is **categorically distinct** from `feature → desirability`, and the two kinds carry **different tokens** (the word `desirability` is not reused for the product-level bet).
- [ ] **`market-existence` reuses the existing pre-PMF qualitative-bar** in `kill-condition.md` (no new de-risk mechanism), and the bet is named as tested **once at the top**, not re-litigated per sibling feature.
- [ ] **The sibling-spawn detector is added** to `frame-intent` / `decompose-intent` as prompt-only behaviour: it trips on the **qualitative shippability test** (the intent won't reduce to a single shippable slice — the sibling *count* is a signal, not a fixed threshold) and **offers** to frame the product parent instead of silently emitting orphaned siblings. It offers, never blocks.
- [ ] **The retroactive-parent affordance is added** with an **altitude-inference rule**: when a rung was skipped and multiple intents already exist, the agent reconstructs a parent and back-links the siblings via the existing `Parent intent:` field (`intent-template.md:14`), inferring the altitude (**architectural slices of one buildable thing → `capability`**; **independent value bets that together constitute one product → `product-vision` / `product-strategy`**), naming the inferred altitude and letting the user correct it.
- [ ] **`recursive-decomposition.md` reads for any level above the leaf** — the existing "Above feature level → produce child intents at the next lower `Level:`" rule is confirmed to already cover the new rungs (no engine or recursion change); any wording that implied a two-level `capability | feature` ceiling is generalized.
- [ ] **`tracker-projection.md` gains rows for the two rungs** (OQ1 default): both map to a higher/intervening tier — Jira Align Theme/Strategy tier; Linear → Initiative / label; `none` → markdown (unchanged) — with the existing `top (capability)` and `feature` rows preserved.
- [ ] **The `init-project` seam is added, by reference only.** Core's `init-project` stage 2 ("value gate") names `intent` / `frame-intent` as a **fourth** recognized discovery source alongside `research`, a PRD, and a `receive-brief` brief, and documents that `frame → de-risk → decompose` hands its leaf into `init-project`. The seam names it as an **optional upstream** — phrased "when the `product-engineering` pack is installed", mirroring `init-project`'s existing `research`-pack "when installed" framing — so a `core`-only adopter reads it as a clearly-optional source, not a dangling cross-reference. `init-project` **imports nothing** from `product-engineering` and **still performs no discovery itself** (the anti-pattern at `init-project/SKILL.md:128` and the by-reference rule at `:143-146` both hold).
- [ ] **Migration is empty and additive.** Existing `capability` / `feature` intents stay valid (the recognized set is a superset); no data migration is needed; the only schema-shaped change is the widened `Level:` comment.
- [ ] **Versions are bumped and projections refreshed.** `product-engineering` `pack.toml` `[pack].version` + `.claude-plugin/plugin.json` `version` go `0.5.1 → 0.6.0` in lockstep and `marketplace.json` re-aggregates drift-clean (this pack is **not** self-host-projected — no `.claude/skills/` copy); `core` is bumped (patch/minor) for the seam and `make build-self` refreshes the projected `.claude/skills/init-project/SKILL.md`; `git status` shows only the expected drift.
- [ ] **A `[Unreleased] → Added` changelog entry** is added in the implementing PR (`docs/product/changelog.md`), written for users (the new product altitudes; Level decoupled from Scale).
- [ ] **The `product-engineering` user guides are touched up** to describe the two rungs and the Level-vs-Scale model, across every page that currently encodes the two-level `capability | feature` model or the `app → feature` stamp:
  - explanation `the-intent-tree.md` — the two product altitudes (`product-vision`, `product-strategy`) and why one recursive shape still covers them;
  - reference `intent-fields-and-modes.md` — the recognized-set `Level` values, the two seeded field blocks, and the `market-existence` de-risk kind;
  - the guides index `README.md` — the overview names the product altitudes alongside capability/feature (not just "a strategy, an epic, and a feature");
  - how-to `shape-a-feature-intent.md` — a note that an app-scale **greenfield concept** can start at a product altitude (`Level` is no longer stamped from `Scale`), not only at `feature`.
- [ ] **The `product-engineering` pack README is updated** (`packs/product-engineering/README.md`) — the "same artifact at different levels" line and the `frame-intent` table row name the product altitudes (`product-vision` / `product-strategy`) and state that `Level` is an open recognized set **decoupled from `Scale`**. Repo-owned source; it ships via `make build` (no `build-self` — `product-engineering` is not self-host-projected).
- [ ] **The core inception guide names the seam** — wherever the `init-project` discovery sources or the cross-pack inception flow are taught (`docs/guides/_shared/how-to/run-a-full-inception.md`, where `product-engineering` already sits around the `core` spine; and the discovery-source list in `docs/guides/core/tutorials/start-a-new-project.md`), `intent` / `frame-intent` is named as a fourth discovery source feeding `init-project`, framed as optional upstream.
- [ ] **Shipped content is adopter-clean.** No shipped file touched by this change — anything under `packs/product-engineering/.apm/**`, `packs/core/.apm/**`, or `packs/product-engineering/README.md` (the pack README ships to adopters via `make build`) — cites `RFC-0043`, any ADR/RFC number, a `docs/rfc/…` path, or a `docs/backlog.md` anchor; provenance lives in this spec and ADR-0033. (The repo-owned `docs/guides/**` pages are *not* shipped to adopters and are exempt — cross-cutting grep, see `plan.md`.)

## Assumptions

- Technical: `Level` is hardcoded `<capability | feature>` at `intent-template.md:11`; `intent-model.md` defines only `capability` (architectural span) and `feature` (desirability) kinds; the recursion ("Above feature level → produce child intents at the next lower `Level:`", `recursive-decomposition.md:14`) already supports N levels above feature with **no engine change** (source: reads of the three files, probe 2026-06-23 — RFC-0043 spike re-verified).
- Technical: `Scale` has two roles in `scale-intake.md:29-30` — the default Level (which becomes a suggestion) and the `app`-brief / `business-unit`-slice leaf-projection (which is preserved); only the first changes (source: `scale-intake.md`, probe 2026-06-23).
- Technical: `kill-condition.md:16-19` carries a pre-PMF / 0-to-1 **qualitative-bar** mode that fits the `market-existence` currency, so no new de-risk mechanism is needed (source: `kill-condition.md`, probe 2026-06-23).
- Technical: `product-engineering` is **not** part of this repo's self-host projection (no `.claude/skills/frame-intent` etc.), so its version bump drifts only `marketplace.json` via `make build`; `core`'s `init-project` **is** projected (`.claude/skills/init-project/SKILL.md`), so the seam edit needs `make build-self` (source: `ls .claude/skills`, probe 2026-06-23; memory: self-host pack scope).
- Process: implementation lands in a **separate** PR; this spec + ADR-0033 + `plan.md` are the **governance deliverable**, and the spec stays `Draft` until that implementing PR flips it (source: RFC-0043 § Follow-on artifacts; the RFC-0042 → ADR-0032 + `agentic-well-architected-overlay` precedent).
- Process: ADR-0019 is **refined, not superseded** — only its part 1 `Level` enum is reopened/decoupled; parts 2 (brief = feature-intent projection) and 3 (staged contracts) stand, and ADR-0019 stays Accepted (source: RFC-0043 Related line + the immutable-ADR convention, `CONVENTIONS.md`).
- Process: shipped `.apm/**` content carries no internal-governance citations (RFC/ADR numbers, `docs/rfc/…` paths, backlog anchors) (source: `AGENTS.local.md` § Shipped pack content carries no internal-governance citations).
- Product: RFC-0043's open questions are settled to their RFC-recommended defaults — OQ1 tracker rows → higher/intervening tier; OQ2 `product-strategy` available at any Scale, mandatory at none; OQ3 adopter demand beyond n=1 → watch post-ship feedback (source: RFC-0043 § Open questions defaults, decide-by "spec").
