# Loop CLI option and constant hygiene

Two determined one-line fixes in the work-loop scripts, found while measuring
`loop-engine.py` and `loop-cohort.py` output cost. Both are outside the touched
area of the change that found them, which is the only reason they are deferred
here rather than fixed. Neither changes behaviour today.

This file follows the parent spec's shape: loop tooling hygiene items with no
shared logic and no shared risk, carried together because each is small and
each has a decided fix.

## 1. `schedule --plan` advertises a capability it refuses

`loop-cohort.py schedule` accepts `--plan`, whose help text reads `path to
plan.md (default: <spec-dir>/plan.md)`. The parenthetical implies an alternate
path is accepted. It is not: `loop-cohort.py:1349` refuses every value other
than `<spec-dir>/plan.md`, and `loop-cohort.py:1354` then assigns
`plan_path = plan_path_canonical`, discarding the argument. The only two
reachable outcomes are "identical to omitting the flag" and "refusal".

The refusal itself is correct and deliberate — the refusal message explains
that an alternate path creates unusable state, because `schedule
check-current` always hashes `plan.md`. The defect is the help text, which
describes an option that can never take effect.

**Decided fix:** change the help string to say the path must be
`<spec-dir>/plan.md`. Do not delete the option:
`test_loop_cohort.py:857` and `test_loop_cohort_schedule.py:214` both pass
`--plan`, and the first exists to pin the refusal.

`--plan` appears in no `SKILL.md` or reference, so no shipped instruction
depends on the current wording.

## 2. `schema_version` is a bare literal in three of five places

`loop-engine.py` names the value (`SCHEMA_VERSION = 1` at line 103, used at
four sites). The other current-schema checks compare against an unnamed `1`:

| File | Line |
| --- | --- |
| `loop-cohort.py` | 683 |
| `loop-cohort.py` | 1136 |
| `_loop_guards.py` | 1018 |

`_loop_guards.py:1201` also compares against `1`, guarded by `phase !=
"implement"`. That skip is deliberate and covered by the golden row
`check/unsupported-schema-non-implement`, so it is listed for completeness
rather than as part of the defect.

A schema bump therefore has to be found in five places under two conventions,
and the three literals give a reader no way to grep for the concept. All five
agree on `1` today, so nothing is broken.

**Decided fix:** give the cohort side a named constant and have
`_loop_guards.py` read one shared name, so a bump has a single owner. The
state template in `state.json` carries the same value and should be counted
when the fix is scoped.

## Not part of this record

The output-cost measurement that surfaced both items concluded that these two
scripts' output should **not** shrink: a full-mode `code`-mode run emits 62
lines and 4,933 characters across 27 commands, and the parsed-contract
inventory plus the 39 byte-pinned rows in
`packs/core/tests/skills/work-loop/fixtures/golden_cli_streams.json` account
for the large majority of it. That verdict needs no follow-on work.
