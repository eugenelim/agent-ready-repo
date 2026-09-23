# Plan: catalogue sync — the apply path and the scoping flags

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
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
- No new module. The apply path extends `commands/catalogue_sync.py`; the only
  edit outside it and `cli.py` is one exported helper in `catalogue.py`.
- Every target-tree write goes through `safety.write_jailed` or
  `safety.write_companion`; the ownership state keeps going through
  `_write_ownership_state`, so its symlink refusal and its random `O_EXCL`
  staging name stay one implementation.
- Phase 2's `Never do` list carries forward in full except its no-write-path
  rule, which this phase replaces with a narrower one.

## Construction tests

`packages/agentbundle/tests/unit/test_catalogue_sync.py` holds every check that
runs against fixtures alone. `packages/agentbundle/tests/unit/test_catalogue_tooling_self_hosted_init.py`
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

**Rollback holds the prior bytes in memory.** Restoring a partially applied tree
needs the bytes that were there, and a Tier-1 verdict gives only a digest. The
apply path reads the prior bytes of every write-set path that exists into a
snapshot before the first write, then restores from it on failure and unlinks
what it created. The cost is one extra copy of the write set alongside the
replay's own `file_bytes`, and § Grounding's snapshot-bound derivation measures
that worst-case peak at 34.5 MiB for the largest selection this repository can
produce. The alternative — a per-path backup file — is a second write set inside
the jail and a predictable staging path, which § Never do forbids.

**A Tier-3 path never enters the recorded state.** Tier-3 means the path is
absent from the recorded state, so `sync` leaves it alone. Recording it would
claim ownership of a file `sync` never wrote and give it a digest that was never
verified against what is on disk. The state's path set is therefore
`(recorded − removed) ∪ written`.

**A companion is not recorded either.** `adapt --ci` owns an unresolved
`.upstream.<ext>` file, and recording it would make the next run's removal guard
a second, disagreeing owner of when it disappears. The adopter's own file keeps
its pre-run recorded digest, which is what makes the next run classify it
Tier-2 again.

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
- With no scoping flag the predicate admits every planned path. Verifies AC-0042.
- Under any scope, `catalogue.toml` and every `tests/conformance/**` path is
  excluded. Verifies AC-0044.
- `--pack core` does not admit `packs/core-extras/pack.toml`. A prefix compared
  without its trailing separator admits the sibling, and no other case in this
  task distinguishes that.

**Done when:** the predicate's tests pass against the planned-path set of a real
replay, not a hand-written list.

**Touches:** packages/agentbundle/agentbundle/commands/catalogue_sync.py, packages/agentbundle/tests/unit/

### T3: the state merge and the pin

**Depends on:** none

**Tests:**
- The merged path set equals `(recorded − removed) ∪ written`; a written path
  carries the digest of the bytes written; an untouched recorded path carries
  its pre-run digest; a removed path is absent; a Tier-3 path is absent.
  Verifies AC-0036.
- The pin builder's four source forms each produce the row AC-0037 states,
  including `source_uri` absent under white-label on every row.
- The recipe's pack list after a `--pack <new>` run equals the pre-run list plus
  that name, order-insensitively, with no entry dropped. Verifies AC-0045.

**Done when:** the merge and pin tests pass and neither function touches the
filesystem.

**Touches:** packages/agentbundle/agentbundle/commands/catalogue_sync.py, packages/agentbundle/tests/unit/

### T4: the write sequence applies a plan or restores the tree

**Depends on:** T2, T3

**Tests:**
- The recorded order of jailed-write calls is packs, profiles, guides, packages,
  then the state. Verifies AC-0032.
- The written path set equals the plan's `would-update` plus `would-companion`
  rows, compared for equality in both directions. Verifies AC-0033.
- A Tier-2 path's companion carries the replayed source bytes and the adopter's
  file has the same digest after the run as before. Verifies AC-0034.
- Stale removal runs after the last write and its keep-set is the full replayed
  set: a `--pack` run over a fixture recording paths outside that pack leaves
  every one of them present. Verifies AC-0035.
- With a write injected to fail on the nth path, the tree's path set and every
  file's digest equal their pre-run values. Verifies AC-0038's restoration half.
- A planned path resolving outside the target root is refused. Verifies AC-0052.

**Approach:**
- Removal after writes, and state after removal, because a crash between them
  must leave a tree whose recorded state under-claims rather than over-claims
  what it owns.

**Done when:** the sequence tests pass, including the injected-failure case
asserting the tree rather than the return value.

**Touches:** packages/agentbundle/agentbundle/commands/catalogue_sync.py, packages/agentbundle/tests/unit/

### T5: consent gates the first write

**Depends on:** none

**Tests:**
- Four inputs — an affirmative at the prompt, a negative, `--yes`, and
  end-of-input with no terminal — drive the gate, and the target tree is the
  oracle in all four. Verifies AC-0031.
- The prompt names no source URI outside attributed mode. Verifies AC-0050's
  prompt surface.

**Approach:**
- The gate reads `--yes` and the terminal, and nothing else. Reading a recorded
  value here is the seam that would reopen phase 2's modes-from-flags invariant,
  which is why the gate takes no state argument at all.

**Done when:** the four-input test passes with the tree as its assertion.

**Touches:** packages/agentbundle/agentbundle/commands/catalogue_sync.py, packages/agentbundle/tests/unit/

### T6: `_run_apply` owns the apply exit rows

**Depends on:** T1, T2, T3, T4, T5

**Tests:**
- Each apply row of AC-0039's table is driven to its code, including the
  `--package` row proving no fetch was performed. Verifies AC-0039.
- A fault injected at each boundary still reaches a named row; no uncaught
  exception sets the status. Verifies AC-0040.
- An unshipped `--pack`, `--profile`, or `--package` name refuses and the tree
  walk shows no write. Verifies AC-0046, AC-0047.
- Two apply runs with identical flags over trees whose recorded modes differ
  write the same bytes to the same paths. Verifies AC-0048.
- A recorded value that fails the terminal-safe check reaches no surface; the
  observable is a length or whitespace bound, because `json.dumps` escapes a
  control character whether the check runs or not. Verifies AC-0049.
- A violating leak check leaves the tree untouched. Verifies AC-0051.

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
- The subcommand help no longer claims the command writes nothing. The message
  and its assertion move together, as runtime text in this package is pinned.

**Done when:** a bare `catalogue sync --source <path> <target>` reaches
`_run_apply`, and both-flags, `--compare-tree` without `--check`, and `--yes`
outside an apply run each exit 2.

**Touches:** packages/agentbundle/agentbundle/cli.py, packages/agentbundle/tests/unit/

### T8: the walk covers both trees

**Depends on:** T7

**Tests:**
- The existing walk helper generalises to any root, and every registered case
  asserts the source tree identical before and after. Verifies AC-0041's
  source-side rail.
- The registry gains one case per apply row: declined, refused, rolled back, and
  applied. The applied case asserts the target differs by exactly the written
  set, the removed set, and the state — not merely that it differs.

**Approach:**
- Generalise the shipped helper rather than adding a second walk. Two walks that
  must agree is the shape that lets one drift into proving less than it reads.

**Done when:** every case in the registry runs both walks and the applied case's
difference is an equality, not a containment.

**Touches:** packages/agentbundle/tests/unit/test_catalogue_tooling_self_hosted_init.py

### T9: the durable outputs are current

**Depends on:** T7

**Tests:**
- Every code citation in the edited architecture file resolves to the construct
  it names, and the rollout's phase count agrees with its own list. Resolution
  is the oracle; an absence check passes a wrong re-pin. Verifies AC-0053.
- The guide's new section is present in the authored source and in the projected
  copy, and both site gates pass. Verifies AC-0054.
- Every derived release surface reads `0.49.0`. Verifies AC-0055.

**Approach:**
- The projected copy is regenerated inside this task, because a task that edits
  an authored source and leaves its projection to another task ships a tree
  where the two disagree.

**Done when:** the three checks pass and the changelog entry is topmost.

**Touches:** docs/architecture/catalogue/upstream-sync.md, guides/_shared/how-to/create-a-self-hosted-catalogue.md, packages/agentbundle/README-pypi.md, packages/agentbundle/CHANGELOG.md, docs/product/changelog.md, packages/agentbundle/agentbundle/version.py, packages/agentbundle/pyproject.toml

### T10: an adopter's apply run is exercised end to end

**Depends on:** T9

**Tests:**
- Visual / manual QA. A real derived tree is built, edited at one path, and
  synced from a moved source. The recorded evidence is the stdout, the exit
  code, and the resulting tree — including the companion beside the edited
  file. Verifies AC-0056.

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

A derivation's value and its oracle are pinned; a script's location and its
invocation arguments stay refinable without an amendment.

## Rollout

Additive. `init`, `install`, `upgrade`, and `adapt` keep their contracts, and
the `sync` flags phase 2 shipped keep their meanings. Removing the apply branch
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
