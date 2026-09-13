# Spec: Index table generation

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0112](../../adr/0112-index-tables-are-generated-or-absent.md); [ADR-0006](../../adr/0006-doc-drift-construction-and-judgment.md) (no fail-closed adopter gate); [ADR-0007](../../adr/0007-ship-doc-drift-lint-as-work-loop-skill-script.md) (skill-script delivery route); [RFC-0002](../../rfc/0002-self-hosting.md) 2026-09-13 erratum
- **Brief:** none
- **Discovery:** none
- **Contract:** none in `contracts/` — the shipped surface is a CLI, for which no conventional contract format applies. Its flags, exit codes, and output shape are pinned by AC9-AC14 instead.
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing PR must match this spec, or update it. Verification must be derivable from it.

> **Not every section is contract.** Objective, Boundaries, Testing Strategy, and
> Acceptance Criteria are contract tier and bind the implementation. Durable
> Outputs and Assumptions are working material: they record decisions and
> evidence, and a finding against them is advisory unless it shows a contract
> section is wrong.

## Objective

A decision-record index is derived from the records it indexes, in any
repository that installs the `governance-extras` pack, and a spec corpus has no
index at all.

Three user-visible outcomes:

1. **`index-records.py [--check] [--type adr|rfc] <record-dir>` maintains
   `<record-dir>/README.md`** from the records in that directory. Without
   `--check` it writes the file; with `--check` it writes nothing and reports
   divergence through its exit code. The file is the record type's heading and
   its table, and nothing else, so it holds no path an adopter's tree might not
   have. The directory is an argument and no path is a constant, so the command
   serves an adopter's record directory wherever it resolves. A directory
   holding no records yields the pack's placeholder sentinel rather than an
   empty table.
2. **`new-adr` and `new-rfc` create a record by invoking the generator**, and
   the repository's gate chain invokes the same script through its installed
   projection for both record directories.
3. **`docs/specs/README.md` describes the `docs/specs/<feature>/` directory
   convention and carries no index**, and no shipped surface instructs anyone to
   maintain one.

The generator's parse contract is the metadata the bundled `adr.md` and `rfc.md`
templates emit. This repository is one validation corpus among three; it is
never the definition.

## Durable Outputs

| Role | Applicability | Destination | Owner | Evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — the governing decision | `docs/adr/0112-index-tables-are-generated-or-absent.md` | eugenelim | Accepted, in tree | Satisfied before this plan; no further write |
| Interface compatibility | Applicable — reclassifies a published RFC row | `docs/rfc/0002-self-hosting.md` § Errata | eugenelim | 2026-09-13 entry | Satisfied before this plan; no further write |
| Maintainer procedure | Applicable — three skills change their record-creation step | `new-adr/SKILL.md`, `new-rfc/SKILL.md`, `new-spec/SKILL.md`, `work-loop/references/light-mode.md` | eugenelim | Step text names the command; no surface names a hand-edit | Projected copies match pack source |
| Adopter scaffold | Applicable — the seed an adopter receives | `packs/core/seeds/docs/specs/README.md` | eugenelim | Seed carries convention prose and no table | Seed lint passes without a spec-index sentinel |
| Interface compatibility (tooling) | Applicable — the seed placeholder map changes | `packages/agentbundle/.../catalogue_tooling/lint.py` | eugenelim | ADR and RFC sentinels still required | Package version bumped per `packages/AGENTS.md` |
| User-facing promise | Applicable — three guides describe the old behaviour | `guides/core/how-to/plan-and-execute-non-trivial-work.md`, `guides/governance-extras/how-to/new-adr.md`, `guides/governance-extras/how-to/new-rfc.md` | eugenelim | No guide describes a hand-maintained spec index | Guide text matches shipped skill behaviour |
| Release history | Applicable — two packs and one package ship | `docs/product/changelog.md` | eugenelim | Entry naming all three versions | Versions match their manifests |
| Reusable learning | Applicable — the prior-art basis | `docs/product/research/document-index-patterns-survey.md` | eugenelim | Landed, cited by ADR-0112 | Satisfied before this plan; no further write |
| Current architecture | Not applicable | — | — | — | No module boundary moves; the generator joins an existing script family |
| Operations | Not applicable | — | — | — | No runtime service, schedule, or deployed surface |

## Boundaries

### Always do

- Derive every index value from the record it describes, or from git history
  where the record's own metadata is absent.
- Take the record directory as a command argument and write the index inside
  that directory, as `<record-dir>/README.md`.
- Reuse `next-ordinal.py`'s record-classification semantics — a strict ordinal
  match, one `lstat` per entry, and refusal of a record-shaped symlink.
- Validate behaviour against three corpora: the bundled templates, a synthetic
  adopter fixture including the zero-record case, and this repository.

### Ask first

- Before changing the column set of an index that `llms.txt` publishes.
- Before changing any status vocabulary, which the record templates own.
- Before removing a test that currently pins skill step text, as opposed to
  re-pointing it.

### Never do

- **Never introduce a new top-level directory, module boundary, or dependency**
  — the generator is one script in an existing skill `scripts/` directory and
  uses only the standard library.
- Never hard-code a repository path, a record count, or a title from this
  repository's corpus into the generator.
- Never read or write outside the supplied record directory.
- Never delete a record file; the generator writes only the index.
- Never assert that the two installed copies of the generator are identical;
  cross-copy drift is out of scope by owner decision (see `## Follow-ons`).

## Testing Strategy

| Objective outcome | Mode | Why |
| --- | --- | --- |
| Rows parsed and rendered from records (1) | TDD | A pure function from a directory of files to index text — a compressible invariant with an exact expected output. |
| Date resolution chain (1) | TDD | Three ordered branches; deterministic against a fixture repository the test creates. |
| Malformed record, empty directory, unresolvable type (1) | TDD | Refusal- and warning-shaped rules that fail silently when unexercised. |
| Confinement and Markdown escaping (1) | TDD | Adversarial inputs an adopter can hold; each has an exact expected refusal or escape. |
| `--check` exit-code contract (1) | TDD | An exit-code contract, trivially stubbed and mutated. |
| Skills and gate chain invoke the script (2) | Goal-based check | Presence and shape of an invocation is a parse assertion, not behaviour. |
| The real CLI runs end-to-end on both directories (2) | Visual / manual QA | The shipped artifact must be exercised; a passing unit gate is not proof the CLI runs. |
| Spec index absent and unreferenced (3) | Goal-based check | An absence is a parse assertion over the file and its consumers. |

## Acceptance Criteria

**Parsing and rendering**

- [x] **AC1.** The generated index lists one row per record, ordered by parsed ordinal ascending, independent of filesystem iteration order.
- [x] **AC2.** A record is a `*.md` file in the record directory whose first heading matches the record type's H1 form and yields an ordinal; any other entry yields no row.
- [x] **AC3.** An ADR row carries ordinal, linked title, status, and date. An RFC row carries ordinal, linked title, status, date opened, and date closed.
- [x] **AC4.** A row's title text equals its record's H1 title, read from the record and from no other source.
- [x] **AC5.** A row's status equals its record's status token, with any qualifying clause following that token removed.
- [x] **AC6.** A title or filename containing a Markdown table or link delimiter renders as a single well-formed cell whose link resolves to that record.

**Dates**

- [x] **AC7.** When a record carries its date field, the row's date is that value.
- [x] **AC8.** When a record omits its date field and git history is available, the row's date is that file's first-commit date.
- [x] **AC9.** When a record omits its date field and git history is unavailable, the row's date is empty.
- [x] **AC10.** The case in AC9 emits a warning naming the file and the missing field.

**Refusals, warnings, and the empty corpus**

- [x] **AC11.** A `*.md` entry whose H1 matches the record form but yields no ordinal, or which carries no status field, emits a warning naming the file and the missing field.
- [x] **AC12.** The run in AC11 writes the index and exits 0.
- [x] **AC13.** A record-shaped symlink, or any entry resolving outside the supplied record directory, is refused and named, and contributes no row.
- [x] **AC14.** A record directory containing no records, invoked with `--type`, yields an index whose table body is that record type's placeholder sentinel.
- [x] **AC15.** The record type is taken from `--type` when supplied and inferred from the records present otherwise.
- [x] **AC15a.** When the record type is neither supplied nor inferable, the run refuses, names the record type as the missing input, and writes nothing.

**The `--check` contract**

- [x] **AC16.** `--check` writes no file.
- [x] **AC17.** `--check` exits 0 when the on-disk file equals the generated file.
- [x] **AC18.** `--check` exits non-zero and names the first differing line otherwise.

**Portability**

- [x] **AC19.** The generator resolves the record directory from its argument.
- [x] **AC20.** The generator's source contains none of the frozen literals `docs/adr`, `docs/rfc`, `docs/specs`, `agent-ready-repo`, or `eugenelim`.
- [x] **AC21.** Applied to a record instantiated from the bundled `adr.md` template and one from `rfc.md`, the generator produces rows satisfying AC1 and AC3.
- [x] **AC22.** Applied to a synthetic record directory the test creates outside this repository's `docs/`, the generator produces rows satisfying AC1 and AC3.

**Integration**

- [x] **AC23.** `new-adr` and `new-rfc` each invoke the generator at their record-creation step.
- [x] **AC24.** No shipped skill, reference, or seed instructs updating an index by hand.
- [x] **AC25.** The repository gate chain invokes the generator in `--check` mode, through the installed `.claude/skills/` projection, for `docs/adr` and for `docs/rfc`.
- [x] **AC26.** `docs/adr/README.md` and `docs/rfc/README.md` each equal the generator's output for their directory.
- [x] **AC27.** A generated index is the record type's heading followed by its table, and contains no path outside the record directory.

**Retirement**

- [x] **AC28.** `docs/specs/README.md` contains no Markdown table.
- [x] **AC29.** `docs/specs/README.md` retains its description of the `docs/specs/<feature>/` directory convention.
- [x] **AC30.** `packs/core/seeds/docs/specs/README.md` contains no Markdown table.
- [x] **AC31.** The seed placeholder map requires no spec-index sentinel.
- [x] **AC32.** The seed placeholder map requires the ADR sentinel and the RFC sentinel.
- [x] **AC32a.** The ADR and RFC seeds each contain the record type's heading and its table carrying the placeholder sentinel, and no other section.
- [x] **AC33.** No shipped guide states that a skill maintains a spec index.
- [x] **AC34.** The ADR and RFC guides name the generator as the mechanism that maintains their index.
- [x] **AC34a.** `docs/CONVENTIONS.md`'s ADR section names `adr/README.md` and its RFC section names `rfc/README.md`, each stating the index is generated, so the guidance the generated files no longer carry is reachable from the convention that owns it. It is named rather than linked because `CONVENTIONS.md` ships with `core` while those directories arrive with `governance-extras`, so a link dangles in a core-only tree.

**Release**

- [x] **AC35.** `packs/core/pack.toml` is above `2.25.18`, `packs/governance-extras/pack.toml` is above `0.10.6`, and `packages/agentbundle/pyproject.toml` is above `0.44.0` — the three values at this spec's base revision `aa176ee2c`.

## Follow-ons

- Shared library scripts copied into two or more skills through the catalogue —
  the `next-ordinal.py` pair is byte-identical with nothing holding it so, and
  this spec adds a second such pair. Owner decision 2026-09-13 routes this to
  separate catalogue work; this spec adds no cross-copy drift detector, and
  `## Boundaries` forbids one.

## Assumptions

- Technical: the parse contract is the shipped template's metadata, not this corpus — ADR emits `# ADR-NNNN:`, `- **Status:**`, `- **Date:**`; RFC emits `# RFC-NNNN:`, `- **Status:**`, `- **Date opened:**`, `- **Date closed:**` (`new-adr/assets/adr.md`, `new-rfc/assets/rfc.md`).
- Technical: the two record types carry different status vocabularies and different date fields, so the generator is parameterised per type (same two template files).
- Technical: the record directory is an argument, never a constant — `next-ordinal.py` takes it via argparse and already ships a `--check <dir>` mode (`new-adr/scripts/next-ordinal.py:194-215`); `new-adr` resolves its destination semantically, naming `docs/adr/` "the catalogue fallback candidate, not a universal location" (`new-adr/SKILL.md` step 1).
- Technical: record-shaped symlink refusal is an existing control to reuse, not one to invent — `next-ordinal.py:162-170` uses one `lstat` per entry and raises on a record-looking symlink.
- Technical: the gate chain already invokes skill scripts through the `.claude/skills/` projection, including a `--check` mode over a record directory (`build_gate_chain.py:267-271`, `check-adr-ordinals`).
- Technical: the generator's tests run only from `tests/roster/` — the pack's natural home is declared `"never gated"` (`tools/lint-pack-test-boundary.py:1269-1270`) and no workflow executes it; `tests/roster/` runs in `test-roster.yml:91`.
- Technical: Python floor is 3.11 (`packages/agentbundle/pyproject.toml`).
- Process: the zero-record state is pinned — the seed lint requires `<!-- no ADRs yet -->` / `<!-- no RFCs yet -->` (`catalogue_tooling/lint.py:515-518`).
- Process: no mechanical check reads a frozen acceptance criterion's assertion, so the 16 ticked criteria naming the retired spec index cannot redden any gate; `lint-spec-status.py`'s dangling-reference invariant does not engage, because `docs/specs/README.md` continues to exist.
- Process: pack content changes bump `pack.toml` and `.claude-plugin/plugin.json` (`packs/AGENTS.md`); an `agentbundle` change bumps that package's own version (`packages/AGENTS.md`).
- Product: the ADR index carries a Date column, with git history as the fallback when a record omits the field (user confirmation 2026-09-13).
- Product: a malformed record warns and the run still produces the index (user confirmation 2026-09-13).
- Product: the row title is the record's H1, and the resulting rewrite of this repository's drifted index titles is accepted rather than preserved by an override map (user confirmation 2026-09-13, on measurements recorded in the plan's *Title provenance* note).
- Process: shipped guides are updated in the same session as the behaviour they describe (user confirmation 2026-09-13).
