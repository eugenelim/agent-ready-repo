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

### Added

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
