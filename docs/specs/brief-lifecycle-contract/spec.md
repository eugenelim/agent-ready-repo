# Spec: a brief's lifecycle is a closed contract, and a closed cut is declared

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0098, ADR-0077
- **Brief:** brief:intent-lifecycle-and-closure
- **Discovery:** docs/product/intents/FEAT-0005-lifecycle-and-closure.md
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy`,
> `The brief state table` and `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A maintainer closing a delivery brief declares that no further slices are
coming, and a brief that claims delivery without that declaration is refused.
A brief's states, legal moves and coherence rules have one defining home in code, so the
vocabulary is decided once rather than restated wherever it is needed.

## What Changes

- The six-token status vocabulary, the coherence predicate and the legal
  transition set — into a new `brief_shape.py` in
  `packs/core/.apm/skills/author-delivery-brief/scripts/`, beside the only
  script that imports it
- `Cut-closed:`, a preamble field declaring the cut finished — onto a brief's
  preamble, absent by default
- A bounded preamble reader, one accessor per field it reads, and the shared
  value tokenizer — into `brief_shape.py`. `extract_token` moves with them, so one
  definition serves the brief and spec paths both; the plan's § Component /
  module decomposition owns how the lint loads it back
- `parse_brief_status` **and `parse_brief_slug`**, both repaired to read
  through that reader, and `_BRIEF_STATUSES` and `_brief_lifecycle_is_valid()`
  removed — in `lint-brief-coverage.py`. The slug read matters most: its own
  docstring records that the rollup joins on that field, so an unbounded read
  lets a `Slug:` line in a body or an HTML comment re-key which specs count as
  a brief's children — which then feeds the coherence rule AC-0012 pins
- `parse_spec_map`, made comment-aware through the same pass — in
  `lint-brief-coverage.py`. It reads a brief's `## Spec map` **body section**
  rather than a preamble field, and is repaired here because its rows become
  `child_states`, the input to the coherence rule AC-0012 pins: a commented-out
  row parses as live today, so a brief can read coherent or delivered on rows
  its author believes they disabled
- One `Cut-closed:` record on `tech-site-completion.md`, the only `Shipped`
  brief — so the gate does not ship refusing the corpus it governs
- The `Cut-closed:` row and the transition table — into
  `guides/core/reference/product-brief-fields.md`, which already owns the
  reader-facing statement of a brief's fields and states, and which gains a
  line naming `brief_shape.py` as the source its tables are derived from
- A citation replacing the restated vocabulary and child-evidence rule — in
  `author-delivery-brief/SKILL.md` § Brief lifecycle, which states both in
  prose today
- The `Cut-closed:` row — into `packs/core/seeds/docs/product/briefs/_template.md`,
  so a closing maintainer is prompted rather than refused
- A note that the refusal is the lint's — in `close-work/SKILL.md`, whose brief
  path is prose and carries no independent behaviour

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Applicable — a new module owns a vocabulary and a rule set that other checks read | `brief_shape.py` module docstring | eugenelim | The docstring cites § The brief state table rather than restating it, carries the refusal registry, and names that two hand-mirror obligations exist. Each mirrored function carries its own note in its own docstring: `extract_token` against `lint-spec-status.extract_status_token`, and the `Cut-closed:` date-grammar check against `intent_shape._check_dated_evidence` — beside the delimiters and the grammar a change would touch, not two hundred lines above them | AC-0019's search returns only `brief_shape.py`; the docstring's refusal set equals the registry; and a read confirms the docstring cites § The brief state table rather than restating the tables, that each mirrored function's docstring names its counterpart, and that the module docstring names both mirrors exist. The citation item needs the read most: AC-0019 matches a collection literal, so a docstring spelling the tables out in prose is out of its scope by design. A read, not a test — the mirrors are hand-held by design |
| Maintainer procedure | Applicable — the reader-facing statement of a brief's fields and states already exists and gains two entries | `guides/core/reference/product-brief-fields.md` | eugenelim | A `Cut-closed:` field row, the transition table, and the per-status declaration rule | The page carries its tables and a line naming `brief_shape.py` as the source they are derived from |
| Release history | Applicable — a gate that newly refuses a brief changes an adopter's obligation | `docs/product/changelog.md` | eugenelim | A free-standing `##` entry with a `### Changed` block and a `### Highlights` block | The entry is not nested under `[Unreleased]` |
| Interface compatibility | Applicable — two symbols are removed from a module another in-flight slice may import | `lint-brief-coverage.py` | eugenelim | AC-0019 green, and slice 2's replacement import named in § Assumptions | No second executable definition survives under `packs/*/.apm/`; prose consolidation is a Follow-on |
| Decision rationale | Not applicable — this slice implements a delivery map the brief already settled and takes no decision an ADR would own | — | — | — | — |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Verify a field's placement by reading it back through the bounded reader, never by eye. A misplaced declaration is invisible to a reader and decisive to the parser.
- Run `git diff --numstat` after touching any brief and confirm each artifact gained only the lines intended.
- Keep the module docstring's refusal registry equal to the refusals the module raises, in the same change that adds or removes one.
- Keep `brief_shape.extract_token` in lockstep with `lint-spec-status.extract_status_token`, and the `Cut-closed:` date grammar in lockstep with `intent_shape._check_dated_evidence`. Both are hand-mirrored because cross-skill import is banned, and neither has a gate.

### Ask first

- Adding, removing or renaming any token in the six-state vocabulary, or any row of the transition table — both are published contract an adopter reads.
- Requiring `Cut-closed:` on a state this spec exempts, which would oblige a migration across the brief corpus.
- Backfilling a `Cut-closed:` record onto any brief other than `tech-site-completion.md`.

### Never do

- Do not add a new top-level directory or a new runtime dependency; `brief_shape.py` uses the standard library only.
- Do not import across skill directories. `guides/_shared/reference/skill-script-conventions.md` bans it and adapter projection breaks it.
- Do not leave a second definition of the vocabulary or the coherence predicate in any source file under `packs/*/.apm/`.
- Do not gate a transition on anything read from an artifact body rather than the bounded preamble. The `## Spec map` section is the one body read the shipped rollup already depends on; it feeds coherence, the drift check and the delivered rollup — but no transition rule, which is what this bullet governs — and AC-0025 through AC-0029 give its comment handling its own contract.

## Testing Strategy

- **The bounded reader at the module boundary — AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006:** TDD. Each is a pure predicate over a parsed preamble. They are stated over *a preamble field* rather than per field, because one reader serves both and a per-field fixture would leave the shared rule unproven.
- **The bounded reader at the consumer — AC-0007:** TDD through the lint's own entry point. The module rules above do not reach it: a correct reader that no consumer calls leaves today's unbounded scan in place, which is the defect this spec exists to repair.
- **No second reader — AC-0024:** goal-based check, a source-absence search over `lint-brief-coverage.py`. Two criteria rather than one, because a leaked delegation and a surviving second reader have different remedies — and different verification modes.
- **Field value shape — AC-0008, AC-0009:** TDD. AC-0009 is AC-0008's accepting twin and pins a well-formed value, so an implementation refusing every value cannot pass.
- **The state table — AC-0010, AC-0011, AC-0012:** TDD at the module boundary, pinning all six states before the predicate moves. The shipped CLI suite exercises only `Executing` and `Shipped`, so four rows are unexercised today and "the existing suite still passes" would not detect a change in them.
- **The declaration matrix — AC-0013, AC-0014, AC-0015, AC-0016:** TDD. Between them they decide all twelve status × presence cells.
- **The transition table — AC-0017, AC-0018:** TDD over ordered snapshot pairs, enumerating the complement of the table this spec states. The oracle is the spec's table, not the implementation's.
- **One home — AC-0019:** goal-based check, as a repository-level search whose match rule the criterion states.
- **The Spec-map reader — AC-0025, AC-0026, AC-0027, AC-0028, AC-0029, AC-0030:** TDD through the lint's entry point, each fixture asserting the coherence verdict as well as the parse, because the failure runs through `child_states` rather than stopping at the parse. Six criteria: three line-level decisions — opening, terminating, row admission — the unterminated case the preamble's AC-0006 established needs its own verdict, and two at the line-span level **for row admission only** — separating a comment whose state changes across the line from one opening and closing within it. The heading decisions resolve a partly commented line on its live prefix instead, which AC-0029 states so it is not left to inference. The second of those pair preserves a shipped annotation shape rather than adding a rule. **AC-0027 carries the dangerous direction**: dropped rows *remove* children, so a `Shipped` brief losing its one non-`Shipped` row would validate and report delivered. Its fixture is that brief, so the assertion reds on a gate wrongly passing rather than only on one wrongly refusing. Measured 2026-09-25, no brief carries a comment in a Spec-map section, so these are preventive and the real-tree run is unaffected.
- **The corpus run — AC-0020:** goal-based check. The real-tree run is the oracle and no fixture stands in for it.
- **Refusal surface — AC-0021, AC-0022:** TDD. Separate criteria because a message defect and an exit-code defect have different remedies.
- **The seed template — AC-0023:** TDD. A template that parses wrong seeds a malformed field into every brief copied from it, so it is checked rather than reasoned about.

## The brief state table

Contract. `brief_shape.py` implements it and its docstring cites this section
rather than restating it. The reader-facing guide restates the tables, because
being the authoritative field list is that page's job, and carries a line
naming `brief_shape.py` as what they are derived from.

**A brief's children** are its Spec-map rows together with any spec that
back-links the brief and is absent from that map. The lint already joins both,
deliberately — an unreconciled map may not hide execution evidence from
lifecycle validation.

| State | Child execution evidence | `Cut-closed:` |
| --- | --- | --- |
| `Draft` | no child at `Implementing` or `Shipped` | refused — `Draft` means open |
| `Ready` | no child at `Implementing` or `Shipped` | permitted |
| `Executing` | at least one child at `Implementing` or `Shipped` | permitted — a cut may close while a slice runs |
| `Shipped` | non-empty child set, every child `Shipped` | required |
| `Withdrawn` | no child at `Implementing` or `Shipped` | permitted, not required |
| `Cancelled` | at least one child at `Implementing` or `Shipped` | permitted, not required |

`Draft` refuses the record for a reason that needs no classification of the
other five: a `Draft` brief is the one a material edit returns a brief to, and
a material edit changes the delivery map, and a cut declaration is a claim about that map, so a material edit falsifies it. No
single predicate separates `Draft` from `Ready` cleanly — the cut confirmation
happens *at* `Ready`, per the parent brief's § Candidate delivery slices — so
the `Cut-closed:` column above carries each other row's disposition directly
rather than deriving all six from one question.
exactly two edges carry a record obligation, and the paragraph below the moves
table names both.

The legal moves. A pair of **two different states** absent from this table is
refused; a state paired with itself is not a move.

| From | To |
| --- | --- |
| `Draft` | `Ready`, `Withdrawn` |
| `Ready` | `Draft`, `Executing`, `Withdrawn` |
| `Executing` | `Ready`, `Shipped`, `Cancelled` |
| `Shipped` | — terminal |
| `Withdrawn` | — terminal |
| `Cancelled` | — terminal |

**Two edges carry a record obligation, and neither is enforced as a move.**
`Executing` → `Shipped` must *add* the record, because `Shipped` requires one
and is terminal — a brief arriving without it is refused by AC-0013 and has no
legal move out. `Ready` → `Draft` must *clear* it, and is the only edge into a
refusing state. The move is `author-delivery-brief` § Mode:
continue › 2. Run shaping review before the Ready decision returning a brief to
`Draft` on a material edit, which reopens the brief — so a declaration that its
cut was closed is no longer true and is removed rather than preserved. **Both obligations are on whoever makes the move, and no gate enforces
either**: the lint reads one snapshot and cannot see a move. What it enforces
is the consequence — AC-0013 for the missing record at `Shipped`, AC-0016 for
the surviving one at `Draft`.

`Executing` → `Ready` is reachable only after a child's own status regresses
below `Implementing` first; a child status is never rewritten to make a brief
transition fit. Because `Ready` permits the record, that return costs a brief
nothing: a cut declared while `Executing` survives the round trip. The parent
brief took this move on 2026-09-24 when its only materialized child was parked,
and `workspace.toml` records it.

## Acceptance Criteria

**Each criterion is one rule, and a brief must satisfy every rule.** "Accepted"
below means *not refused by this rule* — it never means the brief passes the
lint, because a different rule may still refuse it.

- [x] **AC-0001.** A preamble field below the first uncommented `## ` heading is not read.
- [x] **AC-0002.** A preamble field inside an HTML comment is not read, including a comment spanning several lines.
- [x] **AC-0003.** A `## ` heading inside an HTML comment does not end the preamble, so a field between that comment and the first uncommented heading is read.
- [x] **AC-0004.** A field-shaped line that is itself an ATX heading is not read as a preamble field.
- [x] **AC-0005.** A field-shaped line inside a blockquote is not read as a preamble field.
- [x] **AC-0006.** For a brief whose preamble opens an HTML comment that is never closed, the reader returns no fields at all. The refusal that follows is AC-0011's.
- [x] **AC-0007.** Every bounding rule AC-0001 through AC-0006, for every brief preamble field the lint reads — `Status:`, `Cut-closed:` and `Slug:` — is asserted through the lint's own entry point. The value the lint acts on equals what `brief_shape`'s accessor for that field returns on the same input, and every such assertion is a **differential**: the lint's output differs between a bounded and an unbounded read, so no assertion can be satisfied by unrepaired code. The plan owns how each fixture achieves that.
- [x] **AC-0008.** A `Cut-closed:` value that is neither absent-equivalent under AC-0009 nor an ISO 8601 date followed by non-empty evidence text is refused, and the refusal names the value.
- [x] **AC-0009.** A `Cut-closed:` line whose value is empty or only an HTML comment counts as absent, not malformed, so a template row copied into a new brief is not refused.
- [x] **AC-0010.** The brief status vocabulary is exactly `Draft`, `Ready`, `Executing`, `Shipped`, `Withdrawn`, `Cancelled`, and a brief carrying any other token is refused.
- [x] **AC-0011.** A brief whose status is absent is refused, and the refusal says the status is absent rather than reporting it as a contradiction.
- [x] **AC-0012.** For each of the six states, a brief whose children's execution evidence contradicts that state's row in § The brief state table is refused, and one whose evidence matches is not refused by this rule.
- [x] **AC-0013.** A brief whose status is `Shipped` and which carries no `Cut-closed:` record is refused.
- [x] **AC-0014.** A brief whose status is `Draft`, `Ready` or `Executing` and which carries no `Cut-closed:` record is not refused by this rule.
- [x] **AC-0015.** A brief whose status is `Withdrawn` or `Cancelled` and which carries no `Cut-closed:` record is not refused by this rule.
- [x] **AC-0016.** A brief whose status is `Draft` and which carries a `Cut-closed:` record is refused; one in any other state carrying a well-formed record is not refused by this rule.
- [x] **AC-0017.** An ordered pair of two different brief states absent from § The brief state table's legal-moves table is refused.
- [x] **AC-0018.** An ordered pair present in that table, and any state paired with itself, is not refused by this rule.
- [x] **AC-0019.** No `*.py` file under `packs/*/.apm/` other than `brief_shape.py` contains a collection literal among whose own directly enumerated string members all six status tokens appear, compared case-sensitively and without flattening nesting. A superset counts — a literal adding a seventh member such as `"missing"` is still a second definition — and a literal whose members are themselves collections is not one, because the tokens are not its own members. A mapping's keys are its own members and do count: a dict keyed by the six tokens is the most natural way to re-encode this state table. **This is a mechanical proxy for "no second executable definition", not that property itself**: a union of two literals, a split string, or an `Enum` binds the vocabulary and escapes it. The residual is carried by § Agent Rules › Never do rather than by a broader search. Re-implementing the child-execution-evidence predicate is forbidden by § Agent Rules › Never do, which is an authoring rule rather than a searchable one.
- [x] **AC-0020.** `python3 packs/core/.apm/skills/author-delivery-brief/scripts/lint-brief-coverage.py --root .` exits 0 against the real tree at delivery.
- [x] **AC-0021.** Every refusal the lint reports names the offending brief by its path relative to the `--root` it was given, and names the record at fault.
- [x] **AC-0022.** The lint exits 1 on every refusal reachable from a single snapshot.
- [x] **AC-0023.** A brief created by copying `packs/core/seeds/docs/product/briefs/_template.md` is not refused by any rule this spec adds. This is deliberately the one cross-rule criterion: the template's whole value is that a maintainer can copy it and pass every gate.
- [x] **AC-0024.** No second scan of any brief preamble field survives in `lint-brief-coverage.py` — not `Status:`, not `Cut-closed:`, not `Slug:`, and not a field added later. This rule reaches **preamble fields only**. Its one declared exception is `parse_spec`'s scan of a **spec's** status, because specs are not briefs and `brief_shape`'s reader does not govern them. `parse_spec_map` reads a body section and so falls outside this rule's scope entirely; it keeps existing, and AC-0025 through AC-0029 give its comment handling its own contract.
- [x] **AC-0025.** A `## Spec map` heading inside an HTML comment does not open the Spec-map section, so rows below it are not parsed as Spec-map rows.
- [x] **AC-0026.** A Spec-map table row inside an HTML comment is not parsed as a Spec-map row: it produces no per-row coverage entry and the drift check does not compare against it. Its effect on the child set depends on which arm the spec reaches, and both are asserted — a spec that back-links the brief moves from the mapped arm to the untracked arm, so its status still reaches the child set and it is additionally reported as untracked; a mapped spec carrying no back-link leaves the child set entirely.
- [x] **AC-0027.** A `## ` heading inside an HTML comment does not end the Spec-map section, so rows below it are still parsed — the same rule AC-0003 sets for the preamble, applied to the section's closing bound.
- [x] **AC-0028.** An HTML comment opened inside the Spec-map section and never closed yields the rows above it and none after it, and does not end the section by other means.
- [x] **AC-0029.** *Row admission only; AC-0025 and AC-0027 govern the heading decisions, and a heading is judged on its live prefix — `## Spec map <!--` still opens the section and `## Other <!--` still ends it, because only a heading whose live prefix is empty is exempted — `--> ## Other` has a live suffix rather than a prefix and so is not a heading either.* A line across which comment state **changes** — a comment opened on it and not closed on it, or closed on it and not opened on it — is not a Spec-map row, so a live prefix such as `| alpha | Ship<!--` produces no row rather than a truncated one.
- [x] **AC-0030.** A comment that opens **and** closes within one line leaves that row parsed, and the status the lint acts on for it is unchanged from today: `| alpha | Shipped <!-- re-derived 2026-06-01 --> |` is a row whose effective recorded status is `Shipped`. The pinned behaviour is the **entry-point result**, not `parse_spec_map`'s return value — the function returns the raw cell today and the truncation happens later, so an implementation that strips the span earlier also satisfies this. This is a supported annotation shape — `extract_token` truncates at `<!--` by design — and the comment-aware pass may not silently retire it.

## Assumptions

- **Slice 2's interim import.** The parent brief permits slice 2 to consume the shipped `_BRIEF_STATUSES` while slice 3 is in flight, and this branch carries both. After this lands that symbol is gone; slice 2 loads `brief_shape` instead. Recorded here because slice 2's spec does not exist yet and nothing else would carry the change.

## Follow-ons

- **Consolidating the prose statements of the brief lifecycle.** Measured 2026-09-25, four prose surfaces under `packs/*/.apm/` state the six tokens or the child-execution-evidence rule. This slice converts one of them, `author-delivery-brief/SKILL.md` § Brief lifecycle, because T6 already edits that skill. Three are deferred: `close-work/SKILL.md` § Closeout procedure step 1, `lint-brief-coverage.py`'s module docstring, and `close-work/evals/evals.json`. AC-0019 reaches none of them by design — deciding whether a paraphrase restates a rule is a judgement no search performs, and four rounds of review found a new surface each time it was attempted. Each should become a citation of `brief_shape.py`, as a change whose unit is editorial rather than mechanical. Owner: eugenelim, under `brief:intent-lifecycle-and-closure`.
- **A behavioural gate for the two hand-mirrors was available and declined.** § Agent Rules records that `extract_token`/`extract_status_token` and the `Cut-closed:` date grammar against `intent_shape._check_dated_evidence` have no gate. That remains true, and it is a choice rather than an impossibility: a repository-level test can load all three modules by path under pack-and-skill-qualified names and assert each pair agrees over a shared case table, which is behavioural rather than source-text and reds on either mirror drifting. **The cross-skill import ban is not what blocks it** — that ban reaches shipped scripts, not tests, and `packs/core/tests/skills/work-loop/test_loop_guards.py` already reaches into `lint-spec-status.py` from a test. What blocks it is the surface: the check spans three skills, so `tests/AGENTS.md` places it in `tests/roster/`, which obliges a named `build-check.yml` step above the bulk step and a matching `lint-ci-parity.py` disposition entry, and that suite runs about fifteen minutes so the signal arrives on CI rather than locally. Declined 2026-09-25 by eugenelim, lifecycle owner, as disproportionate to a two-function mirror. Recorded here so a later reader does not re-derive the import-ban argument and reach the wrong conclusion. Owner: eugenelim, under `brief:intent-lifecycle-and-closure`.
- **Write-time transition enforcement.** AC-0017 decides a move from an ordered pair. Refusing an illegal move as it is written needs a write-time surface this slice does not build; slice 1 recorded the same boundary for intents. Owner: eugenelim, under `brief:intent-lifecycle-and-closure`.
- **A straddling comment defeats `lint-spec-status.parse_status`.** Measured 2026-09-25: it strips HTML comments before locating the first section heading, so a comment opening in a spec's preamble and closing after that heading extends the preamble into the body. **Reachable only when no live `Status:` precedes the comment** — with one above it the live value is returned, and every spec today carries `Status:` as its first preamble line, so no spec currently reproduces it. Recorded because `Cut-closed:` is absent by default and therefore has no preceding live field. **It is not why this spec's reader uses one pass** — measured 2026-09-25, the two orders return the same value on a terminated straddling comment and diverge only on an unterminated one, which is AC-0006's case and the plan's § Design decisions owns that reasoning. **Nor is the bound-extension itself a defect here**: AC-0003 requires it for briefs deliberately, trading a read past a commented heading against the silent miss of a live field below one. What this Follow-on reports is narrower — that the spec lint reaches that behaviour through an order which also mishandles an unterminated comment. Owner: eugenelim, under `brief:intent-lifecycle-and-closure`.
- **The brief-corpus migration for a required declaration.** Owner decision of 2026-09-24: the field is required only on a brief being closed, so only `tech-site-completion.md` is backfilled. Requiring it universally would oblige a migration across the whole brief corpus — 17 briefs, re-counted 2026-09-25 after `catalogue-discovery-and-release-integrity` was removed upstream in `e56d2a56e`.
