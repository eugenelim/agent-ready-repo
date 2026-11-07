# The desk-research guide maps a brief onto RFC sections that no longer exist

- **Status:** Open
- **Kind:** defect

## Summary

`guides/desk-research/how-to/run-a-research-project-into-an-rfc.md` maps a research brief onto RFC sections that the six-section template removed. Owner: `eugenelim`.

## Observed

- Section 3 says the brief's bottom line seeds "`## Proposal` / `The ask`" and its findings go in "*Evidence & prior art*". It also maps known unknowns to "*Open questions*".
- The current template has six sections: Summary, Motivation, Proposal, Costs and what could go wrong, Alternatives, How we will know it works. `Open questions` and `Evidence` remain as optional sections. It has no `The ask` or `Evidence & prior art` section.
- Found with one bounded search of `guides/` for desk-research and RFC section names; other desk-research guides name no RFC section.

## Intended

- The mapping names the six current sections: bottom line to Summary and Proposal, findings to Evidence (optional), known unknowns to Open questions (optional).
- Owner `eugenelim` checks the rest of the how-to for the same stale names.
