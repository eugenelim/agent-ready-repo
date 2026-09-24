# Spec: One genre-aware information-architecture skill

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0066 D4 and D5(d) (amended by erratum in this change); RFC-0055 D2 (errata structure); RFC-0050; RFC-0033 / ADR-0024 (framework agnosticism); ADR-0038 (alias-free precedent)
- **Brief:** `brief:experience-design-skill-consolidation`
- **Discovery:** [`experience-design-consolidation-analysis.md`](../../product/research/experience-design-consolidation-analysis.md)
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

## Outcome

A designer reaching for information architecture finds one skill that routes by
surface genre, instead of choosing between seven registrations that occupy one
step. Every genre the taxonomy defines is reachable — including the two that no
downstream caller can reach today — and each genre's method is unchanged.

## What Changes

- Six genre skills fold into `information-architecture`, one reference each.
- `information-architecture/SKILL.md`'s existing seven-row genre table stops
  pointing at sibling skills and points at its own references, keeping its
  `transactional-journey → interaction-design` row.
- The surviving `description` absorbs the folded skills' trigger vocabulary.
- `frontend-engineering`'s genre-routing table names one XD skill plus a genre,
  and its pack-availability sentinel stops naming a deleted skill.
- `pack.evals`, the census fixture, the guide tree, `DESIGN.md`, `JOURNEY.md`,
  `README.md`, `docs/index.md` and the Astro content drop the removed names and
  their counts.
- RFC-0066 gains an erratum; the pack takes a major bump.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | Applicable — seven registrations become one | `packs/experience-design/.apm/skills/information-architecture/` | This spec | One `SKILL.md` with a genre-selection rubric and six genre references | Pack lint and the roster suites are clean |
| Interface compatibility | Applicable — a removal | `packs/experience-design/pack.toml`, `.claude-plugin/plugin.json`, regenerated `.claude-plugin/marketplace.json` | `packs/AGENTS.md` § Version bump rule | Matching **major** bump in both source manifests | All three read `3.0.0` |
| Cross-pack contract | Applicable — `frontend-engineering` names the folded skills and probes for one | `packs/frontend-engineering/` | This spec | Genre table restated for all seven rows; sentinel and named-skip text updated; a minimum `experience-design` version floor declared | `frontend-engineering`'s own gates pass |
| Decision rationale | Applicable — an Accepted RFC's decision no longer holds | `docs/rfc/0066-…md` § Errata and `packs/experience-design/DESIGN.md` | RFC-0055 D2 | An approver-signed erratum in the two-layer form; DESIGN.md consistent throughout | The erratum stands alone without naming a spec |
| User promise | Applicable — the skill a reader invokes changes | `guides/experience-design/` | `author-product-docs` | Guide text routing by genre through one skill | Guide-agreement test passes and a named reviewer judges the guide sufficient |
| Public site truth | Applicable — the pack's published journey and pack pages name each skill | `web/src/content/` | This spec | Frontmatter `skills:` list, `whatChanges`, and stage prose updated | The site build succeeds |
| Release history | Applicable — a released artifact's version is bumped | `docs/product/changelog.md` | That file's own header rules | A free-standing `## [experience-design][3.0.0] — <date>` entry directly beneath `[Unreleased]`, naming the removed skills and the adopter action | The entry sits at the right heading level with single blank lines around every heading |
| Reusable learning | Applicable — activation behaviour is the thing at risk | `information-architecture/evals/` | `packs/AGENTS.md` § Security and authoring rules | Pooled trigger queries plus a recorded before/after Tier-A result | `notes/activation-baseline.md` carries both runs |

## Agent Rules

### Always do

- Run the Tier-A activation baseline **before** deleting any skill directory,
  and record it. The single objection that can defeat this fold is that one
  description activates less reliably than seven.
- Carry every genre's method across in substance. A genre reference may be
  reformatted and de-duplicated against the shared body, but no genre-specific
  rule, grounding citation, or scope boundary is dropped.
- Preserve the `transactional-journey → interaction-design` route. It is
  RFC-0066 D5(d) and this delivery does not touch it.
- Pool every folded skill's `eval_queries.json` positive cases into the
  surviving skill's file.
- Update `frontend-engineering`'s genre table, its pack-availability sentinel,
  its named-skip text, and `guides/frontend-engineering/` in the same PR.
- Update `packs/agent-skill-engineering/tests/fixtures/skill-census.json`.
- Bump `pack.toml` and `.claude-plugin/plugin.json` together, in the same edit.

### Ask first

- Renaming the surviving skill. This spec keeps `information-architecture`,
  because `frontend-engineering` and the guide tree already know that name and
  ADR-0038 forbids aliases, so a rename multiplies the sweep.
- Folding `interaction-design`. It is sequential to IA, not a genre of it.
- Changing the `surface-genre:` taxonomy. RFC-0066 D2's seven types are
  untouched; only what each row points at changes.
- Passing `FORCE=1` to `make build-self`, per the standing conflict between
  `packs/AGENTS.local.md` and root `AGENTS.local.md`.

### Never do

- Rewrite a **frozen** record. The test is lifecycle class, not directory: a
  shipped spec, an Accepted RFC, and a closed ADR record what was true when
  written and are amended only by erratum. A **live** record is updated — that
  includes `docs/product/journeys/designer-designs-surface.md`, which RFC-0066's
  own follow-on designates the single source of truth for the design chain, the
  `docs/design/` artifact corpus, and any lifecycle record still open.
- Ship an alias or a deprecation shim for a removed skill name (ADR-0038).
- Name a spec or a delivery brief inside an RFC erratum. Those are
  delivery-time artifacts that get archived and pruned; the RFC is the durable
  record and must stand alone.
- Reduce a genre's method to a summary. The fold removes registrations, not
  content.
- Inline all six genres into the surviving `SKILL.md`. Genre method loads on
  selection, or the fold has traded a resident-index cost for a larger
  resident-body cost.
- Write a colour literal, a unit-bearing dimension or duration literal, a
  contrast or scale ratio, a named easing curve, an ARIA role, CSS syntax, a
  UI-framework name, or a concrete typeface name into any file under
  `packs/experience-design/`.

## Testing Strategy

- **Goal-based check** — a directory is absent, a reference exists, a named
  string is present or absent in a named file, a numeral matches a count, a
  version reads, a gate exits 0. `plan.md` names the command for each.
- **Measured experiment** — the Tier-A activation comparison. Its statistic,
  run count, tolerance, and abort path are acceptance criteria below, not
  conventions. Both runs are recorded in `notes/activation-baseline.md`.
- **Manual QA** — three judgements: whether each genre reference preserves its
  source method; whether the genre-selection rubric is decidable from the brief's
  `surface-genre:` field alone; whether the guide is sufficient. Recorded in
  `notes/verification-ledger.md` with the reviewer's name and date.
- **No TDD.** No compressible invariant and no new Python surface.

## Acceptance Criteria

### The surviving skill

- [ ] `information-architecture/SKILL.md` carries a genre-selection rubric
      mapping each of the seven `surface-genre:` values to exactly one of three
      outcomes: a genre reference in this skill, another skill named explicitly,
      or the general IA path. *(goal-based)*
- [ ] The row `transactional-journey → interaction-design` survives as a
      route-to-another-skill outcome. *(goal-based)*
- [ ] No `surface-genre:` value is unrouted. Failing state: a value in RFC-0066
      D2's taxonomy with no row in the rubric. *(goal-based)*
- [ ] Six genre references exist under `references/`, one per folded skill.
      *(goal-based)*
- [ ] `conversion-design/references/editorial-quality-gates.md` lands
      byte-identical at `information-architecture/references/editorial-quality-gates.md`.
      It is a shared editorial file rather than genre method, so the
      method-preservation criteria do not reach it, and the sibling copy fold
      depends on it existing there. Dropping it on the floor is the failure this
      criterion prevents. The copy travels unchanged, including its
      "Skill autonomy beats DRY at this scale" note, which the sibling copy fold
      removes when it reconciles the pair — this slice knowingly moves a note
      about to be superseded rather than editing a file it only relocates.
      *(goal-based)*
- [ ] `information-architecture/SKILL.md` cites
      `references/editorial-quality-gates.md`. The `containment.md` precedent the
      sibling fold invokes derives its copy set from citation — its roster suite
      asserts that the set of skills citing the module equals the set shipping
      it — so a shipped copy nothing cites fails that suite rather than
      satisfying it. *(goal-based)*
- [ ] `SKILL.md`'s authored body — file bytes minus frontmatter and minus the
      **every managed directive** — the `agentbundle:output-rendering` markers
      and their contents, plus the per-skill directive lines
      `tools/add-rendering-directives.py` emits outside them — is at most
      **8,000 bytes**. The pre-fold figure is 7,194 bytes by that definition and
      `plan.md` names the command. Excluding only the marker block would count
      roughly 200 bytes of generated directive as authored body, which moves
      with that tool's map rather than with an author edit. The rubric rewrite
      replaces a table of comparable size, so the allowance is ~8%.
      Failing state: a genre's method was pasted in rather than referenced.
      *(goal-based)*
- [ ] Each genre reference carries its source skill's method, grounding
      citations, and scope boundaries. *(manual QA)*
- [ ] The rubric is decidable from the brief's `surface-genre:` field alone.
      *(manual QA)*

### The surviving description

- [ ] The `description` is at most 1024 characters. *(goal-based)*
- [ ] It names trigger vocabulary for all seven genres, so a request phrased in
      any genre's own words can match. *(goal-based)*
- [ ] It retains boundary statements against `interaction-design`,
      `design-system`, `design-review`, and `creative-direction`. *(goal-based)*

### Activation evidence

- [ ] `notes/activation-baseline.md` records a Tier-A run over the seven skills
      **before** the fold, naming the command, the date, the CLI version, and the
      model identifier. *(measured experiment)*
- [ ] It records a Tier-A run over the surviving skill **after** the fold,
      against the pooled query set, under the same command, CLI version, and
      model identifier. *(measured experiment)*
- [ ] The pass statistic is **total passing queries over total queries**,
      computed identically on both sides over the same pooled query set. A
      mean-of-per-skill-rates figure is not the gate, because it diverges from
      the pooled figure whenever per-skill query counts differ. *(measured experiment)*
- [ ] Each run is repeated **three times** and the reported figure is the lowest
      of the three, because Tier-A grades on a sampled trigger rate.
      *(measured experiment)*
- [ ] The fold ships only when the post-fold positive-set figure is **greater
      than or equal to** the baseline figure. *(measured experiment)*
- [ ] The fold ships only when the post-fold **negative** set — queries that must
      not trigger, including at least one belonging to `interaction-design` and
      one to `design-system` — passes at a figure greater than or equal to its
      baseline. Recall alone is not the gate: over-triggering is the expected
      failure mode of one broad description. *(measured experiment)*
- [ ] `information-architecture/evals/eval_queries.json` carries the positive
      queries pooled from all seven skills and that negative set.
      *(goal-based — a document-content check, tagged as the sibling tags its twin.)*
- [ ] `notes/activation-baseline.md` names the **abort path** and its two
      triggers: a failing activation gate, **or** the ~3-week window in the
      brief's appetite elapsing without the fold landing. Either trigger leaves
      the same residue — the six directories are not deleted, and the non-fold
      half of the change ships on its own: the `frontend-engineering` table
      repair, its `design-system-foundations` slug correction, and that pack's
      version bump, without the erratum or the `experience-design` major.
      *(measured experiment)*
- [ ] The abort decision names **eugenelim** as the deciding owner. Deferring to
      "the owner named in the brief" resolves to nobody while the brief's own
      Ready gaps record that `ini-003` is owner by initiative fit rather than by
      assignment. *(measured experiment)*

### The removals

- [ ] These six directories are absent: `analytical-design`,
      `conversion-design`, `documentation-design`, `informational-design`,
      `marketplace-design`, `workspace-design`. *(goal-based)*
- [ ] `pack.toml` `[pack.evals].skills` lists fourteen skills and none of the six
      removed names. *(goal-based)*
- [ ] No file under `packs/`, `guides/`, `web/`, `tools/`, or `tests/` names a
      removed skill, and no **live product-truth** record under `docs/` does.
      Four surfaces legitimately keep the names and are exempt by name: the
      RFC-0066 erratum, `docs/product/changelog.md` (whose own AC below requires
      them), `docs/product/briefs/experience-design-skill-consolidation.md`, and
      `docs/specs/xd-copy-router/spec.md`. Two further classes are exempt as
      **dated outputs** — produced artifacts under `docs/design/`, and
      `docs/product/research/experience-design-consolidation-analysis.md` —
      because each records what was measured on a date. Frozen records are out
      of scope by the lifecycle rule above. *(goal-based)*
- [ ] Every **open** lifecycle record under `docs/` naming a removed skill is
      updated, starting with `docs/product/intents/skill-sequence-wayfinding.md`
      (Status: Draft, naming five of the six). The enumeration comes from
      grepping `docs/` for the six names and classifying each hit as frozen,
      dated output, or open. *(goal-based)*
- [ ] No alias, shim, or deprecation stub is shipped. *(goal-based)*
- [ ] Every skill-count numeral for this pack reads **14**, in the three files
      that carry one: `packs/experience-design/docs/index.md`,
      `guides/experience-design/reference/experience-design.md`, and
      `web/src/content/packs/experience-design.md`. The check covers word forms
      as well as digits. `README.md` and `JOURNEY.md` carry no numeral and owe
      only that their enumerated lists name no removed skill, which the sweep
      covers. `web/src/content/packs/experience-design.md:69` reads
      "is an agent, not a twenty-first skill" and becomes "a fifteenth skill".
      *(goal-based)*
- [ ] The pre-fold resident description cost is **re-measured at this spec's
      branch point** and recorded alongside the post-fold figure and their delta,
      using the computation the discovery note names. The 14,966-byte figure was
      taken at `2.0.9`, before `creative-direction-modes` rewrote a description,
      so crediting this fold against it would claim another slice's change.
      *(goal-based)*

### Adopter removal hygiene

- [ ] `notes/verification-ledger.md` records the observed behaviour of
      `agentbundle` install and update against a fixture install that already
      carries the six skills: whether a directory the pack no longer declares is
      pruned or left resident. *(goal-based)*
- [ ] If it is not pruned, the changelog entry states the manual step an adopter
      must take, because a stale `SKILL.md` stays in their skill index and keeps
      activating against a method the pack no longer ships. *(goal-based)*

### The cross-pack contract

- [ ] `frontend-engineering`'s genre-routing table reaches a stated post-state
      for every one of its seven current rows. Four of those rows name folded
      genre skills and collapse into a single row whose **Load cell holds the
      bare slug** `` `information-architecture` `` and whose Surface-type cell
      enumerates all six genres. The genre argument goes in the Surface-type
      cell, never the Load cell: `genre_routing_table()` in
      `packs/frontend-engineering/tests/skills/frontend-engineering/test_public_claims_match_shipped_behaviour.py`
      takes the Load cell verbatim as the routable name, so
      `` `information-architecture <genre>` `` would make every README shape
      fail its cross-check. The
      `interaction-design`, `content-design`, and `design-system-foundations`
      rows are not folded and survive, the last under its corrected name. The
      resulting table is four rows, and the spec states that shape rather than
      leaving it to be inferred. *(goal-based)*
- [ ] All six genres route through that single row, closing the
      `marketplace-design` and `workspace-design` gap; `transactional-journey`
      continues to reach `interaction-design`. *(goal-based)*
- [ ] The stale slug `design-system-foundations` is corrected to
      `design-system` — the real skill directory, and the name RFC-0066 D7 gave
      it — in exactly three places: that routing table,
      `packs/frontend-engineering/README.md`'s route list, and
      `packs/frontend-engineering/tests/skills/frontend-engineering/test_public_claims_match_shipped_behaviour.py`.
      The test cross-checks the README's route list against the table and names
      the stale slug in its own docstring as routable, so correcting the table
      alone reds it. *(goal-based)*
- [ ] The four byte-identical copies of `digital-experience-contract.md`, which
      carry the same stale slug at line 167, are **not** touched. They are pinned
      to one hash across `experience-design`, `product-strategy`,
      `product-engineering` and `frontend-engineering`, so correcting them means
      editing four packs and bumping all four. That is a separate change with its
      own owner, and silently absorbing it here would quadruple this slice's
      blast radius. *(goal-based)*
- [ ] The pack-availability sentinel no longer probes for `conversion-design`. A
      probe naming a deleted skill inverts: a stale install passes it and a fresh
      install fails it. *(goal-based)*
- [ ] `frontend-engineering` declares a minimum `experience-design` version via
      `[[pack.dependencies.recommended]]`, as **documentation of the floor**.
      `required` is not used: it is a hard install gate that would convert the
      documented optional co-install into a mandatory one and kill the
      named-skip path this spec preserves. No detection is claimed —
      `install.py` gates only on `dependencies.required`, and `recommended` is
      read by `catalogue verify` structurally and by nothing at install or
      runtime. The declaration records the constraint for a human; it does not
      enforce it. *(goal-based)*
- [ ] The named-skip text recorded when `experience-design` is absent matches the
      skill actually looked for. *(goal-based)*
- [ ] `packs/frontend-engineering/README.md`'s genre-route list names exactly
      the surviving routing targets. It offers four removed skills today, and the
      suite above cross-checks it against the table. *(goal-based)*
- [ ] `guides/frontend-engineering/how-to/read-the-design-handoff.md` and
      `web/src/content/packs/frontend-engineering.md` contain no removed skill
      name and name the same routing target as the table. *(goal-based)*

### Governance records

- [ ] `docs/rfc/0066-…md` § Errata carries a dated, approver-signed entry naming
      **D4**, stating that the six separate registrations are retired, that the
      genre method is preserved as references under `information-architecture`,
      and that D2's seven-type taxonomy and D5(d)'s `transactional-journey` route
      are unchanged. *(goal-based)*
- [ ] That entry names no spec and no delivery brief, and reads completely for
      someone holding only the RFC. *(goal-based)*
- [ ] The Errata section conforms to RFC-0055 D2's two-layer
      `### Current state` / `### History` structure. Both of its trigger
      conditions fire here: the section holds more than one entry, and this entry
      supersedes a decision. *(goal-based)*
- [ ] `packs/experience-design/DESIGN.md` names no removed skill slug anywhere in
      the file. *(goal-based)*
- [ ] `DESIGN.md` describes one genre-aware IA skill at every point it describes
      the genre step. A slug check cannot settle this: line 41 ("or genre-direct
      skill"), line 61 ("and the genre-direct skills"), line 179
      ("**Information-architecture / genre-direct skills**") and line 249
      ("craft/genre skills") carry no slug, and lines 187–198 assert six skills
      run in place of the IA step — all of which pass a slug check unchanged
      while still describing the old shape. Those five locations are the checked
      set. Line 75 is **not** among them: it names only
      `information-architecture` and `interaction-design`. *(goal-based)*
- [ ] `DESIGN.md` § 10's entry *"Why six genre-direct skills instead of one
      general IA skill with genre flags (from v1)"* records both what was
      rejected — a `genre:`-parameterised skill, on the grounds that it would bury
      the genre logic in a conditional tree — and what now ships, with the
      approver named and dated. It does not assert that the earlier rejection
      fails to apply. *(goal-based)*
- [ ] This delivery is § 10's **only** editor. `creative-direction-modes`
      carries a criterion forbidding itself to touch § 10, so there is no
      interim wording to supersede and a supersession clause here would
      reference text nobody installs. *(goal-based)*

### Queued shaping records this fold invalidates

- [ ] `docs/product/intents/xd-ia-archetypes-objects.md`'s `### Observed state`
      table is re-measured and re-dated. Its row citing
      `information-architecture/SKILL.md:69-77` names the genre table this fold
      rewrites, and its row citing
      `frontend-engineering/.apm/skills/frontend-engineering/SKILL.md:357-374`
      names a range below the table this fold edits, so both line ranges move.
      *(goal-based)*
- [ ] That table's verdict is corrected for what the fold leaves behind. It
      currently reads "no file of that name anywhere" for
      `references/page-archetypes.md` and calls the nearest structure "not
      archetype-shaped"; after the fold, `information-architecture/references/`
      holds six genre files, which moves M3c's starting position rather than
      leaving it unchanged. A stale baseline here risks duplicating the reference
      structure this fold just built. *(goal-based)*
- [ ] `docs/product/intents/xd-state-reviewer-doctrine.md` is checked against the
      `experience-reviewer` edits the sibling copy fold makes, and updated or
      confirmed unaffected in that spec rather than this one. *(goal-based)*

### Live records and the public site

- [ ] `docs/product/journeys/designer-designs-surface.md` describes the surviving
      skill set. It carries `status: shipped` and is designated the single source
      of truth for the design chain, so leaving it naming six deleted skills is a
      defect, not history. *(goal-based)*
- [ ] `web/src/content/journeys/experience-design.md`'s `skills:` frontmatter
      list, its `whatChanges` value, and its per-stage prose name the surviving
      skill. *(goal-based)*
- [ ] The `web/` Astro build succeeds, which is what validates the `skills:`
      frontmatter list against its collection schema. The five
      `guides/AGENTS.md` commands end at `tools/build-site.py`, which builds the
      docs site and does not read `web/src/content/`. *(goal-based)*

### Gates

- [ ] `python3 tools/lint-experience-agnostic.py` exits 0. *(goal-based)*
- [ ] All five `tests/roster/test_experience_*` suites and
      `test_design_handoff_contract_matches_corpus.py` pass. *(goal-based)*
- [ ] `agentbundle catalogue lint --root . --deep` and
      `agentbundle catalogue verify --root .` each exit 0 after the projection is
      regenerated. *(goal-based)*
- [ ] The five commands in `guides/AGENTS.md` § Essential commands each exit 0.
      *(goal-based)*
- [ ] `make lint-ruff lint-mypy` exits 0. *(goal-based)*
- [ ] `python3 -m pytest packs/frontend-engineering/tests -q` passes. That pack's
      own suite reads both the routing table and the README route list, so this
      delivery can red it without any `experience-design` gate noticing.
      *(goal-based)*
- [ ] `notes/verification-ledger.md` records all three manual-QA verdicts with
      the reviewer's name and date. *(goal-based)*

### Release

- [ ] `pack.toml` and `.claude-plugin/plugin.json` both read `3.0.0` — a
      **major** bump, because removals are major under `packs/AGENTS.md`.
      *(goal-based)*
- [ ] `.claude-plugin/marketplace.json` reads `3.0.0` for `experience-design`,
      regenerated by self-host rather than hand-edited. *(goal-based)*
- [ ] `docs/product/changelog.md` carries a free-standing
      `## [experience-design][3.0.0] — <YYYY-MM-DD>` entry directly beneath
      `[Unreleased]`, naming the six removed skills explicitly so an adopter
      reading only the changelog learns which names disappeared. *(goal-based)*
- [ ] `packs/frontend-engineering/pack.toml` and its
      `.claude-plugin/plugin.json` carry a **patch** bump from `0.3.2` to `0.3.3`, and its marketplace entry is
      regenerated. Patch, not major: this edits that pack's content and removes
      no primitive. This delivery edits that pack's
      `SKILL.md`, `AGENTS.md`, and `README.md` — non-cosmetic pack content, which
      `packs/AGENTS.md` § Version bump rule obliges a bump for. *(goal-based)*
- [ ] `docs/product/changelog.md` carries a matching free-standing entry for
      `frontend-engineering` at its new version. *(goal-based)*

### Documentation

- [ ] `guides/experience-design/` routes the reader by genre through one skill,
      and its `**Where it lands:**` paths agree with the surviving `SKILL.md`.
      *(manual QA)*

## Follow-ons

- Repository maintainer: the copy-layer fold is the sibling spec
  [`xd-copy-router`](../xd-copy-router/spec.md), sequenced after this one.
- Repository maintainer: nothing tests routing-table completeness between packs.
  This fold removes today's instance; a test would prevent the next.
- Repository maintainer: `agentbundle-layout.md` exists in twelve copies in nine
  versions pack-wide. `digital-experience-doctrine-completion` routes that S8a
  family **out** of itself to an intake candidate named
  `experience-design-reference-reconciliation`, which has no admitted intent yet,
  so the family is currently unowned rather than owned elsewhere.
- Product owner: the design artifacts improvise their own linking vocabulary. A
  composition contract for design artifacts is larger than any fold.

## Assumptions

- Technical: `information-architecture/SKILL.md` step 1 already carries a
  seven-row genre routing table keyed on `surface-genre:`, so this delivery
  migrates an existing mechanism rather than introducing one (source:
  `packs/experience-design/.apm/skills/information-architecture/SKILL.md:61-79`).
- Technical: `DESIGN.md` § 5 states the six genre skills replace the
  `information-architecture` step only.
- Technical: `frontend-engineering`'s table names four of six genre skills; the
  omission of `marketplace-design` and `workspace-design` is verified by grep and
  covered by no test.
- Technical: Tier-A activation grading runs via the headless detector and needs
  the `claude` CLI on PATH, so CI cannot re-check the figure and the abort path
  above is the only backstop.
- Process: removals are a major bump.
- Technical — **the slug correction targets shipped truth, not the newest
  decision.** RFC-0071 D3b (Accepted) authorises `design-system-foundations` as
  a *new* skill and renames `design-system` → `design-token-taxonomy`. Neither
  shipped: the tree holds `design-system` and no `design-token-taxonomy`, which
  `tools/test-all.py` already records. Correcting the table to `design-system`
  therefore matches what exists while leaving D3b unimplemented. Reconciling D3b
  is routed to the RFC-0071 erratum the sibling copy fold owns; this delivery
  records the conflict rather than resolving it.
- Technical — **knowingly stale for one slice.** RFC-0071 carries "20 skills" in
  operative text at lines 70 and 484, the second itself an erratum correction.
  This fold makes that 14, but RFC-0071's erratum is assigned to the sibling copy
  fold, which lands second. The RFC is therefore wrong on the count between the
  two slices. That is accepted rather than fixed here: splitting one RFC's
  erratum across two slices would leave two partial entries in a section
  RFC-0055 D2 requires to read as one current state. If the copy fold aborts,
  this slice's owner files the count erratum rather than leaving an Accepted RFC
  wrong with no owner. The claim is narrow: lines 70 and 484 describe RFC-0071's
  own delivery scope at its time, not a standing inventory.
- Process — **recorded dissent.** An independent review held that erratum is the
  wrong instrument here: RFC-0066's 2026-07-27 precedent discharged a
  *procedural* obligation for a rename whose substance D7 already authorised,
  whereas retiring six registrations originates a new decision, and guidance
  elsewhere draws the line at "a fresh RFC if the delta is genuinely new
  decisions." The owner decided erratum on 2026-09-24 and the decision stands.
  The Outcome's migration framing narrows the gap — the routing mechanism is
  already shipped and only its targets move — but it does not dissolve the
  objection, and it is recorded here rather than resolved.
- Sequencing: this spec lands after `creative-direction-modes` and before
  `xd-copy-router`. All three edit `DESIGN.md`, `pack.toml`,
  `.claude-plugin/plugin.json` and the changelog, and each carries a version
  bump, so they cannot run in parallel.
