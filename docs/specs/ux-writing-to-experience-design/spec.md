# Spec: ux-writing-to-experience-design

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0107 (D6 and § Errata)
- **Brief:** brief:verb-mode-skills-and-slice-handover
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.



## Outcome

A team using the design seat gets `ux-writing` from the `experience-design` pack,
beside the `user-flow` state matrix and the `content-design` brand register it
reads, under the same skill name and the same description. After the upgrade step the release notes give, an adopter of
product-engineering ends with no `ux-writing` claimed by that pack, and one who
also has experience-design ends with exactly one `ux-writing`, owned by it.

## What Changes

- `ux-writing`, with its references, asset, and evals — from
  `packs/product-engineering/.apm/skills/` to `packs/experience-design/.apm/skills/`.
- The skill body's pack wording — it describes `user-flow`, `quality-floor`, and
  `content-design` as same-pack skills. Its description, procedure, voice-chart path
  (`docs/product/voice/<slug>.md`), and `[design]` layout lookup stay as they are.
- `[pack.evals].skills` — `ux-writing` leaves product-engineering's list and joins
  experience-design's.
- Versions — product-engineering 2.0.0 and experience-design 4.2.0, in `pack.toml`
  and `.claude-plugin/plugin.json`.
- Pack pages — product-engineering's README, JOURNEY, DESIGN, and site page drop
  the skill. Experience-design's README, JOURNEY (a stage after "Design each
  screen"), DESIGN (its "why it lives here" rationale), and site page add it.
- Callers that name its old home or call it cross-pack — experience-design's `content-design`,
  `user-flow`, and `design-review` skill files. Also product-engineering's two
  `agentbundle-layout.md` references and its `align-value-stream` eval,
  product-strategy's DESIGN, and the guides of both packs.
- The how-to `write-product-microcopy.md` — from `guides/product-engineering/how-to/`
  to `guides/experience-design/how-to/`.
- The skill census fixture — its `ux-writing` row names `experience-design`.
- Release notes — a product-engineering 2.0.0 fragment and an experience-design
  4.2.0 fragment under `docs/product/changelog.d/`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Guides tell adopters which pack gives them `ux-writing` | `guides/experience-design/`, `guides/product-engineering/README.md` | eugenelim | Moved and edited guides | AC-0009, AC-0012, AC-0018, AC-0019, AC-0020 pass |
| Current product truth | Pack pages state each pack's skill roster | `packs/{product-engineering,experience-design}/{README,JOURNEY,DESIGN}.md`, `web/src/content/packs/` | eugenelim | Edited pages, regenerated journeys | AC-0010, AC-0017, AC-0018 pass |
| Interface compatibility | Removing a skill from a published pack breaks adopters who name the pack | Pack versions | eugenelim | `pack.toml` and `plugin.json` versions | AC-0007 passes |
| Release history | Adopters need the upgrade step | `docs/product/changelog.d/` | eugenelim | Two fragments | AC-0013, AC-0014 pass |
| Operations | The upgrade step is only as good as its observation | `notes/verification-ledger.md` | eugenelim | Recorded install-then-upgrade runs | AC-0015 passes |
| Decision rationale | Covered upstream | RFC-0107 D6 | — | none owed | none — the RFC already records the move |

## Agent Rules

### Always do

- Move the skill directory with `git mv`, so history follows each file.
- Retarget references only on the operative surfaces: `packs/`, `guides/`,
  `web/src/`, `tools/`, and `docs/architecture/`. Frozen records stay as written:
  ADRs, RFCs, other specs, findings, research, and `docs/design/`.
- Outside the operative surfaces, write only the changelog fragments under
  `docs/product/changelog.d/`, the self-host projections, the brief's status and
  Spec map row, and this spec's own folder.
- Write each changelog entry with `tools/changelog.py new` and edit the created
  fragment, never `changelog.md`.
- Run `agentbundle catalogue self-host --root . --write` after the last `.apm/`
  edit, and edit no adapter projection or generated journey by hand.

### Ask first

- Changing the `ux-writing` name or description. A change owes an activation run.
- Changing where the skill writes the voice chart, or how it resolves `[design]`.
- Changing `agentbundle`'s upgrade or ownership behaviour.

### Never do

- Leave a copy, alias, or stub of `ux-writing` in product-engineering.
- Add a dependency, a module, a pack, or a top-level directory.
- Cite this repository's governance records (RFCs, ADRs, specs, criteria) in
  shipped content under `packs/`.

## Testing Strategy

- **Location, bytes, and manifests (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008): goal-based.** A file
  listing, `git diff --find-renames`, and a `pack.toml` parse each decide one
  criterion.
- **Caller retargeting (AC-0009, AC-0010, AC-0011, AC-0012, AC-0017, AC-0018, AC-0019, AC-0020): goal-based.**
  `git grep` over tracked files (it includes the hidden `.apm/` directories), the
  existing site-parity, journey, and census checks, and the rendered-site link
  check.
- **Release notes (AC-0013, AC-0014): goal-based.** A read of the two fragments for
  their named sections and text, plus the changelog fragment validator.
- **Upgrade path (AC-0015): manual QA.** The step only counts if a real
  `agentbundle` run against the real change shows it. Three starting states are
  walked in scratch repositories, and the state file and installed bytes are
  recorded.
- **Catalogue integrity (AC-0016): goal-based.** `catalogue lint --deep` and
  `catalogue verify` after self-host.
- **No activation run.** Activation reads only the listed name and description,
  and both are byte-identical (AC-0003). For an adopter with both packs the listing
  is unchanged. For an adopter with one pack, the listing gains or loses one whole
  entry, and no other skill's text moves.

## Acceptance Criteria

- [x] **AC-0001.** `packs/experience-design/.apm/skills/ux-writing/` holds exactly
  `SKILL.md`, `assets/voice-chart-template.md`, `evals/eval_queries.json`,
  `evals/evals.json`, and `references/{content-checklist,human-craft-check,microcopy-formulas,voice-axes}.md`.
- [x] **AC-0002.** `packs/product-engineering/.apm/skills/ux-writing/` does not exist.
- [x] **AC-0003.** The `name` and `description` frontmatter values of the moved
  `SKILL.md` are byte-identical to those at `3216c5b40`.
- [x] **AC-0004.** Each moved file other than `SKILL.md` is byte-identical to its
  source at `3216c5b40` (a 100% rename in `git diff --find-renames=100%`).
- [x] **AC-0005.** With every run of whitespace folded to one space, the moved
  `SKILL.md` contains none of `product-engineering`,
  `frames, de-risks, and decomposes`, `` `experience-design` pack ``,
  `(experience-design pack)`, or `` `experience-design`'s ``.
- [x] **AC-0006.** The moved `SKILL.md` still contains `docs/product/voice/<slug>.md`
  and `` `[design] output_dir` ``.
- [x] **AC-0007.** `version` is `2.0.0` in product-engineering's `pack.toml` and
  `.claude-plugin/plugin.json`, and `4.2.0` in experience-design's.
- [x] **AC-0008.** `[pack.evals].skills` contains `ux-writing` for experience-design
  and not for product-engineering, and every skill either list names has a directory
  with `evals/eval_queries.json`.
- [x] **AC-0009.** No tracked line under `packs/`, `guides/`, `web/src/`, `tools/`,
  or `docs/architecture/` contains both `ux-writing` and a case-insensitive match of
  `product.engineering`.
- [x] **AC-0010.** In product-engineering's `README.md`, `JOURNEY.md`, `DESIGN.md`,
  and `pack.toml`, and in `web/src/content/packs/product-engineering.md`, the only
  line containing `ux-writing` is the `README.md` line naming the `docs/product/voice/`
  folder.
- [x] **AC-0017.** experience-design's `README.md`, `JOURNEY.md`, and
  `web/src/content/packs/experience-design.md` each list `ux-writing` as a skill,
  and `tools/lint-site-scope-parity.py`, `tools/lint-pack-journeys.py`, and
  `tools/lint-web-journey-parity.py` exit 0.
- [x] **AC-0018.** None of these strings is present in its file:
  `cross-pack` in `packs/experience-design/.apm/skills/design-review/references/quality-floor.md`,
  `different pack` in `guides/experience-design/how-to/copy-boundary.md`,
  `cross-pack boundary`, `skill in another pack`, and `crosses packs` in
  `packs/experience-design/DESIGN.md`, `crosses packs` in
  `guides/experience-design/README.md`, `thirteen` in
  `packs/product-engineering/pack.toml` and `guides/product-engineering/README.md`,
  and `thirteenth` in `web/src/content/packs/experience-design.md`.
- [x] **AC-0011.** The skill census fixture's `ux-writing` row names
  `experience-design`, and the census suite passes.
- [x] **AC-0012.** `guides/experience-design/how-to/write-product-microcopy.md`
  exists, `guides/product-engineering/how-to/write-product-microcopy.md` does not,
  and no file under `guides/` or `web/src/` links to the old path.
- [x] **AC-0019.** The moved how-to's frontmatter has `pack: experience-design`, and
  each of its lines that tells the reader to install a pack names
  `experience-design` and no other pack.
- [x] **AC-0020.** After `make bootstrap-sites`, `make site-link-check` exits 0, so
  no link on the rendered site, including the moved how-to's page, is broken.
- [x] **AC-0013.** The product-engineering 2.0.0 fragment has a `## Removed` section
  naming `ux-writing` and `experience-design`. It tells every adopter, after
  upgrading, to run `agentbundle uninstall --pack product-engineering` and then
  `agentbundle install --pack product-engineering` at the same scope. It tells an
  adopter with both packs that the two upgrades may run in either order, and one
  without experience-design to install it after that step to keep `ux-writing`.
- [x] **AC-0014.** The experience-design 4.2.0 fragment has an `## Added` section
  naming `ux-writing`. It tells a product-engineering adopter without
  experience-design to run the AC-0013 step before
  `agentbundle install --pack experience-design`, and an adopter with both packs
  that the two upgrades may run in either order. Both fragments pass
  `tools/changelog.py`'s fragment validation.
- [x] **AC-0015.** The verification ledger records three runs of the AC-0013 step
  against this change, in scratch repositories installed from `3216c5b40`:
  - both packs, product-engineering upgraded first;
  - both packs, experience-design upgraded first;
  - product-engineering alone, then experience-design installed after the step.

  Each run ends with exactly one state row claiming
  `.claude/skills/ux-writing/SKILL.md`, at experience-design 4.2.0, and the
  installed file equals the experience-design source.
- [x] **AC-0016.** After self-host, `agentbundle catalogue lint --root . --deep` and
  `agentbundle catalogue verify --root .` exit 0.

## Follow-ons

none

## Assumptions

none
