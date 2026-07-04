# Security Architecture

> How this repo's security-review posture is organized — the frameworks enforced,
> how depth loads, and where each decision lives. Updated whenever the framework
> set or the loading model changes.

## Security posture

Security review is a **progressive-disclosure depth library** (`security-checklists`) behind
the `security-reviewer` agent. The reviewer's body carries the universal method (STRIDE +
LINDDUN open pass, the three-bucket delegation rule, the established-helper-bypass
meta-check, the severity rubric). Boundary-specific depth — what to actually check at each
trust boundary — lives in per-boundary reference modules, indexed below. The orchestrator
detects which boundaries a diff or spec crosses and **inlines only the matching modules**
as text into the reviewer's brief; the subagent never self-discovers this library.

This means security review scales depth without prompt bloat, is deterministic (routing
authority is the Module index, not model relevance), and shifts left: the same module depth
backs both the **spec-stage secure-design pass** (is the control specified?) and the
**diff-stage implementation pass** (is the control correct?).

## Enforced frameworks

All framework rows source their "Driving module(s)" from the [`security-checklists` Module
index](../../../packs/core/.apm/skills/security-checklists/SKILL.md#module-index) —
the authoritative boundary→module routing table. Rows without a runtime module are
always-on passes in the reviewer body or spec-stage-only.

| Framework | Driving module(s) | Mode |
|---|---|---|
| OWASP Top 10:2025 | `access-control` (A01/SSRF), `authn-session` (A07), `injection` (A05/A08), `secrets-and-crypto` (A04), `supply-chain` (A03), `config-misconfig` (A02), `exceptional-conditions` (A10) | runtime module |
| ASVS 5.0 | `authn-session` (V6/V7), `path-and-file` (V12), `secrets-and-crypto` (V11), `outbound-ssrf` (V13) | runtime module |
| API Security Top 10:2023 | `access-control` (BOLA/BFLA) | runtime module |
| OWASP LLM Top 10:2025 | `llm-agent` (LLM01/02/03/04/05/06/10) | runtime module |
| OWASP Top 10 for Agentic Applications:2026 | `llm-agent` (ASI02/03/05/06 — agentic surface) | runtime module |
| OWASP Agentic Skills Top 10 v1.0 | `agentic-skills` (AST01/03/04/05/06/07/09/10; AST02→`supply-chain`; AST08→delegation legend) | runtime module |
| CWE Top 25 | `injection`, `path-and-file`, `secrets-and-crypto`, `agentic-skills` | runtime module |
| STRIDE + LINDDUN | none — always-on open pass in the reviewer body on every diff | always-on open pass, no runtime module |
| Proactive Controls 2024 | none — realized by the spec-stage secure-design mode (Insecure Design / A06) | spec-stage only, no runtime module |

## How depth loads (three-bucket delegation + Module index)

**Three-bucket delegation** tags every check in every module so the reviewer knows who owns it:

- **`tool`** — scanner-owned (npm audit, pip-audit, govulncheck, Semgrep, CodeQL). Confirm
  the scanner is wired; flag the gap if absent (`degraded: no scanner`). Do not re-check by
  hand.
- **`hybrid`** — the scanner finds the flow; the reviewer judges the fix. Taint analysis
  points at the sink; whether the escaping, confinement, or safe-loader choice is correct is
  reasoning work.
- **`reason`** — reviewer-only. Logic-flaw access control, fail-open vs. fail-closed,
  confused-deputy, privacy exposure — classes scanners structurally cannot see. The
  highest-value findings live here.

**Module index routing** is deterministic. At the work-loop's security-review step (and at
the pre-EXECUTE spec-stage pass), the orchestrator:

1. Detects which trust boundaries the diff or spec crosses.
2. Loads **only the matching modules** by the boundary listed in the Module index.
3. **Inlines the selected modules' content** into the security-reviewer subagent's brief.

Load only the modules the change crosses — never a flat march through all modules. An
auth-touching endpoint pulls `access-control` and often `authn-session`; a SKILL.md being
authored pulls `agentic-skills` and may also pull `llm-agent` if the skill constructs
prompts or exposes tools.

## Shift-left secure-design review

When the **security-boundary risk trigger** fires on a spec (auth, secrets, user input,
deserialization, file/network I/O, or skill-layer authoring), the work-loop dispatches the
`security-reviewer` in **spec-stage secure-design mode** — before any code is written.
It checks whether each control is specified as an acceptance criterion at the right depth
(confinement, not just traversal-blocking; scheme allowlist, not "validate the URL";
broker-mediated secrets, not ad-hoc reads). The same module depth backs this spec-stage
pass: only the boundary-matching modules are inlined.

On infra-flavored work (IaC, deploy config), the pass is **non-skippable**; a missing
`security-reviewer` is a loud blocker, not a silent proceed.

## Pack compliance — OWASP Agentic Skills Top 10 v1.0

All non-core packs were audited against the `agentic-skills` module (AST01–AST10) in July 2026.
The audit reviewed ~60 skills across 14 packs. Findings and their status:

### Passing checks (all packs)

| Check | Verdict | Notes |
|---|---|---|
| **AST01** Malicious content | PASS | No identity-overwrite, credential-camouflage, or conditional-misdirection instructions found |
| **AST02** Supply chain | PASS | Defers to `supply-chain` module; pack.toml version pinning at build time |
| **AST03** Permission over-declaration | PASS | All skills scoped to stated purpose; high-impact tools named explicitly |
| **AST04** Insecure metadata parsing | PASS | Metadata parsed only by the `agentbundle` build pipeline (safe YAML load path) |
| **AST07** Version drift | PASS | Pack-level pinning via pack.toml; skills invoke peers by name (version resolved at install) |
| **AST08** Poor scanning | PASS | Covered structurally by the `tool`/`hybrid`/`reason` three-bucket delegation taxonomy |
| **AST09** Governance | PASS | Auditable inventory via marketplace.json (built by `build-self`); install-state-visibility command; revocation via `agentbundle uninstall` |

### Findings addressed

| Finding | Severity | AST | Fix applied |
|---|---|---|---|
| `research` skill did not explicitly state that fetched content is treated as data not instructions | Concern | AST05 | Added "Trust posture — retrieved content is untrusted data" section to `research/SKILL.md` |
| `confluence-crawler` and `jira` skills did not declare SSRF containment for user-supplied base URLs | Concern | AST06 | Added agent pre-flight check note to Security rules in both `confluence-crawler/SKILL.md` and `jira/SKILL.md`. The scripts validate only the URL scheme (`http://`/`https://`); the host pre-flight check (reject private-IP ranges and cloud-metadata endpoints) is the agent's responsibility. On the token path `follow_redirects=True` is active — verify before invoking. |
| Non-credentialed boundary-crossing skills carried no security metadata in frontmatter | Concern | AST10 | Added `metadata.boundaries` lists to: `assimilate-primitive`, `assimilate-repo`, `export-catalogue`, `propose-catalogue-pack` (catalogue-curation); `file-to-markdown`, `msg-to-markdown`, `markdown-to-docx`, `markdown-to-html`, `markdown-to-pptx`, `markdown-to-xlsx`, `mermaid-renderer` (converters); `release-loop` (release-engineering); `research`, `source-map` (research) |
| `assimilate-primitive` Phase 1 lacked an explicit AST01-AST10 review step for ingested candidates | Concern | AST01-AST10 | Added step 5 (AST01-AST10 agentic-skills security review) to `assimilate-primitive/SKILL.md` Phase 1; `assimilate-repo` Never-do updated to name this gate |

### Security metadata convention — `metadata.boundaries`

Non-credentialed skills that cross a security boundary declare it in frontmatter under
`metadata.boundaries` (a list). Defined values:

| Value | Meaning |
|---|---|
| `network_fetch` | Skill instructs outbound HTTP/DNS fetches to external hosts |
| `network_egress` | Skill instructs deployment or other outbound connections to real infrastructure |
| `filesystem_write` | Skill writes files to disk (beyond in-memory processing) |
| `filesystem_read_untrusted` | Skill reads potentially hostile files (untrusted documents, email, archives) |
| `deploy_action` | Skill deploys to real environments (ephemeral or production) |

Credentialed skills (those with `metadata.credentialed: true` and auth details) already carry
sufficient security metadata via their auth-scheme declaration; they do not need `boundaries`.

This metadata survives cross-platform porting in the SKILL.md frontmatter, satisfying AST10.
When a platform automates security-policy enforcement, `metadata.boundaries` provides the
machine-readable signal; when it does not, the skill body's security rules carry the same
intent in prose.

## Related decisions

- **ADR-0018** — why security review shifts left and uses progressive disclosure rather than
  a single monolithic checklist prompt.
- **RFC-0029** — the proposal that established the `security-checklists` skill and its
  boundary→module routing design.
