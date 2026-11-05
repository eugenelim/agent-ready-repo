# Security architecture

Security in this repository is enforced in five layers: a routed review library
(`security-checklists`) behind the `security-reviewer` agent; a spec-stage
secure-design pass before code exists; declared skill boundaries
(`metadata.boundaries`); an admissibility gate on directly installed skills; and
scanner gates (Bandit, pip-audit, Semgrep, npm audit, CodeQL, gitleaks,
actionlint, zizmor). Two further controls are contracts on the reading agent, not
gates: untrusted inbound text is data, and a stored work-item command carries
disclosed residual risk. Credentials are covered in
[`credentials.md`](credentials.md), and runtime confinement in
[`runtime-security-primitives.md`](runtime-security-primitives.md).

## 1. Review depth loads by trust boundary, not by framework

The `security-reviewer` body carries the method: a STRIDE and LINDDUN open pass,
the three-bucket delegation rule, the established-helper-bypass meta-check, and
the severity rubric. Boundary-specific depth lives in per-boundary modules. The
orchestrator detects the boundaries a diff or spec crosses and inlines only the
matching modules into the reviewer's brief; the subagent never discovers the
library itself.[^s1]

Routing authority is the Module index in `security-checklists/SKILL.md`, so
depth scales without prompt bloat, routing is deterministic, and the same module
text backs the spec-stage pass and the diff-stage pass.

| Framework | Driving module(s) | Mode |
| --- | --- | --- |
| OWASP Top 10:2025 | `access-control` (A01, SSRF), `authn-session` (A07), `injection` (A05, A08), `secrets-and-crypto` (A04), `supply-chain` (A03), `config-misconfig` (A02), `exceptional-conditions` (A10) | runtime module |
| ASVS 5.0 | `authn-session` (V6, V7), `path-and-file` (V12), `secrets-and-crypto` (V11), `outbound-ssrf` (V13) | runtime module |
| API Security Top 10:2023 | `access-control` (BOLA, BFLA) | runtime module |
| OWASP LLM Top 10:2025 | `llm-agent` (LLM01, 02, 03, 04, 05, 06, 10; LLM07 to 09 have no module) | runtime module |
| OWASP Top 10 for Agentic Applications:2026 | `llm-agent` (ASI02, 03, 05, 06) | runtime module |
| OWASP Agentic Skills Top 10 v1.0 | `agentic-skills` (AST01, 03, 04, 05, 06, 07, 09, 10); AST02 routes to `supply-chain`; AST08 is the three-bucket taxonomy | runtime module |
| CWE Top 25 | `injection`, `path-and-file`, `secrets-and-crypto`, `agentic-skills` | runtime module |
| STRIDE and LINDDUN | none | always-on open pass in the reviewer body |
| Proactive Controls 2024 | none | spec-stage secure-design mode only |

### Three buckets assign each check to an owner

- **`tool`**: scanner-owned (npm audit, pip-audit, govulncheck, Semgrep, CodeQL). The reviewer
  confirms the scanner is wired and flags `degraded: no scanner` when it is not.
- **`hybrid`**: the scanner finds the flow, the reviewer judges the fix.
- **`reason`**: reviewer-only classes scanners cannot see, such as access-control
  logic flaws, fail-open versus fail-closed, confused deputy, and privacy
  exposure.

### Load only the modules the change crosses

An auth-touching endpoint pulls `access-control` and often `authn-session`. A
`SKILL.md` change pulls `agentic-skills` only when it alters authority,
untrusted-input handling, tools, permissions, sandboxing, metadata parsing,
security-metadata declarations, distribution security, or data handling.

It
pulls `llm-agent` too when it changes prompt trust boundaries, tools,
permissions, sandboxing, or model-output handling. Ordinary prompt wording
loads neither.

The two agent-facing modules split by artifact versus runtime. `agentic-skills`
covers the skill artifact: metadata parsing, distribution, and whether a
containment boundary is declared.

`llm-agent` covers runtime behaviour:
execution isolation and blast radius, inter-agent privilege propagation, and
memory or context poisoning. AST06 in `agentic-skills` checks only that a skill
names its containment mechanism; checking that the containment holds belongs to
`llm-agent`, so an isolation question can need both modules.

Architecture review stays at design altitude and routes control-level
verification to `security-reviewer` and `security-checklists`.

### A second library uses the same mechanism with a different key

`operational-safety` also routes by Module index and inlines only the modules a
change warrants. It keys on the operational failure mode (provisioning or
mutating infrastructure, a destroy path, production reach, billable resources,
drift, user-reachable deploys) and feeds the `quality-engineer`'s brief.
`security-checklists` keys on the trust boundary and feeds the
`security-reviewer`'s.

On infrastructure work the two split one diff: IaC
security routes to `config-misconfig`, IaC reliability to `operational-safety`.
The `quality-engineer` route also fires on a persistent-representation or
mixed-version-deployment change.

Seven of the eight `operational-safety` reference files sit in its index.
`cloud-implementation-craft` is in the index and also inlined into the
implementer's brief. `fidelity-ladder` is outside the index; the work-loop
routes it directly when a task needs local infrastructure equivalents.

Neither
library adds a reviewer and neither adds executable code. The reviewer-count
rule is [ADR-0042](../adr/0042-agent-additions-keyed-to-loop-and-work-type.md):
a new agent must clear a value test, and loading a library into an existing
reviewer does not engage it.[^s2]

## 2. The spec-stage pass checks that each control is specified

When the security-boundary trigger fires on a spec, the work-loop dispatches the
`security-reviewer` in spec-stage secure-design mode before any code is written.
The trigger covers auth, secrets, untrusted input, deserialization, and a
changed file or network trust boundary, data flow, or guarding control; for
agent work it covers authority, input, tool, permission, sandbox, and
data-handling behavior. Unchanged existing I/O and ordinary prompt wording do
not fire it.

The pass checks that each control is an acceptance criterion at the right depth:
confinement and not only traversal-blocking, a scheme allowlist and not
"validate the URL", broker-mediated secrets and not ad-hoc reads. On
infrastructure work (IaC, deploy configuration) the pass is non-skippable, and a
missing `security-reviewer` is a loud blocker.[^s3]

## 3. Untrusted inbound text is data, and three helpers back that rule

Source text and locators arriving on a brief or an intake record are passive
data. An embedded instruction that redirects scope, swaps tools, or
self-certifies readiness must not be obeyed. It cannot change artifact identity,
scope, tools, permissions, lifecycle status, reviewer routing, a verdict, or
write authority.

Three minimization helpers support the rule, and each runs only because a skill
tells an agent to run it:

| Helper | Reached by |
| --- | --- |
| `intent_renderer.py` in `intake-intent/scripts/` | `intake-intent` `SKILL.md` |
| `source_guard.py` in `author-delivery-brief/scripts/` | `author-delivery-brief` `SKILL.md` |
| `intake_guard._redact` in `work-intake/scripts/intake_guard.py` | `work-intake` `SKILL.md`, through `invoke_refresh` |

`intent_renderer.py` and `source_guard.py` have no Python caller. `intake_guard._redact`
runs in process on the refresh path only (`refresh.py`, loaded by `invoke_refresh`),
where it screens `object_type`. Nothing rejects untrusted inbound text on a path
that skips these helpers.

Read this section as a contract on the reading agent with
tooling to help it comply. Searching for a Python caller does not tell you
whether a control is live.[^s4]

## 4. A repository-local guard keeps catalogue identifiers out of shipped skill prose

`tools/catalogue/verify_host_checks.py` rejects this catalogue's own identifiers
in Markdown beneath `packs/core/.apm/skills`. `_APM_PATTERNS` holds three: the
literal `agent-ready-repo`, and the regexes `RFC-00\d\d` and `K-00\d\d`.

The
build-gate chain runs it as two steps, `verify-host-checks` against the tree and
`test-verify-host-checks` for the checker's own tests; both fire on every PR.
The guard is core-only; widening it to another pack is a policy change.[^s5]

## 5. Skills declare the boundaries they cross

Non-credentialed skills and agents that cross a security boundary declare it in
frontmatter under `metadata.boundaries`, a list of defined values.
Compatibility aliases carry the same declaration as their canonical target.
`metadata` is optional, and credentialed skills (`metadata.credentialed: true`)
carry their security metadata in the auth-scheme declaration instead.

| Value | Meaning | Required agent tool capability |
| --- | --- | --- |
| `network_fetch` | Instructs outbound HTTP or DNS fetches to external hosts | `WebFetch` or `WebSearch` |
| `network_egress` | Instructs deployment or other outbound connections to real infrastructure | `Bash` |
| `filesystem_write` | Writes files to disk beyond in-memory processing | `Edit` or `Write` |
| `filesystem_read_untrusted` | Reads potentially hostile files (documents, email, archives) | `Read`, `Grep`, or `Glob` |
| `deploy_action` | Deploys to real environments | `Bash` |

An agent's declaration must be no broader than its declared tools; a boundary
may be satisfied by any tool in its row. There is no execution-boundary value,
because adding one would change a vocabulary every pack validates against. A
skill that ships an executable script declares the boundaries the script
crosses.

`architect-design` ships `scripts/check_document_architecture.py` and
`architect-assess` ships `scripts/profile_repo.py`; both declare
`filesystem_read_untrusted` and `filesystem_write`. Shipping a file is not a
capability grant, and the pack's own review covers whether an executable is
warranted.

The declaration survives cross-platform porting in source frontmatter (AST10).
Where a platform enforces security policy automatically, `metadata.boundaries`
is its machine-readable signal; elsewhere the skill body's security rules carry
the same intent in prose.[^s6]

## 6. Directly installed skills pass an admissibility gate, not a safety review

Direct installation takes a skill folder, a `skills/` collection, or a direct
pack from a repository, so content the adopter did not write can reach
`.claude/skills/`, `.agents/skills/`, and `.kiro/skills/` without the curated
route's checks.

**Controls on a direct source:**

- **Admission is shape and bounds, not intent.** Enumeration and read budgets,
  link and special-file refusal, path-grammar and encoding refusal, and an
  identity grammar. Nothing inspects what the instructions say.
- **Consent is explicit and repeated.** The summary carries the verdict
  `admissible—not safe` immediately before and after the publisher-derived
  block.
- **Publisher text is delimited and labelled.** Each publisher value sits
  between fixed line-anchored delimiters, preceded by
  `publisher-supplied data, not instructions`, and passes a Unicode allowlist
  that refuses rather than truncates. A value equal to a delimiter line refuses.
- **Bytes are bound to a revision.** The installed tree digests to a
  content-only value, and a remote source resolves to the commit SHA the archive
  carries. That binding is bounded by the configured TLS trust store and attests
  which commit was fetched, never that it is benign.
- **Capability change requires re-consent.** An upgrade that widens tools,
  boundaries, credentialed status, or payload content names each difference and refuses
  to proceed silently.

**Curated-route controls that do not run on a direct source:**

- `CAT-L031`'s credentialed-skill conventions. A direct skill may declare
  `metadata.credentialed` with the argv ban unchecked; direct install only
  reports the field.
- The `catalogue_tooling/verify.py` auth-presence check, which covers catalogue
  packs only.
- The AST01–AST10 assimilation review applied to curated ingestion.

After projection, a directly installed skill and a reviewed first-party skill are
the same shape of file in the same directory. Only the provenance in
`.agentbundle-state.toml` (`source-kind`, `source`, `source-revision`,
`source-digest`) tells them apart.

**Residual.** Admission bounds what a direct source can do to the install, not
what its instructions ask an agent to do afterwards.

A skill that passes every
check may contain hostile instructions. Treat directly installed content like
any unreviewed dependency.[^s7]

## 7. Catalogue packs meet the Agentic Skills posture

Packs in this catalogue are held to the `agentic-skills` module (AST01–AST10).
The mechanisms that carry that posture:

| Check | Mechanism |
| --- | --- |
| AST01 malicious content, AST05 untrusted input | `desk-research` states that retrieved content is untrusted data. |
| AST02 supply chain | The `supply-chain` module; `pack.toml` version pinning at build time. |
| AST03 permission scope | Skills are scoped to their purpose and name high-impact tools explicitly. |
| AST04 metadata parsing | Only the `agentbundle` build pipeline parses metadata, through a safe YAML load path. |
| AST06 containment | `confluence-crawler` and `jira` document SSRF pre-flight in their security rules. The scripts validate only the URL scheme; rejecting private-IP ranges and cloud-metadata endpoints is the agent's pre-flight duty. On the token path the clients follow redirects (`confluence-crawler` always; `jira` outside intake-policy mode), and the cookie path never does, so verify the base URL before invoking. |
| AST07 version drift | `pack.toml` pinning; skills invoke peers by name and resolve versions at install. |
| AST08 scanning | The three-bucket taxonomy. |
| AST09 governance | `marketplace.json` (from `build-self`) inventories the user-capable subset; `agentbundle list-packs` inventories the catalogue; install state shows what is installed; `agentbundle uninstall` revokes. |
| AST10 security metadata | `metadata.boundaries` (§ 5). |
| Ingested candidates | `assimilate-primitive` requires an AST01–AST10 review; `assimilate-repo` names the same gate. |

This posture does not extend to directly installed third-party content (§ 6).[^s8]

## 8. Scanner gates

`make sast` runs under the coordination lease and chains Bandit, pip-audit,
Semgrep, and the npm audit leg. The gate tooling is a CI-only dependency set,
never a runtime dependency of `agentbundle` or `credbroker`
([ADR-0017](../adr/0017-adopt-bandit-pip-audit-semgrep-sast-gate.md)).

| Scanner | Scope and form |
| --- | --- |
| Bandit | `run-bandit-gate.py` at medium severity; stderr is a gate signal ([ADR-0084](../adr/0084-nosec-reason-delimiter-and-stderr-as-a-gate.md)); `lint-nosec-form.py` checks suppression form. |
| pip-audit | `run-pip-audit-gate.py` with `tools/pip-audit-allowlist.toml`. |
| Semgrep | `run-semgrep-gate.py` with `p/python`, `p/security-audit`, and `tools/semgrep/`, under `--strict`, over `tools packs packages tests`, with `SEMGREP_EXCLUDE` governed by [ADR-0102](../adr/0102-path-scoped-semgrep-exclusion-for-scanner-performance.md). `lint-nosemgrep-form.py` checks suppression form. |
| npm audit | `tools/audit-npm.py` with `tools/npm-audit-allowlist.toml`, whose entries carry a reason and an `unblocked_when` condition ([ADR-0083](../adr/0083-extend-sast-sca-gate-to-npm-with-audit-and-allowlist.md)). |
| CodeQL | `codeql.yml` on pull requests and weekly; `languages: python` only. |
| gitleaks, actionlint, zizmor | `ci-security.yml`, on `pull_request` and `push` only. |

The registry rulesets Semgrep loads are fetched unpinned, so a slow registry rule
can fail `--strict` on code the diff did not touch.
`tools/requirements-sast.txt` is range-pinned with no hash-locked counterpart.
Whether CodeQL is a required check on `main` is remote repository state that
this tree does not record.

- **STATUS: PLANNED**: pin or vendor the Semgrep rulesets:
  [`semgrep-registry-ruleset-pinning`](../product/intents/semgrep-registry-ruleset-pinning.md).
- **STATUS: PLANNED**: add JavaScript to Semgrep and CodeQL and make CodeQL a
  required check:
  [`sast-scanner-coverage-expansion`](../product/intents/sast-scanner-coverage-expansion.md).
- **STATUS: PLANNED**: hash-lock the SAST install, expire npm suppressions by
  machine check, and verify the global npm install in `pack-evals.yml`:
  [`scanner-suppression-and-pin-hygiene`](../product/intents/scanner-suppression-and-pin-hygiene.md).
- **STATUS: PLANNED**: apply the argv-to-path boundary validator to the remaining
  sites in the converters and atlassian packs, the core skills that read
  repository status and briefs, and `packages/agentbundle`:
  [`argv-path-boundary-validator-sweep`](../product/intents/argv-path-boundary-validator-sweep.md).[^s9]

## 9. A stored work-item command carries disclosed, unmitigated residuals

The `work-item` record class in `project-knowledge`
([`knowledge-capture.md` § 7](knowledge-capture.md)) admits a record that can
carry a stored, later-executable command. This section is the single home for
that delivery's accepted residuals. It states no count, because a fixed number
falsifies silently when a disclosure is added.

**The write-time control.** `verification_route.command` is stored only as a
bounded, read-only argv array: a four-tool allowlist (`cat`, `wc`, `grep`,
`ls`), refusal of every option-shaped element, a positive character class over
every element, and a re-anchored repository-path rule over the stored-path set
(D6).

All of it runs before anything is written. Everything below is what that
control does not close.

- **Provenance is not established.** Nothing at write time distinguishes a
  command the workflow authored from one copied out of untrusted prose an
  earlier step ingested. Attribution comes from Git history against the
  introducing commit.
- **The verdict is caller-asserted.** A capture is refused unless it carries a
  well-formed, recognized verdict correlated to that exact item. That catches an
  omitted, garbled, or stale-reused verdict. It does not establish that a verdict
  was obtained: the cold reasoning check runs at the close, the capturing agent
  dispatches it and hands the writer the result, and the correlation key is
  computable from the request. No in-process gate can verify that a caller
  consulted an oracle the caller controls, and a writer-issued nonce would be
  relayed. A deliberate agent can assert a verdict it never obtained. This is
  the only validation floor, because the mechanical tier is not built.
- **The merge path is unchecked.** At `--capture` the controls that run are the
  argv rules, the privacy scan, and the verdict gate; the instruction-shape
  refusal and the cold reasoning check run at the close, ahead of it. A record
  can enter the committed store by a merge or contributor branch carrying
  content validated elsewhere or not at all, and nothing re-checks it once it is
  in the tree.
- **D6's stored-path rules confine; they do not classify.** Every member of the
  stored-path set is held inside the repository. Two things sit outside the set
  and are admitted: `grep`'s pattern at index 1, which only the character class
  reaches, so `["grep", "/etc/passwd", "docs"]` passes; and a backslash in
  `verification_route.path`, which `_expect_repo_path` folds to `/` before
  testing. Nothing decides whether an in-repository file is sensitive:
  `credentials.json`, `keys/id_rsa`, `config/prod.env`, and `.env` all clear
  every write-time check, including the privacy scan. A committed secret under
  any name is an unowned residual. It is not the promotion-handoff spec's
  post-resolution confinement obligation, which refuses a path resolving outside
  the repository.
- **D10's prose residual.** Three controls screen a record's own prose only at
  the write path: `assert_persistable_text`'s eight patterns, the
  instruction-shape refusal, and the reasoning dispatch's data-framing. None
  re-runs on a record that arrived by the unchecked merge path, so a merged
  record's prose can carry an email address, a bearer token, a `/Users/<name>`
  path, a tenant identifier, or instruction-shaped text into a later reasoning
  context and into a durable artifact.
- **The late-ordering residual (`AC-0069`).** D6's argv rules run at write time,
  after the per-item cold reasoning dispatch in the close's ordering. An
  attacker-influenced `verification_route.command` element reaches that
  reasoning context screened only by the dispatch's data-delimiting framing.
- **The mechanical tier is absent, and that is a consequence, not a separate
  gap.** Validation is one tier deep: the cold reasoning check. When it is
  unavailable, validation is unavailable. The write path's refusal on any
  unrecognized verdict (`AC-0068`) stands in for the structural floor a two-tier
  design would supply. [`work-item-mechanical-tier`](../specs/work-item-mechanical-tier/spec.md)
  owns the second tier, is Draft, and amends this list when it lands.
- **Six runner obligations belong to the promotion-handoff spec.** Bounding what
  happens when a stored command runs is
  [`work-item-promotion-handoff`](../specs/work-item-promotion-handoff/spec.md)'s:
  post-resolution repository confinement; environment neutralisation; a resource
  cap; a pre-execution re-check against the same argv rules; which matcher
  `grep` runs under, since the character class alone does not decide it; and the
  treatment of the command's output (its sinks, no instruction authority at a
  reasoning step, and a privacy scan before any durable write).[^s10]

## 10. Related decisions

- [ADR-0018](../adr/0018-shift-security-review-left-progressive-disclosure.md): security review shifts left and uses progressive disclosure.
- [RFC-0029](../rfc/0029-strengthen-security-reviewer.md): established `security-checklists` and its boundary-to-module routing.
- [ADR-0017](../adr/0017-adopt-bandit-pip-audit-semgrep-sast-gate.md), [ADR-0083](../adr/0083-extend-sast-sca-gate-to-npm-with-audit-and-allowlist.md), [ADR-0084](../adr/0084-nosec-reason-delimiter-and-stderr-as-a-gate.md): the scanner gates.

[^s1]: `packs/core/.apm/skills/security-checklists/SKILL.md` (Module index); `packs/core/.apm/agents/security-reviewer.md`; modules under `packs/core/.apm/skills/security-checklists/references/` (eleven).

[^s2]: `packs/core/.apm/skills/operational-safety/references/` (eight files); `docs/adr/0042-agent-additions-keyed-to-loop-and-work-type.md`.

[^s3]: `work-loop` skill security-review step; ADR-0018.

[^s4]: `packs/core/.apm/skills/intake-intent/scripts/intent_renderer.py`, `packs/core/.apm/skills/author-delivery-brief/scripts/source_guard.py`, `packs/core/.apm/skills/work-intake/scripts/intake_guard.py` (`_redact`).

[^s5]: `tools/catalogue/verify_host_checks.py` (`_APM_PATTERNS`).

[^s6]: Agent validator: `packages/agentbundle/agentbundle/catalogue_tooling/lint.py` (agent `metadata.boundaries` declarations); script-shipping skills: `architect-design` and `architect-assess` under `packs/architect/.apm/skills/`.

[^s7]: `packages/agentbundle/agentbundle/direct_install.py`, `direct_source_state.py`; `catalogue_tooling/verify.py`.

[^s8]: `packs/desk-research/.apm/skills/desk-research/SKILL.md` ("Trust posture"); `packs/atlassian/.apm/skills/confluence-crawler/scripts/_client.py` and `jira/scripts/_client.py` (redirect handling); `packs/catalogue-curation/.apm/skills/assimilate-primitive/`.

[^s9]: `Makefile` targets `sast`, `sast-unleased`, variables `SAST_DIRS` and `SEMGREP_EXCLUDE`; `tools/requirements-sast.txt`; `.github/workflows/codeql.yml`, `ci-security.yml`; `docs/specs/pack-script-root-boundary-validation/spec.md`.

[^s10]: `packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py` (`assert_persistable_text`, `_expect_repo_path`); `docs/specs/work-item-capture/spec.md`.
