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

---

## 5b. Where each of T1's six predeclared questions is answered

T1's discovery predicate named six questions. The answers do not all live in one
place, so this is the index rather than a restatement. Each named home states the
surfaces it read.

| # | Question | Home |
| --- | --- | --- |
| 1 | Which surfaces execute `check --phase implement`, and does each consume the exit code? | § 2, with the `implement` leg re-confirmed against the current tree in § 6 |
| 2 | Which sites fire `wave-complete`, and does each run before or after GATES? | § 2 — seven sites across four files; GATES runs after the transition |
| 3 | What does `check_phase` do with an unsupported `schema_version` for a phase other than `implement`? | `plan.md` § Discovery decisions, first entry — it fired the kill condition |
| 4 | Which statements in the tree assert that `implement` guards `wave-complete`? | § 8.2 — five, not the three T3's `Done when` names |
| 5 | Which surfaces enumerate the phase list? | § 8.1 |
| 6 | What length bound does each refusal channel apply? | § 3 — `_MAX_REASON_CHARS = 4000`, `_scalar` at 120, `_diag` unbounded |

---

## 6. The tier-one premise, re-confirmed against the current tree (T1)

§ 2 recorded the pre-PR chain as measured on 2026-09-17. The separate-phase
design rests on one clause of it — that the hook's `implement` leg is ungated by
engine state and runs for every `docs/specs/*/state.json` — so it is re-read
here rather than inherited. Re-confirmed at `ddd85fc6e`, with 20 commits on this
branch beyond `origin/main`.

**The two halves, read at their current lines:**

| Half | Surface | What it now says |
| --- | --- | --- |
| Runs for every spec directory | `tools/hooks/pre-pr.py:134` | `state_files = sorted(Path("docs/specs").glob("*/state.json"))`, then `for state in state_files:` at 139 |
| `implement` ungated | `tools/hooks/pre-pr.py:156-160` | `for phase in ("implement", "review"):` whose only skip is `if phase == "review" and not review_phase_active: … continue` |

The `review_phase_active` flag is computed at 146-155 from
`spec_dir/engine-state.json`, and the `continue` that consumes it is guarded on
`phase == "review"`. No branch reads engine state for `implement`. Both halves
hold.

**The rest of the chain still holds too, re-read link by link:**

| Link | Surface, current line | Evidence |
| --- | --- | --- |
| 1 | `Makefile:96-97` | `pre-pr:` recipe is `$(PYTHON) tools/catalogue/pre_pr_catalogue.py` — still not `tools/hooks/pre-pr.py` directly |
| 2 | `tools/catalogue/pre_pr_catalogue.py:155-159` | `[py, "tools/hooks/pre-pr.py"]` with `check=False`, then `sys.exit(result.returncode)` — exit code still consumed |
| 3 | `tools/hooks/pre-pr.py:167-176` | non-zero from the check writes both streams and `sys.exit(1)` |
| 4 | `tools/repo/build_gate_chain.py:242-243` | still runs `tools/catalogue/pre_pr_catalogue.py` with `args=("--skip-verify",)` |
| 5 | packaged twin | `shasum -a256` gives `71ddbdc9c9ffc10d…` for both `tools/hooks/pre-pr.py` and `packs/core/.apm/hooks/pre-pr.py` — the same digest § 2 recorded |

**Why the tree moving did not move this.** `git log -1` per file: the two
`pre-pr.py` copies were last touched by `a509e1dbd` (2026-08-06),
`pre_pr_catalogue.py` by `edef05cd4` (2026-08-18), `build_gate_chain.py` by
`6354fda45` (2026-09-13). Only the `Makefile` moved on 2026-09-17
(`f2817fb35`), and its `pre-pr:` recipe is unchanged — the `Makefile:96`
citation in § 2 now points at the `pre-pr:` target line with the recipe on 97,
which is line drift, not a behaviour change.

**Scope of the claim.** `docs/specs/*/state.json` currently matches exactly one
path (this spec's own), counted with `ls docs/specs/*/state.json | wc -l`. The
premise is about the glob, not about today's count: the leg runs for however
many spec directories carry state.

---

## 7. The pinning survey (T1)

What each of the four named suites pins, and what T2 or T3 owes it. Each row
names the assertion, not only the file.

### 7.1 `test_loop_cohort_cli.py`

**Answer to the question the plan named: neither.** This suite pins **no** verb
set and **no** `--help` output. `grep -n -- "--help\|usage\|invalid choice\|Verb
surface\|subparser\|choices\|__doc__"` over the file returns nothing at all. It
reaches the CLI only by naming the verbs it exercises positionally through
`_assert_cli`, so a new `dispatch-receipt` subparser is invisible to it.

**Every `--help` assertion in the whole suite tree, found by grepping `--help`
across `packs/core/tests`, `tests` and `tools`, is subcommand-scoped and
substring-shaped:**

| Surface | Assertion | Does a new verb touch it? |
| --- | --- | --- |
| `test_loop_guards.py:205-208` (`test_load_writes_no_bytecode`) | runs `run_cohort("--help")` only to force a guard-module load; asserts `returncode == 0` and that no new `_loop_guards*.pyc` appeared. Asserts nothing about help text | No |
| `test_loop_cohort.py:907-911` (`test_schedule_help_states_canonical_plan_path`) | `schedule --help` contains `"path to plan.md (must be <spec-dir>/plan.md)"` | No |
| `test_loop_engine.py:2949-2957` (`test_reviewers_clean_record_forms_present`) | `review record --help` contains `--direct-clean`, `--report`, `--all-skipped` | No |

**What it does pin, and what T2 owes it.** `EXPECTED_STATE_KEYS` at lines 31-68
is a 29-name set asserted for **exact** equality against the bundled template by
`test_01_schema_phase_one_keys_match` (line 300):
`self.assertEqual(set(template), EXPECTED_STATE_KEYS)`, followed by
`assertFalse(PHASE_TWO_KEYS & set(template))`. T2 adds the receipts container to
`assets/state.json`, so **T2 must add the container's key to
`EXPECTED_STATE_KEYS`** in the same task or this test reds on the extra key. It
is exact equality, not a subset, so there is no way to land the template change
without touching this constant. `PHASE_TWO_KEYS` (lines 70-77) is a six-name
forbidden set; the container key must not collide with it, and it does not.

Both counts were taken by importing the test module and reading
`len(EXPECTED_STATE_KEYS)` and `len(PHASE_TWO_KEYS)`, not by eyeballing the line
range: a first pass recorded 29 as 33 from the range alone. The bundled template
holds 29 keys and the assertion passes today, so the number T2 changes is 29 to
30.

**What T3 owes it.** `_scheduled()` at line 259 is the fixture 32 call sites in
this file share (counted as the 33 lines matching `_scheduled` minus its own
`def`). Four of its five `wave advance` invocations — lines 430, 436, 443, 450 —
assert exit **0** for `--from-index 0` with **no** receipts written; the fifth,
line 453, asserts exit 1 for `--from-index 1`. So T3's coupling on the advancing
branch reds four passing cases here unless each gets a record in its fixture.
This is the file the earlier hand-picked tally missed.

**The exhaustive `wave advance` call-site count, and how it was counted.**
`find packs/core/tests tests tools -name '*.py' -not -path '*__pycache__*'`, then
`grep -cE '"wave",[[:space:]]*"advance"'` per file — the argv form, so prose
mentions of the verb do not inflate it:

| File | Sites |
| --- | --- |
| `packs/core/tests/skills/work-loop/test_loop_cohort.py` | 7 |
| `packs/core/tests/skills/work-loop/test_loop_engine.py` | 7 |
| `packs/core/tests/skills/work-loop/test_loop_cohort_cli.py` | 5 |
| `packs/core/tests/skills/work-loop/test_loop_concurrency.py` | 1 |
| **Total** | **20 across four files** |

A looser pattern that also matches the prose string `wave advance` reports 25
across the same four files, which is why the argv form is the one counted. T3's
`Tests` field owes the per-site branch triage over these 20, not over a subset.

### 7.2 `test_loop_cohort_schedule.py`

**Three whole-file source scans of `loop-cohort.py`.** These read
`LC_PATH.read_text()` and count lines, so they are file-wide, not
function-scoped — any line T2 or T3 adds anywhere in `loop-cohort.py` carrying
the scanned token reds them:

| Assertion | Line | What it forbids |
| --- | --- | --- |
| `test_detect_unknown_deps_has_exactly_one_call_site` | 698 | more than one non-`def` line containing `detect_unknown_deps(`; the surviving one must pass `scan_task_ids=` by keyword |
| `test_boundary_walk_has_exactly_one_owner` | 838 | more than one line containing `TASK_HEADING_RE.finditer`, and more than one containing `DEPENDS_LINE_RE.search`; the `finditer` must stay inside `walk_task_sections` |
| `test_schedule_is_screen_only_no_gate_call` | 642 | the substrings `dispatch_decision` and `wave_is_disjoint` inside `inspect.getsource` of `cmd_schedule`, `wave_touches_disjoint`, or `globs_overlap`; and pins `str(inspect.signature(lc.dispatch_decision))` to `"(categories, *, merge_tree_clean)"` exactly |

**What T2 owes them.** T2 edits `cmd_schedule` for container creation and stale
pruning. That edit must not introduce the substring `dispatch_decision` or
`wave_is_disjoint` into `cmd_schedule` — a live hazard, because the new verb is
spelled `dispatch-receipt` and a helper named near `dispatch_*` invites the
collision. It must also not add a second `detect_unknown_deps(`,
`TASK_HEADING_RE.finditer`, or `DEPENDS_LINE_RE.search` line anywhere in the
module.

**What it pins about `schedule`'s own behaviour.** `_seed_state` (line 284)
writes a **two-key** state — `{"schema_version": 1, "run_id": …}` — with no
receipts container and no `schedule_waves`, and `_schedule` (line 293) drives
the real CLI against it. So every `schedule` case in this file exercises T2's
absent-container path. `test_schedule_prints_topological_order` (line 306) pins
the stdout strings `"wave 1: T1"` and `"wave 2: T2"`;
`test_schedule_exits_nonzero_on_cycle` (313) pins `"cycle"` on stderr.
**T2 owes this suite that `cmd_schedule` tolerates a state with neither the
container nor `schedule_waves` present, and that it adds no stdout line these
substring assertions sit beside.**
`test_init_state_has_auto_parallel_false` (667) reads `init`'s output state for
one key only, so an added template key does not red it.

### 7.3 `test_loop_guards_parity.py`

**What it pins.** A 49-row replay table. Its `_rows()` list at lines 250-290
carries ten `check` entries — `["check", SPEC, "--phase", <phase>]` — paired with
an API lambda `g.check_phase(d, phase=<phase>)`. `test_api_and_cli_agree`
(line 383) asserts the API `ok` and the CLI return code agree, and for a row with
no `after` compares both normalized streams **byte-for-byte** against
`golden["before"]` (lines 420-427).

Two coverage properties close the table from both ends:

- `test_the_golden_set_is_fully_consumed` (line 501) — every golden row must
  appear in `_rows()` or in `EXEMPT_ROWS`, and `EXEMPT_ROWS` must name no
  vanished row. So a new golden row cannot be added without a parity row.
- `test_every_exemption_names_a_test_that_exists` (line 522) — each exemption is
  checked by AST against a real test function.

**What T2 or T3 owes it: nothing, provided no golden row is added.** The
guard-family assertion is `test_the_table_covers_every_guard` (line 440), and it
derives the family from `key.split("/")[0]` — the **verb** prefix of the golden
key — against the fixed set `{identity, schedule-check-current,
plan-check-current, check, wave-check, check-spec-status}`, requiring both
outcomes per family. A `wave-exit` phase lands under the existing `check`
family, adds no family, and owes no row. What T3 does owe is that the ten
existing `check` rows keep replaying identically — two of them
(`check/implement-ok`, `check/implement-absent-state`) have no `after` and are
therefore byte-pinned on both streams.

### 7.4 `test_golden_fixtures.py`

**What it pins.** The fixture's own shape and its live-code digest, not the CLI:

| Assertion | Line | What it pins |
| --- | --- | --- |
| `test_after_present_iff_change_reason_declared` | 218 | `after` and `change_reason` appear together, and the reason is in the closed `CHANGE_REASONS` set |
| `test_changed_rows_flip_a_verdict` | 249 | a row with an `after` must flip the pass/fail verdict |
| `test_preserved_rows_have_one_line_no_traceback_stderr` | 262 | no `Traceback`; a non-zero row's stderr is non-empty and exactly one line |
| `test_all_six_read_only_verbs_are_covered` | 287 | per-verb row-count floors — `check/` at least **6** — and both outcomes per verb |
| `test_the_unprefixed_refusal_is_recorded` | 309 | `plan-check-current/pending`'s stderr byte-exactly |
| `test_recomputed_digests_match_golden` | 342 | every corpus digest re-derived from the **current** `loop-cohort.py` still equals the frozen golden |

**What T2 or T3 owes it: nothing, and deliberately.** The `check/` floor is a
minimum (`>= 6`) and there are ten rows, so no row need be added. The digest
assertion is the one that can red from a code change, and only if
`canonical_contract` or `sha256_canonical_contract` changes — neither task
touches them. Its failure message says outright: *"Do NOT regenerate the fixture
to make this pass."*

---

## 8. The phase-list surfaces, and the statements that couple `implement` to `wave-complete` (T1)

### 8.1 Every surface that enumerates the phase list

Found by grepping `PHASES` and the literal phase names across `*.py`, `*.md`,
`*.json`, `*.toml`, `*.yml`, excluding `__pycache__`, `build/` and `dist/`.

| Surface | Form | What T3 owes it |
| --- | --- | --- |
| `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py:72` | `PHASES = ("implement", "review", "gates-failed")` — the sole declaration | add `wave-exit` here |
| `loop-cohort.py:2560` | `sp.add_argument("--phase", required=True, choices=PHASES)` — derived, holds no second list | nothing; it follows `PHASES` |
| `loop-cohort.py:16` | usage docstring `--phase {implement,review,gates-failed}` — a hand-maintained **second** enumeration | update it; nothing pins it, so it drifts silently |
| `_loop_guards.py:1220, 1224, 1241` | `check_phase`'s three `if phase == …` branches, an enumeration by exhaustion | add the `wave-exit` branch |
| `_loop_guards.py:1262` | the fall-through `GuardResult(ok=False, reason=f"unknown phase {_scalar(phase)}")` | nothing, but see below |
| `.claude/` and `.agents/` projections of the two scripts | byte copies | regenerated by `build-self`, never hand-edited |

**Nothing pins `loop-cohort.py`'s `PHASES`.** The only pinned `PHASES` in the
tree is an unrelated same-named dict in `packs/core/.apm/skills/new-spec/scripts/
explore-grounding.py`, pinned by `test_explore_grounding.py:314-318`. No test
reads `loop-cohort`'s tuple, asserts its length, or asserts an
`invalid choice` message for it. Verified by grepping `PHASES` tree-wide and by
grepping every `"--phase"` argv literal in `packs/core/tests`, `tests` and
`tools` — every one names `implement`, `review`, or `gates-failed`.

**Two facts that bound the risk of adding a member.**

- **Adding to `PHASES` cannot widen `record-attempt`.** That verb's `--phase` is
  a separate argument with its own literal at `loop-cohort.py:2615`:
  `choices=["implement"]`. Only line 2560 reads `PHASES`.
- **A member added without a branch refuses by name rather than crashing.**
  `check_phase` ends with the `unknown phase` fall-through at `_loop_guards.py:1262`,
  so the two halves of T3's change are independently safe to land in either order.

**The schema-exemption line T3 widens** is `_loop_guards.py:1210`:
`if phase != "implement" and state.get("schema_version") != SCHEMA_VERSION:`,
which sits **before** every phase branch. This is the line the kill condition
fired on, and § Discovery decisions in `plan.md` owns the decision.

### 8.2 Statements asserting that `check --phase implement` guards `wave-complete`

T3's `Done when` says three exist today. Read exhaustively, **five** do — four
prose statements and the code statement itself. The two the plan does not name
are the engine table entry and a `test_loop_engine.py` docstring. Recorded here
so T3 does not discover them.

| # | Surface | The statement | Kind |
| --- | --- | --- | --- |
| 1 | `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py:1194` (`check_phase` docstring) | "Returning `ok` unconditionally for `implement` would drop a live refusal that the `wave-complete` guard depends on." | prose |
| 2 | `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py:1558` (`cmd_check` docstring) | "…and the engine's `wave-complete` guard depends on that." | prose |
| 3 | `packs/core/tests/skills/work-loop/test_loop_guards.py:2037` (`test_check_phase_reads_state_even_for_implement` docstring) | "The engine's `wave-complete` guard is this check, so returning ok unconditionally would drop a live refusal." | prose |
| 4 | `packs/core/tests/skills/work-loop/test_loop_engine.py:1613` (`test_legal_wave_complete_to_code_verification` docstring) | "Requires: schedule check-current (pre-guard) + check --phase implement (guard)." | prose |
| 5 | `packs/core/.apm/skills/work-loop/scripts/loop-engine.py:1012` | `("code", "wave-complete"): _guard_check_phase_implement,` | code |

Both files holding #4 and #3 are already in T3's `Touches`, so no new file is
implicated. #1, #2 and #5 each have two projected copies under `.claude/` and
`.agents/` that `build-self` regenerates.

**`_guard_check_phase_implement` is defined at `loop-engine.py:867` and #5 is its
only reference** — confirmed by `grep -n "_guard_check_phase_implement"` over
`loop-engine.py`, which returns exactly those two lines. So retargeting the table
leaves it with no caller, which is why T3's `Done when` requires it removed or
given one.

**Scope boundary T3 should not try to close.** `docs/specs/loop-infrastructure-phase-1/
plan.md` states the same coupling at lines 627, 653, 823, 1084, 1115 and 1356,
and `docs/specs/work-loop-in-process-guards/spec.md:777` and `plan.md:696` describe
the `implement` stub. Those are Shipped-and-frozen contracts recording what shipped
then; this plan's Constraints require the first to stay unedited. "No statement in
the tree" is therefore satisfiable only over live surfaces, which is the five above.
`tests/roster/test_core_pre_pr_hook.py:190` says "check --phase implement is a
Phase-1 stub; review cap is the active gate", which stays true after this change
and is not a coupling statement.

---

## 9. The golden confirmation (T1)

**No golden row replays `check` with a fourth phase.** Counted by loading
`packs/core/tests/skills/work-loop/fixtures/golden_cli_streams.json` and reading
`argv` structurally rather than grepping: 49 rows, of which **10** have
`argv[0] == "check"`, and **every** row carrying `--phase` is one of those ten.
The phases present are exactly `{implement, review, gates-failed}`.

| Golden key | Phase | Has `after`? |
| --- | --- | --- |
| `check/implement-ok` | `implement` | no — byte-pinned on both streams |
| `check/implement-absent-state` | `implement` | no — byte-pinned on both streams |
| `check/review-under-cap` | `review` | no |
| `check/review-at-cap` | `review` | no |
| `check/gates-failed-under-cap` | `gates-failed` | no |
| `check/gates-failed-at-cap` | `gates-failed` | no |
| `check/unsupported-schema-non-implement` | `review` | no |
| `check/review-string-typed-count` | `review` | yes |
| `check/review-float-typed-count` | `review` | yes |
| `check/review-negative-count` | `review` | yes |

No row lacks `--phase`, and no non-`check` row carries one. So the frozen
fixture makes no statement about a `wave-exit` phase, and the two `implement`
rows are the ones T3 must leave byte-identical.

**The guard-family assertion keys on the verb, not the phase.**
`test_the_table_covers_every_guard` at `test_loop_guards_parity.py:440-461`
computes `family = key.split("/")[0]` and asserts
`set(seen) == {identity, schedule-check-current, plan-check-current, check,
wave-check, check-spec-status}` with both outcomes per family. The six names are
verb names; `check/gates-failed-at-cap` and `check/implement-ok` both reduce to
`check`. A new phase under the existing `check` verb therefore adds no family and
owes no golden row — which is what keeps the never-regenerated fixture
untouched.

**`wave advance` has no golden row either.** No row's `argv[0]` is `wave` with
`advance`, and the parity table's six families are all read-only verbs, so T3's
coupling on the advancing branch is unconstrained by the fixture.

---

## 10. T2 — the record mutation and the record lifecycle, as built

### 10.1 What landed, and where each declaration lives

One new verb, one new template key, three touched lifecycle paths, all inside
`loop-cohort.py` and its `assets/state.json`.

| Declaration | Home | Consumers in T2 |
| --- | --- | --- |
| `RECEIPTS_KEY = "dispatch_receipts"` | `loop-cohort.py` beside `PHASES` | template key, verb, `schedule`, amendment |
| `RECEIPT_KEY_PATH` (3 names) | same block | `malformed_receipts_position` depth, the verb's write, the tests' reader |
| `RECEIPT_KIND` / `DECLINE_KIND` / `DECLINE_REASONS` | same block | `is_dispatch_record`, the reason-code refusal |
| `partition_digest(waves)` | `loop-cohort.py` § dispatch receipts | the verb's write key, `schedule`'s pruning |
| `is_dispatch_record(value)` | same | record definition, total over any value |
| `malformed_receipts_position(container)` | same | the container's by-name refusal |
| `receipts_for_partition(container, digest)` | same | `_schedule_run_impl` |
| `bounded_id_list(ids)` | same | the task-membership refusal |
| `plan_dispatch_receipt(state, …)` | same | `cmd_dispatch_receipt`, and the bool-index case directly |

**The digest helper sits in `loop-cohort.py`, not in `_loop_guards.py`.** T2's
`Touches` does not contain `_loop_guards.py`, and the guard layer cannot import
this CLI (the dependency runs the other way, through `load_guards`). T3's
`Touches` contains both files, so the single-sourced home the plan's approach
note requires is reachable there: T3 relocates the helper into the guard module
and rebinds it here beside `non_negative_int`. Recorded because it is a
sequencing fact a reader of T3 needs, not a departure from the approach.

### 10.2 Reuse, not addition — the `Cut before adding` search

One bounded search for each thing the task could have written fresh:

| Needed | Search | Outcome |
| --- | --- | --- |
| non-negative integer validation | `grep -n "non_negative_int" scripts/*.py` | reused `_loop_guards.non_negative_int`, called with a one-key dict so the `--wave-index` argument reaches the same predicate the state field does |
| per-value length bound | `grep -n "_scalar\|_bounded\|_MAX_SCALAR" _loop_guards.py` | reused `_g._scalar`, newly bound at module level here; `_diag` was rejected because it applies no length bound (§ 3) |
| one-line refusal contract | `stop()` / `_diag` already in `loop-cohort.py` | reused unchanged |
| state lock | `@_locked(...)` decorator | reused; `dispatch-receipt` is the eleventh locked verb |
| atomic write | `write_state_atomic` | reused |
| record shape / key-path semantics | `walk_verdict_partition.py` § predicates | the walk's transcription of the spec was read and the implementation follows it; the walk stays the note's generator and is not imported by shipped code |

Rung reached: 7 for the four new helpers (no existing repository solution
computes a partition digest or walks this container), rung 2 for everything in
the table above.

### 10.3 The verb's refusal order, and what each refusal names

Refuse-cheapest-first, with nothing written until every check passes:

1. run identifier and schema — shared `validate_run_id` (also the `schema_version` refusal)
2. `--receipt` / `--decline` mutual exclusivity, and neither-supplied
3. decline reason membership — names both accepted codes
4. `--wave-index` type — `non_negative_int`
5. `schedule_waves` usable — non-empty list
6. container well-formed — names the malformed position from `RECEIPT_KEY_PATH`
7. `current_wave_index` type and range — `non_negative_int`, then `< len(waves)`
8. `--wave-index` at or below the pointer
9. the named wave's shape — non-empty list of strings
10. task membership — names that wave's identifiers through `bounded_id_list`

### 10.4 Observed stderr, one line per refusal class

Captured by driving the real CLI against a scheduled two-wave fixture
(`schedule_waves = [["T1","T2"],["T3"]]`, `current_wave_index = 0`):

| Input | Exit | stderr (after the `loop-cohort: stop — ` prefix) |
| --- | --- | --- |
| `--wave-index 1` (above the pointer) | 1 | `dispatch-receipt: --wave-index 1 is above current_wave_index=0; the run has not reached that wave` |
| `--receipt --decline human-directed` | 1 | `dispatch-receipt: --receipt and --decline are mutually exclusive; record one assertion per task` |
| `--decline nope` | 1 | `dispatch-receipt: --decline 'nope' is not an accepted reason; accepted: no-implementer-installed, human-directed` |
| `--task T9` | 1 | `dispatch-receipt: 'T9' is not in wave 0, which holds 'T1, T2'` |
| `--wave-index abc` | 1 | `dispatch-receipt: --wave-index must be a non-negative integer, got str` |
| `--wave-index -1` | 1 | `dispatch-receipt: --wave-index must be a non-negative integer, got -1` |
| `--wave-index 1.9` | 1 | `dispatch-receipt: --wave-index must be a non-negative integer, got str` |

The `-1` and `1.9` rows are the same helper reporting different halves of its
contract: `-1` decodes to an `int` and is refused on range, `1.9` does not
decode and is refused on type. Both messages come from `non_negative_int`, which
is what the plan asked for.

### 10.5 Two departures from a task row's literal method, each with its reason

**`--wave-index` is decoded, not parsed by argparse.** The row asks that a
negative, a boolean and a non-integer each refuse *through the guard layer's
existing non-negative-integer validation*. `type=int` in the parser would make a
non-integer die in argparse with a usage message instead, so the argument is
taken as a string and `int()`-decoded in a suppressed block: every **acceptance**
decision stays with `non_negative_int`. The decode is laxer than the validation
about spelling — `int(" 3 ")`, `int("+3")` and `int("1_0")` all decode — and
that is harmless, because each decodes to a non-negative integer the range check
then bounds against the pointer.

**The boolean case is asserted at the verb's validation entry point, not
through argv.** A process argument cannot carry a Python `bool`, so
`test_dispatch_receipt_index_validation_rejects_a_boolean` calls
`plan_dispatch_receipt` directly. This is the discriminating case for reusing
`non_negative_int` at all (§ 3), so it is asserted where it is reachable rather
than dropped. The four spellings a caller can type run through the CLI.

### 10.6 Container generation in the tests is derived, never hand-built

`_malformed_container_cases()` in `test_loop_cohort.py` wraps one hostile value
in `depth` mapping levels for every `depth` in `range(len(RECEIPT_KEY_PATH) + 1)`
— four cases, the last one a non-record leaf at the declared depth. The reader
`_record_at` builds its key list from the same declaration and asserts its
length against it. Both are the rule § 4 of this ledger records: a hand-built
container at a literal depth makes the oracle ratify its author's assumed shape.

### 10.7 The `plan.md` edit that discriminates the lifecycle assertion

`test_schedule_keeps_a_record_when_the_partition_is_unchanged` appends
`"\nProse the contract hash must notice.\n"` to the plan between the two
`schedule` runs and asserts three things in order: `plan_hash` moved,
`schedule_waves` did not, and the container is byte-equal. Observed on the run:
the assertion on `plan_hash` inequality holds, so the edit is not normalised
away by `canonical_contract` and a `plan_hash`-keyed implementation reds here.

### 10.8 Gate results for T2

| Gate | Command | Result |
| --- | --- | --- |
| lint | `make lint-ruff lint-mypy` | pass — three ruff findings (`SIM401` ×2, `SIM105`) were raised on the first run against the new code and fixed in place |
| suites | `python3 -m pytest` over the five files in T2's `Done when` | pass |
| partition walk | `python3 docs/specs/wave-complete-dispatch-receipts/notes/walk_verdict_partition.py` | exit 0, unchanged by this task |
| projection parity | `FORCE=1 make build-self`, then `shasum -a 256` over the three copies | one digest per edited file across `.apm/`, `.claude/`, `.agents/` |

### 10.9 A pre-existing projection drift this task did not land

`FORCE=1 make build-self` also rewrites
`.claude/skills/work-loop/references/supervisor-mode.md` and its `.agents/`
twin, which are **stale at HEAD**: commit `13f3363dd` edited the `.apm/` source
without regenerating. Measured at HEAD — `.apm/` is
`cb60193b40a1e1f98…`, both projections are `d2b9302830005427b…`. The two files
are outside T2's `Touches`, so they were restored to HEAD and the drift is left
for its owner; any `build-self` run reproduces the fix.

### 10.10 Mutation record for T2's clauses

Each clause was deleted in the `.apm/` source, the named case re-run, the file
restored from a byte copy, and the restore verified by digest
(`66767ef3f77c7766…`, equal across all three copies). The suites are green
again after each restore.

| Clause removed | Case re-run | Observed |
| --- | --- | --- |
| `if index > current: …` — the wave-index upper bound | `test_dispatch_receipt_refuses_an_index_above_the_pointer` | **red**, 1 failed |
| the `decline not in DECLINE_REASONS` membership check | `test_dispatch_receipt_refuses_a_reason_outside_the_closed_set` and `test_52_dispatch_receipt_records_and_refuses_through_the_cli` | **red**, 2 failed — the second is the CLI-parser entry path |
| the partition digest, replaced by `plan_hash` in both consumers (`schedule`'s pruning and the verb's write key) | the three `schedule` lifecycle cases | **red at exactly the discriminating one**: `test_schedule_keeps_a_record_when_the_partition_is_unchanged` failed, the other two passed |

The third row is the one worth reading. A `plan_hash`-keyed implementation
satisfies "a changed partition drops the record" and "the container is present",
because a partition change also changes `plan_hash`. Only the case with an
intervening plan edit that leaves the waves alone separates the two keys — which
is why that edit is in the fixture rather than a bare re-schedule.

**What this record does not cover.** The removals above are the two the plan's
inline proof names plus one design-level substitution. The malformed-position
walk, the bounding helper and the container pruning are covered by their own
cases but were not individually deleted; the spec's mutation obligation is
discharged per task, and T5 owns the sweep across every clause this change adds.

---

## 10.11 Controller verification of T2, and one self-inflicted observation (T2)

**How T2's claims were checked.** Every load-bearing claim in the implementer's
report was re-derived rather than accepted. Scope: the twelve changed files are
exactly T2's `Touches` plus this ledger. Three-copy parity: `loop-cohort.py`
hashes `66767ef3f77c7766` and `state.json` `21178af1c9f9e2f1` across
`.apm/`, `.claude/` and `.agents/`. The key set: importing the test module gives
`EXPECTED_STATE_KEYS` 30 and the bundled template 30, equal as sets, the new key
is `dispatch_receipts`, and it does not intersect `PHASE_TWO_KEYS`.

**The `--wave-index` decode, probed through the real CLI.** The deviation claims
a non-integer refuses *through* `non_negative_int` rather than in the parser, and
that the decode is laxer only about spelling. Both hold:

| Argument | Result |
| --- | --- |
| `abc`, empty, `3.5` | `--wave-index must be a non-negative integer, got str` |
| `-1` | `--wave-index must be a non-negative integer, got -1` |
| `1_0`, `+3`, `' 3 '` | decoded to 10, 3, 3, then refused by the range check |
| `0` | recorded |

The first probe of this proved nothing: it passed `--task-id`, which the verb
does not accept, so all seven arguments died in argparse and the uniform output
read as a refusal. The flag is `--task`. A probe whose failures all share one
cause cannot discriminate, which is the same defect class as a timed probe that
never fires.

**A probe against the live run writes live state.** The `0` row above recorded a
real receipt for T2 into this run's own `state.json`, under partition digest
`5199712b035c4200`, wave key `"0"`, task `T2`. It is left in place: the record is
substantively accurate — T2 was dispatched to an implementer and completed, and
the probe supplied the matching `--expect-run-id`, so the write was authorized —
and the skill forbids hand-editing `state.json`, which would be the worse
remedy. What is wrong about it is its *provenance*: it was written during
verification rather than at the dispatch moment the spec's EXECUTE step
describes. Recorded here so no later reader treats it as evidence produced by the
documented path.

The reusable lesson: probe a mutation verb against a throwaway spec directory,
not against the run you are executing. `state.json` is untracked, so the mistake
leaves no commit and no diff to notice — the loudest signal available is this
entry.
