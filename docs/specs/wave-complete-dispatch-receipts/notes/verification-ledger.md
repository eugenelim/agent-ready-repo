# Verification ledger — wave-complete dispatch receipts

Execution observations for this spec. This file is the single home for the
dispatch-rate measurement and for the grounding evidence behind each
load-bearing claim. The spec and plan cite it; they do not restate its figures.

Every entry below states the command that regenerates it. A figure with no
regenerating command is not evidence, because the underlying corpus grows.

---

## 1. Dispatch rate — the measurement the spec rests on

**Generator:** [`measure_dispatch_rate.py`](measure_dispatch_rate.py), committed
beside this file.

**Command:**

```bash
python3 docs/specs/wave-complete-dispatch-receipts/notes/measure_dispatch_rate.py \
    --since 2026-09-15 --self-exclude "$CLAUDE_SESSION_ID"
```

**Recorded run — 2026-09-17:**

| Quantity | Value |
| --- | --- |
| Transcripts scanned | 703 |
| Sessions in window (on/after 2026-09-15) | 295 |
| Engine-driven runs (tight match) | 12 |
| …that dispatched an `implementer` | 4 |
| …that did not | 8 |
| Controller `Edit`/`Write` calls in the 8 | 104 |
| Dispatches per dispatching run | 1, 2, 5, 16 |

**Distribution, not just a total.** The four dispatching runs are not alike:
one dispatched 16 implementers, one 5, one 2, one 1. A single run accounts for
two-thirds of all dispatch in the window, so "4 of 12 runs dispatch" and
"dispatch is now normal practice" are different claims and only the first is
supported.

**Independent comparison.** The generator reports a deliberately loose control
alongside the tight count: 8 further sessions in the window mention
`loop-cohort` without invoking `schedule` with an argument. A loose regex would
have reported 20 engine-driven runs instead of 12. My first pass in this session
used such a regex and over-reported before I tightened it.

**Unresolved residuals.** Of the 12 tight matches, the argument captured after
`schedule` is a real spec path for 8, a shell variable (`$S`, `"$D"`) for 2, and
prose for 2 — a heredoc `<spec-dir>` and a backticked `` `parse_depends_on` ``.
The two shell-variable cases are almost certainly genuine invocations with the
path indirected; the two prose cases are almost certainly not invocations at all.
So the honest engine-driven count is **10 to 12**, and the dispatch rate is
4 of 10 to 4 of 12. I have not classified the two prose cases by reading their
sessions.

**Correction to what I reported earlier in this session.** I previously stated
11 engine-driven runs, 3 dispatching, 100 controller edits, from 783
transcripts over 260 sessions. Re-running the committed generator gives 12, 4,
104, from 703 transcripts over 295 sessions. The corpus is live: sessions were
created and transcript directories pruned while the work proceeded. The
direction of the error is that dispatch is *more* common than I reported, not
less. This is the concrete reason the figure is cited here by command rather
than transcribed into the spec.

**Re-measured after a rewrite.** The generator's directory walk was rewritten
from the `glob` module to `Path.glob` to satisfy the repository's `ruff`
configuration. Re-running it after that change produced identical output on the
same corpus (703 / 295 / 12 / 4 / 104), so the rewrite is behaviour-preserving
here. Recorded because changing an extractor invalidates its prior measurement
until the measurement is taken again through the real entry path.

**Bound on the claim.** Transcripts are per-machine and per-user, so this
measures one workstation's history. It is not a population estimate for the
loop.

---

## 2. Which surfaces execute the wave-exit guard's sibling phase

The round-4 finding that moved the design was that `check --phase implement` has
a caller beyond the engine. Grounding it, with the exact surfaces inspected.

**Chain, each link read rather than inferred:**

| Link | Surface | Evidence |
| --- | --- | --- |
| 1 | `Makefile:96` | `pre-pr:` recipe runs `tools/catalogue/pre_pr_catalogue.py` — *not* `tools/hooks/pre-pr.py` directly |
| 2 | `tools/catalogue/pre_pr_catalogue.py:153-160` | invokes `[py, "tools/hooks/pre-pr.py"]` with `check=False`, then `if result.returncode != 0: sys.exit(result.returncode)` — **the exit code is consumed** |
| 3 | `tools/hooks/pre-pr.py:134` | `sorted(Path("docs/specs").glob("*/state.json"))` — every spec directory |
| 4 | `tools/hooks/pre-pr.py:156-157` | `for phase in ("implement", "review")`, with `review` gated on the engine state and `implement` ungated |
| 5 | `tools/hooks/pre-pr.py:176` | `sys.exit(1)` on any non-zero |

So a refusal added to the `implement` phase fails `make pre-pr` for every spec
directory in the tree. That is why the accounting takes a separate phase.

**What the oracle at link 2 actually compares:** it compares the hook's process
exit code to zero. It does not inspect the hook's output, so a refusal's text is
irrelevant to whether the gate fails.

**Projection probe — the artifact a gate consumes, not only the source.**
`tools/hooks/pre-pr.py` and its packaged twin
`packs/core/.apm/hooks/pre-pr.py` are byte-identical:

```bash
shasum -a256 tools/hooks/pre-pr.py packs/core/.apm/hooks/pre-pr.py
# 71ddbdc9c9ffc10d… both
```

**Other surfaces that execute a copy:**

- `tools/test_build_gate_chain.py:1048` runs `tools/hooks/pre-pr.py`.
- `tests/roster/test_core_pre_pr_hook.py:111` runs
  `packs/core/.apm/hooks/pre-pr.py`, in a seeded `tmp_path` sandbox, so it does
  not see the real `docs/specs/`.

**Residual resolved — the hook is reached by the required PR gate.** I had
scoped this to `make pre-pr` and two test suites and left the CI path
unverified. Round 6 pointed out it is one read away, and it is:
`tools/repo/build_gate_chain.py` runs `tools/catalogue/pre_pr_catalogue.py
--skip-verify`; `--skip-verify` suppresses only the catalogue verify step, so
the delegation to `tools/hooks/pre-pr.py` and the `sys.exit` on its return code
both still run; and the `Makefile` chains that into `build-check`, which is the
always-run PR gate. So the `implement` phase's verdict gates every pull request,
not only a local `make pre-pr`. `make ci` not naming `pre-pr` is not evidence
against this — it reaches it through `build-check`.

This strengthens rather than changes the design conclusion: keeping the
accounting out of `--phase implement` matters more, because the surface it would
have gated is a required check rather than an optional local one. Recorded as a
correction because T1's `Done when` requires the answer for every surface, and
scoping a surface away is not answering it.

**Independent count of the firing sites, since the roster was adopted from a
review rather than measured.** Seven sites across four files, confirmed by
reading each: `SKILL.md` three (changes-requested, further-in-intent-unit,
specialist-adjudication), `references/supervisor-mode.md` one,
`references/session-resumption.md` one, `references/finding-adjudication.md`
two. A mention count gives the wrong answer — `SKILL.md` mentions
`wave-complete` seven times across three sites, and
`session-resumption.md` mentions it twice of which only one is an instruction to
fire it: the `reviewers-clean` row's cell. The other is a resumption row keyed
*by* `wave-complete` as the last event, describing what to do after it fired. My
first tally said six sites for exactly that reason.

**Sweep method, stated because a grep missed it.** `grep -rn -- "--phase"` piped
through a filter for `implement` does **not** find this hook: the phase reaches
the argument list through a loop variable, so no single line carries both
tokens. The surfaces above were found by reading `pre-pr.py` and by grepping for
`hooks/pre-pr` across `Makefile`, `.github/workflows/*.yml`, `tools/**`,
`tests/**`, `docs/**`, `packs/**`.

---

## 3. Helper contracts, each with one discriminating example

The plan reuses three guard-layer helpers rather than writing new ones. Contract
read, and one case run that a wrong implementation would fail.

**`non_negative_int`** (`_loop_guards.py`) — returns the integer, or a reason
string. Run against `{"current_wave_index": <value>}`:

| Input | Result |
| --- | --- |
| `0`, `3` | accepted, returns the int |
| `True`, `False` | reason: `must be a non-negative integer, got bool` |
| `-1` | reason: `…got -1` |
| `"2"` | reason: `…got str` |
| `2.0` | reason: `…got float` |
| `None` | reason: `…got NoneType` |

The discriminating case is `True`: a plain `isinstance(v, int)` check accepts it,
because `bool` subclasses `int`. This helper rejects it, which is why the plan
reuses it instead of writing a predicate.

**`GuardResult`** — a passing result may carry a `message` and may not carry a
`reason`. `GuardResult(ok=True, message="note")` returns the message;
`GuardResult(ok=True, reason="note")` raises `ValueError: GuardResult invariant
violated`. This is the pair of facts the disclosure channel depends on, and the
second is what makes the engine unable to surface a passing guard's text.

**Truncation — what the naming obligation actually collides with.**
`_MAX_REASON_CHARS = 4000`. Run over synthetic unaccounted-task lists:

| Task ids in the reason | Chars in | Chars stored | Ids dropped |
| --- | --- | --- | --- |
| 199 | 1,097 | 1,097 | 0 |
| 799 | 4,697 | 4,000 | 116 |
| 1,999 | 12,897 | 4,000 | 1,316 |

`_scalar` caps an interpolated value at exactly 120 characters, which is about
20 task identifiers. `_diag` in `loop-cohort.py` applies **no** length bound:
200,000 characters in, 200,000 out.

So the criterion "names every such task" holds up to roughly 680 identifiers if
the list is interpolated raw, and up to roughly 20 if it goes through `_scalar`
as the convention for state-derived data requires. The practical collision is
with `_scalar`, not with the 4,000 cap. A refusal that routes unbounded
state-derived text through `_diag` has no bound at all, which is the flooding
class `_loop_guards.py` records this repository already paying for.

---

## 4. The verdict-table partition — what each walk's oracle compared

Every walk run from round 4 onward is recorded below, one row per walk in the
order it ran, because the progression is the finding. Append a row rather than
replacing one.

| Walk | Domain | Oracle | Result |
| --- | --- | --- | --- |
| 480 states | my own row conditions | my intended predicates | found the row-2/row-3 overlap; **missed** the malformed wave element |
| 1,152 states | field *types* of `schedule_waves`, its current element, the container, the pointer | my intended predicates | found the malformed wave element; **missed** malformed container interiors and record leaves |
| 1,800 states | the same, plus `schedule_waves` as a dict and the container as a list | the rows **as the spec words them** | found two wording defects; **missed** record `kind` and record shape |

**What these oracles compare:** each encodes the row preconditions as Python
predicates and asserts that every constructed state satisfies exactly one. The
first two encode what I *meant*; only the third encodes what the spec *says*,
which is the contract. None of the walks above this line varies a record's own
type or `kind`, which is why both review lanes independently found that gap
after the third walk.

| 7,128 states | the same, plus container **interiors**: valid records, a bad decline reason, a non-mapping leaf, a non-mapping wave map, a missing `kind`, a non-string `kind`; plus `schema_version` | the rows as the spec words them, with well-formedness total over the container | 0 overlapping, 0 uncovered, all 8 rows reachable |

| 20,160 states | container values **generated from the declared key path** — a correct instance nested from it, then mutated at each depth with each hostile value — plus the earlier axes and `schema_version` | the nine rows as the spec words them | 0 overlapping, 0 uncovered, all 9 rows reachable |

| 34,720 states | the fifth walk's axes plus the **cohort state read's outcome** across its eight-value refusal vocabulary (ok, missing, unparseable, non-object root, non-regular file, changed-while-reading, oversized, non-finite number) | the nine rows as the spec words them | 0 overlapping, 0 uncovered, all 9 rows reachable |

**Bound on the sixth walk.** Its `0 uncovered` result applies only to the eight
outcomes named in that row; it is not a walk over the state reader's full
refusal vocabulary. It did not traverse invalid UTF-8, a document nested too
deeply to parse, either unopenable-path class (`cannot be examined` or
`cannot be opened safely`), a file changed while being opened, a
`could not be read safely` refusal, or the two size-cap measurement paths
separately: the pre-open stat size and the post-read byte count. The
non-object-root class was traversed and remains part of the bounded claim.

**The sixth walk's discriminating result.** A non-object JSON root classified to
*no row* under the fifth walk's predicates: it parses, so the old row 1 was
false for it, and row 2 needed `schedule_waves` read with its default, which is
undefined on a list root. It now classifies to row 1, because that row takes the
read's own refusal vocabulary rather than enumerating two of its cases. The gap
sat one level *above* the container, and the fifth walk could not exhibit it
because its domain varied the parsed value and never the read outcome.

| 41,664 states | the sixth walk's axes plus an absent `current_wave_index`, over the rows as reworded with the **readable** and **supported** predicates | the nine rows as the spec words them, encoded with no precondition the text does not state | 0 overlapping, 0 uncovered, all 9 rows reachable |

**The seventh walk caught an incomplete repair.** A Codex worker applied the
adjudicated round-7 remedies as briefed, including adding a named
supported-schema predicate to every row below the unsupported-schema row.
Encoding the rows literally afterwards found 23,436 overlapping states in two
classes, both of which the brief had not named: rows 3–9 required a supported
schema but never required the read to have succeeded, so a missing `state.json`
with a supported schema fired the read-refusal row and all of rows 3–9; and row
2 was worded around the file *parsing*, which a non-object root does while the
read still refuses it, so that state fired rows 1 and 2. Adding a named
**readable** predicate and requiring it in rows 2–9 closes both. The defect was
in the brief, not in the worker's execution — the worker did what it was told,
and what it was told was insufficient.

**Why a fifth walk exists: the fourth was green and wrong.** Its container values
were hand-built two keys deep and the predicate under test was worded two keys
deep, while the data model declared three. So a correctly shaped container
classified as malformed and the wave exit would have refused every valid state.
Demonstrated directly: `{digest: {wave: {task: record}}}` fails the fourth
walk's predicate, because `container[digest][wave]` is a `task → record` mapping
and carries no `kind`. The walk could not see it, because its oracle compared the
author's construction against the author's predicate and both were wrong in the
same direction. The fifth walk derives the predicate's depth and the domain's
shapes from one declaration, so that mismatch is not expressible.

**The fifth walk's discriminating results.** A correct three-key container with
every task accounted for passes silently. The same state with
`schema_version: 99` takes the schema row and still passes — verdict
preservation, not merely totality. A two-key container, the shape the fourth
walk built, is now rejected as malformed. An empty mapping at any level remains
well-formed, which is correct: it holds no records.

**The fourth walk's discriminating results.** A record with reason `made-up`
classifies to the malformed-state row, not to "accounted for". A record leaf that
is the string `"receipt"` classifies there too. Both were fail-open or
raise-into-`@contained` before well-formedness was made total over the
container's interior, and both were reported independently by the two review
lanes. `schema_version` is inert across `1`, `99` and absent — the same row in
all three — which is the intended consequence of `wave-exit` sharing
`implement`'s exemption.

### The walk is now a committed, self-asserting instrument

**Generator:** [`walk_verdict_partition.py`](walk_verdict_partition.py).

**Command:**

```bash
python3 docs/specs/wave-complete-dispatch-receipts/notes/walk_verdict_partition.py
```

**Recorded run — 2026-09-17, superseded (see the post-rebuild run below):**
94,080 states, 0 overlapping, 0 uncovered, all nine rows reached. Exit 0
asserts all three; it does not print them for a reader
to check.

**Why it replaced seven ad-hoc scripts.** The pass verdict is "no state matched
two rows and no state matched none", and *both halves are vacuously true of an
empty domain* — so every earlier walk's result in this ledger was consistent
with a generator that produced nothing. Reachability would have shown it, but it
was printed and read by eye, never asserted. The dispatch-rate measurement in
§ 1 was given a committed generator for exactly this reason and the partition
walks were not; that was one standard applied unevenly, and this closes it.

**Round 8 rebuilt the instrument twice, and both times it had been unable to
catch the class it was built for.**

First: accounting was a free boolean and `nest()` wrote the placeholder key
`"k"` at every level, so no state in the 94,080 held a record at
`container[digest][decimal index][task]` — the path the guard reads. The
accounted/unaccounted split rested on a variable no predicate computed, which
left a lookup with the keys in the wrong **form** (integer index rather than its
decimal string) or the wrong **order** green with every row reachable. All five
of the earlier self-mutations varied depth, never keys, because they were
generated from the same model as the instrument. Containers are now built by
`keyed_container`, keyed by the declared path, and accounting is computed from
the container against the current wave's task list.

Second: two vacuous passes. An empty partition, and an empty current wave, were
both well-formed and both exited zero and silent — the empty wave because "every
task in the current wave is accounted for" is vacuously true over zero tasks. A
partition walk cannot catch either: a wrong verdict is neither an overlap nor a
gap. Only a declared expected verdict reddens, so the instrument now carries
verdict anchors for both. Round 10 refuted the reachability half of this
entry's original reasoning: `begin_contract_amendment` writes
`schedule_waves: []` itself, and the engine applies that cohort mutation before
its own state write, so an empty partition is reachable in that crash window.
The malformed verdict stands on the silent-pass argument instead, and the spec
now names the recovery. The rest of this paragraph is the superseded reasoning,
kept because the correction is the finding —
`topological_waves` never emits an empty wave and the `plan-locked` guard
refuses an empty `schedule_waves` — so the spec now classifies both as malformed
rather than passing, and the verdict table lost its empty-partition pass row.

An earlier probe of mine reported that vacuous well-formedness "does not leak",
which was false reassurance: it tested the empty *container*, where accounting
is a separate lookup that still fails, and not the empty *wave*, where the
denominator collapses.

**Recorded run — 2026-09-17, after both rebuilds; this is the current result:**
25,872 states, 0 overlapping, 0 uncovered, all eight rows reached. Superseded
by the round-10 run recorded below, which is the current result. The state count
fell from
94,080 because the read-outcome axis was collapsed to two values: the rows do
not discriminate among refusal kinds, so enumerating fourteen of them inflated
the domain without adding a distinction any predicate makes. The acquisition
vocabulary is listed in the script for the row-1 wording it must cover, and it
now includes the two spec-directory refusals that precede the read entirely —
a class round 8 found outside the previous axis.

**Mutation proof of the rebuilt instrument.** Six mutations, each caught by a
named assertion: an empty partition allowed to pass, an empty current wave
allowed to pass, the accounting lookup using the integer wave key, the
accounting lookup reversing digest and wave, the container predicate bounded one
key short, and the domain generator returning nothing. The first attempt at that
last one was a `SyntaxError` rather than the assertion — exit 1 for the wrong
reason — and was redone with an early `return []` before being counted.

**Mutation proof of the round-9 addition.** Round 9's adversarial lane found
`ACQUISITION_REFUSALS` inert: the read axis is two-valued, so nothing in the
script read the vocabulary and its presence read as coverage it did not provide.
The script now walks every kind in it through `matching_rows` and asserts each
lands on the read-refusal row alone. Mutating `readable` from
`state["read"] == "ok"` to `isinstance(state["read"], str)` reddens it:

```
AssertionError: acquisition refusal 'spec-dir cannot be examined' must
classify to the read-refusal row alone; got ['R7-accounted']
```

That is the evidence for the two-valued axis. The collapse loses no case only
because every kind provably classifies to one row, and that is now asserted
rather than argued in prose. The spec's canonical-axis criterion and T3's
pinned `Tests` entry were reworded to the two-valued axis plus this assertion,
so the instrument no longer contradicts a pinned criterion.

**Mutation proof of the round-10 addition.** Round 10's contract lane found the
hostile leaves varied a record's `kind` and `reason` by presence and value but
never by *type*, so the declared type axis on both fields had never been
exercised. Adding `{"kind": 7}`, `{"kind": ["receipt"]}`,
`{"kind": "decline", "reason": 7}` and
`{"kind": "decline", "reason": ["no-implementer-installed"]}` did not merely
widen the domain — it crashed the run:

```
TypeError: unhashable type: 'list'
```

`is_record` tested `value.get("reason") in DECLINE_REASONS` against a
`frozenset`, and `in` raises for an unhashable left operand. The spec criterion
claims the predicate is total over every value a position can hold, so that
raise **falsified the criterion**, not just the script. Fixed with an
`isinstance(reason, str)` guard — a non-string reason is not in the closed set,
which is an answer rather than an error. Reverting the guard reproduces the
`TypeError`, so the fix is load-bearing. The domain grew from 25,872 states to
35,728, still 0 overlapping and 0 uncovered with every row reached. **This is
the current result**; every earlier run in this section is superseded.

This is the fourth time widening the walk's domain found a defect the previous
domain could not express, and the second time the defect was in a predicate
rather than in a row's wording.

**Mutation proof of the instrument's first version.** Five mutations, each caught by a
named assertion:

| Mutation | Assertion that fires |
| --- | --- |
| the domain generator returns nothing | `the domain generator produced no states` |
| row 3 regains a schema clause the spec text does not have | `rows overlap` |
| rows 3–9 lose the readability precondition | `rows overlap` |
| the container predicate is bounded one key short of the declared path | `a container nested to the declared key-path depth must be well-formed` |
| the container predicate is bounded one key too deep | the same anchor |

The fourth and fifth mutations were **not** caught by the first version of this
script. Partition properties alone do not constrain the predicate's
correctness: an empty mapping is vacuously well-formed at any depth, so every
row stayed reachable while the predicate rejected every real record. Three
anchors now pin it — the canonical container must be well-formed, the
one-key-short shape must be rejected, and the canonical accounted state must
match the accounted row alone. Round 6's blocker is exactly the fourth mutation,
so before those anchors this instrument could not have caught the defect it was
built for.

**The reusable conclusion.** A domain sourced from the predicates under test can
exhibit an overlap but never a gap. The domain has to be generated over
arbitrary values at every position the predicate reads, and the predicate has to
be total by construction rather than bounded one level at a time.

---

## 4b. A recorded alternative that is not an adopted decision

`notes/review-handoff.md` records that `schedule` clearing the receipts
container would remove the partition digest entirely, and the pruning rule, the
amendment clear, and the growth bound with it. When reporting round 5 I said that
was recorded "in the ledger"; it was recorded in the handoff, not here, and a
reviewer looking here found nothing. Correcting the citation, not the claim.

Its status is an **alternative, not a decision.** The live spec and plan specify
digest-keyed records with pruning on a partition-changing `schedule` and a clear
on contract amendment, and they are internally consistent on that reading. The
clearing alternative is attractive because `schedule` rewinds
`current_wave_index` to zero unconditionally, so a re-schedule means every wave
is re-executed and any record written before it describes work that must be
redone. Adopting it is a design change owing its own review, not a tidy-up.

## 5. Task C — boundary-walk consolidation (shipped, `9f0e939d6`)

Recorded here because the equivalence claim needs its command.

**Before/after equivalence.** The consolidated walk was compared
function-by-function against the pre-change implementation over every
`docs/specs/*/plan.md` in the tree: 423 plans, 2,449 task sections, zero
differences across `parse_plan`, `detect_unknown_deps`, `parse_touches_by_task`,
and `_task_sections`. Regenerate by loading both module versions
(`git show <base>:<path>`) and diffing their outputs per plan.

**Mutation proof.** Four mutations, each caught by a named test:

| Mutation | Test that reddened |
| --- | --- |
| refusal walks past its section end | `test_refusal_and_graph_agree_on_every_declared_id` |
| the graph walks past its section end | `test_refusal_and_graph_agree_on_every_declared_id` |
| a second heading walk added | `test_boundary_walk_has_exactly_one_owner` |
| first section starts at offset 0 | `test_task_section_text_opens_at_its_own_heading` |

The first mutation initially reddened only the structural guard, not the
agreement property, because no fixture had a task with no `Depends on:` line
followed by one naming an absent ID. Adding that case is what made the property
load-bearing.
