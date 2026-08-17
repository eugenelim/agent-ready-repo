# Manual QA — project knowledge authoring integrations

Date: 2026-08-16

## Disposable adopter-shaped journey

A disposable Git repository under the approved temporary root received the
real self-hosted `.agents` projection of `project-knowledge`, `receive-brief`,
`new-rfc`, `new-adr`, and `work-loop`. Its coherent v1 map was activated, then
the projected public `project_knowledge.py --capture` CLI received one strict
request for each shipped authoring gate.

Redacted result:

- `brief-ready`: pass;
- `rfc-handoff-ready`: pass;
- `adr-accepted`: pass;
- `spec-approved`: pass;
- `plan-locked`: pass;
- five unique receipts returned; capture IDs and bodies were not printed;
- a private-data and instruction-shaped observation was refused with a
  redacted diagnostic and no rejected body in output;
- a consequential enquiry over a committed topic whose owning source was
  unavailable abstained with an empty selected-topic list.

The fixture used only placeholder identity data and was destroyed when the
run completed. No workspace Git ref or index was changed.

## Negative authoring paths and authority

Construction tests over the canonical sources, followed by forced self-host
parity, prove the corresponding projected behavior:

- Draft brief and spec work, incomplete DoR, failed or rolled-back Ready
  workspace transitions, unclean RFC checks, preview-only RFC/ADR work,
  Proposed/rejected ADRs, stale plan baselines, and abandoned work make no
  capture call; a Ready brief with zero specs remains eligible;
- every producer constructs the published typed request and calls only
  `project-knowledge --capture`;
- producers do not import the private writer, locate journals, derive IDs,
  choose partitions, or create fallback storage;
- missing project knowledge emits exactly `project-knowledge unavailable` and
  leaves authoring completion intact;
- terminal distillation uses only same-gate `workflow-receipts`; spec receipts
  remain pending, and plan locking cannot guess them or select
  `direct-maintainer-pending`;
- brief, RFC, ADR, spec, and plan normative content remains solely in its
  owning artifact;
- optional enquiry is separately declared with `CQ-DESIGN`, `CQ-CHANGE`, or
  `CQ-VERIFY`, one query plus at most one refinement, untrusted-evidence
  treatment, and consequential abstention.

## Automated verification

- Core authoring skill directories: **pass** — author-brief `1`,
  receive-brief `20`, new-spec `1`.
- Governance authoring skill directories: **pass** — new-rfc `10`, new-adr `9`.
- Complete project-knowledge suite: **pass** — `169 passed`.
- Complete work-loop skill suite: **pass** — `457 passed, 5 skipped`.
- Ruff: **pass**.
- Deep catalogue lint and catalogue verify: **pass**.
- Forced self-host write and check: **pass**; canonical `.apm`, `.agents`, and
  `.claude` skill/eval projections agree.
- Journey regeneration also changed the deterministic
  `web/src/content/journeys/core.md` and `governance-extras.md` parity outputs.
  These are required consequences of the planned pack JOURNEY edits, not an
  additional authored behavior surface.
- `SKIP_SAST=1 make build-check`: **pass for every non-SAST gate** after the
  journey-label correction. The command correctly reports the overall run as
  incomplete because its SAST/SCA leg was intentionally skipped and was
  exercised separately as described next.
- Repository security scan: Bandit and audit-requirements self-tests **pass**.
  The dependency-audit leg was attempted once and is environment-blocked
  because the managed Python cannot run `ensurepip` in its temporary virtual
  environments. No install, audit bypass, or retry was attempted.
- Private comparison-name scan of changed implementation bytes: **pass**; only
  this result is recorded.

### Behavior-eval disposition

All six changed skills ship Tier-4 rubric files that parse as strict JSON and
pass catalogue eval-roster/structure checks. `author-brief` also carries nine
activation positives and nine adjacent near misses.

The report-only model-judge runner was attempted once with the installed Codex
read-only backend over representative core artifacts for `author-brief`,
`receive-brief`, `new-spec`, and `work-loop`. The backend returned an
unparseable judge result for all four, so the runner correctly recorded four
`ERROR` verdicts rather than false passes. Governance judging was not retried
through the same failed backend. This managed-environment harness limitation
is an explicit deferral, not a product-test pass; construction tests, strict
eval parsing, catalogue checks, and the disposable real-CLI journey remain the
observable delivery evidence.

## Review

Three implementation review rounds completed. Round 1 found request/confinement
coverage, review-return, non-gate, documentation, Git-root, activation, and
closeout gaps. Round 2 found release-note, legacy-writer, private-boundary,
redacted-diagnostic, security-metadata, and lifecycle-ordering gaps. After the
recorded fixes and repeated gates, the adversarial, security, and quality
reviewers each returned `Clean — ready to commit.`

Lifecycle closeout marks all 22 acceptance criteria complete, the spec
`Shipped`, the plan `Done`, and the workspace entry shipped. A final
`workspace-status` reconciliation reports this item clean and leaves
`project-knowledge-review-research-integrations` as the next lifecycle slice,
blocked because its canonical spec has not yet been created.

The workspace permission profile forbids staging, committing, or updating Git
refs, so delivery will stop at the repository's human merge gate.
