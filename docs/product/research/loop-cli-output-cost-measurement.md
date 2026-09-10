# Loop CLI output cost: measured, with a do-not-shrink verdict

- **Run date:** 2026-09-10
- **Owner:** eugenelim, Platform Core maintainer
- **Verdict:** these two scripts' output is contract-bound and should not
  shrink; the measurement surfaced one correctness defect, fixed in core
  2.25.13

Measured against `packs/core/.apm/skills/work-loop/scripts/loop-engine.py` and
`loop-cohort.py`, the last two unmeasured agent-facing surfaces in this family.
Feeds the accepted
[work-loop delivery efficiency](../intents/work-loop-delivery-efficiency.md)
intent.

The removable fraction is small, and most of what remains is either a contract
the calling agent parses or a byte-pinned test fixture. Recorded here so a
future session does not repeat the measurement or act on a static `print(`
count.

## How it was measured

A synthetic spec and plan in a throwaway git repository, driven through the
real full-mode `code` path one command at a time — `init`, cohort `init`,
`spec-ready`, `plan check-current`, `reviewers-clean`, `spec-approved`,
`plan-approved`, `approve-plan`, `schedule`, `plan-locked`, both `status`
forms, `identity`, the wave-routing pair, `gates-clean`, `raw-classify`,
`review record`, `done`. Transitions and cohort advances were never chained.

A static count would have misled: it ranks these scripts by their 29 and 31
`print(` sites, when the distribution is dominated by a handful of commands
and the worst single event is on an error path.

## Result

A complete happy-path run is **62 lines / 4,933 characters across 27
commands** — about 2.3 lines and 183 characters per command. The rows below
account for all 27 and sum to the total.

| Command(s) | n | Lines | Chars |
| --- | ---: | ---: | ---: |
| `loop-cohort status` (human) | 1 | 21 | 833 |
| `loop-cohort status --json` | 1 | 1 | 812 |
| `loop-engine status` (human) | 1 | 12 | 363 |
| `loop-engine status --json` | 1 | 1 | 333 |
| `loop-cohort schedule` (3-task plan) | 1 | 5 | 326 |
| `loop-cohort init` | 1 | 1 | 296 |
| `loop-engine transition` | 11 | 11 | 1,214 |
| `loop-engine init --json` | 1 | 1 | 99 |
| `approve-plan`, `schedule check-current`, `identity`, `wave check` ×2, `wave advance`, `raw-classify`, `review record` | 8 | 8 | 609 |
| `loop-cohort plan check-current` (stderr; exit 1 is the documented signal) | 1 | 1 | 48 |
| **Total** | **27** | **62** | **4,933** |

Stdout alone is 61 lines / 4,885 characters; the remaining line and 48
characters are `plan check-current`'s refusal on stderr.

`schedule` is the only output proportional to input. Against the largest real
plan in the repository at the time (`docs/specs/site-ui-primitives/plan.md`, 25
tasks) it produced 12 lines / 780 characters, so a large-plan run is about
5,400 characters. For scale, `workspace-status`'s `status` payload alone went
from 220,195 to 86,510 characters in core 2.25.11 (figures from that change's
commit message, `0b75130bd`; the changelog entry states no number).

## Why it cannot shrink

Two independent freeze layers cover the large majority of those bytes.

**Documented parses.** `SKILL.md` instructs the controller to parse `run_id`
from `init --json` and the `(seq=N)` that every `transition` prints;
`references/session-resumption.md` names the `status --json` fields both tools
must return; `references/supervisor-mode.md` reads `predicted-disjoint` per
wave and the wave task set; `plan check-current`'s exit 1 and `wave check
--expect more|last` are documented signals; `raw-classify` and `review
inspect` have parsed JSON fields.

**Byte-pinned fixtures.** `packs/core/tests/skills/work-loop/fixtures/golden_cli_streams.json`
pins 39 `loop-cohort` rows — every `identity`, `plan check-current`, `schedule
check-current`, `check`, and `wave check` message, on both streams, with exit
codes.

Best-case non-contract headroom was about 1,000 characters — 20% of the
4,933-character three-task run, 18% of the ~5,400-character large-plan run: the
`predicted-disjoint` caveat repeated once per wave, `loop-cohort init`'s
absolute path, and the `status` fields no reference names as parsed. The
realistic saving is roughly half that, because both `status` commands are 47%
of the total but run once or twice per run rather than once per request, while
per-request cost is dominated by the transition lines — the frozen ones.

The reduction pattern from core 2.25.11 also does not transfer at the
deciding point. That change withheld informational detail lines, so a consumer
unaware of the new `--verbose` flag lost nothing it acted on. A `status --json`
payload *is* the resume contract; a default that drops a field breaks a
resuming controller that does not know the flag.

## What the measurement did find

The largest single output event in either script was never on the success
path. A `git` lookup failure produced a 33-line, ~2,220-character traceback
that also printed absolute internal script paths — more output than an entire
successful run — because `_get_repo_root` converted `subprocess.TimeoutExpired`
but not `OSError`. That was a correctness defect, not verbosity, and core
2.25.13 fixed it in both copies of the helper.

The same shape had already appeared once in this family: `lint-spec-status.py`
was mis-ranked by a static count because its real cost was its warn-only stderr
lines rather than its single stdout line. Measured on this repository on the run
date, `lint-spec-status.py --root . --verbose` emits 183 of them; the default
run counts them instead, which is what core 2.25.11 changed.

## Structural note

Seven helpers are duplicated between the two scripts. Six share a name —
`_diag`, `stop`, `_resolve_spec_dir`, `_get_repo_root`, `_statelock`, `_locked`
— and the seventh is the guards loader, named `_guards` in `loop-engine.py` and
`load_guards` in `loop-cohort.py` and `check-spec-status.py`.

**Only the guards loader has a parity control**, and it is the one helper of
the seven that does: `test_loader_copies_are_structurally_identical` in
`packs/core/tests/skills/work-loop/test_loop_guards.py` AST-compares its three
copies and refuses to skip when one is missing. The other **six have none**,
and `_get_repo_root` — where the traceback defect lived, in both copies at once
— is one of them.

The six split further, AST-compared with docstrings dropped — the same
criterion the existing control uses:

| Helper | Copies |
| --- | --- |
| `_diag`, `_resolve_spec_dir` | identical |
| `stop`, `_get_repo_root`, `_statelock`, `_locked` | differ |

That split is the actionable part. `_diag` and `_resolve_spec_dir` are already
coverable by the existing control's technique unchanged. The four that differ
need a comparison that tolerates the differences that are deliberate — `stop`
carries each tool's own prefix, `_statelock` and `_locked` name their own tool
in an error string — which is the work a future session would have to scope.
`_get_repo_root` is in that group, and it is where this defect lived.
