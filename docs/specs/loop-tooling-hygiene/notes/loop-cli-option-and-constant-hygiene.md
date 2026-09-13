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

**Delivered 2026-09-11, with one recorded deviation.** A single declaration is
not reachable, though not for the reason first recorded here. Both CLIs do load
`_loop_guards.py` on every path that validates state — `loop-cohort.py` loads it
at import and refuses every verb at one dispatch chokepoint when that failed,
and `loop-engine.py` reaches it through its bounded reader — so a guard-owned
constant would add no new failure path. The obstacle is the re-bind pattern
itself. `loop-cohort.py`'s import must not raise, so each guard-owned name is
bound in an `else` branch with a local fallback in the `except` branch, exactly
as `DEFAULTS` is. That fallback is a second declaration by construction. It also
has to carry a usable value: `build_parser()` runs before the chokepoint refuses,
so a fallback of `None` would render into `identity --help` text on a broken
install.

Each script therefore keeps its own `SCHEMA_VERSION`, and two controls supply
what single ownership was for.

`test_schema_version_declarations_match_state_template` covers **declarations**.
It finds each plain `SCHEMA_VERSION = <number>` assignment at module level by
parsing rather than from a fixed list, so a script that starts declaring its own
is compared too, and it fails when one of those or the `state.json` template
disagrees. It reads only that plain form.

`test_no_script_states_the_schema_version_as_a_bare_literal` covers
**comparison sites and authored text**, and is a tripwire rather than a proof.
It flags a digit compared against the schema version in either direction, and a
digit typed into authored text — the two forms the literals here actually took.
It does not catch an alias, a `match` arm, or `not in (1,)`.

**Standing residual, stated plainly because it is not closed.** The two controls
do not cover each other, and each has the same kind of gap.

A comparison site that states the version literally in a form the tripwire
misses is not a declaration, so a bump could move every declaration and leave
that site pinned to the old value with both tests green. The declaration sweep
misses the mirror case: a declaration written as anything other than a plain
assignment of a literal — annotated, conditional, augmented, tuple-target, or
computed — is not compared, and carries no literal for the tripwire to flag
either.

Five rounds of review each found a new way past whichever control the previous
round had just widened. Chasing exhaustiveness through authored syntax was
stopped deliberately rather than continued, because each widening bought one
syntactic form and the next round found another. What remains is a convention,
mechanically enforced for the common forms only: declare the version plainly,
and compare against the constant rather than against a number. A reviewer, not
a test, is what catches the rest.

The literal count in this record was also low. Seven comparison sites exist,
not five: two already named the constant in `loop-engine.py`, and five were
bare — two in `loop-cohort.py` and three in `_loop_guards.py`. The `identity`
sub-command's help text stated `schema_version=1` as an eighth bare site and
was missed when this record was written; it is fixed too.

## Not part of this record

Both items were found while measuring these scripts' output cost. That
measurement and its do-not-shrink verdict live in
[`docs/product/research/loop-cli-output-cost-measurement.md`](../../../product/research/loop-cli-output-cost-measurement.md),
which outlives this record — closing the two fixes above does not retire the
measurement. No follow-on work is owed for the verdict itself.
