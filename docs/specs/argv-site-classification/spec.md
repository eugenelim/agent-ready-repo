# Spec: every unvalidated argv-to-path site is classified and listed

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** none — authored after approval
- **Constrained by:** ADR-0017
- **Brief:** brief:argv-path-boundary-sweep-delivery
- **Discovery:** intent:argv-path-boundary-validator-sweep
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round.

## Outcome

Maintainers converting argv-to-path sites get one frozen, reproducible list of every site the argv rule matches, each marked as needing conversion, already bounded, or an operator-supplied root. Later conversion slices start from that list instead of re-deriving it.

## What Changes

- A classification note lists every match of `tools/semgrep/argv-path-boundary.yml`, run without its `paths.include` ratchet, over `packs/` and `packages/` excluding tests and fixtures — `docs/specs/argv-site-classification/notes/site-classification.md`.
- The note records the exemption mechanism later slices use for sites that need no conversion — the same note.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — the exemption mechanism and per-site verdicts are decisions later slices rely on | `docs/specs/argv-site-classification/notes/site-classification.md` | eugenelim | The note itself, with the reproduction command | `close-work` confirms the recorded command reproduces the recorded list |
| Current product truth | Applicable — the brief carries delivery state | `docs/product/briefs/argv-path-boundary-sweep-delivery.md` Spec map | `lint-brief-coverage` | Roll-up resolves this spec through its `Brief:` link | No status hand-written into the brief |
| User promise, operations, release history | Not applicable — documentation only; no shipped behavior changes | — | — | — | — |

## Agent Rules

### Always do

- Run the rule with its `paths.include` removed from a temporary copy outside the repository tree, and record the exact command and tool version in the note.
- Classify a site `already-bounded` only when the same function or its caller passes the value through a confinement helper before use, and cite that helper at the site.
- Name each site by file, line and the argv attribute that becomes a path.

### Ask first

- Any edit under `packs/`, `packages/` or `tools/`. This slice changes none.
- Marking a site `operator-root` when the script has a natural confinement root.

### Never do

- Never edit `tools/semgrep/argv-path-boundary.yml` in this slice.
- Never leave a matched site unclassified or omit one because it sits in a test-like path without saying so.

## Testing Strategy

- **Goal-based check:** re-running the recorded command reproduces the recorded site list byte for byte. The reproduction is the oracle for the list's completeness.
- **Goal-based check:** a script over the note confirms every listed site carries exactly one of the three verdicts.

## Acceptance Criteria

- [ ] The note lists every site the unscoped rule matches in `packs/` and `packages/` outside tests and fixtures, and its total equals the count the recorded command prints.
- [ ] Each listed site carries exactly one verdict: `convert`, `already-bounded` or `operator-root`.
- [ ] Each `already-bounded` site cites the confinement helper that bounds it, by file and line.
- [ ] The note names one exemption mechanism for non-converted sites: a `nosemgrep` comment in the form `tools/lint-nosemgrep-form.py` accepts, or exclusion of the file from the rule's `paths.include`.
- [ ] The note records the command, the Semgrep version and the run date, and re-running the command at the same commit reproduces the list.
- [ ] No file under `packs/`, `packages/`, `tools/`, `tests/` or `.github/` changes in this slice.

## Follow-ons

- eugenelim: `docs/product/briefs/argv-path-boundary-sweep-delivery.md` slices 2 to 5 — convert the `convert` sites per area, widening the rule's `paths.include` as each area reaches zero.

## Assumptions

- Defaulted: Product: exemption mechanism — default: a `nosemgrep` comment with a reason at the site, because it is visible where the code is and its form is already linted; if wrong: the note names the `paths.include` exclusion instead and later slices change accordingly (settled by: eugenelim).
- Technical: the name-based helper heuristic (110 of 161 sites in files that already confine paths) is not proof that a given site is bounded — each `already-bounded` verdict needs the per-site citation above (settled by: the classification itself).
