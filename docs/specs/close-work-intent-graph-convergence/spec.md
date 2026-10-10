# Spec: Close-work intent graph convergence

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-10 by eugenelim, spec and plan together, after three spec-mode shaping and adversarial review rounds with every sustained Blocker and Concern resolved (reports under `.context/reviews/509c10d7-e0ac-40d4-b46d-848217991767/`); one advisory Nit is deferred.
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

A maintainer or agent closing work with `close-work` gets closure verdicts whose intent and brief parent edges come from the same header derivation `navigate-intents` uses, so the two skills never disagree about which intent is an artifact's parent. Every intent ancestor a `Parent intent:` pointer records is checked, whatever its typed prefix, no artifact is lost because it shares a slug with an artifact of another type, and a corpus fault or a refused pointer that bears on a decision refuses closure instead of reading as "no parent".

## What Changes

- New byte-identical copy of the shared derivation — `packs/core/.apm/skills/close-work/scripts/intent_graph.py`, pinned with the skill's other copies.
- The derivation's helper loaders bind each copy to the helpers in its own skill folder — both copies of `intent_graph.py`.
- The `children` arm of the descendant closure and the upward ancestor walk take parent edges from the copy — `close-work/scripts/closure_index.py`. Its own `Parent intent:` value matching and the reference-kind vocabulary it carried are removed.
- The descendant set and the ancestor walk tell artifacts apart by kind and slug, not by slug alone — `closure_index.py`.
- The parent-kind parity check now pins the kinds the derivation reads — `tools/check_closure_terminality_parity.py`.
- Three closure refusal reasons, `intent-graph-unavailable`, `parent-edge-refused`, and `artifact-not-in-graph` — `closure_index.py`, documented in `guides/core/how-to/close-and-disposition-work.md`.
- The brief-route and spec-route arms keep reading the delivery resolver's snapshot.
- `closure-eligibility-check`'s read-bound criteria 0024, 0025, and 0037 are superseded in part by this spec's AC-0012 and AC-0013, recorded on that spec's `Status:` line.
- The owner's 2026-10-10 bounds are recorded in [FEAT-0002 § Decomposition](../../product/intents/FEAT-0002-intent-graph-navigation.md#decomposition), and the brief's verdict-change constraint points at them.
- Delivered through the `feature/intent-navigation` integration branch inside its single `core` 3.1.0 release.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision record | The owner widened the verdict-change bound and superseded the read bounds | `docs/product/intents/FEAT-0002-intent-graph-navigation.md` § Decomposition, Amendment 2026-10-10; the brief's verdict-change constraint | eugenelim | Amendment present in the spec-approval change | Amendment names the third cause, the read-bound supersession, and the refusal direction |
| User procedure | Three new refusal reasons a closer can meet | `guides/core/how-to/close-and-disposition-work.md` § the closure verdict codes (whole-section refresh: its list is titled for delivery codes only) | `core` maintainer | Guide passes `tools/lint-guide-titles.py`, `tools/validate_guides.py`, and `tools/lint-guides-no-repo-only-refs.py` | Each new reason is listed with its cause and its remedy |
| Architecture | The derivation gains a consumer and a copy | `packs/core/DESIGN.md` § Intent-edge derivation: source, copies, pins, and consumers | `core` maintainer | Section updated | Names `close-work` as a consumer, the copy's path and its pin, and states that `close-work` holds no second parent-edge parser |
| Historical contract pointer | A shipped contract's read bounds change | `docs/specs/closure-eligibility-check/spec.md` `Status:` line | `core` maintainer | AC-0014's test | The line names this spec and the three superseded criteria; the body is unchanged |
| Release history | A `core` behaviour change | `docs/product/changelog.md` `[core][3.1.0]`, the integration branch's single `core` entry; `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` read `3.1.0`, and no `[core][3.1.1]` entry exists | `core` maintainer | This slice's bullets inside the `[core][3.1.0]` entry, including `### Highlights`; versions match | Entry names the wider ancestor walk, the slug-collision fix, and the three refusal reasons |
| Executable proof | Contract tests for the copy and the closure arms | `packs/core/tests/skills/close-work/`; the existing copies and terminality-parity tests | `core` maintainer | Dispatched `build-check`, `test-corpus`, and `test-roster` runs green on the pull request's last commit before its ledger-only record commit, with run ids in that record | Every acceptance criterion's named test is green |
| Verification record | The one-time verdict comparison over the real corpus | `docs/specs/close-work-intent-graph-convergence/notes/verification-ledger.md` (repository-durable) | Implementer | The comparison script's source, both commits, its exit code, its per-cause counts, and closeout timing | Ledger present and cited by the closing PR |

## Agent Rules

### Always do

- Take every intent and brief `Parent intent:` edge `close-work` uses from its bundled copy of the derivation.
- Use derived edges only for the ancestor chain and the descendant closure, the reading of FEAT-0005's Boundary condition (c) the closure check records.
- Keep the copy byte-identical to `navigate-intents/scripts/intent_graph.py`, and add it to the test that pins the skill's other copies.
- Refuse closure when the derivation fails or a refused parent pointer bears on the decision; never read either as "no parent".
- Merge to `feature/intent-navigation`, not to the default branch.

### Ask first

- Any change to what the derivation returns, beyond the helper-loader binding.
- Any verdict difference over the real corpus that the three causes in AC-0015 do not explain.
- Any change to the brief-route or spec-route arms beyond keying descendants by kind and slug, or any change to the delivery resolver.

### Never do

- Never parse a `Parent intent:` value in `closure_index.py` to find a parent. The one value test it makes is AC-0010's: whether a refused edge's recorded value names an intent, using the parent kinds the bundled resolver copy defines.
- Never import across skills; the copy is loaded from `close-work`'s own `scripts/` folder.
- Never read `workspace.toml` for a parent edge.
- Never add a runtime dependency outside the Python standard library, a new module beyond the copy, or a persisted index.
- Never edit the body of `closure-eligibility-check`'s spec; only its `Status:` line changes.

## Testing Strategy

- **TDD (AC-0002, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0017, AC-0018):** Contract tests over temporary fixture corpora drive `check_ancestor_closure` and `resolve_intent_ancestors` through the real derivation copy. Each arm, refusal, and read bound has its own fixture, because each is an invariant over constructed inputs.
- **Goal-based check (AC-0001, AC-0003, AC-0014, AC-0016):** A byte comparison, a source scan, a hash of a frozen file, and a vocabulary comparison. Each is a one-line property of files, so a fixture would add nothing.
- **Goal-based check over the real corpus (AC-0015):** A comparison script runs the pre-change and post-change `closure_index.py` side by side over one corpus. It exits non-zero on any difference it cannot attribute. Its output is recorded in the verification ledger. This is a goal-based record because it measures one corpus at one commit, not an invariant.

## Acceptance Criteria

### The copy

- [x] **AC-0001.** `packs/core/.apm/skills/close-work/scripts/intent_graph.py` is byte-identical to `packs/core/.apm/skills/navigate-intents/scripts/intent_graph.py`, checked by the test that pins the skill's other byte-identical copies.
- [x] **AC-0002.** With both copies of `intent_graph.py` loaded in one interpreter, in either order, each copy's confinement helper and delivery resolver are the files in that copy's own `scripts/` folder.
- [x] **AC-0003.** `close-work/scripts/closure_index.py` reads no `Parent intent` key from a parsed preamble and defines no parent-kind vocabulary of its own; the parent kinds it uses are those of the delivery resolver copy in `close-work/scripts/`.
- [x] **AC-0016.** `tools/check_closure_terminality_parity.py` fails when the parent kinds the delivery resolver copy in `close-work/scripts/` admits differ, in either direction, from `intent_shape.OUTCOME_CO_OWNER_KINDS`.

### Descendants

- [x] **AC-0004.** For an ancestor whose terminus is `children`, its direct intent children are exactly the non-tombstone intents whose `Parent intent:` edge the derivation resolves to the ancestor's node. A fixture covers each of the `intent:`, `capability:`, `outcome:`, and `opportunity:` prefixes and a repository path to the ancestor's file.
- [x] **AC-0005.** A tombstone file whose `Parent intent:` names an ancestor is never a descendant of that ancestor.
- [x] **AC-0018.** The descendant set tells artifacts apart by kind and slug. When a closure holds intent `X` and also a brief or spec whose slug is `X`, both are descendants, and a non-terminal one of them makes the verdict not-eligible.

### Ancestors

- [x] **AC-0006.** For an intent or a brief, `resolve_intent_ancestors` walks from that artifact's own node in the derivation and returns every non-tombstone intent reached by following resolved `Parent intent:` edges, nearest first, whatever the typed prefix of each hop. Each returned ancestor carries the `Status:` the derivation records for it and the terminus of its own `Decomposed:` field.
- [x] **AC-0017.** When the walked intent or brief has no node of its kind and slug in the derivation, `resolve_intent_ancestors` raises a refusal with the reason `artifact-not-in-graph`. The caller's `fields` argument supplies no parent edge for an intent or a brief.
- [x] **AC-0007.** For a spec, the walk is depth-first over the intents the delivery resolver's snapshot names for it: feature intents from its delivery relations, then other intents from its `Discovery:` provenance records, in snapshot order. Each first-hop intent is followed directly by its own chain under AC-0006, and an intent already returned is not returned again. A first-hop intent with no node in the derivation raises a refusal with the reason `artifact-not-in-graph`.
- [x] **AC-0008.** An artifact whose parent intent shares its slug is not cut off by that collision: a brief whose `Parent intent:` names an intent with the brief's slug returns that intent first, and a spec whose snapshot names an intent with the spec's slug returns that intent first.

### Refusals

- [x] **AC-0009.** Any failure to load or run the derivation refuses. A closure decision that needs it returns refuse with the reason `intent-graph-unavailable: <code>`, and `resolve_intent_ancestors` raises a refusal with the same reason. `<code>` is the derivation's integrity failure code, or `copy-unavailable` for any other failure.
- [x] **AC-0010.** A closure decision refuses with the reason `parent-edge-refused` when the derivation refuses a non-tombstone intent's `Parent intent:` edge that names any intent on the closure whose terminus is `children`, the evaluated ancestor included. A value names an intent when it is that intent's slug after a prefix from the resolver copy's parent kinds, that bare slug, or the repository path of that intent's file; for a `multiple_values` refusal, when any one of its values does.
- [x] **AC-0011.** `resolve_intent_ancestors` raises a refusal with the reason `parent-edge-refused` when the derivation refuses the `Parent intent:` edge of the walked artifact or of any ancestor it reaches. A fixture covers each refusal state the derivation can return for that field on that artifact's type.

### Read bounds

- [x] **AC-0012.** A closure decision runs the derivation once when a `children` terminus is on its closure, and never otherwise. A fixture whose closure names only `brief` or `spec` termini, or whose terminus is `closed-empty` or `direct-light`, runs it zero times. This supersedes `closure-eligibility-check`'s criterion 0025 for a decision that runs the derivation.
- [x] **AC-0013.** Within `close-work`'s own process, a closure decision opens each artifact at most twice, measured from the check's entry to its verdict: at most once inside the derivation and at most once by `close-work`'s own reader. The delivery resolver subprocess's reads are outside this count. `close-work`'s own reader opens only artifacts it adds to the descendant set. The input that makes the bound fire first is a diamond, where one descendant is reachable by two paths. This supersedes `closure-eligibility-check`'s criteria 0024 and 0037.
- [x] **AC-0014.** `docs/specs/closure-eligibility-check/spec.md`'s `Status:` line reads `Shipped (superseded in part by` and names this spec and its criteria 0024, 0025, and 0037. The file's content, with its `Status:` line removed, hashes to the SHA-256 value it had at the delivery's base commit, recorded in the test.

### Verdict bound

- [x] **AC-0015.** A comparison runs the pre-change `closure_index.py` (from the delivery's base commit) and the post-change one (from the delivery's head) over one corpus, the delivery's base commit. It records, for every non-tombstone intent, every brief, and every spec, its ancestor chain, and for every distinct ancestor its descendant set and its verdict kind and reason. It attributes every chain or descendant-set difference to exactly one of the causes in FEAT-0002's 2026-10-07 and 2026-10-10 owner Amendments:
      1. A parent hop written with `capability:`, `outcome:`, or `opportunity:`.
      2. A slug lookup that matched a tombstone.
      3. A slug shared by artifacts of two types.

      A verdict difference is attributed to the cause of the chain or descendant-set difference beneath it; one with no such difference is unattributed. The comparison exits non-zero on any unattributed difference. Its exit code and per-cause counts are recorded in the verification ledger.

## Follow-ons

none

## Assumptions

none
