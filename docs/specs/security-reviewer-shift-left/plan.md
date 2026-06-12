# Plan: security-reviewer-shift-left

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is **content + wiring**, not executable code: a new skill of prose
modules, edits to one agent prompt, edits to one skill's orchestration prose, a
light `AGENTS.md` customization point, and a CONVENTIONS touch. All of it lives in
`packs/core/` and projects via `make build-self`.

Order of operations: author the **skill modules first** (T1) so the agent-body trim
(T2) has somewhere to move the shape-specific depth without a coverage gap; then
wire the **work-loop** (T3) to load those modules and to dispatch the spec-stage
mode; the **AGENTS.md** customization point (T4) is independent and can run in
parallel; the **CONVENTIONS touch** (T5) lands *after* the wiring it describes so it
is never a forward-claim; finally a **projection + governance gate** (T6) bumps the
pack version, proves zero `build-self` drift, and asserts the no-contract-change and
adopter-clean invariants.

The riskiest part is the **agent-body trim (T2)**: removing the deep per-domain
checklists must not lose coverage the modules don't yet carry — so T1 lands first
and T2's verification greps confirm the universal method remains and the deep lists
are gone. The second risk is **work-loop wiring fidelity (T3)** — the new firing is
net-new, and must not perturb the byte-identical risk-trigger block.

## Constraints

- **RFC-0029** (Accepted) — the proposal; D1–D6 are the decision set this plan
  implements.
- **ADR-0018** (Accepted) — records the decision and its boundaries.
- **ADR-0017** — the scanner gate; the "complements, does not replace scanners"
  framing and the three-bucket `tool` delegation must keep faith with it.
- **ADR-0014 / RFC-0025** — the security-boundary risk trigger T3 reuses; its
  wording is byte-identical across four files and must not be disturbed.
- **`AGENTS.local.md`** — non-cosmetic pack updates bump the pack version (T6).
- **Self-host projection** — `docs/CONVENTIONS.md` is projected from
  `packs/core/seeds/docs/CONVENTIONS.md`; root `AGENTS.md` is Manual
  (`EXCLUDED_PATTERNS`, edit directly + sync seed). Edit sources, then
  `make build-self`.

## Construction tests

Most construction tests live under **Tasks** below. Cross-cutting (span tasks):

**Integration tests:**
- **No-contract-change assertion** — `docs/contracts/adapter.toml` (and `_data/`
  twin) `version` unchanged vs `origin/main`; `skill` projection mode stays
  `direct-directory` for every adapter. (AC10)
- **No-new-dir / no-new-dependency assertion** — vs `origin/main`, no new
  top-level directory and no new runtime dependency in any shipped package. (AC13)
- **Projection drift gate** — `make build-self` then `git status` clean (no
  unexpected reverts); the new skill projects into `.claude/skills/` and the other
  adapter trees. (AC11)
- **Adopter-clean grep** — no repo-specific helper name (`write_jailed`,
  `credbroker`, `sso-broker`) appears anywhere under the shipped
  `security-checklists` skill. (AC9)

**Manual verification:**
- On a sample outbound-HTTP (SSRF-shaped) diff, walk the work-loop security-review
  step and confirm **only** `outbound-ssrf` (plus any genuinely-crossed boundary) is
  inlined into the subagent brief — not all ten modules. Record in the PR. (AC5
  behavior)

## Design (LLD)

Shape: **mixed** — but the work is prose artifacts, so most LLD sub-sections are
N/A. Only the two that carry real decisions are kept; the rest are pruned.

### Design decisions
- **Universal-in-body / depth-in-skill split** (RFC D1 refinement). The agent body
  keeps the *method* (delegation rule, load-context-first, STRIDE+LINDDUN open pass,
  established-helper-bypass meta-check, severity rubric, honest-limits footer, output
  format); the ten boundary modules carry the *deep per-domain checklists*. Rejected
  alternative: inline everything (bloats the prompt, dilutes findings). Traces to:
  AC1, AC3.
- **Orchestrator-driven loading, not subagent self-discovery.** The work-loop
  detects crossed boundaries and inlines the matching modules' content into the
  brief. Rejected alternative: subagent loads the skill itself (model-invoked,
  adapter-variable, and the agent's `tools:` excludes a Skill tool). Traces to: AC4,
  AC5.
- **Convention awareness on existing surfaces** (RFC D5). `AGENTS.md` light
  customization point + retained `security.md` reads + inference fallback; no new
  mandatory standard file. Traces to: AC8(repo-convention).

### Component / module decomposition
- **New:** `packs/core/.apm/skills/security-checklists/` (`SKILL.md` + ten
  `references/<module>.md`). Reused projection: `direct-directory` (no new mode).
- **Edited:** `packs/core/.apm/agents/security-reviewer.md` (add spec-stage mode;
  trim deep checklists; add three-bucket rule + 2025 awareness anchor);
  `packs/core/.apm/skills/work-loop/SKILL.md` (pre-EXECUTE dispatch + module-inlining
  + routing table); `AGENTS.md` + `packs/core/seeds/AGENTS.md` (blessed-helpers
  point); `packs/core/seeds/docs/CONVENTIONS.md` *or* `work-loop/SKILL.md` (the
  CONVENTIONS touch — home decided in T5).

### Dependencies & integration
- No new runtime dependency; no new top-level directory. The only cross-artifact
  coupling is the boundary→module routing table (work-loop) referencing the module
  filenames (skill) — verified by T3's grep that every routed module name resolves
  to a real file.

## Tasks

### T1: Author the `security-checklists` skill (SKILL.md + 10 modules)

**Depends on:** none
**Touches:** packs/core/.apm/skills/security-checklists/**

**Tests:**
- Goal-based: the directory contains `SKILL.md` and exactly the ten
  `references/<module>.md` files named in AC1; `grep` confirms each module header
  names a standard+version and each check carries a `tool` / `hybrid` / `reason`
  tag.
- Goal-based (adopter-clean): `grep -ri 'write_jailed\|credbroker\|sso-broker'` over
  the skill returns nothing.

**Approach:**
- Scaffold the skill with frontmatter describing it as orchestrator-loaded
  progressive-disclosure security depth (note in the body that loading is
  orchestrator-driven; auto-discovery is a redundant convenience).
- Write the ten modules anchored on the RFC's OWASP-2025 + cross-cutting table,
  each: standard+version header, a focused ~per-domain checklist, and per-check
  `tool`/`hybrid`/`reason` tags with the language-agnostic scanner names.
- Carry the established-helper-bypass *mechanism* generically (no repo specifics).

**Done when:** the presence/shape greps pass and the adopter-clean grep is empty.

### T2: Add the spec-stage mode + trim the agent body to the universal method

**Depends on:** T1
**Touches:** packs/core/.apm/agents/security-reviewer.md

**Tests:**
- Goal-based: `grep` confirms `security-reviewer.md` cites **OWASP Top 10:2025** and
  no longer anchors on **2021**; a spec-stage / secure-design mode heading exists;
  the three-bucket delegation rule, the always-on STRIDE+LINDDUN pass, and the
  established-helper-bypass meta-check are present.
- Goal-based: the deep per-domain numbered web/LLM checklists are **removed** from
  the body (the depth now lives in the skill) — assert the long enumerated lists are
  gone while the universal method remains.
- Goal-based (AC7 core): `grep` the body for the language-agnostic scanner-detection
  list (`npm audit` / `pip-audit` / `govulncheck` / `cargo audit` / Snyk / Semgrep /
  CodeQL) **and** the tool-absence behavior tokens (`degraded: no scanner` / an
  explicit-gap statement) — not just that the three-bucket rule is *named*.
- Goal-based (AC8b regression): `grep` confirms the trimmed `security-reviewer.md`
  **still names both** conditional read paths `docs/architecture/security.md` and
  `docs/guides/reference/security.md` — the body trim must not drop the existing
  `load context` reads (agent-prose grep; the files need not exist).

**Approach:**
- Add a spec-stage secure-design mode section mirroring `adversarial-reviewer`'s
  spec-stage structure: read the *spec*, ask per-boundary whether the control is an
  AC at the right depth (confinement not traversal; scheme allowlist not "validate
  the URL"; broker-mediated secrets).
- Replace the 2021 web Top 10 + LLM enumerations with the universal method + a
  pointer that the orchestrator inlines the boundary-scoped modules.
- Add the three-bucket delegation rule (detect ecosystem scanner; Tier-1
  declare/detect/fail-clean tool-absence behavior).

**Done when:** the greps pass — the deep per-domain checklists are **gone** from
the body (moved to the skill) and the universal method remains. Note: the file is
not strictly shorter overall, because AC2's spec-stage mode, AC7's three-bucket
rule, the established-helper meta-check, and the LINDDUN pass are **net-new required
capability** the old body didn't carry; the *per-domain depth* is what was trimmed,
not the total line count.

### T3: Wire the work-loop — spec-stage dispatch + module-inlining + routing table

**Depends on:** T1, T2
**Touches:** packs/core/.apm/skills/work-loop/SKILL.md

**Tests:**
- Goal-based: `grep` confirms the pre-EXECUTE review step names `security-reviewer`
  on the **security-boundary trigger**, described as **net-new** wiring (not a reuse
  of the existing adversarial-only firing).
- Goal-based: the security-review step instructs loading the boundary-matching
  `security-checklists` modules and **inlining their content** into the brief; a
  deterministic boundary→module routing table is present and every module name in it
  resolves to a real file from T1.
- Goal-based (regression): the byte-identical risk-trigger block is unchanged
  (`git diff` shows no edit inside the `risk-triggers:start/end` markers).

**Approach:**
- Extend the PLAN-step pre-EXECUTE review to also dispatch the `security-reviewer`
  spec-stage mode when the security-boundary trigger is present, naming it net-new.
- Add the orchestrator module-loading + inlining instruction to the REVIEW-step
  security-reviewer dispatch, plus the boundary→module routing table.

**Done when:** the greps pass and the risk-trigger block is provably untouched.

### T4: `AGENTS.md` blessed-security-helpers customization point (D5)

**Depends on:** none
**Touches:** AGENTS.md, packs/core/seeds/AGENTS.md

**Tests:**
- Goal-based: `grep` confirms a light "blessed security tools/helpers" point exists
  in `AGENTS.md`; growth is ≤ ~4 lines (a sub-bullet on the existing
  `security-reviewer` entry, not a new section — root is already ~202 lines, so the
  "~200" budget is treated as approximate); root `AGENTS.md` and its seed in sync.

**Approach:**
- Add a short list + inference-fallback note (RFC Open Q2 default) as a minimal
  sub-bullet under the existing `security-reviewer` line in **Specialist subagents**;
  do not introduce a `security.md` standard file, do not add a new section.
- Edit root `AGENTS.md` directly (Manual / `EXCLUDED_PATTERNS`) and sync the seed
  byte-for-byte (the two files differ only by the trailing `AGENTS.local.md` line).

**Done when:** the grep passes, growth is ≤ ~4 lines, and root/seed match.

### T5: CONVENTIONS touch — spec-stage security review (lands with the wiring)

**Depends on:** T3
**Touches:** packs/core/.apm/skills/work-loop/SKILL.md

**Home decided (pre-EXECUTE):** the **`work-loop` skill**, not `docs/CONVENTIONS.md`.
ADR-0018 § Consequences left the choice to this spec; the work-loop skill is the
canonical "how" and this is consistent with the ongoing migration of mode mechanics
out of `CONVENTIONS.md`. Because the note lives in the same file T3 edits, it ships
atomically with the wiring by construction — the forward-claim risk is structurally
eliminated, not just sequenced.

**Tests:**
- Goal-based: `grep` the landed note in `work-loop/SKILL.md` describing that security
  review runs at spec stage on security-boundary work; it is in the same file as T3,
  so no separate atomicity check is needed.

**Approach:**
- Write the light note mirroring the existing adversarial spec-stage entry, folded
  into the T3 pre-EXECUTE-review edit (one coherent paragraph, not a duplicate
  section).

**Done when:** the note exists in `work-loop/SKILL.md` alongside the T3 wiring.

### T6: Projection + governance gate (version bump, drift, no-contract-change)

**Depends on:** T1, T2, T3, T4, T5
**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, (generated projections)

**Tests:**
- Goal-based: `docs/contracts/adapter.toml` + `_data/` twin `version` unchanged vs
  `origin/main`; `skill` stays `direct-directory`.
- Goal-based: bump core pack version (pack.toml + plugin.json), run `make
  build-self`, then `git status` is clean — the new skill + edits project with no
  drift and no unexpected reverts.
- Goal-based: re-run the cross-cutting adopter-clean grep over the **projected**
  skill trees (not just the source).
- Goal-based (AC13): assert against `origin/main` that no new top-level directory
  and no new runtime dependency in any shipped package were introduced.

**Approach:**
- Bump the core pack version (non-cosmetic content change).
- Add a `docs/product/changelog.md` `[Unreleased]` entry for the strengthened
  security reviewer (AC14 — user-visible skill/agent prose change per `CONVENTIONS.md`).
- Run `make build-self`; resolve any drift; verify projections landed across adapter
  trees.

**Done when:** contract version unchanged, `make build-self` drift-clean, pack
version bumped, changelog `[Unreleased]` entry present, projected adopter-clean grep
empty.

## Rollout

Pure content/wiring change inside `packs/core/`, shipped in one PR. No infra, no
data migration, no external-system dependency. **Reversible** — revert the PR; the
only "irreversible" surface is the pack version bump, which is monotonic by design.
Deployment sequencing within the PR is the task order above (T1 → T2 → T3, T4 in
parallel, T5 after T3, T6 last). No flag — the strengthened reviewer is the new
default the moment the skill + wiring project.

## Risks

- **Coverage regression on the agent-body trim (T2).** Removing the deep checklists
  could drop a class the modules don't yet carry. Mitigation: T1 lands first; T2's
  greps assert the universal method remains and the modules cover the trimmed
  domains.
- **Perturbing the byte-identical risk-trigger block (T3).** Mitigation: T3's
  regression grep asserts no edit inside the `risk-triggers` markers.
- **CONVENTIONS forward-claim (T5).** Mitigation: T5 depends on T3 and lands in the
  same PR, so doctrine never describes unbuilt wiring.
- **Module granularity churn (RFC Open Q1).** Shipping 10 risks two that always
  co-fire. Mitigation: ship 10, collapse only on observed redundancy (Ask-first
  boundary), so it's a cheap later edit, not a re-do.

## Changelog

- 2026-06-12: initial plan (RFC-0029 follow-on; D1–D6 → T1–T6).
- 2026-06-12: shipped — T1–T6 landed, `make build-check` green (incl. SAST gate),
  adversarial-reviewer and quality-engineer (whole-spec coverage) both returned
  `Clean`; security-reviewer not run (the diff changes no security-boundary code,
  only skill/agent prose, docs, and version bumps). Spec Status→Shipped, all 14 ACs
  checked. README + AGENTS.md lens refresh + quality-engineer README line rode along
  per the user's explicit request (the latter documents already-shipped #285).
- 2026-06-12: pre-EXECUTE adversarial review — resolved the T5 CONVENTIONS-home fork
  to the `work-loop` skill (folds into T3); sharpened AC1 (pin concrete versions) and
  AC8 (three explicit clauses; agent-prose grep for the conditional `security.md`
  reads); added AC14 (changelog `[Unreleased]` entry); made the AGENTS.md budget
  assertion concrete (≤ ~4 lines, ~200 treated as approximate); corrected the stale
  `0.2.0`→`0.3.0` pack-version assumption.
