# Spec: Checkable ADR metadata

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0102](../../rfc/0102-mechanically-checkable-adrs.md), [ADR-0027](../../adr/0027-adr-format-is-madr-aligned-but-lean.md), [ADR-0112](../../adr/0112-index-tables-are-generated-or-absent.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the record format is defined by the `new-adr` template and its shape lint. A parallel schema under `contracts/` would give one rule two homes.
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Objective

An architecture decision record carries a metadata block a program can read, and
a blocking gate keeps it that way. `Status` is one bare lifecycle token,
supersession is a set of mirrored fields naming ordinals and constraint IDs
rather than a sentence, each decision is a numbered constraint with a permanent
address, and every field the template ships is either validated by a shape lint
or declared unvalidated. The freeze at acceptance binds an ADR's prose; a
declared metadata field's value may still change, and a meaning-preserving
correction has a legal home in `## Errata`.

The users are the people who author and read decision records — in this
repository and in any repository that installs the `governance-extras` pack. An
author gets a template that says which facts a checker reads and a lint that
fails their pull request before review does; a reader gets a record whose
supersession state is legible from either end without reading prose.

Success is a portable shape lint that runs over a whole decision-record
directory and blocks on any finding, a corpus that passes it, a template whose
records pass it, and one record recording the format decision itself.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Shared confinement helper | Four sibling scripts across two shipped skills need one reviewed copy of the path-confinement idiom | `packs/governance-extras/.apm/skills/{new-adr,new-rfc}/scripts/_record_paths.py` | governance-extras maintainer | T1: the existing scripts load it, their suites stay green, and both shipped pairs are pinned byte-identical | One definition per shipped skill, pinned identical; the lint routing all reads through it is a design decision, gated behaviourally rather than structurally |
| Current product truth — template | The record format is the product | `packs/governance-extras/.apm/skills/new-adr/assets/adr.md` | governance-extras maintainer | T5: a record authored from the template passes the lint | Template states the field set, the parse tiers, the authoring transformation, and the suggested `Related:` shape |
| Current product truth — skill | `new-adr` states the freeze rule and the write gate | `packs/governance-extras/.apm/skills/new-adr/SKILL.md` | governance-extras maintainer | T6: body under 500 lines; skill-spec lint clean | SKILL.md states the zones, the `Areas` write gate, and the errata convention |
| Governance convention | `docs/README.md` classifies `adr/` as `frozen`, a class it defines as never edited, which RFC-0102 § 4 contradicts | `docs/README.md` | repository maintainer | T7: the `adr/` entry admits the metadata block's mutability | The `adr/` classification no longer asserts a record is never edited |
| Maintainer and adopter procedure | The how-to guide states the freeze rule and carries the `Related:` example | `guides/governance-extras/how-to/new-adr.md` | governance-extras maintainer | T7: same search; guide checks clean | Guide describes the zones and the `Related:` shape |
| Index generator | Two records carry their supersession pointer only in `Status` text; bare-tokening them drops the pointer unless the generator reads the field | `packs/governance-extras/.apm/skills/new-adr/scripts/index-records.py` | governance-extras maintainer | T9: `docs/adr/README.md` still renders both pointers after the records go bare | The generator reads `Superseded by:` and the index check is clean |
| Corpus conformance | The migration left two records non-conformant, and a blocking gate needs them fixed | `docs/adr/0023-*.md`, `docs/adr/0050-*.md` | eugenelim | T9: the lint over `docs/adr` exits 0 | Both carry a bare `Status` and a populated `Superseded by:` |
| Decision rationale | RFC-0102 requires one record of the format decision; ADR-0027 deferred this lint and its D5 is overridden | `docs/adr/` (new record), `docs/adr/0027-*.md` (erratum) | eugenelim | T10: the new record passes the lint; ADR-0027 carries one dated erratum | Both exist and the index regenerates |
| Interface compatibility | A new shipped script is a new pack primitive | `packs/governance-extras/pack.toml`, `.claude-plugin/plugin.json` | governance-extras maintainer | T11: both read `0.11.0` | The two version strings agree |
| Release history | The bump is a user-visible pack release | `docs/product/changelog.md` | governance-extras maintainer | T11: a free-standing release heading beneath `[Unreleased]` | The entry exists with its Highlights decision recorded |
| Reusable learning | Generalisable authoring and verification practice | `project-knowledge` producer profile | implementing session | Capture receipts at the `spec-approved` and `plan-locked` gates | Receipts exist, or `project-knowledge unavailable` is recorded |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep the lint a single implementation under
  `packs/governance-extras/.apm/skills/new-adr/scripts/`, reached by the gate
  chain through its `.claude/skills/new-adr/scripts/` projection, matching
  `check-adr-ordinals` and `check-adr-index`.
- Derive the shared helper's semantics from the shipped
  `packs/core/.apm/skills/work-loop/scripts/file_safety.py`, and load it the way
  that pack's scripts load their own siblings — by path, from the loading
  script's own resolved directory, via `importlib.util.spec_from_file_location`,
  never by bare name.
- Change the index generator before any record's `Status` becomes a bare token;
  RFC-0102 § 7 states that ordering and two records depend on it.
- Update `EXPECTED_SCRIPT_STEPS` in `tools/test_build_gate_chain.py` in the same
  commit that adds a gate-chain step; it is an exact-list pin.
- Pair any new `build-check.yml` step with its `STEP_DISPOSITION` entry in
  `tools/lint-ci-parity.py`.
- Run the real lint against `docs/adr/` and read its output before calling any
  task done.

### Ask first

- Any edit to a record under `docs/adr/` other than ADR-0023 and ADR-0050,
  the metadata normalization of ADR-0055 and ADR-0056, the new record this
  delivery ships, and ADR-0027's erratum.
- Adding, removing, or renaming a check class beyond the fifteen named below.
- Any change to `new-rfc`'s `## Recording corrections` section beyond narrowing
  its sole-home sentence to RFCs.
- Any change to `index-records.py` or `next-ordinal.py` beyond the supersession
  field read and replacing their inline confinement idiom with the shared helper.

### Never do

- Never add a second copy of the lint under `tools/`, a new top-level directory,
  or a new dependency; the scripts use the standard library only.
- Never let the lint exit 0 on a scan that read zero decision records.
- Never rewrite a record's `Date` or attribution value.
- Never change what `docs/README.md` says about `specs/` or `rfc/`. RFC-0102
  § "Reviewer brief" carves the spec and RFC freeze rules out of scope. That
  file gives each of the three its own row, so the edit reaches the `adr/`
  entry and the `frozen` class definition it depends on, and nothing else.
- Never cite this catalogue's internal records, acceptance criteria, or
  repository-only paths in shipped pack content or in `guides/`, per
  `packs/AGENTS.md` § "Shipped pack content carries no internal-governance
  citations"; both surfaces reach adopters, so worked examples use placeholder
  ordinals and the rules are stated directly.
- Never edit a `.claude/` or `.agents/` projection directly; self-host produces
  them and a required gate catches drift.

## Testing Strategy

`LS` = `packs/governance-extras/tests/skills/new-adr/test_lint_adr_shape.py`,
new and pack-local, gated by name in the chain. It exercises the shipped script
and the shared helper against synthetic fixtures and against the shipped
template. It may not read above its own pack, per
`tools/lint-pack-test-boundary.py` check 8.
`LC` = `tests/roster/test_lint_adr_shape_corpus.py`, new and repository-level;
it runs the same script against the real `docs/adr/` directory, which `LS` may
not reach. `LC` is dispatch-only evidence; the pull-request-gated observation of
corpus conformance is the `check-adr-shape` chain step itself, which runs the
same scan and blocks on any finding.

- **Check-class coverage (AC-0001):** TDD on `LS`. Each class is a predicate
  over one record. Each case declares its own expected code set, because two
  classes cannot always be mutated independently: RFC-0102 § 3 mirrors
  field-by-field, so an `ADR-S008` mutation necessarily adds an unmirrored entry
  and reports `ADR-S010` too. The case list is asserted equal to the class-code
  set, so a class added without a case reds.
- **Exit contract (AC-0002) and refusal (AC-0003):** TDD on `LS`. They fail on
  different inputs and have different remedies: AC-0002 is a scan that ran and
  found something, AC-0003 is a scan that could not run at all. A lint that
  exited 0 on an empty directory would satisfy AC-0002 and fail AC-0003, which
  is the failure mode RFC-0102's void test refuted two earlier designs for.
- **Mirrored-pair attribution (AC-0004):** TDD on `LS`. Separate from AC-0001
  because `ADR-S010` firing is not the same observation as its findings naming
  both records; a per-file pass satisfies the first and fails this one.
- **Corpus partition (AC-0005):** TDD on `LC`, which T4 enumerates in
  `build-check.yml` for the same reason T1 enumerates its sibling: this is the
  criterion proving no record silently escapes the blocking scan, and a control
  whose only assertions run on dispatch can regress into a merge with every
  required gate green. The partition predicate is AC-0005's and is not restated
  here; two copies of one rule drift independently, and this one had to change
  in both places the last time it moved.
- **Unchecked entries fail the gate (AC-0031):** TDD on `LS`. Separate from
  AC-0005, which counts the buckets, and from AC-0006, which labels them:
  neither makes a populated refused or unreadable bucket change the exit code.
- **Index escaping (AC-0032):** TDD on the generator's own suite — a record
  whose `Superseded by:` value carries table-delimiter and markup characters
  renders them inert in `docs/adr/README.md`.
- **Refused and unreadable are distinguishable (AC-0006):** TDD on `LS`.
  A refused entry is a control working and an unreadable entry is a control
  coping; under one label a corpus-wide confinement refusal is indistinguishable
  from a corpus-wide read failure.
- **Continuation-block field values (AC-0008):** TDD on `LS`. A record whose
  `**Signal:**` value is an indented block on the following lines is
  conformant, not empty. One record in the corpus is written that way today, so
  a line-scoped emptiness test would red a blocking gate on a valid record.
- **Corpus conformance under the gate (AC-0009):** goal-based check — the
  `check-adr-shape` chain step, running the lint over `docs/adr`, exits 0.
  This is the pull-request-gated observation, and it is what makes the delivery
  a control rather than a worklist.
- **Gate-chain wiring (AC-0010) and CI parity (AC-0011):** goal-based checks on
  `tools/test_build_gate_chain.py` and `tools/lint-ci-parity.py`. Separate
  criteria in separate files with separate remedies, closed by separate tasks.
  AC-0010 includes an argv assertion, because the exact-list pin compares script
  paths only and would not see a missing flag or a wrong directory.
- **The two non-conformant records (AC-0012):** goal-based check.
- **Index pointer survival (AC-0013):** goal-based check on the generator's own
  suite — after the two records go bare, `docs/adr/README.md` still renders both
  supersession pointers. This is the observation RFC-0102 § 7's sequencing
  precondition exists for, and it fails if the generator change is skipped or
  ordered late.
- **Index regeneration (AC-0014):** goal-based check —
  `index-records.py --check docs/adr` exits 0.
- **The new record and ADR-0027's erratum (AC-0015, AC-0016):** visual / manual
  QA for the new record, the built lint invoked against it with the result
  recorded; goal-based check for the erratum's presence and shape.
- **Template content (AC-0017, AC-0018, AC-0019, AC-0020) and conformance
  (AC-0022):** TDD on `LS`, reading the shipped `assets/adr.md` rather than a
  copy so the template and the lint cannot drift apart silently. Five separate
  remedies: the metadata block, the tier table, the authoring note, the
  `Related:` guidance, and whatever the conformance run turns up.
- **The guide's `Related:` example (AC-0021):** goal-based check in T7, not
  `LS`. `guides/` is above the pack, and a pack test may not read it.
- **Retired-rule absence (AC-0023) and zone presence (AC-0024):** goal-based
  checks. They fail independently: a surface can drop the old rule without
  stating the new one.
- **The document-hierarchy classification (AC-0033):** goal-based check over
  `docs/README.md`. Separate from AC-0024 because that file does not state the
  four zones — it classifies document kinds — so the obligation is that its
  `adr/` entry stops contradicting RFC-0102 § 4, not that it restates the zone
  table.
- **Skill prose obligations (AC-0025, AC-0026):** goal-based checks over
  `new-adr`'s SKILL.md and `new-rfc`'s SKILL.md.
- **Release surface (AC-0027, AC-0028, AC-0029):** goal-based checks — the two
  version strings, the changelog heading pattern and placement observed by
  `tools/test_build_site_routing.py`, and the Highlights decision, which that
  test does not read and so carries its own criterion.
- **Eval content (AC-0030):** goal-based check over the two eval files. The
  live-model run is not a gate: `tools/test-run-pack-evals.py` places the
  `claude -p` surface outside every mechanical suite, `pack-evals.yml` is
  dispatch-only and `continue-on-error` and excludes this pack by default, and
  grading is an LLM judge. The live run is recorded in the ledger as advisory.

## Acceptance Criteria

The fifteen check classes are named below by code, subject, and check kind. Their
**value domains are owned by RFC-0102** — the status token set and the `Areas`
arity and token shape by its § 2, the supersession grammar by its § 3 — and are
cited rather than restated, so the spec cannot become a second, silently
disagreeing home for them. What is new here is the code set itself.

| Code | Subject | Check kind | Domain owner |
| --- | --- | --- | --- |
| `ADR-S001` | `Status` | value in a closed token set | RFC-0102 § 2 |
| `ADR-S002` | `Date` | `YYYY-MM-DD`, and not the template placeholder | template |
| `ADR-S003` | `Areas` | present and non-empty | RFC-0102 § 2 |
| `ADR-S004` | `Areas` | arity cap | RFC-0102 § 2 |
| `ADR-S005` | `Areas` | per-token shape, and no repeated token | RFC-0102 § 2 |
| `ADR-S006` | `Reversibility` | value in a closed token set | RFC-0102 § 2 |
| `ADR-S007` | the four supersession fields | present, and `none` or a well-formed entry list | RFC-0102 § 3 |
| `ADR-S008` | `Supersedes` against `Supersedes in part` | no ordinal in both | RFC-0102 § 3 |
| `ADR-S009` | a cited D-ID | defined by the record the entry names | RFC-0102 § 3 |
| `ADR-S010` | a supersession entry | has its mirrored counterpart | RFC-0102 § 3 |
| `ADR-S011` | `## Decision` | `- **D<n>:**` list items dense from `D1`, no gap or duplicate | RFC-0102 § 2 |
| `ADR-S012` | `**Revisit if:**` in `## Consequences` | present and non-empty | RFC-0102 § 1 |
| `ADR-S013` | a present `## Confirmation` | `Mode`, `Signal`, `Owner` present and non-empty | RFC-0102 § 2 |
| `ADR-S014` | a present `## Alternatives considered` | present and non-empty | this spec |
| `ADR-S015` | a correction section | heading is exactly `## Errata`, entries are top-level `- ` | RFC-0102 § 5 |

- [ ] **AC-0001.** For a fixture record mutated to violate one check class, the
  distinct class codes reported equal the set that case declares. A case declares
  more than its own class only where RFC-0102 § 3's field-specific mirroring makes
  a second class unavoidable — mutating `ADR-S008` adds an unmirrored entry and so
  also reports `ADR-S010` — and the unmutated record reports none.
- [ ] **AC-0002.** The lint exits 1 when it reports any finding, and 0 only
  when it reports no finding and every non-read bucket is empty. AC-0031 owns
  the bucket half of the exit contract; this criterion owns the finding half,
  and the two never require opposite codes for one scan.
- [ ] **AC-0003.** The lint exits 1, prints no finding stream, and names which
  case occurred, when its target directory is absent and when the directory's
  candidate listing is empty. "Holds no decision record" means the listing
  produced no candidate, not that every candidate was refused or undecodable —
  that input is AC-0031's.
- [ ] **AC-0004.** A missing counterpart in a mirrored supersession pair is
  reported against both the record that names the target and the record that
  omits the mirror.
- [ ] **AC-0005.** Run over `docs/adr/`, every `*.md` directory entry less
  `README.md` — whatever its file type — is accounted for in exactly one of the
  lint's three outcomes: read, refused, or unreadable. Those three are
  exhaustive of every outcome an entry can have, including a classification
  that raised, so no entry can be enumerated and then counted nowhere.
  Membership is derived from the directory listing at run time.
- [ ] **AC-0006.** A refused entry and an unreadable entry are reported under
  distinct labels, so neither can be read as the other.
- [ ] **AC-0008.** A `**Key:**` metadata value written on the lines following
  the key is read as that key's value, in both forms the corpus uses: an
  indented block, and a blank line followed by an unindented list. A record
  whose `Signal` is a nested list and a record whose `Revisit if:` is a
  column-0 list after a blank line are both conformant rather than empty.
- [ ] **AC-0009.** The `check-adr-shape` chain step, running the projected
  script over `docs/adr` on a pull request, exits 0.
- [ ] **AC-0010.** `tools/repo/build_gate_chain.py` carries a `check-adr-shape`
  step invoking `.claude/skills/new-adr/scripts/lint-adr-shape.py` against
  `docs/adr`, and a `test-lint-adr-shape` step running the pack fixture suite;
  `tools/test_build_gate_chain.py` asserts both steps' argv, on the mechanism it
  already uses for `lint-spec-status.py`, and passes.
- [ ] **AC-0011.** `tests/roster/test_index_records.py` and
  `tests/roster/test_lint_adr_shape_corpus.py` are each enumerated in
  `.github/workflows/build-check.yml` with their matching `STEP_DISPOSITION`
  entries in `tools/lint-ci-parity.py`, and that lint passes.
- [ ] **AC-0012.** `docs/adr/0023-*.md` and `docs/adr/0050-*.md` each carry a
  bare-token `Status` and a `Superseded by:` field naming the record that
  supersedes them.
- [ ] **AC-0013.** `docs/adr/README.md` renders a supersession pointer for both
  of those records after their `Status` values become bare tokens.
- [ ] **AC-0014.** `docs/adr/README.md` regenerates from its records with no
  diff under `index-records.py --check docs/adr`.
- [ ] **AC-0015.** The one new-format decision record this delivery ships exists
  under `docs/adr/`, records the ADR format decision, is `Accepted`, and passes
  the lint.
- [ ] **AC-0016.** `docs/adr/0027-*.md` carries one dated `## Errata` entry
  recording both that the mechanical status lint its Confirmation deferred has
  shipped, and that its `D5` forward-only migration clause is overridden, the
  corpus having been migrated.
- [ ] **AC-0017.** `packs/governance-extras/.apm/skills/new-adr/assets/adr.md`
  pre-declares `Areas`, `Reversibility`, and all four supersession fields, each
  supersession field carrying the `none` sentinel.
- [ ] **AC-0018.** That template states the four parse tiers RFC-0102 § 1
  names — tier T1, tier T1-unchecked, tier T2, tier T3 — and which fields belong
  to each. "Tier" is written out wherever a tier is named, because this plan's
  task identifiers share the `T<n>` shape.
- [ ] **AC-0019.** That template states the transformation an author performs to
  produce a record from it: substitute every placeholder, and delete the
  guidance comments.
- [ ] **AC-0020.** That template states the suggested shape for `Related:`,
  marked as suggested and not checked: entries separated by `;`, each a bare
  ordinal or a `/`-joined pair and never a Markdown link, each followed by a
  parenthetical gloss naming the relationship with an em dash before a secondary
  clause, and no trailing period. Every ordinal in its worked example is the
  literal placeholder form the template uses elsewhere.
- [ ] **AC-0021.** `guides/governance-extras/how-to/new-adr.md` states the same
  suggested `Related:` shape, with a worked example whose ordinals are all
  placeholders.
- [ ] **AC-0022.** A record produced from that template by the transformation
  AC-0019 requires it to state passes the lint.
- [ ] **AC-0023.** None of these surfaces states that a status-only change is
  the only edit permitted on an accepted ADR:
  `packs/governance-extras/.apm/skills/new-adr/assets/adr.md`,
  `packs/governance-extras/.apm/skills/new-adr/SKILL.md`,
  `packs/governance-extras/.apm/skills/new-adr/evals/evals.json`,
  and `guides/governance-extras/how-to/new-adr.md`. Surviving statements
  outside this set are listed under Follow-ons.
- [ ] **AC-0024.** Each of those surfaces except `evals.json` describes the four
  mutability zones — Live, Attested, Frozen, Append-only — in place of the
  retired rule.
- [ ] **AC-0025.** `new-adr`'s SKILL.md write gate surfaces the `Areas` tokens
  already in use in the target directory and requires an explicit answer before
  a record introduces a token none of them uses.
- [ ] **AC-0026.** `new-adr`'s SKILL.md and template define `## Errata` as
  append-only dated entries that clarify meaning and never alter what was
  decided, and `new-rfc`'s sole-home sentence names RFCs rather than all record
  types.
- [ ] **AC-0027.** `packs/governance-extras/pack.toml` and
  `packs/governance-extras/.claude-plugin/plugin.json` both read `0.11.0`.
- [ ] **AC-0028.** `docs/product/changelog.md` carries a heading matching
  `## [governance-extras][0.11.0] — <ISO date>` at top level, directly beneath
  the `[Unreleased]` section and not nested inside it.
- [ ] **AC-0029.** That release entry records its Highlights decision, either as
  a `Highlights` subsection one level below the entry or as a stated
  none-with-reason.
- [ ] **AC-0030.** `packs/governance-extras/.apm/skills/new-adr/evals/evals.json`
  and `eval_queries.json` carry at least one eval whose expected output and
  assertions name `Areas`, `Reversibility`, and the half of a mirrored
  supersession pair a single authored record can carry; and no eval asserts that
  an accepted record's body is immutable.
- [ ] **AC-0031.** Any accounted entry the lint did not read makes it exit
  non-zero — not only the two named buckets, so an outcome landing in neither
  cannot exit 0. An entry the lint could not confine, could not classify, or
  could not decode must fail the run rather than be reported and passed over:
  under a blocking gate, being reported without failing is how a record joins
  the corpus without ever being shape-checked.
- [ ] **AC-0032.** A supersession value reaching the generated index passes the
  same cell or destination escaping every other record-controlled cell in
  `index-records.py` already uses, chosen by where the pointer lands, and the
  generator reads `Superseded by:` as same-line text only. The same-line pin is
  load-bearing: `_escape_cell` neutralizes no line break, so a multi-line read
  would let a record-controlled value terminate its table row. The
  generator is a shipped adopter primitive that runs standalone, and its
  byte-sibling indexes `docs/rfc` where no shape lint validates the field, so it
  cannot assume the value was validated upstream.

- [ ] **AC-0033.** `docs/README.md`'s `adr/` entry does not assert that a
  decision record is never edited. Its `frozen` class means the prose is
  immutable and a correction supersedes rather than rewrites, stated in terms
  that admit the metadata block RFC-0102 § 4 makes writable, and worded so a
  reader can tell the lifecycle class from the mutability zone sharing its name.

## Follow-ons

Each item below is carved out by RFC-0102 § "Follow-on artifacts", or is a
surviving statement of the retired rule that AC-0023's surface set excludes.

- eugenelim: RFC-0102 `:359-363` — the licensed one-time conversion of
  `## Alternatives considered` into list entries, on the 32 records that write
  it as bolded paragraphs. Deferred when `ADR-S014` was narrowed to presence;
  doing it would let the layout half of the check come back.
- eugenelim: RFC-0102 § 6 — rewrite `check-adr-immutability`
  (`.github/workflows/docs.yml:341-360`) and move it to a required context. Its
  `:342` and `:356` both state the retired rule, which is why AC-0023's surface
  set excludes them.
- eugenelim: RFC-0102 § "Follow-on artifacts" — a replacement spec for index-table
  generation, superseding the historical `docs/specs/index-table-generation/`.
  This delivery makes the generator read `Superseded by:` because two records
  depend on it; the broader replacement remains separate.
- eugenelim: RFC-0102 § "Follow-on artifacts" — a rules seed under
  `.agents/rules/` plus its `AGENT_RULES.md` row, the agent-routing consumer.
- eugenelim: RFC-0102 § "Follow-on artifacts" — align `reconcile-iac`'s
  expectation of an ADR `Constraints` section with where constraints live.
- eugenelim: `docs/product/intents/frozen-record-errata-mechanism.md:19` — a
  living product intent restating the retired rule; excluded from AC-0023
  because it is shaping material, not a governing convention.
- eugenelim: `workspace.toml` `[backlog].open` entry on
  `packs/governance-extras/seeds/governance/manifest.example.yaml` — the three
  governance-index documentation-versus-code defects found while measuring
  whether `Areas` duplicates the index's `domains:` key.
- a peer session in this worktree: `docs/rfc/0102-mechanically-checkable-adrs.md`
  §§ 6 and 7 describe a 559-finding corpus that no longer exists. The RFC's own
  errata convention is the mechanism; that session owns the edit.

RFC-0102's corpus-migration and enforcement-flip follow-ons are **closed**: the
migration landed in commit `4b2714112`, and this delivery ships the gate
blocking rather than deferring the flip.

Frozen specs that state the retired rule —
`docs/specs/pack-test-boundary-remaining-packs/spec.md:575` and its `plan.md:711`,
and `docs/specs/npm-dependabot-wiring/spec.md:64` — take Status-line pointers
only and are therefore not editable by this delivery and not follow-on work.

## Assumptions

- Technical: the corpus is migrated. Commit `4b2714112` brought all 115 records
  to the new format and `7fbc73075` normalized the last two shape outliers. The
  residual, measured against all fifteen predicates as this spec states them,
  is **8 finding lines naming 4 record paths, remedied by 2 record edits**. The
  unit is the emitted finding line, because the plan's output contract gives one
  record path per line: ADR-0023 and ADR-0050 each carry a non-bare `Status` and
  no `Superseded by:` field, which is 4 lines, and each of the two unmirrored
  `Supersedes:` entries on ADR-0042 and ADR-0109 is reported against both ends
  under AC-0004, which is 4 more. Fixing the two records clears all eight.
  Every other class measures 0 (source: probe over all fifteen predicates,
  2026-09-17). Two earlier figures here were wrong and are corrected rather than
  defended: "4 findings in 2 records" was measured with a probe implementing
  nine of the fifteen predicates and no mirror rules, and "6 findings" counted
  distinct defects under a unit the contract does not use.
- Technical: the corpus carried two shape variants that a naive reader
  mishandles. ADR-0070's `Signal` value is an indented block on the following
  lines; a line-scoped regex reads it as empty, which is what made an earlier
  probe of mine report a finding that does not exist. It is the only record
  written that way and it stays that way, so AC-0008 makes the reader handle
  it. ADR-0055 and ADR-0056 wrote their whole metadata block as `**Key:** value`
  with a trailing hard break and no leading `- ` — the same shape that makes
  `check-adr-immutability` skip them — and both were normalized to the bulleted
  form in this delivery rather than given a tolerance rule, so no criterion
  carries that variant and the corpus is now uniform. Both already had `Areas`,
  `Reversibility` and all four supersession fields; the migration reached them
  (source: re-measure and normalization 2026-09-17; owner direction; RFC-0102
  § 6 on the bulletless pair).
- Technical: ADR-0023 and ADR-0050 carry their supersession pointer only in
  `Status` text and have no `Superseded by:` field, while their counterparts
  ADR-0042 and ADR-0109 already declare `Supersedes:`. The index derives its
  Status cell from that text through `_status_token`, so bare-tokening the two
  records drops both pointers from `docs/adr/README.md` unless the generator
  reads the field first. This is why the generator change is in scope despite
  the original four-bullet framing (source: the four records, `docs/adr/README.md:27,54`,
  and `index-records.py:62-63,94-100`, 2026-09-17).
- Technical: `## Decision drivers` sits in RFC-0102's tier T2 but has no check
  class, deliberately. The template marks the section OPTIONAL
  (`assets/adr.md:78`), so a presence check can never fire, and its only
  layout property — a list of entries — is what `ADR-S014` already checks on
  the sibling section. The class count stays at fifteen.
- Technical: the two sibling ADR gates run a single projected pack script, not a
  `tools/` copy, and say so in the file (source:
  `tools/repo/build_gate_chain.py:258-278`). RFC-0102 § 6 says the lint is
  "ported to `tools/`"; this spec narrows that to one copy (source: user
  confirmation 2026-09-17).
- Technical: the shared helper sits beside its importers in `scripts/`, not in a
  pack-level `shared-libs/`. `packs/credential-brokers/.apm/shared-libs/` is not
  projected — `git ls-files` shows it only under `packs/` — and these scripts run
  standalone from their projection, while `packs/core/.apm/skills/work-loop/scripts/`
  ships `_loop_guards.py`, `_statelock.py` and `file_safety.py` beside their
  consumers and projects wholesale (source: the two listings, 2026-09-17; owner
  chose extraction over a third copy, user confirmation 2026-09-17).
- Technical: the helper is loaded by path from the loading script's own resolved
  directory. `packs/AGENTS.md:29-33` forbids putting a skill's `scripts/` on
  `sys.path` and importing by bare name, and `check-spec-status.py:69-114` loads
  its sibling through `importlib.util.spec_from_file_location` and refuses every
  verb when the load fails (source: both files, 2026-09-17).
- Technical: **the structural delegation criterion was cut, and identifiers
  were not renumbered, so the seventh slot is deliberately empty.** Four
  formulations failed — a deny list that could not close, a positive claim that
  still needed a classifier, and an over-inclusive collector that no
  implementation could satisfy because `print` and the mandated UTF-8
  reconfigure fall inside it. The behavioural property it protected keeps three
  owners: AC-0006, AC-0031 and T3's hostile fixture tree. What lost its gated
  owner is the structural claim that the lint makes no filesystem call outside
  the helper, which survives as a plan design decision only. Two helper
  guarantees had no behavioural case behind them once that went — the hard-link
  refusal and the root-relative containment check — so T3 gains a case for each
  rather than leaving them unowned. Identifiers keep their numbers and the
  seventh is simply absent, because five rounds of persisted review artifacts
  cite them by number
  (owner direction 2026-09-17).
- Technical: **accepted residual — the finding stream is not neutralized against
  record-controlled values.** A field value or filename carrying a newline or an
  ANSI escape can forge or hide a line in the CI log. The scope is the finding and warning
  stream only: `index-records.py`'s artifact path already neutralizes every
  record-controlled cell through `_escape_cell` and `_escape_destination`, and
  AC-0032 keeps it that way for the value this delivery adds. What the two
  siblings share with this lint is the unneutralized `_warn` stream. Owner-accepted 2026-09-17; no criterion claims otherwise.
- Technical: **accepted residual — the per-file read is unbounded.**
  `file_safety.py`'s budget is caller-supplied (`max_bytes: int | None = None`,
  no default constant), so the helper enforces nothing unless a caller passes a
  value, and this contract states none. The consequence: a single oversized
  committed record exhausts a merge-blocking CI step rather than an advisory
  one, which is a denial of merge rather than a slow warning. No criterion claims
  byte-budget or encoding ownership; the helper owns symlink and
  non-regular-file refusal, which its cases prove. Owner-accepted 2026-09-17
  (source: `file_safety.py:354,428-465`).
- Technical: AC-0001 declares a per-case expected code set rather than a single
  code, because RFC-0102 § 3 mirrors field-by-field: an `ADR-S008` mutation adds
  an entry with no counterpart, and `ADR-S010` fires with it.
- Technical: the lint takes no `--strict` flag. AC-0002 makes exit 1
  unconditional on any finding, so a flag would change nothing, and a flag that
  changes nothing is one a later argv edit drops with every test still green
  (source: spec-stage review round 4, sustained in both lanes).
- Technical: adding a gate-chain step trips an exact-list pin that compares
  script paths, not argv (source: `tools/test_build_gate_chain.py:821`,
  asserted at `:1346`; argv is asserted only for `lint-spec-status.py` at
  `:1347-1351`). AC-0010 now requires an argv assertion for both new steps on
  that same mechanism, so what the path pin alone cannot see — a wrong directory
  or a changed argument — has an owner; AC-0009 observes the step's behaviour
  over the real corpus, which is a different property.
- Technical: `new-adr`'s SKILL.md is 335 body lines — 341 total less a six-line
  YAML frontmatter, `---` on lines 1 and 6 — measured the way
  `skill_spec_lint.py` measures it. CAT-S003 warns above 500 and errors only
  above 1000, so T6 asserts the body line count directly (source:
  `packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py:518-527`).
- Technical: the suggested `Related:` shape is not linted and cannot be. A gloss
  may legitimately contain a `;` inside a quoted clause, so entries are not
  recoverable by splitting on the separator without quote-aware parsing. That is
  why RFC-0102 § 1 places `Related` in tier T1-unchecked, and it is not an
  oversight to be closed later by adding a check.
- Technical: **`ADR-S014` is narrowed to presence, and this spec owns that
  predicate.** As "at least one top-level `- ` entry" it fired on 32 of the 103
  records carrying the section, which write alternatives as bolded paragraphs.
  RFC-0102 fixes no entry shape for the section, so the bullet requirement was
  never the RFC's — an earlier revision credited RFC-0102 § 1 for a predicate
  this spec invented. RFC-0102 `:362` does license "an alternatives shape" among
  its one-time body conversions, so narrowing defers a licensed conversion
  rather than merely correcting a misreading; that conversion is now a
  Follow-on. Owner-confirmed 2026-09-17 (source: probe, 32 of 103; RFC-0102
  `:134`, `:359-363`).
- Technical: `ADR-S014` checks presence only, not that each alternative cites a
  declared driver. RFC-0102 § 1 states tier T2 is "presence and layout checked;
  wording never" (source: `docs/rfc/0102-mechanically-checkable-adrs.md:134`,
  re-read after commit `d6ed7e9a1` moved it). That commit also removed the
  § 7 row asking for alternatives to be rewritten to cite a declared driver, so
  nothing now asks for the stronger check.
- Technical: the adopter seed `packs/governance-extras/seeds/docs/adr/README.md`
  is an empty generated index table and states no freeze rule (source: read
  2026-09-17).
- Technical: the `.claude/` and `.agents/` projections need no task of their own.
  Self-host produces them and `build-check.yml` refuses a merge on projection
  drift (source: spec-stage adjudication against `packs/AGENTS.md`
  § Self-hosting projection and `.github/workflows/build-check.yml:3-6`).
- Process: **named deviation — the gate ships blocking, where RFC-0102 still
  says advisory-then-blocking** (`:18`, `:336`, `:562`, re-read after commit
  `d6ed7e9a1`). The RFC's stated precondition for the flip is a migrated
  corpus, and the migration landed in `4b2714112`, so the deviation is from the
  sequencing rather than from the intent. Recorded on the owner's authority
  (user confirmation 2026-09-17). A peer session owns reconciling the RFC's own
  text; this spec does not edit it.
- Process: a corpus-wide blocking gate cannot leave `main` red behind two
  independently green pull requests. `gh api repos/:owner/:repo/branches/main/protection`
  reports `required_status_checks.strict = true` with `make build-check` among
  the required contexts, so a branch must be up to date before merging and the
  gate chain re-runs against the updated branch. Spec-stage review raised this
  as a risk and left it indeterminate for want of this setting (source: read
  2026-09-17).
- Technical: `docs/CONVENTIONS.md` was retired by commit `813f533f1` after this
  contract's baseline was sealed, and its obligations were re-homed — the
  document lifecycle classes to a new seeded `docs/README.md`, the
  frozen-document supersession rules to
  `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md`. Two
  consequences. The retired Status-only rule survives on no re-homed surface, so
  AC-0023's set drops from five members to four. And `docs/README.md` classifies
  `adr/` as `frozen`, a class it defines at `:43-44` as "an immutable record …
  Never edited to reflect a later change", which contradicts RFC-0102 § 4's
  writable metadata block — so RFC-0102's sequencing precondition now points at
  that file, and AC-0033 carries it. The shared-row problem the earlier
  `Never do` boundary guarded against is gone: `docs/README.md` gives `adr/`,
  `specs/` and `rfc/` separate rows (source: `813f533f1`; `docs/README.md:14-22,41-50`;
  read 2026-09-17).
- Process: scope was RFC-0102's four "Shipped on this RFC's acceptance" bullets;
  the completed migration added the generator change, two record fixes, and
  ADR-0027's erratum, all on user confirmation 2026-09-17.
- Process: ADR-0027's `D5` states existing ADRs keep `Deciders` and are not
  rewritten. The migration removed every `Deciders` key, so D5 is contradicted
  in fact; the override rests on RFC-0102's authority and is recorded on the
  record itself by AC-0020's erratum rather than only here (source: user
  direction 2026-09-17; `docs/adr/0027-*.md:47`).
- Process: this spec registers as a queue entry under ini-002 Platform Core
  (source: user confirmation 2026-09-17).
- Process: the release entry is a free-standing heading directly beneath
  `[Unreleased]` (source: `docs/product/changelog.md:11-18`).
- Process: a non-cosmetic pack update also updates that pack's eval harness,
  which is why AC-0030 is an obligation (source: `packs/AGENTS.md`
  § "Security and authoring rules").
- Product: the users are ADR authors and readers in this repository and in any
  repository installing `governance-extras`. Adopter-facing usability beyond
  shipping the lint portably is not measured here.
