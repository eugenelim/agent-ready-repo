# Spec: catalogue sync — package sync for both `--package` destinations

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0059 (the catalogue-curation pack, which owns the white-label export boundary)
- **Brief:** none
- **Discovery:** none
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

## What this spec supersedes

Phase 3's [`catalogue-sync-apply`](../catalogue-sync-apply/spec.md) is Shipped
and frozen. This phase supersedes the criteria of it named at each replacing
criterion below, and retires one of its § Never do rules. The count is
deliberately not stated here: a numeral in this paragraph decays the first time
a criterion is added or split, and the replacing criteria are the only place the
supersession can be read without decaying. Each supersession is named at the
criterion that replaces it,
in the form phase 3 used when it replaced phase 2's no-write-path rule. Nothing
here edits that spec; a reader who arrives at a superseded criterion finds it
still stated there, and finds its replacement by this spec's identifier.

The retired § Never do rule is phase 3's *"Never write under
`packages/credbroker/` or `.agentbundle/tooling/`, whether or not `--package`
was supplied."* It was the boundary that held this phase open. AC-0078 and
AC-0079 replace it.

Every other rule phase 3 states still binds, including the whole of phase 2's
§ Boundaries that phase 3 carries forward by pointer.

## Outcome

An adopter whose derived tree carries a vendored engine or a credbroker source
takes upstream changes to those subtrees with the same `agentbundle catalogue
sync` run that already updates their packs, profiles and guides. Success is
that the package subtrees move with the rest of the tree, apply after every
other write, and that a run which would overwrite the `agentbundle` supplying
the running command refuses before it writes anything.

## What Changes

- The four seam points holding package sync open are gone —
  `_DEFERRED_PACKAGE_PREFIXES`, `_is_deferred_package_path`, the write-set
  selector's deferral branch, and `run()`'s `--package` refusal — all in
  `packages/agentbundle/agentbundle/commands/catalogue_sync.py`.
- `--package` becomes a fourth scoping flag rather than a reserved selector —
  `cli.py`'s help text and `catalogue_sync.py`'s scope machinery.
- A fifth write-order group, below the derivation-wide paths —
  `catalogue_sync._write_group`.
- A self-replacement refusal reusing the editable-install detector —
  `catalogue_sync.run()`, calling `source_defaults._detect_editable_source`.
- The `deferred_package` count leaves the printed plan and the `--format json`
  summary; a `tree_modified` field joins both.
- The package subtrees leave AC-0069's coverage exclusion list, so a recorded
  path under either one becomes a removal candidate.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Applicable — this delivers the last phase of that rollout, and § Granularity's destination for `agentbundle` contradicts both § Rollout item 4 and the shipped code | [`docs/architecture/catalogue/upstream-sync.md`](../../architecture/catalogue/upstream-sync.md) | eugenelim | § Granularity names `.agentbundle/tooling/` as the whole destination; § Rollout records every phase delivered and the rollout closed; § Known risks records which half of the self-replacement mitigation the refusal covers | AC-0092, AC-0093, AC-0094 and AC-0095 pass |
| User-facing promise | Applicable — the package subtrees are a thing an adopter must decide about, and this guide is projected into the docs site | `guides/_shared/how-to/create-a-self-hosted-catalogue.md` | eugenelim | A section covering `--package`, the two destinations and their presence conditions, and what the self-replacement refusal means for a vendored adopter | AC-0096 passes, including its projected-surface half |
| Interface compatibility | Applicable — the PyPI readme is a pinned release surface and `--package` changes meaning | `packages/agentbundle/README-pypi.md` | eugenelim | A "What's new in" section naming the version AC-0097 fixes | AC-0097 and AC-0098 pass |
| Release history | Applicable — a flag changing from refusal to function is a release-coupling trigger | [`packages/agentbundle/CHANGELOG.md`](../../../packages/agentbundle/CHANGELOG.md), [`docs/product/changelog.md`](../../product/changelog.md) | eugenelim | A topmost entry naming the version AC-0097 fixes, written adopter-first | AC-0097 and AC-0098 pass |
| Decision rationale | Not applicable — the four decisions this phase makes are recorded as criteria here and as design in the plan; none changes a repository-wide rule | — | — | — | — |
| Maintainer procedure | Not applicable — no runbook governs this command | — | — | — | — |

## Agent Rules

### Always do

- Phase 3's § Always do and § Never do carry forward in full, and with them
  phase 2's § Boundaries that phase 3 points at. Re-typing either list here
  would create a third home that degrades at the moment of writing. Phase 3's
  rule against writing a path the printed plan did not name carries forward by
  that pointer and now reaches the package extent.
- The deltas this phase adds:
  - Decide containment for the package extent by the identity-based resolved
    path comparison AC-0069 already requires for coverage, never by a string
    prefix.
  - Take AC-0083 input 1 from `_detect_editable_source`, and take input 2 from
    the running package's own resolved location. Decide both before the run
    resolves its source.

### Ask first

- Before adding a flag beyond the five phase 3 declares and the one this phase
  repurposes.
- Before introducing a sixth exit code, or changing a row of AC-0085's table.
- Before changing what `init` writes, aborts on, or removes.
- Before widening the self-replacement refusal past the vendored `agentbundle`
  extent.

### Never do

- Never write a second detector for AC-0083 input 1.
  `agentbundle/source_defaults.py:341` is the one, and reusing it is a
  condition of this phase, not a preference. AC-0083 input 2 is a separate
  named input, not a second detector for input 1.
- Never add a third self-replacement input beyond AC-0083's two.
- Never add a module, package, or top-level directory: the write extent this
  phase adds lives in the one command module the CLI's lazy-dispatch convention
  already allocates.
- Never add a third-party dependency.
- Never offer a flag, environment variable, or recorded value that overrides
  the self-replacement refusal.
- Never read the tooling mode from recorded state to decide whether the
  `agentbundle` extent is present.

## Testing Strategy

Three modes, over twenty-three criteria.

**TDD** covers AC-0078 through AC-0090 — the criteria whose oracle is a set
comparison, an exit code, or a field's presence and value. Each names the
comparison its oracle performs, not the property it hopes to establish.

- **The package write extent (AC-0078)** — TDD. Oracle: the set of paths a
  replay places under either destination, compared for equality in both
  directions against the paths `init` writes there for the same source, modes
  and selection.
- **Admission (AC-0079)** — TDD. Oracle: the write set of an apply run over a
  vendored fixture, compared against the same run's write set with the package
  paths removed; the difference is exactly the package extent.
- **Write order (AC-0080)** — TDD. Oracle: the index of every package path in
  the observed write sequence, compared against the maximum index of every
  non-package path. The ownership state's index is compared against both.
- **`--package` as a scoping flag (AC-0081)** — TDD. Oracle: the write set of
  `--package credbroker`, compared for equality against the recorded recipe's
  `packages/credbroker/` paths alone.
- **The absent-extent refusal (AC-0082)** — TDD. Oracle: the exit code of
  `--package agentbundle` without `--tooling vendored`, compared against 2, with
  a monkeypatched resolver asserting no fetch ran.
- **The self-replacement refusal (AC-0083, AC-0084)** — TDD at the unit level,
  driven once per AC-0083 input and once with neither holding: input 1 with
  `_detect_editable_source` monkeypatched to return the target root, input 2
  with the running package's resolved location pointed inside a target's
  AC-0078 engine subtree, including a target carrying no `.git`. Plus
  an integration test that pip-installs editable into a temporary venv and
  drives the real detector, in the shape
  `tests/integration/test_editable_source_detection.py` already uses. The unit
  oracle is the exit code and the post-run walk tuple of the target tree; the
  integration oracle is the exit code alone. **No test ever writes to the
  running interpreter's own install root**, whatever it asserts.
- **Exit codes and totality (AC-0085)** — TDD. Oracle: every row of the table,
  driven at the command boundary, compared against the code the row names, plus
  a sweep asserting no input produces a code outside the five.
- **Removal coverage (AC-0086)** — TDD. Oracle: the removal set over a recorded
  state carrying a package path the source has stopped shipping, compared
  against that path's membership.
- **Identity-based containment (AC-0087)** — TDD. Oracle: the admission and
  coverage decisions for a traversal spelling and, where the filesystem is
  case-insensitive, a case-variant spelling, each compared against the decision
  for the canonical spelling. Skipped with a named reason where the platform
  affords no case-insensitive mount.
- **The retired count (AC-0088)** — TDD. Oracle: the key set of the
  `--format json` document's `summary` object and the tokens of the printed
  counts line, each compared against a fixed expected set.
- **`tree_modified` (AC-0089)** — TDD. Oracle: the field's value on every row
  of AC-0085's table an apply run can take that produces a plan or a JSON
  document — the five sharing exit 1, the four code-4 rows, and the success
  row — compared against a pre-run and post-run walk of the target tree. A
  separate case asserts the field appears nowhere on the rows AC-0091 says
  print no plan.
- **Rollback over a package write (AC-0090)** — TDD. Oracle: the post-run walk
  tuple of the whole target tree after a forced package-write failure, compared
  for equality against the pre-run walk.

**Goal-based checks** cover AC-0091 through AC-0098 — each is a documented
surface or a printed-plan accounting whose oracle is a `grep`, a rendered-site
build, or the release-surface derivation, not a behavior.

**Visual / manual QA** covers AC-0099 and AC-0100, which no automated oracle
reaches: a real
`agentbundle catalogue sync --tooling vendored --package agentbundle` against a
constructed vendored fixture, driven end to end, with the printed plan, the
consent prompt, the exit code and the post-run tree recorded. This exists
because the printed plan is a surface a person reads, and no unit assertion
observes whether a reader can tell what the run is about to do to their engine.

**One environment fact bounds every mode above.** This repository self-hosts in
*external* tooling mode: `.agentbundle/tooling/` is empty here. Every check over
the `agentbundle` extent runs against a constructed vendored fixture, and none
of them runs against this tree.

## Acceptance Criteria

- [ ] **AC-0078.** **The package write extent is defined here and nowhere
  else.** The extent is two destinations, and the `agentbundle` destination has
  one named part:

  | `--package` name | Destination | Present when |
  | --- | --- | --- |
  | `agentbundle` | `.agentbundle/tooling/` — the whole root. Its **engine subtree** is `.agentbundle/tooling/agentbundle/`; the rest is the vendored `packs/catalogue-curation/` copy | the run replays `--tooling vendored` |
  | `credbroker` | `packages/credbroker/` | the effective selection carries the `credential-brokers` pack, in either tooling mode |

  The `agentbundle` destination is the whole vendored tooling root because
  `init` writes both subtrees under it from one mode decision, so a phase that
  moved only the engine subtree would leave the vendored `catalogue-curation`
  copy written by no verb. The engine subtree is named because AC-0083 input 2
  tests it alone: the running engine can only be supplied from there.

  The two rows read their presence from different places, and the difference is
  load-bearing. The `agentbundle` row is decided from the run's own `--tooling`
  flag and its default, never from recorded state. The `credbroker` row is
  decided from AC-0033 clause 1's effective selection, which does read the
  recorded recipe — that is what clause 1 is — and phase 2's rule against
  recorded values selecting a mode does not reach it, because a selection is
  not a mode.

- [ ] **AC-0079.** A path under either AC-0078 destination is admitted to the
  write set on the same terms as any other replayed path. **This supersedes
  AC-0033 clause 5**, which excluded them, and with it phase 3's § Never do
  rule against writing under either subtree. AC-0033 clauses 1, 2, 3, 4 and 6
  are unchanged and still govern.

- [ ] **AC-0080.** The paths AC-0079 admits are written in the order packs,
  profiles, guides, the derivation-wide paths, then the AC-0078 destinations,
  and AC-0033 clause 6's ownership state after all five. **This supersedes
  AC-0032**, which named four groups ending at the derivation-wide paths.
  Packages are last because a failed package write is the one whose rollback
  may be executing from the code it just replaced, so every other write is
  already durable before one is attempted.

- [ ] **AC-0081.** `--package <name>` restricts the run to that name's AC-0078
  destination, joining `--pack`, `--profile` and `--guides` in the scope union
  AC-0043 fixes. **This supersedes AC-0047 entirely, supersedes AC-0043's
  closing sentence** naming `--package` a reserved selector, **and supersedes
  AC-0030's malformed enumeration** of which flags are malformed with
  `--check`: that enumeration is now all four scoping flags, `--package`
  included. Absent every scoping flag, the scope is every path, so an apply
  run writes each AC-0078 destination its replay produces.

  `--pack <name>` never reaches a path under an AC-0078 destination. The
  vendored `packs/catalogue-curation/` copy is inside the `agentbundle`
  destination and moves only under `--package agentbundle`, never under
  `--pack catalogue-curation`, which reaches `packs/catalogue-curation/` at the
  tree root alone.

- [ ] **AC-0082.** A `--package <name>` run whose named AC-0078 destination is
  not present refuses as malformed, naming the flag and the presence condition
  it failed. This covers `--package agentbundle` on a
  run not replaying `--tooling vendored`, and `--package credbroker` on a run
  whose effective selection does not carry the `credential-brokers` pack. A
  run that reported success would refresh the pin over a subtree it never
  wrote, and neither the parser's `choices` check nor any later row catches it.

- [ ] **AC-0083.** An apply or `--dry-run` invocation whose **effective scope
  includes** the AC-0078 `agentbundle` destination — a run replaying `--tooling vendored`
  under either no scoping flag or `--package agentbundle` — refuses when the
  target supplies the running `agentbundle`, naming that it does. The trigger
  is the run's scope, not its write set: a write set requires a resolved
  source. AC-0084 is the single home for when both refusals are decided.

  A `--check` run is not covered, which narrows phase 3's AC-0047. `--check`
  writes nothing on any row of AC-0085's table, so it cannot replace the
  running engine and has nothing to refuse.

  It refuses when **either** input holds:

  1. `_detect_editable_source` resolves a catalogue root that is the target
     root. This catches an adopter running the target's own source checkout.
  2. The running `agentbundle` package's own file resolves inside the target's
     AC-0078 engine subtree. This catches an adopter who installed the vendored
     copy editable, and it holds whether or not the target is a git repository.

  Two inputs, because input 1 alone fails open on the sharper case:
  `_detect_editable_source` is bounded by an enclosing git repository
  (`agentbundle/source_defaults.py:394-401`) and returns nothing for a derived
  catalogue that is not one, before it reads the catalogue markers at all. A
  derived catalogue need not be a git repository.

  Each input is decided by the AC-0087 comparison. On refusal, no path under
  the target tree is created, modified, moved, removed, or has its mode
  changed, and the operator is not prompted for consent.

- [ ] **AC-0084.** The AC-0082 and AC-0083 refusals are both decided before
  the run resolves its source, so a run that will refuse performs no fetch.
  This is the single home for that obligation; no other criterion restates it.

- [ ] **AC-0085.** The command's exit code is the first matching row of this
  table, read top to bottom, and no input produces a code outside it. **This
  supersedes AC-0039**, and **every phase-3 criterion referring to AC-0039's
  table refers to this table instead** — AC-0040, AC-0041, AC-0064, AC-0071,
  AC-0076 and AC-0077 among them. Three rows change and the rest are carried
  unchanged: the `--package`-refuses row is retired, an absent-extent row joins
  the malformed group, and a self-replacement row joins the cannot-answer
  group.

  | Invocation | Condition | Code and name |
  | --- | --- | --- |
  | any | the invocation is malformed, including an omitted `--source`, both of `--dry-run` and `--check`, `--compare-tree` without `--check`, `--yes` outside an apply run, a scoping flag with `--check`, an apply run with `--format json` and no `--yes`, or a `--package` name outside `agentbundle` and `credbroker` | 2 — `malformed` |
  | any | `--package agentbundle` on a run not replaying `--tooling vendored`, per AC-0082 | 2 — `malformed` |
  | apply or `--dry-run` | the run's effective scope includes the `agentbundle` destination and the target supplies the running `agentbundle`, per AC-0083 | 3 — `cannot-answer` |
  | any | the source could not be resolved or its integrity could not be verified | 3 — `cannot-answer` |
  | apply or `--dry-run` | a `--pack` or `--profile` name the resolved source does not ship | 2 — `malformed` |
  | apply or `--dry-run` | a recorded selection field is present and invalid per AC-0068, or the recipe carries no derivable selection at all, read before any name a scoping flag introduces is unioned in | 3 — `cannot-answer` |
  | any | `--package credbroker` on a run whose effective selection does not carry the `credential-brokers` pack, per AC-0082 | 2 — `malformed` |
  | apply, `--dry-run`, or `--check --compare-tree` | the recorded-path container is not an array | 3 — `cannot-answer` |
  | apply or `--dry-run` | the identity leak check reported a violation | 1 — `difference` |
  | apply or `--dry-run` | a selected pack's adapter-contract major differs from the CLI's | 1 — `difference` |
  | apply | the write set's paths hold more on disk than AC-0076's bound | 3 — `cannot-answer` |
  | apply | the run could not read a write-set path's pre-run state while building the rollback snapshot | 3 — `cannot-answer` |
  | apply | a companion destination collides with a path the replay plans | 3 — `cannot-answer` |
  | apply | there is no terminal to prompt on and no `--yes` was supplied, so consent cannot be taken | 1 — `difference` |
  | apply | the operator reached the consent prompt and did not give consent | 1 — `difference` |
  | apply | consent was taken and AC-0077's gate recheck, over the write-set destinations that carry a classified row, found one that diverged from the state it was classified against or that it could not read, before any write | 3 — `cannot-answer` |
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

  The two new refusal rows sit above source resolution per AC-0084. The
  absent-extent
  rows split by name, and the split is load-bearing. The `agentbundle` half
  reads only `--tooling`, so it sits above source resolution, and above the
  self-replacement row because a run whose destination is not present has no
  scope reaching it. The `credbroker` half reads the effective selection, so it
  sits **below** the AC-0068 selection-validity row: a run whose recorded
  selection is invalid cannot decide whether the `credential-brokers` pack is
  in it, and a row must not demand an answer from an input the table has not
  yet established is readable. Every other row keeps the position and reason
  AC-0039 gave it.

- [ ] **AC-0086.** A recorded path under an AC-0078 destination is inside the
  run's coverage only under that destination's AC-0078 presence condition: a
  path under the `agentbundle` destination only on a run replaying
  `--tooling vendored`, and a path under the `credbroker` destination only when
  the effective selection carries the `credential-brokers` pack. On every other
  run each is outside coverage, left in place, and reported in the
  `out_of_coverage` count. Inside coverage it is a removal candidate on the
  same terms as any other recorded path, and the sha256 guard still governs
  whether it is removed.

  **This supersedes AC-0069's exclusion 1**, which barred both subtrees
  absolutely. The replacement is a positive condition rather than a deletion,
  because AC-0069's coverage decision ends by admitting every path no clause
  excluded: deleting the exclusion alone would put both subtrees inside
  coverage on every run, reinstating the mass removal AC-0069 measures at 240
  paths for a vendored-derived tree met by this command's external default.
  AC-0069's exclusions 2 and 3 are unchanged.

- [ ] **AC-0087.** Whether a path belongs to an AC-0078 destination or to its
  engine subtree is decided by one comparison used for admission, for coverage,
  for write ordering, and for AC-0083's two inputs. It is taken in two parts,
  always in this order: the longest prefix of the path that has an on-disk
  entry is resolved by directory identity, and only the remainder — which has
  no entry — is compared as a normalised relative path with traversal
  components resolved lexically. A path wholly on disk uses the first part
  alone; a path under a destination a run is about to create uses both.

  Deciding the branch on the *path's* own existence rather than its nearest
  existing ancestor's is what this criterion forbids, and the case that forbids
  it is a planned path whose ancestor is an existing symlink into a
  destination: `link/agentbundle/new` where `link` resolves to
  `.agentbundle/tooling`. That path has no entry of its own, so a path-level
  test takes the lexical branch, judges it outside every destination, and
  admits it to the derivation-wide write group — defeating AC-0080 and writing
  inside the destination anyway, which AC-0052's jail does not catch because
  the write lands inside the target root.

  Identity alone is insufficient because it cannot answer for a path that is
  not yet on disk. A lexical comparison alone is insufficient because a
  traversal spelling and, on a case-insensitive filesystem, a case-variant
  spelling both reach a protected entry that a string comparison misses.

- [ ] **AC-0088.** No invocation reports a `deferred_package` count, on the
  printed plan or in the `--format json` document's `summary` object. **This
  supersedes AC-0066.** The seven counts phase 2 fixes stay computed over the
  full replayed selection and keep their meanings, and phase 2's
  `compared + uncompared` identity is unchanged.

- [ ] **AC-0089.** An apply run reports whether it changed the target tree,
  under the name `tree_modified`, in the `--format json` document's `summary`
  object and on the printed plan. It is reported on every row of AC-0085's
  table an apply run can take **that produces one of those two surfaces**. The
  runs AC-0091 names as printing no plan report it nowhere, and neither does a
  malformed row that emits no document: a refusal that never classified
  anything has no tree state to report on, and its exit code already says the
  tree is untouched.

  Its value is the tree's state when the command returns, compared against its
  pre-run walk tuple per AC-0041: true when that comparison differs, false when
  it does not. So a run whose writes all failed and were fully restored reports
  false, and a run whose restore left any path changed reports true. It is an
  end-state report, not a record of actions taken, because a caller reads it to
  decide whether retrying is safe and a fully restored tree is safe to retry.

- [ ] **AC-0090.** When a write to an AC-0078 destination fails, AC-0038's
  restore covers it on the same terms as any other planned write, and
  AC-0085's two code-4 restore rows select between themselves by whether that
  restore succeeded.

- [ ] **AC-0091.** The printed plan's accounting covers this phase's paths and
  refusals. **This supersedes AC-0057's declined-kind list and its no-plan
  enumeration.** The declined kinds are four: an occupied companion
  destination per AC-0070, a colliding companion pair per AC-0071, an
  out-of-coverage recorded path per AC-0069, and a companion destination
  reported under `companion_residue` per AC-0070's third outcome. The deferred
  kind AC-0066 supplied is retired with it, and `companion_residue` is named
  here because AC-0057's list omitted it while AC-0070 requires it be reported
  — a pre-existing gap this criterion closes rather than inherits. The runs
  that print no plan because they
  refuse before classifying anything are AC-0082's, AC-0083's, source
  resolution's, and an invalid recorded selection's. AC-0057's two-part
  structure and its rule that a criterion adding a kind amends it are
  unchanged.

- [ ] **AC-0092.** `docs/architecture/catalogue/upstream-sync.md` § Granularity
  names the `agentbundle` destination as `.agentbundle/tooling/`. **This
  supersedes AC-0063's § Granularity clause**, which required that section to
  name `.agentbundle/tooling/agentbundle/`. AC-0063's § Rollout item 4 clause
  is unchanged and still binds: that section already records the whole
  vendored root, and the two sections disagreeing is what this criterion ends.

- [ ] **AC-0093.** That file's status banner and its § Rollout agree that the
  rollout is closed and no phase remains. **This supersedes AC-0053**, which
  required both to state that one phase remains.

- [ ] **AC-0094.** That file's § Known risks records which extent AC-0083's
  refusal covers and which it does not.

- [ ] **AC-0095.** Every code citation in each architecture file this delivery
  edits resolves to the construct it names. This carries phase 3's AC-0061
  forward, which was scoped to phase 3's delivery and does not travel on its
  own.

- [ ] **AC-0096.** `guides/_shared/how-to/create-a-self-hosted-catalogue.md`
  covers `--package`, both AC-0078 destinations with their presence conditions,
  and what the AC-0083 refusal obliges a vendored adopter to do instead. The
  projected copy on the rendered site carries the same section.

- [ ] **AC-0097.** Every release surface the plan's § Grounding
  release-surface derivation reports states the version `0.50.0`. That
  derivation supplies the closed set this criterion quantifies over.

- [ ] **AC-0098.** Each **prose** release surface that derivation reports —
  the ones carrying adopter-facing text rather than a version literal alone —
  states that `--package` writes its destination rather than refusing. The
  derivation marks which of its surfaces are prose; a surface that carries only
  a version literal cannot state it and is not quantified over here.

- [ ] **AC-0099.** An apply run against a real vendored derived tree, scoped
  `--package agentbundle`, writes exactly the paths its printed plan named and
  no others, compared by a walk of the target tree before and after.

- [ ] **AC-0100.** That same run against a target that supplies the running
  `agentbundle` returns AC-0085's self-replacement row and leaves the
  before-and-after walk identical.

## Follow-ons

- **An editable `credbroker` install rooted at the target** — AC-0083 covers
  the vendored `agentbundle` extent only, on the evidence that
  `packages/credbroker/` is resolved as a build input by
  `user_libs._package_source_dir`, which looks for the package beneath the
  catalogue root rather than treating it as an install source. An adopter who
  ran `pip install -e packages/credbroker/` against the target falls outside
  the refusal, and `_detect_editable_source` would not detect it, because it
  resolves catalogue roots by their `catalogue.toml` and `packs/` markers.
  Owner: unassigned.

- **AC-0076's snapshot bound now spans the package extent** — the 256 MiB
  ceiling was chosen, not measured, and was calibrated while AC-0033 clause 5
  held both package subtrees out of the write set. A vendored engine and a
  vendored pack are now inside it and inside the rollback snapshot. Its
  headroom was not re-derived. Owner: unassigned.

- **Companion delivery on a filesystem carrying no hard links** — carried
  forward from phase 3 unchanged in mechanism, and widened in reach: this phase
  adds a third write extent to the same non-replacing publish path, so a
  vendored adopter on FAT, exFAT or an affected network or FUSE mount now has
  more paths that can take the write-failed row and roll the whole run back.
  Owner: unassigned.

- **`write_files_no_follow` is POSIX-only** — it calls `os.fchmod`, so seven
  tests in `test_safety.py` fail on Windows. Pre-existing, untouched by this
  delivery, and unrelated to package sync. Owner: unassigned.

- **The remaining exit-1 conditions** — AC-0089 discriminates whether the tree
  was modified, which is what a retrying caller needs. It does not discriminate
  the five exit-1 conditions from one another, which is the wider question
  phase 2 opened and phase 3 carried. Owner: unassigned.

## Assumptions

- Product: whether an adopter running a bare vendored apply expects their
  engine to move without naming it. This phase follows § Granularity and writes
  it (settled by: the owner, 2026-09-24), and the AC-0083 refusal is what makes
  that safe for the case where the engine is the running one.
