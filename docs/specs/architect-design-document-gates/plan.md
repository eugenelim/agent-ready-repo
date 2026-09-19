# Plan: architect-design document-architecture gates

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** ADR-0118 `D5` fixes the gate set and its
  mechanizability. Two analogous shipped implementations:
  `packs/architect/.apm/skills/architect-assess/scripts/profile_repo.py`, a
  pack skill shipping a standard-library script inside `.apm/` with its UTF-8
  stream reconfiguration at `:952-955` and its confinement at `:294-312`; and
  `packs/core/.apm/skills/new-spec/scripts/lint-contract-item-alignment.py`, a
  skill shipping its own lint. Their construction path is
  `packs/architect/tests/skills/architect-assess/test_profile_repo.py:23`,
  which loads the script by `importlib.util.spec_from_file_location` under a
  pack-unique module name. No named deviation.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

## Approach

The gating change lands first, so every later commit is proven by the pull
request rather than by a dispatch. The script follows, because the rubric text
then describes behaviour that exists. The three rubric homes and the parity
test move in one commit: a home written without the comparison that reads it
is the drift this slice exists to stop. The filled reference document lands
before the prechecks are trusted. Release closure is last.

The riskiest part is the precheck corpus. A precheck is executed by a reader,
so nothing mechanical decides whether one fires, and the shipped templates
cannot stand in for a document — their placeholders are the slots a precheck
asks an author to fill, so a walk against them measures the template.

## Constraints

- **ADR-0118 `D5`** fixes the ten identifiers and each one's mechanizability.
- **ADR-0118 `D4`** owns the `D1`–`D6` decomposition criteria, a different
  namespace from the record's own `D1`–`D6` constraint addresses.
- **`packs/AGENTS.md` § Shipped pack content carries no internal-governance
  citations** — nothing under `packs/` cites ADR-0118.
- **`packs/AGENTS.md` § Version bump rule** — matching `pack.toml` and
  `.claude-plugin/plugin.json` bumps, and a non-cosmetic pack update moves the
  pack's eval harness.
- **`packs/AGENTS.local.md:26-40`** — marketplace regeneration, free-standing
  changelog entry, explicit Highlights verdict.
- **`docs/specs/architect-design-scope-templates/spec.md` is frozen at
  `Shipped`.** The supersession takes the `Status`-line form in
  `references/spec-and-plan-contract.md` § *Superseding a frozen document*,
  which points at the ADR rather than at this spec.
- **`tests/AGENTS.md` § Roster is not auto-discovered** — a `tests/roster/`
  module obliges a `build-check.yml` step, a `STEP_DISPOSITION` entry, and a
  `.workspace-prune-protected.toml` entry when it names a `docs/specs/<slug>`
  path as a literal.

## Construction tests

One comparison spans T3 and T4: ten identifiers, tags and severities must
agree across three files no single task owns alone. It extends
`packs/architect/tests/pack/test_design_reviewer_rubric_parity.py`, which
already guards the verdict, severity and taxonomy vocabulary over a different
carrier set in the same module.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale (ADR-0118 `D5`) | T3, T4 | `test_design_reviewer_rubric_parity.py` green | The shipped identifiers and tags read back against `D5` |
| Release history (changelog) | T7 | The dated free-standing entry exists | The Highlights verdict is recorded either way |
| Maintainer procedure (three rubric homes) | T3, T4, T4a | The parity test and the precheck walk | Every identifier, tag and severity agrees in all three homes |
| Interface compatibility (script exit codes) | T2 | The exit-code and refusal tests green | The typed-command transcripts in `notes/verification-ledger.md` |
| Reusable learning | T7 | — | A `project-knowledge` receipt, or the unavailable record |

## Design (LLD)

### Design decisions
Owned by: T2, T3, T4, T4a.

**One module, not two.** `DA3` and `DA10` share `strip_excluded`, which
removes YAML frontmatter and HTML-comment spans. Past that point they diverge:
`DA10` counts every word that survives, while `DA3` further excludes fences,
tables, list items, block quotes and headings, because a table row is not a
prose paragraph though its words are still words in the document.

**The taxonomy glyph carries the mechanizability.** The pack ships a decidable
two-value test — 🔧 when the fix is fully determined, 🧭 when a human must
choose — and the convergence loop routes on those two tokens. ADR-0118's
three-value column collapses onto them by asking who decides: `Mechanizable`
is 🔧, and both `Hybrid` and `Judgment-only` are 🧭. What preserves the
three-way distinction in the text is that every hybrid states a precheck and
`DA5` states that it has none; a third interop token would have to be learned
by every carrier and by the loop, for a distinction the loop does not route
on.

**The eight are checklist items, not a lint with a `--strict` flag.** A gate
written as a lint that no lint can decide goes green on the cases it cannot
see, converting an unchecked property into a recorded pass.

**`DA7` and `DA8` are written onto existing rubric items.**
`test_design_scope_routing.py`'s `REPLACEMENTS` pins `the complete model set`
and `one named question` as graded checklist items in the authoring rubric.
Those items are the same obligations, so the gates attach an identifier, a tag
and a severity to them in place. A reworded successor beside them would give
one obligation two disagreeing homes in the file that ships `DA5`.

**The gates take no new `##` heading.**
`architect-design-scope-templates`' AC-0025 and AC-0031 are ticked criteria on
a frozen `Shipped` spec, stating that the only permitted non-template `##`
headings are `Cross-cutting`, `Decomposition` and `Severity mapping
(typical)`. The gates therefore sit under each rubric's existing
`## Cross-cutting` heading, and `AUTHOR_EXTRA`/`REVIEW_EXTRA` in
`test_design_scope_routing.py` are untouched. Widening those sets instead
would make the test pass and the frozen contract false.
`.apm/agents/design-reviewer.md` has no `## Cross-cutting` heading and no test
pins its heading set, so the gates take a section of their own there, after
`## Severity glossary` so a reader meets the severity vocabulary first.

**The two generic-rubric checks are neither moved, copied, nor cited.**
`rubric-generic.md`'s gratuitous-repetition and length-proportional-to-stakes
checks do not reach a design doc, which routes to the specific rubric
(`architect-review/SKILL.md:56-71`). Moving them strips the genres
`rubric-generic.md` exists for — a strategy memo, a one-pager, a comparison
table have no other rubric. Copying them puts one concern in two homes inside
the file that ships `DA5`. Citing them points a reader at `###` sections
inside `## Generic checks (when no specific rubric fits)`, whose caption
disclaims the case a design-doc reviewer is in. `DA5` owns gratuitous
repetition at greater strength and `DA10` owns proportional length with a
derived bound, so the concerns reach a design doc through the gates and
`rubric-generic.md` is untouched.

### Interfaces & contracts
Owned by: T2.

`check_document_architecture.py` takes one or more document paths and a
required `--root`, following `profile_repo.py:935`. A default of the working
directory would let a `make` target, a CI step and a hand invocation each
establish a different boundary, and a run from `/` would confine nothing.

| Exit | Meaning |
| --- | --- |
| 0 | every target read, no finding |
| 1 | every target read, at least one `DA3` or `DA10` finding |
| 2 | at least one target refused |

**2 dominates 1.** A run that refuses one target and reports a finding on
another exits 2; exiting 1 would report a clean run over a set silently
missing a member. A refusal does not abort the run — the remaining targets are
still read, and the summary states how many were refused.

A finding prints as `<path>:<line>: DA3 — paragraph of N sentences (budget 3)`
or `<path>: DA10 — N words (bound 2400)`, with `<path>` escaped.

### Component / module decomposition
Owned by: T2.

Four pure functions and a thin CLI, so the tests call functions rather than
spawning an interpreter:

- `strip_excluded(text)` — removes YAML frontmatter and HTML-comment spans.
  Both gates consume its output; nothing else defines the shared exclusion.
- `prose_paragraphs(text)` — yields `(start_line, text)` per blank-line
  separated run that is not a fence, table row, list item, block quote or
  heading. A fence is tracked as a span, because a table row inside a fenced
  block is not a table row.
- `count_sentences(paragraph)` — splits on terminal punctuation followed by
  whitespace and a capital, after masking the abbreviation set and decimals by
  literal replacement. The pattern carries no nested quantifier and no
  alternation inside a repetition.
- `read_target(root, path, max_bytes)` — the one place a file is opened. It
  canonicalizes, checks the prefix, checks file type and link count, checks
  size, and raises one refusal type carrying the path and the reason.

### Failure, edge cases & resilience
Owned by: T2.

A parser false positive is a wrong answer about a file the gate read; a
refusal is the gate declining to answer. Conflating them is how a zero-finding
report comes to cover a file nobody looked at.

The parser's false-positive sources are each a test: an abbreviation
mid-sentence, a decimal, a heading directly above wrapped prose, a multi-line
HTML comment containing four sentences, a fenced block containing a
pipe-delimited line, a nested list continuation line.

The refusal set, and why each entry is there:

| Condition | Why it refuses rather than reads |
| --- | --- |
| real path not under the canonicalized root | the CWE-73 check; a resolved target compared against an unresolved root compares the wrong thing |
| not a regular file | a FIFO or character device opens cleanly and blocks forever, turning a CI gate into a hung job |
| more than one hard link, or a reparse point | the entry the gate stats is not necessarily the bytes it reads |
| larger than 1,048,576 bytes | a highly compressible `.md` is read whole into memory by `strip_excluded` |
| resolution raised | `Path.resolve()` raises `RuntimeError`, not `OSError`, on a symlink loop (CPython #109187), and `relative_to` raises `ValueError` on a non-prefix path, so the handler catches all three as `profile_repo.py:279-281` does |

A path reaching stdout or stderr is attacker-chosen data: a filename may
legally contain a newline or a terminal escape. Every emitted path is escaped
so one finding occupies one line.

### Dependencies & integration
Owned by: T2.

The standard library is the floor and
`agentbundle.catalogue_tooling.file_safety` is used on top of it when
importable — `profile_repo.py`'s shape. `_safe_read` (`:294-312`) runs its own
`resolve(strict=True)` plus `relative_to(root)`, an `S_ISREG` check, a
reparse-point check, an `st_nlink > 1` check and a byte budget
unconditionally, and calls `catalogue_read_confined_regular_file` in addition
when the import succeeded. An adopter without `agentbundle` keeps every check;
this repository gets the blessed helper too. Root `AGENTS.md` § Security
considerations blesses that helper, so declining it would be the deviation.

## Tasks

### T1: the architect-design suite runs on a pull request

**Depends on:** none

**Touches:** .github/workflows/build-check.yml, tools/lint-ci-parity.py

**Tests:**
- `python3 tools/lint-ci-parity.py` exits 0. It drives both roster directions
  over `.github/workflows/build-check.yml`'s step list and the
  `STEP_DISPOSITION` table in the lint itself: a step covering a suite whose
  entry says `NO_PR_GATE` fails (AC-0001), and a disposition naming no real
  step fails (AC-0002).
- no stub (goal-based)

**Done when:** the lint exits 0 and the carve-out step names the directory.

**Note:** this landed in commit `81663a467` before approval —
`build-check.yml:435` names the directory and `tools/lint-ci-parity.py:878-882`
carries the matching `PR_GATED` disposition. The task stays in the plan
because every later task rests on it for pull-request evidence.

### T2: the gate script refuses what it cannot read and reds on what it can

**Depends on:** T1

**Touches:** packs/architect/.apm/skills/architect-design/scripts/check_document_architecture.py, packs/architect/tests/skills/architect-design/test_gate_script.py, packs/architect/.apm/skills/architect-design/SKILL.md

**Tests:**
- `test_gate_script.py` loads `check_document_architecture.py` by
  `importlib.util.spec_from_file_location` under the pack-unique name
  `architect_design_gate_script`, matching `test_profile_repo.py:23`. A bare
  `import` would bind whichever `scripts/` directory reached `sys.path` first
  (AC-0003).
- The module's import set is read with `ast` and compared against
  `sys.stdlib_module_names` plus the one permitted optional
  `agentbundle.catalogue_tooling.file_safety`, so a third-party import fails
  rather than passing because this machine has it installed. A second case
  drives `read_target` with that import forced absent, since the
  standard-library floor is unobservable where the helper imports (AC-0004).
- `main()`'s stream setup is driven with `sys.stdout` patched by a recorder
  that requires `reconfigure` to be its first call; asserting the call
  happened would pass on a script that printed first (AC-0005).
- The CLI entry point is driven for 0, 1 and 2 (AC-0006); for a two-target run
  pairing a finding with a refusal, which must exit 2 (AC-0007); and for the
  same run asserted to have still reported the finding and a refused count,
  which separates "2 dominates" from "2 aborts" (AC-0008).
- `read_target`'s refusal type is asserted to carry the path and the reason,
  and the stderr rendering to print both (AC-0009).
- `_parser()` is asserted to make `--root` required, so invoking without it is
  a usage error rather than a run against the working directory (AC-0010).
- `read_target` is driven with a root that is itself a symlink, requiring a
  target under the real directory to be accepted — which fails when only the
  target side is canonicalized (AC-0011).
- `read_target` is driven against real filesystem entries built by the test,
  one per row of the refusal table, each asserting the refusal *reason*: a
  regular file under a symlinked parent whose real path leaves the root
  (AC-0012); a directory, a FIFO, a symlink and a second-hard-link file
  (AC-0013); a file one byte over 1,048,576 with its sibling one byte under
  accepted (AC-0014); a symlink loop, which must refuse rather than raise
  (AC-0015).
- `count_sentences`' compiled pattern is walked with `re` parse introspection
  for a nested quantifier and for alternation inside a repetition (AC-0016).
- The finding and refusal renderers are driven with a filename containing a
  newline and a terminal escape, and the report asserted to hold one line per
  finding (AC-0017).
- `prose_paragraphs` and `count_sentences` are driven over every `*.md` under
  `architect-design/assets/` by glob, requiring zero findings (AC-0020); over
  fixtures built in the test, one per false-positive source in Design →
  Failure (AC-0021, AC-0022, AC-0023); and at 3 and 4 sentences, pinning the
  budget on both sides (AC-0019).
- `count_words` is asserted at exactly the bound and one over (AC-0025), and
  the finding renderer asserted to carry path, line and count (AC-0024).
- An assertion over `SKILL.md` requires it to state that the agent running the
  skill does not invoke the script (AC-0018).

```python
# stub: true — the red contract surface, before the parser exists.
def test_da3_reports_a_four_sentence_paragraph() -> None:
    gate = _load_gate()
    assert gate.count_sentences("One. Two. Three. Four.") == 4
```

**Done when:** `test_gate_script.py` passes, and the two typed CLI runs —
against a non-compliant fixture and against the shipped templates — are in
`notes/verification-ledger.md` with their stdout, stderr and exit codes.

### T3: the authoring rubric carries all ten gates

**Depends on:** T2

**Touches:** packs/architect/.apm/skills/architect-design/references/design-doc-rubric.md, packs/architect/tests/skills/architect-design/test_gate_text.py

**Tests:**
- `test_gate_text.py` slices `design-doc-rubric.md` on its `DA<n>` item
  boundaries and asserts **within one gate's body**, never over the file. A
  whole-file `assertIn("2,400", text)` passes on any second mention of the
  bound, and seven prechecks in one file cross-satisfy each other.
- Inside `DA10`'s body: the derivation's counted features and its multiplier,
  with the test recomputing the arithmetic and requiring it to reach the
  stated bound (AC-0026); the handoff naming
  `references/decomposition-rubric.md` with the disclaimer of split authority
  (AC-0027); the companion-views-and-evidence-links remedy (AC-0028).
- Inside each hybrid's body, its precheck: `DA1` (AC-0039), `DA2` (AC-0040),
  `DA4` (AC-0041), `DA6` (AC-0036), `DA7` (AC-0037), `DA8` (AC-0038), `DA9`
  (AC-0042); each stating the verdict is the reviewer's (AC-0043); each
  stating it applies to an authored document (AC-0046); and `DA9` scoped to a
  routed document (AC-0047).
- `design-doc-rubric.md` is asserted to state what a severity means for an
  author (AC-0034). The file carries no severity vocabulary today.
- `test_design_scope_routing.py`'s existing `REPLACEMENTS` assertions must
  still pass untouched, which is what proves `DA7` and `DA8` were written onto
  the pinned items rather than around them; and
  `test_the_authoring_rubric_names_only_sections_the_templates_have` must stay
  green **without** touching `AUTHOR_EXTRA`.
- no stub (goal-based)

**Done when:** `packs/architect/tests/skills/architect-design/` passes and
`git diff` shows no new `##` heading in the rubric.

### T4: the reviewing rubric, the agent, and the parity test agree

**Depends on:** T3

**Touches:** packs/architect/.apm/skills/architect-review/references/rubric-design-doc.md, packs/architect/.apm/agents/design-reviewer.md, packs/architect/tests/pack/test_design_reviewer_rubric_parity.py

**Tests:**
- `test_design_reviewer_rubric_parity.py` gains a `DA_CARRIERS` tuple naming
  the three gate homes and a `DA_GATES` map from identifier to severity glyph
  and taxonomy glyph, asserting each identifier and its two glyphs in every
  `DA_CARRIERS` entry (AC-0048, AC-0049). It also observes the authoring
  rubric (AC-0029), the reviewing rubric (AC-0030), the agent (AC-0031) and
  the tag assignment (AC-0032), so no home has an assertion of its own that
  could pass while another drifted.
- The existing `CARRIERS` tuple is untouched. It names
  `architect-review/SKILL.md`, `rubric-well-architected.md` and the agent —
  a set overlapping the gate homes in one file. Folding the gates into it
  would assert the identifiers against two files that must not carry them and
  leave the authoring rubric unchecked, so the module holds two named sets and
  its docstring says which obligation each serves.
- Severity is asserted as the glyph adjacent to the identifier. Measured, the
  carriers differ: `design-doc-rubric.md` holds none of 🟥🟧🟨⚪ or 🔧🧭,
  `rubric-design-doc.md` holds the four severity glyphs in its severity
  mapping and neither taxonomy glyph, and `design-reviewer.md` holds all six.
  A file-wide presence check passes on the wrong severity in two of three.
- `DA_GATES`' severity map is a literal in the test, so parity compares the
  homes against a fixed value rather than against each other (AC-0033); three
  homes agreeing on a wrong severity passes the weaker shape.
- `DA5`'s body in each home is asserted on its positive statement — the
  verdict is the reviewer's judgement and no automated measure decides it —
  with the two enumerated measure phrases as a supporting negative (AC-0035).
- `REVIEW_EXTRA` is untouched, for T3's reason. The agent file's gates go
  after its `## Severity glossary`.
- no stub (goal-based)

**Done when:** `packs/architect/tests/pack/` and
`packs/architect/tests/skills/architect-design/` both pass.

### T4a: the prechecks are walked against a document, not a template

**Depends on:** T4

**Touches:** packs/architect/tests/skills/architect-design/testdata/filled-subsystem-design.md, packs/architect/tests/skills/architect-design/test_gate_text.py, docs/specs/architect-design-document-gates/notes/verification-ledger.md

**Tests:**
- A reference document authored from `assets/subsystem-design.md` with every
  placeholder replaced by real content is committed at
  `testdata/filled-subsystem-design.md`, and `test_gate_text.py` asserts it
  carries no `<…>` placeholder token, so a half-filled skeleton cannot serve
  as the corpus (AC-0044).
- Each of the seven prechecks is walked by hand against that document and the
  walk written to `notes/verification-ledger.md` (AC-0045).
- no stub (manual QA for the walk, goal-based for the document)

**Approach:**
- The document carries real content rather than filler. A precheck walked
  against filler measures the filler's shape.

**Done when:** the reference document is committed, the seven-precheck walk is
in the verification ledger, and no precheck fired.

### T5: the loop reports every gate and its contract stops contradicting itself

**Depends on:** T3

**Touches:** packs/architect/.apm/skills/architect-design/SKILL.md, packs/architect/.apm/skills/architect-design/references/convergence-loop.md

**Tests:**
- `test_gate_text.py` asserts over `SKILL.md` step 6 and over
  `convergence-loop.md`'s cycle that each demands a per-identifier verdict,
  as the closed set `DA1`-`DA10` plus the word verdict rather than the phrase
  "report the gates" (AC-0050, AC-0051). The failure this slice closes is a
  gate producing no finding because nothing asked it to, so "reported every
  gate" is the property and a generic instruction is a consequence of it.
- An assertion pins the corrected contract sentence at
  `convergence-loop.md:6-7`: the loop requires and invokes no script
  (AC-0052).
- A second assertion covers `convergence-loop.md:9`, "A script would forfeit
  the pack's pure-markdown, zero-config, portable property" — the sentence
  this slice falsifies. It is replaced by a statement of what the shipped
  script does and does not cost, and the unconditional claim must be absent
  (AC-0053).
- The edits stay outside the `agentbundle:output-rendering` markers and
  outside the pinned description regions; step 6's body is neither.
- no stub (goal-based)

**Done when:** the suite passes and `git diff` shows no line inside any marker
span.

### T6: the superseded criteria point forward without moving

**Depends on:** none

**Touches:** docs/specs/architect-design-scope-templates/spec.md

**Tests:**
- `python3 '<skill-dir>/../work-loop/scripts/lint-spec-status.py' --root .`
  decides the status token (AC-0054). It owns status vocabulary and nothing
  else; that the pointer names the right ADR and scopes the right part is a
  reviewer's call.
- The pull-request diff for that file is recorded in
  `notes/verification-ledger.md` and must be one line (AC-0055).
- **Not a standing test.** `tests/AGENTS.md` puts a repository-level assertion
  in `tests/roster/`, which then obliges a `build-check.yml` step, a
  `STEP_DISPOSITION` of `LOCAL("test-after-build-check")`, and — because the
  test would name a `docs/specs/<slug>` path as a literal — a
  `.workspace-prune-protected.toml` entry, without which
  `test_two_sided_prune_closure_invariant.py:563-570` reds. Four pieces of
  machinery for a frozen document that by convention takes only a
  `Status`-line edit, already watched by a reviewer and by the status lint.
  Declined under `Cut before adding` rung 1.
- no stub (goal-based)

**Done when:** the `Status` line names ADR-0118 and the part superseded, and
the recorded diff for that file is one line.

### T7: the pack release closes

**Depends on:** T2, T3, T4, T4a, T5

**Touches:** packs/architect/pack.toml, packs/architect/.claude-plugin/plugin.json, docs/product/changelog.md, packs/architect/.apm/skills/architect-design/evals/evals.json, .claude-plugin/marketplace.json

**Tests:**
- `python3 -m pytest tests/conformance/test_pack_metadata.py -q` owns the
  `pack.toml`/`plugin.json` equality (AC-0056); this task does not restate
  that comparison.
- `FORCE=1 make build-self` regenerates `.claude-plugin/marketplace.json` and
  refuses a dirty tree, so the version bump commits before it runs. The
  regenerated file is read back for architect at `0.15.12` (AC-0059) — a
  projection is verified by regenerating it, never by editing its bytes.
- The eval's expectation text is asserted against the closed set: it must name
  every identifier `DA1` through `DA10` with a verdict (AC-0058). Requiring
  only that an eval mentions the gates lets the implementation write its own
  comparison value.
- The changelog entry is read and recorded in `notes/verification-ledger.md`
  (AC-0057). No pull-request gate checks it: `build-check.yml` names changelog
  nothing at all, and `pages.yml`'s release-anchor job compares anchors
  against built HTML, so it cannot see position, nesting, or a
  `### Highlights` subsection.
- no stub (goal-based)

**Approach:**
- The Highlights verdict is answered before the entry is written: this change
  gives an adopter a runnable gate script and ten named checks their reviewer
  did not have, so the answer is yes and the bullets are drafted.

**Done when:** `FORCE=1 make build-self` succeeds on a clean tree and the
changelog entry stands free at `##` with its dated heading and its Highlights
subsection.

## Rollout

- **Delivery:** big bang, fully reversible. Repository and pack content only;
  a revert is a revert.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** T1 first, so the rest is proven by the pull
  request rather than by a dispatch. T7 last, because the changelog entry
  describes the finished set and `make build-self` refuses a dirty tree.

## Risks

- **A precheck reds on correct authored output.** The filled reference
  document is one document, written by the same delivery that writes the
  prechecks, so it cannot show what a precheck does to output someone else
  authored. The spec records that gap.
- **The three rubric homes drift in the next slice.** The parity test is the
  mitigation, and its stated limit is inherited: the allowlist does not
  auto-discover a new identifier, so slice 3 adding a `DA11` must add it to
  the constant by hand.
- **`FORCE=1 make build-self` refuses a dirty tree**, which strands T7 if the
  version bump is left uncommitted.

## Changelog

<!--
- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->
