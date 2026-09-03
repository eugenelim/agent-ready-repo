# Skill description semantic drift gate

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/local-gate-ci-parity AC12](../../specs/local-gate-ci-parity/spec.md)
- **Authority:** [spec/pack-description-quality](../../specs/pack-description-quality/spec.md)

## Outcome

Skill descriptions retain valid activation and handoff semantics as the catalogue and Codex skills-context budget evolve.

## Opportunity

The catalogue has structural checks and refreshed descriptions, but it has no current semantic-drift gate for quoted skill references and required neighbours, and no current measurement of activation loss under Codex truncation.

## What this absorbs

### xd-chain-structural-invariants-uncovered

Experience Design has a 20-skill boundary matrix, refreshed frontmatter descriptions, and declared-inventory existence checks. The remaining gap is semantic drift: no gate verifies that backtick-quoted skill names in descriptions resolve across the catalogue, including legitimate cross-pack references, or that descriptions retain their matrix-required nearest-neighbour references.

The marketing-site to docs-site link gap is closed and must not be recreated as open work. The recorded fix was a pure-stdlib `tools/*.py` checker wired into the pages workflow after both builds because it needs the built tree and cannot run in `build-check`. It landed and was reverted twice (`#852` → `#854`). The committed checker is `tools/check-rendered-site-links.py`. `.github/workflows/pages.yml` runs it after both builds, and `make site-link-check` runs it locally. It was verified on 2026-08-17 by `spec/site-contract-provenance-cleanup` AC4. AC5 resolved the `site-link-check-contract-docs` guidance gap into that closure: `guides/AGENTS.md`, `docs-site/AGENTS.md`, and `Makefile` name the checker and distinguish the local sequence from the CI two-phase sequence. This block is closed, has no `{slug = ...}` object, and is not open membership. Do not treat a root-relative link lacking the `/agent-ready-repo` base prefix as off-site; an earlier draft silently skipped 8 such links. Do not reintroduce a `build/primitives-fixture/` exclusion: its 8 dead placeholder `href` values are gone. Verified 2026-08-15, `grep -oE 'href=(\{[^}]*\}|"[^"]*")' web/src/pages/primitives-fixture.astro` returns exactly two, both live. Its original source was `spec/marketing-docs-link-repair` and was out of scope.

The stale `docsUrl` text in the shipped `docs/specs/phase4b-product-docs-completion/spec.md` is also closed. The affected locations were line 24, line 66, and checked AC7 asserting `docsUrl is /guides/frontend-engineering/`. The recorded options were (a) an errata note at the head recording that the direction was superseded on 2026-08-06 and by which spec, or (b) an in-place AC7 amendment. On 2026-08-17, `spec/site-contract-provenance-cleanup` AC1 chose (a): a Status-line annotation names ADR-0055 as standing authority and `spec/marketing-docs-link-repair` as the correcting spec, while stating it is not a supersession. Option (b), amending AC7 in place, was declined because it would edit a frozen body. The body, including stale AC7 text, remains deliberately unchanged. Its original source was `spec/marketing-docs-link-repair` and was out of scope. This must not become a duplicate item.

Three XD-chain structural invariants lost their only implementation. `tools/check-xd-chain.py` and its `xd-chain-gate.yml` workflow are absent from main and readable only from unreachable commit `321c825c`. Two of five old invariants survive elsewhere: description length through `agentbundle catalogue lint`, and Digital-Experience-Contract copy parity through `tools/catalogue/check_contract_parity.py`. The missing three are chain completeness (every chain skill exists at its expected `SKILL.md` path), phantom-handoff resolution (every backtick-quoted skill name in a description resolves to a real in-pack `SKILL.md`), and boundary-guard adjacency (each chain skill description references its required neighbours). Nothing detects a chain skill renamed out from under a sibling description today. Re-derive the chain map against the current experience-design pack because the old `design-token-taxonomy` and `design-system-foundations` names are stale; ADR-0052 and RFC-0071 record that change. Then reimplement the three checks, or explicitly decide that pack lint should carry generic phantom-handoff detection instead of a per-chain check. Unblocks when picked up; no dependency.

### codex-skill-description-budget

Codex CLI 0.146.0 rendered skill descriptions into an approximately 2% skills-context budget and warned, `Skill descriptions were shortened to fit the 2% skills context budget`. At that observation, 122 skill descriptions totalled approximately 72,000 characters, approximately 18k tokens, roughly three times the budget. The longest descriptions, long precisely to drive activation, were cut hardest. This is distinct from the pack-description ceiling, which is marketplace display copy rather than activation text. The catalogue now holds 137 skill descriptions rather than 122. Remeasure aggregate size and activation loss against the current Codex release before shortening activation-bearing text. The direction is an eval-backed pass, not a prose sweep; the per-target 1024 cap was intended to help activation. Unblocks when a current-release measurement establishes activation loss under truncation.

## Assumptions

- The semantic-gate state needs current catalogue evidence resolving quoted names and nearest-neighbour requirements, including cross-pack references.
- The Codex budget state needs a measurement under the current Codex release; the 122-description, approximately 72,000-character observation from Codex CLI 0.146.0 is historical and must not be treated as the current count.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
