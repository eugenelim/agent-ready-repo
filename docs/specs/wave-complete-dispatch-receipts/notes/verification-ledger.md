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

**Residual I did not resolve.** `make ci` is `lint-ruff lint-mypy build-check
test-after-build-check` and does not name `pre-pr`. Whether
`build-check-unleased` reaches the hook transitively is unverified; two
comments in `.github/workflows/build-check.yml` (lines 98 and 968) assert that
`make build-check` chains `tools/hooks/pre-pr.py`, and I did not confirm that
against the recipe. The claim above is therefore scoped to `make pre-pr` and the
two test suites, which I did read.

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

Three walks were run across rounds 4 and 5. Recording all three, because the
progression is the finding.

| Walk | Domain | Oracle | Result |
| --- | --- | --- | --- |
| 480 states | my own row conditions | my intended predicates | found the row-2/row-3 overlap; **missed** the malformed wave element |
| 1,152 states | field *types* of `schedule_waves`, its current element, the container, the pointer | my intended predicates | found the malformed wave element; **missed** malformed container interiors and record leaves |
| 1,800 states | the same, plus `schedule_waves` as a dict and the container as a list | the rows **as the spec words them** | found two wording defects; **missed** record `kind` and record shape |

**What these oracles compare:** each encodes the row preconditions as Python
predicates and asserts that every constructed state satisfies exactly one. The
first two encode what I *meant*; only the third encodes what the spec *says*,
which is the contract. None of the three varies a record's own type or `kind`,
which is why both review lanes independently found that gap after the third
walk.

| 7,128 states | the same, plus container **interiors**: valid records, a bad decline reason, a non-mapping leaf, a non-mapping wave map, a missing `kind`, a non-string `kind`; plus `schema_version` | the rows as the spec words them, with well-formedness total over the container | 0 overlapping, 0 uncovered, all 8 rows reachable |

**The fourth walk's discriminating results.** A record with reason `made-up`
classifies to the malformed-state row, not to "accounted for". A record leaf that
is the string `"receipt"` classifies there too. Both were fail-open or
raise-into-`@contained` before well-formedness was made total over the
container's interior, and both were reported independently by the two review
lanes. `schema_version` is inert across `1`, `99` and absent — the same row in
all three — which is the intended consequence of `wave-exit` sharing
`implement`'s exemption.

**The reusable conclusion.** A domain sourced from the predicates under test can
exhibit an overlap but never a gap. The domain has to be generated over
arbitrary values at every position the predicate reads, and the predicate has to
be total by construction rather than bounded one level at a time.

---

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
