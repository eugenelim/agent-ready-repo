# Spec: RFC-0099 migration and validation record

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0099
- **Brief:** none
- **Discovery:** `docs/product/intents/cut-before-adding-solution-ladder.md`
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Maintainers can audit RFC-0099 follow-on #6 without mistaking executable route
checks for adopter research. The accepted record states that the five-adopter
study is waived and its usability question remains unanswered, closes the two
remaining activation and shaping-review fixture gaps, and provides one
maintained five-field register for all seven fixture families.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision correction | The accepted RFC misstates an unrun study as completed work | `docs/rfc/0099-cut-before-adding-and-artifact-shaping.md` Errata | RFC approver | Approver-signed Errata entry | Preserved body is unchanged and the ledger no longer calls the study a publication task |
| Validation status | The source intent still labels the waived study `to-validate` | `docs/product/intents/cut-before-adding-solution-ladder.md` | Product intent owner | Admitted status value or an explicit no-vocabulary finding | The hook matches the waiver without claiming validation |
| Fixture evidence | Two RFC fixture families lack required coverage | Existing activation suite and shaping-review QA fixture set | Core and shaping-review contract owners | Targeted tests plus fresh isolated reviewer results | R1-R12 and all six seeded defects have expected-result evidence |
| Fixture register | RFC-0099 required a versioned five-field register before acceptance | [`fixture-register.md`](fixture-register.md) | Core pack maintainers | Register integrity construction test | All seven families identify their maintaining evidence without duplicate fixtures |
| Delivery record | The register and corrective work need a durable implementation contract | This spec directory and `docs/specs/README.md` | Work-loop owner | Clean gates and adjudicated reviews | Spec is Shipped, plan is Done, and workspace membership is shipped |

## Boundaries

### Always do

- Preserve RFC-0099 body text above `## Errata` and append corrections only.
- Keep adopter comprehension, activation routing logic, and shaping-review
  detection efficacy as separate evidence claims.
- Reuse the shipped tests for the five already-discharged fixture families.
- Profile-gate governance and architecture activation fixtures.
- Assert seeded defect identity in live reviewer evidence, not exact finding
  totals.

### Ask first

- Change a public routing owner, compatibility window, reviewer mode, or
  lifecycle state beyond this corrective record.
- Add a router, model-test framework, dependency, or top-level directory.
- Modify the shipped shaping-reviewer contract rather than its fixtures and
  evidence.

### Never do

- Claim the five-adopter study passed, was completed, or was replaced by desk
  research or executable activation fixtures.
- Delete or rewrite the frozen R1-R12 answer key.
- Rebuild a fixture family already discharged by a shipped spec.
- Hand-edit generated pack projections or remove an accepted safety,
  validation, review, or approval requirement.

## Testing Strategy

- **Goal-based construction checks:** the activation suite makes R1-R12
  executable against the repository's existing prose-contract seam and skips
  only the optional-pack cases whose owning pack is absent. A register
  integrity test enforces the exact five columns, unique IDs, all seven family
  labels, and resolvable evidence paths.
- **Visual / manual QA:** three fresh isolated shaping-reviewer runs receive
  only the seeded intent, delivery-brief, or spec fixture. Each recorded result
  must identify both expected defects for that mode; finding totals remain
  informational.
- **Goal-based repository gates:** `make build` precedes lint, type, targeted
  and broader tests, catalogue verification, spec-status lint, and workspace
  reconciliation.

## Acceptance Criteria

### AC1 — The adopter study is waived honestly

- [x] One Approver-signed RFC-0099 Errata entry waives the five-adopter card
  sort and tree test while preserving the original body and R1-R12 answer key.
- [x] The Errata states that D7 remains unanswered and that four specs shipped
  on an untested usability premise.
- [x] The Errata records why the waiver is acceptable now without claiming the
  study passed, was superseded by desk research, or was satisfied by activation
  fixtures.
- [x] Follow-on #6 and the 2026-08-31 ledger are corrected through Errata so
  neither describes the unrun study as completed publication work.
- [x] The intent validation hook uses an admitted vocabulary value for a
  waived hook, or records plainly that its vocabulary has no such value rather
  than inventing one.

### AC2 — Activation fixtures cover the frozen answer key

- [x] `tests/roster/test_rfc0099_activation_coverage.py` contains executable
  R1-R12 cases for the eight named entry points and their near misses. The
  suite is repository-level because it reads the RFC answer key and skill
  contracts across packs, which `tools/lint-pack-test-boundary.py` forbids from
  inside `packs/core/tests/`.
- [x] The activation expectations preserve the RFC answer key, including
  `work-intake` delegation counting as one route for R3 and R11.
- [x] R5 and R6 are gated on the governance and architect pack profiles rather
  than assumed available in Core-only installations.
- [x] The test states that the full eight-entry-point contract is prose-based
  because no deterministic callable router owns all eight routes.

### AC3 — Shaping-review fixtures prove defect detection

- [x] Seeded intent, delivery-brief, and spec artifacts cover unnecessary
  intents, wrapper briefs, speculative slices, vague spec objectives, missing
  boundaries, and unsafe simplification.
- [x] Every seeded defect has a stable expected-result key that is kept
  separate from the artifact supplied to the reviewer.
- [x] Each fresh isolated reviewer report is persisted raw and independently
  adjudicated against the unchanged seeded artifact and governing shaping
  authority before any seeded defect key is classified.
- [x] Three fresh isolated reviewer adjudications sustain identification of
  every applicable seeded defect, with no assertion on the total number of
  raw or sustained findings.
- [x] The QA record distinguishes these seeded efficacy results from its prior
  unseeded runs.

### AC4 — One maintained register covers all seven families

- [x] `fixture-register.md` has exactly the fields `Fixture ID`, `Prompt or
  seeded defect`, `Installed profile`, `Exact expected result`, and `Owner` for
  every row.
- [x] The register covers activation, alias, shaping-review, RFC and
  architecture-review, delivery-state, core-only, and boundary families.
- [x] Existing discharged families point to their shipped tests instead of
  gaining parallel fixtures.
- [x] The register says it was written after acceptance even though RFC-0099
  required it before acceptance.
- [x] A pack construction test fails when a field, family, fixture ID, owner,
  or referenced evidence path is missing.

### AC5 — Delivery state is closed and reviewable

- [x] Canonical sources and generated projections are consistent after the
  supported build path.
- [x] Applicable lint, type, targeted test, broader test, catalogue, and
  spec-status gates pass with make exit codes captured directly.
- [x] Adversarial, security, and quality reports are independently adjudicated
  and reach `Clean — ready to commit.`
- [x] This spec is `Shipped`, its plan is `Done`, and `workspace.toml`
  reconciles the spec under shipped work before `CODE-HUMAN-GATE`.

## Follow-ons

None. The frozen R1-R12 answer key remains available if a later owner chooses
to run a new adopter study, but this waiver does not schedule one.

## Assumptions

- Technical: no callable router owns all eight activation entry points, so the
  repository's existing prose-contract construction-test mode is the highest
  deterministic seam (source: `tests/roster/test_rfc0099_activation_coverage.py`; verified 2026-08-31).
- Technical: the shipped shaping reviewer already names all six checks, while
  detection efficacy needs seeded fresh-context evidence (source:
  `docs/specs/shaping-review-contracts/spec.md` and `notes/qa.md`; verified
  2026-08-31).
- Product: the five-adopter study did not run, D7 remains unanswered, and four
  specs shipped on the untested premise (source: user confirmation 2026-08-31).
- Process: the user's three-deliverable brief is the approved scope and the
  repository stops at the final code human gate (source: user confirmation
  2026-08-31).
- Process: RFC-0099 body text is frozen and corrections append under Errata
  (source: `docs/CONVENTIONS.md` and RFC-0099).
