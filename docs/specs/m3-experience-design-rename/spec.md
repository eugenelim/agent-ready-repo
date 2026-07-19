# Spec: m3-experience-design-rename

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `experience` pack is renamed to `experience-design` and bumped to version
1.0.0. All 18 skills are function-named and remain unchanged. The
`experience-reviewer` agent name is also unchanged (functional, not
pack-derived).

Operative cross-pack references are updated across all files that invoke or
reference the pack by its old name — including `work-loop` and `new-spec` (core
pack), `discovery-loop`, `voice-and-microcopy`, and the PE README
(product-engineering pack). An `AGENTS.md` migration guide is created in the
renamed pack. Guide directories are renamed and the slug-named guide file is
updated. All platform-site surfaces — MkDocs nav, `build-site.py` PACKS list,
and Astro web pack and journey files — are updated to use the new name.
RFC-0064 (still Draft) is edited to record that no pack-level alias mechanism
exists and that the migration is documentation-only. `build-self` is run to
propagate the rename into projected outputs.

**Two namespaces that do not change:** the `[experience]` layout table key in
adopter-owned `agentbundle-layout.toml` reference docs is an activity-type
identifier, not a pack name — it stays. The `experience-reviewer` agent name
is functional (not pack-derived) and stays.

## Boundaries

### Always do

- Rename only operative references — files that execute, build, or run against
  the actual pack name. Leave historical references in frozen RFC/ADR/spec
  bodies intact.
- Bump version to `1.0.0` in both `pack.toml` and `plugin.json` (breaking
  change — major bump).
- Update `display_name`, pack-name prose in `description`, and `documentation`
  link in `pack.toml` and `plugin.json` to reflect the new name.
- Sweep the entire `packs/` tree for operative `experience` pack-name
  references — at minimum the six confirmed cross-pack files plus intra-pack
  SKILL.md files within the renamed pack.
- Update guide prose and slug-named guide file within `docs/guides/experience-design/`
  to reflect the new pack name.
- Update all platform-site surfaces: `site/mkdocs.yml` nav entries and guide
  paths; `tools/build-site.py` PACKS list entry and stale description;
  `web/src/content/packs/` and `web/src/content/journeys/` file renames and
  frontmatter; `web/src/pages/journeys/index.astro` display-order entry; and
  `README.md` pack table row.
- Create `packs/experience-design/AGENTS.md` with a migration table: pack name
  change, confirmation that all 18 skill slugs are unchanged, adopter
  install-state impact.
- Edit RFC-0064 body directly (it is still Draft — formal errata apply only
  after acceptance per RFC-0055) to record the alias-assessment outcome.
- Run `make lint-packs`, `make build-self`, and `pytest packages/agentbundle/`
  as the final gate.

### Ask first

- If any SKILL.md body within the renamed pack references the pack by old name
  in a way that is ambiguous between operative and historical — surface before
  editing.
- If the `build-site.py` description update conflicts with in-flight web copy
  changes on another branch.

### Never do

- Rename `experience-reviewer` (functional agent name, not pack-derived;
  confirmed 2026-07-19).
- Rename `[experience]` in any `agentbundle-layout.md` reference file — it
  documents the activity-type identifier, which stays.
- Edit `workspace.toml` `type =` fields (no `type = "experience"` exists, but
  do not introduce one).
- Rename references in frozen RFC/ADR bodies or shipped spec bodies (historical
  record).
- Rename free-prose occurrences of "experience" used as a discipline noun
  unrelated to the pack slug.
- Add a new top-level directory without running `make build-self`.
- Introduce a compatibility shim or dual-name projection — migration is
  documentation-only; no alias code.

## Testing Strategy

**Goal-based check** for all structural ACs: `make lint-packs` exits 0;
`make build-self` exits 0; `pytest packages/agentbundle/` green. These are the
canonical pass/fail signals for the rename.

**Goal-based check** for each name-change AC: targeted `grep` / `find`
one-liners confirming old names are absent and new names are present in the
operative file set. Each task's `Done when:` states the exact check.

No TDD stubs required — this spec has no logic invariants, only renaming
invariants. No manual QA — no user-facing UI surface is introduced.

## Acceptance Criteria

- [x] `packs/experience-design/` directory exists; `packs/experience/` does not
  exist.
- [x] `packs/experience-design/pack.toml` has `name = "experience-design"`,
  `version = "1.0.0"`, `display_name = "Experience Design"`, and `documentation`
  link updated to `.../docs/guides/experience-design/`.
- [x] `packs/experience-design/.claude-plugin/plugin.json` has
  `"name": "experience-design"` and `"version": "1.0.0"`.
- [x] All 18 skill directories in `packs/experience-design/.apm/skills/` are
  unchanged (function-named; none were renamed).
- [x] `tools/lint-experience-agnostic.py` updated: `_scan_root()` default path
  (`packs/experience` → `packs/experience-design`, line 150); docstring references
  updated (lines 2, 4, 8). The lint is invoked by CI (`build-check.yml`) with no
  `EXPERIENCE_ROOT` override; without this fix the path doesn't exist after T1 and CI
  build-check goes red.
- [x] Operative cross-pack references updated: `work-loop/SKILL.md:716,717`
  "experience pack" prose → "experience-design pack"; `new-spec/SKILL.md:241,243`
  "experience pack" prose → "experience-design pack"; `discovery-loop/SKILL.md:210`
  `` `experience` `` pack-name reference → `` `experience-design` `` (line 211 contains
  only `experience-reviewer` / `design-reviewer` agent names — those stay);
  `fresh-context.md:24` pack-name reference → "experience-design";
  `voice-and-microcopy/SKILL.md` — 7 lines (3, 17, 20, 28, 29, 32, 68) reference the
  `` `experience` `` pack name; all updated to `` `experience-design` ``;
  `product-engineering/README.md:123,127,129,139,142` — section heading, pack-name
  prose, install command, and link all updated.
- [x] `packs/experience-design/AGENTS.md` exists and contains: old pack name →
  new pack name; confirmation that all 18 skill slugs are unchanged; adopter
  install-state impact (uninstall `experience`, reinstall `experience-design`; no
  alias available).
- [x] RFC-0064 body (M3 ACs section, `experience → experience-design` bullet)
  records the alias-assessment outcome: pack-level alias unsupported (adapter-
  level only); migration is documentation-only via `packs/experience-design/AGENTS.md`;
  assessed 2026-07-18.
- [x] `docs/guides/experience-design/` directory exists; `docs/guides/experience/`
  does not exist.
- [x] `docs/guides/experience-design/reference/experience-design.md` exists;
  `docs/guides/experience-design/reference/experience.md` does not.
- [x] Guide prose in `docs/guides/experience-design/` contains no operative
  `experience` pack-name references (install commands, skill invocation prose
  updated; `[experience]` layout table key references and `experience-reviewer`
  references are correct and stay).
- [x] `docs/guides/README.md:23` — Designer/UX row: pack link and path updated to
  `experience-design`; "design critique" updated to "design review" (renamed in RFC-0066).
  `docs/guides/README.md:56` — pack table row updated to `experience-design`; stale
  skill descriptions ("aesthetic direction", "design systems", "design critique" — all
  renamed in RFC-0066) updated to current names.
- [x] `README.md:125` — pack table row updated to `experience-design`.
- [x] `site/mkdocs.yml` — all 6 entries updated: top-level packs nav title
  `Experience: packs/experience.md` → `Experience Design: packs/experience-design.md`;
  guides section header `- Experience:` (line 200) → `- Experience Design:`; guide
  README path; two guide page paths; and leaf nav entry "Experience Pack:" →
  "Experience Design Pack:" with `reference/experience-design.md` path.
- [x] `tools/build-site.py:35` — PACKS list entry updated:
  `("experience-design", "Experience Design", "user", ...)` with description
  referencing current skill names (no "aesthetic direction" or "design-critique"
  — both renamed in RFC-0066).
- [x] `web/src/content/packs/experience-design.md` exists; `web/src/content/packs/experience.md`
  does not. Frontmatter has `name: Experience Design`, updated `installCommand`,
  `docsUrl`, and `journeyUrl`; skills list (already current) intact; body prose
  updated.
- [x] `web/src/content/journeys/experience-design.md` exists;
  `web/src/content/journeys/experience.md` does not. Frontmatter `pack`,
  `docsUrl`, and `packUrl` updated; skill name references current.
- [x] `web/src/pages/journeys/index.astro` display-order entry updated to
  `{ slug: 'experience-design', name: 'Experience Design' }`.
- [x] Repo-wide operative sweep exits with zero unremediated pack-name references
  across both `packs/` and `tools/`:
  `` grep -rn '"experience"\|experience pack\|`experience`\|packs/experience[^-]' packs/ tools/ --include="*.md" --include="*.py" | grep -v "^packs/experience-design/" ``
  — `experience-reviewer` hits are expected (agent name unchanged) and are not
  unremediated. Note: backtick-wrapped `` `experience` `` is the dominant form in
  cross-pack SKILL.md files; `packs/experience[^-]` catches hardcoded paths in `.py`
  lint tools.
- [x] `make lint-packs` exits 0; `make build-self` exits 0;
  `pytest packages/agentbundle/` green.

## Assumptions

- Technical: `packs/experience/pack.toml` — `name = "experience"`,
  `version = "0.6.0"`, `display_name = "Experience"`, `documentation` →
  `docs/guides/experience/` (`packs/experience/pack.toml:2,6,55`)
- Technical: `packs/experience/.claude-plugin/plugin.json` — `"name":
  "experience"`, `"version": "0.6.0"` (`packs/experience/.claude-plugin/plugin.json`)
- Technical: 18 skill dirs in `packs/experience/.apm/skills/`, all function-named;
  zero are pack-eponymous (`ls packs/experience/.apm/skills/`)
- Technical: No `AGENTS.md` in experience pack root today (`ls packs/experience/`
  — only `README.md` and `pack.toml`)
- Technical: No pack-level alias mechanism; alias is adapter-scoped only
  (`m3-desk-research-rename/spec.md:152-155`)
- Technical: `agentbundle-layout.toml` has no `[experience]` section — no
  activity-type identifier to protect (`grep experience agentbundle-layout.toml`
  → empty)
- Technical: No `experience` references in `packages/agentbundle/` — zero
  integration test updates needed (`grep -rn experience packages/agentbundle/`
  → empty)
- Technical: Six confirmed cross-pack operative files: `work-loop/SKILL.md:716,717`;
  `new-spec/SKILL.md:241,243`; `discovery-loop/SKILL.md:210` (line 211 contains only
  agent names — leave); `fresh-context.md:24`; `voice-and-microcopy/SKILL.md` (lines
  3,17,20,28,29,32,68); and `product-engineering/README.md:123,127,129,139,142` (grep sweep)
- Technical: `experience-reviewer.md` agent description is purely functional —
  no pack-name prose requiring update
  (`packs/experience/.apm/agents/experience-reviewer.md:2-3`)
- Technical: Six intra-pack `agentbundle-layout.md` files reference `[experience]`
  as the layout table key (activity-type — stays); content needs no update, only
  path changes with the pack rename
  (`find packs/experience/ -name agentbundle-layout.md`)
- Technical: `[pack.evals] skills` in `pack.toml` has 11 function-named skills;
  none require renaming (`packs/experience/pack.toml:48`)
- Technical: `docs/guides/experience/` has `README.md`,
  `explanation/the-experience-thread.md`, `how-to/author-design-intent.md`,
  `reference/experience.md` (`ls docs/guides/experience/`)
- Technical: `site/mkdocs.yml` has 6 operative experience entries — 5 lowercase-path
  entries (caught by `grep experience site/mkdocs.yml`) plus the line-200 guides section
  header `- Experience:` (capital E, caught only by case-insensitive grep)
- Technical: `tools/build-site.py:35` description is stale — references
  "aesthetic direction" (renamed to `creative-direction` in RFC-0066)
  (`grep experience tools/build-site.py`)
- Technical: `web/src/content/packs/experience.md` skills list is already
  up-to-date with RFC-0066 18-skill set — only pack-name/URL changes needed
  (read `web/src/content/packs/experience.md`)
- Technical: `web/src/content/journeys/experience.md` skill names are already
  current (RFC-0066) — only pack-name/URL changes needed
  (read `web/src/content/journeys/experience.md`)
- Technical: `web/src/pages/journeys/index.astro:17` —
  `{ slug: 'experience', name: 'Experience' }` (`grep experience web/src/pages/journeys/index.astro`)
- Technical: `docs/guides/README.md:23,56` — 4 operative experience references
  (`grep experience docs/guides/README.md`)
- Technical: `README.md:125` — 1 operative experience reference in pack table
  (`grep experience README.md`)
- Process: RFC-0064 is still Draft — direct body edit is correct; formal errata
  apply only post-acceptance per RFC-0055
  (`docs/rfc/0064-ini-001-ai-native-ecosystem.md` Status: Draft)
- Process: Operative references renamed; historical references in frozen
  RFC/ADR bodies left intact (convention: `reference_renaming_catalogue_tool_operative_vs_historical`)
- Product: Major version bump 0.6.0 → 1.0.0 — confirmed by brief (Decisions
  already made)
- Product: No pack-level alias — documentation-only migration — confirmed by
  brief (Decisions already made)
- Product: `experience-reviewer` agent name stays unchanged — user confirmed
  2026-07-19
