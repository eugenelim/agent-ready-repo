# Spec: rfc-digital-product-experience-doctrine

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** none — single-task spec; no plan file needed
- **Constrained by:** [RFC-0071](../../rfc/0071-digital-experience-doctrine.md) (D1–D10), [RFC-0062](../../rfc/0062-content-design-and-copy-direction-skills.md) (accepted by RFC-0071)
- **Brief:** none
- **Contract:** none — governance document authoring only; no API/event/RPC interface
- **Shape:** governance

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

RFC-0071 (Digital Experience Doctrine) is in Accepted status. This spec closes
the governance gate that all eleven downstream ini-003 specs depend on. The
deliverable is a single PR that: (1) sets RFC-0071 `Status: Accepted` and
`Date closed: 2026-07-23` in the RFC file (already done in authoring session),
(2) updates `workspace.toml` to move `spec/rfc-digital-product-experience-doctrine`
from `queue` to `active`, and (3) confirms RFC-0062 disposition (already updated
to Accepted, Date closed: 2026-07-23 in the prior session). The spec ships with
no pack changes, no skill changes, and no guide changes — those all belong to the
eleven downstream specs the DAG unlocks.

## Boundaries

### Always do

- Verify RFC-0071 frontmatter: `Status: Accepted`, `Date closed: 2026-07-23`,
  all 10 decisions confirmed (D1–D10), `Review focus` updated to reflect decisions
  resolved
- Verify RFC-0062 frontmatter: `Status: Accepted`, `Date closed: 2026-07-23`,
  and the implementation note pointing to `spec/xd-copy-direction`
- Move `spec/rfc-digital-product-experience-doctrine` from `["ini-003".work].queue`
  to `["ini-003".work].active` in `workspace.toml`
- Validate `workspace.toml` parses clean after the move (`python3 -c "import tomllib; ..."`)

### Ask first

- Any edit to the RFC-0071 decision text itself (decisions are closed)
- Any edit to the RFC-0062 procedure or scope (that RFC is now frozen; amendments
  require an erratum per the governance erratum convention)

### Never do

- Touch any skill, pack, guide, journey, or site file — those belong to the
  downstream specs
- Collapse or reorder the ini-003 dependency DAG in `workspace.toml`
- Add decisions to RFC-0071 after it is Accepted

## Testing Strategy

All verification is structural — no runtime logic.

- **Goal-based:** `grep "Status: Accepted" docs/rfc/0071-digital-experience-doctrine.md`
  exits 0
- **Goal-based:** `grep "Date closed: 2026-07-23" docs/rfc/0071-digital-experience-doctrine.md`
  exits 0
- **Goal-based:** `grep "Status: Accepted" docs/rfc/0062-content-design-and-copy-direction-skills.md`
  exits 0
- **Goal-based:** `python3 -c "import tomllib; f=open('workspace.toml','rb'); d=tomllib.load(f); assert 'spec/rfc-digital-product-experience-doctrine' in d['ini-003']['work']['active']"`
  exits 0
- **Goal-based:** `python3 -c "import tomllib; f=open('workspace.toml','rb'); d=tomllib.load(f); items=d['ini-003']['work']['queue']; assert not any(i=='spec/rfc-digital-product-experience-doctrine' or (isinstance(i,dict) and i.get('path')=='spec/rfc-digital-product-experience-doctrine') for i in items)"`
  exits 0 (confirming the spec is removed from the queue)

## Acceptance Criteria

- [x] `docs/rfc/0071-digital-experience-doctrine.md` has `Status: Accepted` and
  `Date closed: 2026-07-23` in its frontmatter block.
- [x] `docs/rfc/0071-digital-experience-doctrine.md` `Review focus` section is
  updated: D2 and D9 are confirmed (or the open-question note is replaced with
  the confirmed decision text).
- [x] `docs/rfc/0062-content-design-and-copy-direction-skills.md` has
  `Status: Accepted`, `Date closed: 2026-07-23`, and an implementation note
  pointing to `spec/xd-copy-direction` under ini-003 as the fulfillment of
  `copy-direction`.
- [x] `workspace.toml` `["ini-003".work].active` contains
  `"spec/rfc-digital-product-experience-doctrine"`.
- [x] `workspace.toml` `["ini-003".work].queue` no longer contains
  `spec/rfc-digital-product-experience-doctrine` as a string or path key.
- [x] `workspace.toml` passes `python3 -c "import tomllib; tomllib.load(open('workspace.toml','rb'))"` with exit 0 and the 11 remaining queue items intact.
- [x] No skill files, pack files, guide files, site files, or journey files are
  modified in this PR.

## Assumptions

- RFC-0071 and RFC-0062 edits from the authoring session (Status + Date closed
  fields) have already been applied; this spec's implementing PR carries those
  edits as committed changes.
- `workspace.toml` `active` array is currently `[]` for `["ini-003".work]`;
  moving the spec from queue to active is an additive change with no ordering
  conflict.

## Boundaries — site, guide, journey

This spec ships no guide, site, or journey updates. The governance gate has no
user-facing output; downstream specs each ship their own per-phase-slice updates
per the ini-003 phase-slice doctrine.
