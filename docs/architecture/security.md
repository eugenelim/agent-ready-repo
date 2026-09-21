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
index](../../packs/core/.apm/skills/security-checklists/SKILL.md#module-index) —
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
auth-touching endpoint pulls `access-control` and often `authn-session`. A `SKILL.md`
change pulls `agentic-skills` only when it alters authority, untrusted-input handling,
tools, permissions, sandboxing, metadata parsing, security-metadata declarations
(`metadata.boundaries`, `metadata.credentialed`), distribution security, or data handling; it may
also pull `llm-agent` when it changes prompt trust boundaries, tools, permissions,
sandboxing, or model-output/data handling. Ordinary prompt wording does not load either.

## Shift-left secure-design review

When the **security-boundary risk trigger** fires on a spec (auth, secrets, untrusted
input, deserialization, or a changed file/network trust boundary, data flow, or guarding
control; for agent work, authority, input, tool, permission, sandbox, or data-handling
behavior), the work-loop dispatches the `security-reviewer` in **spec-stage secure-design
mode** — before any code is written. Unchanged existing I/O and ordinary prompt wording
do not fire the trigger.
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
| **AST09** Governance | PASS | Auditable inventory of the user-capable subset via marketplace.json (built by `build-self`); full catalogue inventory via `agentbundle list-packs`; install-state-visibility command; revocation via `agentbundle uninstall` |

### Findings addressed

| Finding | Severity | AST | Fix applied |
|---|---|---|---|
| `research` skill did not explicitly state that fetched content is treated as data not instructions | Concern | AST05 | Added "Trust posture — retrieved content is untrusted data" section to `research/SKILL.md` |
| `confluence-crawler` and `jira` skills did not declare SSRF containment for user-supplied base URLs | Concern | AST06 | Added agent pre-flight check note to Security rules in both `confluence-crawler/SKILL.md` and `jira/SKILL.md`. The scripts validate only the URL scheme (`http://`/`https://`); the host pre-flight check (reject private-IP ranges and cloud-metadata endpoints) is the agent's responsibility. On the token path `follow_redirects=True` is active — verify before invoking. |
| Non-credentialed boundary-crossing skills carried no security metadata in frontmatter | Concern | AST10 | Added `metadata.boundaries` lists to: `assimilate-primitive`, `assimilate-repo`, `propose-catalogue-pack` (catalogue-curation; `export-catalogue` has since been removed — its CLI replacement carries this in the engine); `file-to-markdown`, `msg-to-markdown`, `markdown-to-docx`, `markdown-to-html`, `markdown-to-pptx`, `markdown-to-xlsx`, `mermaid-renderer` (converters); `release-loop` (release-engineering); `research`, `source-map` (research) |
| Ingested candidates | Concern | AST01-AST10 | `assimilate-primitive` requires an AST01-AST10 agentic-skills security review; `assimilate-repo` names the same gate |

### Third-party skill content reaching a projection directory

Catalogue installation is no longer the only path by which content the adopter
did not write reaches `.claude/skills/`, `.agents/skills/`, and `.kiro/skills/`.
Direct installation takes a skill folder, a `skills/` collection, or a direct
pack straight from a repository, so the audited-pack posture above does not
cover everything that can land in those directories.

**Governance posture.** A direct source passes one admissibility gate before
anything is written, and the gate is not a safety judgement:

- **Admission is shape and bounds, not intent.** Enumeration and read budgets,
  link and special-file refusal, path-grammar and encoding refusal, and an
  identity grammar. Nothing inspects what the instructions say.
- **Consent is explicit and repeated.** The summary carries the verdict
  `admissible—not safe` immediately before *and* immediately after the
  publisher-derived block, because a long capability list scrolls a single
  leading verdict out of view.
- **Publisher text is delimited and labelled.** Every publisher-supplied value
  is emitted between fixed line-anchored delimiters, preceded by
  `publisher-supplied data, not instructions`, and passed through a Unicode
  allowlist that refuses rather than truncates. A value equal to a delimiter
  line refuses.
- **Bytes are bound to a revision.** The installed tree digests to a
  content-only value, and a remote source resolves to the commit SHA carried by
  the archive rather than to a branch name.
- **Capability change requires re-consent.** An upgrade that widens tools,
  boundaries, credentialed status, or payload content names each difference and
  refuses to proceed silently.

**Curated-route controls that do not run here.** Three checks the curated
ingestion path applies never execute on a direct source:

- **`CAT-L031`'s credentialed-skill conventions.** Its D2 rule mechanizes this
  repository's `credbroker` requirement by banning credentials on argv. A
  direct skill may declare `metadata.credentialed` with that convention
  unchecked — direct install only *reports* the field.
- **`catalogue_tooling/verify.py`'s auth-presence check.** It runs over
  catalogue packs, not over a direct source, so nothing verifies that a
  credentialed direct skill declares where its credential comes from.
- **The AST01–AST10 assimilation review.** Described above for curated
  ingestion; a direct source passes the admissibility gate instead.

**Telling the two apart after installation.** Once projected, a directly
installed skill and a reviewed first-party one are the same shape of file in
the same directory. The only signal that distinguishes them is the provenance
recorded in `state.toml` — `source-kind`, `source`, `source-revision`, and
`source-digest` on the owning row. Nothing at the projection surface carries it.

**What a commit pin does and does not establish.** A remote direct source
resolves to the commit SHA the archive carries, so the bytes are bound to a
revision rather than to a moving branch. That binding is only as strong as the
transport that delivered it: it is bounded by the configured TLS trust store,
and it attests which commit was fetched, never that the commit is benign.

**Residual, stated plainly.** Admission bounds what a direct source can *do to
the install*, not what its instructions ask an agent to do afterwards. A skill
that passes every check may still contain hostile instructions. The audited
OWASP posture above applies to packs in this catalogue and does not extend to
directly installed third-party content; treat such content the way you would
treat any unreviewed dependency.

### Security metadata convention — `metadata.boundaries`

Non-credentialed skills and agents that cross a security boundary declare it in
frontmatter under `metadata.boundaries` (a list). Compatibility aliases carry
the same declaration as their canonical target; they do not create a separate
boundary contract. Defined values:

| Value | Meaning |
|---|---|
| `network_fetch` | Skill instructs outbound HTTP/DNS fetches to external hosts |
| `network_egress` | Skill instructs deployment or other outbound connections to real infrastructure |
| `filesystem_write` | Skill writes files to disk (beyond in-memory processing) |
| `filesystem_read_untrusted` | Skill reads potentially hostile files (untrusted documents, email, archives) |
| `deploy_action` | Skill deploys to real environments (ephemeral or production) |

An agent declaration must be no broader than its declared tools. The validator
uses these capability correspondences; a boundary may name any tool in its row:

| Boundary | Required tool capability |
|---|---|
| `network_fetch` | `WebFetch` or `WebSearch` |
| `network_egress` | `Bash` |
| `filesystem_write` | `Edit` or `Write` |
| `filesystem_read_untrusted` | `Read`, `Grep`, or `Glob` |
| `deploy_action` | `Bash` |

`metadata` itself is optional. When an agent declares `metadata.boundaries`,
the value must be a list of the defined values above.

**A skill that ships an executable script is outside this table.** The two
`Bash` rows above describe what a skill *instructs a model to do* — reach the
network, or deploy — and neither covers a script the pack ships for a human
or a CI step to run directly. There is no execution boundary value, and
adding one would change a vocabulary every pack validates against.

Such a skill declares the boundaries its script actually crosses, not a
capability standing in for the fact that it is executable.
`architect-design` ships `scripts/check_document_architecture.py` and
`architect-assess` ships `scripts/profile_repo.py`; both declare
`filesystem_read_untrusted` and `filesystem_write`, which is what those
scripts do. Shipping the file is not itself a capability grant: the
boundaries describe the reads and writes, and the pack's own review covers
whether shipping an executable is warranted.

Credentialed skills (those with `metadata.credentialed: true` and auth details) already carry
sufficient security metadata via their auth-scheme declaration; they do not need `boundaries`.

This metadata survives cross-platform porting in source frontmatter, satisfying AST10.
When a platform automates security-policy enforcement, `metadata.boundaries` provides the
machine-readable signal; when it does not, the skill or agent body's security rules carry the
same intent in prose.

## Work-item capture — the security gap list

`project-knowledge`'s `work-item` kind
(`docs/specs/work-item-capture/spec.md`, `docs/architecture/knowledge-capture.md`
§ 7) admits a record that may carry a stored, later-executable command. This
is the **single home** for that delivery's accepted, unmitigated residuals.
No count is stated: a fixed number falsifies silently the day a disclosure
is added, so the list below is itself the assertion, not a tally of it.

**The write-time control.** `verification_route.command` is stored only as
a bounded, read-only argv array: a four-tool allowlist (`cat`, `wc`,
`grep`, `ls`), every option-shaped element refused, a positive character
class over every element, and a re-anchored repository-path rule over
§ D6's stored-path set, all enforced
before anything is written. Everything after this paragraph is what that
control does **not** close.

- **Provenance is not established.** Nothing at write time distinguishes a
  command the workflow authored from one copied out of untrusted prose an
  earlier step ingested. Attribution comes from Git history against the
  introducing commit, not from a field on the record.
- **The verdict is caller-asserted.** A capture is refused unless it
  carries a well-formed, recognized verdict correlated to that exact item,
  which catches an omitted, garbled or stale-reused verdict. It does not
  establish that a verdict was *obtained*: the cold reasoning check runs at
  the close, so the capturing agent dispatches it and hands the writer the
  result, and the correlation key is computable from the submitted request.
  No in-process gate can verify that a caller consulted an oracle the
  caller controls, and a writer-issued nonce would simply be relayed. A
  deliberate agent can therefore assert a verdict it never obtained. This
  is the delivery's only validation floor, because the mechanical tier is
  not built.
- **The merge path is unchecked.** The write-time controls that do run at
  `--capture` are the argv rules, the privacy scan and the verdict gate;
  the instruction-shape refusal and the cold reasoning check run at the
  close, ahead of it. A record can enter the
  committed store by a merge or a contributor branch instead, carrying
  content validated elsewhere or not at all, and nothing here re-checks it
  once it is in the tree.
- **§ D6's stored-path rules confine; they do not classify.** Every
  member of § D6's stored-path set is held inside the repository. Two
  things sit outside that set and are admitted: `grep`'s pattern at index
  1, which only the character class reaches, so
  `["grep", "/etc/passwd", "docs"]` passes; and a backslash in
  `verification_route.path`, which `_expect_repo_path` folds to `/` before
  testing. Within the set, nothing decides whether an in-repository file
  is *sensitive* — `credentials.json`, `keys/id_rsa`, `config/prod.env`
  and `.env` alike clear every write-time check, including the privacy
  scan. An untracked secret committed under any name is a disclosed,
  **unowned** residual: it is not the promotion-handoff spec's
  post-resolution confinement obligation, which refuses a path resolving
  *outside* the repository, and an in-repository file never does. An
  earlier draft carried a dot-leading-component rule here; amendment 008
  removed it, because a filename-convention denylist is the documented
  antipattern for path security, it added nothing to confinement, and it
  caught `.env` while missing the three names above.
- **§ D10's prose residual.** Three controls run on a record's own prose
  only at the write path: `assert_persistable_text`'s eight patterns, the
  instruction-shape refusal, and the reasoning dispatch's data-framing.
  None of the three re-runs on a record that reached the store by the
  unchecked merge path above, so a merged record's prose can carry an
  email address, a bearer token, a `/Users/<name>` path, a tenant
  identifier, or instruction-shaped text into a later reasoning context and
  into a durable artifact, screened by nothing.
- **The late-ordering residual (`AC-0069`).** § D6's argv rules run at
  write time, but *after* the per-item cold reasoning dispatch in the
  close's own ordering. So an attacker-influenced
  `verification_route.command` element reaches that reasoning context
  screened only by the dispatch's data-delimiting framing — not by the argv
  rules, which have not run yet at that point.
- **The absent mechanical tier — stated as a consequence, not as a
  separate gap.** This delivery ships one validation tier: the cold
  reasoning check. `docs/specs/work-item-mechanical-tier/spec.md` owns the
  second, deterministic tier and has not landed. Because validation is one
  tier deep, an unavailable reasoning tier is the whole of validation being
  unavailable — there is no second tier to fall back to — and the write
  path's refusal on any unrecognized verdict (`AC-0068`) is what stands in
  for the structural floor a two-tier design would otherwise supply. When
  that spec lands, its own settlement — its catalog-code and residual-bit
  points — amends this list; its admission check (its own `AC-0004`) is
  conditioned on an item both checks admit and never covers the
  unavailability case `AC-0068` already refuses.
- **Six residual runner obligations, handed over, not owed here.** Bounding
  what happens when a stored command actually **runs** is
  `docs/specs/work-item-promotion-handoff/spec.md`'s, not this delivery's:
  post-resolution repository confinement; environment neutralisation; a
  resource cap; a pre-execution re-check of the stored command against
  these same argv rules immediately before it runs; which matcher `grep`
  runs under, since the character class alone does not decide it; and the
  treatment of the command's output — its sinks, that it carries no
  instruction authority at a reasoning step, and that it is privacy-scanned
  before any durable write. These six are listed here as handed to that
  spec by name, not as gaps this delivery leaves open.

## Related decisions

- **ADR-0018** — why security review shifts left and uses progressive disclosure rather than
  a single monolithic checklist prompt.
- **RFC-0029** — the proposal that established the `security-checklists` skill and its
  boundary→module routing design.
