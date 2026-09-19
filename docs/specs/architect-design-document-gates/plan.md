# Plan: architect-design document-architecture gates

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** ADR-0118 `D5` fixes the gate set and its
  mechanizability. The governing implementation is
  `packs/core/.apm/skills/close-work/scripts/` — a skill that carries a
  mirrored `file_safety.py` and loads it as a co-located sibling through a
  guarded loader at `close_work.py:912-957`, which is the confinement shape
  this plan adopts. `packs/core/.apm/skills/new-spec/scripts/lint-contract-item-alignment.py`
  keeps one narrower role: it is the precedent that a skill-shipped lint is
  handed paths by a caller and must confine them, and its twelve-line
  `_read_confined` at `:281-302` is the shape this plan **declines**, being
  check-then-act with no `O_NOFOLLOW`, no descriptor re-check and no
  read-time bound. `packs/architect/.apm/skills/architect-assess/scripts/profile_repo.py`
  contributes its UTF-8 stream reconfiguration at `:952-955` only. The
  construction path is
  `packs/architect/tests/skills/architect-assess/test_profile_repo.py:23`,
  which loads a pack script by `importlib.util.spec_from_file_location` under
  a pack-unique module name.

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

**Precondition, already in the branch.** `packs/architect/tests/skills/architect-design/`
reached CI only through the dispatch-only `test-corpus.yml`, so a suite added
to it proved nothing on a pull request. Commit `81663a467` put the directory
in `build-check.yml`'s carve-out step (`:435`) and flipped its
`tools/lint-ci-parity.py` disposition to `PR_GATED` (`:878-882`). Every task
below rests on that; none of them re-does it.

The script comes first, because the rubric text then describes behaviour that
exists. The three rubric homes and the parity
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
- **`tests/AGENTS.md` § Roster is not auto-discovered** — the byte-identity
  module under `tests/roster/` obliges a `build-check.yml` step naming it and
  a matching `STEP_DISPOSITION` of `LOCAL("test-after-build-check")` in
  `tools/lint-ci-parity.py`. It names no `docs/specs/<slug>` literal, so it
  owes no `.workspace-prune-protected.toml` entry.
- **`docs/specs/architect-design-scope-templates/spec.md` is frozen at
  `Shipped` and this slice does not touch it.** `DA7` and `DA8` attach an
  identifier to the checklist items its AC-0026 and AC-0027 describe, leaving
  both criteria true, so no supersession pointer is owed.

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
a frozen `Shipped` spec, and the two sets differ: `AUTHOR_EXTRA` at
`test_design_scope_routing.py:69` permits `Cross-cutting` and `Decomposition`
in the authoring rubric, while `REVIEW_EXTRA` at `:70` adds
`Severity mapping (typical)` for the reviewing one. The new severity prose
goes in the authoring rubric, the stricter of the two. The gates therefore sit under each rubric's existing
`## Cross-cutting` heading, and `AUTHOR_EXTRA`/`REVIEW_EXTRA` in
`test_design_scope_routing.py` are untouched. Widening those sets instead
would make the test pass and the frozen contract false.
`.apm/agents/design-reviewer.md` has no `## Cross-cutting` heading and no test
pins its heading set, so the gates take a section of their own there, after
`## Severity glossary` so a reader meets the severity vocabulary first.

**How the reviewer is wired to the gates.** No agent in this repository
declares a `Skill` tool — `design-reviewer`'s are `Read, Grep, Glob` — so it
cannot invoke `architect-review` to fetch a rubric. The pattern the repository
already uses for a reviewer that needs another skill's checklist is
`packs/product-engineering/.apm/agents/discovery-threat-reviewer.md:53-66`:
carry a baseline inline, reason from the other skill's modules when its depth
is available, and **raise a finding when that depth is missing** rather than
review quietly at baseline. `design-reviewer` gets the same three parts. Its
inlined ten gates are the baseline; `rubric-design-doc.md` is the depth it
reads by path when `architect-review` is co-installed; a missing rubric
becomes a finding. Its current text has the middle part and claims it
"degrades visibly" without saying how, which is the half that does nothing.

**Inlining the gates does not make the agent report them.** Its output
contract is findings-only — verdict, summary, findings by severity, what's
working — and says "if everything is clean, say so with the `SHIP IT` verdict
… no manufactured findings". Under that contract a gate nobody considered and
a gate that passed both produce nothing, which is the failure this slice
exists to fix, one level down and on the only rung with real independence. The
returned block gains a ten-row roll-call, inside the block because the section
forbids a pre-findings recap.

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
or `<path>: DA10 — N words (bound 3300)`, with `<path>` escaped.

### Component / module decomposition
Owned by: T2.

Four pure functions and a thin CLI, so the tests call functions rather than
spawning an interpreter:

- `strip_excluded(text)` — removes YAML frontmatter and HTML-comment spans.
  Both gates consume its output; nothing else defines the shared exclusion.
- `prose_paragraphs(text)` — yields `(start_line, text)` per blank-line
  separated run that is not a fence, table row, list item, block quote or
  heading. No placeholder rule lives here: `DA3`'s clean corpus is an
  authored document (AC-0018), which carries none. A fence is tracked as a
  span, because a table row inside a fenced block is not a table row.
- `count_sentences(paragraph)` — splits on terminal punctuation followed by
  whitespace and a capital, after masking the abbreviation set and decimals by
  literal replacement. The pattern carries no nested quantifier and no
  alternation inside a repetition.
- `read_target(root, path, max_bytes)` — the one place a file is opened, and
  a thin wrapper over the vendored `read_confined_regular_file`. It translates
  that helper's `UnsafeContentError` into the gate's own refusal type carrying
  the path and the reason, and adds nothing to the confinement: a second
  implementation beside a blessed one is a second thing to keep correct.

### Failure, edge cases & resilience
Owned by: T2.

The parser's false-positive sources are each a test: an abbreviation
mid-sentence, a decimal, a heading directly above wrapped prose, a multi-line
HTML comment containing four sentences, a fenced block containing a
pipe-delimited line, and a nested list continuation line.

**Why no placeholder rule.** Two attempts at one both failed review: a
same-line span missed the very case it was written for, and a
joined-paragraph span silently ate a sentence out of
`Keep p95 <200ms. Throughput must exceed >1k rps.` — a four-sentence
paragraph passing the budget at three. The defect was the corpus, not the
rule. `DA3`'s clean half now runs against an authored document, which has no
placeholders, so no span rule is owed and the under-count path does not
exist.

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

**A vendored projection of `file_safety.py`, loaded as a co-located sibling.**

The repository ships three patterns for a pack script that needs confinement,
not the two an earlier draft of this plan weighed. `profile_repo.py` imports
`agentbundle.catalogue_tooling.file_safety` when it is importable and
hand-rolls the same checks when it is not. `new-spec`'s
`lint-contract-item-alignment.py` hand-rolls a twelve-line `_read_confined`
and cites nothing. And `packs/core/.apm/skills/close-work/scripts/file_safety.py` is the
repository's source of truth, carried beside its skill and loaded as a
sibling; `packs/core/.apm/skills/work-loop/scripts/file_safety.py` is a
hand-maintained copy of it, pinned only by a byte comparison at
`tests/roster/test_policy_family_selector.py:336-348`.

This script takes the third. It needs no `agentbundle` import, so the
adopter-install constraint holds and the `Never do` rule is untouched; it has
one code path, so the conditional import's untested-branch problem does not
arise; and it inherits `read_confined_regular_file`'s full depth rather than a
re-implementation of part of it.

**Two reasons earlier drafts recorded, both wrong, both corrected here.** The
first declined the helper because "a script projected into an adopter install
cannot reach it" — false, and the two copies under `packs/core/` are exactly
such a reach. The second called this copy a declared pair `make build-self`
writes — also false: every pair in
`packages/agentbundle/agentbundle/build/self_host.py:118-150` runs
`packs/… → packages/…`, and no declared destination lives under `packs/`, so
nothing regenerates a pack-to-pack copy.

**What that costs, accepted with owner approval.** The copy is hand-maintained
and a fix to the source reaches it only when someone carries it across. That
is the shape `test_packaged_runtime_closure.py:99-106` calls a defect, and it
is also the only thing the repository currently does for a `packs/**` copy.
Extending the mechanism is an agentbundle engine change needing an
`Engine-Change-RFC:` trailer and matching version bumps, which this slice does
not scope; the owner approved matching the existing practice instead, AC-0079
records that the copy is hand-maintained so a reader does not over-trust the
byte pin, and
[`docs/product/intents/shared-pack-file-projection.md`](../../product/intents/shared-pack-file-projection.md)
carries the mechanism forward.

**What the helper gives that the twelve-line shape does not.** `O_NOFOLLOW` on
the open, an `os.fstat` re-check of `(st_dev, st_ino)` and the link count
against what was stat'd, and a bound applied to the read rather than to
`st_size`. `lint-contract-item-alignment.py:281-302` is check-then-act and has
none of them; it is the weaker of the two standard-library shapes here, and an
earlier draft of this plan cited it as governing.


## Tasks

### T2: the gate script refuses what it cannot read and reds on what it can

**Depends on:** none

**Touches:** packs/architect/.apm/skills/architect-design/scripts/check_document_architecture.py, packs/architect/.apm/skills/architect-design/scripts/file_safety.py, packs/architect/tests/skills/architect-design/test_gate_script.py, packs/architect/.apm/skills/architect-design/SKILL.md, tests/roster/test_architect_design_reviewer_projection.py

**Tests:**
- `test_gate_script.py` loads `check_document_architecture.py` by
  `importlib.util.spec_from_file_location` under the pack-unique name
  `architect_design_gate_script`, matching `test_profile_repo.py:23`. A bare
  `import` would bind whichever `scripts/` directory reached `sys.path` first
  (AC-0001).
- The module's import set is read with `ast` and compared against
  `sys.stdlib_module_names` plus the one co-located sibling, so any other
  import fails — including `agentbundle`, which would pass a runtime smoke
  test in this repository and fail in every adopter install (AC-0002).
- The sibling load is driven against three sabotages — the module absent,
  replaced by a symlink, and truncated so a helper is missing — and each must
  exit non-zero through the script's own refusal channel with no traceback
  (AC-0075). `tests/roster/test_policy_family_selector.py:435-466` sets that
  depth for the same shape.
- The sibling module's import set is read with `ast` and required to be
  standard-library only (AC-0077), because AC-0002's check reads the gate
  script and never sees a module loaded by path.
- An assertion requires the spec to record that the copy is hand-maintained
  and that nothing regenerates it (AC-0079). `make build-self` writes no
  destination under `packs/`, so a byte pin proves the copy matches today and
  says nothing about it staying matched; a reader who assumes regeneration
  would trust it further than it goes.
- `scripts/file_safety.py` is asserted byte-identical to
  `packs/core/.apm/skills/close-work/scripts/file_safety.py` — the source of
  truth, not the generated `catalogue_tooling` copy (AC-0073). The assertion
  goes in `tests/roster/test_architect_design_reviewer_projection.py`, which
  `build-check.yml:546` already names, so it adds no roster module and owes
  none of the three obligations `tests/AGENTS.md` attaches to one (AC-0074).
  Architect carries a sibling precedent at
  `tests/roster/test_architect_assess_profiler_integration.py`, which pins
  `profile_repo._safe_read` against the canonical helper's behaviour.
- `read_target` is driven with the helper monkeypatched to raise
  `UnsafeContentError`, and the gate's refusal type must carry that path and
  reason — which fails if the wrapper decides confinement itself rather than
  delegating (AC-0011). A second case asserts the wrapper passes the caller's
  path through unresolved, since canonicalizing first would collapse the
  symlink components the helper's walk exists to inspect (AC-0076).
- `main()`'s stream setup is driven with `sys.stdout` patched by a recorder
  that requires `reconfigure` to be its first call; asserting the call
  happened would pass on a script that printed first (AC-0003).
- The CLI entry point is driven for 0, 1 and 2 (AC-0004); for a two-target run
  pairing a finding with a refusal, which must exit 2 (AC-0005); and for the
  same run asserted to have still reported the finding and a refused count,
  which separates "2 dominates" from "2 aborts" (AC-0006).
- `read_target`'s refusal type is asserted to carry the path and the reason,
  and the stderr rendering to print both (AC-0007).
- `_parser()` is asserted to make `--root` required, so invoking without it is
  a usage error rather than a run against the working directory (AC-0008).
- `read_target` is driven with a root that is itself a symlink, requiring a
  target under the real directory to be accepted — which fails when only the
  target side is canonicalized (AC-0009).
- `read_target` is driven against real filesystem entries built by the test,
  one per row of the refusal table, each asserting the refusal *reason*: a
  regular file under a symlinked parent whose real path leaves the root
  (AC-0010); a directory, a FIFO, a symlink and a second-hard-link file
  (AC-0011); a file one byte over 1,048,576 with its sibling one byte under
  accepted (AC-0012); a symlink loop, which must refuse rather than raise
  (AC-0013).
- `count_sentences`' pattern *source text* is scanned for a nested quantifier
  and for alternation inside a repetition (AC-0014). Not `re` parse
  introspection: that parser has no public API and was renamed `sre_parse` →
  `re._parser` in CPython 3.11, so a check on it breaks on a version bump, and
  the property is decidable from the string.
- The finding and refusal renderers are driven with a filename containing a
  newline and a terminal escape, and the report asserted to hold one line per
  finding (AC-0015).
- `prose_paragraphs` and `count_sentences` are driven over fixtures built in
  the test, one per false-positive source in Design → Failure (AC-0019,
  AC-0020, AC-0021), and at 3 and 4 sentences, pinning the budget on both
  sides (AC-0017).
- **`test_da3_reports_no_finding_in_any_shipped_asset` is removed**, along
  with the stale `AC-0018` reference in its section header and the
  `ASSETS_DIR` module constant, whose only consumer it is. That criterion is
  verified in T4a now, not here. The test asserts the clean corpus AC-0018 no
  longer states and is red on `assets/design-doc.md:25` today; a withdrawn
  criterion surviving as a live assertion is the withdrawal half-done, and
  ruff does not flag an unused module-level assignment, so the constant would
  outlive it silently.
- **The clean-corpus half belongs to T4a**, not here: AC-0018 runs against the
  reference document, which T4a creates. T4a already depends on this task
  through T3 and T4, so a clean-corpus check placed here could never see that
  file — this is the canonical statement of that ordering, and the other
  mentions defer to it.
- `count_words` is asserted at exactly the bound and one over (AC-0023), and
  the finding renderer asserted to carry path, line and count (AC-0022).
- An assertion over `SKILL.md` requires it to state that the agent running the
  skill does not invoke the script (AC-0016).

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
  whole-file `assertIn("3,300", text)` passes on any second mention of the
  bound, and seven prechecks in one file cross-satisfy each other.
- Inside `DA10`'s body: the derivation's counted features and its multiplier,
  with the test recomputing the arithmetic and requiring it to reach the
  stated bound (AC-0024); the handoff naming
  `references/decomposition-rubric.md` with the disclaimer of split authority
  (AC-0026); the companion-views-and-evidence-links remedy (AC-0027).
- Inside each hybrid's body, its precheck: `DA1` (AC-0038), `DA2` (AC-0039),
  `DA4` (AC-0040), `DA6` (AC-0035), `DA7` (AC-0036), `DA8` (AC-0037), `DA9`
  (AC-0041); each stating the verdict is the reviewer's (AC-0042); each
  stating it applies to an authored document (AC-0047); and `DA9` scoped to a
  routed document (AC-0047). The helper also counts the prechecks: exactly
  seven, one per hybrid, and none under `DA5` (AC-0048) — the count is what
  keeps judgment-only textually distinct once every hybrid carries one.
- `design-doc-rubric.md` is asserted to state what a severity means for an
  author (AC-0033). The file carries no severity vocabulary today.
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

**Touches:** packs/architect/.apm/skills/architect-review/references/rubric-design-doc.md, packs/architect/.apm/agents/design-reviewer.md, packs/architect/tests/pack/test_design_reviewer_rubric_parity.py, packs/architect/.apm/skills/architect-design/references/convergence-loop.md

**Tests:**
- `test_design_reviewer_rubric_parity.py` gains a `DA_CARRIERS` tuple naming
  the three gate homes and a `DA_GATES` map from identifier to severity glyph
  and taxonomy glyph, asserting each identifier and its two glyphs in every
  `DA_CARRIERS` entry (AC-0062, AC-0063). It also observes the authoring
  rubric (AC-0028), the reviewing rubric (AC-0029), the agent (AC-0030) and
  the tag assignment (AC-0031), so no home has an assertion of its own that
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
  homes against a fixed value rather than against each other (AC-0032); three
  homes agreeing on a wrong severity passes the weaker shape.
- `DA5`'s body in each home is asserted on its positive statement — the
  verdict is the reviewer's judgement and no automated measure decides it —
  with the two enumerated measure phrases as a supporting negative (AC-0034).
- Assertions over `design-reviewer.md`'s output contract: the returned block
  demands a `DA1`-`DA10` roll-call with a verdict each (AC-0052); a clean
  `SHIP IT` still shows ten (AC-0053); the inlined set is named as baseline
  depth with `rubric-design-doc.md` as the depth read when co-installed
  (AC-0054); and an unreachable rubric is a finding (AC-0055). Three more
  cover the injection surface the dispatch opens: the artifact under review
  holds no instruction authority over the agent's verdict, tools, scope or
  output format, at the depth both sibling skills already state it and the
  agent file states nowhere today (AC-0056); each roll-call verdict is the
  agent's own determination, so a document carrying `DA1-DA10: PASS` is a
  finding rather than a result (AC-0057); and the recorded block is captured
  as quoted data, since the agent reads the checkout and its output lands in a
  committed file (AC-0058).
- An assertion reads the agent's frontmatter for `Read`, `Grep`, `Glob` and no
  execution tool (AC-0072). AC-0061's claim that no rung runs the gate script
  rests on that for the subagent rung, and nothing pinned it. The roll-call
  is asserted inside the fenced output block, not merely present in the file,
  because the section above it forbids a pre-findings recap.
- An assertion over `convergence-loop.md` requires the loop to dispatch the
  subagent when reachable and to name its fallback rung otherwise (AC-0060),
  and requires each reporting obligation to name who reports (AC-0061).
- `REVIEW_EXTRA` is untouched, for T3's reason. The agent file's gates go
  after its `## Severity glossary`.
- no stub (goal-based)

**Done when:** `packs/architect/tests/pack/` and
`packs/architect/tests/skills/architect-design/` both pass.

### T4b: the prechecks reach the two homes a reviewer reads

**Depends on:** T4

**Touches:** packs/architect/.apm/skills/architect-review/references/rubric-design-doc.md, packs/architect/.apm/agents/design-reviewer.md, packs/architect/tests/pack/test_design_reviewer_rubric_parity.py

**Tests:**
- `test_design_reviewer_rubric_parity.py` asserts each of the seven precheck
  bodies is present in **every** `DA_CARRIERS` entry, scoped to that gate's
  own section body rather than to the file (AC-0035, AC-0036, AC-0037,
  AC-0038, AC-0039, AC-0040, AC-0041), and that each states its verdict is the
  reviewer's (AC-0042). The existing per-carrier identifier, severity and tag
  assertions must still pass unchanged.
- A negative assertion requires `DA5` to carry no precheck in any carrier
  (AC-0047), which is the count that keeps judgment-only distinct once every
  hybrid has one.
- no stub (goal-based)

**Approach:**
- **Why this is a task and not a widening of T4.** T4 is complete and its
  section cannot be edited, so the correction is a new dependency-ordered
  task. The obligation itself is not new: the prechecks group's preamble binds
  every criterion in it to all three homes, and the plan assigned those
  criteria to T3, whose `Touches:` reaches only the authoring rubric. The
  three-home obligation therefore had no owning task that could satisfy it.
- The precheck text already exists in `design-doc-rubric.md`'s `#### DA<n>`
  bodies. Carry the same obligations across rather than re-authoring them; the
  homes may condense the prose, but a reviewer reading either one must be able
  to tell a hybrid from `DA5` without opening the authoring rubric.

**Done when:** `packs/architect/tests/pack/` and
`packs/architect/tests/skills/architect-design/` both pass, and the word
`precheck` appears in all three `DA_CARRIERS` entries.

### T4a: the prechecks are walked against a document, not a template

**Touches:** packs/architect/tests/skills/architect-design/testdata/telemetry-endpoint-default-design.md, packs/architect/tests/skills/architect-design/testdata/precheck-defects.md, packs/architect/tests/skills/architect-design/test_gate_text.py, docs/specs/architect-design-document-gates/notes/verification-ledger.md

**Depends on:** T4b — AC-0059 copies `design-reviewer.md` and dispatches it,
so the dispatch must read the agent after T4b's precheck bodies land, not
a definition this slice edits again afterwards.

**Tests:**
- The reference document is committed at
  `testdata/telemetry-endpoint-default-design.md`, and `test_gate_text.py`
  asserts it carries no `<…>` placeholder token, so a half-filled skeleton
  cannot serve as the corpus (AC-0045).
- `DA3` is driven over the reference document and must report nothing
  (AC-0018). This is the clean half of the paragraph budget, placed here for
  the reason T2's `Tests:` records.
- The reference document's measured word count is compared against the
  derivation's 2,178-word density figure and must sit within 20% (AC-0025).
  This is what gives AC-0024 an oracle: recomputing 2,178 × 1.5 → 3,300 is
  true by construction whatever the inventory leaves out.
- `test_gate_text.py` asserts the **reference document's own header** states
  that its corpus purpose governs an edit to it (AC-0044): it is a baseline,
  so a design improvement nobody re-walks invalidates the recorded walk. The
  assertion reads `testdata/telemetry-endpoint-default-design.md`, not this
  spec — a pack test may not climb to `docs/`
  (`tools/lint-pack-test-boundary.py` check 8), and a test asserting that the
  spec says something makes the spec its own comparison value.
- The defect document states in its own body that it is deliberately
  non-conforming, and the plan records how a repository-wide Markdown reader
  tells it apart: `tools/lint-agents-md.py:547` walks `rglob("*.md")` and
  excludes on the path parts `fixtures` and `tests`, neither of which
  `testdata/` matches (AC-0050).
- A defect document is committed at `testdata/precheck-defects.md` carrying
  one planted defect per precheck (AC-0049), and `test_gate_text.py` asserts
  it names all seven.
- **Both directions, walked by hand and recorded** in
  `notes/verification-ledger.md`: no precheck fires on the reference document
  (AC-0046), and every precheck fires on its planted defect (AC-0051). One
  direction alone is satisfied by a precheck that never fires on anything.
- A scan over every artifact this delivery commits requires no real
  home-directory path or account name, across transcripts, recorded blocks,
  fixtures and corpus files alike (AC-0043), and the plan names where a
  standing check for that class lives rather than leaving it to review
  Every transcript and recorded block this task commits is
  host-clean: the
  root path is written as a placeholder, never as a real absolute path
  (AC-0043). `--root` is required, so a typed transcript otherwise carries an
  operator's account name into a published repository, which root
  `AGENTS.md` § Security considerations forbids — five ledgers under
  `docs/specs/*/notes/` already carry one.
- **The branch's `packs/architect/.apm/agents/design-reviewer.md` is copied to
  `.claude/agents/design-reviewer.md`, the agent is dispatched** against the
  reference document, its returned block is recorded in the ledger showing ten
  verdicts, and the copy is removed in the same step (AC-0059). Copying is the
  point: without it the dispatch reads whatever the operator's profile holds,
  today 8,633 bytes against the pack source's 9,140. Project scope is the
  destination because it is inside the working tree and git-visible;
  overwriting `~/.claude/agents/` would replace a machine-wide definition for
  every project on the host and leave it replaced. The
  agent resolves from either scope a host reads: `.claude/agents/` in the
  repository, or the operator's user profile. This repository sets
  `catalogue.toml:21` `self-host = false`, so architect's agent is absent from
  project scope here and resolves from the user profile; an adopting team that
  installs the pack in-repo gets it for every contributor and for CI. The
  record names which scope the dispatch used, because that is what decides
  whether the evidence is the team's or one operator's.
- no stub (manual QA for the two walks, goal-based for the documents)

**Approach:**
- **The corpus is real pending design work, not a fixture.** It is the
  subsystem design for layer 5 of the telemetry endpoint cascade —
  `catalogue.toml` `[pack-defaults.core]` baked into
  `_data/install-defaults.toml`, the one layer of the five in
  `docs/product/intents/catalogue-level-telemetry-endpoint-default.md`
  § Future state that no component can currently read. Layers 1-4 shipped with
  `telemetry-sender-owns-its-configuration`; `loop-telemetry-export` is
  Shipped and `jsonl-otlp-exporter` is Approved, so the exporter works and an
  enterprise still cannot configure it once for all its users.
- It is a subsystem design because it has a subsystem's shape: a precedence
  chain with a stated fall-through rule, a trust boundary between enterprise,
  repository and user scope, a standard-library-only consumer constraint, and
  an explicit refusal of authenticated endpoints. A design written to exercise
  a rubric would have none of those.
- The document lands only in `testdata/`. A second copy under `docs/` would
  give one design two homes, and a pack test cannot read `docs/` —
  `tools/lint-pack-test-boundary.py` check 8 refuses it. Promotion to an
  accepted design artifact belongs to the telemetry intent's own owner.

**Done when:** both documents are committed, both walks are in the
verification ledger with no precheck firing on the reference document and
every precheck firing on its defect, and the dispatched review's returned
block in the ledger showing ten verdicts.

### T5: the loop reports every gate and its contract stops contradicting itself

**Depends on:** T3

**Touches:** packs/architect/.apm/skills/architect-design/SKILL.md, packs/architect/.apm/skills/architect-design/references/convergence-loop.md

**Tests:**
- `test_gate_text.py` asserts over `SKILL.md` step 6 and over
  `convergence-loop.md`'s cycle that each demands a per-identifier verdict,
  as the closed set `DA1`-`DA10` plus the word verdict rather than the phrase
  "report the gates" (AC-0064, AC-0065). The failure this slice closes is a
  gate producing no finding because nothing asked it to, so "reported every
  gate" is the property and a generic instruction is a consequence of it.
- An assertion pins the corrected contract sentence at
  `convergence-loop.md:6-7`: the loop requires and invokes no script
  (AC-0066).
- A second assertion covers `convergence-loop.md:9`, "A script would forfeit
  the pack's pure-markdown, zero-config, portable property" — the sentence
  this slice falsifies. It is replaced by a statement of what the shipped
  script does and does not cost, and the unconditional claim must be absent
  (AC-0067).
- The edits stay outside the `agentbundle:output-rendering` markers and
  outside the pinned description regions; step 6's body is neither.
- no stub (goal-based)

**Done when:** the suite passes and `git diff` shows no line inside any marker
span.

### T7: the pack release closes

**Depends on:** T2, T3, T4, T4b, T4a, T5

**Touches:** packs/architect/pack.toml, packs/architect/.claude-plugin/plugin.json, docs/product/changelog.md, packs/architect/.apm/skills/architect-design/evals/evals.json, .claude-plugin/marketplace.json

**Tests:**
- `python3 -m pytest tests/conformance/test_pack_metadata.py -q` owns the
  `pack.toml`/`plugin.json` equality (AC-0068); this task does not restate
  that comparison.
- `FORCE=1 make build-self` regenerates `.claude-plugin/marketplace.json` and
  refuses a dirty tree, so the version bump commits before it runs. The
  regenerated file is read back for architect at `0.15.12` (AC-0071) — a
  projection is verified by regenerating it, never by editing its bytes.
- The eval's expectation text is asserted against the closed set: it must name
  every identifier `DA1` through `DA10` with a verdict (AC-0070). Requiring
  only that an eval mentions the gates lets the implementation write its own
  comparison value.
- The changelog entry is decided by `tools/test_build_site_routing.py`, which
  `build-check.yml:357` runs on every pull request (AC-0069). Three of its
  tests read the real file:
  `test_the_real_changelog_has_no_silently_withheld_highlights` (`:2156`) reds
  when a `### Highlights` block is not its release entry's immediate child,
  `test_every_changelog_section_is_separated` (`:2268`) checks heading
  separation, and
  `test_no_projected_release_heading_lives_under_an_unreleased_region`
  (`:2332`) walks the raw file for nesting under `[Unreleased]`. The dated
  heading form is the part they do not decide;
  `tools/test_build_site_routing.py:908` is where `/now/` eligibility
  requires it.
- no stub (goal-based)

**Approach:**
- The Highlights verdict is answered before the entry is written: this change
  gives an adopter a runnable gate script and ten named checks their reviewer
  did not have, so the answer is yes and the bullets are drafted.

**Done when:** `FORCE=1 make build-self` succeeds on a clean tree and the
changelog entry stands free at `##` with its dated heading and its Highlights
subsection.

## Rollout

- **Delivery:** big bang, fully reversible. Repository and pack content only:
  T4a's dispatch copies the agent definition to `.claude/agents/` inside the
  working tree and removes it in the same step, so nothing outside the
  repository is written and a revert is a revert.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** T7 last, because the changelog entry describes
  the finished set and `make build-self` refuses a dirty tree. Nothing else
  is ordered by deployment; the task graph's dependencies carry the rest.

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

- 2026-09-18: spec approved by eugenelim
- 2026-09-18: plan approved by eugenelim
- 2026-09-19: spec re-approved by eugenelim after the AC-0019 amendment
- 2026-09-19: plan re-approved by eugenelim after the AC-0019 amendment
