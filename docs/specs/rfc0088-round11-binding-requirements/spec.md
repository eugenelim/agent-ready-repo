# Spec: rfc0088-round11-binding-requirements

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0088](../../rfc/0088-web-pilot-foundation.md) — Experimental; this spec measures the binding requirements its 2026-08-18 approver dispositions attach, and changes none of those dispositions
- **Contract:** none — this spec produces evidence, not interfaces.
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full (work-loop). Risk triggers that fired: security boundary
(browser launch, network I/O, filesystem, OS sandbox profiles, an authentication
flow) and multi-feature/dependent tasks (five measurement arms). Full-mode
scripts live at .claude/skills/work-loop/scripts/ — skill-relative, NOT
repo-relative scripts/; round 10 recorded a named skip here that was simply a
wrong path, and CI caught it. Subagent reviewers are a named skip under a
standing session instruction not to dispatch them. -->

## Objective

RFC-0088's four approver decisions were answered on 2026-08-18. Decision A
commissioned an eleventh Experimental round for one reason, stated in the RFC
itself: **four of the five binding requirements those dispositions attach are
themselves unmeasured**. A requirement that no arm has exercised is a
requirement, not a result.

This round measures them. Its user is the approver, who needs each binding
requirement to be either a measured fact or an explicitly named gap before a
later acceptance can carry it. Success is that every one of the five arms below
produces an artifact containing a row that **could have failed**, and that any
arm contradicting the disposition it tests is reported as a finding rather than
smoothed over.

The round measures the **architecture** and does **not** re-measure the
apparatus. No coverage percentage, claim-accounting total, or mutation-harness
figure is a deliverable, because round 9 established that those figures move
when controls are added — so a round that both adds facts and re-measures
coverage reports its own activity as progress.

The five arms, derived from the RFC's own commissioned list
([`0088-web-pilot-foundation.md`](../../rfc/0088-web-pilot-foundation.md), §
*What round 11 is commissioned to measure*), not proposed independently:

1. **Destination-only enforcement without TLS termination**, as a standalone
   arm, with a control that fails when the destination policy is absent.
   Decision C rests on the architectural claim that destination filtering needs
   no termination while method filtering does; round 7 measured the composed
   *terminating* broker instead.
2. **Service workers disabled** — that the control holds, **and** whether an
   authentication flow survives it. The second half is the one that matters and
   is the only arm in this round capable of reversing a disposition.
3. **`--allow-addons` denied** — that the denial holds and that round 10 task
   3's filesystem confinement survives it.
4. **One consumer per connection** — that the three surviving residue classes do
   not cross a consumer boundary when the connection is not shared.
5. **The two remaining macOS drivers, re-measured sandboxed** —
   `s1/r4-attachment-authorization.mjs` and `s2/r5-deny-default-boundary.mjs`.

D/item 2's requirement — that the first browser-digest pin is established from
an independently verified channel, and that channel recorded — is a **process
commitment, not a measurable property**. No arm exists for it and none is
invented.

## Boundaries

### Always do

- Run every subprocess under an explicit environment allowlist (`env -i` plus
  exactly the variables the arm needs), never the ambient environment, and prove
  it by having the child print its own environment.
- Give every arm a control that fails when the control under test is removed,
  and admit the arm only if that control arm actually failed in the same run.
- Compare every touched evidence member against `manifest-r7.sha256` before
  promoting, and restore from the archive if a promoted member's digest moved.
- Mutation-test each new fact individually — mutate the artifact field it
  guards, watch the fact fail, restore — and record the one-line result per
  fact.
- Read a mode, platform, or state back from the artifact rather than asserting
  what was requested.

### Ask first

- Adding any dependency, toolchain, or compile step to the evidence tree.
- Extending the round beyond the five arms, including to close a residual an arm
  discovers.
- Any change to an RFC decision, disposition, blocker item, or status field.
- Deleting a branch before its merge lane is confirmed.

### Never do

- **No implementation.** No production packs, runtime code, dependencies,
  contracts, catalogue entries, SDK, adapters, scheduling, account integrations,
  or new top-level directories. This round produces evidence and nothing else.
- **No apparatus re-measurement as a deliverable.** No new coverage percentage,
  claim-accounting total, or mutation-harness corpus figure. A control defect
  found in passing is fixed and recorded, and does not extend the round.
- **No credential, real profile, or live account.** Synthetic data and fresh
  synthetic profiles only; never print, log, compare, or archive a credential
  value, even a synthetic one.
- **Never convert a characterisation fixture, inspection-only result, hard-coded
  literal, or failed security precondition into a Pass.**
- **Never move RFC-0088 to Accepted, close a blocker item, or revise a recorded
  disposition.** Those are the approver's.

## Testing Strategy

Verification mode for every task is **visual / manual QA against the real
artifact**, exercised end-to-end. These are measurement fixtures: the
deliverable *is* the observed output of a real browser, a real OS sandbox
profile, or a real Node permission-model process. A passing unit gate would
prove nothing, because the thing under test is whether the platform behaves as
the disposition assumes.

Each task therefore:

1. Runs the real driver end-to-end and writes a results artifact with per-row
   `ok` / `result` fields plus a `provenance` block.
2. Is admitted only if the artifact records a row that **could have failed** — a
   control arm that did fail, a denied operation, or a read-back disagreeing
   with the request. An arm with no failable row is not evidence, and an arm
   whose control passed when it should have failed invalidates that arm rather
   than the round.
3. Has its published figures derived by `verify-note-figures-r7.py`, and every
   new fact mutation-tested individually by the `r10-fact-negative-tests.py`
   mechanism.

Mapping each Objective outcome to its mode and why:

| Objective outcome | Mode | Why |
| --- | --- | --- |
| Arm 1 destination-only enforcement | manual QA, E2E through a live non-terminating proxy | The claim is about what a real CONNECT proxy can and cannot see; only a real TLS tunnel shows that the method is unreadable |
| Arm 2 worker suppression + auth survival | manual QA, E2E through a real browser and a real restored profile | A persisted service worker is a property of an on-disk profile across a restart; nothing short of a restart creates the case |
| Arm 3 addon denial | manual QA against a real Node permission-model process | The discriminator is a runtime error code the real runtime emits |
| Arm 4 residue crossing a consumer boundary | manual QA, E2E in real browser connections | Residue classes are live browser state; round 3's driver asserts each was actually planted before teardown |
| Arm 5 the two drivers sandboxed | manual QA, E2E, mode read back from the browser | The question *is* whether real launch behaviour differs sandboxed |
| Gates and figure integrity | goal-based check | `build-archive.py`, `verify-note-figures-r7.py` and `r9-gates.sh` each pass or fail on a one-liner |

Gate order: `build-archive.py` (privacy, provenance, duplicate-digest,
failing-row, `expectedFatal`, import-closure) → `verify-note-figures-r7.py` →
`r9-gates.sh`.

## Acceptance Criteria

- [x] **AC1 — Destination-only enforcement measured standalone, without TLS
      termination.** A non-terminating CONNECT proxy enforces the round-4
      production destination rule. The artifact records that a forbidden
      destination is refused, that an allowed destination is reached (proved by
      the destination's own receive log, not a proxy decision), and that with the
      destination policy removed the same forbidden destination **is** reached —
      so the enforcement row could have failed.
- [x] **AC2 — The cost of not terminating is recorded as a measured fact.** The
      same artifact records that the HTTP method is **not** readable at the
      non-terminating connection point, from the bytes the proxy actually
      observes. This is the architectural fact decision C rests on, and it is
      measured rather than asserted.
- [x] **AC3 — Service-worker suppression measured against a restored profile.**
      With `serviceWorkers: 'block'`, a profile carrying a persisted service
      worker is restarted and the controller state is read **at document start**,
      by an init script, before any page script runs. A control arm with
      `serviceWorkers: 'allow'` on the same profile reads a controller at that
      same instant; if it does not, the arm is invalid rather than passing.
- [x] **AC4 — Whether the shim's uncovered realm survives suppression.** The
      artifact records the UDP packet count from the service-worker realm under
      block and under allow, so round 10's "4 packets on any profile" finding is
      either closed by suppression or shown to survive it.
- [x] **AC5 — Authentication-flow survival measured as a taxonomy.** Three
      synthetic authentication flow variants — service worker absent, service
      worker present but not load-bearing, service worker load-bearing on the
      auth path — each run under block and under allow, with per-variant
      completion recorded. Whether real-world identity providers fall into the
      load-bearing class is **not** measured here and is recorded as a named
      residual, not as a Pass.
- [x] **AC6 — `--allow-addons` denial holds and is distinguishable from an
      unrelated failure.** The artifact records that addon loading is refused by
      **policy** when the flag is absent and reaches a **non-policy** failure when
      it is present, by distinct runtime error codes — so "denied" cannot be
      satisfied by a file that merely does not load.
- [x] **AC7 — Round 10 task 3's filesystem confinement survives the addon
      configuration.** The synthetic browser-profile read stays denied in the
      addons-denied arm, measured in the same run rather than inherited from
      round 10. Whether a *working* compiled addon defeats that confinement is
      recorded as an explicit unmeasured residual (deferred: rfc0088-native-addon-confinement-bypass).
- [x] **AC8 — Residue does not cross an unshared connection.** Using round 3's
      own planting mechanics, all eight residue classes are verified as planted,
      and the three that survive teardown are checked against a second consumer
      on its **own** connection. A shared-connection control arm in the same run
      reproduces round 3's three-survivor result; if it does not, the arm is
      invalid.
- [x] **AC9 — The two remaining macOS drivers run sandboxed.**
      `s1/r4-attachment-authorization.mjs` and `s2/r5-deny-default-boundary.mjs`
      each run sandboxed and sandbox-off, with the renderer mode **read back**
      and a run whose observed mode disagrees with its requested mode failing.
      Each driver's result is stated **per driver**, not as one aggregate.
- [x] **AC10 — No promoted round-7 or round-10 member is overwritten.** Every
      touched member is compared against `manifest-r7.sha256` before promotion,
      and the note records that comparison as performed.
- [x] **AC11 — Every new fact is mutation-tested individually**, with the
      one-line result of each test recorded in the note rather than summarised as
      a pass.
- [x] **AC12 — No apparatus figure is a deliverable.** The round publishes no new
      coverage percentage, claim-accounting total, or mutation-corpus figure. Any
      control defect found is fixed and recorded and does not extend the round.
- [x] **AC13 — An arm that contradicts its disposition is reported as a
      finding.** If any arm falsifies the requirement it tests — arm 2 is
      specifically capable of this against D/item 6 — the note states it plainly
      and the RFC's evidence layer records it, without changing the disposition
      itself.
- [x] **AC14 — Gates clean**: the archive builds, `verify-note-figures-r7.py`
      reports zero wrong and zero claimed-nowhere, `r9-gates.sh` passes,
      `make build-check` passes when `dist/` is built by the gate chain with
      bytecode writing disabled, and the RFC status is still `Experimental`.

## Resolve-vs-surface record

Opened at PLAN, closed here. Everything a referent could settle was settled; only
the irreducible is surfaced.

**Resolved (no human input needed).**

- R11-1 to R11-5 — five instrument defects found and fixed in-round, each with the
  fix verified rather than asserted (a purge that purged nothing; a manifest that
  could not match its tree; a corpus denominator whose round-10 remedy re-broke; 18
  figures matching artifacts but not the note's line-wrapping; round 10's
  negative-test harness silently refusing to run).
- The `CAT-V-014` build-check failure — diagnosed as stale local `dist/` state
  rather than a repository defect, and cleared. An earlier draft of this spec
  recorded it as pre-existing, which was wrong in the direction of blaming the repo.
- `site-link-check` failing on `astro: command not found` — uninstalled `web/`
  dependencies, not a broken gate. Installed; the gate passes.
- The `services.mjs` reuse assumption — its handlers cannot express the request
  header and 401 both new arms need, and it is a promoted member, so each arm owns
  its origin instead.

**Surfaced (needs a decision that is not this round's to take).**

- **R11-6 — the published archive digest cannot converge.** Diagnosed precisely (a
  two-cycle, because the archive contains an artifact recording the archive's own
  size) and deliberately left unfixed: breaking the self-reference means changing
  what the archive contains or what the accounting tool records, which is an
  evidence-base design decision. The strictly worse defect underneath it (R11-2) is
  fixed, so the manifest now matches its tree at rest.
- **Whether real identity providers put a service worker on the login path.** A
  landscape question, not a fixture question. It bounds how expensive D/item 6's
  requirement is in practice, and no arm here answers it.
- **Whether a compiled native addon defeats the filesystem confinement**
  (`rfc0088-native-addon-confinement-bypass`). Needs a toolchain in the evidence
  tree, which is a new dependency.
- **AGENTS.md drift** (`agents-md-missing-web-npm-ci`) — flagged rather than fixed,
  because root `AGENTS.md` is not a sibling of `docs/rfc` and so falls outside the
  bundled-fixes carve-out, and this round's own scope boundary is evidence-only.
- **What the approver does with two contradicted requirements.** Round 11 reports
  them; restating a binding requirement is the approver's act, not the round's.

## Assumptions

- Technical: the evidence tree survives at `/private/tmp/rfc0088-round9-evidence.C5FnKi` with all helpers present, so no reconstruction from the base64 payload is needed (source: `ls` of that path, 2026-08-18)
- Technical: reproduction identity holds — Node v26.4.0, Playwright 1.62.0, matching the promoted round-7 evidence (source: probe `node --version`; `_env/versions.json`)
- Technical: arm 2's suppression mechanism exists as the Playwright **context** option `serviceWorkers: "allow"|"block"` (source: probe `grep serviceWorkers node_modules/playwright-core/types/types.d.ts` → `serviceWorkers?: "allow"|"block"`). Being per-context is why it may not suppress a worker persisted in a restored profile — which is what AC3 measures rather than assumes.
- Technical: arm 3 is measurable without compiling an addon, because the two outcomes carry distinct error codes — `ERR_DLOPEN_DISABLED` without `--allow-addons`, `ERR_DLOPEN_FAILED` with it (source: probe `node --permission --allow-fs-read=/tmp -e "process.dlopen(...)"`, both variants, 2026-08-18). Node additionally emits `SecurityWarning: The flag --allow-addons must be used with extreme caution. It could invalidate the permission model.`
- Technical: round 3's residue driver `s5/s5-round3.mjs` is recoverable from `round3-evidence-archive.md`, whose payload digest matches its recorded SHA-256 (source: probe decoding the payload and comparing to `d13ed745…ee689`), so arm 4 reuses round 3's actual planting mechanics
- Technical: the three surviving residue classes are an init script registered by another holder, origin-scoped storage, and an artifact already committed to the shared job root (source: `docs/rfc/0088-web-pilot-foundation.md:1514`)
- Product: "a real authentication flow" for AC5 means a synthetic three-variant taxonomy, because the security preconditions forbid a live identity provider or any real credential; the landscape question stays a named residual (source: user confirmation 2026-08-18)
- Product: the native-addon confinement bypass stays an unmeasured named residual rather than adding node-gyp and a C++ toolchain to the evidence tree (source: user confirmation 2026-08-18)
- Process: the `CAT-V-014` `catalogue-verify` failure is **stale local build state, not a repository defect** — an initial probe of `SKIP_SAST=1 make build-check` on a clean worktree exited 2 with four `CAT-V-014` errors, and the first draft of this spec recorded that as pre-existing. That was wrong in the direction of blaming the repo: `rm -rf dist && PYTHONDONTWRITEBYTECODE=1 SKIP_SAST=1 make build-check` clears every `CAT-V-014` error. `dist/` must be built by the gate chain, and `__pycache__` written under the packs tree mid-run is what trips the check (source: both probes, 2026-08-18)
- Process: `workspace.toml` carries no `[work]` table, so the work-loop's canonical preflight has no ready or active item and this round proceeds on the commissioning brief, as round 10 did (source: parsing `workspace.toml` with `tomllib`)
- Process: RFC-0088 stays `Experimental` and no blocker item closes in this round (source: `docs/rfc/0088-web-pilot-foundation.md` § *Approver dispositions — 2026-08-18*)
