# Plan: new-guide conversation-first

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

All changes are in `packs/user-guide-diataxis/.apm/skills/new-guide/` (the source copy). Tasks T1–T7 produce the source files; T8 bumps the version; T9 runs `build-self` to sync all three install copies. T1–T7 have no dependencies between them and can run in parallel; T8 gates on all of them; T9 gates on T8.

The riskiest part is SKILL.md (T1): it must preserve three existing behaviors (gated checkpoint, posture→quadrant table, slug + template scaffolding) while restructuring the procedure around the conversation contract. The reference files (T2–T5) reduce SKILL.md's body size by receiving the per-page-type rules that currently live inline. The evals (T6–T7) are additive.

Verification: manual QA by invoking the revised skill on one create and one revise request in Claude Code, observing the conversation contract gate, the page-type contract load, and the 120-word first-example criterion.

## Constraints

- Skill authoring rules: `.claude/skills/README.md` — skill-relative paths in SKILL.md bodies; no install-path prefixes.
- Three-copy sync: always via `build-self`, never manual copy (byte-identical requirement).
- Eval format: `evals.json` `{skill_name, evals: [{id, prompt, expected_output, assertions}]}`; `eval_queries.json` `[{query, should_trigger}]`.
- `clear-prose.md` extension: product-behavioral rules excluded; prose/structural rules only.

## Construction tests

**Integration tests:** none beyond per-task goal-based checks.

**Manual verification:**
1. Invoke revised `new-guide` with "Rewrite this Jira guide so the reader sees what to ask first." Observe: conversation contract emitted and skill waits before drafting; contract contains all seven fields; appropriate page-type contract loaded.
2. Invoke revised `new-guide` with "Write a new how-to guide for rotating an API token." Observe: conversation contract emitted; How-to page contract loaded; first useful example within 120 words of output.
3. Check that "Fix the broken link in the installation guide" does NOT auto-trigger the skill (routes to normal PR guidance) — covers AC1.
4. Explicitly invoke `new-guide` on "Fix the broken link in the installation guide" and observe that step 1 detects the minor scope and redirects to normal-PR guidance before emitting the conversation contract — covers AC5's explicit-invocation path.

## Design (LLD)

### Design decisions

- **Conversation contract replaces audience contract** — the new contract has seven fields vs. the old three-field contract, and adds first_result, write_boundary, and next_request. The gated "wait for human confirmation" behavior is preserved. Traces to: AC4.
- **Per-page-type rules move to `page-contracts.md`** — the long inline step 4 rules in current SKILL.md (per-quadrant write rules, anti-patterns) move to the reference file. SKILL.md procedure steps shrink to control flow only. Traces to: AC6.
- **Pack page and journey page get no asset templates** — these surfaces don't have fixed quadrant-directory destinations, so `page-contracts.md` is sufficient. Asset templates remain only for the four Diátaxis quadrants. Traces to: AC6, spec Boundaries § Ask first.
- **Two density rules excluded from `clear-prose.md`** — "state result-set coverage" and "summarize large result sets" are Atlassian skill behavioral rules. The remaining eight are page-level structural rules that complement the existing word/sentence-level rules. Traces to: AC9, spec Boundaries § Never do.
- **Minor bump (0.2.0)** — new surface types + major procedure change, backward-compatible (existing usage still activates; no removal of prior capability). Traces to: AC12.

## Tasks

### T1: Rewrite SKILL.md source copy

**Depends on:** none

**Tests:**
- Frontmatter description contains trigger phrases for revise/audit/modernize (AC1)
- Doctrine sentence present near top of body (AC2)
- Intent-first test sentence present in body (AC3)
- Procedure step for conversation contract emits all seven fields (AC4)
- Procedure step for revise mode names the "substantial" threshold and redirects minor edits (AC5)
- Procedure references `references/page-contracts.md`, `references/conversation-first.md`, `references/clear-prose.md`, `references/usability-review.md` by skill-relative path (AC6–AC9)
- Posture→quadrant table present (AC6)
- Slug-pick and asset-template-scaffold steps present for 4 Diátaxis quadrants in create mode (spec Boundaries § Always do)
- "Editing an existing guide" anti-pattern amended to distinguish minor edits (normal PR) from substantial revisions (in scope) (AC14)
- All paths use skill-relative form (`references/X.md`, not `.claude/skills/new-guide/references/X.md`)

**Approach:**
- Open `packs/user-guide-diataxis/.apm/skills/new-guide/SKILL.md`
- Replace frontmatter `description` with the expanded version that triggers on create AND revise/audit/modernize
- Add doctrine sentence + intent-first test sentence at top of body (before `## Prerequisites` or as its own short paragraph)
- Rewrite procedure steps:
  - Step 1: Choose create or revise mode (define substantial-revision threshold inline)
  - Step 2: Pick slug (create) or confirm target file (revise)
  - Step 3: Write the conversation contract [all seven fields; gated — wait for human confirmation]
  - Step 4: Choose the page contract type [include posture→quadrant table for four Diátaxis types; pack/journey pages by context]
  - Step 5: Load the relevant contract from `references/page-contracts.md`
  - Step 6: (Create + four Diátaxis types) Scaffold from the matching asset template
  - Step 7: Draft using conversation-first structure (first useful example within 120 words; Say this / What happens / What you get / What to ask next)
  - Step 8: Load `references/conversation-first.md` and apply
  - Step 9: Load `references/clear-prose.md` and edit for density
  - Step 10: Run `references/usability-review.md`
  - Step 11: Check links and remove cross-quadrant material; cross-link existing siblings
- Amend anti-patterns section: replace "Editing an existing guide via this skill" with a nuanced rule distinguishing minor edits from substantial revisions
- Verification: `scripts/lint-skill-spec.py` passes (skill-relative paths, no install-path prefixes)

**Done when:** `packs/user-guide-diataxis/.apm/skills/new-guide/SKILL.md` is saved; doctrine sentence, intent-first test, conversation contract, and revised anti-pattern are present; `python tools/lint-skill-spec.py` exits 0 for this skill.

---

### T2: Author `references/conversation-first.md`

**Depends on:** none

**Tests:**
- File exists at `packs/user-guide-diataxis/.apm/skills/new-guide/references/conversation-first.md`
- Contains the eight page-level conversation-first structure rules (AC7)
- Does NOT contain the two product-behavioral rules (result-set coverage, truncation state) (spec Boundaries § Never do)

**Approach:**
- Create `packs/user-guide-diataxis/.apm/skills/new-guide/references/conversation-first.md`
- Section heading: `# Conversation-first structure`
- List the eight rules:
  1. Put one observable outcome before the first conceptual explanation.
  2. Put a realistic user request within the first 120 words.
  3. Introduce no more than two product-specific terms before that request.
  4. Do not lead with a component, skill, command, or pack inventory.
  5. Use user language first and implementation names second.
  6. Show the next likely request, not only the initial request.
  7. Separate read-only exploration from remote writes.
  8. Put exhaustive options in reference, not in the main procedure.
- Add a brief framing paragraph explaining the purpose (not a prose style checklist — this is structural/sequencing discipline)

**Done when:** file exists with all eight rules, no product-behavioral rules, prose is in clear-prose style.

---

### T3: Author `references/page-contracts.md`

**Depends on:** none

**Tests:**
- File exists at `packs/user-guide-diataxis/.apm/skills/new-guide/references/page-contracts.md`
- All six surface types are defined: Tutorial, How-to, Reference, Explanation, Pack page, Journey page (AC6)
- Each contract covers: what the first screen must answer, required content, what to move lower
- Per-quadrant write rules from current SKILL.md step 4 are incorporated for the four Diátaxis types
- Pack page and journey page contracts capture the contract matrix from the proposal
- Posture→quadrant table is present (may be duplicated from SKILL.md or cross-referenced)

**Approach:**
- Create `packs/user-guide-diataxis/.apm/skills/new-guide/references/page-contracts.md`
- Section per surface type, each with three subsections: `### First screen`, `### Required content`, `### Move lower`
- For the four Diátaxis types: incorporate the per-quadrant rules currently in SKILL.md step 4 (tutorials anti-pedagogical temptations; how-to problem-named title; reference neutral+complete; explanation About-frame)
- For Pack page: "What can this help me do?" / job cards + natural prompts + result previews + common journey / full skill inventory
- For Journey page: "What happens from start to finish?" / You say + Agent does + You get + Decision / skill cards + implementation vocabulary
- Open with a brief intro explaining when to load only the relevant section
- Include posture→quadrant table (copied from current SKILL.md) so it survives the SKILL.md restructure

**Done when:** file exists with all six surface types, posture table present, per-quadrant rules transferred from current SKILL.md step 4.

---

### T4: Author `references/usability-review.md`

**Depends on:** none

**Tests:**
- File exists at `packs/user-guide-diataxis/.apm/skills/new-guide/references/usability-review.md` (AC8)
- All six checklist items from AC8 are present
- Note: intent-first test sentence ("A reader who does not know any skill or pack name…") lives in SKILL.md, not in this file — do not add it here (AC3 not AC8)

**Approach:**
- Create `packs/user-guide-diataxis/.apm/skills/new-guide/references/usability-review.md`
- Opening: "Run this checklist before finalizing any guide. Each 'yes' is a finding to fix."
- Six items (each phrased as a yes/no question):
  1. Does a first actionable example appear within the first 120 words?
  2. Can the reader begin a real task without knowing any skill or pack name?
  3. Is read/write behavior explicit (what the agent reads vs. what it may change)?
  4. Does the page show at least one realistic follow-up request?
  5. Does skill/command inventory appear after user outcomes, not before?
  6. Does the guide show a visible start AND finish for at least one complete task?
- Verification: verify section — a check on the seven-field conversation contract (reader, job, natural_start, minimum_scope, first_result, write_boundary, next_request all present)

**Done when:** file exists with all six checklist items and the contract-verification section.

---

### T5: Extend `references/clear-prose.md`

**Depends on:** none

**Tests:**
- File at `packs/user-guide-diataxis/.apm/skills/new-guide/references/clear-prose.md` has a new `## Conversation-first structure` section (AC9)
- Eight rules present in the section
- Two product-behavioral rules absent (AC9, spec Boundaries § Never do)
- Existing content unchanged (additive only)

**Approach:**
- Append a new section `## Conversation-first structure` to the end of `packs/user-guide-diataxis/.apm/skills/new-guide/references/clear-prose.md`
- Brief intro: "These are page-level structural rules that complement the word-level checklist above."
- List the eight rules (same content as `conversation-first.md` but in checklist form, e.g., "Put one observable outcome before the first conceptual explanation.")
- Note at the bottom: "For the full framing, see `references/conversation-first.md`."

**Done when:** `clear-prose.md` has the new section appended; existing content byte-identical to before the change; `references/conversation-first.md` is the canonical version, `clear-prose.md` section is the in-checklist form.

---

### T6: Update `evals/eval_queries.json`

**Depends on:** none

**Tests:**
- JSON syntax valid
- 6 new `should_trigger: true` entries (revise/simplify/audit/restructure requests) (AC10)
- 4 new `should_trigger: false` entries (Jira story, Atlas team blockers, README spelling, Diátaxis explanation) (AC10)
- All existing entries unchanged

**Approach:**
- Open `packs/user-guide-diataxis/.apm/skills/new-guide/evals/eval_queries.json`
- Append to the existing array (additive):

  New `true` entries:
  ```json
  {"query": "Rewrite this Jira guide so the reader sees what to ask first", "should_trigger": true},
  {"query": "Turn this skill-list page into a task-led pack page", "should_trigger": true},
  {"query": "Make this Diátaxis how-to less dense", "should_trigger": true},
  {"query": "Add a realistic multi-turn conversation to this guide", "should_trigger": true},
  {"query": "Audit these docs for inventory-first writing", "should_trigger": true},
  {"query": "Revise this journey page to show a complete user flow", "should_trigger": true}
  ```

  New `false` entries:
  ```json
  {"query": "Create a Jira story for password reset", "should_trigger": false},
  {"query": "Show me the Atlas team's blockers", "should_trigger": false},
  {"query": "Fix spelling in this README", "should_trigger": false},
  {"query": "What is Diátaxis and how does it work", "should_trigger": false}
  ```

- Validate JSON syntax with `python -c "import json, sys; json.load(open(sys.argv[1]))" <path>`

**Done when:** the 10 new query strings are present in the file and JSON is valid (assert on content, not a brittle total count).

---

### T7: Update `evals/evals.json` with output rubric

**Depends on:** none

**Tests:**
- JSON syntax valid
- Second eval (id: 2) present in the `evals` array (AC11)
- Good-artifact assertions present: reader+job stated, natural-language request near top, first result explained, at least one follow-up, read/write boundaries explicit, inventory after outcomes, reference material out of primary flow
- Exactly five discrete negative assertions present: (1) no architecture-first opener, (2) no skill-list before task, (3) reader needs no skill name to begin, (4) not isolated snippets only / shows agent response (compound), (5) no indiscriminate quadrant mixing — matches AC11's effective count of five
- `skill_name` unchanged: `"new-guide"`

**Approach:**
- Open `packs/user-guide-diataxis/.apm/skills/new-guide/evals/evals.json`
- Add second element to the `evals` array:
  ```json
  {
    "id": 2,
    "prompt": "Create or revise a user-facing guide following the conversation-first doctrine.",
    "expected_output": "A guide that states the reader and their job early, shows a natural-language request near the top (within the first 120 words), explains the first result the reader gets, shows at least one realistic follow-up request, makes read/write boundaries explicit, puts skill/command inventory after user outcomes rather than before, and keeps reference material out of the primary flow. It does not open with product architecture or a skill list. The reader can begin a task without knowing any skill or pack name. The page shows a visible start and finish for at least one complete task.",
    "assertions": [
      "States the reader and their job — the page has an implied or explicit audience",
      "Shows a natural-language request near the top, within the first 120 words",
      "Explains the first result — the reader knows what they will get before the detail starts",
      "Shows at least one realistic follow-up request, not only the entry request",
      "Makes read/write boundaries explicit — separates what the agent reads from what it may change",
      "Puts skill/command inventory after user outcomes, not before",
      "Keeps reference material (exhaustive options, parameter tables) out of the primary flow",
      "Does not open with product architecture, an internal component diagram, or a skill/pack list",
      "Does not require the reader to know any skill or pack name to begin",
      "Is not a collection of isolated prompt snippets — shows what the agent returns",
      "Does not indiscriminately mix Diátaxis quadrants — tutorial material is not blended with reference"
    ]
  }
  ```
- Validate JSON syntax

**Done when:** `evals.json` has 2 evals; JSON is valid; assertions cover all AC11 criteria.

---

### T8: Bump version in `pack.toml` and `plugin.json`

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T10, T11

**Tests:**
- `pack.toml` version field is `"0.2.0"` (AC12)
- `.claude-plugin/plugin.json` version field is `"0.2.0"` (AC12)

**Approach:**
- Edit `packs/user-guide-diataxis/pack.toml`: change `version = "0.1.7"` → `version = "0.2.0"`
- Edit `packs/user-guide-diataxis/.claude-plugin/plugin.json`: update version field to `"0.2.0"`
- Verify with `grep '"0.2.0"' packs/user-guide-diataxis/pack.toml` and `grep '"0.2.0"' packs/user-guide-diataxis/.claude-plugin/plugin.json`

**Done when:** both files show `0.2.0`; no other fields changed.

---

### T9: Run `build-self` and verify three-copy parity

**Depends on:** T8

**Tests:**
- All three copies of SKILL.md byte-identical (AC13)
- All three copies of each reference file byte-identical (AC13)
- All three copies of each eval file byte-identical (AC13)

**Approach:**
- Run the project's `build-self` command (or `make build-self` — check `Makefile` for the correct target)
- Verify parity with `diff packs/user-guide-diataxis/.apm/skills/new-guide/SKILL.md .claude/skills/new-guide/SKILL.md` and equivalent for `.agents/skills/new-guide/SKILL.md`
- Verify reference files: `diff` for `clear-prose.md`, `conversation-first.md`, `page-contracts.md`, `usability-review.md` across the three install paths
- Verify eval files: `diff` for `eval_queries.json`, `evals.json`
- If any diff is non-empty, investigate the build-self output rather than hand-copying

**Done when:** all `diff` calls return empty; `git status` shows changes under `packs/`, `.claude/skills/new-guide/`, `.agents/skills/new-guide/`, and `.claude-plugin/marketplace.json` (version propagated by `build-self`).

---

### T10: Write changelog entry

**Depends on:** none

**Tests:**
- `docs/product/changelog.md` has a `user-guide-diataxis 0.2.0` entry under `## [Unreleased]` (AC15)
- Entry names: broadened trigger (create + substantially revise), conversation contract (7 fields, gated), six page-type contracts in `page-contracts.md`, three new reference files

**Approach:**
- Open `docs/product/changelog.md` and locate `## [Unreleased]`
- Add an entry following the existing format for pack version bumps in this file
- Content: `user-guide-diataxis 0.2.0` — skill trigger broadened to cover create and substantially-revise requests; conversation contract (reader, job, natural_start, minimum_scope, first_result, write_boundary, next_request) replaces audience contract as the gated checkpoint; six page-type contracts in new `references/page-contracts.md`; three new reference files (`conversation-first.md`, `page-contracts.md`, `usability-review.md`); `clear-prose.md` extended with conversation-first structure rules; evals updated with revise/audit trigger cases and output-quality rubric.

**Done when:** entry present under `## [Unreleased]` with the four named items; existing entries unchanged.

---

### T11: Review and update `pack.toml [pack.first-value]`

**Depends on:** T1

**Tests:**
- `[pack.first-value]` in `pack.toml` accurately describes the revised skill's gate, or has a comment explaining why it intentionally describes only create-mode scaffold (AC16)

**Approach:**
- Read the current `[pack.first-value]` block in `packs/user-guide-diataxis/pack.toml`
- Compare `safety-gate`, `starter-task`, `starter-prompt`, and `expected-result` against the revised T1 SKILL.md procedure
- If `safety-gate` still describes only the create-mode scaffold preview (not the conversation-contract gate), update it to name the conversation contract as the first gate
- If `starter-task`/`starter-prompt` are still scaffold-only, update or note that the first-value path is intentionally the create-mode scaffold (simpler entry point)
- Minimal change — don't rewrite the whole block

**Done when:** `[pack.first-value]` accurately reflects the conversation-contract gate for create mode, or carries a comment explaining why the create-scaffold path remains the install-time entry point.

---

## Rollout

Pure skill-body and eval update. No infrastructure. No deployment sequencing. Ships as a normal PR; install copies are synced via `build-self` before commit. No data migration or published event. Reversible by reverting the PR.

**Deferred:** `web/src/content/packs/user-guide-diataxis.md` and any matching journey content file still describe the skill as "scaffolds a new guide document." These are hand-maintained web files not regenerated by `build-self`. Updating them is a follow-on PR; the PR description will note this deferral.

## Risks

- **SKILL.md rewrite loses an existing behavior** — the three behaviors to preserve (gated checkpoint, posture table, slug + scaffold) are explicitly listed in the task T1 tests; the adversarial-reviewer pass should catch drift.
- **`build-self` is slow or not available** — if `build-self` is unavailable, investigate `make build-self` or the equivalent; do not hand-copy files.
- **`lint-skill-spec.py` fails on a skill-relative path** — verify that all new `references/` paths use the skill-relative form before running the linter.

## Changelog

- 2026-07-23: initial plan.
- 2026-07-23: added T10 (changelog entry, AC15), T11 (pack.first-value review, AC16), marketplace.json to T9 expected changes (AC12), manual-QA step 4 for AC5 explicit-invocation redirect, fixed T7 assertion count to five discrete negatives, fixed T6 done-when to content-based check, fixed T4 mislabel on intent-first test, noted web-description deferral in Rollout — all from adversarial-reviewer pass.
