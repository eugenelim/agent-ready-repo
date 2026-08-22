# Spec: rfc0088-round14-destination-adapter-contract

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0088](../../rfc/0088-web-pilot-foundation.md) — Experimental. This spec amends
    open question 3's bar in the amendment layer, records four decision records and one
    scope residual there, and adds one measurement arm. It moves no status field,
    closes no blocker item, and creates no follow-on artifact.
  - [RFC-0093](../../rfc/0093-intent-scoped-completion.md) — the accepted intent is the
    whole round; it is delivered as one review unit in one session.
- **Contract:** none for production interfaces. This spec produces an RFC
  amendment-layer entry, one evidence note, one digest entry, and changes only the
  existing out-of-repository evidence apparatus named in the plan.
- **Shape:** service

## Objective

Round 14 answers the one question that blocked open question 3 from being ruled
usefully: **what should the bar actually measure?** The recommended default counted
shipped consumers. That count is unsatisfiable in principle, not merely unsatisfied —
`web-pilot`'s legitimate destinations are predominantly operator-internal surfaces no
pack may bundle, so the count measures what the pack is *permitted to ship* rather than
whether the foundation works.

The bar is therefore re-denominated as a **destination adapter contract**, exercised by
two independent fixtures of differing render and authentication shape, plus one
documented reference consumer an adopter runs against their own account. The contract
is asserted in CI; the reference consumer is a recorded observation.

Two things follow that this round has to *establish* rather than assert.

**The fixture pair has to be measured, not proposed.** A bar naming two fixtures of
differing shape is empty until two such containers are known to exist, to start, and to
differ in the way claimed. This round stands them up and observes them.

**The measurement that selects them also tests open question 5.** Round 12 established
the page-resident replay accommodation *conditionally* — it held only when the issuing
response was marked `no-store` — against a synthetic issuer this project controls. The
condition is a property of a destination, so it had never been tested against one. This
round tests it, and it does not hold.

### Sequencing, recorded rather than backfilled

The measurement was taken **before** this spec was written. That ordering is deliberate
and is not presented as anything else: the fixture pair could not be specified until it
was known which candidates start as a single pinned container, and the leading
candidate was eliminated only by trying to run it. This spec describes the intended
final state and the already-observed repository reality; no implementation chronology
is implied that did not happen.

## Boundaries

- **No follow-on artifact.** RFC-0088 is `Experimental`, so no ADR file, no `Spec 1/2/3`
  and no `auth: browser-session` convention artifact is created. The four decision
  records live in the RFC's amendment layer, which the RFC already designates as the
  authoritative current contract, and graduate to ADRs on acceptance.
- **No production interface changes.** No pack, no adapter, no CLI surface.
- **No third-party contact from the repository.** Fixtures are pinned containers reached
  over loopback. The reference consumer never runs in CI.
- **No captured fixtures.** Every fixture is synthetic and created against the container
  at run time. A recorded response would place third-party content and personal data in
  the repository.
- **No credential, personal identifier, or destination origin** in the repository or in
  any results artifact. Generic placeholders only.
- **No terms-of-service or case-law reasoning** in any repository artifact. The
  amendment layer receives architectural statements only.

## Acceptance criteria

- [x] **AC1 — Open question 3's bar is amended in one place, and no earlier reading of
  it survives.** The amendment layer states the bar as a destination adapter contract
  exercised by two independent fixtures of differing render and authentication shape
  plus one documented reference consumer, and closes with "The contract is asserted in
  CI; the reference consumer is a recorded observation." The superseded count-based
  ruling is **rewritten, not appended to**, so the RFC carries exactly one answer to
  question 3.
- [x] **AC2 — Open question 4's ruling is untouched.** The per-destination-group worker
  policy re-draft and its carried `rfc0088-destination-group-split-cost` residual are
  unchanged by this round.
- [x] **AC3 — Four decision records and one scope residual are recorded as
  architecture.** Authentication as an optional layer; per-destination degradation as
  first-class; credential resolution through the broker and never across a process
  boundary to a model; a pinned container as the load-bearing CI fixture. Plus the
  withdrawn scope narrowing's one surviving constraint. Each states what the approver
  accepts by taking it.
- [x] **AC4 — The credential-free core and the live-session layer are separable, and
  the fixture pair can tell them apart.** This is structural, not conventional: the
  server-rendered half's credential is unreadable by page script, so a page-resident
  consumer cannot operate against it *at all*, while page driving against it is
  unaffected. A pair that could not distinguish the two layers would let a build
  conflate them and still pass.
- [x] **AC5 — The fixture pair is selected on measurement, and the rejection is
  recorded with its reason.** Both halves are pinned container images. Their render
  shapes are observed from the login document as delivered — one arrives without a
  `<form>` element or password input and acquires both under script; the other arrives
  with each already present. The leading candidate's elimination (its server refuses to
  start without a cluster API, so it is a control plane and not a pinned container) is
  recorded as a measurement, not a preference.
- [x] **AC6 — The token-landing and cache-control observations are recorded as a
  finding against open question 5, and question 5 stays outstanding.** The issuing
  response carries no cache directive; the destination's own frontend writes the token
  to a page-readable web-storage key from which it reaches browser user-data at rest.
  The record states plainly that no consumer controls either, so the accommodation's
  precondition sits outside the boundary this RFC governs.
- [x] **AC7 — The measurement arm carries a declared row inventory, in-region anchor
  uniqueness, and a mutation harness that fails on a stale anchor rather than
  skipping.** Every declared row has a mutation that changes that row's outcome, the
  harness asserts the flipped value, and the unmutated baseline is recorded immediately
  before the harness runs so both directions are observed.
- [x] **AC8 — Declared-failing rows mutate toward passing.** For a row whose recorded
  outcome is a finding, the risk is not a spurious failure but a row that could never
  have passed. Both declared-failing rows are mutated in the passing direction.
- [x] **AC9 — Absence claims are decoy-verified.** The at-rest scan plants a labelled
  decoy and requires its recovery; a buffer with no recovered plant is recorded
  absence-unverifiable and supports no absence claim.
- [x] **AC10 — No credential reaches the results artifact, asserted over serialized
  bytes.** The privacy row scans the serialized artifact for every encoded form of the
  issued token and the fixture credential, rather than trusting the construction code.
- [x] **AC11 — The reference consumer is an observation with provenance, never an
  acceptance criterion.** Its unauthenticated surface is probed read-only; the
  public-by-identifier case and the gated manager-scoped case are both recorded, and the
  private-league case is named as unmeasured with the one input that would close it. No
  identifier enumeration was performed against a third party.
- [x] **AC12 — The round's governance controls stay green.** The digest covers the new
  note with exactly one entry; the decision surface still carries one record per open
  question; every RFC hunk sits below the `## Amendments` anchor; the follow-on-absence
  detector reports nothing created.
- [x] **AC13 — The round's verdict remains NOT FINAL with its carried residuals
  unchanged.** No residual is relabelled, and no disposition moves. This round adds
  evidence and amends one bar; it does not shorten the tail.

## Testing strategy

Goal-based checks and one measurement arm; no production code changes, so no unit
surface.

- **Governance controls** — `r13-digest-coverage.py`, `r13-decision-surface.py` (and its
  follow-on-detector self-test), and `r13-spec-consistency.py` are run against the
  working tree. These are the checks that would catch a frozen-body edit, a missing or
  duplicated digest entry, a prohibited apparatus figure, and a created follow-on
  artifact.
- **Measurement arm** — the driver is run unmutated to record the baseline, then run
  under its own mutation harness. A row that does not flip, or an anchor that is not
  unique within the mutable region, fails the harness loudly.
- **Repository gates** — `SKIP_SAST=1 make build-check`, the documentation-entry link
  tests, and the site link check, via the round's existing gate chain.

## Non-goals

- Building the adapter contract the amended bar names. That is implementation, gated
  behind RFC acceptance and separate authorisation.
- Closing open question 5. This round supplies a finding against its recommended
  accommodation; deciding which destination behaviours the pack will refuse to
  accommodate is a ruling, not a measurement.
- Registering the new note in the figure-verifier document corpus. Doing so brings it
  under claim accounting, which this round did not commission; the note states the
  limitation.
