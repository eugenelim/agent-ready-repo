# Plan: Intent dependency graphs

- **Status:** Approved
- **Spec:** [`spec.md`](spec.md)
- **Constrained by:** RFC-0106 D3; RFC-0105; RFC-0103
- **Repository anchors:** `docs/specs/intent-navigation/spec.md` and `plan.md` own the navigator contract and planned source/test surfaces; `docs/specs/intent-navigation-export/` owns its export. The analogous production query/export is `packs/governance-extras/.apm/skills/navigate-decisions/`, with its query/publication/browser tests.
- **Retention:** repository-durable spec and plan, fingerprints recorded at approval. Implementers, reviewers, resuming agents, and CI need them. Source/tests, the navigator guide, pack design, and release entry own post-closeout truth.

## Constraints

- One slice PR targets the default branch after slices 1 and 4 land; T1–T3 are ordered commits inside it. No commit or push without owner permission.
- Reuse the existing navigator and export. No new dependencies, cross-skill imports, shared renderer, index, or writer migration.
- Each task completes on its own checks. Run the required local lint and combined targeted suites before final review; dispatch full gates once on the slice PR, not per task.
- Expected review shape: DEEP, bounded to one navigator enhancement. Stop if the prerequisite contracts cannot support the extension without changing this slice's accepted boundary.

## Durable-output map

| Output | Tasks | Evidence owner |
| --- | --- | --- |
| Dependency interpretation, bounded query, text, and compatibility | T1 | Core navigator tests |
| Offline dependency view, accessibility, and inert content | T2 | Export and browser tests |
| Guide, pack design, versions, release, activation and projections | T3 | Existing guide/evaluation/catalogue checks and ledger |
| Contract extension and frozen predecessor pointers | T1 | This spec; permitted status pointers only after predecessors ship |

## Design (LLD)

### Integration and discovery

Owned by: T1, T2

The approved navigator plan names `packs/core/.apm/skills/navigate-intents/scripts/intent_graph.py`, `navigate_intents.py`, and `packs/core/tests/skills/navigate-intents/`. Those are planned anchors, not an assertion that implementation exists here. The current worktree has no navigator source and slice 4 has an empty scaffold. The source-only disconfirming check found all three real intent dependency headers use paths, so a typed-only reader would omit every currently recorded dependency. The owner selected path compatibility at the assumption checkpoint.

Discover the landed navigator entry point, dependency parser extension point, and export/query selection seam before writing code. Reuse their node admission, preamble parsing, safety helper, envelope, and scratch publication. The required result is the spec's dependency view under the inherited contracts, verified through production query and export boundaries. If the prerequisites are absent, the shared derivation needs a new cross-skill boundary, or the export cannot retain its safety/accessibility contract, stop and bring the owner the concrete conflict.

No second dependency-enforcement reader is created. The navigator interprets pointers for display; FEAT-0034 decides readiness, receipts, cooled dependencies, and migration.

### Contract extension and failure scope

Owned by: T1

The dependency operation is additive to the versioned navigator query. Existing operations keep their output contract. The operation accepts `id`, `direction`, and `depth` through the landed query interface, and the existing CLI gains the corresponding direction selector. Each node's dependency pointers are resolved through the existing node index; only the dependency operation consumes their edges and diagnostics.

The dependency view does not convert cycles into a topological order, decide completion from status, or remove a cycle edge to manufacture a DAG. Duplicate pointers join at the waiting/prerequisite pair while retaining their bases.

By this slice's build, the predecessor spec directories are frozen. The new spec owns the extension of `intent-navigation` AC-0003 and AC-0013 and relevant query-result clauses, and the export's edge coverage. Read the final predecessors when they land and identify the exact affected clauses before approval of implementation. Add only the status-line supersession pointers the spec/plan lifecycle permits; leave frozen bodies and completed engines alone.

### Offline presentation

Owned by: T2

Reuse slice 4's visual conventions and browser harness. The new view's design goals, in order, are finding prerequisites/dependents, reading arrow direction, and seeing unresolved or cyclic dependencies. Graph layout remains an implementation choice. A text list supplies the same facts without requiring a pointer device or interpreting color.

The query's bounded selection is the fact oracle for the view. The existing export contract owns the full-corpus representation and publication budget; this plan introduces no new export threshold. The landed renderer determines the component and event seams.

### User-documentation draft

Owned by: T3

Add a dependency task to the navigator guide: “Ask which intents this intent depends on, or which depend on it. Select an intent, choose prerequisites or dependents, and set the depth. An arrow points from the waiting intent to its prerequisite. The result reads `Depends on:` headers, accepting typed references and legacy repository paths. It does not include workspace-only dependencies or decide whether work may start. Inspect the visible diagnostics before relying on a dependency chain.”

Adapt the runnable command to the landed CLI: the approved navigator plan's command grammar uses `query --operation dependencies --id <identity> --direction prerequisites --depth 2 --format text`. Validate it on the task fixture rather than inventing an installed command.

## Tasks

### T1: Dependency query and text fixtures pass

**Depends on:** none

**Verification mode:** TDD

**Tests:**
- **VI-1001.** In the owning Core navigator suite, drive its production query boundary over a hand-authored intent corpus: all registered kinds, a typed/path alias pair, repeated and comma-separated fields, null values, body/comment decoys, non-intent targets, malformed/wrong-kind/missing/retired targets, a chain, a diamond, a self-loop, and a multi-node cycle (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005).
- **VI-1002.** Query fixtures assert independent expected node/edge sets for each direction and depths 0, 1, and 2; invalid selectors/identities; exactly-at and over each result limit; and text goldens including an isolated node and escaped controls (AC-0006, AC-0007, AC-0008).
- **VI-1003.** Derive a real-input manifest of active intent dependency headers, classify accepted forms and faults, and record accept/reject counts before finalizing refusal fixtures. Keep copies of exact inputs or immutable corpus fingerprints in the ledger. Add workspace-absent/present/unreadable and repository-byte-snapshot checks, and compatibility fixtures proving that dependency faults do not change existing operation results (AC-0012–AC-0013).
- **VI-1004.** The contract-extension record identifies the final predecessor clauses this slice extends; permitted frozen status pointers resolve to this spec and bodies remain byte-identical. Existing navigator operations' construction assertions remain effective (Agent Rules; AC-0012).

**Approach:** `no stub (implementation-discovered)`. Ground the callable seam under the discovery condition above. Then record and red-validate a contract-surface assertion through the landed production query boundary before implementation; do not guess internal symbols at authoring time.

**Done when:** T1's dependency/query/text, corpus, and compatibility checks pass, with counts and runtime in the ledger.

### T2: Offline dependency navigation exposes the same facts

**Depends on:** T1

**Verification mode:** TDD plus rendered/manual checks

**Tests:**
- **VI-2001.** Extend the landed export/browser suite to open a self-contained dependency fixture and compare visible identities, directed edges, and diagnostics to T1's independent manifest for each selection, direction, and depth. Include a cycle and a refused pointer, and verify the graph's arrow legend and relationship distinction (AC-0009).
- **VI-2002.** Keyboard-only browser checks exercise selection, direction/depth changes, following a prerequisite and a dependent, returning to the start, focus visibility, and text equivalents. Review the rendered graph against the ordered design goals above and record the concrete fixture/browser evidence (AC-0010).
- **VI-2003.** Run the owning export's existing hostile-content, source-link, no-network, and publication-boundary probes with dependency metadata added; unsafe read and hostile value fixtures assert the inherited refusal or inert result (AC-0011; AC-0013).

**Approach:** `no stub (implementation-discovered)`. Use the prerequisite export's production seam and safety/browser harness. Stop on the discovery kill conditions above.

**Done when:** T2's export and keyboard/safety checks pass; rendered evidence is recorded in the ledger.

### T3: Installed dependency view and its promise agree

**Depends on:** T1, T2

**Verification mode:** goal-based integration and activation

**Tests:**
- **VI-3001.** Extend the landed navigator's activation evaluation with the dependency positives and enforcement/migration/mutation near-misses; run its declared evaluator and record prompt-set identity and results (AC-0014).
- **VI-3002.** Update the entire dependency task in the landed navigator guide, preserving the rest of its current story, and its owning design section. Guide checks `tools/validate_guides.py`, `tools/lint-guide-titles.py`, and `tools/lint-guides-no-repo-only-refs.py` pass. The demonstrated query and export produce T1's expected facts (AC-0015; Durable Outputs).
- **VI-3003.** Bump the Core pack/plugin version pair and write the outcome-led release entry with free-standing Highlights. Run live-source `agentbundle catalogue self-host --root . --write`, then `agentbundle catalogue verify --root .`; invoke the installed query and export over T1's typed/path fixture. Run the shipped-text citation check from `packs/AGENTS.local.md` (AC-0015).

**Done when:** T3's evaluation, guide, version/release, and installed-fixture checks pass with ledger evidence.

## Slice verification

Run `make lint-ruff lint-mypy` and the combined touched suites once before final code review. Dispatch the full gates once on the slice PR and record their identifiers/results. No `make ci` push precheck.

## Rollout

One post-initial-release Core update merges to the default branch after slices 1 and 4. No flag, infrastructure, migration, or external service is added. Rollback reverts this slice's source, guides, release, and permitted supersession-pointer changes; canonical dependency records are untouched.

## Risks

- Legacy pointers can be read without repairing their authoring form. The guide distinguishes compatibility from the canonical typed form.
- A dependency view can be mistaken for dispatch authority. Direction, scope, and trust labels remain visible.
- Prerequisite implementation and export design are unavailable in this authoring worktree. The discovery conditions prevent guessing those seams.

## Changelog

- 2026-10-08: spec and plan approved together by the repository owner. Shaping round 1 is clean. Adversarial round 1 returned two findings; adjudication refuted both, so the review is clean with no repair. Reports are under `.context/reviews/e40bed9c-cd45-4488-aef0-1d6c56224584/`.
- Approved reviewed revisions, before lifecycle-only approval annotations: spec SHA-256 `4c9c1b52f7571116e35a4b5da5739ea6547b5aaf377f4b10eb67b55de942c86e`; plan SHA-256 `691bbbf216858ab641c273ad5d8bfcdfeda09ab8e2887c7cf713268fe30c0405`.
- 2026-10-08: nonmaterial wording correction after approval. AC-0007 names the navigator's limits by their operations, not by that spec's criterion numbers, so the alignment check no longer reads them as local criteria. The referenced rules and the obligation are unchanged.
