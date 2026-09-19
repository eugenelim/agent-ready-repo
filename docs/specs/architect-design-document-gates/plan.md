# Plan: architect-design document-architecture gates

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** ADR-0118 `D5` fixes the gate set and its
  mechanizability. Two analogous shipped implementations:
  `packs/architect/.apm/skills/architect-assess/scripts/profile_repo.py` (a
  pack skill shipping its own standard-library script inside `.apm/`, with its
  UTF-8 stream reconfiguration at lines 952-955) and
  `packs/core/.apm/skills/new-spec/scripts/lint-contract-item-alignment.py` (a
  skill shipping its own lint). Their construction path is
  `packs/architect/tests/skills/architect-assess/test_profile_repo.py:23`,
  which loads the script by `importlib.util.spec_from_file_location` under a
  pack-unique module name. Named deviation: none on confinement. This script
  copies `profile_repo.py`'s actual shape rather than a simplified reading of
  it — an unconditional standard-library check plus the blessed
  `agentbundle.catalogue_tooling.file_safety` helper when the import succeeds.
  The adopter constraint is that the helper cannot be *required*, not that it
  must be declined.

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

The gating change lands first and alone, so every later commit in this slice is
proven by the pull request rather than by a dispatch. The script follows,
because its behaviour is what the rubric text then describes. The three rubric
homes and the parity test move together in one commit: a home written without
the test that compares it is the drift this slice exists to stop. Release
closure is last, since its changelog entry describes the finished set.

The riskiest part is `DA3`'s parser. A prose-paragraph gate that reds on
correct prose is deleted by the next maintainer, so it is tuned against the
five shipped assets and must show zero findings there before it is trusted,
and must show a red on a deliberately non-compliant fixture before it is
believed. Both halves are recorded, not just the green one.

## Constraints

- **ADR-0118 `D5`** fixes the ten identifiers and each one's mechanizability.
  The plan implements that table and re-decides none of it.
- **ADR-0118 `D4`** owns the `D1`–`D6` decomposition criteria, a different
  namespace from the ADR's own `D1`–`D6` constraint addresses.
- **`packs/AGENTS.md` § Shipped pack content carries no internal-governance
  citations** — nothing under `packs/` cites ADR-0118.
- **`packs/AGENTS.md` § Version bump rule** — matching `pack.toml` and
  `.claude-plugin/plugin.json` bumps.
- **`packs/AGENTS.local.md:26-40`** — marketplace regeneration, free-standing
  changelog entry, explicit Highlights verdict.
- **`docs/specs/architect-design-scope-templates/spec.md` is frozen at
  `Shipped`.** The supersession takes the `Status`-line form in `new-spec`'s
  `references/spec-and-plan-contract.md` § *Superseding a frozen document*,
  which points at the ADR and not at this spec.

## Construction tests

One cross-cutting test spans T3 and T4: the same ten identifiers and severities
must agree across three files that no single task owns alone. It lives in
`packs/architect/tests/pack/test_design_reviewer_rubric_parity.py` under a new
`DA_CARRIERS` constant, deliberately separate from the module's existing
`CARRIERS`.

**The two carrier sets are different, and that is the point.** `CARRIERS`
(lines 43-47) is `architect-review/SKILL.md`,
`architect-review/references/rubric-well-architected.md` and
`.apm/agents/design-reviewer.md` — the homes of the verdict, severity and
taxonomy vocabulary. The gate homes are
`architect-design/references/design-doc-rubric.md`,
`architect-review/references/rubric-design-doc.md` and that same agent file.
One file overlaps. Folding the gates into `CARRIERS` would assert the gate
identifiers against two files that must not carry them and would leave the
authoring rubric unchecked, so the module holds two named sets and its
docstring says which obligation each one serves.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale (ADR-0118 `D5`) | T3, T4 | The parity test green against the `D5` identifiers and tags | The ten shipped gates and their mechanizability read back against `D5` |
| Release history (changelog) | T7 | The dated free-standing entry exists | The Highlights verdict is recorded either way |
| Maintainer procedure (three rubric homes) | T3, T4 | `test_design_reviewer_rubric_parity.py` green | Every identifier, tag and severity agrees in all three homes |
| Interface compatibility (script exit codes) | T2 | The exit-code and refusal tests green | The typed-command transcripts in `notes/verification-ledger.md` |
| Reusable learning | T7 | — | A `project-knowledge` receipt or the unavailable record |

## Design (LLD)

### Design decisions
Owned by: T2, T3, T4.

**The gate script is one module, not two.** `DA3` and `DA10` share the same
document model — strip YAML frontmatter, strip HTML-comment spans, then walk
what remains. `DA10` counts the words that survive; `DA3` further classifies
the surviving lines into prose and non-prose. Splitting them into two scripts
would duplicate `strip_excluded`, which is the part they genuinely share.
Past that point the two diverge on purpose: `DA10` counts everything that
survives it, while `DA3` further excludes fences, tables, list items, block
quotes and headings, because a table row is not a prose paragraph but its
words are still words in the document.

**Why the taxonomy glyph carries the mechanizability, and not a third token.**
The pack already ships a decidable two-value test — 🔧 when the fix is fully
determined, 🧭 when a human must choose — and `architect-design`'s convergence
loop routes on exactly those two tokens. ADR-0118's three-value column collapses
onto them by asking who decides: `Mechanizable` is 🔧, and both `Hybrid` and
`Judgment-only` are 🧭, because a hybrid's verdict is a reviewer's. A third
token would be a new interop value every carrier and the convergence loop would
have to learn, for a distinction the loop does not route on. The hybrids'
prechecks are what preserves the three-way distinction in the text, and `DA5`'s
stated absence of one is what preserves the difference between hybrid and
judgment-only.

**Why the two generic-rubric checks are neither moved nor copied.**
`rubric-generic.md`'s gratuitous-repetition and length-proportional-to-stakes
checks do not reach a design doc today, because a design doc routes to the
specific rubric (`architect-review/SKILL.md:56-71`). Three moves were
available and two are wrong. Moving the pair strips the genres
`rubric-generic.md` exists for — a strategy memo, a one-pager, a comparison
table have no other rubric. Copying the pair puts one concern in two homes,
inside the very file that ships `DA5`, "one concern, one home". Citing it is
also wrong here, and less obviously: the two checks sit at `###` level inside
`## Generic checks (when no specific rubric fits)`, a section whose caption
disclaims exactly the case a design-doc reviewer is in, so the pointer would
send a reader somewhere that tells them they are in the wrong place. So
neither: `DA5` owns gratuitous repetition at greater strength, and `DA10`
owns proportional length with a derived bound. The concerns reach a design
doc through the gates, and `rubric-generic.md` is untouched.

**Why the eight are checklist items, not a lint with a `--strict` flag.** A gate
written as a lint that no lint can decide goes green on the cases it cannot
see, which is worse than no gate: it converts an unchecked property into a
recorded pass.

**Why two existing rubric items are renamed rather than replaced.**
`test_design_scope_routing.py`'s `REPLACEMENTS` pins the strings
`the complete model set` and `one named question` as graded checklist items in
the authoring rubric — they are slice 1's record that four retired checks found
successors. `DA8` and `DA7` are those same obligations with an identifier and a
severity, so they are written onto the existing items in place. Deleting the
items and writing new ones elsewhere would red that anchor and would give one
obligation two homes on the way.

### Interfaces & contracts
Owned by: T2.

`check_document_architecture.py` takes one or more document paths and a
**required** `--root`. The root is required rather than defaulted, following
`profile_repo.py:935`: a default of the working directory makes a `make`
target, a CI step and a hand invocation each establish a different unstated
boundary, and a run from `/` confines nothing.

| Exit | Meaning |
| --- | --- |
| 0 | every target read, no finding |
| 1 | every target read, at least one `DA3` or `DA10` finding |
| 2 | at least one target refused |

**2 dominates 1.** A run that refuses one target and reports a finding on
another exits 2, because exiting 1 would tell the caller the gate ran cleanly
over a set that is silently missing a member. A refusal does not abort the
run: the remaining targets are still read, and the summary line states how
many were refused.

A finding prints as `<path>:<line>: DA3 — paragraph of N sentences (budget 3)`
or `<path>: DA10 — N words (bound 2400)`, with `<path>` escaped.

### Component / module decomposition
Owned by: T2.

Three pure functions and a thin CLI, so the tests call functions rather than
spawning an interpreter:

- `strip_excluded(text)` — removes YAML frontmatter and HTML-comment spans.
  Both gates consume its output; nothing else defines the exclusion set.
- `prose_paragraphs(text)` — yields `(start_line, text)` for each blank-line
  separated run of lines that is not a fence, table row, list item, block
  quote or heading. A fence is tracked as a span, because a table row inside a
  fenced block is not a table row.
- `count_sentences(paragraph)` — splits on terminal punctuation followed by
  whitespace and a capital, after masking the abbreviation set and decimals.
- `read_target(root, path, max_bytes)` — the one place a file is opened. It
  canonicalizes, checks the prefix, checks the file type and link count,
  checks the size, and raises a single refusal type carrying the path and the
  reason. Every refusal in the table below comes out of this function, so
  there is one home for the boundary rather than one per call site.

### Failure, edge cases & resilience
Owned by: T2.

**Two failure families, and they are not the same shape.** A parser
false positive is a wrong answer about a file the gate read; a refusal is the
gate declining to answer at all. Conflating them is how a zero-finding report
comes to cover a file nobody looked at.

The parser's false-positive sources are each a test: an abbreviation
mid-sentence, a decimal, a heading directly above wrapped prose, a multi-line
HTML comment containing four sentences, a fenced block containing a
pipe-delimited line, a nested list continuation line.

**The refusal set, and why each entry is there.** The gate reads documents in
an adopter's repository, which the skill's own `filesystem_read_untrusted`
boundary marks as untrusted. A refusal is a first-class outcome with its own
exit code, its own stderr line and its own precedence over a finding:

| Condition | Why it is a refusal rather than a read |
| --- | --- |
| real path not under the canonicalized root | the CWE-73 check; a resolved target compared against an unresolved root silently compares the wrong thing |
| not a regular file | a FIFO or character device opens cleanly and blocks forever, turning a CI gate into a hung job |
| more than one hard link, or a reparse point | the entry the gate stats is not necessarily the bytes it reads |
| larger than 1,048,576 bytes | a highly compressible `.md` is read whole into memory by `strip_excluded` |
| resolution raised | `Path.resolve()` raises `RuntimeError`, not `OSError`, on a symlink loop (CPython #109187), and `relative_to` raises `ValueError` on a non-prefix path, so the handler catches all three the way `profile_repo.py:279-281` does |

**Linear-time matching.** `count_sentences` masks abbreviations and decimals
by literal replacement, then splits on a pattern with no nested quantifier and
no alternation inside a repetition, so a pathological paragraph cannot force
backtracking. The property is measured against a growing adversarial input
rather than asserted, because a backtracking blow-up leaves the parse result
correct and only the time wrong.

**Rendering.** A path reaches stdout and stderr, and a path is attacker-chosen
data: a filename may legally contain a newline or a terminal escape. Every
emitted path is escaped so one finding occupies one line and no path can forge
a finding or rewrite a reader's terminal.

### Dependencies & integration
Owned by: T2.

The standard library is the floor, and `agentbundle.catalogue_tooling.file_safety`
is used on top of it when importable. This is exactly `profile_repo.py`'s
shape: `_safe_read` (`:294-312`) runs its own `resolve(strict=True)` plus
`relative_to(root)`, a `stat.S_ISREG` check, a reparse-point check, an
`st_nlink > 1` hard-link check and a byte budget unconditionally, and calls
`catalogue_read_confined_regular_file` in addition when the import succeeded.
An adopter without `agentbundle` therefore keeps every check; this repository
gets the blessed helper as well. Root `AGENTS.md` § Security considerations
blesses that helper, so declining it outright would be the deviation, not
using it.

## Tasks

### T1: the architect-design suite runs on a pull request

**Landed before approval,** in commit `81663a467` on this branch:
`.github/workflows/build-check.yml:435` names the directory inside the
`pytest catalogue-test carve-out destinations (RFC-0082)` step, and
`tools/lint-ci-parity.py:878-882` carries the matching `PR_GATED` disposition.
AC-0001 and AC-0002 hold in the tree today. The task stays in the plan because
every later task depends on it for its evidence, and a reader comparing the
criteria against the task graph should find the gating accounted for rather
than missing.

**Depends on:** none

**Touches:** .github/workflows/build-check.yml, tools/lint-ci-parity.py

**Tests:**
- `python3 tools/lint-ci-parity.py` exits 0, which decides AC-0001 and AC-0002
  in both directions: it fails when a step covers a suite whose roster entry
  says `NO_PR_GATE`, and fails when a disposition names no real step.
- no stub (goal-based)

**Done when:** the lint exits 0 and the step names the directory.

### T2: DA3 and DA10 red on a non-compliant fixture and green on the shipped assets

**Depends on:** T1

**Touches:** packs/architect/.apm/skills/architect-design/scripts/check_document_architecture.py, packs/architect/tests/skills/architect-design/test_gate_script.py, packs/architect/.apm/skills/architect-design/SKILL.md

**Tests:**
- A new suite `test_gate_script.py` loads the script by
  `importlib.util.spec_from_file_location` under the pack-unique name
  `architect_design_document_architecture_gate`, matching
  `test_profile_repo.py:23` — a bare `import` would bind whichever `scripts/`
  directory reached `sys.path` first. Loading it from that path is what
  observes AC-0003.
- The module's import set is read with `ast` and compared against
  `sys.stdlib_module_names` plus the single permitted optional
  `agentbundle.catalogue_tooling.file_safety`, so a third-party import fails
  rather than passing because this machine happens to have it installed
  (AC-0004). A second case simulates the import failing and requires every
  refusal in the table to still hold — the standard-library floor is the
  claim, and it is unobservable on a machine where the helper imports.
- The stream reconfiguration is asserted to precede the first write, by
  patching `sys.stdout` with a recorder and requiring `reconfigure` to be the
  first call it sees — asserting the call merely happened would pass on a
  script that printed first (AC-0005).
- The exit-code contract is driven through the CLI entry point: 0, 1, and 2
  (AC-0006); a two-target run pairing a finding with a refusal, which must
  exit 2 (AC-0007); and the same run asserted to have still reported the
  finding and a refused count, which is what separates "2 dominates" from "2
  aborts" (AC-0008).
- The refusal's stderr line is asserted to carry the refused path and the
  reason (AC-0009). A refusal that exits 2 silently leaves the caller unable
  to tell which target was skipped or why.
- `--root` is asserted absent-required: invoking without it is a usage error,
  not a run against the working directory (AC-0010). A second case roots the
  run at a symlinked directory and requires a target under the real directory
  to be accepted, which fails when only the target side is canonicalized
  (AC-0011) — on macOS `/tmp` resolving to `/private/tmp` makes this reachable
  without constructing anything exotic.
- Refusals are driven against real filesystem entries built by the test, one
  per row of the plan's refusal table: a regular file under a symlinked parent
  directory whose real path leaves the root, asserted on the out-of-root
  *reason* and not the exit code, because a symlinked target alone is refused
  by AC-0013 for its file type and never reaches the prefix comparison
  (AC-0012); a directory, a FIFO, a symlink, and a file with a second
  hard link (AC-0013); a file one byte over 1,048,576 (AC-0014), with its
  sibling one byte under accepted, so the boundary is pinned on both sides;
  and a symlink loop, which must refuse rather than raise (AC-0015). The loop
  case is the one that fails against a handler catching only `OSError`.
- AC-0016 is measured, not asserted: `count_sentences` runs against an
  adversarial paragraph at several lengths and the growth must stay linear. A
  result assertion cannot see backtracking, because the answer is still right.
- A target whose filename contains a newline and a terminal escape is required
  to render escaped, on both the finding line and the refusal line, and the
  report is asserted to hold exactly one line per finding (AC-0017).
- The green half drives `prose_paragraphs` and `count_sentences` over every
  `*.md` under `architect-design/assets/` by glob, the only corpus of this
  skill's own output that exists, and requires zero findings (AC-0020).
- The red half drives the same functions over fixtures built in the test, one
  per false-positive source named in Design → Failure: abbreviation, decimal,
  heading-above-prose, multi-line HTML comment, fenced pipe line, list
  continuation (AC-0021, AC-0022, AC-0023).
- `count_sentences` is asserted at 3 and at 4 sentences, so the budget's
  boundary is pinned on both sides rather than only above it (AC-0019).
- `DA10` is asserted at exactly 2,400 words and at 2,401, for the same reason
  (AC-0025).
- A finding's rendered line is asserted to carry the path, the line number and
  the count (AC-0024).

```python
# stub: true — the red contract surface, before the parser exists.
def test_da3_reports_a_four_sentence_paragraph() -> None:
    gate = _load_gate()
    para = "One. Two. Three. Four."
    assert gate.count_sentences(para) == 4
```

**Done when:** the suite passes, `SKILL.md` states that the agent does not
invoke the script (AC-0018), and the observations required by the `Tests:`
bullets are recorded — the shipped-asset run and the non-compliant-fixture run
are both reported, with their counts and exit codes.

### T3: the authoring rubric carries all ten gates

**Depends on:** T2

**Touches:** packs/architect/.apm/skills/architect-design/references/design-doc-rubric.md, packs/architect/tests/skills/architect-design/test_design_scope_routing.py, packs/architect/tests/skills/architect-design/test_gate_text.py

**Tests:**
- `test_the_authoring_rubric_names_only_sections_the_templates_have` must stay
  green **without** touching `AUTHOR_EXTRA`. The gates go under the existing
  `## Cross-cutting` heading as a `### Document architecture` sub-heading, so
  no new `##` heading appears. This is not a style choice:
  `architect-design-scope-templates`' own AC-0025 and AC-0031 are ticked
  criteria on that frozen `Shipped` spec stating that the
  only permitted non-template `##` headings are `Cross-cutting`,
  `Decomposition` and `Severity mapping (typical)`. Adding an eleventh would
  make two ticked criteria false, and this slice's own AC-0054 and its
  `Ask first` rule forbid amending them. Widening `AUTHOR_EXTRA` would make
  the test pass and the frozen contract false, which is the worse outcome.
- The existing `REPLACEMENTS` assertions stay untouched and must still pass,
  which is what proves `DA7` and `DA8` were written onto the pinned items
  rather than around them.
- The gate-presence and severity assertions for all three homes live in T4's
  parity test, not here, so one comparison owns AC-0029, AC-0030, AC-0031,
  AC-0032 and AC-0035 rather than three partial ones.
- A new module `test_gate_text.py` holds the gate-text
  assertions. **Every one is scoped to a single gate's section body, never to
  the file.** A helper slices the rubric on its `DA<n>` item boundaries and
  returns one body per identifier; a whole-file `assertIn("2,400", text)` is
  the failure mode this avoids, because it passes on any second mention of the
  bound — a summary table, a changelog line — without `DA10`'s definition ever
  stating it.
- Inside `DA10`'s body: the bound (AC-0026), and its derivation, which is
  asserted as the counted features the derivation rests on rather than as the
  number, since the number alone is what a bare figure already satisfies
  (AC-0026); the handoff naming `references/decomposition-rubric.md` together
  with the disclaimer of split authority (AC-0027); the
  companion-views-and-evidence-links remedy (AC-0028).
- Inside each hybrid's body, its precheck: `DA1` (AC-0039), `DA2` (AC-0040),
  `DA4` (AC-0041), `DA6` (AC-0036), `DA7` (AC-0037), `DA8` (AC-0038), `DA9`
  (AC-0042), and each one stating that its verdict is the reviewer's
  (AC-0043). Scoping matters most here: seven prechecks in one file would
  otherwise cross-satisfy each other.

- An assertion requires `design-doc-rubric.md` to state what a severity means
  for an author (AC-0034). The authoring rubric carries no severity vocabulary
  today, so this is the sentence that stops an author reading a reviewer's
  glyph as decoration.
- no stub (goal-based)

**Done when:** the architect-design suite passes and the rubric carries the ten
identifiers.

### T4: the reviewing rubric, the agent, and the parity test agree

**Depends on:** T3

**Touches:** packs/architect/.apm/skills/architect-review/references/rubric-design-doc.md, packs/architect/.apm/agents/design-reviewer.md, packs/architect/tests/pack/test_design_reviewer_rubric_parity.py, packs/architect/tests/skills/architect-design/test_design_scope_routing.py

**Tests:**
- `test_design_reviewer_rubric_parity.py` gains a `DA_CARRIERS` tuple naming
  the three gate homes and a `DA_GATES` constant mapping each identifier to its
  severity glyph and its taxonomy glyph, and asserts each identifier and its
  two glyphs appear in every `DA_CARRIERS` entry (AC-0047, AC-0048). The
  existing `CARRIERS` tuple is left alone; the module's docstring gains the
  sentence saying why there are two sets, so the obvious wrong edit — extending
  `CARRIERS` and expecting gate coverage to follow — is refused in writing. The constant is a literal in the test, not parsed from a rubric: a
  domain read from an artifact under test lets that artifact shrink its own
  coverage, the reasoning already recorded in
  `test_both_rubrics_cover_every_model_bearing_section`.
- Severity is asserted as the glyph adjacent to the identifier, not merely
  present in the file. Measured, the three carriers differ:
  `design-doc-rubric.md` holds none of 🟥🟧🟨⚪ or 🔧🧭 today,
  `rubric-design-doc.md` holds the four severity glyphs in its severity
  mapping and neither taxonomy glyph, and `design-reviewer.md` holds all six.
  A file-wide presence check would therefore pass on the wrong severity in two
  of the three, and pass vacuously in the third.
- `DA5` is checked by its positive statement — its section body must say the
  verdict is the reviewer's judgement and that no automated measure decides it
  — with the two enumerated measure phrases as a supporting negative (AC-0035).
  The positive carries the obligation, because a prohibition over the open set
  of things a measure can be called never converges.
- The same parity constant is what observes the authoring rubric (AC-0029),
  the reviewing rubric (AC-0030) and the `design-reviewer` agent (AC-0031)
  carrying the full identifier set with the right tags (AC-0032), so no home
  has an assertion of its own that could pass while another drifted.
- The severity map of AC-0033 is a literal in the test, so parity compares
  the three homes against a fixed value rather than against each other. Three
  homes agreeing on a wrong severity is a passing run under the weaker shape.
- `REVIEW_EXTRA` is likewise untouched, for the reason recorded in T3: the
  reviewing rubric's gates sit under its existing `## Cross-cutting` heading.

- no stub (goal-based)

**Done when:** `packs/architect/tests/pack/` and
`packs/architect/tests/skills/architect-design/` both pass.

### T4a: the prechecks are walked against a real document, not a skeleton

**Depends on:** T4

**Touches:** packs/architect/tests/skills/architect-design/testdata/filled-subsystem-design.md, docs/specs/architect-design-document-gates/notes/verification-ledger.md

**Tests:**
- A filled reference document is authored from `assets/subsystem-design.md`
  with every placeholder replaced by real content, and committed at
  `packs/architect/tests/skills/architect-design/testdata/filled-subsystem-design.md`
  (AC-0044). An assertion requires it to contain no `<placeholder>` token, so
  a half-filled skeleton cannot pass as the corpus.
- Each of the seven prechecks is walked by hand against that document and the
  walk written to `notes/verification-ledger.md` (AC-0045).
- An assertion requires the spec's stated reason for excluding the shipped
  assets from the corpus to be present (AC-0046).
- no stub (manual QA for the walk, goal-based for the document)

**Approach:**
- **Why this task exists at all.** The first two drafts of these prechecks
  were written against the shipped assets and both were wrong, in the same
  way: `DA7`'s caption trigger red on `subsystem-design.md:33`, and its
  replacement zoom trigger red on four of the twelve shipped diagrams,
  including `subsystem-design.md:52` whose cell is literally
  `<this diagram's zoom level>`. Measuring a finished-document check against
  a skeleton measures the skeleton's placeholders. There was no filled
  document in the repository to measure against, so this task makes one
  rather than asserting that a walk happened.
- The document is real content, not lorem: a precheck walked against filler
  tells you the filler's shape.

**Done when:** the reference document is committed, the seven-precheck walk
is in the verification ledger, and no precheck fired.

### T5: the loop reports every gate and its contract stops contradicting itself

**Depends on:** T3 (step 6 reports the identifiers the authoring rubric defines)

**Touches:** packs/architect/.apm/skills/architect-design/SKILL.md, packs/architect/.apm/skills/architect-design/references/convergence-loop.md

**Tests:**
- An assertion in the architect-design suite requires step 6's text to demand a
  per-identifier verdict report (AC-0049) and requires `convergence-loop.md` to
  demand the same of each pass (AC-0050). Both are asserted as the closed set
  `DA1`-`DA10` plus the word verdict, not as the phrase "report the gates":
  the failure this slice exists to close is a gate that produces no finding
  because nothing asked it to, so "reported every gate" is the property and a
  generic instruction is only a consequence of it.
- An assertion pins the corrected contract sentence: the loop requires and
  invokes no script (AC-0051). This replaces the current absolute "there is no
  script" wording at `convergence-loop.md:6-7`, which the shipped `scripts/`
  directory would otherwise falsify.
- A second assertion covers `convergence-loop.md:9`, "A script would forfeit
  the pack's pure-markdown, zero-config, portable property" — the sentence
  this slice actually falsifies, and the one a reader lands on. It is replaced
  by a statement of what the shipped script does and does not cost, and the
  unconditional claim must be gone (AC-0052).
- The edit stays outside the `agentbundle:output-rendering` markers in
  `SKILL.md` and outside the pinned description regions; step 6's body is
  neither.
- no stub (goal-based)

**Done when:** the suite passes and `git diff` shows no line inside any marker
span.

### T6: the superseded criteria point forward without moving

**Depends on:** none

**Touches:** docs/specs/architect-design-scope-templates/spec.md

**Tests:**
- `python3 '<skill-dir>/../work-loop/scripts/lint-spec-status.py' --root .`
  decides the status token (AC-0053). It owns status vocabulary and nothing
  else: that the pointer names the right ADR and scopes the right part is a
  reviewer's call, and no lint replaces it.
- The pull-request diff for that file is read and recorded in
  `notes/verification-ledger.md`; it must be exactly one line (AC-0054).
- **Deliberately not a standing test.** `tests/AGENTS.md` § *A
  repository-level assertion cannot live in a package test tree* puts such a
  test in `tests/roster/`, and its § *Roster is not auto-discovered* then
  obliges three more edits: a `build-check.yml` step naming the file, a
  matching `STEP_DISPOSITION` of `LOCAL("test-after-build-check")` in
  `tools/lint-ci-parity.py`, and — because the test would name a
  `docs/specs/<slug>` path as a literal — an entry in
  `.workspace-prune-protected.toml`, without which
  `test_two_sided_prune_closure_invariant.py:563-570` reds. That is four
  pieces of machinery to guard a frozen document which by convention takes
  only a `Status`-line edit, already watched by a reviewer and by the status
  lint's vocabulary check. Declined under `Cut before adding` rung 1, and
  written down so it reads as a decision rather than an omission.
- no stub (goal-based)

**Done when:** the `Status` line names ADR-0118 and the part superseded, and
the recorded diff for that file is one line.

### T7: the pack release closes

**Depends on:** T2, T3, T4, T5 (the changelog entry describes the shipped set,
and `FORCE=1 make build-self` refuses a dirty tree)

**Touches:** packs/architect/pack.toml, packs/architect/.claude-plugin/plugin.json, docs/product/changelog.md, packs/architect/.apm/skills/architect-design/evals/evals.json, .claude-plugin/marketplace.json

**Tests:**
- `python3 -m pytest tests/conformance/test_pack_metadata.py -q` owns the
  `pack.toml`/`plugin.json` equality (AC-0055); this task does not restate that
  comparison.
- `FORCE=1 make build-self` regenerates `.claude-plugin/marketplace.json` and refuses a dirty
  tree, so the version bump commits before it runs. The regenerated file is
  read back for architect at `0.15.12` (AC-0058) — a projection is verified by
  regenerating it, never by editing its bytes.
- The changelog entry is read by hand and the result recorded (AC-0056).
  **No pull-request gate checks it.** `build-check.yml` names changelog
  nothing at all, and `pages.yml`'s release-anchor job compares anchors
  against built HTML, so it cannot see position, nesting, or a `### Highlights`
  subsection. The check is the dated free-standing heading and the Highlights
  block, read and recorded in `notes/verification-ledger.md`; attributing it
  to a gate would be attributing it to nothing.
- The eval is asserted against a closed set: its expectation text must name
  every identifier `DA1` through `DA10` with a verdict (AC-0057). Requiring
  only that an eval "mentions the gates" would let the implementation write its
  own comparison value.
- no stub (goal-based)

**Approach:**
- The Highlights verdict is answered before the entry is written, not after:
  this change gives an adopter two runnable gates and ten named checks their
  reviewer did not have, so the answer is yes and the bullets are drafted.

**Done when:** `FORCE=1 make build-self` succeeds on a clean tree and the
changelog entry stands free at `##` with its Highlights subsection.

## Rollout

- **Delivery:** big bang, fully reversible. Everything is repository content
  and pack content; a revert is a revert.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** T1 before everything, so the rest of the slice is
  proven by the pull request rather than by a dispatch. T7 last, because the
  changelog entry describes the finished set and `make build-self` refuses a
  dirty tree.

## Risks

- **`DA3` reds on correct prose and is deleted by the next maintainer.** The
  five shipped assets are the whole available corpus of this skill's own
  output, and they are placeholders rather than finished documents, so a
  green there is weaker evidence than a green on real output would be. The
  mitigation is that every false-positive source found while prototyping is a
  named test rather than a tuned constant.
- **The three rubric homes drift in the next slice.** The parity test is the
  mitigation, and its stated limit is inherited: an allowlist does not
  auto-discover a newly added identifier, so slice 3 adding a `DA11` must add
  it to the constant by hand.
- **`FORCE=1 make build-self` refuses a dirty tree**, which strands T7 if the
  version bump is left uncommitted. Sequenced in T7's `Approach:`.

## Changelog

<!--
- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->
