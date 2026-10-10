# Plan: product documentation for any repository

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (export boundary, version bump,
  no internal citations, eval update); `docs/guides/guide-source-model.md`
  (guide frontmatter, aliases); cross-pack handoff precedent
  `packs/architect/.apm/skills/architect-design/SKILL.md:47` and
  `packs/product-engineering/.apm/skills/discovery-loop/SKILL.md:144`; pack-test
  precedent `packs/product-documentation/tests/pack/test_product_documentation_pack.py`.
  Uncertainty: no test corpus of real non-pack repositories.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> execution observations belong in `notes/verification-ledger.md`.

## Approach

Write the content-rule tests first, against today's skill, which fails them.
Add the non-pack evals next, so coverage for a non-pack surface exists before
the skill contract changes (FEAT-0010 boundary). Then rewrite the skill in one
pass: the body, two new references, and the five existing references, so the
procedure and its references change together. Pack docs and the two other packs
follow and don't depend on each other. Release bookkeeping and the
real-invocation check close the work. The riskiest part is the surface-discovery
reference. It must be specific enough to choose sources and checks, without
becoming a page template per surface (FEAT-0010's non-goal).

Grounding: [`product-docs-authoring-survey.md`](../../product/research/product-docs-authoring-survey.md)
(F1–F13) for every new rule. The experience-design documentation genre sits in
`information-architecture/references/documentation-design.md`, the
`journey-mapping` documentation journey, and the 5-item docs rubric in
`design-review`. The skill hands off to these rather than copying them.

## Constraints

- ADR-0060: Diátaxis is a page contract, not a directory scaffold, and the pack ships no seeds.
- `packs/AGENTS.md`: no repository-only paths in shipped content. A content change is a patch bump in `pack.toml` and `plugin.json`. A non-cosmetic change updates that pack's eval harness — for all three packs (`information-architecture` and `ux-writing` evals included).
- `tests/roster/test_shipped_pack_manifests.py:153-170`: `user-guide-diataxis` pins `product-documentation ^0.1`.
- `guide-nav-baseline.toml`: every listed slug must still be generated, so the two baselined how-to slugs and `getting-started` keep their paths.

## Construction tests

**Integration tests:** none beyond per-task tests.

**Manual verification:** T7, the real invocation against a non-pack fixture repository (AC11).

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise: pack README, JOURNEY, guides, web card | T4 | `validate_guides.py`, guide lints, link check | AC13–AC15, AC21, AC22 |
| Current product truth: skill, references, evals | T1, T2, T3 | Pack tests green | AC1–AC10, AC19 |
| Release history: changelog and versions | T6 | Three `##` entries | AC16, AC17 |
| Reusable learning: survey | done before planning | `docs/product/research/product-docs-authoring-survey.md` | Linked from Approach |
| Cross-pack handoff truth | T5 | Search finds no `new-guide` in the AC12 region | AC12, AC20 |

## Design (LLD)

### Design decisions

- **One skill with two new references, not new skills.** Surface discovery and the journey are steps inside every mode. A separate skill would split one procedure in two. Traces to AC3, AC4. Owned by T2.
- **The journey has nine stages, and the docs set is audited per stage.** The stages merge the survey's F1/F2 stages with the `journey-mapping` documentation genre. Upgrade and contribute are added because that genre lacks them. Readers enter at any page, so the stages are a coverage map, not a reading order. Traces to AC5, AC6. Owned by T2.
- **Surface sections describe evidence and checks, never a page template.** Each section names what reveals the surface, what to read, which reference artifact it needs, and how to verify that artifact. Page shape stays in `page-contracts.md`. Traces to AC3, AC4. Owned by T2.
- **The pack README becomes a README variant.** A pack is the agent-context-pack surface: its README contract adds starter prompts and defers machine facts to the manifest. Traces to AC7. Owned by T2.
- **Destination discovery replaces hardcoded paths.** The order is: an explicit user destination, the repository's agent-guidance documentation map, the existing docs layout, then one question. Traces to AC1. Owned by T2.
- **Handoffs, not copies.** Navigation and landing-page structure go to `information-architecture`; the journey picture goes to `journey-mapping`; rendered-site critique goes to `design-review`'s documentation rubric; register for reference docs goes to `content-design`; UI strings and error text go to `ux-writing`. Each handoff carries an "if installed" guard. When the skill is absent, this skill applies its own contracts. Traces to AC8 and the spec's Always-do rule. Owned by T2.
- **The skill owns the upgrade and contribute artifacts.** Release notes, changelogs, migration guides, and contributing guides are user-facing journey pages, and no other catalogue skill writes them (`release-loop` only gathers a commit delta). Internal maintainer runbooks and CI docs stay out of scope. Traces to AC7, AC19. Owned by T2, T3.
- **Two guide how-tos with distinct tasks.** `author-product-docs.md` covers improving an existing doc set (audit, then retrofit). `write-a-guide.md` covers documenting one shipped feature. `use-author-product-docs.md` merges into the first and leaves an alias. Baselined slugs and their nav labels stay, so `guide-nav-baseline.toml` is unchanged. Traces to AC13, AC14. Owned by T4.

### Behavior & rules

Content rules that are design, pinned by content tests in T1 rather than criteria:

- FAQ content folds into task pages; a standalone FAQ page is an audit finding (survey F9).
- Never create `llms.txt` by default; plain Markdown sources and self-contained pages are the machine-reader baseline (F12).
- Verification by surface: doc tests or running examples for libraries, `--help` output for CLIs, the API contract for HTTP reference, and the config schema for services. A claim no check covered is labeled unverified (F5, F11).
- The documentation contract gains `surface` and `journey stage` fields.
- The conversation-first rule becomes "first runnable action": a request, command, or code sample within the first 120 words.

Owned by T2.

## Tasks

### T1: Content-rule tests red against today's skill

**Depends on:** none
**Touches:** `packs/product-documentation/tests/pack/test_product_documentation_pack.py`
**Tests:**
- Forbidden-path scan over `SKILL.md` and `references/*.md` for the five AC1 strings (AC1).
- Description surface words (AC2).
- Exact-heading scan of `surface-discovery.md` for the 7 surfaces and their four labels (AC3, AC4).
- Stage scan of `docs-journey.md` (AC5).
- `SKILL.md` audit/retrofit text names the four row states (AC6).
- Exact-heading scan of `page-contracts.md` for the 8 headings and their four part labels (AC7).
- Handoff-guard scan: every `SKILL.md` line naming one of the five skills carries "if installed" (AC8).
- Eval JSON counts, case ids, fixture paths, and the release-notes flag (AC9, AC10, AC19).
- Content pins: FAQ rule, `llms.txt` rule, first-runnable-action rule, and the `surface` and `journey stage` fields of the documentation contract.
- Replace the `docs/guides/` anti-pattern pin with a pin on the generic rule (user-facing docs never go into a maintainer-only tree). Keep the "This skill is portable" pin.

stub: the new test functions above, collected and failing.
**Done when:** `python3 -m pytest packs/product-documentation/tests/pack -q` collects the new tests, they fail on today's skill, and the scope and seeds tests still pass.

### T3: Non-pack evals

**Depends on:** T1
**Touches:** `.../author-product-docs/evals/eval_queries.json`, `.../evals/evals.json`, `.../evals/files/`
**Tests:**
- The T1 tests for AC9, AC10, and AC19.
- Eval case 1's `expected_output` and assertions state the generic audience rule; the unused `fixture_weak_catalogue_misdirected.md` is deleted.
- A scan of every file under `evals/` finds none of the five AC1 strings (pinned in the pack tests).
**Done when:** those tests pass.

### T2: Generic skill body and references

**Depends on:** T1, T3
**Touches:** `packs/product-documentation/.apm/skills/author-product-docs/SKILL.md`, `.../references/*.md`
**Tests:** the T1 tests for AC1–AC8 and the content pins.
**Approach:**
- Write `surface-discovery.md` and `docs-journey.md` first. The body's new steps cite them.
- In `artifact-model.md` and `repository-ownership.md`, replace path tables with roles and the destination discovery order. Remove the catalogue-specific trees.
- Make `rendered-verification.md` say "the repository's docs build", not `web/`/`docs-site/`, and add the surface checks.
- Run self-host so the projected skill exists for T7.
**Done when:** the T1 tests pass, `agentbundle catalogue lint --root . --deep` passes, and self-host has written the projections.

### T4: Pack docs describe any-repository use

**Depends on:** T2
**Touches:** `packs/product-documentation/README.md`, `JOURNEY.md`, `pack.toml` (description, keywords, first-value), `.claude-plugin/plugin.json` (description), `guides/product-documentation/**`, `guides/README.md`, `docs/guides/how-to/author-product-documentation.md`, `web/src/content/packs/product-documentation.md`
**Tests:**
- `python3 tools/validate_guides.py guides/`, `python3 tools/check-guide-index.py`, and `python3 tools/lint-guide-titles.py` exit 0.
- The how-to directory listing and the alias (AC13, AC14).
- No `validate_guides.py` or `build-site.py` under `guides/product-documentation/` (AC15).
- `how-to/author-product-docs.md` keeps `Write a how-to guide explaining how to` in exactly one Markdown blockquote that sits outside any aside, the shape `web/src/test/e2e/docs-asides.spec.ts` pins.
- Every relative link in the touched pages resolves, including the repointed link in `docs/guides/how-to/author-product-documentation.md`.
- The AC21 surface-word check over the four user-facing descriptions.
- The AC22 inbound-link search and relative-link resolution.
**Done when:** those checks pass.

### T5: Cross-pack pointers name author-product-docs

**Depends on:** none
**Touches:** `packs/experience-design/.apm/skills/information-architecture/**`, `packs/product-engineering/.apm/skills/ux-writing/**`, `packs/product-engineering/DESIGN.md`, both packs' `pack.toml` and `plugin.json`
**Tests:** the AC12 search; every line in the AC12 region that names `author-product-docs` carries "if installed"; the AC20 eval query; both packs' own test suites.
**Done when:** those checks pass.

### T6: Release bookkeeping and projections

**Depends on:** T2, T3, T4, T5
**Touches:** `packs/product-documentation/pack.toml`, `.claude-plugin/plugin.json`, `docs/product/changelog.md`, generated projections
**Tests:** AC16 and AC17 reads; the AC18 command list; `FORCE=1 make build-self` regenerates `marketplace.json`.
**Done when:** every AC18 command exits 0.

### T7: Real invocation against a non-pack repository

**Depends on:** T2
**Tests:** manual QA (AC11). Build a throwaway CLI fixture repository outside the worktree: an argparse entry point, a `pyproject.toml` `[project.scripts]` entry, and a README that leads with a flag dump. Give a fresh subagent only the projected skill files and the request "audit this project's docs". Record whether it names the CLI surface, opens the parser file before returning its report, and returns a nine-row stage report.
**Done when:** `notes/verification-ledger.md` holds the transcript, showing the surface identification, the parser-file read before the report, and all nine stage rows, with the verdict.

## Rollout

- **Delivery:** big bang, through a pack patch release. Reverting the PR reverts it.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** none.

## Risks

- The surface reference could grow into per-surface templates. Mitigation: the design rule above, plus review against FEAT-0010's non-goal.
- An LLM-judged eval may score the new non-pack cases poorly at first. It runs in `pack-evals.yml`, which is not a required gate. A failure is a follow-up signal, not a blocker.

## Changelog

- 2026-10-10: spec approved by eugenelim
- 2026-10-10: plan approved by eugenelim
