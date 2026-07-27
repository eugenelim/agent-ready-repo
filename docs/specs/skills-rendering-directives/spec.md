**Mode:** light (user-directed)

**Status:** Shipped

**Objective:** Add rendering directives to all output-producing skill SKILL.md files so agents know which output shape each skill emits — table, status-list, mermaid, key-value, diff, tree, narrative — without loading the full catalog. Also create the reference catalog and update the skill authoring guide.

**Acceptance Criteria:**

- [x] `docs/guides/core/reference/output-rendering.md` created with the full directive catalog (8 directives + authoring how-to + omit rules with carve-out)
- [x] `.claude/skills/README.md` authoring section updated with rule 5 (declare output rendering directives inline)
- [x] All output-producing skills (~70 skills across 19 packs) have a `## Output rendering` section with only their applicable directive lines — batch-inserted via `tools/add-rendering-directives.py`
- [x] `new-package` includes the tree directive for scaffolded directory output
- [x] `jira-team-status` has the formal table directive block
- [x] `ai-adoption-report` has table + key-value directives
- [x] `flow-metrics` has table + key-value directives for human-facing summary presentation
- [x] User docs example output in `web/src/content/packs/atlassian.md` updated to use table shape (Ready-to-pull: 3 rows matching summary count)
- [x] Pack sources (`packs/`) updated; projected targets (`.claude/skills/`, `.agents/skills/`) regenerated via `build-self --force`
- [x] `AGENTS.local.md` updated with skills projection model: both targets, README.md exception, `--force` usage

**Tasks:**

1. ~~Create reference catalog~~ → created at `docs/guides/core/reference/output-rendering.md` (not `.claude/skills/references/` — that path doesn't project to adopters)
2. ~~Update `.claude/skills/README.md`~~ → Rule 5 added
3. ~~Write and run `tools/add-rendering-directives.py`~~ → 70 skills updated across all packs; build-self projected to both targets
4. ~~Update `web/src/content/packs/atlassian.md`~~ → table shape + row count corrected
5. ~~Adversarial review → fix~~ → design-review and devils-advocate added; severity-list label fixed; omit-rule carve-out added
