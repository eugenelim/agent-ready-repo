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

The step-3 rewrite (T1) lands first with its content tests written red; the spec's criteria fix the literal sentences, so T1 places them rather than wording them. The template line (T2) is the only home of the defaulted-assumption format that T1 points at. The eval cases (T3) follow. The guide updates were committed before approval, so the release task (T4) only checks them alongside the version. The riskiest part is keeping every pinned sentence in step 3 while inserting the sort between the corpus-absence rule and the gate; the existing suites are the check.

## Constraints

- Step 3's reversibility sentence and protected-class sentence are each stated once; the new text points at them (spec Agent Rules).
- `SKILL.md`'s body stays under the 900-line budget `test_lld_change_preserves_pinned_texts.py` enforces; it is 778 body lines before this change.
- No new table inside step 3: `test_load_bearing_claim_grounding.py` parses step 3's one table as the routing table.
- `test_acceptance_criteria_discipline.py` requires the corpus-absence paragraph to precede `Surface the Unverified list and wait`, so the sort paragraph goes between them.
- A pack test may not read `guides/`; AC-0021 and AC-0022 are greps run at the gates.
- The supervisor protects the spec directory during a worker attempt; ledger records are controller commits between attempts.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Maintainer procedure | T1, T2 | `test_default_reversible_assumptions.py` green; existing new-spec suites green | suites green at the delivery commit |
| User-facing promise | none — committed before approval; checked in T4 | AC-0021 and AC-0022 greps | ledger records them |
| Release history | T4 | version-equality assertion; fragment | `check-core-release.py` result recorded |

## Design (LLD)

### Design decisions

Owned by: T1, T2, T3.

**Step-3 placement.** Three edits inside step 3, in order:

1. A new paragraph headed `**Sort each Unverified item before you surface the list.**`, inserted after the corpus-absence paragraph. It holds, in order, the AC-0001, AC-0002, AC-0003 and AC-0004 sentences (the default is named, then checked, then the item moves to `## Defaulted`), and closes with the AC-0007 sentence.
2. The chat-block fence gains `## Defaulted` and the AC-0009 line after the `## Unverified` bullets.
3. The gate paragraph opens with the AC-0010 text, keeps the list of body sections it gates, then carries the AC-0011, AC-0012 and AC-0013 sentences, keeping today's "a vague "looks good" doesn't count" clause after `and wait`. The `Only once …` line becomes `Only once every waiting item has been signed off, or none waited:`, and its bullet list gains one bullet carrying the AC-0014 and AC-0025 sentences, placed after the `Write only what is still unresolved` bullet.

**Anti-pattern.** The entry beginning "Writing into the spec body before the Unverified list has been confirmed" becomes "… before every waiting Unverified item has been confirmed", keeping the rest of the entry.

**Template.** The `## Assumptions` comment's "Unresolved comes in two shapes" becomes three, adding a **defaulted assumption** — an item step 3 let proceed on a stated, reversible default — with the AC-0016 line. The existing "When an item is settled later … delete the line" paragraph covers the owner confirming or correcting a default.

**Content tests.** `test_default_reversible_assumptions.py` slices step 3 with the same start and end markers `_step_3` uses, the anti-patterns section from `## Anti-patterns` to end of file, and the template from `## Assumptions` to end of file; flattens whitespace as `flattened` does; and asserts each criterion's literal text as a module constant copied from the spec, one test per criterion.

## Tasks

### T1: Sort the Unverified list at the gate

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`, `packs/core/tests/skills/new-spec/test_default_reversible_assumptions.py`

**Tests:** goal-based — content tests over step 3 and the anti-patterns section, written red first
- AC-0001, AC-0002, AC-0003, AC-0004, AC-0007: each literal sentence present in step 3.
- AC-0005, AC-0006: each sentence counted exactly once in `SKILL.md`.
- AC-0008: the three headings in order inside step 3's chat-block fence.
- AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0025: each literal text present in step 3.
- AC-0015: index of the AC-0001 sentence < index of the gate phrase < index of `Only once every waiting item has been signed off`.
- AC-0017: the anti-patterns literal present.
- AC-0018: the existing new-spec suites, unchanged.
- AC-0019: `git diff <merge-base> -- packs/core/tests/skills/new-spec` lists only the new file, or each changed assertion is recorded in the ledger.

**Done when:** `python3 -m pytest packs/core/tests/skills/new-spec -q` exits 0.

### T2: Template admits a defaulted assumption

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/new-spec/assets/spec.md`, `packs/core/tests/skills/new-spec/test_default_reversible_assumptions.py`

**Tests:** goal-based — content test over the template's `## Assumptions` section
- AC-0016: the three shape names and the `Defaulted:` line present.

**Done when:** `python3 -m pytest packs/core/tests/skills/new-spec -q` exits 0.

### T3: Eval cases

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/new-spec/evals/evals.json`, `packs/core/tests/skills/new-spec/test_default_reversible_assumptions.py`

**Tests:** goal-based — shape check
- AC-0020: the two ids present, each case with `id`, `prompt`, `expected_output`, and a non-empty `assertions` list.

**Done when:** `python3 -m pytest packs/core/tests/skills/new-spec/test_default_reversible_assumptions.py -q` exits 0.

### T4: Core release and guide checks

**Depends on:** T1, T2, T3

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/<uuid>.md`

**Tests:** goal-based — checks run at the gates
- AC-0021: the how-to's `### What to expect` section contains `## Defaulted` and `Defaulted:` and not `each needing your input`.
- AC-0022: `grep -c "stops\*\* before building on them" guides/core/explanation/core-pack.md` prints 0.
- AC-0023: both versions equal, one patch above `packs/core/pack.toml` at `<merge-base>`.
- AC-0024: `python3 tools/check-core-release.py --base <merge-base>` exits 0.

**Done when:** the four checks pass and the ledger records them. The spec's § Closeout projection checks run after the run is terminal.

## Risks

- A concurrent core release may land first. The version is re-derived from `<merge-base>` at each rebase, and the fragment's version and anchor move with it.
- An author may still mis-sort an item. AC-0002's tie-break sends an item the author cannot place to the owner.

## Changelog
