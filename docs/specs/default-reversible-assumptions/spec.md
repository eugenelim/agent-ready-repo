# Spec: default reversible assumptions

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
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
- The chat block gains a `## Defaulted` heading, and the empty-list confirmation stops only for a wait-class item — same step.
- Each defaulted item is written to the spec's `## Assumptions` as a `Defaulted:` line — same step, and the `## Assumptions` comment in `packs/core/.apm/skills/new-spec/assets/spec.md`.
- The anti-pattern about writing the body early names the waiting items — `SKILL.md` § Anti-patterns.
- Two eval cases — `packs/core/.apm/skills/new-spec/evals/evals.json`.
- A content-test suite — `packs/core/tests/skills/new-spec/test_default_reversible_assumptions.py`.
- The adopter how-to and the core explanation describe the new stop — `guides/core/how-to/plan-and-execute-non-trivial-work.md`, `guides/core/explanation/core-pack.md`.
- The core version, a core changelog fragment, and the self-hosted projections.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | The skill's assumptions gate is the rule an authoring agent follows | `packs/core/.apm/skills/new-spec/SKILL.md` step 3 and § Anti-patterns; `assets/spec.md` § Assumptions | core pack maintainers | content tests green | suites green at the delivery commit; projections regenerated |
| User-facing promise | Adopters read when the skill stops for them | `guides/core/how-to/plan-and-execute-non-trivial-work.md` step 3; `guides/core/explanation/core-pack.md` | eugenelim | AC-0012 grep recorded in the ledger | ledger records it at delivery |
| Release history | A non-cosmetic pack change ships under a new version | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, a core fragment in `docs/product/changelog.d/` | core pack maintainers | version-equality assertion | `tools/check-core-release.py` result recorded in the ledger |
| Decision rationale | not applicable | — | — | the rule reuses step 3's existing reversibility test and protected-class list, so no new decision record is needed | — |
| Current architecture | not applicable | — | — | no module, boundary, or interface moves | — |

## Agent Rules

### Always do

- Reuse step 3's existing reversibility test and protected-class list by pointing at them; state neither a second time.
- Keep every sentence an existing test pins in the files this change edits, including `Surface the Unverified list and wait` and the routing table's reversibility condition, which this change does not widen.
- Bump `pack.toml` and `.claude-plugin/plugin.json` together, and regenerate projections with self-host rather than editing them.
- Rebase onto freshly fetched `origin/main` before opening the PR, then rebuild projections.

### Ask first

- Adding any class to the wait list beyond the five AC-0001 names, or removing one.
- Any change to the load-bearing-claim routing table in step 3.

### Never do

- Let a default approve the spec, skip `spec-approved` or `plan-approved`, or let a defaulted item settle a load-bearing claim the routing table sends before approval.
- Default an item that is a product or preference call, touches a protected class, is irreversible, or has no stated default.
- Cite this repository's internal records in shipped pack content, or edit an adapter projection except through self-host.

## Testing Strategy

- **Shipped skill guidance (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009):** goal-based, by pytest content tests in `packs/core/tests/skills/new-spec/test_default_reversible_assumptions.py`, each reading step 3 alone (from `3. **Surface assumptions before writing any spec body` to `\n3a. `), the anti-patterns section, or the template's `## Assumptions` section, with whitespace flattened. Written red before the guidance changes.
- **Pinned texts survive (AC-0010):** the existing new-spec suites, run unchanged.
- **Evals (AC-0011):** goal-based shape check in the same suite; the cases are not run against a model in this delivery.
- **Guides (AC-0012):** goal-based, a `grep` run once at delivery and recorded in the ledger, because a pack test may not read `guides/`.
- **Release (AC-0013, AC-0014):** goal-based, run at the gates and recorded in the ledger. The projection checks are § Closeout duties, not criteria.

**What these controls do not reach.** A content test sees that a sentence is present and where it sits. It cannot see whether an authoring agent sorts an item correctly. The eval cases document that behaviour; nothing in this delivery gates on it.

## Acceptance Criteria

`<merge-base>` is the merge base of `HEAD` with freshly fetched `origin/main`. "Step 3" is the text of `packs/core/.apm/skills/new-spec/SKILL.md` from `3. **Surface assumptions before writing any spec body` to the next `\n3a. `.

### The gate

- [ ] **AC-0001.** Step 3 states that an Unverified item waits for the owner when it is any of exactly five things: a product or preference call, a question of who may approve, sign off, or decide, an item touching a protected class, an irreversible choice, or an item with no stated default.
- [ ] **AC-0002.** Step 3 states that every other Unverified item is reversible with a stated default and proceeds on that default without waiting, and it defines "reversible" by pointing at the routing table's reversibility test; the sentence `Reversible means undoing it needs no migration, no external side effect, and no change to a user-visible contract` occurs exactly once in `SKILL.md`, and the sentence beginning `The protected classes are` occurs exactly once.
- [ ] **AC-0003.** Step 3's chat-block shape carries the headings `## Verified`, `## Unverified`, and `## Defaulted`, in that order, and its `## Defaulted` line shape names the default and what changes if it is wrong.
- [ ] **AC-0004.** Step 3 still contains `Surface the Unverified list and wait`, scopes that wait to the items left in Unverified after sorting, and states that when none is left the skill surfaces the block and proceeds without waiting.
- [ ] **AC-0005.** Step 3 states that when Unverified is empty after sorting, the highest-stakes item is named, and the skill asks the owner to confirm that item specifically and waits only when it falls in a wait class; otherwise it is logged under `## Defaulted` and the skill proceeds.
- [ ] **AC-0006.** Step 3 states that each defaulted item is written to the spec's `## Assumptions` as one line beginning `Defaulted:`, naming the default, what changes if it is wrong, and who settles it, and states that a default does not approve the spec.
- [ ] **AC-0007.** Step 3 states that defaulting decides only whether an item waits, and that a load-bearing claim still routes by the routing table.
- [ ] **AC-0008.** In step 3, the sorting rule (AC-0001) precedes `Surface the Unverified list and wait`, which precedes the line beginning `Only once`.

### The template and anti-patterns

- [ ] **AC-0009.** The `## Assumptions` section of `assets/spec.md` admits three shapes — `open question`, `named gap`, and `defaulted assumption` — and gives the `Defaulted:` line format; the anti-patterns section of `SKILL.md` names writing the spec body before every waiting item is confirmed.
- [ ] **AC-0010.** Every test under `packs/core/tests/skills/new-spec/` passes, and each assertion in an existing file there that differs from `<merge-base>` is named in the ledger with the step-3 sentence that moved it.

### Evals and guides

- [ ] **AC-0011.** `new-spec`'s `evals/evals.json` holds one case where a reversible assumption with a stated default proceeds and is logged as `Defaulted:`, and one where an assumption touching a migration waits for the owner; each carries `id`, `prompt`, `expected_output`, and a non-empty `assertions` list.
- [ ] **AC-0012.** At delivery, step 3 of `guides/core/how-to/plan-and-execute-non-trivial-work.md` § What to expect contains `Defaulted`, and `guides/core/explanation/core-pack.md` no longer says the skill stops before building on every assumption; the ledger records both checks.

### Release

- [ ] **AC-0013.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the same version, one patch above `packs/core/pack.toml` at `<merge-base>`.
- [ ] **AC-0014.** `python3 tools/check-core-release.py --base <merge-base>` exits 0, and the ledger records it.

## Closeout

Post-run duties, run by the controller after the supervisor's run is terminal and again after the final rebase; they are not acceptance criteria.

- `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .` exit 0, and `agentbundle catalogue self-host --root . --write` leaves no tracked change after the delivery commit; the ledger records all three.
- AC-0013 and AC-0014 are re-checked against the merge base after the final rebase, because task D's Core release may land first.

## Terminal Intent

`code` — ship the sorted assumptions gate, its template line, eval cases, guide updates, and the core release with its projections.

## Follow-ons

none

## Assumptions

- Process: when every Unverified item is defaulted, the empty-list rule (AC-0005) still applies, so a Verified fact in a protected class can still stop the run — the owner's answer named only "Unverified is empty", and this reads it as "empty after sorting" (settled by: eugenelim at spec approval).
