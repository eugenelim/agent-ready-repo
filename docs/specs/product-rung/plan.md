# Plan: product-rung

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is **prompt-only** edits across the three `product-engineering` skills plus one `core` seam, in two clusters that meet at the `intent` template. **First, the model edits** (the load-bearing semantics): reopen `Level` to an open field with a recognized set, turn the Scale→Level stamp into a suggestion while preserving Scale's leaf-projection role, and add the `market-existence` de-risk kind. **Second, the seeded content and behaviours** that sit on top of the model: the two level-conditional field blocks, the sibling-spawn detector, the retroactive-parent affordance, the tracker-projection rows, and — in `core` — the by-reference `init-project` discovery-source seam.

The riskiest part is **altitude and adopter-cleanliness of the seeded prose**: the field sets must read as a *prompt sheet, not a schema* (an empty heading is a prompt, not an error), stay at the pack's name-the-bet altitude, and carry **no** internal-governance citations (no `RFC-0043`, no ADR/RFC numbers, no `docs/rfc/…` paths, no backlog anchors) since they ship into adopters' repos under `.apm/**`. That is the focus of the adopter-clean cross-cutting grep and the adversarial/quality reviewer passes. The model edits themselves are small, well-bounded prose changes; the spike (RFC-0043 Evidence) already confirmed no engine or recursion change is needed.

This plan describes the **implementing PR**. The governance PR that introduces ADR-0033 and this spec/plan **does not execute it** — it ships the ADR + spec + plan only, and the spec stays `Draft` until the implementing PR flips it.

## Constraints

- **ADR-0033** — the load-bearing decisions: open `Level` + recognized set; Level decoupled from Scale (stamp → suggestion, leaf-projection preserved); the two rungs are the same recursive `intent`; `market-existence` a distinct de-risk kind; the `init-project` seam by reference only; prompt-only, no new primitive.
- **RFC-0043** — D1–D6 and the open-question defaults (OQ1 tracker rows → higher/intervening tier; OQ2 `product-strategy` at any Scale; OQ3 demand watched post-ship).
- **ADR-0019** — refined, not superseded; its part 2 (`receive-brief` level-agnostic, brief has no `level:`, Scale's leaf-projection) and part 3 (staged contracts) are preserved and out of scope.
- **CHARTER Principles 2 & 3** — no duplication (no new artifact type / skill), habit not infrastructure (no engine, hook, or executable tooling).
- **`AGENTS.local.md` adopter-clean rule** — shipped `.apm/**` content carries no internal-governance citations.
- **Self-host projection scope** — `core` is self-host-projected (the `init-project` seam needs `make build-self`); `product-engineering` is **not** (its bump drifts only `marketplace.json`).

## Construction tests

Most verification is per-task below. Cross-cutting checks that span tasks:

**Integration / cross-cutting checks:**
- **Adopter-clean:** a `grep` over every shipped file this change touches — `packs/product-engineering/.apm/**`, `packs/core/.apm/**`, and `packs/product-engineering/README.md` (the pack README ships to adopters) — finds no `RFC-\d`, `ADR-\d`, `docs/rfc/`, or `docs/backlog.md` anchor citation. The repo-owned `docs/guides/**` pages are exempt (not shipped to adopters).
- **Both field blocks present + level-conditional:** `grep` confirms `intent-template.md` carries both a `product-vision` and a `product-strategy` field block, each marked filled-only-at-that-rung.
- **Projection drift-clean:** after `make build-self`, `git status` shows only the expected `.claude/skills/init-project/SKILL.md` drift (core) and, after `make build`, only the expected `marketplace.json` version line (product-engineering) — no unexpected reverts.

**Manual verification:**
- Dogfood the rungs end-to-end (T10): `frame-intent` on a greenfield product concept offers `product-vision`; `de-risk-intent` on it picks `market-existence`; the sibling-spawn path offers the product parent.

## Tasks

### T1: Reopen `Level` to an open field with a recognized set

**Depends on:** none

**Tests:**
- `grep` confirms `intent-model.md` documents the recognized set `product-vision › product-strategy › capability › feature` and states `Level` stays open-valued (AC: Level open + recognized set).
- `grep` confirms `intent-template.md`'s `Level:` comment (line 12) is widened from `<capability | feature>` to show the recognized set without closing the field (AC: Level open).
- `grep`/read confirms `intent-model.md` documents `product-vision` (existence bet) and `product-strategy` (the path) semantics, vision above strategy above capability (AC: semantics).
- `grep`/read confirms the existing "same artifact at every level" tree diagram and the two-consequences de-risk-kind list in `intent-model.md` are **generalized above `capability`** — no wording still presents `capability` as the top of the tree (AC: semantics, generalization clause).

**Approach:**
- Edit `frame-intent/references/intent-model.md` to add the recognized set + the two-rung semantics, keeping the "no fixed ladder / open field" framing.
- Generalize the existing capability-rooted tree diagram and the two-consequences kind list so they read for any level above the leaf, rather than topping out at `capability`.
- Widen the `intent-template.md` `Level:` field comment to the recognized set, leaving the value a free string.

**Done when:** the recognized set and the two-rung semantics are documented in `intent-model.md`, the existing tree/consequences prose is generalized above `capability`, the template comment shows the recognized set with `Level` still an open field, and the T1 greps pass.

### T2: Decouple Scale→Level to a suggestion; preserve leaf-projection

**Depends on:** T1

**Tests:**
- `grep` confirms `scale-intake.md`'s "default level" wording is reframed as a *suggested starting altitude* and `frame-intent` SKILL.md step 3 no longer hard-nudges `feature` at `app` Scale (AC: stamp → suggestion).
- `grep` confirms `scale-intake.md`'s leaf-projection sentence and the intake table's "Leaf lands as" column are **unchanged in meaning** — `app` → same-repo brief, `business-unit` → per-component slices (AC: leaf-projection preserved).
- `grep`/read confirms `frame-intent` step 3 asks the altitude explicitly for concept-shaped / greenfield input and offers the suggested starting points (AC: ask altitude for concepts).
- `grep` confirms `frame-intent/SKILL.md:3`'s `description:` frontmatter no longer reads "Authors a capability or feature intent" — the shipped trigger blurb names the product altitudes / the open recognized set (AC: frontmatter no longer encodes the two-level ceiling).

**Approach:**
- In `scale-intake.md`, split Scale's two roles explicitly: keep leaf-projection as-is; reword the "default level" role to a suggestion (`app` greenfield concept → `product-vision`; `app` known feature → `feature`; `business-unit` → `product-strategy`/`capability`), overridable in one word.
- In `frame-intent/SKILL.md` step 3, replace the hard `feature`-at-`app` nudge with an explicit altitude question for concept-shaped/greenfield input.
- Widen `frame-intent/SKILL.md:3`'s `description:` frontmatter so the trigger blurb names the product altitudes (keep it adopter-clean — no RFC/ADR citation; mind the Kiro frontmatter limits — no unquoted `: ` in the description).

**Done when:** Scale suggests rather than stamps the altitude, the `frame-intent` `description:` no longer encodes the two-level ceiling, the leaf-projection role is provably untouched, and the T2 greps pass.

### T3: Seed the `product-vision` and `product-strategy` field blocks

**Depends on:** T1

**Tests:**
- `grep` confirms `intent-template.md` carries a `product-vision` field block with all nine elements (customer-shaped pitch, the change, job + struggling moment, who-by-circumstance, existing alternatives, narrowest wedge, demand evidence, tiered open assumptions, counter-metrics) (AC: vision block).
- `grep` confirms a `product-strategy` field block with its five elements (central challenge, guiding policy, coherent actions, problem/segment sequence, horizon) (AC: strategy block).
- `grep`/read confirms both blocks are marked **level-conditional** (filled only at that rung) and live in the single `intent-template.md` file with no new schema (AC: level-conditional, prompt-not-schema).

**Approach:**
- Add the two level-conditional field blocks to `frame-intent/assets/intent-template.md`, each prose/short-field, each with a one-line "fill only when `Level:` is this rung" cue and the template-not-schema posture preserved.
- Keep the prose adopter-clean — no RFC/backlog citation.

**Done when:** both blocks exist, are level-conditional, and the T3 greps pass.

### T4: Add the `market-existence` de-risk kind

**Depends on:** T1

**Tests:**
- `grep` confirms `de-risk-intent/SKILL.md` and `intent-model.md`'s level→kind mapping gain `product-vision`/`product-strategy` → `market-existence` (market desirability + viability) (AC: market-existence kind).
- `grep`/read confirms the prose states `market-existence` is **categorically distinct** from `feature → desirability` and uses a **different token** (the word `desirability` is not reused for the product-level bet) (AC: distinct token).
- `grep`/read confirms the kind reuses `kill-condition.md`'s pre-PMF qualitative bar and is framed as tested **once at the top** (AC: reuses qualitative bar).

**Approach:**
- Add the `market-existence` row to the level→kind mapping in `de-risk-intent/SKILL.md` (the `## Skill` intro mapping) and mirror it in `intent-model.md`'s two-consequences section.
- State the value+viability content and the distinct-token rule in prose; point at the existing qualitative-bar in `kill-condition.md` rather than adding a mechanism.

**Done when:** the `market-existence` row exists with a distinct token, reuses the qualitative bar, and the T4 greps pass.

### T5: Sibling-spawn detector + retroactive-parent affordance

**Depends on:** T1, T2

**Tests:**
- `grep`/read confirms `frame-intent` / `decompose-intent` carry the **sibling-spawn detector** — trips on the qualitative shippability test (won't reduce to one shippable slice; count is a signal not a threshold) and **offers** to frame the product parent, never blocks (AC: sibling-spawn detector).
- `grep`/read confirms the **retroactive-parent** affordance with its altitude-inference rule (architectural slices → `capability`; independent value bets → `product-vision`/`product-strategy`), back-linking via `Parent intent:`, naming the inferred altitude as user-correctable (AC: retroactive parent).
- `grep` confirms `recursive-decomposition.md` reads for any level above the leaf (no two-level ceiling wording) (AC: recursion reads for any level).

**Approach:**
- Add the offer-not-block sibling-spawn behaviour to `frame-intent/SKILL.md` and `decompose-intent/SKILL.md`, anchored on the existing shippability test.
- Add the retroactive-parent affordance (reusing the `Parent intent:` field and `decompose-intent`'s upward-feedback edge) with the explicit altitude-inference rule.
- Generalize any `recursive-decomposition.md` wording that implied a `capability | feature` ceiling.

**Done when:** both behaviours are prompt-only, the recursion reads for the new rungs, and the T5 greps pass.

### T6: Tracker-projection rows for the two rungs

**Depends on:** T1

**Tests:**
- `grep` confirms `tracker-projection.md`'s profile table gains rows for `product-vision` and `product-strategy`, each mapping to a higher/intervening tier — Jira Align Theme/Strategy tier; Linear → Initiative/label; `none` → markdown — with the existing `top (capability)` and `feature` rows preserved (AC: tracker rows, OQ1 default).

**Approach:**
- Add the two rows to the profiles table in `decompose-intent/references/tracker-projection.md` per the OQ1 default; keep the one-way / `none`-first-class framing.

**Done when:** the two rows exist at the higher/intervening tier and the T6 grep passes.

### T7: The `init-project` seam — fourth discovery source, by reference

**Depends on:** none

**Tests:**
- `grep` confirms `core/init-project/SKILL.md` stage 2 names `intent` / `frame-intent` as a **fourth** recognized discovery source alongside `research`, a PRD, and a `receive-brief` brief (AC: seam added).
- `grep`/read confirms the source is framed as an **optional upstream** ("when the `product-engineering` pack is installed", mirroring the `research`-pack "when installed" framing) so a `core`-only adopter reads it as optional, not a dangling reference (AC: by reference only; design-review R2).
- `grep`/read confirms `init-project` still imports nothing from `product-engineering` and still performs no discovery (the "Performing discovery / research yourself" anti-pattern and the "Adding a new top-level directory, or importing another pack's code" by-reference rule are intact, the latter naming `frame-intent` only as an upstream discovery shape it receives) (AC: by reference only, no discovery).

**Approach:**
- In `init-project/SKILL.md` stage 2 (and the matching anti-pattern bullet), add `intent` / `frame-intent` as a fourth recognized fed-in discovery shape, phrased as an optional upstream ("when the `product-engineering` pack is installed"), and document the `frame → de-risk → decompose` → `init-project` hand-off, by reference only.

**Done when:** the fourth source is named by reference, the no-discovery / no-import rules still hold, and the T7 greps pass.

### T8: Guides + READMEs touch-up

**Depends on:** T1-T7

**Tests:**
- `grep`/read confirms the four `product-engineering` guide pages describe the rungs and the Level-vs-Scale model: `explanation/the-intent-tree.md` (the two altitudes), `reference/intent-fields-and-modes.md` (recognized-set `Level` values + the two field blocks + the `market-existence` kind), `README.md` (overview names the altitudes), `how-to/shape-a-feature-intent.md` (the app-scale-greenfield-can-start-at-a-product-altitude note) (AC: user guides touched up).
- `grep`/read confirms `packs/product-engineering/README.md` names `product-vision` / `product-strategy` and states `Level` is an open recognized set decoupled from `Scale` — both the "same artifact at different levels" line and the `frame-intent` row updated (AC: pack README updated).
- `grep`/read confirms the core inception guide(s) name `intent` / `frame-intent` as a fourth `init-project` discovery source, framed as optional upstream — `docs/guides/_shared/how-to/run-a-full-inception.md` and the discovery-source list in `docs/guides/core/tutorials/start-a-new-project.md` (AC: core inception guide names the seam).

**Approach:**
- Extend the four `product-engineering` guide pages: the explanation with the two altitudes + Level/Scale orthogonality; the reference with the recognized-set values, the two field blocks, and `market-existence`; the index overview and the feature-shaping how-to with the altitude option for greenfield concepts.
- Update `packs/product-engineering/README.md`'s "same artifact at different levels" line and the `frame-intent` table row.
- Add the fourth discovery source to the core inception flow guide(s) where the source list / pack composition is taught, by reference and optional.
- Keep all guide / README prose adopter-clean (no RFC/ADR/backlog citation).

**Done when:** all four guide pages, the pack README, and the core inception guide(s) describe the rungs / the seam, and the T8 checks pass. (The pack README re-projects via `make build` in T9; guides and the pack README are repo-owned — no `build-self`.)

### T8b: Update the pack eval harnesses for the product altitudes

**Depends on:** T1, T2, T4, T6

**Tests:**
- `grep` confirms `frame-intent/evals/evals.json` no longer asserts the intent is level-tagged *only* `capability or feature` — the rubric recognises the open recognized set including `product-vision` / `product-strategy` (AC: eval harnesses recognise the altitudes).
- `grep`/read confirms `de-risk-intent/evals/` and `decompose-intent/evals/` need **no** change: the de-risk rubric describes de-risk currencies generically (no `desirability`/level token to widen) and the decompose rubric already reads "above feature level" for any level — this bullet is a *verification that no ceiling is encoded*, not a required edit (AC: eval harnesses; reviewer C1–C3).
- `grep` confirms the touched eval file(s) carry no `RFC-\d` / `ADR-\d` / `docs/rfc/` / backlog-anchor citation (they ship under `.apm/**`; adopter-clean cross-cutting check).
- `python tools/run-pack-evals.py --pack product-engineering --mode judge` smoke-check (Tier-B-light) does not regress on the existing queries after the rubric widening.

**Approach:**
- Widen the `frame-intent` `evals/evals.json` `expected_output` + rubric assertions so a `product-vision` / `product-strategy` intent is judged correct, not penalised. This is the only substantive eval edit; `eval_queries.json` is a trigger-phrase activation list with no level assertion to widen (add a product-altitude trigger query only if a near-miss surfaces).
- Read `de-risk-intent/evals/` and `decompose-intent/evals/` to confirm neither encodes the two-level ceiling; edit only if a ceiling is actually found (none expected — the `desirability` token lives in the skill bodies T4 edits, and the decompose rubric is already level-agnostic).
- Keep all eval prose adopter-clean.

**Done when:** `frame-intent`'s evals recognise the product altitudes, the de-risk/decompose evals are confirmed not to encode a ceiling (edited only if one is found), the judge smoke-check does not regress, and the T8b greps pass.

### T9: Version bumps, projection refresh, changelog

**Depends on:** T1-T8, T8b

**Tests:**
- `grep`/build confirms `product-engineering` `pack.toml` `[pack].version` and `.claude-plugin/plugin.json` `version` are bumped `0.5.1 → 0.6.0` in lockstep and `marketplace.json` re-aggregates the new version drift-clean (AC: version bump). `product-engineering` is **not** self-host-projected — there is no `.claude/skills/frame-intent` projection; the only drift target is `marketplace.json` via `make build`.
- `make build-self` refreshes the projected `.claude/skills/init-project/SKILL.md` for the `core` seam and bump; `git status` shows only the expected drift (AC: version bump / projection — core is projected).
- `grep` confirms the `[Unreleased] → Added` changelog entry exists (AC: changelog).

**Approach:**
- Bump `packs/product-engineering/pack.toml` + `.claude-plugin/plugin.json` to `0.6.0`; bump `packs/core/pack.toml` + `plugin.json` (patch/minor) for the seam; run `make build` (re-aggregate `marketplace.json`) and `make build-self` (refresh the projected `init-project`); confirm drift is only the expected version lines + the projected seam.
- Add the `[Unreleased] → Added` entry to `docs/product/changelog.md`, written for users.

**Done when:** both packs are bumped, `marketplace.json` and the `core` projection are drift-clean, and the changelog carries the entry.

### T10: Dogfood the rungs end-to-end

**Depends on:** T7, T9

**Tests:**
- Manual QA: run `frame-intent` on a greenfield product concept — record that it **offers `product-vision`** (not a silent `feature` stamp) and asks the altitude.
- Manual QA: run `de-risk-intent` on the resulting `product-vision` intent — record that it picks **`market-existence`** and reuses the qualitative bar.
- Manual QA: drive a concept that won't reduce to one slice — record that the sibling-spawn detector **offers** the product parent rather than emitting orphaned siblings.

**Approach:**
- Exercise the built skills the way a user would; capture the observed behaviour (what altitude was offered, what de-risk kind, the sibling-spawn offer) in the PR description.

**Done when:** all three runs are recorded and show the rungs route correctly.

## Rollout

Pure skill-prose / template / reference change. **Delivery:** ships with the next `product-engineering` release (`0.6.0`, T9) and the next `core` release (the seam bump); reversible by reverting the prose edits and the version bumps. No infrastructure, no external-system integration. **Deployment sequencing:** the model edits (T1–T4) land before the behaviours that sit on them (T5), and the version bump / projection refresh (T9) lands after all content edits so `build-self` and `marketplace.json` re-aggregation see the final tree. **Irreversible:** none — the migration is empty and additive (existing intents stay valid). Adopters pick up the new rungs on pack upgrade.

## Risks

- **Field-set prose drifts toward a schema or PM ceremony.** Mitigation: the prompt-sheet altitude and "apply what bites / an empty heading is a prompt" posture are spec Boundaries; the adversarial + quality reviewer passes check it.
- **An internal-governance citation leaks into shipped `.apm/**`.** Mitigation: the adopter-clean cross-cutting grep (a Construction test) and the `Never do` boundary; provenance lives in the spec/ADR only.
- **The two rungs blur** (users fill vision and strategy with the same content). Mitigation: distinct field sets + a one-line "vision = why it should exist; strategy = the path" cue; the open field lets a user collapse to one rung.
- **The no-engine-change assumption is wrong.** Mitigation: the RFC spike confirmed it against the shipped pack; T1 re-confirms the recursion needs no change before any behaviour is built on it.
- **The `core` seam reads as a dangling reference** to a pack a pure-engineering adopter never installs. Mitigation: it is named as an *optional upstream discovery shape*, by reference, consistent with `init-project`'s existing optional-source framing (`research` pack "when installed").

## Changelog

- 2026-06-23: initial plan (governance PR — ADR-0033 + this spec/plan). Implementation deferred to a separate PR; this plan describes that implementing PR.
- 2026-06-23: implementing-PR pre-EXECUTE review amendments — added T8b (pack eval-harness update, per the standing pack-eval-coverage rule); added the `frame-intent` `description:` frontmatter widening to T2; extended T1 to generalise the existing capability-rooted tree/consequences prose in `intent-model.md`; noted the migration AC is verified by T1. Reviewer findings C1–C4.
- 2026-06-23: EXECUTE complete — all 11 tasks (T1–T8, T8b, T9, T10) implemented in one PR; both packs bumped (`product-engineering` 0.6.0, `core` 0.4.15), `marketplace.json` + the projected `init-project` (both adapter roots) refreshed drift-clean, changelog `[Unreleased] → Added` entry added, T10 dogfood recorded in `notes/dogfood.md`. Post-EXECUTE review (adversarial + quality-engineer) clean after the status-flip / AC-check / anchor-refresh fixes and lifting the `frame-intent` sibling-spawn offer out of the anti-patterns section. **Bundled fix:** genericised all four pre-existing `RFC-0040` citations across the pack — `frame-intent` (SKILL.md + references/agentbundle-layout.md) and `align-value-stream` (SKILL.md + references/agentbundle-layout.md) — so the whole `product-engineering` pack is adopter-clean (the `align-value-stream` pair was folded in at the user's request rather than deferred).
