# Plan: catalogue sync — the apply path and the scoping flags

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - Design of record: [`docs/architecture/catalogue/upstream-sync.md`](../../architecture/catalogue/upstream-sync.md) § Stage 3, § Stage 4, § Granularity, § Rollout.
  - Analogous implementation 1 — the write/remove/state sequence this mirrors without changing: `init_self_hosted`'s write block in `packages/agentbundle/agentbundle/catalogue_tooling/initialise_self_hosted.py`, and its tests in `packages/agentbundle/tests/unit/test_catalogue_tooling_self_hosted_init.py` (432 passing, and the `walk_target_tree` helper plus the `TREE_WALK_CASES` registry this plan extends).
  - Analogous implementation 2 — plan-then-consent-then-apply: `_print_plan_table` / `_confirm_or_abort` / `_finalize` in `packages/agentbundle/agentbundle/commands/upgrade.py`.
  - Phase 2's shipped half: `packages/agentbundle/agentbundle/commands/catalogue_sync.py` and `packages/agentbundle/tests/unit/test_catalogue_sync.py` (92 passing).
  - Named uncertainty: the rollback snapshot's memory bound — see § Design decisions.

## Approach

Phase 2 already resolves the source, replays the derivation in memory, and
classifies every planned path. Apply is that pipeline plus four steps: consent,
write, remove, record. Nothing about the first half moves.

The one structural decision is that `sync` gets its own write block rather than
sharing `init`'s. `init_self_hosted`'s `CONFLICT` abort and unconditional
overwrite stay byte-identical, so `init`'s contract and its 432-test suite are
untouched (owner decision 2026-09-22). The architecture's § Stage 3 wording —
that the overwrite "is replaced by" `classify` — describes `sync`'s block, not
an edit to `init`'s, and this delivery corrects the sentence.

## Constraints

- Standard library only. The apply path imports nothing new beyond `os` and
  `hashlib` alongside phase 2's existing set.
- No new module. The apply path extends `commands/catalogue_sync.py`. Outside
  it and `cli.py` there are exactly two edits: one exported helper in
  `catalogue.py`, and a non-replacing publish selector on
  `safety.write_jailed` and `safety.write_companion` whose **default is the
  behaviour those helpers have today**, per AC-0070. The selector is named
  distinctly from the `mode` parameter `write_jailed` already carries for
  permission bits, which `render.py` passes. The second touches a blessed security helper and
  is an owner decision of record, taken because the primitive's unconditional
  rename makes AC-0070 otherwise unsatisfiable.

  AC-0077 is satisfied by a third value on that same selector — publish only
  when the destination still matches the state the caller classified against —
  not by a third edit site. The check has to sit where the rename does: a
  re-read performed in `catalogue_sync.py` before calling the helper leaves the
  whole staging sequence inside the window, which is the width AC-0077 exists
  to remove. It narrows that window rather than closing it — recheck and
  `os.replace` are two operations, so a read-to-rename gap survives, and no
  portable compare-and-replace primitive is available to close it. What the
  criterion buys is that the destination is verified microseconds before the
  rename instead of before an unbounded consent wait; the residual gap is
  recorded, not eliminated. The default stays today's behaviour across all
  three values, so the caller-set argument in the paragraph above is unchanged
  and so is its audit.

  The default is what makes it safe, not the caller list. § Grounding's
  write-helper derivation counts the two sets by resolution: `write_companion`
  has 4 call sites in 4 modules, `write_jailed` 16 in 10 — so a list walked for
  the first understates the second fourfold. The four `write_companion` callers
  were walked, and each rewrites an existing companion on every run: they would
  all begin failing under a flipped default, and `upgrade` catches only the jail
  error, so the failure would escape uncaught mid-write after earlier paths
  landed.
- Every target-tree write goes through `safety.write_jailed` or
  `safety.write_companion`, the latter passing the non-replacing mode; the ownership state keeps going through
  `_write_ownership_state`, so its symlink refusal and its random `O_EXCL`
  staging name stay one implementation.
- Phase 2's `Never do` list carries forward in full except its no-write-path
  rule, which this phase replaces with a narrower one.

## Construction tests

`packages/agentbundle/tests/unit/test_catalogue_sync.py` holds every check that
runs against fixtures alone, with one exception: AC-0052's default-mode guard
belongs in the write helper's own suite, `test_safety.py`, because that is
where a flipped default would be observed and the shipped companion test there
writes to a path that does not yet exist, so it passes unchanged today. `packages/agentbundle/tests/unit/test_catalogue_tooling_self_hosted_init.py`
holds the tree-walk registry, because the helper and the cases already live
there and splitting them would leave two walks to keep agreeing.

No check in this delivery reads `docs/` or the repository root, so none belongs
in `tests/roster/` and no CI wiring edit is owed. Phase 2's roster suite and its
three wiring surfaces are untouched.

`packages/agentbundle/tests/fixtures/catalogue_sync/` gains an `edited_tree`
fixture: a derived tree with recorded paths at three Tier verdicts, recorded
paths outside every scope a test names, and a stale recorded path the guard
admits. A scoping test over a fixture with nothing outside its scope cannot
fail, which is the vacuity the fixture exists to prevent.

## Durable-output map

| Durable output | Task |
| --- | --- |
| `docs/architecture/catalogue/upstream-sync.md` | T9 |
| `guides/_shared/how-to/create-a-self-hosted-catalogue.md` | T9 |
| `packages/agentbundle/README-pypi.md`, both changelogs, `version.py`, `pyproject.toml` | T9 |

## Design (LLD)

### Design decisions

Owned by: T2, T3, T4

**The scope filter selects what is written, never what is replayed.** A
non-`None` `cfg.packs` replaces the recorded recipe inside `collect_fields`, and
`_plan_stale_owned_paths` treats every recorded path outside its `current_paths`
argument as a removal candidate. Narrowing the replay to implement a scoped run
would therefore mark the rest of the adopter's tree stale. The replay always
covers the recorded recipe — plus any name `--pack` or `--profile` introduces —
and the scope predicate filters only the write set. The removal keep-set is the
full replayed set on every run.

**An empty recorded selection must not reach `select_packs`.** That helper and
`_select_profiles` both read a falsy `explicit` argument as "no narrowing
requested" and return everything the source ships, so an empty list and `None`
are indistinguishable to them. § Grounding's widening derivation walks the
type-and-validity domain across both selection fields and reports how many
resolve to the source's full contents; the existing underivable check fires
only when `packs` and `profiles` are both absent. On phase 2's read-only path
that produced a wrong plan; here it would write everything the source ships
into the adopter's tree. The apply path resolves each category separately and
skips selection entirely for a category whose effective list is empty — which
is AC-0068's narrowing outcome for both an absent field and an empty list —
rather than handing an empty list down.

**A non-replacing publish, without giving up atomicity.** The obvious
mechanism for "never replace" is to open the destination `O_CREAT | O_EXCL`
and write into it, but that trades away what the staged write buys: a crash
mid-write leaves a partial file, and AC-0070 makes any existing destination
permanently un-writable, so the tool's own truncated output would block
delivery forever while reporting only an occupancy count. It also lands the
destination at a umask-dependent mode where the staged path yields 0600.

Staging as today and publishing with a link avoids both. A link fails when
anything is already at the destination — including a symlink, a dangling
symlink or a directory, each checked separately in § Grounding's publish
derivation — and is atomic, so no partial artifact is ever observable and the
destination inherits the staged file's permission bits.

It differs from a rename in one way that matters, and the criterion carries
it: a link does not consume the staged name. Until the publish unlinks it the
destination has a link count above one, which the confinement helpers this
command is bound to refuse outright — so an unlink that does not happen leaves
a companion the tool itself cannot read. The two modes leave the same thing
behind only on the success path; the crash window between link and unlink is
the exception AC-0070's third outcome names.

**The removal set needs its own filter, and it is not the keep-set.** The two
constraints on removal are independent and compose rather than conflict:
`_plan_stale_owned_paths`'s keep-set is the full replayed set on every run,
which is what stops a scoped run treating the rest of the recipe as stale; and
a scoped run additionally confines removal to its own scope, so a genuinely
stale path outside the scope survives until a full sync. Composed:

    removal set = (recorded − full replayed set) ∩ coverage

The shipped guard takes only the keep-set argument, so the scope half has no
seam in it and the apply path filters the returned removable list before acting
on it. Passing a scope-narrowed keep-set instead would be the § Never do
violation, because it would make every out-of-scope recipe path look stale.

The write-set filter has a second clause, and it is the one that makes phase 3
shippable at all: `credential-brokers` is default-selected, so
`packages/credbroker/**` is in essentially every derived tree's planned set, and
a vendored tree also plans `.agentbundle/tooling/**`. Refusing an
apply on such a tree would refuse almost every real tree, so the filter excludes
those paths from the write set and AC-0057 makes the printed plan show what the
filter admits. Phase 2's plan vocabulary is untouched: the deferred paths are
reported as a count, not as a sixth verdict, because a sixth verdict would
supersede phase 2's five-verdict criterion's closed set for a defect that does not need it.

**Rollback holds the prior walk tuple in memory.** Restoring a partially applied
tree needs what was there, and a Tier-1 verdict gives only a digest. The apply
path snapshots the pre-run entry set over every write-set path and its ancestor
directories — bytes, entry kind, mode and symlink target, the same tuple
AC-0041 compares — then restores from it on failure, unlinking files it created
and removing directories the pre-run walk lacked.

The snapshot and the restore have different extents, and conflating them is
the defect AC-0038 now forecloses. The snapshot spans the whole write set,
because the run cannot know which path it will fail on. The restore spans only
the paths it actually wrote, created or removed, so the run needs a record of
what it acted on, not only of what it planned to. Restoring the whole snapshot
would rewrite an adopter edit made during the run at a path the command never
reached. AC-0076 owns the bound and
the figure; this section does not restate it. Bytes alone would satisfy
AC-0038's digest half and still fail AC-0041 on a changed mode; files alone
would fail it on a `--pack <new-name>` run, which creates `packs/<new-name>/`
and leaves a `dir` entry the before-walk does not carry.

The snapshot's bound is on the **adopter** axis, not the source axis.
What is held is the adopter's prior bytes at each write-set path, and an
adopter file at a planned path is unbounded, so the source-side figure
§ Grounding measures bounds nothing here. AC-0076 owns the cap and states that
its value is a chosen ceiling rather than a measurement. The alternative — a per-path backup file — is a second write set inside
the jail and a predictable staging path, which § Never do forbids.

**Why the recorded path set excludes Tier-3 and companion paths.** AC-0059 owns
the rule; this is why it takes that shape. Recording a Tier-3 path would claim
ownership of a file `sync` never wrote and give it a digest never verified
against what is on disk. Recording a companion would make the next run's removal
guard a second, disagreeing owner of when that companion disappears — while
leaving the adopter's own file on its pre-run digest is exactly what makes the
next run classify it Tier-2 again.

**`--pack` amends the recipe by construction.** The apply path resolves
`cfg.packs` to the recorded recipe's list unioned with the requested names, so
`replay.pack_names` is already the amended selection and the new state records
it without a second code path. A run naming only packs already in the recipe
produces the same list it started with.

### Interfaces & contracts

Owned by: T1

`catalogue.py` exports the ref its `git+https://` parse already computes, so the
pin records the same value `_resolve_https` fetches against rather than a second
parse that can disagree. The module-level pattern both use is already there.

### Component / module decomposition

Owned by: T2, T3, T4, T5, T6

Six seams inside `catalogue_sync.py`, each independently testable: the scope
predicate, the write-set selector, the rollback snapshot, the consent gate, the
state merge, and the pin builder. `_run_apply` composes them and owns the exit
rows.

### Failure, edge cases & resilience

Owned by: T6

The refusal order matters twice. A `--package` run refuses before the source is
resolved, so a run that will never write performs no fetch. A leak violation
refuses before the consent prompt, so an operator is never asked to approve a
plan that cannot be applied.

### Dependencies & integration

Owned by: T1, T2, T3, T4, T5, T6

Standard library only.

## Tasks

**Review shape: MIXED.** The pure helpers, the write sequence, and the docs are
different kinds of reading, so the work decomposes into dependency-ordered
layers. T1 through T6 each leave the repository working because nothing they add
is reachable until T7 wires the parser.

### T1: the `git+https://` ref is readable without fetching

**Depends on:** none

**Tests:**
- A `git+https://host/owner/repo@v1.2.3` URI yields `v1.2.3`; the same URI with
  no `@<ref>` yields `main`; a local path and each digest-bearing scheme yield
  `None`. Verifies AC-0037's second row.
- `_resolve_https` builds its archive URL from the same helper, so a change to
  the default reaches both. The oracle is that the fetch's ref and the pin's ref
  are the same value, not that each is separately correct.

**Approach:**
- Reuse the module-level pattern `_resolve_https` already matches with. A second
  parse would be a second answer to "which ref is this", and the pin exists to
  record the one the fetch used.

**Done when:** the new tests pass and `_resolve_https` has no ref parse of its own.

**Touches:** packages/agentbundle/agentbundle/catalogue.py, packages/agentbundle/tests/unit/

### T2: a scope predicate selects the write set

**Depends on:** none

**Tests:**
- The predicate admits `packs/<name>/**` for `--pack <name>`, the exact
  `profiles/<name>.toml` for `--profile <name>`, and `guides/_shared/**` for
  `--guides`; a repeated `--pack` admits the union. Verifies AC-0043.
- With no scoping flag the predicate excludes nothing, so the admitted set is
  whatever AC-0033 clause 3 produced. Verifies AC-0042.
- Under any scope, `catalogue.toml` and every `tests/conformance/**` path is
  excluded. Verifies AC-0033 clause 4.
- Under every scope and under none, each `packages/credbroker/**` and
  `.agentbundle/tooling/**` path is excluded from the write set and reported in
  the deferred count under `deferred_package`. The whole vendored tooling root
  is the extent, not its `agentbundle/` subdirectory: the 43 paths under
  `.agentbundle/tooling/packs/catalogue-curation/` are the ones a narrower
  reading admits. Verifies AC-0033 clause 5 and AC-0066.
- `--pack core` does not admit `packs/core-extras/pack.toml`. A prefix compared
  without its trailing separator admits the sibling, and no other case in this
  task distinguishes that.

**Done when:** the predicate's tests pass against the planned-path set of a real
replay, not a hand-written list.

**Touches:** packages/agentbundle/agentbundle/commands/catalogue_sync.py, packages/agentbundle/tests/unit/

### T3: the state merge and the pin

**Depends on:** none

**Tests:**
- The merged path set equals `(recorded − removed) ∪ written`, with Tier-3 and
  companion paths absent. Verifies AC-0059.
- The state merge carries the effective selection AC-0033 clause 1 produced.
  AC-0068's own domain is driven in T6, which owns that criterion; this task
  asserts only that the merge records what clause 1 resolved.
- A written path carries the digest of the bytes written and an untouched
  recorded path carries its pre-run digest. Verifies AC-0036.
- The pin builder's four source forms each produce the row AC-0037 states,
  including `source_uri` absent under white-label on every row.
- The recipe's pack list after a `--pack <new>` run equals the pre-run list plus
  that name, order-insensitively, with no entry dropped. Verifies AC-0045.
- A scoped run's merged state carries every recorded identity field at its
  pre-run value. T2's scope predicate is a pure function over planned paths and
  cannot observe the recorded state, so this half belongs here. Verifies
  AC-0044.

**Done when:** the merge and pin tests pass and neither function touches the
filesystem.

**Touches:** packages/agentbundle/agentbundle/commands/catalogue_sync.py, packages/agentbundle/tests/unit/

### T4: the write sequence applies a plan or restores the tree

**Depends on:** T2, T3

**Tests:**
- The recorded order of jailed-write calls is packs, profiles, guides, the
  derivation-wide paths, then the state. The fourth group is non-empty only on
  an unscoped run, which is the default one, so a fixture that always supplies a
  scoping flag cannot observe it. There is no packages group: clause 5 excludes
  those paths, and asserting over a group that must always be empty is a check
  that cannot fail. Verifies AC-0032.
- The written path set equals the printed plan's admitted rows — `would-update`,
  `would-companion` contributing its companion path, and `untouched` rows for a
  pack or profile the run introduced — plus the ownership state, compared for
  equality in both directions. An oracle over `would-update` and
  `would-companion` alone rejects exactly the implementation AC-0045 requires,
  because an introduced pack's paths are all `untouched`. Verifies AC-0033
  clauses 3 and 6.
- A Tier-2 path's companion carries the replayed source bytes and the adopter's
  file has the same digest after the run as before. Verifies AC-0034.
- Stale removal runs after the last write and its keep-set argument is the full
  replayed set. Verifies AC-0035.
- An UNSCOPED run over a tree whose recorded state came from a
  `--tooling vendored` derivation leaves every `.agentbundle/tooling/**` path
  present and reports them out-of-coverage. This case is the one that matters:
  a `--pack` run excludes those paths by scope alone, so a scoped-only fixture
  passes against an implementation with no coverage rule at all. Verifies
  AC-0069.
- A `--pack` run over a fixture recording paths outside that pack leaves every
  one present — including a path the guard would otherwise admit for removal.
  Verifies AC-0064's scope axis.
- A `--guides-mode none` run over a default-derived tree leaves its recorded
  `guides/**` paths present. This is the case that separates a flag-derived
  coverage rule from a hardcoded never-remove list: `guides/` is on no such
  list, so an implementation carrying two fixed prefixes passes every other
  case here and fails only this one.
- A recorded path under `packages/credbroker/` that the source has stopped
  shipping — so the keep-set no longer protects it — is still not removed, in
  either tooling mode. Coverage, not the keep-set, is what makes that absolute,
  and no other case distinguishes the two.
- A recorded entry that becomes link-like between planning and acting is
  refused at the unlink. Verifies AC-0073.
- A recorded path spelled with a traversal, and on a case-insensitive
  filesystem one spelled with differing case, both resolve inside the protected
  subtree and are not removed. Verifies AC-0069's spelling clause.
- An occupied companion destination carrying adopter edits is byte-identical
  after the run, absent from the write set, and named on the plan and under
  `companion_occupied` in the JSON summary. Verifies AC-0070's admission half.
- A destination that is absent at admission and created before the write is
  byte-identical afterwards and the run takes the write-failed row. A
  stat-at-admission implementation using the clobbering rename passes the
  bullet above and fails only this one. Verifies AC-0070's admission race.
- After a successful publish the destination's link count is one, no staged
  sibling remains, and the confinement helpers read it back without refusing.
  A publish that links and omits the unlink passes every occupancy case and
  fails this one. Verifies AC-0070's post-publish state.
- A publish failing for a reason other than an existing destination takes the
  write-failed row and is not counted as `companion_occupied`. Verifies
  AC-0070's failure attribution.
- In the write helper's own suite, two cases against an occupied destination:
  a `safety.write_jailed` call that does not request the non-replacing publish
  replaces it, and a `safety.write_companion` call that does not request it
  replaces it too. The `write_jailed` case supplies permission bits, so it is
  not written as "passes no `mode`" — `mode` already carries those bits and
  `render` supplies them, so a case phrased that way is not the default this
  criterion pins. The `write_companion` case omits only the new publish
  selector: that helper takes `root`, `relpath` and `content` and forwards
  without `mode`, and giving it a permission-bits parameter is a third edit
  site § Constraints does not permit.
  Pinning the two separately is what catches a flipped default on the thin
  forward, which a guard written against `write_jailed` alone stays green
  through. Verifies AC-0052's default. They live there rather than here because
  that is where a flipped default is observed.
- A source planning both `x.md` and `x.upstream.md` against a Tier-2 `x.md`
  refuses the whole run, reports both paths under `companion_collision`,
  returns the cannot-answer code, and leaves the tree identical on AC-0041's
  walk tuple. Asserting only that neither path was written passes a run that
  wrote the rest of the set. Verifies AC-0071.
- A `--pack <new-name>` run whose write is injected to fail leaves no
  `packs/<new-name>/` directory behind. A file-only restore passes every other
  rollback case and fails this one. Verifies AC-0038's entry-set half.
- A fixture whose adopter-side write-set paths exceed the bound by `st_size`
  refuses before the prompt and before the first write. Verifies AC-0076's
  pre-prompt sum.
- A write-set path that grows past the bound during the prompt wait refuses
  having read no more than the bound. A finished-total implementation passes
  the bullet above and fails this one. Verifies AC-0076's as-built half.
- With a write injected to fail on the nth path, the walk tuple — path, entry
  kind, mode, symlink target and bytes — equals its pre-run value at every path
  the run wrote or created. Comparing paths and digests alone passes a restore
  that changed a mode. Verifies AC-0038's restore half.
- In the same run, a write-set path beyond the nth — one the run never reached
  — is edited by another writer after the before-walk, and still carries that
  writer's bytes after the restore. A restore driven off the whole snapshot
  rather than off what the run acted on passes the bullet above and fails this
  one, and it is the same rewrite-adopter-work defect AC-0077 refuses a write
  to avoid. Verifies AC-0038's leave-as-found half and AC-0041's every-row
  permitted difference.
- With the restore itself injected to fail, every unrestored path is named in
  the output. Verifies AC-0058.
- A planned path resolving outside the target root is refused at the write.
  Verifies AC-0052.
- A `would-update` path diverges between classification and the write, in
  three shapes, and the three do not share an exit row. Changed digest, and a
  destination classification found absent, each refuse on a `4` write-failed
  row with the adopter's bytes byte-identical afterwards. A changed entry kind
  is refused by AC-0065's confined re-read and so matches AC-0039's earlier
  `3 — cannot-answer` pre-write-read row; its oracle is AC-0041's walk tuple,
  because a regular file replaced by a symlink is a difference bytes cannot
  express. Driving all three to one expected row is the error a first-match
  reading of AC-0039's table catches. What the adopter left is the first
  assertion and the code is the second, because a stat-at-classification
  implementation that refuses only after clobbering passes an exit-code-only
  check. Verifies AC-0077.
- The apply path's target reads are refused on the hard-link and reparse-point
  inputs phase 2's path-confinement criterion fixes. Verifies AC-0065.

**Approach:**
- Removal after writes, and state after removal, because a crash between them
  must leave a tree whose recorded state under-claims rather than over-claims
  what it owns.

**Done when:** the sequence tests pass, including the injected-failure case
asserting the tree rather than the return value.

**Touches:** packages/agentbundle/agentbundle/commands/catalogue_sync.py, packages/agentbundle/agentbundle/safety.py, packages/agentbundle/tests/unit/

### T5: consent gates the first write

**Depends on:** none

**Tests:**
- Four inputs — an affirmative at the prompt, a negative, `--yes`, and
  end-of-input with no terminal — drive the gate, and its returned decision is
  the oracle in all four. AC-0031's own oracle is the target tree, which moves
  only once `_run_apply` composes this gate with the write sequence; that half
  is driven in T6, so this task keeps `Depends on: none` and the gate stays the
  stateless seam § Approach argues for. Building a T5-local composer to reach a
  tree here would test duplicated test logic rather than the planned
  implementation.
- The prompt names no source URI outside attributed mode. Verifies AC-0050.
- Each of the four source forms produces its own fidelity token on the prompt,
  and a `--yes` run carries it in the printed plan and the `--format json`
  document. The `--yes` half never prompts, so a prompt-only case leaves the
  surfaces the widening exists for unverified. Verifies AC-0072.
- A recorded value failing the terminal-safe check does not reach the prompt;
  the observable is a length or whitespace bound, not a control character, which
  an escaping sink would neutralise either way. Verifies AC-0049.

**Approach:**
- The gate reads `--yes` and the terminal, and nothing else. Reading a recorded
  value here is the seam that would reopen phase 2's modes-from-flags invariant,
  which is why the gate takes no state argument at all.

**Done when:** the four-input test passes with the gate's decision as its
assertion, and the gate takes no state argument.

**Touches:** packages/agentbundle/agentbundle/commands/catalogue_sync.py, packages/agentbundle/tests/unit/

### T6: `_run_apply` owns the apply exit rows

**Depends on:** T1, T2, T3, T4, T5

**Tests:**
- Every row of AC-0039's table is driven to its code — the apply rows and the
  four new `4 — apply-failed` rows are new here; the `--dry-run` and `--check`
  rows are re-driven rather than inherited, because the table is this spec's and
  a row phase 2 discharged for a shorter table is not evidence for this one. The
  `--package` row additionally proves no fetch was performed. Verifies AC-0039.
- The row set the run prints equals phase 2's classification of the replayed
  selection with both filters applied, and separately equals the row set its
  write phase acts on. Verifies AC-0057.
- The reported deferred count equals the number of planned package paths, and
  phase 2's seven counts over the same run match a phase-2 classification of the
  full replayed selection. Verifies AC-0066.
- A recorded selection of each invalid type, and one carrying a single name the
  source does not ship, each return the cannot-answer code naming the field —
  driven independently for `packs` and for `profiles`, since both carry the
  same falsy widening and a packs-only fixture prices only half the criterion.
  The admitted/refused split is computed by asking the selector what it
  resolves, not from an enumerated name: a fixture naming `catalogue-curation`
  is satisfiable by special-casing that string, while the drop rule is a
  selector behaviour.
  An absent field, and separately an empty list, each select nothing from that
  category and do not refuse — the empty list is named because it moved out of
  the refusing bucket and no oracle followed it. The unshipped-name case is the
  one a presence-and-emptiness fixture misses. Verifies AC-0068.
- An empty recorded category over a non-empty recorded path set removes nothing
  under that category. This is the consequence of accepting the empty list, and
  the case that would delete a recorded pack tree if coverage's selection axis
  regressed. Verifies AC-0069's selection axis.
- A run that cannot read a write-set path's pre-write state returns
  cannot-answer with no write. Verifies AC-0039's pre-write row.
- A fault injected at each boundary still reaches a named row; no uncaught
  exception sets the status. Verifies AC-0040.
- An unshipped `--pack` or `--profile` name refuses as malformed and the tree
  walk shows no write. Verifies AC-0046.
- Each recognised `--package` name refuses on an apply run, on a `--dry-run`,
  and on a `--check`; an unrecognised one is malformed. AC-0047 names all three
  invocations, and no other task drives the `--check` one, so an implementation
  that ignores a recognised package under `--check` passes every other oracle
  here. Verifies AC-0047.
- Two apply runs with identical flags over trees whose recorded modes differ
  write the same bytes to the same paths. Verifies AC-0048.
- A recorded value that fails the terminal-safe check reaches no surface; the
  observable is a length or whitespace bound, because `json.dumps` escapes a
  control character whether the check runs or not. Verifies AC-0049.
- A violating leak check leaves the tree untouched, and the consent gate T5
  introduces is never invoked. AC-0051 carries both clauses, and an
  implementation that prompts and then refuses without writing satisfies the
  tree half alone — which is also the ordering § Failure, edge cases states as
  intent and no other oracle checks. Verifies AC-0051.
- Four inputs — an affirmative at the prompt, a negative, `--yes`, and
  end-of-input with no terminal — drive a full apply run, and the target tree on
  AC-0041's walk tuple is the oracle in all four. This oracle lives here rather
  than in T5 because the tree moves only once `_run_apply` composes the gate
  with the write sequence, and T5 is the gate's decision seam alone. Verifies
  AC-0031.

**Approach:**
- The `--package` refusal and the leak refusal are placed by what they protect,
  not by convenience: the first above source resolution so no fetch happens, the
  second above the consent prompt so no operator approves an inapplicable plan.

**Done when:** every apply row of the table has a test driving it to its code.

**Touches:** packages/agentbundle/agentbundle/commands/catalogue_sync.py, packages/agentbundle/tests/unit/

### T7: the parser admits an apply run

**Depends on:** T6

**Tests:**
- The three invocation modes and each malformed combination are driven through
  the real parser, not a hand-built namespace, because the defaults a hand-built
  namespace supplies are what the parser decides. Verifies AC-0030.
- `--guides` resolves to the scoping flag and an abbreviation of
  `--guides-mode` is rejected. Verifies AC-0060.
- The registered subparser's help string, read from the parser, does not claim
  the command is read-only. Verifies AC-0074.
- An apply run with `--format json` and no `--yes` exits 2. Verifies AC-0030's
  document clause. Asserting only that `--guides`
  works passes a parser that still abbreviates.
- Scoping flags restrict a `--dry-run` plan and are malformed on `--check`.
  Verifies AC-0043's preview half and AC-0030's `--check` clause.
- The subcommand help no longer claims the command writes nothing. The message
  and its assertion move together, as runtime text in this package is pinned.

**Done when:** a bare `catalogue sync --source <path> <target>` reaches
`_run_apply`, and both-flags, `--compare-tree` without `--check`, and `--yes`
outside an apply run each exit 2.

**Touches:** packages/agentbundle/agentbundle/cli.py, packages/agentbundle/tests/unit/

### T8: the walk covers both trees

**Depends on:** T7

**Tests:**
- `walk_target_tree` already takes any root and already returns AC-0041's exact
  tuple, so no generalisation is owed — only new call sites. The sync-level
  registry is `SYNC_TREE_WALK_CASES` in `test_catalogue_sync.py`, which imports
  that helper; the registry in the init test file drives `replay_derivation`,
  not `sync`, and is not the one this task extends.
- `SYNC_TREE_WALK_CASES`'s existing test asserts `after == before`
  unconditionally, so it cannot express a permitted difference. The apply rows
  need a second parametrised test over a permitted-difference expectation; the
  no-write rows extend the existing one. Folding the apply rows into the
  unconditional test would force its assertion to weaken for every row it
  already holds.
- Between them the two tests cover every row of AC-0039's table. Each case walks
  the subject AC-0041's table names for its source form; the two digest-bearing
  forms have no source subject and are recorded as discharged by phase 2's
  deletion obligation rather than skipped silently. The `git+https://`
  form is discharged separately and on its own ground: its clone root is created
  under a fresh temporary directory after the before-walk and lies outside the
  adopter's tree entirely, so no adopter-owned path is reachable at either
  moment. The `atexit` handler is not that ground — it runs at interpreter exit,
  after the command returns, so it says nothing about the after-walk. Verifies
  AC-0041.
- The registry gains one case per row of AC-0041's permitted-difference table,
  named by that table's own row labels: `0 — success` apply, the partial-restore
  `4`, the removal-failed `4`, and the state-write-failed `4`. Declined and
  refused stay cases of the unchanged-tree rail, not permitted-difference cases
  — matching arity is not correspondence, and pairing them by count is how a
  registry comes to cover four rows while reading as though it covers five.
- Each permitted-difference case asserts the stated difference as an equality,
  not a containment.

**Approach:**
- Generalise the shipped helper rather than adding a second walk. Two walks that
  must agree is the shape that lets one drift into proving less than it reads.

**Done when:** every case in the registry runs both walks and the applied case's
difference is an equality, not a containment.

**Touches:** packages/agentbundle/tests/unit/test_catalogue_sync.py

### T9: the durable outputs are current

**Depends on:** T7

**Tests:**
- The banner and § Rollout agree on how many phases remain. Verifies AC-0053.
- The phase § Rollout marks struck through is phase 3. Verifies AC-0067.
- Every code citation in each edited architecture file resolves to the construct
  it names. Resolution is the oracle; an absence check passes a wrong re-pin.
  Verifies AC-0061.
- § Stage 3 states that `sync` classifies where `init` overwrites. Verifies
  AC-0062.
- § Granularity names both `--package` destinations and § Rollout item 4 no
  longer calls them both `packages/` subtrees. Verifies AC-0063.
- § Rollout no longer assigns the pin's first real value to phase 2. Verifies
  AC-0075.
- The phase-2 spec's Status line carries a supersession pointer naming its
  exit-code criterion's first row and its no-write walk criterion as partly
  superseded. That pointer is the only edit a frozen spec takes. Verifies
  AC-0030's supersession clause.
- The guide's new section is present in the authored source and in the projected
  copy, and both site gates pass. Verifies AC-0054.
- The release-surface derivation reports every surface reading `0.49.0`, and
  reports agreement. The derivation supplies the closed set, so a surface added
  upstream appears rather than being silently omitted. Verifies AC-0055.

**Approach:**
- The projected copy is regenerated inside this task, because a task that edits
  an authored source and leaves its projection to another task ships a tree
  where the two disagree.

**Done when:** the three checks pass and the changelog entry is topmost.

**Touches:** docs/architecture/catalogue/upstream-sync.md, docs/specs/catalogue-sync-dry-run/spec.md, guides/_shared/how-to/create-a-self-hosted-catalogue.md, packages/agentbundle/README-pypi.md, packages/agentbundle/CHANGELOG.md, docs/product/changelog.md, packages/agentbundle/agentbundle/version.py, packages/agentbundle/pyproject.toml

### T10: an adopter's apply run is exercised end to end

**Depends on:** T9

**Tests:**
- Visual / manual QA. A real derived tree is built, edited at one recorded path,
  and synced from a moved source. The run exits 0; the companion is present
  beside the edited file carrying the source bytes; the adopter's file's digest
  is unchanged; and no path outside the printed plan is altered. The ledger
  records that comparison, not only the output. Verifies AC-0056.

**Done when:** the observed output and tree are recorded in the verification
ledger.

**Touches:** docs/specs/catalogue-sync-apply/notes/verification-ledger.md

## Grounding

Each derivation below is a read-only script under
[`notes/grounding/`](notes/grounding/), invoked from the repository root. No
measured value is restated in a second prose home; the value's home is the
passage that uses it, and this section holds the command that reproduces it.

| Derivation | Command | What it establishes |
| --- | --- | --- |
| Scope subtrees | `python3 docs/specs/catalogue-sync-apply/notes/grounding/probe-scope-subtrees.py` | Each `--package` subtree's real destination, and that narrowing the replay's own selection would make the rest of the tree stale |
| Pin ref | `python3 docs/specs/catalogue-sync-apply/notes/grounding/probe-pin-ref.py` | The `git+https://` ref is parsed and discarded, and the parse is reusable from the module-level pattern |
| Jailed-write admission | `python3 docs/specs/catalogue-sync-apply/notes/grounding/probe-jailed-write-admits-planned-paths.py` | Every planned path is admitted as a direct write and as a companion write, in both tooling modes |
| Snapshot bound | `python3 docs/specs/catalogue-sync-apply/notes/grounding/probe-rollback-snapshot-bound.py` | The rollback snapshot's worst-case peak alongside the replay |
| Release surfaces | `python3 docs/specs/catalogue-sync-apply/notes/grounding/derive-release-surfaces.py` | The closed set of surfaces a version bump must move, each read by the form that surface states its version in, and whether they agree |
| Write-helper callers | `python3 docs/specs/catalogue-sync-apply/notes/grounding/derive-write-helper-callers.py` | Each write helper's call sites and modules, counted by resolution, so the opt-in audit names the set it was walked against |
| Non-replacing publish | `python3 docs/specs/catalogue-sync-apply/notes/grounding/probe-non-replacing-publish.py` | Whether a link publish refuses each occupant kind, matches the staged permission bits, and what it leaves behind after success |
| Mode asymmetry | `python3 docs/specs/catalogue-sync-apply/notes/grounding/probe-mode-asymmetry.py` | How many recorded paths a run's own modes fail to plan, per mode, and which of them any named exclusion covers |
| Recorded recipe shapes | `python3 docs/specs/catalogue-sync-apply/notes/grounding/derive-recorded-recipe-shapes.py` | Which selection shapes `init` actually writes, read from the state file after real runs rather than from a hand-built dataclass |
| Selection widening | `python3 docs/specs/catalogue-sync-apply/notes/grounding/probe-empty-recipe-widening.py` | Which recorded selection values, over the type-and-validity domain and across both `packs` and `profiles`, resolve to the source's full contents, and whether the existing underivable check fires on each |

A derivation's value and its oracle are pinned; a script's location and its
invocation arguments stay refinable without an amendment.

## Rollout

Additive with one recorded compatibility break, and one shared helper gaining
a publish selector whose default is the behaviour it has today — § Approach
states that argument and this section does not restate it. `init`, `install`, `upgrade`,
and `adapt` keep their contracts, and every `sync` flag phase 2 shipped keeps
its meaning when spelled in full. The break is abbreviation: `cli.py` sets no
`allow_abbrev=False`, so `catalogue sync --guides selected` resolves to
`--guides-mode` in 0.48.0. AC-0060 withdraws abbreviation on the `sync`
subparser, which turns that invocation into a loud error rather than a silent
change of meaning, and costs every other abbreviation of a `sync` flag. Removing the apply branch
restores phase 2 exactly. No infrastructure, no external system, no deployment
sequencing: the change ships in one package release.

## Risks

- **A scoped run's keep-set.** Getting it wrong deletes the adopter's tree
  outside the scope. Mitigated by making the full replayed set the keep-set on
  every path, and by a fixture that records paths outside every scope a test
  names.
- **Rollback fidelity.** A restore that misses a path leaves the half-applied
  tree the outcome forbids. Mitigated by asserting the tree's digests rather
  than the exit code.
- **Consent drift.** A prompt is the natural place for a recorded value to creep
  back in. Mitigated by giving the gate no state argument.

## Changelog

- 2026-09-22 — Drafted.
- 2026-09-23 — Scope approved (`spec-approved`) and build strategy approved
  (`plan-approved`) by eugenelim. Eight shaping rounds plus eight adversarial
  and eight secure-design rounds preceded approval; the blocker trend across
  the two review lanes ran 5, 11, 9, 4, 3, 1, 2, 1, with secure-design
  returning no blocker in the final two. `plan-locked` is not taken here: the
  build session's engine init seals the baseline.
- 2026-09-23 — Pre-EXECUTE review round 1 under run
  `34823a23-d407-4b5d-997f-1d306358ea18`. Two reviewers, seven raw findings,
  five sustained by adjudication and two refuted. Revised from the sustained
  five only, on eugenelim's decisions taken in session:
  - T4's AC-0052 oracle restated as two occupied-destination cases, one per
    helper, neither phrased "passes no `mode`" — the phrasing the spec's
    § Testing Strategy entry for AC-0052 already forbids.
  - T6's `--package` oracle extended to `--check`, the third invocation
    AC-0047 names and no task drove.
  - T6's leak oracle extended with AC-0051's not-prompted clause.
  - AC-0031's four-input target-tree oracle moved from T5 to T6, where
    `_run_apply` composes the gate with the write sequence. T5 keeps
    `Depends on: none` and asserts the gate's returned decision.
  - **AC-0077 added** — a replacing write rechecks its destination at the
    moment of the write. Sustained by secure design: AC-0073 binds removals
    and AC-0065 binds reads, so a replacing write was the one act still
    trusting a pre-consent verdict, and AC-0076 already records that prompt as
    an unbounded wait. Criterion counts moved 47 → 48 and the TDD group
    38 → 39. Round 2 corrected two claims made here: the refusal reaches two
    exit rows rather than one, and the recheck narrows the window rather than
    closing it.
- 2026-09-23 — Pre-EXECUTE review round 2, same run. Two reviewers, seven raw
  findings, four sustained and three refuted. Round 2 reviewed the round-1
  repairs rather than the contract, and three of the four sustained findings
  were introduced by those repairs — the fifth consecutive round in this
  contract's history where a repair opened the next round's finding. Revised
  on eugenelim's decision taken in session:
  - T4's AC-0052 companion case no longer claims to supply permission bits:
    `safety.write_companion` takes `root`, `relpath` and `content` only, and
    giving it a `mode` parameter is a third edit site § Constraints forbids.
  - AC-0077's exit-row mapping split. A changed entry kind is refused by
    AC-0065's confined re-read and so matches AC-0039's earlier
    `3 — cannot-answer` pre-write-read row; only a changed digest and a
    destination found present reach a `4` write-failed row. The blanket
    write-failed claim was false against a first-match read of that table, and
    the entry-kind fixture's oracle is now AC-0041's walk tuple rather than
    bytes.
  - AC-0077 and § Constraints now state that the recheck narrows the window
    and does not close it; recheck and rename are two operations and no
    portable compare-and-replace primitive exists here.
  - **AC-0038 and AC-0041 amended.** AC-0038's restore spanned "the whole entry
    set", so a rollback rewrote every write-set path back to the before-walk —
    including a path the command never touched, destroying an adopter edit made
    during the run. AC-0077 refused a write to prevent exactly that and the
    restore then reinstated it, which made the contract unsatisfiable. The
    restore is now scoped to what the run wrote, created or removed; the
    snapshot's extent is unchanged. AC-0041 gains an every-row permitted
    difference for a path another writer changed and the command did not act
    on. The hole was general, not AC-0077's: every write-failure path carried
    it. No row of AC-0039's table changed.
