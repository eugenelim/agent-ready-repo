# Loop CLI output cost: measured, with a do-not-shrink verdict

Measured 2026-09-10 against `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`
and `loop-cohort.py`, the last two unmeasured agent-facing surfaces in this
family. Feeds the accepted
[work-loop delivery efficiency](../intents/work-loop-delivery-efficiency.md)
intent.

**Verdict: these two scripts' output should not shrink.** The removable
fraction is small, and most of what remains is a contract the calling agent
parses or a byte-pinned test fixture. Recorded here so a future session does
not repeat the measurement or act on a static `print(` count.

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
commands** — about 2.3 lines and 183 characters per command.

| Command | Lines | Chars |
| --- | --- | --- |
| `loop-cohort status` (human) | 21 | 833 |
| `loop-cohort status --json` | 1 | 812 |
| `loop-engine status` (human) | 12 | 363 |
| `loop-engine status --json` | 1 | 333 |
| `loop-cohort schedule` (3-task plan) | 5 | 326 |
| `loop-cohort init` | 1 | 296 |
| 11 × `loop-engine transition` | 11 | 1,224 |
| 10 remaining cohort verbs | 9 | 698 |

`schedule` is the only output proportional to input. Against the largest real
plan in the repository at the time (`docs/specs/site-ui-primitives/plan.md`, 25
tasks) it produced 12 lines / 780 characters, so a large-plan run is about
5,400 characters. For scale, `workspace-status`'s `status` payload alone was
220,195 characters before core 2.25.11 reduced it.

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

Best-case non-contract headroom was about 1,000 characters (18%): the
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
2.25.12 fixed it in both copies of the helper.

The same shape had already appeared once in this family: `lint-spec-status.py`
was mis-ranked by a static count because its real cost was 183 warn-only
stderr lines rather than its single stdout line.

## Structural note

Six helpers are duplicated between the two scripts: `_diag`, `stop`,
`_resolve_spec_dir`, `_get_repo_root`, `_statelock`, and `_locked`. Exactly one
has a parity control — `test_loader_copies_are_structurally_identical` in
`packs/core/tests/skills/work-loop/test_loop_guards.py`, which AST-compares the
three loader copies and refuses to skip when one is missing. The traceback
defect above lived in one of the five uncovered copies.
