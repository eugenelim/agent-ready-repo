# Spec: Intent preamble closure declarations

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0103
- **Brief:** brief:intent-identity-and-registration
- **Discovery:** docs/product/intents/FEAT-0001-intent-identity-and-registration.md
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons`
> and `Assumptions` are working material.

## Outcome

An intent author can declare that an Outcome is shared with another intent and can distinguish a deliberately childless decomposition from one that has not been completed, using preamble data that readers validate without body prose. Success is that hidden HTML-comment content supplies neither declaration, each live example carries a valid declaration, and malformed or unresolved declarations fail an existing repository gate.

## What Changes

- `Outcome co-owner:` becomes a constrained-when-present intent field — `intent_shape.py`
- A co-owner value uses the canonical typed pointer form and must resolve to a different intent artifact without creating a parent, delivery, or structural graph edge — `lint-traceability.py`
- `closed-empty` joins the `Decomposed:` terminus vocabulary while the literal `no` keeps its existing meaning — `intent_shape.py`
- `read_preamble()` ignores field-shaped and heading-shaped lines inside HTML comment regions while preserving visible trailing-comment normalization — `intent_shape.py`
- The two live cases gain declarations in their preambles — `remote-ci-verification-parity.md` and `STRAT-0002-platform-core.md`
- The adopter field reference, the intent template, the preamble-writing how-tos, and refusal guidance describe the two declarations
- Core and Product Engineering pack evals, versions, projections, and release history move with their changed runtime surfaces

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable — authors write one new field and one new terminus | `guides/product-engineering/reference/intent-fields-and-modes.md` | eugenelim | field and terminus rows held to the runtime table by the parity suite | Each runtime-decided field appears once at the correct tier, and the `Decomposed` row names the runtime terminus set |
| Current product truth | Applicable — the intent template and two how-tos show the preamble authors copy | `frame-intent`'s intent template; `frame-the-intent.md`; `hand-it-to-build.md` | eugenelim | rendered-template conformance and a closed surface check | Every named preamble surface offers `Outcome co-owner:` as optional and offers `closed-empty` as a `Decomposed:` terminus |
| Maintainer procedure | Applicable — malformed, unresolved, self-referential, and unexpectedly absent commented declarations need repairs | `guides/product-engineering/how-to/fix-a-refused-intent.md` | eugenelim | one worked before/after remedy per failure class | A maintainer can repair each failure without reading this spec |
| Current architecture | Applicable — two validators share the declaration contract without turning the peer relation into a graph edge | module docstrings in `intent_shape.py` and `lint-traceability.py` | eugenelim | docstrings name ownership and the non-edge rule | Each rule has one implementation owner and the resolver documents that peer validation adds no edge |
| Release history | Applicable — two published packs change | `docs/product/changelog.md` | eugenelim | release entries for Core and Product Engineering | Each entry states the adopter-visible declaration change |
| Decision rationale | Not applicable — this adds a field and a value under the existing field-contract and pointer-grammar decisions; it reverses no accepted decision | — | — | — | No ADR or RFC is created |

## Agent Rules

### Always do

- Keep packet-decidable field rules in `intent_shape.py`, and derive co-owner resolution from the node identities `lint-traceability.py` already builds.
- Treat `Outcome co-owner:` as a peer declaration only. Validate it without adding a producer, parent, delivery, or structural edge.
- Verify each migrated value through `intent_shape.read_preamble()`; a visible line below the first `## ` heading is absent even when a text search finds it.
- Update the source under `packs/*/.apm/`, its pack eval, its matching pack and plugin versions, and generated projections together.

### Ask first

- Allowing more than one co-owner, changing the field from optional to required, or accepting an untyped fallback.
- Changing the meaning of any existing `Decomposed:` terminus or the literal `no`.
- Expanding this slice into closure refusal behavior, child traversal, or transition policy.

### Never do

- Add a distinct closed-empty preamble field; `YYYY-MM-DD closed-empty` is a `Decomposed:` value.
- Read an intent body to supply either declaration.
- Add a dependency, module boundary, or top-level directory.
- Put repository governance citations or spec identifiers into shipped `.apm/` content.

## Testing Strategy

- **Preamble visibility and value rules (AC-0001, AC-0005, AC-0006, AC-0007, AC-0008): TDD.** Fixture intents decide typed-pointer shape, the expanded terminus set, progress reporting, HTML-comment regions, and unchanged visible suffix-comment normalization.
- **Co-owner resolution and non-edge behavior (AC-0002, AC-0003, AC-0004, AC-0019): TDD through the traceability linter.** Temporary corpora exercise a valid peer, a missing peer, a self-reference, hidden closed and unclosed comment regions, and the graph built from the same files.
- **Live migrations (AC-0009 and AC-0010): goal-based checks.** The production parser reads the real files and compares their effective preamble values, so a misplaced body line fails.
- **Published-surface agreement (AC-0011, AC-0012, AC-0020): goal-based checks.** The field-reference parity suite and template-conformance checks compare published rows and rendered preambles with runtime tables; a closeout read checks each worked refusal repair against its named runtime class.
- **Repository integration (AC-0013 and AC-0014): goal-based checks.** The intent corpus and traceability commands run unfiltered over the real repository and must exit zero.
- **Pack release integrity (AC-0015, AC-0016, AC-0017, AC-0018): goal-based checks.** Pack-eval cases exercise the changed adopter behavior, source projections reproduce cleanly, each changed pack's manifest pair moves together, release history names both changes, and the shipped-content citation gate remains clean.

## Acceptance Criteria

Every field value below is decided after the existing normalization stage: a visible trailing HTML comment is discarded, then surrounding backticks are stripped. A value emptied by that stage is absent.

- [x] **AC-0001.** A visible `Outcome co-owner:` value is accepted by `validate_live_intent()` exactly when it is a kind token from `outcome`, `opportunity`, `capability`, or `intent`, followed by `:` and a non-empty target identity. A bare slug, an empty target, or any other kind token is refused; the target-identity remainder is not otherwise constrained because the target intent's `Slug:` value is not otherwise constrained.
- [x] **AC-0002.** Where AC-0001 passes, the traceability lint accepts an `Outcome co-owner:` value whose exact canonical node id names another intent artifact and refuses a value naming no intent artifact, with a non-zero exit and a report naming the source intent, field, and target.
- [x] **AC-0003.** The traceability lint refuses an `Outcome co-owner:` value equal to the source intent's own canonical node id, with a non-zero exit and a report naming the self-reference.
- [x] **AC-0004.** For the same fixture corpus, adding a valid `Outcome co-owner:` declaration leaves `Graph.edges` unchanged and adds no dangling-target, cycle, structural-orphan, or reachability finding.
- [x] **AC-0005.** `Decomposed:` accepts the literal `no`, or an ISO 8601 calendar date followed by exactly one terminus from `children`, `brief`, `spec`, `direct-light`, and `closed-empty`; it refuses every other terminus or value shape. A `closed-empty` value needs no checkbox item under `## Decomposition`; the existing checkbox rule remains exclusive to `direct-light`.
- [x] **AC-0006.** `progress_state()` reports absent `Decomposed:`, the literal `no`, and `2026-09-24 closed-empty` as three distinct states.
- [x] **AC-0007.** `read_preamble()` returns no field or heading text contained inside a closed or unclosed HTML comment region before the first visible `## ` heading. A required field inside such a region does not satisfy presence, while a retired or malformed field inside it produces no violation; a `## ` line inside the region does not end the visible preamble.
- [x] **AC-0008.** Comment-region handling leaves visible value normalization unchanged: bare, backticked, trailing-commented, and backticked-plus-trailing-commented forms of each accepted new value reach the same verdict, and a visible comment-only optional field remains absent.
- [x] **AC-0009.** Parsing the real `remote-ci-verification-parity` intent returns `Outcome co-owner: intent:native-platform-verification-coverage` from its preamble.
- [x] **AC-0010.** Parsing the real `STRAT-0002-platform-core` intent returns `Decomposed: 2026-09-24 closed-empty` from its preamble and no longer returns the literal `no`.
- [x] **AC-0011.** The adopter field table carries exactly one `Outcome co-owner` row at the constrained-when-present tier, and its `Decomposed` row names exactly the members of `DECOMPOSITION_TERMINI` plus the separately accepted literal `no`. The parity test fails if either runtime set or either row moves alone.
- [x] **AC-0012.** The `frame-intent` template, `frame-the-intent.md`, and `hand-it-to-build.md` each offer the optional co-owner field and the `closed-empty` terminus; resolving every placeholder in each preamble produces a value set accepted by `validate_live_intent()`.
- [x] **AC-0013.** `intent_corpus_lint.py --dir docs/product/intents --root .` exits zero over the real corpus after both migrations.
- [x] **AC-0014.** `lint-traceability.py` exits zero over the real repository after co-owner validation is enabled.
- [x] **AC-0015.** The Core pack's Work Intake eval exercises a hidden declaration, malformed co-owner shape, and `closed-empty`; the Product Engineering pack's Frame Intent eval exercises the optional co-owner field and the new terminus. Each named case fails when its corresponding runtime or template change is removed and passes with the change present.
- [x] **AC-0016.** Core and Product Engineering each carry a bumped, matching version in their `pack.toml` and `.claude-plugin/plugin.json`, and rebuilding from `.apm/` source leaves every generated projection byte-for-byte current.
- [x] **AC-0017.** `docs/product/changelog.md` carries Core and Product Engineering release entries that name the adopter-visible co-owner declaration and `closed-empty` terminus change, respectively.
- [x] **AC-0018.** `tools/lint-pack-test-boundary.py` exits zero, and the changed shipped files under `packs/*/.apm/` contain no repository ADR, RFC, spec path, task id, or acceptance-criterion id.
- [x] **AC-0019.** At command level, `lint-traceability.py` treats `Outcome co-owner:` inside either a closed or unclosed preamble HTML comment region as absent: it emits no unresolved-target or self-reference finding for the hidden value. The linter obtains this field through `intent_shape.read_preamble()` or an equivalent shared comment-aware preamble reader, not a second raw field regex.
- [x] **AC-0020.** `fix-a-refused-intent.md` contains a worked before/after repair for malformed co-owner shape, an unresolved target, a self-reference, and a declaration made absent by placing it inside an HTML comment. Each repair uses the actual field vocabulary and the runtime refusal class or absence behavior.

## Follow-ons

None.

## Assumptions

None.
