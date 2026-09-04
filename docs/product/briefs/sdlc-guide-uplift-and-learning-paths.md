# Brief: a new team can walk the whole SDLC from the guides

- **Slug:** `sdlc-guide-uplift-and-learning-paths`
- **Received:** 2026-09-03
- **Owner:** eugenelim
- **Status:** Draft

## Outcome

A team adopting this catalogue can go from install to a shipped, governed change
by following the guides alone. Every skill they must invoke shows what to type,
what to supply, what comes back, and what they hold at the end. The guides are
grouped into ordered paths that state their prerequisites, so a newcomer gets a
route rather than a menu of 203 files.

The route this repository's own owner uses is walkable end to end: shape on
`desk-research` + `product-engineering` + `architect`, hand over with
`intake-intent`, build with `new-spec` + `work-loop`, and collaborate
through RFCs and ADRs sourced from those shaping artifacts.

## Success metrics

Measured by re-running `python3 tools/audit-guide-affordances.py`, which ships
with the audit:

- A literal chat input reaches **every in-scope guide** — the 33 in the
  instrument's harvest table, plus the `product-engineering` and
  `product-strategy` how-tos. Corpus-wide this moves A from 21% toward ~40%; it
  does **not** reach 100%, because the `experience-design` and
  `frontend-engineering` guides have no phrase to project and are out of scope
  with U14.
- A stated outcome rises from 10% to every in-scope how-to and tutorial.
- A demonstrated workflow input rises from 4% (8 files) to every tutorial
  (currently 0 of 17).
- One how-to owns the shaping-to-build handover and names `intake-intent`
  (currently zero guides in the three shaping packs name it), and the
  `architect` and `desk-research` guide sets each link to it, so no shaping path
  dead-ends.
- Zero guides carry a known factual defect (currently seven: D1, D2, and D6 are
  names that do not exist; D3 a wrong config table; D4 a false claim about human
  gates; D5 a wrong primitive count; D7 an obsolete workspace entry shape).

## Scope / Non-goals

**In scope.** All 15 uplift rows in the audit's Part 7; the optional
chat-input slot in the `JOURNEY.md` `contract:` schema and its validator; the
path grouping in the audit's Part 8; the seven verified defects D1-D7; and the
two-mode tracker documentation the owner's first decision requires.

**Owner decisions, 2026-09-03.** Three questions this brief routed out have
been settled, and their consequences are in scope:

- **The catalogue supports multiple tracker modes.** The Atlassian
  write-back-to-Jira journey **survives**. It is not a contradiction to remove
  but a second supported mode to name and bound, alongside repo-first
  projection. Both modes must be documented, with the choice made explicit.
- **Light intents are the primary shaping path**; the robust path stays
  supported and must be **surfaced in the guides**, not deleted. This settles
  U12 and unblocks S6.
- **No workspace registration.** This ships in one session, so the brief and
  intent are not registered in `workspace.toml`.

**Out of scope.**

- Building a tracker exporter. The audit confirms a documented projection
  mapping with no live API integration, and `tracker-projection.md` records
  that deferral deliberately. This brief documents the mapping and both modes;
  it does not ship the export.
- Any change to skill behaviour. This is a documentation and schema outcome.
- Nothing else. The owner asked for the full set in one session, so **U12 and
  U14 are now in scope** and the row count is the full 15.

## Appetite

A few weeks, not a quarter. The bulk of the work is projection of content that
already exists in `JOURNEY.md` contracts and SKILL.md descriptions. Any slice
that turns into net-new authoring is a signal to stop and re-slice rather than
to spend.

## Assumptions / Risks

- **Constraint, not assumption.** The journey contract is closed:
  `journey_validator.py:69-75` rejects unknown contract fields. So S2 touches the
  validator, the authoring standard, the generator, and their tests, and the
  field must be **optional** — a required field breaks packs authored outside
  this repository. S2 is a **regression gate**: it stops the affordance being
  dropped again. It is not a content source for S3, because one pack-level
  utterance cannot supply distinct inputs to 30 skill-specific guides.
- **Assumption.** The 64 existing SKILL.md trigger phrases are correct
  invocations, so lifting them projects fact rather than inventing phrasing.
- **Assumption.** A path grouping is orthogonal to `kind:` and needs no file
  moves, so generated navigation and published URLs survive. **Open:** whether
  it needs a new frontmatter key at all. `contracts/guide.schema.json` sets
  `additionalProperties: false` (line 56) and already carries optional `journey`
  (line 33) and `order` (line 39) keys; S6 must test those before adding a
  third.
- **Retired 2026-09-03.** The Atlassian write-back conflict is resolved: both
  modes are supported. The residual risk is now *documentation* — a reader who
  cannot tell which mode they are in will mix them, so every tracker guide must
  name its mode.
- **Retired 2026-09-03.** The shaping-chain question is resolved: light is
  primary, robust is surfaced. The residual risk is that "primary" reads as
  "only", stranding the higher-uncertainty path; the robust route needs a
  visible entry point, not a footnote.
- **Risk.** The affordance measurement is regex-based. It proves presence, not
  quality, so a slice can satisfy the metric with a weak example. Slice
  acceptance criteria must name the exemplar
  (`architect/how-to/diagram-a-system.md`, the one file of 203 scoring 5/5)
  rather than the count alone. Two review rounds moved every headline count in
  this audit, so a slice that reports only a percentage has not shown its work.

## Delivery

**Delivered directly on 2026-09-03, without materializing slices.** The owner
asked for the full set in one session, so the ten candidate slices below were
executed as five file-partitioned lanes rather than as specs. No spec was
authored, nothing was registered in `workspace.toml`, and the brief never passed
the Ready gate — so its status stays `Draft` and the Spec map stays empty. That
is the accurate record, not an omission.

What shipped: the seven verified defects, plus three more classes of broken
link found in passing and 20 further broken links swept from the rest of the
guide tree at the owner's request — `guides/` now carries zero broken relative
links; the
`youType` contract field with its validator, standard, back-fills, and mutation
proof; chat inputs and outcomes across the how-tos and tutorials of eight packs;
invocation phrasing for 29 previously-unphrased skills; three new guides — the
shaping-to-build handover, repo-first tracker projection, and whole-lifecycle
install; the two-mode tracker framing; architecture-artifact registration; and
the six-path curriculum on the guides front door.

Measured outcome against the success metrics above: chat input 21% → 45%, stated
outcome 10% → 32%, skill phrasing 41% → 63%. The full before/after table is in
the audit's Result section. Two metrics were not met: a demonstrated workflow
input reached only 2 of 17 tutorials, and sample output did not move.

## Spec map

No slices are confirmed. The candidate slices below are proposals for the human
slice confirmation that `author-delivery-brief continue` owns; they are not
specs and are not registered as work.

| Spec | Status |
| --- | --- |

## Candidate slices

Ordered. S2 precedes the bulk passes to prevent regression, not to feed them.
S7 runs before S3 because it corrects names in files S3 also edits. Lanes are
partitioned by file, not by slice, so no two run in the same file.

| # | Candidate slice | Uplift rows | Why it is separately shippable |
| --- | --- | --- | --- |
| S1 | Document the shaping-to-build handover | U1, U7 | One new how-to, a link to it from the `architect` and `desk-research` guide sets, and an Inputs section in two governance guides; unblocks the owner's route on its own |
| S2 | Add an optional chat-input slot to the journey contract | U8 | Validator + authoring standard + generator + tests + 14 back-fills; a regression gate that must land before the bulk passes, but supplies no content to them |
| S3 | Project chat inputs and outcomes onto the shaping spine | U2, U3, U9 | 33 guides, source strings already exist; consumes the harvest table from `tools/audit-guide-affordances.py`, so it needs no output from S2 |
| S4 | Make the repo-first tracker position reachable | U4, U5 | One new `_shared` guide plus reframing two shipped ones; independent of the guide-affordance work |
| S5 | Wire architecture artifacts into the workspace | U6 | One registration step across the `architect` guides |
| S6 | Group the guides into ordered paths | U11, U12, U15 | Front-door, frontmatter, and navigation change; depends on S1 for P2's endpoint. Unblocked: P2 orders the light path and links the robust path as its alternative |
| S7 | Correct the seven verified defects | D1–D7 | Independent, small, and each one currently hands a newcomer a dead command or name |
| S8 | Bring tutorials to a demonstrated input | U10 | 17 files, the genre whose job is a worked run; currently 0/17 |
| S9 | Bring the two-file tracker packs to baseline | U13 | `linear` and `github`, two guides each |
| S10 | Author invocation phrasing for the design and frontend packs | U14 | 29 SKILL.md descriptions; the only net-new authoring, so it runs last and its phrasing is checked against each skill's own body |
| S11 | Document both tracker modes and how to choose | owner decision 1 | Names repo-first projection and tracker-authoritative write-back as two supported modes, with a selection rule; depends on S4 for the projection half |

## Rabbit holes

- **Rewriting the audit instrument into a shipped lint.** The instrument
  measures presence by regex and was built to size the problem. Promoting it to
  a gate is its own decision — S2's lint is scoped to the journey contract
  field, not to prose affordances.
- **Re-litigating Diataxis.** The `kind:` axis works and drives generated
  navigation. The path axis is additive.
- **Expanding the tracker mapping into a sync design.** The one-way rule in
  `tracker-projection.md` is load-bearing; documenting it is not an invitation
  to design round-tripping.
- **Fixing every guide to 5/5.** Explanation and reference pages do not need a
  chat input or a demonstrated input. The target is every guide that documents
  an invocable skill, not every file.

## Source

- Mode: repo-origin
- Locator: docs/product/intents/sdlc-guide-uplift-and-learning-paths.md
- Revision: sha256-bytes-v1:d0ff456f4541b9d2b06819ac7b886ffdfe670f08772f1a4791c3b8eece213cf3

## Supporting artifacts

- [Feature intent](../intents/sdlc-guide-uplift-and-learning-paths.md) — the
  outcome, opportunity, and what the decision requires.
- [New-team SDLC adoption — journey map and guide uplift audit](../findings/new-team-sdlc-guide-uplift-audit.md)
  — the evidence: the six-phase journey, the five-affordance measurement over
  203 guide files, the 15-row uplift table keyed to source content, the proposed
  path structure, and the seven verified defects with per-file evidence.
