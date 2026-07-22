# Plan: m5-tracker-guides

## Tasks

### Task 1. Write `choose-a-tracker-integration.md` (how-to)
Verification: goal-based — file exists at `docs/guides/_shared/how-to/choose-a-tracker-integration.md`
and grep confirms all five intake paths are named.
Approach: Author the decision guide with a decision table at the top, per-tracker
sections with prerequisites and cross-links, and a brief note on single-issue
inputs (→ `new-spec`).

### Task 2. Write `tracker-vocabulary.md` (reference)
Verification: goal-based — file exists at `docs/guides/_shared/reference/tracker-vocabulary.md`
and grep confirms both the vocabulary table and the skill routing table are present.
Approach: Author the reference with the cross-tracker vocabulary table (adapting
`tracker-projection.md` for an adopter audience with a GitHub column added), the
skill routing table, and a brief note on the impedance model.

### Task 3. Update READMEs and changelog
Verification: goal-based — grep confirms new file names appear in `_shared/how-to/README.md`,
`_shared/reference/README.md`, `docs/guides/README.md`, and `docs/product/changelog.md`.
Approach: Add one-line entries to each README and a changelog entry under `[Unreleased]`.
