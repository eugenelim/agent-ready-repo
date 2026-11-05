# Argv path boundary validator sweep

- **Slug:** `argv-path-boundary-validator-sweep`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [spec/pack-script-root-boundary-validation](../../specs/pack-script-root-boundary-validation/spec.md)

## Outcome

No shipped pack or `packages/agentbundle` script lets an unvalidated command-line value choose a filesystem path outside the root it declares, except sites recorded as exempt.

## Opportunity

`docs/specs/pack-script-root-boundary-validation/spec.md` (Out of scope) identifies an estimated 68 remaining argv-to-path sites across `packs/` and `packages/agentbundle`.

## What this absorbs

### pack-argv-path-boundary-sweep

Apply the argv-to-path boundary validator to the remaining ~68 sites across the converters, atlassian, core, repo-governance, architect and catalogue-curation packs, and `packages/agentbundle`.

## Assumptions

- The ~68-site count is the current scoped estimate recorded by `spec/pack-script-root-boundary-validation`.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

## Current truth

Measured 2026-11-05 by running `tools/semgrep/argv-path-boundary.yml` with its path ratchet removed: 159 unvalidated `Path(args.x)` sites remain in shipped code (`packages/agentbundle` 51, `packs/core` 50, `packs/converters` 23, `packs/repo-governance` 17, `packs/atlassian` 9, `packs/architect` 6, `packs/catalogue-curation` 3). Two more sites sit outside those groups (`packages/jsonl-otlp-exporter` 1, `packs/code-intelligence` 1), so the full count is 161, which the De-risk result below uses. The "about 68" figure is out of date. The rule misses intermediate bindings, so 159 is a lower bound, and many sites are operator-supplied scan roots.

## Readiness

- **Route:** brief. See [argv-path-boundary-sweep-delivery](../briefs/argv-path-boundary-sweep-delivery.md).
- **First slice:** classify every site as convert, already-bounded or operator-root, and freeze the list beside the rule.
- **Agent-only proof:** re-running the rule reproduces the recorded list; each later slice widens the rule's `paths.include` and reports zero for its area.
- **Manual dependency:** none.

## Non-goals

- Binding checked paths to file objects; that race class is withdrawn in `checked-then-reopened-path-confinement`.
- `tools/` scripts and test files, which are not shipped surface.
- A taint-style rule; OSS Semgrep cannot express it, per the rule's own header.

## Riskiest assumption

**Riskiest assumption:** the rule's match count reflects real boundary gaps. Many matches are operator-supplied scan roots with no natural confinement root. Tested agent-only in slice 1: classify every match as convert, already-bounded or operator-root, and record the list; the count of `convert` sites then sizes the rest.

## De-risk result

2026-11-05. Re-ran the unscoped argv rule and split the matches by whether the file already uses a confinement helper (`_validated_root`, `file_safety`, `relative_to`, and similar). Result: 161 non-test sites in `packs/` and `packages/` across 91 files; 110 sites sit in files that already confine paths somewhere, and 51 sites in 24 files have no confinement helper. Slice 1 starts from those 24 helper-free files. The count is therefore not a count of gaps: at most 51 sites are clearly unconfined, and the other 110 need the slice-1 classification to separate already-bounded from unconfined. This is a name-based heuristic, not proof. Verdict: partly holds; not stamped De-risked. Readiness is unchanged except that slice 1 now starts from the 24 helper-free files.
