# Spec: catalogue verify classification

- **Status:** Shipped
- **Owner:** maintainers
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0002, RFC-0013, `docs/specs/credbroker-user-scope/spec.md`
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Repository maintainers can run `agentbundle catalogue verify --root .` and see
no `unclassified` notices for the repository's current tracked inventory. Each
path is accounted for by its existing self-host ownership class: normal and
special-rail generated files are Projected; repository-owned source and living
documents are Excluded from self-host projection. A genuinely unknown future
path still surfaces as an informational notice, and projected `.agentbundle/`
drift still fails verification.

## Boundaries

### Always do

- Derive special-rail Projected membership from the same projection enumerators
  that drive writes and drift checks.
- Classify repository-owned trees by ownership boundary, with exact root-file
  entries where no directory boundary exists.
- Keep unclassified notices informational and preserve the warning emitted when
  Git enumeration is unavailable.

### Ask first

- Changing an existing path between Source, Projected, Manual, and Excluded.
- Making unclassified notices fail verification.
- Extending the work to unrelated defects in `catalogue-verifier-correctness`.

### Never do

- Blanket-exclude `.agentbundle/**`; its committed `bin/` and `lib/` files are
  generated and drift-gated.
- Maintain a second hard-coded list of special projected filenames.
- Add a dependency, top-level directory, or new public CLI option.

## Testing Strategy

- **TDD, unit:** exclusion matching accounts for every newly recognized
  repository-owned boundary while a synthetic unknown path remains
  unclassified.
- **TDD, integration:** self-host dry-run recognizes special-rail outputs as
  Projected and fails when one of those outputs drifts; step 15 maps that
  failure to `CAT-V-015`.
- **TDD, security:** Git filenames are enumerated losslessly; unknown symlinks
  remain visible; and special projections preserve file type and POSIX mode
  without following target symlinks.
- **Goal-based, end to end:** `agentbundle catalogue verify --root .` exits zero
  with no `unclassified` lines for this repository.
- **Goal-based:** the AgentBundle package tests and repository build gate pass.

## Acceptance Criteria

- [x] **AC1.** The current Git-visible repository inventory produces zero
  `[info] unclassified:` notices from `catalogue verify`.
- [x] **AC2.** A Git-visible path, including a symlink, outside every Projected
  and Excluded ownership boundary still emits one informational unclassified
  notice without changing a clean self-host exit code.
- [x] **AC3.** `.agentbundle/bin/*.py` and
  `.agentbundle/lib/credbroker/**/*.py` targets are derived as Projected from
  their projection enumerators, not copied into `EXCLUDED_PATTERNS`.
- [x] **AC4.** A modified, missing, or orphaned special-rail projection makes
  self-host dry-run fail with a drift diagnostic, and catalogue verification
  maps that failure to `CAT-V-015`.
- [x] **AC5.** Special `.agentbundle/bin/*.py` and
  `.agentbundle/lib/credbroker/**/*.py` drift checks use `lstat`, never follow a
  projected target symlink, and reject a regular-file/symlink type mismatch.
  On POSIX, executable targets enforce `0o755` and user-lib targets match their
  source mode. Target-root ancestors are checked without following links, and
  every nested parent component is checked as well. `--write` repairs rejected
  target, root, and nested-parent links with held-directory atomic replacement,
  without modifying their referents even if a leaf is swapped concurrently.
- [x] **AC6.** Git-visible filenames are consumed losslessly from NUL-delimited
  `git ls-files` output. A path containing whitespace or a newline is classified
  as the filename Git returned, not a stripped or C-quoted surrogate. Diagnostic
  rendering is reversible and one-line escaped so control bytes cannot forge
  terminal or CI output.
- [x] **AC7.** When Git enumeration is unavailable or exits non-zero, self-host
  emits the existing warning and does not present silence as evidence of a
  fully classified inventory; the warning remains non-failing.
- [x] **AC8.** An append-only RFC-0002 amendment, the living self-host spec, and
  the conventions summary
  describe the special `.agentbundle/` projection rails without changing their
  previously approved semantics.
- [x] **AC9.** AgentBundle and core pack versions plus their changelogs identify
  the classification and drift-check correction. The AgentBundle PyPI landing
  page documents the complete read-only verifier, the self-host-enabled
  catalogue boundary for informational unknown-path behavior and special-rail
  drift failure, and the separate write command.
- [x] **AC10.** Targeted classification/self-host tests, the complete AgentBundle
  package suite, and `SKIP_SAST=1 make build-check` pass.

## Assumptions

- Technical: `.agentbundle/bin/**` and `.agentbundle/lib/credbroker/**` are
  drift-gated projections (source: RFC-0013; `adapter_root_bins.py`;
  `user_libs.py`).
- Technical: ownership classification is implemented by self-host projection
  membership plus `EXCLUDED_PATTERNS`, not `workspace.toml` (source: RFC-0002;
  `self_host.py`).
- Product: all current Git-visible files should be classified while unknown
  future paths remain visible (source: user confirmation 2026-08-09).
- Process: this focused child fix leaves the broader 13-defect
  `catalogue-verifier-correctness` release queued (source: user confirmation
  2026-08-09).
- Process: base-freshness verification is skipped for this run (source: user
  confirmation 2026-08-09).
