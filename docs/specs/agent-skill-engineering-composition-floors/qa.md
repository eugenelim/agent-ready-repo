# QA record — agent-skill-engineering composition floors (INI-009 slice 3a)

## What this slice is, and what it deliberately is not

Slice 3 was cut into 3a and 3b at the owner's decision on 2026-08-31. This is 3a:
the three portable composition floors, a probe-backed Claude Code pilot profile,
and the runtime capability-claim ledger those rest on. Seven runtime profiles,
the two behaviour fixtures, the `runtime-package` mode, and the router's
per-claim state reporting are 3b's, each named in `spec.md`'s Follow-ons against
the brief's slice-3b row.

## The scope change that cost two review rounds, and why it was right

The first draft carried four criteria requiring the router to report each
claim's lifecycle state and the profile roll-up, which RFC-0097 D3 mandates. It
also declared `Contract: none`. Those cannot both hold. The shipped provider
response is a closed field set; its status set is closed; a non-`ok` status is
refused if it carries any payload at all; and `profile_provenance` entries are
validated against exactly `{profile, retrieved_at, verified_at}`. There is
nowhere to put a capability state.

Round 2 surfaced this as three separate blockers — "AC17 names no status",
"AC18's guidance clause is refused by the validator", "AC19 needs fields that do
not exist" — each reading as a criterion-shape defect with its own fix. All three
were one premise being wrong. Rewording each, which the previous round's
adjudication had sustained as the general remedy, would have produced three more
findings, because no wording satisfies a contract with no field for the value.

**The signal that caught it was origin tagging.** Round 2 was asked to mark each
finding `draft-origin` or `round-1-repair`; 20 of 24 came back `round-1-repair`.
That ratio, not any individual finding, is what said the loop was thrashing
rather than converging.

## Review ledger

| Round | Raised | Sustained | Refuted | Mooted |
| --- | ---: | ---: | ---: | ---: |
| 1 — shaping | 18 | 16 | 2 | — |
| 1 — adversarial | 25 | 23 | 2 | — |
| 2 — adversarial | 24 | 14 | 7 | 3 |
| 3 — convergence | 6 | 6 | 0 | — |
| 4 — bounded cold read | 0 (clean sentinel) | — | — | — |

Every report, including the clean one, went through `finding-adjudicator`. The
clean round was recorded by byte comparison against the sentinel rather than on
the controller's account of what was said.

**Eleven proposed fixes were refuted and not applied.** Four would have made the
artifacts worse:

- Replacing a correct "four binding digests" claim with a wrong "three". The
  negative record asserts four digests at `test_foundation_corpus.py:491-502`;
  its own docstring says "triple" and is wrong.
- Splitting the re-taken-pin arithmetic from its exception clause, which is what
  keeps that exception non-vacuous.
- Enumerating the forbidden runtime-identifier set across eight unprofiled
  runtimes — an open class, where the next release defeats the list, and whose
  transcription would then need its own control.
- Replacing a determinate probe-count floor with an unmechanizable judgment
  predicate over floor prose.

## Two design defects the review caught before any code existed

**A failed probe computed `verified`.** The state function branched on probe
*presence*, so a probe that ran and failed took the present branch. That inverts
the one property the ledger exists to carry. The probe record now carries a
result and a failed probe inside its window resolves `experimental`; past its
window the elapsed window decides it.

**The verification window ran from a field an author can bump.** `last_verified`
was the base, so a row whose source was retrieved 200 days ago but whose
verification date was touched yesterday computed `verified`. It now runs from the
maximum `retrieved_at` across the row's sources — which is what RFC-0097 D3 makes
`verified` depend on — and a `last_verified` later than that is rejected.

## The retrieval measurement, and the control that changed its verdict

The raw re-measurement moved five inherited pins and read precision 0.851, which
reads as this slice degrading retrieval.

It is not. The 24 pinned cases were re-measured against the **pre-slice compiled
tree** staged from commit `02e91f1bb` — 12 topics, none of them this slice's —
under identical instructions. Three of the same five pins moved there too.

| Pin | Moves on pre-slice tree | Attribution |
| --- | --- | --- |
| `asset-or-reference` | yes | instrument |
| `authorization-at-trigger` | yes | instrument |
| `mode-loading` | yes | instrument |
| `python-extension` | no | this slice |
| `node-extension` | no | this slice |

Only two are attributable here, and both are recall losses rather than wrong
picks: each dropped `resources-scripts-and-exit-contracts` from a two-topic set
as attention spread across sixteen topics. Without the control this record would
have claimed five regressions where two exist.

**Declarations were corrected by a stated rule, not case by case.** Correcting a
declaration after seeing the measurement is how a retrieval gate becomes
vacuous, so the rule is written down and its exceptions are visible:

1. Where two independent instruments on *different trees* agree a declaration is
   too narrow, the declaration is stale and was corrected — `mode-loading` and
   `asset-or-reference`.
2. This slice's own new cases had no control and were corrected on the prompt
   text where the span is genuine — six cases.
3. Everything else keeps its declaration, and the disagreement is the finding —
   seven cases left uncorrected, including both attributable pin moves.

### Pin re-takes

Five of 24, each with prior and current value. The count of re-takes recorded
here equals the count of pins whose value differs.

| Pin | Prior | Current |
| --- | --- | --- |
| `authorization-at-trigger` | framing-and-trigger-quality | activation-discoverability-and-mode-wayfinding, framing-and-trigger-quality |
| `mode-loading` | instruction-density-and-progressive-disclosure | activation-discoverability-and-mode-wayfinding, instruction-density-and-progressive-disclosure |
| `asset-or-reference` | instruction-density-and-progressive-disclosure | instruction-density-and-progressive-disclosure, resources-scripts-and-exit-contracts |
| `python-extension` | python-and-pytest, resources-scripts-and-exit-contracts | python-and-pytest |
| `node-extension` | resources-scripts-and-exit-contracts, typescript-node-and-javascript-test-runners | typescript-node-and-javascript-test-runners |

## The ledger contract slice 3b inherits

- One fixture keyed by runtime, so 3b appends rows rather than adding files.
- `state` is stored **and** recomputed, as is `roll_up`. Storing makes the
  intended value reviewable in the diff; recomputing makes a hand-edit fail.
- The window runs forward from the maximum `retrieved_at` across a row's sources.
- Source identity is the URL that served the content **after every redirect**.
  `docs.claude.com/en/docs/claude-code/` 301-redirects to `code.claude.com/docs/en/`,
  so a pre-redirect URL still resolves while no longer naming the page read.
- A row's `probe` carries gesture, observed outcome, and whether it passed.
  `verified` requires a recorded pass; documentation alone is `experimental`.
- The required-capability set carries a `source_ref` and an `expected_count`, so
  deleting a capability from both the rows and the required set fails.

## The probe boundary

Three of seven Claude Code rows are `verified`, each by a gesture run in a live
session: skill body loading, subagent context isolation, worktree isolation. Four
are `experimental` — nesting limits, component-scoped hooks, managed hook policy,
package-supplied agent precedence — because they are documented and were not
independently exercised. That distinction is the point of the state, and shipping
seven `verified` rows on citations would have made the pilot exactly the
citation-only profile its inclusion was meant to prevent.

## Deviations from the frozen plan

- **T1 did not re-pin the brief revision on the shipped spec entries**, which
  T1's Approach called for. The foundation entry still pins `42fe891e`, a brief
  hash that stopped matching some time ago, and produces no finding in any
  canonical collection — only the active entry is refresh-evaluated. Re-pinning
  would have rewritten the derivation revision each shipped spec was built
  against. T1's two gates pass either way; this deviates from an Approach bullet,
  not from a criterion.
- **The engine's findings-remain / spec-ready cycle fired once at the end of the
  review loop rather than once per round.** The review rounds ran ahead of the
  state machine. The transition log is therefore an accurate record of *what*
  happened and an inaccurate record of *when*.
- **The per-wave engine transitions were fired in the wrong order and refused.**
  `wave-passed` is legal only from `CODE-VERIFICATION`, and each wave was still
  in `CODE-IMPLEMENTATION`, so the engine rejected all five as illegal
  transitions. The cohort wave pointer advanced independently to the last wave,
  and `wave-complete` then `gates-clean` succeeded from there, so the end state
  is coherent — but the engine log shows one wave boundary rather than six. The
  correct per-wave cycle is `wave-complete`, then `wave-passed`, then
  `wave advance`.

## Carried-forward dispositions

**The work-loop engine's absent per-task completion verb is a decided cut, not an
unfiled gap. Do not investigate it again.** `completed_task_ids` is written only
by `begin_contract_amendment`, which derives the set as
`[task for wave in waves[:current_index] for task in wave]`
(`packs/core/.apm/skills/work-loop/scripts/loop-cohort.py:743`), so completion is
wave-granular and inferred from the pointer. RFC-0099 (Accepted) cuts per-task
recording explicitly at lines 999-1006, and the owning spec
`docs/specs/sealed-baseline-replacement/spec.md:182-189` is Archived carrying the
same cut. The under-count is fail-safe: `completed_task_ids` is always a subset
of what actually finished, so an amendment redoes completed work and never skips
unfinished work. Three separate investigations have now been spent on this across
two sessions; the premise is true every time and the disposition was what nobody
had written down. The only fileable item is the reopening condition both
documents name — a measurement of how much work an amendment actually redoes —
which needs a recorded instance of costly rework to justify.

## Residual

Five fixes landed after the last adversarial pass: the pack-test boundary
repair, the `/now/` projection regeneration, the pin ordering alignment, the
three incremental depth-library cases, and this record. Each was verified against
the gate that caught it, and the boundary repair was re-verified by exit code
rather than by a pipeline's last line. None has had an independent reader. On
this programme's own record that is not a small caveat, and it is the same
residual slice 2b carried.

The instrument control is one run. It establishes that three pin moves reproduce
on a tree without this slice's topics, which is enough to attribute them; it does
not establish that the measuring subcontext is stable in general. A second
control run would strengthen the attribution and was not taken.

Six case declarations were corrected after their measurement. The rule that
governed it is stated above and seven disagreements were deliberately left
uncorrected, but a reader should treat the retrieval figures as measured under a
declaration set that this slice adjusted, not one frozen before measurement.

## Gates

Measured on the shipping tree after every edit this slice makes. Written last,
because a figure recorded mid-work stops describing the tree the moment the next
commit lands.

| Gate | Invocation | Result |
| --- | --- | --- |
| Pack suite | `python3 -m pytest packs/agent-skill-engineering/tests -q` | 222 passed |
| Repository suites | `python3 -m pytest tests/ -q` | 1044 passed, 6 skipped, 46 subtests |
| Tooling suite | `python3 -m pytest tools/ -q` | 1207 passed, 2 skipped, 85 subtests; 2 failed, both attributed `owned-elsewhere` below |
| Site routing | `python3 -m pytest tools/test_build_site_routing.py -q` | 93 passed, 1 skipped |
| Lint | `make lint-ruff` | All checks passed |
| Pack-test boundary | `python3 tools/lint-pack-test-boundary.py` | exit 0 |
| Brief coverage | `lint-brief-coverage.py --root .` | 3 briefs checked |
| Spec metadata | `lint-spec-status.py --root .` | spec metadata clean |
| Plugin roster and membership | `lint-plugin-roster.py`, `lint-plugin-membership.py` | ok — 15 published, 7 withheld; ok |
| Site build | `make site-build` | 233 pages built, exit 0 |
| Web suite | `npm test --prefix web` | 18 files, 129 tests passed, exit 0 |

The site build and the web suite ran after the final `/now/` regeneration rather
than against a stale `build/`. This worktree had no `node_modules`; they are
gitignored, so `make bootstrap-sites` is required in every new worktree before
either gate can run.

### Measured evidence

| Measurement | Figure | Floor |
| --- | --- | --- |
| Retrieval precision | 0.924 | 0.90 |
| Retrieval recall | 0.955 | 0.90 |
| Exact selection | 0.919 | 0.90 |
| Declared retrieval cases | 86 | 40 |
| Topics measured solo at least twice | 16 of 16 | 16 |
| Generic-engineering negatives answered | 0 of 40 | at most 2 |
| Inherited foundation pins holding | 19 of 24, 5 re-taken and recorded above | 24 |
| Claude Code rows probe-backed | 3 of 7 | 3 |
| Claude Code profile roll-up | `complete-current` | `complete-current` |
| Admitted topics | 16 of 36 | — |
| Absence register | 20 | — |

## Failure attribution

Every failure this slice's gate chain observed, with the invocation that
reproduces it. Nothing observed is dropped.

| Failure | Reproducing invocation | Attribution | Attributor |
| --- | --- | --- | --- |
| `test_guide_typed_asides.py::test_ledger_has_complete_terminal_classifications` and `::test_ledger_matches_converted_asides_and_unchanged_quotations` | `python3 -m pytest tools/test_guide_typed_asides.py -q` → 2 failed, 2 passed | `owned-elsewhere`. Reproduces on `origin/main` independently of this branch; neither file is touched here. Routed against the existing `[backlog].open` entry `guide-blockquote-ledger-has-no-regenerator`. | Claude, this session |
| `lint-pack-test-boundary.py` → 2 failures | `python3 tools/lint-pack-test-boundary.py` → exit 1 | `caused-here`, **fixed**. The new test joined paths from a variable, which the lint cannot statically resolve, so a pack-local path read as climbing above the pack. Rebuilt as a glob-built map. Found only by reading the exit code: piped to `tail -1` the check printed nothing and looked clean. | Claude, this session |
| `test_the_committed_now_projection_matches_the_changelog_source` | `python3 -m pytest tools/test_build_site_routing.py -q` → 93 passed, 1 skipped | `caused-here`, **fixed**. The new changelog entry restaled the committed `/now/` projection. Regenerated with `tools/build-site.py --journeys-only`; a second run changes nothing. | Claude, this session |
| First combined gate run killed at its 600s limit | `sysctl -n vm.loadavg` → `{ 94.25 68.25 64.91 }` | `environmental`, **not carried**. A shared host under peer-worktree load; the run reached no verdict, so it is not a measurement. Gates were re-run individually and serialized against the site build, which writes `build/` that the tooling suite reads. | Claude, this session |
| Four mutation results reported `no tests ran` | `python3 -m pytest $T -q` with `T` holding two paths | `caused-here`, **discarded and re-run**. zsh does not word-split an unquoted parameter, so both paths became one argument matching nothing. Every figure from that batch was void and none was carried; the batch was re-run with explicit paths. | Claude, this session |
| One mutation reported `18 passed` where a redness was expected | the mutation's anchor assert failed, so no mutation applied | `caused-here`, **discarded and re-run**. A stale anchor means the harness proved nothing; re-run with the correct anchor, it reddened one test. A mutation that did not apply is not evidence that a guard is weak. | Claude, this session |
