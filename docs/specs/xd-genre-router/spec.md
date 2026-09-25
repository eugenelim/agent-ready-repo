# Spec: One genre-aware information-architecture skill

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
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
  version reads, a gate exits 0. Coverage is stated as a **rule**, not as a
  list or a count, so a criterion added later is classified without editing a
  tally: **a goal-based criterion whose subject is any of the six kinds this
  bullet opens with — a directory's absence, a file's existence, a named
  string's presence or absence in a named file, a numeral matching a count, a
  version reading, or a gate's exit status, plus a file's byte count — is
  settled by a command in `plan.md`'s Verification command map; a goal-based criterion whose subject is a prose
  post-state — what a passage now says, what a record now describes, what an
  install was observed to do — is settled by its owning task's `Tests:`, and
  that task is named in the criterion or in the durable-output map.** Both
  routes are mechanical and both can fail; neither is a judgement. Worked
  examples of the second route: the pre-fold resident-description re-measure
  (T1), the six `DESIGN.md` location checks and the § 10 rationale entry (T5),
  the sentinel, the `recommended` floor and the named-skip text (T6), the three
  queued-shaping-record updates T7 owns — the third routes to `xd-copy-router`
  explicitly — the governance-records block (T8), and
  the adopter install/update prune observation (T11). Two earlier drafts stated
  this as coverage counts — first "a command for each", then "four criteria" —
  and both were false in the same direction, the second also contradicting
  itself within two clauses. A false claim of coverage is worse than a stated
  split: a closeout reviewer who finds no command substitutes a judgement,
  which is what the measured framing exists to prevent.
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
      "Skill autonomy beats DRY at this scale" note. The reconciliation the
      sibling copy fold owns is **three-way, not a pair**: the tree holds three
      copies at three distinct hashes — under `tone-of-voice`,
      `conversion-design`, and `copy-direction` — and `xd-copy-router` records
      that the `conversion-design` copy this slice relocates carries a
      substantively **weaker** gating clause than `copy-direction`'s. This slice
      therefore relocates bytes and asserts nothing about which variant
      survives; reading the relocated copy as the presumptive survivor is the
      rule loss `xd-copy-router` forbids. *(goal-based)*
- [ ] `information-architecture/SKILL.md` cites
      `references/editorial-quality-gates.md`. The `containment.md` precedent the
      sibling fold invokes derives its copy set from citation: the roster suite
      for **`containment.md`** asserts that the set of skills citing that module
      equals the set shipping it. That is the **argument** for this criterion,
      not a suite that would red here —
      `test_experience_design_write_declaration_and_containment.py` hard-codes
      `MODULE_REFERENCE = "references/containment.md"`, and no suite anywhere
      reads `editorial-quality-gates.md`. The criterion is gated by the
      `grep -q` in `plan.md`, which decides it. Stating the precedent as
      existing coverage would be exactly the false-coverage claim this spec
      elsewhere refuses. *(goal-based)*
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
- [ ] **"Passing" is defined for both worlds, in terms T9 can reproduce
      unchanged.** Post-fold every pooled positive has one expected skill and
      every negative must not reach it — but pre-fold the same positives belong
      to seven different skills, and a negative must miss all seven. The
      baseline is therefore graded as: a **positive** passes when the query
      activates **any one** of the seven in-scope skills; a **negative** passes
      when it activates **none** of the seven. Post-fold the same sentences read
      with "the seven" replaced by "the surviving skill", which is what makes
      the two figures comparable — both ask whether the query reached this
      pack's IA surface, and neither grades which registration answered.
      Without this the two runs measure different things and the gate clears on
      an artefact. *(measured experiment)*
- [ ] **The pooled file is keyed on the distinct query string, not on the
      source entry.** The seven files hold 71 positive and 71 negative entries,
      but the negatives include two strings that appear in two files each:
      `Design the landing page to convert trial visitors`
      (`analytical-design` + `informational-design`) and `Design the article
      page layout for our editorial blog` (`conversion-design` +
      `documentation-design`). Pooling by entry would ship benign duplicates;
      pooling by distinct string gives 71 positives and 69 negatives before the
      contradiction rule. *(measured experiment)*
- [ ] **A query that is positive for one folded skill and negative for another
      is resolved before pooling, and the resolution is recorded.** Two exist
      today, quoted verbatim because the string is the key the dedup decision
      turns on: `Design the article page layout for our editorial blog` is
      positive for `informational-design` and negative for both
      `conversion-design` and `documentation-design`; `Design the workspace UI
      for our collaborative editing tool` is positive for `workspace-design`
      and negative for `conversion-design`. Once the seven are one skill, both
      readings cannot hold. The rule: **a query positive for any folded skill
      is positive for the survivor**, and its negative copies are dropped —
      those negatives existed only to separate two registrations that no longer
      compete. Note the first query is both a cross-file duplicate *and* a
      contradiction, which is why entry-arithmetic and string-arithmetic give
      different answers; the criterion above fixes which one governs. Failing
      state: a contradictory duplicate, which makes one copy fail by
      construction and decides the gate by arithmetic. *(measured experiment)*
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
- [ ] The six removed skills' **`evals/evals.json`** quality-eval sets — the
      prompt-and-expected-output cases, distinct from the activation queries —
      are carried into `information-architecture/evals/evals.json`, one case set
      per genre, or a named subset is knowingly dropped with the reason recorded
      in the ledger. Each removed skill ships **both** files; an earlier draft
      pooled only `eval_queries.json` and said nothing about the other, which
      would delete six quality-eval sets silently. Nothing reds:
      `skill_spec_lint` cross-checks `pack.evals.skills` against
      `eval_queries.json` only, so `catalogue lint --deep` stays green after
      they vanish. This is what `packs/AGENTS.md`'s eval-harness obligation asks
      for on a non-cosmetic pack change, and what this spec's own "the fold
      removes registrations, not content" requires. *(goal-based)*
- [ ] `information-architecture/evals/eval_queries.json` carries the positive
      queries pooled from all seven skills and that negative set, with a
      **stated expected count**, derived by the two rules above rather than by
      subtracting from an entry tally. Measured on the seven source files: 71
      positive entries, all 71 distinct, so the pooled positives are **71**; 71
      negative entries but only 69 distinct, of which the contradiction rule
      drops the two that are positive elsewhere, so the pooled negatives are
      **67**. An earlier draft said 69 by subtracting two from the negative
      *entry* count, which double-counted the cross-file duplicates it had not
      measured — and no file could satisfy it, so a correct implementation would
      have read as a miss and been "fixed" by re-adding a dropped contradictory
      negative, which is the defect these criteria exist to prevent.
      `plan.md` names a command that **asserts** — not prints — the two counts,
      the absence of any opposite-`should_trigger` collision, and the presence
      of the two named negatives **by their exact query text** rather than by
      keyword. A keyword proxy cannot settle it: the current negative set
      contains neither the substring `interaction` nor `design system`, and
      "belongs to `interaction-design`" is not decidable from a word. Failing
      state: a file that pooled nothing satisfies a check that only prints a
      number.
      *(goal-based — a document-content check, tagged as the sibling tags its twin.)*
- [ ] `notes/activation-baseline.md` names the **abort path** and its two
      triggers: a failing activation gate, **or** the ~3-week window in the
      brief's appetite elapsing without the fold landing. Either trigger leaves
      the same residue — the six directories are not deleted, and the non-fold
      half of the change ships on its own: the `frontend-engineering` table
      repair, its `design-system-foundations` slug correction, that pack's
      version bump, **its regenerated marketplace entry, and its changelog
      entry**, without the erratum or the `experience-design` major. The last
      two are named because they are what a bumped manifest needs to stay
      consistent: a `pack.toml` reading `0.3.3` against a projection reading
      `0.3.2` reds `agentbundle catalogue verify`, so a residue that ships the
      bump without the projection is not a shippable residue. `plan.md` gives
      them an owning task that does not sit behind the activation gate.
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
      removed skill **as a skill**, and no **live product-truth** record under
      `docs/` does. Two carve-outs are structural, not discretionary, and
      `plan.md`'s canonical sweep expression encodes both, alongside a third
      exclusion for the two documented exemptions in the criterion below — so
      "a real hit" below means a match that is neither carved out nor exempt,
      and a reviewer checking this criterion in isolation does not report a
      violation the exemption criterion already settled:
      **(a)** the six surviving genre references are named
      `information-architecture/references/<genre>-design.md`, so the reference
      filenames and the `SKILL.md` lines citing them match the removed-skill
      pattern by construction — the sweep excludes
      `.apm/skills/information-architecture/` for that reason, and a match
      anywhere else inside `packs/experience-design/` is a real hit;
      **(b)** the exclusion strips only the six removed skills' own
      directories. An earlier draft excluded `.apm/skills/[a-z]+-design/`, which
      also hid three files in two surviving skills that name removed skills
      today. `plan.md` § Verification command map is the **single** home for
      the measured figures and the enumerated hidden filenames; this criterion
      does not restate them, because a duplicated measurement moves in one copy
      and not the other. `information-architecture/SKILL.md` is not left
      unchecked by carve-out (a), but only because two controls were added to
      cover it: the routing criteria decide the **destination cell against the
      three permitted outcomes**, failing when a row still names a deleted
      skill, and the genre-reference scan opens `SKILL.md` alongside the six
      references. Reading both cells is not by itself the stronger check — an
      earlier version asserted only that each destination was non-empty, which a
      table routing all six genres at deleted skills satisfies. Failing state: a sweep that
      reports zero because its own exclusion swallowed the hits. *(goal-based)*
- [ ] **Two sweep hits are documented exemptions rather than edits, and the
      reason for each is recorded in the ledger.** First,
      `tools/lint-guidebook-steps.py:406` carries `analytical-design` inside an
      explanatory comment that names a file without referencing the skill;
      rewriting an unrelated tool's comment to silence a completeness check is
      a worse outcome than the hit. Second,
      `packs/experience-design/.apm/skills/tone-of-voice/references/editorial-quality-gates.md:3`
      says its content "is intentionally duplicated into `conversion-design`'s
      `references/editorial-quality-gates.md`" — a note that points at a
      directory T4 deletes. It is **not** corrected here: that file is one of
      the three distinct-hash copies whose reconciliation this spec routes to
      `xd-copy-router`, and editing its bytes moves a hash that sibling slice is
      measured against. **The ledger** records that the note is stale until the
      copy fold lands — the same place both sweep-exemption reasons go, and a
      place T11's `Done when` already reads. An earlier version routed this to
      the changelog, where no task's condition and no command reached it, so
      the clause would have shipped missing with nothing red. Without these two exemptions the sweep can never return
      empty, and a reviewer facing a non-empty result must adjudicate it by eye.
      *(goal-based)*
- [ ] **The six new genre references are read for removed-skill names that are
      not their own filenames or the citations to them.** Carve-out (a) puts
      `references/<genre>-design.md` inside the excluded directory, and T3
      authors those files by carrying method across from six skills that
      cross-reference each other today —
      `interaction-design/references/pattern-families.md` cites both
      `marketplace-design`'s transaction bridge and `analytical-design`'s widget
      hierarchy. Failing state: a genre reference ships a sentence reading "see
      `conversion-design` for the above-fold contract", the sweep returns empty
      because the whole directory is excluded, and the alias-free guarantee is
      broken inside the surviving skill. `plan.md` names the narrower command.
      *(goal-based)*
- [ ] Under `docs/`, the exempt set is stated as **classes**, not as a list of
      filenames, because a name list silently omits a file added after it was
      written. The classes are: the RFC-0066 erratum; `docs/product/changelog.md`
      (whose own AC below requires the names); the delivery brief; **any
      file under `docs/specs/<delivery>/`, which takes **its owning delivery's
      lifecycle class — never its own file type**.** That is the whole rule, and
      it replaces two wrong attempts. The first said "spec or plan", which left
      another live delivery's execution notes in the "open, owed an edit"
      default. The second widened to "any directory still in flight" and listed
      four files, which failed twice over: a list is the enumeration this rule
      forbids, and two of the four
      (`docs/specs/communication-modes-editorial/test-results.md`,
      `docs/specs/xd-skill-boundaries/benchmark.md`) belong to deliveries whose
      specs read **Shipped** — so they were neither in flight nor, being neither
      a spec nor a plan, frozen under a rule that named only "a shipped spec".
      They fell straight back to the default. Under the rule as now stated: a
      **closed** delivery's notes, benchmarks and test results are **frozen**,
      whatever their filename; an **in-flight** delivery's are that delivery's
      to sweep, not this one's. Either way they are not open here. Rewriting a
      shipped benchmark to remove the names of the skills it benchmarked is the
      same failure as the `findings/` omission, two directories over; and **dated outputs** —
      anything under `docs/design/`, anything under `docs/product/research/`,
      and anything under `docs/product/findings/` — each records what was
      measured or observed on a date. `findings/` was missed by an earlier
      two-directory version, which is the same omission the class rule exists to
      prevent: two live hits sit there today
      (`experience-design-thread-pressure-test.md`, whose own status says the
      blind comparison did not run, and `s7-walkability-handoff.md`), and the
      "every remaining hit is open" sentence below would have sent T7 to rewrite
      two dated measurement records to remove the names of the skills they
      measured. Frozen records are out
      of scope by the lifecycle rule above. Every remaining hit is **open** and
      owed an edit. *(goal-based)*
- [ ] Every **open** lifecycle record under `docs/` naming a removed skill is
      updated, starting with `docs/product/intents/skill-sequence-wayfinding.md`
      (Status: Draft, naming **all six** — measured per-name on 2026-09-25, one
      occurrence each at lines 138–140; an earlier "five of the six" would have
      let an implementer stop one short). The enumeration comes from
      grepping `docs/` for the six names and classifying each hit as frozen,
      dated output, or open. *(goal-based)*
- [ ] No alias, shim, or deprecation stub is shipped. *(goal-based)*
- [ ] `tools/add-rendering-directives.py`'s per-skill map carries none of the
      six removed keys, and `information-architecture`'s own entry states what
      it becomes. It is registered `["table"]` today while `informational-design`
      is registered `["table", "narrative"]`, so a fold that only deletes keys
      ships the informational genre's method under a skill whose injected
      directives dropped the narrative guidance that method depends on. This
      spec sets the surviving entry to `["table", "narrative"]` — the union of
      the seven folded entries, which is exactly those two values. No gate reads
      this map, so without the criterion the loss is silent. *(goal-based)*
- [ ] Every skill-count numeral for this pack reads **14**. The set is
      **re-derived by measurement, not enumerated** — an earlier three-file list
      missed `guides/experience-design/README.md:83` ("That is the complete
      20-skill inventory"), whose numeral carries no removed skill name and so
      survives both the sweep and a negative grep scoped to three other paths.
      Measured on 2026-09-24 there are **five numerals across four files**:
      `packs/experience-design/docs/index.md` lines 3 and 11,
      `guides/experience-design/reference/experience-design.md:17`,
      `guides/experience-design/README.md:83`, and
      `web/src/content/packs/experience-design.md:69`. The check covers word
      forms as well as digits. `packs/experience-design/README.md` and
      `JOURNEY.md` carry no numeral — verified — and owe only that their
      enumerated lists name no removed skill, which the sweep covers. `web/src/content/packs/experience-design.md:69` reads
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

The criteria in this section have **two post-states**, because the cross-pack
repair ships on either branch. Unless a criterion says otherwise it states the
**fold branch**. The abort branch is stated once, at the end of the section, and
it is a real contract rather than a note: the four-row collapsed table, the
all-six-genres row, and the retired `conversion-design` sentinel below are all
unreachable while the six skills still exist, so a residue governed by the fold
branch's wording would contradict itself.

- [ ] `frontend-engineering`'s genre-routing table reaches a stated post-state
      for every one of its seven current rows. Four of those rows name folded
      genre skills and collapse into a single row whose **Load cell holds the
      bare slug** `` `information-architecture` `` and whose Surface-type cell
      enumerates all six genres **by their `surface-genre:` token** —
      `marketing`, `documentation`, `informational`, `analytical`,
      `marketplace`, `workspace` — and not only in the table's existing prose
      idiom. Today's cells read "Dashboard, reporting view, analytics screen"
      and "Article page, editorial page, blog", which carry neither
      `analytical` nor `informational`, so a prose-only merge leaves the
      `marketplace` and `workspace` gap unverifiable by the very check written
      to close it. Prose may accompany the tokens; the tokens are what is
      contracted. **A second parser constraint binds the same cell and is
      stated here rather than discovered:**
      `test_the_example_genre_route_is_the_one_the_table_names` asserts that
      **exactly one** row has a Surface-type cell containing the substring
      `interaction`, case-insensitively, and routes the notification-panel
      worked example to it. So no other row's Surface-type cell may contain
      `interaction` — including the collapsed row, whose six tokens happen not
      to, and including any prose beside them. This binds hardest on the abort
      branch, where T9a adds a `workspace-design` row: prose such as
      "collaborative editing, real-time interaction surfaces" makes two rows
      match and reds the suite with a message about a notification panel, which
      explains nothing. The genre argument goes in the Surface-type
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
      it — in the **two** places that carry the string, verified by grep over
      `packs/frontend-engineering/` on 2026-09-24:
      `.apm/skills/frontend-engineering/SKILL.md:189` (the routing table) and
      `tests/skills/frontend-engineering/test_public_claims_match_shipped_behaviour.py:419`
      (the `readme_offered_genre_skills` docstring, which names the stale slug
      as routable to justify matching any backticked identifier rather than a
      `-design` suffix). `packs/frontend-engineering/README.md` carries **no**
      occurrence — an earlier draft named it as a third site, which would have
      sent an implementer to introduce the slug in order to correct it. The
      README's own obligation is the separate criterion below. The four
      byte-pinned contract copies are excluded by the criterion after next.
      *(goal-based)*
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
      read by `catalogue verify` structurally, rendered by `agentbundle list` in
      its dependencies column, and **enforced** by nothing at install or
      runtime. The declaration records the constraint for a human; it does not
      enforce it. **The entry's shape is stated, because getting it wrong reds
      a gate this delivery must pass.** `verify.py` requires three non-empty
      string fields on every dependency entry — `catalogue`, `pack`, and
      `version` — and runs `version` through `parse_version_range`, which splits
      on whitespace: `>= 3.0.0` parses as two atoms and **fails**, while
      `>=3.0.0` passes. Both were measured against the repository's own parser.
      **`catalogue` must read `agent-ready-repo`** — `catalogue.toml:7`. It is
      the one field of the three that does **not** red when wrong:
      `verify.py` does `if dep_catalogue != catalogue_name: continue`, so a
      mistyped catalogue silently skips resolution and exits 0, leaving a
      documented floor that resolves to nothing while this criterion reads
      satisfied. No `pack.toml` declares `dependencies.**recommended**` today,
      but several packs declare `dependencies.required` in the byte-identical
      three-field shape, every one of them reading
      `catalogue = "agent-ready-repo"` — `packs/atlassian/pack.toml:20-23` is
      the shortest. Copy that shape. No count is given here: an earlier draft
      said "four", the tree holds eight such `pack.toml` files carrying nine
      entries, and the figure is not load-bearing for the criterion. **The value is branch-dependent:** on the
      fold branch `>=3.0.0`; on the abort branch the highest **released**
      `experience-design` version at the time T6 runs — `>=2.0.10` if and only
      if `creative-direction-modes` has landed its bump, which it had in the
      working tree on 2026-09-24. If that sibling slips or aborts, the
      abort-branch floor is whatever `packs/experience-design/pack.toml` then
      reads, because a residue documenting a floor against a version that was
      never released is a constraint no adopter can satisfy, and `catalogue
      verify` reads `recommended` structurally and would not catch it.
      *(goal-based)*
- [ ] The named-skip text recorded when `experience-design` is absent is
      **unchanged**. Today it reads
      `XD genre routing: skipped (experience-design pack absent)` — it names the
      **pack**, not a skill, and the pack's name does not change in this
      delivery, so there is nothing to reconcile. An earlier wording ("matches
      the skill actually looked for") implied an edit that was unsatisfiable as
      written and would have put this literal out of step with its verbatim
      copy at `guides/frontend-engineering/tutorials/scaffold-a-component.md:82`
      — a file T6 cannot reach, T7a never names, and no suite compares against
      the skill. Leaving the literal alone keeps the two in agreement with no
      cross-tree edit. The sentinel beside it *does* change, and that is the
      criterion above. *(goal-based)*
- [ ] `packs/frontend-engineering/README.md`'s genre-route list names exactly
      the surviving routing targets. It offers **three** removed skills today —
      `conversion-design`, `documentation-design`, `analytical-design` — and a
      fourth name, `interaction-design`, which **survives this fold and must
      stay**: the worked example at `README.md:52` reads
      `Genre route: interaction-design`, and
      `test_the_readme_offers_the_route_its_own_example_takes` asserts the
      example's route is in the offered set. **"Exactly the surviving routing
      targets" means the post-fold routable set**, which is
      `information-architecture`, `interaction-design`, `content-design` and
      `design-system` — so `information-architecture` **must appear**. Dropping
      the three removed names and stopping there would leave a genre-route
      pre-flight offering no skill for the six genres this change exists to
      route, and `test_every_route_the_readme_offers_is_one_the_skill_routes_to`
      checks offered ⊆ routable in one direction only, so that narrower list
      would stay green. *(goal-based)*
- [ ] That route list stays inside a `(pick …)` parenthetical that splits into
      **exactly three** em-dash-delimited parts, with the backticked names in the
      middle part. `readme_offered_genre_skills()` asserts the part count and
      reads names only from `parts[1]`, so a rewrite that drops the trailing
      `— if \`experience-design\` is co-installed` clause reds the suite with a
      message about prose structure rather than about routing. The criterion
      pins the sentence shape, not only the name set. *(goal-based)*
- [ ] `web/src/content/packs/frontend-engineering.md` contains no removed skill
      name — which `sweep` settles — **and** names the same routing target as
      the table, which `sweep` cannot settle because it is a positive claim.
      **T7** owns it — it holds `web/src/content/**`; T6's `Touches` cannot
      reach the file. *(goal-based)*
- [ ] `guides/frontend-engineering/how-to/read-the-design-handoff.md` is
      confirmed to carry **no** routing target and no genre-skill name — grep
      on 2026-09-24 returns zero occurrences of any genre skill,
      `information-architecture`, `experience-design`, or the word "genre". It
      was previously bundled into the criterion above, whose negative half
      passed with no edit while its positive half had nothing to check. The
      obligation here is a **recorded confirmation** in the ledger, not an
      edit; if the grep ever returns a hit, the file joins the sweep's open
      class. *(goal-based)*
- [ ] **Abort-branch post-state.** If the activation gate fails, the six skills
      still exist, and the cross-pack repair ships against them: the table
      **grows from seven rows to nine** rather than collapsing to four. The four
      genre rows keep naming their own skills, `interaction-design`,
      `content-design` and `design-system` survive as today, and
      `marketplace-design` and `workspace-design` are **added** as two new rows,
      which closes the routing gap on this branch too. Seven plus two is nine;
      an earlier draft said "keeps seven rows" *and* "adds two", which made the
      branch's only cross-pack content task unsatisfiable by its own tests;
      the sentinel keeps probing `conversion-design`, which is correct while
      that skill ships; the `design-system-foundations` → `design-system` slug
      correction lands unchanged, since it never depended on the fold; the
      README route list keeps its three genre names and `interaction-design`;
      and the `recommended` version floor is declared against the pre-fold
      `experience-design` version. The removed-name sweep, the erratum, the
      `experience-design` major, and every skill-count numeral are **not** owed
      on this branch. *(goal-based)*
- [ ] **The abort branch has a stated closeout.** T11 depends on T10, which the
      abort branch forbids, so without this the slice has no task whose
      `Done when` can be reached: nobody records the `docs/` classification, the
      documented sweep exemptions, or any manual-QA verdict. On the abort branch
      closeout is T11 run against T10a alone, and it owes exactly three things —
      the ledger's record of the abort decision and its deciding owner, the
      `guides/frontend-engineering` confirmation above, and judgement 1 if T3
      was authored before the gate failed. The install/update prune observation
      and judgements 2 and 3 are **not** owed, because nothing was removed and
      no guide was rewritten. *(goal-based)*

### Governance records

- [ ] `docs/rfc/0066-…md` § Errata carries a dated, approver-signed entry naming
      **D4**, stating that the six separate registrations are retired, that the
      genre method is preserved as references under `information-architecture`,
      and that D2's seven-type taxonomy and D5(d)'s `transactional-journey` route
      are unchanged. *(goal-based)*
- [ ] That entry names no spec and no delivery brief, and reads completely for
      someone holding only the RFC. *(goal-based)*
- [ ] The Errata section conforms to RFC-0055 D2's two-layer structure, whose
      headings are `### Current state` and `### History / audit trail` — quoted
      as RFC-0055 writes them, not paraphrased. D2's trigger is "more than one
      entry, **or** any entry supersedes **another**"; only the first limb fires
      here — the section holds one entry today and gains a second — which is
      sufficient, and the second limb is not claimed. *(goal-based)*
- [ ] The existing 2026-07-27 entry travels into the history layer
      **verbatim**, including its reference to `docs/specs/ux-writing-rename/`.
      The never-do rule against naming a spec inside an erratum binds only
      entries **this delivery authors**; RFC-0055 D3 makes correction sections
      append-only, so rewording a prior entry to satisfy a rule written later is
      the larger violation. Without this statement T8's implementer must pick
      between two rules with no guidance, which is a review round, not a
      judgement. *(goal-based)*
- [ ] `packs/experience-design/DESIGN.md` names no removed skill slug anywhere in
      the file. *(goal-based)*
- [ ] `DESIGN.md` describes one genre-aware IA skill at every point it describes
      the genre step. A slug check cannot settle this: line 41 ("or genre-direct
      skill"), line 61 ("and the genre-direct skills"), line 179
      ("**Information-architecture / genre-direct skills**"), line 185 (the
      section heading `### The genre-direct skills`) and line 249
      ("craft/genre skills") carry no slug, and lines 187–198 assert six skills
      run in place of the IA step — all of which pass a slug check unchanged
      while still describing the old shape. Those **six** locations are the
      checked set. Line 185 was added to it after a review found that a section
      still headed "The genre-direct skills" would survive both the slug check
      and the five-location check while its body described one genre-aware
      skill. Line 75 is **not** among them: it names only
      `information-architecture` and `interaction-design`. *(goal-based)*
- [ ] `DESIGN.md` § 10's entry *"Why six genre-direct skills instead of one
      general IA skill with genre flags (from v1)"* records both what was
      rejected — a `genre:`-parameterised skill, on the grounds that it would bury
      the genre logic in a conditional tree — and what now ships, with the
      approver named and dated. It does not assert that the earlier rejection
      fails to apply. *(goal-based)*
- [ ] This delivery is § 10's **only** editor. The evidence is the sibling's
      own criterion — `docs/specs/creative-direction-modes/spec.md` requires
      that `DESIGN.md` § 10 is not edited by that delivery — so there is no
      interim wording to supersede and a supersession clause here would
      reference text nobody installs. T5 settles this by reading that criterion
      in the sibling spec, not by asserting a negative about edits it cannot
      observe. *(goal-based)*

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
- [ ] `docs/product/intents/xd-state-reviewer-doctrine.md` is **not** updated
      here — the `experience-reviewer` edits it must be checked against belong to
      the sibling copy fold. What this delivery owes is the **hand-off itself**:
      T7 confirms that `docs/specs/xd-copy-router/spec.md` carries a criterion
      naming that file, and records the confirmation in the ledger. An earlier
      draft stated the update as this spec's criterion while assigning the work
      to another spec, which left this delivery's completion gate reading a box
      nothing here could tick. *(goal-based)*

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
      docs site and does not read `web/src/content/`. **The build has a
      prerequisite this criterion owns:** `web/node_modules` is absent on a
      fresh checkout, and `npm run build` then exits **127** with
      `sh: astro: command not found` — a failure that looks identical to a
      schema rejection. The criterion is met only by a run that installed
      dependencies first, and the recorded evidence distinguishes the two
      outcomes: exit 127 with `astro: command not found` is *toolchain absent
      and the criterion unsettled*, a non-zero exit carrying a Zod or collection
      error is *schema rejected and the criterion failed*. `plan.md` names the
      install step. *(goal-based)*

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
- [ ] That entry carries a `### Highlights` subsection. The changelog's own
      header rules — which this spec's Durable Outputs name as the owner —
      require one "when the release changes what a consumer can do", and say
      that a release changing nothing consumer-facing carries none but that
      "*none* is a verdict to record with its reason, not a step to skip".
      Retiring six skills at a major bump plainly qualifies, and the sibling's
      `[experience-design][2.0.10]` entry carries one. Nothing downstream
      enforces it — the `/now/` projection is a pure parser and no model runs in
      the build — so without this criterion the release is absent from the
      public page permanently and invisibly. Blank-line and heading-level
      conformance is separately covered by `tools/test_build_site_routing.py`;
      `Highlights` is the one header rule with no instrument. *(goal-based)*
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
- Repository maintainer: **no durable control fails when a shipped document
  names a skill the catalogue no longer exports.** This is the gap the whole
  sweep exists to close by hand, once. `tests/roster/test_skill_census.py`
  asserts set equality between the census fixture and the shipped `SKILL.md`
  files, so it catches a deleted skill missing from the census — but not a
  surviving guide, README, or Astro page that still names one. The completeness
  expression lives in `plan.md`, a delivery artifact that gets archived, so this
  fold's control does not outlive it. Related and narrower: nothing tests
  routing-table completeness *between* packs either, which is how
  `marketplace-design` and `workspace-design` went unrouted. A roster suite
  covering both would prevent the next instance; this delivery removes today's
  and records the need rather than landing it.
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
- Technical — **knowingly stale for one slice, and anchored to the right line.**
  RFC-0071's operative sweep statement is **line 311**, "All 19 skills: update
  trigger descriptions…", which its own 2026 erratum at line 482–484 corrects to
  20. Line 70 reads "20 existing skills **touched** (19 + `copy-direction`)" — a
  delivery-scope figure that describes what RFC-0071 did and stays true however
  many skills the pack later holds. An earlier draft of this assumption named
  lines 70 and 484 as carrying "20 skills" in operative text; neither does, and
  an owner acting on it would have filed an erratum against two lines that were
  never wrong while leaving line 311 uncorrected.
  So the resolution is: **line 311 is the only line this fold makes stale**, and
  a count erratum **is** owed for it. RFC-0071's erratum is assigned to the
  sibling copy fold, which lands second, so the RFC reads wrong on that line
  between the two slices. That is accepted rather than fixed here: splitting one
  RFC's erratum across two slices would leave two partial entries in a section
  RFC-0055 D2 requires to read as one current state. If the copy fold aborts,
  this slice's owner files the line-311 count erratum rather than leaving an
  Accepted RFC wrong with no owner.
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
