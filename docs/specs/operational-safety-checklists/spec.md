# Spec: operational-safety-checklists

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0031, RFC-0041 (P3 + the deferred-authority pointer); ADR-0018 (orchestrator-loaded progressive-disclosure depth library — the `security-checklists` pattern this mirrors); ADR-0023 (the three-reviewer ceiling — why this feeds `quality-engineer`, not a new reviewer); ADR-0017 (the SAST/SCA scanner family the deferred-authority pointer complements)
- **Brief:** none
- **Contract:** none
- **Shape:** n/a — new reference-library skill (prose modules) + prose wiring edits; no application LLD

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Agents and adopters running the `core` pack get an **`operational-safety`
reference library** — a new skill of boundary-keyed `references/*.md` modules,
structurally identical to `security-checklists` — that gives infrastructure work
an operational-safety depth library the **existing `quality-engineer` reviewer**
reasons from. When the work-loop orchestrator detects infra/destructive work it
loads only the matching modules and inlines them into the `quality-engineer`
brief, via the same table-driven mechanism it already uses for
`security-checklists` — so idempotency, blast radius, environment isolation,
cost/teardown, drift/rollback, and observability/smoke get first-class reviewer
depth **without a fourth reviewer** (ADR-0023). The skill carries **six** modules
(MECE along operational failure mode), a routing-table entry in `work-loop`
SKILL.md, a one-line consumer note in `quality-engineer.md`, and a URL-free,
version-free deferred-authority pointer added to `security-checklists`'
`config-misconfig` module. The change adds **no executable code**: the modules
are prose the reviewer reasons from, exactly as the security depth library is.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Place the new skill at `packs/core/.apm/skills/operational-safety/`
  (source), mirroring `security-checklists`' structure: a `SKILL.md` with a
  front-matter `description`, a "How it loads (orchestrator-driven, not
  self-discovered)" section, the carve statement, and a `references/` directory
  of six module files. Then `make build-self` to project it to
  `.claude/skills/operational-safety/`.
- Name the six module files exactly: `state-and-idempotency.md`,
  `blast-radius.md`, `environment-isolation.md`, `cost-and-teardown.md`,
  `drift-and-rollback.md`, `observability-and-smoke.md`.
- Write **every** module tool-neutral; illustrative examples are labelled
  illustrative, never normative (Principle 1).
- State the **reliability-vs-security carve** in both skills' front matter /
  bodies: `security-checklists` owns *security* config; `operational-safety` owns
  *reliability/ops* config. The routing assigns IaC-security → `config-misconfig`,
  IaC-reliability → `operational-safety`.
- Exclude `operational-safety` from `[pack.evals]` in `packs/core/pack.toml` and
  add a comment naming it as deliberately excluded (reviewer-internal, never
  self-discovered — exactly as `security-checklists` is excluded).
- Run **all** lint surfaces before declaring done: `make build-check`,
  `python tools/lint-agent-artifacts.py`, `python tools/lint-agents-md.py`.
- Bump the `core` pack version (`pack.toml` + projected `marketplace.json` via
  `make build-self`) and add a `docs/product/changelog.md` `[Unreleased]` entry.

### Ask first

- **Merging any `operational-safety` module with a `security-checklists`
  module**, or moving content across the carve — the reliability-vs-security
  split is load-bearing; surface before blurring it.
- **Adding a seventh module** beyond the six RFC-0041 fixed — surface the case.
- Editing `quality-engineer.md` beyond the one consumer note (its review
  checklists are out of scope; the modules supply depth, they don't rewrite the
  agent).

### Never do

- **Ship executable code in the skill** — the modules are prose the reviewer
  reasons from (ADR-0031); no scripts, no runtime.
- **Bind any module to a specific IaC tool** (Principle 1).
- **Put a URL or a version number in the deferred-authority pointer** — it names
  the stable publisher + document only (CIS Benchmarks; the per-provider
  well-architected security guidance), kept evergreen by naming not linking; the
  actual depth lives in the self-updating scanner, not the pointer.
- **Duplicate security config into `operational-safety`**, or migrate operational
  config out of where it correctly lives — the carve stays clean both ways.

## Testing Strategy

This change is a new prose skill plus prose wiring edits — no executable logic —
so verification is **goal-based** plus **judgmental review**, with no TDD. This
mirrors how `security-checklists` and `work-loop-light-mode` were verified.

- **Skill structure** (the skill exists at the source path; six module files
  present with the exact names; SKILL.md mirrors the `security-checklists` shape):
  goal-based — `ls` / `grep`.
- **Wiring presence** (the `operational-safety` routing table is in `work-loop`
  SKILL.md; the `quality-engineer.md` consumer note is present; the
  deferred-authority pointer is in `config-misconfig.md`): goal-based — `grep`.
- **Deferred-authority pointer hygiene** (no URL, no version string in the
  pointer): goal-based — `grep` for `http`/`www`/version patterns in the added
  block returns nothing.
- **Carve correctness** (no security config duplicated into `operational-safety`;
  no operational config in `security-checklists` beyond `config-misconfig`'s
  scope; each module is a distinct operational failure-mode family): judgmental —
  the adversarial pass plus a `quality-engineer` read (the consumer of the
  library) checking lens-fit.
- **Tool-neutrality**: judgmental — adversarial pass checks for stack-binding.
- **Projection + lint**: goal-based — `make build-self` clean; the three lint
  surfaces exit 0.

## Acceptance Criteria

- [ ] **Skill exists, mirrors the pattern.** `packs/core/.apm/skills/
  operational-safety/SKILL.md` exists with a front-matter `description`, a "How
  it loads (orchestrator-driven, not self-discovered)" section stating the
  orchestrator loads matching modules and inlines them into a reviewer's brief
  (the subagent never self-discovers the skill), and the reliability-vs-security
  carve. It is a depth library, **not** a reviewer prompt.
- [ ] **Six modules, exact names, MECE by failure mode.** `references/` holds
  exactly six files — `state-and-idempotency.md` (convergent re-apply, state
  locking, single-writer), `blast-radius.md` (parse-plan destroy/replace gating,
  `prevent_destroy`, proposer≠approver for destructive ops), `environment-isolation.md`
  (throwaway/staging vs prod, separate state/accounts), `cost-and-teardown.md`
  (cost-ceiling-as-gate, destroy-on-fail, TTL, no orphans), `drift-and-rollback.md`
  (read-only drift detection, known-good re-apply path, and — per ADR-0031 and
  RFC-0041 F1.4 — recording the **auto-remediation default as an unresolved
  tension**: gate-it, per the Terraform community, vs auto-sync, per GitOps; the
  module surfaces the tension, it does not pick a side), and
  `observability-and-smoke.md` (active end-to-end probe — load real URL, assert
  render — access/error-log access, health endpoints, the verify-status signal,
  log-driven debugging). `state-and-idempotency` and `drift-and-rollback` are
  **kept separate** (write-path convergence vs divergence-detection/recovery),
  and observability is its own sixth module.
- [ ] **Each module grounded (greppably) and tool-neutral.** Each module carries
  a `> **Grounded in:**` line near its top naming the RFC-0041 module-table
  groundings it rests on (the relevant F-citations and taxonomy sources — e.g.
  AWS Well-Architected, Google SRE, the Terraform/Pulumi Day-1/Day-2 split),
  mirroring how each `security-checklists` module carries a `> **Standards:**`
  line — so grounding is mechanically checkable (grep), not merely asserted.
  Every module is written tool-neutral; illustrative examples are labelled
  illustrative, never normative.
- [ ] **Routing table in `work-loop` SKILL.md.** `work-loop` SKILL.md gains an
  `operational-safety` boundary→module routing table (mirroring the existing
  `security-checklists` routing table) so the orchestrator loads 1–N matching
  modules on the infra/destructive trigger and inlines them into the
  `quality-engineer` brief — never a flat march of all six.
- [ ] **`quality-engineer` consumer wiring.** `quality-engineer.md` carries a note
  that it consumes orchestrator-inlined `operational-safety` depth (mirroring how
  `security-reviewer` consumes `security-checklists`), without self-discovering
  the skill — `quality-engineer` remains the consumer; **no new reviewer** is
  added (ADR-0023).
- [ ] **Deferred-authority pointer in `config-misconfig`.** `security-checklists`'
  `config-misconfig.md` gains a thin pointer naming the standing authorities —
  **CIS Benchmarks** and each provider's well-architected security guidance (AWS
  Well-Architected Security Pillar; Microsoft Cloud Adoption Framework / Azure
  Well-Architected Security; Google Cloud Architecture Framework Security) —
  **by stable publisher + document name, with no URL and no version**, and noting
  the actual per-provider depth lives in the self-updating scanner.
- [ ] **Carve stated both ways.** The reliability-vs-security carve is stated in
  both `operational-safety` and `security-checklists` (front matter / body): the
  security library owns security config; the operational library owns
  reliability/ops config; the routing splits IaC-security → `config-misconfig`,
  IaC-reliability → `operational-safety`. No security config is duplicated into
  `operational-safety`.
- [ ] **Eval exclusion.** `operational-safety` is excluded from `[pack.evals]` in
  `packs/core/pack.toml`, with a comment naming it as reviewer-internal / never
  self-discovered (mirroring the `security-checklists` exclusion).
- [ ] **No executable mechanism.** The skill ships prose only — no scripts, no
  runtime. `loop-cohort.py` and `lint-spec-status.py` are byte-unchanged.
- [ ] **Projection + lint + release hygiene.** `make build-self` projects the new
  skill to `.claude/skills/operational-safety/` cleanly; `make build-check`,
  `python tools/lint-agent-artifacts.py`, and `python tools/lint-agents-md.py`
  all pass; `packs/core/pack.toml` version is bumped and `marketplace.json`
  reflects it; `docs/product/changelog.md` `[Unreleased]` carries an entry.

## Assumptions

- Technical: `security-checklists` lives at
  `packs/core/.apm/skills/security-checklists/` (SKILL.md + ten `references/*.md`)
  and its SKILL.md already documents the orchestrator-loads-not-self-discovered
  mechanism and the boundary→module routing table in `work-loop` SKILL.md —
  `operational-safety` mirrors this exactly (source: `ls` +
  `security-checklists/SKILL.md` "How it loads").
- Technical: skills are **directory-discovered**, not enumerated in a manifest
  array — adding `operational-safety/` under the pack and running `make
  build-self` projects it; the only manifest touch is the `[pack.evals]`
  exclusion comment and the version bump (which drifts the projected
  `marketplace.json`) (source: `packs/core/pack.toml` `[pack.evals]` comment
  block naming `security-checklists` as excluded; no `skills = [...]` array
  beyond the evals allowlist).
- Technical: `quality-engineer` source is `packs/core/.apm/agents/
  quality-engineer.md`, and its existing lens already carries Observability and
  Reliability checklists — so the `operational-safety` modules supply depth to an
  existing lens, not a new persona (source: read `quality-engineer.md`).
- Technical: `make build-check` does not run build-self, the projection lint, or
  the AGENTS hygiene lint; those run by hand / in CI (source:
  `work-loop-light-mode` spec Assumptions).
- Process: this spec and `infra-aware-work-loop` **both edit `work-loop`
  SKILL.md** — this one adds the `operational-safety` routing table, the other
  edits the verification-mode step + security wiring. Land them sequentially
  (`infra-aware-work-loop` first) or in one PR to avoid a co-edit collision
  (source: the two specs' scopes; RFC-0041 Follow-on artifacts).
- Process: decision frozen in ADR-0031 (Accepted) + RFC-0041 (Accepted
  2026-06-22); the module taxonomy (six, with state/drift kept separate and
  observability sixth) was resolved by the RFC's follow-up research (source:
  `docs/rfc/0041-…` Decision 4 + `0041-notes/research.md` § Follow-up research).
- Product: the library ships in `core` and is consumed by `quality-engineer` for
  every adopter, dormant until the infra/destructive trigger fires (source:
  RFC-0041 Decision 4).
