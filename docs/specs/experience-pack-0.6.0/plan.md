# Plan: Experience pack 0.6.0 — surface-genre uplift

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Follows:** RFC-0066

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially,
> note why in the changelog at the bottom.

## Approach

Nine tasks in dependency order. The rename-first ordering is load-bearing:
all new skills (D3, D4) and all extensions (D5) reference canonical post-rename
slugs, so the 9 directory renames run first. After the rename wave, T2 (screen-brief
template) and T3 (design-principles skill) are independent and can be reviewed in
parallel, though execution is sequential. T4 (6 genre skills) and T5a/T5b
(extensions) follow. T7 (web/ marketing site), T8 (docs guides content pass), and
T6 (metadata, ADR, changelog) close out the implementation tasks. T9 (journey doc
update) is the final step and depends on T6 confirming the as-built state.

All tasks land in a single PR — RFC-0066 specifies one coherent PR at 0.6.0.
Every task runs `tools/lint-experience-agnostic.py packs/experience/` before
marking done; the post-rename grep is the gate for T1.

The riskiest part is T1 (the rename sweep): RFC-0066's spike confirmed ~43 files
in `packs/experience/` contain old slug references across SKILL.md bodies,
`references/*.md`, `assets/*` templates, `evals/*.json`, the agent file, README,
and pack.toml — plus 4 files in `docs/guides/experience/` — plus cross-pack
inbound references in core/product-engineering/research. The post-rename grep
covers all file types and directories; T1 does not advance until the grep returns
zero and the cross-pack audit is resolved.

## Constraints

- RFC-0066: all 8 decisions (D1–D8) and all follow-on artifacts required in the PR.
- ADR-0038: alias-free rename shape — rename live surface, bridge frozen governance,
  no install-time alias.
- ADR-0024: agnosticism guardrails — no values tables, no platform primitives in
  any new or modified skill.
- `tools/lint-experience-agnostic.py` is the mechanical gate and runs after every
  task that modifies skills.

## Construction tests

**Cross-task integration:**
- Post-rename grep (gate for T1 — covers all file types including JSON):
  `grep -r "map-customer-journey\|blueprint-service\|map-screen-flow\|map-internal-process\|aesthetic-direction\|layout-and-information-architecture\|design-critique\|design-system-foundations\|copy-direction" packs/experience/ docs/guides/experience/ --include="*.md" --include="*.toml" --include="*.json"`
  → zero results.
- Agnosticism lint (runs after T1, T2, T3, T4, T5a, T5b):
  `python tools/lint-experience-agnostic.py packs/experience/` → exit 0.
- Final skill count: `ls packs/experience/.apm/skills/ | wc -l` → 18.
- Pack version: `grep 'version = "0.6.0"' packs/experience/pack.toml` → matches.

**Manual QA (run at T6 before declaring done):**
- Read each of the 7 new skills end-to-end: methodology complete, no ADR-0024
  violations, cross-references use canonical slugs.
- Read each of the 6 extended skills at the changed sections: additions present
  and correctly placed.
- Confirm `## Genre-specific notes` has all 7 sub-sections as comment blocks.
- Confirm ADR-0052 has the 9-row mapping table and no-alias statement.

## Design (LLD)

### Design decisions

- **Rename-first ordering:** D7 runs before D1/D3/D4/D5 so all new and extended
  content uses canonical names; no content ever references a pre-rename slug.
  Traces to: AC6.
- **Single PR:** All 8 decisions ship together — genre skills without renames
  would mix canonical and invented names within the same pack; renames without
  genre skills would leave a partial system. Traces to: AC1–AC13.
- **`surface-genre:` in screen-brief frontmatter:** Declared once at the planning
  step, read by all downstream skills. Standalone invocations degrade to inline
  elicitation ("What kind of surface is this?"). Traces to: AC1, AC2.
- **ADR-0052 in the same PR:** Creates the frozen-governance bridge for the renames
  simultaneously with the live surface change, per ADR-0038 precedent. Traces to: AC9.
- **evals list updated in T1 (slugs) and T6 (version + new skills):** T1 touches
  the evals list only to rename existing slugs; T6 adds the 7 new skills to the
  list and bumps the version. Separates mechanical rename from policy decision
  (which new skills qualify under RFC-0037/ADR-0028). Traces to: AC7.

### Component / module decomposition

```
packs/experience/.apm/skills/
├── [renamed T1] journey-mapping/          (was map-customer-journey) ← T5a
├── [renamed T1] service-blueprint/        (was blueprint-service)    ← T5a
├── [renamed T1] user-flow/                (was map-screen-flow)      ← T2
├── [renamed T1] process-mapping/          (was map-internal-process)
├── [renamed T1] creative-direction/       (was aesthetic-direction)  ← T5b
├── [renamed T1] information-architecture/ (was layout-and-IA)        ← T5a
├── [renamed T1] design-review/            (was design-critique)      ← T5b
├── [renamed T1] design-system/            (was design-system-foundations)
├── [renamed T1] tone-of-voice/            (was copy-direction)
├── [unchanged]  content-design/           ← T1 cross-ref update
├── [unchanged]  interaction-design/       ← T5a
├── [new T3]     design-principles/
├── [new T4]     conversion-design/
├── [new T4]     documentation-design/
├── [new T4]     analytical-design/
├── [new T4]     marketplace-design/
├── [new T4]     informational-design/
└── [new T4]     workspace-design/
```

### Behavior & rules

**ADR-0024 agnosticism in new skills:** Genre-specific skills name real-world
practitioner sites as "canonical aesthetic reference" study subjects in D4 and D5f.
This is permitted by ADR-0024 when framed as "internalize the philosophy, not
copy the surface." Naming a tool, framework, or CMS as a prescriptive implementation
target is not permitted. Each new skill is checked against the lint before T advances.

**Standalone elicitation fallback (D1):** Each downstream skill gains an
instruction: "Check the per-screen brief for `surface-genre:`. If no brief
exists, elicit: 'What kind of surface is this?'" This ensures genre routing is
always available regardless of invocation order. Added to each relevant skill
in T5a and T5b (not enumerated here — each task's Tests: confirms presence).

## Tasks

---

### T1: Rename 9 skill directories and sweep all cross-references (D7)

**Depends on:** none

**Touches:** `packs/experience/.apm/skills/` (all 11 dirs + their `evals/evals.json`), `packs/experience/.apm/agents/experience-reviewer.md`, `packs/experience/README.md`, `packs/experience/pack.toml`, `packs/experience/.claude-plugin/plugin.json` (description only; version bump stays in T6), `docs/guides/experience/**`, `packs/experience/.apm/skills/content-design/SKILL.md`, cross-pack inbound files in `packs/core/`, `packs/product-engineering/`, `packs/research/` (imperative references only; voice-and-microcopy `copy-direction` ref backlogged not updated; `.py` code-comment refs out of scope)

**Tests:**
- Post-rename grep returns zero across all file types:
  `grep -r "map-customer-journey\|blueprint-service\|map-screen-flow\|map-internal-process\|aesthetic-direction\|layout-and-information-architecture\|design-critique\|design-system-foundations\|copy-direction" packs/experience/ docs/guides/experience/ --include="*.md" --include="*.toml" --include="*.json"` → zero results.
- Cross-pack audit: same grep extended to `packs/core/ packs/product-engineering/ packs/research/` with `--include="*.md" --include="*.toml" --include="*.json"` (prose-only matches and voice-and-microcopy exception recorded in backlog; `.py` code-comment refs noted as out of scope; imperative invocation matches fixed).
- `ls packs/experience/.apm/skills/ | sort` shows exactly 11 directories with canonical names.
- `python tools/lint-experience-agnostic.py packs/experience/` exits 0.

**Approach:**
1. Run 9 `mv` commands in `packs/experience/.apm/skills/`:
   - `mv map-customer-journey journey-mapping`
   - `mv blueprint-service service-blueprint`
   - `mv map-screen-flow user-flow`
   - `mv map-internal-process process-mapping`
   - `mv aesthetic-direction creative-direction`
   - `mv layout-and-information-architecture information-architecture`
   - `mv design-critique design-review`
   - `mv design-system-foundations design-system`
   - `mv copy-direction tone-of-voice`
2. In **every** skill directory (both the 9 renamed and the 2 unchanged — `content-design` and `interaction-design`): update all cross-references to renamed slugs. Specifically:
   - In each renamed SKILL.md: update the `name:` frontmatter value and every body cross-reference.
   - In `content-design/SKILL.md`: update references to `map-customer-journey`, `map-screen-flow`, `copy-direction` (→ `journey-mapping`, `user-flow`, `tone-of-voice`).
   - In `interaction-design/SKILL.md` and `interaction-design/references/interaction-pillars.md`: update references to `design-critique`, `layout-and-information-architecture`, `aesthetic-direction`, `map-screen-flow` (→ canonical names).
3. In all `references/*.md` and `assets/*` files under **every** skill dir: update every cross-reference to a renamed slug. Pay special attention to cross-directory path references (e.g. `../design-critique/references/quality-floor.md` → `../design-review/references/quality-floor.md`, `../layout-and-information-architecture/...` → `../information-architecture/...`) — these are physical paths that break after `mv`.
4. In **every** skill's `evals/evals.json` (if present): update `skill_name` field to the canonical slug; update any evaluation query or description text that names old slugs. This includes `content-design/evals/evals.json` (contains `copy-direction` and `map-screen-flow` references) and `interaction-design/evals/evals.json` (contains `design-critique`, `layout-and-information-architecture` references).
5. In `packs/experience/.apm/agents/experience-reviewer.md`: update all 9 slug
   references.
6. In `packs/experience/README.md`: update all slug references.
7. In `packs/experience/pack.toml`:
   - `[pack.evals]` skills list: replace old slugs with new slugs (version bump in T6).
   - `description` field: rewrite to use canonical names and note the 18-skill chain.
   (Moving description sweep here, not T6, so T1's grep gate can pass.)
8. In `packs/experience/.claude-plugin/plugin.json`:
   - Update `description` field to use canonical skill names and note the 18-skill chain.
   (Version bump from 0.5.0 → 0.6.0 stays in T6 step 2. Moving description here so the T1 grep gate can pass — plugin.json is inside `packs/experience/` and is included in the `*.json` grep.)
9. In `docs/guides/experience/` (4 files): update all old slug references.
10. In `packs/experience/.apm/skills/content-design/SKILL.md`: update
    `copy-direction` → `tone-of-voice`; leave `voice-and-microcopy` references
    unchanged.
11. **Cross-pack audit:** Run the grep across `packs/core/ packs/product-engineering/ packs/research/` with `--include="*.md" --include="*.toml" --include="*.json"`. For each match:
    - **Imperative invocation** (e.g. "invoke `aesthetic-direction`", "run `design-critique`"): update to the canonical slug.
    - **`packs/product-engineering/.apm/skills/voice-and-microcopy/SKILL.md`** referencing `copy-direction`: **do not edit** — this reference belongs to the voice-and-microcopy→ux-writing rename deferred to a separate RFC (spec § Ask first). Record in `docs/backlog.md`.
    - **Prose-only description** (educational text, not an agent instruction): add a one-line entry to `docs/backlog.md` under `experience-pack-rename-cross-pack-prose` and leave the file unchanged.
    - **`.py` code-comment references** (e.g. docstrings in tool scripts naming old skills): out of scope — these are in tool code, not agent-invocable surfaces. Record in backlog if found; do not edit.
12. Run post-rename verification grep (experience pack + guides + JSON); confirm zero results before proceeding.

**Done when:** Post-rename grep (including JSON) returns zero; cross-pack audit complete; lint exits 0.

---

### T2: Add surface-genre field and Genre-specific notes to user-flow template (D1)

**Depends on:** T1

**Touches:** `packs/experience/.apm/skills/user-flow/assets/screen-brief-template.md`, `packs/experience/.apm/skills/user-flow/SKILL.md`

**Tests:**
- `grep 'surface-genre:' packs/experience/.apm/skills/user-flow/assets/screen-brief-template.md` → matches.
- `grep '## Genre-specific notes' packs/experience/.apm/skills/user-flow/assets/screen-brief-template.md` → matches.
- Template has 7 comment-block sub-sections: `### If marketing`, `### If documentation`, `### If informational`, `### If analytical`, `### If marketplace`, `### If workspace`, `### If transactional-journey`.
- `user-flow/SKILL.md` "When to invoke" has exactly 5 items; item 5 is the genre confirmation step.
- `python tools/lint-experience-agnostic.py packs/experience/` exits 0.

**Approach:**
1. Edit `user-flow/assets/screen-brief-template.md`:
   - Add `surface-genre: <marketing | documentation | informational | analytical | transactional-journey | marketplace | workspace>` to YAML frontmatter after the `surface:` field.
   - In `## Place in the whole`, add: `- Surface genre: <genre> — determines design patterns and IA approach`.
   - Append `## Genre-specific notes` section with the 7 sub-sections from RFC-0066 D1 as comment blocks (implementers uncomment and populate only the matching sub-section).
2. Edit `user-flow/SKILL.md`:
   - In "When to invoke", add item 5: "**You know the surface genre.** Before drafting briefs, confirm the genre from `marketing | documentation | informational | analytical | transactional-journey | marketplace | workspace`. If absent from context, elicit inline: 'What kind of surface is this?' Genre is orthogonal to platform — a marketplace surface on iOS is both `marketplace` AND `iOS`. Genre determines which design pattern families and IA approaches apply downstream."
   - Add standalone elicitation fallback note (for skills invoked without a brief).
3. Run lint.

**Done when:** Grep confirms field and section present; SKILL.md has 5-item checklist; lint exits 0.

---

### T3: Create design-principles skill (D3)

**Depends on:** T1

**Touches:** `packs/experience/.apm/skills/design-principles/` (new directory)

**Tests:**
- `ls packs/experience/.apm/skills/design-principles/SKILL.md` → exists.
- SKILL.md contains: NNGroup 4-step model with step labels (insight → user-grounded → arbitration-aware → team-owned); the arbitration test phrase; example well-formed principles (at least 2); evidence-level carry-through rule; chain position (consumed by list).
- `python tools/lint-experience-agnostic.py packs/experience/` exits 0.

**Approach:**
1. Create `packs/experience/.apm/skills/design-principles/` directory.
2. Write `design-principles/SKILL.md`:
   - **Frontmatter:** `name: design-principles`, `description:` (one-line), `triggers`, `phase: define` (positions it in the Define phase of the design chain).
   - **What it produces:** 3–5 named design principles; form `[Imperative verb] + [what] + [why/for whom]`; arbitration test.
   - **Not brand values:** distinction between design principles (decision-making tools) and brand values (belong in `creative-direction`).
   - **Procedure:** NNGroup 4-step model: (1) identify core product values → (2) articulate why each matters to users → (3) surface known tradeoffs → (4) draft collaboratively, converge through critique. Map each step to: insight → user-grounded → arbitration-aware → team-owned.
   - **Evidence-level carry-through:** if the source journey map is `assumption-based`, derived principles are marked as hypotheses.
   - **Chain position:** Consumes `journey-mapping` peak moments and highest-opportunity pains. Consumed by: `creative-direction`, `information-architecture`, `content-design`, `design-review`.
   - **Example principles** (from RFC-0066 D3): 3 well-formed examples to anchor the pattern.
3. Run lint.

**Done when:** SKILL.md exists with all required sections; lint exits 0.

---

### T4: Create 6 genre-specific skills (D4)

**Depends on:** T1, T2, T3

**Touches:** `packs/experience/.apm/skills/conversion-design/`, `packs/experience/.apm/skills/documentation-design/`, `packs/experience/.apm/skills/analytical-design/`, `packs/experience/.apm/skills/marketplace-design/`, `packs/experience/.apm/skills/informational-design/`, `packs/experience/.apm/skills/workspace-design/` (all new)

**Tests:**
- `ls packs/experience/.apm/skills/ | wc -l` → 18 (11 renamed + design-principles + 6 genre skills).
- Each of the 6 new SKILL.md files exists.
- `python tools/lint-experience-agnostic.py packs/experience/` exits 0 — zero ADR-0024 violations across all 6 new skills.
- Manual QA: no prescriptive framework or CMS name appears in skill bodies as a required implementation tool (study examples are acceptable per ADR-0024 interpretation; prescriptive tooling references are not).

**Approach:**
Create each skill directory and write SKILL.md per RFC-0066 D4:

1. **conversion-design** — marketing surfaces: hero approach selection (5 types), above-fold 6-element spec (headline ≤10 words + sub + primary CTA + secondary CTA + proof signal + friction microcopy), IC-first principle, scroll story 7-zone structure with one-job-per-zone, social proof 6-tier hierarchy by maturity stage, numbered product tour spine. Grounded: Evil Martians study, NNGroup page-fold, PLG.news.

2. **documentation-design** — documentation surfaces: Diátaxis type mapping (tutorial/how-to/reference/explanation each with a distinct density target), navigation-at-scale 3 strategies by page count, docs landing page as hub (Start Here + content-type entry points + search), TTFV as design target, machine-readability requirements as design-phase decisions. No CMS tool names.

3. **analytical-design** — analytical surfaces: domain-model-first (model objects/attributes/relationships/actions before widget placement), business-question anchoring (3–5 explicit questions), 3-tier widget hierarchy (primary KPIs ≤9 / secondary / tertiary), Shneiderman's mantra, role-based views, spatial layout grammar (top=state signals / left=worklist / centre=primary diagnostic / right=context+filter), per-widget state handling. Scope boundary: chart IA only — individual chart encoding design is out of scope.

4. **marketplace-design** — marketplace surfaces: listing card IA (hierarchy, density, card vs. detail-page), filter/facet architecture (taxonomy, chip vs. sidebar, instant vs. apply-button, empty-filter vs. zero-results distinction), comparison affordances, browse-first vs. search-first routing, cart/transaction bridge to `interaction-design` wizard patterns.

5. **informational-design** — informational surfaces: typography as primary design tool (45–75 char line length, 1.4–1.6× line height, scale contrast between heading levels), F-pattern and Z-pattern calibration, editorial grid (column-based, often asymmetric), article page structure, "what's next" chain design (4 category types), content entry point diversity. Grounded: Bringhurst; NNGroup F-pattern.

6. **workspace-design** — workspace and agentic UI surfaces: context-persistence patterns (last-location, returning-session re-orientation, breadcrumb+recents+activity), session arc (5 stages: arrive/orient/work/persist/collaborate), collaboration state IA (presence, live-editing, following mode), interrupt/notification design (ambient by default), permission/sharing model IA, ambient vs. focal attention zones, agentic UI patterns (task queue, agent status indicators, HITL confirmation surfaces, output review, multi-agent coordination visibility).

After all 6 are created, run lint.

**Done when:** 18 skill directories exist; all 6 new SKILL.md files pass lint; zero ADR-0024 violations.

---

### T5a: Extend journey-mapping, interaction-design, service-blueprint, information-architecture (D5a–d)

**Depends on:** T1, T2, T4

**Touches:** `packs/experience/.apm/skills/journey-mapping/SKILL.md`, `packs/experience/.apm/skills/journey-mapping/references/surface-genre-journeys.md` (new), `packs/experience/.apm/skills/interaction-design/SKILL.md` or `interaction-design/references/pattern-families.md`, `packs/experience/.apm/skills/service-blueprint/SKILL.md`, `packs/experience/.apm/skills/information-architecture/SKILL.md`

**Tests:**
- `grep 'peak moment' packs/experience/.apm/skills/journey-mapping/SKILL.md` → matches (step 5b).
- `grep 'evidence-level' packs/experience/.apm/skills/journey-mapping/SKILL.md` → matches.
- `ls packs/experience/.apm/skills/journey-mapping/references/surface-genre-journeys.md` → exists with 7 genre stage scaffolds.
- `grep 'wizard-and-stepper\|data-table\|destructive-action\|save-state\|analytical-dashboard' packs/experience/.apm/skills/interaction-design/references/pattern-families.md` → all 5 match.
- `grep 'evidence-of-service\|fail-point' packs/experience/.apm/skills/service-blueprint/SKILL.md` → matches.
- `grep 'success metric\|genre routing' packs/experience/.apm/skills/information-architecture/SKILL.md` → matches.
- `python tools/lint-experience-agnostic.py packs/experience/` exits 0.

**Approach:**
1. **journey-mapping (D5a — 3 additions):**
   - After step 5 (emotion arc), insert step 5b: peak moments — identify the 1–3 stages with steepest negative dip and the single most-positive peak; mark explicitly; downstream design weighted toward improving these first (Kahneman peak-end rule).
   - In step 2 (elicit persona), add evidence-level elicitation: declare `observational | survey-backed | assumption-based`; record as `evidence-level:` in frontmatter. Assumption-based map is a hypothesis, not a defect.
   - In step 1 (set the surface), add genre confirmation alongside platform axis; reference `references/surface-genre-journeys.md`.
   - Create `journey-mapping/references/surface-genre-journeys.md` with canonical stage scaffolds for all 7 genres (per RFC-0066 D5a stage lists).

2. **interaction-design (D5b — 5 new pattern families):**
   - In `interaction-design/references/pattern-families.md` (create if absent): add the 5 families: wizard-and-stepper (linear stepper, save-and-resume, conditional disclosure), data-table (filter types, bulk operations, row detail options, alignment), destructive-action 5-tier escalation (inline → toast+undo → modal → typed confirmation → 2FA/two-person), save-state (autosave with 3 indicator states, unsaved-changes guard, draft vs. published), analytical-dashboard-widgets (KPI card anatomy, alert/signal design, drill-down affordance).

3. **service-blueprint (D5c — 2 additions):**
   - Add evidence-of-service row to blueprint definition: physical or digital artifacts the customer encounters at each frontstage touchpoint (notifications, confirmation screens, receipts, error messages, emails).
   - Add fail-point marking: explicit identification of most-likely-to-fail steps with design priority (critical / high / medium). Distinguish from gaps (which the skill already identifies).

4. **information-architecture (D5d — 2 additions):**
   - Add success-metric binding to "When to invoke" item 4: before designing hierarchy, name the measurable outcome the surface serves.
   - Add genre routing in procedure step 1 for all 7 genres (per RFC-0066 D5d routing table).
   - Each genre routes to the appropriate upstream skill output to read before designing hierarchy (conversion-design for marketing, documentation-design for documentation, etc.).

5. Run lint after all 4 skills are updated.

**Done when:** All 4 extensions verified present via grep; lint exits 0.

---

### T5b: Extend design-review and creative-direction (D5e–g)

**Depends on:** T1, T3

**Touches:** `packs/experience/.apm/skills/design-review/SKILL.md`, `packs/experience/.apm/skills/creative-direction/SKILL.md`

**Tests:**
- `grep 'design-principles' packs/experience/.apm/skills/design-review/SKILL.md` → matches (references the artefact path pattern `docs/design/principles/<slug>.md`).
- `grep 'Director.*notes\|quality.floor\|new.*principle' packs/experience/.apm/skills/design-review/SKILL.md` → matches (D5e three routing paths for unfound principles).
- `grep 'genre.*rubric\|documentation.*rubric\|marketing.*rubric' packs/experience/.apm/skills/design-review/SKILL.md` → matches (D5g rubrics present).
- `grep 'genre.*canonical\|Vercel\|Linear' packs/experience/.apm/skills/creative-direction/SKILL.md` → matches (D5f reference tier present).
- `python tools/lint-experience-agnostic.py packs/experience/` exits 0.

**Approach:**
1. **design-review D5e (design-principles integration chain):**
   - Add to procedure step 1 (before evaluating screens): load the `design-principles` artefact at `docs/design/principles/<slug>.md`. Every finding must be mapped to the principle it was judged against. A finding that cannot be mapped routes to one of: (a) quality-floor violation (handle-all-states, accessibility, reduced-motion — always valid regardless of principles), or (b) a new-principle decision (surface to the team for a principles update). Pure aesthetic preferences with no principle backing go in a "Director's notes" section, not the main findings list. This is a mandatory procedure step.

2. **creative-direction D5f (genre canonical references):**
   - Add genre axis to the existing reference selection method: for each of the 7 genres, name the canonical aesthetic reference tier (per RFC-0066 D5f table). Frame as "study subjects" — internalize the aesthetic philosophy, not copy the surface. Verify each reference site named passes ADR-0024: they are practitioner examples, not prescriptive tooling.

3. **design-review D5g (genre-specific rubrics):**
   - Add genre routing section to review procedure (after loading design-principles artefact): route to the genre-specific checklist.
   - Add 6 genre rubrics per RFC-0066 D5g (documentation ⑤-item, marketing ④-item, analytical ④-item, informational ③-item, marketplace ③-item, workspace ③-item). Each rubric has numbered checklist items for the reviewer to work through.

4. Run lint.

**Done when:** Both skills have additions verified via grep; lint exits 0.

---

### T7: Marketing site update — rename sweep in web/ (RFC-0066 Follow-on)

**Depends on:** T1

**Touches:** `web/src/content/packs/experience.md`, `web/src/content/journeys/experience.md`, `web/src/components/layout/Section.astro`, `web/src/components/marketing/HumanGates.astro`, `web/src/components/marketing/Hero.astro`, `web/src/components/marketing/BuildYourOrg.astro`

**Tests:**
- Post-rename grep for old slugs in `web/` returns zero:
  `grep -r "map-customer-journey\|blueprint-service\|map-screen-flow\|map-internal-process\|aesthetic-direction\|layout-and-information-architecture\|design-critique\|design-system-foundations\|copy-direction" web/ --include="*.md" --include="*.astro" --include="*.ts" --include="*.tsx"` → zero results.
- New skill names (journey-mapping, service-blueprint, user-flow, etc.) are legible and contextually correct in any surrounding prose (not just a slug swap that breaks grammar).

**Approach:**
1. Read each of the 6 affected files to understand the current context (description text, list items, trigger phrases).
2. Replace old skill slugs and their display names with canonical names in each file. Where prose wraps the slug (e.g. "the `map-customer-journey` skill helps you…"), update both the code span and the surrounding description to use the new name and remain grammatically correct.
3. Update any count or summary that references "11 skills" to "18 skills" if visible to users.
4. Run the post-rename grep on `web/` to confirm zero results.

**Done when:** Grep across web/ returns zero old-slug results; prose reads naturally with new names.

---

### T8: Docs site guide content update — content verification + new skill stubs (RFC-0066 Follow-on)

**Depends on:** T1, T3, T4

**Touches:** `docs/guides/experience/README.md`, `docs/guides/experience/explanation/the-experience-thread.md`, `docs/guides/experience/how-to/author-design-intent.md`, `docs/guides/experience/reference/experience.md`

**Tests:**
- Each of the 4 guide files reads naturally with canonical skill names (not just slug-swapped — trigger descriptions, "when to use" prose, and chain-position descriptions match the updated skills).
- `docs/guides/experience/` README (or reference/experience.md) lists all 18 skills with their canonical names.
- New skills mentioned in the guides or listed in the reference page include at minimum a one-line description of what each does and when to use it (stub level — not full guide pages; those are deferred follow-on).
- `grep 'design-principles\|conversion-design\|documentation-design\|analytical-design\|marketplace-design\|informational-design\|workspace-design' docs/guides/experience/reference/experience.md` → matches (new skills visible in the reference).

**Approach:**
1. Read each of the 4 guide files (slug updates were already applied in T1; this task is the content pass).
2. In `docs/guides/experience/reference/experience.md`: add the 7 new skills to the skill list/table with one-line descriptions and the phase they belong to (Define: design-principles; Genre-specific: 6 others).
3. In `docs/guides/experience/explanation/the-experience-thread.md`: verify the experience chain narrative reflects the renamed skills and the new chain structure (11 → 18); update any chain description that would be misleading with new names.
4. In `docs/guides/experience/how-to/author-design-intent.md`: verify the how-to steps read correctly with new skill names; update any "invoke `design-critique`" or "run `aesthetic-direction`" references that now use renamed skills.
5. In `docs/guides/experience/README.md`: update skill list and any navigation references.
6. Verify no old-slug reference remains in the 4 files (the T1 sweep should have caught these; this is a content-quality pass on top).

**Done when:** 4 files verified for content correctness; 7 new skills visible in reference/experience.md; no old-slug references remain.

---

### T6: Pack metadata, ADR-0052, changelog, RFC row (D8 + follow-on)

**Depends on:** T1, T2, T3, T4, T5a, T5b, T7, T8

**Touches:** `packs/experience/pack.toml`, `packs/experience/.claude-plugin/plugin.json` (version bump only; description was rewritten in T1 step 8), `.claude-plugin/marketplace.json` (re-aggregated by make build-self), `docs/adr/0052-nine-experience-pack-skill-renames.md` (new), `docs/product/changelog.md`, `docs/rfc/README.md`, `docs/specs/README.md`

**Tests:**
- `grep 'version = "0.6.0"' packs/experience/pack.toml` → matches.
- `packs/experience/pack.toml` `[pack.evals]` contains all renamed canonical slugs and the 7 new skills.
- `grep '"version".*"0.6.0"' packs/experience/.claude-plugin/plugin.json` → matches.
- `.claude-plugin/marketplace.json` experience pack entry shows `0.6.0`: `grep -A6 '"experience"' .claude-plugin/marketplace.json | grep '"version"' | grep '0.6.0'` → matches (confirms make build-self regenerated the aggregate; wider window tolerates key reordering).
- `ls docs/adr/0052-nine-experience-pack-skill-renames.md` → exists.
- ADR-0052 has Status: Accepted, 9-row old→new table, frozen-governance bridge statement, no-alias statement.
- `grep '0.6.0' docs/product/changelog.md` → matches entry listing renames and new skills.
- `grep 'RFC-0066' docs/rfc/README.md` → matches Accepted row.
- `grep 'experience-pack-0.6.0' docs/specs/README.md` → matches row.
- Final: `python tools/lint-experience-agnostic.py packs/experience/` exits 0.
- Final: post-rename grep returns zero results.
- Final: `ls packs/experience/.apm/skills/ | wc -l` → 18.

**Approach:**
1. **pack.toml version bump:**
   - Version: `0.5.0` → `0.6.0`.
   - `[pack.evals]` skills: add the 7 new skills (`design-principles`, `conversion-design`, `documentation-design`, `analytical-design`, `marketplace-design`, `informational-design`, `workspace-design`). All qualify under RFC-0037/ADR-0028 policy (judgment/authoring skills with user-triggered activation). Renamed skills' slugs were updated in T1; verify the list uses all canonical names. (Note: `description` was rewritten in T1 step 7 to avoid blocking T1's grep gate.)

2. **plugin.json version bump:** In `packs/experience/.claude-plugin/plugin.json`, bump `"version"` to `"0.6.0"`. (`description` was already rewritten in T1 step 8; verify it is current before bumping version only.)

3. **make build-self:** Run `make build-self` from the repo root to re-aggregate `.claude-plugin/marketplace.json` with the updated pack version and description. Verify the experience pack entry in `.claude-plugin/marketplace.json` shows `"version": "0.6.0"` (not `0.5.0`).

4. **ADR-0052:** Create `docs/adr/0052-nine-experience-pack-skill-renames.md` following ADR-0038's shape exactly:
   - Title: `ADR-0052: Nine experience-pack skill renames — live surface renamed, frozen governance bridged, no install-time alias`
   - Status: Accepted, Date: 2026-07-19, Decision-makers: eugenelim
   - 9-row old→new mapping table (same format as ADR-0038's rename table)
   - Context: references RFC-0066, ADR-0038 precedent, alias-free posture
   - Decision: canonical names, no alias, frozen governance bridged by this ADR
   - Consequences: adopters with old names must reinstall or update references; inbound cross-references from `voice-and-microcopy → ux-writing` rename (deferred) are noted

5. **Changelog:** In `docs/product/changelog.md`, add a 0.6.0 entry (under `[Unreleased]` or as a new `## [0.6.0]` section):
   - List 9 renames (old → new)
   - List 7 new skills
   - List 6 extended skills (with brief summary of additions)

6. **RFC README:** Verify RFC-0066 row is present in `docs/rfc/README.md` with Accepted status and date closed 2026-07-19 — this row was added when marking RFC-0066 Accepted earlier in this session; confirm only, don't re-add.

7. **Specs README:** Verify `experience-pack-0.6.0` row is present in `docs/specs/README.md` active list — added at spec-authoring time; confirm only, don't re-add.

8. **Final verification:**
   - Run post-rename grep → zero results.
   - Run lint → exit 0.
   - Count skills → 18.

**Done when:** All metadata files updated; plugin.json bumped; make build-self run; ADR-0052 exists; changelog updated; all mechanical gates pass.

---

### T9: Journey doc update — as-built state and status promotion (post-implementation)

**Depends on:** T6

**Touches:** All files in `docs/product/journeys/` that contain old experience-pack skill slugs (enumerated by discovery grep in step 1); known files include `designer-designs-surface.md`, `README.md`, `product-engineer-shapes-initiative.md`, `product-strategist-sets-direction.md`, `engineer-adopts-coordination.md`, `pm-intakes-from-tracker.md`, `engineer-scales-to-swarm.md`, `agent-executes-spec.md`.

**Tests:**
- Discovery grep enumerates the set of files to update (step 1 output).
- After updates: zero **imperative** old-slug invocations remain across `docs/product/journeys/`; prose-only educational mentions are recorded in `docs/backlog.md` under `experience-pack-rename-journey-prose`, not required to be zero.
- `grep 'status.*live\|live.*status' docs/product/journeys/designer-designs-surface.md` → matches (frontmatter status promoted).
- `grep 'planned' docs/product/journeys/designer-designs-surface.md` → zero results (confirms frontmatter and status-table cell both updated).
- `grep 'current (0.5.0)\|11 skills' docs/product/journeys/designer-designs-surface.md` → zero results (prereq table row updated to 0.6.0 / 18 skills).
- `grep 'To-be state\|after RFC-0066' docs/product/journeys/designer-designs-surface.md` → zero results (To-be header present-tensed).
- `designer-designs-surface.md` Shipped-state section names as-built 0.6.0 skills (journey-mapping, service-blueprint, user-flow, design-principles, creative-direction, information-architecture, design-review, conversion-design, etc.) and mentions the surface-genre contract.

**Approach:**
1. **Discovery grep:** Run `grep -rl "map-customer-journey\|blueprint-service\|map-screen-flow\|map-internal-process\|aesthetic-direction\|layout-and-information-architecture\|design-critique\|design-system-foundations\|copy-direction" docs/product/journeys/` to enumerate files with old slugs. Read each match in context to classify as imperative invocation or prose-only mention.
2. In `designer-designs-surface.md`, make the following targeted updates:
   - **Prereq table row (~line 41):** Update the experience pack row from "current (0.5.0) | 11 skills …" to "live (0.6.0) | 18 skills …" reflecting the shipped state.
   - **Status-table cell (~line 42):** Update "planned (0.6.0 — RFC-0066)" to "live".
   - **Frontmatter:** Promote `status:` from `planned` → `live`.
   - **To-be header (~line 84):** Rename `### To-be state — experience 0.6.0 (after RFC-0066)` → `### Shipped state — experience 0.6.0`.
   - **Preserve** (historical-section definition from AC17(e) — any section whose heading or bold label carries `(experience 0.5.0)`, `(before RFC-0066)`, or `As-is`): the `### Current state — experience 0.5.0 (before RFC-0066)` Mermaid section; all six per-stage `### Now (experience 0.5.0)` subsection headers and their content; and the `**As-is setup (experience 0.5.0)**` prose block (~lines 44–47) which contains imperative old-slug invocations that are historical record, not active agent calls.
   - In the Shipped-state section: ensure the skill chain and genre routing description uses canonical 0.6.0 names (journey-mapping, service-blueprint, user-flow, design-principles, creative-direction, information-architecture, design-review, conversion-design, etc.) and mentions the `surface-genre:` contract.
3. In all other journey files found in step 1: if a match is an imperative invocation of an old skill slug and falls outside a historical section (as defined in AC17(e): heading/label carries `(experience 0.5.0)`, `(before RFC-0066)`, or `As-is`), update to the canonical name; if it is a prose-only educational description, add a one-line entry to `docs/backlog.md` under `experience-pack-rename-journey-prose` and leave the file unchanged.
4. Re-read `designer-designs-surface.md` to confirm all four targets from step 2 (prereq table, status cell, frontmatter, header rename) are correct.

**Done when:** `designer-designs-surface.md` has live status in frontmatter and status table; prereq table shows 0.6.0/18 skills; To-be header is present-tensed; zero imperative old-slug invocations remain in `docs/product/journeys/` outside historical-baseline sections; prose-only mentions are recorded in backlog.

---

## Rollout

Single PR. Pure-markdown skills — no infra, no migration, no feature flag. Breaking change: 9 skill renames require adopters to update references (no alias). Rollback: the PR can be reverted cleanly. Not reversible for adopters who have already pulled 0.6.0 — they must update references; there is no alias path back. Pre-stable pack (0.x), so breaking renames are acceptable per ADR-0038 precedent.

Task sequence: T1 → (T2, T3 in parallel) → T4 → (T5a, T5b in parallel) → (T7, T8 in parallel) → T6 → T9. All in one PR; T9 is the final step that confirms the as-built state and closes the journey doc.

## Risks

- **Rename sweep incompleteness (T1):** The spike confirmed ~43 files in `packs/experience/` contain old slug references. A missed reference in a `references/` file or asset template would leave stale slugs. Mitigation: post-rename grep (including `*.json`) is the T1 completion gate; T1 does not advance until the grep returns zero.
- **JSON files missed in sweep (T1):** `evals.json` and `plugin.json` can contain old slug references and are invisible to a `*.md`-only grep. Mitigation: T1 grep explicitly includes `--include="*.json"`; T1 approach step 4 updates each renamed skill's `evals/evals.json`.
- **Cross-pack imperative invocations (T1):** `packs/core/`, `packs/product-engineering/`, or `packs/research/` may contain imperative invocations of old experience-pack skill slugs that require updating. Mitigation: T1 step 10 runs a dedicated cross-pack audit; any imperative invocations are fixed; prose-only mentions are recorded in `docs/backlog.md`.
- **ADR-0024 violation in a new skill (T4):** A genre skill accidentally prescribes a tool or CMS. Mitigation: lint runs after T4 with zero-violation gate.
- **`experience-reviewer.md` stale references (T1):** The agent file aggregates skill references across the whole pack. Mitigation: T1 explicitly updates this file; it is named in the approach steps.
- **evals list inconsistency (T1/T6):** Slug renames in T1 must be complete before T6 adds new slugs. Mitigation: T6 depends on T1; T1's approach step 7 updates renamed slugs in the evals list.
- **ADR ordinal collision:** A concurrent PR might claim ADR-0052. Mitigation: check `docs/adr/` for 0052 before creating the file in T6.

## Changelog

- 2026-07-19: initial plan
- 2026-07-19: added T7 (marketing site web/ sweep) and T8 (docs guide content update) after user directed that all site surfaces be completed in the same PR; removed marketing site from deferred rollout section; updated T6 to depend on T7, T8
- 2026-07-19: adversarial-reviewer pass 1 findings applied — blocker fixes: (1) added cross-pack inbound reference sweep to T1 with backlog-recording for prose-only matches; (2) extended all grep gates to include `*.json`; (3) added plugin.json update + make build-self to T6; (4) moved pack.toml `description` sweep from T6 into T1 to avoid T1 grep gate contradiction; (5) promoted journey doc update from deferred to in-scope T9 (depends on T6); updated T5a to depend on T4; rewrote T6 steps 6–7 to "verify-present" (rows already added in this session); updated Risks and Rollout sections accordingly
- 2026-07-19: adversarial-reviewer pass 2 findings applied — (1) moved plugin.json `description` sweep to T1 step 8 (version-only stays in T6) to close the identical pack.toml-style grep gate contradiction; (2) broadened T9 Touches to enumerate all ~8 known journey files + discovery grep in step 1; (3) aligned T9 test to imperative-only with prose-to-backlog carve-out (mirrors T1 cross-pack pattern); updated AC16 in spec to match; (4) added voice-and-microcopy carve-out to T1 step 11 (its `copy-direction` ref is part of the deferred rename RFC, not in-scope); added `.py` code-comment refs as out of scope in T1 step 11; (5) added `marketplace.json` to T6 Touches and a version-check test; (6) T9 approach step 2 now preserves pre-0.6.0 Mermaid/stage-table narrative, updates only live-state sections; (7) T9 step 2 and test updated to cover both frontmatter status field and line-42 status table cell
- 2026-07-19: adversarial-reviewer pass 3 findings applied — (1) T1 steps 2–4 generalized to cover all 11 skill dirs (not just renamed); explicitly calls out content-design and interaction-design cross-references and interaction-design physical path references (../design-critique/ → ../design-review/) that break after mv; (2) AC17 rewritten to name concrete file targets (prereq table, status-table cell, frontmatter, To-be header rename to Shipped-state); `### Now (experience 0.5.0)` per-stage sections explicitly preserved as historical baseline; (3) fixed marketplace.json path to `.claude-plugin/marketplace.json` in T6 Touches, Tests, and approach step 3; fixed test to use context-sensitive grep; (4) T9 updated: prereq table update (0.5.0→0.6.0, 11→18) and To-be header present-tensing added to step 2 and tests; historical-section exemption in step 3 made explicit
- 2026-07-19: adversarial-reviewer pass 4 findings applied — (1) AC17(e) line numbers removed (inaccurate); corrected to "all six per-stage headers (Stages 1–6)" + added As-is setup block (~lines 44–47) to preserved list; (2) unified "historical-section" definition in AC17(e): any section heading/label carrying `(experience 0.5.0)`, `(before RFC-0066)`, or `As-is`; T9 steps 2–3 reference this definition; (3) spec and plan Status fields aligned: both set to Approved (were Implementing/Drafting — no implementation has started yet); (4) T6 marketplace grep widened to -A6 to tolerate key reordering
