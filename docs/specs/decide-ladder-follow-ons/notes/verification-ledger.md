# Verification ledger — DECIDE ladder follow-ons

Execution observations for this spec. The approved `spec.md` and `plan.md` hold
obligations only; observations belong here and need no amendment.

## T1 — R1 and R2 DECIDE class guards

**Stub materialization.** The three approved blocks were copied byte-identical
from `plan.md` T1, each keeping its `# STUB:` line. Intended red observed before
any deferred assertion was filled: **3 failed, 40 passed** in 1.24s, missing
`some check can reach the claimed property`, `check asserts the repaired property
itself`, and `literal sweep`.

**Mutation proofs.** Each mutation was applied by editing and restored by
editing; no `git checkout`, `reset`, or `stash` was used.

| # | Invariant | Exact mutation | Old/naive guard | New guard |
| --- | --- | --- | --- | --- |
| 1 | A claim outrunning a reachable check is strengthened, not narrowed | Restored the pre-change `narrow-the-claim` body | `test_narrow_the_claim_keeps_the_obligation_in_contract` — **1 passed** | **failed**, missing reachable-check strengthening |
| 2 | A repair's check asserts the property, not a consequence | Changed the Fix sentence to "A repair's check may assert a consequence of the repaired property." | naive repair-token guard — **1 passed** | **failed**, rejecting consequence-only checking |
| 3 | A review round closes with both traversal instruments | Replaced both instrument sentences with the pre-change one-mode sentence, keeping the repair rerun | old exact-quote guard — **1 passed** | **failed**, missing the literal-sweep obligation |
| 4 | The post-repair anchor-test rerun is obliged in its own right | Reduced the repair rule to "After a repair, run both instruments again." — traversal instruments left intact | traversal-only guard — **1 passed** | **failed**, missing `step-8a anchor-test sweep` |
| 5 | The per-round obligation names both instruments | Renamed only the semantic-walk instrument to "a second pass", leaving the literal sweep and the rerun intact | — | **failed** at the `semantic walk` assertion; restored by editing, 43 passed |

Mutation 4 is deliberately isolated: the combined mutation 3 removes both R2
rules at once and so proves nothing about the rerun obligation on its own.

**Guard correction during EXECUTE.** The stub's per-round assertions originally
pinned two exact sentence openers (`After every review round, run a literal
sweep` / `... a semantic walk`). That is a phrasing blacklist, which the spec's
`Always do` boundary forbids: it reds on a faithful rewrite and stays green when
the same claim is reworded away. It was replaced with a property assertion over
the sentences carrying the per-round obligation, then mutation-proved as row 5.
This is construction detail filled during EXECUTE — `plan.md` T1 requires the
test to pin "both traversal instruments" and scan "every traversal-instrument
sentence", and never specifies a sentence opener — so it is not a plan amendment.

**Simplify pass.** The first R2 draft stated each instrument twice and wrapped
mid-sentence. Rewriting it to one sentence per claim removed 5 body lines
(885 → 880) with no loss of obligation.

**T1 `Done when` results.**

- `pytest packs/core/tests/skills/work-loop/test_finding_response_fields.py` — **43 passed** in 0.33s
- `sed -n '11,$p' packs/core/.apm/skills/work-loop/SKILL.md | wc -l` — **880**, within the 890 ceiling and far below the 1000-line CAT-S003 error
- `make lint-ruff lint-mypy` — ruff `All checks passed!`; mypy `Success: no issues found in 139 source files`
- Portability count for `SKILL.md` — **0**, unchanged from its pre-change baseline

## T2 — upstream demotion destinations (AC-0001, AC-0002, AC-0003)

**Stub materialization.** Four approved blocks copied byte-identical, all six
`# STUB: AC-000n` lines exact. Intended red observed before deferred assertions
were filled: intent 1 failed / 6 passed (missing `Opportunity`); brief 2 failed /
6 passed (missing `Rabbit holes`, `Design artifacts`); work-loop 1 failed / 43
passed (missing `revision-bound lifecycle invalidation`).

**Mutation proofs.** Each destination deleted independently; a combined deletion
would prove nothing about any one of them. Restored by editing throughout.

| # | Invariant | Exact mutation | Existing broad test | New guard |
| --- | --- | --- | --- | --- |
| 1 | `Opportunity` is material to intent review | Deleted only `opportunity,` from the intent materiality list | **passed** | **failed** — missing `opportunity` |
| 2 | `Rabbit holes` is material to brief review | Deleted only `rabbit holes,` from the brief list | **passed** | **failed** — missing `rabbit holes` |
| 3 | `Design artifacts` is material to brief review | Deleted only `design artifacts,` from the brief list | **passed** | **failed** — missing `design artifacts` |
| 4 | Upstream and downstream pins stay distinct | Reverted the DECIDE pin sentence to content-test-only | prior pin-vocabulary guard **passed** | **failed** — missing `revision-bound lifecycle invalidation` |

Mutation 1 was re-verified independently by the controller: deleting only
`opportunity,` reds exactly `test_intent_opportunity_edit_is_material_lifecycle_change`
and leaves the other six tests, including the pre-existing broad materiality
test, green — the precise blindness that made these three omissions invisible.

**T2 `Done when` results.**

- intake-intent suite — **7 passed**
- author-delivery-brief suite — **8 passed**
- work-loop suite — **44 passed** (T1's guards intact)
- three suites together — **59 passed** in 0.29s
- `sed -n '11,$p' … work-loop/SKILL.md | wc -l` — **883**, within the 890 ceiling
- `make lint-ruff lint-mypy` — ruff and mypy clean
- Portability — **0** in each of the three shipped skill files

## T3 — mutation-proof discipline gets one routed owner

**Stub materialization.** Three approved blocks copied byte-identical with their
`# STUB:` lines. Intended red observed: **3 failed, 44 passed**. The first two
raised `FileNotFoundError` because `references/mutation-proof.md` did not exist
yet, and the routing stub failed on the missing reference. An absent artifact
supplying the red is a valid intended red under this repository's stub rules,
and the same rules forbid inventing a fixture to manufacture one — a round-2
finding proposing exactly that fixture was refuted on this authority.

**Mutation proofs.** Applied and restored by editing.

| # | Invariant | Exact mutation | Naive guard | New oracle |
| --- | --- | --- | --- | --- |
| 1 | A proof reverts to the pre-fix implementation, never a do-nothing stub | Permitted `pre-fix implementation or a do-nothing stub`, keeping every mutation keyword and `never` | keyword grep **passed** | **failed** at the stub-prohibition assertion |
| 2 | Restoration is by editing, never a Git operation | Changed restoration to `with a Git restore operation`, keeping `restore` and all forbidden-operation keywords | `restore` keyword grep **passed** | **failed** — `editing` absent |
| 3 | The routing row names this owner | Pointed the repair predicate at `state-schema.md` | generic routing-row guard **passed** | **failed** — two state-schema exceptions |

**Merge rather than duplicate.** `delivery-contract-lifecycle.md` remains the
single owner of where observations are recorded. The new reference links to its
`#verification-ledger` anchor (verified present exactly once) and does not
restate the placement rule.

**Lint repair.** `make lint-ruff` reported PIE810 on the routing-table parser
(`startswith` called three times instead of once with a tuple). Merged into a
single tuple call; no behaviour change.

**T3 `Done when` results.**

- `test_finding_response_fields.py` — **47 passed** in 0.58s
- full `packs/core/tests/skills/work-loop/` — **1055 passed, 5 skipped, 46 subtests** in 810s
- `sed -n '11,$p' … work-loop/SKILL.md | wc -l` — **884**, within the 890 ceiling
- `references/mutation-proof.md` — **22** lines, within its 24-line ceiling
- `make lint-ruff lint-mypy` — clean after the PIE810 repair
- Portability — **0** in both the new reference and `SKILL.md`
- Conditional-routing rows added — exactly **1**
