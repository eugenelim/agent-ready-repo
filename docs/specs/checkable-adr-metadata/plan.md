# Plan: Checkable ADR metadata

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** conventions from root `AGENTS.md` § Coding conventions,
  `packs/AGENTS.md` §§ "Security and authoring rules", "Shipped pack content
  carries no internal-governance citations" and "Self-hosting projection", and
  [`docs/README.md`](../../README.md); three analogous production
  implementations — the two shipped record-directory scripts
  `packs/governance-extras/.apm/skills/new-adr/scripts/index-records.py` and
  `next-ordinal.py`, which carry the confinement idiom this change extracts and
  the index generator it changes, and `packs/core/.apm/skills/work-loop/scripts/`,
  which supplies both halves of the helper pattern: `file_safety.py` for the
  confinement semantics and `check-spec-status.py:69-114` for the by-path
  sibling load and its refuse-on-failure posture; their construction path is
  `tools/repo/build_gate_chain.py:258-278` and their tests are
  `tests/roster/test_index_records.py` and
  `packs/governance-extras/tests/skills/new-adr/test_next_ordinal.py`. Named
  deviation: RFC-0102 § 6 says the lint ships in two copies; this plan ships one,
  on the sibling precedent, recorded in the spec's Assumptions.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md`. A genuine artifact error
> follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material: an implementer corrects them in place as the
> work teaches, without an amendment and without a review round.

## Approach

The corpus arrived migrated, so this delivery ships a gate rather than a
worklist. That inverts the original sequencing: instead of a lint that tolerates
559 findings, the lint blocks on any finding, and the delivery must leave the
corpus passing it. The residual the spec's Assumptions state stands between
here and that, and clearing it forces the index-generator change in — the two
records it names carry
their supersession pointer only in `Status` text, so bare-tokening them without
teaching the generator to read `Superseded by:` would silently drop two rows'
pointers from a generated index.

The shared confinement helper still comes first. Extracting it before the lint
is what makes one reviewed copy possible: writing the lint first would produce a
third hand-made copy of an idiom whose weaker form was already shipped once and
repaired (`index-records.py:194-196`), and extracting afterwards is a refactor
nobody schedules. The same task gives the two existing scripts' regression suite
a pull-request-gated home, because a confinement control whose only assertions
run on dispatch can regress into a merge with every required gate green.

Prose lands after the lint, because the lint is what makes a prose claim
checkable. The corpus work lands after the gate step exists, so the closing
observation is the real gate running over the real corpus.

The riskiest part is the mirrored supersession pair. Every other check reads one
file; `ADR-S009` and `ADR-S010` need the whole directory resolved first, and
`ADR-S010` must attribute one broken pair to two files. That is why the script
parses every record into a record map before evaluating any cross-record rule,
and why an `ADR-S008` fixture necessarily reports `ADR-S010` alongside it.

## Constraints

- [RFC-0102](../../rfc/0102-mechanically-checkable-adrs.md) — accepted; owns the
  field set, the parse tiers, the mutability zones and the supersession grammar.
  Its § 6 two-copy claim is narrowed to one copy. Its § 7 sequencing
  precondition — generator before bare-token statuses — is live and binding on
  T9. Its advisory-then-blocking posture is a named deviation: the RFC still
  states it at `:18`, `:336` and `:562` after commit `2eb5e01ed` ("scope RFC-0102's evidence to mechanism, not one corpus"), and this
  delivery ships blocking because the flip's stated precondition, a migrated
  corpus, was met by `4b2714112`. A peer session owns the RFC's own text.
- [ADR-0027](../../adr/0027-adr-format-is-madr-aligned-but-lean.md) — deferred
  this lint; T10 records both the discharge and the D5 override on the record.
- [ADR-0112](../../adr/0112-index-tables-are-generated-or-absent.md) —
  `docs/adr/README.md` is generated, so T9 and T10 regenerate rather than edit.
- `packs/AGENTS.md` — `.apm/` scripts canonicalize before every read; a skill's
  `scripts/` is never put on `sys.path` for a bare-name import; any such script
  writing to stdout or stderr reconfigures both to UTF-8 first; shipped pack
  content cites no repository-only paths; a non-cosmetic pack update also
  updates that pack's eval harness; `.apm/` is the source of truth.
- `tools/lint-pack-test-boundary.py` check 8 — a pack test may not climb above
  its own pack. This is why the corpus walk is in `tests/roster/`, why the
  guide's `Related:` observation is T7's and not `LS`'s, and why T5's template
  check is expressed against a literal placeholder form rather than against
  whether an ordinal resolves.
- `tools/AGENTS.md` — a `build-check.yml` step needs a matching
  `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py`.
- `packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py:518-527`
  — CAT-S003 warns above 500 body lines and errors only above 1000, so T6
  asserts the body line count directly rather than reading the lint's verdict.
- `packages/agentbundle/agentbundle/build/self_host.py:386-414` — `is_dirty_tree`
  reads `git status --porcelain`, so `make build-self` refuses while any task's
  own new file is uncommitted. T4 and T9 state their commit points rather than
  assuming a clean tree.

## Construction tests

**Integration tests:** none beyond per-task tests. The cross-task property —
a record authored from the shipped template passes the shipped lint — is
verified inside T5 against the real template, and again in T10 against the real
record.

**Manual verification:** T10 invokes the built lint against the new decision
record and records the observed exit code and output in the verification ledger.
This is the spec's Testing Strategy manual-QA item and a fixture pass does not
substitute for it.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Shared confinement helper | T1, T3 | Both existing scripts' suites green; both shipped pairs pinned byte-identical | One definition per shipped skill, pinned identical; no script left carrying the old inline idiom |
| Template | T5 | Template-derived record passes the lint | Template states fields, tiers, authoring note, `Related:` shape |
| `new-adr` SKILL.md | T6 | Body line count under 500; skill-spec lint clean | SKILL.md states zones, write gate, errata convention |
| `docs/README.md` | T7 | The `adr/` entry no longer asserts a record is never edited | Classification admits the writable metadata block; `specs/` and `rfc/` untouched |
| How-to guide | T7 | Same search; guide checks clean | Guide states the zones and the `Related:` shape |
| Index generator | T9 | `README.md` still renders both pointers after the statuses go bare | Generator reads `Superseded by:`; index check clean |
| Corpus conformance | T9 | `check-adr-shape` exits 0 over `docs/adr` | Both records bare-token with a populated field |
| New record and ADR-0027 erratum | T10 | Recorded lint invocation; erratum present and dated | Both exist; index regenerates |
| `pack.toml`, `plugin.json` | T11 | Both read `0.11.0` | Version strings agree |
| `docs/product/changelog.md` | T11 | Heading pattern and placement; `tools/test_build_site_routing.py` green | Entry present with its Highlights decision |
| Reusable learning | all | Capture receipts at `spec-approved` and `plan-locked` | Receipts exist, or `project-knowledge unavailable` recorded |

## Design (LLD)

### Design decisions

- **The gate blocks.** Traces to: AC-0002, AC-0009. The migration removed the
  reason for an advisory phase, and an advisory check over a corpus that would
  pass is a control that cannot fail.
- **Filesystem safety is delegated, and observed behaviourally.** Traces to:
  AC-0006, AC-0031. Four attempts to gate the delegation structurally failed —
  the last was unsatisfiable against the script's own mandatory calls — so the
  delegation is a design decision here and the property is gated by what the
  lint does to a hostile tree, not by what its call graph looks like. T3's cases
  are what a bypassing implementation fails.
- **The helper is loaded by path, from the script's own directory, and refuses
  on any failure.** Traces to: AC-0006, AC-0031. `packs/AGENTS.md:29-33` forbids a
  bare-name import from a skill's `scripts/`; `check-spec-status.py:69-114`
  fixes both the loader shape and the posture. A confinement control that
  silently degrades to absent is worse than one that never shipped.
- **The generator changes before the statuses do.** Traces to: AC-0013.
  RFC-0102 § 7 states the ordering, and two records make it real rather than
  theoretical.
- **The record map is built before any rule runs.** Traces to: AC-0004, AC-0001.
- **A refused entry and an unreadable entry carry different labels.** Traces to:
  AC-0006. One label for both lets a corpus-wide confinement refusal read as a
  corpus-wide read failure.

### Interfaces & contracts

`lint-adr-shape.py <dir>`, standard library only, mirroring
`index-records.py`'s `main(argv) -> int` shape and its 0-clean / 1-problem exit
convention.

**Confinement root.** The helper's entry points are root-relative, so the root
is the supplied scan directory, resolved once before enumeration and reused for
every classification and read. Passing each entry's own parent would satisfy the
signatures and confine nothing.

Output has three parts:

- a **finding line** per finding, carrying the record path, the class code, and
  the message;
- a **scan summary** partitioning every candidate entry into read, refused, or
  unreadable, under three distinct labels;
- a **refusal message** on the AC-0003 paths, naming which case occurred,
  printed instead of a finding stream.

Both streams are reconfigured to UTF-8 before the first print, as
`packs/AGENTS.md` requires of every `.apm/` script.

The index generator reads `Superseded by:` as **same-line text only**, unlike
the lint's block-aware reader. `_escape_cell` neutralizes no line break, so a
multi-line read there would let a record-controlled value terminate its table
row. The two readers differ deliberately, and this is the one place saying so.

### Behavior & rules

The fifteen check classes and the RFC section owning each value domain are the
spec's table. Three parsing rules the table does not fix:

- a field's key may or may not carry a leading `- ` bullet. The sibling
  `_STATUS` pattern at `index-records.py:62` already tolerates the optional
  bullet and this reader matches it, which costs one character of regex. No
  criterion carries this: the two records that used the bulletless form were
  normalized in this delivery, so the corpus is uniform and the template ships
  the bulleted form.
- a field's value is its same-line text, or the block that follows the key in
  either form the corpus uses: indented continuation lines, or a blank line
  then an unindented list. ADR-0070 uses both — an indented `Signal` and a
  column-0 `Revisit if:` list — and a reader handling only the indented form
  reports a present value as empty, which under a blocking gate reds a valid
  record forever.
- a D-ID is defined by a `- **D<n>:**` list item in `## Decision`, and any other
  bolded `**D<n> …**` occurrence is a restatement or a citation, not a
  definition. Four records carry a second bolded series alongside their
  definitions; without this rule the density check reports them duplicated and
  non-dense. RFC-0102 `:191-200` already fixes the definition form, so this
  states the RFC's shape rather than choosing one.
- a field's value has its trailing HTML comment stripped before comparison,
  matching `index-records.py:62`'s `_STATUS` handling.
- `;` separates supersession entries while `,` separates D-IDs within an entry
  and `Areas` tokens, so the two splits never share a function and neither is
  expressed as a nested repeated group.

`ADR-S015` recognises a correction section by a closed heading set — `## Errata`,
`## Amendments`, and `## Erratum` with or without a parenthesised date — and
reports every spelling except the first.

The suggested `Related:` shape is guidance only and no class checks it: a gloss
may carry a `;` inside a quoted clause, so entries are not recoverable by
splitting on the separator.

### Failure, edge cases & resilience

Every failure mode on the read path is the helper's, and the lint's obligation
is to attribute it correctly and continue. A supersession entry naming an
ordinal with no record on disk is an `ADR-S010` finding, not a crash. If the
helper cannot be loaded — a missing path, a raising `exec_module`, a `None`
spec or loader, or a module lacking an expected entry point — every script
refuses rather than proceeding.

## Tasks

### T1: Three scripts share one confinement helper, with a gated oracle

**Depends on:** none

**Touches:** packs/governance-extras/.apm/skills/new-adr/scripts/_record_paths.py, packs/governance-extras/.apm/skills/new-adr/scripts/index-records.py, packs/governance-extras/.apm/skills/new-adr/scripts/next-ordinal.py, packs/governance-extras/.apm/skills/new-rfc/scripts/_record_paths.py, packs/governance-extras/.apm/skills/new-rfc/scripts/index-records.py, packs/governance-extras/.apm/skills/new-rfc/scripts/next-ordinal.py, packs/governance-extras/tests/skills/new-adr/test_lint_adr_shape.py, tests/roster/test_index_records.py, .github/workflows/build-check.yml, tools/lint-ci-parity.py

**Tests:** the two existing suites,
`packs/governance-extras/tests/skills/new-adr/test_next_ordinal.py` and
`tests/roster/test_index_records.py`, are the regression oracle; they cover the
behaviour being moved, at `test_next_ordinal.py:366,377,400` and
`test_index_records.py:288,304`.

- Both suites green before and after, with no existing assertion edited.
- The two shipped `index-records.py` copies and the two `_record_paths.py`
  copies are each asserted byte-identical, and each assertion fails on a
  one-line mutation to either side. `next-ordinal.py` already carries such a
  pin at `test_next_ordinal.py:456`; the generator pair had none, which is how
  a confinement change landing in one copy alone passed every gate.
- `tests/roster/test_index_records.py` is enumerated in `build-check.yml` with
  its matching `STEP_DISPOSITION` entry, and `tools/lint-ci-parity.py` passes,
  so the refactored script's confinement assertions run before merge rather than
  only on dispatch. Verifies AC-0011.
- New cases in `test_lint_adr_shape.py`, which T8 gates by name: the helper
  refuses a symlink, a FIFO, a directory, and a symlinked supplied directory,
  and accepts an ordinary directory beneath a symlinked ancestor.
- One case that a `lstat`-then-`read_text` implementation fails and a
  descriptor-based one passes — an entry swapped between classification and
  read, a hard link, or a reparse point. Without it every listed case is also
  passed by the weaker idiom already shipped, and the extraction proves nothing.
- Every load outcome that does not yield a helper exposing the expected entry
  points is a refusal: a path that does not resolve, an `exec_module` that
  raises, a `None` spec or loader, and a module missing an entry point. A silent
  fallback to a direct scan fails this bullet.

**Approach:**
- Read `packs/core/.apm/skills/work-loop/scripts/file_safety.py` and reuse its
  semantics — `O_NOFOLLOW` on the parent and the final component, and the
  before/after `st_dev`/`st_ino` comparison across the open. Do not import it:
  it belongs to another pack's skill and these scripts run standalone.
- Load the module the way `check-spec-status.py:69-114` loads its sibling.
- Ship one helper copy per skill, not one shared module. Each skill's scripts
  run standalone from their own projected directory and a pack-level
  `shared-libs/` is not projected, so a single module is unreachable; the
  byte-identity pin is what keeps two copies from becoming two implementations.
  The `next-ordinal.py` pair must move together because an existing assertion
  already pins them identical.

**Done when:** both existing suites pass with no assertion edited, the new
helper cases pass, and `tools/lint-ci-parity.py` is clean.

### T2: The lint reports each of the fifteen check classes from fixtures

**Depends on:** T1

**Touches:** packs/governance-extras/.apm/skills/new-adr/scripts/lint-adr-shape.py, packs/governance-extras/tests/skills/new-adr/test_lint_adr_shape.py, packs/governance-extras/tests/skills/new-adr/fixtures/**

**Tests:** `packs/governance-extras/tests/skills/new-adr/test_lint_adr_shape.py`,
loading the script by path the way `tests/roster/test_index_records.py:18-20`
does.

- One clean fixture directory holding a conforming record and one conforming
  mirrored pair; zero findings and exit 0. The floor every mutation case is
  measured against.
- Parametrised over the fifteen codes: each case applies that class's mutation
  and asserts the distinct class codes reported equal the set that case
  declares. The declared set is part of the fixture definition, not read back
  from the output. `ADR-S008` declares `{ADR-S008, ADR-S010}`. Verifies AC-0001.
- The parametrisation's id list is asserted equal to the fifteen codes.
- `ADR-S009` is exercised in BOTH directions: a `Supersedes in part` entry whose
  D-ID the named record defines, and a `Superseded in part` entry whose D-ID the
  citing record defines. One direction alone passes a lint that resolves every
  entry to the named record, which is a false positive on three real records.
- The clean fixture directory is scanned through a RELATIVE directory argument
  as well as an absolute one, and reports a non-zero read count both times. The
  gate chain passes `docs/adr`; an absolute-only fixture cannot tell a working
  scan from one that refuses every entry.
- Exit contract: exit 1 when any finding is reported, 0 when none. Verifies
  AC-0002.
- A directory holding one entry the lint refuses and one it cannot decode, and
  no other finding, exits non-zero. Distinct from AC-0002's finding path: a
  bucket is not a finding, and nothing else makes an unchecked record fail a
  blocking gate. Verifies AC-0031.
- Absent directory and present-but-empty directory each assert exit 1, an empty
  finding stream, and a message naming which case it was. Verifies AC-0003.
- `ADR-S010` mutation deletes one half of the mirrored pair; findings are
  attributed to both record paths. Verifies AC-0004.
- A fixture whose `**Signal:**` value is an indented block on the following
  lines reports no `ADR-S013` finding. Modelled on the one corpus record written
  that way. Verifies AC-0008.

**Approach:**
- Parse each record into a dataclass carrying path, metadata fields, D-IDs, and
  supersession entries; build the record map; then per-record rules, then
  cross-record rules.
- Obtain every entry and every byte through T1's helper.

**Done when:** `python3 -m pytest packs/governance-extras/tests/skills/new-adr/test_lint_adr_shape.py -q` is green with all fifteen parametrised cases collected.

### T3: The lint attributes bad entries correctly

**Depends on:** T2

**Touches:** packs/governance-extras/.apm/skills/new-adr/scripts/lint-adr-shape.py, packs/governance-extras/tests/skills/new-adr/test_lint_adr_shape.py

**Tests:** extends T2's suite, over fixture trees built in a temporary directory
because a symlink and a FIFO cannot be committed.

- A directory holding a symlinked `.md`, a FIFO named like a record, an
  undecodable record, and a record with an undecodable name: each appears in the
  scan summary under the label its outcome earns, refused and unreadable never
  sharing one, and the records around them are still checked. Verifies AC-0006.
- A hard link to a record outside the scan directory, and a record path that
  resolves outside the scan root, are each refused and named. These two are the
  helper guarantees that lost their gated owner when the structural criterion
  was cut, so they get behavioural cases here rather than going unobserved.
  Contributes to AC-0006 and AC-0031.

**Approach:**
- Route every directory entry and every read through T1's helper, and report a
  refusal and an unreadable entry through distinct summary labels.

**Done when:** the two case groups pass and no fixture is left on disk.

### T4: The real corpus is partitioned exhaustively

**Depends on:** T3

**Touches:** tests/roster/test_lint_adr_shape_corpus.py, .github/workflows/build-check.yml, tools/lint-ci-parity.py

**Tests:** `tests/roster/test_lint_adr_shape_corpus.py`, beside
`test_index_records.py` and `test_decision_record_ordinal_uniqueness.py`, whose
non-empty-floor-before-property discipline this reuses. Dispatch-only evidence.

- The partition AC-0005 states holds over `docs/adr/`, with membership derived
  from the directory listing at run time. The predicate is AC-0005's and is not
  restated here: it moved in review, the Testing Strategy copy was updated and
  this one was not, so for a while the criterion covered every `*.md` entry
  whatever its type while this bullet still said "regular, non-symlink".
  Verifies AC-0005.
- The file is enumerated in `build-check.yml` with its `STEP_DISPOSITION` entry,
  on the same reasoning T1 uses for its sibling: this is the criterion proving
  no record escapes the blocking scan, and dispatch-only is where that regresses
  unobserved.

**Approach:**
- Invoke the script as a subprocess against the pack source path, not the
  projection, so this task does not depend on a self-host run. The projected
  copy is what T9's gate-step observation exercises.

**Done when:** `python3 -m pytest tests/roster/test_lint_adr_shape_corpus.py -q` is green.

### T5: The template states the format and produces a passing record

**Depends on:** T2

**Touches:** packs/governance-extras/.apm/skills/new-adr/assets/adr.md, packs/governance-extras/tests/skills/new-adr/test_lint_adr_shape.py

**Tests:** extends T2's suite, reading the shipped template rather than a copy.

- The template declares `Areas`, `Reversibility`, and all four supersession
  fields, each supersession field carrying `none`. Verifies AC-0017.
- The template states the four parse tiers and which fields belong to each.
  Verifies AC-0018.
- The template states the authoring transformation — substitute every
  placeholder, delete the guidance comments. Verifies AC-0019.
- The template states the suggested `Related:` shape, marked not checked, and
  every ordinal in its worked example matches the literal placeholder form the
  template uses elsewhere. Expressed against the literal form, not against
  whether an ordinal resolves, because a pack test may not read `docs/adr/`.
  Verifies AC-0020.
- Instantiating the real template by exactly the transformation it documents
  produces a record the lint passes. Verifies AC-0022.

**Approach:**
- Add the new fields; replace the `Status` comment's compound
  `Superseded by ADR-NNNN` with the five bare tokens; add the `D1..Dn` example;
  add the parse-tier table; replace the lifecycle comment's Status-only sentence
  with the four zones; add the authoring note; add the `Related:` guidance with
  a placeholder-ordinal example. State the rules directly and cite no repository
  record.

**Done when:** T2's suite is green including the five template cases.

### T6: `new-adr` and `new-rfc` state the new rule

**Depends on:** T5

**Touches:** packs/governance-extras/.apm/skills/new-adr/SKILL.md, packs/governance-extras/.apm/skills/new-rfc/SKILL.md, packs/governance-extras/.apm/skills/new-adr/evals/evals.json

**Tests:** goal-based checks, run and recorded in the verification ledger.

- The write gate surfaces the `Areas` tokens already in use in the target
  directory and requires an explicit answer before an unused token is coined.
  Verifies AC-0025.
- `new-adr`'s SKILL.md defines the `## Errata` convention and `new-rfc`'s
  sole-home sentence at `:279` names RFCs. Verifies AC-0026.
- The `new-adr` SKILL.md body line count, measured after the six-line YAML
  frontmatter the way `skill_spec_lint.py` measures it, is under 500. It is 335
  today. The CAT-S003 verdict is not the oracle: it warns at 500 and errors only
  above 1000.

**Approach:**
- Replace the status-only sentence at `:243` with the four mutability zones; add
  the confirm-before-coining step to the write gate at `:208`; add the errata
  convention; narrow `new-rfc`'s sole-home sentence; remove the retired
  immutability clause from `evals.json` eval 1, whose replacement is T11's.

**Done when:** the three checks above hold and the skill-spec lint is clean.

### T7: No governing surface states the retired rule, and each states the zones

**Depends on:** T6

**Touches:** guides/governance-extras/how-to/new-adr.md, docs/README.md

**Tests:** goal-based checks.

- A search across the four surfaces AC-0023 names returns no statement that a
  status-only change is the only permitted edit. Verifies AC-0023.
- Each of those surfaces except `evals.json` describes the four mutability
  zones. Verifies AC-0024.
- `docs/README.md`'s `adr/` entry no longer asserts that a record is never
  edited, and its `frozen` class definition admits the metadata block RFC-0102
  § 4 makes writable. Verifies AC-0033.
- `docs/README.md`'s `specs/` and `rfc/` rows are byte-identical to their
  current text. Asserted as a diff-scoped check: the retirement gave the three
  separate rows, so the edit must not reach the other two.
- The guide states the suggested `Related:` shape with a placeholder-ordinal
  example matching the template's. Verifies AC-0021.
- `python3 tools/check-guide-index.py` and the guide-affordance audit stay clean.

**Approach:**
- Rewrite the guide's frozen-body caution at `:215` and the sentence at `:170`.
- Reword `docs/README.md`'s `adr/` entry and the `frozen` class definition it
  leans on, so "never edited" no longer contradicts RFC-0102 § 4's writable
  metadata block, and so a reader can tell the lifecycle class from the
  mutability zone that shares its name. `docs/CONVENTIONS.md` is not edited: it
  was retired by `813f533f1` and its obligations re-homed.

**Done when:** the closed-set search returns no hit, the row's other two classes
are unchanged, and the guide checks are clean.

### T8: The gate chain runs the lint and its fixture suite

**Depends on:** T2

**Touches:** tools/repo/build_gate_chain.py, tools/test_build_gate_chain.py

**Tests:** `tools/test_build_gate_chain.py`.

- `EXPECTED_SCRIPT_STEPS` at `:821` gains the two new steps, the equality
  assertion at `:1346` passes, and both steps' argv is asserted on the
  mechanism the file already uses for `lint-spec-status.py` at `:1347-1351`.
  The path pin alone cannot see a wrong directory or a missing flag, which is
  why the argv half needs its own assertion. That mechanism is a single
  lookup — find the one argv containing a named script, assert its last element
  equals a literal — so extending it means writing an analogous lookup per
  step, not reusing a parameterised helper. An exact-list pin, so the update is
  part of this task rather than a discovery during GATES. Verifies AC-0010.

**Approach:**
- Add `_pytest_step("test-lint-adr-shape", …)` naming the pack test file,
  mirroring `test-next-ordinal` at `:262-266`, and `_script_step(
  "check-adr-shape", ".claude", "skills", "new-adr", "scripts",
  "lint-adr-shape.py", args=("docs/adr",))` beside `check-adr-index`. No flag:
  AC-0002 makes the lint exit 1 on any finding, so blocking is not
  argv-conditional and cannot be lost by an argv edit.

**Done when:** `python3 -m pytest tools/test_build_gate_chain.py -q` is green,
AND the projected script the step names exists and runs: `make build-self` has
emitted `.claude/skills/new-adr/scripts/lint-adr-shape.py` and
`_record_paths.py`, and invoking that projected path over `docs/adr` reports
the same finding count as the `packs/` source. The test alone cannot observe
this — `_script_step` wraps `subprocess.run` without checking the target
exists, and `EXPECTED_SCRIPT_STEPS` compares declared path strings — so a step
naming a missing file passes it. The projection today holds only
`index-records.py` and `next-ordinal.py`, both pre-T1.

### T9: The generator reads the field, the last two records conform, and the gate is green

**Depends on:** T3, T8

**Touches:** packs/governance-extras/.apm/skills/new-adr/scripts/index-records.py, packs/governance-extras/.apm/skills/new-rfc/scripts/index-records.py, tests/roster/test_index_records.py, docs/adr/0023-reviewer-ceiling-scopes-core-code-review-lenses.md, docs/adr/0050-astro-marketing-site-toolchain-and-deploy.md, docs/adr/README.md

**Tests:** `tests/roster/test_index_records.py` for the generator, plus the
chain step for the corpus.

- A record whose `Status` is a bare `Superseded` and whose `Superseded by:`
  names a target renders a supersession pointer in the generated index. A new
  case in the generator's own suite, so the behaviour is pinned independently of
  the two records that motivate it. Verifies AC-0013.
- A record whose `Superseded by:` value carries both character classes — the
  cell-breaking set (`|`, `[`, `]`, `<`, `>`) and the destination-terminating
  set (`)`, whitespace, `#`, `?`) — renders inert at every slot the value
  reaches. One class alone passes the wrong escaper: `_escape_cell` handles the
  first and only `_escape_destination` handles the second. The status cell is
  already `_escape_cell(status)`, so a pointer composed into it inherits the
  escaping with no change to the emission code. The generator runs standalone for
  adopters and its byte-sibling indexes `docs/rfc`, where no shape lint
  validates the field, so it cannot assume upstream validation. Verifies
  AC-0032.
- `docs/adr/0023-*.md` and `docs/adr/0050-*.md` each carry a bare-token `Status`
  and a `Superseded by:` naming ADR-0042 and ADR-0109 respectively. Verifies
  AC-0012.
- `index-records.py --check docs/adr` exits 0. Verifies AC-0014.
- The `check-adr-shape` chain step over `docs/adr` exits 0. This is
  the closing observation of the whole delivery: the real gate, the real corpus.
  Verifies AC-0009.

**Approach:**
- ADR-0055 and ADR-0056 were already normalized, in commit `2f9e9308a` ("bullet ADR-0055 and ADR-0056's metadata blocks") ahead of
  this plan; that is why the lint needs no tolerance rule and no criterion, and
  no step here repeats it.
- Change BOTH shipped generator copies together. `test_index_records.py` pins
  them byte-identical, so changing the ADR copy alone reds that assertion — the
  defect T1 shipped and this pin now catches.
- Change the generator first, commit, then edit the two superseded records. RFC-0102 § 7
  states that ordering and these two records are why it matters; reversing it
  drops both pointers from the index in the intervening commit.
- Run `make build-self` from a committed state so the projected script the chain
  step invokes exists; the build refuses a dirty tree, so the commit precedes it.
- Regenerate `docs/adr/README.md` rather than editing it.

**Done when:** the generator case passes, the index check is clean, and the
chain step exits 0 over `docs/adr`.

### T10: A new-format record exists and ADR-0027 records what changed

**Depends on:** T5, T9

**Touches:** docs/adr/, docs/adr/0027-adr-format-is-madr-aligned-but-lean.md, docs/adr/README.md

**Tests:** manual QA plus goal-based checks.

- Invoke the built lint against a directory holding only the new record and
  record the observed exit code and output in
  `docs/specs/checkable-adr-metadata/notes/verification-ledger.md`. Verifies
  AC-0015.
- `docs/adr/0027-*.md` carries one dated `## Errata` entry recording both the
  shipped lint and the `D5` override, and that heading is exactly `## Errata`,
  so the lint's own `ADR-S015` accepts it. Verifies AC-0016.
- `index-records.py --check docs/adr` exits 0 after both edits.

**Approach:**
- Author the new record through `new-adr` so the write gate and the new
  authoring step are exercised; `next-ordinal.py` supplies the ordinal at
  authoring time. Record the allocated ordinal in the verification ledger — the
  spec names the record by role.
- Write ADR-0027's erratum as one entry covering both facts. It is the first
  exercise of the convention this delivery defines, which is the test of whether
  the convention is usable; note in the ledger whether it was.

**Done when:** the recorded invocation shows exit 0, the erratum is present, and
the index check is clean.

### T11: The pack releases 0.11.0 with its changelog entry and evals

**Depends on:** T6, T10

**Touches:** packs/governance-extras/pack.toml, packs/governance-extras/.claude-plugin/plugin.json, docs/product/changelog.md, packs/governance-extras/.apm/skills/new-adr/evals/**

**Tests:** goal-based checks.

- Both version strings read `0.11.0`. Verifies AC-0027.
- The changelog heading matches its pattern and sits at top level directly
  beneath `[Unreleased]`, observed by `tools/test_build_site_routing.py`.
  Verifies AC-0028.
- The entry records its Highlights decision. That test does not read it, so the
  observation is a direct check of the entry's content. Verifies AC-0029.
- `evals.json` and `eval_queries.json` carry at least one eval naming `Areas`,
  `Reversibility`, and the half of a mirrored pair one authored record can
  carry, and no eval asserts body immutability. The live-model run is recorded
  in the ledger as advisory. Verifies AC-0030.

**Approach:**
- Minor bump in both files, because the shipped lint and the shared helper are
  new primitives.

**Done when:** the four checks above pass and `make lint-ruff lint-mypy` is clean.

## Rollout

The gate ships blocking. The `check-adr-shape` chain step runs the lint over
`docs/adr` on every pull request and fails on any finding, which is possible
only because the migration landed first and T9 clears the residual the spec's Assumptions state.
Nothing here needs infrastructure, an external system, or deployment
sequencing. The one ordering constraint that is not a task dependency is
internal to T9: the generator change is committed before the two records change,
per RFC-0102 § 7.

Rollback is a revert. The two record edits and the generator change revert
together; nothing is irreversible. T1 is the one task that changes shipped,
passing code, and its regression oracle runs before merge once that task
enumerates it.

## Risks

- **T9 is the task that can red main.** It is the first change to make the gate
  blocking, and it does so in the same task that edits the corpus. If a
  sixteenth latent defect exists in a record no probe class covers, the gate
  catches it at T9 rather than earlier, and the remedy is another record edit
  rather than a design change. The probe behind the four-finding figure covered
  the fifteen classes; a class the lint implements differently from the probe
  would surface here.
- **T1 changes two shipped scripts that currently pass.** The refactor is
  behaviour-preserving by construction — no existing assertion may be edited —
  and enumerating the roster suite gives it a pre-merge oracle. The residual is
  that two working confinement controls are touched at once.
- **The delegation allowlist is only as good as the AST walk's name
  resolution.** A dynamically constructed call, `getattr(os, "listdir")`, or an
  `eval` would evade any static walk. The walk is a guard against the ordinary
  mistake, not against a determined author of the script it guards.
- **`packs/governance-extras/tests/skills/new-adr` is declared "never gated" in
  `tools/lint-pack-test-boundary.py:1269` while the chain already gates one file
  from it.** T8 adds a second gated file, widening that inaccuracy. Out of this
  spec's intent; if the boundary lint refuses the second step, T8 surfaces.
- **`tools/test_local_ci_shared_test_deduplication.py` is red on a clean tree**
  (`workspace.toml` `[backlog].open`). This plan adds no `tools/` test file and
  no Makefile line, so a failure there during GATES is pre-existing.
- **Two accepted residuals ship.** The finding stream is not neutralized against
  record-controlled values, and the per-file read is unbounded. Both are
  recorded in the spec's Assumptions with the owner's acceptance, and both are
  exposures the two sibling scripts already carry.

## Changelog

- 2026-09-17: initial plan.
- 2026-09-17: revised from spec-stage review round 1 — helper extraction added,
  lint split across tasks, corpus floor replaced with a run-time comparison,
  value domains cited to RFC-0102, `docs/CONVENTIONS.md` pulled into scope.
- 2026-09-17: revised from round 2 — four safety-envelope criteria collapsed into
  one delegation criterion, by-path loader and refuse-on-failure pinned, T1's
  oracle given a pre-merge home, per-case expected code sets, three-bucket
  partition, template authoring note, suggested `Related:` shape, task
  cross-references renumbered.
- 2026-09-17: revised from round 3 and the completed corpus migration
  (`4b2714112`). The gate now ships blocking rather than advisory, because the
  migration left only four findings in two records and the flip's stated
  precondition is met; the advisory/strict split and the enforcement-flip
  follow-on are gone. The index-generator change and those two records came into
  scope, forced by RFC-0102 § 7's sequencing precondition. The delegation
  criterion's negative
  call list became a positive allowlist with one home here, after both review
  lanes independently showed `Path.read_bytes` and `Path.glob` walking past it.
  Added the continuation-block field rule, after a re-measure showed a
  line-scoped reader falsely reporting the corpus's one nested-list `Signal`.
  Added T1's descriptor-versus-`lstat` case, without which the extraction proves
  nothing. Split the CI-parity criterion out of the gate-chain one. Recorded
  output neutralization and the unbounded read as accepted residuals rather than
  claiming criteria for them. Corrected the body-line derivation to 341 − 6.
- 2026-09-17: normalized ADR-0055 and ADR-0056 rather than specifying around
  them, after the owner flagged them. Their `Areas` was present — the migration
  reached them — but they were the only two records written `**Key:** value`
  with no leading bullet, the same shape `check-adr-immutability` skips, and
  under a blocking gate a bullet-requiring reader would have reported every
  field of both absent. Fixing the records keeps that out of the contract
  entirely. Also recorded the blocking posture as a named deviation from
  RFC-0102's still-current advisory text, and re-pinned the tier-table citation
  after commit `2eb5e01ed` ("scope RFC-0102's evidence to mechanism, not one corpus") moved it.
- 2026-09-17: round 4. Re-measured the corpus against all fifteen predicates
  after review showed the earlier figure was taken with a probe implementing
  nine of them and no mirror rules: as written they produced 42 findings, not 4.
  Three predicates were the cause, not the corpus. `ADR-S011` now defines a
  D-ID as a `- **D<n>:**` list item, which is RFC-0102's own shape, so four
  records' bolded restatements stop reading as duplicates. The value reader now
  accepts a blank-line-separated unindented list, so ADR-0070's `Revisit if:`
  stops reading as empty. `ADR-S014` is narrowed to presence on owner
  confirmation, which drops 32 findings and defers the layout conversion
  RFC-0102 `:359-363` licenses to a Follow-on; the table now credits this spec
  for that predicate instead of the RFC. The corrected residual is 6 findings
  naming 4 record paths, remedied by 2 record edits.
  The delegation criterion's allowlist was inverted again: the compared set
  became every statically
  resolvable call target, because "filesystem-reaching names" needed a
  classifier and a classifier is the deny list under a positive label. Added
  AC-0031, so a refused or unreadable entry fails the blocking gate instead of
  being reported and passed over, and AC-0032, so the new `Superseded by:` value
  reaching the index is escaped like every other record-controlled cell.
  Dropped `--strict`, which AC-0002 had made inert. Gave AC-0010 an argv
  assertion and AC-0005 a pull-request-gated home. Cleared T9's stale `Touches`.
  Refuted the corpus-wide-block risk with branch protection: `strict = true`
  with `make build-check` required.
- 2026-09-17: round 5. Cut the structural delegation criterion on owner
  decision after a fourth formulation
  proved unsatisfiable — it failed against `print` and the UTF-8 reconfigure the
  plan itself mandates. The property it protected stays gated behaviourally by
  AC-0006, AC-0031 and T3's fixture tree, which gains a hard-link case and a
  containment case so the two helper guarantees that lost their gated owner keep
  one. Resolved the exit-code contradiction AC-0031 created last round: AC-0002
  owns the finding half, AC-0031 the bucket half, and they can no longer demand
  opposite codes. Widened AC-0005's universe to every `*.md` entry regardless of
  file type and made the three outcomes exhaustive, because the criterion whose
  job is proving nothing escapes was excluding exactly the entries that can.
  Partitioned AC-0003 against the candidate listing so it and AC-0031 stop
  claiming the same input. Extended AC-0011 to both roster files. Pinned the
  generator's field read same-line and the helper's confinement root. Added T3
  to T9's dependencies so the closing observation runs against the lint T3
  changes. Corrected the residual to the figure and counting unit the spec's
  Assumptions state, after two earlier figures used units the contract does not
  produce. Regenerate it with
  `python3 packs/governance-extras/.apm/skills/new-adr/scripts/lint-adr-shape.py docs/adr`
  rather than reading it from here.
- 2026-09-17: amendment, before any task ran. Commit `813f533f1` retired
  `docs/CONVENTIONS.md` after this contract's baseline sealed, re-homing the
  document lifecycle classes to a seeded `docs/README.md` and the
  frozen-document supersession rules to a new-spec reference. Seven references
  were stale. The retired Status-only rule survives on no re-homed surface, so
  AC-0023's surface set drops to four; `docs/README.md`'s `adr/` entry
  classifies records as `frozen` = "never edited", which contradicts RFC-0102
  § 4, so AC-0033 now carries that and T7 edits that file instead. The
  `Never do` carve-out narrowed because the three record classes no longer
  share one row. Amended with zero completed tasks, so re-approval and
  re-scheduling cost nothing beyond the gates themselves.

