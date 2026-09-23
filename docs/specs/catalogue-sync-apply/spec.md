# Spec: catalogue sync — the apply path and the scoping flags

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0059 (the catalogue-curation pack, which owns the white-label export boundary)
- **Contract:** none — `sync` reads and writes `.agentbundle/self-host-state.json`, which is defined in code only and has no file under `contracts/`
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author
> corrects them in place as the work teaches, without an amendment and without
> a review round. A review finding against working material is advisory — it
> cannot block, because nothing gates the text it cites.

## Outcome

An adopter who derived a catalogue and then edited it takes later upstream
changes by running `agentbundle catalogue sync`, and gets exactly the plan
`--dry-run` printed: their edited files survive behind `.upstream.<ext>`
companions, everything else moves to the source's bytes, and the tree records
which upstream it now matches. Success is that a run never leaves a
half-applied tree silently — every path the plan named is written, or the tree
is the one that existed before the command started, or the run names exactly
what it left behind.

## What Changes

- `agentbundle catalogue sync` gains a write path — `catalogue_sync.py` grows
  an apply branch beside `_run_dry_run`, `_check_digest_only` and
  `_check_compare_tree`.
- `--dry-run` and `--check` stop being jointly required. Neither flag means
  apply — `cli.py`'s mutually exclusive group loses `required=True`.
- Five new flags on the `sync` subparser: `--pack` (repeatable), `--profile`,
  `--guides`, `--package`, and `--yes`.
- A fifth exit code, `4 — apply-failed`, for a run whose writes were undone.
  Codes `0`–`3` keep the meanings they have.
- The recorded pin gains real values: `source_revision` for a `git+https://`
  source, `archive_sha256` for a digest-bearing one. `catalogue.py` exposes the
  ref its `git+https://` parse already computes.
- `init_self_hosted` is untouched. Its `CONFLICT` abort and its unconditional
  overwrite stay exactly as they are; `sync` classifies in its own write block.
- The subcommand help stops saying "Read-only: writes nothing."

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Applicable — this delivers phase 3 of that rollout; § Rollout item 4 calls both `--package` targets `packages/` subtrees, and only one is | [`docs/architecture/catalogue/upstream-sync.md`](../../architecture/catalogue/upstream-sync.md) | eugenelim | Banner and § Rollout mark phase 3 done and one phase remaining; § Rollout item 4's subtree claim corrected; § Stage 3 says `sync` classifies where `init` overwrites rather than that the overwrite is replaced; § Granularity, which today names no destination for either subtree, gains one | AC-0053, AC-0061, AC-0062, AC-0063, AC-0067 and AC-0075 pass |
| User-facing promise | Applicable — apply is the reason the verb exists, and this guide is projected into the docs site | `guides/_shared/how-to/create-a-self-hosted-catalogue.md` | eugenelim | A section covering the apply run, consent, the scoping flags, and what a companion file obliges | AC-0054 passes, including its projected-surface half |
| Interface compatibility | Applicable — the PyPI readme is a pinned release surface | `packages/agentbundle/README-pypi.md` | eugenelim | A "What's new in" section naming the version AC-0055 fixes | AC-0055 passes |
| Release history | Applicable — new flag semantics and a new write path are release-coupling triggers | [`packages/agentbundle/CHANGELOG.md`](../../../packages/agentbundle/CHANGELOG.md), [`docs/product/changelog.md`](../../product/changelog.md) | eugenelim | A topmost entry naming the version AC-0055 fixes, written adopter-first | AC-0055 passes |
| Decision rationale | Not applicable — every decision this delivery makes is recorded as a criterion or in the plan's design; none changes a repository-wide rule | — | — | — | — |
| Maintainer procedure | Not applicable — no runbook governs this command | — | — | — | — |

## Agent Rules

### Always do

- Phase 2's § Boundaries § Always do carries forward in full and unchanged,
  including the recorded decision attached to `_is_attributed`: it is the single
  attribution gate, that obligation is enforced by review rather than
  mechanically, and review must catch two shapes — an output-only duplicate gate
  and an agreeing duplicate that drifts later. Re-typing those bullets here
  would create a second home that degrades at the moment of writing, which is
  what this pointer replaces.
- The deltas this phase adds to that list:
  - Take consent before the first write, and apply the same plan the operator
    consented to.
  - Write every file under the target tree through the jailed write primitive.
  - Treat the consent prompt as an output surface: every obligation phase 2
    states about stdout, stderr and the `--format json` document reaches it too.
  - Leave the target tree as it was before the run whenever the run does not
    complete.

### Ask first

- Before adding a flag beyond the five this spec declares.
- Before introducing a sixth exit code, or changing a row of AC-0039's table.
- Before changing what `init` writes, aborts on, or removes.
- Before widening what a scoped run may touch beyond its declared subtree.

### Never do

- Phase 2's § Boundaries § Never do carries forward in full, with one
  replacement: its no-write-path rule is replaced by the first two deltas below,
  because this phase has a write path. Every other rule it states still binds,
  including that URI dispatch, the Tier contract and the removal guard are never
  re-implemented. Its recorded-value rule binds here with one narrowing: a
  recorded `managed_paths` entry does resolve as a path, because the removal
  guard AC-0035 requires must resolve one to act, and the confinement helpers
  AC-0065 names are what bound that resolution.
- The deltas this phase adds to that list:
  - Never write, move, delete, or change the mode of a path the printed plan did
    not name.
  - Never leave a half-applied tree without naming what is unrestored.
  - Never write anything under the target tree when the identity leak check
    reported a violation.
  - Never introduce a predictable staging path.
  - Never narrow the stale-removal keep-set to a scoped subset.
  - Never write under `packages/credbroker/` or `.agentbundle/tooling/`,
    whether or not `--package` was supplied.

## Testing Strategy

Three modes, over 47 criteria. Each entry names the comparison its oracle
performs, not the property it hopes to establish.

**TDD** covers AC-0030 through AC-0052, AC-0057 through AC-0060, AC-0064 and
AC-0065, AC-0066, AC-0068 through AC-0074, and AC-0076 — thirty-eight
criteria, each a compressible invariant over a pure function or a single `sync`
call. AC-0075 is goal-based and is counted there, not here.

- **Invocation grammar (AC-0030)** — TDD. Oracle: the parser's exit status and
  the handler's returned code across the three modes and each malformed
  combination, driven through the real `cli.py` parser rather than a hand-built
  `Namespace`, because a hand-built namespace supplies the defaults the parser
  is what decides.
- **Abbreviation posture (AC-0060)** — TDD. Oracle: `--guides` resolves to the
  restrictor and an abbreviation of `--guides-mode` is rejected. Asserting only
  that `--guides` works passes a parser that still abbreviates, which is the
  state this criterion exists to end.
- **The help text (AC-0074)** — TDD. Oracle: the registered subparser's help
  string, read from the parser rather than from the source file.
- **Consent (AC-0031)** — TDD. Oracle: the target tree's file set before and
  after on the walk tuple AC-0041 compares, under each of four inputs — an
  affirmative at the prompt, a refusal, `--yes`, and EOF with no TTY. Comparing
  only the file set passes a decline that rewrote every file's bytes, and
  asserting only the declined message passes one that wrote anyway.
- **The printed plan (AC-0057)** — TDD. Oracle: the row set the run prints,
  compared against phase 2's classification of the replayed selection with the
  two filters applied — an anchor outside the run, so AC-0033's equality rests
  on something the run does not itself define. A second assertion compares the
  printed rows against the rows the write phase acts on, which is the
  consented-plan-is-applied half.
- **The deferred count (AC-0066)** — TDD. Oracle: the `deferred_package` count,
  on the printed table and in the `--format json` `summary` object, equals the
  number of planned paths under the two subtrees, and phase 2's seven counts
  over the same run are byte-identical to what a phase-2 classification of the
  full replayed selection produces. The second half is what proves the identity survived.
- **Apply order (AC-0032)** — TDD. Oracle: the recorded sequence of jailed-write
  calls, compared against the fixed order. An assertion that all paths exist
  after the run cannot observe order at all.
- **The write set (AC-0033)** — TDD. Oracle: the set of paths written, compared
  for equality in both directions against the rows AC-0033 clauses 1 to 5 admit
  — `would-update`, `would-companion` contributing its computed companion path,
  and `untouched` for a pack or profile the run introduced — plus clause 6's
  ownership state, which AC-0057 keeps off the printed plan. A subset check
  passes a run that wrote nothing.
- **Companion write (AC-0034)** — TDD. Oracle: the companion's bytes equal the
  replayed source bytes, and the adopter's file's sha256 is unchanged across the
  run. The second half catches a companion written correctly and the original
  clobbered.
- **An occupied companion destination (AC-0070)** — TDD. Oracle: with an
  adopter-edited `.upstream.<ext>` already present, its bytes after the run are
  unchanged, its path is a reported entry rather than an acted row, the
  `summary` object carries it under `companion_occupied`, and the run's code is
  the difference row rather than success. A second case creates the destination
  between admission and the write and asserts the write fails rather than
  replaces. Asserting only that the original survives passes the clobber this
  criterion exists to stop.
- **A companion collision (AC-0071)** — TDD. Oracle: a source planning both
  `x.md` and `x.upstream.md` against a Tier-2 `x.md` refuses the whole run with
  the cannot-answer code, names both paths under `companion_collision`, and
  leaves the tree identical on AC-0041's walk tuple. Asserting only that
  neither path was written passes a run that wrote the rest of the set.
- **Stale removal ordering and keep-set (AC-0035)** — TDD. Oracle: the recorded
  call order places removal after the last write, and the keep-set argument
  equals the full replayed planned set.
- **Removal stays inside coverage (AC-0064, AC-0069)** — TDD. Oracle: an
  **unscoped** run over a tree whose recorded state was written by a
  `--tooling vendored` derivation leaves every `.agentbundle/tooling/**` path
  present, and the `summary` object carries them under `out_of_coverage` on
  both the printed plan and the `--format json` document. A second case spells
  a recorded path with a traversal and, where the platform allows, a differing
  case, and asserts the protected path still resolves inside the exclusion. The unscoped run is the oracle
  that matters: a `--pack` run excludes those paths by scope alone, so a
  scoped-only fixture passes against an implementation carrying no coverage
  rule at all. A second case covers the scoped axis.
- **Removals are confined at the unlink (AC-0073)** — TDD. Oracle: a recorded
  entry that becomes link-like between planning and acting is refused at the
  unlink, not only at the plan.
- **The recorded path set (AC-0059)** — TDD. Oracle: the state's path set after
  the run equals `(recorded − removed) ∪ written`, with Tier-3 paths and
  companion paths absent, compared for equality.
- **The recorded digests (AC-0036)** — TDD. Oracle: for each path in that set,
  the digest equals the written bytes' digest when the run wrote it and the
  pre-run recorded value when it did not.
- **The pin per source form (AC-0037)** — TDD. Oracle: the four-row table, each
  row asserting which of the three pin fields is present and which absent.
- **Rollback (AC-0038)** — TDD. Oracle: with a write injected to fail partway,
  the target tree's walk tuple equals its pre-run walk tuple — path, entry kind,
  mode, symlink target and bytes, the same tuple AC-0041 compares. Comparing
  only paths and digests passes a restore that changed a mode.
- **A failed restore is named (AC-0058)** — TDD. Oracle: with both the write and
  its restore injected to fail, the reported output names each unrestored path.
- **The snapshot bound (AC-0076)** — TDD. Oracle: a fixture whose adopter-side
  write-set paths exceed the bound by `st_size` refuses with no write and
  before the prompt, and the tree walk proves it. A fixture sized from the
  source tree cannot reach the bound, which is the measurement error the
  criterion exists to correct.
  This is the one outcome § Never do forbids absolutely, so the criterion exists
  to make it legible rather than to permit it.
- **Exit codes and totality (AC-0039, AC-0040)** — TDD. Oracle: every row of the
  table driven to its code, plus a fault injected at each boundary to prove no
  uncaught exception sets the status.
- **The before-and-after walks (AC-0041)** — TDD. Oracle: a non-dereferencing
  walk of the target, and of the source subject the criterion names for that
  source form, compared before and after each row of the table.
- **Recipe as filter (AC-0042)** — TDD. Oracle: with none of the four flags,
  AC-0033 clause 1's effective selection equals the recorded recipe's lists
  exactly, and the scope predicate excludes no admitted path. Comparing the
  written set instead fails a correct run over a tree already matching its
  source, where clause 3 admits nothing and the write set is the ownership
  state alone.
- **The scoping flags (AC-0043)** — TDD. Oracle: the written set and the printed
  plan's row set both compared against the declared subtree, for each of
  `--pack`, `--profile` and `--guides`, for a repeated `--pack`, and on
  `--dry-run` as well as on an apply run.
- **Derivation-wide paths stay whole (AC-0044)** — TDD. Oracle: a scoped run
  over a fixture whose `catalogue.toml` and `tests/conformance/` entries are
  stale leaves both untouched and the recorded identity fields unchanged.
- **A new name amends the recipe (AC-0045)** — TDD. Oracle: the recorded
  recipe's pack list after the run equals the pre-run list plus the named pack.
- **An unshipped name refuses (AC-0046)** — TDD. Oracle: the code, plus the tree
  walk proving no write.
- **`--package` reserves without writing (AC-0047)** — TDD. Oracle: each
  recognised name refuses on an apply run and on a `--dry-run`; the tree walk
  proves neither subtree was written; an unrecognised name is malformed.
- **Modes still come from flags and defaults (AC-0048)** — TDD. Oracle: two
  apply runs with identical flags over trees whose recorded modes differ produce
  the same written byte map. This is the phase-2 invariant a consent prompt is
  most likely to reopen, so the oracle drives the whole run, not the seam.
- **The consent prompt is an output surface (AC-0049, AC-0050)** — TDD. Oracle:
  the prompt is driven through the same two checks phase 2 fixes for its other
  surfaces — a value failing the terminal-safe check does not reach it, and the
  source URI does not appear on it outside attributed mode. The observable for
  the first is a bound the sink does not normalise, length or surrounding
  whitespace, because an escaping sink makes a control-character test vacuous.
- **Fidelity on every apply surface (AC-0072)** — TDD. Oracle: each of the
  four source forms produces its own fidelity token on the prompt, and on a
  `--yes` run — which never prompts — in the printed plan and in the
  `--format json` document. The `--yes` half is the one the widening exists
  for, so a prompt-only fixture leaves it unverified.
- **A leak violation reaches no write (AC-0051)** — TDD. Oracle: the tree walk
  after a violating run. The pass direction cannot distinguish a working refusal
  from an absent one, so the fixture must violate.
- **Every write is jailed (AC-0052)** — TDD. Oracle: a planned path resolving
  outside the target root is refused at the write.
- **Every target read is confined (AC-0065)** — TDD. Oracle: the hard-link and
  reparse-point cases phase 2's path-confinement criterion fixes, re-driven through the apply
  path's own reads. The criterion is phase 2's; only the caller is new.
- **The selection never widens (AC-0068)** — TDD. Oracle: the selection
  resolved for each recorded value, over the type-and-validity domain the
  criterion fixes, driven independently for `packs` and for `profiles` because
  both fields carry the same falsy widening. Three outcomes, each named: a
  present-but-invalid value refuses; an absent field selects nothing; **an
  empty list selects nothing**. The empty list is the case whose regression
  deletes a recorded category, and it moved out of the refusing bucket without
  an oracle following it, so it is named here rather than left inside "each
  invalid type". A fourth case pairs an empty recorded category with a
  non-empty recorded path set and asserts nothing under that category is
  removed, which is AC-0069's selection axis. § Grounding's
  widening derivation measures how many shapes resolve to the source's full
  contents today, so a fixture carrying only valid non-empty lists cannot
  fail.

**Goal-based checks** cover AC-0053, AC-0054, AC-0055, AC-0061 through AC-0063,
AC-0067 and AC-0075 — eight delivery conditions, each a command whose output is
the answer.

- **Rollout phase count (AC-0053)** — goal-based. Oracle: the banner's claim and
  § Rollout's own list agree on how many phases remain.
- **The delivered phase (AC-0067)** — goal-based. Oracle: the phase § Rollout
  marks struck through is phase 3. A file whose banner and list agree on a count
  while still naming phase 2 as delivered passes AC-0053 and fails this.
- **Citations resolve (AC-0061)** — goal-based. Oracle: every code citation in
  the edited architecture file resolves to the construct it names. An absence
  check passes a wrong re-pin, which is why resolution is the oracle and not a
  grep.
- **§ Stage 3 wording (AC-0062)** — goal-based. Oracle: the section states that
  `sync` classifies where `init` overwrites, and does not state that the
  overwrite is replaced.
- **The package subtrees (AC-0063)** — goal-based. Oracle: § Rollout item 4 no
  longer calls both targets `packages/` subtrees, and § Granularity names each
  one's destination.
- **The pin's phase (AC-0075)** — goal-based. Oracle: the sentence assigning
  the pin's first real value to phase 2 is absent from § Rollout.
- **Guide covers the apply run (AC-0054)** — goal-based. Oracle: the section
  exists in the authored source and in the projected copy, and both site gates
  pass.
- **Version across the release surface (AC-0055)** — goal-based. Oracle: the
  release-surface derivation the plan's § Grounding names reports every surface
  reading the same string, and that string is `0.49.0`. The derivation supplies
  the closed set; this criterion does not enumerate it by hand.

**Visual / manual QA** covers AC-0056 — one criterion. That is 38 + 8 + 1 = 47.

- **The apply run an adopter performs (AC-0056)** — visual / manual QA. Oracle:
  the comparison the criterion names, performed against a real derived tree and
  recorded. Recording the output without comparing it is what the criterion's
  wording exists to rule out.

## Acceptance Criteria

- [ ] **AC-0030.** `--dry-run`, `--check`, and neither are three mutually
  exclusive invocation modes; neither flag means apply. This supersedes two
  criteria of [phase 2's spec](../catalogue-sync-dry-run/spec.md), which is
  frozen: its exit-code criterion's "neither or both" malformed row, and its
  no-write walk criterion's coverage of the bare invocation. Both assume no
  apply path exists, and the phase-2 spec's Status line records that
  supersession — the one edit a frozen spec takes. Supplying both
  flags is malformed, `--compare-tree` without `--check` is malformed, `--yes`
  outside an apply run is malformed, and any of `--pack`, `--profile` or
  `--guides` supplied with `--check` is malformed. An apply run with
  `--format json` and without `--yes` is malformed, because the prompt and the
  document would share stdout and phase 2 makes that document a parse
  contract.
- [ ] **AC-0031.** An apply run writes nothing until consent is given. Consent
  is an affirmative answer at the prompt or `--yes` on the command line; a
  negative answer, an end-of-input, or an absent terminal with no `--yes` all
  leave the target tree identical on the walk tuple AC-0041 compares.
- [ ] **AC-0032.** The paths AC-0033 clause 5 leaves admitted are written in
  the order packs, profiles, guides, then the derivation-wide paths — which an
  unscoped run still admits — and AC-0033 clause 6's ownership state after all
  four.
- [ ] **AC-0033.** **The write set is defined here and nowhere else.** Every
  other criterion that constrains what an apply run writes names a clause of
  this definition rather than restating a scope over it. The set of paths an
  apply run writes is constructed in this order, and equals the result exactly:

  1. **Effective selection.** The recorded recipe's packs and profiles, unioned
     with every name `--pack` or `--profile` supplies that the recipe does not
     already carry. AC-0068 fixes what an empty or absent recorded list
     resolves to; it never resolves to the source's full contents.
  2. **Replay and classify.** Replay that selection and classify every planned
     path by the verdicts phase 2's five-verdict criterion fixes.
  3. **Admit** a path that is `would-update`; the path
     `safety.companion_path` computes for a path that is `would-companion`,
     unless AC-0070 finds that destination already occupied, in which case that
     companion is not admitted; and a path that is
     `untouched` only because it belongs to a pack or profile clause 1
     introduced. A path `untouched` for any other reason is not admitted, which
     is what keeps an adopter's unrecorded file untouched.
  4. **Exclude** every admitted path outside the scope AC-0043 fixes. That
     scope contains no derivation-wide path, so a scoped run excludes
     `catalogue.toml` and every path under `tests/conformance/` by this clause
     alone and needs no second exclusion for them.
  5. **Exclude** every admitted path under `packages/credbroker/` or
     `.agentbundle/tooling/`. The architecture defers the whole vendored
     tooling root to phase 4, not only its `agentbundle/` subdirectory, so the
     write set and AC-0069's coverage name the same extent and "a run that may
     not write a subtree may not delete from it" is true of every path in it.
  6. **Add** the ownership state whenever the run reaches its write phase with
     consent given, whatever clause 4 excluded. A run that refuses or is
     declined never reaches that phase, so its write set is empty.

  No other path under the target tree is created, modified, moved, or has its
  mode changed.
- [ ] **AC-0034.** A `would-companion` path whose computed companion
  destination AC-0033 clause 3 admits receives that path carrying the replayed
  source bytes, and the adopter's own file at the original path has the same
  sha256 after the run as before it.
- [ ] **AC-0035.** Stale removal runs only after every planned write has landed,
  keeps its sha256 guard unchanged, and computes its keep-set from the full
  replayed planned set rather than from the write set.
- [ ] **AC-0036.** For every path in the recorded path set AC-0059 fixes, the
  recorded sha256 equals the digest of the bytes the run wrote to it when the
  run wrote it, and the value recorded before the run when it did not.
- [ ] **AC-0037.** The pin each source form records is the row for that form.
  Three rows relocate the values phase 2's source-fidelity criterion already
  fixes. The `git+https://` row does not: phase 2 reports `source_revision`
  absent for that form because the resolver computes the ref and discards it,
  and recording it is the change phase 2's own follow-on assigned to this
  phase. § Grounding's pin-ref derivation establishes that value:

  | Source form | `source_uri` | `source_revision` | `archive_sha256` |
  | --- | --- | --- | --- |
  | local clone path | the resolved path, under `attributed` only | absent | absent |
  | `git+https://…[@<ref>]` | the URI, under `attributed` only | the ref the URI names, or `main` | absent |
  | `archive+https://…` | the URI, under `attributed` only | absent | the verified digest |
  | `catalogue+https://…` | the URI, under `attributed` only | the descriptor's `source_revision`, or absent | the verified digest |

  `synced_at` is recorded on every row. Under `--attribution white-label` a
  recorded `source_revision` passes the bounded terminal-safe scalar check and
  a ref-shaped constraint before it is written, and is omitted when it fails
  either. The architecture's decision that a ref identifies nothing reasons over
  a ref such as `v1.2.3`; the value reaching the pin is free text from an
  operator-supplied URI, and the state file is the one artifact § Never do keeps
  permanently outside the identity leak check.
- [ ] **AC-0038.** When any planned write fails, the command restores the target
  tree before returning to the walk tuple AC-0041 compares — relative path,
  entry kind, mode, symlink target and bytes — over the whole entry set, so a
  directory the run created and the pre-run walk lacks is removed too. Whether that restore succeeds
  selects between two rows of AC-0039's table, which is the sole authority on
  the resulting code; AC-0058 governs what a restore that does not succeed must
  report.
- [ ] **AC-0039.** The command's exit code is the first matching row of this
  table, read top to bottom, and no input produces a code outside it:

  | Invocation | Condition | Code and name |
  | --- | --- | --- |
  | any | the invocation is malformed, including an omitted `--source`, both of `--dry-run` and `--check`, `--compare-tree` without `--check`, `--yes` outside an apply run, a scoping flag with `--check`, an apply run with `--format json` and no `--yes`, or a `--package` name outside `agentbundle` and `credbroker` | 2 — `malformed` |
  | any | `--package` was supplied with a recognised name | 3 — `cannot-answer` |
  | any | the source could not be resolved or its integrity could not be verified | 3 — `cannot-answer` |
  | apply or `--dry-run` | a `--pack` or `--profile` name the resolved source does not ship | 2 — `malformed` |
  | apply or `--dry-run` | a recorded selection field is present and invalid per AC-0068, or the recipe carries no derivable selection at all, read before any name a scoping flag introduces is unioned in | 3 — `cannot-answer` |
  | apply, `--dry-run`, or `--check --compare-tree` | the recorded-path container is not an array | 3 — `cannot-answer` |
  | apply or `--dry-run` | the identity leak check reported a violation | 1 — `difference` |
  | apply or `--dry-run` | a selected pack's adapter-contract major differs from the CLI's | 1 — `difference` |
  | apply | the write set's paths hold more on disk than AC-0076's bound | 3 — `cannot-answer` |
  | apply | the run could not read the pre-write state of a path it was about to write | 3 — `cannot-answer` |
  | apply | a companion destination collides with a path the replay plans | 3 — `cannot-answer` |
  | apply | there is no terminal to prompt on and no `--yes` was supplied, so consent cannot be taken | 1 — `difference` |
  | apply | the operator reached the consent prompt and did not give consent | 1 — `difference` |
  | apply | a planned write failed and the tree could not be fully restored | 4 — `apply-failed` |
  | apply | a planned write failed and the tree was restored | 4 — `apply-failed` |
  | apply | every planned write landed and stale removal failed | 4 — `apply-failed` |
  | apply | every planned write landed and the ownership state could not be written | 4 — `apply-failed` |
  | apply | every planned write landed, stale removal completed, the state was written, and `companion_occupied` is non-zero | 1 — `difference` |
  | apply | every planned write landed, stale removal completed, the state was written, and `companion_occupied` is zero | 0 — `success` |
  | `--dry-run` | a plan was printed, whatever its counts | 0 — `success` |
  | `--check`, no `--compare-tree` | the resolved source affords no verified digest | 3 — `cannot-answer` |
  | `--check`, no `--compare-tree` | the recorded `archive_sha256` is absent, or is not a 64-character lowercase hex string | 3 — `cannot-answer` |
  | `--check`, no `--compare-tree` | the recorded digest equals the resolved source's verified digest | 0 — `success` |
  | `--check`, no `--compare-tree` | the recorded digest differs from it | 1 — `difference` |
  | `--check --compare-tree` | the recorded path set is empty, or any recorded path could not be compared | 3 — `cannot-answer` |
  | `--check --compare-tree` | every recorded path was compared and none differs | 0 — `success` |
  | `--check --compare-tree` | every recorded path was compared and some differ | 1 — `difference` |

  The `--package` row sits above source resolution so a run that will refuse
  performs no fetch. The unshipped-name row sits below it because whether the
  source ships a name is not decidable until the source resolves. Every apply
  refusal that lands before the prompt sits above the consent row, because
  "consent was not given" is otherwise true of a run that never reached the
  prompt and would shadow the row its own criterion names.
- [ ] **AC-0040.** Every invocation and every failure reaches a named row of
  AC-0039's table at the command boundary. No uncaught exception sets the
  process exit status.
- [ ] **AC-0041.** The walk this criterion compares is non-dereferencing and
  covers relative path, entry kind, mode, symlink target and bytes. It is taken
  immediately before the command runs and immediately after it returns.

  **The source.** The walk is identical across those two moments on every row of
  AC-0039's table, for the one source form that has a tree at both of them:

  | Source form | Source subject |
  | --- | --- |
  | local clone path | the adopter's directory at that path |
  | `git+https://` | none — the clone is created under a fresh temporary directory after the before-walk and lies wholly outside the adopter's tree, so no adopter-owned path is reachable at either moment |
  | `archive+https://` or `catalogue+https://` | none — phase 2's § Always do requires the extracted directory be deleted, and it too lies outside the adopter's tree |

  **The target.** The walk is identical across those two moments on every row of
  AC-0039's table except the four below, each of which may differ only as
  stated. Every other apply row leaves the tree identical. Both `1 — difference`
  consent rows and every `3` refusal do so by never reaching the write phase;
  the `4` row where a planned write failed and the tree **was** restored does
  so by restore, which AC-0038 is what obliges:

  | Row | Permitted difference in the target tree |
  | --- | --- |
  | an apply run whose planned writes all landed — the `0 — success` row, and the `1 — difference` row where `companion_occupied` is non-zero | the paths AC-0033 defines, and the paths stale removal removed |
  | `4` a planned write failed and the tree could not be fully restored | the paths AC-0058 names, and no others |
  | `4` writes landed and stale removal failed | the paths AC-0033 defines less its clause 6 ownership state, and the paths removal had removed before it failed |
  | `4` writes landed and the state write failed | the paths AC-0033 defines less its clause 6 ownership state, and the paths stale removal removed |

- [ ] **AC-0042.** With none of `--pack`, `--profile`, `--guides`, or
  `--package` supplied, AC-0033 clause 1's effective selection is exactly the
  recorded recipe and clause 4 excludes nothing.
- [ ] **AC-0043.** The scope AC-0033 clause 4 excludes against is the union of
  the subtrees the supplied scoping flags name: `packs/<name>/` for each
  `--pack <name>`, `profiles/<name>.toml` for `--profile <name>`, and
  `guides/_shared/` for `--guides`. With no scoping flag supplied the scope is
  every path, so clause 4 excludes nothing. The same scope restricts the plan a
  `--dry-run` prints, so a preview and the apply it previews name the same
  paths. *Scoping flag* means `--pack`, `--profile` or `--guides`; `--package`
  is a reserved selector, not a scoping flag, and AC-0047 governs it.
- [ ] **AC-0044.** A run supplying a scoping flag leaves every recorded
  identity field at its pre-run value. The derivation-wide *paths* are AC-0033
  clause 4's scope exclusion, which contains no derivation-wide path; this
  criterion covers the recorded fields, which no clause of that definition
  reaches.
- [ ] **AC-0045.** A `--pack` or `--profile` name absent from the recorded
  recipe enters the effective selection at AC-0033 clause 1, so clause 3 admits
  its planned paths, and the ownership state records the name in the recipe's
  matching list with that list's existing entries left in place.
- [ ] **AC-0046.** A `--pack` or `--profile` name the resolved source does not
  ship refuses as malformed, naming the field, and writes nothing.
- [ ] **AC-0047.** `--package` accepts exactly the names `agentbundle` and
  `credbroker`. Either one refuses the invocation it appears on — apply,
  `--dry-run` or `--check` alike — naming that package sync is not available.
  The code is AC-0039's first matching row, which is the cannot-answer row
  unless the invocation is also malformed. A `--dry-run` or `--check`
  invocation writes no path under either subtree; on an apply run AC-0033
  clause 5 is what excludes them.
- [ ] **AC-0048.** Two apply runs with identical flags, over target trees whose
  recorded `attribution`, `tooling`, and `guides` differ, write the same bytes
  to the same paths.
- [ ] **AC-0049.** The consent prompt is an output surface for phase 2's terminal-safe scalar criterion:
  every value the command renders on it that it did not itself author passes the
  bounded terminal-safe scalar check first, and a value that fails is reported
  by field name and reason, without the value.
- [ ] **AC-0050.** The consent prompt is an output surface for phase 2's source-disclosure criterion:
  outside `--attribution attributed`, the source URI does not appear on it, on
  any row of AC-0039's table.
- [ ] **AC-0051.** When the identity leak check reports a violation, no path
  under the target tree is created, modified, moved, removed, or has its mode
  changed, and the operator is not prompted for consent.
- [ ] **AC-0052.** Every write the apply path performs under the target tree
  goes through the jailed write primitive, and a planned path resolving outside
  the target root is refused at that write.
- [ ] **AC-0053.** `docs/architecture/catalogue/upstream-sync.md` banner and
  § Rollout both state that one phase remains.
- [ ] **AC-0054.** `guides/_shared/how-to/create-a-self-hosted-catalogue.md`
  carries a section covering the apply run, how consent is given, the scoping
  flags, what an `.upstream.<ext>` companion obliges the adopter to do, and
  that a file upstream added to an already-recorded pack is reported but not
  written, because it is absent from the recorded state —
  present in the authored source and in the projected copy, with both site gates
  passing.
- [ ] **AC-0055.** Every release surface the plan's § Grounding release-surface
  derivation reports states the version `0.49.0`. That derivation supplies the
  closed set this criterion quantifies over.
- [ ] **AC-0056.** An apply run against a real derived tree, edited at one
  recorded path, exits 0; the companion for that path is present beside it
  carrying the source bytes; the adopter's file's digest is unchanged; and no
  path outside the printed plan is altered. The verification ledger records that
  comparison, not only the observed output.
- [ ] **AC-0057.** The plan an apply run prints has two parts, and they are
  distinguished on the page.

  Its **acted rows** name every path AC-0033 clauses 1 to 5 admit, each under
  the verdict clause 2 gave it, together with every path stale removal will
  remove. They do not name AC-0033 clause 6's ownership state. These are the
  rows the run consents against and acts on, and the set AC-0033 compares
  against.

  Its **reported entries** name what the run declined to act on and why — an
  occupied companion destination per AC-0070, a colliding companion pair per
  AC-0071, an out-of-coverage recorded path per AC-0069, and the paths deferred
  per AC-0066. They are not acted rows and are never counted as such. Every
  entry another criterion requires on this plan is one of these kinds; a
  criterion adding a fifth amends this one.

  On a run that refuses before its first write, the acted-rows part is empty
  and the reported entries carry the refusal's own paths.
- [ ] **AC-0058.** When a restore cannot return the tree to its pre-run walk
  tuple, the command names every path it could not restore before returning.
- [ ] **AC-0059.** The ownership state's recorded path set after an apply run
  equals the pre-run recorded set, less the paths stale removal removed, plus
  the paths the run wrote. A path the run classified Tier-3 is absent from it,
  and a companion path is absent from it.
- [ ] **AC-0060.** The `sync` subparser resolves no abbreviated option name:
  `--guides` is the scoping flag, and `--guides-mode` must be supplied in full.
- [ ] **AC-0061.** Every code citation in each architecture file this delivery
  edits resolves to the construct it names.
- [ ] **AC-0062.** `upstream-sync.md` § Stage 3 states that `sync` classifies
  where `init` overwrites, does not state that `init`'s overwrite is replaced,
  and records the one exception to its Tier-3 row: a path is written despite
  being absent from the recorded state when it belongs to a pack or profile the
  run introduces, which is what § Granularity's "`--pack <new-name>` both syncs
  that pack and amends the recipe" requires.
- [ ] **AC-0063.** `upstream-sync.md` § Granularity names
  `.agentbundle/tooling/agentbundle/` and `packages/credbroker/` as the two
  `--package` destinations, and § Rollout item 4 neither describes both as
  `packages/` subtrees nor scopes phase 4 to those two destinations alone: it
  records that phase 4 owns the whole `.agentbundle/tooling/` root, including
  the vendored `packs/catalogue-curation/` copy. The engine and the curation
  pack are installed as a pair, so they move as a pair; scoping phase 4 to
  `agentbundle/` alone would leave that copy written by no verb while this
  phase reports it as deferred.
- [ ] **AC-0064.** No invocation removes a recorded path outside the coverage
  AC-0069 fixes. This holds when the source has stopped shipping that path, so
  the keep-set no longer protects it: coverage, not the keep-set, is what makes
  the protection absolute.
- [ ] **AC-0065.** Every read or hash of a target path the apply path performs
  goes through the confinement helpers phase 2's path-confinement criterion names, and is refused on
  the same hard-link, non-regular and reparse-point inputs that criterion fixes.
- [ ] **AC-0066.** An apply run reports the number of paths AC-0033 clause 5
  excluded under the name `deferred_package`, in the printed table and in the
  `--format json` document's `summary` object. The seven counts phase 2 fixes stay computed over the
  full replayed selection and keep their meanings, so an excluded path is
  counted there exactly as phase 2 counts it and phase 2's
  `compared + uncompared` identity is unchanged.
- [ ] **AC-0067.** `docs/architecture/catalogue/upstream-sync.md` records phase
  3 as the delivered phase.
- [ ] **AC-0068.** AC-0033 clause 1's effective selection never resolves to
  contents the recorded recipe did not name. The domain this quantifies over is
  the recorded value's **type and validity**, because that is what the
  resolution branches on: a recorded selection is admitted only when it is a
  list every one of whose entries is a name the source ships. The rule is per
  selection field — `packs` and `profiles` each decide separately:

  - A **valid** list narrows that category to the names it carries.
  - An **absent field or an empty list** selects nothing from that category.
    Both are the narrowing outcome, not the widening one, and AC-0069 bounds
    what an empty category can cost: it puts no path in that category inside
    coverage, so nothing there becomes a removal candidate.

    The state writer records the **resolved** lists, not the flags: an `init`
    that omits `--profile` records every profile the source ships, because the
    selector widens a falsy argument. § Grounding's recorded-shape derivation
    shows an empty list is what `init` writes when the source ships no such
    directory at all — so it is producible, and refusing it would refuse a
    real tree, but it does not mean "the adopter selected none".
  - A **present but invalid** value — a null, a string, a number, a boolean, an
    object, a list of non-strings, or a list carrying one name the source does
    not ship — refuses the run, naming that field. The code is AC-0039's first
    matching row, which owns every code this command returns.

  No value resolves to every pack or profile the source ships.

  Quantifying over presence and emptiness instead is what hides the sharp case:
  a recorded selection that fails its own read-time constraint reads as a
  well-formed non-empty list, and the shipped resolution collapses it to "no
  narrowing requested". § Grounding's widening derivation measures the figure
  over both selection fields, since `profiles` carries the identical widening
  and a packs-only sweep prices it as covered.
- [ ] **AC-0069.** A recorded path is a removal candidate only when it lies
  inside the run's **coverage**: the set of path prefixes this run could have
  planned, given its own flags and defaults and the effective selection AC-0033
  clause 1 resolved. Coverage is that positive set, narrowed by the exclusions
  below — it is not the exclusions themselves, because a coverage defined only
  by what it excludes re-admits every axis nobody enumerated.

  On the selection axis, coverage holds `packs/<name>/` for each pack in the
  effective selection and `profiles/<name>.toml` for each profile, and nothing
  else under either prefix. An effective selection that is empty for a category
  therefore puts no path in that category inside coverage, which is what stops
  a recorded `packs` list of `[]` making the whole recorded pack tree a removal
  candidate — the keep-set cannot protect those paths, because a run that
  selected no packs replays none of them.

  Coverage reads the recorded recipe's selection, which is what a recipe is
  for. It never reads a recorded **mode** — `attribution`, `tooling` or
  `guides` — which is the rule phase 2 fixes and AC-0048 carries. The
  exclusions:

  1. `packages/credbroker/` and `.agentbundle/tooling/`, on every invocation and
     in every mode. These are the subtrees AC-0033 clause 5 keeps out of the
     write set, and a run that may not write a subtree may not delete from it
     either.
  2. `guides/` under `--guides-mode none` — the mode-narrowing axis. The
     tooling half of that axis is already absolute under clause 1, so this
     clause carries the guides case, which no subtree list reaches: § Grounding
     measures 47 recorded `guides/` paths orphaned by a `--guides-mode none`
     run over a default-derived tree.
  3. Everything outside the scope AC-0043 fixes.

  Coverage membership is decided against the confined, resolved path the
  removal would act on, by a comparison that holds for every spelling naming
  the same path on the platforms this command supports — not by a
  case-sensitive string prefix. Two spellings defeat a textual test: a
  traversal such as `.agentbundle/tooling/../tooling/agentbundle/x`, and, on a
  case-insensitive filesystem, `.agentbundle/Tooling/agentbundle/x`, which
  resolves to the protected file while a prefix comparison misses.

  A recorded path outside coverage is left in place and reported as an
  `out_of_coverage` count, on the printed plan and in the `--format json`
  document's `summary` object.

  This criterion exists because the replayed set is mode-dependent while the
  recorded set is not. A tree derived with `--tooling vendored` records every
  path under `.agentbundle/tooling/`, and `sync` defaults `--tooling` to
  `external`, so without this criterion a bare `catalogue sync --source <uri> .`
  finds all of them absent from its replayed set and the sha guard admits each
  unedited one. § Grounding's mode-asymmetry derivation measures that at 240
  paths. Naming those subtrees as exclusions would repair the measured instance
  and leave the class, which is any mode whose replay plans more paths than the
  running mode's.
- [ ] **AC-0070.** A companion destination that already exists is never
  written. The run leaves the occupant byte-identical, is the condition AC-0033
  clause 3 reads when it declines to admit that companion, and names it on the
  plan the operator consents against and in the
  `--format json` document's `summary` object under `companion_occupied`.
  Nothing records what a previous run wrote to a companion destination — AC-0059
  keeps companion paths out of the recorded state — so no rule that asks whether
  an occupant is the command's own output is decidable from what the run holds.
  Never overwriting is the fail-safe reading, and it is what stops an adopter
  part-way through resolving a companion losing that work.

  A companion write cannot replace an existing destination — there is no
  interval in which an occupant can appear and be overwritten. Stating this as
  a check performed at some moment would not close it: the repository's atomic
  write finishes with a rename that clobbers unconditionally and reports
  nothing, so a stat before that rename leaves exactly the window an adopter's
  editor writes into. The obligation is on the write's outcome, not on a check
  preceding it, and a write that finds its destination occupied fails, taking
  AC-0039's write-failed row.
- [ ] **AC-0071.** When the replayed source itself plans a path equal to a
  companion destination this run would compute, the run refuses before its
  first write, naming both paths under `companion_collision` on the plan and in
  the `--format json` document's `summary` object. The code is AC-0039's first
  matching row, which owns every code this command returns. The refusal is whole-run
  rather than a per-path carve-out: a partial admission would return the
  cannot-answer code over a tree AC-0041 requires to be unchanged. Letting the
  set collapse the duplicate instead would leave AC-0032's order deciding which
  content wins.
- [ ] **AC-0072.** Every apply run names the source fidelity, including whose
  word a digest rests on, on the consent prompt when it prompts and in the
  printed plan and the `--format json` document on every apply run including
  `--yes`. Scoping it to the prompt alone would put it exactly where a human is
  already reading and leave it absent from every automated path. Fidelity is what separates a `git+https://` sync —
  TLS only, no content integrity, a force-pushable ref — from a digest-verified
  one, and on this verb it is the basis on which an operator authorises writes
  rather than reads.
- [ ] **AC-0073.** Every removal the apply path performs resolves its path
  through the same confinement the removal planner applies, at the moment of the
  unlink rather than only when the path was planned. AC-0065 covers reads and
  hashes and AC-0052 covers writes; without this the delete is the one action on
  a target path bound by neither.

- [ ] **AC-0074.** The `sync` subcommand's help text does not state that the
  command is read-only or writes nothing.
- [ ] **AC-0075.** `upstream-sync.md` § Rollout no longer states that a source
  form affording a resolved ref or a digest first reaches the pin when `sync`
  resolves it in phase 2. Phase 2 shipped with no write path and wrote no pin;
  AC-0037 assigns that value to this phase.
- [ ] **AC-0076.** The rollback snapshot is bounded on the adopter tree the run
  reads, not on the source it replays. Before the consent prompt and before the
  first write, the run sums `st_size` over every write-set path that exists; if
  that sum exceeds 256 MiB it refuses, naming the bound and the measured sum.
  The bound also holds over the bytes already read at every point during
  snapshot construction, not only over the finished total. The pre-prompt sum
  is taken before an unbounded wait at the prompt, during which another writer
  can grow a write-set file; a bound checked only against the running total
  still reads one grown path in full before it can trip.

  The figure is a **chosen ceiling, not a measurement**. No adopter-axis
  measurement exists: § Grounding measures the source tree, and an adopter file
  at a planned path is unbounded, so nothing here establishes the headroom a
  256 MiB resident snapshot leaves beside the replay's own bytes. The ceiling is
  set where a tree an order of magnitude past anything this repository produces
  still refuses rather than risks the partial-restore row. `st_size` is named
  because the alternative, allocated blocks, makes the bound unreachable for a
  sparse fixture and forces a quarter-gigabyte write into a unit suite.

## Follow-ons

- **Package sync** — writing both `--package` subtrees. Owner: phase 4 of
  [`upstream-sync.md`](../../architecture/catalogue/upstream-sync.md) § Rollout.
- **`--check --compare-tree` resolves a source it does not read** — phase 2
  recorded three routes and left the choice to the owner; this phase does not
  take it (owner confirmation 2026-09-22). Owner: unassigned.
- **A read-time constraint on the recorded mode fields and the pin** — carried
  forward from phase 2, and its consequence changed here. AC-0048 pins the
  replay's modes to flags and defaults, so a bare apply over a tree recorded
  `attribution = "attributed"` replays white-label bytes, which classify Tier-1
  against the recorded digests and are written in place across every recorded
  path. AC-0069's coverage rule bounds what such a run may remove but not what
  it may rewrite. Owner: unassigned.
- **A scanner rule for unbounded rendered values** — no rule detects a value
  reaching stdout without the terminal-safe check, so AC-0049's class is
  enforced by review. Owner: unassigned.
- **A ceiling on the recorded path set and the total bytes hashed** — carried
  forward from phase 2 unchanged, and now reached on a writing verb rather than
  a read-only one. Owner: unassigned.
- **A discriminator for the conditions sharing exit 1** — phase 2 left the
  field's shape and which rows carry it to the owner. This phase adds three
  more rows to that code, and one of them is not a refusal at all: a completed
  run with a non-zero `companion_occupied` returns 1 over a tree it fully
  rewrote, while the two consent rows return 1 over a tree AC-0041 requires to
  be identical. A caller reading only the exit code cannot tell whether the
  tree was modified, so retrying a run it believes wrote nothing re-enters the
  write path over a mutated tree. Owner: unassigned.

## Assumptions

- Product: whether an adopter wants a scoped apply to refresh the pin at all,
  given the pin then describes a tree only partly at that source — this phase
  records it on every successful apply, scoped or not (settled by: the owner,
  after the first real scoped run).
