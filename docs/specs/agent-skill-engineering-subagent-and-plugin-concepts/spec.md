# Spec: Agent Skill Engineering Subagent and Plugin Concepts

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`RFC-0097`](../../rfc/0097-agent-skill-engineering.md), including
  its 2026-09-01 § *Errata* narrowing of D3 and its 2026-09-04 § *Errata*
  runtime-profile de-scope;
  [`Agent Skill Engineering Composition Floors`](../agent-skill-engineering-composition-floors/spec.md)
- **Brief:** docs/product/briefs/agent-skill-engineering.md
- **Discovery:** none
- **Contract:** none. This slice touches no provider seam. The router's per-claim
  state reporting and the provider response-contract change it needs belong to
  the `3c-r` row in this spec's brief, which depends on this slice.
- **Shape:** mixed

> **Hard dependency.** The composition-floors slice is Shipped. These concepts
> live on the topics it admitted; the taxonomy carries no leaf of its own for
> them.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A skill author deciding whether to hand work to an isolated worker, or whether to
distribute a set of components as one installable package, gets the concepts that
decision needs from the pack's governed corpus — without being routed to a
runtime profile that does not exist. The corpus states the delegation boundary in
both directions, so an author knows what a worker receives and what does not come
back from it; it states the four things the Agent Plugins v1 portable core fixes
for every conforming client, so packaging guidance stands on the specification
rather than on a per-vendor matrix; and it keeps the one runtime divergence that changes an
authoring decision — where Claude Code reads a plugin manifest — in the runtime
profile that owns dated runtime facts. That profile teaches the concepts in the
vocabulary this audience actually writes, naming Claude Code's own component
surfaces, while the portable floors stay vendor-neutral. Taxonomy leaves with no committed
delivery owner say so, with an admission condition a contributor can satisfy on
their own.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | The README's knowledge-grounding paragraph is the pack's own account of what the floors cover and what stays absent | `packs/agent-skill-engineering/README.md` | this spec | Governed-topic count agreement test, and the shipped-surface absence-claim scan | README describes the floors' plugin-core content and asserts no later-slice runtime profile |
| Current product truth | Editing any topic body moves the compiled source digest, so both recorded retrieval runs are re-measured against the tree they describe | `packs/agent-skill-engineering/tests/fixtures/` | this spec | Re-recorded router and generic-negative runs, each binding every digest its assertions require to the edited tree | Every digest in both recorded runs matches the tree and case fixture it names |
| Current architecture | The planned architecture document is the repository's account of which slice-3 surfaces exist and which runtime profiles are committed | `docs/architecture/agent-skill-engineering.md` | this spec | Section states which slice-3 surfaces exist, which are retired to open extension, and where the claim-state obligation sits | Document names no committed profile beyond Claude Code |
| Decision rationale | No new decision is taken. The de-scope and the D3 narrowing are already Approver-signed in RFC-0097 § *Errata*, and this slice implements them | RFC-0097 § *Errata* (existing) | RFC-0097 owner | Citation from this spec's `Constrained by` header | No new ADR or RFC is required, and this spec cites the erratum it implements |
| Spec index | The active-spec table carries one row per spec with its shape and AC/task counts | `docs/specs/README.md` | this spec | Row matches the shipped spec | Row states the shipped shape and the final AC and task counts |
| Release history | Pack content changes for installers, with no new primitive | `docs/product/changelog.md`, `packs/agent-skill-engineering/pack.toml`, `packs/agent-skill-engineering/.claude-plugin/plugin.json` | this spec | Matching patch bump in both manifests; topmost pack changelog entry | Both manifests carry the same new patch version and one changelog entry leads the pack's history |
| Maintainer procedure | `none`. Both candidate facts already have owners: AC9 puts the admission condition a later contributor needs into the corpus register itself, and the re-measurement obligation belongs to `test_foundation_corpus.py`'s two recorded-run digest assertions rather than to prose. A separate procedure document would be a second home for both | — | — | — | — |
| Execution evidence | Re-measurement, any inherited-pin re-take with prior and current values, the guard-narrowing rationale, each observed mutation, and the named reviewer's readings are all produced by execution | `notes/verification-ledger.md`, the destination `docs/CONVENTIONS.md` assigns | this spec | Ledger entries naming each gesture, each moved pin, each observed mutation, and each reviewer reading | Every task that closes on a ledger record has one, carrying the gate results that admitted it |
| Reusable learning | Capture gates fire at `spec-approved` and `plan-locked` | `project-knowledge` producer profile | work-loop | Capture receipts, or a recorded unavailability | Receipts exist or `project-knowledge unavailable` is recorded |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Record every operative external claim with its source identity as the URL that
  served the content after every redirect, the date it was retrieved, and the
  version or last-updated date that source exposed, or the literal
  `none exposed`.
- Keep specification-fixed behavior in a portable floor and dated runtime
  behavior in the runtime profile, following RFC-0097's 2026-09-01 narrowed
  charter.
- Re-measure both recorded retrieval runs in the same change that edits any
  topic body, so no recorded result describes a tree that no longer exists.
- State a divergence only where it changes an authoring decision, and state the
  decision it changes.

### Ask first

- Admitting, retiring, or renaming a taxonomy leaf, or changing the leaf count
  the topology fixture declares.
- Making any authoring mode available that the unsupported-mode fixture records
  as unavailable.
- Editing a frozen shipped spec's body or a ticked acceptance criterion, in this
  programme or another.
- Adding a claim group whose basis is `doctrine` on the strength of a single
  runtime's documentation.

### Never do

- Never add a top-level directory, a pack, a package dependency, or a new module
  boundary.
- Never cite this catalogue's internal records, acceptance criteria, commit
  identifiers, or repository-only paths inside `packs/`; state the rule directly.
- Never describe a capability as verified without either a passing probe or a
  first-party source carrying a retrieval date.
- Never change the provider response contract, the router's response fields, or
  any provider case fixture. That surface belongs to the `3c-r` row.
- Never restate a rule the corpus-admission suite already enforces as an
  acceptance criterion here.

## Testing Strategy

Most outcomes below are containment or absence predicates over governed source
and recorded evidence, and those are **goal-based checks**. One is not: the
portability guard is a predicate with a compressible invariant — admit the
specification's filename, flag a runtime-owned one — so it is **TDD**. Its
admitting direction is driven red-first before the predicate changes. Its
flagging direction cannot earn red there, because the base predicate already
flags both filenames, so that specimen ships as an erosion control proved by its
own mutation rather than by a manufactured red. No outcome is visual or manual
QA, because the slice has no user interface.

The design constraint that shapes every mode below: prose is authored, so a
criterion that only names a semantic outcome lets the author choose the words the
check then looks for, and the artifact grades itself. Each content criterion
therefore fixes the value its check compares against — the specification's
normative literal, the exact sentence that must be gone, or the direction an
answer must take.

That fixes detectability, not adequacy. Whether authored prose *adequately*
answers a subject is a judgement no predicate decides, and this corpus already
routes that judgement: RFC-0097's § *Errata* of 2026-08-28 requires each delivery
slice to name the reviewer who made it, and the composition-floors slice's AC5
records the same division — a criterion asserts that a subject is named, and the
named slice reviewer records whether it is adequately answered.

**This slice's named reviewer is `foundation-corpus-reviewer`**, and the
judgement is recorded in `notes/verification-ledger.md`, which
`docs/CONVENTIONS.md` assigns as the home for an observation produced by
execution.

**That judgement is advisory and never blocks.** Three of the criteria below
have a semantic neighbour a predicate cannot decide: whether a newly authored
sentence defers the manifest in different words, whether it reserves a profile in
different words, and whether naming a mode amounts to directing a reader to
invoke it. Each criterion is the mechanical proxy and nothing more, and the proxy
is what the gate reads — a judgement no predicate settles must not become a gate
over taste. The reviewer records the semantic reading beside the gate result so a
paraphrase that slipped past a proxy is visible to the next author; a criterion
below neither asserts that reading nor waits on it.

- **Corpus content outcomes** (the plugin core, the client-delegated concerns,
  the delegation boundary, the tool-restriction caveat, and the divergence
  caveat) — goal-based, verified by the pack suites that read the authored and
  compiled trees. Each criterion states the literal that decides it, so the check
  is a containment or absence read over a value this spec fixes.
- **The portability-guard outcome** — TDD. Both specimens are required, because
  a guard that flags every manifest filename satisfies the flagging specimen
  alone and a guard that flags nothing satisfies the admitting specimen alone.
  Only the admitting specimen is written red-first: the base predicate flags both
  filenames, so it is the one that can earn red, and the flagging specimen is an
  erosion control whose stated mutation is its can-fail proof. The shipped guard
  independently corroborates the admitting direction: it asserts that no floor
  body matches a forbidden class, so an unnarrowed guard turns red the moment the
  floor states the specification's filename.
- **The two vocabulary outcomes** (AC13 and AC14) — goal-based, each over the
  component-surface names its own criterion fixes and each checked against the passage that states
  the matching concept, so a profile stating one concept in runtime terms and the
  other generically fails exactly one of them. Whether the vocabulary reads
  naturally to an author is the named reviewer's judgement, not this check's.
- **Retired-leaf outcomes** (the absence reason, and the admission condition) —
  goal-based over the leaves read from the compiled register rather than from a
  list written here, so a leaf added later is covered without editing this spec.
- **The later-slice-promise outcome** — goal-based across the three surfaces the
  criterion names, each checked independently, because one control satisfied by
  any one surface says nothing about the other two.
- **The unavailable-mode outcome** — goal-based over the mode set the
  unsupported-mode fixture records, read from that fixture rather than from a
  list written here.
- **The re-measured retrieval runs** — goal-based at an integration surface:
  each recorded run binds every digest its assertions declare to the tree and
  the case fixture it measured, so an assertion passes only against evidence
  recorded after the edits. The shipped digest assertions already enforce this, so it is a plan
  task rather than a criterion here.

## Acceptance Criteria

- [x] **AC1 — The portable package floor states the four behaviors the plugin
      specification fixes.** For each of these four, the floor states the named
      value: the manifest is `plugin.json` at the plugin root; every
      package-supplied path a client reads or executes resolves within the
      filesystem-resolved plugin root; `version` uses semantic versioning as a
      recommendation, and a client does not reject a plugin for a version string
      that fails it; and a failure isolated to a component type, entry, or
      process still leaves independently valid components loadable. A floor
      omitting any one of the four fails.
- [x] **AC2 — The portable package floor carries neither manifest-deferral
      sentence.** Neither of these two statements appears in it: that the floor
      "leaves the manifest to the runtime profile", and that "manifest shape,
      install commands, and enablement behavior are runtime-specific and are
      deliberately absent here". Both are quoted as the fixed comparison the
      absence check reads. Whether a differently worded sentence defers the
      manifest is a reading recorded by the named reviewer, not a property this
      criterion asserts.
- [x] **AC3 — The portable package floor names all seven concerns the
      specification delegates to clients.** Installation, discovery location,
      distribution, enablement, permissions, sandboxing, and user experience are
      each stated as client-owned. Discovery location is load-bearing: AC7 places
      a runtime's manifest location in its profile only because this criterion
      keeps that concern delegated rather than specification-fixed.
- [x] **AC4 — The narrowed portability guard admits the specification's filename
      and still flags a runtime's.** Two specimens decide it: the guard leaves a
      bare `plugin.json` unflagged, and flags a runtime-owned manifest path. Both
      are required — a guard that flags nothing satisfies the first alone, and a
      guard that flags every manifest filename satisfies the second alone. The
      portability rule itself is owned by the composition-floors slice's AC4 and
      is not restated here; what this criterion adds is that widening what the
      guard permits did not widen what reaches a portable floor.
- [x] **AC5 — The portable delegation floor resolves an unanswered capability
      question conservatively, without a runtime profile.** It states that a
      capability question the floor cannot answer and no profile covers is
      treated as absent rather than assumed present, and states the design
      consequence: the operation stays in the parent. A pointer to a profile is
      not the only route to a resolution.
- [x] **AC6 — The portable delegation floor states the value crossing at each
      direction of the delegation boundary.** Outbound: the worker receives only
      the context the parent passes it, not the parent's conversation. Inbound:
      the parent receives only the worker's declared result, and the worker's
      intermediate reads do not return.
- [x] **AC7 — The Claude Code runtime profile states that this runtime reads its
      plugin manifest from its own location, not the specification's.** The
      profile states that the manifest is read from a client-specific location
      beside the package root rather than at the root, and names only the
      specification's own filename. The client's path is a delivery mechanic the
      portable pack does not carry, and a shipped boundary guard forbids it
      anywhere in the projected pack tree.
- [x] **AC8 — The Claude Code runtime profile states the authoring consequence
      of that location.** A package carrying its manifest only at the plugin root
      is not discovered by this runtime. Separate from AC7 because a profile can
      name the path and omit what follows from it, and the remedy differs.
- [x] **AC9 — Every retired leaf's absence reason is open extension.** The
      retired leaves are selected by slug from the declared-absent register — a
      leaf whose slug names a runtime other than Claude Code — because a slug is
      stable while the prose under it is what this slice rewrites. Each such
      leaf's reason states open extension rather than a reserved slice.
- [x] **AC10 — Every retired leaf's admission condition names no delivery
      slice.** Selected by the same slug predicate as AC9, so removing a runtime
      name from a reason cannot empty the set. Whether the replacement condition
      is one a contributor could actually meet is a reading recorded by the named
      reviewer, not a property this criterion asserts: no predicate distinguishes
      an actionable condition from an unmeetable one.
- [x] **AC11 — No named surface carries its reserving sentence.** Three
      surfaces, three fixed comparisons, each checked separately. The
      declared-absent register does not state that a leaf is "Reserved for the
      later slice that covers runtime composition". The pack README does not
      state that "Seven further runtime profiles, the router's per-claim state
      reporting, provider authoring, runtime packaging, installation, projection,
      publication, and catalogue governance belong to later slices or external
      delivery tooling". `docs/architecture/agent-skill-engineering.md` does not
      state that the router's reporting and its contract change "belong to the
      slice that completes the eight profiles". Whether a differently worded
      sentence makes the same reservation is a reading recorded by the named
      reviewer, not a property this criterion asserts.
- [x] **AC12 — No sentence in the concept prose puts a fixture-named mode in
      the imperative.** This is a lexical proxy, stated as the criterion because
      the property behind it — whether prose recommends an unavailable mode — is
      not mechanizable, and a criterion claiming more than its gate delivers is
      worse than one that admits its reach. The proxy: no fixture-named mode
      appears as the object of `invoke`, `select`, `run`, `use`, `choose`, or
      `package with`, nor as the object of a `should`/`must` addressed to the
      reader. It does not reach every recommendation, and a miss is a reading the
      named reviewer records rather than a gate failure. Naming a mode while
      explaining a concept is permitted and is the accepted case the proxy must
      not reject. AC1 and AC5-AC8 carry the positive half: the concepts those
      modes would package are stated regardless.
- [x] **AC13 — The Claude Code profile teaches the delegation concepts in this
      runtime's own component vocabulary.** Where the profile states delegation
      and worker boundaries, it names the runtime's own component surfaces — its
      `agents/` and `skills/` directories — so a Claude skill author reaches
      those concepts through the surfaces they author rather than through generic
      worker terms.
- [x] **AC14 — The Claude Code profile teaches the packaging concepts in this
      runtime's own component vocabulary.** Where the profile states packaging
      and component behavior, it names this runtime's own component surfaces —
      its `hooks/` directory alongside the `agents/` and `skills/` AC13 names —
      and refers to its manifest by location rather than by path, for the reason
      AC7 states. Separate from AC13 because a profile can state one concept in
      runtime terms and the other generically, and the remedy differs.

## Follow-ons

No criterion asks for the subagent tool-allowlist caveat the brief's slice row
names, because it is already shipped and the composition-floors slice's AC5 owns
the subject. This spec's Assumptions record the observation that grounds the
deletion. A criterion here would hold on the tree as authored and so could never
fail.

- INI-009 slice `3c-r` owner, via the `3c-r` row in
  `docs/product/briefs/agent-skill-engineering.md`: the router's per-claim state
  and roll-up reporting, and the provider response-contract change it needs,
  scoped to the ledger the composition-floors slice shipped.
- INI-009 slice 3d owner, via the 3d row in the same brief: the
  `runtime-package` authoring mode and its
  `compatibility-and-runtime-package-patterns` leaf, whose recorded admission
  condition this slice narrows to the one runtime that has a profile.
- INI-009 slice 3e owner, via the 3e row in the same brief: the
  subagent-composition and hook/plugin-design behavior fixtures. This slice
  ships corpus prose and recorded retrieval evidence, not behavior fixtures.
- INI-009 slice 6 owner, via the slice 6 row in the same brief, which already
  owns freshness policy and architecture promotion: promoting the planned
  architecture document to `CURRENT`. This slice refreshes the sections its own
  edits make false and leaves the document `PLANNED`.

## Assumptions

Each entry records repository or external state as observed on 2026-09-09, when
this contract was drafted, and names how it was settled. Several describe state
the contract above deliberately changes; they are the frame the criteria were
written against, not claims about state after this slice ships.

- Technical: Agent Plugins v1.0.0 fixes all four concepts this slice states as portable — "Clients MUST check for a manifest at `plugin.json` in the plugin root" with required `$schema` and `name`; "the filesystem-resolved path MUST remain within the filesystem-resolved plugin root"; "Plugins SHOULD use Semantic Versioning for `version`"; and "A failure isolated to a component type, component entry, or component process MUST NOT prevent the client from loading independently valid components" (source: https://agent-plugins.org/specification and https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md, retrieved 2026-09-09, spec version 1.0.0, no last-updated date exposed)
- Technical: two first-party runtime sources state the root-manifest clause against schema `1.0.0`, so the plugin-core claims can rest on a two-runtime public contract rather than on one vendor — "A portable plugin has a `plugin.json` manifest at its root" (source: https://developers.openai.com/plugins/build/plugins, retrieved 2026-09-09, no version exposed) and a power's root `plugin.json` declaring `$schema: https://agent-plugins.org/schemas/1.0.0/plugin.schema.json` (source: https://kiro.dev/docs/powers/create/, retrieved 2026-09-09, no version exposed)
- Technical: Claude Code reads its plugin manifest at `.claude-plugin/plugin.json` and claims no Agent Plugins conformance — "Only `plugin.json` goes inside `.claude-plugin/`" — which is the one divergence in this subject that changes an authoring decision. Component-level isolation is not divergent: an invalid entry "is skipped instead" (source: https://code.claude.com/docs/en/plugins, retrieved 2026-09-09, no version exposed)
- Technical: the portable package floor currently defers the manifest to a runtime profile, in both its scope and its provenance section, and the portable delegation floor directs every unanswered capability question to the same profile (source: `packs/agent-skill-engineering/okf/agent-skill-engineering-foundation/concepts/plugin-package-common-floor.md`, `packs/agent-skill-engineering/okf/agent-skill-engineering-foundation/concepts/skills-and-subagents-common-floor.md`)
- Technical: RFC-0097's 2026-09-01 erratum makes a specification-fixed capability ineligible for a profile row, which is what moves the plugin core into the portable floor rather than leaving it profile-owned (source: `docs/rfc/0097-agent-skill-engineering.md` § *Errata*, 2026-09-01)
- Technical: the taxonomy is a closed leaf set partitioned by exclusive-or between the admitted topics and the declared-absent register, and no leaf in it names these concepts, so they are stated on already-admitted topics (source: `packs/agent-skill-engineering/tests/fixtures/topology-leaves.json`, `packs/agent-skill-engineering/tests/pack/test_corpus_admission.py::test_every_leaf_is_in_exactly_one_set`)
- Technical: editing any authored topic body moves the compiled source digest that both recorded retrieval runs bind, so both runs are re-measured in the same change (source: `packs/agent-skill-engineering/tests/pack/test_foundation_corpus.py::test_independent_router_results_meet_precision_and_recall_gate`, `::test_generic_negative_record_is_attributable_to_the_tree_it_measured`)
- Technical: the pack README's governed-topic count is asserted in words against the admitted set, and a fixed tuple of absence sentences is forbidden across four shipped surfaces including the README (source: `packs/agent-skill-engineering/tests/integration/test_provider_contract.py::test_language_extension_families_are_distinct_and_populated`)
- Technical: no test asserts the literal absence-rationale prose for a declared-absent leaf, so re-homing the retired leaves' rationale needs a criterion here rather than inheriting one (source: `packs/agent-skill-engineering/tests/pack/test_corpus_admission.py`, register transcription asserts the declared count and leaf list only)
- Technical: the delegation floor's security-and-authority section already states the tool-allowlist caveat the brief's slice row names — where a runtime cannot carry a restriction across the delegation boundary, the restricted operation stays in the parent. This is why no criterion asks for it (source: `packs/agent-skill-engineering/okf/agent-skill-engineering-foundation/concepts/skills-and-subagents-common-floor.md`, `## Security and authority`)
- Technical: the shipped portability guard is stricter than the frozen criterion it implements. The criterion forbids "a file path belonging to any runtime the corpus profiles", while the guard's `runtime-settings-file` class matches any `plugin.json`, including the specification's vendor-neutral filename. Narrowing the guard to runtime-owned manifests conforms it to its own contract and amends no ticked criterion (source: `packs/agent-skill-engineering/tests/pack/test_composition_floors.py`, `FORBIDDEN_IDENTIFIER_CLASSES`; `docs/specs/agent-skill-engineering-composition-floors/spec.md` AC4)
- Technical: the same suite pins each floor's subject count from module literals and requires each subject phrase to appear in the body, under a separate frozen criterion. Adding the plugin core is new content rather than a new subject, so the counts and the seven package-floor subject phrases stay unchanged (source: `packs/agent-skill-engineering/tests/pack/test_composition_floors.py`, `SUBJECT_COUNTS`; `docs/specs/agent-skill-engineering-composition-floors/spec.md` AC5)
- Technical: only the root-manifest clause is restated in two runtimes' own words; confinement, versioning, and component-level failure isolation are stated by the specification, and both runtimes reach them by declaring conformance to it rather than by restating them. Kiro states "Powers follow the Agent Plugins specification" and a power's `version` is a "Semantic version of the power" (source: https://kiro.dev/docs/powers/create/, retrieved 2026-09-09, page last updated 2026-08-04); the OpenAI skills-authoring page shows the manifest and a semantic `version` without restating either clause (source: https://developers.openai.com/plugins/build/skills, retrieved 2026-09-09, no version exposed)
- Product: a client's declared conformance to the specification counts as repeating that specification's normative clauses, so all four behaviors ship in one two-runtime public-contract claim group sourced to the specification and both conforming runtimes (source: user confirmation 2026-09-09)
- Product: the shipped portability guard is narrowed to match its frozen criterion rather than the floor avoiding the specification's filename (source: user confirmation 2026-09-09)
- Process: slice 3c is unblocked and ships concepts only; the seven remaining runtime profiles are retired to open extension and the claim-state reporting is row `3c-r`, which depends on this slice (source: `docs/product/briefs/agent-skill-engineering.md` § *Confirmed delivery slices* and § *The runtime-profile de-scope, and what it needs*)
- Process: every milestone lists its own advertised modes, required topics, and fixtures, and no fixture may cite a mode belonging to a later milestone, which is why this slice teaches the concepts without making any packaging mode available (source: `workspace.toml`, the INI-009 staged-delivery constraint)
- Product: this slice admits no new taxonomy leaf and states the concepts on the shipped floors and the Claude Code profile, leaving the governed-topic count unchanged (source: user confirmation 2026-09-09)
- Product: this slice owns re-homing the retired runtime-profile leaves' absence rationale, rather than leaving it to closeout (source: user confirmation 2026-09-09)
- Process: spec-stage shaping and adversarial review are required before this spec is indexed or approved; no repository rule names a security-boundary trigger for corpus prose, and this slice crosses no trust boundary (source: `.claude/skills/new-spec/SKILL.md` steps 6-8; `docs/CONVENTIONS.md` carries no such corpus-prose trigger)
