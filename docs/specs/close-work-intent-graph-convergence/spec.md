# Spec: Close-work intent graph convergence

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0105, RFC-0103, ADR-0119, ADR-0007, ADR-0074
- **Brief:** brief:intent-navigation-delivery
- **Discovery:** none
- **Contract:** none
- **Shape:** service

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

A maintainer or agent closing work with `close-work` gets closure verdicts whose intent and brief parent edges come from the same header derivation `navigate-intents` uses, so the two skills never disagree about which intent is an artifact's parent. Every intent ancestor a `Parent intent:` pointer records is checked, whatever its typed prefix, and a corpus fault or a refused pointer naming the ancestor refuses closure instead of reading as "no parent".

## What Changes

- New byte-identical copy of the shared derivation — `packs/core/.apm/skills/close-work/scripts/intent_graph.py`, pinned with the skill's other copies.
- The derivation's helper loaders bind each copy to the helpers in its own skill folder — both copies of `intent_graph.py`.
- The `children` arm of the descendant closure and the upward ancestor walk take parent edges from the copy — `close-work/scripts/closure_index.py`. Its own `Parent intent:` value matching and the reference-kind vocabulary it carried are removed, with that vocabulary's parity check in `tools/check_closure_terminality_parity.py`.
- Two closure refusal reasons, `intent-graph-unavailable` and `parent-edge-refused` — `closure_index.py`, documented in `guides/core/how-to/close-and-disposition-work.md`.
- The brief-route and spec-route arms keep reading the delivery resolver's snapshot unchanged.
- `closure-eligibility-check`'s read-bound criteria 0024, 0025, and 0037 are superseded in part by this spec's AC-0012 and AC-0013, recorded on that spec's `Status:` line.
- Delivered through the `feature/intent-navigation` integration branch as a `core` patch release.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User procedure | Two new refusal reasons a closer can meet | `guides/core/how-to/close-and-disposition-work.md` § the closure verdict codes (whole-section refresh: its list is titled for delivery codes only) | `core` maintainer | Guide passes `tools/lint-guide-titles.py`, `tools/validate_guides.py`, and `tools/lint-guides-no-repo-only-refs.py` | Each new reason is listed with its cause and its remedy |
| Architecture | The derivation gains a consumer and a copy | `packs/core/DESIGN.md` § Intent-edge derivation: source, copies, pins, and consumers | `core` maintainer | Section updated | Names `close-work` as a consumer, the copy's path and its pin, and states that `close-work` holds no second parent-edge parser |
| Historical contract pointer | A shipped contract's read bounds change | `docs/specs/closure-eligibility-check/spec.md` `Status:` line | `core` maintainer | AC-0014's test | The line names this spec and the three superseded criteria; the body is unchanged |
| Release history | A `core` behaviour change | `docs/product/changelog.md` `[core][3.1.1]`; `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` at `3.1.1` | `core` maintainer | Changelog entry with a `### Highlights` bullet; versions match | Entry names the wider ancestor walk and the two refusal reasons |
| Executable proof | Contract tests for the copy and the closure arms | `packs/core/tests/skills/close-work/`; the existing copies and terminality-parity tests | `core` maintainer | Dispatched `build-check`, `test-corpus`, and `test-roster` runs green on the pull request's last commit before its ledger-only record commit, with run ids in that record | Every acceptance criterion's named test is green |
| Verification record | The one-time verdict comparison over the real corpus | `docs/specs/close-work-intent-graph-convergence/notes/verification-ledger.md` (repository-durable) | Implementer | The comparison script's source, its base commit, its exit code, and its per-cause counts | Ledger present and cited by the closing PR |

## Agent Rules

### Always do

- Take every intent and brief `Parent intent:` edge `close-work` uses from its bundled copy of the derivation.
- Keep the copy byte-identical to `navigate-intents/scripts/intent_graph.py`, and add it to the test that pins the skill's other copies.
- Refuse closure when the derivation fails or a refused parent pointer bears on the decision; never read either as "no parent".
- Merge to `feature/intent-navigation`, not to the default branch.

### Ask first

- Any change to what the derivation returns, beyond the helper-loader binding.
- Any verdict difference over the real corpus that the three causes in AC-0015 do not explain.
- Any change to the brief-route or spec-route arms, or to the delivery resolver.

### Never do

- Never parse a `Parent intent:` value in `closure_index.py`.
- Never import across skills; the copy is loaded from `close-work`'s own `scripts/` folder.
- Never read `workspace.toml` for a parent edge.
- Never add a runtime dependency outside the Python standard library, a new module beyond the copy, or a persisted index.
- Never edit the body of `closure-eligibility-check`'s spec; only its `Status:` line changes.

## Testing Strategy

- **TDD (AC-0002, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013):** Contract tests over temporary fixture corpora drive the real derivation copy through `check_ancestor_closure` and `resolve_intent_ancestors`. Each arm, refusal, and read bound has its own fixture, because each is an invariant over constructed inputs.
- **Goal-based check (AC-0001, AC-0003, AC-0014):** A byte comparison, a source scan, and a status-line read. Each is a one-line property of a file, so a fixture would add nothing.
- **Goal-based check over the real corpus (AC-0015):** A comparison script runs the pre-change and post-change `closure_index.py` side by side at the delivery's base commit. It exits non-zero on any difference it cannot attribute. Its output is recorded in the verification ledger. This is a goal-based record because it measures one corpus at one commit, not an invariant.

## Acceptance Criteria

### The copy

- [ ] **AC-0001.** `packs/core/.apm/skills/close-work/scripts/intent_graph.py` is byte-identical to `packs/core/.apm/skills/navigate-intents/scripts/intent_graph.py`, checked by the test that pins the skill's other byte-identical copies.
- [ ] **AC-0002.** With both copies of `intent_graph.py` loaded in one interpreter, in either order, each copy's confinement helper and delivery resolver are the files in that copy's own `scripts/` folder.
- [ ] **AC-0003.** No line of `close-work/scripts/closure_index.py` reads a `Parent intent` key from a parsed preamble. The only `Parent intent` reads it keeps are of the delivery resolver's snapshot provenance records.

### Descendants

- [ ] **AC-0004.** For an ancestor whose terminus is `children`, its direct intent children are exactly the live intents whose `Parent intent:` edge the derivation resolves to the ancestor's node. A fixture covers each of the `intent:`, `capability:`, `outcome:`, and `opportunity:` prefixes and a repository path to the ancestor's file.
- [ ] **AC-0005.** A tombstone file whose `Parent intent:` names an ancestor is never a descendant of that ancestor.

### Ancestors

- [ ] **AC-0006.** For an intent or a brief, `resolve_intent_ancestors` returns every live intent reached by following resolved `Parent intent:` edges from it, nearest first. The chain continues through every hop, whatever the typed prefix of each.
- [ ] **AC-0007.** For a spec, the first ancestors are the intents the delivery resolver's snapshot names for it: feature intents from its delivery relations, and other intents from its `Discovery:` provenance records. Each one's own ancestors follow, under AC-0006.
- [ ] **AC-0008.** A brief whose `Parent intent:` names an intent with the same slug as the brief returns that intent as its nearest ancestor.

### Refusals

- [ ] **AC-0009.** When the derivation fails with an integrity failure, a closure decision that needs it refuses with the reason `intent-graph-unavailable: <code>`, where `<code>` is the derivation's failure code. `resolve_intent_ancestors` raises a refusal with the same reason.
- [ ] **AC-0010.** A closure decision for ancestor `A` with a `children` terminus refuses with the reason `parent-edge-refused` when the derivation refuses a live intent's `Parent intent:` edge whose recorded value, or one of whose recorded values, names `A`.
- [ ] **AC-0011.** `resolve_intent_ancestors` raises a refusal with the reason `parent-edge-refused` when the derivation refuses the `Parent intent:` edge of the walked artifact or of any ancestor it reaches. A fixture covers each refusal state the derivation can return for that field, including a parent that is a tombstone.

### Read bounds

- [ ] **AC-0012.** A closure decision runs the derivation once when a `children` terminus is on its closure, and never otherwise. A fixture whose closure names only `brief` or `spec` termini, or whose terminus is `closed-empty` or `direct-light`, runs it zero times. This supersedes `closure-eligibility-check`'s criterion 0025 for a decision that runs the derivation.
- [ ] **AC-0013.** Outside the derivation, `close-work`'s own reader opens each artifact at most once per decision. It opens only artifacts in the returned descendant set. This supersedes `closure-eligibility-check`'s criteria 0024 and 0037, which counted every open from the check's entry to its verdict.
- [ ] **AC-0014.** `docs/specs/closure-eligibility-check/spec.md`'s `Status:` line reads `Shipped (superseded in part by` and names this spec and its criteria 0024, 0025, and 0037. Every one of its `- [x]` criterion lines is unchanged from the delivery's base commit.

### Verdict bound

- [ ] **AC-0015.** At the delivery's base commit, a comparison runs the pre-change and post-change `closure_index.py` over the real corpus. It records, for every live intent, brief, and spec, its ancestor chain, and for every distinct ancestor its verdict kind and reason. It attributes every difference to exactly one of three causes:
      1. A parent hop written with `capability:`, `outcome:`, or `opportunity:`.
      2. A slug lookup that matched a tombstone.
      3. A parent intent that shares its slug with the walking artifact.

      It exits non-zero on any difference it cannot attribute. Its exit code and per-cause counts are recorded in the verification ledger.

## Follow-ons

none

## Assumptions

none
