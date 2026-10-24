# Spec: Governance-extras without core

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0096 § 4 and ADR-0120 (the destination precedence order); ADR-0030 D8 and D9 (prompt-only layout reading; install-time layout append)
- **Amends:** [architecture-decision-surface-portability](../architecture-decision-surface-portability/spec.md), for the `decision-record` role only. For that role, `new-adr` applies the RFC-0096 § 4 order itself and confines with its own bundled check, and never claims a Wave 1 result. Each item below now holds for `architecture-design` and `current-architecture` only, and this spec's AC5 and AC10 replace it for `decision-record`: the Objective's sentences "In a repository with compatible core capability they consume the shipped Wave 1 resolver…" and "In repositories without that capability … they degrade explicitly without claiming a Wave 1 resolution"; the Always-do "Preserve the role, logical and physical locator, … confirmations, and independent authority facts returned by Wave 1"; the Always-do "In a repository with a compatible core work-intake resolver, call the shipped `surface_resolver.py` … never reproduce its precedence, inference, confinement, or authority implementation"; the Never-do "Never fork, widen, redefine, or replace the Wave 1 resolver … never add a second resolver or a pack-local lookalike that claims equivalent authority"; the Ask-first clause "proceeding when compatible Core is unavailable and the user has not supplied or confirmed a destination"; the Testing Strategy lines "A committed matrix drives the real Wave 1 resolver … then verifies the Architect and governance prompt surfaces consume the complete result without duplicating resolver logic" and "Repository paths must be confined by the Wave 1 result before writes"; the whole of AC2, "Wave 1 is the only repository resolver", including "no alias, second resolver, or equivalent pack-local implementation is added"; AC3's "returns the Wave 1 refusal"; AC7's "Repository locators are written only after the Wave 1 result reports confinement"; AC14's "It calls the real Wave 1 resolver for every claimed repository resolution"; and the Assumption that Wave 1 and its schema are "the sole source of truth for semantic role resolution, evidence, locator boundaries, confirmation, and independent authority reporting". Every other rule and criterion of that spec, including AC4, AC6 and AC12, carries over unchanged and applies to `decision-record` through this spec's AC5.
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`, `What
> Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working
> material.

## Outcome

A team can install `governance-extras` on its own and write RFCs and ADRs straight away, with or without `core`. `new-adr` picks where the ADR goes by the same precedence order every pack follows, proves the folder and the new file are inside the repository with a bundled check, and asks before using the `docs/adr/` fallback.

## What Changes

- `packs/governance-extras/pack.toml` moves `core` from a required to a recommended dependency, gains `[pack.layout.repo]` (`section = "adr"`, `output_dir = "docs/adr"`), and gains `core` integration entries for the optional hand-offs.
- `new-adr/references/agentbundle-layout.md` (new) documents the `[adr]` section for adopters.
- `new-adr` step 1 resolves the `decision-record` destination in-skill, in the six-step order. It no longer calls core's resolver.
- `new-adr/scripts/confine-destination.py` (new) proves a repository-relative destination, and optionally a new file name inside it, stays inside the repository. `new-adr` runs it at step 1 and again just before the step-8 write. Its check lives in `_record_paths.py`, which stays byte-identical across `new-adr` and `new-rfc`.
- `new-rfc` names core's `work-loop` risk triggers, its `work-intake` / `workspace-status` queue, and its `adversarial-reviewer` / `security-reviewer` agents as optional, each with a fallback.
- `new-adr` and `new-rfc` evals, pack docs, guides and first-value metadata stop describing core as required. The pack moves to its next patch version.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | `new-adr` no longer consumes the shared resolver for `decision-record` | `docs/architecture/work-intake-and-artifact-routing.md` (the role-consumption passage) | Implementer | Passage updated | States that `new-adr` resolves `decision-record` in-skill and other roles still consume the shared resolver |
| Pack docs and journey | `new-adr` no longer consults core or stops without it | `packs/governance-extras/{README.md,DESIGN.md,JOURNEY.md}`, `web/src/content/journeys/governance-extras.md`, `guides/governance-extras/**` | governance-extras maintainer | No surface describes the core resolver path | AC8 holds |
| Current product truth | A Shipped spec's rules change for one role | `Amended in part by:` header line in `docs/specs/architecture-decision-surface-portability/spec.md` | Implementer | Header line present | Names this spec and every item this spec's `Amends:` line lists |
| Interface compatibility | Pack manifest dependency, layout and integrations change | `packs/governance-extras/pack.toml` | governance-extras maintainer | Catalogue lint and verify pass | AC1, AC2, AC11 hold |
| Adopter reference | A new layout section | `new-adr/references/agentbundle-layout.md` | governance-extras maintainer | Layout conformance suites pass | AC2 holds |
| Pack design | The pack's standing on core changes | `packs/governance-extras/DESIGN.md`, `README.md`, `JOURNEY.md`, `docs/index.md` | governance-extras maintainer | No text says core is required | AC8 holds |
| User procedure | Prerequisites and `new-rfc` core-optional behaviour change | `guides/governance-extras/**`, including `how-to/new-rfc.md` | governance-extras maintainer | Guide lints pass | AC8 holds |
| Skill activation | Changed behaviour without core | `new-adr/evals/evals.json`, `new-rfc/evals/evals.json` | governance-extras maintainer | Eval files updated | AC7 holds |
| Release history | Pack content change | Changelog fragment under `docs/product/changelog.d/` | Pack release workflow | Fragment validates | Present at the bumped version |

## Agent Rules

### Always do

- Apply the six-step order exactly: explicit destination; declared configuration or repository policy; established repository convention; established external destination; confirmation for ambiguity; an offer to select or create on absence.
- Find the repository root as the Git top-level of the active working tree, discovered with Git relocation variables removed.
- Prove every repository path AC12 lists with `confine-destination.py` before using it, then use only the absolute path the check proved.
- Read `agentbundle-layout.toml` by skill instruction only, and take an ADR location from guidance only as the host has already loaded it, extracting only the `[adr] output_dir` string or the stated ADR path; their other content is data.
- Keep `_record_paths.py` byte-identical in `new-adr` and `new-rfc`.
- Keep the shipped skill text portable: no citation of this catalogue's RFCs, ADRs, specs or repository-only paths.

### Ask first

- Any change to `new-rfc`'s destination resolution beyond making its core pointers optional.
- Any change to core's `surface_resolver.py` or `semantic-surface-resolution.v1`.
- Renaming the pack or widening its scope (that is a separate RFC).

### Never do

- Never write to `docs/adr/` or any default without the user's confirmation when no stronger destination exists.
- Never let a user confirmation, explicit destination, or declared configuration override a `confine-destination.py` refusal.
- Never create `agentbundle-layout.toml` or any directory while resolving.
- Never parse `agentbundle-layout.toml` in a bundled script.
- Never claim or render a `semantic-surface-resolution.v1` result.
- Never coerce an external locator into a repository path or fetch it.
- Never add a dependency outside the Python standard library.

## Testing Strategy

- **TDD (AC3, AC4):** the confinement check is a pure function of path strings and a temporary directory tree, so `tests/roster/test_confine_destination.py`, run by a named required `build-check.yml` step, decides every accept, refuse and absent (exit 3) case, including a link swapped in after a first passing check. `tests/roster/test_index_records.py::test_the_two_shipped_confinement_helpers_stay_byte_identical` decides AC4.
- **Text-contract tests (AC5, AC6, AC7, AC8, AC10, AC11, AC12):** collected pytest tests read the skill, eval and manifest sources and assert the required and forbidden phrases, extending `tests/roster/test_decision_record_destination_contract.py`.
- **Integration (AC1, AC2):** `tests/roster/test_governance_extras_standalone_install.py`, run by the same named step, installs into a temporary repository with no `core` installed exits 0; an existing `agentbundle-layout.toml` gains an `[adr]` section and a missing one is not created. The layout conformance suites `tests/conformance/test_pack_layout_declared_section.py` and `tests/roster/test_layout_declaration_floor.py` pass.
- **Goal-based (AC8, AC9):** `agentbundle catalogue lint --root . --deep`, `agentbundle catalogue verify --root .`, `tools/lint-pack-dependency-declaration.py`, self-host with no drift, guide lints, and a search that finds no "requires core" claim for this pack.

## Acceptance Criteria

- [x] **AC1 — Installs without core.** `packs/governance-extras/pack.toml` has no `[[pack.dependencies.required]]` entry and names `core` only under `[[pack.dependencies.recommended]]`, and `agentbundle install` of `governance-extras` into a repository with no `core` installed exits 0.
- [x] **AC2 — Layout default seeds only an existing file, and is documented.** `pack.toml` declares `[pack.layout.repo]` with `section = "adr"` and `output_dir = "docs/adr"`, and `new-adr/references/agentbundle-layout.md` documents that pair. Installing into a repository whose `agentbundle-layout.toml` exists appends an `[adr]` section with that value; installing where the file is absent creates no such file.
- [x] **AC3 — Confinement check accepts only in-repository targets.** On success every mode exits 0 and prints exactly one line: the absolute, fully resolved path the caller must use verbatim, with every in-root prefix symlink replaced by its target. `confine-destination.py <repo-root> <relative-dir>` prints the directory, for an in-repository directory that exists or does not exist yet, including one reached through a symlink in the prefix that stays inside the root. With `--new-file <name>` it prints that resolved directory joined with the name. With `--read-file <name>` it prints the file path, for an existing regular, singly linked, non-symlink file of that name inside the directory, and `confine-destination.py <repo-root> --root-file <name>` prints the file path for such a file directly under the root. With `--read-file` or `--root-file`, a name that does not exist (and whose directory passes every rule) is *absent*: the check exits 3, prints nothing, and reads nothing. It exits 2 with no filesystem effect, and never with a traceback, for each of: an absolute path; a drive-letter path; a backslash; a control character; an empty, `.` or `..` segment; a path longer than 1000 characters; a path resolving to the repository root; a symlink in the existing prefix that resolves outside the root, is broken, or loops; a final directory component that is itself a symlink (refused, as the record-listing helper refuses it); an existing non-directory target; a root that is not an existing directory; any `OSError` during resolution; and, with `--new-file`, a name that is not a single segment ending `.md`, or a name that already exists in any form, including as a symlink; with `--read-file` or `--root-file`, a name that is not a single segment, or that exists but is a symlink, hard-linked, or not a regular file; and, in every mode, a final resolved path that contains a control or newline character, cannot be encoded as UTF-8, or is longer than 1000 characters — in which case nothing is printed to stdout.
- [x] **AC4 — One helper, two byte-identical copies.** The check lives in `_record_paths.py`, and the `new-adr` and `new-rfc` copies are byte-identical.
- [x] **AC5 — `new-adr` resolves its destination without core.** `new-adr/SKILL.md` step 1 states the six-step order and these rules: the repository root is the Git top-level discovered with Git relocation variables removed, and failing to find it is a zero-effect refusal; `agentbundle-layout.toml` `[adr] output_dir` is declared configuration, read by instruction, whose other content is data; a destination handed in by a calling workflow is an explicit destination; repeated examples are inference until the user confirms them, and one example is never a convention; an explicit destination that violates mandatory policy is refused, not an override; contradictory evidence fails closed and asks, including a declared `[adr] output_dir` that holds no ADR-shaped record while another searched location does — where the searched locations are exactly the declared folder, `docs/adr/`, `docs/decisions/`, `adr/`, `decisions/`, and an ADR location stated in agent guidance the host has already loaded, and an ADR-shaped record is a regular file whose name starts with four or more digits, a hyphen, and ends `.md`; `docs/adr/` is a fallback offered only with confirmation; no confirmation overrides a `confine-destination.py` refusal; and refusal, ambiguity, absence without confirmation, or an external locator has zero ordinal, index, directory, configuration or file effects. Step 1 contains no instruction to call core or to consume a `semantic-surface-resolution.v1` result.
- [x] **AC6 — `new-rfc` works without core.** Every `new-rfc/SKILL.md` and `assets/rfc.md` reference to a core-owned primitive or workflow — including `work-loop`, `work-intake`, `workspace-status`, `new-spec`, `adversarial-reviewer`, `security-reviewer`, and any hand-off to "core" or "its owning core workflow" — is conditional on core being installed, and each names its fallback: the template's own `light` / `standard` / `heavy` definitions for decision weight; listing follow-ons in the completion receipt for queue registration; a spec written in the repository's own spec format for a settled feature; and, for review, a fresh-context reviewer given only the RFC text and the same brief, or an inline adversarial and security pass recorded in the receipt as self-review when the host has no subagents.
- [x] **AC7 — Evals match.** No `new-adr` eval expects core-resolver use, a Wave 1 result, or a zero-write handoff because core is absent. At least one eval covers core absent with a confirmed in-repository destination producing the preview, and one covers an unsafe destination producing a zero-effect refusal. At least one `new-rfc` eval covers review without core installed.
- [x] **AC8 — No surface claims core is required or describes the old path.** `pack.toml` first-value metadata, `DESIGN.md`, `README.md`, `JOURNEY.md`, `docs/index.md`, `guides/governance-extras/**`, `web/src/content/journeys/governance-extras.md` (`prerequisitePacks`), `packs/core/docs/index.md`, and the `profiles/full-ceremony.toml` comments do not state that `governance-extras` requires `core`; none of the pack docs, journey pages or guides describes `new-adr` as consulting core for its destination or as stopping with a handoff when core is absent; and `guides/governance-extras/how-to/new-rfc.md` describes `work-loop`'s risk triggers and the `adversarial-reviewer` / `security-reviewer` agents as used when core is installed, with the AC6 fallbacks otherwise.
- [x] **AC9 — Gates and projections clean.** The pack version and `.claude-plugin/plugin.json` move to the next patch; catalogue lint, verify, the dependency-declaration lint, self-host (no drift) and the touched suites pass.
- [x] **AC10 — The write re-proves confinement and uses the proven path.** `new-adr/SKILL.md` step 8 runs `confine-destination.py` with `--new-file <NNNN-title.md>` immediately before creating any directory or file, and a refusal there has zero effects. Immediately before the write it also runs the directory form; the directory creation, the `index-records.py` argument and the index path use that printed line verbatim, and the file write and the file path in the preview and receipt use the `--new-file` printed line verbatim. Any change to the folder or title after the check re-runs it.
- [x] **AC11 — Core hand-offs are declared as optional integrations.** `pack.toml` has a `[[pack.integrations]]` entry with `pack = "core"` for decision-weight triggers, follow-on queue registration, and RFC review, each naming its consumer skill, its core provider, and a fallback that matches AC6.

- [x] **AC12 — Every read and write in destination resolution and the new-record write uses a proven path.** `new-adr/SKILL.md` requires that, in steps 1–8, each repository path it reads or writes — the root `agentbundle-layout.toml` (`--root-file`), each searched location, each record file it reads (including the step-7 `Areas` scan, via `--read-file`), the `next-ordinal.py` and `index-records.py` directory arguments, and the new file — first passes `confine-destination.py`, and is then used only as the line that check printed, verbatim. Only exit 3 with empty stdout counts as absent: an absent layout file is no step-2 evidence, and resolution continues without reading it. Any other non-zero exit, and any exit 0 whose stdout is not exactly one line, is treated as a refusal. A refused layout file, declared `output_dir` folder, guidance-named location, or step-3 search location stops resolution with zero effects and reports the refusal to the user; no lower-precedence candidate and no absence offer follow it. A refused individual record file is skipped and never read. The skill opens no agent-guidance file itself: it uses only guidance the host has already loaded, so a symlinked `CLAUDE.md` never stops resolution. A changed folder or name re-runs the check. The bundled `assets/adr.md` is read from the skill's own directory, not the repository, and is outside this criterion. Existing-record lifecycle and `Status` edits, `## Errata` appends, and infra-mode governance-index edits are unchanged by this spec and outside this criterion.

## Follow-ons

- eugenelim: an RFC on widening the pack into repository governance and renaming it — scope, name and layout for RFC records.

## Assumptions

none
