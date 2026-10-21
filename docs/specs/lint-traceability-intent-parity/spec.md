# Spec: Lint traceability intent parity

- **Status:** Approved
- **Approved:** 2026-10-21 by the repository owner, spec and plan together, after a clean shaping review and a clean adjudicated adversarial review in round 3.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0103 D2; RFC-0105 D1; ADR-0007; ADR-0074
- **Brief:** brief:intent-navigation-delivery
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> `Agent Rules`, `Testing Strategy`, and `Acceptance Criteria` are contract.
> `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons`, and `Assumptions`
> are working material.

## Outcome

A maintainer running `lint-traceability.py` gets the same node id for every intent file as `navigate-intents` derives for it, because both read the intent's kind, slug and retirement from its visible preamble by one rule. A build-check step compares the two over the real `docs/product/intents/` corpus and fails, naming each file, on any difference.

## What Changes

- `lint-traceability.py` reads an intent file's `Kind:`, `Level:`, `Slug:` and `Tombstone:` from its visible preamble, by the navigator's field-line grammar — `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py`.
- The ladder recognizer skips tombstones, as the intent recognizer already does.
- A pack-local fixture suite holds `lint-traceability`, `lint-graph-pointers` and the navigator to one verdict per fixture — `packs/core/tests/skills/work-loop/`.
- A roster parity check compares the lint and the navigator over the real corpus — `tests/roster/`, with its named `build-check` step.
- The living architecture page's sentence on intent-ladder markers names the preamble — `docs/architecture/work-intake-and-artifact-routing.md`.
- Core ships the change as the next patch release.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | The lint's intent reading changes | `lint-traceability.py` docstrings for `recognize_ladder`, `recognize_intents` and `_is_tombstone` | Core maintainer | Fixture suite and parity suite | Docstrings state the preamble-only reading and cite the navigator as the rule's other port |
| Current architecture | The architecture page describes where the lint finds ladder markers | `docs/architecture/work-intake-and-artifact-routing.md` § 8 | Architecture maintainer | Whole-section read against source | The ladder-marker sentence says the markers are read from the intent's preamble |
| Release history | Core runtime content changes | `docs/product/changelog.d/` fragment; `packs/core/pack.toml` and `.claude-plugin/plugin.json` | Core maintainer | Catalogue verify; changelog checks | One outcome-led fragment for the next Core patch |
| Eval coverage | `packs/AGENTS.md` requires an eval update with a non-cosmetic pack change | `packs/core/.apm/skills/work-loop/evals/evals.json` | Core maintainer | Eval JSON schema checks | One case on a body-only `Kind:` |
| Verification record | Gate runs and corpus counts need a stable home | `docs/specs/lint-traceability-intent-parity/notes/verification-ledger.md` | Implementer | Run ids and counts | Ledger names the head revision it verifies |

`packs/product-engineering/.apm/skills/intent/references/intent-model.md` § Placing an intent on the traceability chain names the markers without saying where they are read, and stays unchanged.

## Agent Rules

### Always do

- Mirror the navigator's reading by hand in `lint-traceability.py`, and pin the agreement in tests. The rule's owner is `intent-navigation` AC-0004.
- Keep the ladder recognizer's filename-stem fallback for a file with no preamble `Slug:`.
- Run the real-corpus parity check against the pack sources under `packs/core/.apm/`, not a projected copy.
- Bump Core to exactly the next patch above `main` at landing time.

### Ask first

- The real-corpus parity check finds a difference that only a corpus edit would fix.
- A change to `navigate-intents` or `lint-graph-pointers.py` source looks necessary.
- Commit, push, or merge any part of this work.

### Never do

- Import across skills, or load the navigator from the lint at run time.
- Change the navigator's derivation, its spec, or `lint-graph-pointers.py` behavior.
- Change how the lint reads briefs, specs, screens, contracts, components, or the `Outcome co-owner:` field.
- Add a dependency, a top-level directory, a new lint script, or a new finding code.
- Weaken or delete an existing assertion to make a suite pass.
- Edit generated adapter projections by hand.

## Testing Strategy

- **TDD — lint reading (AC-0001, AC-0002, AC-0003):** fixture intent files in a temporary root drive `recognize_ladder` and `recognize_intents` directly. The reading is a compressible rule over constructed inputs.
- **TDD — three-port agreement (AC-0004):** the same fixtures run through the lint, `lint-graph-pointers.py`, and the navigator's `derive`, compared per file. This is the parity pinning that stands in for the banned import.
- **Goal-based check — real corpus (AC-0005):** one roster test over the repository's own intents. A measurement over the real tree, not an invariant over constructed inputs.
- **Goal-based check — wiring and projection (AC-0006, AC-0007):** the CI-parity and gate-chain lints, and catalogue verification, decide these.

## Acceptance Criteria

- [ ] **AC-0001.** For each fixture intent file below, `lint-traceability` registers exactly the node id that `intent-navigation` AC-0004 assigns to it, and no other `outcome`, `opportunity`, `capability`, or `intent` node for that file:
      - `Kind: outcome` appearing only below the first `## ` heading;
      - `Kind: opportunity` appearing only inside an HTML comment in the preamble;
      - `` Kind: `outcome` extra ``;
      - a lowercase `**kind:** outcome` field line;
      - a `**Kind:** outcome` that is not on a line starting `- **`;
      - `Kind: opportunity (note)` with `Level: capability`;
      - `` Kind: `outcome (note)` ``;
      - `` Level: `capability (note)` `` with no `Kind:`;
      - `Level: Capability` with no `Kind:`.
- [ ] **AC-0002.** The lint takes a live intent's slug from the first visible preamble `Slug:` field line. A `Slug:` only below the preamble or only inside a comment is not read. A ladder file with no such line keeps its filename stem as the slug. A non-ladder file with no such line gets no node and a note naming the file. A first `Slug:` value that is empty, `none` in any letter case, or a single-word `<…>` placeholder counts as no such line.
- [ ] **AC-0003.** A file whose visible preamble has a `Tombstone:` field line, with any value, gives the lint no `outcome`, `opportunity`, `capability`, or `intent` node. That holds when the file also has `Kind: outcome`. A `Tombstone:` only below the preamble or only inside a comment does not retire the file.
- [ ] **AC-0004.** For every AC-0001 and AC-0003 fixture whose visible preamble `Slug:` the navigator admits and is not `none`, and whose `Tombstone:`, if any, has a non-empty value, the three ports agree per file:
      - on a live file, the lint's node id equals the navigator's, and the lint's node kind equals the `lint-graph-pointers.py` registered kind;
      - on a retired file, neither the lint nor the navigator derives a node, and `lint-graph-pointers.py` marks it retired.

      AC-0002's fixtures stay outside this check, because the navigator refuses a live intent with no admitted `Slug:`. The AC-0003 fixture with an empty `Tombstone:` value stays outside it too, because `lint-graph-pointers.py` reads that file as live.
- [ ] **AC-0005.** Over the real `docs/product/intents/` directory, for each file path, the set of node ids the lint's ladder and intent recognizers derive together equals the set the navigator derives. The navigator's set is one id for a live intent and empty otherwise. On any difference, the check fails and names each differing path with both sets. If the navigator refuses the derivation, the check fails rather than skips. If the compared corpus lacks one of the four kinds, the check fails as vacuous.
- [ ] **AC-0006.** The real-corpus check runs as its own named step in `.github/workflows/build-check.yml`, above the bulk roster step. The fixture suite runs as its own `make build-check` gate-chain step. `tools/lint-ci-parity.py` and `tools/test_build_gate_chain.py` pass with both registered.
- [ ] **AC-0007.** The self-hosted copies of `lint-traceability.py` are byte-identical to the pack source, and `agentbundle catalogue verify --root .` reports no drift.

## Follow-ons

None.

## Assumptions

- Technical: `lint-graph-pointers.py` treats a preamble `Tombstone:` line with an empty value as live, while the navigator and this lint treat it as retired. This spec does not change that script, so the three-port agreement is ungrounded for an empty `Tombstone:` value. No file in the real corpus has one. The owner accepted this gap at approval on 2026-10-21.
