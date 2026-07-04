# Spec: owasp-ast10-module

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0029 (the `security-checklists` skill and its Module index this extends); ADR-0018 (shift-security-review-left progressive-disclosure decision); the Shipped `llm-agent-agentic-boundary-extension` spec (whose Module index pattern this follows)
- **Contract:** none — pure-markdown skill reference content; no API/event/RPC surface
- **Shape:** additive — new `agentic-skills` reference module in `core`'s `security-checklists` skill + Module index update + security architecture doc authoring + README badge update; no application LLD

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A `security-reviewer` reasoning about a skill-layer change — an authored SKILL.md, a
skill distribution package, or a skill-metadata parser — gets **control-altitude depth**
for the **OWASP Agentic Skills Top 10 v1.0 (AST01–AST10)** from a new `agentic-skills`
module in `security-checklists`, instead of having no skill-layer-specific checks at all.
The OWASP Agentic Skills Top 10 covers risks that are distinct from both the LLM Top 10
(runtime model behaviour) and the Agentic Applications Top 10 (orchestration architecture):
it treats skill files themselves as an attack surface — a vector for malicious NL
instructions, supply-chain compromise, metadata deception, and governance gaps.

Additionally, a `docs/architecture/security.md` document is created that comprehensively
documents all security frameworks and practices enforced in this repo, giving it an honest
and verifiable security posture suitable for adopters to reference.

## Mode

Mode: full — security boundary (adding a security enforcement framework) + structural
change (new module in security-checklists, new architecture doc)

## Boundaries

### Always do

- Follow the established module format exactly: header block (`Loaded when`, `Standards`,
  `Delegation legend`), `## Spec-stage (proactive control)`, `## Implementation checks`,
  `## Established-helper bypass` — in that order, matching `llm-agent.md` style.
- Tag every implementation check with exactly one delegation bucket (`tool`, `hybrid`, or
  `reason`) per the three-bucket legend.
- For AST08 (Poor Scanning): state in the module header the specific delegation-legend
  mechanism that covers it (the `tool`/`hybrid`/`reason` taxonomy explicitly names what
  scanners can and cannot detect — that structural separation IS the AST08 mitigation),
  so the coverage claim is verifiable. No separate implementation check is needed.
- For AST02 (Supply Chain Compromise): state in the module header that this risk defers
  to the existing `supply-chain.md` module, which already covers dependency confusion,
  provenance, and pinning. Cross-reference is the fix, not a redundant check.
- The `Established-helper bypass` section must follow the established-helper mechanism:
  name the **generic kind** of helper this boundary usually has (skill-metadata validator,
  installation-audit trail), not any repo-specific tool names. The module stays portable;
  the reviewer resolves the repo's actual helper at review time via AGENTS.md precedence.
- Wire the new module row into the Module index in `security-checklists/SKILL.md` with a
  boundary trigger and a primary anchor that names the standard.
- Update `security-checklists/SKILL.md` frontmatter to name OWASP Agentic Skills Top 10 v1.0.
- Keep the existing module shape of `llm-agent.md` intact.
- Bump `core` pack to `0.10.0` in `pack.toml` (`[pack]` table's `version` key only, not
  the layout/contract version on line 29) and `.claude-plugin/plugin.json` in lockstep.
- Run `make build-self FORCE=1` and confirm `.claude/skills/security-checklists/references/agentic-skills.md`
  matches source.
- Run the security-reviewer with the `agentic-skills.md` module content inlined against
  the core pack's skill files; record the output. Fix Blockers in-PR. Apply only Concerns
  that are mechanical, in-scope, and limited to the `agentic-skills` boundary — all
  other Concerns defer to `docs/backlog.md`.
- Add the OWASP Agentic Skills Top 10 badge to the README badge line as:
  `[![OWASP Agentic Skills Top 10](https://img.shields.io/badge/OWASP-Agentic%20Skills%20Top%2010%20v1.0-blue)](https://owasp.org/www-project-agentic-skills-top-10/)`
- Add index entry for `docs/architecture/security.md` in `docs/architecture/README.md`.

### Ask first

- Adding any new skill to `security-checklists` beyond the `agentic-skills` module.
- Changing the Module index boundary trigger for any existing module.
- Adding enforcement (CI gates, linters) based on AST compliance — this spec covers
  the reference module only, not automated enforcement.

### Never do

- Edit `.claude/skills/security-checklists/` directly (projected; source is `packs/core/.apm/skills/security-checklists/`).
- Cite unverified "real-world evidence" from the OWASP AST10 project as confirmed incidents —
  several named incidents (ClawHavoc, ClawHub, ClawJacked/CVE-2026-28363) reference a
  non-existent "OpenClaw" platform. Reference the framework by name and standard number only.
- Merge AST01–AST10 checks into `llm-agent.md` — the boundaries are distinct (see Verified
  assumption below).

## Acceptance Criteria

- [x] Source file `packs/core/.apm/skills/security-checklists/references/agentic-skills.md`
  exists with eight implementation checks covering AST01, AST03, AST04, AST05, AST06,
  AST07, AST09, AST10; the module header cross-references `supply-chain.md` for AST02
  and states the delegation-legend coverage for AST08
- [x] Each implementation check tagged `tool`, `hybrid`, or `reason` with a one-line description
- [x] `Spec-stage (proactive control)` section names the skill-layer design-time controls:
  minimal-permission declaration, isolation boundary, external reference pinning, and
  distribution trust / security-metadata survival on port
- [x] `Established-helper bypass` section names the **generic kind** of helper (skill-metadata
  validator and installation-audit trail), not repo-specific tool names
- [x] Module index row added in `packs/core/.apm/skills/security-checklists/SKILL.md` with
  boundary: "skill-file authoring / modification, skill metadata parsing, skill distribution
  packaging, skill execution sandbox config" and primary anchor "OWASP Agentic Skills Top 10 v1.0"
- [x] `security-checklists/SKILL.md` frontmatter `description` is updated to the exact text:
  module list adds `agentic-skills` after `llm-agent`; standards parenthetical adds
  `OWASP Agentic Skills Top 10 v1.0 (AST01–AST10)` after the existing
  `OWASP Top 10 for Agentic Applications:2026` entry — distinct names, no conflation
- [x] `make build-self FORCE=1` exits 0; `diff` of source vs projected `agentic-skills.md`
  shows no differences
- [x] `docs/architecture/security.md` created, covering: all enforced frameworks — OWASP
  Top 10:2025, ASVS 5.0, API Security Top 10:2023, OWASP LLM Top 10:2025, OWASP Agentic
  Applications Top 10:2026, OWASP Agentic Skills Top 10 v1.0, CWE Top 25, STRIDE + LINDDUN,
  Proactive Controls 2024 — where each framework table row notes either its driving module(s)
  or "always-on open pass / spec-stage, no runtime module" for STRIDE+LINDDUN and Proactive
  Controls; the three-bucket delegation model; the Module index routing approach; and the
  shift-left secure-design review pass
- [x] `docs/architecture/README.md` contains an index entry pointing to `security.md`
- [x] `README.md` badge line includes the pinned OWASP Agentic Skills Top 10 badge
- [x] Security-reviewer dispatched against the **full core pack skill surface** with new
  module inlined — covering all components of each skill: `SKILL.md` bodies, `references/*.md`,
  `scripts/*.py`, `assets/`, and any other files under `packs/core/.apm/skills/`; output
  recorded; Blocker-severity findings **in files this PR adds or touches** (the new
  `agentic-skills.md` and the updated `security-checklists/SKILL.md`) are fixed;
  pre-existing Blockers in untouched files are recorded and deferred to `docs/backlog.md`;
  Concerns either applied (mechanical, in-scope, agentic-skills boundary only) or deferred
  to `docs/backlog.md` with one-line rationale; a `## owasp-ast10-module audit deferred findings`
  heading is created in `docs/backlog.md` before any deferral is written into it
- [x] `packs/core/pack.toml` `[pack]` table version → `0.10.0`
- [x] `packs/core/.claude-plugin/plugin.json` version → `0.10.0`
- [x] `docs/product/changelog.md` existing `[Unreleased]` `### Added` subsection has an
  entry appended for the new module (the subsection already exists; do not create a duplicate)

## Assumptions

- **Verified:** the OWASP Agentic Skills Top 10 v1.0 project is a real OWASP project;
  main page `https://owasp.org/www-project-agentic-skills-top-10/` resolves (confirmed by
  evidence-retriever fetch); the framework is legitimate even though some illustrative
  "evidence" in its documentation references fictional platforms. The badge link target
  `https://owasp.org/www-project-agentic-skills-top-10/` is the same verified URL and
  will not produce a 404.
- **Verified:** `make build-self FORCE=1` is the correct projection command (from Makefile).
- **Verified:** `packs/core/pack.toml` current `[pack]` version is `0.9.0`;
  `packs/core/.claude-plugin/plugin.json` current version is `0.9.0`.
- **Verified:** `agentic-skills` boundary is orthogonal to `llm-agent`. `llm-agent.md`
  fires on "prompts, model/tool exposure, MCP, model-output handling, agentic action" —
  the runtime model behaviour surface. `agentic-skills` fires on the skill *artifact* as
  an attack surface: skill file authoring, metadata parsing, distribution packaging, and
  sandbox config. The boundaries do not overlap: a plain LLM call crosses `llm-agent`; a
  SKILL.md being authored or installed crosses `agentic-skills`. An agentic system that
  both runs models AND ships skill files crosses both — that is the intended multi-module
  loading behaviour.

## Testing Strategy

**Goal-based check** for the module file: `grep` for the eight AST IDs (AST01, AST03,
AST04, AST05, AST06, AST07, AST09, AST10); confirm four required sections are present;
confirm `make build-self FORCE=1` exits 0 and `diff` shows no drift.

**Manual QA** for the security audit: dispatch security-reviewer with new module inlined;
record output; verify each finding is routed to apply/defer. The observed report is the
deliverable — correctness is whether every finding has an explicit resolution.

No unit test file — pure markdown skill reference content.
