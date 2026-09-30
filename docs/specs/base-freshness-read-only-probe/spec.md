# Spec: Read-only base freshness probe

- **Status:** Shipped
- **Owner:** maintainer
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the JSON result remains a private handoff between `work-loop` and its bundled helper
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons`
> and `Assumptions` are working material.

## Outcome

Agents can prove that a branch contains its remote target without first writing
Git metadata. A current base proceeds, while a stale base stops with an update
offer when the environment can refresh it and a separate-update instruction
when it cannot.

## What Changes

- Remote freshness is advertised through a non-writing Git operation before any
  write-capable fetch — `check-base-freshness.py`.
- A single configured remote uses its advertised `HEAD` directly, so the normal
  no-`--target` work-loop path does not depend on a separate `ls-remote`
  discovery call — `check-base-freshness.py`.
- A write-capable fetch is reserved for a base already proven stale so the
  helper can prepare or decline the update path — `check-base-freshness.py`.
- The work-loop distinguishes a writable stale result from a stale result that
  the user must update outside the session — `work-loop/SKILL.md` and its evals.
- Pack tests and release surfaces pin the new decision order — core pack tests,
  manifests, projections, and changelog.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise and maintainer procedure | Applicable: this changes when the work-loop may proceed or offer an update | `packs/core/.apm/skills/work-loop/SKILL.md` | core pack | skill eval and projected copies | source and projections state the same fresh, stale, and unavailable handling |
| Executable behavior | Applicable: the helper owns Git probing and JSON results | `packs/core/.apm/skills/work-loop/scripts/check-base-freshness.py` | core pack | targeted pytest and real local-transport invocation | fresh checks make no metadata write; both stale remediation paths match this contract |
| Release history | Applicable: installed core behavior changes | `docs/product/changelog.md` | release workflow | versioned entry with a consumer-facing highlight | manifests and changelog name the same patch release |
| Interface compatibility | Applicable only to the private helper result | existing `status`, `message`, and `target` JSON fields | core pack | bounded consumer search and regression tests | no independent consumer or new public schema is introduced |
| Architecture and decision rationale | Not separately applicable: no module or ownership boundary changes | none | maintainer | diff review | no placeholder architecture record is created |

## Agent Rules

### Always do

- Decide whether the advertised remote target is contained in `HEAD` before
  invoking a write-capable fetch.
- Treat a remote target not contained in `HEAD` as stale even when Git metadata
  writes are denied.
- Run every network-capable Git subprocess inside the current repository and
  against a remote name enumerated from that repository's Git configuration.
- Sanitize remote failures through closed classifiers and keep raw Git stderr out
  of helper messages.
- Preserve the work-loop's `network_fetch` boundary metadata in source and every
  generated adapter projection.

### Ask first

- Ask the user before changing the working branch through rebase, merge, pull, or
  another history-changing operation.
- Ask before widening the unavailable-result classifier or changing the existing
  JSON fields and status meanings.

### Never do

- Never report `status: "ok"` from only a cached remote-tracking ref.
- Never let a denied stale-remediation fetch downgrade a proven stale base to
  `status: "skipped"`.
- Never accept a raw URL as a target, add a separate HTTP transport, widen Git
  schemes or redirect behavior, inspect credentials, or bypass host policy.
- Never add a dependency, module boundary, credential probe, policy bypass, or
  retry loop for this change.

## Testing Strategy

- **Read-only fresh decision (AC-0001, AC-0009):** TDD at the helper entry point
  records every Git command and proves explicit and default fresh targets return
  `ok` without a write-capable fetch or preemptive `ls-remote` discovery.
- **Stale remediation split (AC-0002, AC-0003):** TDD uses real local Git
  repositories plus a denied-metadata seam to prove both stale outcomes remain
  blocking and carry different next actions; a remote-move seam proves the
  successfully fetched live target is authoritative.
- **Unavailable and refusal boundaries (AC-0004, AC-0005):** TDD keeps the
  existing closed failure classifiers and local-state regressions red on any
  broadening.
- **Older Git compatibility (AC-0006):** TDD substitutes the exact unsupported
  option diagnostic and proves the read-only `ls-remote` fallback preserves the
  same ancestry decision.
- **Caller and pack delivery (AC-0007, AC-0008, AC-0010, AC-0011):** goal-based checks
  cover the work-loop eval, bounded source inspection, verification gates,
  patch-version agreement, security-metadata preservation, generated projection
  drift, and release history.
- **Outbound confinement (AC-0012):** command-trace tests prove every remote
  operation uses a configured remote name from the current repository and that
  `--target` cannot introduce a URL or alternate transport.
- **Real invocation:** a local transport exercises fresh and stale repositories
  without external credentials or network access and records exit code, JSON,
  and the absence or presence of a write-capable fetch.

## Acceptance Criteria

- [x] **AC-0001.** When the read-only remote advertisement names a target commit
  reachable from `HEAD`, the helper exits 0 with `status: "ok"`; a recorded
  command trace contains no write-capable `git fetch`.

- [x] **AC-0002.** After an advertisement proves staleness and the stale-only
  fetch succeeds, the fetched live target is authoritative: when it is not
  reachable from `HEAD`, the helper exits 1 with `status: "surface"` and tells
  the work-loop to ask whether it should update the branch before emitting or
  running the existing safe rebase path; when a concurrent remote move makes
  that fetched target reachable from `HEAD`, the helper exits 0 with
  `status: "ok"`.

- [x] **AC-0003.** When the advertised target is not reachable from `HEAD` and
  Git metadata policy denies the stale-only fetch, the helper exits 1 with
  `status: "surface"`; its message says the base is stale, this environment
  cannot prepare the update, and the user must update separately.

- [x] **AC-0004.** When neither the primary read-only advertisement nor its
  compatibility fallback can reach the remote because of a timeout or an
  existing classified transport or authentication failure, the helper exits 0
  with `status: "skipped"` and retains the existing unverified-base notice.

- [x] **AC-0005.** A missing target, malformed advertisement, unclassified Git
  failure, invalid or ambiguous target, unsafe local state, unrelated history,
  or ancestry comparison failure other than the advertised commit being absent
  locally exits 1 with `status: "surface"` and exposes no raw remote diagnostic.
  An advertised commit absent locally is stale because it cannot be reachable
  from `HEAD` and follows AC-0002 or AC-0003.

- [x] **AC-0006.** When Git rejects fetch `--porcelain` as unsupported, the
  helper uses a read-only `ls-remote` query and applies the same reachable,
  stale, missing-target, unavailable, and unclassified verdicts; it never falls
  back to a cached remote-tracking ref.

- [x] **AC-0007.** The work-loop proceeds silently on `ok`, gives the existing
  notice and proceeds on `skipped`, stops and offers the approved update on a
  writable stale result, and stops with a separate-update recommendation on an
  unwritable stale result.

- [x] **AC-0008.** The targeted helper suite, work-loop eval, local gates,
  self-host projection check, and catalogue verification pass.

- [x] **AC-0009.** With one configured remote and no `--target`, the helper
  advertises that remote's `HEAD` through the primary dry-run fetch. When the
  advertised commit is reachable from local `HEAD`, it exits 0 with
  `status: "ok"` without invoking `ls-remote` or a write-capable fetch.

- [x] **AC-0010.** Matching core source manifests carry one patch-version bump,
  generated adapter projections contain the changed behavior, and the release
  changelog records the user-visible outcome under that version.

- [x] **AC-0011.** The source work-loop skill and every generated adapter
  projection retain `metadata.boundaries` with `network_fetch`; this change does
  not broaden the declared tool authority.

- [x] **AC-0012.** Every fetch and `ls-remote` subprocess runs within the current
  repository and names only a remote enumerated from that repository's Git
  configuration. `--target` remains limited to `<configured-remote>/<branch>`;
  the implementation adds no raw-URL target, HTTP client, scheme or redirect
  widening, credential inspection, or policy bypass.

## Follow-ons

none

## Assumptions

none
