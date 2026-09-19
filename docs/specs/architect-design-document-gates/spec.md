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

A design document that ignores the model-first templates is rejected rather
than converged as clean. Ten named gates `DA1`–`DA10` decide document
architecture — how the document is built, as distinct from what it says about
the system — and every review pass reports each one by identifier and verdict,
so a gate that did not fire is visible instead of silent.

## What Changes

- Two mechanical gates ship as one script inside the pack's runtime boundary —
  `packs/architect/.apm/skills/architect-design/scripts/check_document_architecture.py`,
  reachable by an adopter, not only by this repository
- `DA3` caps a prose paragraph at three sentences; `DA10` triggers the
  decomposition walk above 2,400 words
- The gate reads adopter-repository documents, which are untrusted content, so
  it takes a required `--root`, canonicalizes both sides of the boundary
  comparison, refuses anything that is not a confined regular file under
  1 MiB, and escapes what it prints
- Eight gates are reviewer checks — each of the seven hybrids `DA1`, `DA2`,
  `DA4`, `DA6`, `DA7`, `DA8` and `DA9` carries a structural precheck whose
  verdict is still the reviewer's, and `DA5` alone carries none, which is what
  keeps judgment-only textually distinct from hybrid
- Three rubric homes each carry the full gate set. The two rubrics take it
  under their existing `## Cross-cutting` heading rather than a new `##`
  heading of their own, because slice 1 pinned which `##` headings they may
  carry; `.apm/agents/design-reviewer.md` has no `## Cross-cutting` heading
  and no criterion pins its headings, so the gates take a section of their own
  there, beside its severity glossary
- Every gate carries a fixed severity, so an author's fix order and a
  reviewer's finding order come from one vocabulary
- `packs/architect/tests/pack/test_design_reviewer_rubric_parity.py` pins the
  ten identifiers and their severities across those three homes
- `SKILL.md` step 6 and `references/convergence-loop.md` report every gate
  result by identifier, and the loop's own contract stops contradicting a
  skill that ships scripts
- `packs/architect/tests/skills/architect-design/` runs on a pull request

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — the gate set and its mechanizability split are already decided | [`docs/adr/0118-architect-design-scope-routed-model-first-templates.md`](../../adr/0118-architect-design-scope-routed-model-first-templates.md) `D5` | architect pack maintainer | The record is Accepted and its `D5` table matches the shipped identifiers | The ten shipped gates and their mechanizability agree with `D5` |
| Release history | Applicable — the pack ships a version | [`docs/product/changelog.md`](../../product/changelog.md) | architect pack maintainer | A free-standing `## [architect][0.15.12]` entry with a `### Highlights` verdict | The entry exists, is not nested under `[Unreleased]`, and states its Highlights disposition |
| Maintainer procedure | Applicable — a reviewer and an author both walk the gates | The three rubric homes named in What Changes | architect pack maintainer | The parity test passes across all three | Every gate identifier and severity agrees in all three homes |
| Interface compatibility | Applicable — the two scripts are an adopter-reachable surface | The shipped script's `--help` and exit codes | architect pack maintainer | Exit 0 clean, 1 findings, 2 refusal, exercised by tests | The exit-code contract is tested, not only documented |
| Current product truth | Not applicable — no user-facing guide describes the design-doc rubric's internals; `guides/architect/` documents the journey, which does not change | — | — | — | — |
| Reusable learning | Applicable — the mechanizable/judgment split is the reusable lesson | `project-knowledge` at the work-loop's capture gates | implementing agent | A capture receipt or `project-knowledge unavailable` | Recorded either way |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- State a gate's rule directly in `packs/`; cite no ADR, RFC, or
  repository-only path from shipped pack content.
- Give every gate the same identifier and severity in all three rubric homes.
- Reconfigure stdout and stderr to UTF-8 before the script's first print.
- Tune a mechanical gate against every shipped asset in
  `architect-design/assets/` and show it green there before trusting it.
- Refuse a target rather than read it when confinement, file type, or size
  cannot be established; a zero-finding report on a file the gate never read
  is the failure the refusal exists to prevent.

### Ask first

- Changing the `DA10` bound, its unit, or its derivation.
- Adding a gate identifier outside `DA1`–`DA10`, or retiring one.
- Editing any acceptance criterion of
  `docs/specs/architect-design-scope-templates/spec.md` beyond its `Status`
  line.

### Never do

- Add a size figure to `references/decomposition-rubric.md`, or weaken
  `test_size_alone_never_justifies_a_split` to make room for one.
- Phrase a hybrid or judgment-only gate as a lint, or let text similarity
  decide `DA5`.
- Add a new top-level directory, a new pack primitive, or a new dependency.
  The script runs on the standard library alone; `agentbundle`'s blessed
  confinement helpers are used when importable and are never required.
- Edit inside the `agentbundle:output-rendering` markers in any `SKILL.md`, or
  inside the `knowledge-provider-handoff` or `scope-determination` marker spans.

## Testing Strategy

Each group below is one `###` subsection of the criteria, so the two lists
cannot drift apart.

- **Pull-request gating (AC-0001, AC-0002): goal-based check.**
  `python3 tools/lint-ci-parity.py` decides it in both directions — it fails
  when a step covers a suite whose roster entry denies a gate, and fails when
  a disposition names no real step.
- **The shipped mechanical gate (AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009): TDD.** An exit code is
  the whole interface a CI caller sees, and exit-code precedence across a
  multi-target run is the part a single-target test never reaches.
- **What the gate refuses to read (AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018): TDD, except AC-0018.**
  Each refusal is driven by a real filesystem entry built in the test — a
  regular file under a symlinked parent, a symlink loop, a FIFO, a
  hard-linked file, an oversize file — because a refusal asserted against a
  literal `..` string proves nothing about resolution, and each asserts the
  refusal *reason*, not only the exit code, or one criterion's case is
  silently swallowed by another's. AC-0016 is a static property of the
  pattern, not a timing measurement: an elapsed-time bound on a shared
  runner is a flake. AC-0018 is a goal-based text assertion, and it is the
  only thing standing between step 6's "report every gate" instruction and
  an agent deciding to execute the gate itself.
- **`DA3` — paragraph budget (AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024): TDD.** A compressible
  invariant over text with a boundary pinned on both sides, shown red on a
  deliberately non-compliant fixture before it is trusted — a gate observed
  only passing has not been tested.
- **`DA10` — size trigger (AC-0025, AC-0026, AC-0027, AC-0028): TDD for the count,
  goal-based for the text.** AC-0026 is the one with a real oracle rather
  than a presence check: the test recomputes the stated arithmetic and
  requires it to reach the stated bound, so a derivation that does not add up
  fails even though every figure is present.
- **The ten gates in three homes (AC-0029, AC-0030, AC-0031, AC-0032, AC-0033, AC-0034, AC-0035): goal-based check.** A
  set comparison across three files against the severity map fixed in
  AC-0033, so parity has a value to agree *to* rather than agreeing on
  whatever the implementer chose.
- **The prechecks (AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041, AC-0042, AC-0043, AC-0044, AC-0045, AC-0046): goal-based check for their text,
  visual / manual QA for AC-0044 and AC-0045.** Whether a hybrid states a
  precheck is decidable from its section body in each of the three homes.
  Whether a precheck *fires* is not — a precheck is executed by a reader —
  so the seven are walked by hand against the filled reference document and
  the walk recorded in `notes/verification-ledger.md`. The corpus is that
  document and not the shipped skeletons: walking a precheck against a
  template measures the template's unfilled placeholders, not the check.
- **Parity (AC-0047, AC-0048): goal-based check.** The `DA` gates get their
  own `DA_CARRIERS` constant; the module's existing `CARRIERS` names a
  different set that overlaps the gate homes in one file, so folding them
  together would assert the identifiers against two files that must not carry
  them and leave the authoring rubric unchecked.
- **Reporting (AC-0049, AC-0050, AC-0051, AC-0052): goal-based check.** Whether the loop
  demands a per-identifier verdict is decidable from the instruction text,
  which is the artifact a model reads.
- **Supersession (AC-0053, AC-0054): goal-based check for the token, visual /
  manual QA for the diff.** `lint-spec-status.py` decides the status
  vocabulary and nothing else. AC-0054 is read from the pull-request diff and
  recorded, not guarded by a standing test: that would need a `tests/roster/`
  module, a `build-check.yml` step, a `STEP_DISPOSITION` entry and a
  `.workspace-prune-protected.toml` entry, to protect a frozen document that
  by convention takes only a `Status`-line edit. That the pointer names the
  right ADR and scopes the right part stays a reviewer's call, which is why
  AC-0053 states the shape rather than the judgement.
- **Release closure (AC-0055, AC-0057, AC-0058): goal-based check.** Version
  equality is owned by `tests/conformance/test_pack_metadata.py`, the eval's
  expectation by a closed-set assertion over its text, and
  `.claude-plugin/marketplace.json` by regeneration rather than hand-edited
  bytes.
- **The changelog entry (AC-0056): visual / manual QA, with the gap stated.**
  No pull-request gate checks it. `build-check.yml` names changelog nothing
  at all, and `pages.yml`'s release-anchor job compares anchors against built
  HTML, so it cannot see position, nesting, or a `### Highlights` subsection.
  The check is a read of the file with the result recorded; calling it
  goal-based would attribute the criterion to a gate that does not exist.
- **The gate script as an invoked artifact: visual / manual QA, owned by T2.**
  The script is a CLI an adopter runs, so it is typed at the repository root
  twice — once against a non-compliant fixture, once against the shipped
  templates — and both runs' full stdout, stderr and exit codes are written
  to `notes/verification-ledger.md`. The session ends when both transcripts
  are in that file. A passing unit test does not show that the command works
  when typed, and a run nobody recorded is not evidence.

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
- [ ] **AC-0012.** A regular file reached through a symlinked **parent
      directory**, whose real path is not under the canonicalized root, is
      refused with the out-of-root reason. The target is a regular file on
      purpose: a symlinked target is already refused by AC-0013 for its file
      type, so a case built that way never reaches the prefix comparison and
      passes whether or not the comparison exists.
- [ ] **AC-0013.** A target that is not a regular file is refused. A
      directory, a FIFO, a character or block device, a socket, a symbolic
      link, a reparse point, and a file with more than one hard link are each
      refused rather than opened.
- [ ] **AC-0014.** A target larger than 1,048,576 bytes is refused, and the
      size is checked before the file is read. The bound is the byte budget
      the sibling skill already applies to one file
      (`architect-assess/scripts/profile_repo.py`'s `DEFAULT_MAX_FILE_BYTES`);
      a document at `DA10`'s 2,400-word bound is roughly 16,000 bytes, so the
      budget is about 65 times the largest document the gate expects and
      cannot fire on real content.
- [ ] **AC-0015.** Every failure to resolve or read a target produces a
      refusal and never an uncaught exception. A symbolic-link loop, which
      raises `RuntimeError` rather than `OSError`, a permission error, and a
      non-prefix result are each covered.
- [ ] **AC-0016.** `DA3`'s sentence-matching pattern contains no nested
      quantifier and no alternation inside a repetition, the two constructs
      that make backtracking super-linear. The property is structural because
      an elapsed-time bound on a shared pull-request runner is a flake, not a
      check.
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
      it as a supporting tripwire; `overlap` is deliberately not on that list,
      because it is the plainest word for the defect `DA5` names and banning
      it would penalize the clearest statement of the gate. The obligation
      rests on the positive statement, because a prohibition over an open set
      of measure names can never be completed.

### The prechecks the hybrids carry

Each criterion in this group holds in all three homes named in the group
above. A precheck present only in the authoring rubric would leave the two
homes a reviewer reads unable to tell a hybrid from judgment-only `DA5`, which
is the one distinction ADR-0118 fixes and the 🧭 tag alone cannot carry.

- [ ] **AC-0036.** `DA6`'s precheck rejects a `Revision History` or
      `Decision Log` heading in the document body.
- [ ] **AC-0037.** `DA7`'s precheck is the obligation already carried by the
      authoring rubric's checklist item — every diagram states one named
      question and one zoom level — with `DA7`'s identifier, severity and tag
      attached to that item in place. It is not restated as a second,
      differently worded obligation: the item's `one named question` is pinned
      by `test_design_scope_routing.py`'s `REPLACEMENTS`, and a reworded
      successor beside it would give one obligation two disagreeing homes in
      the file that ships `DA5`.
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
      `above`: the templates' own fixed opening question for Implementation
      Mapping contains `the model above`, so a bare positional search would
      red the pack's own output.
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
- [ ] **AC-0046.** The shipped `assets/*.md` are **not** the precheck corpus,
      and the spec says why: they are skeletons whose unfilled placeholders —
      `<this diagram's zoom level>`, `<element from section 2>` — are the
      slots a precheck asks an author to fill, so a skeleton failing a
      finished-document check is the template working, not a defect. The one
      precheck this distinction does not rescue is `DA9`, whose `Appendix`
      trigger fires on `assets/design-doc.md`'s real `## Appendix (optional)`
      heading; that asset is the unrouted compatibility pointer this
      procedure never routes to, and `DA9` is scoped to a routed document.

### Parity

- [ ] **AC-0047.** `packs/architect/tests/pack/test_design_reviewer_rubric_parity.py`
      asserts every identifier `DA1` through `DA10` appears in all three homes.
- [ ] **AC-0048.** The same test asserts each gate's severity agrees across the
      three homes, and permits the explanatory prose to differ.

### Reporting

- [ ] **AC-0049.** `architect-design/SKILL.md` step 6 requires every gate
      result to be reported by identifier and verdict before a draft is shown.
- [ ] **AC-0050.** `references/convergence-loop.md` requires each review pass
      to report every gate identifier with a verdict.
- [ ] **AC-0051.** `references/convergence-loop.md` states that the loop
      requires and invokes no script, and names the shipped gate script as a
      human- or CI-run accelerant outside the loop, in the same words AC-0018
      requires of `SKILL.md`.
- [ ] **AC-0052.** `references/convergence-loop.md` states which property the
      shipped script does and does not cost — the loop stays pure-prose and
      zero-config, and the script is optional and run outside the loop — and
      carries no unconditional claim that shipping a script forfeits a pack
      property.

### Supersession

- [ ] **AC-0053.** `docs/specs/architect-design-scope-templates/spec.md`
      carries a `Status`-line supersession pointer naming ADR-0118 and the part
      superseded.
- [ ] **AC-0054.** This change alters no line of
      `docs/specs/architect-design-scope-templates/spec.md` except its
      `Status` line, and the one-line pull-request diff for that file is
      recorded.

### Release closure

- [ ] **AC-0055.** `packs/architect/pack.toml` declares version `0.15.12`.
      Its equality with `.claude-plugin/plugin.json` is owned by
      `tests/conformance/test_pack_metadata.py`.
- [ ] **AC-0056.** `docs/product/changelog.md` carries a free-standing
      `## [architect][0.15.12] — <YYYY-MM-DD>` entry, dated in that exact
      form, with a `### Highlights` subsection. The date is not decoration:
      `/now/` eligibility is versioned and dated, so an undated heading never
      publishes.
- [ ] **AC-0057.** `packs/architect/.apm/skills/architect-design/evals/evals.json`
      carries an eval whose expectation requires the response to name every
      identifier `DA1` through `DA10` with a verdict.
- [ ] **AC-0058.** `.claude-plugin/marketplace.json` is regenerated by
      `FORCE=1 make build-self` and records architect at `0.15.12`.

## Follow-ons

- architect pack maintainer: the `metadata.boundaries` vocabulary in
  `docs/architecture/security.md` has no value for a skill that ships an
  executable, and its capability table maps `Bash` only to `network_egress`
  and `deploy_action`. `architect-assess` already ships `profile_repo.py`
  under the same three boundaries, so this slice inherits the gap rather than
  creating one, and AC-0018 resolves the local question by stating that the
  agent does not invoke the script. Adding an execution value, or recording
  that shipped scripts are out of that convention's scope, is a separate
  change.
- architect pack maintainer: slice 3, tracked by ADR-0118 — the system-shape
  and workload axes and the conditional ports-and-adapters view.
- architect pack maintainer: `packs/architect/tests/skills/architect-review/`
  and `.../architect-diagram/` still reach CI only through the dispatch-only
  `test-corpus.yml`. This slice gates the suite it adds to and leaves the other
  two, whose dispositions in `tools/lint-ci-parity.py` remain accurate.

## Assumptions

- Process: the two checks in `architect-review/references/rubric-generic.md` —
  gratuitous repetition and length proportional to stakes — stay there as well
  as reaching the design-doc rubric through `DA5` and `DA10`. The generic
  rubric is the only rubric a strategy memo, one-pager or comparison table
  routes to, so deleting them would strip those genres of the check to give it
  to a genre that gains a stronger one anyway. If the owner wants a single
  home, the generic pair is what moves and those genres lose the check.
