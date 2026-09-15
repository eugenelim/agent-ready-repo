# Spec: review-recurrence-family-key

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0104](../../adr/0104-light-mode-review-stops-on-divergence.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A review finding carries a second identity that survives being moved,
renumbered, or re-graded.

The existing fingerprint, `sha256("<file>|<line>|<title>")`, identifies a
finding within a round and is unchanged. The **family** drops every part of that
preimage that moves while the finding does not, and is emitted beside the
fingerprints on the classification payloads.

This slice derives and exposes the key. Nothing stores it, nothing compares it
across rounds, and no count or verdict is computed from it. Those belong to the
follow-on unit named below, which is a state-schema and public-interface change.

### Why the current key cannot carry recurrence

`state-schema.md` records `finding_fingerprints` as
`sha256("<file>|<line>|<title>")` per finding and names stasis detection as its
consumer. Three parts of that preimage move while the finding does not:

| Part | Moves when | Present in |
| --- | --- | --- |
| The cited line | any repair edits above the finding | every finding |
| The leading ordinal, captured inside `<title>` by the finding patterns | an earlier finding is retired and the survivors renumber | every finding — the pattern requires it |
| A bracketed severity tag, also inside `<title>` | a finding is re-adjudicated | most titles |

The ordinal is the decisive one. A converging round retires findings, so the
survivors renumber, so every survivor hashes differently — in exactly the case
recurrence detection exists to see.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable — a new key on shipped classification payloads | `references/finding-adjudication.md` | Spec owner | The file names the key, its preimage, and that nothing yet consumes it | AC-0009 |
| Current architecture | Applicable — the loop contract page describes full mode's review termination | `docs/architecture/loop-contract.md` | Spec owner | The page states that identity within a round is keyed with position and recurrence across rounds without it | AC-0010 |
| Release history | Applicable — core pack content changes | `docs/product/changelog.md` | Spec owner | Changelog entry naming the core bump | Entry present, version matches the pack manifests |
| Reusable learning | Applicable — a position-bearing identity hash cannot track an item across an edit that moves it | `project-knowledge --capture` | Spec owner | A topic recording the trap and the two-keys-two-jobs split | Captured at a semantic gate after ship |
| Decision rationale | Not applicable | — | — | — | No decision is settled here; the ADR question is in Follow-ons |
| User-facing promise, current product truth, operations, maintainer procedure | Not applicable | — | — | — | Internal to the review loop |

## Boundaries

### Always do

- Keep `matches_previous_round` byte-identical in value for every input.
- Emit the family key on every classification payload that already carries
  `fingerprints`, including the payload a report classified `invalid` returns.

### Ask first

- Any change to the existing fingerprint preimage or its within-round dedup.
- Adding the family key to `review raw-classify`, whose field set is
  deliberately closed.
- Adding the family key to any reviewer format beyond the three the finding
  parser already handles.

### Never do

- Add a state field, a CLI flag, a rotation, a count, a comparison across
  rounds, or any change to the recorded payload digest. Every one of those
  belongs to the follow-on unit, and admitting one here reintroduces the
  replay-semantics question this slice exists to avoid.
- Add a stop, gate, cap, or transition keyed on the family. ADR-0104 decides
  this for both modes and records the measurements behind it, including its
  rejection of the family-recurrence stop that
  `review-loop-nonconvergence-survey.md` § 6 option 3 proposed. That ADR also
  states why an absence sweep cannot mechanically protect the boundary, so it is
  prose here by design rather than by omission.
- Modify `packages/agentbundle/`, `loop-engine.py`, `_loop_guards.py`,
  `review_retry_count`, or `max_review_retries`.
- Add a top-level dependency, a new module, or a new script.

## Testing Strategy

- **Family key derivation (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005)** — TDD.
  The stable-title normaliser is a pure function with a compressible invariant.
  Each instability has an obvious disconfirming case — one part changed, same
  family expected — and the two negative cases fix the other edge, so a
  normaliser that strips too much also reds.
- **Reviewer-format coverage (AC-0006)** — TDD. A closed set of three formats, so
  the oracle is one case per member rather than a sample. The experience-reviewer
  case exercises the no-line branch, which hashes a location rather than a file
  and a line.
- **Payload shape (AC-0007, AC-0008)** — TDD. A shape assertion per named
  producer. AC-0007's `invalid` member is the one that reds if the key is added
  only on the success path, which is the likeliest way a consumer breaks.
- **Compatibility (AC-0011)** — TDD. A characterisation test over the existing
  flag's inputs, which must not move.
- **Documentation (AC-0009, AC-0010)** — Goal-based check. Presence assertions
  against required wording, so there is something falsifiable to match.

**What is not mechanically protected.** Nothing here proves the family key is
*useful* — that it matches a real finding across a real repair. The evidence for
that is the plan's spike, which measured title instability structurally and
could not measure semantic rewording, because no corpus of real multi-round
reports was reachable. The first mechanical answer arrives with the follow-on
unit, which is the first thing to compare families across rounds.

## Acceptance Criteria

**Family.** A finding's family identifies the same finding across rounds where
the fingerprint cannot, because the fingerprint's preimage carries position that
a repair moves. The plan's *Data & schema* owns both preimage forms and the
normalisation; the criteria below fix the properties that normalisation must
have, which is what makes them checkable without restating it.

### Family key

- [ ] **AC-0001.** Two findings sharing a cited location and a stable title, and
  differing only in cited line, produce the same family.
- [ ] **AC-0002.** Two findings sharing a cited location and a stable title, and
  differing only in leading ordinal, produce the same family.
- [ ] **AC-0003.** Two findings sharing a cited location and a stable title, and
  differing only in bracketed severity tag, produce the same family.
- [ ] **AC-0004.** Two findings differing in stable title produce different
  families.
- [ ] **AC-0005.** Two findings differing in cited location produce different
  families.
- [ ] **AC-0006.** Each of the three reviewer formats the finding parser accepts
  produces a family for every finding it produces a fingerprint for.

### Payload

- [ ] **AC-0007.** The family key is present on each of the three classification
  payloads — the one `review inspect --json` emits, the one
  `review classify --json` emits, and the one returned for a report classified
  `invalid` — and is an empty list on the `invalid` payload. The first two are
  distinct call sites through one emitter; only the `invalid` return is a
  separate builder, so the third case is the one that can fail alone.
- [ ] **AC-0008.** `review raw-classify`'s field set is unchanged.

### Documentation

- [ ] **AC-0009.** `references/finding-adjudication.md` names the family key and
  its preimage, and states that nothing consumes it yet, so a reader cannot
  mistake it for a signal already in use.
- [ ] **AC-0010.** `docs/architecture/loop-contract.md` states that identity
  within a review round is keyed with position and recurrence across rounds is
  keyed without it.

### Compatibility

- [ ] **AC-0011.** For the `findings` and `clean` classifications,
  `matches_previous_round` remains a function of the round's canonical
  fingerprint set and the `finding_fingerprints` value the classifier reads —
  not `previous_finding_fingerprints`, which is a separate documented key the
  comparison does not use.

## Follow-ons

- **Retiring full mode's stasis stop disposition** is specified separately, in
  [`stasis-stop-retirement`](../stasis-stop-retirement/spec.md). ADR-0104 decides
  the retirement; that spec carries it out. This spec has one dependency on it:
  ADR-0104 requires recurrence to be Surfaced, and today the only shipped
  Surface instruction sits in the same sentence as the halt being removed. That
  spec preserves the Surface disposition; this one supplies the key read there.

- **The follow-on unit: store families and compare them across rounds.** This
  slice exposes the key; nothing yet uses it. Comparing rounds requires a state
  field pair, a way for family digests to reach `review record` — whose findings
  branch takes digests from `--fingerprint` on the command line and never
  re-parses the report — rotation across the three record paths that rotate the
  fingerprint pair today, and a decision on whether families enter the recorded
  payload digest. They must, or two rounds with equal fingerprints and unequal
  families collide as a replay; including them changes replay semantics. That is
  a state-schema and public-interface change and takes its own spec.
- **Retiring `matches_previous_round`'s stop route.** ADR-0104 decides it: the
  route is retired rather than re-keyed. Carrying that out — removing the
  disposition from `references/finding-adjudication.md` and
  `references/state-schema.md` — is not in this slice, which only makes the
  replacement signal derivable. Owner: the work-loop maintainer.
- **Nothing collects the key, so nothing can calibrate anything built on it.**
  `repair-origin-gating-survey.md` § 10 records that `state.json` is per-run
  scratch, gitignored, so observations are discarded. A committed sink is the
  blocker on ever revisiting the never-gate boundary with evidence.
- **This slice implements one half of ADR-0104's full-mode decision.** The ADR
  retires the stasis stop route and makes the recurrence signal advisory; this
  spec delivers only the position-free key the signal needs. Removing the
  retired route's disposition from the shipped reference docs is the other half
  and has no spec yet.

## Assumptions

- Technical: the recurrence key embeds position — the `finding_fingerprints` row
  of `references/state-schema.md` documents `sha256("<file>|<line>|<title>")`,
  and the finding patterns capture the ordinal inside the title group.
- Technical: the findings branch of `cmd_review_record` takes digests from
  `--fingerprint` and never re-parses the report, which is why storage is a
  separate unit rather than part of this one.
- Technical: `review raw-classify` projects a deliberately closed field set and
  reaches neither the classifier nor state, so it is excluded by AC-0008.
- Technical: the human-readable print line is a hand-written format naming three
  fields; the family key is a digest list and is emitted on the JSON payloads
  only. The text line is unchanged.
- Technical: light mode's `review classify` calls the same classifier with an
  empty state dict, so it emits the family key and reads nothing from it.
- Technical: `_invalid` is a module-level function holding no state, so its
  family value can only be the empty list. AC-0007 contracts that rather than
  leaving it an implementation accident.
- Technical: no `packages/agentbundle/` coupling; a search for the cohort and
  fingerprint identifiers finds only a docstring path mention in a catalogue
  lint test.
- Technical: `loop-engine.py` contains no fingerprint reference.
- Process: a core pack bump and its file set are owned by
  [`packs/AGENTS.md`](../../../packs/AGENTS.md) § *Version bump rule*. This
  branch already carries an unreleased bump from another change, so the target is
  a patch above whatever the manifests hold at execution time, never a literal
  fixed at authoring time.
- Process: `workspace.toml` registration is selective, so this spec is not
  registered unless the owner asks.
