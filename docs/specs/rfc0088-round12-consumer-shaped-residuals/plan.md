# Plan: rfc0088-round12-consumer-shaped-residuals

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

## Approach

Five tasks: shared apparatus first, the three commissioned measurements, then
promotion. T0 changes the gates and rails that every later artifact needs, so no arm
can create an artifact before the apparatus capable of rejecting it exists.

The planned runner is explicit-allowlist only. It retains the historical runner’s
restored bytes, keeps only the system-browser input needed by the signing arm, requires
browser-cache and short-temporary-directory inputs, reads privacy patterns from an
operator-supplied external term file, and hard-fails when the signing requirement file is absent. It
does not carry external endpoint inputs or a signing-requirement default.

## Constraints

- No dependency, toolchain, compile step, real credential/profile/account, live
  authenticated session, local-account creation, or administrator operation.
- Fixtures bind loopback ephemeral ports; recorded addresses are redacted.
- Live token material remains only in the issuer process. Decoys are distinct,
  labelled values; transient staged-copy mutations are restored before promotion.
- Privacy-exemption records live in a non-regenerated source member. A mandated
  shared-tool edit may refresh only its digest after a scan confirms count stability;
  all other changes remove the exemption.

## Construction tests

T0 and T6 are goal-based checks. T1–T3 are visual/manual QA with no red stub. Each
task lists its enforcing controls before its approach. Gate outputs retain control and
harness counts; the published note does not.

## Tasks

### T0: Shared runner, privacy, purge, and corpus apparatus

**Depends on:** none
**Touches:** `run-r11.sh` (restore), `run-r12.sh` (new),
`s1/confined-remove.mjs` (new), `r12-privacy-term-policy.json` (new),
`r12-privacy-exemptions.json` (new), `corpus_docs.py`, `build-archive.py`,
`s1/redact.mjs`, `r9-privacy-sweep.py`, `r9-promote.sh`,
`verify-note-figures-r7.py`

**Tests:** goal-based. `Done when:` runner absent-input controls fail; expected
row inventory rejects omission; confined removal rejects all four escape classes;
privacy consumers reject empty and count-minus-one terms; and each declared shared
tool meets its AC9 earlier-input compatibility check.

**Approach:** Restore `run-r11.sh`; create `run-r12.sh` with no endpoint pass-throughs
and only required system-browser, cache, temporary-root, term-file, and
requirement-file inputs. Add the named confined-removal helper. Derive the exemption
table by scan into its protected source member, applying the declared-edit rule.
Centralise figure-corpus membership so the round-12 note can be registered in T6, and
make promotion use that list in order. Add the operator-supplied term-file contract to both privacy consumers
and the outer gate chain. Satisfies AC1; AC5 requirement-file/runner clauses; AC6
missing-row, removal, and privacy mutations; AC7 term-source/count clauses; and AC9
runner restoration, corpus, exemption, and per-tool compatibility clauses.

### T1: Destination-scoped worker policy

**Depends on:** T0
**Touches:** `s3/r12-destination-scoped-worker-policy.mjs` and results

**Tests:** manual QA. Global block breaks the worker-dependent destination; global
allow observes registration; selective purge retains its retained store; whole-profile
purge removes both stores.

**Approach:** Execute global-allow, global-block, and destination-policy arms over
synthetic role-addressed destinations. Route every removal through the helper and
report a non-scopable clause as a finding. Satisfies AC2 and AC6 worker-policy
control mutations.

### T2: Page-resident token and durable-surface boundary

**Depends on:** T0
**Touches:** `s3/r12-page-resident-token.mjs` and results

**Tests:** manual QA. No shim fails; every mandatory encoded decoy and browser-written
cookie/local-storage decoy is detected; cap truncation fails; log deletion is observed.

**Approach:** Use a distinct loopback issuer and page-resident replay code. Enable all
declared logging, byte-scan every file under profile/download roots, self-report argv
and environment names, then delete non-promotable logs through the helper. Record the
same-uid residual beside the result. Satisfies AC3, AC4 except T6’s staged-member
clause, and AC6 token-surface mutations.

### T3: Signing-identity anchor

**Depends on:** T0
**Touches:** `s1/r12-signing-identity-anchor.mjs` and results

**Tests:** manual QA. Both binaries produce separate strict and requirement rows; an
unrelated resource failure does not admit the absence control; a modified copy fails.

**Approach:** Read the requirement only from its temporary-root file, emit redacted
categories and realpath booleans, and retain update survival solely as the deferred
backlog property. Satisfies AC5 verification clauses and AC6 signing-control
mutations.

### T6: Promotion, note, RFC evidence layer, and negative tests

**Depends on:** T0, T1, T2, T3
**Touches:** round-12 note; RFC evidence layer only;
`docs/rfc/0088-notes/spikes/round7-evidence-archive.md`; `r12-fact-negative-tests.py`;
`workspace.toml`; `s1/r12-host-owned-profile-reattach.mjs` and results;
`s2/r12-provider-adapter-packaging.mjs` and results;
`s3/r12-per-destination-policy.mjs` and results;
`s3/r12e2-post-auth-reattach-worker-dependency.mjs` and results

**Tests:** goal-based. `Done when:` only T2-verified artifacts promote; staged-copy
decoy search catches and restores its mutation; every gate passes in the required
order; note figures respect AC8; and contradiction names appear in both documents.

**Approach:** Publish measured facts without changing RFC decisions and add the
round-12 note to the already-centralised `corpus_docs.docs()` list. Run the staged
member-copy positive control before the promoted-state decoy absence check. Record
gate output separately from note prose, then run all gates in Testing Strategy order.
Satisfies AC4 promotion clauses; AC6 remaining mutations; AC8; AC9 promotion checks;
and AC10.

## Rollout

- **Delivery:** one PR; one note and one RFC evidence layer cover all measurements.
- **Infrastructure / external systems:** none. Fixtures are local loopback only.
- **Deployment sequencing:** T0, then T1–T3, then T6.

## Risks

- A worker clause may not be destination-scopable; that is a finding.
- Token scanning can be fooled by encoding or binary stores; mandatory encodings and
  browser-written decoys keep the control non-vacuous.
- Shared-tool edits can alter historical verdicts; each tool has a concrete earlier
  input compatibility check before measurement artifacts run.

## Changelog

- 2026-08-19 — Amended AC7 under AGENTS.md § Privacy: organisation identifiers may
  not be committed even when non-secret. T0 implementation found the contradiction
  when `build-archive.py` correctly refused the committed term file; both consumers
  now require an operator-supplied external source. T0 corpus wording now correctly
  assigns round-12 note registration to T6.
- 2026-08-19 — T4 and T5 were deferred to round 13; their task identifiers were not recycled.
- 2026-08-18 — Review-round-3 rewrite: moved shared rails before arms; defined the
  privacy corpus and reproducible term source; strengthened token, signing, removal,
  exemption, compatibility, and promotion controls.
