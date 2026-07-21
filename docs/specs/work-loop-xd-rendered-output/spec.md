# Spec: work-loop — XD rendered-output clarification

- **Status:** Shipped
- **Mode:** light (no risk trigger fired)
- **RFC:** RFC-0064 (experience-design gap remediation)

## Objective

Add a one-sentence clarification to the `experience-reviewer` bullet in the
work-loop REVIEW section: for web surface diffs, "rendered output" means the
built site (describe key pages from build output), not the code diff. Without
the built artifact, genre rubrics and cross-page consistency checks cannot be
applied.

## Acceptance Criteria

- [x] The experience-reviewer bullet in the REVIEW section of
  `packs/core/.apm/skills/work-loop/SKILL.md` includes a sentence clarifying
  that for web surfaces (HTML/CSS/JS), "rendered output" means the built site —
  run the build and describe key pages from the output, not the code diff.
- [x] The same clarification is present in the two projected copies:
  `.claude/skills/work-loop/SKILL.md` and `.agents/skills/work-loop/SKILL.md`.
- [x] The backlog item `work-loop-xd-rendered-output` is removed from
  `[backlog].open` in `workspace.toml`.
- [x] `packs/core` version is bumped to 0.13.2 in `pack.toml` and
  `packs/core/.claude-plugin/plugin.json`.

## Tasks

1. Edit experience-reviewer block in pack source + two projections (goal-based).
2. Bump pack version to 0.13.2.
3. Remove backlog item from workspace.toml.
