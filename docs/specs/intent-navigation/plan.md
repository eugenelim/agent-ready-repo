# Plan: Intent navigation — navigator core

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/reference.md` (standard-library-only constraint); `packs/governance-extras/.apm/skills/navigate-decisions/` with `packs/governance-extras/tests/skills/navigate-decisions/` (query envelope, limits, and loader precedent); `packs/core/.apm/adapter-root-bins/intent_delivery_relations.py` with `packs/core/tests/pack/test_intent_delivery_relations_copies.py` (shared-copy and pin precedent); `packs/core/.apm/skills/close-work/scripts/closure_terminality.py` with `tools/check_closure_terminality_parity.py` (terminality projection and parity precedent). Deviation: the shared intent-edge derivation's source lives in this skill, not in `adapter-root-bins/`, because no adopter bin consumes it.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/intent-navigation/notes/verification-ledger.md`. A genuine
> artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan.

## Approach

Build the shared derivation first, because every operation reads it. The query surface follows, then the outstanding-work view, then activation, packaging, and documentation. Everything merges to `feature/intent-navigation`, which reaches the default branch in one pull request after the brief's slice 4. The riskiest part is outstanding-work completeness: it must match a hand-written manifest exactly over every fixture.

## Constraints

- RFC-0105 D1 to D5 govern the navigator: D1 to D3 its population and independence from `workspace.toml`, D5 that design advice stays non-binding. D4 and § Experiment items 3 to 5 belong to the brief's slice 4. Item 1 maps here to AC-0033 and AC-0034; item 2's query side to AC-0010 and AC-0072, and its view side to slice 4.
- The commit T4 builds on contains the `[core][2.30.1]` terminality repair, because AC-0058 and AC-0067 depend on its leading-word reading. Before T1, `feature/intent-navigation` is created from, or rebased onto, a default-branch commit that includes the repair, and the slice pull-request branch is cut from it, so T1 to T6 all build on the repair. Before T4's first commit, `git merge-base --is-ancestor <repair commit> HEAD` passes on the slice branch.
- RFC-0103 D1 to D3: the typed reference grammar, its ladder kinds, and its refusal of ordinals. Its refusal of an ambiguous bare slug binds within the field's target type, under FEAT-0002's constraint C1; a slug shared across types is not ambiguous.
- ADR-0112 D1: the graph is derived, never stored.
- ADR-0007 and ADR-0074: an agent-invoked skill script is permitted and is standard-library-only.
- `packs/AGENTS.md`: UTF-8 stream reconfiguration before printing, unique module names in tests, no internal-record citations in shipped files, and eval updates with pack changes. The version bump and changelog entry land when the integration branch merges, under slice 4.
- `packs/AGENTS.local.md`: each hand-maintained `packs/**` copy of a shared helper is pinned by a test.
- The brief's constraints: publication waits for slices 1, 3, and 4 through `feature/intent-navigation`.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none; the activation run is recorded in the ledger by T5.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User procedure and orientation hand-off | T6 | Guide lints green | Both guides route intent questions to `navigate-intents` |
| Pack promise and user journey | T6 | README, docs index, guides README, JOURNEY rows | Rows present |
| Architecture | T6 | `packs/core/DESIGN.md` section | Names the derivation's source, copies, pins, consumers |
| Skill census | T5 | `test_skill_census.py` green | Entry present |
| Executable proof | T1, T2, T3, T4, T5 | Suites wired and green | Makefile, `lint-ci-parity`, build-gate-chain entries present |
| Verification record | T4, T5 | Ledger entries for AC-0019, the activation run, and the integration-branch gate runs | Ledger cited by closing PR |

## Design (LLD)

### Design decisions

Owned by: T2, T3, T4

- **One derivation module.** `intent_graph.py` owns node admission (AC-0001), preamble parsing (AC-0002), the admitted pointer fields (AC-0003), resolution (AC-0004, AC-0005, AC-0006, AC-0007, AC-0043, AC-0064, AC-0070), and integrity failures (AC-0009). The brief's slice 2 later loads a byte-identical copy into `close-work`. Owned by T2.
- **Delivery relations stay the resolver's.** Typed delivery relations come only from loading the bundled `intent_delivery_relations` copy in process and calling `resolve_repository`. The derivation's own `Brief:` and `Discovery:` pointer edges place specs; they never become delivery relations. Owned by T3.
- **One preamble parser.** The derivation parses a preamble as `intent_shape.read_preamble` does, hiding multi-line HTML comment regions and stopping at the first `## ` heading. It keeps every value of each admitted edge field, so AC-0003's `multiple_values` can be decided. A brief's `Parent intent:` is the exception: it is read with the resolver's line rule, comment regions included, keeping every value, so AC-0064's equality and `multiple_values` hold. Owned by T2.
- **Resolver primitives are called; the brief-parent composition is re-implemented and pinned.** The derivation loads the bundled `intent_delivery_relations.py` copy by path and calls its `_ARTIFACT_FILE_RE`, `_SPEC_DIR_RE`, `_SLUG_RE`, `_PARENT_INTENT_KINDS`, `_preamble_all`, `_normalize`, and `_is_unsafe_ref`. The resolver's accept, reject, and merge-by-slug loop for a brief's `Parent intent:` is inline in `resolve_repository`, so the derivation re-composes it from those primitives, and AC-0064's equality proof against the resolver's output pins it. Both read files through the bundled `_file_safety.py`. Owned by T2.
- **Node ids follow the traceability lint's precedence, over the preamble only.** The derivation computes each intent's node id with `recognize_ladder`'s precedence, `Kind:` before `Level:`, but reads only the preamble, so a field quoted in a body never changes an id. It resolves an intent's typed `Parent intent:` by id equality. On 2026-10-08 every typed `Parent intent:` in the corpus already equalled its target's id. Bringing the lint to the same preamble-only reading, and the parity check between the two, is the brief's slice 6. Owned by T2.
- **Edge basis and trust class.** Every edge records its source field, value form, and trust class (AC-0071). Owned by T2, T3.
- **Terminality is a parity-checked copy.** `navigate-intents/scripts/intent_terminality.py` carries the leading-word rule and terminal sets. The parity tool checks it against `closure_terminality`'s upstreams, and against `closure_terminality` only for the spec subset (AC-0067). Owned by T4.
- **Text tree is a format of `tree` and `outstanding`, not an operation.** Owned by T3, T4.
- **Vocabulary.** Node kinds and edge names follow the traceability sidecar's node and edge vocabulary at a different scope, without its `_state/traceability.json` filename or `schema_version` namespace, per FEAT-0002's settled decision. Owned by T3.

### Interfaces & contracts

Owned by: T3, T4

- CLI: `python3 scripts/navigate_intents.py query --root <repo> [--operation <op>] [--id <identity>] [--from <identity>] [--depth <n>] [--format json|text] [--selectors <json>]`. Exit code 0 on `status: ok` and 1 on every `status: error`, including `invalid_query` and `missing_operation`. Exit code 2 is only for an argument the command-line parser rejects before any query is formed, and prints no envelope.
- Query error codes, closed: `resolver_unavailable`, `invalid_query`, `missing_operation`, `unknown_operation`, `not_found`, `ambiguous_identity`, `invalid_selector`, `invalid_depth`, `result_too_large`, `input_too_large`, `unsafe_input`, `malformed_record`, `duplicate_identity`, `delivery_incomplete`.
- Refused-edge states: AC-0007's closed set.
- No `contracts/` file: the query schema is versioned in its envelope, and the spec's criteria are its contract.

### Behavior & rules

Owned by: T2, T3, T4

- Bare-slug lookup is a dictionary over live intents only, so a cross-type collision cannot reach it (AC-0005).
- Cycle detection runs after resolution: in each cycle of parent edges, including a self-parent, the edge leaving the lowest-sorting slug is refused as `cycle` (AC-0043), so `ancestors` always terminates.
- A `none` value is detected on its first whitespace-separated word, compared case-insensitively; an empty value is no edge (AC-0006).
- Ordinal identities match the filename prefix `^[A-Z]+-\d{4}` (AC-0014).
- Limits are checked in AC-0016's order on the assembled result object.

### Failure, edge cases & resilience

Owned by: T2, T3

- Integrity failures raise one internal exception type carrying the AC-0009 code, checked in AC-0009's order; the CLI converts it to an error envelope.
- `generated_at` is the only nondeterministic field in a query response; tests compare with it removed.
- A missing intents, briefs, or specs directory is an empty collection, as in the resolver.

### Quality attributes (NFRs)

Owned by: T4

- Latency (AC-0019): the de-risk measured 1.55 s median for confined derivation over 739 files, so the 5-second bar leaves room for the query and the resolver load.

## Tasks

### T1: Contract fixtures fail for the absent capability

**Depends on:** none

**Touches:** `packs/core/tests/skills/navigate-intents/`, `docs/specs/intent-navigation/spec.md` (`Status:` to `Implementing`), `docs/product/briefs/intent-navigation-delivery.md` (`Status:` from `Ready` to `Executing`, in the same commit as the spec's status move, because `lint-brief-coverage.py` refuses a `Ready` brief with an `Implementing` child), `workspace.toml` (in that same commit, the spec's entry moves from `["ini-010".work].queue` to `.active` and the brief's from `["ini-010".brief_queue].ready` to `.executing`, so status and membership move together)

**Tests:**
- `packs/core/tests/skills/navigate-intents/fixtures/` holds a `mixed/` corpus and one committed `negative/<case>/` corpus per AC-0007 state, per AC-0009 code other than `unsafe_input` and `input_too_large`, and per AC-0064 resolver diagnostic, plus a brief whose `Parent intent:` line sits inside a multi-line comment, and an intent with `Level: capability` and `Kind: outcome`. The five AC-0042 confinement cases and AC-0009's `unsafe_input` and `input_too_large` cases are not committed corpora; the next bullet says how they are built.
  - `mixed/` carries capability, feature, outcome, and opportunity intents; a tombstone with `Reissued as:`; briefs, including the seeded template; specs with typed, path, and markdown-link `Discovery:` values and with `Brief:`; statuses with text after the status word; `none` parents with and without a comment; and a cross-type slug collision.
  - Symlink, FIFO, hard-link, and swap cases, and the intent over 1,000,000 bytes, are built in a temporary directory at test time, not committed.
  - Repair fixtures: a brief whose `Parent intent:` mixes one accepted value with malformed ones (AC-0064), and a value matching no recognized shape (AC-0071's `unrecognized`).
  - Every corpus carries `expected-outstanding.json`, a hand-written list of its non-terminal artifacts.
- `test_derivation_contract.py`, `test_query_contract.py`, `test_text_tree.py`, and `test_outstanding.py` load modules by path under names prefixed `core_navigate_intents_`, and every test fails because the modules are absent.

**Done when:** the four test files collect and fail on import of the absent modules, nothing else fails, and `python3 packs/core/.apm/skills/author-delivery-brief/scripts/lint-brief-coverage.py --root .` passes with the spec at `Implementing` and the brief at `Executing`, and `python3 -m pytest tests/roster/test_workspace_status_projection.py -q -k test_no_fail_closed_lifecycle_findings` passes over the real `workspace.toml`.

### T2: The shared derivation resolves every admitted pointer field-scoped and kind-checked

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/navigate-intents/SKILL.md`, `packs/core/.apm/skills/navigate-intents/scripts/intent_graph.py`, `packs/core/.apm/skills/navigate-intents/scripts/intent_delivery_relations.py`, `packs/core/.apm/skills/navigate-intents/scripts/_file_safety.py`, `.claude/skills/navigate-intents/`, `.agents/skills/navigate-intents/`, `packs/core/tests/skills/navigate-intents/test_derivation_contract.py`, `packs/core/tests/pack/test_intent_delivery_relations_copies.py`, `tests/roster/test_intent_delivery_relations_repository.py`

**Tests:**
- `test_derivation_contract.py` proves, at the derivation's own interface, AC-0001, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0043, AC-0064's parsing and refusal states, AC-0070, the pointer and refused-edge part of AC-0071, and AC-0009's codes as the derivation's integrity failures.
- The resolver copy and its `_file_safety.py` sibling are added to both existing pin tests' accepted lists, and `navigate-intents` is added to VI-1903's installed-skill loop (AC-0011, AC-0037).
- A first lint-valid `SKILL.md` (name, description, and body stating the read-only boundary) is created, so the skill directory passes `catalogue lint` from its first merge; T5 completes its activation wording.
- `agentbundle catalogue self-host --root . --write` refreshes the skill's projections.

**Done when:** `python3 -m pytest packs/core/tests/skills/navigate-intents/test_derivation_contract.py -q`, both pin tests, and `agentbundle catalogue verify --root .` pass.

### T3: The query surface answers bounded questions and prints the tree

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py`, `.claude/skills/navigate-intents/`, `.agents/skills/navigate-intents/`, `packs/core/tests/skills/navigate-intents/`

**Tests:**
- `test_query_contract.py` proves AC-0002, AC-0008, AC-0009 and AC-0042 as whole-operation envelopes, the `delivery_contract` part of AC-0071, AC-0075 through a loader seam, AC-0076, AC-0010, AC-0012, AC-0013 for its five operations other than `outstanding`, AC-0014 for `record`, `tree`, and `ancestors`, AC-0015, AC-0016, AC-0018, AC-0038, AC-0072, AC-0073, AC-0063 for each of `summary`, `record`, `tree`, `ancestors`, and `search` (a lowered resolver limit for `resource_limit`, a provider-seam fixture returning `complete: false` with empty diagnostics for `unsafe`, and the oversized-intent precedence case), AC-0045's search-hit ordering, and AC-0064 (each brief fixture's derived parent compared with the resolver's output for the same corpus). AC-0010's fixture substitutes the resolver through a provider seam, as `closure_index._snapshot_provider` does.
- `test_text_tree.py` proves AC-0017's line format byte-for-byte on `mixed/` and its escaping on a fixture whose `Level:`, `Kind:`, and `Status:` values carry bidirectional controls, AC-0045's tree part on the cycle fixture, and AC-0046 through a lowered-limit seam.
- `test_independence.py` proves AC-0035 with three fixture variants compared with `provenance.generated_at` removed, and AC-0036 with an import scan of `navigate-intents/scripts/`.
- `agentbundle catalogue self-host --root . --write` refreshes the skill's projections.

**Done when:** `python3 -m pytest packs/core/tests/skills/navigate-intents/test_query_contract.py packs/core/tests/skills/navigate-intents/test_text_tree.py packs/core/tests/skills/navigate-intents/test_independence.py -q` and `agentbundle catalogue verify --root .` pass.

### T4: The outstanding-work view finds every open artifact and places it under its parent

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py`, `packs/core/.apm/skills/navigate-intents/scripts/intent_terminality.py`, `packs/core/tests/skills/navigate-intents/test_outstanding.py`, `tools/check_closure_terminality_parity.py`, `tools/test_check_closure_terminality_parity.py`, `.claude/skills/navigate-intents/`, `.agents/skills/navigate-intents/`, `docs/specs/intent-navigation/notes/verification-ledger.md`

**Tests:**
- `test_outstanding.py` proves AC-0013 for `outstanding`, AC-0014 for `outstanding --from` (node id, bare slug, ordinal, `not_found`, and `ambiguous_identity`), AC-0074, AC-0063's precedence case for `outstanding`, AC-0045's outstanding ordering and `(no parent)`-last parts, AC-0058 against every fixture's `expected-outstanding.json`, AC-0059, AC-0060, AC-0065, AC-0061 (through a lowered resolver limit), AC-0062 byte-for-byte on `mixed/`, and AC-0066.
- `tools/check_closure_terminality_parity.py` checks `intent_terminality.py` as AC-0067 states, including the extraction probe set; `tools/test_check_closure_terminality_parity.py` mutates one terminal set and the extraction rule to prove each fails. Its docstring and remediation text are widened to name the navigator's check.
- Ledger: AC-0019's seven timed `outstanding` runs and the result's byte size. If the whole-corpus result exceeds 512 KiB, the size finding goes back to the spec as an amendment before the slice merges.

**Done when:** `test_outstanding.py`, the parity script, `python3 -m pytest tools/test_check_closure_terminality_parity.py -q`, and `agentbundle catalogue verify --root .` pass, and the ledger holds the AC-0019 result.

### T5: Activation, skill instructions, and pack wiring route intent questions here

**Depends on:** T3, T4

**Touches:** `packs/core/.apm/skills/navigate-intents/SKILL.md` (activation wording), `packs/core/.apm/skills/navigate-intents/evals/eval_queries.json`, `packs/core/pack.toml`, `packs/agent-skill-engineering/tests/fixtures/skill-census.json`, `Makefile`, `tools/lint-ci-parity.py`, `tools/repo/build_gate_chain.py`, `tools/test_build_gate_chain.py`, `tools/test_local_ci_shared_test_deduplication.py`, `.claude/skills/navigate-intents/`, `.agents/skills/navigate-intents/`, `docs/specs/intent-navigation/notes/verification-ledger.md`

**Tests:**
- `eval_queries.json` carries AC-0033's positives and AC-0034's near-misses; `[pack.evals].skills` lists `navigate-intents`; `agentbundle catalogue lint --root . --deep` passes its eval-shape check.
- A dispatched `pack-evals` run records each prompt's trigger rate in the ledger.
- `tests/roster/test_skill_census.py` and `tools/test_build_gate_chain.py` pass, and the build gate chain runs `tools/test_check_closure_terminality_parity.py`.
- The new `Makefile` suite line changes the recipe that `tools/test_local_ci_shared_test_deduplication.py` pins, so both `APPROVED_STANDALONE_PLAN_DIGEST` and `APPROVED_COMPOSED_PLAN_DIGEST` are re-pinned with a note in the file's established form naming the added line as the sole cause and the prior pins as current before it; `python3 -m pytest tools/test_local_ci_shared_test_deduplication.py -q` passes.
- `grep -rnE '\b(RFC|ADR)-0[0-9]{3}\b|\bAC-?[0-9]+[a-z]?(\([a-z]\))?\b|docs/(specs|rfc|adr|contracts)/[a-z0-9]' packs/core/.apm/skills/navigate-intents/`, the canonical pattern from `packs/AGENTS.local.md`, returns no match, so ADR and RFC near-miss prompts use unnumbered wording.
- `agentbundle catalogue self-host --root . --write`, then `agentbundle catalogue verify --root .` passes.

**Done when:** the listed tests, including `tools/test_local_ci_shared_test_deduplication.py`, and `catalogue verify` pass, and the ledger holds the activation run.

### T6: Orientation, architecture, and pack documentation match the capability

**Depends on:** T5

**Touches:** `docs/specs/intent-navigation/notes/verification-ledger.md` (the post-dispatch record), `guides/core/how-to/navigate-intents.md`, `guides/core/how-to/orient-at-session-start.md`, `guides/core/README.md`, `packs/core/README.md`, `packs/core/docs/index.md`, `packs/core/JOURNEY.md`, `packs/core/DESIGN.md`, `web/src/content/journeys/core.md` (regenerated by `tools/build-site.py --journeys-only`, never hand-edited)

**Tests:**
- `tools/lint-guide-titles.py`, `tools/validate_guides.py`, and `tools/lint-guides-no-repo-only-refs.py` pass.
- `make lint-ruff lint-mypy` passes.

**Done when:** each Durable Outputs row's closeout condition is visible in its destination, and the listed checks pass.

## Rollout

- **Delivery, by owner decision on 2026-10-08:** the slice merges into `feature/intent-navigation` as one pull request, and T1 to T6 are ordered commits inside it. Each task's `Done when` runs only that task's own tests. That branch merges to the default branch in one pull request after the brief's slice 4, which carries the `core` version bump and changelog entry. Rebase the branch onto the default branch at least weekly.
- **Gates on the slice pull request:** pull-request workflows trigger only for the default branch, so before the slice pull request merges, dispatch `build-check`, `test-corpus`, and `test-roster` on its head, then add one ledger-only commit recording their run ids, which is the slice's last commit. The runs prove the commit before it, and nothing but that ledger record follows. The final pull request to the default branch runs the full gate chain.
- **Infrastructure, external systems:** none.
- **Deployment sequencing:** none within this slice; `close-work` is unchanged until slice 2.

## Risks

- The long-lived integration branch drifts from the default branch, especially in `Makefile`, `tools/lint-ci-parity.py`, and the skill census, which other work edits often.
- The activation near-miss "how many roadmap intents do we have" is a positive for `navigate-decisions`, so the two evaluation files must agree on it.

## Changelog

- 2026-10-08: spec approved by eugenelim
- 2026-10-08: plan approved by eugenelim
- 2026-10-08: revised before execution, with owner approval, from a sustained pre-EXECUTE review: T5 owns the command-plan digest re-pin in `tools/test_local_ci_shared_test_deduplication.py`; T1 moves the brief to `Executing` with the spec's move to `Implementing`, moves both `workspace.toml` memberships in the same commit, and states which negative cases are committed and which are built at test time; T6 owns the regenerated `web/src/content/journeys/core.md`.
- 2026-10-08: spec re-approved by eugenelim after the pre-EXECUTE revision
- 2026-10-08: plan re-approved by eugenelim after the pre-EXECUTE revision
