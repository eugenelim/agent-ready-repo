# Spec: workspace-queue-reconciliation

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none — this spec corrects `workspace.toml` lifecycle membership. It
  adds no artifact and changes no code, but it does change dispatchability, which
  § Consequence records explicitly.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light (work-loop). No risk trigger fired. The governance-boundary trigger
was checked and did NOT fire: `[work]` membership is read by the dispatch classifiers,
but this change moves entries to the collection their own artifact Status already
mandates rather than defining new routing. The one substantive consequence (a spec
becoming dispatchable) was MEASURED before the edit and is recorded in § Consequence
rather than discovered afterwards. Lean fill: Objective + Acceptance Criteria +
Consequence + Boundaries + Assumptions. -->

## Objective

`workspace-status reconcile` reported four Type 2 findings: four specs whose `Status`
is `Shipped` while their `workspace.toml` entry still sits in a `[work].queue`. A
Shipped spec in a queue is not a stale label — it is a contradiction the canonical
classifiers refuse (`impossible_transition` + `unapproved_spec`), so each one is
permanently non-dispatchable and permanently reported.

Success: Type 2 and Type 3 findings reach zero, every moved entry keeps its complete
structured record, and the one dispatchability change the correction causes is stated
in advance rather than found later.

## Acceptance Criteria

- [x] **AC1 — the three auto-eligible entries move queue → shipped via the tool.**
  `docs/specs/work-loop-in-process-guards/spec.md`,
  `docs/specs/ci-gate-parallelization/spec.md` and
  `docs/specs/ci-gate-credbroker/spec.md` (all `ini-002`) move through
  `repair-plan` → `repair-apply --yes`, which is the only sanctioned
  `workspace.toml` writer for this class.

  `workspace.toml` is **not** hand-edited for these three. `repair-apply` preserves
  the complete structured entry, re-reads each spec's `Status` at apply time, and
  revalidates canonical eligibility immediately before the atomic write — none of
  which a manual move guarantees.

  Verification: `repair-apply` reports `applied: true`,
  `operations_applied: 3`, and `applied: true` for each of the three in
  `per_operation`.

- [x] **AC2 — the fourth entry moves by hand, because the tool correctly refused it.**
  `docs/specs/tracker-intake-adapters/spec.md` (`ini-008`) is moved queue → shipped
  manually, carrying its two Group 5 comment lines with it.

  Why the tool refused, precisely — this is not a tool defect:
  `_repair_entry_eligibility` admits an entry only when its blocking codes are a
  subset of `{impossible_transition, unapproved_spec}`
  (`workspace_status_engine.py`). This entry's set is larger, because
  `unsatisfied_dependency` findings raised by its two **dependents**
  (`tracker-refresh-writeback`, `work-intake-migration-docs`, both of which declare a
  typed `needs` on it) carry *its* path as their `path`. So the refusal is the engine
  declining to make a routing change with consequences for other entries without
  review — exactly the right call, and the reason AC2 is a separate criterion with
  § Consequence attached.

  Verification: `repair-plan` lists it under `manual_findings` with
  `reason: "type2-queue-canonical-blocked"`, and after the move
  `tomllib` finds it in `ini-008.work.shipped` and not in any queue.

- [x] **AC3 — Type 2 and Type 3 findings reach zero.**
  `workspace-status reconcile --root .` reports `type2=0` and `type3=0` with
  `complete: true`.

- [x] **AC4 — the surviving Type 1 finding is dispositioned, not registered.**
  `spec/rfc0088-round10-measurement` (`Status: Implementing`, in no initiative list)
  is deliberately left unregistered, and this criterion is the durable record of why,
  so the next reader does not "fix" it.

  Measured against this PR's base (`e999b396`):
  - Registration is **selective**, not universal: 122 work entries against 373
    `docs/specs/*/spec.md` on disk. Being absent from `workspace.toml` is the norm.
  - RFC-0088 is its own tracker. `docs/rfc/0088-web-pilot-foundation.md` records at
    length what each round measured, closed, and commissioned next.
  - The round-10 spec names no initiative.
  - **Registration of RFC-0088 rounds is prospective, not retroactive.** All three
    rounds on disk:

    | Spec | Status | Registered |
    | --- | --- | --- |
    | `rfc0088-round10-measurement` | Implementing | no |
    | `rfc0088-round11-binding-requirements` | Shipped | no |
    | `rfc0088-round12-consumer-shaped-residuals` | Draft | `ini-002.work.queue` |

    Round 12 was registered by #1027 while it was still `Draft` — i.e. when it became
    *planned* work. Rounds 10 and 11 were executed outside the queue and were never
    added after the fact.

  So registering round-10 now would be a retroactive entry of exactly the kind the
  repository has declined to make for its Shipped sibling, and would imply ini-002
  ("Platform Core · P5 Adopt") owns a web-pilot measurement round it never claimed.
  The finding is a true observation about a deliberately out-of-queue spec, and Type 1
  is advisory — it blocks nothing.

  Note this criterion was revised mid-PR: an earlier reading claimed *no* RFC-0088
  spec was registered, which #1027 falsified between this PR's first gate run and its
  rebase. The conclusion is unchanged and now rests on the prospective/retroactive
  distinction rather than on absence.

## Consequence

**`docs/specs/tracker-refresh-writeback/spec.md` becomes canonically ready.** This
was measured before the edit, by simulating AC2's move against a scratch copy and
diffing the `canonical.ready` set:

```
before: guide-metadata-completion, journey-page-completion, site-shared-chrome,
        catalogue-wave4-semantic-contracts-index
after:  … + docs/specs/tracker-refresh-writeback/spec.md   (ini-008)
```

It should **not** be built as it stands: `[backlog].open` carries
`tracker-refresh-writeback-reanchor`, recording that its spec/plan predates the
Group 2/3 contracts it builds on and needs a refresh loop first. Nothing in the repo
detects that — which is the open `ini-008-anchor-staleness-check` item, and this PR
appends the live instance to that entry, including the observation that the guard must
fire on a **membership** change and not only on a dependency shipping, since that is
what triggered this one.

The alternative was to leave a Shipped spec sitting in a queue. That keeps a false
record, keeps a permanent Type 2 finding, and keeps reconciliation non-clean forever —
a worse trade than a measured, documented dispatchability change.

## Boundaries

**Never do**

- Hand-edit `workspace.toml` for a Type 2 finding the tool accepts. `repair-apply` is
  the only sanctioned writer for that class (AC1).
- Convert a structured entry to a bare `spec/<slug>` string while moving it. `ini-008`
  documents that a legacy path there yields `invalid_artifact_path` and refuses dispatch.
- Register `spec/rfc0088-round10-measurement`, or move it to `[backlog]`. See AC4.
- Change any `needs` edge, `source` block, `summary`, or initiative `status`.
- Touch `[shaping_queue]`, `[brief_queue]`, or `[backlog].open` membership. The only
  `[backlog]` change is comment text appended to one existing entry.

## Assumptions

1. `tomlkit` is installed, which `repair-apply` requires and exits 2 without.
   Confirmed: 0.15.1.
2. The four spec `Status` fields do not change between plan and apply.
   `repair-apply` revalidates and would skip any that did; all three reported applied.
3. Type 1 remaining non-zero is acceptable and blocks no gate. Confirmed —
   `reconcile` exits 0 with the finding present, and `lint-spec-status` does not read it.
