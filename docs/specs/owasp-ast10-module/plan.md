# Plan: owasp-ast10-module

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

## Tasks

### T1 — Write `agentic-skills.md` reference module

**Depends on:** none
**Verification mode:** goal-based check
**Done when:** file exists at `packs/core/.apm/skills/security-checklists/references/agentic-skills.md`;
`grep -l "AST01\|AST03\|AST04\|AST05\|AST06\|AST07\|AST09\|AST10" packs/core/.apm/skills/security-checklists/references/agentic-skills.md`
returns the file (all eight implementation-check IDs present — authoritative check-count gate);
`grep -q "AST02" packs/core/.apm/skills/security-checklists/references/agentic-skills.md && grep -q "AST08" packs/core/.apm/skills/security-checklists/references/agentic-skills.md`
exits 0 (both header cross-references present);
all four required sections present (`Spec-stage`, `Implementation checks`, `Established-helper bypass`, plus the header block).

Approach: write following `llm-agent.md` structure. Header block includes cross-references
for AST02 (→ `supply-chain.md`) and AST08 (→ three-bucket delegation legend as the
structural mitigation). Eight implementation checks: AST01 (malicious skill content,
`reason`), AST03 (permission over-declaration, `reason`), AST04 (insecure metadata
parsing, `hybrid`), AST05 (external reference pinning, `reason`), AST06 (isolation
declaration, `reason`), AST07 (version drift, `tool`), AST09 (governance gap, `reason`),
AST10 (cross-platform security metadata, `reason`). `Established-helper bypass` names
the *generic kind* of helper (skill-metadata validator, installation-audit trail) — no
repo-specific names; reviewer resolves via AGENTS.md precedence at review time.

---

### T2 — Update `security-checklists/SKILL.md` Module index and frontmatter

**Depends on:** T1
**Verification mode:** goal-based check
**Done when:** `grep "agentic-skills" packs/core/.apm/skills/security-checklists/SKILL.md`
returns the new row; `grep "Agentic Skills" packs/core/.apm/skills/security-checklists/SKILL.md`
returns a match in both the frontmatter `description` and the Module index table.

Approach: (1) update frontmatter `description:` field — the module list changes from
`(..., llm-agent)` to `(..., llm-agent, agentic-skills)`; the standards parenthetical
appends `, OWASP Agentic Skills Top 10 v1.0 (AST01–AST10)` immediately after
`OWASP Top 10 for Agentic Applications:2026` — the two agentic OWASP standards must be
on separate, distinctly-named entries so a reader can't conflate them;
(2) append a new row at the bottom of the Module index table:
`| \`agentic-skills\` | skill-file authoring / modification, skill metadata parsing, skill distribution packaging, skill execution sandbox config | OWASP Agentic Skills Top 10 v1.0 (AST01–AST10) |`

---

### T3 — Author `docs/architecture/security.md` and index it

**Depends on:** T2
**Verification mode:** goal-based check
**Done when:** `docs/architecture/security.md` exists; each framework name present
individually (`for f in "OWASP Top 10:2025" "ASVS 5.0" "API Security Top 10:2023" "LLM Top 10:2025" "Agentic Applications Top 10:2026" "Agentic Skills Top 10 v1.0" "CWE Top 25" "STRIDE" "Proactive Controls 2024"; do grep -q "$f" docs/architecture/security.md || echo "MISSING: $f"; done` produces no MISSING lines);
`docs/architecture/README.md` contains a line pointing to `security.md`.

Approach: write a concise architecture reference doc (docs/architecture style). Sections:
- **Security posture** — one-paragraph overview
- **Enforced frameworks** — table; each row's "driving module(s)" column is sourced from
  the `security-checklists` SKILL Module index (the authoritative enumeration, not the
  security-reviewer agent body); STRIDE+LINDDUN and Proactive Controls rows are annotated
  "always-on open pass / spec-stage, no runtime module"
- **How depth loads** — three-bucket delegation model; Module index as routing authority;
  orchestrator-driven inlining (not self-discovered)
- **Shift-left secure-design review** — spec-stage pass in the work-loop
- **Related decisions** — ADR-0018, RFC-0029

Add one-line index entry to `docs/architecture/README.md` pointing to `security.md`.

---

### T4 — README badge + pack version bump + changelog

**Depends on:** none (parallel with T1–T3)
**Verification mode:** goal-based check
**Done when:** `grep "Agentic Skills" README.md` matches the badge line; `grep "version = \"0.10.0\"" packs/core/pack.toml`
matches; `grep '"0.10.0"' packs/core/.claude-plugin/plugin.json` matches; `grep "Agentic Skills" docs/product/changelog.md`
returns a match.

Approach:
1. **README badge**: insert on the existing badge line (after License badge):
   `[![OWASP Agentic Skills Top 10](https://img.shields.io/badge/OWASP-Agentic%20Skills%20Top%2010%20v1.0-blue)](https://owasp.org/www-project-agentic-skills-top-10/)`
2. **pack.toml**: change `version = "0.9.0"` → `version = "0.10.0"` under the `[pack]`
   table header (line 3), NOT the layout/contract version (`version = "0.12"` on line 29).
3. **plugin.json**: change `"version": "0.9.0"` → `"version": "0.10.0"`.
4. **changelog**: append to the existing `[Unreleased]` `### Added` subsection (do not create
   a new subsection — it already exists): `- **New \`agentic-skills\` module in \`security-checklists\` (core 0.10.0).** Security-reviewer now has control-altitude depth for the OWASP Agentic Skills Top 10 v1.0 (AST01–AST10), covering malicious skill content, permission over-declaration, insecure metadata parsing, external reference pinning, isolation declaration, version drift, governance gaps, and cross-platform security metadata. AST02 defers to the existing \`supply-chain\` module; AST08 is addressed by the three-bucket delegation legend.`
   **Reconcile** the risk-category list in this entry against T1's final module before T5 lands.

---

### T5 — Run `make build-self FORCE=1` and verify projection

**Depends on:** T1, T2, T3, T4
**Verification mode:** goal-based check
**Done when:** `make build-self FORCE=1` exits 0;
`diff packs/core/.apm/skills/security-checklists/references/agentic-skills.md .claude/skills/security-checklists/references/agentic-skills.md`
shows no differences; `diff packs/core/.apm/skills/security-checklists/SKILL.md .claude/skills/security-checklists/SKILL.md` shows no differences.

---

### T6 — Dispatch security-reviewer against full core pack skill surface; fix Blockers

**Depends on:** T5
**Verification mode:** manual QA
**Done when:** security-reviewer dispatched with `agentic-skills.md` module content
inlined; audit covers the full skill surface (SKILL.md bodies, references/*.md, scripts/*.py,
assets/, and any other files under `packs/core/.apm/skills/`); output recorded; all
Blocker findings fixed with gates confirmed green; Concerns routed to apply (only if
mechanical, in-scope, and limited to the agentic-skills boundary) or deferred to
`docs/backlog.md` with one-line rationale; Nits applied if bundled-fixes-carve-out
eligible, otherwise deferred.

Approach: (1) create `## owasp-ast10-module audit deferred findings` heading in
`docs/backlog.md` before any deferral; (2) read `agentic-skills.md` content in full;
(3) build the security-reviewer brief with the module inlined; (4) scope the audit to
all files under `packs/core/.apm/skills/` (SKILL.md, references/*.md, scripts/*.py,
assets/); (5) dispatch security-reviewer subagent; (6) record report; (7) route each
finding per work-loop DECIDE rules — Blockers in PR-touched files (new `agentic-skills.md`
and updated `SKILL.md`) apply/fix; pre-existing Blockers in untouched files defer to
backlog; Concerns assessed against scope constraint; all deferred items go to `docs/backlog.md`
under the heading created in step (1).
