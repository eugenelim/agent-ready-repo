# Plan: rfc0088-round12-consumer-shaped-residuals

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

## Approach

Five independent arms in the existing RFC-0088 evidence tree, promoted through the
tree's existing cycle (`r9-promote.sh`). Ordered by **information value**: the two
that decide open questions with a recommended candidate the RFC would otherwise
adopt on reasoning alone go first.

Every arm follows the shape this evidence base converged on over eleven rounds: an
enforcing arm plus a control that removes exactly the control under test in the
same run; ground truth from an independent observer; read-back rather than
assertion; per-row `ok` fields and a `provenance` block.

**Naming and privacy.** New drivers write to `s3/r12-*`, `s2/r12-*`, `s1/r12-*`.
Destinations are addressed by **role**; endpoints and binary paths come from the
environment via the runner's explicit allowlist and are never hard-coded or
persisted. No arm records a URI, vendor, product, tenant, or account identifier.

## Constraints

- macOS only; Linux and Windows remain deferred by disposition B.
- No new dependency, toolchain, or compile step — that is an *Ask first* boundary
  and is why the native-addon residual is not in this round.
- No credential, account, or live authenticated session in any arm.
- Playwright's browsers live under the real home cache; a synthetic HOME needs
  `PLAYWRIGHT_BROWSERS_PATH` set explicitly.
- Short `TMPDIR` — macOS caps Unix socket paths near 104 bytes.
- Node's permission model realpaths an absolute entry script's ancestors; pass the
  entry relative with cwd inside the granted scope.
- A bootstrap read grant must not be an ancestor of the paths under test.

## Construction tests

Per-task `Tests:` below; every task is **visual / manual QA**, so no red stubs
(`no stub (manual QA)`). The construction test for each arm is its **control arm**.

Two cross-cutting checks after all arms: extend `r11-fact-negative-tests.py` with
one mutation per new fact, and scan every artifact and note for URIs and vendor or
product names.

## Design (LLD)

### Design decisions

- **A1 models a destination as a browser context**, because `serviceWorkers` is a
  per-context option. If per-destination scoping requires something stronger, that
  is the finding.
- **A2 keeps the token in a closure inside the page**, installed by the same
  `addInitScript` mechanism the egress shim already uses, so the design is
  consistent with what the RFC already requires rather than a parallel mechanism.
- **A3 reads the signature from the binary**, never from a vendor claim.
- **A4 uses a second OS user**, not a container — round 10 measured that a
  container cannot start a sandboxed renderer without `SYS_ADMIN`, so containerising
  trades the renderer sandbox for isolation, while a second uid does not.

### Failure, edge cases & resilience

- Any driver that cannot complete sets `fatal`; `build-archive.py` refuses such an
  artifact unless declared via `expectedFatal`.
- A control arm that passes when it should have failed **invalidates its own arm**
  and is recorded as such.

### Dependencies & integration

None new. Existing Playwright, Node, `/usr/bin/codesign`, `/usr/sbin/spctl`, macOS
`sandbox-exec`.

## Tasks

### T1: Destination-scoped worker policy

**Depends on:** none
**Touches:** `s3/r12-destination-scoped-worker-policy.mjs` + results

**Tests:** manual QA. Control: a **global** block must break the worker-dependent
destination's flow in the same run — otherwise "scoping helped" is unfalsifiable.
Second control: the worker-independent destination must complete in every arm.

**Approach:** Two synthetic destinations — one whose flow depends on a service
worker, one that registers a worker but does not need it (both shapes are already
built in round 11's arm 2). Three arms: workers global-allow, workers global-block,
and per-destination policy (block for the independent destination, allow for the
dependent one). Record per destination whether the flow completed and whether a
registration existed. Satisfies AC1.

### T2: Page-resident token boundary

**Depends on:** none
**Touches:** `s3/r12-page-resident-token.mjs` + results

**Tests:** manual QA. Control: the identical calls without the shim must fail
(the synthetic API refuses unauthenticated requests). Second control: the driver's
own token-visibility check must be shown capable of failing, by a deliberately
leaky arm that does pass the token through the driver.

**Approach:** A synthetic API that issues a scoped bearer token to page JS and
requires it on every call. An init script hooks `fetch`, captures the token into a
**closure**, and exposes only `__call({url, method, body})`. The driver issues
request shapes and never receives the token. Assert from the driver side that the
token value appears in none of: the job file, the child environment, argv, stdout,
or the results artifact. Satisfies AC2, AC3.

### T3: Browser signing-identity anchor

**Depends on:** none
**Touches:** `s1/r12-signing-identity-anchor.mjs` + results

**Tests:** manual QA. Control: a binary **without** a vendor team identifier (the
bundled browser, which round 10 recorded as carrying none) must be distinguishable
from one with it — otherwise the anchor cannot discriminate.

**Approach:** Read team identifier, notarization/Gatekeeper verdict, and hardened
runtime plus library-validation flags from a system browser and from a bundled one,
via the OS tools. Record whether the identity is present, and whether it is stable
in form across the two. Satisfies AC4. **The identifier value is recorded as a
presence boolean and a stable-form check, not as a vendor identifier string.**

### T4: Separate-uid attachment isolation

**Depends on:** none
**Touches:** `s1/r12-separate-uid-attach.mjs` + results

**Tests:** manual QA. Control: a **same-uid** process must reach the bind endpoint
in the same run — that is disposition B's accepted exposure, and if it does not
reproduce, the isolation arm proves nothing.

**Approach:** Launch a browser with a bind endpoint. Arm 1: a same-uid process
attaches (expected to succeed). Arm 2: a process running as a different OS user
attempts the same attach (expected to be refused). Record the refusal shape.
**Requires a second local account; if none is available the arm is recorded as
not-run rather than inferred.** Satisfies AC5.

### T5: What the worker purge touches

**Depends on:** none
**Touches:** `s3/r12-purge-blast-radius.mjs` + results

**Tests:** manual QA. Control: a store the purge is **not** expected to touch must
be shown present both before and after — otherwise "it only removed one thing"
could be satisfied by a purge that removed nothing.

**Approach:** Seed a profile with a worker plus several profile-resident stores.
Enumerate the store inventory before and after the item-6 purge, recording store
names only (never contents). Report which stores the purge removes and which it
leaves. Satisfies AC6.

### T6: Promotion, note, RFC evidence layer, negative tests

**Depends on:** T1, T2, T3, T4, T5
**Touches:** a round-12 note, the RFC's evidence layer and open questions,
`r11-fact-negative-tests.py`, `corpus_docs.py`, `build-archive.py`, `workspace.toml`

**Tests:** goal-based. `build-archive.py` exits 0; figure verifier reports zero
wrong and zero claimed-nowhere with the round-12 note added **via `corpus_docs.py`,
the single definition**; negative tests catch every new fact; `r9-gates.sh` all OK;
RFC status still `Experimental`; the privacy scan finds no URI or vendor name.

**Approach:** Write the round-12 note; add its layer to the RFC without touching a
disposition; answer open questions 4, 5 and 6 with measurements or record why an
arm could not. Satisfies AC7, AC8, AC9.

## Rollout

- **Delivery:** one PR per arm, then a promotion PR — the increment shape the
  round-11 retrospective settled on.
- **Infrastructure / external systems:** none. All arms are synthetic or local; no
  live destination is contacted.
- **Deployment sequencing:** T1–T5 independent; T6 depends on all five.

## Risks

- **Per-destination scoping may not be expressible** with a per-context option
  alone. That is a finding against open question 4's candidate, not a failure.
- **The leaky-arm control in T2 must genuinely leak**, or the token-visibility
  check is a control that cannot fail — the defect this base has produced most.
- **T4 may be unrunnable** without a second local account; recorded as not-run
  rather than inferred either way.
- **Scope pressure** to fold in the native-addon residual or a credentialed SSO
  arm. Both are *Ask first*; neither is in this round.

## Changelog

- 2026-08-18 — Initial plan. Arms ordered by information value; the two residuals
  needing a toolchain or a credential are deliberately excluded and named.
