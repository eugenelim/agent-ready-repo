# Spec: workspace-backlog-reconciliation

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none — this spec changes `workspace.toml` display metadata only. It
  adds, removes, and changes no dispatchable membership.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: light (work-loop). No risk trigger fired. The one conditional trigger —
governance boundary — was checked and did NOT fire: `[backlog].open` is a display
projection that the dispatch classifiers never read (workspace_status_engine.py
:3237 `extract_repo_backlog`), so no entry here can authorize or block work. Lean
fill: Objective + Acceptance Criteria + Boundaries + Assumptions. -->

## Objective

A cold reader of `workspace.toml [backlog].open` should find claims that are true
against the repository as it stands today. An audit of all 143 open entries against
the code found eight that are not: one describes work already done, one describes
work half-done, one is materially broader than the gap that survives it, three say
they are blocked on gates that have since passed, and two state a measurement or a
mechanic that the code contradicts.

Success: every corrected entry's claim is verifiable by a command recorded in the
entry itself, and `workspace-status` still parses and reports the same open-entry
count (one entry removed as done, one added for the decision AC6 surfaces).

## Acceptance Criteria

- [x] **AC1 — `web-primitives-fixture-dead-placeholders` closes.** The entry is
  removed from `[backlog].open`, and the closure evidence is recorded in the PR
  description and in this spec.

  It is **not** moved to `[backlog].closed`, and that is deliberate:
  `_ALLOWED_KIND_BY_COLLECTION["backlog.closed"]`
  (`workspace_status_engine.py:1076`) admits only `kind = "defect"`, and
  `:2050` additionally requires the referenced artifact to carry
  `Status: Closed` plus a resolution in `{fixed, declined, superseded}`. A closed
  entry is therefore a canonical target entry backed by a real defect artifact.
  This item has no such artifact, and inventing one to satisfy the array would be
  the same fabrication this spec's Boundaries forbid. Deletion is also the
  repository's established practice: `[backlog].closed` has stayed empty across the
  project's history while entries have come and gone from `open`.

  Evidence:
  `web/src/pages/primitives-fixture.astro` carries exactly two `href` attributes,
  both live (`withBase('/docs/guides/github/how-to/…')` and `#decision-band`); none
  of the eight named placeholders (`/guides/github-auth`, `/review`, `/issues`,
  `/run`, `/confirm`, `/cancel`, `/get-started`, `/example`) remains.

- [x] **AC1b — the sibling trap note that AC1 invalidates is corrected.**
  `web-docs-link-check-gate` records two traps a future link-checker must carry;
  trap 2 is "`build/primitives-fixture/` must be excluded explicitly and visibly".
  With the eight placeholders gone (AC1) the fixture needs no carve-out, so that
  trap is obsolete. The entry records this, and keeps trap 1 (root-relative links
  lacking the base prefix are not off-site), which is unaffected.

- [x] **AC1c — the deferral anchors AC1 would leave dangling are resolved.**
  Removing the entry orphans two references in the Shipped
  `docs/specs/marketing-docs-link-repair/`:
  - `spec.md:93` is a **live instruction**, not history: it tells a future link
    gate that `build/primitives-fixture/` is a disclosed exclusion carrying eight
    placeholder hrefs. That is now false, and an agent reading it as current-state
    truth would build the exclusion back in — the same failure mode
    `phase4b-docsurl-instruction-stale` records for this exact page, which has now
    landed and reverted twice (#852 → #854). It gets an errata note.
  - `plan.md:39` is a declined-pattern record and stays as history, with a
    one-clause note that the item has since been resolved so the pointer does not
    read as live.

  Editing a Shipped spec is in bounds here: `AGENTS.md` § How we work makes specs
  validation gates rather than write-once records, and requires drift to be fixed
  in the same PR. The errata note preserves the original text rather than
  rewriting it.

- [x] **AC2 — `ast07-sca-scanner-agentbundle` narrows, and does not close.** The
  entry is rewritten to record that the concern it names is closed for shipped code
  — both `packages/agentbundle` and `packages/credbroker` declare
  `dependencies = []`, and `Makefile:241` audits credbroker's `[crypto]` extra
  explicitly — and that one residual remains: agentbundle's `[lint]` extra
  (`pyyaml>=6.0`) is third-party and reaches no `pip-audit` invocation. The rewritten
  entry names that residual as its remaining scope.

- [x] **AC3 — `desk-research-install-name-drift` narrows.** The content half is
  done: `rg -F 'install research' guides/` returns no hit (the only hits are in
  `docs/specs/research-pack/`, which is frozen spec history and correctly records
  the id in force at the time). The entry is rewritten so its remaining scope is
  only the retired-id negative fixture in the owning lint.

- [x] **AC4 — three blocked entries record that their gate has passed.**
  - `contract-drift-check-gate-promotion` — the entry asks for two clean
    `check_contract_drift.py` passes and logs one (2026-08-01). A second pass is
    recorded (2026-08-15, exit 0), so the entry states it is now unblocked.
  - `lint-sso-config-profile-charset` — reads "Unblocks: after AC4 lands"; AC4 is
    `[x]` in `docs/specs/jira-check-sso-auto-login/spec.md:307`. The entry records
    that it is unblocked.
  - `nonjson-2xx-guard-all-read-paths` — reads "Unblocks: after AC11"; AC11 is
    satisfied per the same spec. The entry records that it is unblocked.

- [x] **AC5 — `spec-ac-heading-casing-silent-gate`'s measurement is corrected.**
  The entry says "eight specs" carry `## Acceptance criteria`. Measured
  2026-08-15: 17. The entry carries the corrected count and the command that
  produced it.

- [x] **AC6 — the `type = "spec"` comment defect is corrected.** The comment above
  the five reanchor entries claims a bare typed shaping object "yields
  `legacy_entry`". It does not: `_SHAPING_TYPES`
  (`workspace_status_engine.py:3229`) is `{shape, research, strategy, signal,
  design}`, so `type = "spec"` fails `_accepted_legacy_entry`'s backlog branch and
  yields `unsupported_legacy`. The comment is corrected to state what the engine
  actually does. The five entries' `type` values are left as they are — retyping
  them is a routing decision, not a comment fix, and is recorded as its own entry.

- [x] **AC7 — the retyping decision is recorded as a new entry.** A new
  `[backlog].open` entry captures the open question AC6 surfaces: whether the five
  reanchor entries should keep `type = "spec"` (permanently `unsupported_legacy`),
  drop the key (plain build items), or take a `_SHAPING_TYPES` member.

- [x] **AC8 — no dispatchable membership changes.** `git diff` touches
  `[backlog]` only. `[work]`, `[shaping_queue]`, `[brief_queue]`, and every
  `[ini-NNN]` section are byte-identical to their pre-change state.

- [x] **AC9 — the file still parses and the backend still runs.**
  `python3 .claude/skills/workspace-status/scripts/workspace_status.py status
  --root .` exits 0, and its `repo_backlog.open` count equals 143 − 1 (AC1's
  closure) + 1 (AC7's new entry) = 143.

## Boundaries

### Always do

- Verify each claim with a command before writing it into an entry, and record the
  command in the entry so the next reader can re-run it.
- Preserve every entry's existing comment prose except where an AC requires a
  correction.

### Never do

- Never change `[work]`, `[shaping_queue]`, `[brief_queue]`, or initiative
  sections. This spec is scoped to `[backlog]`.
- Never close an entry whose remaining scope is non-empty. Narrow it instead.
- Never migrate a build entry to a canonical target entry by inventing a `path`.
  The engine's `unsupported_legacy` remediation says exactly this: "Route the item
  manually; do not infer a target entry."

## Assumptions

- `[backlog].open` is display-only. Verified: `extract_repo_backlog`
  (`workspace_status_engine.py:3237`) is the sole reader, and it projects for
  display; no dispatch classifier consumes it. This is what makes the change
  behavior-preserving.
- `[backlog].closed` exists in the schema (the blank-file template in the
  `workspace-status` skill declares it) and is currently empty, so AC1 is the first
  use. An empty-to-one-element transition needs no migration.
