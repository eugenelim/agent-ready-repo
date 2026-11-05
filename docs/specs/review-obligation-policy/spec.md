# Spec: Review obligation policy

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0158, ADR-0144
- **Brief:** none
- **Discovery:** capability:work-loop-delivery-efficiency
- **Depends on:** spec:execution-supervisor-review-gate, spec:structured-review-boundary
- **Contract:** `contracts/delivery/review-carry.v1.schema.json` (defined here); `contracts/delivery/execution-request.v1.schema.json` (amended additively: `delta_base` and `repair_finding_ids` on `review-role`, and the `review-cap` request fields); `contracts/delivery/execution-result.v1.schema.json` (amended additively: `protected_classes` and `review_tier` on the selection object, and the `extend-review` decision); `packs/core/.apm/skills/work-loop/review-rules.json` (new keys); `delivery/review-anchors.jsonl` (defined here)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A maintainer running a full-mode `code` run gets one full reviewer pass per unit, after which each repair costs only the reports its diff earns: none for a wording-only repair, one delta pass for a rebase or a minor fix, and the full set otherwise. Every protected reviewer reports on every revision, and an unprotected review that has not converged after two rounds stops with a `review-cap` decision naming each open finding by finding id, role, and report id.

## What Changes

- A diff classifier assigns each repaired review subject a tier: `wording-only`, `rebase`, `minor-fix`, or `full` — `packs/core/.apm/skills/work-loop/scripts/`.
- The supervisor records the facts of each anchor round in `delivery/review-anchors.jsonl`, and the classifier compares against those facts only.
- A supervisor-written `review-carry.v1` record lets a role that a tier excuses stand on its latest report — `contracts/delivery/review-carry.v1.schema.json`, the evidence store's semantic-record registry, and review readiness.
- Every reviewer selection declares `protected_classes`, and each declared class makes its mapped reviewer protected — `review-rules.json`, the selection object, and `delivery/review-selections.jsonl`.
- `review-rules.json` gains `code_review_round_cap`, `minor_fix_max_lines`, the prose allowlist, and the class-to-reviewer map.
- The supervisor issues `review-cap` at the cap and admits `extend-review` — `execution-request.v1`, `execution-result.v1`, and `references/supervisor.md`.
- The Obligation and Disposition tables of `structured-review-boundary`, and the mechanical-predicate rule of `execution-supervisor-review-gate`, gain the rows and carve-out ADR-0158 decides.
- The skill's full-mode REVIEW step names tiers, protected classes, and the cap — `packs/core/.apm/skills/work-loop/SKILL.md`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | The policy is an accepted decision. | `docs/adr/0158-review-obligation-policy-round-cap-and-tiers.md` (Accepted) | eugenelim | ADR shape lint | ADR-0158 is Accepted and ADR-0144 records `Superseded in part: ... ADR-0158 D8`. |
| Interface compatibility | New and amended delivery contracts. | `contracts/delivery/`, `contracts/README.md`, `contracts/REGISTRY.md` | Core pack maintainers | Delivery contract bundle tests | AC-0015, AC-0032, and AC-0033 hold. |
| Current architecture | Two Shipped specs state rules this policy amends. | `docs/specs/structured-review-boundary/spec.md` (Obligation truth table: a carried-report row; Disposition truth table: an `accept-risk` row for a finding on an earlier subject of the unit; Never-do: the carry carve-out), `docs/specs/execution-supervisor-review-gate/spec.md` (Never-do: the tier-predicate exception) | eugenelim | Reviewer read; the owner's approval of ADR-0158 and of this spec authorizes exactly these edits | Each edited row and rule names ADR-0158 and this spec, and no other criterion of either spec changes. |
| Maintainer procedure | The controller answers new requests and declares classes. | `packs/core/.apm/skills/work-loop/references/supervisor.md` (Review section, request-kinds table, human-decision table), `packs/core/.apm/skills/work-loop/SKILL.md` (Step 4, full mode) | Core pack maintainers | Supervisor reference content pins | The human-decision table has a `review-cap` row, and the Review section names the tiers, the carry record, `protected_classes`, and the cap. |
| Skill evaluation | Live review behaviour changes. | `packs/core/.apm/skills/work-loop/evals/evals.json` | Core pack maintainers | Skill evals | Evals cover a tier, a carried role, a protected role under `wording-only`, and `review-cap`. |
| Release history | Live code changes. | Core manifests and a `docs/product/changelog.d/` fragment | Core pack release maintainers | Version parity | AC-0034 holds. |

## Agent Rules

### Always do

- Classify a tier only from the supervisor's own Git reads and the recorded anchor facts, and classify `full` on any doubt.
- Show a `review-cap` finding only by its supervisor-derived reference, its role, and the round it was raised on.
- Write `review-carry.v1` and `review-anchors.jsonl` lines only inside the supervisor's own `review` step.

### Ask first

- Changing the class-to-reviewer map, `code_review_round_cap`, `minor_fix_max_lines`, or the prose allowlist defaults.
- Adding, removing, or redefining a tier or a protected class.
- Amending any criterion, table row, or rule of `structured-review-boundary` or `execution-supervisor-review-gate` beyond the edits this spec's Durable Outputs name.

### Never do

- Let a tier, a carry record, or the cap excuse, carry, or cap a protected role.
- Let a tier add or remove a role from the controller's selection, or let any input lower a tier below the one the diff earns.
- Echo a reviewer-supplied identifier or string in an owner-facing decision.
- Change pre-approval review, light mode, `review-artifact.py`, or `max_review_retries`.
- Add a dependency outside the standard library and Git, or a new top-level directory.

## Testing Strategy

- **Tier classification (AC-0002, AC-0003, AC-0004, AC-0006, AC-0008, AC-0011):** TDD over throwaway Git repositories built in the test, one fixture per tier and per fail-closed case, because the classifier is a pure function of the anchor facts, the current result, and the rules.
- **Anchor facts (AC-0013):** TDD over the anchor writer and reader, with a fixture whose history an adopted rebase rewrote.
- **Carry and readiness (AC-0014, AC-0015, AC-0016):** TDD over evidence-store fixtures, because the carry rules are a decision table over typed records.
- **Selection and protection (AC-0017, AC-0018, AC-0019, AC-0021, AC-0022):** TDD over selection records and the resolver.
- **Requests across subjects (AC-0001, AC-0005, AC-0007, AC-0009, AC-0010, AC-0012, AC-0020):** goal-based, exercised by integration runs in the supervisor harness that drive one unit through every tier and past the cap round, because these properties only show across several subjects.
- **Cap and decisions (AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028, AC-0029):** goal-based integration runs in the supervisor harness, with TDD for decision admission.
- **Rules (AC-0030, AC-0031):** TDD over rules validation.
- **Contracts and release (AC-0032, AC-0033, AC-0034):** goal-based schema-bundle and version-parity checks.

## Acceptance Criteria

### Definitions

- **Unit.** One run's code-review stage.
- **Round.** A review subject on which the supervisor issued at least one `review-role` request, and which is either the unit's first full-set subject or the first subject reached after a repair of supported findings. A subject counts once, however many `implement` steps produced it. A `rebase` subject and a `wording-only` subject are not rounds.
- **Anchor round.** The last round of the unit on which every selected role returned a report for that round's subject.
- **Anchor facts.** The line the supervisor appends to `delivery/review-anchors.jsonl` when an anchor round's last report is admitted: the anchor result commit, the run base, the changed-path set, and each path's `git patch-id --verbatim` from the run base to the anchor result.
- **Run base.** The parent of the earliest `stub` or `implement` commit of the run in the current result's history, defined only when every commit between it and the result is a commit of this run.
- **Open finding.** A supported material finding raised on any subject of the unit, the anchor round's included, and not closed by `fixed-by` or `accept-risk`.
- **Protected class.** One of five tokens: `security-boundary`, `data-durability`, `migration`, `public-interface`, `irreversible-operation`.
- **Protected role.** A role in the resolved policy (the always-selected roles plus the selected ones) that `review-rules.json` maps from a class the unit declares: `security-boundary` → `security-reviewer`; `data-durability` → `quality-engineer`; `migration` → `quality-engineer`; `public-interface` → `adversarial-reviewer`; `irreversible-operation` → `adversarial-reviewer`.
- **Protected unit.** A unit that declares any protected class, or that reads a selection line with no `protected_classes` field (protection unknown).
- **Cap finding reference.** `cap-finding:` followed by the first 16 hex characters of the sha256 of the finding's report id, a NUL byte, and its finding id.

### Criteria

Tiers

- [ ] **AC-0001.** A unit's first review subject is requested from every selected role.
- [ ] **AC-0002.** A repaired subject classifies `full` when, over the union of the anchor's and the current changed-path sets, the diff from the anchor result holds any of: a status other than modified; a mode other than `100644` or `100755` on either side; a blob that contains a NUL byte or is not valid UTF-8 on either side, read by the supervisor without Git attributes; an unreadable blob; more than 1 MiB of diff output; no anchor facts; an anchor result commit that is not in the object store; or a classifier error.
- [ ] **AC-0003.** A repaired subject classifies `wording-only` only when no finding is open, every changed path matches the prose allowlist, no changed path's basename matches an instruction name without regard to case, and no instruction-named file at the current result names a changed path on an `@` import line.
- [ ] **AC-0004.** A repaired subject also classifies `wording-only` only when a whole-file scan at both the anchor and current results places every changed line in plain prose, gives every unchanged line the same block kind at both results, and finds no inline code, link, link target, reference link definition, autolink, heading, or table on any changed line. Plain prose excludes fenced code, indented code, front matter, HTML comments, and raw HTML.
- [ ] **AC-0005.** A `wording-only` subject issues no `review-role` request to a role that is not protected.
- [ ] **AC-0006.** A subject classifies `rebase` only when all of these hold:
  - no finding is open;
  - an adopted reanchor changed the product but not the spec directory;
  - the run base is defined;
  - the changed-path set equals the anchor's;
  - each path's `git patch-id --verbatim` from the run base to the current result equals its anchor fact.
  With Git older than 2.39 it classifies `full`.
- [ ] **AC-0007.** A `rebase` subject's only non-protected request is one delta pass from `adversarial-reviewer`, naming the anchor result as `delta_base` and an empty `repair_finding_ids`.
- [ ] **AC-0008.** A subject classifies `minor-fix` only when a finding is open, every changed path is in the anchor's changed-path set, and the added plus removed lines from the anchor result over the union of the two changed-path sets number at most `minor_fix_max_lines`. A delta of `minor_fix_max_lines + 1` lines from the anchor result classifies `full`, however many repairs it took to accumulate.
- [ ] **AC-0009.** A `minor-fix` subject requests one delta pass from each non-protected role that raised an open finding, and from no other non-protected role. Each request names the anchor result as `delta_base` and that role's open findings as `repair_finding_ids`.
- [ ] **AC-0010.** A supported material finding raised on a rebase delta pass stays open through each later `minor-fix` subject until a fresh report closes it with `fixed-by` or a risk owner accepts it.
- [ ] **AC-0011.** A subject whose resolved roles, kinds, or declared classes differ from the anchor round's classifies `full`.
- [ ] **AC-0012.** A selection answer with `review_tier: "full"` makes a subject `full` and requests every selected role, even when its diff earns a lower tier. Any other `review_tier` value is refused with `review-selection-invalid`.

Anchor facts

- [ ] **AC-0013.** Each anchor round appends exactly one anchor-facts line, and the classifier reads the anchor result, run base, changed-path set, and patch ids only from that line. After an adopted rebase rewrites the run's commits, the classifier compares against the recorded facts, not against the rewritten history.

Carry

- [ ] **AC-0014.** For each selected role that a tier excuses, readiness counts that role's obligation on the current subject as satisfied by exactly one `review-carry.v1` record. The carried report's assessments and dispositions count with it.
- [ ] **AC-0015.** Readiness does not count a `review-carry.v1` record that names a protected role, a role with an open finding, a report that is not that role's latest report or carry, a subject other than the current one, or a tier or policy fingerprint other than the ones readiness derives for the current subject.
- [ ] **AC-0016.** `contracts/delivery/review-carry.v1.schema.json` is closed and listed in the delivery contract bundle.

Selection and protection

- [ ] **AC-0017.** A selection answer is refused with `review-selection-invalid` when it has no `protected_classes`, names a token outside the five, declares a class whose mapped reviewer is not in the resolved policy, or selects `security-reviewer` without declaring `security-boundary`.
- [ ] **AC-0018.** These selection answers are admitted: `protected_classes: []` without `security-reviewer`; `["security-boundary"]` with `security-reviewer` selected; and `["public-interface"]` with no conditional role selected.
- [ ] **AC-0019.** Two selections that differ only in declared classes resolve to different `review_policy_fingerprint` values.
- [ ] **AC-0020.** In a unit that selects `security-reviewer`, every new subject under every tier (`full`, `minor-fix`, `rebase`, `wording-only`), and every subject after the cap round, issues a whole-change `security-reviewer` `review-role` request with no `delta_base`, and no `review-carry.v1` record names `security-reviewer`. The same holds for each other protected role of its unit.
- [ ] **AC-0021.** A selection whose declared classes or protected roles are not a superset of the unit's earlier selections is refused, unless an admitted owner `reselect-review` decision for that selection key authorizes it.
- [ ] **AC-0022.** A unit that reads a selection line with no `protected_classes` field classifies every subject `full`.

Cap and decisions

- [ ] **AC-0023.** The round count covers the whole unit, counts exactly the subjects the Round definition names, counts a repair spanning two `implement` steps once, and does not change when a selection is recorded.
- [ ] **AC-0024.** In an unprotected unit, when round `code_review_round_cap` leaves a supported material finding open, the next request is a `review-cap` human decision, not `review-not-eligible` and not a repair. It carries the round count, the unit's current selection key, and each open finding as its cap finding reference, role, and round. It holds no reviewer-supplied identifier or string.
- [ ] **AC-0025.** The `review-cap` request id is derived from the run id, the round count, and the sorted cap finding references, and stays the same across commits that change none of them.
- [ ] **AC-0026.** A `review-cap` answer of `accept-risk` with a `risk-owner` authority reference and a set of cap finding references disposes exactly those findings, whichever subject raised them, and readiness then counts them closed.
- [ ] **AC-0027.** A `review-cap` answer of `extend-review` with an `owner` authority reference permits exactly one more round before the next `review-cap`.
- [ ] **AC-0028.** A `review-cap` answer of `reselect-review` with an `owner` authority reference and the request's selection key authorizes one new selection. Any other answer, a malformed answer, or no answer leaves the findings open and the same request outstanding.
- [ ] **AC-0029.** A protected unit never issues `review-cap`.

Rules

- [ ] **AC-0030.** The resolver refuses with a named error, and the review stage stays unsatisfied, when `code_review_round_cap` or `minor_fix_max_lines` is missing or not a positive integer, or the prose allowlist or the class-to-reviewer map is missing or malformed.
- [ ] **AC-0031.** The shipped `review-rules.json` holds `code_review_round_cap` 2 and `minor_fix_max_lines` 40, and its `max_review_retries` equals the value at `git merge-base origin/main HEAD`.

Contracts and release

- [ ] **AC-0032.** `execution-request.v1` admits `delta_base` and `repair_finding_ids` on a `review-role` request, and a `review-cap` request whose `open_findings` entries hold exactly a cap finding reference, a role, and a round. It refuses an entry with any other field.
- [ ] **AC-0033.** `execution-result.v1` admits a selection with `protected_classes` drawn from the five tokens and an optional `review_tier` of `full`, and admits an `extend-review` decision with an `owner` authority reference.
- [ ] **AC-0034.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry one patch above the version `packs/core/pack.toml` carries at `git merge-base origin/main HEAD`, checked right after `git fetch origin` with the merge base equal to `origin/main`, and one `docs/product/changelog.d/` fragment names that version.

## Follow-ons

- eugenelim: ADR-0158 D8 — a round cap on the pre-approval review loops (shaping, spec-mode adversarial, and security review of the spec and plan).

## Assumptions

- Defaulted: Technical: release size — default: one Core patch, because `review-carry.v1` is a contract schema, not a pack primitive; if wrong: a minor bump (settled by: eugenelim).
- Defaulted: Technical: `minor_fix_max_lines` — default: 40 added plus removed lines from the anchor result; if wrong: a data edit to `review-rules.json` (settled by: eugenelim).
- Defaulted: Technical: prose allowlist — default: Markdown and plain text under `docs/`, plus root `README.md`, `CHANGELOG.md`, and `CONTRIBUTING.md`; instruction names `AGENTS.md`, `AGENTS.local.md`, `CLAUDE.md`, `CLAUDE.local.md`, `GEMINI.md`, `SKILL.md`, `AGENT_RULES.md`, and `copilot-instructions.md` refused anywhere, without regard to case; if wrong: a data edit to `review-rules.json` (settled by: eugenelim).
- Defaulted: Product: parent intent — default: `capability:work-loop-delivery-efficiency`, because CAP-0012's boundary names delivery speed and token cost as that intent's; if wrong: the `Discovery:` header names CAP-0012 and CAP-0012 gains a child (settled by: eugenelim).
