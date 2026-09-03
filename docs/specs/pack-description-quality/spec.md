# Spec: pack-description-quality

- **Status:** Shipped (§ Acceptance criteria's register anchor `credential-brokers-description-rewrite` was closed by commit 1bdf7514d; not a supersession — every decision here stands)
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none — this spec changes no published schema or adapter contract.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light (work-loop). No risk trigger fired. Checked and did NOT fire:
structural/public-interface — the cap lands in `tools/lint-pack-descriptions.py`,
a repository-only policy lint. Nothing under `packages/agentbundle/` changes, so
no adopter-facing validation contract moves and no adopter pack can newly fail
`agentbundle validate` or `agentbundle catalogue lint`.
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

Success: every pack description leads with the job the adopter accomplishes, and
the standard that says so is written down where authors will find it.

**A length check is not that standard, and this spec does not pretend otherwise.**
The defect is *shape* — inventory-first openings, insider vocabulary, cross-pack
references, provenance dumps, internal paths — and none of those is a length. A
799-character component inventory would pass any ceiling and still be wrong. The
lint here exists only to stop the field running away again (it reached 1122
characters ungoverned); the authoring standard carries the actual bar.

### The two-audience distinction this spec depends on

`description` means two different things in this repo, and the change must not
conflate them:

| Field | Audience | Job | Governed by |
| --- | --- | --- | --- |
| **Skill/agent** `description` (frontmatter) | The *model* | Drives **activation** — the agent decides whether to load the skill | `lint_packs.Constraints.description_max`, a strictest-cap snapshot of `contracts/target-vocab.toml` (a technical ingest cap, 1024) |
| **Pack** `[pack].description` | A *human* | **Display copy** in a marketplace browser, catalogue listing, or CLI output | `catalogue-authoring-standards.md` § 2 (the bar) + a repo-only drift backstop, both added by this spec |

Keyword density is *correct* in a skill description and *noise* in a pack
description. Pack discoverability is already carried by the separate
`[pack].keywords` and `[pack].categories` fields, so shortening the description
costs no findability.

## Acceptance Criteria

- [x] AC1. `guides/_shared/reference/catalogue-authoring-standards.md` § 2
      carries the authoring standard: the outcome-first shape and the named
      anti-patterns. **This is the quality bar.**
- [x] AC1b. `tools/lint-pack-descriptions.py` is a *drift backstop*, not the
      quality bar: it refuses a `[pack].description` past `MAX_DESCRIPTION`
      (800 — more than double the longest shipped description, so it fires only
      on an outlier), names the pack and points at the standard, and is wired
      into both the local gate chain and `build-check.yml`. A test asserts the
      backstop stays clear of real copy.
- [x] AC2. The new check uses its own constant and does **not** read, reuse, or
      mutate the target-derived skill/agent cap. A test asserts the two are
      independent.
- [x] AC3. Nothing under `packages/agentbundle/` changes — not
      `pack.schema.json`, not the packaged `lint_packs`. Both run against
      adopter catalogues, so neither may carry this repository's house style.
- [x] AC4. Every pack in `packs/` has a description inside the backstop, and every
      rewritten one opens on an adopter outcome rather than a component
      inventory. One pack is deliberately not rewritten —
      `credential-brokers`, whose tree the catalogue-curation guard protects
      with no carve-out and whose description is already inside the backstop at
      241 chars (deferred: credential-brokers-description-rewrite — closed 2026-09-03 by 1bdf7514d).
- [x] AC5. No pack description contains a cross-pack reference, a bare component
      inventory as its opening clause, or an internal file path.
- [x] AC6. For every pack whose description changed, `pack.toml`,
      `packs/<pack>/.claude-plugin/plugin.json`, and the root
      `.claude-plugin/marketplace.json` all carry the identical new string.
- [x] AC7. No pack version is bumped, and every pack's version remains identical
      across `pack.toml`, `plugin.json`, and `marketplace.json`. See
      Assumption 2 for why a bump is not warranted here.
- [x] AC8. `make build-check` and the `agentbundle` test suite pass.
- [x] AC9. `docs/product/changelog.md` records both the description rewrite and
      the new lint under `[Unreleased]`. `packages/agentbundle/CHANGELOG.md` is
      deliberately untouched — nothing in that package changed. This repo has no
      root `CHANGELOG.md`.

## Boundaries

### Always do

- Verify the three-file description sync empirically (edit → `make build-self` →
  re-read) rather than trusting either the recipe name or prior assumption.
- Keep each rewritten description's first sentence standalone and ≤ ~90 chars.

### Never do

- **Never touch a skill or agent `description`.** Those drive activation; this
  spec is display copy only. A shortened skill description is a regression.
- Never put the backstop anywhere inside `packages/agentbundle/` — neither
  `pack.schema.json` (adopter-facing via `agentbundle validate`) nor the packaged
  `lint_packs` (adopter-facing via `agentbundle catalogue lint`). An editorial
  rule in either converts our house style into someone else's build break. It
  belongs in `tools/`, which runs only on this repository's build.
- Never drop a `keywords` or `categories` entry to compensate for shortened prose.

## Testing strategy

- **AC1–AC3 — TDD.** `tools/test-lint-pack-descriptions.py`: a pack fixture past
  the backstop produces a finding; one exactly at it does not; absent, malformed,
  and non-pack directories are ignored; the backstop is asserted distinct
  from the target-vocab ingest cap; the in-tree catalogue satisfies its own lint;
  and both exit codes are exercised. Backed by a real-tree negative control —
  restoring `core`'s 439-char description makes the lint exit 1, and reverting it
  returns exit 0, so the gate is proven capable of failing.
- **AC4–AC5 — goal-based.** `Done when:` the backstop exits clean across `packs/`
  and every rewritten description satisfies the § 2 shape on review. AC5 is a
  human-review criterion by construction — no length check can assert it.
- **AC6–AC7 — goal-based.** `Done when:` a script confirms the three files agree
  per pack, and `make build-check` passes.
- **AC8 — goal-based.** `Done when:` `make build-check` and `python3 -m pytest
  packages/agentbundle/ -q` both exit 0.

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
