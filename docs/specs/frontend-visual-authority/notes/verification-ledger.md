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

## Implementation review — findings and repairs

Nine findings against the slice-1 diff. Two were blockers, and one of them
invalidated a proof recorded above.

**The pre-flight assertion could not fail for the thing it was written to
catch.** It searched the whole of `SKILL.md` for the four rung keys. The T5
evidence-manifest row lists all four, in precedence order, as the field's
vocabulary — so deleting the entire pre-flight section left the assertion
green. The T3 mutation proof in this ledger was sound when it ran and stopped
being sound when T5 changed the file; it was never re-run. The assertion is now
scoped to the PLAN pre-flight section, as its EXECUTE sibling already was, and
re-proved against the current file: deleting the section reds it.

The general lesson, recorded because it cost a blocker: **a mutation proof is
evidence about one file state.** Later edits to the same file can silently
restore the property the mutation was meant to remove.

**Moving the token block carried the print/PPT CSS out of reach.** It became
the sole home of `@page`, `print-color-adjust` and the page-break rules, inside
a reference the skill says to load only at the lowest authority rung — while
the skill still advertises slide decks and its QA checklist still asks whether
print output is correct. A deck whose tokens came from a taxonomy was told
never to load the only guidance satisfying its own gate. The print block now
lives in `references/print-surface.md`, routed independently of rung, with an
assertion that reds if it returns to the rung-gated file.

Also repaired: the renamed skip wording no longer forbids the precedence
chain's own demotions; `token-architecture`'s pointer to the moved block; the
stranded-phrase sweep widened to the whole export tree, which the criterion
always said but the test did not do; the lens-count guard made case-insensitive
as its criterion states; the version assertion pinned to the value the
criterion names; and the standalone eval case restated so its assertions
describe one reachable world.

| Gate | Result |
| --- | --- |
| ruff / mypy | clean |
| pack suite | 413 passed |
| deep catalogue lint | exit 0 |
| roster + conformance | 75 passed |
| spec-status lint | metadata clean |

## Implementation review round 2 — no blockers

Three concerns, five nits. Two are worth recording because they are repeats of
traps this work already hit once.

**The print-route assertion I added to fix a whole-file-search hole was itself
a whole-file search.** It asserted the link appeared somewhere in `SKILL.md`,
so moving that link inside the rung-gated fallback bullet — restoring the exact
defect it was written to prevent — would have left it green. It is now scoped
to a position after the rung list, and proved: link present but rung-gated
reds.

**Verifying a stale sentence, I grepped for a phrase that wraps across a line
break and concluded it was absent.** It was present. This is the same
line-wrap trap that made the original stranded-pointer criterion miss two of
its nine sites, and the reason that criterion's predicate is
whitespace-normalized. A containment grep over raw text is not a safe way to
prove a phrase is gone.

Also repaired: the trim had dropped "continue with the checks that genuinely
run", which the shipped no-browser eval asserts — the skill no longer
instructed behaviour its own eval graded; the pre-flight assertion's window now
stops at the first mode subsection rather than running to the end of the PLAN
phase; the version pin's failure message reads as scheduled slice-2 work rather
than a regression; the print reference states its trigger once; and the release
note names where print guidance now lives.

`references/print-surface.md` is held by a regression assertion rather than an
acceptance criterion, deliberately: it guards a defect this slice introduced
and fixed, which the accepted intent never asked for.

| Gate | Result |
| --- | --- |
| ruff / mypy | clean |
| pack suite | 413 passed |
| deep catalogue lint | exit 0 |
| roster + conformance | 65 passed |
| spec-status lint | metadata clean |
| self-host | ok |
