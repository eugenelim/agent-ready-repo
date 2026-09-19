# Spec: architect-design document-architecture gates

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0118
- **Brief:** none
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

An architect using `architect-design` gets document-architecture defects back
as findings their convergence loop can act on, instead of silence. Success is
that a document too large or too dense to review stops converging clean.

## What Changes

**The ten gates.** Every criterion below names one by identifier, so the
identifiers are what the document is about. ADR-0118 `D5` owns the set and
fixes which of the three kinds each one is; this table reproduces the names so
a reader can follow the criteria without opening that record.

| ID | The gate asks | Kind | Decided by |
| --- | --- | --- | --- |
| `DA1` | Is the body written in the present tense? | Hybrid | reviewer |
| `DA2` | Does every cross-reference name its target? | Hybrid | reviewer |
| `DA3` | Does any prose paragraph run past three sentences? | Mechanizable | the script |
| `DA4` | Does each model come before the prose explaining it? | Hybrid | reviewer |
| `DA5` | Does each concern live in exactly one place? | Judgment-only | reviewer |
| `DA6` | Have settled decisions been removed from the body? | Hybrid | reviewer |
| `DA7` | Does each diagram state one question at one zoom? | Hybrid | reviewer |
| `DA8` | Can the reader build from the models plus the mapping? | Hybrid | reviewer |
| `DA9` | Is evidence linked rather than piled into the document? | Hybrid | reviewer |
| `DA10` | Is the document over the size bound? | Mechanizable | the script |

A **precheck** is a mechanical hint inside one gate — for `DA6`, "is there a
`Revision History` heading?" — that narrows what the reviewer reads. It never
decides the gate. Every hybrid carries one; `DA5` carries none, and that
absence is what separates judgment-only from hybrid in the text.

**When the gates run, and in what order.** They run on a drafted document, at
two points: the author's self-check (`SKILL.md` step 6) and the review pass
the convergence loop obtains (step 7). `DA10` runs first — a document over the
bound may become several documents, and checking paragraph budgets in one
about to be split is wasted work. The other nine are a single pass, because a
reviewer reads the document once and wants every finding.

**The gates do not choose the document type.** Altitude — application/system,
subsystem, or architecture change — and document count are resolved at
`SKILL.md` step 3, before any drafting, and step 5 loads the matching
template. That routing ships already. Eight of the ten gates are
scope-independent because they judge how a document is built rather than which
sections it has. Two are not: `DA8` reads whichever section carries the build
mapping, which an architecture-change document names `Build Mapping` rather
than `Implementation Mapping`, and `DA7` fires only where there are diagrams.

- `DA3` and `DA10` — one script at
  `packs/architect/.apm/skills/architect-design/scripts/check_document_architecture.py`
- A confinement and refusal contract for that script — required `--root`,
  canonicalized boundary, regular files under 1 MiB, escaped output
- Seven hybrid prechecks and judgment-only `DA5` — reviewer checks in three
  homes
- The ten gate identifiers, tags and severities — under the existing
  `## Cross-cutting` heading of `architect-design/references/design-doc-rubric.md`
  and `architect-review/references/rubric-design-doc.md`, and a section of
  their own in `.apm/agents/design-reviewer.md`
- Gate-identifier and severity parity across those three homes —
  `packs/architect/tests/pack/test_design_reviewer_rubric_parity.py`
- A filled reference document the prechecks are walked against —
  `packs/architect/tests/skills/architect-design/testdata/filled-subsystem-design.md`
- Per-gate verdict reporting — `architect-design/SKILL.md` step 6 and
  `references/convergence-loop.md`
- A supersession pointer for the two interim rubric criteria —
  `docs/specs/architect-design-scope-templates/spec.md` `Status` line
- Pull-request gating for this pack suite — `.github/workflows/build-check.yml`
  and `tools/lint-ci-parity.py`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — ADR-0118 `D5` already fixes the gate set and its mechanizability | [`docs/adr/0118-architect-design-scope-routed-model-first-templates.md`](../../adr/0118-architect-design-scope-routed-model-first-templates.md) | architect pack maintainer | The parity test green against the `D5` identifiers and tags | The ten shipped gates and their mechanizability read back against `D5` |
| Release history | Applicable — the pack ships a version | [`docs/product/changelog.md`](../../product/changelog.md) | architect pack maintainer | A dated free-standing `## [architect][0.15.12]` entry | The Highlights verdict is recorded either way |
| Maintainer procedure | Applicable — an author and a reviewer both walk the gates | The three rubric homes named in What Changes | architect pack maintainer | `test_design_reviewer_rubric_parity.py` green | Every identifier, tag and severity agrees in all three homes |
| Interface compatibility | Applicable — the script is an adopter-reachable surface | The script's `--help` and exit codes | architect pack maintainer | The exit-code and refusal tests green | The typed-command transcripts in `notes/verification-ledger.md` |
| Current product truth | Not applicable — `guides/architect/` documents the journey, which does not change | — | — | — | — |
| Reusable learning | Applicable — the mechanizable-versus-judgment split generalizes | `project-knowledge` at the work-loop capture gates | implementing agent | A capture receipt | The receipt exists, or `project-knowledge unavailable` is recorded |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- State a gate's rule directly in `packs/`; cite no ADR, RFC, or
  repository-only path from shipped pack content.
- Give every gate the same identifier, tag and severity in all three homes.
- Reconfigure stdout and stderr to UTF-8 before the script's first print.
- Refuse a target rather than read it when confinement, file type, or size
  cannot be established.
- Walk a precheck against the filled reference document before trusting it.

### Ask first

- Changing the `DA10` bound, its unit, or its derivation.
- Adding a gate identifier outside `DA1`–`DA10`, or retiring one.
- Editing any line of `docs/specs/architect-design-scope-templates/spec.md`
  other than its `Status` line.

### Never do

- Add a size figure to `references/decomposition-rubric.md`, or weaken
  `test_size_alone_never_justifies_a_split` to make room for one.
- Phrase a hybrid or judgment-only gate as a lint, or let text similarity
  decide `DA5`.
- Add a new `##` heading to either rubric.
- Add a new top-level directory, a new pack primitive, or a new dependency.
- Import `agentbundle` from a shipped pack script, conditionally or otherwise.
- Edit inside the `agentbundle:output-rendering`, `knowledge-provider-handoff`
  or `scope-determination` marker spans.

## Testing Strategy

Each group below maps to one `###` subsection of the criteria, with two stated
exceptions: the changelog criterion is split out of `Release closure` because
its mode differs from its siblings', and the final bullet declares a mode for
the built artifact rather than for a criterion.

- **The shipped mechanical gate (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005,
  AC-0006, AC-0007): TDD.** An exit code is the whole interface a CI caller
  sees, and exit-code precedence across a multi-target run is the part a
  single-target test never reaches.
- **What the gate refuses to read (AC-0008, AC-0009, AC-0010, AC-0011,
  AC-0012, AC-0013, AC-0014, AC-0015, AC-0016): TDD, except AC-0016.** Each
  refusal is driven by a real filesystem entry and asserts the refusal
  *reason*, not only the exit code: a refusal asserted on the exit code alone
  passes when a different criterion's check fired instead. AC-0013 states
  which entry kinds are exercised and which share the predicate untested.
  AC-0015 is a static property of the pattern — an elapsed-time bound on a
  shared runner is a flake. AC-0016 is a text assertion.
- **`DA3` — paragraph budget (AC-0017, AC-0018, AC-0019, AC-0020, AC-0021,
  AC-0022): TDD.** A compressible invariant over text, its budget pinned on
  both sides, shown red on a non-compliant fixture before it is trusted.
- **`DA10` — size trigger (AC-0023, AC-0024, AC-0025, AC-0026, AC-0027): TDD
  for the count, goal-based for the text.** AC-0025 is what gives AC-0024 an
  oracle: the derivation is compared against the reference document's measured
  word count, not against its own multiplication, which is true by
  construction whatever the inventory omits.
- **The ten gates in three homes (AC-0028, AC-0029, AC-0030, AC-0031,
  AC-0032, AC-0033, AC-0034): goal-based check.** A set comparison across
  three files against the severity map fixed in AC-0032, so parity has a value
  to agree *to*.
- **The prechecks (AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040,
  AC-0041, AC-0042, AC-0043, AC-0047): goal-based check; (AC-0044, AC-0045,
  AC-0046, AC-0048, AC-0049): visual / manual QA.** Whether a hybrid states a
  precheck is decidable from its section body in each home, and AC-0047 pins
  the count that keeps `DA5` distinct. Whether a precheck *fires* is not
  decidable mechanically, so the seven are walked by hand twice — against the
  clean reference document, where none may fire, and against the defect
  document, where each must. One direction alone is satisfied by a precheck
  that never fires on anything.
- **How the reviewer reports the gates (AC-0050, AC-0051, AC-0052, AC-0053,
  AC-0055, AC-0056): goal-based check; (AC-0054): visual / manual QA.**
  AC-0050 through AC-0053, AC-0055 and AC-0056 are obligations written into
  `design-reviewer.md` and `convergence-loop.md`, decidable from those files.
  AC-0054 is the one that watches the agent obey them, and it is manual
  because the agent is a model: a dispatch is read, not asserted.
- **Parity (AC-0057, AC-0058): goal-based check.** The gates get a
  `DA_CARRIERS` constant of their own; the module's existing `CARRIERS` names
  a set that overlaps the gate homes in one file.
- **Reporting (AC-0059, AC-0060, AC-0061, AC-0062): goal-based check.**
  Whether the loop demands a per-identifier verdict is decidable from the
  instruction text, which is the artifact a model reads.
- **Release closure (AC-0063, AC-0065, AC-0066): goal-based check.** Version
  equality is owned by `tests/conformance/test_pack_metadata.py`, the eval's
  expectation by a closed-set assertion over its text, and
  `.claude-plugin/marketplace.json` by regeneration.
- **The changelog entry (AC-0064): goal-based check.**
  `.github/workflows/build-check.yml:357` runs
  `tools/test_build_site_routing.py`, which carries
  `test_the_real_changelog_has_no_silently_withheld_highlights` (`:2156`),
  `test_every_changelog_section_is_separated` (`:2268`) and
  `test_no_projected_release_heading_lives_under_an_unreleased_region`
  (`:2332`) over the real file. Between them they decide the `### Highlights`
  child, the heading separation and the `[Unreleased]` nesting.
- **The gate script as an invoked artifact: visual / manual QA.** The script
  is a CLI an adopter runs, so it is typed at the repository root against a
  non-compliant fixture and against the shipped templates, and both runs'
  stdout, stderr and exit codes go to `notes/verification-ledger.md`.

## Acceptance Criteria

### The shipped mechanical gate

- [ ] **AC-0001.** `packs/architect/.apm/skills/architect-design/scripts/check_document_architecture.py`
      implements `DA3` and `DA10`.
- [ ] **AC-0002.** The script imports only the Python standard library. It
      does not import `agentbundle`, conditionally or otherwise.
- [ ] **AC-0003.** The script reconfigures `sys.stdout` and `sys.stderr` to
      UTF-8 before its first write to either.
- [ ] **AC-0004.** The script exits 0 when it reports no finding, 1 when it
      reports at least one, and 2 when it refuses a target.
- [ ] **AC-0005.** A refusal anywhere in a run dominates a finding: a run that
      both refuses one target and reports a finding on another exits 2.
- [ ] **AC-0006.** A refused target does not stop the run; every remaining
      target is still read, and the report states how many targets were
      refused.
- [ ] **AC-0007.** A refusal writes the refused path and the reason to stderr.

### What the gate refuses to read

- [ ] **AC-0008.** `--root` is required; the script does not infer a
      confinement boundary from the working directory.
- [ ] **AC-0009.** The root is canonicalized before any prefix comparison, so
      both sides of the comparison are real paths.
- [ ] **AC-0010.** A regular file reached through a symlinked parent
      directory, whose real path is not under the canonicalized root, is
      refused, and the refusal names the out-of-root reason rather than a
      file-type reason.
- [ ] **AC-0011.** A target that is not a confined regular file is refused:
      the check is `stat.S_ISREG` on the resolved path plus a hard-link count
      of one, so every other entry kind fails it. Four kinds are exercised
      directly, being the four a test on Linux and macOS can build — a
      directory, a FIFO, a symbolic link, and a file with a second hard link.
      A character device, a block device and a socket are covered by the same
      predicate and not exercised; an NTFS reparse point is unbuildable on
      either runner and is not claimed.
- [ ] **AC-0012.** A target larger than 1,048,576 bytes is refused, and its
      size is checked before it is read. The bound is
      `architect-assess/scripts/profile_repo.py`'s `DEFAULT_MAX_FILE_BYTES`;
      a document at `DA10`'s bound is roughly 16,000 bytes, so the budget is
      about 65 times the largest document the gate expects.
- [ ] **AC-0013.** Every failure to resolve or read a target produces a
      refusal and never an uncaught exception. A symbolic-link loop, which
      raises `RuntimeError` rather than `OSError`, a permission error, and a
      non-prefix result are each covered.
- [ ] **AC-0014.** `DA3`'s sentence-matching pattern contains no nested
      quantifier and no alternation inside a repetition, the two constructs
      that make backtracking super-linear.
- [ ] **AC-0015.** A path the script emits, on the finding path and on the
      refusal path alike, is rendered with control characters, newlines and
      escape sequences escaped, and one finding occupies one output line, so a
      path cannot forge a finding line or rewrite a reader's terminal.
- [ ] **AC-0016.** `architect-design/SKILL.md` states that the agent running
      the skill does not invoke the gate script, and that the script is run by
      a human author or an adopter's CI.

### DA3 — paragraph budget

- [ ] **AC-0017.** `DA3` reports a prose paragraph carrying more than three
      sentences.
- [ ] **AC-0018.** `DA3` reports no finding in any `*.md` under
      `packs/architect/.apm/skills/architect-design/assets/`. The budget
      applies to every asset there, including `concept.md` and the
      `design-doc.md` compatibility pointer: a prose paragraph is a prose
      paragraph whatever the document routes to, so the glob carries no
      exclusion.
- [ ] **AC-0019.** `DA3` treats none of these as prose: YAML frontmatter, a
      fenced code block, an HTML-comment span, a Markdown table row, a list
      item, a block quote, an ATX heading.
- [ ] **AC-0020.** `DA3` counts a sentence boundary across `e.g.`, `i.e.`,
      `etc.`, `vs.` and a decimal number without splitting at their periods.
- [ ] **AC-0021.** A heading on the line immediately above wrapped prose
      yields one prose paragraph holding the prose alone.
- [ ] **AC-0022.** `DA3` reports the file, the line the paragraph starts on,
      and the sentence count it counted.

### DA10 — size trigger

- [ ] **AC-0023.** `DA10` reports a document whose word count exceeds the
      bound stated in AC-0024 and reports nothing at the bound or below.
      Words are counted over the document with YAML frontmatter and
      HTML-comment spans removed.
- [ ] **AC-0024.** The derivation that produces the bound is stated where
      `DA10` is defined, and its arithmetic reaches the bound: 752 words of
      scaffolding the subsystem template hands a filled document verbatim,
      9 model tables at 5 rows of 12 words, 4 diagrams at 40 words of labels,
      and 11 sections at 3 sentences of 22 words — 2,178 words at intended
      density — multiplied by a headroom factor of 1.5 and rounded to the
      nearest hundred, giving a bound of **3,300 words**. The scaffolding
      figure is measured:
      the template's word count after frontmatter, HTML comments and every
      `<…>` placeholder are removed, counting only tokens carrying an
      alphanumeric character. All eleven sections get a body allocation,
      including the three no rationale marker covers.
- [ ] **AC-0025.** The reference document's own measured word count sits
      within 20% of the derivation's 2,178-word density figure. Recomputing
      the stated multiplication proves only that its author can multiply.
- [ ] **AC-0026.** `DA10`'s definition states that a document over the bound is
      walked against `references/decomposition-rubric.md`, and that `DA10`
      decides no split itself.
- [ ] **AC-0027.** `DA10`'s definition states that a document over the bound
      whose children meet no criterion moves detail to companion views and
      evidence links.

### The ten gates in three homes

- [ ] **AC-0028.** `architect-design/references/design-doc-rubric.md` carries
      every identifier `DA1` through `DA10`, each with a severity.
- [ ] **AC-0029.** `architect-review/references/rubric-design-doc.md` carries
      every identifier `DA1` through `DA10`, each with a severity.
- [ ] **AC-0030.** `.apm/agents/design-reviewer.md` carries every identifier
      `DA1` through `DA10`, each with a severity.
- [ ] **AC-0031.** Each of `DA1`, `DA2`, `DA4`, `DA5`, `DA6`, `DA7`, `DA8` and
      `DA9` carries the 🧭 judgment tag in all three homes, and each of `DA3`
      and `DA10` carries the 🔧 mechanical tag in all three homes.
- [ ] **AC-0032.** Each gate carries this severity in all three homes:
      🟥 `DA5` and `DA8`; 🟧 `DA2`, `DA4`, `DA7` and `DA10`; 🟨 `DA1`, `DA3`,
      `DA6` and `DA9`.
- [ ] **AC-0033.** `design-doc-rubric.md` states what a severity means for an
      author: it orders the fixes made before a draft is shown, in the same
      vocabulary the reviewer will apply to it, so an author and a reviewer
      never disagree about which failure matters more.
- [ ] **AC-0034.** `DA5`'s definition in all three homes states that its
      verdict is the reviewer's judgement and that no automated measure decides
      it. The tokens `similarity score` and `distance metric` are absent from
      it as a supporting tripwire. `overlap` is not on that list: it is the
      plainest word for the defect `DA5` names. The obligation rests on the
      positive statement, because a prohibition over an open set of measure
      names never completes.

### The prechecks the hybrids carry

Each criterion in this group holds in all three homes named in the group
above. A precheck present only in the authoring rubric would leave the two
homes a reviewer reads unable to tell a hybrid from judgment-only `DA5`, which
is the one distinction ADR-0118 fixes and the 🧭 tag alone cannot carry.

- [ ] **AC-0035.** `DA6`'s precheck rejects a `Revision History` or
      `Decision Log` heading in the document body.
- [ ] **AC-0036.** `DA7` carries its identifier, severity and tag on the
      authoring rubric's existing checklist item — every diagram states one
      named question and one zoom level — and states no second, differently
      worded obligation beside it.
- [ ] **AC-0037.** `DA8`'s precheck requires every implementation-mapping row
      to resolve to an element the document's models name.
- [ ] **AC-0038.** `DA1`'s precheck rejects a future-tense or prior-state
      construction in the document body — `will be`, `previously`, `used to`,
      or a deprecation date.
- [ ] **AC-0039.** `DA2`'s precheck rejects a cross-reference that names no
      target, against the closed list `see above`, `see below`, `as described
      above`, `as described below`, `the previous section`, `the following
      section`, `the table below` and `the diagram above`. A reference that
      names what it points at — `the structural model above` — is not a
      finding, which is why the list is closed rather than a search for
      `above`: the templates' fixed opening question for Implementation
      Mapping contains `the model above`.
- [ ] **AC-0040.** `DA4`'s precheck requires the first block after a modelled
      section's opening question to be a table or a fenced diagram, not prose.
- [ ] **AC-0041.** `DA9`'s precheck rejects a body heading that accumulates
      evidence rather than linking it — `Appendix`, `References`, `Evidence`.
- [ ] **AC-0042.** Each of the seven prechecks states that its verdict is the
      reviewer's.
- [ ] **AC-0043.** The reference document's corpus purpose governs an edit
      to it. It is a baseline, so any change to its content obliges a re-walk
      of the seven prechecks and a fresh record; a design improvement that
      nobody re-walks silently invalidates AC-0045.
- [ ] **AC-0044.** A reference document exists at
      `packs/architect/tests/skills/architect-design/testdata/telemetry-endpoint-default-design.md`,
      authored from `assets/subsystem-design.md` and carrying the subsystem
      design for the layer-5 enterprise telemetry endpoint default that
      `docs/product/intents/catalogue-level-telemetry-endpoint-default.md`
      frames. It holds no `<…>` placeholder token.
- [ ] **AC-0045.** No precheck fires on that reference document, and each of
      the seven is walked against it with the walk recorded.
- [ ] **AC-0046.** The precheck corpus excludes `assets/*.md`, and each
      precheck's text states that it applies to an authored document rather
      than to a template. A template's unfilled placeholder —
      `<this diagram's zoom level>`, `<element from section 2>` — is the slot
      the precheck asks an author to fill. `DA9` is the worked case: its
      `Appendix` trigger does not reach `assets/design-doc.md`, the unrouted
      compatibility pointer carrying `## Appendix (optional)`.
- [ ] **AC-0047.** Exactly seven prechecks exist, one per hybrid gate, and
      `DA5` carries none. The count is the pin: a precheck added to `DA5`
      erases the only textual difference between judgment-only and hybrid.
- [ ] **AC-0048.** A defect document exists at
      `packs/architect/tests/skills/architect-design/testdata/precheck-defects.md`,
      carrying one planted defect per precheck.
- [ ] **AC-0049.** Each of the seven prechecks fires on its planted defect,
      and the walk is recorded. A precheck checked only against a clean
      document is satisfied by one that never fires on anything.

### How the reviewer reports the gates

- [ ] **AC-0050.** `.apm/agents/design-reviewer.md` requires its returned
      block to carry a gate roll-call — every identifier `DA1` through `DA10`
      with a verdict, inside the block rather than before it — **when the
      artifact under review is a design document**. The agent also reviews
      assessment reports, RFCs, ADRs and four diagram genres, and a
      document-architecture roll-call on an ER diagram is noise.
- [ ] **AC-0051.** `.apm/agents/design-reviewer.md` requires a clean
      design-document review to state ten verdicts, so a gate nobody
      considered and a gate that passed stop looking identical.
- [ ] **AC-0052.** `.apm/agents/design-reviewer.md` states that its inlined
      gate set is its baseline depth, that it reads
      `architect-review/references/rubric-design-doc.md` for the fuller
      per-gate text when that skill is co-installed, and that it degrades only
      in depth, never to nothing.
- [ ] **AC-0053.** `.apm/agents/design-reviewer.md` requires the agent to
      raise an unreachable `rubric-design-doc.md` as a finding on a
      design-document review, rather than reviewing quietly at baseline.
- [ ] **AC-0054.** The roll-call contract is exercised, not only asserted:
      `design-reviewer` is dispatched against the reference document and its
      returned block recorded in `notes/verification-ledger.md`, showing ten
      verdicts. The record names the scope the dispatch resolved the agent
      from, because an in-repo install makes the agent available to every
      contributor and to CI, while a user-scope install makes it available to
      one operator.
- [ ] **AC-0055.** `references/convergence-loop.md` requires the loop to
      dispatch the `design-reviewer` subagent when it is reachable, and to
      name the rung it fell back to when it is not.
- [ ] **AC-0056.** Each reporting obligation names who reports: step 6 is the
      author's own self-check, and the review pass is whichever rung
      `convergence-loop.md` resolved. No rung runs the gate script — AC-0016
      keeps the agent from invoking it and AC-0061 keeps the loop from
      invoking it — so every rung counts sentences and words by reading.

### Parity

- [ ] **AC-0057.** `packs/architect/tests/pack/test_design_reviewer_rubric_parity.py`
      asserts every identifier `DA1` through `DA10` appears in all three homes.
- [ ] **AC-0058.** The same test asserts each gate's severity agrees across the
      three homes, and permits the explanatory prose to differ.

### Reporting

- [ ] **AC-0059.** `architect-design/SKILL.md` step 6 requires every gate
      result to be reported by identifier and verdict before a draft is shown.
- [ ] **AC-0060.** `references/convergence-loop.md` requires each review pass
      to report every gate identifier with a verdict.
- [ ] **AC-0061.** `references/convergence-loop.md` states that the loop
      requires and invokes no script, and names the shipped gate script as a
      human- or CI-run accelerant outside the loop, in the same words AC-0016
      requires of `SKILL.md`.
- [ ] **AC-0062.** `references/convergence-loop.md` states which property the
      shipped script does and does not cost — the loop stays pure-prose and
      zero-config, and the script is optional and run outside the loop — and
      carries no unconditional claim that shipping a script forfeits a pack
      property.

### Release closure

- [ ] **AC-0063.** `packs/architect/pack.toml` declares version `0.15.12`.
      Its equality with `.claude-plugin/plugin.json` is owned by
      `tests/conformance/test_pack_metadata.py`.
- [ ] **AC-0064.** `docs/product/changelog.md` carries a
      `## [architect][0.15.12] — <YYYY-MM-DD>` entry, dated in that exact
      form, free-standing at `##`, directly beneath `[Unreleased]` and newest
      first, with a `### Highlights` subsection as its immediate child. The
      date is not decoration: `/now/` eligibility is versioned and dated, so
      an undated heading never publishes.
- [ ] **AC-0065.** `packs/architect/.apm/skills/architect-design/evals/evals.json`
      carries an eval whose expectation requires the response to name every
      identifier `DA1` through `DA10` with a verdict.
- [ ] **AC-0066.** `.claude-plugin/marketplace.json` is regenerated by
      `FORCE=1 make build-self` and records architect at `0.15.12`.

## Follow-ons

- architect pack maintainer: the `metadata.boundaries` vocabulary in
  `docs/architecture/security.md` has no value for a skill that ships an
  executable, and its capability table maps `Bash` only to `network_egress`
  and `deploy_action`. `architect-assess` already ships `profile_repo.py`
  under the same three boundaries. Adding an execution value, or recording
  that shipped scripts sit outside that convention, is a separate change.
- architect pack maintainer: the two interim rubric items in
  `docs/specs/architect-design-scope-templates/spec.md` — AC-0026
  (implementation sufficiency) and AC-0027 (diagram question) — are not
  superseded by this slice. `DA7` and `DA8` attach an identifier, a severity
  and a tag to the very checklist items those criteria describe, leaving both
  obligations true word for word, so no part exists for a `Status`-line
  pointer to name. Moving authority over them to the gate identifiers is a
  governance change on a frozen peer spec and belongs in its own change.
- architect pack maintainer: `packs/architect/tests/skills/architect-design/`
  reaching pull requests landed in commit `81663a467` on this branch —
  `build-check.yml:435` and the matching `PR_GATED` roster entry at
  `tools/lint-ci-parity.py:878-882`. It is a precondition every task here
  rests on, not an obligation of this contract, and no criterion claims it.
- AgentBundle distribution maintainers: the reference document this delivery
  writes is a design for the layer-5 enterprise telemetry endpoint default,
  and it lands as the gates' corpus rather than as an accepted design. Whether
  that design is adopted, reshaped, or dropped belongs to
  `docs/product/intents/catalogue-level-telemetry-endpoint-default.md` and to
  the owner it names, jointly with `credential-pack-defaults-projection`.
- architect pack maintainer: slice 3, tracked by ADR-0118 — the system-shape
  and workload axes and the conditional ports-and-adapters view.
- architect pack maintainer: `packs/architect/tests/skills/architect-review/`
  and `.../architect-diagram/` reach CI only through the dispatch-only
  `test-corpus.yml`. Their `tools/lint-ci-parity.py` dispositions are accurate.

## Assumptions

- Technical: one design document authored by this skill exists after this
  delivery — the telemetry endpoint-default reference — so the prechecks'
  false-positive rate rests on a single document written by the same delivery
  that wrote them, and stays ungrounded against output another author
  produced.
- Product: whether an adopter runs the gate script at all is unknown — the
  pack ships no telemetry, so `DA3` and `DA10`'s value to an adopter rests on
  the reviewer checks they back rather than on observed script use.
