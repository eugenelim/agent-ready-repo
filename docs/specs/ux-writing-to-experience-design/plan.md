# Plan: ux-writing-to-experience-design

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:**
  - `docs/specs/intent-short-route/` and its `notes/verification-ledger.md` § "T9
    install-then-update observation", for the delete-bump-record order and the
    scratch-repo upgrade walk.
  - `packs/AGENTS.md` § Version bump rule and § Self-hosting projection.
  - `docs/product/AGENTS.md`, for changelog fragments.
  - Non-structural: no new module, boundary, or dependency.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `notes/verification-ledger.md`. A genuine artifact error follows the
> controlled-amendment path.

## Approach

One pull request in five tasks: move the skill, retarget pack callers, retarget
guides, record and project, then observe the upgrade. The move is mechanical, so
the review shape is WIDE. Its proof is the rename similarity (AC-0004), one
`git grep` (AC-0009), fixed-file checks (AC-0010, AC-0018), and the existing site,
journey, census, link, and catalogue checks.
The riskiest part is the adopter upgrade, so it is observed last, against the
finished catalogue.

## Constraints

- RFC-0107 D6: the old place hard-retires with no alias, every operative reference
  moves first, frozen records stay as written, and release notes map the old name
  to its new home.
- RFC-0107 § Errata (2026-10-13): the nine longer-route skills keep their names.
  Nothing here touches them beyond removing a `ux-writing` mention.
- `packs/AGENTS.md`: major bump for a removal, minor bump for a new primitive.
- product-strategy changes only its non-projected `DESIGN.md` and takes no bump
  (owner ruling, eugenelim, 2026-10-14).
- No shipped pack text cites RFCs, ADRs, or specs.

## Construction tests

Cross-cutting checks run once, in T4, after self-host:

- `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .`.
- `python3 tools/lint-site-scope-parity.py`, `python3 tools/lint-pack-journeys.py`,
  `python3 tools/lint-journey-contract.py`, and `python3 tools/lint-web-journey-parity.py`.
- The census suite under `packs/agent-skill-engineering/tests/`.
- `make lint-ruff lint-mypy`.

## Durable-output map

| Spec durable output | Task |
| --- | --- |
| User promise (guides) | T3 |
| Current product truth (pack pages, site) | T2 |
| Interface compatibility (versions) | T1 |
| Release history (fragments) | T4 |
| Operations (upgrade observation) | T5 |

## Design (LLD)

### Design decisions

Owned by: T1, T2, T3, T5

- **The skill moves whole.** Only the `SKILL.md` body changes. The description stays
  byte-identical, so no activation run is owed (spec § Testing Strategy).
- **Voice charts stay at `docs/product/voice/<slug>.md`.** Adopters with existing
  charts keep them, and the skill keeps finding them.
- **Body wording.** The opening paragraph stops describing product-engineering's
  frame, de-risk, and decompose loop. References to `user-flow`, `quality-floor`, and
  `content-design` say "this pack" or name the skill alone. Routing to `intent frame`
  and `author-product-docs` stays, because both still name skills.
- **Adopter step.** After upgrading, every product-engineering adopter uninstalls
  and reinstalls product-engineering at the same scope. With both packs, the two
  upgrades run in either order. Without experience-design, the adopter installs it
  after the step to keep `ux-writing`. This rests on the spike in
  `notes/verification-ledger.md` (2026-10-14). `upgrade` keeps product-engineering's
  claim on `ux-writing`, and only the uninstall drops it. Installing
  experience-design before the step is refused. Deleting the folder by hand leaves
  the stale claim, so the notes do not offer it.
- **Journeys.** product-engineering's `JOURNEY.md` drops its `ux-writing` stage.
  experience-design's `JOURNEY.md` gains one after "Design each screen". The site
  journeys come from `tools/build-site.py --journeys-only`.
- **Rationale.** product-engineering's `DESIGN.md` loses § 5 "The ux-writing content
  layer" and § "Why ux-writing lives in product-engineering". Its `README.md`
  keeps one line naming the `docs/product/voice/` folder, written by
  experience-design's `ux-writing`. experience-design's `DESIGN.md` states why the
  skill lives beside `user-flow` and `content-design`, with no internal citations.
- **experience-design's artifact rules.** `DESIGN.md` § "Where artifacts live" and the
  `[pack.layout.repo]` comment in `pack.toml` say every artifact-writing skill writes
  under `[design] output_dir` and ships `references/agentbundle-layout.md`. Both
  name `ux-writing` as the one exception: it writes `docs/product/voice/<slug>.md`
  and only reads `[design]`.
- **Census.** The `ux-writing` row changes `pack` and moves to the
  experience-design block. `population_size` stays 132.

### Behavior & rules

Owned by: T2, T3, T4

- Operative surfaces are `packs/`, `guides/`, `web/src/`, `tools/`, and
  `docs/architecture/`. `docs/architecture/lifecycle-flow.md` already places
  `ux-writing` under Experience and needs no edit.
- Not operative, left as written: `docs/adr/`, `docs/rfc/`, `docs/specs/` other than
  this one, `docs/product/{findings,research,intents}/`, `docs/design/`, and the
  backlog comment in `workspace.toml`.

## Tasks

### T1: ux-writing lives in experience-design, and both manifests agree

**Depends on:** none
**Touches:** packs/product-engineering/.apm/skills/ux-writing/**, packs/experience-design/.apm/skills/ux-writing/**, packs/*/pack.toml, packs/*/.claude-plugin/plugin.json, packs/agent-skill-engineering/tests/fixtures/skill-census.json

**Tests:** no stub (goal-based).
- AC-0001, AC-0002: `git ls-files` under both skill paths.
- AC-0003: compare the frontmatter of `git show 3216c5b40:packs/product-engineering/.apm/skills/ux-writing/SKILL.md` with the moved file.
- AC-0004: `git diff --find-renames=100% --name-status 3216c5b40 -- packs/` shows `R100` for the seven non-`SKILL.md` files.
- AC-0005: `tr -s '[:space:]' ' '` on the moved `SKILL.md`, then `grep -F` each
  string. At `3216c5b40` this fails on `frames, de-risks, and decomposes`, which is
  wrapped across lines 8-9.
- AC-0006: `grep` on the moved `SKILL.md`.
- AC-0007, AC-0008: parse both `pack.toml` files and both `plugin.json` files.
- AC-0011: the census suite.

**Done when:** the T1 checks pass.

### T2: no pack surface places ux-writing in product-engineering

**Depends on:** T1
**Touches:** packs/experience-design/**, packs/product-engineering/**, packs/product-strategy/DESIGN.md, web/src/content/**, tools/add-rendering-directives.py

**Tests:** no stub (goal-based).
- AC-0009 with `git grep -h ux-writing -- packs web/src tools | grep -i 'product.engineering'`.
  `-h` drops the file path, so only line content is matched.
- AC-0010, AC-0017: `git grep -n ux-writing` on the named files, then the three
  lints after `tools/build-site.py --journeys-only`.
- AC-0018 for its `packs/` and `web/src/` members.
- product-engineering's `align-value-stream` eval and both `agentbundle-layout.md`
  references drop the `ux-writing` reader sentence, which AC-0009 catches.

**Done when:** the T2 checks pass.

### T3: the guides send adopters to experience-design for ux-writing

**Depends on:** T1
**Touches:** guides/experience-design/**, guides/product-engineering/**

**Tests:** no stub (goal-based).
- AC-0012: `git mv` the how-to, then search `guides/` and `web/src/` for the old path.
- AC-0019: read the moved page's frontmatter and its `install` lines.
- AC-0020: `make bootstrap-sites`, then `make site-link-check`, which builds
  `build/` and `build/docs/` and audits them. The page's relative links to `shape-a-feature-intent.md` and
  `../reference/intent-fields-and-modes.md` become `../../product-engineering/...`.
- AC-0009 (`git grep -h`) over `guides/`, including the `<!-- rung: -->` comments in
  `hand-it-to-build.md`, which point at the new skill path.
- AC-0018 for its `guides/` members.
- `guides/product-engineering/README.md` line 57 names the walk as twelve
  skills from this pack plus experience-design's `ux-writing`, on lines that never
  also name product-engineering (AC-0009), with no `thirteen` (AC-0018).
- `tools/validate_guides.py`, `tools/check-guide-index.py`, `tools/lint-guidebook-steps.py`,
  and `tools/lint-guides-no-repo-only-refs.py` pass. `tools/check-guidebook-walk.py`
  passes against the `build/docs` output that `make site-link-check` builds.

**Done when:** the T3 checks pass.

### T4: the catalogue is projected, valid, and released

**Depends on:** T2, T3
**Touches:** .claude/**, .agents/**, docs/product/changelog.d/**, docs/product/briefs/verb-mode-skills-and-slice-handover.md

**Tests:** no stub (goal-based).
- AC-0013, AC-0014: two fragments from `tools/changelog.py new`, then the fragment
  validator.
- AC-0016: self-host, then the cross-pack construction tests above.
- AC-0009 (`git grep -h`) over all five operative surfaces, once, on the final tree.

**Done when:** the T4 checks pass, and the brief's Spec map row matches this spec's
status.

### T5: the adopter step is observed against this change

**Depends on:** T4

**Tests:** no stub (manual QA).
- AC-0015: three scratch git repositories, `claude-code` adapter, repo scope, an
  isolated `AGENTBUNDLE_USER_ROOT`, the `3216c5b40` catalogue installed first, and
  the HEAD catalogue as the upgrade source. Record each command's last line, the
  `.agentbundle-state.toml` rows for `.claude/skills/ux-writing/SKILL.md`, and a
  `cmp` of the installed file against the experience-design source.

**Done when:** the ledger entry exists. If a run ends differently, stop: the
AC-0013 step is wrong, and the spec needs an amendment.

## Rollout

- **Delivery:** one PR. It is reversible by revert until the packs are released.
- **Deployment sequencing:** product-engineering 2.0.0 and experience-design 4.2.0
  release together in Wave A. The adopter step holds in either order.

## Risks

- A surface that names the old home without naming product-engineering on the
  same line slips past AC-0009. T2 and T3 read every hit of `git grep -n ux-writing`
  on the operative surfaces, not only the AC-0009 hits.
- The census or journey generator orders rows. Run the generator rather than
  hand-placing rows.

## Changelog

- 2026-10-14: spec approved by eugenelim
- 2026-10-14: plan approved by eugenelim
- 2026-10-19: spec amendment (AC-0010 wording) approved by eugenelim
- 2026-10-19: plan amendment (Rationale wording) approved by eugenelim
