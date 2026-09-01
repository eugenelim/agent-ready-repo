# Plan: RFC-0099 migration and validation record

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `docs/rfc/0099-cut-before-adding-and-artifact-shaping.md`; `docs/specs/core-guidance-artifact-routing/spec.md`; `docs/specs/shaping-review-contracts/{spec.md,notes/qa.md}`; `packs/core/tests/skills/work-intake/test_routing_precedence.py`; deviation: the RFC-required fixture register does not yet exist, and the eight-route activation contract has no single callable router

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. Once it is `Done` and the spec is `Shipped`, the directory
> freezes as a unit.

## Approach

Correct the accepted record first, then close only the two missing fixture
families and compile their evidence with the five already-shipped families into
one register. Activation uses the existing prose-contract test seam. Shaping
efficacy uses three seeded artifacts reviewed in fresh isolated contexts, with
expected keys checked independently from non-deterministic finding totals.

## Constraints

- RFC-0099 and its Approver-signed Errata are normative; body text above
  `## Errata` is preserved.
- `docs/CONVENTIONS.md` freezes accepted RFC bodies and shipped spec
  directories.
- Root and pack `AGENTS.md` require the cut-before-adding ladder, canonical
  `.apm` source ownership, supported projection generation, and direct gate
  exit-code capture.
- The user explicitly bars rebuilding the five discharged fixture families,
  inventing a callable router, conflating logic checks with comprehension, and
  proceeding past `CODE-HUMAN-GATE`.

## Construction tests

**Integration tests:** the register integrity test resolves every evidence path
and maps all seven families; the targeted activation suite and three recorded
fresh reviewer results jointly discharge the two open families.

**Manual verification:** inspect the RFC diff to prove every change is below
`## Errata`; inspect the final workspace-status reconciliation; confirm the
three live reviewer records identify their expected defect keys without exact
count assertions.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| RFC Errata and intent hook | T1 | RFC/intent diff plus doc checks | AC1 and final adversarial review |
| Activation fixtures | T2 | Targeted pytest | AC2 and register rows R1-R12 |
| Shaping efficacy fixtures | T3 | Three seeded targets and fresh isolated reports | AC3 and QA record |
| Five-field fixture register | T4 | Register integrity pytest | AC4 and specs index |
| Delivery record and workspace state | T5 | Full gates and adjudicated reviewer artifacts | AC5 and workspace reconciliation |

## Design (LLD)

### Design decisions

- Use the existing static/prose contract mode for routes with no runtime router;
  adding a synthetic router would create a second owner for activation.
- Keep expected shaping defect keys outside the reviewed fixture bodies so the
  live reviewer must detect defects rather than echo an answer key.
- Register already-shipped families by stable suite reference rather than by
  duplicating their fixtures.

### Component / module decomposition

- Governance correction: RFC Errata plus the source intent hook.
- Executable coverage: the existing activation suite and a small register
  integrity construction test.
- Manual efficacy evidence: three fixture targets and the existing shaping QA
  record.
- Durable navigation: one fixture register linked from this spec and the specs
  index.

### State & control flow

The full-mode work-loop owns Draft → Approved → Implementing → Shipped and
Drafting → Approved → Executing → Done. `workspace.toml` moves the spec through
active to shipped membership and is reconciled before the final human gate.

### Behavior & rules

- Study waiver evidence and activation evidence remain separate claims.
- R1-R12 route expectations stay byte-faithful in meaning to the frozen answer
  key, including the one-route delegation rule.
- Shaping efficacy passes on expected defect identification, not a fixed number
  of findings.
- The register schema is exactly five fields per row.

## Tasks

### T1: The accepted record describes an explicit waiver without a false completion claim

**Depends on:** none

**Tests:**
- Goal-based: a bounded RFC diff shows changes only in a new Errata entry below
  `## Errata`, and the entry contains the unanswered D7, four-spec premise,
  waiver rationale, preserved-answer-key, and no-conflation statements.
- Goal-based: a repository search confirms the intent hook uses an admitted
  status value or contains an explicit vocabulary-gap statement.

**Approach:**
- Append one Approver-signed Errata entry that corrects both follow-on #6 and
  the 2026-08-31 ledger by reference.
- Update only `validation_hook.status` and the immediately owned intent wording
  needed to make the waiver honest.

**Done when:** AC1 is mechanically and textually reviewable without editing the
frozen RFC body.

### T2: R1-R12 exercise all eight activation entry points without a synthetic router

**Depends on:** T1

**Tests:**
- Goal-based: targeted pytest of
  `packs/core/tests/skills/work-intake/test_routing_precedence.py` passes all
  R1-R12 parameter cases and existing precedence checks.
- Goal-based: governance and architect rows skip only when their profile pack
  is absent.

**Approach:**
- Extend the existing suite with a typed case matrix, bounded frontmatter/body
  reads, and route-specific contract assertions.
- Preserve the existing callable-router tests for the three routes it owns;
  treat prose activation as the explicit verification mode for the other five.

**Done when:** the frozen answer key is executable and no test invents a second
public route.

### T3: Seeded shaping artifacts prove all six defect types are detected

**Depends on:** T2

**Tests:**
- Visual/manual QA: fresh isolated intent, delivery-brief, and spec reviews
  each identify the two expected defects for their mode.
- Goal-based: persist and validate each raw report, pass it through
  `finding-adjudicator` against the unchanged seed and shaping authority, then
  map stable expected-result keys only from the adjudication artifact; assert
  no exact raw or sustained finding total.

**Approach:**
- Add one intentionally flawed artifact per reviewer mode, with two applicable
  defects in each and no embedded answer key.
- Run fresh isolated shaping reviewers against those artifacts and record the
  adjudicated defect identification in the existing QA method and scope.

**Done when:** all six expected keys have live detection evidence distinct from
the older unseeded runs.

### T4: The five-field fixture register is complete and maintained

**Depends on:** T2, T3

**Tests:**
- Goal-based: a pack construction test parses the register table and asserts
  its exact header, unique fixture IDs, all seven family prefixes, non-empty
  owners, and repository-confined evidence paths that exist.
- Goal-based: the test asserts the post-acceptance disclosure and the specs
  index links the register-owning spec.

**Approach:**
- Write the register with R1-R12, six shaping defects, and bounded aggregate
  entries for the five shipped fixture families that cite their existing
  suites.
- Add the smallest dedicated integrity test because no existing test owns a
  cross-family registry contract.

**Done when:** maintainers can update one file rather than reconstruct coverage
by grep.

### T5: Generated state, gates, reviews, and workspace membership are clean

**Depends on:** T1-T4

**Tests:**
- Goal-based: run `make build` before every repository gate group and capture
  `EXIT=$?` from make itself.
- Goal-based: targeted and broader pytest, lint, type, catalogue, spec-status,
  projection, and workspace reconciliation checks pass.
- Review: adversarial, security, and quality reports each pass independent
  finding adjudication and reach exact clean.

**Approach:**
- Regenerate only through supported build/projection commands.
- Mark ACs and lifecycle statuses only after evidence exists, move the
  workspace entry to shipped, then stop at `CODE-HUMAN-GATE`.

**Done when:** AC5 is satisfied and the engine reports a pending final human
gate.

## Rollout

This is a documentation-and-fixture release with no runtime migration. Revert
the single change set if evidence is rejected; the frozen answer key and all
five pre-existing fixture families remain intact.

## Risks

- Static activation assertions can become tautological if they check only the
  test matrix; each row must bind to the owning skill's activation or routing
  prose.
- A live shaping reviewer may report extra defects; only the seeded defect
  identities are deterministic.
- A register path can drift silently unless its integrity test resolves every
  cited repository file.
- Workspace state can become premature if it moves to shipped before spec and
  plan statuses reach their terminal values.

## Changelog

- 2026-08-31: initial plan from RFC-0099 follow-on #6 and the user's migration
  and validation brief; declined a synthetic router, duplicated shipped
  fixtures, and exact live-review finding counts.
- 2026-08-31: repaired the draft-origin review gap by requiring independent
  adjudication before seeded shaping findings are mapped to expected keys.
