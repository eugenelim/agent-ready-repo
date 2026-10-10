# Spec: Core impact-evidence routing

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0079
- **Brief:** none
- **Discovery:** `docs/product/intents/CAP-0011-optional-code-intelligence-composition.md`
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

Core adopters whose agents plan a change, decide a review finding, or trace a bug get one named, tool-neutral route for caller, dependents, and impact questions: Core's `repository-exploration` skill, which uses an already-exposed capability only when it fits and otherwise answers from repository search. An installed code-intelligence provider is reached through that route when a workflow needs decision evidence, and `repository-exploration`'s description states that decision-bound trigger without naming any provider.

## What Changes

- `work-loop` PLAN step 5 points dependents questions for a rename, signature change, removal, or refactor at `repository-exploration` — `packs/core/.apm/skills/work-loop/SKILL.md`.
- `work-loop` DECIDE's execution-path check drops "grep for callers" for tool-neutral wording that names `repository-exploration` as the route for caller evidence — same file.
- `bug-fix` step 6 points caller and dependents tracing at `repository-exploration`, and its "same class of bug" question says "search" instead of "grep" — `packs/core/.apm/skills/bug-fix/SKILL.md`.
- `repository-exploration`'s description names a pending decision as its trigger, drops the provider's trigger wording, and says the calling workflow owns planning, building, and fixing — `packs/core/.apm/skills/repository-exploration/SKILL.md`.
- `repository-exploration` gains activation evals and is registered in Core's activation-eval allowlist — `evals/eval_queries.json`, `packs/core/pack.toml`.
- Behavior evals gain one decision-bound case each for `repository-exploration`, `work-loop`, and `bug-fix`.
- The consumer-boundary test allows the name in `work-loop` and `bug-fix` only inside the three sentences AC-0001–AC-0003 quote — `packs/core/tests/pack/test_exploration_consumer_boundary.py`.
- Two `new-spec` eval prompts stop saying "code-intelligence pack" — `packs/core/.apm/skills/new-spec/evals/evals.json`.
- The shipped exploration spec's VI-0008 entry (the consumer-boundary name scan) carries a pointer to this narrowing; its AC-0008 ceremony ban is unchanged — `docs/specs/optional-intelligence-exploration-composition/spec.md`.
- Core moves to 3.0.2 with a changelog entry; projections are regenerated.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Adopters read which workflows route impact questions to exploration. | `packs/core/README.md` § Repository exploration | Core pack maintainers | `test_impact_evidence_routing.py` README assertion; section read whole | The section names `work-loop` and `bug-fix` as callers that route caller, dependents, and impact questions to the skill. |
| Decision rationale | The name-absence check in the shipped VI-0008 scan is narrowed by owner decision on 2026-10-10; AC-0008's ceremony ban is unchanged. | This spec, plus a pointer under VI-0008 in `docs/specs/optional-intelligence-exploration-composition/spec.md` | eugenelim | Pointer present; spec-status lint clean | A reader of the shipped VI-0008 reaches this spec in one link. |
| Release history | Non-cosmetic Core content changes. | `docs/product/changelog.md` | Core release maintainer | Matching pack and plugin versions; a dated `## [core][3.0.2]` entry directly beneath `[Unreleased]` with a `Highlights` disposition | Entry present and outcome-led. |

## Agent Rules

### Always do

- Edit `.apm/` sources only, then run `agentbundle catalogue self-host --root . --write`.
- Phrase every mention of `repository-exploration` in a consuming procedure as an optional route, with repository search still a valid answer.
- Keep `repository-exploration`'s no-provider path unchanged: it still answers from repository-native evidence when no exposed capability fits.

### Ask first

- Naming `repository-exploration` in any consuming file other than `work-loop` and `bug-fix`, or in any sentence other than the three that AC-0001, AC-0002, and AC-0003 quote.
- Changing `repository-grounding`'s description.
- Changing any `repository-exploration` procedure step, evidence-record field, or locator-reader rule.

### Never do

- Name the code-intelligence pack, its path, its skill, or Wicked Estate in any shipped Core file, and never edit `packs/code-intelligence/`.
- Add a gate, reviewer, required phase, workflow state, provider setup, provider call, index-freshness step, or provider fallback branch to `work-loop` or `bug-fix`.
- Copy the risk-triggers block out of `work-loop/SKILL.md`.
- Add an eval that scores whether an agent picks a provider skill or `repository-exploration` for a bare caller or dependents question. `docs/specs/native-provider-selection-validation/spec.md` excludes unaided provider selection, and CAP-0011 holds it as future research.
- Add a dependency, module, or top-level directory.

## Testing Strategy

- **Workflow routing (AC-0001, AC-0002, AC-0003):** goal-based. A pack test reads each source file, flattens whitespace, and asserts the quoted sentence is present and the replaced grep wording is absent; prose has no runtime to drive.
- **Narrowed ban (AC-0004):** TDD. The consumer-boundary test changes first; a mutation (an extra, unquoted mention) proves it reds.
- **Description route (AC-0005):** goal-based. A pack test reads the frontmatter description from the `.apm/` source only; projection parity is AC-0011's job.
- **Provider-name absence (AC-0006):** goal-based. A pack test scans every regular file under `packs/core/` outside `packs/core/tests/`.
- **Evals (AC-0007, AC-0008):** goal-based. The existing eval-shape and balance tests plus pin updates, and a pack test for the decision markers and fixed phrase.
- **Release and projection (AC-0009, AC-0010, AC-0011):** goal-based. Version parity, changelog placement, the shipped-spec pointer, `catalogue verify`, and a clean self-host on the committed tree.

## Acceptance Criteria

- [x] **AC-0001.** `work-loop/SKILL.md`'s DECIDE execution-path check contains no "grep for callers" and contains this sentence fragment, compared after collapsing whitespace: "trace the entry point or find its callers; `repository-exploration` can gather that caller evidence when one search will not settle it."
- [x] **AC-0002.** `work-loop/SKILL.md`'s PLAN step 5 contains this sentence, compared after collapsing whitespace: "When the touch list depends on what calls or depends on the code you change — a rename, signature change, removal, or refactor — you may ask `repository-exploration` for that dependents evidence; it answers from repository search when no better tool fits."
- [x] **AC-0003.** `bug-fix/SKILL.md`'s step 6 contains no "Grep for" and contains this sentence, compared after collapsing whitespace: "When the trace needs callers or dependents that one search will not settle, you may ask `repository-exploration` for them with attribution."
- [x] **AC-0004.** In `test_exploration_consumer_boundary.py`, the allowlist of text that may name `repository-exploration` is exactly the three quotations in AC-0001, AC-0002, and AC-0003, each tied to its file. The name ban still covers the other seven subject files, every provider-ceremony phrase ban still covers all nine, and the test fails when an unquoted mention is added to `work-loop` or `bug-fix`.
- [x] **AC-0005.** `repository-exploration`'s description contains "pending decision", "The caller keeps the decision", "no provider is required", "repository-grounding", and "Do NOT use it to plan, build, or fix", and contains none of these, case-insensitively: "blast radius", "what calls", "what depends on", "what breaks", "callers and callees", "find callers".
- [x] **AC-0006.** No regular file under `packs/core/` outside `packs/core/tests/` contains, case-insensitively, `wicked estate`, `wicked-estate`, `code-intelligence pack`, `code-intelligence skill`, `` `code-intelligence` ``, or `packs/code-intelligence`.
- [x] **AC-0007.** `repository-exploration` is listed in `pack.toml` `[pack.evals].skills` and `test_eval_allowlist_has_balanced_activation_sets` passes with its `evals/eval_queries.json` registered. Every `should_trigger: true` query contains, as a whole word and case-insensitively, one of: `plan`, `planning`, `rename`, `renaming`, `refactor`, `refactoring`, `remove`, `removing`, `removal`, `fix`, `fixing`, `finding`, `decide`, `deciding`, `decision`, `approve`, `approving`, `safe`. The marker check rejects "Using the supplied fixture, list everything that depends on parse()". The `should_trigger: false` set includes one query that is a `should_trigger: true` query in `bug-fix/evals/eval_queries.json` and one query beginning with `Implement`. No query begins, case-insensitively, with `what calls`, `what depends on`, or `what breaks if`.
- [x] **AC-0008.** `repository-exploration`, `work-loop`, and `bug-fix` each gain one behavior eval in `evals/evals.json` whose prompt contains "No language-server, code-graph, or MCP capability is exposed." and whose assertions include one containing "repository search".
- [x] **AC-0009.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` both carry version `3.0.2`, and the first versioned heading directly beneath `## [Unreleased]` in `docs/product/changelog.md` is `## [core][3.0.2] — ` followed by a `YYYY-MM-DD` date, with a `### Highlights` subsection.
- [x] **AC-0010.** In `docs/specs/optional-intelligence-exploration-composition/spec.md`, the text between its VI-0008 entry and its VI-0009 entry contains, after collapsing whitespace, each of `core-impact-evidence-routing/spec.md`, `name-absence`, `` `work-loop` ``, `` `bug-fix` ``, and `AC-0008 ceremony criterion is unchanged`.
- [x] **AC-0011.** On the committed tree, `agentbundle catalogue verify --root .` passes and `agentbundle catalogue self-host --root . --write` leaves `git status --porcelain` empty.

## Follow-ons

none

## Assumptions

- Product: an agent asked a bare caller or dependents question with no decision attached may still match a provider skill's description; this change sharpens only the decision-bound route, and the CAP-0011 owner (eugenelim) holds the bare-question case as future research. FEAT-0032's guided sessions teach the provider skill by name, so this description change does not alter what those sessions teach.
