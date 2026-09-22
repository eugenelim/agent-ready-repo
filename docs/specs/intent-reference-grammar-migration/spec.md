# Spec: Cross-artifact reference grammar and pointer migration

- **Status:** Implementing
- **Owner:** eugenelim
- **Mode:** full
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0033; ADR-0108; ADR-0112; RFC-0103
- **Brief:** docs/product/briefs/intent-identity-and-registration.md
- **Discovery:** docs/product/intents/FEAT-0001-intent-identity-and-registration.md
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

An author or agent writing a pointer between two repository artifacts names
exactly one artifact, and a reader resolving that pointer reaches it or is told
the name is ambiguous. Success is that no resolution step chooses among
candidates on the author's behalf.

## What Changes

- Canonical pointer form becomes `<kind>:<slug>` — the `Parent intent:` and
  `Brief:` fields of every artifact that carries one
- Ambiguity refusal replaces sort-order selection — `resolve_endpoint` in
  `lint-traceability.py`
- `intent:` becomes a recognized graph node kind — the intent files under
  `docs/product/intents/` that no ladder rung already claims
- The canonical `Brief:` form moves from a repository-relative path to
  `brief:<slug>` — five surfaces that state or stamp the old form
  (`guides/core/reference/product-brief-fields.md`,
  `guides/core/how-to/write-the-contract.md`, the `new-spec` spec template,
  `new-spec`'s `references/spec-and-plan-contract.md`, and
  `author-delivery-brief`'s `SKILL.md`), plus `lint-brief-coverage.py`'s join
  and the dispatch provenance check in `workspace-status`'s
  `workspace_status_engine.py`
- Slug identity becomes the `Slug:` field value rather than a filename stem —
  node-id derivation for every `intent:` node
- A locally-resolving producer pointer outranks an earlier external-only one —
  `_wire_up`'s candidate preference

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — the change supersedes an accepted convention, so the grammar needs a record an adopter can cite | `docs/rfc/<ordinal>-cross-artifact-reference-grammar.md` | repository decision process | Accepted RFC naming the grammar, the `intent:` kind, and the superseded `Brief:` path pin | The RFC is `Accepted` and this spec's `Constrained by:` cites its assigned ordinal |
| Interface compatibility | Applicable — `Brief:` is a field adopters write by hand and three scripts read, one of them on the dispatch path | `guides/core/reference/product-brief-fields.md`; `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` (source; three copies are projections) | maintainer | The field row states `brief:<slug>` and what still accepts the path form; the dispatch provenance check admits the typed form and still refuses an unrecognized one | The guide, the shipped template, the two stamping skills, and both readers agree on one form |
| Maintainer procedure | Applicable — the template is what stamps the field on every new spec | `new-spec` `assets/spec.md` and its two projections | maintainer | `make build-self` reprojects all three copies identically | The three copies are byte-identical |
| Current architecture | Applicable — the resolver's endpoint states are the contract other checks read | `lint-traceability.py` module docstring and `resolve_endpoint`'s docstring | maintainer | The docstring enumerates the refusal state alongside the existing three | The docstring names every state the function returns |
| Reusable learning | Applicable — the collision count differs from the brief's by measurement method, which is the trap a later slice repeats | `docs/product/briefs/intent-identity-and-registration.md` erratum | shaping owner | An erratum recording that slug identity is the `Slug:` field, not the filename stem, and the corrected count | The brief states the method its count depends on |
| Release history | Applicable — the grammar is a published convention adopters follow | the repository changelog | maintainer | One entry naming the new canonical form and the retained fallback | The entry names the fallback, not only the new form |
| User promise | Not applicable — no end-user-facing surface changes; the audience is authors and agents inside the repository | — | — | — | — |
| Operations | Not applicable — no runtime, deployment, or monitored surface changes | — | — | — | — |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Derive the migration cohort from the corpus at run time, so a pointer added
  between authoring and execution is swept too.
- Edit `packs/core/.apm/` as the source and reproject with `make build-self`.
  This governs every script in this change, not only `lint-traceability.py`:
  `workspace_status_engine.py` also has a pack source and three byte-identical
  copies, one of which is `packages/agentbundle/agentbundle/_data/`. Confirm a
  file is the source, not a projection, before editing it.
- Derive a node's slug from its `Slug:` field, falling back to the directory
  name for a spec, and never from a filename stem.
- Re-run the corpus measurement after each resolver change and record the
  node, edge, and exit-code deltas in the verification ledger.

### Ask first

- Widening the cohort past `Parent intent:` and `Brief:` to `Contract:` or
  `Discovery:`.
- Repairing any `Contract:` value whose target path is already missing. No count
  is given: the figure of eight recorded in an earlier revision did not
  reproduce, and a rule keyed to a wrong count either over- or under-applies.
- Changing which endpoint state a path-shaped value resolves to.

### Never do

- Add a module, top-level directory, abstraction layer, or dependency; the
  change lands inside the existing scripts and guides.
- Resolve an ambiguous bare slug by any tiebreak — sort order, kind priority,
  recency, or the shortest candidate.
- Accept an ordinal, or an ordinal-prefixed filename stem, as a pointer value.
- Widen the dispatch provenance check to admit a `Brief:` value that is neither
  the typed form nor a canonical local brief path. Admitting the typed form is
  the change; weakening the refusal is not.
- Sweep a pointer value whose target the corpus cannot resolve; leave it and
  report it.
- Add a new top-level file for the corpus probe. It belongs beside this spec's
  other working material, under
  `docs/specs/intent-reference-grammar-migration/notes/`, which the `Never do`
  rule against new modules does not reach because it adds no importable unit to
  a package.
- Run `tests/roster/` locally; dispatch it on CI.

## Testing Strategy

- **Resolution behaviour (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005):** TDD.
  Canonical resolution, unique bare-slug fallback, ambiguity refusal, ordinal
  refusal, and the exit code they produce are all functions of a target and a
  node-id set, which is the compressible invariant TDD is for. The unit surface
  is `resolve_endpoint` directly, which no test among the existing 48 reaches.
- **Node recognition (AC-0006, AC-0007):** TDD. Recognition is a derivation
  from a directory of files to a set of ids, and id uniqueness is a property of
  that set, so a fixture corpus decides both. They share a group because the
  same derivation produces both outcomes.
- **Surface derivation (AC-0019, AC-0020, AC-0021):** goal-based check. The
  outcome is a committed inventory plus a zero-diff re-run, so the command is
  the test. It is derived by behaviour — resolving each field's readers through
  the functions that consume it, and each writer by the form it emits — because
  the three surfaces this delivery missed (a generic preamble parser, a
  four-copy projection set, and fifteen templates that emit the form without
  reading it) are each invisible to a search for the field's name. AC-0021 is a
  one-line assertion over the brief corpus rather than a fixture, because the
  property it pins is a fact about real files.
- **Corpus sweep completeness (AC-0008):** goal-based check. The outcome is an
  absence over the whole repository, so a command that re-derives the cohort
  and reports a non-empty remainder proves it where an example-based test
  cannot. The remainder predicate is "not `<kind>:<slug>`", not "still the
  shape this field started from" — the second admits the four markdown-link
  `Parent intent:` values, which are neither typed nor bare.
- **Field-form agreement (AC-0009, AC-0010):** goal-based check for the
  agreement between the guide, the template, the two skill instructions that
  stamp the field, and the coverage join; and TDD for the join itself, whose
  implementation is separate from `resolve_endpoint` and which a green
  traceability suite therefore does not cover.
- **Dispatch acceptance and its refusals (AC-0016, AC-0017, AC-0018):** TDD.
  `workspace_status_engine.py` reads the `Brief:` header through a generic
  preamble parser (`_parse_preamble_fields`), lands it in the artifact's
  provenance parent, and validates it as a canonical local brief path, so the
  typed form has to be admitted there explicitly. A string search for `Brief` in
  that module does not reach this code, which is why the criteria name the
  behaviour rather than a line.

  The three criteria are separate because they fail independently and a single
  happy-path test would satisfy none of the other two. AC-0016 drives the real
  validation entry point with the typed form and the surviving path form.
  AC-0017 walks the malformed set case by case — empty, over-length, separator,
  traversal, backslash, control byte, non-ASCII, bare slug — because "admits the
  typed form" is also true of an implementation that admits everything. AC-0018
  drives the shared helper's other call sites with the same values, since the
  helper guards `workspace.toml` paths where a slug is meaningless; the design
  keeps it unchanged by normalizing at the provenance read, and that test is
  what detects a repair that instead widened the helper.
- **Producer-candidate preference (AC-0013):** TDD. A consumer carrying one
  pointer that resolves local and an earlier one that resolves only to an
  external reference is a two-candidate fixture, and the outcome is which id
  the in-edge carries — a predicate over the built edge set.
- **Absent-field handling (AC-0014, AC-0015):** TDD. A fixture file with the
  field removed decides both, and they are separate criteria because the report
  and the node-set absence fail independently: an implementation can emit the
  report and still contribute a stem-keyed node. No corpus input reaches this
  case today, which is why it needs a fixture rather than a corpus check.
- **Projection consistency (AC-0011):** goal-based check. A byte comparison
  across the three copies is the whole test; there is no behaviour to drive.
- **The lint's behaviour on the real repository (AC-0012):** visual / manual
  QA, exercised end to end. `lint-traceability` is a command a maintainer runs,
  so the evidence is its actual stdout, stderr, and exit code over the
  repository rather than a unit gate standing in for them.

## Acceptance Criteria

- [ ] **AC-0001.** A pointer value equal to a node id resolves to that node and
      no other.
- [ ] **AC-0002.** A bare slug matching exactly one node id resolves to that
      node.
- [ ] **AC-0003.** A bare slug matching more than one node id refuses, and the
      report names the value together with every matching candidate.
- [ ] **AC-0004.** A refused ambiguous pointer makes `lint-traceability` exit
      non-zero in both members of the closed set of its exit-affecting
      invocation modes: default and `--strict`.
- [ ] **AC-0005.** A pointer value that is an ordinal, or a filename stem
      carrying an ordinal prefix, refuses.
- [ ] **AC-0006.** Every file under `docs/product/intents/` that no ladder rung
      already recognizes **and that carries a `Slug:` field** is a node whose id
      is `intent:` joined to that field's value. The `Slug:`-bearing condition is
      what keeps this from contradicting the absent-field criteria below, which
      require such a file to contribute no node.
- [ ] **AC-0007.** No two nodes share an id.
- [ ] **AC-0008.** Re-deriving the cohort over the repository reports that every
      resolvable value in both migrated fields is `<kind>:<slug>` — not merely
      that the shape each field started from is gone. The corpus holds 23
      builder-visible `Parent intent:` values, of which 19 are bare slugs and 4
      are markdown links; a criterion naming only the bare-slug shape would
      leave those 4 in place and still pass. A value the corpus cannot resolve
      is reported and left, per the Agent Rules.
- [ ] **AC-0019.** A committed derivation produces, for **each of the four
      pointer fields** — not only the two this spec migrates — the closed
      inventory of surfaces that touch it, each labelled by role — writes
      the form, states the form as guidance, reads the value, or is a generated
      copy of something that does. It is derived by behaviour rather than by
      searching for the field's name, because a generic preamble parser, a
      projection, and a template that emits the form without reading it are all
      invisible to a name search and all three were missed that way. The
      derivation re-runs with a zero diff.
- [ ] **AC-0009.** Every surface the AC-0019 inventory labels as writing or
      stating the `Brief:` form names `brief:<slug>` as canonical, and every
      surface it labels as reading the value accepts it. The criterion is
      discharged against the derived inventory and names no count or file list
      of its own — an inline list is what three earlier revisions got wrong,
      each stating a total that the next round falsified.
- [ ] **AC-0023.** The migration cohort is derived *after* the intent files are
      recognized as nodes, because recognizing them makes their own
      `Parent intent:` pointers builder-visible. 14 of the 117 carry one, taking
      the cohort from 23 values to 37; a sweep sized against the pre-recognition
      figure leaves 14 values untyped and still passes a check that counts only
      what was visible before.
- [ ] **AC-0020.** Every surface the AC-0019 inventory labels as writing or
      stating the `Parent intent:` form emits `<kind>:<slug>`. Without this the
      sweep does not converge: the inventory finds templates and guides that
      stamp a bare slug, so swept values would be re-emitted in the old form by
      the next author who used one.
- [ ] **AC-0021.** Each brief's identity, as the brief recognizer derives it,
      equals its filename stem — the condition that makes `brief:<slug>`
      resolvable to `docs/product/briefs/<slug>.md`. It holds for all 17 briefs
      today; it is asserted because nothing enforces it and the typed form
      silently misresolves where it fails.
- [ ] **AC-0010.** `lint-brief-coverage.py` rolls a brief's Spec map up from
      specs whose `Brief:` value is `brief:<slug>`.
- [ ] **AC-0011.** `lint-traceability.py` is byte-identical across its
      `packs/core/.apm/`, `.agents/`, and `.claude/` copies.
- [ ] **AC-0012.** `python packs/core/.apm/skills/work-loop/scripts/lint-traceability.py
      --root . --strict` exits 0 over the repository.
- [ ] **AC-0013.** A producer pointer resolving to a local node takes the
      consumer's in-edge in preference to an earlier producer pointer that
      resolves only to an external reference.
- [ ] **AC-0014.** An intent file carrying no `Slug:` field is reported.
- [ ] **AC-0015.** An intent file carrying no `Slug:` field contributes no
      node.
- [ ] **AC-0024.** `Brief:` remains optional. An omitted header, a blank value,
      the template's HTML comment, and `none` all mean "no brief", produce no
      provenance finding, and are outside AC-0016's and AC-0017's scope, which
      govern only a non-placeholder value. Without this the two-form predicate
      would refuse every spec that legitimately has no brief — a far larger
      blast radius than the migration itself.
- [ ] **AC-0016.** A spec's **non-placeholder** `Brief:` value is admitted by
      `workspace_status_engine.py` in exactly two forms: `brief:<slug>` where
      `<slug>` matches the repository's existing single-segment identifier rule
      — one to two hundred characters, ASCII alphanumeric, hyphen or underscore,
      beginning alphanumeric — and the repository-relative path form
      `docs/product/briefs/<slug>.md`, whose `<slug>` satisfies that same rule.
      Both admitted forms also satisfy AC-0022. The set is defined positively
      and self-containedly; "the form it accepts today" would be a predicate
      that moves with the implementation being judged.
- [ ] **AC-0017.** Every **non-placeholder** `Brief:` value outside the two
      admitted forms produces
      a provenance finding and blocks dispatch. This is asserted as the
      complement of AC-0016's predicate, not as a list of bad examples: an
      enumerated list of malformed cases cannot converge, since any finite list
      omits something — a space, `!`, `%`, a second colon — and an
      implementation admitting every `brief:`-prefixed string would still pass
      it. Representative cases are exercised as evidence, not as the criterion.
- [ ] **AC-0022.** Acceptance of a `Brief:` value requires its target, once
      canonicalized with symlinks resolved, to remain beneath the resolved
      `docs/product/briefs/` directory. That is the single boundary, and it sits
      strictly inside the repository root, so a target escaping the briefs
      directory is refused whether it lands elsewhere in the repository or
      outside it. A lexical check on the slug does not satisfy this: a slug
      naming a symlink is lexically valid.
- [ ] **AC-0018.** Admitting the typed form at spec provenance changes no other
      consumer of the shared brief-path rule: at each of its other call sites —
      `workspace.toml` entry, dependency, legacy-queue and receipt paths — a
      typed value and a malformed `brief:` value both remain invalid.

## Follow-ons

- eugenelim: recorded in `notes/verification-ledger.md` § Follow-ons until a
  `work-intake` record exists — migrate the 38 `Contract:` and 25 `Discovery:`
  values to the grammar this spec establishes. RFC-0103 deliberately leaves
  those two fields ungoverned — `Contract:` ids carry a version and some
  `Discovery:` targets have no registered kind at all — so their migration needs
  the later decision RFC-0103 names, not only an implementation spec. They are
  also out of this cohort because some `Contract:` paths are already broken and
  repairing them is separable work.
- eugenelim: same record — `Contract:` values whose target path does not exist.
  `_CROSSREPO_RE` classifies any value containing `/` as a cross-repo shape, so
  these report `unresolvable` rather than `dangling` and are invisible today.
  The count of eight recorded in an earlier revision did not reproduce under any
  stated method and is withdrawn; T0's inventory supplies the real figure.
- eugenelim: same record — `author-delivery-brief`'s `continue`-mode stamping
  instruction, if the template change does not already reach it.

## Assumptions

- Technical: whether attaching the 34 newly local `Brief:` edges changes
  `lint-traceability`'s orphan, reachability, or cycle verdict — it changes
  which tasks the plan's sweep task must also repair (settled by: running the
  changed resolver over the corpus, which is a plan task)
