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

## T4 — changed skills update their eval registers

One case added per changed skill, matching each register's existing schema
(`skill_name` + `evals`; case fields `id`, `prompt`, `expected_output`,
`assertions`).

| Register | New case id | Content pin tokens found |
| --- | --- | --- |
| work-loop | `decide-repair-traversal` | `literal sweep`, `semantic walk` |
| intake-intent | `intent-opportunity-materiality` | `Opportunity` |
| author-delivery-brief | `brief-materiality-destinations` | `Rabbit holes`, `Design artifacts` |

**T4 `Done when` results.**

- identifier command — exactly one owning case per register (work-loop:712,
  intake-intent:88, author-delivery-brief:69)
- three bounded content-pin commands — every named token present inside its
  matched case region
- `agentbundle catalogue lint --root . --deep` — **exit 0, 70 findings, 0 errors**;
  every finding is a pre-existing WARN category. `work-loop/SKILL.md` carries the
  expected CAT-S003 body-length WARN at 884 lines, which it already carried at
  874 before this change (the warn threshold is 500; the error threshold is 1000)
- JSON validity re-verified by parsing each register: 62, 9 and 7 cases
- Portability, before → after — work-loop **14 → 14** (pre-existing permitted
  illustrative adopter examples, deliberately preserved), intake-intent
  **0 → 0**, author-delivery-brief **0 → 0**

No eval was executed and none is claimed to have run; these registers are not
driven by any suite.

## T5 — source release and roadmap records

**Deviation from the approved contract: version 2.25.25 → 2.25.27.** The spec's
`Always do` bullet and T5 name 2.25.25. Between plan approval and this task, a
peer released both 2.25.25 and 2.25.26 to `main`, so the approved number no
longer existed to take and bumping to it would have collided silently — no gate
in this repository catches a duplicate pack version. The branch was rebased onto
`origin/main` (5 commits replayed cleanly) and both carriers moved 2.25.26 →
**2.25.27**, the next free patch. The contract's substance — bump both carriers
by one matching patch — is met; only the literal number moved, and it moved
because of external release traffic rather than any design change. Owner
confirmed this disposition rather than opening a controlled amendment.

**Second drift, absorbed without deviation: the `/now/` obligation.** The plan
required regenerating and committing `web/src/lib/now-highlights.generated.json`.
`main` has since removed that obligation — `docs/product/AGENTS.md` now reads
"Edit the changelog and stop there", the old
`test_the_committed_now_projection_matches_the_changelog_source` is gone, and the
path is listed at `.gitignore:146`. The plan's commands were still run and both
pass, so no `Tests` entry was skipped. The file is nonetheless still *tracked*
(`.gitignore` does not apply to an already-tracked path), so the regeneration is
committed to keep the tree clean for `FORCE=1 make build-self`, which refuses a
dirty tree. The tracked-but-ignored state is pre-existing and is not repaired
here.

**T5 `Done when` results.**

- both carriers at **2.25.27**, exactly one occurrence in each, no `2.25.26`
  remaining in either
- changelog — a free-standing `## [core][2.25.27] — 2026-09-13` directly beneath
  `[Unreleased]` and above 2.25.26; no released section edited
- highlights — four `-` bullets; all four verified present in the regenerated
  projection payload (paragraph form is dropped silently, so bullet form was
  checked rather than assumed)
- `python3 tools/build-site.py --journeys-only` — 153 released highlights in 104
  release groups
- `python3 -m pytest tools/test_build_site_routing.py -k now -q` — **1 passed**
- roadmap register — all four rows now read `→ spec/decide-ladder-follow-ons`;
  **0** rows remain `Open`
- R4 evidence corrected in the register: the row claimed one non-state-change
  occurrence of "mutation"; there are three (`SKILL.md:528`,
  `references/delivery-contract-lifecycle.md:71`, `scripts/_loop_guards.py:578`).
  None states an obligation, so the row's substantive claim stands
- portability, measured against the recorded per-file baseline — work-loop evals
  **14** (unchanged, pre-existing permitted illustrative examples); the other six
  touched `packs/` files **0** each. No new match introduced

## T6 — self-host projections

`FORCE=1 make build-self` run from the clean T5 source commit (it refuses a dirty
tree, which is why the source and projection commits are separate).

- 14 generated files changed, every one under `.agents/` or `.claude/`; no source
  file was touched by the build
- `references/mutation-proof.md` projected to both adapters
- projected `work-loop/SKILL.md` body — **884** lines, matching source exactly
- `marketplace.json` unchanged: `core` is one of 7 packs excluded from the
  marketplace as not installable at user scope, so the forced rebuild correctly
  produced no marketplace delta
- `test_ac11_work_loop_projections_are_byte_identical_to_the_source` — **passed**
- `test_self_host_skill_projections_match_their_canonical_sources` — **passed**
- `git diff --check` — clean

## T7 — complete bounded change passes local gates

- three touched pack suites together — **62 passed** in 0.64s
- both projection roster nodes — **2 passed**
- `make lint-ruff lint-mypy` — ruff `All checks passed!`; mypy `Success: no issues
  found in 139 source files`
- `work-loop/SKILL.md` body — **884** lines, within the 890 ceiling and 116 below
  the 1000-line CAT-S003 error
- `lint-spec-status.py --root .` — **exit 0**, spec metadata clean (1 of 457 specs
  changed against `origin/main`)

Heavier corpus and roster-wide runs are left to CI, per this repository's stated
local gate.

## Post-GATES review round 1 — repairs

Three blockers raised; one refuted, two sustained.

**Refuted — "the strengthen-or-narrow choice is not decidable".** The shipped
`narrow-the-claim` text reproduces the governing deferred criterion's own wording
verbatim, and the operational definition of reach the reviewer asked for is a
*different* deferred criterion owned by the gating intent. Applying the proposed
fix would have imported deferred criterion content into shipped prose, which this
change exists to avoid. No edit made.

**Sustained blocker — materiality guarded by occurrence, not classification.**
Both destination oracles asserted only that the destination name appeared
somewhere in the materiality region, so a text that listed the destination and
then reclassified it as nonmaterial kept AC-0001 through AC-0003 green. The
oracle is now bounded to the positive `material means …` declaration — the list
sentence up to its terminating period.

| Invariant | Exact mutation | Old occurrence oracle | New bounded oracle |
| --- | --- | --- | --- |
| `Opportunity` is classified material, not merely mentioned | Removed `opportunity,` from the positive list and appended "A change to opportunity is nonmaterial." — an exact reversal that leaves the word present in the region | **PASS** — would not have caught the reversal | **failed**, as required |

**Sustained advisory — the post-repair selector was keyed to an exact opener.**
Verified both halves: a negation stayed green and a faithful paraphrase red. The
adjudicator scoped the required outcome to subject-based selection at the seam
`round_scope` already uses, and ruled the reviewer's general
subject/action/polarity classifier over-broad. The selector now keys on the
subject `a repair`.

| Mutation | Required behaviour | Observed |
| --- | --- | --- |
| Faithful paraphrase: `After a repair` → `Following a repair` | stay GREEN (the old opener-keyed guard would have red) | **47 passed** |
| Remove the rerun obligation, leaving both instruments intact | RED | **failed**, as required |

**Deliberately not fixed: the polarity half.** Asserting polarity over free prose
admits several defensible implementations and none is fixed by code, test, schema
or stated constraint; the adjudicator ruled it needs a mechanizable criterion
before it can be pinned at all. Pinning it here would also create the kind of
unmechanizable obligation the gating intent exists to keep out of criterion form.
Recorded rather than silently dropped.

**Gates after repair.**

- three touched pack suites — **62 passed**
- `make lint-ruff lint-mypy` — clean
- both projection roster nodes — **2 passed**; only test files changed this
  round, so no reprojection was required

## Post-GATES review round 2 — all findings refuted

Four findings raised, **all four refuted**; main-loop result `Clean`. Two of the
four originated in round-1 repairs.

The materiality guard had by then held three strictness positions in three
rounds, which is the signal that a control is measuring something its medium
cannot decide. The adjudication tested finding 1's own demonstration and it does
not hold: "material means every listed change except Opportunity" reds the
`unresolved questions` membership assertion, and the alleged sentence-split
false-red is unreachable because the shipped declaration is a single sentence and
the normalizer moves no period. It also found the proposed structured-list
mechanism non-convergent — exact list items would decide an in-list reversal
while relocating the same polarity question to the next sentence, which is
strictness position (i), already ruled too loose.

Disposition taken: **KEEP the guard as proportionate, and SHRINK the claim rather
than harden a fourth time.** The helper's docstring asserted that bounding to one
sentence "is what makes the guard polarity-aware", which overstates what a
substring test delivers. It now states what the check actually performs, names
the in-declaration exclusion as out of its reach, and says deciding polarity over
free prose needs a mechanism this medium does not offer. That is this change's
own `narrow-the-claim` rule applied to its own work: no check here can reach the
general polarity claim, so the claim shrinks to what the check reaches.

The other three refusals rested on authority: phrase-binding is the *prescribed*
behaviour for a content pin with no criterion; the repair-selector collision
requires prose that does not exist and would fail loud rather than silent; and
the reference test is required to *name* the placement exception, not verify it.

Gates after the shrink: three touched suites **62 passed**; ruff and mypy clean.
