# Plan: m3-experience-design-rename

- **Spec:** [`spec.md`](spec.md)
- **Status:** Draft

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Seven sequential tasks. T1 renames the pack directory — everything else keys
off the new path. T2 updates the manifests (pack.toml + plugin.json). T3 sweeps
all operative cross-pack references in `packs/` plus the root `README.md`. T4
renames the guide directory, updates the slug-named guide file and all guide
prose, and updates `docs/guides/README.md`. T5 updates all platform-site surfaces
(MkDocs, build-site.py, and the Astro web content). T6 creates the AGENTS.md
migration guide and edits RFC-0064. T7 runs the build gates.

No skill directory renames — all 18 skills are function-named. No agentbundle
test updates — no `experience` references exist in `packages/agentbundle/`. The
riskiest part is the operative-vs-historical distinction: the rule is "does this
reference cause a build, test, or runtime failure if stale?" If yes, update. If
it's frozen prose in a shipped RFC/ADR/spec body, leave it. `experience-reviewer`
references are always correct and stay.

## Constraints

- RFC-0064 M3 governs this rename; no sub-RFC needed.
- `experience-reviewer` agent name is functional — do not rename it.
- `[experience]` table key in `agentbundle-layout.md` reference docs is an
  activity-type identifier — leave as-is.
- No pack-level alias is possible; migration is documentation-only.
- `build-self` must run after all pack-tree edits (it overwrites projected paths;
  make all source edits before running it).

## Construction tests

**Structural gate:** `make lint-packs && python3 tools/lint-experience-agnostic.py && make build-self` — catches pack-schema violations, confirms the agnosticism lint resolves the new path, and propagates rename into projected outputs.

**Integration gate:** `pytest packages/agentbundle/` — full suite confirms the
renamed pack round-trips correctly (no experience-specific tests exist, but the
suite covers pack install/resolve infrastructure).

**Manual verification:**
- `[ -d packs/experience-design ] && [ ! -d packs/experience ]` — directory move
  complete.
- `` grep -rn '"experience"\|experience pack\|`experience`' packs/ --include="*.md" | grep -v "^packs/experience-design/" `` — zero unremediated operative hits after T3. The backtick form `` `experience` `` is the dominant reference form in cross-pack SKILL.md files and must be included.
- `[ -d docs/guides/experience-design ] && [ ! -d docs/guides/experience ]` — guide
  directory move complete.

## Design (LLD)

### Component / module decomposition

The change touches six layers:

1. **Pack registry** — `pack.toml` + `plugin.json`: name, version, display_name,
   docs link. No evals-list changes (all 11 evals skills are function-named).
2. **Pack directory** — `packs/experience` → `packs/experience-design` (git mv);
   skill directories unchanged inside it.
3. **Operative cross-pack references** — six files outside the pack plus
   `product-engineering/README.md` and the root `README.md`.
4. **Guide directory** — `docs/guides/experience` → `docs/guides/experience-design`;
   one slug-named file renamed; prose updated; `docs/guides/README.md` updated.
5. **Platform site** — `site/mkdocs.yml` (MkDocs nav), `tools/build-site.py`
   (Astro pack list), `web/src/content/packs/experience.md` (file rename + content),
   `web/src/content/journeys/experience.md` (file rename + content),
   `web/src/pages/journeys/index.astro` (display order).
6. **Migration docs** — new `packs/experience-design/AGENTS.md`; RFC-0064 body
   amendment.

Layer 3 disambiguation guide — use for every reference encountered:

| Reference type | Action |
|---|---|
| "experience pack" / `` `experience` `` pack-name slug in operative SKILL.md body | Rename |
| Pack name in SKILL.md T1/T2 prereq block | Rename |
| `experience-reviewer` (agent name) | Leave — functional, not pack-derived |
| `[experience]` in agentbundle-layout.md reference docs | Leave — activity-type key |
| `/experience` URL in an already-shipped RFC/ADR/spec body | Leave |
| Free-prose "experience design" as a discipline noun | Leave |

### Dependencies & integration

- `work-loop/SKILL.md` checks for `experience-reviewer` by name and describes
  it as needing "the experience pack" — two lines need the pack-name text
  updated; the agent-name references stay.
- `new-spec/SKILL.md` step 4d references "experience pack" by name in the
  design-readiness check — two lines updated; no skill-slug changes.
- `voice-and-microcopy/SKILL.md:32` references "the `experience` pack's
  `tone-of-voice` skill" twice — pack name updated; skill slug stays.
- `discovery-loop/SKILL.md:210` references the pack name in a detect-and-degrade
  block — updated. Line 211 contains only agent names (`experience-reviewer` /
  `design-reviewer`) — leave unchanged. `fresh-context.md:24` also updated.
- `product-engineering/README.md:142` — operative markdown link pointing to
  `../experience/README.md` will break after T1; update in T3.
- Platform site: `site/mkdocs.yml` references guide paths that T4 changes; T5
  must run after T4 to stay in sync.

## Tasks

### T1: Rename the pack directory

**Depends on:** none

**Touches:** `packs/experience/` → `packs/experience-design/`

**Tests:**
- `[ -d packs/experience-design ] && [ ! -d packs/experience ]` exits 0

**Approach:**
```
git mv packs/experience packs/experience-design
```

**Done when:** `packs/experience-design/` exists; `packs/experience/` does not;
`git status` shows the move cleanly.

---

### T2: Update pack manifests (pack.toml + plugin.json)

**Depends on:** T1

**Touches:** `packs/experience-design/pack.toml`,
`packs/experience-design/.claude-plugin/plugin.json`

**Tests:**
- `grep 'name = "experience-design"' packs/experience-design/pack.toml` exits 0
- `grep 'version = "1.0.0"' packs/experience-design/pack.toml` exits 0
- `grep 'display_name = "Experience Design"' packs/experience-design/pack.toml` exits 0
- `grep '"name": "experience-design"' packs/experience-design/.claude-plugin/plugin.json` exits 0
- `grep '"version": "1.0.0"' packs/experience-design/.claude-plugin/plugin.json` exits 0

**Approach:**

*`pack.toml`:*
- `name = "experience"` → `name = "experience-design"`
- `version = "0.6.0"` → `version = "1.0.0"`
- `display_name = "Experience"` → `display_name = "Experience Design"`
- `documentation` URL: `.../docs/guides/experience/` →
  `.../docs/guides/experience-design/`
- `description` field: update "experience pack" prose if present; leave
  `experience-reviewer` and `[experience]` layout-key references intact.
- Comments in pack.toml that name "the experience pack" → "the experience-design
  pack"; comments referencing `experience-reviewer` or `[experience]` layout key
  stay.

*`plugin.json`:*
- `"name": "experience"` → `"name": "experience-design"`
- `"version": "0.6.0"` → `"version": "1.0.0"`
- `"description"`: update any "experience pack" prose to "experience-design pack";
  `experience-reviewer` stays.

**Done when:** all five grep checks above exit 0.

---

### T3: Operative cross-pack sweep (packs/ + README.md)

**Depends on:** T1

**Touches:**
`packs/core/.apm/skills/work-loop/SKILL.md`,
`packs/core/.apm/skills/new-spec/SKILL.md`,
`packs/product-engineering/.apm/skills/discovery-loop/SKILL.md`,
`packs/product-engineering/.apm/skills/discovery-loop/references/self-coverage/fresh-context.md`,
`packs/product-engineering/.apm/skills/voice-and-microcopy/SKILL.md`,
`packs/product-engineering/README.md`,
`README.md`,
`tools/lint-experience-agnostic.py`,
intra-pack SKILL.md files within `packs/experience-design/` that reference the
old pack name

**Tests:**
- Repo-wide sweep (run after all edits in this task):
  `grep -rn '"experience"\|experience pack' packs/ --include="*.md" | grep -v "^packs/experience-design/"` — review every hit; zero unremediated operative references.
- `grep -n '"experience"\|experience pack' README.md` returns 0 lines.

**Approach:**

*Step 0 — run the repo-wide sweep first (packs/ AND tools/):*
```
grep -rn '"experience"\|experience pack\|`experience`\|packs/experience[^-]' packs/ tools/ --include="*.md" --include="*.py"
```
Review every hit using the disambiguation table in Design (LLD). The list below
covers all confirmed operative files; the sweep catches any stragglers. The
`packs/experience[^-]` pattern specifically catches hardcoded paths in `tools/*.py`
lint scripts.

*`work-loop/SKILL.md`:*
- Line 716: `no \`experience-reviewer\` is installed (experience pack absent)` →
  `no \`experience-reviewer\` is installed (experience-design pack absent)`
- Line 717: `absence of the experience pack is a named skip` →
  `absence of the experience-design pack is a named skip`
- Lines 346, 708, 710, 714, 786: `experience-reviewer` only — leave.

*`new-spec/SKILL.md`:*
- Line 241: `If the experience pack is absent` →
  `If the experience-design pack is absent`
- Line 243: `` `experience pack not installed; design intent for this surface is ungrounded` `` →
  `` `experience-design pack not installed; design intent for this surface is ungrounded` ``

*`discovery-loop/SKILL.md`:*
- Line 210: `` `desk-research` / `experience` / `architect` `` — update
  `` `experience` `` pack name → `` `experience-design` ``.
- Line 211: `experience-reviewer / \`design-reviewer\` if those packs are` —
  contains only agent names; leave unchanged.

*`fresh-context.md` (`discovery-loop/references/self-coverage/`):*
- Line 24: `experience-reviewer (if \`experience\` is` →
  `experience-reviewer (if \`experience-design\` is`

*`voice-and-microcopy/SKILL.md`:*
Seven lines carry the `` `experience` `` pack name — update all to `` `experience-design` ``:
- Line 3 (frontmatter `description:` — projected to all adapters):
  `` `experience`'s `user-flow` `` → `` `experience-design`'s `user-flow` ``
- Line 17: `` `experience`'s `user-flow` `` → `` `experience-design`'s `user-flow` ``
- Line 20: `` `experience` pack's shared `` → `` `experience-design` pack's shared ``
- Line 28: `` `experience` pack `` → `` `experience-design` pack ``
- Line 29: `` `experience` pack's `user-flow` `` → `` `experience-design` pack's `user-flow` ``
- Line 32 (multiple occurrences): all `` `experience` `` pack-name refs →
  `` `experience-design` ``
- Line 68: `` `experience` pack `` → `` `experience-design` pack ``

*`product-engineering/README.md`:*
- Line 123 section heading: `` ## Cross-pack: `experience` `` →
  `` ## Cross-pack: `experience-design` ``
- Line 127: `experience pack` → `experience-design pack`
- Line 129: `` `experience`'s `user-flow` `` → `` `experience-design`'s `user-flow` ``
- Line 139: `agentbundle install experience product-engineering` →
  `agentbundle install experience-design product-engineering`
- Line 142: `See the [\`experience\` pack README](../experience/README.md)` →
  `See the [\`experience-design\` pack README](../experience-design/README.md)`

*`tools/lint-experience-agnostic.py`:*
- Line 150 (`_scan_root()` default): `_repo_root() / "packs" / "experience"` →
  `_repo_root() / "packs" / "experience-design"`. This is the path CI invokes
  (no `EXPERIENCE_ROOT` override in `build-check.yml`) — without this fix the lint
  exits 2 ("scan root … does not exist") and CI build-check goes red post-merge.
- Lines 2, 4, 8 (docstring): update `experience` pack name references to
  `experience-design`.

*`README.md` (root):*
- Line 125: `[\`experience\`](docs/guides/experience/)` and description →
  `[\`experience-design\`](docs/guides/experience-design/)` with updated description.

*Intra-pack SKILL.md sweep:*
- Review every hit from the Step 0 grep within `packs/experience-design/.apm/skills/`.
  Apply the disambiguation table. `[experience]` layout-key references and
  `experience-reviewer` references stay; "experience pack" prose → "experience-design pack".

**Done when:** repo-wide sweep `` grep -rn '"experience"\|experience pack\|`experience`\|packs/experience[^-]' packs/ tools/ --include="*.md" --include="*.py" | grep -v "^packs/experience-design/" `` returns zero unremediated operative pack-name references (excluding `experience-reviewer` and `[experience]` layout-key hits); `` grep -n '"experience"\|experience pack\|`experience`' README.md `` returns 0 lines; `tools/lint-experience-agnostic.py:150` references `packs/experience-design`.

---

### T4: Guide directory rename + prose + docs/guides/README.md

**Depends on:** T1

**Touches:**
`docs/guides/experience/` → `docs/guides/experience-design/`,
`docs/guides/experience-design/reference/experience.md` →
`docs/guides/experience-design/reference/experience-design.md`,
all guide prose files within `docs/guides/experience-design/`,
`docs/guides/README.md`

**Tests:**
- `[ -d docs/guides/experience-design ] && [ ! -d docs/guides/experience ]` exits 0
- `[ -f docs/guides/experience-design/reference/experience-design.md ] && [ ! -f docs/guides/experience-design/reference/experience.md ]` exits 0
- `` grep -rn '"experience"\|experience pack\|`experience`\|install.*experience[^-]' docs/guides/experience-design/ --include="*.md" `` returns 0 lines (excluding `[experience]` layout-key and `experience-reviewer` hits)

**Approach:**
- `git mv docs/guides/experience docs/guides/experience-design`
- Rename the slug-named reference file:
  `git mv docs/guides/experience-design/reference/experience.md docs/guides/experience-design/reference/experience-design.md`
- Update prose in all guide files:
  - Heading in `reference/experience-design.md` line 1: `` # `experience` — `` →
    `` # `experience-design` — ``
  - Install commands: `agentbundle install --pack experience` →
    `agentbundle install --pack experience-design`
  - Pack-name prose: "the `experience` pack" → "the `experience-design` pack"
  - Leave `[experience]` layout-table references intact (activity-type key).
  - Leave `experience-reviewer` references intact.
- Update `docs/guides/README.md`:
  - Line 23: `` [`experience`](experience/) `` → `` [`experience-design`](experience-design/) ``;
    "design critique" → "design review" (renamed in RFC-0066).
  - Line 56: `` [`experience`](experience/) `` → `` [`experience-design`](experience-design/) ``;
    stale skill descriptions updated — "aesthetic direction" → "creative direction",
    "design systems" → "design system", "design critique" → "design review"
    (all renamed in RFC-0066).
- Verify no other operative files reference the old guide path:
  `grep -rn "guides/experience[^-]" . --include="*.md" --include="*.toml" --include="*.yml" --include="*.py" | grep -v "docs/rfc\|docs/adr\|docs/specs"` — update any hits outside frozen bodies.

**Done when:** directory move and file rename complete; all three test checks above pass.

---

### T5: Platform site (MkDocs + build-site.py + Astro web)

**Depends on:** T4

**Touches:**
`site/mkdocs.yml`,
`tools/build-site.py`,
`web/src/content/packs/experience.md` → `web/src/content/packs/experience-design.md`,
`web/src/content/journeys/experience.md` → `web/src/content/journeys/experience-design.md`,
`web/src/pages/journeys/index.astro`

**Tests:**
- `grep -in "experience" site/mkdocs.yml | grep -v experience-design` returns 0 lines
- `grep -n '"experience"' tools/build-site.py` returns 0 lines
- `[ -f web/src/content/packs/experience-design.md ] && [ ! -f web/src/content/packs/experience.md ]` exits 0
- `[ -f web/src/content/journeys/experience-design.md ] && [ ! -f web/src/content/journeys/experience.md ]` exits 0
- `grep "slug: 'experience-design'" web/src/pages/journeys/index.astro` exits 0

**Approach:**

*`site/mkdocs.yml`:* — 6 entries total:
- Line 117 top-level packs nav: `Experience: packs/experience.md` →
  `Experience Design: packs/experience-design.md`
- Line 200 guides section header: `- Experience:` → `- Experience Design:`
- Guide paths (×4): `guides/experience/README.md` → `guides/experience-design/README.md`;
  `guides/experience/explanation/the-experience-thread.md` → `.../experience-design/...`;
  `guides/experience/how-to/author-design-intent.md` → `.../experience-design/...`;
  `guides/experience/reference/experience.md` →
  `guides/experience-design/reference/experience-design.md`.
- Line 207 leaf nav entry title: `Experience Pack:` → `Experience Design Pack:`

Verification (must return 0 lines after edits):
`grep -in "experience" site/mkdocs.yml | grep -v experience-design`

*`tools/build-site.py`:*
- Line 35: `("experience", "Experience", "user", "<old description>")` →
  `("experience-design", "Experience Design", "user", "<updated description>")`.
  Updated description must reference current skill names — replace "aesthetic
  direction" (renamed to `creative-direction` in RFC-0066) with current names.
  Suggested: `"The full design thread: journey mapping, screen flows, creative direction, surface-genre design (6 types), and the shared quality floor."`.

*`web/src/content/packs/experience.md` → `experience-design.md`:*
- `git mv web/src/content/packs/experience.md web/src/content/packs/experience-design.md`
- Frontmatter: `name: Experience` → `name: Experience Design`;
  `installCommand: "agentbundle install --pack experience --scope user"` →
  `"agentbundle install --pack experience-design --scope user"`;
  `docsUrl: /docs/guides/experience/` → `/docs/guides/experience-design/`;
  `journeyUrl: /journeys/experience/` → `/journeys/experience-design/`.
- Skills list is already current (RFC-0066) — no changes needed.
- Body prose: "Experience installs..." → "Experience Design installs..."; any
  other "experience" pack-name references updated; `experience-reviewer` stays.

*`web/src/content/journeys/experience.md` → `experience-design.md`:*
- `git mv web/src/content/journeys/experience.md web/src/content/journeys/experience-design.md`
- Frontmatter: `pack: experience` → `pack: experience-design`;
  `docsUrl: /docs/guides/experience/` → `/docs/guides/experience-design/`;
  `packUrl: /packs/experience/` → `/packs/experience-design/`.
- `whatChanges` prose: "After installing experience," → "After installing
  experience-design,"; `experience-reviewer` stays.
- Body prose: update "experience" pack-name references; skill names are already
  current; `experience-reviewer` stays.

*`web/src/pages/journeys/index.astro`:*
- Line 17: `{ slug: 'experience', name: 'Experience' }` →
  `{ slug: 'experience-design', name: 'Experience Design' }`

**Done when:** all five test checks above pass.

---

### T6: Create AGENTS.md + record assessment in RFC-0064

**Depends on:** T2

**Touches:**
`packs/experience-design/AGENTS.md` (new file),
`docs/rfc/0064-ini-001-ai-native-ecosystem.md`

**Tests:**
- `[ -f packs/experience-design/AGENTS.md ]` exits 0
- `grep "experience-design" packs/experience-design/AGENTS.md` exits 0
- `grep 'experience-design/AGENTS.md' docs/rfc/0064-ini-001-ai-native-ecosystem.md` exits 0 (scoped to the experience-design AC bullet — avoids a false pass from the desk-research assessment note already present in the RFC)

**Approach:**

*`AGENTS.md` — create with these sections:*

```markdown
# AGENTS.md — experience-design pack

## Migration from `experience` (v0.6.x → v1.0.0)

The pack was renamed from `experience` to `experience-design` in v1.0.0
(RFC-0064 M3).

### Name changes

| Before (≤ 0.6.x) | After (≥ 1.0.0) |
|---|---|
| Pack: `experience` | Pack: `experience-design` |

### What does not change

All 18 skill slugs are unchanged (all are function-named):
`journey-mapping`, `user-flow`, `service-blueprint`, `process-mapping`,
`creative-direction`, `design-system`, `information-architecture`,
`interaction-design`, `design-review`, `content-design`, `tone-of-voice`,
`design-principles`, `conversion-design`, `documentation-design`,
`analytical-design`, `marketplace-design`, `informational-design`,
`workspace-design`.

The `experience-reviewer` agent name is unchanged (functional, not pack-derived).

The `[experience]` table key in `agentbundle-layout.toml` is an activity-type
identifier, not a pack name — it stays.

### Adopter install-state impact

Your install state (`~/.agentbundle/state.toml`) tracks the old pack name
`experience`. After upgrading to the catalogue with v1.0.0:
1. Uninstall the old pack: `agentbundle uninstall experience --adapter <adapter>`
2. Reinstall: `agentbundle install experience-design --adapter <adapter>`

No alias is available — the installer does not support pack-level aliases.
```

*RFC-0064 body edit — RFC-0064 is still Draft; edit directly:*

In the M3 ACs section, locate the `` `experience` pack renamed to `experience-design` ``
bullet (currently unchecked `- [ ]`). Mark it checked and append the assessment
parenthetical:
> (Alias assessment: agentbundle alias mechanism is adapter-scoped only — no
> pack-level alias; migration is documentation-only via
> `packs/experience-design/AGENTS.md`. `agentbundle-layout.toml [experience]`
> section key is an activity-type identifier and does not change. Assessed
> 2026-07-18, eugenelim.)

**Done when:** AGENTS.md exists with the migration table; RFC-0064 experience-design
AC bullet is checked and contains the assessment note.

---

### T7: Build gates

**Depends on:** T1–T6

**Tests:**
- `make lint-packs` exits 0
- `python3 tools/lint-experience-agnostic.py` exits 0
- `make build-self` exits 0
- `pytest packages/agentbundle/` green (full suite)

**Approach:**
- Run `make lint-packs` first — catches pack-schema violations before the
  expensive build-self step.
- Run `python3 tools/lint-experience-agnostic.py` — confirms the agnosticism lint
  finds the renamed pack at its new path. This runs in CI via `build-check.yml`
  with no `EXPERIENCE_ROOT` override; it must pass locally before pushing.
- Run `make build-self` — propagates the rename into projected outputs
  (marketplace, per-adapter projections). Note: build-self overwrites projected
  paths; all source edits in T1–T6 must be complete before running it.
- Run `pytest packages/agentbundle/` — full suite; no experience-specific tests
  exist, but the pack install/resolve infrastructure is exercised.
- If any gate fails, fix before marking T7 done; do not skip or suppress.

**Done when:** all four commands exit 0 with no suppressed failures.

---

## Rollout

Big-bang cutover — no flag, no gradual. The rename is a single PR. Adopters with
`experience` in their install state must reinstall (documented in AGENTS.md).
No infrastructure changes, no data migration, no external-system sequencing.

**Irreversible aspect:** once the PR merges, the old pack name `experience` is
gone from the catalogue. An adopter who does not reinstall will have a stale
state entry but no pack to install. The AGENTS.md migration guide is the only
mitigation.

## Risks

- **Operative references missed in the packs/ sweep.** T3's grep must be
  exhaustive — a missed reference leaves a broken skill invocation or a stale
  pack-name in a skill prompt. Mitigation: run the Step 0 sweep before editing
  and re-run after.
- **Platform-site path drift.** T5 edits five platform-site files; a missed
  path update in mkdocs.yml will break the docs site navigation. Mitigation:
  verify with `grep -n "experience[^-]" site/mkdocs.yml` after T5.
- **build-self undoes projection-only edits.** Memory note: `build-self` can
  overwrite projection-only edits made directly in projected paths. Mitigation:
  make all edits in source (`packs/`) before running build-self in T7.
- **`experience-reviewer` misidentified as a pack-name reference.** The agent
  name contains "experience"; the disambiguation table must be applied on every
  hit. Mitigation: treat `experience-reviewer` hits as expected-correct and skip.
- **Intra-pack SKILL.md prose missed.** Six agentbundle-layout.md reference
  files mention `[experience]` as the layout key — these are correct and must not
  be updated. Mitigation: apply the disambiguation table on every intra-pack hit.

## Changelog

- 2026-07-19: initial plan
- 2026-07-19: pre-commit adversarial review (4 passes) — added backtick `` `experience` ``
  form to all verification greps (T3/T4 Done-when + construction tests); expanded
  voice-and-microcopy to all 7 lines (3,17,20,28,29,32,68); corrected discovery-loop
  citation to line 210; expanded PE README to lines 123,127,129,139,142; added mkdocs
  guides section header (line 200) and leaf nav title retitle to T5; added
  docs/guides/README.md:23 stale "design critique" fix to T4; scoped T6 RFC grep to
  experience-design bullet; added case-insensitive mkdocs verification grep;
  added tools/lint-experience-agnostic.py to T3 Touches + approach (CI path breaks
  without it); widened Step 0 sweep to tools/ + .py; added lint to T7 gates and
  construction tests.
