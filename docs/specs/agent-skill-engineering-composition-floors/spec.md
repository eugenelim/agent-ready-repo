# Spec: Agent Skill Engineering Composition Floors

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`RFC-0097`](../../rfc/0097-agent-skill-engineering.md);
  [`Agent Skill Engineering Languages and Execution`](../agent-skill-engineering-languages-and-execution/spec.md)
- **Brief:** docs/product/briefs/agent-skill-engineering.md
- **Discovery:** none
- **Contract:** none — the foundation semantic provider request/response contract is unchanged; this slice populates fields it already declares.
- **Shape:** mixed

> **Hard dependency.** The corpus and languages slices are Shipped. This slice
> admits four of the eleven taxonomy leaves reserved for runtime composition and
> leaves the remaining seven runtime profiles to its successor.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An agent-skill author asking how to compose a skill with subagents, hooks, or a
plugin package gets portable guidance that separates a capability floor from
runtime-specific behavior, and gets it without being told a capability is
supported when nobody checked. The corpus carries three portable composition
floors and one runtime profile — Claude Code — whose every capability row names
a first-party source, the date it was retrieved, the product version that
exposed it, and a lifecycle state that the router reports rather than averages
away. A claim nobody could verify reads as `experimental`; a claim whose
verification window elapsed reads as `stale` and returns provenance instead of
guidance; a capability that is genuinely absent reads as `unavailable` and is
recorded as an enterprise delta rather than a gap.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | The pack README states which topics are governed and what the pack does not yet cover; both change | `packs/agent-skill-engineering/README.md` | this spec | Shipped-statement agreement test over the admitted set | README states sixteen governed topics and no longer claims composition floors are later-slice work |
| Current product truth | Topology accounting, admitted-versus-absent partition, and retrieval measurement all move | `packs/agent-skill-engineering/tests/fixtures/` | this spec | Partition test; re-measured retrieval and negative records | Every fixture digest matches the tree it describes |
| Current architecture | The planned architecture names composition floors and runtime profiles as unimplemented | `docs/architecture/agent-skill-engineering.md` | this spec | Section names the shipped floors, the pilot profile, and what stays `PLANNED` | Document states which slice-3 surfaces exist and which remain |
| Interface compatibility | `profile_provenance` and `stale-profile` are declared but unreachable | `packs/agent-skill-engineering/tests/fixtures/provider-contract.json` and the provider suite | this spec | Provider-contract test reaching both | Both are exercised by a case that fails if the wiring is removed |
| Release history | Pack behavior changes for installers | `docs/product/changelog.md`, `pack.toml`, `.claude-plugin/plugin.json` | this spec | Version bump in lockstep; topmost pack entry | `0.3.0` to `0.4.0` in both manifests, one changelog entry |
| Maintainer procedure | Slice 3b needs the ledger's field contract and the redirect rule | this spec's `qa.md` | this spec | QA record naming the ledger schema and its probe boundary | `qa.md` records the ledger contract, the residual, and gate results |
| Reusable learning | Capture gates fire at `spec-approved` and `plan-locked` | `project-knowledge` producer profile | work-loop | Capture receipts, or a recorded unavailability | Receipts exist or `project-knowledge unavailable` is recorded |

## Boundaries

### Always do

- Record a capability claim's source identity as the URL that served the content
  after every redirect, together with the date it was retrieved and the product
  version or last-updated date the source exposed, or the literal `none exposed`.
- Classify a capability honestly against its evidence. A claim with a source but
  no passing probe is `experimental`, never `verified`.
- Keep the three composition-floor topics free of runtime-specific behavior, and
  keep runtime-specific behavior inside the profile topic.
- Re-measure the retrieval record and the generic-negative record after admission
  moves the binding digests, rather than re-stamping either.
- State degradation wherever the floor names a capability a runtime may lack.

### Ask first

- Before admitting any leaf beyond the four this spec names.
- Before changing the closed set of five unavailable authoring modes.
- Before adding a dependency to make a predicate categorical, including a
  CommonMark parser.
- Before changing the fixed size of the forty-case generic-negative set.

### Never do

- Never advertise a capability as supported on evidence weaker than `verified`.
- Never let a profile's roll-up be a declared string that no test recomputes from
  the rows beneath it.
- Never cite this repository's own paths, specs, ADRs, RFCs, acceptance-criterion
  identifiers, or `workspace.toml` inside shipped pack content.
- Never introduce a new top-level directory, a new module boundary, or a new
  runtime dependency for this slice.
- Never write a capability claim for a runtime this slice does not profile, and
  never infer one runtime's behavior from another's.

## Testing Strategy

- **Topic admission, basis fields, and source parity: TDD.** The admission record
  and the shipped projection are two representations of one fact set, so the
  invariant compresses to an equality and a wrong implementation is detectable.
- **Lifecycle-state transitions and the profile roll-up: TDD.** The state
  function and the roll-up are pure over `(rows, reference_date)`. Tests drive
  synthetic dates so the suite stays deterministic; a date-dependent assertion
  against the wall clock would redden unrelated work on a timer.
- **Router behavior per lifecycle state: TDD, at integration surface.** Each
  state's router response is observable only across the provider seam, so the
  check drives the contract rather than the state function.
- **Retrieval precision, recall, and the negative set: goal-based check.** The
  existing gate recomputes the measurement from a recorded independent run; this
  slice re-measures and the same thresholds apply unchanged.
- **The Claude Code capability probes: visual / manual QA.** Each probed row
  records the gesture and the observed outcome, because the evidence is runtime
  behavior rather than a value a unit test can assert.
- **Shipped-statement agreement: goal-based check.** A scan over shipped surfaces
  compared against the admitted set.

## Acceptance Criteria

- [ ] **AC1 — The four named leaves are admitted with a declared basis.**
  `skills-and-subagents-common-floor`, `hooks-common-floor`,
  `plugin-package-common-floor`, and
  `claude-code-skills-subagents-hooks-and-plugins` are admitted topics. Each
  carries every field its declared basis requires, and the taxonomy stays at 36
  leaves with the absence register reduced to 20. Each admitted topic carries the
  eight required sections. A leaf appears in the admitted set or the absence
  register, never both and never neither.

- [ ] **AC2 — The composition floors carry no runtime-specific behavior.** Each
  of the three floor topics states capability questions and a conservative
  default without naming any runtime's event names, matcher semantics,
  configuration scopes, output protocols, or file paths. A reader following a
  floor topic alone is told which behaviors are runtime-owned and that the floor
  does not establish them. The scan that establishes this resolves each forbidden
  runtime identifier by name, so one identifier's absence cannot be satisfied by
  another's.

- [ ] **AC3 — Every capability row RFC-0097 requires of Claude Code exists.** The
  ledger carries a row for each of the seven capabilities the profile table
  assigns Claude Code: skill preloading versus invocation, isolated subagent
  context, worktree isolation, nesting limits, component-scoped hooks,
  plugin-agent restrictions, and managed hook policy. A missing required row
  makes the profile `incomplete`, and the test that establishes completeness
  fails when any single row is removed.

- [ ] **AC4 — Every capability row carries its provenance set.** Each row names
  at least one source with a non-empty title and an absolute URL that is the
  post-redirect location, that source's `retrieved_at` date, and the source's
  exposed version or last-updated date or the literal `none exposed`; plus the
  row's claim scope, its last verification date, and its revalidation trigger. A
  row missing any of these is rejected rather than defaulted.

- [ ] **AC5 — Each of the four lifecycle states is reachable and distinct.**
  `verified`, `experimental`, `stale`, and `unavailable` are each produced by at
  least one input to the state function, and no two states are produced by the
  same input. `verified` requires a passing probe record in addition to a source
  inside the window; a row with a source and no probe resolves `experimental`.

- [ ] **AC6 — Window elapse is computed, not declared.** A row's `stale`
  resolution is a function of its last verification date, the profile's declared
  window, and a supplied reference date, where the declared window never exceeds
  90 days. Holding a row's fields fixed and advancing only the reference date
  past the window changes its state from `verified` to `stale`.

- [ ] **AC7 — The profile roll-up is recomputed from its rows.** The roll-up
  resolves `complete-current` only when every required row is present and no row
  is `stale`; `needs-revalidation` when a required row is `stale`; and
  `incomplete` when a required row is absent. A row honestly recorded
  `unavailable` does not prevent `complete-current`. The declared roll-up in the
  ledger is compared against the recomputed value, so a hand-edited roll-up
  fails.

- [ ] **AC8 — The router reports the state it was given.** A request selecting a
  `stale` row returns the `stale-profile` status with provenance and no operative
  guidance. A request selecting an `experimental` row returns the sourced facts
  with a warning and no support claim. A request selecting an `unavailable` row
  returns the known limit and provenance. A request spanning rows of differing
  states never reports the most favorable of them.

- [ ] **AC9 — Advertised mode availability is unchanged.** `runtime-package`,
  `runtime-profile`, `plugin`, `hook`, and `subagent` remain the closed set of
  five unavailable authoring modes returning the versioned unavailable result.
  Because neither user-facing workflow's `SKILL.md` changes, the recorded
  activation observation and its digest pin remain the ones in force.

- [ ] **AC10 — Retrieval and baseline safety hold.** Every admitted topic has at
  least two solo-declared retrieval cases. The re-measured record meets the
  established precision, recall, exact-selection, and topic-count thresholds, and
  answers no more than the permitted share of the forty generic negatives. Every
  inherited foundation pin holds at its recorded value, or a re-taken pin is
  recorded in `qa.md` with its prior and current value, and the count of re-taken
  pins equals the count of pins whose value differs.

- [ ] **AC11 — Shipped availability statements match what shipped.** Every
  shipped statement describing the corpus as lacking composition floors or a
  Claude Code profile, and every shipped statement of a topic count that
  admission changes, agrees with the admitted set. The count check reports a
  diagnostic naming the observed and expected counts rather than raising an
  unhandled exception on an unmapped count.

- [ ] **AC12 — Records and published surfaces are current.** The initiative's
  milestone string names this slice while it is in flight; this spec is
  registered as active work while in flight and moved to shipped work at close;
  the pack version moves in lockstep across both manifests; the changelog carries
  one entry for this pack, topmost; and the architecture document states which
  slice-3 surfaces exist and which remain `PLANNED`.

## Follow-ons

- INI-009 slice 3b owner: `docs/product/briefs/agent-skill-engineering.md` slice
  3b row — the seven remaining runtime profiles (Codex, GitHub Copilot, Cursor,
  Kiro IDE, Kiro CLI, Gemini CLI, Google Antigravity), which fill the ledger this
  slice establishes and complete RFC-0097's eight-profile M2 roll-up condition.
- INI-009 slice 3b owner: the `compatibility-and-runtime-package-patterns` leaf,
  whose recorded admission condition is the runtime profiles that make packaging
  claims verifiable.
- Repository maintainers: a freshness check that reports elapsed verification
  windows across profiles. This slice makes window elapse computable and asserts
  the shipped ledger is inside its window at its own recorded evaluation date; a
  wall-clock gate belongs with the freshness-lint family, not the pack suite,
  because a timer-driven failure reddens unrelated work.

## Assumptions

- Technical: exactly 11 taxonomy leaves are reserved for runtime composition, of
  which 3 are composition floors (source: `packs/agent-skill-engineering/okf/agent-skill-engineering-foundation/concepts/declared-absent/unpopulated-leaves.md`, 24 `##` blocks of which 11 read "Reserved for the later slice that covers runtime composition")
- Technical: topic frontmatter is a closed five-key set carrying no provenance, which lives in the body's `## Provenance and lifecycle` section (source: `packs/agent-skill-engineering/okf/agent-skill-engineering-foundation/concepts/trust-boundaries-and-instruction-provenance.md:1-7`)
- Technical: the provider contract already declares the `runtime` request field, the `profile_provenance` response field, and the `stale-profile` status, none of which any case reaches (source: `packs/agent-skill-engineering/tests/fixtures/provider-contract.json:4,8,10,12`)
- Technical: all five composition authoring modes are `unavailable` today (source: `packs/agent-skill-engineering/tests/fixtures/unsupported-mode-cases.json`)
- Technical: admitting a topic moves four binding digests on both the retrieval and negative records, so both are re-measured rather than re-stamped (source: `packs/agent-skill-engineering/tests/pack/test_foundation_corpus.py:278-292` and `:481-503`)
- Technical: every admitted topic requires at least two solo-declared retrieval cases (source: `packs/agent-skill-engineering/tests/pack/test_foundation_corpus.py:258`)
- Technical: a runtime profile may rest on the single-ecosystem-contract promotion class, which D8 extends to profiles by name (source: `docs/rfc/0097-agent-skill-engineering.md:503`)
- Technical: Claude Code's first-party documentation states the isolated-context, nesting-depth, and tool-inheritance claims, and exposes product version v2.1.251 (source: probe — `https://code.claude.com/docs/en/sub-agents` retrieved 2026-08-31)
- Technical: Claude Code documentation URLs under `docs.claude.com/en/docs/claude-code/` 301-redirect to `code.claude.com/docs/en/`, so the pre-redirect URL is not a durable source identity (source: probe — WebFetch of `https://docs.claude.com/en/docs/claude-code/sub-agents` returned `301 Moved Permanently` on 2026-08-31)
- Process: splitting one RFC follow-on into two brief slices needs no RFC amendment; follow-on 3 became brief slices 2a and 2b (source: `docs/rfc/0097-agent-skill-engineering.md:620` compared against `docs/product/briefs/agent-skill-engineering.md:172-173`)
- Process: two `tools/test_guide_typed_asides.py` failures reproduce on `origin/main` and are owned elsewhere (source: probe — `python3 -m pytest tools/test_guide_typed_asides.py -q` returned 2 failed, 2 passed; `workspace.toml:284`)
- Product: slice 3 is cut into 3a and 3b, this spec being 3a (source: user confirmation 2026-08-31)
- Product: `runtime-package` stays deferred and its package-lifecycle rows are out of scope (source: user confirmation 2026-08-31)
- Product: slice 3a carries the Claude Code profile as a pilot so the ledger schema has a consumer that can fail (source: user confirmation 2026-08-31)
- Product: the `subagent`, `hook`, and `plugin` authoring modes stay `unavailable` until profile data supports stating degradation (source: user confirmation 2026-08-31)
