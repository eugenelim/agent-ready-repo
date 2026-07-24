# Spec: xd-state-reviewer-doctrine

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0071 (D3d, D9)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `design-review` skill and its shared `quality-floor.md` reference are the
quality gate every experience-design artifact passes through. The floor's state
set is incomplete — it covers 8 of the 18 states the `frontend-engineering`
skill enforces at build time, leaving 10 states (offline, blocked,
destructive-confirmation, long-content, large-data-set, high-zoom,
reduced-motion, keyboard-only, no-results, and content) unguarded at design
time. The skill runs a single undifferentiated review pass, making it hard for
designers to distinguish what failed and how seriously. The evals do not cover
the failure modes currently observed in weak submissions.

This spec closes the gap: the quality floor matches the FE state matrix exactly
(18 states), `design-review` enforces a three-pass structure with severity tiers
and rendered evidence, and the evals include weak fixtures for each named failure
mode. Adopters receive a how-to guide, a state coverage reference, and an updated
journey page showing design-review as the explicit gate before the independent experience-reviewer pass.

## Boundaries

### Always do

- Match the quality-floor.md state set exactly to the 18-state matrix in
  `packs/core/.apm/skills/frontend-engineering/SKILL.md`.
- Use platform-agnostic language throughout all SKILL.md additions (no CSS,
  SwiftUI, React, Android, iOS, Angular, Vue, or similar names).
- Keep SKILL.md description ≤ 1024 characters.
- Apply the same severity tiers (blocker / concern / suggestion) consistently
  across all three review passes.

### Ask first

- Any change to the `digital-experience-contract.md` ownership fields (would
  trigger drift in other packs).
- Any new top-level directory under `packs/` or `docs/`.

### Never do

- Add a new skill or rename an existing skill in this PR (skill boundary changes
  are governed by separate RFC decisions).
- Add a new external dependency to the pack.
- Mention specific framework or platform names in SKILL.md description or body
  (experience agnosticism lint will fail).
- Split the three passes into separate skills.

## Testing Strategy

All behaviors are skill-doc and guide changes verified by goal-based checks and
manual QA:

- **Goal-based** — version parity: `grep version packs/experience-design/pack.toml`
  and `python3 -c "import json; print(json.load(open('packs/experience-design/.claude-plugin/plugin.json'))['version'])"` both return `1.5.0`.
- **Goal-based** — experience agnosticism lint: `python3 tools/lint-experience-agnostic.py` exits 0.
- **Goal-based** — contract drift check: `python3 tools/check-contract-drift.py --root .` exits 0.
- **Goal-based** — build-self: `python3 tools/build_gate_chain.py build-self --force --packs-dir packs` exits 0; dry-run shows no drift.
- **Goal-based** — state count: quality-floor.md covers exactly 18 named states.
- **Goal-based** — description length: SKILL.md frontmatter description ≤ 1024 chars.
- **Manual QA** — read quality-floor.md and confirm all 18 state names appear verbatim matching the FE matrix.
- **Manual QA** — read design-review SKILL.md and confirm: three-pass structure named; severity tiers defined; rendered evidence required.
- **Manual QA** — read how-to guide and confirm it shows the three-pass structure and severity rubric.
- **Manual QA** — read journey page and confirm design-review three-pass is the explicit gate before FE handoff.

## Acceptance Criteria

- [x] `quality-floor.md` contains all 18 states matching the FE matrix verbatim: loading, empty, error, partial, disabled, content, success, first-run, no-results, permission/denied, offline, blocked, destructive-confirmation, long-content, large-data-set, high-zoom, reduced-motion, keyboard-only.
- [x] `design-review` SKILL.md enforces a three-pass structure: Pass 1 (cold-read: audience + job + rendered only), Pass 2 (primary task + one unhappy path across desktop/tablet/mobile, keyboard + focus + zoom + reduced-motion), Pass 3 (contract review across all disciplines).
- [x] Severity tiers (blocker / concern / suggestion) are defined with explicit rules: a11y failures must not be softened to suggestion; aesthetic preferences must not be presented as usability defects.
- [x] Rendered evidence is required when a rendered surface exists.
- [x] `eval_queries.json` includes weak-fixture queries covering: architecture-first hero, inventory-first pack page, every-section-as-cards, desktop-only, missing permission states, attractive UI with unclear write consequences.
- [x] `evals.json` assertions reflect the three-pass structure and severity tier rules.
- [x] `docs/guides/experience-design/how-to/design-review.md` exists and shows the three-pass structure and severity rubric.
- [x] `docs/guides/experience-design/reference/` contains a state coverage reference with all 18 states and example treatment per state.
- [x] `web/src/content/journeys/experience-design.md` shows design-review three-pass as the explicit gate before the independent experience-reviewer pass.
- [x] `packs/experience-design/pack.toml` version is `1.5.0`.
- [x] `packs/experience-design/.claude-plugin/plugin.json` version is `1.5.0`.
- [x] `workspace.toml` has `spec/xd-state-reviewer-doctrine` in `["ini-003".work].shipped`, not in `.queue`.
- [x] `python3 tools/lint-experience-agnostic.py` exits 0 on the XD pack.
- [x] `python3 tools/check-contract-drift.py --root .` exits 0.
- [x] `python3 tools/build_gate_chain.py build-self --dry-run --packs-dir packs` shows no drift.

## Assumptions

- Technical: experience-design pack is at 1.4.0 on `origin/main` (source: `git show origin/main:packs/experience-design/pack.toml`)
- Technical: Canonical 18-state set is in `packs/core/.apm/skills/frontend-engineering/SKILL.md` lines 197–221 (source: Read of that file)
- Technical: quality-floor.md currently covers 8 states explicitly, missing 10 vs. the FE matrix (source: Read of quality-floor.md)
- Technical: `lint-experience-agnostic.py` currently passes on the XD pack (source: probe run)
- Technical: CI test `test_pack_toml_version_matches_plugin_json` enforces version parity (source: Rule 4 in task brief)
- Process: Per-spec minor bump: 1.4.0 → 1.5.0 (source: RFC-0071 D9)
- Process: Spec is constrained by RFC-0071 (source: docs/rfc/0071-digital-experience-doctrine.md)
- Process: Conventional Commits format, no Co-Authored-By trailer (source: docs/CONVENTIONS.md + Rule 9)
