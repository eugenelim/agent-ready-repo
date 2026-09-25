# Spec: One copy-layer skill with three modes

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0062 and its 2026-08-02 erratum (amended by erratum in this change); RFC-0071 (digital-experience doctrine, amended by erratum); RFC-0055 D2 (errata structure); RFC-0033 / ADR-0024 (framework agnosticism); ADR-0038 (alias-free precedent)
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

Someone shaping what a surface says reaches one copy-layer skill and picks a
mode, instead of choosing between three registrations whose boundary the pack
needs a documentation section to explain. Each mode still produces its own
artifact, at its own path, and the rules they share exist once.

## What Changes

- `copy-direction` and `tone-of-voice` fold into `content-design`, which gains
  three modes: message and narrative structure, per-surface acquisition copy
  goals, and the brand-level register.
- Six duplicated references collapse to one copy each, with per-mode differences
  expressed as named clauses inside the surviving file.
- `editorial-quality-gates.md` — a three-way duplicate also held by
  `information-architecture` after the genre fold — gets one canonical copy plus
  a byte-equality test, following the `containment.md` precedent.
- `experience-reviewer`'s sync citation and artifact-exclusion clause stop
  naming a deleted path.
- RFC-0062 and RFC-0071 gain errata; the pack takes a major bump to `4.0.0`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | Applicable — three registrations become one | `packs/experience-design/.apm/skills/content-design/` | This spec | One `SKILL.md` with three modes; one copy of each shared reference | Pack lint and the roster suites are clean |
| Current product truth | Applicable — the reviewer cites a path this change deletes | `packs/experience-design/.apm/agents/experience-reviewer.md` | This spec | Its sync citation resolves; its exclusion clause names surviving artifact types | The agent and the skill agree |
| Shared-reference integrity | Applicable — one reference is held by two skills | `content-design/` and `information-architecture/` | This spec | One canonical copy plus a byte-equality assertion | The roster suite covers it |
| Interface compatibility | Applicable — a removal | `packs/experience-design/pack.toml`, `.claude-plugin/plugin.json`, regenerated `.claude-plugin/marketplace.json` | `packs/AGENTS.md` § Version bump rule | Matching **major** bump in both source manifests | All three read `4.0.0` |
| Interface compatibility | Applicable — a second pack's content changes | `packs/product-engineering/pack.toml`, `.claude-plugin/plugin.json`, regenerated marketplace entry | `packs/AGENTS.md` § Version bump rule | One **patch** above the merge-base value in both source manifests | Both read one patch above the merge-base. Reading on 2026-09-25: `0.13.18`, so the target is `0.13.19` |
| Decision rationale | Applicable — two Accepted RFCs carry decisions that no longer hold | `docs/rfc/0062-…md` § Errata, `docs/rfc/0071-…md` § Errata, and `DESIGN.md` § 4 | RFC-0055 D2 | Approver-signed errata in the two-layer form | Each erratum stands alone without naming a spec |
| User promise | Applicable — the skills a reader invokes change | `guides/experience-design/` | `author-product-docs` | Updated copy-boundary guidance | Guide-agreement test passes and a named reviewer judges the guide sufficient |
| Public site truth | Applicable — the pack's published pages name each skill | `web/src/content/` | This spec | Frontmatter, `whatChanges`, and stage prose updated | The site build succeeds |
| Release history | Applicable — a released artifact's version is bumped | `docs/product/changelog.md` | That file's own header rules | A free-standing `## [experience-design][4.0.0] — <date>` entry directly beneath `[Unreleased]`, naming the removed skills | The entry sits at the right heading level with single blank lines around every heading |
| Reusable learning | Applicable — activation behaviour is the thing at risk | `content-design/evals/` | `packs/AGENTS.md` § Security and authoring rules | Pooled trigger queries plus a recorded before/after Tier-A result | `notes/activation-baseline.md` carries both runs |

## Agent Rules

### Always do

- **Keep `content-design` as the surviving skill name.**
  `tests/roster/test_content_design_communication_mode_contract.py` hard-codes
  `.../skills/content-design` and reads its `SKILL.md`,
  `references/communication-modes.md`, `assets/content-brief-template.md`, and
  `evals/evals.json`. Any other name makes the Gates criteria unsatisfiable
  without a test edit this spec does not scope.
- Run the Tier-A activation baseline **before** deleting any skill directory.
- Reconcile each drifted reference deliberately, one file at a time, recording
  which variant won and why. A silent pick is a rule change disguised as a merge.
- Preserve all three output contracts exactly, including `type:` **and** every
  frontmatter field the skills gate on together.
- Preserve the `brand-register` slug reservation and its refusal behaviour, which
  RFC-0062's 2026-08-02 erratum established.
- Preserve the cross-pack boundary against `product-engineering`'s `ux-writing`,
  and retarget that pack's references to the folded names in the same PR.
- Pool every folded skill's `eval_queries.json` positive cases into the surviving
  file.
- Bump `pack.toml` and `.claude-plugin/plugin.json` together, in the same edit.

### Ask first

- Passing `FORCE=1` to `make build-self`, per the standing conflict between
  `packs/AGENTS.local.md` and root `AGENTS.local.md`.

### Never do

- Rewrite a **frozen** record. The test is lifecycle class, not directory: a
  shipped spec, an Accepted RFC, and a closed ADR are amended only by erratum. A
  live record is updated.
- Name a spec or a delivery brief inside an RFC erratum. Those are
  delivery-time artifacts that get archived and pruned; the RFC is the durable
  record and must stand alone.
- Ship an alias or deprecation shim for a removed skill name (ADR-0038).
- Resolve a drifted reference by concatenating both variants. Two contradictory
  rules joined by a heading is worse than either alone.
- Touch `creative-direction/references/interrogation-sequence.md`. The brief
  settles the boundary flat: the copy-layer instances reconcile and the
  `creative-direction` variant is left alone. There is no permission path, so
  this is a refusal rather than an ask; the Follow-on is the only record.
- Change what any mode produces, or merge the three output artifacts into fewer.
  The brief settles this twice — as a confirmed-slice statement and as a rabbit
  hole — so it is not an open question at delivery time. Merging them would
  change `frontend-engineering`'s handoff read and the reviewer's
  marketing-clarity lens, and belongs to a different spec.
- Write a colour literal, a unit-bearing dimension or duration literal, a
  contrast or scale ratio, a named easing curve, an ARIA role, CSS syntax, a
  UI-framework name, or a concrete typeface name into any file under
  `packs/experience-design/`.

## Testing Strategy

- **Goal-based check** — a directory is absent, a reference exists exactly once,
  a named string is present or absent in a named file, a numeral matches a
  count, a version reads, a gate exits 0. `plan.md`'s verification command map
  covers every goal-based criterion here, in one of two forms. Most reduce to a
  command and appear in a fenced block. The rest are claims about the content of
  a `SKILL.md` or a note — a rubric that must be decidable, an enumeration that
  must be complete, an erratum that must say three specific things — and those
  appear in the map's table of **bounded reads**, each stating what the read must
  show so a reviewer can execute it and record a verdict. A goal-based criterion
  with no entry in either form is a defect in this spec, not a criterion exempt
  from checking.
- **Measured experiment** — the Tier-A activation comparison, recorded in
  `notes/activation-baseline.md`. Its statistic, run count, tolerance and abort
  path are acceptance criteria in this spec rather than a citation of the
  sibling genre spec, which is Draft and whose abort residue is genre-specific.
- **Manual QA** — four judgements: whether each reconciliation preserved the
  right rule; whether no rule was silently dropped; whether the three modes
  remain distinguishable to a reader; whether the guide is sufficient. Recorded
  in `notes/verification-ledger.md` with the reviewer's name and date.
- **No TDD.** No compressible invariant and no new Python surface.

## Acceptance Criteria

### The surviving skill

- [ ] `content-design/SKILL.md` carries exactly three modes, named literally:
      **message and narrative structure**, **per-surface acquisition copy
      goals**, and **brand-level register**. Naming them literally prevents
      confusion with the three `communication_mode` values a roster suite already
      asserts. *(goal-based)*
- [ ] `SKILL.md` carries a mode-selection rubric decidable without loading a
      reference. *(goal-based)*
- [ ] The merged `description` is at most **1024 characters**. This is a hard
      error in `skill_spec_lint.py`, not a warning, and the three source
      descriptions total 2,273 characters (769 + 732 + 772), so roughly 55% must
      compress away. The criterion exists because catalogue lint would otherwise
      be the first thing to notice. *(goal-based)*
- [ ] Each mode states what it produces, where it lands, and what it must not do.
      *(goal-based)*
- [ ] The three modes remain distinguishable to a reader. *(manual QA)*

### Reference reconciliation

- [ ] Each of these six references exists exactly once under `content-design`:
      `copy-arbitration.md`, `copy-grounding.md`, `interrogation-sequence.md`,
      `plain-language-floor.md`, `editorial-quality-gates.md`, and
      `copy-jtbd.md` — the merged jobs-to-be-done reference, named literally so
      the existence check can run. *(goal-based)*
- [ ] The merged file is **not** named `audience-jtbd.md`.
      `creative-direction/references/audience-jtbd.md` is a third instance of
      that basename and is out of scope here, so reusing the name would create a
      new two-copy, two-hash family instead of closing one. *(goal-based)*
- [ ] The sixth pair is reconciled: `copy-direction/references/audience-jtbd.md`
      and `tone-of-voice/references/copy-jtbd.md` are the same role under two
      names. The reconciliation note enumerates **every** substantive difference
      and classifies each as per-mode clause, winner, or drop — not only the
      ranking criterion. Enumerating a subset in this criterion would license a
      merge that silently drops the differences it omits, and the pair is known
      to diverge on more than one ranking criterion and to carry a section on
      each side the other lacks. *(goal-based)*
- [ ] `notes/reference-reconciliation.md` records, for each reconciled file,
      which variant won, the substantive differences, and why. *(goal-based)*
- [ ] `docs/product/briefs/digital-experience-doctrine-completion.md` has its own
      rows amended in this PR, with post-fold counts: its re-check row currently
      reads "31 files / 24 hashes: containment 5/1; layout 12/9; editorial gates
      3/3; interrogation 3/3; four other pairs 2/2", and its Adjacent-work row
      reads "S8a's **eight** duplicate-basename families". The amendment states
      the **full** post-fold row — every sub-count, the new file and hash
      totals, and the new family count — not a subset. **All four** of the "four
      other pairs" leave the family: `copy-arbitration.md`, `copy-grounding.md`
      and `plain-language-floor.md` exist only in the two folded skills and drop
      to one copy each, and `audience-jtbd.md` — whose two copies are
      `copy-direction`'s and `creative-direction`'s — drops to one because
      `copy-direction`'s instance merges into `copy-jtbd.md` and only
      `creative-direction`'s survives under that basename. Editorial gates goes
      to 2/1; the copy-layer interrogation instances reconcile to one, leaving
      that family at 2/2 alongside `creative-direction`'s; and deleting two
      directories takes layout from 12/9 to 10/7. Containment is untouched at
      5/1. **Eight families become four, and 31 files / 24 hashes becomes 19
      files / 11 hashes.** These figures are **derived, not pinned**: `plan.md`
      carries a regenerator that rebuilds the inventory from the tree, and the
      check compares the brief's row against that run's output. The numbers
      appear here so the criterion reads on its own; the regenerator is what
      decides a disagreement. Restating three sub-counts and leaving the 31/24
      headline and the family count stale discharges the obligation in form
      only. *(goal-based)*
- [ ] The brief's **second** stale occurrence is amended too. The 31/24 figure
      appears twice: in the re-check row and again in the Adjacent-work row as
      "the 31/24 measurement rules out a mechanical dedup sweep". Amending the
      first alone leaves a contradicting stale count one screen below.
      *(goal-based)*
- [ ] Where a mode genuinely needs a different rule, and the divergence is
      **localized**, the difference is a named per-mode clause inside the one
      file, not a second file. *(manual QA — paired with the classification
      verdict above.)*
- [ ] Where the divergence is **pervasive and scope-borne** — the same rule
      restated throughout, differing only in whose scope it names — the file is
      rewritten as one body with a single named scope parameter. The
      "one variant wins outright" branch is **not** available here: the scope is
      the divergence, so letting one win deletes the other surviving mode's
      scope, which the preservation criterion forbids. That branch remains open
      only for divergence that is not scope-borne.
      Per-mode-clausing every paragraph is the concatenation this spec forbids
      wearing a different name. `copy-arbitration.md` is the case that forces
      this rule: both variants restate each paragraph for their own scope, and
      one carries a section the other lacks. *(manual QA — the classification is
      a judgement; the verdict for each reconciled file is recorded in the
      ledger.)*
- [ ] The reconciliation note states which brand-naming convention wins.
      `tone-of-voice`'s `copy-grounding.md`, `interrogation-sequence.md` and
      `SKILL.md` body name real companies as examples where `copy-direction`'s
      equivalents say `[example service]`, and `tools/lint-experience-agnostic.py` checks neither,
      so nothing else will catch a regression. *(goal-based)*
- [ ] No reconciled reference is the concatenation of both variants.
      *(manual QA)*
- [ ] No rule present in either variant is silently dropped; a dropped rule is
      named in the reconciliation note with its reason. *(manual QA)*
- [ ] Each reconciliation preserves the rule the surviving modes need, verified
      against the modes that cite it. *(manual QA)*

### The three-way shared reference

- [ ] The `editorial-quality-gates.md` reconciliation is **three-way, not a
      pair**, and its verdict on one clause is recorded explicitly.
      `conversion-design`'s copy — the one the genre fold relocates and pins —
      differs from `copy-direction`'s on five lines, and one is substantive:
      `conversion-design` reads "Apply these gates to product-copy mode output"
      where `copy-direction` reads "Apply these gates **when the upstream content
      brief declares `communication_mode: product-copy`**". Byte-pinning the
      surviving pair to the relocated bytes without a verdict would silently drop
      that upstream condition, which is exactly the rule loss this spec forbids.
      The reconciliation note records which gating condition survives and why.
      *(goal-based)*
- [ ] `editorial-quality-gates.md` exists in `content-design` as the canonical
      copy and in `information-architecture`. **This is a dependency on the genre
      fold, not an assumption about it**: that spec carries matching criteria
      requiring the file to land byte-identical under `information-architecture`
      and to be cited from its `SKILL.md`. Failing state: the genre fold lands
      without both, in which case this fold stops and the genre fold is amended
      before it resumes — it does not create the file itself, because a second
      author of a shared file is how the drift started. *(goal-based)*
- [ ] The two copies are byte-identical, asserted by extending
      `tests/roster/test_experience_design_write_declaration_and_containment.py`,
      whose `test_every_containment_copy_is_byte_identical` is the exact pattern.
      Extending an existing suite avoids the three further guarded edits
      `tests/AGENTS.md` obliges for a **new** `tests/roster/test_*.py` — a named
      step in `build-check.yml`, a `STEP_DISPOSITION` entry in
      `tools/lint-ci-parity.py`, and a `.workspace-prune-protected.toml` entry.
      A new suite instead of an extension owes all three. *(goal-based)*
- [ ] `content-design/SKILL.md` cites `references/editorial-quality-gates.md`
      directly, not from a reference body — `communication-modes.md` is where the
      citation lives today. This mirrors the obligation the genre fold carries on
      `information-architecture`. **The citation rests on the grep in `plan.md`,
      not on the suite.** The containment precedent has two distinct tests:
      `test_every_containment_copy_is_byte_identical` globs the filesystem and
      never reads a citation, and
      `test_every_skill_citing_the_module_ships_its_own_copy` runs citation →
      copy, which cannot fail on a copy that nothing cites. The extension this
      spec mandates is of the first, so nothing in the suite would catch an
      uncited copy. An earlier draft claimed the suite derives its copy set from
      `SKILL.md` text and therefore enforced this; it does not. *(goal-based)*
- [ ] The recorded note in each copy reading *"Skill autonomy beats DRY at this
      scale"* is removed, and `DESIGN.md` records that the byte-equality test
      supersedes it. The fold reverses that decision, so it is addressed rather
      than left dangling. *(goal-based)*
- [ ] No surviving reference cites a deleted sibling skill's path.
      *(goal-based)*
- [ ] Inside the surviving skill, no removed name survives **as a registration
      or a path**. This is scoped deliberately: `type: tone-of-voice` contains
      the string `tone-of-voice`, so a bare `\b(copy-direction|tone-of-voice)\b`
      grep over `content-design/SKILL.md` is **mutually exclusive** with the
      carve-out criterion above, which requires seven such discriminator
      occurrences in that same file. The check is therefore for the removed names
      in registration or path position — `skills/copy-direction`, "the
      `tone-of-voice` skill", a routing target — never the `type:` literal.
      *(goal-based)*

### Output contracts unchanged

- [ ] **All three assets survive the directory deletions**, under
      `content-design/assets/`: `content-brief-template.md` (already there),
      `copy-direction-template.md` (today under `copy-direction/assets/`), and
      `tone-of-voice-template.md` (today under `tone-of-voice/assets/`). Each
      mode writes through its template, so a template deleted with its directory
      breaks the output contract the next two criteria assert while leaving every
      name-based check green. This criterion exists because an earlier draft
      named neither moved file anywhere — the plan's own commands already read
      `content-design/assets/tone-of-voice-template.md` as though the move had
      been specified. *(goal-based)*
- [ ] The per-surface copy direction still writes
      `<output_dir>/copy/<surface-slug>.md` with `type: copy-direction`, through
      the relocated `content-design/assets/copy-direction-template.md`.
      *(goal-based)*
- [ ] The brand register still writes the reserved
      `<output_dir>/copy/brand-register.md`, and its relocated template at
      `content-design/assets/tone-of-voice-template.md` emits **both**
      `type: tone-of-voice` **and** `scope: brand-level`. Both skills gate on the
      pair together, so a fold that keeps only `type:` breaks the upstream
      referent read and the legacy discriminator while passing a `type:`-only
      criterion. *(goal-based)*
- [ ] The content brief still writes its existing path and `type: content-brief`.
      *(goal-based)*
- [ ] Requesting `brand-register` as a per-surface slug is still refused, not
      repaired. *(manual QA — prose behaviour in a `SKILL.md`; the verdict is
      recorded in `notes/verification-ledger.md`, which is the single route.)*
- [ ] The three legacy-1.x migration prompts survive: `type: tone-of-voice` found
      at a per-surface slug; `type: tone-of-voice` without `scope: brand-level`;
      and user-profile `output_dir` cross-brand confirmation. *(goal-based)*
- [ ] The three-branch `type:`-collision handling on write survives.
      *(goal-based)*

### The removals

- [ ] The `copy-direction` and `tone-of-voice` directories are absent and
      `content-design` survives. *(goal-based)*
- [ ] `pack.toml` `[pack.evals].skills` and the set of directories under
      `.apm/skills/` are **equal**, at twelve. Membership, not cardinality: a
      length-only check passes a list that dropped an unrelated skill and kept
      `tone-of-voice`, and set equality is also what makes ADR-0038's alias-free
      rule checkable — an undeclared directory is a stub, including one shipped
      under a third name like `copy-direction-legacy`, which counting the two
      removed names could never see. Neither removed name is declared;
      `content-design` is. *(goal-based)*
- [ ] The two removed skills' quality-eval sets — each ships `evals/evals.json`
      **and** an `evals/files/` fixture tree that `content-design/evals/` does
      not have — are either carried into the surviving harness or dropped with a
      recorded reason. `packs/AGENTS.md` § Security and authoring rules obliges a
      non-cosmetic pack update to update that pack's eval harness, and
      `skill_spec_lint` cross-checks `pack.evals.skills` against
      `eval_queries.json` only, so a vanished `evals.json` leaves
      `catalogue lint --deep` green. The sibling genre spec carries the matching
      criterion for the same reason; an earlier draft here covered
      `eval_queries.json` alone and left `evals.json` and the fixtures to die
      with the directory. *(goal-based)*
- [ ] No file names a removed skill **as a registration** — in a skill roster, a
      routing target, an availability probe, or an install list. **Scope:**
      `packs/`, `guides/`, `web/`, `tools/`, `tests/`, the repo-root
      `workspace.toml`, and the five `docs/` files this delivery edits
      (`docs/rfc/0062-…md`, `docs/rfc/0071-…md`,
      `docs/product/briefs/digital-experience-doctrine-completion.md`,
      `docs/product/intents/xd-state-reviewer-doctrine.md`,
      `docs/product/changelog.md`). **Out of scope and deliberately so:** the
      rest of `docs/`. **The reason is what a registration sweep owns, not the
      frozen-record rule.** A registration is a place the catalogue is told a
      skill exists — a roster, a routing target, an availability probe, an
      install list. `docs/` outside the five files holds delivery and decision
      records that *mention* the skills: shipped specs, closed ADRs, the
      `docs/design/` corpus, and — the case that rules the frozen-record
      justification out — the two sibling specs `xd-genre-router` (Approved) and
      `creative-direction-modes` (Implementing), which are **live** records under
      this spec's own test and would be updated, not refused, if they held a
      registration. They do not; they name the skills as delivery context. An
      earlier draft claimed `docs/` was in scope while the command excluded it
      entirely, then justified the exclusion on a rule that does not apply to two
      of the excluded files. The bound is now stated on both sides and rests on
      the right reason. *(goal-based)*
- [ ] The string `tone-of-voice` survives wherever it is the **artifact
      discriminator** rather than a skill name, because the output contract above
      requires the template to keep emitting `type: tone-of-voice`. The sweep
      must not touch: `packs/product-engineering/.apm/skills/ux-writing/evals/evals.json`,
      the legacy branch inherited from `copy-direction/SKILL.md`, the amend gate
      inherited from `tone-of-voice/SKILL.md`,
      `packs/experience-design/.apm/skills/experience-status/SKILL.md` (whose
      artifact-scan table reads `type: tone-of-voice` **and**
      `scope: brand-level` together), and the files below. The list is a
      **measured occurrence count**, not prose, so a sweep that removes one fails
      a number rather than a reading. Every count was re-measured on 2026-09-25:

      | File | `type: tone-of-voice` uses that must survive |
      | --- | ---: |
      | `copy-direction/SKILL.md` (inherited into the merged skill) | 4 |
      | `tone-of-voice/SKILL.md` (inherited) | 3 |
      | `tone-of-voice/assets/tone-of-voice-template.md` (inherited) | 1 |
      | `tone-of-voice/evals/evals.json` (inherited) | 2 |
      | `experience-status/SKILL.md` | 1 |
      | `product-engineering/.apm/skills/ux-writing/SKILL.md` | 3 |
      | `product-engineering/.apm/skills/ux-writing/evals/evals.json` | 2 |

      A sweep that removes these breaks the discriminator while passing a
      name-based check.

      **Not on the list, deliberately:**
      `tone-of-voice/references/agentbundle-layout.md` holds five further uses
      (five occurrences across four lines) and is **deleted with its directory**
      — it is a pack-wide duplicated reference, not a copy-layer one, and the
      surviving skill already carries its own copy. Listing it as must-survive
      would oblige the delivery to preserve occurrences inside a file it
      removes, which is unsatisfiable. The Follow-on records that this shrinks
      the `agentbundle-layout` family rather than closing it. *(goal-based)*
- [ ] `ux-writing/SKILL.md`'s cross-skill pointer "surface the same migration
      prompt as `tone-of-voice` step 6" is retargeted to the surviving mode's
      step, while its **three** `type: tone-of-voice` discriminator literals
      stay — the count the carve-out table below records and the tree measures
      (all three sit on one line). An earlier draft said four here and three in
      the table. *(goal-based)*
- [ ] `packs/product-engineering`'s `ux-writing` `SKILL.md` and its
      `DESIGN.md` name the surviving skill as a registration. `DESIGN.md` names
      `tone-of-voice` at two points that the registration sweep reaches and the
      discriminator carve-out does not. *(goal-based)*
- [ ] `workspace.toml` entries naming a removed skill are reconciled.
      *(goal-based)*
- [ ] Every skill-count numeral for this pack reads **12** post-fold. The count
      is expressed three different ways across these files, so the criterion is
      stated per file and per numeral rather than as one value asserted across
      all of them. Readings are from 2026-09-25, pre-genre-fold; the genre fold
      lands first and takes each to its 14-skill form, which is what this
      delivery actually edits:

      | File | Numeral | Today | Post-fold |
      | --- | --- | --- | --- |
      | `packs/experience-design/docs/index.md` | prose, line 3 | `pack of 20 skills` | `pack of 12 skills` |
      | `packs/experience-design/docs/index.md` | heading, line 11 | `**Skills (20) in two families:**` | `**Skills (12) in two families:**` |
      | `guides/experience-design/reference/experience-design.md` | prose, line 17 | `20 pure-Markdown skills` | `12 pure-Markdown skills` |
      | `web/src/content/packs/experience-design.md` | **ordinal**, line 69 | `twenty-first skill` | `thirteenth skill` |
      | `packs/experience-design/README.md` | none | — | still none |
      | `packs/experience-design/JOURNEY.md` | none | — | still none |

      `docs/index.md` carries **two** numerals, not one: checking only the prose
      line leaves the heading stale. `README.md` and `JOURNEY.md` carry no
      skill-count numeral, so asserting "reads 12" of them cannot fail; their
      obligation is the registry criterion above — they name the surviving skill
      set — plus the negative check that neither acquires a stale count. The
      `web/` construct is ordinal and counts the reviewer agent as the last
      entry, so `12` never appears in it and a cardinal check would fail a
      correct page. *(goal-based)*

### Activation evidence

- [ ] `notes/activation-baseline.md` records Tier-A runs before and after,
      naming the command, date, CLI version, and model identifier for each.
      *(measured experiment)*
- [ ] The pass statistic is **total passing queries over total queries**,
      computed identically on both sides over the same pooled set; each run is
      repeated **three times** and the reported figure is the lowest.
      *(measured experiment)*
- [ ] `notes/activation-baseline.md` names this fold's own **abort path** and its
      two triggers — a failing gate, or the brief's ~3-week window elapsing. On
      either, the two directories are not deleted and **nothing else in this
      slice ships**: unlike the genre fold, this slice has no separable repair to
      land on its own, and saying so prevents a partial fold. The deciding owner
      is **eugenelim**. *(measured experiment)*
- [ ] The surviving `eval_queries.json` carries the pooled positives plus
      negatives that must not trigger, including at least one belonging to
      `ux-writing` and one to `creative-direction`. *(goal-based)*
- [ ] The fold ships only when both the positive and the negative figures are
      greater than or equal to their baselines. *(measured experiment)*
- [ ] `notes/verification-ledger.md` records the observed `agentbundle`
      install-and-update behaviour for a removed skill directory, and the
      changelog states the adopter action if stale directories are not pruned.
      *(goal-based)*

### Governance records

- [ ] `docs/rfc/0062-…md` § Errata carries a dated, approver-signed entry
      recording that the three registrations become one, that all three output
      contracts are unchanged, and that the 2026-08-02 erratum's brand-register
      reservation survives. *(goal-based)*
- [ ] `docs/rfc/0071-…md` § Errata carries its own entry. RFC-0071 carries the
      skill inventory in operative text, an ordering dependency that references
      `copy-direction` by name, and a boundary statement this fold reverses. The
      entry names the post-fold count — **12** — and states that it **supersedes**
      the 2026-08-02 erratum, which already corrected that same count from 19 to
      20. A new entry that silently restates a number an earlier erratum set is
      the case RFC-0055 D2's two-layer form exists for: the supersession is what
      makes the `### Current state` layer authoritative over the log.
      *(goal-based)*
- [ ] Neither **new** erratum entry names a spec or a delivery brief, and each
      reads completely for someone holding only that RFC. RFC-0062's existing
      2026-08-02 entry cites a spec path twice and moves into `### History`
      unchanged; the rule binds what this delivery writes, not what it inherits.
      *(goal-based)*
- [ ] Both Errata sections conform to RFC-0055 D2's two-layer
      `### Current state` / `### History` structure. Both trigger conditions fire
      on each. *(goal-based)*
- [ ] `DESIGN.md` § 4's "Content-design vs. tone-of-voice vs. copy-direction vs.
      ux-writing" section is rewritten as mode selection within one skill plus
      the one cross-pack boundary that remains. *(goal-based)*
- [ ] `DESIGN.md` names no removed skill as a registration, **including § 7's
      artifact table**, whose `copy/` row reads "tone-of-voice (the brand-level
      register), copy-direction (per surface)" — two skill-name registrations the
      sweep must retarget. `DESIGN.md` contains no `type: tone-of-voice` literal
      at all, so it is not a discriminator surface and carries no carve-out.
      *(goal-based)*

### Cross-pack and reviewer boundaries

- [ ] `experience-reviewer.md`'s sync citation — which today points at
      `tone-of-voice`'s `references/editorial-quality-gates.md` — resolves to the
      surviving canonical path. *(goal-based)*
- [ ] Its artifact-exclusion clause naming "tone-of-voice docs" names a surviving
      artifact `type:` rather than a skill name, since "tone-of-voice" becomes a
      mode name. *(goal-based)*
- [ ] `experience-reviewer.md`'s `Does NOT fire on` list and its sync
      parenthetical name only surviving skills or artifact types. The lens itself
      names no skill, so a criterion asking whether it "names a skill that
      exists" could not fail. *(goal-based)*

- [ ] `docs/product/intents/xd-state-reviewer-doctrine.md` is updated against
      this delivery's `experience-reviewer.md` edits, or recorded as confirmed
      unaffected. The brief and the sibling genre spec both delegate this check
      here, and it appears in neither's criteria. *(goal-based)*

### Registry and projection surfaces

- [ ] `packs/agent-skill-engineering/tests/fixtures/skill-census.json` matches
      the new inventory. *(goal-based)*
- [ ] `JOURNEY.md`, `README.md`, `docs/index.md`, and
      `web/src/content/{journeys,packs}/experience-design.md` name the surviving
      skill only, including the journey page's `skills:` frontmatter list.
      *(goal-based)*
- [ ] `tools/add-rendering-directives.py`'s per-skill map carries no removed
      name. *(goal-based)*
- [ ] The site build succeeds. *(goal-based)*

### Release

- [ ] `pack.toml` and `.claude-plugin/plugin.json` both read `4.0.0` — the second
      **major** bump, because the genre fold takes `3.0.0` and lands first.
      *(goal-based)*
- [ ] `.claude-plugin/marketplace.json` reads `4.0.0` for `experience-design`,
      regenerated by self-host. *(goal-based)*
- [ ] `docs/product/changelog.md` carries a free-standing
      `## [experience-design][4.0.0] — <YYYY-MM-DD>` entry directly beneath
      `[Unreleased]`, naming both removed skills explicitly. *(goal-based)*
- [ ] `packs/product-engineering/pack.toml` and its
      `.claude-plugin/plugin.json` read exactly **one patch above the value at
      this delivery's merge-base**, its marketplace entry is regenerated, and the
      changelog carries its entry. Patch, not major: this delivery changes that
      pack's content and removes no primitive. This delivery edits that pack's
      `ux-writing` skill and its `DESIGN.md`, which `packs/AGENTS.md` § Version
      bump rule obliges a bump for. **The target is derived, not literal.** An
      earlier draft wrote `0.13.17 → 0.13.18`; the pack reached `0.13.18` on its
      own before this spec was approved, which made the criterion pass against an
      untouched tree and would have let the obliged bump be skipped in silence.
      The reading on 2026-09-25 is `0.13.18`, so the target is `0.13.19` unless
      the merge-base has moved again. *(goal-based)*

### Gates

- [ ] `python3 tools/lint-experience-agnostic.py` exits 0. *(goal-based)*
- [ ] `tests/roster/test_content_design_communication_mode_contract.py` and all
      `test_experience_*` suites pass. *(goal-based)*
- [ ] `agentbundle catalogue lint --root . --deep` and
      `agentbundle catalogue verify --root .` each exit 0 after the projection is
      regenerated. *(goal-based)*
- [ ] The five commands in `guides/AGENTS.md` § Essential commands each exit 0.
      *(goal-based)*
- [ ] `make lint-ruff lint-mypy` exits 0. *(goal-based)*
- [ ] `notes/verification-ledger.md` records all four manual-QA verdicts with the
      reviewer's name and date. *(goal-based)*

### Documentation

- [ ] `guides/experience-design/how-to/copy-boundary.md` describes mode selection
      within one skill. *(manual QA)*

## Follow-ons

- Repository maintainer: `interrogation-sequence.md` has a third variant under
  `creative-direction`. This spec reconciles the copy-layer instances only.
- Repository maintainer: the copy skills declare their output inside a procedure
  step rather than through the `**Writes:**` / `**Confinement:**` declaration
  lines four other skills use, so the roster write-declaration suite does not
  cover them. Extending it would catch the next drift.
- Repository maintainer: `agentbundle-layout.md` is duplicated pack-wide.
  `digital-experience-doctrine-completion` routes that S8a family **out** of
  itself to an intake candidate named
  `experience-design-reference-reconciliation`, which has no admitted intent
  yet, so the family is currently unowned rather than owned elsewhere. This fold
  reduces the copy count as a side effect of deleting two skill directories,
  which is why that brief's measurement rows are amended here.

## Assumptions

- Technical: all five same-named references shared between `copy-direction` and
  `tone-of-voice` differ; `copy-arbitration.md` differs on 37 lines. Changed-line
  counts come from `diff <a> <b> | grep -c '^[<>]'` per pair and count both
  sides, not a one-directional edit distance. Line counts come from `wc -l`,
  which agrees with `splitlines()` here because every file ends in a newline:
  `copy-arbitration.md` is 33 and 42 lines, `audience-jtbd.md` 42,
  `copy-jtbd.md` 40. Both commands, 2026-09-24, re-run unchanged on 2026-09-25.
- Technical: a sixth pair, `audience-jtbd.md` and `copy-jtbd.md`, is the same
  role under two names — 42 and 40 lines, 22 differing (same commands, same
  dates).
- Technical: `editorial-quality-gates.md` exists in three skills today, one of
  which (`conversion-design`) the genre fold absorbs into
  `information-architecture` before this spec runs.
- Technical: the copy skills carry no `**Writes:**` or `**Confinement:**`
  declaration line; containment is inlined in a procedure step, so
  `test_experience_design_write_declaration_and_containment.py` does not pin them.
- Technical: `tests/roster/test_content_design_communication_mode_contract.py`
  hard-codes the `content-design` directory and three of its files, which fixes
  the surviving skill's name.
- Technical: automated Tier-B eval grading is deferred repository-wide.
- Process — **where a number lives.** Load-bearing values were stated twice, once
  here and once in `plan.md`, and drifted: the `ux-writing` literal count read
  four here and three in the same document's own table, and the
  `product-engineering` version went stale in both. The split is now: this spec
  owns **contract values** — what must be true when the delivery is done — and
  `plan.md` owns **measured readings** of the pre-delivery tree, each dated. A
  number that is both carries its reading date so a reviewer can tell a stale
  record from a failing check. Every count in this spec was re-measured on
  2026-09-25.
- Process: removals are a major bump; this is the second of two, so `4.0.0`.
- Process — **recorded dissent.** The same objection recorded in the sibling
  genre spec applies here: an independent review held that retiring registrations
  originates a new decision rather than recording where an authorised one landed,
  and that a fresh RFC is the instrument for that. The owner decided erratum on
  2026-09-24 and the decision stands; the objection is recorded, not resolved.
- Sequencing: this spec lands after `xd-genre-router`, which lands after
  `creative-direction-modes`. All three edit `DESIGN.md`, `pack.toml`,
  `.claude-plugin/plugin.json` and the changelog, and each carries a version
  bump.
