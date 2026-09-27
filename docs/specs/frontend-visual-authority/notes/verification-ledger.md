# Verification ledger — frontend-visual-authority

Execution observations. Not contract; the spec and plan are pinned.

## T1 — pre-change baseline

| Reading | Value |
| --- | --- |
| `python -m pytest packs/frontend-engineering/tests/skills/frontend-engineering/ -q` | 355 passed, 0.84 s |
| `python3 -m agentbundle catalogue lint --root . --deep` | exit 0; `SKILL.md` body 997 lines (WARN >500) |
| `python3 -m agentbundle catalogue lint --root .` (shallow) | exit 0, **zero** CAT-S003 findings — cannot fail on body length |
| `git status` | clean but for the untracked spec directory |

**Mutation proof that the body gate fires.** Appending 5 blank lines produced
`[CAT-S003] ERROR ... body exceeds 1000 lines (got 1001)`, exit 1. Restoring
returned `WARN ... got 997`. The gate is real and `--deep` is required to reach
it.

**Probe: the table parser is reusable.** `table_rows` and `unique_keyed` in
`frontend_engineering_rendered_page_rules.py` both take markdown as an argument
and parse an arbitrary heading; only `read_rules` is path-bound. A new rules
module reuses the readers rather than adding a second parser.

**Probe: the token predicate must be anchored.** Against the pre-change file,
bare containment on `--ds-color-primary` matches 3 lines (195 prose, 215
declaration, 510 focus-visible rule); the anchored form `^\s*--ds-color-primary\s*:`
matches 1 (215). Only the declaration is in scope.

## T1 — anchor inventory

Shipped assertions this slice moves, and the task that moves each.

| Anchor | File | Moved by |
| --- | --- | --- |
| `count("six lenses") >= 2`, stale-phrase guard | `test_rendered_page_reviewer_sight.py` | T5 |
| `Lenses 1-5` / `Lens 6 reads the page` confirmation scoping | `test_rendered_page_reviewer_sight.py` | T5 |
| Manifest field-count derived from the table | `test_rendered_page_result_recording.py` | T5 (heading count only) |
| `PINNED_SKIP_COST` gate fields | `test_rendered_page_journey_promise.py` | none — slice 1 stays outside them |
| Four proportionality allowances, cue pairs co-located per line | `tests/roster/test_experience_journey_composition.py` | slice 2, T6 |

**Not moved, deliberately.** `SKILL.md`'s "full 12-field contract" is the
page/screen contract — a different twelve from the evidence manifest's — and an
adversarial round proposed changing it. It stays.

## T2 — seed token block relocated

| Reading | Value |
| --- | --- |
| `SKILL.md` body | 997 → 908 lines (89 freed) |
| deep catalogue lint | exit 0 |
| pack suite | 355 → 357 passed (+2 = shipped-content guards auto-parametrising over the new reference) |

Four assertions added and each mutation-proved: reintroducing a `:root` block,
repointing the reference, removing the focus-visible token usage, and exceeding
the budget each red exactly one test; all restored clean.

The scoped predicate earned its scoping — `var(--ds-color-primary)` survives
once, in the focus-visible rule, where a bare containment check would have red
on correct content.

## T3 — precedence rule, product table deleted

| Reading | Value |
| --- | --- |
| `SKILL.md` body | 915 lines (budget 960) |
| deep catalogue lint | exit 0 |
| pack suite | 382 passed |
| aesthetic-anchor literals under the swept roots | 0 |
| stranded pointers to the deleted set | 0 |

All eight surviving pointers renamed rather than dropped, across the skill, the
handoff read contract and the shipped `design-handoff-read` eval. The refusal
clauses keep their semantics: a refusal still must not fall through to a lower
rung, which is the property that outlives the old table's name.

Seven mutations proved the assertions: dropping the rung keys from the
entrypoint, repointing the reference, unbinding a rung from its read path,
inverting a demotion edge, keying the top rung on the upstream enum,
reintroducing an anchor, and naming an upstream pack each red. The first three
are the ones that close the two adversarial blockers — before them, the
reference could ship correct while the always-loaded skill routed to none of it.
