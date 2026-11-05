# Brief: remaining argv-to-path sites use the repository validator

- **Slug:** `argv-path-boundary-sweep-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Draft
- **Parent intent:** intent:argv-path-boundary-validator-sweep

## Outcome

Every command-line value that becomes a filesystem path in a shipped script either goes through the repository boundary validator or is a recorded exemption. A semgrep rule keeps each converted area from regressing.

## Scope / Non-goals

**In scope.** Converting the unvalidated sites that `tools/semgrep/argv-path-boundary.yml` finds in `packs/` and `packages/agentbundle`, and widening that rule's `paths.include` ratchet one area at a time.

**Out of scope.**

- Binding checked paths to file objects. That race class is withdrawn as accepted risk in `checked-then-reopened-path-confinement`.
- `tools/` scripts and test files. They are not shipped surface.
- A taint-style rule. The rule's header records why OSS Semgrep cannot do it.

## Current-state evidence

Measured 2026-11-05 by running the rule with its `paths` ratchet removed, over `tools packs packages`.

- 283 non-test sites match. In `packs/` and `packages/` that is 161 sites: `packages/agentbundle` 51, `packs/core` 50, `packs/converters` 23, `packs/repo-governance` 17, `packs/atlassian` 9, `packs/architect` 6, `packs/catalogue-curation` 3, plus `packages/jsonl-otlp-exporter` 1 and `packs/code-intelligence` 1. The first seven groups sum to 159; the other two sites make 161.
- A name-based split found 110 sites in files that already use a confinement helper and 51 sites in 24 files with none. Slice 1 starts from those 24 files.
- The intent's [Current truth](../intents/argv-path-boundary-validator-sweep.md) section explains why its older estimate no longer applies.
- The rule only matches `Path(args.x)` shapes. It misses an intermediate binding and argv passed to a helper, so the count is a lower bound.
- The rule's header records that most matches are operator-supplied scan roots. A site is converted when it uses the validator, not because an attacker controls it.

## Constraints / Appetite

- Non-waivable: no behaviour change for valid input. A converted script refuses only paths outside its declared root.
- Landing in `packs/**` carries a pack version bump per `packs/AGENTS.md`.
- Exemptions: a site classified `already-bounded` or `operator-root` carries a `nosemgrep` comment in the form `tools/lint-nosemgrep-form.py` accepts, with the reason; or its file stays out of the rule's `paths.include`. Slice 1 picks one and records it. "Reports 0" in later slices means zero unexempted matches.
- Slice 5 edits `packages/agentbundle/`, so its commit needs an `Engine-Change-RFC:` trailer, conventionally `n/a - <justification>` when no RFC governs it (`tools/AGENTS.md`). Slices 4 and 5 edit packages (`packages/jsonl-otlp-exporter`, `packages/agentbundle`), so each also bumps that package's version in both `version.py` and `pyproject.toml` (`packages/AGENTS.md`).
- Slices 2 to 4 edit packs, so each updates that pack's eval harness (`packs/AGENTS.md`).
- `packages/agentbundle` ships as a published CLI, so slice 5 is in scope and not optional.
- Appetite: five slices; slice 3 is the large one.

## Assumptions / Risks

- **[Risk]** The frozen slice-1 list goes stale as code changes. Each later slice re-runs the rule for its own area before converting and updates the list.
- **[Risk]** Many matches are scan roots where a confinement root has no natural value. De-risk in slice 1 by classifying every site as `convert`, `already-bounded`, or `operator-root` and recording the list.
- **[Risk]** The validator rejects a currently working input. Each slice adds a refusal test and a valid-input test per script.

## Governance references

- `docs/specs/pack-script-root-boundary-validation/spec.md` owns the validator and the first three conversions.

## Proposed cut

Slice 3 is the largest: 76 sites across four packs, each needing a version bump and an eval-harness update, so it may split per pack at spec time. Each slice is independently shippable and verified by the rule plus targeted tests.

| Slice | Gating | Proof |
| --- | --- | --- |
| 1. Classify all 161 sites, starting from the 24 helper-free files, and freeze the list in a note beside the rule | agent-only | The rule run reproduces the recorded list |
| 2. `packs/converters` (23) | agent-only, after 1 | Rule include widened to converters scripts reports 0 |
| 3. all `packs/core` sites (50, including workspace-status and receive-brief), `packs/repo-governance`, `packs/architect`, `packs/catalogue-curation` (76) | agent-only, after 1 | Same, per pack |
| 4. `packs/atlassian` (9), `packs/code-intelligence` (1) and `packages/jsonl-otlp-exporter` (1) | agent-only, after 1 | Same |
| 5. `packages/agentbundle` (51) | agent-only, after 1 | Same |

Slices 2 to 5 do not depend on each other.

## Ready gaps (Draft only)

None open.

## Spec map

| Spec | Status |
| --- | --- |

## Source

- Mode: repo-origin
- Locator: docs/product/intents/argv-path-boundary-validator-sweep.md
