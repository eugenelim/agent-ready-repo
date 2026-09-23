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
| Current architecture | Applicable — this delivers phase 3 of that rollout, and § Granularity misnames one of the two package subtrees | [`docs/architecture/catalogue/upstream-sync.md`](../../architecture/catalogue/upstream-sync.md) | eugenelim | Banner and § Rollout mark phase 3 done and one phase remaining; § Stage 3 says `sync` classifies where `init` overwrites rather than that the overwrite is replaced; § Granularity names each `--package` subtree at its real destination | AC-0053 passes |
| User-facing promise | Applicable — apply is the reason the verb exists, and this guide is projected into the docs site | `guides/_shared/how-to/create-a-self-hosted-catalogue.md` | eugenelim | A section covering the apply run, consent, the scoping flags, and what a companion file obliges | AC-0054 passes, including its projected-surface half |
| Interface compatibility | Applicable — the PyPI readme is a pinned release surface | `packages/agentbundle/README-pypi.md` | eugenelim | A "What's new in" section naming the version AC-0055 fixes | AC-0055 passes |
| Release history | Applicable — new flag semantics and a new write path are release-coupling triggers | [`packages/agentbundle/CHANGELOG.md`](../../../packages/agentbundle/CHANGELOG.md), [`docs/product/changelog.md`](../../product/changelog.md) | eugenelim | A topmost entry naming the version AC-0055 fixes, written adopter-first | AC-0055 passes |
| Decision rationale | Not applicable — every decision this delivery makes is recorded as a criterion or in the plan's design; none changes a repository-wide rule | — | — | — | — |
| Maintainer procedure | Not applicable — no runbook governs this command | — | — | — | — |

## Agent Rules

### Always do

- Resolve the attribution, tooling, and guides-replay modes from an explicit
  flag or that flag's safe default, never from the recorded recipe. The consent
  prompt is an output surface like any other and reads no recorded mode.
- Keep `_is_attributed` the single attribution gate. A second check that agrees
  on every input today is a defect, because nothing then constrains the two to
  keep agreeing.
- Pass every value the command renders that it did not itself author through the
  bounded terminal-safe scalar check before it reaches stdout, stderr, or the
  `--format json` document.
- Report a refusal, a decline, or a discard by naming the field and the reason,
  never by reproducing a rejected value.
- Write every file under the target tree through the jailed write primitive, and
  read or hash every path under it through the confinement helpers the root
  `AGENTS.md` § Security considerations declares.
- Keep the removal guard, the identity leak check, the ownership-state writer,
  and the Tier verdict as one implementation each, shared with their existing
  callers.
- Take consent before the first write and prove the plan the operator consented
  to is the plan that is applied.

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
- Never write under a `--package` subtree.

## Testing Strategy

Three modes, over 27 criteria. Each entry below names the comparison its oracle
performs, not the property it hopes to establish.

**TDD** covers AC-0030 through AC-0052 — twenty-three criteria, each a
compressible invariant over a pure function or a single `sync` call.

- **Invocation grammar (AC-0030)** — TDD. Oracle: the parser's exit status and
  the handler's returned code across the three modes and each malformed
  combination, driven through the real `cli.py` parser rather than a
  hand-built `Namespace`, because a hand-built namespace supplies the defaults
  the parser is what decides.
- **Consent (AC-0031)** — TDD. Oracle: the target tree's file set before and
  after, under each of four inputs — an affirmative at the prompt, a refusal,
  `--yes`, and EOF with no TTY. A test asserting only the declined message
  passes while the write happens anyway, so the tree is the oracle and the
  message is not.
- **Apply order (AC-0032)** — TDD. Oracle: the recorded sequence of jailed-write
  calls, compared against the fixed order. An assertion that all paths exist
  after the run cannot observe order at all.
- **Per-path action and the plan's authority (AC-0033)** — TDD. Oracle: the set
  of paths written, compared for equality against the set the same run's plan
  named. Equality in both directions — a subset check passes a run that wrote
  nothing.
- **Companion write (AC-0034)** — TDD. Oracle: the companion's bytes equal the
  replayed source bytes, and the adopter's file's sha256 is unchanged across the
  run. The second half is what catches a companion written correctly *and* the
  original clobbered.
- **Stale removal after writes, with the full keep-set (AC-0035)** — TDD.
  Oracle: a scoped run over a tree with recorded paths outside the scope leaves
  every one of them present. The failure this catches deletes the rest of the
  adopter's tree, so the fixture must record paths outside the scope or the
  check is vacuous.
- **State written last, with fresh and preserved hashes (AC-0036)** — TDD.
  Oracle: for each recorded path, the state's sha256 after the run equals the
  written bytes' digest when the run wrote it and the pre-run recorded value
  when it did not.
- **The pin per source form (AC-0037)** — TDD. Oracle: the four-row table, each
  row asserting which of the three pin fields is present and which absent.
- **Rollback (AC-0038)** — TDD. Oracle: with a write injected to fail partway,
  the target tree's path set and every file's sha256 equal their pre-run values,
  and the code is 4. Asserting the code alone passes a run that returned 4 over
  a mangled tree.
- **Exit codes and totality (AC-0039, AC-0040)** — TDD. Oracle: each table row
  driven to its code, plus a fault injected at each boundary to prove no
  uncaught exception sets the status.
- **The before-and-after walk over both trees (AC-0041)** — TDD. Oracle: a
  non-dereferencing walk of the target and of the source, compared before and
  after each case. The source-side half has no antecedent that permits a
  difference, which is what makes it a fixed rail rather than a case analysis.
- **Recipe as filter, and the applying scoping flags (AC-0042, AC-0043)** —
  TDD. Oracle: the written path set compared against the declared subtree, for
  each of `--pack`, `--profile` and `--guides` and for a repeated `--pack`.
- **Derivation-wide paths stay whole (AC-0044)** — TDD. Oracle: a scoped run
  over a fixture whose `catalogue.toml` and `tests/conformance/` entries are
  stale leaves both untouched, and the recorded identity fields unchanged.
- **A new name amends the recipe (AC-0045)** — TDD. Oracle: the recorded
  recipe's pack list after the run equals the pre-run list plus the named pack.
- **An unknown name refuses (AC-0046)** — TDD. Oracle: the code, plus the tree
  walk proving no write.
- **`--package` reserves without writing (AC-0047)** — TDD. Oracle: both valid
  names refuse; the tree walk proves neither subtree was written; an invalid
  name is malformed.
- **Modes still come from flags and defaults (AC-0048)** — TDD. Oracle: two
  apply runs with identical flags over trees whose recorded modes differ produce
  the same written byte map. This is the phase-2 invariant a consent prompt is
  most likely to reopen, so the oracle drives the whole run, not the seam.
- **Terminal-safe rendering on the apply surface (AC-0049)** — TDD. Oracle: a
  hostile recorded value reaches no output surface. The observable is a bound
  the sink does not normalise — length or surrounding whitespace — because
  `json.dumps` escapes a raw control character whether the check runs or not.
- **The source URI stays absent outside attributed (AC-0050)** — TDD. Oracle:
  stdout, stderr, the JSON document, and the consent prompt, on every apply row
  including each refusal.
- **A leak violation reaches no write (AC-0051)** — TDD. Oracle: the tree walk
  after a violating run. The pass direction cannot distinguish a working refusal
  from an absent one, so the fixture must violate.
- **Every write is jailed (AC-0052)** — TDD. Oracle: a planned path escaping the
  root is refused. An inline prefix check does not satisfy it, which the
  reparse-point and hard-link cases are what distinguish.

**Goal-based checks** cover AC-0053, AC-0054 and AC-0055 — three delivery
conditions, each a command whose output is the answer.

- **Architecture doc consistency (AC-0053)** — goal-based. Oracle: every
  citation in the edited file resolves to the construct it names, and the
  rollout's phase count agrees with its own list. An absence check passes a
  wrong re-pin, which is why resolution is the oracle and not a grep.
- **Guide covers the apply run (AC-0054)** — goal-based. Oracle: the section
  exists in the authored source *and* in the projected copy, and both site
  gates pass.
- **Version across the pinned release surface (AC-0055)** — goal-based. Oracle:
  every derived release surface reads the same string.

**Visual / manual QA** covers AC-0056 — one criterion.

- **The apply run an adopter performs (AC-0056)** — visual / manual QA. Oracle:
  the observed stdout, the observed exit code, and the resulting tree of a real
  apply against a real derived tree. A passing unit suite does not establish
  that the command an adopter types works.

## Acceptance Criteria

- [ ] **AC-0030.** `--dry-run`, `--check`, and neither are three mutually
  exclusive invocation modes; neither flag means apply. Supplying both is
  malformed, `--compare-tree` without `--check` is malformed, and `--yes`
  outside an apply run is malformed.
- [ ] **AC-0031.** An apply run writes nothing until consent is given. Consent
  is an affirmative answer at the prompt or `--yes` on the command line; a
  negative answer, an end-of-input, or an absent terminal with no `--yes` all
  leave the target tree byte-identical to its pre-run state.
- [ ] **AC-0032.** Writes land in the order packs, profiles, guides, packages —
  and the ownership state after all four.
- [ ] **AC-0033.** The set of paths an apply run writes equals the set its own
  printed plan named as `would-update` or `would-companion`. No other path under
  the target tree is created, modified, moved, or has its mode changed.
- [ ] **AC-0034.** A `would-companion` path receives `safety.companion_path`'s
  computed path carrying the replayed source bytes, and the adopter's own file
  at that path has the same sha256 after the run as before it.
- [ ] **AC-0035.** Stale removal runs only after every planned write has landed,
  keeps its sha256 guard unchanged, and computes its keep-set from the full
  replayed planned set. A scoped run removes no recorded path outside its scope.
- [ ] **AC-0036.** The ownership state is written last. For every recorded path
  the run wrote, its recorded sha256 equals the digest of the bytes written; for
  every recorded path the run did not write, its recorded sha256 equals the
  value recorded before the run.
- [ ] **AC-0037.** The pin each source form records is the first matching row:

  | Source form | `source_uri` | `source_revision` | `archive_sha256` |
  | --- | --- | --- | --- |
  | local clone path | the resolved path, under `attributed` only | absent | absent |
  | `git+https://…[@<ref>]` | the URI, under `attributed` only | the ref the URI names, or `main` | absent |
  | `archive+https://…` or `catalogue+https://…` | the URI, under `attributed` only | as the fetch resolved it | the verified digest |

  `synced_at` is recorded on every row.
- [ ] **AC-0038.** When any planned write fails, the target tree is restored to
  its pre-run path set and per-file sha256 before the command returns, and the
  exit code is 4.
- [ ] **AC-0039.** The command's exit code is the first matching row of this
  table, read top to bottom, and no input produces a code outside it:

  | Invocation | Condition | Code and name |
  | --- | --- | --- |
  | any | the invocation is malformed, including an omitted `--source`, both of `--dry-run` and `--check`, `--compare-tree` without `--check`, `--yes` outside an apply run, or an unrecognised scoping name | 2 — `malformed` |
  | apply | `--package` was supplied with a recognised name | 3 — `cannot-answer` |
  | any | the source could not be resolved or its integrity could not be verified | 3 — `cannot-answer` |
  | apply or `--dry-run` | no recorded selection is derivable | 3 — `cannot-answer` |
  | apply, `--dry-run`, or `--check --compare-tree` | the recorded-path container is not an array | 3 — `cannot-answer` |
  | apply or `--dry-run` | the identity leak check reported a violation | 1 — `difference` |
  | apply or `--dry-run` | a selected pack's adapter-contract major differs from the CLI's | 1 — `difference` |
  | apply | consent was not given | 1 — `difference` |
  | apply | a planned write failed and the tree was restored | 4 — `apply-failed` |
  | apply | every planned write landed and the state was written | 0 — `success` |
  | `--dry-run` | a plan was printed, whatever its counts | 0 — `success` |
  | `--check`, no `--compare-tree` | the resolved source affords no verified digest | 3 — `cannot-answer` |
  | `--check`, no `--compare-tree` | the recorded `archive_sha256` is absent, or is not a 64-character lowercase hex string | 3 — `cannot-answer` |
  | `--check`, no `--compare-tree` | the recorded digest equals the resolved source's verified digest | 0 — `success` |
  | `--check`, no `--compare-tree` | the recorded digest differs from it | 1 — `difference` |
  | `--check --compare-tree` | the recorded path set is empty, or any recorded path could not be compared | 3 — `cannot-answer` |
  | `--check --compare-tree` | every recorded path was compared and none differs | 0 — `success` |
  | `--check --compare-tree` | every recorded path was compared and some differ | 1 — `difference` |

  The `--package` row sits above source resolution so a run that will refuse
  performs no fetch.
- [ ] **AC-0040.** Every invocation and every failure reaches a named row of
  AC-0039's table at the command boundary. No uncaught exception sets the
  process exit status.
- [ ] **AC-0041.** A non-dereferencing walk of the source tree is identical
  before and after every invocation, on every row of AC-0039's table. The same
  walk of the target tree is identical before and after every row except the
  `0 — success` apply row, where it differs exactly by the paths AC-0033 names,
  the paths AC-0035 removed, and the ownership state.
- [ ] **AC-0042.** With none of `--pack`, `--profile`, `--guides`, or
  `--package` supplied, an apply run covers the recorded recipe.
- [ ] **AC-0043.** Each applying scoping flag restricts the written set to its
  subtree: `--pack <name>` to `packs/<name>/`, `--profile <name>` to
  `profiles/<name>.toml`, and `--guides` to `guides/_shared/`. A repeated
  `--pack` covers the union of the named packs. `--package` restricts nothing,
  because AC-0047 refuses the run it appears on.
- [ ] **AC-0044.** A run supplying `--pack`, `--profile`, or `--guides` writes
  neither `catalogue.toml` nor any path under `tests/conformance/`, and leaves
  every recorded identity field at its pre-run value.
- [ ] **AC-0045.** `--pack <name>` naming a pack absent from the recorded recipe
  writes that pack's subtree and records the name in the recipe's pack list,
  leaving the list's existing entries in place. `--profile <name>` does the same
  for the profile list.
- [ ] **AC-0046.** A `--pack`, `--profile`, or `--package` name the source does
  not ship refuses as malformed, naming the field, and writes nothing.
- [ ] **AC-0047.** `--package` accepts exactly the names `agentbundle` and
  `credbroker`. Either one refuses the run with the cannot-answer code, naming
  that package sync is not available. No invocation writes any path under
  `packages/credbroker/` or `.agentbundle/tooling/agentbundle/`.
- [ ] **AC-0048.** Two apply runs with identical flags, over target trees whose
  recorded `attribution`, `tooling`, and `guides` differ, write the same bytes
  to the same paths.
- [ ] **AC-0049.** Every value the apply surface renders that the command did
  not itself author — whatever its origin — passes the bounded terminal-safe
  scalar check before it reaches stdout, stderr, the consent prompt, or the
  `--format json` document. A value that fails is reported by field name and
  reason, without the value.
- [ ] **AC-0050.** Outside `--attribution attributed`, the source URI appears on
  no output surface, including the consent prompt, on every row of AC-0039's
  table.
- [ ] **AC-0051.** When the identity leak check reports a violation, no path
  under the target tree is created, modified, moved, removed, or has its mode
  changed.
- [ ] **AC-0052.** Every write the apply path performs goes through the jailed
  write primitive, and every read or hash of a target path goes through the
  declared confinement helpers. A planned path resolving outside the target root
  is refused, and an inline lexical prefix check does not satisfy this criterion.
- [ ] **AC-0053.** `docs/architecture/catalogue/upstream-sync.md` records phase
  3 as delivered with one phase remaining; every code citation in it resolves to
  the construct it names; § Stage 3 states that `sync` classifies where `init`
  overwrites rather than that the overwrite is replaced; and § Granularity names
  `.agentbundle/tooling/agentbundle/` and `packages/credbroker/` as the two
  `--package` subtrees.
- [ ] **AC-0054.** `guides/_shared/how-to/create-a-self-hosted-catalogue.md`
  carries a section covering the apply run, how consent is given, the four
  scoping flags, and what an `.upstream.<ext>` companion obliges the adopter to
  do — present in the authored source and in the projected copy, with both site
  gates passing.
- [ ] **AC-0055.** The version is `0.49.0` across every derived release surface.
- [ ] **AC-0056.** An apply run against a real derived tree is exercised end to
  end through its documented happy path, and its stdout, exit code, and
  resulting tree are recorded.

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
