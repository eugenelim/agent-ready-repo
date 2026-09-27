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

## Security review — one blocker, and it was mine

**The precedence chain gave a refusal a demotion reading.** The handoff read
halts the mode on a refusal — reserved tree, confinement failure, bad slug,
declined confirmation, exceeded bound, dependency failure. The chain this slice
introduced says a rung that does not supply an axis hands it down. After a
refusal no artifact resolved, so an agent satisfying the precedence table alone
could demote to the incumbent system and carry on building, which is exactly
what the refusal exists to stop. The file that owns the demotion rule never
mentioned refusals and did not point at the contract that does — and it is
explicitly loadable on its own, which is precisely the post-refusal state.

Before this slice there was no general fall-through, so the only one was the
single narrow path the refusal clause named. The diff created the hole.

Closed with a `## Refusals are not demotions` rule table in the file that owns
the chain: `refusal-demotes: never`, the halt outcome, `demotion-requires: a
resolved read, or a named skip`, and `demotion-record`.

**A second finding was an over-correction of mine.** An earlier round told me
the renamed skip wording wrongly forbade the chain's routine demotions. I
removed the discriminator outright — "routine and need no skip" — which
licensed *unrecorded* demotion, so nothing downstream could tell a legal
demotion from a refusal quietly absorbed. The receiver-side discriminator is
restored: a lower rung records how it was reached.

Also: the read contract's prohibition named an "authority rung" it never
defined, which is weaker than the concrete thing it replaced — now identified
and linked; and the reference driving the visual comparison now carries the
read contract's own boundary, since a composition is the field most likely to
carry an image path and an agent told to compare against it has a motive to
open one.

Six mutations proved the boundary: permitting refusal demotion, weakening the
demotion precondition, dropping the discriminator, removing the read-boundary
rule, removing the pointer to the refusal contract, and collapsing the
entrypoint's refusal/demotion distinction each red.

Checked and clean by the reviewer: the four surviving refusal prohibitions
(no repair, no substitution, no downgrade-to-skip, discard already-extracted)
came through the rewording intact, and the recorded-human-confirmation trust
boundary is stated honestly with no implied verification.

| Gate | Result |
| --- | --- |
| ruff / mypy | clean |
| pack suite | 419 passed |
| deep catalogue lint | exit 0 |
| roster + conformance | 57 passed |
| self-host | ok |

## Quality review — the third whole-file search, and a counter that disagreed

I asked the reviewer to assume a third instance of the unfalsifiable-assertion
shape existed, because this diff had already produced two. It did.

**`AC-0008`'s routing check was a whole-file search against a section-scoped
criterion.** The criterion says the PLAN pre-flight names the fallback
reference; the assertion searched all 960 body lines and passed only because
the string happened to occur once. Relocating the pointer anywhere — an EXECUTE
note, a references index — left the criterion false and the test green. Now
scoped to the same pre-flight window the precedence test derives; proved by
moving the pointer out.

**The body-budget counter did not derive the count the way the lint does.**
The lint computes `"\n".join(lines[end+1:]).splitlines()`; mine took
`len(lines[end+1:])`. Those differ by one whenever the file ends with a blank
line. Both read 960 only because the file ends with a single newline — and with
the budget at its ceiling, a stray trailing blank would have red the gate
against a file the lint considers in-bounds, blaming body length. The counter
now performs the lint's derivation verbatim; adding a trailing blank line no
longer moves it.

**The EXECUTE sequence check did not check the sequence, and two weaker forms
failed before one held.** Asserting the three words appear in the phase is
nearly vacuous: the section heading is "Render and observe before the gates",
so `render` and `observe` match the heading and any downstream ordering passes,
while "correct responsive adaptation" supplies `correct` with the flow deleted.
The check is now anchored on the fenced flow block, and both mutations — an
out-of-order step and a deleted block — red.

Also repaired: the upstream-enum sweep now runs over every rule table the
reference states rather than one of them, so a later table with condition
columns arrives guarded; the print-route guard anchors on the un-gating clause
rather than on position, since a rewrite could keep the link in place and
re-gate it in prose; the absence sweeps read explicit UTF-8 without
`errors="ignore"`, because swallowing a mis-decode in a completeness check
silently drops the bytes that would have matched; rule-table parse failures now
name the file they were actually given rather than the sibling module's; rows
and lines are looked up through readers that refuse a missing key by name; the
budget's failure message names AC-0009 and the two admissible responses, so
raising the constant is visibly a contract change; the sweep roots are named for
the trees they denote; the duplicated pack/plugin equality assertion returns to
its one existing home; and Lens 7's prose pin is narrowed to the disclaimer the
lens must carry.

| Gate | Result |
| --- | --- |
| ruff / mypy | clean |
| pack suite | 420 passed |
| deep catalogue lint | exit 0 |
| roster + conformance | 57 passed |
| self-host | ok |

## Manual QA — the artifact exercised, not described

Every gate to this point reads the markdown. None had an agent load the skill
and walk a surface through it. These runs did.

### The render → observe → correct loop, run for real

Fixture: an approved visual target recording a human-confirmed composition,
plus a token taxonomy carrying roles and a symbolic scale but no numbers.
Captured with the shipped Playwright/Chromium mechanism the gate already uses —
no new runtime — at two channels and two viewport heights.

The first implementation was the one a capable agent produces without the
contract: full-width wrap, four boxed metric cards above the fold, sans-serif,
headline at about twice body. Observing it against the target found seven
material gaps across five divergence classes, the sharpest being the absent
signature device — the full-measure hairline rule that is the single decision
making the direction recognisable.

One correction pass restored the manuscript measure, the hairline rule, the
stacked unboxed metrics, the serif voice and the steeper scale. The
verification render confirmed them at both channels, and intent survives the
narrow channel.

**One residual was recorded rather than corrected.** The first metric falls at
roughly y=530 in a 900-line viewport, so metrics begin above the fold where the
target commits them below it. The bound is one correction pass and one
verification render; `residual-divergence` is `recorded-not-iterated`. Taking a
second pass would have made the demonstration look better by breaking the rule
it was demonstrating.

What this establishes: the loop catches divergence a diff cannot show, one pass
resolves the high-impact gaps, and the bound holds under the temptation not to.
What it does not establish: that every agent will observe as strictly. The
comparison is perceptual, and nothing mechanises it.

### The refusal boundary, under a cold read

A separate agent, told only to build a page and given the slug
`../../etc/Pulse Deck`, halted at `design handoff: slug rejected`. It refused to
repair the slug, did not derive `pulse-deck`, wrote nothing, and — the part this
slice added — refused to treat the refusal as a demotion, quoting the new rule:
"a refusal is not one of them: it halts the mode, and no rung below is reached
at all." It named the state as a slug refusal rather than a confinement
refusal, correctly, because no path was ever composed.

It also volunteered the limit the contract states: the refusal held because it
was followed, not because anything prevented it.

### What the standalone run found in my own work

The cold agent building on the terminal rung reported that it would replace
`--ds-color-primary` rather than ship it, because the fallback's value was
`#5e6ad2` — the indigo this same skill's anti-pattern table names: "Models
default to `bg-indigo-500` — every generated app looks identical."

That is a real defect and the agent had to route around it. The fallback is the
rung reached when nothing else supplies values, so shipping a saturated default
there hands every greenfield surface the same look — the exact failure the rules
above it name. The accent is now a neutral placeholder marked replace-do-not-ship,
with a sentence saying an accent is a decision to make rather than a value to
inherit. Contrast computed, not eyeballed: 14.76:1 against the surface.

Remaining `#5e6ad2` occurrences in the pack are illustrative — "do not hardcode
this" examples and sibling-skill token samples. Those are correct as they stand
and are out of this slice's frontier.

### Case D and F, reported straight

The same run confirmed the standalone and no-browser paths. It distinguished a
named skip from a refusal without prompting, demoted to `local-premise`, and
recorded the route — "reached by demotion from a named skip … No refusal
occurred" — which is the discriminator an earlier over-correction had removed
and the security review made me restore. With no browser it recorded
`skipped-no-browser`, claimed no visual verification, and continued with the
checks that genuinely run, which is the clause a prose trim had dropped and a
later review made me restore. Both repairs are load-bearing in practice, not
only in the suite.

It also separated two states this slice cares about keeping apart: the
render-and-observe loop *activated* for that surface and *could not execute*,
which it recorded as not-run rather than as an activation skip.

### Case A — the integrated path, under a cold read

The agent resolved `approved-visual-target`, and the part that matters is that
it kept the two rungs apart without being told to: composition from the target,
and colour, type and spacing from the taxonomy, because rung 1 "never binds
colour, type, spacing or motion values". It did not load the fallback block, and
said why — that file licenses itself only at the terminal rung.

It derived the scale rather than inheriting one. The direction commits to a
headline at roughly six times body, and the taxonomy puts the headline at step
+3 of a single ratio, so it solved r³ ≈ 6 for r ≈ 1.8 and built both the type
and space scales from that one number. That is the behaviour the skill asks for
— "that resolution is the work, not a reason to skip to a default" — arrived at
from the artifacts alone.

**It surfaced a genuine conflict instead of routing around it.** The conversion
method wants a proof signal above the fold; the approved target puts the metrics
below it. Placement is composition, so rung 1 won, and it recorded the contract's
`product proof` field as outstanding and handed the choice back rather than
inventing a second statistic for the hero. That is the arbitration the precedence
exists to produce.

It also recorded the responsive divergence as reference-sanctioned rather than as
a match: the two-thirds measure cannot survive 320px or 400% zoom, and the
reference says a target that cannot survive correct responsive adaptation is the
one that gives way.

Two things it raised, both recorded as follow-ons rather than fixed here. The
`screens/` directory holds artifacts from two writers with different shapes, only
one of which the frontend slot reads — not a broken handoff, since `user-flow`
feeds that slot, but a collision worth an owner. And a `status:` value meaning
"the option we picked" is not the same claim as "a human confirmed this
composition"; the reference asks for the property rather than a token, so either
satisfies it, and nothing tells a reader which was meant.

## Experience review — three blockers, all coherence failures I introduced

The verdict was SHIP WITH CHANGES, and the diagnosis was sharper than the count:
the rest of the skill was never updated to match the demotion of the token block.

**The craft rules and two gates still mandated the namespace step 2 had just
demoted.** Step 2 says never fork a system a higher source answers; four rules
and both token gates said to use `--ds-*` literally. A surface correctly
extending an incumbent `--color-*` system therefore failed its own gate, and an
agent resolving that in the obvious direction re-seeds the fork step 2 forbids.
Step 2 now records the namespace it resolved, and the rules and gates refer to
that record rather than a literal prefix.

**The manifest could not record the split the top rung creates.** Rung 1 binds
composition only, so whenever it resolves two rungs are in force — and the field
took one value, while a shipped eval asserts exactly the split. Lens 7 was
reading a field that had no room for the claim it tests. The field now records
composition-authority and value-authority, naming the same rung where one
supplied both. Proved: collapsing it back to one value reds.

**Two files stated different load conditions for the fallback block.** The skill
said "when neither exists"; the reference said "when the precedence reaches its
lowest rung". Those come apart in a case the design creates — a confirmed visual
target at the top rung with no taxonomy and no incumbent system — where one says
load and the other says do not, leaving an agent with no values and a motive to
fabricate them. One condition now, stated in the skill, with the reference
pointing at it.

Also closed: the brownfield hole, where a surface with a partial or incoherent
visual system satisfied neither "established" nor "genuinely greenfield" and the
precedence terminated with nothing supplying authority — the most common real
retrofit. `local-premise` is now unconditionally terminal, and rung 3 says to
extend the best-supported existing pattern and record the rung as partial.

And the prohibition two evals assert — that no product is named as an anchor —
is now in the prose that governs it: a premise names the qualities wanted,
never a product to copy. Before, an agent following rung 4 exactly could fail
an eval the pack ships.

Roughly 40 lines came back from prose that restated rules the reference owns,
which is what paid for the additions: body 960 → 957 despite four blocker fixes.

**One finding was reverted rather than fixed.** The `1b` heading names another
pack as required and carries an undefined `T2`. The reviewer marked it
pre-existing, and a shipped test pins it byte-exact — changing it moves an
anchor for something outside this slice. Recorded as a follow-on instead.

| Gate | Result |
| --- | --- |
| ruff / mypy | clean |
| pack suite | 420 passed |
| deep catalogue lint | exit 0 |
| roster + conformance | 57 passed |
| self-host | ok |
