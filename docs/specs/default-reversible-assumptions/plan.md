# Plan: default reversible assumptions

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (version bump, self-host, eval harness, no internal citations); `packs/core/.apm/skills/new-spec/SKILL.md` step 3 (the gate, its routing table, and its protected-class list); `packs/core/tests/skills/new-spec/test_load_bearing_claim_grounding.py` `_step_3` as the analogous step-scoped content test; `test_acceptance_criteria_discipline.py` (pins `Surface the Unverified list and wait` and its order after the corpus-absence rule); `test_lld_change_preserves_pinned_texts.py` (pins the reversibility condition and a 900-line body budget); `test_artifact_prose_discipline.py` (pins the template's `## Assumptions` shapes).

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none: the controller makes it
> as an in-envelope working-plan change while no execution attempt is open, and
> the run continues with every finished task still finished. Execution
> observations belong in `docs/specs/<feature>/notes/verification-ledger.md` (or
> the adopter's equivalent). A genuine error in a protected section follows the
> controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are working
> material the controller corrects in place, before or after approval, while no
> attempt is open.

## Approach

The step-3 rewrite (T1) lands first with its content tests written red, because the template line (T2) and the eval cases (T3) restate its `Defaulted:` format. The guides (T4) describe the shipped rule, so they follow T1. The release (T5) is last. The riskiest part is keeping every pinned sentence in step 3 while inserting the sort between the corpus-absence rule and the gate; the existing suites are the check.

## Constraints

- Step 3's reversibility sentence and protected-class sentence are each stated once; the new text points at them (spec Agent Rules).
- `SKILL.md`'s body stays under the 900-line budget `test_lld_change_preserves_pinned_texts.py` enforces; it is 789 lines before this change.
- No new table inside step 3: `test_load_bearing_claim_grounding.py` parses step 3's one table as the routing table.
- A pack test may not read `guides/`; AC-0012 is a delivery-time grep.
- The supervisor protects the spec directory during a worker attempt; ledger records are controller commits between attempts.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Maintainer procedure | T1, T2 | `test_default_reversible_assumptions.py` green; existing new-spec suites green | suites green at the delivery commit |
| User-facing promise | T4 | AC-0012 grep | ledger records it |
| Release history | T5 | version-equality assertion; fragment | `check-core-release.py` result recorded |

## Design (LLD)

### Design decisions

Owned by: T1, T2, T3.

**Step-3 text.** Inserted after the corpus-absence paragraph and before `**Surface the Unverified list and wait**`:

1. A **sort** paragraph: an Unverified item *waits for the owner* when it is a product or preference call, a question of who may approve, sign off, or decide, an item touching a protected class (pointing at the sentence `The protected classes are …` above), an irreversible choice, or an item with no stated default. Every other item is *reversible with a stated default* — reversible as the routing table's `cheap-with-an-oracle` row defines it — and moves from `## Unverified` to `## Defaulted` with its default named. An item you cannot place is a waiting item. Defaulting decides only whether the item waits; a load-bearing claim still routes by the table.
2. The chat-block fence gains `## Defaulted` after `## Unverified`, with the line shape `- <category>: <item> — default: <what you build on>; if wrong: <what changes>`.
3. The gate paragraph keeps `**Surface the Unverified list and wait**`, now "for confirmation or correction of every item still in it". When none is left, surface the block and proceed. The empty-list rule becomes: name the highest-stakes item; ask the owner to confirm that one specifically and wait only when it falls in a wait class; otherwise log it under `## Defaulted` and proceed.
4. `Only once …` reads "Only once every waiting item has been signed off (or none waited)", and gains one bullet: write each defaulted item into `## Assumptions` as `- Defaulted: <category>: <item> — default: <X>; if wrong: <what changes> (settled by: <owner>)`; the owner reads it at spec approval, and a default never approves the spec.

**Anti-pattern.** "Writing into the spec body before the Unverified list has been confirmed" becomes "before every waiting Unverified item has been confirmed", keeping the rest of the entry.

**Template.** The `## Assumptions` comment's "two shapes" becomes three, adding a **defaulted assumption** with the same `Defaulted:` line, and a sentence that the line is deleted once the owner confirms or corrects the default, routing the fact as for any settled item.

**Content tests.** `test_default_reversible_assumptions.py` slices step 3 with the same start and end markers `_step_3` uses, flattens whitespace as `flattened` does, and asserts phrases and their relative order. Phrases are module constants so a reworded rule fails one named assertion.

## Tasks

### T1: Sort the Unverified list at the gate

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`, `packs/core/tests/skills/new-spec/test_default_reversible_assumptions.py`

**Tests:** goal-based — content tests over step 3 and the anti-patterns section, written red first
- AC-0001: the five wait classes present in step 3.
- AC-0002: the proceed-on-default sentence present; the reversibility sentence and the `The protected classes are` sentence each counted once in `SKILL.md`.
- AC-0003: `## Verified`, `## Unverified`, `## Defaulted` in order inside step 3, and the Defaulted line shape carries `default:` and `if wrong:`.
- AC-0004: the gate phrase present, scoped to items still in the list, and the proceed-without-waiting sentence present.
- AC-0005: the empty-after-sorting rule present.
- AC-0006: the `Defaulted:` line instruction and the "does not approve the spec" sentence present.
- AC-0007: the "decides only whether an item waits" sentence present.
- AC-0008: index of the sort phrase < index of the gate phrase < index of `Only once`.
- AC-0009 (anti-pattern half): the anti-patterns section names waiting items.
- AC-0010: the existing new-spec suites, unchanged.

**Done when:** `python3 -m pytest packs/core/tests/skills/new-spec -q` exits 0.

### T2: Template admits a defaulted assumption

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/new-spec/assets/spec.md`, `packs/core/tests/skills/new-spec/test_default_reversible_assumptions.py`

**Tests:** goal-based — content test over the template's `## Assumptions` section
- AC-0009 (template half): `open question`, `named gap`, and `defaulted assumption` present, and the `Defaulted:` line format present.

**Done when:** `python3 -m pytest packs/core/tests/skills/new-spec -q` exits 0.

### T3: Eval cases

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/new-spec/evals/evals.json`, `packs/core/tests/skills/new-spec/test_default_reversible_assumptions.py`

**Tests:** goal-based — shape check
- AC-0011: two cases with ids `reversible-assumption-proceeds-on-logged-default` and `migration-assumption-waits-for-owner`, each with `id`, `prompt`, `expected_output`, and a non-empty `assertions` list.

**Done when:** `python3 -m pytest packs/core/tests/skills/new-spec/test_default_reversible_assumptions.py -q` exits 0, and `python3 -c "import json; json.load(open('packs/core/.apm/skills/new-spec/evals/evals.json'))"` exits 0.

### T4: Guides describe the new stop

**Depends on:** T1

**Touches:** `guides/core/how-to/plan-and-execute-non-trivial-work.md`, `guides/core/explanation/core-pack.md`

**Tests:** goal-based — delivery-time grep
- AC-0012: `grep -n Defaulted guides/core/how-to/plan-and-execute-non-trivial-work.md` prints a line inside § What to expect step 3; `grep -n "stops\*\* before building on them" guides/core/explanation/core-pack.md` prints nothing.

**Done when:** both greps behave as stated.

### T5: Core release

**Depends on:** T1, T2, T3, T4

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/<uuid>.md`, the self-hosted projections

**Tests:** goal-based — delivery-time checks
- AC-0013: both versions equal, one patch above `packs/core/pack.toml` at `<merge-base>`.
- AC-0014: `python3 tools/check-core-release.py --base <merge-base>` exits 0.

**Done when:** both checks pass and the ledger records them. The spec's § Closeout projection checks run after the run is terminal.

## Risks

- Task D also bumps Core. The version is re-derived from `<merge-base>` at each rebase; if D merges first, T5's version moves and the fragment's version and anchor move with it.
- An author may still mis-sort an item. The wait list errs toward waiting: an item with no default, or one the author cannot place, waits.

## Changelog
