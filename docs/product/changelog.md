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

### Changed

- **`voice-and-microcopy` renamed to `ux-writing` in the `product-engineering` pack (0.13.0).** The skill name now reflects its function — writing the words users read — rather than its category. Pack page, journey pages, how-to guides, and cross-pack references (experience-design, product-strategy) are updated throughout. ADR-0038 alias-free precedent applied: no install-time alias. ([spec](../specs/product-engineering-shaping-doctrine/spec.md))

- **`place-bet` skill requires four new fields: `thin-slice`, `first-success-event`, `specialist-lenses`, and `learning-contract` (product-engineering pack 0.13.0).** The thin-slice field enforces the four-criterion definition — one user, one real task, one meaningful result, one material failure and recovery, plus a named instrumentation event. `first-success-event` names what "adopted" looks like for one user 30 days out. `specialist-lenses` defaults to product, experience, architecture, safety. `learning-contract` requires signals, review cadence, and a pivot trigger. Three anti-patterns added: betting without a thin slice, first-success-free briefs, and blank learning contracts. ([spec](../specs/product-engineering-shaping-doctrine/spec.md))

- **`de-risk-intent` skill gains evidence ladder (product-engineering pack 0.13.0).** Assumptions are now classified on a five-level evidence ladder: `observed | supported | inferred | assumed | unknown`. Step 2 instructs testing from the lowest rung first — `unknown` before `assumed`, `assumed` before `inferred`. The `validation_hook` output template gains an `evidence_level` field. ([spec](../specs/product-engineering-shaping-doctrine/spec.md))


### Changed

- **`jira-team-status` and `jira-story-triage` reshaped to activate from natural team language (atlassian pack 0.6.0).** Both skills now trigger from the words delivery leads and POs actually use — no need to name the skill. `jira-team-status` is a read-only status view organized by the dimensions people ask about (Ready to pull · In progress · Blocked · Unassigned · Needs detail, plus recently-changed and stale markers), answering "what can the team pick up next?", "what is blocked?", "what is sitting unassigned?", "what changed in this sprint?", and "team status for stand-up". "Ready to pull" is now a documented, team-overridable rule — in the selected scope + an eligible backlog state (default `statusCategory = "To Do"`) + no known blocker + meets the five-question readiness bar — and signals it can't read are labelled "needs confirmation" rather than asserted. `jira-story-triage` now explains *why* each item is not ready (which question failed and the specific gap, not a bare tier label) and can improve weak items — draft acceptance criteria, clarify the outcome — writing back via `update-issue` only after per-item approval. The write/improvement path moved from `jira-team-status` (now read-only by default, routing "shape this" to triage) into `jira-story-triage`. The five-question bar remains the shared engine; "agent-readiness / Tier A/B/C" is retired as the headline framing. ([spec](../specs/jira-activation-reframe/spec.md))

- **`new-guide` skill broadened to create or substantially revise guides (user-guide-diataxis 0.2.0).** The skill now triggers on rewrite, audit, simplify, and modernize requests in addition to new-guide creation — covering pack pages and journey pages alongside the four Diátaxis quadrants. The audience contract is replaced by a seven-field conversation contract (reader, job, natural_start, minimum_scope, first_result, write_boundary, next_request) as the gated checkpoint before any prose is drafted. Per-page-type contracts for all six surface types now live in a dedicated `references/page-contracts.md`. Three new reference files ship with the skill: `conversation-first.md` (sequencing rules), `page-contracts.md` (six surface contracts), and `usability-review.md` (pre-publish checklist). `clear-prose.md` gains a `## Conversation-first structure` section with eight page-level structural rules. Evals updated with revise/audit trigger cases and a conversation-first output-quality rubric. Key doctrine: *Diátaxis determines where information lives. User intent determines how readers enter it.* ([spec](../specs/new-guide-conversation-first/spec.md))

### Added

- **Story quality gate on `jira: create-issue` (atlassian pack 0.5.0).** The `jira` skill now runs a pre-create quality gate before every `create-issue` call: it detects the invocation repo via `git remote -v` ("Invocation repo" label), then checks the candidate story against the five-question actionability bar (self-contained change, reachable repo scope, binary ACs, no mid-flight decision, right-sized for one PR — Q5 added because Jira stories are a legacy capacity-allocation mechanism and oversized stories cannot be handed to a single agent or engineer). Six concrete checks with story-points as the primary Q5 signal. Gate fires on `create-issue` only; `update-issue` is unaffected. ([spec](../specs/jira-story-actionability/spec.md))

- **`jira-story-triage` skill (atlassian pack 0.5.0).** Audits a Jira backlog, sprint, or JQL-scoped set of stories for agent-readiness. Scores each story against the five-question actionability bar, applies a Blocked pre-check (image-only descriptions and discovery issuetypes short-circuit before Q1–Q5), classifies into Tier A (all five pass), B (exactly one named external gate fails), or C (any content failure or Q5 fail), then groups Tier A by complexity: Quick (≤ 2pts or ≤ 100 words), Standard (3–5pts), Involved (> 5pts). Read-only; composes `jira` for all reads. ([spec](../specs/jira-story-actionability/spec.md))

- **`jira-team-status` skill (atlassian pack 0.5.0).** Session-entry-point for sprint planning and daily coordination — modelled on the `workspace-status` pattern. Shows a scored sprint snapshot in four sections (§1 Agent-ready grouped by Quick/Standard/Involved, §2 Parallel batching candidates, §3 Gated, §4 Needs shaping), then offers a pick-up hand-off: Option A routes delivery to `jira-defect-flow` (bugs) or `new-spec` (tasks/stories); Option B shapes a blocked story collaboratively and calls `update-issue` once with explicit user consent. No reference to local workspace files or workspace.toml — completely separate from local queue management. ([spec](../specs/jira-story-actionability/spec.md))

### Changed

- **`capture-work` captures machine-readable dependencies for backlog items (core pack 0.13.7).** When a `[backlog]` entry's unblock condition is the completion of another tracked item (a `[backlog]` slug or a `[work]` spec) as a hard prerequisite, `capture-work` now adds the matching `needs` edge instead of recording the dependency in prose only — so `workspace-status` can resolve it. Disjunctive ("A or B"), untracked-target, and external ("credentials provisioned", "someone takes the PR") unblocks deliberately stay prose. The `workspace.toml` seed and `[backlog]` schema header now state the same rule.

### Added

- **First-value handoff block in `agentbundle install` (agentbundle 0.12.0).** A successful `agentbundle install` now prints a guidance block after the `installed:` line. Level B packs (non-technical audience, `level-b = true`) show four labelled lines — `Verify:`, `Try:`, `Expected:`, and optionally `Next:` — drawn from the pack's `[pack.first-value]` schema. Level A packs show `Verify:` only. Packs without `[pack.first-value]` are unchanged. Dry-run, upgrade, and profile-install paths are not affected. ([RFC-0064 Amendment #4](../rfc/0064-ini-001-ai-native-ecosystem.md) · [spec](../specs/agentbundle-first-value-handoff/spec.md))

- **`workspace.toml` seed (core pack 0.13.6).** `agentbundle install core` now
  delivers a minimal `workspace.toml` — schema comments and a `[backlog]` section
  — so the file exists from day one. Closes the gap where the installed
  CONVENTIONS.md references `workspace.toml [backlog].open` but install never
  created the file. The workspace-status "offer to initialise" path remains the
  upgrade tool for adding the full initiative schema. ([RFC-0069](../rfc/0069-workspace-toml-adopter-seeding.md))

- **Tracker intake guides — decision tree + vocabulary mapping table.** Adds two
  cross-cutting guides in `docs/guides/_shared/`: `choose-a-tracker-integration.md`
  (decision table and per-tracker sections covering GitHub `github-brief-intake`,
  Linear `linear-brief-intake`, Jira `jira-brief-intake`, Jira Align
  `jira-align-brief-intake`, and the no-tracker `author-brief` path) and
  `tracker-vocabulary.md` (cross-tracker object-level mapping table + brief-intake
  skill routing table). P4 guide slice for the RFC-0064 tracker intake phase.
  ([spec](../specs/m5-tracker-guides/spec.md))

- **governance-extras 0.8.2 — first-session tutorial (preview-confirm write pilot).** Adds `docs/guides/governance-extras/tutorials/governance-extras-first-session.md`: a step-by-step walkthrough of the `new-adr` preview-confirm write gate — decision framing, ADR content preview, target path preview, confirm/stop/revise, recovery, and next actions. Adds `tutorial` field to `[pack.first-value]` in `pack.toml`. Completes the `portfolio-first-run-pilot-governance-extras` pilot (RFC-0064 Amendment #4 preview-confirm write archetype).
- **`architect-first-session.md` first-session tutorial (architect pack 0.13.3).** First-value guided tutorial for the no-terminal architecture path; wires the `tutorial` pointer in the pack's first-value contract. Covers install verification, verbatim starter-prompt, expected-result (`docs/architecture/reference.md`), recovery, and next action. Pilot transcript confirms the path works via direct model reasoning (no skill required for the starter-prompt).

- **`jira-align-brief-intake` skill (atlassian pack 0.4.0).** Turns a Jira Align Feature into a product brief and shippable specs: fetches the Feature and its child stories, tasks, and defects via the `jira-align` skill, maps them onto a Shape B product brief using a configuration-guided field mapping reference (customised for org-specific workflow state names and Program Increment cadences), and hands off to `receive-brief` to elicit gaps, decompose, and build. 1-way intake only — never writes to Jira Align. Mirrors the `jira-brief-intake` choreography pattern for Jira Align's program-level delivery unit. ([RFC-0064 M5](../rfc/0064-ini-001-ai-native-ecosystem.md))
- **New `github` pack (v0.1.0) with `github-brief-intake` skill.** Pull a GitHub Milestone and its issues via the `gh` CLI, map them to a Shape B product brief (milestone title → Outcome draft; open and closed issues → `US-n (#NNN)` stories, closed issues annotated `[closed]`; milestone URL → `Epic:` provenance pointer), write the brief to `docs/product/briefs/<slug>.md`, and hand off to `receive-brief`. Three-way auth model: authenticated → proceed; unauthenticated + public repo → note posture and continue; unauthenticated + 404 → ambiguous message (private and nonexistent repos are indistinguishable). Graceful degradation when `receive-brief` is absent. Optional post-intake write-back (comment / label / close — never body edits). Ships with a Diátaxis how-to guide. ([spec](../specs/m5-github-brief-intake/spec.md))

- **`figma` pack (0.1.6) — first-run tutorial for the credentialed read-only archetype.** Adds `docs/guides/figma/tutorials/figma-first-session.md`: a step-by-step tutorial for non-technical designers to reach their first visible result (page and frame structure from a Figma file they own). The tutorial covers `credential-brokers` prerequisite install, user-initiated credential setup via the `credential-setup` skill (token entered at the terminal `getpass` prompt, never in chat), connection verification via `figma check` + `figma whoami`, and the starter task. Corrects a factual error in the pack's `[pack.first-value]` `verification` field (workspace-listing was not a real capability; corrected to `check`/`whoami` path). Adds the `tutorial` field to `[pack.first-value]`, making the contract independently verifiable. ([spec](../specs/portfolio-first-run-pilot-figma/spec.md))

- **architect 0.14.0 — Stage-0 concept stop point + adopter front-door fixes.** `architect-design` now treats the Stage-0 concept as a valid stopping point: you can save the concept on its own (or stop at chat) without proceeding to the full design doc, and the skill ends with a Stage-0 completion receipt — either `Result: chat only; no file was created.` or the exact saved path and what it contains. The README leads with plain outcomes (shape a concept / draw a system / review an architecture) before internal vocabulary, adds a surface-aware route cue, corrects the install example to `agentbundle install --pack architect <catalogue>` (the bare `install architect` form the current parser rejects), and lists the correct adapter names. Adds a regression test locking the README's documented install commands to the live CLI parser. (RFC-0064 Amendment #4 adopter-persona mechanical fixes.)

- **figma 0.2.0 — render completion receipt + credential source-of-truth fix + front-door prerequisites.** Every `export-images` render now ends with a mandatory receipt: source frame, exact local output path, format, skipped/lower-fidelity warnings, and `No Figma changes made`. The SKILL's credential-resolver reference is corrected from the stale `credentials_shim` to the standalone `credbroker` library (matching the live client), and the shared pack-catalogue guide's stale `from agentbundle.credentials import …` line is corrected to `credbroker` for both `figma` and `atlassian`. The README leads with plain outcomes, states the precise remote consequence (no REST node edits; collaborator-visible comments that require confirmation), front-loads the Figma account / plan / token-scope / 403 conditions, and gives one authoritative setup sequence with `<catalogue>` explained. (RFC-0064 Amendment #4.)

- **governance-extras 0.9.0 — preview-confirm write gate + completion receipt for `new-adr` / `new-rfc`.** Both skills now resolve and display the repository root, detect a non-default ADR/RFC location, draft the content, and show a preview (identifier, status, target path, index path, content) that waits for explicit confirmation — no file is created and no index updated before you confirm. After writing, each returns a completion receipt (identifier, file path, index path, status, files changed, owner, next step). Identity fields no longer assume GitHub handles. The README leads with outcomes (record a decision / propose a change / change the rules) before the ADR/RFC acronyms, corrects the skill count (four skills, including `rfc-status`), states the repo-scope consequence (adds capabilities and files to the current project), and shows a `--dry-run` preview route. (RFC-0064 Amendment #4.)

### Fixed

- **Shared install/upgrade guides — removed the stale `--to <version>` flag.** The `agentbundle upgrade` verb no longer accepts `--to`; version selection is by pointing `<catalogue>` at a git ref. Corrected the flag out of `preview-install-or-upgrade`, `install-user-scope-pack-into-kiro`, `install-user-scope-pack-into-codex`, and the `file-safety-contract` explanation.

- **Invalid bare `agentbundle install <name>` forms corrected across the remaining packs.** The install verb requires `--pack`; the bare-positional form the current parser rejects was still documented in `linear` (0.1.2), `iac-terraform` (0.1.2), `product-strategy` (0.1.2), `product-engineering` (0.12.2 — including a two-pack-in-one-command line split into two invocations), and `release-engineering` (0.1.3) READMEs, plus the `catalogue-curation`, `desk-research`, `figma`, and `governance-extras` first-session tutorials. All now use `agentbundle install --pack <name> …`; the `desk-research` tutorial also drops the pre-rename `research` pack name. Follow-up to the RFC-0064 Amendment #4 adopter front-door fixes.

- **Claude plugin marketplace manifest now passes `claude plugin validate` (Claude Code 2.1.209).** Three generator defects caused 35 errors: (1) marketplace missing top-level `name` field, (2) plugin `author` emitted as a plain string instead of a `{name, email}` object, (3) plugin `source` field absent entirely. All three are fixed in the build pipeline (`derive_projectable_subset`, `_run_aggregate`, `_aggregate_marketplace`). The `.claude-plugin/marketplace.json` in the working tree now validates with 0 errors.

### Changed

- **RFC-0064 Amendment #4 — cross-pack first-value adoption overlay.** Records Level A/B pack obligations, a pilot-first rollout contract, and eight decisions governing non-technical pack onboarding. Adds five work queue entries (`spec/portfolio-pack-first-value-contract`, three pilot specs, `spec/agentbundle-first-value-handoff`) and two shaping entries to `workspace.toml`. Reconciles `spec/m2-frame-intent-jtbd` from queue to shipped. ([RFC-0064 Amendment #4](../rfc/0064-ini-001-ai-native-ecosystem.md))

- **`frame-intent` skill (product-engineering pack 0.12.0) — three-tier JTBD elicitation in step 5.** The Opportunity framing step now explicitly elicits a functional job, emotional job, social job, and struggling moment. The intent template's Opportunity section carries four corresponding optional sub-fields. Existing intents with free-form Opportunity prose remain valid without migration.

- **`workspace-status` skill (core pack 0.13.3) — Findings step shows inline tables.** When either `docs/product/findings/rfc-candidates.md` or `docs/product/findings/roadmap-intents.md` has data rows, `workspace-status` now prints both tables inline rather than a bare count. When both registers are empty, a single summary line is shown (`0 rfc candidates · 0 roadmap intents — both registers empty`) instead of silently omitting the section.

- **`work-loop` skill (core pack 0.13.5) — pre-existing failure capture + progressive disclosure.** Adds a "Pre-existing failure triage" step to GATES: when a gate fails on a file not in the diff, the loop captures it to `workspace.toml [backlog].open` as a `pre-existing-*` slug and treats it as a known-skip rather than going to FIX. Full schema in new `references/pre-flight-failures.md`. Also collapses the self-coverage gate section (~30 inline lines → 4-line summary + `references/self-coverage/protocol.md`) and removes the infra/deploy multi-artifact preflight paragraph (already covered by `references/infra-verification.md`).
- **`work-loop` skill (core pack 0.13.2) — experience-reviewer rendered-output clarification for web surfaces.** The `experience-reviewer` bullet in the REVIEW section now explicitly states that for web surfaces (HTML/CSS/JS), "rendered output" means the built site — run the build and describe key pages from the output; the code diff alone cannot serve as the rendered artifact for genre-rubric or cross-page consistency checks. Backlog item `work-loop-xd-rendered-output`.
- **Claude plugin install command updated to use marketplace format.** The documented install flow in `README.md` and the web catalogue now uses `claude plugin marketplace add eugenelim/agent-ready-repo` followed by `claude plugin install <pack>@agent-ready-repo`, replacing the deprecated repository-tree-URL form (`claude plugin install https://github.com/…/tree/claude-plugins-dist/<pack>`).

- **`check-workspace` renamed to `workspace-status` (core pack — clean retire, no alias).** The workspace-level cold-start orient skill is now invoked as `workspace-status`. All operative references swept in one PR. Adopters invoking `check-workspace` by name will receive a "skill not found" signal; update to `workspace-status`. The new description triggers cover all phrasing the old skill responded to, plus "workspace status", "where am I", "orient me", "session start". ([RFC-0067](../rfc/0067-session-arc-conventions-and-pack-workflow-guide.md), [ADR-0054](../adr/0054-session-arc-verb-taxonomy-and-pack-type-classification.md))

### Added

- **`linear` pack (0.1.0) — Linear integration: credentialed CLI + brief intake/sync.** New opt-in user-scope pack. Adds three skills: (1) `linear` — a credentialed GraphQL CLI for read-only access to Linear Issues and Projects (check, get-issue, get-project; Personal API Key via `credbroker`; paginated up to 250 issues; 429 Retry-After); (2) `linear-brief-intake` — maps a Linear Issue (with sub-issues) or Project onto a Shape B product brief, caps at 10 stories, hands off to `receive-brief`; (3) `linear-brief-sync` — delta catch-up for existing briefs: diffs Linear-sourced fields, presents section-level before/after for PE approval, refuses when Status is Executing. ([RFC-0068](../rfc/0068-linear-brief-intake-and-sync.md))
- **Pack first-value contract — all 17 packs (RFC-0064 Amendment #4).** Every pack now carries a `[pack.first-value]` section in `pack.toml` recording audience posture, verified surfaces, prerequisites, verification steps, and recovery steps. Level B packs (10 of 17) additionally carry a starter task, starter prompt, expected result, and next action for non-technical or mixed audiences. Two packs (`governance-extras`, `user-guide-diataxis`) include a `safety-gate` because their starter task writes a shared governance or structural record. `tools/lint-first-value-contract.py` enforces the contract at build time; `tools/build_gate_chain.py build-check` now includes the new gate.

- **`frontend-engineering` skill (core pack 0.13.1) — XD genre routing step (step 1b).** After naming the aesthetic reference (step 1), the `frontend-engineering` PLAN phase now routes to the matching XD discipline skill by surface type: `conversion-design` for marketing pages, `documentation-design` for docs/help, `analytical-design` for dashboards, `informational-design` for editorial pages, `interaction-design` for form flows and component state machines, `content-design` for content strategy. T2 conditional — experience-design pack detected by checking for `conversion-design` in available skills; absent pack records a named skip and proceeds to step 2. Backlog item `xd-genre-routing-frontend-engineering`.

- **`capture-work` skill (core) — classify-then-triage front-door for `workspace.toml`.** Replaces `queue-add`. Before writing, `capture-work` classifies each item as `[build]` (implement, fix, spec, refactor) or `[shape]` (research, strategy, design, signal) and surfaces that classification for confirmation. Build items route to the same destinations as `queue-add` (active initiative's `[work].queue` or `[backlog].open`), with all prior behaviors preserved: slug derivation + collision check, dependency inference from explicit language only, grouping (independent batch / atomic bundle), prioritization elicitation, escalation rubric, cold-start-sufficient comments, comment-preserving write, graceful degradation. Shaping items route to `[shaping_queue].backlog` (initiative-scoped) or `[backlog].open` with a `type` field (repo-level); `signal` items route to `[shaping_queue].active`. After writing, the skill offers a progressive capability-detected hand-off to the matching shaping skill if its pack is installed, or emits a named install hint if not. Triggers on "capture this", "add these to the queue", "capture these as queue items", "queue this up", "add this to the backlog". ([RFC-0064 Amendment #3](../rfc/0064-ini-001-ai-native-ecosystem.md))
- **`workspace-status` mode tags** — every item in the Ready-to-start and Backlog sections is now prefixed with its room: `[build]` (work queue items and untyped backlog entries), `[shape]` (shaping queue items and typed backlog entries), `[brief]` (brief queue items). The two-room model is immediately visible at session start.
- **`work-loop` orient-step guard** — step 0 now checks whether the argument slug matches a shaping entry in `[shaping_queue]` (active or backlog) or a typed `[backlog].open` entry. If matched, the skill emits a redirect naming the appropriate shaping skill and stops before PLAN. Prevents accidentally running `work-loop` on items that belong in the shaping room.

- **Verb taxonomy section in `docs/guides/_shared/how-to/author-a-skill.md`.** A new `## Naming your skill` section (after `## Body structure`) documents the canonical five-verb taxonomy (`status`, `start`, `check`, `init`, `resume`) and the banned-label list (`arrive`, `orient`, `onboard`, `return`, `onboarding`) from ADR-0054. Pack authors now have a lookup table before naming a new skill.

- **`product-strategy` pack 0.1.0 — the strategy seat upstream of product engineering and experience design (RFC-0063, ADR-0053).** A new user-scope, pure-markdown pack with 9 skills across 3 pillars. **Pillar 1 — Market and competitive strategy:** `run-swot` (SWOT analysis → `swot-analysis.md`); `run-porters-five-forces` (industry structure analysis → `competitive-landscape.md`); `run-pestle-analysis` (macro-environment scan → `macro-environment.md`); `run-bcg-matrix` (portfolio position by quadrant → `portfolio-position.md`); `run-okr-cascade` (company → team OKR derivation + gap identification → `okr-cascade.md`; gaps routed as `{type = "strategy"}` entries to the active initiative's `["ini-NNN".shaping_queue].backlog` in `workspace.toml` for `frame-situation` (PE pack) to pick up); `write-prfaq` (altitude-0 press release + FAQ forcing function → `prfaq.md`); `synthesize-stakeholder-research` (consumes desk-research pack outputs → `stakeholder-synthesis.md`). **Pillar 2 — UX strategy:** `define-ux-strategy` (NN/g three-layer model + Jaime Levy four tenets + Gothelf/Seiden OKR-linked framing → `ux-strategy.md`). **Pillar 3 — Content strategy:** `define-content-strategy` (Halvorson quad: Purpose + Process + Structure + Governance → `content-strategy.md`). All artifacts resolve their write path through the `[product-strategy]` table of `agentbundle-layout.toml` (config → default `docs/product/shaping/` → discover-by-marker). Each skill ships trigger evals (`eval_queries.json`) and a Tier-4 LLM-judge eval (`evals.json`). The OKR-cascade → PE-pack cross-pack routing contract is documented in `packs/product-strategy/.apm/skills/run-okr-cascade/references/cross-pack-routing.md`; `workspace-status` routes `{type = "strategy"}` items to `frame-situation` (M2) or `frame-intent` as interim. Journey: `docs/product/journeys/product-strategist-sets-direction.md`.

- **`experience` pack 0.6.0 — surface-genre uplift: 9 canonical renames, 7 new skills.** The experience pack moves from 11 skills at 0.5.x to 18 skills at 0.6.0. **Nine skill renames** to canonical industry vocabulary (ADR-0052): `map-customer-journey` → `journey-mapping`, `blueprint-service` → `service-blueprint`, `map-screen-flow` → `user-flow`, `map-internal-process` → `process-mapping`, `aesthetic-direction` → `creative-direction`, `layout-and-information-architecture` → `information-architecture`, `design-critique` → `design-review`, `design-system-foundations` → `design-system`, `copy-direction` → `tone-of-voice`. **Seven new skills**: `design-principles` (Define-phase: NNGroup 4-step model, arbitration test, evidence-level carry-through); `conversion-design` (marketing surfaces: hero approach, above-fold spec, scroll story, social proof tier); `documentation-design` (docs surfaces: Diátaxis type map, navigation-at-scale strategies, TTFV target, machine-readability as design-phase decision); `analytical-design` (dashboard surfaces: domain-model-first, business-question anchoring, 3-tier widget hierarchy, Shneiderman's mantra, spatial layout grammar); `marketplace-design` (catalogue surfaces: card IA hierarchy, filter/facet architecture, comparison affordances, browse-first vs. search-first); `informational-design` (editorial surfaces: typography as primary design tool, F/Z-pattern calibration, editorial grid, "what's next" chain); `workspace-design` (productivity and agentic surfaces: context-persistence, session arc, collaboration state IA, agentic UI patterns). **Surface-genre contract**: `user-flow/assets/screen-brief-template.md` gains a `surface-genre:` frontmatter field; genre declared once in the brief propagates to all downstream skills. **Seven D5 extensions** across six existing skills: `journey-mapping` gains peak-moment identification and evidence-level elicitation; `interaction-design/references/pattern-families.md` adds 5 pattern families (wizard-and-stepper, data-table, destructive-action escalation, save-state, analytical-dashboard-widgets); `service-blueprint` gains evidence-of-service row and fail-point marking; `information-architecture` gains success-metric binding and genre routing; `design-review` gains design-principles integration chain and 6 genre-specific rubrics; `creative-direction` gains genre canonical reference tier for all 7 genres.

- **`rfc-status` skill added to governance-extras (0.7.0) — RFC landscape dashboard.** A new read-only skill scans `docs/rfc/*.md` and groups RFCs by lifecycle state (`Draft`, `Open`, `Final Comment Period`, `Accepted`, `Rejected`, `Withdrawn`, `Experimental`, `Superseded`); surfaces active RFCs by name and resolved RFCs by count. Also counts non-header rows in `docs/product/findings/rfc-candidates.md` and `docs/product/findings/roadmap-intents.md` and surfaces them as a findings summary. Useful at session start alongside `workspace-status`. Read-only — never creates or modifies RFC files.
- **`docs/product/findings/` registers seeded (RFC-0064 M3).** Two new governance registers: `rfc-candidates.md` (candidate RFCs surfaced by work-loop scope-deferrals or `frame-situation` escalations) and `roadmap-intents.md` (deferred roadmap items not yet shaped into specs). Both use the same five-column schema: `Problem | Source | Surfaced by | Date | Priority | Disposition`.
- **`workspace-status` surfaces findings count (core 0.13.0).** After resolving the queue DAG, `workspace-status` now surfaces a count line — "N rfc candidates · M roadmap intents" — from the findings registers when either count is non-zero. Omitted when both are zero or the files are absent.

### Changed

- **`experience-design` pack 1.1.0 — multi-surface audit protocol, 6-element above-fold spec, and surface-specific mobile paths.** Seven gaps identified by a UX audit benchmarked against Linear and Stardog (the skills got within-surface findings right but missed every cross-surface and surface-specific mobile finding — root cause: no multi-surface protocol and no surface-specific mobile path in the quality floor pass). **Multi-surface protocol (Gaps 1, 3):** `design-review` and `information-architecture` each gain a Step 0 surface inventory for multi-surface platforms; `design-review` genre routing and `experience-reviewer` both state that a marketing surface and a documentation surface require separate passes with a third cross-surface integration pass after. **Above-fold spec (Gap 2):** the marketing genre rubric item 2 now enumerates all six required above-fold elements (IC-first headline ≤10 words, conviction-building subheadline, outcome-language primary CTA, optional secondary CTA, adjacently-positioned proof signal, friction microcopy — absence of friction microcopy is a blocker when the primary CTA implies commitment) and adds a tone collision check between headline approach and subheadline register. **Cross-surface wayfinding (Gap 4):** `information-architecture` step 6 gains a cross-surface wayfinding check — the docs→marketing bridge must be present on every page (not just the footer or landing page) and its absence is a blocker finding. **Docs landing page hub structure (Gap 5):** documentation genre rubric item 3 now verifies the three hub jobs (Start Here entry point, four Diátaxis-typed entry points named by reader outcome, above-fold search) and flags the search-first requirement for >200-page sites. **Surface-specific mobile checklists (Gap 6):** `design-review` step 2 and `interaction-design` step 6 each gain surface-specific mobile priorities for marketing surfaces (above-fold CTA visibility on small-phone viewports, full-width drawer targets, grid overflow) and documentation surfaces (code block horizontal scroll, sidebar collapse, comfortable reading width). **Cross-surface copy voice continuity (Gap 7):** marketing genre rubric gains item 4 — register mismatch flags as minor; contradicted product claims flag as major; requires reading the docs landing page and one how-to page alongside the marketing surface.

- **`work-loop` deferred-items step prompts for findings registers (core 0.13.0).** After recording a deferred item in `docs/backlog.md`, the loop now prompts: "Does this look like an RFC candidate or a roadmap intent? If so, also add a row to `docs/product/findings/rfc-candidates.md` or `docs/product/findings/roadmap-intents.md`." The backlog anchor remains the primary durable record; the findings registers add governance visibility. Prompt skipped when neither file exists.

### Fixed

- **`new-rfc` session-fragmentation guard (governance-extras 0.8.0).** Generating specs or ADRs for an already-Accepted RFC in a follow-on session now re-surfaces the `workspace.toml` queue-write prompt for any `spec/<path>` entries absent from the active initiative's queue. Previously the prompt fired only when an RFC transitioned to Accepted within the current session; a follow-on session silently skipped it. The `new-rfc` trigger description is also extended to activate on "generate follow-on specs for RFC-NNNN" and similar phrasing, routing those sessions through the queue-write guard.

- **`desk-research-project-start` no longer silently falls back to `.context/research` (desk-research 1.1.0).** The pre-fix skill defaulted to `.context/research/` when no `agentbundle-layout.toml [research]` config was found — a gitignored scratch path that does not survive workspace resets or session boundaries. The fix removes this silent fallback and replaces it with two-branch elicitation: the agent asks whether to commit output to the repo (`docs/product/research/`) or to a personal workspace (user-supplied absolute path, e.g. an Obsidian vault). Elicitation writes the chosen path to the appropriate `agentbundle-layout.toml` so subsequent projects skip the prompt. The config key is renamed from `parent` to `output_dir`; resolution order is now user-scope first (personal vault wins across repos), then repo-scope, then elicitation.

- **`iac-terraform` pack (v0.1.0) — Terraform and OpenTofu IaC accelerator.** A new opt-in accelerator pack for generating and maintaining Terraform/OpenTofu infrastructure code. Two skills: `generate-iac` (8-stage generation loop from ADR gate through G4 handoff) and `reconcile-iac` (drift audit required before every follow-on change). Dual-engine — the engine-neutral HCL baseline runs unchanged on both Terraform ≥ 1.6 and OpenTofu ≥ 1.6 (the validation floor); the native S3 lockfile feature (`use_lockfile = true`) requires Terraform ≥ 1.11 or OpenTofu ≥ 1.7 and is configured separately in `backend.hcl`; OpenTofu-only features (state encryption, early variable eval) are opt-in via the `.tofu` override mechanism. Zero seeds, zero agents — the pack emits provider files and pipeline config into the adopter's repo via `generate-iac`, not via scaffold seeds. Validated providers in v1: AWS (both engines), GCP, and Databricks; Azure, Kubernetes workloads, edge/CDN/DNS, HashiCorp platform (Vault, HCP), data platforms, and observability vendors are experimental. Standards: terraform layout, networking, security/IAM, tagging, observability, OPA/Conftest policy-on-plan (Sentinel incompatible with OpenTofu — not supported). CI templates for GitHub Actions (reference), Azure DevOps and GitLab (experimental). G4 handoff artifact set: deploy-ready TF directory, pinned plan + digest, OPA/Conftest exit-0 evidence, Trivy/Checkov exit-0 evidence, reversibility classification per resource, and optional Infracost delta. Depends on `core >= 0.1` and `governance-extras >= 0.6`.
- **`governance-extras` 0.6.0 — governance-index template, extension-contract how-to, `new-adr` infra mode.** Three companion additions from RFC-0065 D16: (1) `seeds/governance/manifest.example.yaml` — the governance-index template (a domain → ADR/standard manifest loaded first by `generate-iac` Stage 0; tool-neutral, used by any governed repo); (2) `new-adr` skill gains infra mode (`mode: infra`), which loads a new reference (`references/infra-decisions.md`) with the seven IaC ADR topics and their framing questions — `state`, `layout`, `iam`, `tagging`, `networking`, `pipeline_auth`, `remediation`; (3) new how-to guides for the governance index and extension-contract conventions.
- **`architect-review` Proposal rubric gains an extension-contract check.** When a design doc introduces a plugin, hook, or customisation point, the Proposal rubric now checks that the extension contract is named, its shape is described, and what is stable vs unstable is stated.

- **`workspace-status` skill added to core pack (core 0.12.0, originally `check-workspace` — renamed in this release).** A new session-start skill reads the repo-level `workspace.toml` and surfaces ready-to-start items, blocked items with reason, parallel candidates, and active signals — all in one command. Resolves the dependency DAG across all queues and initiatives using `needs` prefix notation (`work:`, `shape:`, `research:`, `brief:`, and cross-initiative `ini-xxx:work:` prefixes). Surfaces `type = "signal"` entries as "active context" separately from actionable "ready to start" items; surfaces each shaping entry with the matching skill invocation for the installed packs. Offers to initialise `workspace.toml` when absent. Run `workspace-status` at every session start from Batch 2 onward.
- **`workspace.toml` committed to `main` as the repo-level declared-intent coordination artifact.** Pre-populated with the INI-002 (Platform Core) M1 bootstrap queue: three queues (`shaping_queue`, `brief_queue`, `work`) with all Batch 3–5 specs pre-seeded and their `needs` wiring in place. `spec/m1-workspace-core` is marked shipped (this PR). The `agentbundle-layout.toml [product]` table is documented in `workspace-status`'s reference file: `projects` and `shaping` paths are configurable; `briefs` stays pinned.

### Changed

- **`voice-and-microcopy` human-craft check gains vocabulary tells, an editorial methodology, and voice authenticity tests (product-engineering 0.11.0).** `human-craft-check.md` now covers three additional layers beyond its existing structural tells: a vocabulary-tell section (hollow verbs, inflated adjectives, abstract container nouns, hedging openers — each with a concrete replacement rule); a three-pass editorial methodology (vocabulary scan → delete the opening → specificity audit); and three voice authenticity tests (pub test, founder test, one-person test). Scoped to the same context as before — longer copy: onboarding text, feature descriptions, help text — not short UI strings.

### Added

- **`voice-and-microcopy` gains a human-craft structural-tell check (product-engineering 0.10.1).** A new reference file, `human-craft-check.md`, inlines six structural AI tells — treadmill effect, symmetrical lists, false precision, performative thoroughness, nice-nice wrap, subtext vacuum — and a four-question self-check for longer copy (onboarding text, feature descriptions, help text). The content checklist gains an eighth item, Human-crafted, that routes longer copy through this check. Self-contained within the pack; no cross-pack references.

### Changed

- **`architect-diagram` gains Mermaid layout guidance, ELK renderer docs, and an explanation guide (architect 0.12.0).** `mermaid-flowchart.md` gains three new sections: `## Edge routing — curve style` (the `curve: step` orthogonal-routing recommendation for architecture diagrams, with a full routing-value table), `## Layout control` (subgraph direction override, `inheritDir`, diagram-global spacing keys, the `subGraphTitleMargin` workaround, and label wrapping), and `## ELK renderer — for complex graphs` (Brandes-Köpf node-placement strategy, `mergeEdges`, `LINEAR_SEGMENTS` option, and a venue-caveat matrix). `mermaid-c4.md` gains `## Layout config` (`c4ShapeInRow`, `c4BoundaryInRow`, `UpdateLayoutConfig()` syntax, and a note that `Lay_*` direction directives are silently ignored). `mermaid-mindmap.md` gains `## Layout algorithms` (`cose-bilkent` vs `tidy-tree`, determinism trade-off, `maxNodeWidth`, `padding`). `## Common architecture pitfalls` in the flowchart reference adds three new entries: invisible links as a layout crutch, non-grammatical edge labels, and edge-label overlap. A new Diátaxis explanation guide (`docs/guides/architect/explanation/architect-diagram-skill-design.md`) documents the design principles behind the skill — Sugiyama / dagre / ELK algorithm choices, direction defaults, Gestalt visual-encoding rationale, notation-routing logic, portability constraints, and the anti-pattern register. 16 `.mmd` fixture files covering all supported diagram types and a `pytest`-based validation harness (`scripts/test_fixtures.py` + `scripts/testdata/`) are added to the skill source.
- **`architect-diagram` gains portable Mermaid title, accessibility, and pipeline-orientation guidance (architect 0.11.0).** Three Mermaid-native additions to the skill's references: (1) `flowchart LR` is now explicitly the orientation for pipeline / ETL / CI-CD / data-flow diagrams (a decision-table row plus strengthened flowchart guidance); (2) the config-frontmatter `title:` is documented as the in-source diagram title (Mermaid ≥ 10.5), with the prose scope sentence kept as the always-portable baseline; (3) `accTitle` / `accDescr` are documented as the diagram's screen-reader alt text. The change also explicitly rejects three renderer-proprietary conventions (`:::external`, `label\|tech`, `%% title:`) that no-op or break in stock Mermaid (GitHub, Confluence, `mmdc`, and the repo's own renderers) — they contradict the skill's "survive enterprise wiki rendering" north star. Guidance only; no renderer or skill-contract change.

### Fixed

- **`aesthetic-direction` grounding reference now cites WCAG thresholds by name, not literal values (experience 0.4.1).** The Standards section of the grounding reference described contrast thresholds using specific ratio and point-size literals, which violated RFC-0033's portable-method rule. The section now refers to the named WCAG SC thresholds and the OS-level reduced-motion preference concept rather than reprinting the values table. No change to skill behavior — only the reference prose that informs the aesthetic-direction pass.

### Added

- **Platform marketing site — Phase 1 (Astro homepage).** A new Astro marketing
  site in `web/` (approved as a top-level directory by [RFC-0061](../rfc/0061-web-top-level-directory.md),
  toolchain recorded in [ADR-0050](../adr/0050-astro-marketing-site-toolchain-and-deploy.md))
  becomes the platform anchor at `/`, with the existing MkDocs reference docs
  co-deployed at `/docs/` from one GitHub Pages origin. The homepage ships all
  nine sections from the platform-site spec in the amber-gold Option B aesthetic
  (dark hero + stat strip, light content bands, dark closer); all interactions —
  install tabs, catalogue expand, mobile nav — are CSS-only (zero JavaScript) and
  the page passes `pa11y` WCAG 2.2 AA. The CI pipeline now builds Astro first,
  then MkDocs, into a single `build/` artifact.

- **`frontend-engineering` skill added to core pack (core 0.11.0).** The work-loop now loads
  inline craft rules — design pre-flight, HTML semantics, CSS token discipline,
  accessibility, state completeness, and verification commands — whenever a
  task's primary output is HTML, CSS, or JS. The design-intent pass is mandatory
  (not a recommendation) for that surface.

- **OWASP Agentic Skills Top 10 v1.0 compliance pass — all non-core packs.**
  All non-core packs audited and hardened against AST01–AST10. Three classes of changes:
  (1) AST05 — `research` skill now explicitly declares that fetched web content is untrusted
  data, never instructions;
  (2) AST06 — `confluence-crawler` and `jira` skills now declare the SSRF pre-flight host
  check the agent must run before invoking a user-supplied base URL (scripts validate scheme
  only; the agent verifies the host and rejects private-IP ranges and cloud-metadata endpoints);
  (3) AST10 — all non-credentialed skills that cross a security boundary now carry
  `metadata.boundaries` in their SKILL.md frontmatter (`network_fetch`, `filesystem_write`,
  `filesystem_read_untrusted`, `network_egress`, or `deploy_action`). The `assimilate-primitive`
  skill also gains an explicit AST01–AST10 security review step so any ingested primitive is
  checked before landing. Compliance record in `docs/architecture/security.md`.

- **New `agentic-skills` module in `security-checklists` — OWASP Agentic Skills Top 10 v1.0 coverage (core 0.10.0).**
  The `security-reviewer` now has control-altitude depth for the OWASP Agentic Skills Top 10
  v1.0 (AST01–AST10): malicious skill content (AST01), permission over-declaration (AST03),
  insecure metadata parsing (AST04), external reference pinning (AST05), isolation declaration
  (AST06), version drift (AST07), governance gaps (AST09), and cross-platform security metadata
  (AST10). AST02 (Supply Chain) defers to the existing `supply-chain` module; AST08 (Poor
  Scanning) is addressed by the three-bucket delegation legend. The module fires when a diff
  authors or modifies a skill file, parses skill metadata, builds a distribution package, or
  adds skill execution sandbox config. Accompanied by a new `docs/architecture/security.md`
  reference documenting all enforced security frameworks.

- **New `agentbundle show <pack>` command — a pack's skills and agents, derived live (agentbundle).**
  Answers "what does this pack contain?" by walking the pack's `.apm/` source tree on
  each call, printing its `pack.toml` metadata alongside the full, sorted skill and agent
  inventory. `--format json` emits a stable object (`name`, `version`, `description`,
  `skills`, `agents`, `source`) for scripts and agents. Nothing is persisted and no
  manifest is touched, so the answer can't drift from what the pack ships. When the
  catalogue can't be resolved, an *installed* pack still reports its inventory from the
  install-state files (`source: installed-state`); a not-installed pack errors and exits
  non-zero. Implements RFC-0060 / ADR-0049.

- **`design-critique` now includes a marketing clarity pass (experience 0.4.0).** A new
  fourth mode runs when the artifact has above-fold copy with a persuasion/conversion
  goal (landing pages, pack cards, product announcements — not settings screens or forms).
  It checks the tweet test (headline stands alone as a conviction statement), the
  five-second scan (above-fold answers what / who / should I care), and painkiller-first
  structure (copy leads with the reader's problem, not the author's feature list). Each
  finding maps to the violated criterion with a `marketing` source label and a 0–4
  severity using the existing frequency × impact × persistence rubric, where impact means
  conversion/persuasion cost.

- **`new-spec` now prompts for design-readiness on ui-shaped specs (core 0.9.0).** When
  `Shape: ui` is confirmed, a new step 4d checks whether a grounded aesthetic reference
  (`aesthetic-direction` output) exists before the Acceptance Criteria are written,
  offers to run `design-critique` on any existing affected surface, and requires at
  least one design-intent AC whose outcome is observable from the rendered surface —
  not derivable from code. If the experience pack is absent, it notes that in Assumptions
  and proceeds. This is the spec-authoring complement to `work-loop`'s pre-EXECUTE
  design-intent pass: both target the same failure mode (technically correct surfaces
  with no design sense) at different stages of the loop.

- **`work-loop` now includes a pre-EXECUTE design-intent pass and an `experience-reviewer`
  gate for user-facing surface diffs (core 0.8.0).** When a change produces a user-facing
  surface — a new page, a redesigned screen, a pack card, a docs page — the PLAN section
  now recommends running `aesthetic-direction` and/or `design-critique` before writing
  code (advisory in both light and full mode, analogous to "write the test first"). For
  full-mode user-facing surface diffs, `experience-reviewer` is added to the specialist
  reviewer roster alongside `security-reviewer` and `quality-engineer`: it receives the
  rendered output plus the grounded aesthetic reference and constraints, and runs with
  the standard select-or-note fallback when the experience pack is absent. Decision
  recorded in ADR-0047.

- **New `catalogue-curation` pack — the catalogue-operator's toolkit (opt-in, repo-scope).**
  Skills to grow and maintain an agent-skill catalogue: `propose-catalogue-pack`
  (stand up a new pack), `assimilate-primitive` / `assimilate-repo` (bring
  external skills/agents/hooks in — safely, and reshaped to the repo's craft,
  resumable via a ledger), and `export-catalogue` (produce a white-label or
  attributed derivative for another org or domain, with a fail-closed leak
  check). Ingested code runs the repo's own lints + SAST/SCA before it lands; a
  guard blocks any change to the `agentbundle` engine or credential brokers
  through the pack. Domain-agnostic — the same toolkit serves a non-SDLC
  catalogue. Requires `core` + `governance-extras`; not in any default profile.
  (RFC-0059, ADR-0048.)
- **`msg-to-markdown` is now a pure-Python skill that also reads `.eml`, and
  emits the unified output contract (converters 0.6.0).** The Outlook `.msg`
  converter is re-hosted from Node.js onto Python: `.msg` is read via `olefile` +
  first-party MAPI decoding (replacing the `msg-parser`/`extract-msg`/npm readers
  — see ADR-0046), and MIME `.eml` is now supported through the same render path
  (multipart bodies, nested `message/rfc822`, richer headers). Every conversion
  now carries the same versioned frontmatter contract (`contract-version`, `tier:
  0-no-ml`, `content-type`, `ingestion-quality`) that `file-to-markdown` emits, so
  email ingests into a context layer exactly like documents. It preserves headers
  (From/To/CC/**BCC**/Date/Importance), the body (HTML reduced to Markdown, or
  plain text), and an attachments table, and it **closes the attachment-extraction
  path-traversal sink** the old Node script carried (every write is basename-
  reduced and confined). No Node.js, no ML/OCR model, no network call.

- **`file-to-markdown` gains three opt-in higher-fidelity capabilities
  (converters 0.5.0).** All three are **off by default** — the default one command
  (`python scripts/convert.py "<file>"`) is unchanged. (1) **`--enrich`** turns on
  Docling's **local-model** enrichment on the Tier-2 path — formulas → LaTeX, code
  understanding, figure classification and captioning. It is local-model-only by
  construction (Docling's remote-services / remote-VLM path is never enabled), so
  enrichment can never become a hidden data-egress channel; enriched captions are
  treated as untrusted model output (inert body content, never instructions).
  (2) **`--chunk`** also writes Docling `HybridChunker` output (tokenizer-aware,
  structure-preserving chunks) to a `<basename>.chunks.jsonl` sidecar — one JSON
  record per chunk carrying the full contract field set — so an extraction can feed
  a retrieval store as chunks, not just a flat file (needs the
  `docling-core[chunking]` tokenizer extra, installed on demand). (3) **`--tier3`**
  assembles adopter-obtained managed-OCR text into the unified contract with
  `tier: "3-managed-api"` and `requires-review: true`. Tier 3 crosses a
  **data-egress boundary**, so it is **explicit-only and never auto-reached**, and
  the skill itself **makes no network call** — you run the approved vendor through
  your own transport, and the skill validates an egress declaration
  (`{endpoint-allowlist, residency-region}`), stamps the contract, and records the
  destination in provenance. See the skill's `references/tier3-managed-api.md` for
  the adopter controls (vendor retention/no-training, transport-binding, and
  redaction as your responsibility — documents are sent unmodified). No ML model or
  per-vendor data ships with the pack.

- **`file-to-markdown` reads scans and non-diagram images via agent-vision
  (converters 0.4.0).** The image branch gains a general **`text-table`**
  strategy for non-diagram content — a screenshot of prose, a table image, a
  form, a receipt, a scanned page — that emits Markdown prose and tables instead
  of forcing everything through the diagram extractor. For a scanned or
  image-only PDF (the case the Tier-0 floor flags `requires-review` and points at
  Tier 1), a new `scripts/rasterize_pdf.py` renders each page to an image, which
  the in-session model then reads. This is **Tier 1 (agent-vision)**: the
  already-running model reading a rendered image — *not* an installed OCR model.
  The read carries `tier: "1-agent-vision"` with an honest
  `extraction-confidence`/`requires-review` signal, treats all document text as
  **untrusted data** (transcribe, never obey — a prompt-injection defense), and,
  when the PDF has a digital text layer, is **cross-checked** against it to bound
  hallucination. The page rasterizer is `pdf2image` (MIT), installed on demand
  (`python scripts/rasterize_pdf.py --check`) and needing a system poppler; it is
  never auto-installed, and when it is absent the skill keeps the Tier-0 output
  and says so rather than crashing. Tier 1 adds **no new network egress from the
  skill** — though a cloud-hosted in-session model still receives the page
  content at its already-approved endpoint.
- **`file-to-markdown` gains a no-ML Tier-0 floor and a versioned output
  contract (converters 0.3.0).** Where Docling's ML models are banned or
  un-fetchable, `file-to-markdown` can now convert a digital PDF (via `pypdf`),
  Office files (`.docx`/`.xlsx`/`.pptx`, degrading to a stdlib path when the
  ordinary library is absent), and the everyday text formats (HTML, EPUB,
  CSV/TSV, OpenDocument, `.eml`) to Markdown using only pure-Python or standard-
  library parsers — no ML model, no network. Docling stays as the higher-
  fidelity Tier 2 for `.xls` and images. Every extraction, across both the
  document and image branches, now carries one versioned YAML frontmatter
  contract recording provenance and a quality signal (`contract-version`,
  `tier`, `extraction-confidence`, `requires-review`), so a scanned PDF that
  yields sparse text is flagged `requires-review` and pointed at an escalation
  tier instead of passing silently. The default invocation is unchanged
  (`python scripts/convert.py "<input-file>"`); the Tier-0 PDF/Office libraries
  install on demand (`python scripts/convert.py --check`), and untrusted input
  is parsed defensively (XXE-safe XML, decompression-bomb guards, output-path
  confinement, resource ceilings).

### Fixed

- **`file-to-markdown` image extraction no longer silently loses elements
  (converters 0.2.3).** The image reconciler used to collapse every element
  that shared a `(type, name)` into one before checking where it sat — so two
  genuinely distinct nodes with the same label (a second "Validate" step, a
  repeated "Queue") were merged into a single element with no warning, and
  elements the model saw but couldn't label were dropped entirely. The
  reconciler now clusters by position: same-named nodes that overlap across
  tiles still merge, but spatially distinct ones are kept as separate elements,
  and unlabeled elements are retained and shown as `(unlabeled)`. The document
  branch (`convert.py`) now fails with actionable guidance — naming
  password-protection/encryption and corruption as likely causes — instead of a
  bare stack trace, and the image branch warns (to stderr; stdout stays clean)
  when handed a multi-frame image (animated GIF, multi-page TIFF) that only its
  first frame is read.

### Added

- **`architect-diagram` now draws timeline, quadrant, and mindmap diagrams (architect 0.10.0).**
  The diagram skill routes three new intents to Mermaid: a **timeline** for
  roadmaps / chronologies / release history, a **quadrant** (`quadrantChart`)
  for 2×2 prioritization and positioning, and a **mindmap** for hierarchical
  decomposition — joining the existing C4 / sequence / state / ER / flowchart
  set. Each has its own on-demand syntax reference and rubric budget. Because
  the three are newer Mermaid grammars with uneven enterprise-wiki rendering,
  the skill offers them with the same rendering-support caveat it already
  applies to `architecture-beta` (with a table / bullet-list fallback), so
  flowchart and C4 stay the defaults. The diagram rubric also gains explicit
  per-type complexity budgets plus additive accent- and edge-count caps.
- **Docs now call out the catalogue and skill/pack format as first-class, and ship an `llms.txt`.**
  New `docs/architecture/catalogue.md` names what a catalogue *is* on disk (the
  `packs/` + `.claude-plugin/marketplace.json` markers), how `agentbundle`
  resolves one through its four-layer chain, and how to point it at your own —
  the starting point for standing up your own catalogue. New
  `docs/architecture/skill-and-pack-format.md` maps the format in three layers
  (the agentskills.io skill standard, the pack envelope, projection). A root
  `llms.txt` indexes the key docs so an agent can read the relevant pages
  instead of scanning the whole repo. The architecture and top-level READMEs
  route to both.
- **The `methodology` output shape for research (research 0.6.0).** Ask
  *"the best way to do / run / build / train X, end to end, for my situation"*
  and `/research` now answers with a **method, not a reading list** — a staged,
  contingency-adapted, maturity-aware, evidence-graded description of how the
  activity is done. The shape produces `<topic-slug>-methodology.md` (episodic) or
  `methodology.md` (project mode) from six sections, each grounded in a discipline:
  a SIPOC scope frame, a stage spine, **mandatory** contingency branches
  (which path *your* situation takes) and a **mandatory** maturity ladder
  (novice→expert, or crawl→walk→run for one-off deliverables), failure modes, and
  GRADE evidence tags. It defaults to `applied` depth, is slide-ready for
  `markdown-to-pptx` with no reshaping (sections at H1, stages at H2, no H3), and
  is fenced against `frame-domain` (product/MVP grounding) and
  `map-internal-process` (your own operations). Prompt-only — no new dependency,
  no runtime engine.
- **`agentbundle list-installed` — see what you actually have installed (CLI 0.10.0).**
  A new read-only command lists every installed `(pack, adapter)` row across the
  user and repo scope with its version and an `up-to-date` / `upgrade-available`
  / `unknown` status against the catalogue. The status check runs by default and
  degrades to `unknown` (never an error) when the catalogue can't be resolved;
  `--no-check` / `--offline` skips it for a fast, network-free listing; `--scope`
  filters to one scope; `--check-drift` adds a per-row count of files edited
  locally since install. Closes the gap where no command could report installed
  state — only what a *catalogue* offered.
- **The release loop — a new opt-in `release-engineering` pack (release-engineering 0.1.0).**
  Adds the SRE/ops **outer loop** above `work-loop`'s inner build loop: a
  **`release-lead`** agent (the outer-loop supervisor — a peer of `work-loop`'s
  supervisor and `discovery-lead`, **not** a `work-loop` mode) and a
  **`release-loop`** skill that deploys the integrated whole to an **ephemeral
  environment**, runs e2e, observes telemetry, feeds deployed findings back to the
  inner loop (no human relay), redeploys, and **iterates until the deployed whole
  converges** — then stops at the **human consent gate** for the prod ship (G5),
  surfaced as a **release-readiness record** to ratify rather than a bare
  go/no-go. Autonomy is carved by **minimum-regret**: the agent runs the inner and
  outer loops on reversible ephemeral envs unwatched; humans gate the irreversible
  exits (first real users or data, data migrations, spend over threshold,
  security/auth-boundary changes, anything irreversible, and prod). Convergence up
  to that gate is judged by **policy** (canary SLOs + e2e coverage of the changed
  surface + flake < 2%), with **DORA** as the health signal. The pack is
  **repo-scope** (co-located in the build repo where `core` is installed) and
  **reuses** `core`'s `operational-safety` modules + `quality-engineer` +
  `security-reviewer`, consuming the discovery sidecar by convention — **no new
  runtime engine and no new reviewer**. This completes the **company OS**: product
  (discovery) → engineering (build) → SRE/ops (release). *(Implements RFC-0049,
  now Accepted; ADR-0044 records the inner/outer split + the minimum-regret deploy
  carve; the `release-loop` spec is Shipped, all 15 ACs checked.)*

### Changed

- **Shipped skill content is now self-contained — internal RFC/ADR citations removed.**
  Skills, subagents, reference docs, and scripts across `core`, `governance-extras`,
  `atlassian`, `converters`, `research`, and `product-engineering` no longer cite the
  bundle's own governance artifacts (`RFC-00xx`, `ADR-00xx`, `docs/rfc/…`, spec
  task/AC numbers) as load-bearing references — each rule now reads on its own terms.
  Adopters install these skills without the bundle's `docs/` tree, so a dangling
  `RFC-00xx` pointer was an unresolvable reference; the rules are unchanged, only the
  provenance citations are gone. Real external standards (e.g. RFC-1918, RFC-9457) are
  left intact. Also: the `.claude/skills/` README inventory now matches the projected
  skill set, the scaffolded `docs/product/roadmap.md` is marked as a template, and the
  `work-loop` activation hook's docstring points at `tools/hooks/README.md` for wiring.
- **`agentbundle upgrade` reports honestly, and its multi-adapter refusal is
  actionable (CLI 0.10.0).** A same-version re-apply no longer prints
  `upgraded: X -> X`; it reads `re-applied: <pack> @ <scope> <version>
  (already current)`, or names the count of locally edited files kept as
  `.upstream` companions when there were edits — and an upfront notice before the
  confirm tells you how many edits will be preserved. The "pass --adapter"
  refusal (also in `diff` / `uninstall`) now lists each installed adapter **with
  its version**, e.g. `claude-code (0.9.0), codex (0.9.0)`, so the next command
  is obvious without a second lookup.
- **The traceability lint gains a root→leaf reachability pass (core 0.7.1).** On the
  authoritative sidecar graph, `work-loop`'s `lint-traceability.py` now flags every
  node that does not lie on a path from `root` to a leaf — a **`UNREACHABLE`
  (disconnected subtree)** finding, additive to and non-overlapping with the
  existing per-node orphan check. Where the presence check caught only the orphan
  *tip* of a broken branch, reachability catches the **whole** stranded subtree —
  the refinement the `discovery-loop` cascade backstop depends on (RFC-0053 AC34).
  A cross-repo reference resolved through the value-stream rollup is a clean
  terminus (a legitimately federated graph is never failed); an *unresolvable*
  cross-repo hop is surfaced informationally, **never silently counted as closed**
  (the sidecar is untrusted input — a fabricated edge must not green a stranded
  subtree). `UNREACHABLE` joins the `--strict` tier (exit 1); dangling edges and
  cycles stay hard in every mode. Reachability runs in sidecar mode only — a
  standalone derived graph is legitimately partial and multi-root. The
  `discovery-loop` skill's traceability seam is updated to record the dependency as
  met. *(Amends the `traceability-lint` spec; closes the
  `discovery-loop-traceability-reachability` backlog item and the RFC-0048
  § Amendments 2026-06-30 cross-spec gap.)*

### Added

- **The discovery-side producer skills now emit the traceability markers the
  structural-orphan lint reads (experience 0.3.0, product-engineering 0.10.0).**
  `map-screen-flow`'s per-screen brief carries a bold-body `- **Type:** screen-brief`;
  `map-customer-journey` records each frontstage action as a `- **Action:** <slug>`
  marker and `blueprint-service` each backstage service as a `- **Service:** <slug>`
  marker; `frame-intent`'s intent template gains an optional `- **Kind:**
  outcome|opportunity` field (beside the existing `Level:`), and `decompose-intent`
  carries `Kind:`/`Level:` onto decomposed child intents. `work-loop`'s
  `lint-traceability.py` recognizes each producer node **by marker, not path** —
  previously only `frame-domain` emitted markers, so a fail-closed traceability
  up-edge would have been load-bearing on markers that didn't exist. Three
  reconciliations ride along: **CONVENTIONS § 4** is corrected to describe the
  marker as the **bold-body field** the lint reads (it had said "frontmatter
  `type:`" — a factual erratum); the lint's **`recognize_screens` now recurses**
  (`core` 0.7.1 → 0.7.2) so a real nested per-screen brief
  (`screens/<slug>/<screen>.md`) is found, not only a flat one; and the
  **intent↔chain rung mapping** is documented in `product-engineering`'s
  `intent-model.md` (`Kind:` → outcome/opportunity rung, `Level: capability` →
  capability rung), landing the `recognize_ladder` docstring. (Closes the
  `discovery-loop-type-marker-producers` and `screen-brief-nested-path-glob`
  backlog items; RFC-0053 AC36 / DRIFT-G, RFC-0048 note 04 + § Amendments 2026-06-30.)

- **`new-rfc` now drafts RFCs that read from zero prior context and hands you
  decisions you can make in the chat message itself (governance-extras 0.5.0).**
  The skill glosses every project-coined term, acronym, and sibling-RFC
  back-reference in plain language on first use (inline, not a glossary), so a
  reviewer who hasn't read the related RFCs can still follow it; a new
  **cold-reader check** in the pre-handoff gate dispatches a context-denied
  subagent — given only the RFC text — to flag any jargon it can't resolve, so
  inherited vocabulary gets caught before a reviewer hits it cold. The
  research/de-risk handoff now presents each decision **self-contained** — the
  plain-language question, the concrete options with their trade-offs and the
  consequence of each, and a recommendation — so you can decide without opening a
  file. The how-to guide and the Tier-4 eval ride along.

- **The `product-engineering` pack gains the discovery loop — a `discovery-loop`
  skill, a `discovery-lead` agent, and two discovery reviewers (product-engineering
  0.9.0, implementing RFC-0053 / the `discovery-loop` spec).** The upstream loop
  turns a raw idea into a ratified, build-ready **decision brief**: it diverges
  across candidate product shapes (the new `explore-options` skill), converges the
  chosen one through a lens roster, pauses at three consent gates (G0 / G1.5 / G2),
  emits a **connected hypothesis** with validation hooks (the new `plan-validation`
  skill — *converged ≠ validated*), and hands off to `work-loop` at G3 — **with no
  new engine, scheduler, or service**. It ships as content: the agent + skills, a
  carried, versioned **sidecar-schema** reference, and a **plan-tree** template
  asset. `de-risk-intent` gains a validation-hook field and `decompose-intent` an
  optional ranking step. The two discovery reviewers
  (`discovery-threat-reviewer` / `discovery-reliability-reviewer`) are **distinct**
  from `work-loop`'s code reviewers, required at G2, degrading only in depth. A
  coordinator ADR (ADR-0043) records the no-engine, spike-confirmed shape, and a
  four-page Diátaxis guide set under `docs/guides/product-engineering/` covers it.
  The discovery loop is the full-battery home of the self-coverage gate (RFC-0051),
  wired as its pre-G2 phase. *(Eval coverage for the three new skills is a tracked
  follow-up, matching the `frame-domain` precedent.)*
- **`new-spec` and the spec-metadata contract gain an optional `Discovery:` up-edge
  header + discovery-artifact `type:` markers (core 0.7.0, format-only — DRIFT-G).** A
  spec descended from an upstream discovery artifact records it in a `Discovery:`
  header (the discovery-side sibling of `Brief:`), the producer edge a traceability
  check walks; discovery-side artifacts carry a `type:` marker so a check finds them
  by marker, not path. Format only — no operating-model doctrine. This resolves
  RFC-0048 acceptance blocker #4; the traceability lint's `--strict` flip is
  sequenced after the header lands (warn-only until then).
- **The `work-loop` skill now carries the self-coverage gate as a thin, named
  phase (core 0.6.0, implementing RFC-0051 for the `work-loop` slice).** The loop
  doctrine now names its existing passes as the gate's steps (REVIEW *is* the
  fresh-context-adversarial step; the PLAN assumption trio + declined-pattern
  register *are* the pre-mortem hook; `Surface` + DECIDE's apply/defer routing
  *are* the resolve-vs-surface bones), and adds two net-new spec-time checks
  governed by the existing light/full mode — a **resolve-vs-surface disposition
  record** (every open item is resolved-with-referent or surfaced-with-reason) and
  a **conditional domain-grounding** check (fires only on an ungrounded
  load-bearing domain claim, else degrades). One new end-of-session-checklist
  refusal item makes the disposition record non-skippable. A self-contained
  `references/self-coverage/resolve-vs-surface.md` calibrates the
  resolve-vs-surface call. No new reviewer, no new pack, no `docs/CONVENTIONS.md`
  change, no second right-sizing knob; the heavy seven-module design-convergence
  battery stays `discovery-loop`'s, never bolted onto the build loop.
- **The `design-craft` pack grows up into the `experience` pack — the design/UX
  seat that carries the whole design thread from journey to realization
  (experience 0.2.0, implementing RFC-0050 D1–D10; the rename is bridged by the
  already-Accepted ADR-0038, frozen governance untouched).** `design-craft` is
  **renamed in place to `experience`** (dirs, manifests, guides dir, the
  catalogue rows, and the framework-agnosticism CI lint
  `lint-design-craft-agnostic.py → lint-experience-agnostic.py` retargeted to
  `packs/experience/`, env `DESIGN_CRAFT_ROOT → EXPERIENCE_ROOT`; the RFC-0033
  docstring citation and the `(design-craft-pack AC8)` CI step tag stay pinned;
  **no install-time alias**). The seat gains **five new pure-markdown skills**:
  the connective trio **`map-customer-journey`** (stages × actions / emotions /
  pains / opportunities, with a platform/surface axis), **`map-screen-flow`**
  (the journey's screens *sequenced* — transitions, error/edge flows, the
  per-screen state matrix, one per-screen brief per screen, a cross-brief
  consistency pass, and a **non-droppable whole-journey steel thread** that
  degrades from an MCP prototype to a text-only walk but never to nothing, plus
  an optional design-tool handover that is instructions-not-pixels), and
  **`blueprint-service`** (frontstage / line-of-visibility / backstage / support,
  the backstage column the slicing instrument handed to `architect` / `contracts`
  by-name); the inside-out **`map-internal-process`** (APQC L3→L4, as-is + to-be
  with a delta table, SIPOC, a mermaid swimlane, a pain/waste register); and the
  behavioral-pillar craft skill **`interaction-design`** (feedback & timing,
  input & forms, component state machines as mermaid `stateDiagram-v2`, purposeful
  motion honoring reduced-motion, navigation-as-behavior, gesture, cognitive-law
  fit — enriching the per-screen brief, owning no artifact). The three-part
  **`quality-floor`** (handle-all-states + accessibility + reduced-motion, now
  with `permission/denied` as an additional gated state) becomes the pack-shared
  floor every consuming skill defers to. **`aesthetic-direction`** now grounds
  each named goal in persona + precedent + standards + platform conventions and
  carries the surface axis; **`design-critique`** gains a **taste mode** while
  staying an interactive authoring-time skill. A forked-context **`experience-reviewer`**
  agent gives the design step an independent design-time review (grounded
  aesthetic reference + platform fit + cross-brief coherence + the full quality
  floor incl. accessibility) — the only independent a11y check between
  human-value-add gates; collision-hardened name + a design-time-only `description`
  cue (never code diffs, never architecture design docs). Artifact paths resolve
  through a new `[experience]` layout table (`parent = "docs/design"`,
  config → default → discover-by-marker). The five new skills join the pack's
  eval surface (trigger + Tier-4 judge). **Pure-markdown method + manifests + one
  CI-lint rename — no runtime, hook, validator, values table, or pixel comp**
  (RFC-0033 / ADR-0024 guardrails unchanged). User-scope-default: re-aggregates
  `marketplace.json`, not projected into this repo's tree.
- **`voice-and-microcopy` (in `product-engineering`) learns the screen flow
  (product-engineering 0.8.0, RFC-0050 D5).** When a `map-screen-flow` per-screen
  state matrix is present it writes copy **per screen × state**, keyed to the
  matrix; absent one it behaves as before (detect-and-degrade). The `experience`
  and `product-engineering` READMEs now cross-link, so the design seat reads as
  one even though the words live in PE.

- **A new `lint-traceability.py` work-loop script in the `core` pack mechanically
  checks that the product-team artifact chain holds together — `outcome →
  opportunity → capability → screen → action → service → contract → spec →
  component` — and flags every structural orphan (a node with no producer above
  it or no consumer below it), across repositories (core 0.5.0, implementing
  `docs/specs/traceability-lint`; RFC-0048 Decision 6, consuming the RFC-0053
  traceability slot).** It generalizes `receive-brief`'s brief↔spec coverage lint
  to the full nine-layer chain: it reads an authoritative sidecar
  `_state/traceability.json` when present (by convention + its `schema_version`
  stamp) or derives the edge set from local artifacts when absent, resolves each
  cross-repo edge endpoint to **local / satisfied-by-reference / unresolvable**
  (an unresolvable target is reported `unknown / not-yet-catalogued`, never a
  false orphan), and reports orphans informationally (exit 0) while failing hard
  (exit 1) on a dangling edge or a cycle. `--strict` additionally fails on any
  orphan for the convergence / CI gate. It is **structural only** — it never
  judges whether a node is parented to the *right* outcome (semantic scope-creep
  stays a human call). It no-ops cleanly in a repo with no discovery chain, runs
  stdlib-only, and projects to every adapter like `lint-spec-status.py`.

- **A new `frame-domain` skill in the `product-engineering` pack grounds a product
  in its real-world domain and bounds its MVP before any screen, service, or
  architecture is drawn (product-engineering 0.7.0, implementing RFC-0048
  Decision 4).** Run at the discovery loop's G1.5 Domain & MVP point or
  standalone, it produces **two typed artifacts** from one `research`-grounded
  pass: **Domain Framing** (`domain-framing.md`, `type: domain-framing`) — a
  real-world-activity half (how the activity is really done · best practice ·
  naive-design failure modes, grounded by wrapping `research` applied mode) plus a
  brownfield current-system half (reverse-engineered via `decision-archaeology` +
  architecture extraction, omitted with a note when greenfield); and **Scope
  Boundary** (`scope-boundary.md`, `type: scope-boundary`) — the MVP out-of-scope
  register, each excluded capability paired with its appetite reason, the
  scope-creep guard the brief inherits and refines at G3. Each artifact carries a
  stable marker and resolves its write path in three tiers (config → designed
  default → discover-by-marker); findings the wrapped research could not ground
  surface as named residual assumptions, never silent assertions; absent optional
  dependencies degrade cleanly rather than fail. Prompt-only (Charter Principle 3).

### Changed

- **The `new-rfc` skill now documents a convention for recording post-publication
  RFC corrections (governance-extras 0.4.0, implementing RFC-0055).** A published
  RFC's body is frozen, but it can still need a correction — a spec finds a gap, a
  later RFC reframes a decision. The skill now names two lifecycle-keyed sections
  for recording one *inside* the RFC: `## Errata` for a Frozen RFC
  (Accepted/Rejected) and `## Amendments` for an in-flight Open one. Corrections
  are append-only, and once a section accumulates (more than one entry, or any
  entry supersedes another) it splits into an optional two-layer structure — an
  authoritative *current state* layer over a dated *audit trail*, where the
  current-state layer wins on disagreement. The bundled `assets/rfc.md` template
  carries the same shape as a clearly-conditional commented scaffold, so it travels
  into every RFC an adopter drafts without being filled into empty sections.
  Forward-only — existing correction sections are untouched.
- **The `new-adr` skill now helps you isolate the decision before drafting, so
  ADRs stay lean (governance-extras 0.4.0).** Four guidance refinements, none of
  which changes the ADR template's sections or fields: (1) a "frame the decision
  before drafting" step that *offers, doesn't force* — it infers the frame when
  the decision is already crisp and walks a short decision frame (the decision in
  a sentence, the problem, the alternatives, the winning driver, the tradeoff,
  any prior ADR it amends) when the request arrives tangled; (2) stronger title
  discipline — the title *identifies* the decision rather than encoding the whole
  rationale; (3) a one-decision-wide push-back that routes an umbrella of three
  or more load-bearing sub-decisions to an RFC spawning smaller ADRs; (4)
  pointer-like metadata guidance — `Consulted`/`Related` are short reference
  lists, not prose. The behavioral evals gain matching usability assertions.
- **The `new-rfc` skill now sizes each RFC to its two humans — the author and
  the reviewer (governance-extras 0.4.0, implementing RFC-0054).** Four changes,
  the deferred half of the human-consumption work whose RFC-0014-clean half
  shipped in 0.3.2: (1) a `Decision weight: light | standard | heavy` header
  field that right-sizes research depth and the pre-handoff gate — an
  author-picked prose heuristic off `work-loop`'s risk triggers, defaulting to
  `standard`; (2) a top-of-doc `## Reviewer brief` orientation grid that gives a
  reviewer first-screen bearings above "The ask"; (3) "The ask" decisions
  rendered as a table (with a per-decision *reviewer action* column) instead of
  numbered prose; (4) a guided shape/intake step before research that asks
  framing questions when intent is vague and infers when it's already specified
  — offered, never forced. Weight-based right-sizing changes how much research
  and draft an RFC carries, never whether a mandated pre-handoff gate check runs.
- **The `new-rfc` skill now drafts more reviewer- and author-friendly RFCs
  (governance-extras 0.3.2).** Three refinements, none of which changes the
  answer-first template or the research→draft→gate flow: (1) the skill draws an
  explicit *body-as-argument* line — a section that changes the reviewer's
  decision stays in the RFC body, while proof-of-work (research transcripts,
  prior-art matrices, review logs) is summarized and its detail linked from the
  optional `NNNN-notes/` companion; (2) the pre-handoff gate runs the same checks
  but hands back a concise, reviewer-oriented *readiness summary* with the heavy
  proof linked rather than pasted; (3) RFC titles are kept short and identifying,
  with the fuller explanation living in "The ask" so the RFC index stays
  scannable.
- **One pack can now be installed for several adapters at the same scope, and
  the adapters that all read `.agents/skills/` share one skill copy
  (RFC-0052).** The `agentbundle` install identity is now the *footprint* — the
  set of file paths a `(pack, adapter, scope)` install writes, each with its
  content SHA — not the pack name. Installing `research` for `codex` after
  `claude-code` now succeeds (their trees are disjoint), and installing it for
  `cursor` after `codex` *shares* the existing `.agents/skills/` skill files
  instead of fighting over them. A genuine collision — the same path at
  different content, or two different packs claiming one path — is refused,
  naming the conflicting paths; `--force` keeps your copy as a `.upstream`
  companion. `uninstall`, `upgrade`, and `diff` gain an `--adapter`
  disambiguator (required only when a pack has more than one adapter row at the
  scope); `uninstall` removes a shared file only when its last owner goes.
  **Behaviour change:** cursor, gemini, and copilot now project the *skill*
  primitive to the shared `.agents/skills/` home (joining codex) instead of
  their native `.cursor/skills/` / `.gemini/skills/` / `.github/skills/`; their
  agents/hooks/commands are unchanged. After an install that writes a shared
  skill, stderr names the other adapters that read it.
- **The install state file is now schema `v0.4` (`[pack.<name>.adapters.<adapter>]`).**
  Migration is greenfield: a pre-v0.4 state file is refused (on read and write)
  with a re-install prompt — there is no auto-converter, and existing installs
  re-install to regenerate state. Existing cursor/gemini/copilot installs may
  leave a now-unused `.cursor/skills/` / `.gemini/skills/` / `.github/skills/`
  (or `.copilot/skills/`) tree behind; re-installing lands skills at the shared
  home.
- **The `work-loop`'s two reviewer routing tables now live in the depth-library
  skills they route into, not in `work-loop`'s `SKILL.md`.** The security
  boundary→module table moved into `security-checklists`'s Module index and the
  operational failure-mode→module table moved into `operational-safety`'s Module
  index; the `work-loop` `security-reviewer` and `quality-engineer` review steps
  now dispatch against those indexes. This removes the last copy-paste duplication
  between `work-loop` and the two depth libraries — the routing table and the
  modules it routes to can no longer drift apart — and trims `work-loop`'s
  `SKILL.md` further under its size cap. The routing *behavior* is unchanged:
  orchestrator-loaded (never subagent-self-discovered), loaded 1–3 / 1–N and
  never a flat march, with the reliability-vs-security carve and the
  infra-mandatory security pass intact.
- **`work-loop`'s `SKILL.md` moves more situational depth into on-demand
  `references/`.** Three blocks that only matter in a subset of loops were
  relocated out of the always-loaded `SKILL.md` body, each leaving a
  load-bearing trigger/contract one-liner inline: the **visual / manual-QA**
  verification-mode depth → new `references/verification-modes.md` (loaded when a
  task picks that mode); the **pre-EXECUTE review** depth (how the reviewer
  measures a structural change, the re-plan re-fire, the gate mechanism, the
  infra-mandatory secure-design detail) → new `references/pre-execute-review.md`
  (loaded when a trigger fires); and the **supervisor parallel-dispatch gate**
  detail → the existing `references/supervisor-mode.md` (it had been duplicated
  inline). No behavior change — the doctrine is identical, just disclosed
  progressively; `SKILL.md`'s body drops further under its size cap.

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

- **The ADR *template* now offers three optional fields — a first-screen Decision
  summary, a named Revisit-if trigger, and a structured Confirmation
  (governance-extras 0.4.0, implementing RFC-0056).** Distinct from the track-1
  `new-adr` change above (which refined guidance and changed none of the
  template's sections or fields), this track-2 change adds template surface, all
  optional and lean-keyed: (1) a `## Decision summary` block before Context
  (Decision / Because / Applies to / Tradeoff accepted / Revisit if), offered once
  an ADR is long enough that the decision isn't on the first screen and skipped on
  a short one; (2) a named `Revisit if:` trigger whose canonical home is
  Consequences (so it survives deletion of the optional summary), with `stable —
  no foreseeable trigger` as a valid explicit value; (3) a `Mode` / `Signal` /
  `Owner` sub-structure for the existing Confirmation section, where an explicit
  `Mode: none` is preferred over silently dropping the section. None of the three
  is mandatory, the skill and how-to guide describe them in the offer-don't-force
  shape, and the behavioral evals gain three matching format-dependent assertions.
  Forward-only — no existing ADR is converted.
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
- **A how-to for shipping your organization's standard stack as a reusable
  pack.** [*Ship your organization's standard stack as a reusable pack*](../guides/_shared/how-to/build-an-org-stack-pack.md)
  walks a platform lead through composing an org-stack pack from primitives that
  already exist — a filled-in `reference.md` seed (plus optional
  `CONVENTIONS.md` / `AGENTS.md` deltas), `.apm/skills/<framework>/` skills as
  the work-loop's framework-grounding detect target, and a repo-scope profile
  that installs the org's forked `core` first — distributed from a detached fork
  the organization owns via the editable-install path, with no upstream
  dependency. No new machinery. (RFC-0047 Decision 5, ADR-0037 D3.)
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
  against an unfamiliar internal framework or third-party library whose contract
  (a versioned signature, a deprecation, a call-order or lifecycle constraint)
  the agent doesn't already hold, the gate routes to the **same tiered oracle
  protocol** in `contract-acquisition` (the skill formerly named
  `infra-contract-acquisition`, renamed now that it grounds both surfaces) that
  infra uses: **T0** detect the
  installed version (the contract is version-specific); **T1** run the type
  checker / compiler against the call site (`mypy`/`pyright`, `tsc --noEmit`,
  `go build`/`vet`, `cargo check`) plus extract the installed package's API
  surface — the deterministic signature oracle; **T2** consult a curated
  framework-library skill for the behavioral contract no type encodes (the
  supplied-not-bundled tier — detect-and-recommend, never bundled); **T3**
  versioned docs / changelog; and a **runtime invoke-and-observe probe**. It
  declares its oracle tier honestly — strong (typed / stub-equipped) → medium
  (untyped-but-introspectable) → weak (dynamic / C-extension → probe-primary) —
  and `references/oracle-table.md` gives the concrete commands per ecosystem
  (Python / TypeScript / Go / Rust / Java). The bare "grep to verify a symbol
  exists" rule confirmed existence but never the contract; this closes that gap.
  The optional doc-retrieval surface stays **Tier-1 detect-and-stop — never
  auto-installed**, retrieved docs are treated as untrusted data, and
  `quality-engineer` re-derives the cited software contract slice at REVIEW,
  symmetric with infra. No new skill, no bundled per-library data.
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
