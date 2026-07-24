# Spec: new-guide conversation-first

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `new-guide` skill in `packs/user-guide-diataxis` guides agents through authoring user-facing documentation. Today it covers only creating new guides and refuses revision work entirely. Two gaps limit its value: it has no mechanism to enforce conversation-first page structure (where the reader sees a natural-language task before any skill inventory), and its trigger set doesn't activate on rewrite or audit requests that need exactly the same discipline.

This spec extends the skill in three ways. First, the trigger broadens from "create a new guide" to "create or substantially revise" — capturing rewrites, usability audits, and conversation-first retrofits. Second, the procedure gains a conversation contract as its gated checkpoint, replacing the existing audience contract: the contract makes visible the reader, their job, their natural first request, the minimum scope the agent needs, the expected first result, the read/write boundary, and the most likely follow-up. Third, page-type contracts — for all six surface types including pack pages and journey pages — move out of the SKILL.md body into `references/page-contracts.md`, with three companion references (`conversation-first.md`, `usability-review.md`, and an extension to `clear-prose.md`) making the conversation-first structure explicit and reviewable. Evals are updated to cover the new trigger surface and to grade output on the new quality bar.

The key doctrine: **Diátaxis determines where information lives. User intent determines how readers enter it.** A reader who does not know any pack or skill name must still be able to begin a real task from the first screen.

## Boundaries

### Always do

- Keep byte-identical copies across all three install paths (`packs/user-guide-diataxis/.apm/skills/new-guide/`, `.claude/skills/new-guide/`, `.agents/skills/new-guide/`) — sync via `build-self`, never manual copy.
- Preserve the posture→quadrant mapping table (the Diátaxis load-bearing logic) in the rewritten SKILL.md.
- Retain the gated checkpoint behavior — the skill must wait for human confirmation of the conversation contract before proceeding to draft.
- Keep the slug-pick and asset-template-scaffold steps for the four Diátaxis quadrants in create mode.
- Preserve all non-trivially-changed eval query entries (`eval_queries.json` additions are additive; no existing `true` case becomes `false`, and "Update the existing installation how-to to mention the new --force flag" stays `should_trigger: false`).

### Ask first

- Any change to the asset templates (`assets/tutorials.md`, `assets/how-to.md`, `assets/reference.md`, `assets/explanation.md`) — they are not in scope for this spec.
- Adding asset templates for pack pages or journey pages — decided out of scope here; `page-contracts.md` is sufficient.
- Any change to the version-bump magnitude (patch vs. minor) if the decision feels wrong at implementation time.

### Never do

- Write prose into any spec file that contradicts CONVENTIONS.md § 4.
- Add product-behavioral rules to `clear-prose.md` (e.g., "state result-set coverage when the user asks for 'all'" — this is an Atlassian skill rule, not a documentation prose rule).
- Touch `docs/guides/` content — this spec changes the skill, not the guides the skill has already produced.
- Add new top-level directories to the pack.

## Testing Strategy

All changes are to skill-body text, reference files, and eval fixtures — no application code.

- **Goal-based check** — JSON syntax validity for `evals.json` and `eval_queries.json`; version bump present in `pack.toml`, `.claude-plugin/plugin.json`, and propagated to `.claude-plugin/marketplace.json` via `build-self`; three install-copy files byte-identical after `build-self`; `tools/run-pack-evals.py --skill new-guide --mode activation` exercises the `eval_queries.json` cases (or its invocation is recorded in the manual-QA note if the ANTHROPIC_API_KEY secret is not configured in this run).
- **Manual QA (visual / artifact exercise)** — invoke the revised skill in Claude Code on a real guide-authoring request; observe that: (a) the conversation contract is emitted and the skill waits before proceeding, (b) the correct page-type contract is loaded, (c) the first useful example appears within 120 words of the draft, (d) no skill or pack name is required to begin.

## Acceptance Criteria

- [x] AC1: The frontmatter `description` triggers on create AND substantially-revise requests (rewrite, restructure, audit, simplify, modernize a guide/pack-page/journey-page) and does NOT trigger on: Jira story creation, team-status queries, README spelling fixes, conceptual Diátaxis questions, or minor single-line updates to existing guides.
- [x] AC2: The doctrine sentence "Diátaxis determines where information lives. User intent determines how readers enter it." appears at or near the top of the SKILL.md body.
- [x] AC3: The intent-first test is stated in the skill: "A reader who does not know any pack or skill names must still be able to begin a real task from the first screen."
- [x] AC4: The skill procedure produces a conversation contract with all seven fields (reader, job, natural_start, minimum_scope, first_result, write_boundary, next_request) **before** any prose is drafted, and the procedure explicitly waits for human confirmation of the contract before continuing.
- [x] AC5: The procedure distinguishes create mode from revise mode. Revise mode requires the proposed change to be substantial (restructure, quadrant correction, major rewrite, conversation-first audit); minor edits (typo, single-line command update, link fix) are redirected to a normal PR. The redirect applies whether the skill is auto-triggered by the frontmatter description or explicitly invoked — when explicitly invoked on a minor edit, the skill detects the minor scope in step 1 and redirects before emitting the conversation contract.
- [x] AC6: `references/page-contracts.md` exists and defines the required content and "move lower" rules for all six surface types: Tutorial, How-to, Reference, Explanation, Pack page, Journey page. The posture→quadrant table for the four Diátaxis types is present **in SKILL.md** (not delegated solely to `page-contracts.md`).
- [x] AC7: `references/conversation-first.md` exists and contains the conversation-first structure rules (observable outcome before explanation, realistic request within 120 words, no inventory-first lead, user language before implementation names, next request shown, read/write boundary explicit, exhaustive options in reference).
- [x] AC8: `references/usability-review.md` exists and contains a reviewable checklist including: first actionable example within 120 words; reader needs no skill name to begin; read/write behavior explicit; at least one realistic follow-up shown; skill inventory appears after user outcomes; a complete task has visible start and finish.
- [x] AC9: `references/clear-prose.md` gains a new `## Conversation-first structure` section with the eight page-level usability rules (the two product-behavioral rules — result-set coverage and truncation-state — are excluded).
- [x] AC10: `evals/eval_queries.json` includes the six new should-trigger queries (rewrite/simplify/audit/restructure requests for existing guides) and the four new should-not-trigger queries (Jira story, team-status query, README spelling, Diátaxis explanation).
- [x] AC11: `evals/evals.json` includes a second eval (id: 2) grading output quality: the rubric asserts that a good artifact states reader and job, shows a natural-language request near the top, explains the first result, shows at least one follow-up, makes read/write boundaries explicit, puts inventory after outcomes, and keeps reference material out of the primary flow. It asserts against exactly six weak-artifact patterns: architecture-first opener; skill-list before task; reader must know a skill name to begin; isolated snippets only, no agent response; indiscriminate quadrant mixing. (Five discrete negatives — the sixth pattern "no agent response shown" is composed with "isolated snippets only" as a single compound assertion, reducing the effective count to five discrete checks; AC11 counts five.)
- [x] AC12: `pack.toml` version is bumped to `0.2.0`; `.claude-plugin/plugin.json` version matches; `.claude-plugin/marketplace.json` reflects `0.2.0` after `build-self`.
- [x] AC13: After `build-self`, the three install copies of SKILL.md, all reference files, and all eval files are byte-identical.
- [x] AC14: The "Editing an existing guide via this skill" anti-pattern is amended — it no longer is a blanket refusal but redirects minor edits to a normal PR, while substantial revisions are in scope.
- [x] AC15: `docs/product/changelog.md` gains a `user-guide-diataxis 0.2.0` entry under `## [Unreleased]` describing the broadened trigger, conversation contract, six page-type contracts, and three new reference files.
- [x] AC16: `pack.toml [pack.first-value]` is reviewed against the revised procedure and either updated to reflect the conversation-contract gate or annotated with a comment explaining why it intentionally describes only the create-mode scaffold path.

## Assumptions

- Technical: three install copies (pack source, `.claude/skills/`, `.agents/skills/`) are byte-identical and synced via `build-self` (source: Explore agent inspection, 2026-07-23).
- Technical: `references/clear-prose.md` exists in all three copies; new reference files follow the same pattern (source: Explore agent inspection, 2026-07-23).
- Technical: `evals.json` uses `{skill_name, evals: [{id, prompt, expected_output, assertions}]}` format; `eval_queries.json` is `[{query, should_trigger}]` (source: file reads, 2026-07-23).
- Technical: pack version bump requires `pack.toml` and `.claude-plugin/plugin.json` to both be updated, followed by `build-self` (source: project memory — pack-bump-needs-plugin-json).
- Product: "journey page" and "pack page" are user-facing documentation surfaces (not design artifacts), describing a complete product journey or a pack's capabilities — distinct from the experience-design pack's journey mapping artifacts (source: proposal text + Explore agent inspection, 2026-07-23).
- Product: the two product-behavioral density rules ("state coverage/truncation when user asks for 'all'" and "summarize large result sets before listing records") are Atlassian skill behavioral rules that do not belong in `clear-prose.md` (source: adversarial analysis, 2026-07-23).
- Process: no RFC is required for this skill doctrine change; the change is additive and backward-compatible in adoption (source: user instruction — "do this in the work-loop").
- Process: minor version bump (0.2.0) is appropriate — new surface types and major procedure change, no breaking change to existing usage (source: judgment call, may need confirmation at T8).
