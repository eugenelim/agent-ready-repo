# Spec: rfc0088-round12-consumer-shaped-residuals

- **Status:** Shipped (reconciled 2026-08-25: round 13 completed AC4's staged-member decoy search and AC6's mutation coverage; their frozen-body tokens were removed under owner authorization)
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0088](../../rfc/0088-web-pilot-foundation.md) — Experimental; this spec
    measures open questions 4, 5, and 6 and changes no disposition
- **Contract:** none for production interfaces — this spec produces evidence and
  changes only the existing evidence-tree apparatus named in the plan.
- **Shape:** service

## Objective

Round 12 measures the three consumer-shaped open questions RFC-0088 assigns to the
approver: destination-scoped worker policy, a page-resident replay token boundary,
and a signing-identity anchor. That measurement is this round's purpose and
deliverable.

It also repairs the shared apparatus controls those measurements depend on. Round 12
found the organisation-identifier privacy gate had never run: its term input was
unset, no runner supplied it, and the archive gate silently returned on an empty list.
A gate that cannot fail cannot admit this round's artifacts, so repairing that control
is a measurement precondition, not a separate ambition.

The round records measurements against each open question's recommended candidate;
it does not answer the question or change a disposition. The approver decides at
Experimental exit.

Each measurement arm that runs produces a row that could have failed. A
contradicting arm is a finding, not an implementation decision. Separate-uid
attachment isolation and worker-purge inventory are deferred to round 13; neither
is measured here.

The round publishes no apparatus figures: no coverage percentage, claim-accounting
total, mutation-corpus figure, or harness count in the note. Control counts that
establish whether a control can fail are in scope only in gate output.

## Boundaries

### Forbidden identifiers and privacy corpus

No round-12 artifact, note, fixture, or commit may contain a real vendor, product,
employer, tenant, or account identifier; signing-team identifier; non-loopback URI;
credential value; home directory; per-user temporary path; or hostname. A numeric uid
is permitted in results provenance: the platform's default first-user uid is not an
identifier; an arm may instead record a same-uid boolean.

For this rule, a non-loopback URI is a URI whose host is not `localhost`, `127.0.0.1`,
or `[::1]`; those loopback forms are excluded. The **round-12 privacy corpus** is
only round-12 drivers, round-12 results, and the round-12 note. It is neither
`corpus_docs.docs()` nor the inherited privacy-sweep glob corpus.

At execution, a scan derives the pre-existing exemption table from manifested
members. Each record is `(member path, occurrence count, digest)` and contains no
matched literal. The table is frozen in a source member that the archive-note
regenerator never rewrites. A changed member removes its exemption; the set cannot
widen without a spec amendment. The sole planned exception is a declared shared-tool
edit: its digest is re-recorded in the same task only after the scan confirms the
unchanged allowed occurrence count.

### Always do

- Run subprocesses under an explicit allowlist; record variable names and presence
  booleans only. Every `env -i` runner requires an explicit browser-cache path and a
  short temporary directory.
- Give every arm a control that fails when the tested control is removed, and admit
  an arm only when its control failed in that run.
- Read platform and identity state, fixture-server loopback binding, and expected
  row-id inventory back from results rather than asserting requested state.
- Bind every fixture server to loopback on an ephemeral port.
- Route recorded observables through the shared redaction helper.
- Route every round-12 purge through the single manifested `s1/confined-remove.mjs` helper:
  real-path resolution; separator-bounded root containment; symlink/junction
  refusal; depth and entry bounds; root-relative recording.
  The carried round-11b purge remains outside this round's implementation scope.
- Mutation-test every new fact and control individually (AC6).

### Ask first

- Adding a dependency, toolchain, or compile step.
- Creating a local OS account or performing an administrator operation.
- Using a credential, account, or live authenticated session at a destination.
- Extending the round beyond the three commissioned measurements and promotion.
- Changing an RFC decision, disposition, blocker item, or status field.

### Never do

- Implement production packs, runtime code, dependencies, contracts, catalogue
  entries, adapters, or top-level directories.
- Modify another catalogue or pack; the consumer pack is read-only context.
- Record anything forbidden above, a real credential/profile/account, an invoked
  signing command line, or a driver literal for the signing requirement.

  **NAMED EXCEPTION — approver-authorised 2026-08-19, for the post-authentication
  service-worker arm only.** The one remaining question in the item-6 chain —
  whether *post*-authentication silent re-attach depends on a service worker —
  cannot be measured without a real authenticated session. The approver authorised
  a single attended arm against a live account, under conditions recorded here
  rather than agreed verbally, because a precondition quietly crossed once stops
  constraining anything:

  1. **The approver performs the interactive sign-in.** No credential is seen,
     typed, stored, or handled by the agent at any point.
  2. **A fresh profile**, created for the run and removed at teardown. Never an
     existing personal or automation profile.
  3. **Strictly read-only.** Registration state and re-attach outcome only. No
     mailbox or message content is read, no API call is issued, and nothing is
     written, sent, moved, or deleted.
  4. **Attended and time-boxed.** The approver is present for the whole run.
  5. **Booleans and counts only** in the artifact. No URI, no content, no account,
     tenant, or organisation identifier, and no credential value.
  6. **Credentials rotated afterwards regardless of outcome.**
  7. **Organisational policy confirmed** by the approver as permitting automated
     browser access to the tenant. The agent cannot determine this and must not
     assume it.

  This exception is scoped to that single arm. It does not generalise to any other
  arm, round, or destination, and it does not alter the standing precondition
  above, which continues to govern everything else. The round-2 incident — whose
  broader account-level exposure remains **accepted, not resolved** — is the reason
  the conditions are enumerated rather than summarised.

- Convert a characterisation fixture, inspection-only result, missing expected row,
  or failed security precondition into a Pass.
- Move RFC-0088 to Accepted, close a blocker item, or revise a disposition.

## Testing Strategy

| Outcome | Mode | Verification |
| --- | --- | --- |
| T0 shared apparatus | Goal-based check | Runner, privacy, confinement, row-inventory, and compatibility controls have failable command outcomes. |
| T1–T3 measurements | Visual / manual QA against real artifacts | Real drivers, enforcing/control rows, provenance, expected row-id inventory, and read-back. |
| T6 promotion and document layer | Goal-based check | Existing archive, figure, negative-test, privacy, and repository gates exit successfully. |

The gate order has one home here: `build-archive.py`, then
`verify-note-figures-r7.py`, then the round-10, round-11, and round-12 negative-test
harnesses, then `r9-gates.sh`, then full-SAST `make build-check`. The last gate runs
with `dist/` built by the chain and bytecode writing disabled.

## Acceptance Criteria

- [x] **AC1 — Shared apparatus makes its rails observable and enforceable.** A
      round-12 runner restores the drifted historical runner, hard-fails when its
      required browser path, cache path, short temporary directory, privacy-term
      source, or signing-requirement file is absent, and supplies no default signing
      requirement. No manifested member contains that requirement literal. Every arm
      declares an expected row-id inventory; an enforcing check fails a missing row.
      The named confined-removal helper refuses a symlinked store, `..` escape,
      prefix-matching sibling root, and depth/entry-bound violation. Its controls
      prove those refusals. The runner setup carries AC5’s requirement-file clause,
      AC7’s privacy-term-source clause, and AC9’s historical-runner restoration.
- [x] **AC2 — Worker policy is observed per destination for both amended item-6
      clauses.** Role-addressed destinations with opposite worker needs report
      registration blocking and persisted-worker-storage purge separately. Global
      block breaks the worker-dependent flow; global allow shows registration before
      destination policy blocks it. A selective-purge attempt records removed and retained
      inventories; a non-scopable result is a declared finding, while a whole-profile purge removes both destinations’ stores. The note draws no
      conclusion about credential survival from that control. A non-scopable clause
      is reported as a finding against open question 4’s candidate.
- [x] **AC3 — A scoped API token can be replayed without the broker holding it only when the issuing response is marked `no-store`.** A
      synthetic issuer in a process distinct from the driver supplies a unique,
      per-run CSPRNG token of at least 128 bits to page-resident code only. The
      driver receives none; an otherwise identical no-shim control fails; navigation
      records survival. The note states that this claim remains bounded by
      `rfc0088-same-uid-attach-exposure`: any local process able to connect to the
      loopback listener can obtain a token without client authentication.
- [x] **AC4 — The AC3 token surfaces are searched, and absence is claimed only where the detector is proven.** The issuer
      scans job input, driver/child environment reports, driver argv report, stdout,
      stderr, results, page address/query, captured console output, trace, HAR,
      video, browser tracing, and every byte of every file beneath user-data and
      download roots. Trace is the protocol-log surface; all listed surfaces are
      enabled, searched as bytes, then removed through the confined-removal helper
      and never promoted. The driver self-reports argv and allowlisted environment
      names; its labelled-decoy control proves report collection, not resistance to
      a malicious driver. Fixed-size overlapping normalisation uses overlap at least
      the longest encoded token form minus one and fails on any byte cap truncation.
      Mandatory decoys are raw, UTF-16LE, base64, percent-encoded, and JSON-escaped;
      one browser-written decoy reaches local storage; the encrypted cookie store is not
      byte-verifiable. A surface without a recovered decoy is recorded as
      absence-unverifiable, not clean. Live-token results contain absence booleans only;
      decoy offsets may be recorded. Promotion
      accepts only T2-verified artifacts. Round 13 added the staged-member
      positive-control, verified-restore, and re-promotion search, so the
      promoted-state assertion is admitted only when that detector first
      recovers the planted decoy.
- [x] **AC5 — Signing identity is measured as a provenance anchor at the observed depth.** For each system and bundled binary, results record redacted verdict categories for strict verification and separate strict requirement verification, plus permitted platform observations. The requirement is read from a file under the run temporary root, never argv or any manifested-member literal; the runner hard-fails if it is unset. The system binary is recorded only as a resolved executable non-user-writable boolean. The absence control is admitted only for a requirement-attributable difference, never an unrelated resource-sealing failure; a modified copy must fail. Update survival alone is deferred.
- [x] **AC6 — Every new fact and control is mutation-tested individually.** Gate
      output, not the note, records harness counts. Mutations include missing expected
      row, confined-removal refusals, every token encoding, browser-store decoy,
      empty privacy terms, count-minus-one privacy terms, and
      privacy-exemption second occurrence.
- [x] **AC7 — Privacy controls are fail-closed, reproducible, and narrowly scoped.**
      An operator-supplied term file outside the repository and archive, named by an
      environment variable, is read by both privacy consumers and the gate chain.
      Both hard-fail when it is absent, empty, unreadable, or count-mismatched; no
      term is committed or carried in a manifested member or base64 payload, and a
      reconstruction hard-fails with a concise instruction to supply the source. Its
      expected term count is a recorded round-12 fact compared every run,
      while gate output records the count and never terms. Empty or count-mismatched
      input fails. Identifier, team-identifier, and non-loopback-URI classes scan
      only the round-12 privacy corpus. Scan-derived exemption records follow the
      frozen-table rule in Boundaries, including the declared shared-tool exception.
- [x] **AC8 — No apparatus headline figure is a deliverable.** The note contains no
      coverage percentage, claim-accounting total, mutation-corpus figure, or harness
      count. It may state only qualitative control outcomes; an explicit check
      confirms the boundary.
- [x] **AC9 — Promotion preserves earlier-tool compatibility and declared changes.**
      Manifest comparison records declared shared-tool edits and historical-runner
      restoration. Per tool, compatibility re-runs `corpus_docs.py` list derivation,
      `build-archive.py` validation verdicts, `s1/redact.mjs` redaction fixtures,
      `r9-privacy-sweep.py` earlier-corpus verdict, `r9-promote.sh` promotion-member
      selection, and `verify-note-figures-r7.py` earlier derived facts; each result
      remains unchanged for its earlier inputs. The round-12 note is added to
      `corpus_docs.docs()`, and promotion/verifier arguments follow that list order.
- [x] **AC10 — Contradictions and gates are reported without deciding RFC-0088.**
      Every contradicting arm is named in the round-12 note and RFC evidence layer;
      a check verifies both names. The Testing Strategy gate order passes and RFC-0088
      remains Experimental.

## Assumptions

- Technical: the evidence-tree locator is
  [`docs/specs/rfc0088-round11-binding-requirements/spec.md`](../rfc0088-round11-binding-requirements/spec.md#assumptions),
  not a circular runner reconstruction.
- Technical: worker blocking is context-shaped while persisted worker storage may be
  profile-shaped; the round measures that distinction.
- Product: consumer context is read-only; this round writes nothing to that pack.
- Process: native-addon and authenticated-session residuals remain out of scope.
