# Spec: Base freshness in policy-limited environments

- **Status:** Shipped
- **Owner:** maintainer
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the JSON is a private handoff between one skill and its bundled helper
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

## Outcome

Agents can continue a work-loop when network, authentication, timeout, or Git
metadata policy prevents the base-freshness check from running. They see that
the base is unverified and may need a separate update, while proven stale or
unsafe repository states still stop the loop.

## What Changes

- The unavailable-check outcome becomes non-blocking in the bundled
  `check-base-freshness.py` helper.
- The work-loop distinguishes a skipped check from a current base and tells the
  user before continuing.
- Pack tests and the work-loop eval harness pin the skip boundary and the
  remaining blocking outcomes.
- The core pack release surfaces record the changed workflow.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise and maintainer procedure | Applicable: the skill tells agents when work may continue | `packs/core/.apm/skills/work-loop/SKILL.md` | core pack | skill eval and projected copies | source and projections state the same tri-state handling |
| Executable behavior | Applicable: the bundled helper decides exit status and JSON | `packs/core/.apm/skills/work-loop/scripts/check-base-freshness.py` | core pack | targeted pytest and real invocation | unavailable and blocking cases match this contract |
| Release history | Applicable: the core pack behavior and version change | `docs/product/changelog.md` | release workflow | versioned entry with a consumer-facing highlight | released section is free-standing beneath `[Unreleased]` |
| Interface compatibility | Not separately applicable: the JSON result is consumed only by its owning skill and tests | none | core pack | bounded reference search confirms no independent consumer | script docstring, caller guidance, tests, and eval agree |
| Current architecture and reusable learning | Not applicable: no module boundary or reusable cross-feature decision changes | none | maintainer | diff review | no placeholder artifact is created |

## Agent Rules

### Always do

- Return a non-blocking skipped result only when a closed, sanitized category
  proves that the environment prevented a remote query or fetch from completing.
- Tell the user that freshness was not verified and that they may want to
  update the branch separately, then continue the work-loop.
- Preserve blocking behavior when Git establishes stale or unsafe state.

### Ask first

- Ask before widening the skipped set beyond network, authentication, timeout,
  or Git metadata write failures.
- Ask before changing any existing JSON field name or the meaning of the
  existing `ok` and `surface` statuses.

### Never do

- Never describe a skipped check as proof that HEAD is current.
- Never continue after the helper proves the branch is behind its target.
- Never inspect credentials, alter enterprise policy, or repeatedly retry a
  blocked Git operation to establish freshness.

## Testing Strategy

- **Unavailable remote query and fetch (AC-0001, AC-0002):** TDD through the real bundled CLI.
  Temporary Git repositories make each unavailable route fail before the
  production change and assert exit status, JSON status, notice text, and the
  closed classifier boundary.
- **Stale and invalid repository states (AC-0003, AC-0004, AC-0005, AC-0009):** TDD regression coverage through the
  existing real-Git cases, because these outcomes must remain blocking.
- **Caller behavior and declared authority (AC-0006, AC-0010):** goal-based
  checks through a work-loop eval case and bounded source inspection that
  distinguishes `skipped` from `ok` and `surface`.
- **Regression boundary (AC-0007):** goal-based check through the targeted
  pytest collection and the work-loop eval fixture.
- **Pack delivery (AC-0008):** goal-based checks through catalogue verification and
  self-host projection drift checks.
- The real invocation is construction evidence for AC-0001, AC-0002, and
  AC-0004, recorded in the plan rather than as a second verification group.

## Acceptance Criteria

- [x] **AC-0001.** Remote-query unavailability is non-blocking. When automatic
  target discovery cannot complete `git ls-remote`, the helper exits 0 with
  `status: "skipped"` only for a timeout or a closed, sanitized
  network/transport/authentication category. Its message says freshness was
  not verified, work may continue, and the user may want to update the branch
  separately. Malformed, unsafe, missing-target, and unclassified
  `ls-remote` failures exit 1 with `status: "surface"` and expose only a
  bounded category rather than raw stderr.

- [x] **AC-0002.** Fetch unavailability is non-blocking. When an explicit or
  discovered target reaches `git fetch`, the helper exits 0 with
  `status: "skipped"` only for a timeout, a classified remote
  transport/authentication failure, or a classified permission/policy denial
  while Git writes fetch metadata or the remote-tracking ref. The message has
  the same user-facing consequence as AC-0001.

- [x] **AC-0003.** A missing target branch remains blocking. When Git reports
  that the named remote branch does not exist, the helper exits 1 with
  `status: "surface"` and tells the user to verify the branch name.

- [x] **AC-0004.** A proven stale base remains blocking. When the remote query
  and fetch succeed and `HEAD` is behind the target, the helper exits 1 with
  `status: "surface"` and retains its safe rebase guidance.

- [x] **AC-0005.** Local-state and target-selection refusals remain blocking. An
  active rebase, unresolvable HEAD, malformed or ambiguous target, multiple
  remotes without a target, invalid branch name, comparison failure, and dirty
  or unrelated histories continue to exit 1 with `status: "surface"`.

- [x] **AC-0006.** The caller handles all three statuses explicitly. The
  work-loop proceeds silently on `ok`, informs the user and proceeds on
  `skipped`, and stops on `surface`. It does not retry an unavailable operation
  or claim that a skipped check established freshness.

- [x] **AC-0007.** Regression coverage pins the boundary. The targeted pytest
  suite covers unavailable `ls-remote`, unavailable fetch caused by a denied
  ref update, missing target branch, confirmed stale base, and representative
  local/configuration refusals; the work-loop eval harness covers the required
  agent response to `skipped`.

- [x] **AC-0008.** The published pack is consistent. The core pack patch version
  is bumped in its source manifests, self-hosting regenerates adapter
  projections, catalogue verification reports no drift, and the release
  changelog records the non-blocking unavailable-check behavior.

- [x] **AC-0009.** An unclassified fetch failure remains blocking. When fetch
  exits non-zero and its C-locale diagnostic matches neither the missing-branch
  case nor a closed unavailable category from AC-0002, the helper exits 1 with
  `status: "surface"`, says freshness could not be established, and preserves
  the diagnostic only as a bounded category rather than copying raw stderr.

- [x] **AC-0010.** The skill declares the minimum authority used by base
  freshness. Its source metadata includes the repository's `network_fetch`
  boundary. Its procedure permits the local read-only Git checks required by
  AC-0004 and AC-0005, while confining network-capable Git subprocesses to
  remote discovery and fetch, network egress to configured Git remotes, and
  Git metadata writes to the current repository. It forbids credential
  inspection and policy bypass; generated projections preserve the same
  metadata and prose.

## Follow-ons

none

## Assumptions

none
