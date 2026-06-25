# Changelog

All notable user-visible changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Maintenance: this file is updated in the same PR that introduces the
> change. CI will warn (configurable: block) when a PR touches code that
> changes user-visible behavior but does not touch this file.
>
> Entries can be drafted from conventional commits: `git log --oneline`
> filtered to `feat:` and `fix:` since the last tag is a starting point,
> not a finished product. Rewrite for users, not contributors. See the
> [Common Changelog guidance](https://common-changelog.org/) — the audience
> is humans who use the software, not humans who wrote it.

## [Unreleased]

### Fixed

- **The `agentbundle` CLI now writes LF line endings on every platform.** Every
  generated text artifact — adapter projections (Kiro, Cursor, Codex, Gemini,
  Copilot), the composed `AGENTS.md`, the self-host tree, merged
  `.claude/settings.json`, hooks, and TOML/JSON config — is emitted with `\n`
  regardless of OS. Previously, running the CLI on Windows produced CRLF
  (Python's text-mode writers translate `\n`→`\r\n` there), so a repo populated
  on Windows drifted from one populated on macOS/Linux and polluted diffs with
  line-ending churn. All 24 text-mode writers now pass `newline="\n"`, a
  repo-root `.gitattributes` pins `* text=auto eol=lf` at the commit boundary,
  and an AST guard test fails CI if a future writer omits the kwarg.

### Added

- **Guides for shaping a new engagement — product vision, product strategy, and
  the architecture concept.** Three new how-tos document the top of the shaping
  funnel that previously had no guide:
  [*Frame a product vision*](../guides/product-engineering/how-to/frame-a-product-vision.md)
  and [*Shape a product strategy*](../guides/product-engineering/how-to/shape-a-product-strategy.md)
  in the `product-engineering` pack (the two product altitudes of `frame-intent`,
  with their market-existence de-risk), and
  [*Shape an architecture concept*](../guides/architect/how-to/shape-an-architecture-concept.md)
  in the `architect` pack (the ≤½-page Stage-0 concept `architect-design` agrees
  before a full design doc). A new cross-pack explanation,
  [*Shaping a new engagement*](../guides/_shared/explanation/shaping-a-new-engagement.md),
  ties them together — how product intent and the architecture concept co-shape
  each other at engagement start — and the affected pack indexes and existing
  guides gain cross-links.
- **An optional grounding surface lets you record where you deploy and how you
  verify — in files you already own.** The `core` seed `AGENTS.md` "Commands
  you'll need" gains an **optional** infra/verification command block
  (`<deploy>` / `<smoke / verify-status>` / `<teardown>` / `<seed-test-data>`),
  and the `reference.md` golden-path slots now prompt for the managed-runtime /
  platform target, framework-/library-level contracts, and where verification
  tooling lives. The work-loop infra preflight reads these recorded coordinates
  **if present** and falls back to cold oracle discovery if absent — a repo that
  fills nothing runs exactly as before. Recorded values **seed** oracle
  acquisition, never replace it; a coordinate that contradicts the live oracle
  is surfaced as a drift signal. No new config file, and absence never fails the
  loop or any CI gate. `adapt-to-project` and `init-project` now optionally
  offer to record these coordinates.
- **`architect` grounds the design phase in platform reality — a backed
  serverless workload-class lens plus two dual-consumed disciplines.** The
  `architect` pack gains **`lens-serverless.md`** (in both `architect-design`
  and `architect-review`), the cloud-agnostic serverless workload-class lens
  that fills the slot the well-architected rubric named but never backed. It
  carries five durable, concern-grouped concerns — execution & throughput
  limits + the **sync-vs-async gate**, cold-start & readiness, scale-to-zero
  economics / capacity floors / cost cliffs, statelessness & idempotency &
  delivery semantics, and private-serverless network reachability — applied
  across the whole serverless class (compute, data, search/analytics, event
  glue). Two cross-cutting disciplines ride the same routing axis: a
  **platform-contract grounding discipline** (`architect-design` grounds every
  load-bearing managed-service contract on a critical path in an authoritative
  source with stated confidence — never model memory — and `architect-review`
  **independently re-checks** it) and a **synchronous-path viability check**
  (sum worst-case latency across every hop, compare it to the binding
  front-door timeout, and force a sync-vs-async gate for a long-running
  operation — caught at design *and* re-checked at review). The lens stays
  cloud-agnostic; version-specific numbers route to curated platform skills. The
  agentic lens gains a one-line cross-reference into the gate. **No new skill,
  reviewer, or executable tooling, and no per-vendor numbers ship.** (RFC-0045,
  ADR-0035.)

- **`work-loop` grounds its infrastructure inner loop in the platform's real
  contract, not model memory.** A new `core` skill,
  **`infra-contract-acquisition`**, runs a tiered, tool-keyed protocol that
  acquires a stack's real contract from the deterministic oracles its own
  toolchain ships (`terraform validate` + `plan`, `cdk synth`, `pulumi
  preview`, CloudFormation change sets, `kubectl --dry-run=server` + a
  machine-readable schema slice), declares its oracle tier and confidence, and
  degrades honestly to a runtime probe when the toolchain ships no strong static
  oracle. `work-loop` gains an **EXECUTE contract-grounding gate** ("acquire the
  contract before you guess a flag, schema shape, field constraint, or
  packaging assumption" — the infra generalization of "grep to verify a function
  exists before importing it"). A new `operational-safety` module,
  **`cloud-implementation-craft`**, is inlined into the **implementer's EXECUTE
  brief** (least-privilege-but-sufficient permissions, eventual-consistency
  waits, timeout / cold-start / backoff, dependency ordering,
  terminal-failed-state, the managed-runtime packaging / entrypoint model, and
  externalized script configuration). The infra preflight gains a fifth artifact
  (a **durable credential session** — establish once, reuse), a
  **reusable-script corollary** (every live interaction goes through a reusable,
  idempotent, externally-parameterized script), **phased oracle fidelity** (the
  cheap early oracle is necessary, not sufficient), a **readiness-aware
  data-plane probe** (in-network-if-private, write → read-back, poll-with-backoff,
  self-teardown), and a **symptom→layer log playbook** for failure localization.
  Contract-conformance review rides the existing `quality-engineer`, which
  re-derives the contract independently from the oracles — **no new reviewer or
  agent**, and **no executable tooling or per-vendor data** ships. (RFC-0044,
  ADR-0034.)
- **`product-engineering` gains two product altitudes above `capability` — and
  `Level` is now decoupled from `Scale`.** You can shape a greenfield product
  concept (or a multi-feature bet) as a `product-vision` intent (the existence
  bet: why this product should exist, for whom, through what wedge) or a
  `product-strategy` intent (the path: central challenge, guiding policy,
  coherent actions, problem/segment sequence), instead of being forced into a
  `feature`. `Level` is now an **open recognized set**
  (`product-vision › product-strategy › capability › feature`); `Scale` only
  *suggests* a starting altitude you override in a word, and `frame-intent` asks
  the altitude for concept-shaped input. The product-existence bet is de-risked
  once at the top as `market-existence` (market desirability **and** viability),
  distinct from feature-level `desirability`. A sibling-spawn detector *offers*
  to frame a product parent when work won't reduce to one shippable slice, and a
  retroactive-parent affordance back-links orphaned siblings at an inferred
  altitude. Existing `capability` / `feature` intents stay valid — the change is
  additive.
- **`init-project` recognises an `intent` from `frame-intent` as a fourth
  discovery source.** When the `product-engineering` pack is installed, the
  `frame → de-risk → decompose` loop hands its leaf into `init-project`'s value
  gate as an optional upstream source, alongside `research`, a PRD, and a
  `receive-brief` brief.

### Changed

- **The catalogue's seed lint is now opt-in by construction and renamed
  `lint-catalogue-seeds`.** `tools/lint-seeds.py` becomes
  `tools/lint-catalogue-seeds.py` (the CI job, its path filters, the
  `pre-pr-catalogue.py` gate, and the `tools/hooks/README.md` reference are
  renamed in lockstep), and **all** of its checks — the anti-leak blocklist and
  the placeholder-shape checks — now run only on packs whose `pack.toml` carries
  `[pack].lint-seeds = true`. The four first-party scaffold packs (`core`,
  `governance-extras`, `monorepo-extras`, `user-guide-diataxis`) carry the flag,
  so their seeds stay enforced exactly as before; any other pack — including an
  organization pack that intentionally ships filled-in *instance* content — omits
  the flag and is unenforced by construction, with no edit to the lint or any
  central pack list. The flag is catalogue-internal metadata and is not projected
  to `plugin.json` / `marketplace.json`. (RFC-0047 Decision 6 / ADR-0037 D4.)
- **The work-loop's EXECUTE contract-grounding gate now fires on unfamiliar
  frameworks and libraries, not just infrastructure.** Before generating code
  against an unfamiliar internal framework or third-party library whose
  *behavioral* contract (a versioned signature, a deprecation, a call-order or
  lifecycle constraint) the agent doesn't already hold, the gate now routes to a
  **software detect-and-recommend tier** in `infra-contract-acquisition` —
  mirroring its infra tier exactly: detect a framework-library skill (internal or
  a published vendor skill), a Context7-style doc-retrieval surface, or official
  versioned docs via `research`; consult and cite the contract slice if present;
  recommend a source and surface the gap as a decision if absent. The bare "grep
  to verify a symbol exists" rule confirmed existence but never the behavioral
  contract; this closes that gap. The optional doc-retrieval surface stays
  **Tier-1 detect-and-stop — never auto-installed**, and `quality-engineer`
  re-derives the cited software contract slice at REVIEW, symmetric with infra.
  No new skill, no bundled per-library data.
- **`agentbundle uninstall` gains `--dry-run` and `--yes`, and confirms before
  removing anything.** Previously `uninstall` deleted every bundle-owned (Tier-1)
  file immediately with no preview. It now classifies each recorded file
  (`remove` Tier-1 / `keep` Tier-2) and: `--dry-run` prints that plan and writes
  nothing; without `--dry-run` it asks before the first removal (`--yes` skips
  the prompt; a non-interactive stdin refuses rather than hanging). Adopter-edited
  files are still preserved exactly as before.
- **`agentbundle install --force` confirms before its destructive cleanup, and
  `install` offers to upgrade an already-installed pack.** `--force` now lists the
  paths it will remove (the pre-RFC-0012 dist-tree subtrees, or orphan files) and
  asks before deleting; `install` gains `--yes` to skip that prompt. Used purely
  as a cross-scope bypass (no deletion), `--force` is unchanged and never prompts.
  **Migration:** CI that runs the *deleting* form of `install --force`
  non-interactively must now add `--yes` (a non-TTY without `--yes` refuses rather
  than deleting unattended — mirroring `upgrade`). Separately, installing a pack
  already installed at the requested scope now offers to run `upgrade` instead of
  flatly refusing; `install --yes` runs it, and a non-interactive stdin keeps the
  old `use 'upgrade'` refusal.
- **`agentbundle reconcile` and `list-targets` drop their dead `--scope` flag.**
  `reconcile`'s `--scope` had a single legal value (`user`) equal to its default,
  and `list-targets`'s `--scope` was parsed but never read; both are removed, so
  passing `--scope` to either now reports `unknown flag for <verb>: --scope`.
  Default behaviour of both verbs is unchanged.

- **`agentbundle upgrade` no longer takes `--to`; it derives the version and
  confirms (breaking).** The upgrade target is now read from the catalogue you
  point at (its `pack.toml` `[pack] version`) instead of an operator-supplied
  `--to` that was never validated against the catalogue. The command shows
  `installed → target`, asks before writing (`--yes` skips the prompt; a
  non-interactive stdin refuses rather than hanging), names both versions in the
  recap, and says so when you're already current. To upgrade to a specific past
  version, point the catalogue at that git ref. See the agentbundle CHANGELOG
  for the full migration note.

### Added

- **Agentic security boundaries are now control-level checks in the
  `security-checklists` `llm-agent` module (core 0.4.13 → 0.4.14; architect
  0.8.0 → 0.8.1; RFC-0029 / ADR-0032).** The `llm-agent` module — the
  orchestrator-inlined depth the `security-reviewer` reasons from — gains three
  control-altitude checks for the agentic boundaries the well-architected overlay
  previously named only at design time: **execution isolation & blast radius**
  (the three confinement axes — filesystem scope, network egress, resource/time
  caps — distinct from authorization), **inter-agent identity/privilege
  propagation** (a sub-agent must not amplify the spawning request's authority),
  and **memory poisoning** (a write gate that trust-checks content before it is
  persisted, plus the read side). The module's Standards surface adds the **OWASP
  Top 10 for Agentic Applications:2026** (ASI02 / ASI03 / ASI05 / ASI06) and
  **OWASP LLM04** (Data & Model Poisoning), keeping the existing
  LLM01/02/03/05/06/10 surface and the module's delegation legend, spec-stage
  proactive-control, and established-helper-bypass sections intact. As the
  ride-along, the `architect` GenAI/agentic lens (`lens-genai-agentic.md`, both
  skill copies) drops its now-stale "these boundaries reach beyond the module's
  current checks" caveat — they route to a named `llm-agent` check like every
  other security-boundary concern.
- **Agentic well-architected overlay, applied at design time (architect
  0.7.1 → 0.8.0; ADR-0032 / RFC-0042).** Designing an agentic system — one
  that uses tools, takes autonomous action, or runs an agent loop — now gets
  the GenAI/agentic well-architected overlay **by construction**, not only when
  a reviewer later runs well-architected mode. `architect-design`'s Stage 0
  gains a **workload-class** routing axis alongside its provider axis: an
  agentic concept loads the shared `lens-genai-agentic.md` overlay (and, on a
  named cloud, the provider pillars too — the axes are orthogonal). The shared
  lens is reorganised into a **progressive, capability-tiered** taxonomy —
  Tier A (the LLM is on the path) → Tier B (the system acts) → Tier C (the
  agent persists or collaborates) — so a plain RAG/chat design applies only the
  baseline tier while a multi-agent system with spend authority applies all
  three. Tier B makes the trust triad first-class — **human oversight,
  intent verification, and auditable action trails** — alongside tool-use
  authorization, tool/MCP source provenance, output handling, execution
  isolation, and reliability under non-determinism; Tier C adds memory & context
  integrity, sub-agent provenance, and inter-agent identity/privilege
  propagation. Graduated autonomy is framed as engineering judgment bounded by
  irreversibility and blast radius, never a standards mandate. Design time and
  review time consume **one shared lens file**, so the two never diverge.
  Security-boundary concerns name the boundary at design altitude and route
  control-level verification to `security-reviewer` / `security-checklists`
  (`llm-agent`). Prose only — no new reviewer, skill, or tooling ships.
- **`operational-safety` reference library for infra/destructive work (core
  0.4.12 → 0.4.13; RFC-0041 P3 / ADR-0031).** Infrastructure and destructive
  operational work now gets a first-class operational-safety depth library — a
  new `operational-safety` skill of six failure-mode-keyed prose modules
  (`state-and-idempotency`, `blast-radius`, `environment-isolation`,
  `cost-and-teardown`, `drift-and-rollback`, `observability-and-smoke`),
  structurally identical to `security-checklists`. When the work-loop detects
  infra/destructive work, the orchestrator loads only the matching modules
  (1–N, never all six) and inlines them into the **existing `quality-engineer`**
  reviewer's brief — so idempotency, blast radius, environment isolation,
  cost/teardown, drift/rollback, and observability/smoke get reviewer depth
  with **no fourth reviewer** (ADR-0023). The split against `security-checklists`
  is clean: security config → `security-checklists` (`security-reviewer`);
  reliability/ops config → `operational-safety` (`quality-engineer`).
  `security-checklists`' `config-misconfig` also gains a URL-free, version-free
  deferred-authority pointer (CIS Benchmarks + the per-provider well-architected
  security guidance) noting the real per-provider depth lives in the
  self-updating scanner. Prose only — no executable code ships.
- **One consolidated, namespaced pack-output layout file — `agentbundle-layout.toml`
  (RFC-0040 / ADR-0030).** An adopter who wants to control where a pack's durable
  output lands now edits **one** namespaced file instead of a per-pack config.
  `agentbundle-layout.toml` carries one `[<pack>]` table per output-producing pack
  (`research`, `architect`, `product-engineering`), each with a single `parent`
  **base** under which the skill creates a topic-named folder per unit of work. Two
  locations resolve with clear precedence — a checked-in `./agentbundle-layout.toml`
  overrides a personal `~/.agentbundle/agentbundle-layout.toml`, per table. The file
  is **adopter-owned and never shipped**: it comes into being by hand, or an
  `agentbundle install` step **appends** a pack's default section to one that already
  exists (never creating it, never overwriting a section you wrote). Reading stays
  **prompt-only** (Charter Principle 3 — no engine, index, daemon, or watcher); each
  consumer confines the resolved path (realpath-resolve, reject `..`, surface the
  absolute path before the first write) and treats a repo-sourced out-of-tree
  `parent` as an Ask-first, untrusted-origin case. Each consuming pack ships a
  `references/agentbundle-layout.md` schema doc and a scope-keyed `[pack.layout]`
  manifest default; `pack.toml` gains the optional `[pack.layout]` table (adapter
  contract → v0.16). `architect` (0.6.1 → 0.7.0) and `product-engineering`
  (0.4.2 → 0.5.0) become consumers; `research` (0.4.0 → 0.5.0) migrates from the
  undistributed `research-layout.toml` by a **clean rename, no alias**.
- **Infra-aware `work-loop` — the loop can now drive an infrastructure inner
  loop end-to-end (`core` pack, bumped to `0.4.12`; RFC-0041 / ADR-0031).** The
  loop's verification modes previously assumed the verification mechanism
  already existed and assumed a fast, local, stateless, single-hop gate — so a
  cloud deploy stalled the agent and the human became a relay, pasting deploy
  errors back into the session by hand. Four doctrine additions close that gap,
  all prose (no executable tooling, no new reviewer, no new risk trigger): (P1)
  a **generalized verification-mechanism preflight** — picking a verification
  mode now obligates confirming its mechanism exists, and if not, building it is
  *task zero*; this is agnostic (a missing test runner or build command, not
  just an infra smoke check) and **universal across light and full mode**, with
  the infra mechanism enumerated as a multi-artifact set (verify-status +
  teardown + test-data/mock-user seeding + a provider-appropriate
  policy-as-code/CSPM scanner). (P2) a fourth **infra/deploy verification
  flavor** whose contract is a layered GATES sequence (static preflight →
  plan/preview → idempotent convergent apply → active end-to-end smoke →
  rollback), cross-linked to the plan's `## Rollout` section. (P4) an
  **agent-drives-verification** doctrine — the agent runs the deploy and reads
  real environment output itself, with the human-as-relay named as the
  anti-pattern and Claude Code background tasks / `asyncRewake` / `PreToolUse`
  as accelerant only. (P5) **mandatory infra security** — infra-flavored work
  non-skippably runs `security-reviewer` at both spec stage and on the diff,
  force-loading the infra-relevant `security-checklists` modules, paired with
  the P1 policy-as-code/CSPM scanner for per-provider depth.
- **Research project mode — a four-skill lifecycle for sustained investigations
  (`research` pack, bumped to `0.4.0`).** Alongside the existing depth axis
  (`/research` quick/standard/applied/deep), the pack gains a *lifecycle* axis
  for multi-week investigations that accumulate a corpus:
  `research-project-start` scaffolds a three-layer project folder (raw
  `sources/` → a `synthesis-matrix.md` + `memos.md` **digest** middle layer the
  pack previously lacked → a typed synthesis); `research-project-digest` clusters
  sources into emergent, constructed matrix columns; `research-project-synthesize`
  emits the typed verdict **and** a single-file, self-contained
  `<topic-slug>-brief.md` that governance can lift whole into an RFC; and
  `research-project-check` is a passive saturation stop-signal that reads the
  matrix by eye and recommends — it never advances the lifecycle. Projects live
  in scratch / out-of-repo by default (configurable via the `[research]` table
  of an adopter-created `agentbundle-layout.toml`); the corpus is never committed
  to the repo, only the distilled brief. Prompt-only by construction (no engine, index, or counter);
  the seven existing skills are reused as phase operations. RFCs may now carry an
  optional `docs/rfc/NNNN-notes/` companion folder for promoted research.
- **Pack activation evals (Tier A) — `tools/run-pack-evals.py` + `[pack.evals]`
  (RFC-0037 / ADR-0028).** A catalogue maintainer can now measure, repeatably
  and empirically, whether each covered skill *activates* on the prompts it
  should and stays quiet on the near-misses it shouldn't. Each covered skill
  ships `evals/eval_queries.json` (a flat `[{query, should_trigger}]` array);
  a pack's `pack.toml` `[pack.evals].skills` lists the covered skills; the
  runner projects the pack in isolation, runs each query through the headless
  `claude` detector, computes a `trigger_rate` over N runs, grades against a
  0.5 threshold, and writes a gitignored, iteration-numbered eval-workspace.
  It runs report-only in a scheduled `pack-evals.yml` workflow — never on the
  PR critical path — and the first cut covers the `core` and `converters`
  packs. `lint-skill-spec.py` now accepts and validates `eval_queries.json`
  and enforces `[pack.evals].skills` coverage. A second, **in-harness** mode
  (`run-pack-evals.py --mode in-harness`, RFC-0037 § Errata E2) extends the
  reach to **Kiro IDE** and interactive Claude Code where there is no `claude`
  CLI: the host agent dispatches a read-only sub-context per query and reports
  activation — a lower-fidelity (reported, not observed) proxy, labelled as such
  in the summary so it is never mistaken for the headless baseline. A
  **lightweight behavior/output check** (`--check behavior`, RFC-0037 § Errata
  E3) goes further where it's safe: the agent runs the skill in a confined
  per-eval working dir and the runner re-derives deterministic post-conditions
  (an `evals/evals.json` `expect` block — produced files, output substrings)
  plus attested assertions (`tier: B-lite`). And a report-only **LLM-judge**
  (`--mode judge`, RFC-0037 § Errata E4) grades the *quality* layer against the
  eval rubric, behind a **config-driven, multi-adapter** backend seam: built-in
  `claude-code` (same model) + `codex` (independent model/IDE), and adopters add
  their own — e.g. a `kiro-cli` headless judge — and pick the model purely by a
  `--judge-config` entry, no code change. The judge is judgment-only and
  fails closed on an unparseable verdict. The **full** Tier-B grading (pass-rate
  deltas, with/without-skill, train/validation, the human-feedback loop) stays a
  future RFC.
- **Per-prompt work-loop activation hook (`core` pack).** A new
  `work-loop-check` hook nudges the agent, on every prompt, to load the
  work-loop skill for non-trivial work — closing a gap where the loop was
  not reliably activated. It ships as a matched pair so it reaches both
  surfaces: a `UserPromptSubmit` hook-wiring + hook body for Claude Code
  (and Copilot / Cursor / Gemini / Codex), and a standalone `promptSubmit`
  `askAgent` `.kiro.hook` for Kiro IDE, which reads only `.kiro/hooks/`
  files and ignores hook-wiring. (`agentbundle validate core`'s info line
  now lists both core hook-wirings as not projecting to the Kiro CLI
  adapter — `session-start.toml` and `work-loop-check.toml` — since neither
  declares `attach-to-agent`; this is informational, not a refusal.)
- **Markdown → Office publishing skills (`converters` pack, RFC-0036).** Three new
  skills publish a Markdown artifact back out as a distribution-ready, on-brand
  Office file by **filling a user-provided template** at its existing fill-points —
  `markdown-to-docx` (Word, via `docxtpl`), `markdown-to-pptx` (PowerPoint, via
  `python-pptx`), and `markdown-to-xlsx` (Excel, via `openpyxl`). A designer's
  cover page, slide master, logo, and named cell regions survive because the skill
  fills the template rather than converting Markdown into a fresh document. Each
  detects a template, confirms or elicits one, and proceeds unbranded only on the
  user's explicit opt-out — it never invents a brand and never auto-installs its
  Tier-1 render library. This completes the pack's Office round-trip, which until
  now ran only inward (Office → Markdown). The `converters` pack is bumped to
  `0.2.0`. See
  [Publish Markdown as a branded Office file](../guides/converters/how-to/publish-markdown-to-office.md).
- **SSO web-session cookie auth for `jira` reads + `confluence-crawler` (atlassian
  pack, RFC-0035).** On an Atlassian Data Center instance behind corporate SSO
  where API tokens are blocked, both skills can now authenticate by a captured web
  session instead of a token: pre-bake `references/sso-config.toml`
  (`auth_default = "sso-cookie"`), run `python scripts/setup_sso.py` once to
  register the session, and reads work with no token. The session is resolved
  through the `credbroker` SSO resolver (new `load_sso_cookies`, credbroker 0.2.0)
  and the captured jar is confined to the declared `cookie_domains`; no
  `Authorization` header is sent and redirects are not followed (the session
  cookie never crosses to another host). Both skills keep a `creds` (token)
  fallback — token users with no SSO config see no change. Data Center reads only;
  writes are refused pending XSRF design; Cloud is unchanged. See
  [Authenticate Jira / Confluence with an SSO web session](../guides/atlassian/how-to/authenticate-jira-confluence-with-sso-cookies.md).
- **`jira-brief-intake` skill (atlassian pack).** Turns a Jira epic — or a
  board / sprint / JQL selection of issues — into shippable specs for teams who
  plan kanban-style in Jira. It pulls the epic and its children via the `jira`
  skill, maps them onto a Shape B product brief (epic → Outcome, child issues →
  `US-n` user stories tagged with their Jira key, epic key → `Epic:` provenance
  pointer) at `docs/product/briefs/<slug>.md`, then hands off to the
  `receive-brief` skill to elicit any missing fields, decompose, and build. It
  is read-only against Jira and degrades gracefully — when `receive-brief` is
  not installed it inlines a decompose/execute instruction for the agent to act
  on directly. Pure choreography, mirroring `jira-defect-flow`.

### Changed

- **`architect-design` writes each design effort into its own per-effort folder**
  (`<parent>/<topic-slug>/`) instead of scanning for a loose-file home every run
  (RFC-0040). The previous `docs/design/`→`design/`→`architecture/`→`docs/`
  scan-then-elicit becomes the **default** when no `[architect]` layout section
  resolves. Additive — a folder around what was a file — and documented in the
  pack's `references/agentbundle-layout.md`.
- **`new-rfc` now surfaces the optional `NNNN-notes/` companion
  (`governance-extras` pack, bumped to `0.3.0`).** The skill and its RFC
  template point authors at the optional sibling `docs/rfc/NNNN-notes/` folder
  for promoted research — a distilled brief and supporting material summarized
  into *Evidence & prior art* and linked, rather than pasted into the RFC body.
  Pairs with the companion convention added to `docs/CONVENTIONS.md` § 3, and is
  the landing place for a `research`-pack project's `<topic-slug>-brief.md`.
- **The `work-loop` skill's Context hygiene section now covers output, not just
  input (`core` pack, bumped to `0.4.11`).** A new *Emit less, too* note adds two
  zero-cost habits to the existing window-management guidance: don't restate code,
  files, diffs, or tool output already in the conversation — reference them by path
  and line — and continue with the substance instead of narrating a tool call's
  success. It is framed as waste reduction, not terseness for its own sake: the
  rationale, edge cases, and findings prose that review and the human actually read
  stay in.
- **Research outputs are now named by topic and type (`research` pack, bumped
  to `0.3.0`).** Episodic `/research` artifacts are written as
  `<topic-slug>-<type>.md` (e.g. `oauth-pkce-survey.md`) instead of the generic
  `research.md`, so two investigations in one working directory no longer
  overwrite each other and a file's name says what it is — `survey`,
  `fact-check`, `comparison-matrix`, `shortlist`, `blueprint`, `hypotheses`, or
  `counterpoints`. The scoping skills (`source-map`, `build-outline`,
  `identify-perspectives`, `decision-archaeology`) gain the same
  `<topic-slug>-` prefix. Quick mode is unchanged (inline, no file). The former
  name `research.md` is retained as a recognised legacy alias for one release.
- **The `new-adr` skill and ADR template now follow MADR conventions
  (`governance-extras` pack, bumped to `0.2.0`).** The ADR template gains a
  `Rejected` status (a declined proposal is now kept as a record, not deleted)
  and two optional sections — **Decision drivers** (the criteria a choice was
  judged against) and **Confirmation** (how conformance with the decision will
  be verified). Frontmatter adopts MADR's decision-roles split: the `Deciders`
  field is renamed to **`Decision-makers`** and gains optional **`Consulted`**
  and **`Informed`** lines. The H1 title now names the problem *and* the chosen
  solution together (the `ADR-NNNN` ordinal prefix is unchanged), and the skill
  now carries the full post-acceptance lifecycle discipline inline (bidirectional
  supersession, `Deprecated`-vs-`Superseded`, backfilling). The decision stays
  first in the body (answer-first; no options-first reordering). **Breaking for
  the template only:** new ADRs use `Decision-makers`; existing ADRs keep
  `Deciders` and are not rewritten (ADRs are immutable).

- **`credential-setup` now gives a clear install hint instead of a traceback
  when `credbroker` is missing.** Running the setup script without the
  `credbroker` resolver installed prints a single line telling you how to
  install it from your repository checkout and exits cleanly (code `3`),
  rather than dumping a `ModuleNotFoundError` stack trace. A different import
  failure (a broken `credbroker` submodule, say) still surfaces unchanged.

### Fixed

- **Kiro custom agents now reach the bundle's skills — CLI and IDE (contract
  v0.15).** On both Kiro targets, only the **default** agent auto-discovers
  skills; a **custom** agent (`kiro --agent <name>`, including every headless
  `--no-interactive` run, or an IDE subagent) loaded **zero** skills unless it
  declared them in its `resources` field. Packs projected agents without that
  field, so agent-driven runs saw none of the catalogue's skills. Both the
  `kiro-cli` and `kiro-ide` adapters now inject a skill-resources glob
  (`skill://.kiro/skills/**/SKILL.md` and the `~/.kiro/skills/**/SKILL.md`
  user-scope twin) into every projected agent — CLI into the agent JSON, IDE
  into the `.md` YAML frontmatter (quoted, YAML-safe). An agent that declares
  its own `resources` keeps it; the deprecated `kiro` alias inherits the IDE
  behavior. Default-agent runs were already fine and are unaffected.
  (RFC-0022 erratum E4; kiro #6887/#6888/#4993.)
- **`agentbundle install --adapter kiro` now behaves exactly like `kiro-ide`.**
  The deprecated `kiro` alias (RFC-0022) was honored by `make build` but not by
  the install path, which still emitted `.json` agents and merged hook-wiring —
  the legacy behavior. Installing, upgrading, or uninstalling via `kiro` now
  projects `.md` agents and **drops** hook-wiring (the IDE shape), consistent
  with the build registry. The legacy `.json`-agents + hook-wiring-merge
  behavior is unchanged — it lives under the `kiro-cli` adapter. The dropped-
  primitives warning for `kiro` now names what is actually dropped (hook-wiring
  and commands). `state.adapter` still records the name you chose (`kiro` stays
  `kiro`), so the alias remains a working, named adapter. The `attach-to-agent`
  validation and path-confinement rails now also fire for `kiro-cli`, so a
  malformed or path-traversing wiring declaration is refused for the adapter
  that performs the merge.

### Added

- **Pack profiles — install a curated set of packs in one command (RFC-0034).**
  `agentbundle install --profile <name> <catalogue>` reads a first-party
  `profiles/<name>.toml` from the catalogue and installs its packs at the
  profile's single declared scope, in deps-first order, on one pinned adapter,
  with all preconditions checked before any write. `agentbundle list-profiles
  <catalogue>` lists the available profiles (id, scope, description). Two
  profiles ship: `solution-architect` (user scope → `architect` + `research` +
  `contracts`) and `full-ceremony` (repo scope → `core` + `governance-extras`
  + `user-guide-diataxis` + `monorepo-extras`). `--profile` is mutually
  exclusive with `--pack`, and `--scope` is rejected with it (a profile
  declares its own scope). Already-installed packs are skipped, not reinstalled;
  per-pack state rows record `install_route = "profile"`. No new state schema,
  no adapter-contract bump, no new install route — distribution hygiene over
  the existing single-pack install path.

- **New `inception` profile.** A user-scope toolkit for taking an idea from
  zero to a buildable repo — `research` + `product-engineering` + `architect`,
  installed once and carried across ventures. Install with `agentbundle install
  --profile inception <catalogue>`, then use as much of it as the venture
  warrants: architecture alone for a learning project, plus product shaping for
  a side project, plus research when sizing a market. The build loop itself
  stays the repo-scope `core` pack, installed into the new repo at bootstrap.

- **`design` joins the soft `categories` vocabulary.** `agentbundle validate`
  now recognizes `design` as a known pack category, so the `design-craft` pack
  (and any future design pack) declares it without a soft warning. The
  vocabulary is extensible by design (RFC-0031 D8) — this grows it by one slug,
  no RFC required, no behavior change for any other pack.

- **New `design-craft` pack for interaction/visual designers (design-craft
  0.1.0).** An opt-in, user-scope pack of four pure-markdown skills —
  `aesthetic-direction` (turn a vague vibe into named, ranked goals),
  `design-system-foundations` (derive a token/scale taxonomy from intent),
  `layout-and-information-architecture` (hierarchy, reading flow, wayfinding as
  concepts), and `design-critique` (severity-rated heuristic evaluation) —
  plus a shared `quality-floor` checklist (handle all states, accessibility
  floor, "motion communicates state, honor reduced-motion"). Designers author
  the upstream **design intent** the build consumes, the design-side twin of
  `product-engineering`'s product-intent seam. Every skill is strictly
  framework-agnostic: it points to the recognized standards (WCAG, the W3C
  Design Tokens interchange shape) and ships the method to *derive* values,
  never a stack or a values table — enforced by a pack-scoped agnosticism lint
  wired into CI. No hooks, no engine, no in-pack validator, no reviewer
  subagent. Installs across all seven adapters; user-scope by default.

- **`decompose-intent` records the decomposition decision (product-engineering
  0.4.1).** When a cut drops or replaces a branch — most often after an upward
  `de-risk-intent` kill bubbles up — there was no instruction to record *why* on
  the parent, so a parent intent read as if its tree were always this shape and a
  later reader re-litigated branches already ruled out. A new procedure step (and
  an optional "Decomposition decisions" log in the intent template) asks for the
  grouping rationale plus any dropped/replaced branch, pointing to the killed
  child's verdict. This mirrors the de-risk trail, which already records why a bet
  was tested the way it was; a line or two per decision, omit if the cut was
  obvious. No new fields are required and the artifact stays a template, not a
  schema. (Pure-markdown; dependency-contract paths between siblings and
  confidence in a bet were audited and already covered by the business-unit
  provider/consumer projection and the survive/kill verdict respectively — no
  change there.)

- **`architect` ships a forked-context `design-reviewer` subagent (architect
  0.6.0, RFC-0032).** A read-only sibling of the `architect-review` skill: the
  same genre-routed verdict critique and well-architected risk register, with
  the same severity and mechanical/judgment tags — but run in an isolated
  context that hasn't seen the authoring, so it can't mark its own homework. It
  is the *fresh-context (preferred)* rung of `architect-design`'s convergence
  loop (which previously had only an in-thread skill and a weaker cold-re-read
  floor); its tools are `Read, Grep, Glob`, so it flags and never rewrites the
  design. The `architect-review` skill is unchanged and the two coexist. The
  convergence loop stays a soft dependency — it degrades gracefully when the
  subagent isn't installed. ADR-0023 records that the charter's "three reviewers
  is the ceiling" scopes the core code-review lenses, not opt-in design-side
  review.

- **`work-loop` makes "run it as a real user" first-class for non-UI tools (core 0.4.9).**
  The manual-QA verification mode was framed almost entirely around UI rendering
  and UX flows; it now explicitly covers any artifact a user invokes — a CLI, a
  library's public API, an agent or skill, a service endpoint. The doctrine:
  when a change ships something a user invokes, verification includes exercising
  the real built artifact end-to-end through its documented happy path and
  recording what you observed (real stdout/exit code, returned value, file
  written, on-screen result), not internal state or a unit gate standing in for
  the real invocation. Framed harness-agnostic like the EXECUTE simplify pass —
  done by hand on any agent, with Claude Code's native `/verify` and `/run` as
  an optional accelerant. The DECIDE end-of-session checklist gains a line that
  refuses "done" until that end-to-end exercise has happened. Existing
  UI-specific guidance is preserved as the UI instantiation of the general rule.

- **`architect-diagram` learns deliberate visual encoding (architect 0.5.3).**
  A new `references/visual-encoding.md` turns scattered correctness rules into
  one design heuristic: when a diagram distinguishes more than one category of
  thing or relationship, map each visual channel (shape, grouping, position,
  edge style, marker) to meaning *by the data type it carries*, rather than
  decorating arbitrarily. It names which channels are robust across enterprise
  wiki renderers versus fragile (colour, opacity) — colour is reinforcement,
  never the sole carrier — and notes honestly that Mermaid can't size nodes, so
  magnitude goes in a label. Mermaid-only; no rendering-library code. The draft
  step in the skill now loads it when a diagram carries more than one
  dimension.

- **`quality-engineer` catches two more test/edge-case shapes (core 0.4.8).**
  The tautological-tests finding now also flags a test that asserts on the
  mock's own configured return value (it can never fail, so it pins nothing),
  and the edge-case enumeration adds `permission-denied` and
  `resource-exhausted` to the cases the reviewer checks for.

- **The `architect-design` NFR lens gains a performance-budget optimization
  discipline (architect 0.5.2).** The "Performance and scale" checklist now
  asks for a performance budget committed up front (a latency, throughput, or
  resource target stated as a testable claim), and adds an "earn each
  optimization against the budget" prompt: measure before optimizing (no
  optimizing an unmeasured hotspot), spend effort on the hotspot where most of
  the cost sits, and weigh each optimization's ongoing complexity cost against
  the gain it actually buys. Framework- and stack-agnostic — no profiler or
  tool names. The optimization discipline was previously absent; budget-setting
  itself stays cross-linked to the existing quality-attribute-scenarios
  guidance rather than restated.

- **The `product-engineering` pack gains a content layer — `voice-and-microcopy`
  (product-engineering 0.4.0).** A fifth pure-markdown skill that turns shaped
  product intent into the **words a user reads** in the UI — the angle the pack's
  intent-shaping habits (`frame-intent`, `de-risk-intent`, `decompose-intent`)
  deliberately left open. The adopter characterizes their product's **voice**
  along a few axes (humor / formality / respect / enthusiasm) and records it in a
  travelling voice-chart template, writes the recurring UI states — **error,
  empty, button, label** — from blame-free, actionable formulas (each with a
  before/after), and runs a **content checklist** before copy ships. Voice is
  constant, tone flexes by context (calm in errors, warm in success). Fully
  framework-agnostic and habits-shaped — no engine, no schema, `SKILL.md` under
  100 lines with depth in `references/`. Distinct from the
  `house-voice-writing-craft` clear-prose rules, which shape *documentation*
  prose, not product UI copy.
- **The `bug-fix` skill gains two debugging-discipline moves (core 0.4.6).**
  A new "list candidate causes, then falsify each" step sits between
  reproduction and the root-cause assertion — name 2-3 rival causes and rule
  each in or out with Expected / Actual / Verdict, so you don't fixate on the
  first plausible cause. And a "Why wasn't it caught?" question joins the
  root-cause set, so the regression test closes a *named* coverage gap rather
  than only pinning the observed input. Both are language- and
  framework-agnostic. The renumbering shifts `bug-fix`'s tracker-loopback
  step from 8 to 9; the atlassian `jira-defect-flow` skill's references to it
  are updated to match (atlassian 0.1.4).

- **Spec and guide authoring skills teach two doc-writing disciplines: retcon
  writing and context poisoning (core 0.4.7, user-guide-diataxis 0.1.4).**
  *Retcon writing* — `new-spec` and `new-guide` now instruct authors to write
  spec/guide bodies in the present tense, as if the feature already exists and
  always worked this way: no "will be implemented", no "previously X, now Y", no
  deprecation timelines, no version-stamped history in the body (decision history
  stays in ADRs and the changelog). The rule lands as a failure-mode bullet in
  `new-spec` step 4, a guide-voice anti-pattern in `new-guide` step 4, a reminder
  in the `new-spec` `spec.md` template, and a `clear-prose.md` checklist item;
  `plan.md` is exempt, since it keeps its own changelog. *Context poisoning* —
  `new-spec` now names the failure mode its single-source-of-truth / drift-is-a-bug
  discipline prevents (an agent loading a stale, duplicated, or self-contradicting
  doc and deciding wrong from it) in one canonical place, tying the
  one-canonical-home rule and the retcon body together as the two halves of the
  defense.

- **`work-loop` gains a "Scale with a tool, not turns" technique for large,
  repetitive tasks (core 0.4.5).** When a task spans many similar items —
  applying one change across N files, transforming a large set, auditing every
  module — the skill now points you at writing a small enumeration script backed
  by a resumable tracking file (`progress.jsonl` or a checklist with per-item
  `pending`/`done`/`failed` state), so an idempotent re-run skips finished items
  and the loop reliably reaches 100% completion instead of stalling when context
  turns over. A short headline lands in the EXECUTE phase; the full playbook —
  tracking-file schema, idempotency, when to shell out to the agent per item, and
  keep-vs-delete the tool — is a new on-demand reference,
  `references/scale-with-a-tool.md`.

- **The research pack learns to preserve irreducible ambiguity instead of
  always collapsing to one rated answer (research 0.2.0).** Four skills gain a
  first-class way to hold a question open when the honest output is not a single
  verdict: `/identify-perspectives` adds a **tension map** recording, per
  irreducible disagreement, the conditions under which each camp holds and what
  a forced resolution would destroy; `/devils-advocate` adds a **do-not-resolve
  verdict** for productive tensions where both sides are well-evidenced under
  different conditions, distinct from its confidence-downgrade; `/research` adds
  a first-class **known-unknowns / unknowables** gap section, distinct from
  rating a weak finding `[uncertain]`; and `/decision-archaeology` adds a
  **revival check** that flags a rejected alternative whose original rejection
  rationale no longer holds because a constraint changed. Each is additive — no
  existing schema field or downstream contract changes.

- **The rest of the catalogue-internal references are swept from shipped
  content (core 0.4.4, figma 0.1.3).** Following the first pass, the remaining
  `make build-*` build-target mentions, an internal RFC citation, and the "this
  catalogue" identity asides are removed from the work-loop and receive-brief
  skill scripts, the session-start hook, the `pre-pr` hook, and the
  adapt-to-project reference; figma's exit-code test drops a dangling internal-RFC
  comment. Comment, docstring, and prose only — no behavior change.
  (`credential-brokers`, which is frozen, is left for a separate pass.)

- **Shipped pack content sheds catalogue-internal references (core 0.4.3,
  atlassian 0.1.3).** The `conventions-check` command no longer instructs
  running this repo's own `tools/lint-*` scripts — which never install into an
  adopter tree — and is reframed as checks you (or your own linters) perform
  directly. The `jira` skill's error-handling guidance drops a `make
  build-self` remediation hint in favour of "reinstall the pack", and four
  shipped atlassian test scripts drop dangling internal-RFC comment citations.

- **`make build-self` no longer litters the tree with by-quadrant guide
  scaffolds.** Self-host projection skips `docs/guides/**`: guides are
  repo-owned and reach adopters through install-time seed delivery, so a repo
  that organizes its guides by pack no longer gets untracked
  `docs/guides/{tutorials,how-to,reference,explanation}/README.md` re-created
  on every build.

- **`new-guide` now coaches prose, not just structure (user-guide-diataxis
  0.1.3).** The skill ships a `clear-prose` checklist. It names the tells that
  make docs read machine-made (hedges, uniform sentence rhythm, em-dash
  overuse, throat-clearing openers, inflated verbs) and the habits that keep
  them human (one claim per sentence, concrete over abstract, strong verbs,
  omit needless words). The voice section points to it. An optional copyedit
  pass hands the draft to a read-only subagent when one is available.

- **A guide home for every pack, and real guides for the packs that lacked
  them (ADR-0020).** `docs/guides/` is reorganized from flat Diátaxis quadrants
  to a per-pack hierarchy — `docs/guides/<pack>/{tutorials,how-to,reference,explanation}/`
  for each pack, `docs/guides/_shared/` for cross-cutting topics (install routes,
  the adapter support matrix, the catalogue model, authoring a skill). All 12
  packs now have a guide home reachable from `[pack.links].documentation` and a
  "go deeper →" link from the pack README, and the README catalogue points each
  pack at its guides. The seven previously-undocumented packs (`atlassian`,
  `contracts`, `converters`, `figma`, `governance-extras`, `monorepo-extras`,
  `user-guide-diataxis`) gained full Diátaxis guides; `architect` gained diagram
  and review how-tos; flow-heavy guides carry ASCII diagrams; and `core`'s
  explanation now leads with *why loop engineering*. The adopter-facing
  `user-guide-diataxis` seed scaffold stays organized by quadrant; the
  `new-guide` skill is layout-aware (user-guide-diataxis 0.1.2). Every pack's
  version is bumped for the new `documentation` link.

- **`architect-design` now consults the enterprise's own knowledge when the
  environment exposes a retrieval surface (architect pack 0.3.0).** A new
  progressive-disclosure reference (`knowledge-surfaces.md`) carries an 8-area
  MECE knowledge taxonomy — business domain, current landscape, interfaces,
  operational reality, constraints & standards, patterns, decisions, in-flight —
  plus a **harness-agnostic detection** mechanism that discovers a retrieval
  surface (an MCP knowledge tool, an internal CLI, an in-repo doc set) from the
  session itself, hardcoding no tool name. A single conditional procedure step
  loads the reference **only when a surface is detected**, and otherwise
  **degrades gracefully** — asks for the missing context, lowers confidence, and
  never fabricates landscape/standards/in-flight facts — reusing the existing
  compose-with-`research` framing. No knowledge server or RAG engine ships (out
  of charter); no registry, shared config, or cross-pack dependency.
  The `architect-review`, `architect-diagram`, and `product-engineering`
  siblings have all since shipped (see below) — the line is complete.

- **`architect-review` now checks that a design was grounded in the enterprise's
  own knowledge (architect pack 0.4.0).** The review-side counterpart of the
  `architect-design` awareness above: a duplicated, **verification-lens**
  `knowledge-surfaces.md` reuses the same 8-area MECE taxonomy as a checklist —
  *is this area's claim grounded?* — and one conditional procedure step flags any
  landscape / standards / in-flight / interface claim asserted as fact without
  grounding (no cited surface and no "unverified — confirm" marker), plus any
  available knowledge surface the design ignored. It **does not redesign** and
  **does not consult surfaces to author a better answer** — if an internal
  surface is reachable it may spot-check the claims (naming what it checked
  against, or "none"); if not, it flags them for the author to confirm rather
  than guessing, and never fabricates a "ground truth" to judge against.
  Harness-agnostic detection (no hardcoded tools, public web excluded); no
  registry, shared config, or cross-pack/cross-skill dependency. The
  `architect-diagram` and `product-engineering` siblings have since shipped (see
  below).

- **`architect-diagram` now consults the enterprise's own knowledge to draw an
  accurate as-is diagram (architect pack 0.5.0).** The third and final
  architect-skill sibling of the awareness above, with a deliberately different
  lens: in **document** and **update** mode only, when the as-is system
  integrates beyond the repo boundary and a retrieval surface is reachable, a
  duplicated **as-is-drawing-lens**
  `knowledge-surfaces.md` extends "read the repo" to "read the landscape" — so the
  boxes, arrows, and edge labels beyond the repo boundary are grounded from the
  **descriptive current-system facets** (current landscape, interfaces,
  operational reality — areas 2/3/4) instead of guessed. It reuses the same 8-area
  MECE canonical core (kept byte-identical across all three copies; only the
  trigger column, lens paragraph, and detection/degrade framing change) and one
  conditional procedure step. **Mode-scoped:** it does **not** fire in design mode
  (the user's hypothetical — fabrication is allowed-but-flagged) or review mode
  (routes to `architect-review`). Harness-agnostic detection (no hardcoded tools,
  public web excluded); three honesty rails recast for drawing — name what you
  drew from, leave an ungroundable node `<unnamed>` or ask rather than guess, flag
  a surface-derived edge the repo contradicts rather than drawing over it —
  strengthening the skill's standing never-fabricate-names discipline. No
  registry, shared config, or cross-pack/cross-skill dependency. `architect-design`
  and `architect-review` are unchanged. The new copy is **registered in
  `tools/lint-knowledge-surface-parity.py`** (the drift guard shipped alongside
  the `product-engineering` sibling, extended here + its self-test) so the
  canonical core is mechanically guarded. This **completes the
  knowledge-surface line** — all three architect skills plus the
  `product-engineering` sibling now ship it.

- **The `product-engineering` pack gains its business-unit cross-component layer
  (pack 0.2.0).** A product org whose work fans out across **many component
  repos** can now stand up a **value-stream meta-repo** — a coordinating repo with
  no app code — via a new pure-markdown skill, **`align-value-stream`**. It holds
  the cross-cutting artifacts a polyrepo has nowhere else to put: a **federated
  Backstage catalog** (Domain→System→Component→API, referencing each repo's own
  `catalog-info.yaml`, never re-authored), the **shared-contract authority**
  (referenced by `contract@version` with a read-only courier snapshot, never
  forked), the **C4/bounded-context architecture**, and a **cross-component
  delivery rollup**. At business-unit scale `decompose-intent` now **slices a
  feature intent per component** into one `core` brief per repo, each carrying an
  optional **`parent-intent:`** provenance pointer (the one additive, never-
  interpreted `core` brief field, distinct from `Epic:`), a versioned contract
  reference, and a `providesApi`/`consumesApi` role; each brief crosses into its
  component repo where `receive-brief` → `new-spec` → `work-loop` take over, and
  the meta-repo rolls up "delivered across **all** components?" The rollup is a
  **markdown snapshot** (absent-source rows show `unknown / not-yet-catalogued`,
  never silently delivered) — **no runtime hub, no live API, no validator, no new
  subagent**. The hard limits are stated honestly: **no atomic cross-repo commit,
  no shared release train, snapshot-not-live**. Habits, not infrastructure
  (RFC-0030 phase 2, ADR-0022).

- **`frame-intent` now consults the enterprise's own knowledge through a
  problem-framing lens when the environment exposes a retrieval surface
  (product-engineering pack 0.3.0).** The product-engineering counterpart of the
  `architect-design` awareness above — same mechanism, different lens. A new
  progressive-disclosure reference (`frame-intent/references/knowledge-surfaces.md`)
  carries a **strict four-area subset** of architect's taxonomy — business domain
  & meaning and in-flight & roadmap (both primary), current landscape
  (brownfield-only), and operational reality (light) — and **deliberately omits**
  the four solution-design areas (interfaces, standards, patterns, decisions) so
  framing stays in problem space. The same **harness-agnostic detection** (no
  hardcoded tool name) and three honesty rails apply; a single conditional step
  loads the reference **only when a surface is detected** and otherwise
  **degrades gracefully** — asks for the missing domain/in-flight context, lowers
  confidence into the intent's `Assumptions`, and never fabricates. The
  current-landscape area wires into `frame-intent`'s existing brownfield maturity
  gate. A shared-canonical-core anchor names the architect reference as canonical
  so the copies don't diverge. The detection audit home ("name what you detected,
  or 'none detected'") is pinned to a fixed slot in the intent template's
  `## Assumptions` and — symmetrically — in `architect-design`'s Stage-0
  `concept.md` (bumping the architect pack `0.4.1 → 0.4.2`). A new stdlib
  `tools/lint-knowledge-surface-parity.py` CI gate guards **every copy** of the
  shared taxonomy core — `architect-design` (canonical), `architect-review`, and
  `frame-intent` — against silent drift. No knowledge server or RAG engine, no
  registry, shared config, or cross-pack dependency.

- **`pack.toml` is now the rich source of truth for pack metadata, projected
  into every catalogue listing (adapter contract → 0.14).** Packs can declare
  `license`, `display_name`, `[[pack.maintainers]]`, `[pack.links]`
  (homepage/repository/documentation/changelog/issues/icon), `categories` and
  `keywords` (each capped at 5), an opaque `[pack.metadata.<tool>]` table, and a
  `readme` pointer — all optional, so packs that omit them build and validate
  exactly as before. The build projects the cleanly-mappable subset (author ←
  first maintainer, `category` ← first category, `displayName`, plus
  license/keywords/homepage/repository) — and each pack's `README.md` — into the
  claude-plugins and APM routes' `plugin.json` / aggregated `marketplace.json`
  entry, so a pack is described richly rather than with a single sentence.
  `categories` is a **soft vocabulary**: an unknown slug warns (exit 0), never
  fails. `agentbundle list-packs` renders a pack's canonical identity as
  `@<catalogue>/<pack>` when `[pack].catalogue` is set (declare-only — no
  resolution change). **All 12 shipped packs** now declare the enriched metadata
  and bump a patch version. (RFC-0031, ADR-0021; the per-pack guide-home
  `documentation` links and the `docs/guides/` per-pack reorg land in a
  follow-on, ADR-0020.) As part of the same sweep, `product-engineering`'s
  intent/rollup templates moved from repo-scaffolding `seeds/` into the owning
  skills' `assets/` (so the pack carries no `seeds/` and stays user-scope).

- **A new opt-in `product-engineering` pack shapes product intent into the specs
  your delivery loop already builds (pack 0.1.0).** Three pure-markdown skills —
  `frame-intent`, `de-risk-intent`, `decompose-intent` — work a recursive,
  level-tagged `intent` (a capability intent and a feature intent are the same
  artifact at different levels; a PRD is a feature intent written as a document).
  Name an outcome and the opportunity behind it, de-risk the riskiest assumption
  against a **predeclared kill condition** under a choosable **prototype-approach**
  (`prototype-led` ↔ `validate-first`), then decompose to a shippable spec — at app
  scale the leaf *is* a `core` brief, so `receive-brief` → `new-spec` → `work-loop`
  take it from there with **no change to `core`**. One global **Scale** axis (app ↔
  business-unit) plus per-intent maturity / reversibility / prototype-approach flags;
  one-way tracker projection (Linear / Jira Align / none); habits, not infrastructure.
  v1 is app/solo + single-component; the business-unit cross-component value-stream
  layer is a later phase (RFC-0030, ADR-0019).

- **The `architect` pack designs *and* reviews cloud architecture to the
  well-architected standard, and the design skill now converges (architect pack
  0.2.0).** `architect-design` shapes a one-page **concept first**, makes the
  design **well-architected by construction** for the chosen provider — AWS /
  Azure / GCP, **primitives providers like Hetzner** (it names the capability
  gaps you must build yourself), or **local-first** (the local→production delta +
  graduation path) — and then runs a **convergence loop**: it obtains a review
  pass, **auto-resolves the mechanical findings** without asking, re-reviews, and
  **surfaces only the judgment calls** (tradeoffs, risk acceptances,
  low-confidence assumptions) to you as decisions. `architect-review` gains a
  **well-architected / lens mode** (security · FinOps · SRE · DR · data ·
  compliance · green concern-lenses, plus ML / **GenAI-agentic** / SaaS /
  serverless workload-class lenses) that emits a risk register with every finding
  tagged **mechanical / judgment** — the signal the design loop consumes. The
  loop is an enhancement when both skills are present and degrades to an embedded
  rubric self-check when it isn't; for genuinely novel domains the design takes a
  **leading-edge path** that composes with the `research` skill when available and
  degrades to flagged-novelty + lowered-confidence when absent. Pure-markdown, no
  subagents, no new pack; the loop is an in-conversation procedure with no script
  or state file. `architect-diagram` gains a `cloud-primitives` diagram vocab for
  parity with its AWS/Azure/GCP references.
- **The `security-reviewer` is stronger, current, and shifts left (core pack 0.4.0).**
  Security review is no longer only a late gate: on security-boundary work the
  `work-loop` now dispatches the reviewer in a **spec-stage secure-design mode**
  at the pre-EXECUTE step, asking whether each control is specified as an
  acceptance criterion *at the right depth* (confinement, not just traversal;
  a scheme/host allowlist, not "validate the URL"; broker-mediated secrets, not
  ad-hoc reads) — collapsing post-implementation round-trips into one design-time
  pass. The awareness stack is current — **OWASP Top 10:2025** (replacing the
  2021 list), ASVS 5.0, API Security Top 10:2023, OWASP LLM Top 10:2025, CWE
  Top 25 — and a **STRIDE + LINDDUN** open pass adds the privacy lens STRIDE
  blind-spots. Depth ships through a new **`security-checklists` skill**: ten
  boundary-keyed modules the orchestrator loads *per boundary the change
  crosses* and inlines into the reviewer's brief, so the lens is deep without
  bloating the prompt and travels to every adapter with **no contract change**.
  Tool-delegation is now language-agnostic (`npm audit` / `pip-audit` /
  `govulncheck` / `cargo audit` / Snyk / Semgrep / CodeQL) and fails honestly
  (`degraded: no scanner`) rather than silently skipping. A new **established-helper
  bypass** meta-check flags code that rolled its own where the repo has a blessed
  helper — customize the list via a light "blessed security tools/helpers" point
  in `AGENTS.md`. Complements, does not replace, the SAST/SCA scanners (ADR-0017).
  See RFC-0029 / ADR-0018.

- **The default quality floor is now higher by doctrine (core pack 0.3.0).**
  Agent output tends to clear a strict external static-analysis gate (a
  SonarQube quality profile, a CI-only coverage threshold) regardless of tech
  stack, without bundling any linter, shipping any threshold, or detecting the
  repo's shape. Three coordinated, stack-agnostic changes: (1) the
  `quality-engineer` reviewer gains four universal code-smell findings —
  bounded complexity (split what's *reducible*, complementing the existing
  comment-the-irreducible finding), nesting depth (idiom-appropriate
  flattening, not a mandated early `return`), duplicated production blocks past
  the rule-of-three (tests stay DAMP), and magic-literals/parameter-bloat
  (judgment-based, threshold-free) — plus a mutation-testing-mindset Test
  Design headline ("a test must be able to fail") as the Goodhart-safe stand-in
  for chasing a coverage number; (2) `work-loop` gains a **simplify pass** in
  EXECUTE/REVIEW that shrinks the diff before review — harness-agnostic
  doctrine, with Claude Code's `/simplify` an optional accelerant, never a
  dependency; and (3) light mode now **retains** the `quality-engineer` pass
  when the adopter declares in their `AGENTS.md` that the repo is judged by a
  strict external gate the local loop can't run (adopter-declared policy, not
  repo detection). Mode *mechanics* begin migrating out of `CONVENTIONS.md`
  into the `work-loop` skill as their single owner.

- **The repo now has a SAST/SCA gate** — `make sast` runs **Bandit** (Python pattern SAST),
  **pip-audit** (dependency/SCA), **Semgrep** (cross-cutting SAST, including custom `mode: taint`
  rules under `tools/semgrep/`), and a **CodeQL** code-scanning workflow (deep interprocedural
  taint — the open-source analogue of Snyk Code). The first three are chained into
  `make build-check` so every PR is scanned by the repo's own single native gate (locally and in
  `build-check.yml` CI); CodeQL runs as its own workflow. Bandit fails on medium-or-higher findings
  (tuning in `bandit.yaml`). The genuine findings surfaced were fixed in the same change: weak SHA-1
  digests marked `usedforsecurity=False`; the arXiv retriever upgraded to HTTPS; the `session-start`
  hook's env-var path overrides sanitized against directory traversal (a fix every adopter inherits);
  and the SSO broker's `test` verb now rejects non-`http(s)` URL schemes. A committed `.snyk` policy
  file is the Snyk-native suppression vehicle for the organisational scan. All four scanners are
  CI-only dev tools (`tools/requirements-sast.txt`) and are **never** added to a shipped package's
  runtime dependencies. See ADR-0017.

- **Gemini CLI is now a full-parity adapter** — `agentbundle install --adapter gemini` (repo or
  user scope) projects every catalogue primitive to Gemini CLI's native `.gemini/*` layout:
  skills → `.gemini/skills/`, subagents → `.gemini/agents/<name>.md` (the `tools:` allowlist is
  **kept** and name-mapped to Gemini's tool ids — `Read`→`read_file`, `Bash`→`run_shell_command`,
  … — and `model` maps tier-preserving to the Gemini 2.5 line), commands →
  `.gemini/commands/<name>.toml`, and hook bodies → `.gemini/hooks/` with the wiring + a managed
  `context.fileName = ["AGENTS.md", "GEMINI.md"]` bridge merged into `.gemini/settings.json` so the
  canonical `AGENTS.md` is read. Every pack admits `gemini` at both scopes. Previously Gemini CLI
  got nothing (it doesn't read `AGENTS.md` by default). Contract v0.12 → v0.13 (RFC-0027 /
  ADR-0016). Distribution-only.
- **Cursor can now install the `research` and `architect` packs** — both packs added `cursor`
  to their `allowed-adapters`, so `agentbundle install --pack research --adapter cursor` (and
  `--pack architect`) now projects their skills to `.cursor/skills/` — and, for `research`, the
  two retrieval subagents to `.cursor/agents/` with `readonly: true` — instead of refusing the
  install up front. The Cursor adapter shipped in the previous release, but no pack had opted
  in. (The credentialed packs are covered by the next entry.)
- **Credentialed packs can now install via Cursor and Copilot** — `atlassian`, `contracts`,
  `converters`, `figma`, and `credential-brokers` added `copilot` + `cursor` to their
  `allowed-adapters`, so a Cursor- or Copilot-based adopter can install them (and the SSO/token
  broker lands at `~/.agentbundle/bin/` as before — the broker delivery is adapter-independent).
  Previously these packs admitted only `claude-code`, `kiro-ide`, and `codex`. Recorded as an
  RFC-0013 § Errata decision; no contract change (both adapters already declare the
  `.agentbundle/` install prefix the broker needs).
- **`--dry-run` previews an install or upgrade without writing anything** —
  `agentbundle install --dry-run` and `agentbundle upgrade --dry-run` run the
  full read-only pre-flight, print a per-file plan to stdout (one
  `<action> <tier> <target>` line each — `create` / `overwrite` /
  `companion`, with Tier-2 lines naming the `.upstream.<ext>` companion the
  real run would drop), and exit 0 without touching the tree, state, or
  install marker. A present Tier-2 collision does not change the exit code;
  the preview is informational. `install --dry-run --force` is refused
  (`--force`'s destructive cleanup is incompatible with a read-only preview).
  The install preview covers the rendered adapter projection; it does not yet
  enumerate the governance seeds (`AGENTS.md`, `docs/CHARTER.md`,
  `docs/CONVENTIONS.md`) a real install also delivers. See the
  [preview how-to](../guides/_shared/how-to/preview-install-or-upgrade.md).

### Changed

- **`agentbundle upgrade` tells you when it keeps your edits** — when a
  projected file you edited since install collides with the new version
  (Tier-2), the upgrade preserves your file and drops the upstream version
  as a `<path>.upstream.<ext>` companion, exactly as before. It now also
  prints, on stderr after the upgrade commits, how many files were kept
  and the companion path of each — so you can find them and run
  `adapt-to-project` to merge. Parity with what `install` already reports;
  no change to the file-safety contract (the CLI still never clobbers or
  prompts). Per
  [RFC-0001 § Errata (2026-06-11)](../rfc/0001-bundle-distribution-by-adapter-spec.md#errata),
  which reconciles the original draft's unbuilt in-CLI Tier-2 prompt with
  this deterministic companion-drop design.

- **Leaner work-loop context use, same rigor** — the review reviewers
  (`adversarial-reviewer`, `security-reviewer`, `quality-engineer`) now return
  only their distilled findings block (or `Clean — ready to commit.`), with no
  pre-findings methodology recap or process narration. The `work-loop` skill
  drops the full reviewer report from resident context once findings are
  recorded — the on-disk report plus `state.json` fingerprints are the durable
  record — and gains a `## Context hygiene` section with three context-saving
  levers (reference-read reduction, task-boundary compaction, narrowest-gate
  during FIX), each with a portable no-subagent floor, plus a "reduce, never
  lossily transform" guardrail. No verification surface changes: gates, the
  iterate-to-Clean loop, fingerprint stasis detection, the quality-engineer
  floor, and the iteration cap all behave exactly as before. See
  [`docs/specs/work-loop-context-hygiene/`](../specs/work-loop-context-hygiene/spec.md).

- **Codex receives full skill bodies** — the `skill` projection for the
  Codex adapter flips from `managed-block-inline` (one-line teasers
  in `AGENTS.md` between `<!-- agent-skills:start -->` /
  `<!-- agent-skills:end -->`) to `direct-directory`. Codex users now
  read `.agents/skills/<name>/SKILL.md` byte-equal to source — the
  same surface Claude Code and Kiro have always had. Per
  [RFC-0009 § Adapter contract change](../rfc/0009-codex-native-skills.md#adapter-contract-change).
  On the first install after upgrade, the adapter strips the
  legacy `<!-- agent-skills:start --> … <!-- agent-skills:end -->`
  region from any pre-existing `AGENTS.md` in place; outside-block
  content is preserved. The strip is destructive by design: hand-
  edited content *between* the delimiters is not migrated
  (RFC-0009 § Failure modes). The strip mechanism
  (`_strip_legacy_skill_block` + the retained `_splice_managed_block`
  helper) is kept for one minor release as the migration window
  (released N) and then removed in the release after (N+1).
  **Self-host mirrors Codex repo projection.** The self-host allow-list
  includes both `claude-code` and `codex`, so this repo now carries
  Codex's repo-scope projection alongside Claude Code: `.agents/skills/`
  for full skill bodies, `.codex/agents/` for subagent TOML, and
  `.codex/hooks.json` for hook wiring. `make build-check` enforces those
  paths the same way it enforces `.claude/`.

- **Uniform multi-pack entry point across `direct-directory` adapters**
  — `codex`, `claude-code`, and `kiro` all expose
  `project_packs(pack_paths, contract, output_root)` as the
  canonical orchestrator-facing surface. Single-pack `project()`
  is retained as a wrapper. Same-name skill collisions across
  packs resolve deterministic-last-wins by source-order.

- **Orphan-skill cleanup across `direct-directory` adapters** — after
  every multi-pack `project_packs(...)` call, the projected skill
  directory is swept: child directories whose names are not in the
  union of source skill names across the call's pack list are
  removed. Bound to the `skill` primitive only; symlinks are
  removed via `Path.unlink()` (never followed).

### Deprecated

- (nothing yet)

### Removed

- (nothing yet)

### Fixed

- (nothing yet)

### Security

- (nothing yet)

<!--
## [1.0.0] — YYYY-MM-DD

### Added
- Initial public release.

[Unreleased]: https://github.com/<org>/<repo>/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/<org>/<repo>/releases/tag/v1.0.0
-->
