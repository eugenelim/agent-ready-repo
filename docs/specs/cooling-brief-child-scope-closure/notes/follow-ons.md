# Follow-ons this delivery discovered

One separately scoped item surfaced while closing `cooling-brief-child-scope`.
It does not belong to this delivery's accepted contract. This document is the
artifact of the canonical `[backlog].open` entry
`docs/specs/cooling-brief-child-scope-closure/notes/follow-ons.md`
(`kind = "defect"`), which is its register.

It is recorded here rather than in an RFC-0096 erratum because the errata are
Approver-signed and the 2026-09-03 entry — the one that re-cut Wave 7b — was
written before it was known.


## `cooled-parent-scope-declaration-writer` — the fail-open answer is trusted, not verified

**Owner:** unassigned. Routed through `work-intake` at the register entry above.

The concurrent Wave 7c delivery has not accepted this item, so naming it as the
owner would park unfinished intent against a party that never agreed to it.

A cooled spec entry has three parent-scope answers, and two of them release
work: a declared brief path attributes the child, and a declared **empty** value
says the spec has no parent at all, so nothing is attributed and every dependant
dispatches.

That second answer is **trusted rather than verified**.
`provenance_mismatch` (`workspace_status_engine.py:3172`) does compare a declared
value against the artifact body, and it fires in both directions. But it is
emitted below the cooled early return at `:3138`, so it only ever runs while the
artifact is uncooled — and only if a reconciliation happens in that window.
Measured: a value declared *after* the lifecycle record lands is never compared
to anything, and `:3152-3154` returns at `missing_artifact` before the comparison
for an entry whose artifact is absent.

The engine's own shipped comment at `:2676-2683` already states the general form
of this: a declared value on a cooled entry "is unverifiable by construction,
which is the point of failing closed rather than trusting it." That reasoning
covers the *undeclared* case, which this delivery now fails closed. It does not
cover the declared-empty case, which this delivery lets through.

**What would close it.** A writer that stamps `source.parent` onto the work entry
at closeout, while the body is still readable, and refuses to write a
declared-empty value that contradicts a body-declared brief. `close-work` is the natural home, and `close_work.py` is held by the concurrent
Wave 7c delivery, so the decision crosses slice boundaries and is not this
delivery's to make.

**Why it is not a blocker.** The direction of the residual is fail-open on a
value a human wrote into a reviewed, committed file, which is the same trust
`workspace.toml` already carries for every other routing fact. ADR-0106 records
the limitation as accepted in its § *Consequences*, and this delivery's
contribution is that the *undeclared* case — the one nobody asserted anything
about — is no longer silent.


## `wave6-superseded-case-names-contradict-their-bodies` — two retained test names now misdescribe what they assert

**Owner:** unassigned. Routed through `work-intake`.

AC17 pins three function names in
`tests/roster/test_status_projection_and_context_exclusion.py` so that closing
this residual had to *update* those cases rather than delete them. The pin
worked — all three were rewritten deliberately, and the diff touches only their
three bodies. Two of the retained names now contradict the behaviour they
assert:

- `test_cooled_parentless_child_scope_residual_is_pinned` now pins the
  **closure** of that residual, not the residual.
- `test_unrelated_cooled_spec_does_not_affect_different_initiative_brief` now
  asserts that a cooled undeclared spec in another initiative **does** hold the
  first initiative's brief dependency, because the unknown-scope floor is
  repository-wide.

`test_a_cooled_parentless_spec_leaves_an_unrelated_brief_alone` is **not**
affected: its fixture was changed to declare `none`, so the name stays true and
the availability guarantee it pins survives.

This is the same shape Wave 7c measured on `cooling-scope-closure`'s AC23 — a
falsified title over a body that still holds. It is recorded rather than fixed
because renaming either function would falsify AC17, which pins the names by
string. The repair is a rename plus an AC17 amendment in one change, and it
needs this delivery to have shipped first.

Each docstring names this file, so a reader who lands on the mismatch finds the
record rather than guessing.


## `pack-scripts-cite-internal-governance-records` — a documented rule and the shipped engine disagree

**Owner:** unassigned. Routed through `work-intake`. Reported rather than
resolved, because resolving it means either changing the rule or editing eight
comments this delivery does not own.

`packs/AGENTS.md` § *Shipped pack content carries no internal-governance
citations* says: "Under `packs/`, write portable guidance only. Do not cite this
catalogue's internal records, acceptance criteria, or repository-only paths;
state the rule directly."

Measured on the shipped `workspace-status` scripts at base `58da5cc7c`, eight
citations already violate it:

| File | Line | Citation |
| --- | --- | --- |
| `workspace_status_engine.py` | 1948 | `AC37` |
| `workspace_status_engine.py` | 2138 | `AC38` |
| `workspace_status_engine.py` | 2713 | `RFC-0096` |
| `workspace_status_engine.py` | 3499 | `AC20` |
| `workspace_status_engine.py` | 4262 | `RFC-0096` |
| `workspace_status.py` | 722 | `AC28` |
| `workspace_status.py` | 791 | `AC29` |

(The eighth was this delivery's own `ADR-0106`, since removed.)

**What this delivery did.** Wrote the limitation directly instead of citing the
ADR, so its additions add nothing to the count. The pre-existing seven are left
untouched: they belong to the deliveries that wrote them, and rewriting another
delivery's comments is a larger boundary move than this scope admits.

**What the owner has to decide.** Either the rule means what it says and those
seven are debt, or the rule is meant to bind prose and not code comments, in
which case it should say so. Nothing mechanises it today — no lint checks for
this pattern under `packs/`, which is why the drift accumulated silently.


## `dedup-guard-leaks-untracked-test-files-into-the-repository-root`

**Owner:** unassigned. Routed through `work-intake`. Found while running gates
for this delivery; not caused by it.

`tools/test_local_ci_shared_test_deduplication.py` writes scaffolding test
files into the **repository root** with random suffixes — observed as
`test_state_guard_following_eo71xn6s.py` and
`test_state_guard_mutator_z0soap7h.py` — and does not remove them. They are not
covered by `.gitignore`, so `git status` reports them as untracked additions
alongside real work.

**Why it matters.** A session that stages with `git add -A` after running that
suite commits two stub tests into the repository root, where pytest's default
collection will find them. One of them starts a `multiprocessing.Process`, so
the leak is not inert. This delivery removed both by hand before committing;
nothing would have caught it otherwise.

**What would close it.** Either write the scaffolding under `tmp_path` like
every other suite, or clean up in a fixture teardown. A `.gitignore` entry
would hide the symptom while leaving the files on disk for collection to find,
so it is the weaker repair.

Observed at base `58da5cc7c`, immediately after that file was changed upstream.
