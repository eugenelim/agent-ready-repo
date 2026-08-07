# Spec: pack-description-quality

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none — this spec changes no published schema or adapter contract.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light (work-loop). No risk trigger fired. Checked and did NOT fire:
structural/public-interface — the cap lands in `build/lint_packs.py` (a
catalogue-build lint), NOT in `pack.schema.json`, so no adopter-facing validation
contract changes and no adopter pack can newly fail `agentbundle validate`.
Lean fill: Objective + Acceptance Criteria + Boundaries + Testing Strategy +
Assumptions (the last three earn their place via the two-audience distinction and
the three-file sync obligation). -->

## Objective

A person scanning a marketplace or catalogue listing should be able to tell what a
pack is *for* from its description alone, in one screen, without repo-insider
vocabulary. Today they cannot: our 22 pack descriptions run to a median of 227
characters and a maximum of 1122, against a 177-character median in the reference
marketplace we are listed alongside; six exceed 400 characters, and the worst read
as component inventories rather than descriptions.

Success: every pack description leads with the job the adopter accomplishes, fits
inside a mechanically-enforced ceiling, and a regression cannot land silently.

### The two-audience distinction this spec depends on

`description` means two different things in this repo, and the change must not
conflate them:

| Field | Audience | Job | Governed by |
| --- | --- | --- | --- |
| **Skill/agent** `description` (frontmatter) | The *model* | Drives **activation** — the agent decides whether to load the skill | `lint_packs.Constraints.description_max`, a strictest-cap snapshot of `contracts/target-vocab.toml` (a technical ingest cap, 1024) |
| **Pack** `[pack].description` | A *human* | **Display copy** in a marketplace browser or catalogue listing | Nothing today — this spec adds it |

Keyword density is *correct* in a skill description and *noise* in a pack
description. Pack discoverability is already carried by the separate
`[pack].keywords` and `[pack].categories` fields, so shortening the description
costs no findability.

## Acceptance criteria

- [x] AC1. `build/lint_packs.py` refuses a `[pack].description` longer than
      `_PACK_DESCRIPTION_MAX` (400), with a finding naming the pack, the actual
      length, and the ceiling.
- [x] AC2. The new check uses its own constant and does **not** read, reuse, or
      mutate `Constraints.description_max` — the target-derived skill/agent cap.
      A test asserts the two are independent.
- [x] AC3. `pack.schema.json` is unchanged. A test asserts no `maxLength` was
      added under `properties.pack.properties.description`.
- [x] AC4. Every pack in `packs/` has a description that is ≤400 characters and
      whose first sentence names an adopter outcome, not a component inventory.
- [x] AC5. No pack description contains a cross-pack reference, a bare component
      inventory as its opening clause, or an internal file path.
- [x] AC6. For every pack whose description changed, `pack.toml`,
      `packs/<pack>/.claude-plugin/plugin.json`, and the root
      `.claude-plugin/marketplace.json` all carry the identical new string.
- [x] AC7. No pack version is bumped, and every pack's version remains identical
      across `pack.toml`, `plugin.json`, and `marketplace.json`. See
      Assumption 2 for why a bump is not warranted here.
- [x] AC8. `make build-check` and the `agentbundle` test suite pass.
- [x] AC9. Both changelogs record the change under `[Unreleased]`:
      `docs/product/changelog.md` (the user-visible description rewrite) and
      `packages/agentbundle/CHANGELOG.md` (the new lint ceiling). This repo has
      no root `CHANGELOG.md`.

## Boundaries

### Always do

- Verify the three-file description sync empirically (edit → `make build-self` →
  re-read) rather than trusting either the recipe name or prior assumption.
- Keep each rewritten description's first sentence standalone and ≤ ~90 chars.

### Never do

- **Never touch a skill or agent `description`.** Those drive activation; this
  spec is display copy only. A shortened skill description is a regression.
- Never add the ceiling to `pack.schema.json` — that schema validates adopter
  packs via `agentbundle validate`, and an editorial rule there converts our house
  style into someone else's build break.
- Never drop a `keywords` or `categories` entry to compensate for shortened prose.

## Testing strategy

- **AC1–AC3 — TDD.** Unit tests in the `agentbundle` build test suite: a pack
  fixture over the ceiling produces a finding; one at the ceiling does not; the
  pack ceiling and `Constraints.description_max` are asserted independent; a test
  reads `pack.schema.json` and asserts the absence of a description `maxLength`.
- **AC4–AC5 — goal-based.** `Done when:` a repo-wide script reports every pack
  ≤400 chars, and the lint added in AC1 exits clean across `packs/`.
- **AC6–AC7 — goal-based.** `Done when:` a script confirms the three files agree
  per pack, and `make build-check` passes.
- **AC8 — goal-based.** `Done when:` `make build-check` and `python3 -m pytest
  packages/agentbundle/tests/ -q` both exit 0.

## Assumptions

1. ~~The root `.claude-plugin/marketplace.json` is regenerated from per-pack
   `plugin.json` by `make build-self`.~~ **Confirmed empirically in T3.** Editing
   the 22 per-pack `plugin.json` files and running `make build-self` rewrote
   exactly 21 lines of `.claude-plugin/marketplace.json` (one per shipped pack;
   `_example` is not listed), all of them `description` values and nothing else.
   The prior session note claiming `build-self` syncs none of the three files is
   wrong for `description` — it holds only for `version`, which this change does
   not touch. `build-self` refuses to run against a dirty tree, so the sequence
   is: edit → commit → `make build-self` → commit the regenerated marketplace.
2. ~~A description change is adopter-visible and therefore earns a patch bump.~~
   **Resolved during T4 — no version bump.** Three findings moved this:
   - No gate requires one. No test pins a real catalogue pack version (the
     version assertions in the suite are all synthetic fixtures).
   - The goal of this change is the *marketplace listing*, and
     `.claude-plugin/marketplace.json` republishes on every merge to `main`
     independent of pack version — so the new copy reaches a browsing adopter
     with no bump at all.
   - Semver tracks functional content. No skill, agent, hook, command, or seed
     changed; this is display metadata *about* the pack.

   The residual cost is that an already-installed pack keeps its old description
   locally until its next real release — cosmetic only, since no behaviour
   differs. Bumping 21 packs to fix that would have tripled the diff for no
   functional gain, against the repo's *limit the diff* rule.

## Out of scope (deferred)

- **Codex 2% skill-description budget.** The catalogue ships 122 skills totalling
  ~72,000 description characters (~18k tokens); Codex truncates skill descriptions
  to a ~2% context budget, so the longest descriptions — long precisely to drive
  activation — are cut hardest. Real, measured, and a *skill*-description concern,
  not a pack-description one. Recorded in `workspace.toml [backlog].open`.
