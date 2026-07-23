# Spec: product-brief-intake-leak-guard

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim

Mode: light (no risk trigger fired)

## Objective

Extend `tools/lint-agent-artifacts.py` to cover SKILL.md bodies and `examples/` files under `packs/core/.apm/skills/`, applying the adopter-facing leak guard (no `agent-ready-repo`, `RFC-NNNN`, or `K-NNNN`) as a regression guard. Files are currently clean; the check prevents future leaks.

## Acceptance Criteria

- [x] `lint-agent-artifacts.py` defines `_APM_SKILL_BLOCKLIST` with three patterns.
- [x] `lint-agent-artifacts.py` scans `packs/core/.apm/skills/*/SKILL.md` bodies and `packs/core/.apm/skills/*/examples/*.md` for the three blocklist patterns.
- [x] A file containing `agent-ready-repo`, `RFC-00XX`, or `K-00XX` causes the linter to exit non-zero and name the offending file and pattern.
- [x] A `LINT_APM_ROOT` env var overrides the default path, enabling fixture-based self-tests.
- [x] Negative fixture tests covering all three patterns are added to `tools/test-lint-agent-artifacts.sh`.
- [x] The check passes clean on the current `packs/core/.apm/skills/` tree.

## Tasks

1. Add `_APM_SKILL_BLOCKLIST` constant to `lint-agent-artifacts.py`.
2. Add the APM scan loop in `main()` with `LINT_APM_ROOT` env override.
3. Add negative fixture test cases to `tools/test-lint-agent-artifacts.sh`.

**Verification:** goal-based — `LINT_APM_ROOT=<tmp-dir-with-leak> python3 tools/lint-agent-artifacts.py` exits non-zero; `python3 tools/lint-agent-artifacts.py` on the real repo exits 0.

**Declined:**
- Extending to all packs (not just core) — backlog item scopes to `packs/core/.apm/skills/`.
- Checking frontmatter — body content is the higher-risk surface.
- Deduplicating patterns with `lint-catalogue-seeds.py` — avoiding cross-tool coupling for a small closed set.
