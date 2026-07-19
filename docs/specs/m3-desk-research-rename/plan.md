# Plan: m3-desk-research-rename

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Eight sequential tasks, each a self-contained edit or git-mv. Start with the
directory rename (T1) — everything else keys off the new path. Skill directory
renames (T3) come before cross-pack reference updates (T4) so grep verification
in T4 can confirm the new slugs are in place. Test updates (T7) follow the pack
and skill renames so the test fixtures match the live pack. Build gates (T8) are
the final task and the canonical pass/fail signal.

No logic changes — every edit is a string substitution or a file/directory move.
The riskiest part is the operative-vs-historical distinction: the rule is
"does this reference cause a build, test, or runtime failure if stale?" If yes,
update. If it's frozen prose in a shipped RFC/ADR body, leave it. When in doubt,
surface rather than guess.

## Constraints

- RFC-0064 M3 governs this rename; no sub-RFC needed.
- `[pack.layout.repo] parent = ".context/research"` in `pack.toml` is the
  bug-fix spec's concern — do not touch it here.
- `workspace.toml` `type = "research"` and `agentbundle-layout.toml [research]`
  section key are activity-type identifiers — do not rename them.
- Adapter-level alias mechanism is adapter-scoped; no pack-level alias is
  possible. Migration is documentation-only.

## Construction tests

**Integration:** `pytest packages/agentbundle/tests/integration/` — covers the
live pack install round-trip; must pass with the renamed pack before T8 closes.

**Manual verification:**
- `find packs/desk-research/.apm/skills -maxdepth 1 -type d | sort` — confirm
  five renamed dirs present, five old names absent.
- `grep -rn "\/research\b\|research-project" packs/desk-research/.apm packs/core/.apm/skills/check-workspace packs/product-engineering/.apm/skills/frame-domain` — confirm zero
  operative hits after T4 (excluding the `[research]` activity-type key and
  historical frozen prose).

## Design (LLD)

### Component / module decomposition

The change touches four layers:

1. **Pack registry** — `pack.toml` + `plugin.json`: name, version, display_name,
   docs link, evals skill list.
2. **Skill directories** — `git mv` on five skill dirs within `.apm/skills/`.
3. **Operative cross-pack references** — three files outside the pack:
   `check-workspace/SKILL.md`, `frame-domain/SKILL.md`, `evidence-retriever.md`.
   Plus intra-pack SKILL.md files that invoke peer skills by old slug.
4. **Test fixtures** — integration tests that install the actual pack by name;
   unit tests that assert shipped-pack metadata.

Layer 3 disambiguation guide — use this for every reference encountered:

| Reference type | Action |
|---|---|
| Skill invocation slug in operative SKILL.md body (e.g. `invoke \`research\``) | Rename |
| Pack name in SKILL.md T1/T2 prereq block | Rename |
| Skill slug in test `pack=` / `pack_name=` / `has_pack()` against live catalogue | Rename |
| `type = "research"` in workspace.toml or `[research]` in agentbundle-layout.toml | Leave |
| `/research` URL in an already-shipped RFC/ADR/spec body | Leave |
| `"research"` as an arbitrary fixture string in a schema-shape unit test | Leave |

### Dependencies & integration

- `frame-domain` (PE pack) wraps `research` applied mode — it calls the skill
  by slug. After T3 renames the skill dir, T4 must update all call-site slugs in
  `frame-domain/SKILL.md`.
- `check-workspace` (core pack) surfaces the skill prompt for `type = "research"`
  shaping queue entries — line 89 already says "requires desk-research pack" but
  names the old skill slug `research-project-start`. T4 fixes the slug.
- `evidence-retriever.md` description names `/research` in its frontmatter
  description field — this is the canonical agent description read by harnesses.
  T4 updates it to `/desk-research`.

## Tasks

### T1: Rename the pack directory

**Depends on:** none

**Touches:** `packs/research/` → `packs/desk-research/`

**Tests:**
- `[ -d packs/desk-research ] && [ ! -d packs/research ]` exits 0

**Approach:**
- `git mv packs/research packs/desk-research`

**Done when:** `packs/desk-research/` exists; `packs/research/` does not; `git status`
shows the move cleanly.

---

### T2: Update pack manifest (pack.toml + plugin.json)

**Depends on:** T1

**Touches:** `packs/desk-research/pack.toml`, `packs/desk-research/.claude-plugin/plugin.json`

**Tests:**
- `grep 'name = "desk-research"' packs/desk-research/pack.toml` exits 0
- `grep 'version = "1.0.0"' packs/desk-research/pack.toml` exits 0
- `grep '"name": "desk-research"' packs/desk-research/.claude-plugin/plugin.json` exits 0
- `grep '"version": "1.0.0"' packs/desk-research/.claude-plugin/plugin.json` exits 0
- `grep 'desk-research-project-start' packs/desk-research/pack.toml` exits 0 (evals list updated)

**Approach:**
- In `pack.toml`: update `name = "research"` → `name = "desk-research"`;
  `version = "0.6.1"` → `version = "1.0.0"`;
  `display_name = "Research"` → `display_name = "Desk Research"`;
  `documentation` URL: `.../docs/guides/research/` → `.../docs/guides/desk-research/`;
  `[pack.evals] skills` list: update `"research"` → `"desk-research"` and
  `"research-project-start"` → `"desk-research-project-start"`;
  inline comment prose that names "research's skills" or "research-project-start as the
  lifecycle entry point" — update to `desk-research`.
- In `plugin.json`: update `"name"` → `"desk-research"`;
  `"version"` → `"1.0.0"`;
  `"description"`: update any prose that names "research" as the pack name to "desk-research"
  (keep the methodology/discipline description intact).

**Done when:** all five grep checks above exit 0.

---

### T3: Rename the five skill directories

**Depends on:** T1

**Touches:** `packs/desk-research/.apm/skills/research/`,
`packs/desk-research/.apm/skills/research-project-{start,digest,check,synthesize}/`

**Tests:**
- `find packs/desk-research/.apm/skills -maxdepth 1 -type d -name "desk-research" | wc -l` returns 1
- `find packs/desk-research/.apm/skills -maxdepth 1 -type d -name "desk-research-project-*" | wc -l` returns 4
- `find packs/desk-research/.apm/skills -maxdepth 1 -type d -name "research" | wc -l` returns 0
- `find packs/desk-research/.apm/skills -maxdepth 1 -type d -name "research-project-*" | wc -l` returns 0

**Approach:**
```
git mv packs/desk-research/.apm/skills/research           packs/desk-research/.apm/skills/desk-research
git mv packs/desk-research/.apm/skills/research-project-start     packs/desk-research/.apm/skills/desk-research-project-start
git mv packs/desk-research/.apm/skills/research-project-digest    packs/desk-research/.apm/skills/desk-research-project-digest
git mv packs/desk-research/.apm/skills/research-project-check     packs/desk-research/.apm/skills/desk-research-project-check
git mv packs/desk-research/.apm/skills/research-project-synthesize packs/desk-research/.apm/skills/desk-research-project-synthesize
```

**Done when:** all four find-checks above return the expected counts.

---

### T4: Update operative cross-pack and intra-pack references

**Depends on:** T3

**Touches:**
`packs/core/.apm/skills/check-workspace/SKILL.md`,
`packs/core/.apm/skills/init-project/SKILL.md`,
`packs/core/.apm/skills/contract-acquisition/SKILL.md`,
`packs/product-engineering/.apm/skills/frame-domain/SKILL.md`,
`packs/product-engineering/.apm/skills/frame-domain/examples/example-assistant.md`,
`packs/product-engineering/.apm/skills/discovery-loop/SKILL.md`,
`packs/product-engineering/.apm/skills/frame-intent/references/knowledge-surfaces.md`,
`packs/experience/.apm/skills/map-internal-process/SKILL.md`,
`packs/desk-research/.apm/agents/evidence-retriever.md`,
`packs/desk-research/.apm/skills/desk-research-project-start/references/agentbundle-layout.md`,
`packs/desk-research/README.md`,
intra-pack SKILL.md files that invoke peer skills by old slug

**Tests:**
- Repo-wide sweep (run after all edits in this task):
  `grep -rn "\/research\b\|research-project\|\`research\`\|\"research\"\|'research'" packs/ --include="*.md" | grep -v "docs/rfc\|docs/adr\|docs/specs\|# \|<!--"` — review every hit; zero unremediated operative references.
- `grep -n "research-project-start" packs/core/.apm/skills/check-workspace/SKILL.md` returns 0 lines.

**Approach:**

*Step 0 — run the repo-wide sweep first (backtick form is the most common operative shape — include it):*
```
grep -rn "\/research\b\|research-project\|\`research\`\|\"research\"\|'research'" packs/ --include="*.md"
```
Review every hit using the disambiguation table in Design (LLD). The list below covers
all confirmed operative files; the sweep catches any others.

*check-workspace/SKILL.md:*
- Line 64: `run \`research-project-start\`` → `run \`desk-research-project-start\``
- Line 89: `research-project-start (requires desk-research pack)` →
  `desk-research-project-start (requires desk-research pack)`

*init-project/SKILL.md:*
- Lines 69, 141, 159 — operative pack/skill slug references: `research` pack name →
  `desk-research`; `research` skill slug → `desk-research`.

*contract-acquisition/SKILL.md:*
- Line 149 — operative skill reference: `research` skill → `desk-research`.

*frame-domain/SKILL.md:*
- All operative invocation slugs: `` `research` `` applied mode → `` `desk-research` ``
  applied mode. Disambiguation: slug = backtick-wrapped standalone or `invoke \`research\``
  / `wraps \`research\``; free prose like "research-grounded" or "the wrapped research"
  is not a slug and is left intact.
- Line 207: `research-project-start` sibling skills → `desk-research-project-start`.

*frame-domain/examples/example-assistant.md:*
- Lines 19, 22 — update operative `research` references.

*discovery-loop/SKILL.md:*
- Line 210 detect-and-degrade: update `research` pack name to `desk-research`.

*frame-intent/references/knowledge-surfaces.md:*
- Line 118 — update operative reference.

*evidence-retriever.md:*
- Frontmatter description: `Used by \`/research\` standard and deep modes` →
  `Used by \`/desk-research\` standard and deep modes`

*agentbundle-layout.md reference doc (post-T3 path: `desk-research-project-start/references/`):*
- Update prose that names the pack as "research" or "the \`research\` pack" to
  "desk-research" / "the \`desk-research\` pack". The section key `[research]` stays;
  update prose only.

*map-internal-process/SKILL.md (packs/experience):*
- Line 17: `use \`research\`'s \`methodology\` shape instead` — leave (discipline prose, not a
  skill-invocation slug). This reference correctly names the skill the user should invoke;
  update the slug to `` `desk-research` ``.

*README.md (packs/desk-research/ — post-T1):*
- Line 11: `` `research` `` in skills list → `` `desk-research` ``
- Line 47: `guides/research/` link → `guides/desk-research/`

*Frontmatter `name:` fields — all five renamed SKILL.md files:*
- `packs/desk-research/.apm/skills/desk-research/SKILL.md`: `name: research` → `name: desk-research`
- `packs/desk-research/.apm/skills/desk-research-project-start/SKILL.md`: `name: research-project-start` → `name: desk-research-project-start`
- `packs/desk-research/.apm/skills/desk-research-project-digest/SKILL.md`: `name: research-project-digest` → `name: desk-research-project-digest`
- `packs/desk-research/.apm/skills/desk-research-project-check/SKILL.md`: `name: research-project-check` → `name: desk-research-project-check`
- `packs/desk-research/.apm/skills/desk-research-project-synthesize/SKILL.md`: `name: research-project-synthesize` → `name: desk-research-project-synthesize`

*Intra-pack SKILL.md sweep:*
- Review every hit from the Step 0 grep within `packs/desk-research/.apm/skills/`.
  Apply the disambiguation table: skill invocation slugs → rename; free discipline
  prose and `[research]` layout key references → leave.

**Done when:** repo-wide sweep returns zero unremediated operative skill-slug references;
`check-workspace` grep returns 0 lines.

---

### T5: Create AGENTS.md + record assessment in RFC-0064

**Depends on:** T2

**Touches:**
`packs/desk-research/AGENTS.md` (new file),
`docs/rfc/0064-ini-001-ai-native-ecosystem.md`

**Tests:**
- `[ -f packs/desk-research/AGENTS.md ]` exits 0
- `grep "desk-research" packs/desk-research/AGENTS.md` exits 0
- `grep -i "alias\|assessment" docs/rfc/0064-ini-001-ai-native-ecosystem.md` exits 0

**Approach:**

*AGENTS.md — create with these sections:*

```markdown
# AGENTS.md — desk-research pack

## Migration from `research` (v0.6.x → v1.0.0)

The pack was renamed from `research` to `desk-research` in v1.0.0 (RFC-0064 M3).

### Name changes

| Before (≤ 0.6.x) | After (≥ 1.0.0) |
|---|---|
| Pack: `research` | Pack: `desk-research` |
| Skill: `/research` | Skill: `/desk-research` |
| Skill: `/research-project-start` | Skill: `/desk-research-project-start` |
| Skill: `/research-project-digest` | Skill: `/desk-research-project-digest` |
| Skill: `/research-project-check` | Skill: `/desk-research-project-check` |
| Skill: `/research-project-synthesize` | Skill: `/desk-research-project-synthesize` |

### What does not change

- `workspace.toml` `type = "research"` entries — activity-type field, not pack name.
- `agentbundle-layout.toml [research]` section key — activity-type identifier.
- The six function-named skills: `build-outline`, `compare-hypotheses`,
  `decision-archaeology`, `devils-advocate`, `identify-perspectives`, `source-map`.

### Adopter install-state impact

Your install state (`~/.agentbundle/state.toml`) tracks the old pack name `research`.
After upgrading to the catalogue with v1.0.0:
1. Uninstall the old pack: `agentbundle uninstall research --adapter <adapter>`
2. Reinstall: `agentbundle install desk-research --adapter <adapter>`

No alias is available — the installer does not support pack-level aliases.
```

*RFC-0064 body edit — RFC-0064 is still Draft; formal post-acceptance errata (RFC-0055
mechanism) do not apply. Edit the RFC body directly:*

1. In the Affected-surface line (contains "M3 pack renames: `research` → `desk-research`…
   `agentbundle-layout.toml`, deprecation aliases, build-self"), remove
   "`agentbundle-layout.toml`" and "deprecation aliases" from the list — neither
   applies (layout key stays; no alias exists or will be added).
2. In the `research → desk-research` AC bullet, append a parenthetical:
   > (Alias assessment: agentbundle alias mechanism is adapter-scoped only — no pack-level
   > alias; migration is documentation-only via `packs/desk-research/AGENTS.md`. Assessed
   > 2026-07-18, eugenelim.)

**Done when:** AGENTS.md exists with the migration table; RFC-0064 M3 pack-rename AC
contains the assessment note; grep checks above exit 0.

---

### T6: Rename docs/guides/research → docs/guides/desk-research + update guide content

**Depends on:** T2

**Touches:** `docs/guides/research/` → `docs/guides/desk-research/` (directory move);
guide files within (prose + slug-named file renames)

**Tests:**
- `[ -d docs/guides/desk-research ] && [ ! -d docs/guides/research ]` exits 0
- `grep -rn "\/research\b\|research-project\|\`research\`" docs/guides/desk-research/ --include="*.md"` returns 0 lines

**Approach:**
- `git mv docs/guides/research docs/guides/desk-research`
- Rename the two pack-named slug files:
  - `git mv docs/guides/desk-research/reference/research-pack.md docs/guides/desk-research/reference/desk-research-pack.md`
  - `git mv docs/guides/desk-research/tutorials/research-first-session.md docs/guides/desk-research/tutorials/desk-research-first-session.md`
- Update prose in all guide files — any invocation slug `/research` → `/desk-research`,
  `research-project-*` → `desk-research-project-*`, pack-name mentions `research pack` →
  `desk-research pack`. Leave topic-level prose ("research methodology", "how to do
  desk research") intact — these describe the discipline, not the skill slug.
- Verify no other operative files reference the old guide path:
  `grep -rn "guides/research" . --include="*.md" --include="*.toml" | grep -v "docs/rfc\|docs/adr\|docs/specs"` —
  update any hits outside frozen bodies.

**Done when:** directory move and file renames complete; both grep checks above pass.

---

### T7: Update test files that reference the actual pack by name

**Depends on:** T1, T3

**Touches:**
`packages/agentbundle/tests/integration/test_install_research_user_scope.py`,
`packages/agentbundle/tests/integration/test_install_copilot_full_parity.py`,
`packages/agentbundle/tests/integration/test_install_profile_live.py`,
`packages/agentbundle/tests/integration/test_install_default_source.py`,
`packages/agentbundle/tests/unit/test_enriched_pack_metadata.py`,
`packages/agentbundle/tests/unit/test_research_retrievers_conformance.py`,
possibly `tests/unit/test_render_table.py`, `tests/unit/test_cli_profile_surface.py`,
and `tests/unit/test_profile_reader.py`

**Tests:**
- `pytest packages/agentbundle/tests/integration/test_install_research_user_scope.py` green
- `pytest packages/agentbundle/tests/unit/test_enriched_pack_metadata.py` green
- `pytest packages/agentbundle/tests/unit/test_research_retrievers_conformance.py` green

**Approach:**

For each file, apply the disambiguation rule: update references that install, assert,
or path-resolve against the actual pack/skill from `packs/`; leave references that
use `"research"` as a generic test-fixture string unrelated to the live catalogue.

*Definite renames (live-catalogue references):*
- `test_install_research_user_scope.py`: rename throughout — `RESEARCH_PACK_SRC`,
  `"research"` pack name strings, `has_pack("research")` assertions, `packs/research`
  path strings.
- `test_install_copilot_full_parity.py:152`: `"research"` in the pack list → `"desk-research"`
- `test_install_profile_live.py:83`: `("architect", "research", "contracts")` →
  `("architect", "desk-research", "contracts")`
- `test_install_default_source.py:124,146`: `pack_name="research"` → `pack_name="desk-research"`
- `test_enriched_pack_metadata.py:40`: `{"core", "research", ...}` → `{"core", "desk-research", ...}`

*Definite rename (live-catalogue path):*
- `test_research_retrievers_conformance.py`: update `REPO_ROOT / "packs" / "research" / ".apm" / "skills" / "research"` path
  constant → `REPO_ROOT / "packs" / "desk-research" / ".apm" / "skills" / "desk-research"`.
  Read line 15 context comment and any `pack="research"` assertion strings before editing.

*Verify before touching (may be fixtures, not live-catalogue references):*
- `test_render_table.py:21`: `["research", "0.3.0", ...]` — if this row is a snapshot of
  actual catalogue metadata, update to `["desk-research", "1.0.0", ...]`; if it is an
  arbitrary fixture that tests table-rendering logic only, leave intact.
- `test_cli_profile_surface.py:39`: the inline profile string with `pack = "research"` —
  if this test installs from the live catalogue, update; if it tests profile-parsing with
  an arbitrary pack name, leave intact.
- `test_profile_reader.py:39,54`: `pack = "research"` / `("architect", "research", "contracts")` —
  if these are arbitrary profile-parser fixtures, leave intact; confirm before touching.

Read all three files before editing; apply the rule from the Design section.

**Done when:** both targeted pytest runs above are green; no `packs/research` path
references remain in the updated test files.

---

### T8: Build gates

**Depends on:** T1–T7

**Tests:**
- `make lint-packs` exits 0
- `make build-self` exits 0
- `pytest packages/agentbundle/` green (full suite)

**Approach:**
- Run `make lint-packs` first — it catches pack-structure violations before the
  expensive build-self step.
- Run `make build-self` — propagates the rename into projected outputs (marketplace,
  per-adapter projections).
- Run `pytest packages/agentbundle/` — full suite, not just integration.
- If any gate fails, fix before marking T8 done; do not skip or suppress.

**Done when:** all three commands exit 0 with no suppressed failures.

---

## Rollout

Big-bang cutover — no flag, no gradual. The rename is a single PR. Adopters with
`research` in their install state must reinstall (documented in AGENTS.md). No
infrastructure changes, no data migration, no external-system sequencing.

**Irreversible aspect:** once the PR merges, the old pack name `research` is gone
from the catalogue. An adopter who does not reinstall will have a stale state entry
but no pack to install. The AGENTS.md migration guide is the only mitigation.

## Risks

- **Intra-pack SKILL.md operative references missed.** The sweep in T4 must be
  exhaustive; a missed reference leaves a broken skill invocation. Mitigation:
  run the grep check in T4 before declaring done.
- **test_render_table.py / test_cli_profile_surface.py disambiguation error.** If
  these are live-catalogue fixtures and are not updated, the test suite will fail.
  Mitigation: read both files in T7 before deciding.
- **build-self undoes projection-only edits.** Memory note: `build-self` can overwrite
  projection-only edits made directly in projected paths. Mitigation: make edits in
  source (`packs/`) not in projected paths, then run build-self last.
- **Parallel bug-fix spec conflict.** If `research-project-start` bug-fix lands in
  the same session and touches `research-project-start/references/agentbundle-layout.md`,
  T4's prose update to that file may conflict. Mitigation: coordinate at T4 start;
  if the bug-fix is in-flight, defer that file to the bug-fix PR.

## Changelog

- 2026-07-18: initial plan
- 2026-07-19: pre-execute adversarial review — added backtick-form grep patterns to T4/T6
  sweep and Done-when checks; added map-internal-process/SKILL.md and README.md to T4
  Touches; added frontmatter name: field edits for all five renamed SKILL.md files to T4;
  added test_research_retrievers_conformance.py (live-catalogue path) to T7; added
  test_profile_reader.py to T7 verify-before-touching; added RFC-0064 Affected-surface
  line correction to T5 approach.
