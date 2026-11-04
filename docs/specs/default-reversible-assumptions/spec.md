# Spec: default reversible assumptions

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
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

A spec owner using `new-spec` is asked to stop only for the assumptions they alone can settle: product or preference calls, who may approve or decide, anything in a protected class, irreversible choices, and items with no stated default. Every other open assumption proceeds on a stated, reversible default that is logged in the spec, so the owner reads each default at spec approval instead of waiting on it before the body is written.

## What Changes

- The assumptions gate sorts each Unverified item into "waits for the owner" or "reversible with a stated default", and only the first kind blocks — `packs/core/.apm/skills/new-spec/SKILL.md` step 3.
- The chat block gains a `## Defaulted` heading, and the no-candidates confirmation stops only for a wait-class item — same step.
- Each defaulted item is written to the spec's `## Assumptions` as a defaulted assumption — same step, pointing at the line format in the `## Assumptions` comment of `packs/core/.apm/skills/new-spec/assets/spec.md`, its only home.
- The anti-pattern about writing the body early names the waiting items — `SKILL.md` § Anti-patterns.
- Two eval cases — `packs/core/.apm/skills/new-spec/evals/evals.json`.
- A content-test suite — `packs/core/tests/skills/new-spec/test_default_reversible_assumptions.py`.
- The adopter how-to and the core explanation describe the new stop, drafted before approval — `guides/core/how-to/plan-and-execute-non-trivial-work.md`, `guides/core/explanation/core-pack.md`.
- The core version, a core changelog fragment, and the self-hosted projections.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | The skill's assumptions gate is the rule an authoring agent follows | `packs/core/.apm/skills/new-spec/SKILL.md` step 3 and § Anti-patterns; `assets/spec.md` § Assumptions | core pack maintainers | content tests green | suites green at the delivery commit; projections regenerated |
| User-facing promise | Adopters read when the skill stops for them | `guides/core/how-to/plan-and-execute-non-trivial-work.md` § What to expect step 3; `guides/core/explanation/core-pack.md` | eugenelim | drafted before approval; AC-0021 and AC-0022 greps recorded in the ledger | ledger records both |
| Release history | A non-cosmetic pack change ships under a new version | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a core fragment in `docs/product/changelog.d/` | core pack maintainers | version-equality assertion | `tools/check-core-release.py` result recorded in the ledger |
| Decision rationale | not applicable | — | — | the rule reuses step 3's existing reversibility test and protected-class list, so no new decision record is needed | — |
| Current architecture | not applicable | — | — | no module, boundary, or interface moves | — |

## Agent Rules

### Always do

- Reuse step 3's existing reversibility test and protected-class list by pointing at them; state neither a second time.
- Keep the defaulted-assumption line format in the template's `## Assumptions` comment only; step 3 points at it.
- Keep every sentence an existing test pins in the files this change edits, including `Surface the Unverified list and wait` and the routing table's reversibility condition, which this change does not widen.
- Bump `pack.toml` and `.claude-plugin/plugin.json` together, and regenerate projections with self-host rather than editing them.
- Rebase onto freshly fetched `origin/main` before opening the PR, then rebuild projections.

### Ask first

- Adding any class to the wait list AC-0001 fixes, or removing one.
- Any change to the load-bearing-claim routing table in step 3.

### Never do

- Let a default approve the spec, skip `spec-approved` or `plan-approved`, or let a defaulted item settle a load-bearing claim the routing table sends before approval.
- Default an item that is a product or preference call, a question of who may approve or decide, touches a protected class, is irreversible, or has no stated default.
- Cite this repository's internal records in shipped pack content, or edit an adapter projection except through self-host.

## Testing Strategy

- **Shipped skill guidance (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0025):** goal-based, by pytest content tests in `packs/core/tests/skills/new-spec/test_default_reversible_assumptions.py`. Each reads one slice with whitespace flattened — step 3, the anti-patterns section, or the template's `## Assumptions` section — and asserts the literal text the criterion fixes. Written red before the guidance changes.
- **Pinned texts survive (AC-0018, AC-0019):** the existing new-spec suites, run unchanged, and a `git diff` of that directory recorded in the ledger.
- **Evals (AC-0020):** goal-based shape check in the same suite; the cases are not run against a model in this delivery.
- **Guides (AC-0021, AC-0022):** goal-based, a `grep` run at the gates and recorded in the ledger, because a pack test may not read `guides/`.
- **Release (AC-0023, AC-0024):** goal-based, run at the gates and recorded in the ledger. The projection checks are § Closeout duties, not criteria.

**What these controls do not reach.** A content test sees that a fixed sentence is present and where it sits. It cannot see whether an authoring agent sorts an item correctly. The eval cases document that behaviour; nothing in this delivery gates on it.

## Acceptance Criteria

`<merge-base>` is the merge base of `HEAD` with freshly fetched `origin/main`. "Step 3" is the text of `packs/core/.apm/skills/new-spec/SKILL.md` from `3. **Surface assumptions before writing any spec body` to the next `\n3a. `. "Contains" compares after collapsing every whitespace run to one space.

### The sort

- [x] **AC-0001.** Step 3 contains `An item waits for the owner when it is a product or preference call, a question of who may approve, sign off, or decide, an item touching a protected class, an irreversible choice, or an item with no stated default.`
- [x] **AC-0002.** Step 3 contains `Where you cannot tell whether an item is one of these, it is.`
- [x] **AC-0003.** Step 3 contains `Every other item is reversible with a stated default` and `It proceeds on that default without waiting.`
- [x] **AC-0004.** Step 3 contains `check it against the reversibility test in the routing table above`.
- [x] **AC-0005.** `SKILL.md` contains `Reversible means undoing it needs no migration, no external side effect, and no change to a user-visible contract` exactly once.
- [x] **AC-0006.** `SKILL.md` contains `The protected classes are a security boundary, data loss or durability, migration or persisted state, a public interface, and an irreversible operation.` exactly once.
- [x] **AC-0007.** Step 3 contains `Defaulting decides only whether an item waits; a load-bearing claim still routes by the routing table.`

### The chat block and the wait

- [x] **AC-0008.** Step 3's chat-block fence carries the headings `## Verified`, `## Unverified`, and `## Defaulted`, in that order.
- [x] **AC-0009.** Step 3 contains `- <category>: <item> — default: <what you build on>; if wrong: <what changes>`.
- [x] **AC-0010.** Step 3 contains `**Surface the Unverified list and wait** for confirmation or correction of every item still in it`.
- [x] **AC-0011.** Step 3 contains `When Unverified had candidates and sorting moved every one to `## Defaulted`, surface the block and proceed without waiting.`
- [x] **AC-0012.** Step 3 contains `When there were no Unverified candidates at all, name the highest-stakes Verified item. If it is a product or preference call, a question of who may approve, sign off, or decide, an item touching a protected class, or an irreversible choice, ask the user to confirm *that one specifically* and wait`.
- [x] **AC-0013.** Step 3 contains `Otherwise list it under `## Defaulted` with `default: as verified; if wrong: <what changes>` and proceed. It stays a settled fact and is not written to `## Assumptions`.`
- [x] **AC-0014.** Step 3 contains `Write each item sorted out of Unverified into the spec's `## Assumptions` as a defaulted assumption, in the line format that section's comment gives.`
- [x] **AC-0025.** Step 3 contains `A default does not approve the spec.`
- [x] **AC-0015.** In step 3, the AC-0001 sentence precedes `**Surface the Unverified list and wait**`, which precedes `Only once every waiting item has been signed off`.

### The template and anti-patterns

- [x] **AC-0016.** The `## Assumptions` section of `assets/spec.md` names three shapes — `open question`, `named gap`, and `defaulted assumption` — and contains `- Defaulted: <category>: <item> — default: <what was built on>; if wrong: <what changes> (settled by: <owner>)`.
- [x] **AC-0017.** The anti-patterns section of `SKILL.md` contains `before every waiting Unverified item has been confirmed`.
- [x] **AC-0018.** Every test under `packs/core/tests/skills/new-spec/` passes.
- [x] **AC-0019.** Each assertion in an existing file under `packs/core/tests/skills/new-spec/` that differs from `<merge-base>` is named in the ledger with the step-3 sentence that moved it, or the ledger records that none differs.

### Evals and guides

- [x] **AC-0020.** `new-spec`'s `evals/evals.json` holds a case with id `reversible-assumption-proceeds-on-logged-default` and one with id `migration-assumption-waits-for-owner`, each carrying `id`, `prompt`, `expected_output`, and a non-empty `assertions` list.
- [x] **AC-0021.** In `guides/core/how-to/plan-and-execute-non-trivial-work.md`, the text from `### What to expect` to the next `### ` heading contains `## Defaulted` and `Defaulted:` and does not contain `each needing your input`, and the ledger records the check.
- [x] **AC-0022.** `guides/core/explanation/core-pack.md` does not contain `stops** before building on them`, and the ledger records the check.

### Release

- [x] **AC-0023.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the same version, one patch above `packs/core/pack.toml` at `<merge-base>`.
- [x] **AC-0024.** `python3 tools/check-core-release.py --base <merge-base>` exits 0, and the ledger records it.

## Closeout

Post-run duties, run by the controller after the supervisor's run is terminal and again after the final rebase; they are not acceptance criteria.

- `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .` exit 0, and `agentbundle catalogue self-host --root . --write` leaves no tracked change after the delivery commit; the ledger records all three.
- AC-0023 and AC-0024 are re-checked against the merge base after the final rebase, because a concurrent core release may land first.

## Terminal Intent

`code` — ship the sorted assumptions gate, its template line, eval cases, and the core release with its projections; the guide updates are committed before approval.

## Follow-ons

none

## Assumptions

none
