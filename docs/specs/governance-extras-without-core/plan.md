# Plan: Governance-extras without core

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** core's `packs/core/.apm/skills/work-intake/scripts/surface_resolver.py` `_resolve_repository_locator`, `_validate_existing_symlink_chain`, `_validate_repository_path` and `_requires_convention_confirmation` (the rules this pack reproduces, not imports); the pack's own `_record_paths.py` and its by-path loader in `next-ordinal.py`; `index-records.py`'s existing symlink refusal and create-and-replace index write; desk-research's in-skill layout resolution and its `references/agentbundle-layout.md` (the analogue); `[pack.layout.repo]` in `packs/architect/pack.toml`; construction path `packs/governance-extras/tests/skills/new-adr/test_next_ordinal.py`, `tests/roster/test_decision_record_destination_contract.py`, `tests/roster/test_index_records.py`, `tests/conformance/test_pack_layout_declared_section.py`.

> **Plan contract:** this is the implementation strategy. `Touches`, `Tests` and
> `Done when` are pinned at approval; `Design`, `Approach` and `Risks` are
> working material.

## Approach

Four tasks. The confinement helper comes first because the skill text calls it. The manifest and layout reference follow, then the two skills and their evals, then docs, version and projections. The pack reproduces core's confinement rules locally instead of importing them, because installed skills run standalone from their own projection.

## Constraints

- RFC-0096 § 4 and ADR-0120: one six-step order; no silent pack default; `[pack.layout.repo]` is an install-time seed that counts only once written into the adopter's file.
- ADR-0030 D8 and D9: layout reading is prompt-only; the installer appends a layout section only to an existing `agentbundle-layout.toml`.
- `packs/AGENTS.md`: bump `pack.toml` and `.claude-plugin/plugin.json` together, add a changelog fragment, update the eval harness, self-host after edits, cite no internal governance in shipped pack text, reconfigure stdout and stderr to UTF-8 in any `.apm/` script that prints.
- `tests/AGENTS.md`: a new roster file needs a named `build-check.yml` step above the bulk step, a `tools/lint-ci-parity.py` entry, and a `.workspace-prune-protected.toml` entry if it names this spec path.
- Standard library only.

## Construction tests

**Unit:** `tests/roster/test_confine_destination.py` loads `_record_paths.py` and `confine-destination.py` by path under unique names and drives every AC3 case over `tmp_path`.
**Contract:** `tests/roster/test_index_records.py` already pins byte identity (AC4). `tests/roster/test_decision_record_destination_contract.py` asserts the AC5, AC6, AC7, AC8, AC10, AC11 and AC12 phrases.
**Integration:** `tests/roster/test_governance_extras_standalone_install.py` installs the real pack into a temporary repository without core (AC1, AC2); the existing layout conformance suites cover the documented pair.

## Design (LLD)

### Interfaces & contracts

`_record_paths.confine_destination(root: Path, relative: str, new_file: str | None = None, read_file: str | None = None) -> str`, plus `confine_root_file(root: Path, name: str) -> str` returning the absolute resolved path of a file directly under the root. `confine_destination` returns the absolute, fully resolved path (the directory; or, with `new_file` or `read_file`, the file in it); both raise `EntryRefused` on refusal. Rules, in order: `relative` is a 1–1000 character string with no leading `/`, no drive prefix, no backslash, no control character, and no empty, `.` or `..` segment; `root.resolve(strict=True)` is a directory; every existing prefix component that is a symlink resolves with `strict=True` inside the root (broken and looping links raise and become refusals); the resolved candidate is inside the root and is not the root; an existing candidate is a directory; a final component that exists and is a symlink is refused; with `new_file`, the name passes the same segment rules, is one segment ending `.md`, and `os.lstat(candidate / name)` raises `FileNotFoundError`; with `read_file`, the name is one segment and `os.lstat` shows a regular, non-symlink file with `st_nlink == 1`; a `FileNotFoundError` there raises `EntryAbsent` (CLI exit 3, nothing printed). Before returning, the final resolved path must contain no control or newline character, encode as UTF-8, and be at most 1000 characters. Every `OSError`, `RuntimeError`, `ValueError` and `UnicodeError` becomes `EntryRefused`, and the CLI prints nothing to stdout on refusal.

`confine-destination.py <repo-root> <relative-dir> [--new-file <name> | --read-file <name>]`, or `confine-destination.py <repo-root> --root-file <name>`, prints that one absolute path and exits 0; prints `refused: <reason>` to stderr and exits 2; or, for an absent `--read-file`/`--root-file` name, prints nothing and exits 3 without opening the file. Callers use the printed line verbatim and never recompose it. It only `stat`s and resolves, and writes nothing.

### Behavior & rules

`new-adr` step 1:

1. Find the root: `git rev-parse --show-toplevel` with `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR` and `GIT_INDEX_FILE` removed. No root is a zero-effect refusal.
2. Before reading any evidence, confine it and then use only the proven absolute path: `confine-destination.py <root> --root-file agentbundle-layout.toml` for the layout file, `confine-destination.py <root> <dir>` for each searched location (the declared folder, `docs/adr/`, `docs/decisions/`, `adr/`, `decisions/`, and a guidance-named location), and `--read-file` for any record file read. Only exit 3 with empty stdout is absent, meaning no step-2 evidence; any other non-zero exit, or an exit 0 without exactly one stdout line, is a refusal. A refused layout file, declared folder, guidance-named location or step-3 search location stops resolution with zero effects and reports it; a refused record file is skipped. Guidance is taken only from what the host has already loaded; the skill opens no guidance file. Then collect bounded candidates by precedence: an explicit destination in the request or handed in by a calling workflow; `[adr] output_dir` from the root `agentbundle-layout.toml` and an ADR location stated in guidance the host has already loaded; an existing folder holding ADR-shaped records (inference until confirmed); a declared external destination.
3. Take the highest-precedence candidate. Mandatory-policy conflict refuses an explicit destination. Contradicting evidence fails closed and asks, including a declared `[adr] output_dir` that holds no ADRs while any ADR-shaped record exists in another folder. An external locator stays external: render a handoff and stop.
4. With no candidate, offer `docs/adr/` or another folder and wait for confirmation.
5. Run `confine-destination.py`. Refusal stops with zero effects, and no later confirmation overrides it.
6. Surface the destination, then continue to step 2; `next-ordinal.py` and the step-7 sibling scan take the printed directory line verbatim.

Step 8 runs `confine-destination.py <root> <dir> --new-file <NNNN-title.md>` immediately before creating the directory or file, together with the directory form; the directory creation and `index-records.py` take the directory line, and the file write and file paths in the preview and receipt take the `--new-file` line, each verbatim. A changed folder or title re-runs the check.

`new-rfc` review without core: dispatch a fresh-context reviewer with only the RFC text and the same adversarial (and, when warranted, security) brief; if the host has no subagents, run the pass inline and record it in the receipt as self-review.

## Tasks

### T1: Confinement helper

- **Depends on:** none
- **Touches:** `packs/governance-extras/.apm/skills/new-adr/scripts/_record_paths.py`, `packs/governance-extras/.apm/skills/new-rfc/scripts/_record_paths.py`, `packs/governance-extras/.apm/skills/new-adr/scripts/confine-destination.py` (new), `tests/roster/test_confine_destination.py` (new); `.github/workflows/build-check.yml` (a named step "pytest governance-extras standalone (roster-owned)" above the bulk step, running this file and T2's install test); `tools/lint-ci-parity.py` (`STEP_DISPOSITION` entry `LOCAL("test-after-build-check")`); `tools/test_build_gate_chain.py` and `tools/lint-pack-test-boundary.py` only if their lists must name the new files.
- **Tests:** TDD. One test per AC3 accept, refuse and absent case, including a test that fails if a missing `--root-file` or `--read-file` name exits 2; a refusal leaves the tree's listing unchanged; a link swapped in after a first passing check is refused on the second call; a junction case skips on platforms that cannot make one.
- **Done when:** `pytest tests/roster/test_confine_destination.py tests/roster/test_index_records.py -q` and `tools/lint-ci-parity.py` pass.

### T2: Manifest and layout reference

- **Depends on:** T1
- **Touches:** `packs/governance-extras/pack.toml` (core under `[[pack.dependencies.recommended]]`; `[pack.layout.repo]`; `[[pack.integrations]]` entries for core; first-value prerequisites); `packs/governance-extras/.apm/skills/new-adr/references/agentbundle-layout.md` (new); `tests/roster/test_shipped_pack_manifests.py` (`CORE_DEP_PACKS` drops governance-extras); `packs/governance-extras/tests/skills/new-rfc/test_project_knowledge_handoff.py` (its required-dependency lookup); `tests/roster/test_governance_extras_standalone_install.py` (new, run by T1's named step) and, if it names this spec path, a `.workspace-prune-protected.toml` entry.
- **Tests:** install without core exits 0; layout append into an existing file; no file created when absent; integration entries carry consumer, provider and fallback.
- **Done when:** the touched suites, `tests/conformance/test_pack_layout_declared_section.py`, `tests/roster/test_layout_declaration_floor.py`, `tools/lint-pack-dependency-declaration.py` and `agentbundle catalogue lint --root . --deep` pass.

### T3: Skills and evals

- **Depends on:** T1, T2
- **Touches:** `new-adr/SKILL.md` (steps 1 and 8); `new-adr/evals/evals.json` (ids 5, 10, 11 and 13 rewritten off the core resolver; new unsafe-destination case); `new-rfc/SKILL.md`; `new-rfc/assets/rfc.md`; `new-rfc/evals/evals.json` (a review-without-core case); `packs/governance-extras/tests/skills/new-rfc/test_precreate_checkpoint.py` and any other pack test pinning rewritten text; generated projections (`agentbundle catalogue self-host --root . --write`, after a commit, so the projection byte-equality assertions hold); `tests/roster/test_decision_record_destination_contract.py`; `tests/roster/test_architecture_decision_surface_portability.py` (its `"semantic-surface-resolution.v1" in adr` assertion becomes a never-claim assertion).
- **Tests:** text-contract assertions for AC5, AC6, AC7, AC10, AC11, AC12 (AC8's assertions belong to T4).
- **Done when:** self-host has regenerated the projections, and the touched roster and pack suites pass.

### T4: Docs, version, projections

- **Depends on:** T3
- **Touches:** `tests/roster/test_decision_record_destination_contract.py` (AC8 assertions), `guides/governance-extras/how-to/new-rfc.md`, `docs/architecture/work-intake-and-artifact-routing.md` (role-consumption passage), `packs/governance-extras/{DESIGN.md,README.md,JOURNEY.md,docs/index.md}`, `guides/governance-extras/tutorials/governance-extras-first-session.md`, `web/src/content/journeys/governance-extras.md`, `packs/core/docs/index.md`, `profiles/full-ceremony.toml` comments, `packs/governance-extras/.claude-plugin/plugin.json`, a changelog fragment, the amended spec's `Amended in part by:` header, generated projections.
- **Tests:** text-contract assertions for AC8; goal-based for AC9.
- **Done when:** catalogue lint and verify pass, self-host shows no drift, guide lints pass, and a search finds no claim that the pack requires core.

## Rollout

- **Delivery:** pack release. Existing installs keep working; core stays an optional companion.
- **Migration effect:** on upgrade, an adopter whose existing `agentbundle-layout.toml` lacks `[adr]` gains `[adr] output_dir = "docs/adr"`. If an ADR-shaped record lives in another searched location while `docs/adr` holds none, step 1 sees contradictory evidence and asks instead of switching folders; they can edit or delete the section.
- **Rollback:** revert the PR; the dependency and core resolver call return.

## Risks

- Reproducing confinement rules invites drift from core's resolver. Mitigation: the unit tests cover every refusal class core refuses, listed in AC3.
- The step-8 re-check narrows but cannot remove the window between the check and the host's write; the new-file check and the preview gate bound it.

## Work-loop decision record

- **Files expected:** as listed in T1–T4.
- **Tests that demonstrate done:** the AC3 unit matrix, the existing copy-identity test, the AC1/AC2 install test, the layout conformance suites, the AC5–AC8, AC10, AC11, AC12 text-contract tests.
- **Not changing:** synthetic governance-extras fixtures in `packages/agentbundle/tests/_support.py` and `unit/test_dependencies_batch.py` (they model a generic required dependency and read no real manifest); core's resolver; `new-rfc`'s destination resolution; `navigate-decisions`; the pack name or scope.
- **Declined: keep calling core's resolver when core is present.** Rung 1 (not needed): two resolution paths for one role would make the result depend on what else is installed, and the in-pack path meets the same order and confinement.
- **Declined: an ADR.** The owner asked for none; the spec's `Amends:` line records the change.
- **Expected review shape:** DEEP, below 2,000 reviewable lines; one PR.

## Resolve-vs-surface disposition

Opened at PLAN; closed at DECIDE.

| Finding | Source | Disposition |
| --- | --- | --- |
| Step-8 write not re-confined | security 1 / adversarial 10 | repair-the-artifact: AC10, `--new-file`, Always-do |
| Repository root unspecified | security 4 / adversarial 10 | repair-the-artifact: Always-do, AC5, LLD step 1 |
| Broken/looping links, OS errors | security 5 / adversarial 9 | repair-the-artifact: AC3 |
| Layout reference missing | adversarial 1 | repair-the-artifact: AC2, T2 |
| Amends incomplete | adversarial 2 | repair-the-artifact: `Amends:` line |
| § 4 safeguards unpinned | adversarial 3 | repair-the-artifact: AC5, LLD step 1 |
| `new-rfc` reviewer dispatch | adversarial 4 | repair-the-artifact: AC6, AC11 |
| Eval ids | adversarial 5 | repair-the-artifact: AC7, T3 |
| `Depends on:` | adversarial 6 | repair-the-artifact |
| Handed-in destination | adversarial 7 | repair-the-artifact: AC5 |
| Layout seed vs convention | adversarial 8 | repair-the-artifact: AC5 contradiction rule, Rollout |
| Integrations unpinned | adversarial 12 | repair-the-artifact: AC11 |
| Write not bound to proven path | security r2-1 | repair-the-artifact: AC10, LLD |
| Amends still incomplete | adversarial r2-1 | repair-the-artifact: `Amends:` line |
| Evidence read before confinement | adversarial r2-2 | repair-the-artifact: Always-do, AC3 `--read-file`, AC5, LLD |
| T3 needs projections | adversarial r2-3 | repair-the-artifact: T3 regenerates |
| `new-spec` and core hand-off | adversarial r2-4 | repair-the-artifact: AC6, T3 |
| Architecture doc stale | adversarial r2-5 | repair-the-artifact: Durable Outputs, T4 |
| Scope of "no core" | adversarial r2-6 | repair-the-artifact: AC5 |
| Final-component symlink | adversarial r2-7 | repair-the-artifact: AC3 refuses |
| Rollout vs contradiction rule | adversarial r2-8 | repair-the-artifact: AC5 widened, Rollout |
| Record reads unconfined | security r3-1 | repair-the-artifact: AC12 |
| Reads not bound to proven path | security r3-2 / adversarial r3-5 | repair-the-artifact: AC12, LLD |
| AC3 tests ungated | adversarial r3-1 | repair-the-artifact: roster file + named step, T1 |
| AC10 dir vs file path | adversarial r3-2 | repair-the-artifact: AC10, LLD |
| Stale resolver prose | adversarial r3-3 | repair-the-artifact: AC8, Durable Outputs |
| Unbounded search scope | adversarial r3-4 | repair-the-artifact: AC5 named locations, Rollout |
| Sole-source Assumption | adversarial r3-6 | repair-the-artifact: `Amends:` line |
| AC12 overclaims coverage | security r4-1 / adversarial r4-3 | narrow-the-claim: AC12 scoped to steps 1–8; guidance reads in; template, lifecycle, errata, infra out |
| AC8 assertions unowned | adversarial r4-1 | repair-the-artifact: T4 owns them |
| `new-rfc` how-to guide | adversarial r4-5 | repair-the-artifact: AC8 clause, T4 |
| Decision-record test list | adversarial r4-6 | repair-the-artifact |
| LLD omits guidance reads | security r5-1 (Nit) | deferred: AC12 governs; the T3 text-contract test enforces it |
| Printed output undefined | adversarial r5-1 | repair-the-artifact: AC3 one absolute resolved line per mode; AC10, AC12, LLD use it verbatim |
| Printed path unchecked | security r6-1 | repair-the-artifact: AC3 output rule, LLD |
| Skip vs stop on refused source | adversarial r6-1 | repair-the-artifact: AC12 split, LLD step 2 |
| Absent file treated as refusal | adversarial r7-1 | repair-the-artifact: AC3 exit 3 absent, AC12, LLD |
| Symlinked `CLAUDE.md` stops resolution | adversarial r7-2 | repair-the-artifact: skill opens no guidance file; uses host-loaded guidance |
| Refused search location | adversarial r7-3 | repair-the-artifact: AC12 stop-and-report, LLD |
| Absent outcome untested | adversarial r8-1 | repair-the-artifact: Testing Strategy, T1 Tests, LLD CLI contract |
| Other exit codes unhandled | security r8-1 (Nit) | repair-the-artifact: AC12, LLD step 2 |

## Changelog

- 2026-10-23: spec approved by eugenelim
- 2026-10-23: plan approved by eugenelim
