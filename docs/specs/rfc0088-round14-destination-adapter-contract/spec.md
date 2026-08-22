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

The bar is therefore re-denominated. Its canonical statement is the blockquote in
RFC-0088's amendment layer, and this spec deliberately does not restate it — the same
entry declares that a bar written twice is a bar that disagrees with itself at the first
edit, and a spec that copies it would be the second copy. AC1 quotes its closing
sentence, which is an assertion about the text rather than a second home for the bar.

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

### Always do

- Put every RFC hunk **below** the `## Amendments` anchor; the body above it is frozen.
- Pin each fixture by image digest, and record the digest where a reader can re-derive
  the measurement from it.
- Record a residual that cannot be measured as a residual, naming the one input that
  would close it — never as a weaker claim that can be met.
- Re-run the inherited apparatus controls after touching anything shared, and the
  privacy sweep with its detector self-test, so a clean result is not a vacuous one.

### Ask first

- **Probing any third-party surface**, even read-only and unauthenticated. The
  reference-consumer probe in T2a is the only one this round performs; it is
  operator-run, outside the repository's execution path, and bounded to a handful of
  requests against documented public endpoints. Enumerating identifiers to find a
  private one is refused outright, not asked about.
- Registering a new note in the figure-verifier document corpus, which brings it under
  claim accounting and changes what later rounds must maintain.
- Adding any repository dependency, toolchain, or compile step.

### Never do

- **Create a follow-on artifact.** RFC-0088 is `Experimental`, so no ADR file, no
  `Spec 1/2/3` and no `auth: browser-session` convention artifact. The four decision
  records live in the RFC's amendment layer, which the RFC already designates as the
  authoritative current contract, and graduate to ADRs on acceptance.
- Change a production interface — no pack, no adapter, no CLI surface.
- Create any path by which the repository or CI contacts a third party **beyond the
  one allowlisted egress AD-4 names**. Fixtures are reached over loopback once pulled;
  the digest-pinned registry pull is that egress, and calling it an absence of egress
  would be the claim AD-4 explicitly withdraws. The reference consumer never runs in CI.
- Capture a fixture from a live account. Every fixture is synthetic and created against
  the container at run time; a recorded response would place third-party content and
  personal data in the repository.
- Put a credential, personal identifier, account relationship, or destination origin in
  the repository or in any results artifact. Generic placeholders only.
- Put terms-of-service or case-law reasoning in any repository artifact. The amendment
  layer receives architectural statements only.

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
- [x] **AC4 — The fixture pair discriminates the credential-free core from the
  live-session layer, and a declared row fails if it does not.** This is structural, not
  conventional, and it is checked rather than argued: `R14-SR-TOKEN-NOT-PAGE-READABLE`
  asserts that the contrast half's credential is unreadable from page script — no
  JS-visible cookie, no web-storage entry — on a session `R14-SR-AUTHENTICATED-SESSION`
  has separately proven is authenticated. A page-resident consumer therefore cannot
  operate against that half at all, which is what makes the live-session layer separable
  from page driving rather than a precondition of it. Both rows carry mutations, and the
  contrast row carries a second case aimed at the `HttpOnly` conjunct specifically, so
  the property the criterion rests on is not the one conjunct nobody tests.
- [x] **AC5 — The fixture pair is selected on measurement, and the rejection is
  recorded with its reason.** Both halves are pinned container images. Their render
  shapes are observed from the login document as delivered — one arrives without a
  `<form>` element or password input and acquires both under script; the other arrives
  with each already present. Both are pinned by image digest, recorded in the note. The
  leading candidate's elimination is recorded as a measurement rather than a preference,
  and is re-derivable: the note quotes the fatal startup line its server emits with no
  cluster configuration, which is what makes it a control plane and not a container.
- [x] **AC6 — The token-landing and cache-control observations are recorded as a
  finding against open question 5, and question 5 stays outstanding.** On the half that
  issues a token, that response carries no cache directive; the destination's own
  frontend writes the token to a page-readable web-storage key from which it reaches
  browser user-data at rest. The claim is scoped to that half in every place it appears,
  because the contrast half issues no token and its cookie arrives `private`-marked.
  The record states plainly that no consumer controls either, so the accommodation's
  precondition sits outside the boundary this RFC governs.
- [x] **AC7 — The measurement arm carries a declared row inventory, in-region anchor
  uniqueness, and a mutation harness that fails on a stale anchor rather than
  skipping.** Every declared row has a mutation that changes that row's outcome, the
  harness asserts the flipped value, and the unmutated baseline is recorded immediately
  before the harness runs so both directions are observed. The harness's own summary is
  persisted beside the results artifact, because the artifact's `coverage` block is
  derived from the row inventory and would report clean whether the harness ran or not.
  A row that is a conjunction carries a case per load-bearing conjunct, not one per row.
- [x] **AC8 — Declared-failing rows mutate toward passing.** For a row whose recorded
  outcome is a finding, the risk is not a spurious failure but a row that could never
  have passed. Both declared-failing rows are mutated in the passing direction.
- [x] **AC9 — Absence claims are decoy-verified.** The at-rest scan plants a labelled
  decoy and requires its recovery; a buffer with no recovered plant is recorded
  absence-unverifiable and supports no absence claim.
- [x] **AC10 — No credential, origin or fixture identity reaches the results artifact,
  and a detected leak blocks the write.** Two passes, because the row's own result is
  part of the artifact and a single pass over the final bytes cannot produce the row it
  must contain. Pass one yields the row; pass two scans the exact bytes about to be
  written and refuses the write on a hit, emitting a counts-only refusal instead. The
  needle set covers the issued token, the fixture credential, both destination origins
  and the fixture user name — origins included because a navigation timeout embeds the
  URL in the error text and that text reaches the failure record.
- [x] **AC12a — No browser user-data directory survives any exit path, and a survivor
  is fatal.** The temporary profile holds the live token, so its removal is the round's
  highest-consequence control and is asserted rather than described: `R14-PROFILE-REMOVAL`
  fails if either profile remains, symlinks are unlinked before the confined removal (a
  browser that exits uncleanly leaves `SingletonLock` behind, and the confined remover
  refuses a symlink-bearing tree by design), a forced removal backs that up, a root that
  survives every path is a fatal outcome rather than a field, and signal handlers cover
  the interrupt path because `finally` does not run on a kill. Confinement is established
  before anything is unlinked, so the blessed helper is used rather than bypassed.
- [x] **AC11 — The reference consumer is an observation with provenance, never an
  acceptance criterion.** Its unauthenticated surface is probed read-only; the
  probe date, the four surfaces and their observed status codes are recorded in a table
  in the note, so the observation can be re-run rather than taken on trust. The private
  variant is named as unmeasured with the one input that would close it. No identifier
  enumeration was performed against a third party, and the provider is described by
  shape rather than named — including its endpoint vocabulary, because a provider's API
  terminology identifies it as surely as its name does.
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

- **Governance controls** — `r13-digest-coverage.py` and `r13-decision-surface.py` (with
  its follow-on-detector self-test) are run against the working tree. These are the
  checks that would catch a frozen-body edit, a missing or duplicated digest entry, a
  prohibited apparatus figure, and a created follow-on artifact.
  `r13-spec-consistency.py` is deliberately **not** listed: it hard-codes round 13's spec
  directory, so running it here exercises nothing of round 14's, and reporting its green
  result as this round's evidence would be a skip dressed as a pass. It is still run, as
  a regression check that round 14 did not disturb round 13.
- **Inherited apparatus controls** — the archive self-tests and the privacy sweep with
  its detector self-test, because extending a shared tree has previously disabled a
  second harness silently. The detector self-test is what stops a clean sweep from being
  a vacuous one.
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
