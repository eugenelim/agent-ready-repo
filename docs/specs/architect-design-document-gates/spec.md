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

An architect using `architect-design` gets a draft whose document architecture
is decided by ten named gates rather than left to whoever is reading. Success
is that a review pass reports every gate by identifier and verdict, so a gate
that did not fire is visible instead of absent.

## What Changes

- `DA3` paragraph budget and `DA10` size trigger — one script at
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
- Edit inside the `agentbundle:output-rendering`, `knowledge-provider-handoff`
  or `scope-determination` marker spans.

## Testing Strategy

Each group is one `###` subsection of the criteria below, so the two lists
cannot drift apart.

- **Pull-request gating (AC-0001, AC-0002): goal-based check.**
  `python3 tools/lint-ci-parity.py` decides it in both directions — it fails
  when a step covers a suite whose roster entry denies a gate, and fails when
  a disposition names no real step.
- **The shipped mechanical gate (AC-0003, AC-0004, AC-0005, AC-0006, AC-0007,
  AC-0008, AC-0009): TDD.** An exit code is the whole interface a CI caller
  sees, and exit-code precedence across a multi-target run is the part a
  single-target test never reaches.
- **What the gate refuses to read (AC-0010, AC-0011, AC-0012, AC-0013,
  AC-0014, AC-0015, AC-0016, AC-0017, AC-0018): TDD, except AC-0018.** Each
  refusal is driven by a real filesystem entry and asserts the refusal
  *reason*, not only the exit code: a refusal asserted on the exit code alone
  passes when a different criterion's check fired instead. AC-0016 is a static
  property of the pattern — an elapsed-time bound on a shared runner is a
  flake. AC-0018 is a text assertion.
- **`DA3` — paragraph budget (AC-0019, AC-0020, AC-0021, AC-0022, AC-0023,
  AC-0024): TDD.** A compressible invariant over text, its budget pinned on
  both sides, shown red on a non-compliant fixture before it is trusted.
- **`DA10` — size trigger (AC-0025, AC-0026, AC-0027, AC-0028): TDD for the
  count, goal-based for the text.** AC-0026 has an oracle rather than a
  presence check: the test recomputes the stated arithmetic and requires it to
  reach the stated bound, so a derivation that does not add up fails with
  every figure present.
- **The ten gates in three homes (AC-0029, AC-0030, AC-0031, AC-0032,
  AC-0033, AC-0034, AC-0035): goal-based check.** A set comparison across
  three files against the severity map fixed in AC-0033, so parity has a value
  to agree *to*.
- **The prechecks (AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041,
  AC-0042, AC-0043, AC-0046, AC-0047): goal-based check; (AC-0044, AC-0045):
  visual / manual QA.** Whether a hybrid states a precheck is decidable from
  its section body in each home. Whether a precheck *fires* is not — a
  precheck is executed by a reader — so the seven are walked by hand against
  the filled reference document and the walk recorded in
  `notes/verification-ledger.md`. The corpus is that document rather than the
  shipped templates, which measure their own placeholders.
- **Parity (AC-0048, AC-0049): goal-based check.** The gates get a
  `DA_CARRIERS` constant of their own; the module's existing `CARRIERS` names
  a set that overlaps the gate homes in one file.
- **Reporting (AC-0050, AC-0051, AC-0052, AC-0053): goal-based check.**
  Whether the loop demands a per-identifier verdict is decidable from the
  instruction text, which is the artifact a model reads.
- **Supersession (AC-0054, AC-0055): goal-based check for the token, visual /
  manual QA for the diff.** `lint-spec-status.py` decides the status
  vocabulary and nothing else. Whether the pointer names the right ADR and
  scopes the right part is a reviewer's call, which is why AC-0054 states the
  shape rather than the judgement.
- **Release closure (AC-0056, AC-0058, AC-0059): goal-based check.** Version
  equality is owned by `tests/conformance/test_pack_metadata.py`, the eval's
  expectation by a closed-set assertion over its text, and
  `.claude-plugin/marketplace.json` by regeneration.
- **The changelog entry (AC-0057): visual / manual QA.** No pull-request gate
  checks it. `build-check.yml` names changelog nothing at all, and
  `pages.yml`'s release-anchor job compares anchors against built HTML, so it
  cannot see position, nesting, or a `### Highlights` subsection.
- **The gate script as an invoked artifact: visual / manual QA.** The script
  is a CLI an adopter runs, so it is typed at the repository root against a
  non-compliant fixture and against the shipped templates, and both runs'
  stdout, stderr and exit codes go to `notes/verification-ledger.md`.

## Acceptance Criteria

### Pull-request gating

- [ ] **AC-0001.** `.github/workflows/build-check.yml` runs
      `packs/architect/tests/skills/architect-design/` inside its
      `pytest catalogue-test carve-out destinations (RFC-0082)` step.
- [ ] **AC-0002.** `tools/lint-ci-parity.py` records that suite as `PR_GATED`
      naming that step, and the lint exits 0.

### The shipped mechanical gate

- [ ] **AC-0003.** `packs/architect/.apm/skills/architect-design/scripts/check_document_architecture.py`
      implements `DA3` and `DA10`.
- [ ] **AC-0004.** The script runs on the Python standard library alone, and
      uses `agentbundle.catalogue_tooling.file_safety` in addition when that
      import succeeds.
- [ ] **AC-0005.** The script reconfigures `sys.stdout` and `sys.stderr` to
      UTF-8 before its first write to either.
- [ ] **AC-0006.** The script exits 0 when it reports no finding, 1 when it
      reports at least one, and 2 when it refuses a target.
- [ ] **AC-0007.** A refusal anywhere in a run dominates a finding: a run that
      both refuses one target and reports a finding on another exits 2.
- [ ] **AC-0008.** A refused target does not stop the run; every remaining
      target is still read, and the report states how many targets were
      refused.
- [ ] **AC-0009.** A refusal writes the refused path and the reason to stderr.

### What the gate refuses to read

- [ ] **AC-0010.** `--root` is required; the script does not infer a
      confinement boundary from the working directory.
- [ ] **AC-0011.** The root is canonicalized before any prefix comparison, so
      both sides of the comparison are real paths.
- [ ] **AC-0012.** A regular file reached through a symlinked parent
      directory, whose real path is not under the canonicalized root, is
      refused, and the refusal names the out-of-root reason rather than a
      file-type reason.
- [ ] **AC-0013.** A target that is not a regular file is refused. A
      directory, a FIFO, a character or block device, a socket, a symbolic
      link, a reparse point, and a file with more than one hard link are each
      refused rather than opened.
- [ ] **AC-0014.** A target larger than 1,048,576 bytes is refused, and its
      size is checked before it is read. The bound is
      `architect-assess/scripts/profile_repo.py`'s `DEFAULT_MAX_FILE_BYTES`;
      a document at `DA10`'s bound is roughly 16,000 bytes, so the budget is
      about 65 times the largest document the gate expects.
- [ ] **AC-0015.** Every failure to resolve or read a target produces a
      refusal and never an uncaught exception. A symbolic-link loop, which
      raises `RuntimeError` rather than `OSError`, a permission error, and a
      non-prefix result are each covered.
- [ ] **AC-0016.** `DA3`'s sentence-matching pattern contains no nested
      quantifier and no alternation inside a repetition, the two constructs
      that make backtracking super-linear.
- [ ] **AC-0017.** A path the script emits, on the finding path and on the
      refusal path alike, is rendered with control characters, newlines and
      escape sequences escaped, and one finding occupies one output line, so a
      path cannot forge a finding line or rewrite a reader's terminal.
- [ ] **AC-0018.** `architect-design/SKILL.md` states that the agent running
      the skill does not invoke the gate script, and that the script is run by
      a human author or an adopter's CI.

### DA3 — paragraph budget

- [ ] **AC-0019.** `DA3` reports a prose paragraph carrying more than three
      sentences.
- [ ] **AC-0020.** `DA3` reports no finding in any `*.md` under
      `packs/architect/.apm/skills/architect-design/assets/`. The budget
      applies to every asset there, including `concept.md` and the
      `design-doc.md` compatibility pointer: a prose paragraph is a prose
      paragraph whatever the document routes to, so the glob carries no
      exclusion.
- [ ] **AC-0021.** `DA3` treats none of these as prose: YAML frontmatter, a
      fenced code block, an HTML-comment span, a Markdown table row, a list
      item, a block quote, an ATX heading.
- [ ] **AC-0022.** `DA3` counts a sentence boundary across `e.g.`, `i.e.`,
      `etc.`, `vs.` and a decimal number without splitting at their periods.
- [ ] **AC-0023.** A heading on the line immediately above wrapped prose
      yields one prose paragraph holding the prose alone.
- [ ] **AC-0024.** `DA3` reports the file, the line the paragraph starts on,
      and the sentence count it counted.

### DA10 — size trigger

- [ ] **AC-0025.** `DA10` reports a document whose word count exceeds the
      bound stated in AC-0026 and reports nothing at the bound or below. Words are counted over the
      document with YAML frontmatter and HTML-comment spans removed.
- [ ] **AC-0026.** The derivation that produces the bound is stated where
      `DA10` is defined, and its arithmetic reaches the bound: the subsystem
      template's 9 model tables at 5 rows of 12 words, 4 diagrams at 40 words
      of labels, 8 rationale blocks at 3 sentences of 22 words, 11 opening
      questions at 20 words, and 120 words of header and goal bullets — 1,568
      words at intended density — multiplied by a headroom factor of 1.5 and
      rounded to the nearest hundred. Each figure is stated, because a
      derivation whose density and multiplier are unrecorded is satisfied by
      any arithmetic.
- [ ] **AC-0027.** `DA10`'s definition states that a document over the bound is
      walked against `references/decomposition-rubric.md`, and that `DA10`
      decides no split itself.
- [ ] **AC-0028.** `DA10`'s definition states that a document over the bound
      whose children meet no criterion moves detail to companion views and
      evidence links.

### The ten gates in three homes

- [ ] **AC-0029.** `architect-design/references/design-doc-rubric.md` carries
      every identifier `DA1` through `DA10`, each with a severity.
- [ ] **AC-0030.** `architect-review/references/rubric-design-doc.md` carries
      every identifier `DA1` through `DA10`, each with a severity.
- [ ] **AC-0031.** `.apm/agents/design-reviewer.md` carries every identifier
      `DA1` through `DA10`, each with a severity.
- [ ] **AC-0032.** Each of `DA1`, `DA2`, `DA4`, `DA5`, `DA6`, `DA7`, `DA8` and
      `DA9` carries the 🧭 judgment tag in all three homes, and each of `DA3`
      and `DA10` carries the 🔧 mechanical tag in all three homes.
- [ ] **AC-0033.** Each gate carries this severity in all three homes:
      🟥 `DA5` and `DA8`; 🟧 `DA2`, `DA4`, `DA7` and `DA10`; 🟨 `DA1`, `DA3`,
      `DA6` and `DA9`.
- [ ] **AC-0034.** `design-doc-rubric.md` states what a severity means for an
      author: it orders the fixes made before a draft is shown, in the same
      vocabulary the reviewer will apply to it, so an author and a reviewer
      never disagree about which failure matters more.
- [ ] **AC-0035.** `DA5`'s definition in all three homes states that its
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

- [ ] **AC-0036.** `DA6`'s precheck rejects a `Revision History` or
      `Decision Log` heading in the document body.
- [ ] **AC-0037.** `DA7` carries its identifier, severity and tag on the
      authoring rubric's existing checklist item — every diagram states one
      named question and one zoom level — and states no second, differently
      worded obligation beside it.
- [ ] **AC-0038.** `DA8`'s precheck requires every implementation-mapping row
      to resolve to an element the document's models name.
- [ ] **AC-0039.** `DA1`'s precheck rejects a future-tense or prior-state
      construction in the document body — `will be`, `previously`, `used to`,
      or a deprecation date.
- [ ] **AC-0040.** `DA2`'s precheck rejects a cross-reference that names no
      target, against the closed list `see above`, `see below`, `as described
      above`, `as described below`, `the previous section`, `the following
      section`, `the table below` and `the diagram above`. A reference that
      names what it points at — `the structural model above` — is not a
      finding, which is why the list is closed rather than a search for
      `above`: the templates' fixed opening question for Implementation
      Mapping contains `the model above`.
- [ ] **AC-0041.** `DA4`'s precheck requires the first block after a modelled
      section's opening question to be a table or a fenced diagram, not prose.
- [ ] **AC-0042.** `DA9`'s precheck rejects a body heading that accumulates
      evidence rather than linking it — `Appendix`, `References`, `Evidence`.
- [ ] **AC-0043.** Each of the seven prechecks states that its verdict is the
      reviewer's.
- [ ] **AC-0044.** A filled reference document, authored from
      `assets/subsystem-design.md` with every placeholder replaced by real
      content, exists at
      `packs/architect/tests/skills/architect-design/testdata/filled-subsystem-design.md`.
- [ ] **AC-0045.** No precheck fires on that reference document, and each of
      the seven is walked against it with the walk recorded.
- [ ] **AC-0046.** The precheck corpus excludes `assets/*.md`, and each
      precheck's text states that it applies to an authored document rather
      than to a template. A template's unfilled placeholder —
      `<this diagram's zoom level>`, `<element from section 2>` — is the slot
      the precheck asks an author to fill.
- [ ] **AC-0047.** `DA9` is scoped to a routed document, so its `Appendix`
      trigger does not reach `assets/design-doc.md`, the unrouted
      compatibility pointer that carries `## Appendix (optional)`.

### Parity

- [ ] **AC-0048.** `packs/architect/tests/pack/test_design_reviewer_rubric_parity.py`
      asserts every identifier `DA1` through `DA10` appears in all three homes.
- [ ] **AC-0049.** The same test asserts each gate's severity agrees across the
      three homes, and permits the explanatory prose to differ.

### Reporting

- [ ] **AC-0050.** `architect-design/SKILL.md` step 6 requires every gate
      result to be reported by identifier and verdict before a draft is shown.
- [ ] **AC-0051.** `references/convergence-loop.md` requires each review pass
      to report every gate identifier with a verdict.
- [ ] **AC-0052.** `references/convergence-loop.md` states that the loop
      requires and invokes no script, and names the shipped gate script as a
      human- or CI-run accelerant outside the loop, in the same words AC-0018
      requires of `SKILL.md`.
- [ ] **AC-0053.** `references/convergence-loop.md` states which property the
      shipped script does and does not cost — the loop stays pure-prose and
      zero-config, and the script is optional and run outside the loop — and
      carries no unconditional claim that shipping a script forfeits a pack
      property.

### Supersession

- [ ] **AC-0054.** `docs/specs/architect-design-scope-templates/spec.md`
      carries a `Status`-line supersession pointer naming ADR-0118 and the part
      superseded.
- [ ] **AC-0055.** This change alters no line of
      `docs/specs/architect-design-scope-templates/spec.md` except its
      `Status` line, and the one-line pull-request diff for that file is
      recorded.

### Release closure

- [ ] **AC-0056.** `packs/architect/pack.toml` declares version `0.15.12`.
      Its equality with `.claude-plugin/plugin.json` is owned by
      `tests/conformance/test_pack_metadata.py`.
- [ ] **AC-0057.** `docs/product/changelog.md` carries a free-standing
      `## [architect][0.15.12] — <YYYY-MM-DD>` entry, dated in that exact
      form, with a `### Highlights` subsection. The date is not decoration:
      `/now/` eligibility is versioned and dated, so an undated heading never
      publishes.
- [ ] **AC-0058.** `packs/architect/.apm/skills/architect-design/evals/evals.json`
      carries an eval whose expectation requires the response to name every
      identifier `DA1` through `DA10` with a verdict.
- [ ] **AC-0059.** `.claude-plugin/marketplace.json` is regenerated by
      `FORCE=1 make build-self` and records architect at `0.15.12`.

## Follow-ons

## Follow-ons

- architect pack maintainer: the `metadata.boundaries` vocabulary in
  `docs/architecture/security.md` has no value for a skill that ships an
  executable, and its capability table maps `Bash` only to `network_egress`
  and `deploy_action`. `architect-assess` already ships `profile_repo.py`
  under the same three boundaries. Adding an execution value, or recording
  that shipped scripts sit outside that convention, is a separate change.
- architect pack maintainer: slice 3, tracked by ADR-0118 — the system-shape
  and workload axes and the conditional ports-and-adapters view.
- architect pack maintainer: `packs/architect/tests/skills/architect-review/`
  and `.../architect-diagram/` reach CI only through the dispatch-only
  `test-corpus.yml`. Their `tools/lint-ci-parity.py` dispositions are accurate.

## Assumptions

- Technical: no design document authored by this skill exists in the
  repository — the filled reference document this delivery writes is the only
  corpus the prechecks and `DA3` are measured against, so their false-positive
  rate against real authored output is ungrounded until the skill has produced
  some.
- Product: whether an adopter runs the gate script at all is unknown — the
  pack ships no telemetry, so `DA3` and `DA10`'s value to an adopter rests on
  the reviewer checks they back rather than on observed script use.
