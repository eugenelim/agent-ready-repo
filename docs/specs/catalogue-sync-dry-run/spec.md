# Spec: catalogue sync — dry-run and check

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0059 (the catalogue-curation pack, which owns the white-label export boundary)
- **Contract:** none — `sync` reads `.agentbundle/self-host-state.json`, which is defined in code only and has no file under `contracts/`
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Objective

An adopter who derived a catalogue from an upstream one, then edited it, can see
exactly what taking later upstream changes would do to their tree — before
anything can apply them. `agentbundle catalogue sync --dry-run` resolves the
source, replays the recorded derivation in memory, classifies every planned path
against what the adopter has edited, and prints a plan. `agentbundle catalogue
sync --check` answers the narrower question "is my tree current?" and sets an
exit code.

Neither writes. A `--dry-run` and a `--check` leave the target tree unchanged on
every path the command can return from, including every refusal.

Success for the adopter is three numbers and a reason. The plan says how many
files would be updated in place, how many of their edited files would instead
receive an `.upstream.<ext>` companion beside the original, and how many files
sync would not touch at all. When sync cannot answer a question it says which
question and why, and returns the code that means "cannot answer" rather than
the one that means "no difference". A zero from a comparison nothing performed
is the single outcome this command exists to prevent, and the recorded state it
reads is third-party input, so that zero has to be unreachable by construction
rather than by care.

The source forms in AC-0001 differ in how much they prove about what they
delivered. The plan says which fidelity applies, including whose word a digest
rests on. Every pin recorded in the field today is the weakest form, so naming
the fidelity stops a local-path sync reading as a verified one.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Applicable — this delivers a numbered phase of that rollout, and § Stage 3's two code citations move | [`docs/architecture/catalogue/upstream-sync.md`](../../architecture/catalogue/upstream-sync.md) | eugenelim | Status and rollout mark phase 2 done; § Stage 3's citations re-pinned; § Granularity records the vacated `--guides` name | AC-0022, AC-0023, and AC-0024 pass |
| Current architecture | Applicable — § What a re-run does today carries two stale citations and one claim phase 1 made false | [`docs/architecture/catalogue/derived-catalogue.md`](../../architecture/catalogue/derived-catalogue.md) | eugenelim | Citations re-pinned; the "recipe is not remembered" bullet replaced by current state | AC-0022 and AC-0025 pass |
| Current architecture | Applicable — its entrypoint list enumerates `catalogue`'s subcommands and is missing one already | [`docs/architecture/agentbundle.md`](../../architecture/agentbundle.md) | eugenelim | § 2 Entrypoints names the same set the parser registers | AC-0021 passes |
| User-facing promise | Applicable — `catalogue sync` is a new adopter-invocable command, and this guide is projected into the docs site | `guides/_shared/how-to/create-a-self-hosted-catalogue.md` | eugenelim | A section naming both read-only flags, that neither writes, and the attributed-only source disclosure | AC-0026 passes, including its projected-surface half |
| Interface compatibility | Applicable — the PyPI readme is a pinned release surface | `packages/agentbundle/README-pypi.md` | eugenelim | A "What's new in" section naming the version AC-0027 fixes | The roster suite is dispatched explicitly and its result recorded in the verification ledger; it has no pull-request trigger |
| Release history | Applicable — a new public CLI verb is a release-coupling trigger | [`packages/agentbundle/CHANGELOG.md`](../../../packages/agentbundle/CHANGELOG.md), [`docs/product/changelog.md`](../../product/changelog.md) | eugenelim | A topmost entry naming the version AC-0027 fixes, written adopter-first | AC-0027 passes |
| Decision rationale | Applicable — the conflict between the stub-marker convention and the scoped source rule was resolved at the rule's owner, not per-PR | [`packages/AGENTS.local.md`](../../../packages/AGENTS.local.md) | eugenelim | The criterion-ordinal exemption, stating which source yields and why | AC-0028 and AC-0029 pass |
| Maintainer procedure | Not applicable — no runbook governs this command | — | — | — | — |

## Boundaries

### Always do

- Resolve the attribution, tooling, and guides modes from an explicit flag or
  that flag's safe default, never from the recorded recipe.
- Keep `_is_attributed` the single attribution gate. This obligation is enforced
  by review rather than mechanically, by decision: a one-line equality gate
  affords no discriminating fixture, so an added second check that agrees on
  every input is invisible to any outcome oracle. AC-0004 alone fails closed on
  a second check shaped as an inequality against `"white-label"`, because its
  oracle drives an unrecognised third value through the replay; that oracle is
  the leak check over the replayed byte map, so it cannot observe a duplicate
  gate on an output channel. Review has to catch two shapes: an output-only
  duplicate gate, and an agreeing duplicate that drifts later. Owner decision
  2026-09-17, raised by the secure-design pass.
- Pass every value this command renders that it did not itself author through
  the bounded terminal-safe scalar check before it reaches any output surface.
  AC-0012 states the class; the Assumptions record which values it resolves to
  today and the probe that established the check admits each of them.
- Report a discard, a refusal, or a decline by naming the field and the reason,
  never by reproducing a rejected value.
- Name the source fidelity in every plan, including whose word a digest rests on.
- Delete the extracted archive directory a digest-bearing fetch returns; that
  fetch hands the caller ownership on success and self-cleans only on failure.
- Read and hash every path under the target tree through the confinement
  helpers the root `AGENTS.md` § Security considerations declares, never an
  inline prefix check.
- Keep the removal guard and the identity leak check as one implementation each,
  shared with `init`, and the Tier verdict as one implementation shared with
  `upgrade`. `init` has no Tier verdict of its own.
- Regenerate and re-measure a projected surface inside the task that changes its
  authored source, and name which representation each gate reads.

### Ask first

- Before adding any flag beyond the eight § Interfaces declares.
- Before changing what `init` writes, aborts on, or removes.
- Before introducing a fifth exit code, or changing a row of AC-0013's table.
- Before widening the discovery channel's declared bounds, or refining a task
  that has started.

### Never do

- Never write, move, delete, or change the mode of any path under the target
  tree. This phase has no write path.
- Never add a module, package, or top-level directory beyond the one command
  module the CLI's lazy-dispatch convention requires.
- Never add a third-party dependency.
- Never bring the state file inside the identity leak check.
- Never let a recorded value select a mode, widen a selection, or resolve as a
  path.
- Never return the no-difference code from a comparison that was not performed,
  and never resolve an absent or discarded recorded selection to the source's
  full contents.
- Never re-implement the Tier contract, the removal guard, or URI dispatch.
- Never copy a measured value into a second prose home instead of citing the
  derivation that produces it.

## Testing Strategy

Three modes. **TDD** covers AC-0001, AC-0002, AC-0003, AC-0004, AC-0005,
AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013,
AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, and AC-0020 — twenty
criteria, each a compressible invariant over a pure function or a single `sync`
call. **Goal-based checks** cover AC-0021, AC-0022, AC-0023, AC-0024, AC-0025,
AC-0026, AC-0027, AC-0028, and AC-0029 — nine delivery conditions. **Visual /
manual QA** covers the printed plan, which is the product an adopter reads and
which no unit gate can establish is legible. That is 20 + 9 = 29 criteria; the
plan's § Stub tally records covered, uncovered and `no stub` counts, and
§ Construction tests owns where each check lives.

Each entry below names the comparison its oracle performs, not the property it
hopes to establish.

- **Source fidelity and digest provenance (AC-0001)** — TDD, parametrised over
  four source forms. Oracle: string equality between the plan's fidelity token
  and a fixed literal per form. The `archive+https://` and `catalogue+https://`
  arms are separate rows because they differ in whose digest is verified, which
  a single `verified-digest` token cannot express.
- **The source is named only under `attributed` (AC-0002)** — TDD, parametrised
  over both attribution modes, all three output channels, and every exit-table
  row, including refusals. Oracle: substring absence of the source URI in
  stdout, stderr and the parsed JSON document under every non-`attributed` mode;
  presence in a printed plan under `attributed`; and absence from a resolution
  or verification refusal in every mode. Absence across three channels and the
  refusing rows is what the criterion needs; a happy-path or single-channel
  check passes while another path discloses.
- **Mode fields fail closed (AC-0003)** — TDD, one case whose recorded state is
  wrong in all three fields at once. Oracle: equality of each resolved mode
  against `white-label`, `external`, `selected`. Driven together because a
  per-field case passes while a sibling reads through.
- **Identity leak check and its refusal (AC-0004, AC-0005)** — TDD against the
  extracted replay callable, not the CLI. AC-0004's oracle is the repository's
  own leak check over the replayed byte map, so the anchor set stays identical
  to `init`'s. AC-0005's oracle is the exit code plus the violation count on a
  source crafted to leak; the pass direction cannot distinguish a working
  refusal from an absent one. Parametrised over `white-label` and an
  unrecognised third value, which the CLI rejects before the replay — hence the
  callable-level surface.
- **Recipe admission parity with `init` (AC-0006)** — TDD, differential. Oracle:
  set equality of admitted recipe values and list equality of emitted
  diagnostics between the extracted reader and `init_self_hosted` over one
  state file. A fixed expected list would let both drift while each stayed green
  against its own copy.
- **The replayed modes are reported (AC-0007)** — TDD. Oracle: presence of the
  three resolved mode tokens and the flags-and-defaults provenance in the plan.
- **Recorded modes do not affect the plan (AC-0008)** — TDD. Oracle: byte
  equality of two plans driven with identical flags and state files that differ
  only in their recorded mode values.
- **Every underivable recorded selection refuses (AC-0009)** — TDD over every
  condition the criterion enumerates. Oracle: equality of the exit code against
  the cannot-answer code, absence of a plan, and presence of the distinguishing
  condition name. The widening it forbids is observable only on a run that does
  print a selection, so that half is carried by AC-0010's reported selection.
- **Tier verdict and companion path (AC-0010, AC-0011)** — TDD over the closed
  set of five path states. Oracle: equality of the reported verdict against
  `safety.classify`'s verdict for each non-inert path, exact equality of the
  inert class for the present null-digest path, and for AC-0011, string equality
  of the companion path against `safety.companion_path`'s result.
- **Rendered values are bounded (AC-0012)** — TDD, one rejecting case per value
  kind the Assumptions enumerate. Oracle: the field name and the reason appear
  and the rejected value does not. The pass direction cannot distinguish an
  applied check from an absent one, so each kind needs its own rejecting case.
- **The exit table is total at the command boundary (AC-0013, AC-0014)** — TDD,
  one input per row plus one malformed invocation and one resolver exception.
  Oracle: equality of the observed code and name against the first matching
  row, membership in the four-code set, and absence of an uncaught exception or
  traceback as the process exit mechanism.
- **The tree is unchanged (AC-0015)** — TDD, and the one check that must not be
  per-path. Oracle: equality of a recursive non-dereferencing walk of the target
  — relative path, entry kind, mode, symlink target, and bytes for regular files
  only — taken before and after, over every row of AC-0013's table.
- **Counts and their identity (AC-0016)** — TDD. Oracle: equality of the same
  counts between the table text and the parsed JSON from one run, plus the
  identity `compared + uncompared == len(raw managed_paths)`, an inert member
  fixture, and one malformed and one unrenderable member. The raw array is read
  before filtering, so dropping an entry cannot make a constant zero pass.
- **Every decline names a distinguishable reason (AC-0017)** — TDD, one fixture
  per post-change decline branch. Oracle: each independently pinned fixture
  produces its branch's reason token; the tokens are pairwise distinct; and
  their count equals the post-change AST derivation. Removing a branch fails its
  independent fixture even though the derived count also shrinks.
- **Warn-only compatibility (AC-0018)** — TDD, two arms of one parametrisation.
  Oracle: equality of the exit code between a run whose source declares each
  signal and the same run with the signal absent. One arm compares against a
  constant.
- **The existing spec-version gate still refuses (AC-0019)** — TDD against a
  fixture pack declaring adapter-contract major `1`. Oracle: the exit code and
  the existing refusal message. Every pack in the repository declares major `0`,
  so the fixture is what makes this able to fail.
- **Recorded-path reads use the declared confinement helper (AC-0020)** — TDD
  over hard-linked, non-regular, and reparse-point entries. Oracle: each fixture
  is accepted by an inline lexical-prefix check but refused by the applicable
  `file_safety` helper, so substituting the inline check makes the test fail.
- **The entrypoint roster (AC-0021)** — goal-based check. Oracle: set equality
  between the documented names and the derivation in the plan's § Grounding, so
  the criterion reads the parser rather than a copied list.
- **Citations resolve to their construct (AC-0022)** — goal-based check. Oracle:
  each citation the § Grounding derivation reports is opened at its line and the
  construct named there compared against the sentence, and the derivation's
  residual is empty within the edited-file scope. An absence check passes
  against a wrong re-pin, which is why resolution is the oracle and not a grep.
- **The rollout status is current (AC-0023)** — goal-based check. Oracle:
  substring presence of the delivered-status banner, the struck phase-2 entry,
  and the sentence that two phases remain.
- **The guides flag name stays free (AC-0024)** — goal-based check. Oracle:
  substring presence of the vacated-name record in § Granularity.
- **The recipe bullet describes current state (AC-0025)** — goal-based check.
  Oracle: substring absence of the "not remembered" claim and presence of the
  read-back it replaced.
- **The guide, and its projected surface (AC-0026)** — goal-based check with two
  oracles, because the two site gates read different representations: substring
  presence in the authored guide, then the authored-source entry-link gate, which
  runs on every pull request and needs no regeneration, and the rendered-links
  checker over a tree regenerated by the command § Grounding names.
- **The release surfaces (AC-0027)** — goal-based check. Oracle: string equality
  of the version across the surfaces the § Grounding release-surface derivation
  enumerates.
- **The marker conflict is resolved at its owner (AC-0028)** — goal-based check.
  Oracle: substring presence of the exemption and of which source yields.
- **Criterion ordinals stay bare (AC-0029)** — goal-based check. Oracle: absence
  of any path or section reference beside a criterion-ordinal label under the
  package test tree.

## Acceptance Criteria

- [x] **AC-0001.** For each source form, a `--dry-run` plan names exactly one
      fidelity token and reports the pin values that form affords:

      | `--source` form | Fidelity token | `archive_sha256` | `source_revision` |
      | --- | --- | --- | --- |
      | a local filesystem path | `local-path` | reported absent | reported absent |
      | `git+https://github.com/<owner>/<repo>[@<ref>]` | `git-tls` | reported absent | reported absent |
      | `archive+https://…#sha256=<64hex>` | `digest-adopter-pinned` | the digest the adopter supplied | reported absent |
      | `catalogue+https://…` | `digest-publisher-asserted` | the digest the descriptor declared | the descriptor's `source_revision`, or reported absent when it declares none |

- [x] **AC-0002.** Under `--attribution attributed` the plan names the resolved
      source. On every row of AC-0013's table, including every refusal, under
      every other attribution value the source URI appears in none of stdout,
      stderr, or the `--format json` document. A resolution or verification
      failure is reported without reproducing the URI under any attribution
      value, and the fidelity token of AC-0001 appears in every printed plan.
- [x] **AC-0003.** Given a schema-3 state whose recipe records
      `attribution = "attributed"`, `tooling = "vendored"`, and
      `guides = "none"`, a `--dry-run` invoked without `--attribution`,
      `--tooling`, or `--guides-mode` replays `white-label`, `external`, and
      `selected` respectively.
- [x] **AC-0004.** Under any `--attribution` value other than `attributed`,
      including an unrecognised one supplied to the replay callable directly,
      the replayed byte map passes the same identity leak check `init` applies,
      against the same anchor set built from the same source metadata.
- [x] **AC-0005.** When that leak check reports a violation, the command returns
      AC-0013's difference code and reports the violation count.
- [x] **AC-0006.** For any state file, the recipe values `sync` admits and the
      discard diagnostics it emits equal those `init` produces from that same
      file.
- [x] **AC-0007.** The plan names the three modes the run replayed with, and
      states that they come from flags and their defaults.
- [x] **AC-0008.** Two runs whose recorded `attribution`, `tooling`, and
      `guides` differ, invoked with identical flags, produce identical plans.
- [x] **AC-0009.** The command returns AC-0013's cannot-answer code and prints
      no plan for each state from which no recorded selection is derivable, and
      names which condition it hit. The conditions are: no state file at the
      target; the ownership-state loader could not return a state object for any
      reason, including a confinement refusal, invalid UTF-8, invalid JSON, a
      non-object document, an I/O failure, or recursion exhaustion; no `recipe`
      key at any `schema_version`; a `recipe` that is not a JSON object; a
      `recipe` carrying neither `packs` nor `profiles`; and a recorded `packs`
      or `profiles` value its read-time check discards.
- [x] **AC-0010.** Each planned path is reported as exactly one of
      `would-update`, `would-companion`, `schema-1-inert`, or `untouched`. For
      every non-inert path the reported verdict equals the Tier contract's
      verdict across the closed set of five path states, and the reported
      selection equals the recorded recipe's.

      | Path's state | Reported as |
      | --- | --- |
      | recorded, present on disk, and on-disk `sha256` equals the recorded non-null value | `would-update` |
      | recorded, absent on disk | `would-update` |
      | recorded, present on disk, and on-disk `sha256` differs from the recorded non-null value | `would-companion` |
      | recorded, present on disk, with `sha256: null` | `schema-1-inert` |
      | not recorded | `untouched` |

- [x] **AC-0011.** A `would-companion` row names the companion path
      `safety.companion_path` computes for that path.
- [x] **AC-0012.** Every value this command renders that it did not itself
      author — whatever its origin: the recorded state, a remote document, or a
      source-tree entry name, including the rendered source URI and a
      descriptor's `artifact` URL — passes the bounded terminal-safe scalar
      check before it reaches stdout, stderr, or the `--format json` document. A
      value that fails is reported by field name and reason, without the value.
- [x] **AC-0013.** The command's exit code is the first matching row of this
      table, read top to bottom, and no input produces a code outside it:

      | Invocation | Condition | Code and name |
      | --- | --- | --- |
      | any | the invocation is malformed, including an omitted `--source`, neither or both of `--dry-run` and `--check`, or `--compare-tree` without `--check` | 2 — `malformed` |
      | any | the source could not be resolved or its integrity could not be verified | 3 — `cannot-answer` |
      | `--dry-run` | no recorded selection is derivable | 3 — `cannot-answer` |
      | `--dry-run` or `--check --compare-tree` | the recorded-path container is not an array, so the recorded path set cannot be interpreted | 3 — `cannot-answer` |
      | `--dry-run` | the identity leak check reported a violation | 1 — `difference` |
      | `--dry-run` | a selected pack's adapter-contract major differs from the CLI's | 1 — `difference` |
      | `--dry-run` | a plan was printed, whatever its counts | 0 — `success` |
      | `--check`, no `--compare-tree` | the resolved source affords no verified digest | 3 — `cannot-answer` |
      | `--check`, no `--compare-tree` | the recorded `archive_sha256` is absent, or is not a 64-character lowercase hex string | 3 — `cannot-answer` |
      | `--check`, no `--compare-tree` | the recorded digest equals the resolved source's verified digest | 0 — `success` |
      | `--check`, no `--compare-tree` | the recorded digest differs from it | 1 — `difference` |
      | `--check --compare-tree` | the recorded path set is empty, or any recorded path could not be compared | 3 — `cannot-answer` |
      | `--check --compare-tree` | every recorded path was compared and none differs | 0 — `success` |
      | `--check --compare-tree` | every recorded path was compared and some differ | 1 — `difference` |

- [x] **AC-0014.** Every invocation and every source, state, or comparison
      failure reaches a named row of AC-0013 at the command boundary; no
      uncaught exception or traceback determines the process exit status.
- [x] **AC-0015.** A recursive non-dereferencing walk of the target tree —
      every relative path, its entry kind, its mode, the link target for a
      symlink, and the bytes for a regular file only — records the same result
      before and after the command, on every row of AC-0013's table. Hard-link
      counts, extended attributes, and timestamps are outside this oracle by
      decision.
- [x] **AC-0016.** A `--dry-run` reports `would-update`, `would-companion`,
      `untouched`, `would-remove`, the schema-1 inert-entry count, the
      compared-path count, and the uncompared-path count; `--format json`
      reports the same seven under a `summary` object; and
      `compared + uncompared` equals the length of the `managed_paths` array as
      the state document carries it, before any filtering. A recorded entry is
      compared when the run reached a decided verdict for it and uncompared
      otherwise; every entry that leaves the pipeline for any reason, including
      a malformed entry or an unrenderable value, is uncompared. An entry is in
      the schema-1 inert count exactly when it is recorded with `sha256: null`
      and present on disk; it appears in no verdict count, and the report tells
      the adopter to regenerate schema-3 ownership state with hashes before
      retrying sync.
- [x] **AC-0017.** Every recorded path that leaves `would-remove` is reported
      with a reason, the reasons are pairwise distinguishable, and their number
      equals the number of decline branches the plan's § Grounding derivation
      reports from the post-change removal guard at verification time. The
      confinement refusal and the unreadable entry are undecided; every other
      decline reason is decided, and AC-0013's "could not be compared" means
      that fixed undecided set. Each post-change decline branch has an
      independent fixture pinned to its reason token, so deleting a branch
      fails even when the derived branch count also shrinks.
- [x] **AC-0018.** A source declaring a `[pack] version` or
      `[pack.adapter-contract] version` differing from the derived tree's own
      copy of that pack's manifest, or a `[pack.dependencies] required` or
      `conflicts` edge violated against the replay's resolved pack selection,
      produces one advisory row per signal and does not change the exit code the
      same run produces with that signal absent.
- [x] **AC-0019.** Given a pack whose `[pack.adapter-contract] version`
      declares a major component differing from the CLI's `SPEC_VERSION` major,
      `sync` refuses with the existing uniform-refusal message and returns
      AC-0013's difference code.
- [x] **AC-0020.** For each recorded path that is hard-linked, non-regular, or
      a reparse point, the applicable `agentbundle.catalogue_tooling.file_safety`
      confinement helper refuses the read or hash before comparison; an inline
      lexical-prefix check does not satisfy this criterion.
- [x] **AC-0021.** The catalogue subcommands `docs/architecture/agentbundle.md`
      § 2 Entrypoints names equal the direct children of the `catalogue`
      subparser, derived by the command the plan's § Grounding names. The verbs
      nested under `contracts` are out of scope.
- [x] **AC-0022.** Every line citation in `initialise_self_hosted.py` that the
      plan's § Grounding derivation reports in a file this change edits resolves
      to the construct its sentence describes, with no unresolved residual
      inside that scope.
- [x] **AC-0023.** `upstream-sync.md` states this phase's rollout status
      consistently: its STATUS banner says phase 2 is delivered, § Rollout
      marks phase 2 done, and the phase summary says two phases remain.
- [x] **AC-0024.** `upstream-sync.md` § Granularity records that this phase
      shipped its guides replay mode under a different name so `--guides` stays
      free for the restrictor.
- [x] **AC-0025.** `derived-catalogue.md` § What a re-run does today describes
      the recorded recipe `init` reads back, rather than its absence.
- [x] **AC-0026.** `guides/_shared/how-to/create-a-self-hosted-catalogue.md`
      names `agentbundle catalogue sync`, both `--dry-run` and `--check`, that
      neither writes to the tree, and that the plan names the upstream source
      only under `attributed`; the authored-source site link gate passes over
      the edited guide; and, after the plan's § Grounding regeneration command
      rebuilds the projected site, the rendered-links checker passes over that
      regenerated tree.
- [x] **AC-0027.** The version string in
      `packages/agentbundle/agentbundle/version.py` is `0.47.0`, and every
      surface the plan's § Grounding release-surface derivation names carries
      that same value.
- [x] **AC-0028.** `packages/AGENTS.local.md` states which source yields on the
      stub-marker conflict and why.
- [x] **AC-0029.** Every criterion-ordinal label under
      `packages/agentbundle/tests/` is a bare ordinal carrying no path or
      section reference.

## Follow-ons

- **The apply path** — replacing the unconditional overwrite and the `CONFLICT`
  abort in `init_self_hosted`'s write block with the Tier verdicts this phase
  reports, and writing the pin. Owner: phase 3 of
  [`upstream-sync.md`](../../architecture/catalogue/upstream-sync.md) § Rollout.
- **The scoping flags** — `--pack`, `--profile`, `--package`, and `--guides` as
  § Granularity's restrictor, whose name this phase deliberately vacates.
  Owner: phase 3 of the same rollout.
- **Package sync** — both `packages/` subtrees a derived catalogue can carry.
  Owner: phase 4 of the same rollout.
- **Exposing a resolved ref from the resolver** — `git+https://` affords a ref
  that `_resolve_https` computes and discards. It first matters when a pin is
  written. Owner: phase 3 of the same rollout.
- **A repository-wide citation lint** — the resolve-to-construct property is
  desirable for every citation, not only the ones this change edits, but it is
  not mechanisable at repo scope: a bare `` `:NNNN` `` inherits its filename
  from a preceding sentence, which no line-oriented pattern resolves. The
  § Grounding citation derivation records the unresolved residual outside this
  change's scope. Owner: unassigned; raised by the adversarial pass.
- **Phase 1's AC-0020 overclaims its own scope** — it states its read-time
  rejection "applies to every field" while its own Assumptions and the shipped
  code scope it to the replay-eligible values. An erratum against a `Shipped`
  spec, not taken here (user confirmation 2026-09-17). Owner: unassigned.
- **A read-time constraint on the recorded mode fields and the pin** —
  `attribution`, `tooling`, `guides`, and `SelfHostPin`'s three fields are
  recorded as unconstrained text. This phase bounds them at the sink under
  AC-0012 and validates the digest's shape under AC-0013, but a read-time
  validator would bound the class. Owner: unassigned; raised by the
  secure-design pass.
- **A scanner rule for unbounded rendered values** — no rule in this repository
  detects a value reaching stdout without passing the terminal-safe check, so
  AC-0012's class is enforced by review rather than mechanically. A Semgrep rule
  anchored on the plan-rendering sink would catch it. Owner: unassigned; raised
  by the secure-design pass.
- **A ceiling on the recorded path set and the total bytes hashed** —
  `_OWNERSHIP_STATE_MAX_BYTES` caps the state document at 4 MiB, but nothing
  caps the entry count or the bytes those entries cause to be hashed, and
  `sha256_confined_regular_file` takes no byte budget where its sibling
  `read_confined_regular_file` does. A state repeating one large path admits
  unbounded hashing of a local, interruptible read-only command. An over-budget
  state would route to AC-0013's cannot-answer code. The ceiling values are the
  owner's call. Owner: unassigned; raised by the secure-design pass.
- **A discriminator for the two refusal conditions sharing exit 1** — an
  identity-leak refusal and an adapter-contract refusal both return
  `1 — difference` under AC-0013, and AC-0016 pins no condition field, so a JSON
  consumer cannot tell them apart. The required outcome is that a consumer can
  distinguish them on the machine surface; the field's shape and which rows
  carry it are the owner's call inside § Ask first's four-code limit. Owner:
  unassigned; raised by the secure-design pass.
- **`--check --compare-tree` resolves a source it does not read** — AC-0013
  makes an omitted `--source` malformed for every invocation, yet all three
  `--compare-tree` rows have antecedents reading only the recorded path set and
  the on-disk tree, so a network fetch and an archive extraction are performed
  for a local-only answer. The owner decides whether this form must supply a
  source, whether it must resolve one, or neither — keeping the flag
  syntactically required while not resolving it is a third route, and the
  cheapest — and must record the security-relevant reason for any resolution it
  retains. AC-0013's table is unchanged in this phase. Owner: unassigned;
  raised by the secure-design pass.
- **Extending the no-write walk to a local-path source** — AC-0015's
  before-and-after walk observes the target only, so with `--source` given as a
  local filesystem path no oracle observes the source tree. A future accepted
  change must prove the local source tree is unchanged before and after every
  local-source run; the snapshot mechanism, and whether to admit this follow-on
  at all, are the owner's call. This phase has no write path, so the gap is a
  missing net rather than a reachable write, and the work stays outside it. The
  walk helper the plan establishes is the seam. Owner: unassigned; raised by the
  secure-design pass.

## Assumptions

Every measured value below cites the derivation that produces it. The plan's
§ Grounding holds the commands; no measured value is restated in a second prose
home.

- Technical: runtime is Python >=3.11 (`packages/agentbundle/pyproject.toml`).
- Technical: the bounded terminal-safe scalar check AC-0012 names is phase 1's
  `_is_safe_recipe_text`, and it admits every value kind this command renders
  while rejecting each one's hostile variant. Established by the sink-class
  probe in § Grounding over the recorded `schema_version`, the descriptor's
  `source_revision` in tag and SHA forms, the recorded `archive_sha256`, a
  recorded `managed_paths[].path`, a source-derived planned path, a companion
  path, a `[pack] version`, an adapter-contract version, a dependency edge name,
  the rendered source URI, and the descriptor's `artifact` URL. The same probe
  owns the non-string and length-bound cases rather than restating their results
  here.
- Technical: `safety.classify` accepts a `State` synthesised from
  `managed_paths` and returns every Tier verdict AC-0010's table names. For a
  `sha256: null` entry it returns Tier-2 only when the path is present on disk;
  an absent path returns Tier-1 before the digest is consulted. Established by
  the Tier probe in § Grounding.
- Technical: the null entry is recorded as `{}` rather than `{"sha": None}`
  because the latter is a type lie, not because a gate rejects it. Both shapes
  type-check and, when the path is present on disk, both reach Tier-2: the root
  mypy config sets
  `no_strict_optional = true`, so `None` is assignable to `str`, and
  `entry.get("sha256")` yields `Any` regardless. The claim that `{"sha": None}`
  reds `make lint-mypy` is refuted by the shape probe in § Grounding.
- Technical: the removal guard's decline branches, how many emit a reason, and
  which are silent are derived by the decline-branch generator in § Grounding
  rather than counted by hand, which is why AC-0017 compares against the
  derivation.
- Technical: `resolve_catalogue()` returns a bare `Path` and discards
  provenance, so a digest reaches `sync` only through
  `fetch_catalogue_archive_with_provenance`, whose caller owns cleanup of
  `result.path`.
- Technical: the two digest-bearing forms differ in whose word the digest rests
  on, which is why AC-0001 gives them separate tokens. `archive+https://` takes
  the expected digest from the adopter's own URI fragment and refuses before any
  fetch when the fragment is absent; `catalogue+https://` reads
  `descriptor["sha256"]` from the document the same origin serves. Established
  by the digest-provenance probe in § Grounding, which needs no network.
- Technical: `init_self_hosted` steps 1 through 9 are already write-free and end
  at the in-memory leak check, whose temporary directory sits outside the target.
- Technical: phase 1's read-time handling reaches the six identity scalars its
  `validators` dict names plus `preferred_adapter`, `packs`, and `profiles`, and
  nothing else — `_is_safe_recipe_text` has exactly four call sites, and no
  reader of the recorded `attribution`, `tooling`, or `guides` exists. AC-0012
  is therefore a new control rather than a restatement.
- Technical: `SelfHostOwnershipState` records no pack versions, so AC-0018's
  baseline is the derived tree's own copied `packs/<name>/pack.toml`, which
  exists because `init` copies each selected pack wholesale.
- Technical: `init` has no Tier verdict. Its classifier is `classify_conflicts`,
  and neither `initialise.py` nor `initialise_self_hosted.py` imports
  `agentbundle.safety`; the live callers of `safety.classify` are in
  `commands/upgrade.py`, with `install` running a documented carve-out.
- Technical: `check_spec_version_gate` compares major components only, and every
  declaring pack in this repository declares major `0`, so AC-0019 needs a
  crafted fixture to be able to fail.
- Technical: `.claude/skills/**` is a tracked projection of
  `packs/core/.apm/skills/**`, byte-identical for the files this work reads.
  Phase 2 edits no skill, so no skill regeneration is owed.
- Technical: the guide AC-0026 edits is projected into the docs site, and the
  two site gates read different representations — the entry-link gate reads
  authored sources by design and runs on every pull request, while the
  rendered-links checker reads the generated HTML tree and raises rather than
  passing when that tree is unsafe. § Grounding names both and the regenerating
  command.
- Process: a new public CLI verb is a release-coupling trigger; the target is
  the version AC-0027 fixes (user confirmation 2026-09-17).
- Process: a change under `packages/agentbundle/agentbundle/` needs an
  `Engine-Change-RFC:` footer; phase 1 used `RFC-0059`.
- Process: the stub-marker conflict between `docs/CONVENTIONS.md` and
  `packages/AGENTS.local.md` is resolved at the scoped rule's owner by exempting
  a bare criterion ordinal in a test comment, which three suites already carry
  (user confirmation 2026-09-17).
- Process: a repository-level assertion cannot live in
  `packages/agentbundle/tests/`, which ships inside the sdist, so AC-0021,
  AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028, and AC-0029
  are delivery-time checks rather than package tests.
- Process: the roster suite has no pull-request trigger, so the Durable Outputs
  row that closes on it names the dispatch act.
- Process: this spec is registered in `["ini-007".work].queue` (user
  confirmation 2026-09-17). The phase order stays in `upstream-sync.md`
  § Rollout.
- Process: `--check` refuses on a digest-free pin rather than reporting an
  unmeasured zero, and `--compare-tree` answers without one; guides selection
  ships under a name that leaves `--guides` free; the plan names the source only
  under `attributed`; and `derived-catalogue.md`'s stale citations and false
  recipe claim are corrected here (user confirmations 2026-09-17).
- Product: the beneficiary is the adopter of a derived catalogue who needs to
  see what a sync would do before any phase can apply it. No canonical local
  source records this; phase 1 carried the same assumption.
- Product: no usage signal exists for `--compare-tree`. The reachable corpus is
  one derived-catalogue shape rather than observed adopter behaviour.
