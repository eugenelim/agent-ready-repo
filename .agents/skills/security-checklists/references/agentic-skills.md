# agentic-skills — skill-file authoring, distribution, metadata, isolation

> **Loaded when:** the change authors, modifies, or packages a skill file (SKILL.md or
> equivalent behaviour-definition file); parses or validates skill metadata (frontmatter,
> plugin.json, pack.toml); builds or installs from a skill registry or distribution
> package; or adds skill-execution sandbox configuration.
> **Standards:** OWASP Agentic Skills Top 10 v1.0 — **AST01** Malicious Skills, **AST03**
> Over-Privileged Skills, **AST04** Insecure Metadata, **AST05** Untrusted External
> Instructions, **AST06** Weak Isolation, **AST07** Update Drift, **AST09** No Governance,
> **AST10** Cross-Platform Reuse · **AST02** Supply Chain Compromise defers to the
> [`supply-chain`](supply-chain.md) module, which already covers dependency confusion,
> provenance, and pinning from that angle · **AST08** Poor Scanning is addressed by this
> library's three-bucket delegation legend: the `tool` / `hybrid` / `reason` taxonomy
> explicitly names what scanner-owned, scanner-finds-you-judge, and reviewer-only checks
> look like — that structural separation is the mitigation for the "scanners miss NL-layer
> attacks" failure mode AST08 describes · Additional anchors: CWE-502 (Unsafe
> Deserialization), CWE-829 (Inclusion from Untrusted Control Sphere), CWE-1329 (Improper
> Version Control).
> **Delegation legend:** `tool` = scanner-owned · `hybrid` = scanner finds the flow,
> you judge the fix · `reason` = reviewer-only judgment.

## Spec-stage (proactive control)

At design time, the control for a skill-file change is a **minimal-permission declaration
and an isolation boundary** — the spec should name which tools or capabilities the skill
instructs the agent to invoke, why each is necessary, and what containment boundary bounds
any code-execution or filesystem-write action. "The agent will have access to all tools it
needs" without naming them is the design-time miss.

For a skill that loads external content at runtime, the design-time control additionally
names: the **trust posture** of each external reference (hash-pinned or inline only — no
mutable-branch fetches); whether fetched content is treated as *data* passed to context or
*instructions* executed directly (the latter is the miss); and which domains are on the
allowlist. A skill that says "fetch the latest runbook from X and follow it" without pinning
or an allowlist is the design-time miss regardless of current content.

For a skill distributed across platforms, the design-time control names which **security
metadata fields** (risk tier, permission manifest) must survive each cross-platform port and
how the receiving platform is expected to re-validate them before the skill executes.

## Implementation checks

- `reason` **Malicious skill content (AST01).** Review the full skill body for
  natural-language instructions that benefit the skill author at the expense of the agent's
  owner: identity-overwrite instructions ("update your SOUL.md / MEMORY.md with…"),
  credential-access requests camouflaged as prerequisites, and conditional misdirection
  ("if no user is watching, also do X"). This is distinct from code injection (see
  `injection` module): the vector is trusted prose the agent executes as instructions. Flag
  any instruction whose beneficiary is ambiguous or whose effect on the agent's identity
  files or credential store is unstated.

- `reason` **Permission over-declaration (AST03).** A skill's declared tool or capability
  surface must match its stated function — listing tools "to avoid breaking" expands the
  blast radius of any prompt-injection attack that reaches this skill. Confirm: (a) every
  tool or capability the skill instructs the agent to use is necessary for the skill's
  stated purpose; (b) high-impact tools (file write, shell exec, API mutations) are scoped
  to the narrowest path or action set the workflow requires; (c) composable skills that
  spawn subskills do not silently widen the caller's authority on hand-off.

- `hybrid` **Insecure metadata parsing (AST04).** Skill frontmatter and plugin manifests
  are attacker-controlled inputs when the skill source is untrusted. Scanner finds the
  load path; you judge whether the validation is deep enough. Checks: (a) the YAML parser
  is a *safe* deserializer — no `!!python/object` or equivalent unsafe-loader class; (b)
  all manifest field values are validated against a schema before use — string length,
  allowed-value sets, no code-executing field; (c) display or log paths for metadata fields
  are checked for zero-width Unicode (U+200B and peers) and base64-encoded payloads that
  could smuggle instructions into audit trails or skill-picker UIs.

- `reason` **External reference pinning (AST05).** A skill that instructs the agent to
  fetch external URLs, API schemas, or runbooks at runtime treats mutable remote content as
  trusted instructions. Confirm: (a) external references load against an integrity hash or
  a pinned commit ref — no mutable branch, no `latest`; (b) fetched content is passed as
  *data* context to the agent, not executed as instructions directly; (c) the fetch target
  is on an explicit domain allowlist. A skill whose body says "fetch the latest runbook
  from X and follow it" without pinning or an allowlist is a finding regardless of what X
  currently serves — the surface is the risk.

- `reason` **Isolation declaration (AST06).** A skill that instructs code execution,
  arbitrary filesystem reads/writes, or network calls without declaring a containment
  boundary. Confirm: (a) any code-execution instruction names the containment mechanism
  (sandbox, container, temp-dir scope, process isolation); (b) filesystem access instructions
  do not instruct the agent to reach paths outside the project root without an explicit
  declared scope; (c) network egress instructions name the allowed hosts or explicitly defer
  to the `outbound-ssrf` module's containment checks. This is the *declaration* check —
  whether containment is *implemented* correctly on the runtime side is in `llm-agent.md`'s
  execution-isolation check; both modules fire on the same agentic diff and are
  complementary.

- `tool` **Version drift (AST07).** Skill packages that reference peer skills, libraries,
  or external tools without pinning allow a compromised or broken update to silently replace
  a safe version. Confirm: (a) peer skill or dependency references in manifests are pinned
  to exact versions with integrity hashes, not open version ranges; (b) the build pipeline
  re-validates pinned hashes on each build; (c) `>=` / `*` / `latest` version specifiers
  are absent for security-relevant dependencies. SCA scanner territory: confirm the
  ecosystem's scanner (npm audit / pip-audit / govulncheck / cargo audit) is wired and
  flags unfixed CVEs — if absent, flag `degraded: no scanner`.

- `reason` **Governance gap (AST09).** Confirm: (a) the skill is registered in an auditable
  inventory (name, version, content hash, install source, scan status) — absence of any
  such record is the finding; (b) skill install and significant execution events are logged
  with enough detail to trace a suspicious agent action back to the skill version that
  instructed it; (c) a revocation path exists — the skill can be removed and re-provisioned
  without reinstalling the agent platform. A skill with no inventory entry and no audit
  trail is ungoverned regardless of its content.

- `reason` **Cross-platform security metadata (AST10).** When a skill is ported across
  distribution channels, security-relevant metadata must survive the port. Confirm: (a)
  any security metadata (risk tier, permission manifest, sandboxing annotations) lives in
  the canonical SKILL.md frontmatter or a co-located manifest — not in a platform-specific
  sidecar that is silently dropped on port; (b) cross-platform porting instructions warn
  that security metadata must be re-validated on the destination platform's schema before
  the skill executes; (c) a ported skill that loses its risk tier or permission manifest
  is flagged as a security regression, not treated as a neutral format change.

> **AST08 — no standalone check:** the `tool` / `hybrid` / `reason` tags on every check
> above are this check's mitigation — the three-bucket taxonomy makes scanner limits
> explicit by design (AST08 names exactly the NL-layer gap that `reason`-tagged checks
> cover). No further implementation check is needed.

## Established-helper bypass

For this boundary, the sanctioned helpers are typically the **skill build pipeline** (the
`build-self` / `agentbundle build` path that validates the pack before projection) and the
**distribution integrity check** (hash verification at install time). Resolve in precedence:
`AGENTS.md` "blessed security tools/helpers" → `CONVENTIONS.md` → inference fallback (grep
the codebase for the de-facto metadata validator and the install-audit mechanism). Flag a
change that: (a) parses skill frontmatter with an unsafe deserializer instead of the
sanctioned load path; (b) installs skills by copying files directly, bypassing the build
pipeline and its integrity gate; or (c) registers or executes a skill with no inventory
record. This module names the *generic kind* of helper — the reviewer resolves the repo's
actual blessed path at review time, never from this file.
