# Plan: Agent Skill Engineering Composition Fixtures

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/rfc/0097-agent-skill-engineering.md`
  § *Experiment / validation*, Gate 2, for the fixture inventory, its success
  conditions, and the architecture-update fields;
  `docs/specs/agent-skill-engineering-composition-floors/` for the floors the
  payloads seed defects against, and its Follow-ons for the residual this slice
  discharges; `docs/specs/agent-skill-engineering-languages-and-execution/` T8
  for the two-fixture precedent and the three-context grading procedure;
  `packs/AGENTS.md` for the export boundary and the version-bump rule;
  `docs/CONVENTIONS.md` for the verification-ledger owner and the
  stub-to-EXECUTE handoff this plan does not pre-empt.
- **Review shape:** MIXED. The change spans authored payloads, a graded
  measurement round, several pinned enumerations, and a records layer. Two tasks
  carry the substance rather than four, because every enumeration the pack pins
  is an equality: any split between declaring a case, recording its result, and
  reconciling the exemption its result may produce leaves a knowingly red tree.
- **TDD stubs:** authored at work-loop PLAN, per `docs/CONVENTIONS.md`
  § *Stub → EXECUTE handoff*. This document names each task's verification mode
  and the mechanism its tests turn on; it does not carry test code.

## Approach

1. In one commit, move the registration from `.queue` to `.active` and roll the
   status tokens, the milestone, and the brief's Spec-map row with it, so the
   queue never advertises this slice as startable while it is in flight and no
   path is left in two lifecycle collections.
2. Declare, pin, grade, and reconcile the exemption set in one task, holding
   authoring, execution, and grading in three contexts and retaining every
   transcript.
3. Publish the records and surfaces, and close the pair the first task opened.

## Constraints

- Three contexts, not two. The authoring context writes payloads, assertions,
  and pattern identifiers. The executing context receives the prompt and the
  payload and nothing else — the payload carries the seeded defects on purpose,
  because finding them unaided is the measurement; what it must not receive is
  the authoring material describing them. The grading context receives the
  captured transcript and the assertion list. An executor that has seen the
  assertion list is measuring its own recall of it.
- Every comparison set describing the state before this slice is read with
  `git show <base>:<path>`, and the base commit is recorded in the verification
  ledger before the first edit. A baseline read from the working tree is one
  this change can edit first — the mutation that defeated the earlier draft of
  AC3 and AC5.
- The skill body is not edited, and no inherited declaration's marker set is
  widened. A body edit moves the digest every record pins and forces a second
  full grading round; widening an inherited marker set is how a marker this
  slice invented becomes "inherited".
- Payload content is portable: no repository document path, criterion
  reference, or workspace-file mention, because the payloads ship inside
  `.apm/`.
- Retained transcripts are scrubbed before commit and live under this spec's
  `notes/`, never under `.apm/`.
- Each lifecycle move is one commit: the spec status, the plan status, the
  registration, and the milestone change together. This is an operating rule,
  not a criterion — five attempts at a Git-history predicate for the pairing
  each admitted a reconciling second commit, so AC21 and AC22 state the
  invariant the projection can actually read and this constraint states how to
  keep it.

## Construction tests

The guards this slice moves live in
`packs/agent-skill-engineering/tests/skills/author_or_update/test_contract.py`.
The enumerations there that scope what a pack guard reads are the authoring
workflow's declared-case set, `AUTHORING_EVAL_IDS` with its anti-vacuity length
pin, the behavior-result id set, and `AUTHOR_EVIDENCE_SOURCES`, the tuple the
digest sweep is parametrized over. Each is an equality or subset check against a
derived set, and each widens in T2.

Two pack-level scans reach the new artifacts without change, each asserting its
population is at or above a lower bound over a recursive walk:
`test_pack_boundary.py::test_shipped_content_names_no_repository_only_reference`
reads the payloads, and
`test_corpus_admission.py::test_recorded_evidence_fields_carry_no_host_identifying_data`
reads both the declarations and the records. Retained transcripts sit outside
both roots, so T2 extends the host scan over this spec's `notes/` directory
rather than assuming coverage.

Roster and catalogue gates own the manifest, changelog, index, brief Spec-map,
and workspace reconciliation; this slice adds no assertion there.

**What the enumeration inventory does and does not establish.** Recompute it
rather than trusting a stored verdict: search the tracked tree for the inherited
case ids, then classify each hit as a live enumeration owner, a record, or
prose. Predecessor specs, their ledgers, and research notes all mention the ids
and are none of the three. One hit is a consumer of a different kind:
`topic-admission.json` names inherited fixture ids as the fixture backing a
doctrine group, which `test_corpus_admission.py` resolves against the recorded
results — so a fixture id is a stable external identifier, and an id may be
added but not renamed. The search finds literal-id consumers only. A guard that
selected authoring records by a computed predicate — a slice, a field test —
would not appear in it, which is why AC16 is bounded to the enumerations named
above rather than claiming exhaustive coverage.

## Durable-output map

The Never-do rule forbidding a Gate 2 claim reads this table together with the
Construction tests section above as its enumeration of what this slice writes.
This table carries the lasting records; that section names the guard files.
Test files are deliberately not rows here — a durable-output map routes semantic
owners of lasting truth, and tests do not preserve product intent — so the
prohibition reaches them through the pairing rather than through a row.

| Durable output | Task | Evidence |
| --- | --- | --- |
| Two eval payloads and two declarations | T2 | Declaration, payload-binding, and marker-provenance guards green |
| Graded behavior records | T2 | Every record bound to a retained transcript and the shipping digests |
| Retained transcripts (`notes/`) | T2 | One per graded case, each recomputing to its record's digest |
| Verification ledger (`notes/verification-ledger.md`) | T1, T2, T3 | Base freshness verdict and base commit, moved verdicts, exemption authorities, mutation proofs, every advisory reading and attestation, gate failures |
| Interface compatibility (both authored manifests) | T3 | Publication and roster gates green at the bumped version |
| Regenerated aggregate manifest | T3 | Running the projection generator leaves `.claude-plugin/marketplace.json` unchanged |
| Release history (changelog) | T3 | Topmost free-standing `agent-skill-engineering` entry with its `Highlights` disposition decided |
| Current architecture | T3 | Names, paths, dependency edge, and verification evidence; document still `PLANNED` |
| Product provenance (brief Spec map) | T1 | A row carrying the bare slug, resolving under brief-coverage lint |
| Spec index | T3 | Row's counts equal this spec's |
| Current product truth (pack README) | T3 | No stale evaluation-evidence sentence |
| Lifecycle record | T1, T3 | The `workspace.toml` registration entry and the `["ini-009"]` milestone string, plus the `Status` tokens in `spec.md` and `plan.md` — enumerated here because the Gate 2 Never-do reads this table, together with the Construction tests section, as the set of artifacts this slice writes |
| Reusable learning | work-loop | Capture receipts at `spec-approved` and `plan-locked`, or the named skip |

## Design (LLD)

### Design decisions

The two cases attach to `author-or-update-agent-skill` rather than to
`review-or-optimize-agent-skill`. The authoring workflow's `frame` mode is
read-only, and `pytest-suite` — the inherited case with this same shape —
already declares the exact marker set a composition-framing case needs, so no
body change is required to make one gradable. A
review-workflow case would instead need each seeded defect to map to a shipped
`ASE-*` finding identifier, and the composition floors ship none.

The declaration gains two fields the inherited cases do not carry: the pattern
identifiers the case exercises, and the text of the one assertion that reports
the defect its payload seeds. Both are additive and required only of the two
cases this slice authors, because a guard requiring them everywhere would redden
on cases this slice does not own. The second field exists because "the assertion
naming the seeded defect" is otherwise whichever assertion the implementer had
in mind, and dropping it while keeping the others leaves every check green.

The record gains three fields and the tree gains one artifact class. An
observation identifier ties the round together; a transcript path locates the
retained response under this spec's `notes/`; and a captured-response digest
binds the verdict to that transcript's bytes. The path is a separate field
because a digest is not a locator — the shipped records carry only `eval_id`,
`actual_markers`, `assertions`, and `source_files`, so there is no existing
field for AC9's per-record path to inherit. The transcript
is the point: without it the digest is self-issued, and refreshing a source
digest is indistinguishable from re-running the case. With it, a fabricated
record has to produce a transcript that both hashes correctly and contains every
declared marker, and a reader can check the verdicts against it by hand.

### Interfaces & contracts

No provider request/response change. The eval declaration keeps the field set
the inherited cases use and adds two fields on the two cases this slice
authors: the pattern-identifier list, and the exact text of the assertion that
reports the defect its payload seeds. Both are named in Design decisions above
and required by AC4 and AC6.

### Failure, edge cases & resilience

An inherited case that flips from pass to miss under the blind round is recorded
as measured — not exempted without owner authority, and not reworded. An
inherited exemption that flips to pass is deleted, because the suite asserts
exemptions are still failing in both directions. Both reconciliations happen
inside T2, alongside the measurement that produced them: the bidirectional
exemption assertion reddens the moment a verdict moves, so deferring the
reconciliation to a later task hands that task a red tree. A payload whose
seeded defect the workflow does not surface is reported as a measurement;
rewriting the payload after seeing the verdict is the *Never do* this slice most
needs.

## Tasks

### T1: Open the status and registration pair

**Depends on:** none

**Verification mode:** goal-based.

**Tests:**
- The workspace projection at this commit, which must emit neither
  `impossible_transition` nor `duplicate_membership` for this spec — the second
  is what a registration appended to `.active` without being removed from
  `.queue` produces (AC21)
- The `["ini-009"]` milestone string read from `workspace.toml` itself and
  compared with `git show <base>:workspace.toml`. The projection cannot serve
  here: it emits `"milestone": "workspace.toml"`, a pointer to the source rather
  than the value, so a check reading the projection can never see what the
  string says (AC22)
- `lint-brief-coverage.py --root .` over the Spec-map row added here. The row
  belongs in this commit rather than at close, matching the shipped precedent in
  the languages-and-execution slice's T1 (AC24)
- `workspace_status.py explain` over this spec's item. Its `dependencies` output
  is the direct evidence that the edge resolved, and it is the only such
  evidence: no roster suite asserts an `unsatisfied_dependency` ceiling.
  `tests/roster/test_status_projection_and_context_exclusion.py` carries
  dependency-finding cases and `test_workspace_status_projection.py` carries
  `impossible_transition`; neither would redden on this slice's edge, so neither
  is cited as proof of it (AC21, AC22)

**Approach:** run `check-base-freshness.py` and record both its verdict and the
resolved base commit in the verification ledger before any edit. The freshness
check and the base record are one step: every comparison set in T2 is read from
that commit, so a base that has fallen behind `origin/main` since authoring
silently changes what "before this slice" means.

Then make every lifecycle move in one commit. Move this spec's registration out
of `["ini-009".work].queue` and into `.active`, carrying its brief parent and
the brief's current digest — remove and append together, because a path present
in two lifecycle collections emits `duplicate_membership`, which the roster
projection treats as zero-tolerance and which none of this task's other checks
would see. Rewrite the `["ini-009"]` milestone string so it no longer advertises
3e as unblocked or parallel and instead names it as the slice in flight; AC22
compares it against the base-commit string, so leaving it untouched fails. Add the brief's Spec-map row carrying this spec's bare slug; a
path-shaped entry does not resolve. Reconcile the brief's *Not yet started*
paragraph, which asserts that 3e has no spec, plan, or workspace entry and that
`["ini-009".work].queue` is empty, and which is false about 3e the moment this
task lands. Roll the spec to `Implementing` and this plan to `Executing`.

Rolling one of those without the others trips the workspace projection ratchet
or leaves an illegal status pair — the invariant AC21 and AC22 read from the
projection. Keeping the moves in one commit is the operating constraint above,
not something either criterion checks.

**Done when:** one commit carries the registration moved out of `.queue` and
into `.active` with no entry left behind, the milestone, both status tokens, the
Spec-map row, and the corrected *Not yet started* paragraph; the resolved dependency edge is visible in
`explain` output; and the ledger carries the freshness verdict and the base
commit.

### T2: Declare, pin, grade, and reconcile

**Depends on:** T1

**Verification mode:** TDD for the declaration and record contracts; observed
behavior fixture, graded blind, for the measurement.

**Tests:**
- Per-case field non-emptiness across `prompt`, `expected_output`, `assertions`,
  `expect.output_contains`, and `files`. The shipped shape test asserts a
  resolvable path for one inherited case and nothing about emptiness, so an
  empty `files` list passes it vacuously (AC1)
- Payload-set disjointness across all declared cases, plus canonical path
  containment: each declared path is resolved, symlinks included, and the
  resolved path must sit under the authoring skill root. Existence alone is not
  the check — `../review-or-optimize-agent-skill/evals/evals.json` resolves to a
  real file outside the root (AC2)
- Declared-case set equality against `git show <base>:<declarations path>` plus
  the two ids, with the same base-derived widening applied to
  `AUTHORING_EVAL_IDS`, its length pin, the behavior-result id set, and
  `AUTHOR_EVIDENCE_SOURCES` (AC3, AC16)
- Per-case equality between each new case's declared pattern list and the exact
  list the criterion fixes, and resolution of each identifier against
  `topic-admission.json`. Membership in the admitted set is the weaker check
  that an unrelated topic passes (AC4)
- Set equality between each new case's `expect.output_contains` and the set
  `pytest-suite` declares at the base commit, plus equality between
  `pytest-suite`'s set on the shipping tree and at the base commit. Containment
  against the union of base declarations is the weaker check that admits
  `Mode: knowledge-provider` from a provider case and `Write status: awaiting
  explicit authorization` from `cross-session-resumption` — both present in the
  base declarations, neither producible by a read-only framing case (AC5)
- Each new case's declared seeded-defect assertion text is a member of that
  case's own `assertions` list, and the two cases name different assertions
  (AC6)
- Payload non-emptiness and digest distinctness against each other and against
  every payload the base commit carried (AC8)
- For every record: its transcript resolves under `notes/`, the recorded digest
  recomputes from that transcript's bytes, and every declared marker occurs in
  it. This is the assertion a fabricated record must defeat; comparing
  `actual_markers` to the declaration is a mirror and proves nothing (AC9)
- Transcript distinctness compared on resolved canonical targets, not on the
  path strings, using the same resolution the AC2 payload check applies. Two
  lexically distinct paths under `notes/` — one a symlink to the other — satisfy
  a string comparison while a single transcript backs both records, which is the
  mutation AC9 exists to stop (AC9)
- The assertion each new case names as its seeded-defect assertion is recorded
  true, or appears in the exemption set (AC13)
- One observation identifier across all authoring records, verdict count equal
  to assertion count, and `source_files` key set equal to the declared files
  plus the shared sources (AC11)
- `test_authoring_behavior_evidence_matches_its_source_digest` across every
  entry in the widened `AUTHOR_EVIDENCE_SOURCES`, and equality between each
  inherited record's observation identifier and this round's (AC12)
- The bidirectional exemption assertions, evaluated after the exemption set is
  reconciled in this same task. The same assertions are what force a new case's
  seeded-defect miss to be either repaired or authorised rather than left
  unremarked (AC13, AC14)
- The host-identity scan extended over this spec's `notes/` directory, and both
  pack scans over the payloads, declarations, and records (AC17)
- The committed portability grep from `packs/AGENTS.local.md` run over the two
  payloads, in addition to the pytest export-boundary scan. It is the only one
  of the two that matches a bare `RFC-NNNN` or `ADR-NNNN`, and it is a
  maintainer-run command rather than a suite, so it is scheduled here or it does
  not run at all (AC18)

**Approach:** author both payloads and both declarations together, because a
seeded defect and the assertion that must surface it are one decision. Give each
new case the marker set `pytest-suite` declares at the base commit — that exact
set, not a selection from the base declarations at large. Widen the enumerations, then
grade every authoring case in one round, with the executing context withheld
from the authoring material about the payload — the assertion list, the pattern
identifiers, and any statement of which defects were seeded or what a good
answer names. The payload itself, defects and all, is what the executor is
given; finding them unaided is the measurement. Retain
each transcript, scrubbed, under `notes/`. Overwrite the inherited records with
this round's verdicts; carrying a verdict forward with a refreshed digest is the
re-stamping the spec forbids. Then set the exemption set to exactly the pairs
this round measured false, deleting a repaired one and seeking owner authority
before adding a new one.

Write to the verification ledger, which is where every judgement no guard can
reach is recorded:

- every inherited verdict that moved, with its prior and measured value;
- each exemption's authority fields;
- each enumeration's mutation proof, naming the assertion that reddened, its
  message, and that the file was restored by editing and confirmed
  byte-identical;
- for each assertion either new case declares, the requirement in the declared
  floor's shipped text it tests, and the reviewer's judgement that a response
  could satisfy it only by meeting that requirement (AC7);
- for each recorded verdict, the grading context's reading of the transcript
  passage it rests on (AC10);
- the operator's attestation, for the round as a whole, that the responses were
  generated in it rather than copied under a new identifier, and that the
  executing context received the prompt and payload only — no assertion list, no
  pattern identifiers, no statement of which defects were seeded — naming how
  the separation was arranged. Neither claim is decidable from tree bytes, which
  is why it is an attestation and not a gate (AC11);
- whether each payload's prose carries the defect its declaration names;
- whether any bare identity survives the structural host scanner.

**Done when:** every authoring case has a record from one observation with its
own retained transcript whose digest recomputes; the enumerations equal their
base-derived subjects; the exemption set equals the measured misses; and the
ledger carries every entry in the list above.

### T3: Publish the records and close the pair

**Depends on:** T2

**Verification mode:** goal-based, with the exemption authority read at review.

**Tests:**
- A read of the verification ledger confirming each exemption carries the fields
  the *Never do* rule enumerates. No test can see whether an authority exists,
  so this is a review step named as one (AC15)
- A read of the architecture record confirming all four RFC-required fields.
  Repository search finds no gate asserting them, so this is the second half of
  the same review pass, not an automated check (AC20)
- The behavior-result id set compared against the list RFC-0097's M2 expanded
  measure states, transcribed into the check as this slice's reading of that
  prose and cited to the RFC section, so the expected set does not come from the
  fixture file it grades (AC19)
- `FORCE=1 make build-self` followed by
  `git diff --exit-code -- .claude-plugin/marketplace.json`, which must be
  empty. The generator writes its target in place, so there is no separate
  artifact to diff against; running it and requiring no change is the form of
  the parity check that has a subject. It reddens both on a stale aggregate and
  on a hand-edit that diverges from the projection (AC25)
- `agentbundle catalogue lint --root . --deep` and
  `agentbundle catalogue verify --root .` over the bumped manifests, and the
  publication and roster gates (AC25)
- The changelog placement check, over a free-standing `##` entry topmost for
  this pack (AC26)
- Brief-coverage lint over the Spec-map row. It reports an unresolved back-link
  informationally and exits zero, so the row's presence is confirmed by reading
  the brief, not by the linter's exit code (AC24)
- This spec's own `["ini-009".work]` entry's `source.revision` compared with a
  freshly computed `sha256-bytes-v1` digest of the brief. One entry, computed
  rather than copied. No other registration is touched: `brief_queue.executing`
  pins RFC-0097, not the brief, and the shipped siblings' older pins are the
  pre-existing drift the Follow-on records (AC23)
- The spec-index row's shape and counts read against this spec's final
  criterion and task counts (AC27)

**Approach:** read the version both authored manifests carry, bump both by one
patch in lockstep, regenerate the aggregate manifest, and write the changelog
entry at that version.

Decide the entry's `Highlights` disposition in the same step rather than leaving
it to a reviewer. Read the release diff and answer whether this change alters
what a consumer of the pack can do. Two new behavior fixtures and a
re-measurement round change the pack's evidence, not its installed surface, so
the expected answer is no and the verdict plus its reason goes in the PR's *what
did you not change that you considered* answer. If the round moves a verdict
that changes shipped guidance, the answer flips and outcome-led bullets go under
a `### Highlights` subsection. Nothing downstream makes this call: the public
projection is a parser over the file's bytes (AC26).

Update the architecture record with this slice's implemented
names, their paths, its dependency edge on the composition floors slice, and the
verification evidence for the two fixtures, leaving the document `PLANNED`. Add
the index row, and reconcile any pack README sentence describing the evaluation
evidence.

Then close the pair T1 opened: set the spec to `Shipped` and this plan to
`Done`, move the registration from `["ini-009".work].active` to `.shipped` in
the same commit, and re-pin this spec's own entry to a freshly computed brief digest if the
brief moved during the slice. Make the status roll and the registration move one
commit. A `work.shipped` entry whose
spec does not read `Shipped` emits `impossible_transition`.

**Done when:** both authored manifests agree at the bumped version and
regenerating the aggregate leaves it unchanged, the changelog entry is topmost for the pack
with its `Highlights` disposition recorded either in the entry or in the PR
answer, the architecture record carries all four RFC-required fields and stays
`PLANNED`, the brief Spec-map row and index row are present, and the spec reads
`Shipped` in `work.shipped` with this spec's own entry carrying a freshly
computed brief digest and no other registration touched.

## Risks

| Risk | Mitigation |
| --- | --- |
| A record is fabricated or re-stamped rather than measured | The retained transcript is the falsifier: the digest must recompute from bytes in the tree, every declared marker must occur in them, and the verdicts must be the ones a reader reaches from them. Comparing `actual_markers` to the declaration is a mirror and is not treated as evidence. |
| The change under test supplies its own baseline | Every "before" set is read with `git show <base>:<path>`, and the base commit is recorded in the ledger before the first edit. |
| A marker this slice invented is laundered through an inherited declaration | Each new case's marker set must equal `pytest-suite`'s set at the base commit, and that sibling's set on the shipping tree must equal its base-commit set. Containment in the union of base declarations was tried and rejected: the union spans modes and authorization states, so it admits `Mode: knowledge-provider` and `Write status: awaiting explicit authorization`. |
| The blind round flips an inherited verdict and leaves a red tree | Expected, not unlikely: every inherited verdict is re-taken against a body last graded in the predecessor slice. The exemption reconciliation is inside T2 for exactly this reason. |
| The grading context is contaminated by authoring | Three contexts, with the assertion list, the pattern identifiers, and any description of the seeded defects withheld from the executor — never the payload itself. Separation is evidenced by the transcript and read at review; a round whose separation cannot be attested is discarded. |
| An unreliable harness run is recorded as a measurement | Discard and re-run; an unreliable run is not a measurement. |
| A widened pin is later narrowed, dropping a record from coverage | One recorded mutation proof per enumeration, each restoring by editing rather than by checkout, with the file confirmed byte-identical afterwards. |
| A future consumer selects records by a computed predicate and escapes every named pin | Not covered, and AC16 is bounded to say so rather than claiming coverage it cannot establish. The inventory method above finds literal-id consumers only. |
| A payload's seeded defect is not the defect its declaration names | No predicate over authored prose decides this, so it is read at review and recorded in the ledger. A machine-readable defect marker inside the payload was rejected: it would put a repository-only annotation inside shipped content. |
| A retained transcript leaks host or personal data | Transcripts are scrubbed before commit and T2 extends the structural host scan over the `notes/` directory; the bare-identity residual stays an advisory read. |
| Scope drifts into corpus content to make a fixture pass | The spec's *Ask first* routes any topic, retrieval case, or mode addition to the owner, and slice 3c owns the composition vocabulary. |
| The slice is read as closing Gate 2 | A Never-do forbids the claim across both enumerating sections — the durable-output map, which carries the lasting records, and the Construction tests section, which names the guard files — and the Follow-on names slice 6 as the owner of the verdict. Naming only the map would leave a guard name or docstring outside the ban. |

## Changelog

- 2026-09-09 — Drafted, then revised across six rounds of paired independent
  cold review — one shaping-lens, one adversarial, each in its own context — and
  against the spec-authoring rubric. Owner decisions: both cases attach to the
  authoring workflow; every inherited result is re-measured blind rather than
  re-stamped; the two authored cases declare pattern identifiers while the
  shipped cases stay a Follow-on; and no stored count of current state survives
  in either document.

  The fixture half of the contract settled early and has held: transcripts are
  retained so a verdict has something outside itself to be read against, every
  "before" set is read from the base commit, each new case's marker set equals
  one named inherited sibling's, and each case names the assertion that reports
  its seeded defect.

  The lifecycle half took the remaining rounds and ended by being cut back
  rather than sharpened. Successive drafts tried to gate the *pairing* of a
  status roll with a registration move; each Git-history predicate admitted a
  reconciling second commit. AC21 and AC22 now state the invariant the workspace
  projection can actually read, and the same-commit discipline is an operating
  constraint. AC25 stopped claiming the aggregate was "regenerated rather than
  hand-edited" — not decidable from a tree — and now requires that running the
  generator change nothing.

  AC23 was rescoped after measurement contradicted the precedent it was modelled
  on. The predecessor slice re-pinned "both registrations that carry the brief
  digest"; on this tree no registration carries the brief's current digest at
  all, the four entries referencing it carry three different older ones, and
  `brief_queue.executing` pins RFC-0097 rather than the brief. No gate reads
  `source.revision`, which is how that accumulated. This slice pins the one
  entry it creates and records the rest as a Follow-on for the workspace-hygiene
  owner.

  Three claims are operator attestations rather than gates, because no artifact
  in the tree distinguishes them from their negation: that the responses were
  generated in this round, that the executing context was withheld from the
  authoring material, and — retired into AC25's parity check — how the aggregate
  manifest's bytes were produced.

  Two reviewer demands were refused with evidence. Compilable red TDD stubs in
  this document: `docs/CONVENTIONS.md` § *Stub → EXECUTE handoff* assigns stub
  code to work-loop's PLAN phase. And the claim that T1 cannot own the lifecycle
  roll: the shipped languages-and-execution slice's T1 does exactly this.
