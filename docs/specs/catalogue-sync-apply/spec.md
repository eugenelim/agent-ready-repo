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
which upstream it now matches. Success is that no run ever leaves a half-applied
tree — every path the plan named is written, or the tree is the one that existed
before the command started.

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
| Current architecture | Applicable — this delivers phase 3 of that rollout; § Rollout item 4 calls both `--package` targets `packages/` subtrees, and only one is | [`docs/architecture/catalogue/upstream-sync.md`](../../architecture/catalogue/upstream-sync.md) | eugenelim | Banner and § Rollout mark phase 3 done and one phase remaining; § Rollout item 4's subtree claim corrected; § Stage 3 says `sync` classifies where `init` overwrites rather than that the overwrite is replaced; § Granularity, which today names no destination for either subtree, gains one | AC-0053, AC-0061, AC-0062 and AC-0063 pass |
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

- Never write, move, delete, or change the mode of a path the printed plan did
  not name.
- Never leave a half-applied tree: a failed write restores the pre-run tree
  before the command returns.
- Never write anything under the target tree when the identity leak check
  reported a violation.
- Never add a module, package, or top-level directory: the apply path extends
  the existing command module.
- Never add a third-party dependency.
- Never bring the state file inside the identity leak check.
- Never let a recorded value select a mode, widen a selection, or resolve as a
  path.
- Never introduce a predictable staging path.
- Never narrow the stale-removal keep-set to a scoped subset.
- Never write under `packages/credbroker/` or `.agentbundle/tooling/agentbundle/`, whether or not `--package` was supplied.

## Testing Strategy

Three modes, over 36 criteria. Each entry names the comparison its oracle
performs, not the property it hopes to establish.

**TDD** covers AC-0030 through AC-0052, AC-0057 through AC-0060, AC-0064 and
AC-0065 — twenty-three plus four plus two, so twenty-nine criteria, each a
compressible invariant over a pure function or a single `sync` call.

- **Invocation grammar (AC-0030)** — TDD. Oracle: the parser's exit status and
  the handler's returned code across the three modes and each malformed
  combination, driven through the real `cli.py` parser rather than a hand-built
  `Namespace`, because a hand-built namespace supplies the defaults the parser
  is what decides.
- **Abbreviation posture (AC-0060)** — TDD. Oracle: `--guides` resolves to the
  restrictor and an abbreviation of `--guides-mode` is rejected. Asserting only
  that `--guides` works passes a parser that still abbreviates, which is the
  state this criterion exists to end.
- **Consent (AC-0031)** — TDD. Oracle: the target tree's file set before and
  after, under each of four inputs — an affirmative at the prompt, a refusal,
  `--yes`, and EOF with no TTY. A test asserting only the declined message
  passes while the write happens anyway.
- **The consented plan is the applied plan (AC-0057)** — TDD. Oracle: the row
  set of the plan an apply run prints equals the row set its write phase acts
  on, compared for equality. This is the criterion that makes AC-0033's
  equality well-founded, so a test that reads the plan from anywhere but the
  run's own output does not discharge it.
- **Apply order (AC-0032)** — TDD. Oracle: the recorded sequence of jailed-write
  calls, compared against the fixed order. An assertion that all paths exist
  after the run cannot observe order at all.
- **The write set (AC-0033)** — TDD. Oracle: the set of paths written, compared
  for equality in both directions against the filter-admitted rows of the run's
  own plan, with companion rows contributing their computed companion path. A
  subset check passes a run that wrote nothing.
- **Companion write (AC-0034)** — TDD. Oracle: the companion's bytes equal the
  replayed source bytes, and the adopter's file's sha256 is unchanged across the
  run. The second half catches a companion written correctly and the original
  clobbered.
- **Stale removal ordering and keep-set (AC-0035)** — TDD. Oracle: the recorded
  call order places removal after the last write, and the keep-set argument
  equals the full replayed planned set.
- **Nothing outside scope is removed (AC-0064)** — TDD. Oracle: a scoped run
  over a tree recording paths outside the scope, and paths under a `--package`
  subtree, leaves every one of them present. The fixture must record paths
  outside the scope or the check is vacuous.
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
  This is the one outcome § Never do forbids absolutely, so the criterion exists
  to make it legible rather than to permit it.
- **Exit codes and totality (AC-0039, AC-0040)** — TDD. Oracle: every row of the
  table driven to its code, plus a fault injected at each boundary to prove no
  uncaught exception sets the status.
- **The before-and-after walks (AC-0041)** — TDD. Oracle: a non-dereferencing
  walk of the target, and of the source subject the criterion names for that
  source form, compared before and after each row of the table.
- **Recipe as filter (AC-0042)** — TDD. Oracle: with no scoping flag, the
  written set covers the recorded recipe.
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
- **A leak violation reaches no write (AC-0051)** — TDD. Oracle: the tree walk
  after a violating run. The pass direction cannot distinguish a working refusal
  from an absent one, so the fixture must violate.
- **Every write is jailed (AC-0052)** — TDD. Oracle: a planned path resolving
  outside the target root is refused at the write.
- **Every target read is confined (AC-0065)** — TDD. Oracle: the hard-link and
  reparse-point cases phase 2's path-confinement criterion fixes, re-driven through the apply
  path's own reads. The criterion is phase 2's; only the caller is new.

**Goal-based checks** cover AC-0053, AC-0054, AC-0055 and AC-0061 through
AC-0063 — six delivery conditions, each a command whose output is the answer.

- **Rollout phase count (AC-0053)** — goal-based. Oracle: the banner's claim and
  § Rollout's own list agree on how many phases remain.
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
- **Guide covers the apply run (AC-0054)** — goal-based. Oracle: the section
  exists in the authored source and in the projected copy, and both site gates
  pass.
- **Version across the release surface (AC-0055)** — goal-based. Oracle: the
  release-surface derivation the plan's § Grounding names reports every surface
  reading the same string, and that string is `0.49.0`. The derivation supplies
  the closed set; this criterion does not enumerate it by hand.

**Visual / manual QA** covers AC-0056 — one criterion. That is 29 + 6 + 1 = 36.

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
  apply path exists. Supplying both
  flags is malformed, `--compare-tree` without `--check` is malformed, `--yes`
  outside an apply run is malformed, and any of `--pack`, `--profile` or
  `--guides` supplied with `--check` is malformed.
- [ ] **AC-0031.** An apply run writes nothing until consent is given. Consent
  is an affirmative answer at the prompt or `--yes` on the command line; a
  negative answer, an end-of-input, or an absent terminal with no `--yes` all
  leave the target tree byte-identical to its pre-run state.
- [ ] **AC-0032.** Writes land in the order packs, profiles, guides — and the
  ownership state after all three. No group writes a path under
  `packages/credbroker/` or `.agentbundle/tooling/agentbundle/`.
- [ ] **AC-0033.** The set of paths an apply run writes equals, exactly: the
  `would-update` paths of the plan AC-0057 fixes, together with
  `safety.companion_path`'s computed path for each of that plan's
  `would-companion` rows. No other path under the target tree is created,
  modified, moved, or has its mode changed.
- [ ] **AC-0034.** A `would-companion` path receives `safety.companion_path`'s
  computed path carrying the replayed source bytes, and the adopter's own file
  at that path has the same sha256 after the run as before it.
- [ ] **AC-0035.** Stale removal runs only after every planned write has landed,
  keeps its sha256 guard unchanged, and computes its keep-set from the full
  replayed planned set rather than from the write set.
- [ ] **AC-0036.** For every path in the recorded path set AC-0059 fixes, the
  recorded sha256 equals the digest of the bytes the run wrote to it when the
  run wrote it, and the value recorded before the run when it did not.
- [ ] **AC-0037.** The pin each source form records is the first matching row.
  The `source_revision` and `archive_sha256` values are the ones phase 2's source-fidelity criterion
  already fixes for that form; this criterion adds only that they are now
  written to the state rather than printed:

  | Source form | `source_uri` | `source_revision` | `archive_sha256` |
  | --- | --- | --- | --- |
  | local clone path | the resolved path, under `attributed` only | absent | absent |
  | `git+https://…[@<ref>]` | the URI, under `attributed` only | the ref the URI names, or `main` | absent |
  | `archive+https://…` | the URI, under `attributed` only | absent | the verified digest |
  | `catalogue+https://…` | the URI, under `attributed` only | the descriptor's `source_revision`, or absent | the verified digest |

  `synced_at` is recorded on every row.
- [ ] **AC-0038.** When any planned write fails, the target tree is restored
  before the command returns to the walk tuple AC-0041 compares — relative path,
  entry kind, mode, symlink target and bytes — and the exit code is 4.
- [ ] **AC-0039.** The command's exit code is the first matching row of this
  table, read top to bottom, and no input produces a code outside it:

  | Invocation | Condition | Code and name |
  | --- | --- | --- |
  | any | the invocation is malformed, including an omitted `--source`, both of `--dry-run` and `--check`, `--compare-tree` without `--check`, `--yes` outside an apply run, a scoping flag with `--check`, or a `--package` name outside `agentbundle` and `credbroker` | 2 — `malformed` |
  | any | `--package` was supplied with a recognised name | 3 — `cannot-answer` |
  | any | the source could not be resolved or its integrity could not be verified | 3 — `cannot-answer` |
  | apply or `--dry-run` | a `--pack` or `--profile` name the resolved source does not ship | 2 — `malformed` |
  | apply or `--dry-run` | no recorded selection is derivable | 3 — `cannot-answer` |
  | apply, `--dry-run`, or `--check --compare-tree` | the recorded-path container is not an array | 3 — `cannot-answer` |
  | apply or `--dry-run` | the identity leak check reported a violation | 1 — `difference` |
  | apply or `--dry-run` | a selected pack's adapter-contract major differs from the CLI's | 1 — `difference` |
  | apply | consent was not given | 1 — `difference` |
  | apply | a planned write failed and the tree could not be fully restored | 4 — `apply-failed` |
  | apply | a planned write failed and the tree was restored | 4 — `apply-failed` |
  | apply | every planned write landed and stale removal failed | 4 — `apply-failed` |
  | apply | every planned write landed and the ownership state could not be written | 4 — `apply-failed` |
  | apply | every planned write landed, stale removal completed, and the state was written | 0 — `success` |
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
  source ships a name is not decidable until the source resolves.
- [ ] **AC-0040.** Every invocation and every failure reaches a named row of
  AC-0039's table at the command boundary. No uncaught exception sets the
  process exit status.
- [ ] **AC-0041.** A non-dereferencing walk comparing relative path, entry kind,
  mode, symlink target and bytes is identical before and after every invocation,
  on every row of AC-0039's table, for both subjects below:

  | Subject | Local-path `--source` | `git+https://` | `archive+https://` or `catalogue+https://` |
  | --- | --- | --- | --- |
  | the source | the adopter's directory at that path | the extracted clone, for as long as the run holds it | not applicable: phase-2's § Always do requires the extracted directory be deleted, so no tree exists on either side and that deletion obligation discharges the rail |
  | the target | the target tree | the target tree | the target tree |

  The target walk is identical on every row except the `0 — success` apply row,
  where it differs exactly by the paths AC-0033 names, the paths stale removal
  removed, and the ownership state.
- [ ] **AC-0042.** With none of `--pack`, `--profile`, `--guides`, or
  `--package` supplied, an apply run covers the recorded recipe, less the paths
  AC-0047 defers.
- [ ] **AC-0043.** Each applying scoping flag restricts both the written set and
  the plan the run prints to its subtree: `--pack <name>` to `packs/<name>/`,
  `--profile <name>` to `profiles/<name>.toml`, and `--guides` to
  `guides/_shared/`. A repeated `--pack` covers the union of the named packs.
  The restriction applies identically on `--dry-run`, so a preview and the apply
  it previews name the same paths.
- [ ] **AC-0044.** A run supplying `--pack`, `--profile`, or `--guides` writes
  neither `catalogue.toml` nor any path under `tests/conformance/`, and leaves
  every recorded identity field at its pre-run value.
- [ ] **AC-0045.** `--pack <name>` naming a pack absent from the recorded recipe
  writes that pack's subtree and records the name in the recipe's pack list,
  leaving the list's existing entries in place. `--profile <name>` does the same
  for the profile list.
- [ ] **AC-0046.** A `--pack` or `--profile` name the resolved source does not
  ship refuses as malformed, naming the field, and writes nothing.
- [ ] **AC-0047.** `--package` accepts exactly the names `agentbundle` and
  `credbroker`. Either one refuses the invocation it appears on — apply,
  `--dry-run` or `--check` alike — with the cannot-answer code, naming that
  package sync is not available. No invocation writes any path under
  `packages/credbroker/` or `.agentbundle/tooling/agentbundle/`.
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
- [ ] **AC-0053.** `docs/architecture/catalogue/upstream-sync.md` records phase
  3 as delivered, and its banner and § Rollout agree on how many phases remain.
- [ ] **AC-0054.** `guides/_shared/how-to/create-a-self-hosted-catalogue.md`
  carries a section covering the apply run, how consent is given, the scoping
  flags, and what an `.upstream.<ext>` companion obliges the adopter to do —
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
- [ ] **AC-0057.** The plan an apply run prints, and consents against, contains
  exactly the rows that run will act on: scope-filtered per AC-0043, and with
  every path under `packages/credbroker/` and `.agentbundle/tooling/agentbundle/`
  excluded. The run reports the number of planned paths it excluded for that
  second reason as a named count, without adding a verdict to the five that
  phase 2's five-verdict criterion fixes.
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
  where `init` overwrites, and does not state that `init`'s overwrite is
  replaced.
- [ ] **AC-0063.** `upstream-sync.md` names `.agentbundle/tooling/agentbundle/`
  and `packages/credbroker/` as the two `--package` destinations in
  § Granularity, and § Rollout item 4 no longer describes both as `packages/`
  subtrees.
- [ ] **AC-0064.** A run supplying a scoping flag removes no recorded path
  outside that scope, and no invocation removes a recorded path under
  `packages/credbroker/` or `.agentbundle/tooling/agentbundle/`.
- [ ] **AC-0065.** Every read or hash of a target path the apply path performs
  goes through the confinement helpers phase 2's path-confinement criterion names, and is refused on
  the same hard-link, non-regular and reparse-point inputs that criterion fixes.

## Follow-ons

- **Package sync** — writing both `--package` subtrees. Owner: phase 4 of
  [`upstream-sync.md`](../../architecture/catalogue/upstream-sync.md) § Rollout.
- **`--check --compare-tree` resolves a source it does not read** — phase 2
  recorded three routes and left the choice to the owner; this phase does not
  take it (owner confirmation 2026-09-22). Owner: unassigned.
- **A read-time constraint on the recorded mode fields and the pin** — carried
  forward from phase 2 unchanged. Owner: unassigned.
- **A scanner rule for unbounded rendered values** — no rule detects a value
  reaching stdout without the terminal-safe check, so AC-0049's class is
  enforced by review. Owner: unassigned.
- **A ceiling on the recorded path set and the total bytes hashed** — carried
  forward from phase 2 unchanged, and now reached on a writing verb rather than
  a read-only one. Owner: unassigned.
- **A discriminator for the refusal conditions sharing exit 1** — phase 2 left
  the field's shape and which rows carry it to the owner; this phase adds a
  third condition to that code without taking the decision. Owner: unassigned.

## Assumptions

- Product: whether an adopter wants a scoped apply to refresh the pin at all,
  given the pin then describes a tree only partly at that source — this phase
  records it on every successful apply, scoped or not (settled by: the owner,
  after the first real scoped run).
