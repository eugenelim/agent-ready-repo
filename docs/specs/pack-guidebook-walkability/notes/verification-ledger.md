# Verification ledger

Execution evidence for the build run beginning 2026-09-11. Recorded here rather
than in the spec, because the spec states outcomes and this records what was
observed.

## T1 — the contract in `guides/AGENTS.md`

**Destination.** `guides/AGENTS.md`, 36 lines before and 108 after. Precedent
for a substantive scoped file is 66 to 80 lines (`packs/AGENTS.md`,
`web/AGENTS.md`, `docs-site/AGENTS.md`), with root `AGENTS.md` at 120.

**Why not `docs/CONVENTIONS.md`:** it is byte-identical to
`packs/core/seeds/docs/CONVENTIONS.md` and listed as a self-hosting projection
at `packs/AGENTS.local.md:12`. `AGENT_RULES.md` and root `AGENTS.md` are seeded
for the same reason. `guides/AGENTS.md` is not seeded, and root `AGENTS.md`
§ Rule lookups already obliges an agent to read every scoped `AGENTS.md` on the
path to the file it is changing — so the contract is read by construction.

**Gates.** `git diff -- packs/ docs/CONVENTIONS.md AGENT_RULES.md AGENTS.md` is
empty, so no seeded surface was touched.

| Gate | Result |
| --- | --- |
| `python3 tools/validate_guides.py` | 0 |
| `python3 tools/lint-guide-titles.py` | 0 |
| `python3 tools/check-guide-index.py` | 0 |
| `python3 -m pytest tools/test_lint_guidebook_steps.py -q` | 5 passed, 0.18s |

### Mutation proofs — AC-0001

Each mutation was applied to `guides/AGENTS.md`, the suite run, and the mutation
restored **by editing**; every restore was confirmed byte-identical with `diff`.

| Mutation | Observed |
| --- | --- |
| Remove the whole contract section | **Killed.** 5 of 5 failed |
| Keep the identifiers, delete the normative statement | **Killed.** Only the binding case failed — 1 failed, 4 passed |
| Keep the statement, delete the obligation table rows | **Killed.** Only the identifier case failed |
| Add a machine-owned obligation id to the judgement-kinds closed set | **Killed** — see the two defects below |
| Delete the judgement-kinds closed set | **Killed.** Only that case failed |
| Delete the prohibited-vocabulary section | **Killed.** Only that case failed |

### Two guards that could not fail, found by mutation

Both were in the first draft of the judgement-kinds parser, and both were found
because the mutation survived rather than by reading the code.

1. **The parser could not see the shape it existed to detect.** The judgement
   kinds were matched with `` `([a-z][a-z-]+)` ``, which cannot match an
   underscore — and **every** machine-owned obligation identifier contains one.
   So adding `artifact_outline` to the closed set was invisible and the mutation
   passed. Widened to `[a-z_-]`.
2. **Widening it then produced a false positive.** The section's prose names
   `judgement_check`, which is itself an obligation identifier, so a
   whole-section parse flagged an overlap that was not there and the green
   baseline failed. **The contract's shape was the defect, not the parser:** the
   closed set is now stated as a list, and the parser reads list items only.

The second is the more useful finding. A contract meant to be read by a tool
has to be written to be parsed unambiguously, and prose that mentions an
identifier while describing it is indistinguishable from prose that declares it.

## Divergence between the spec and the implementation, resolved by amendment

The spec's Testing Strategy said AC-0001's observation is that "the enumerated
obligation identifiers match the spec's table, compared rather than read".
**That is not implementable:** the spec's obligation table is numbered `1`…`12`
and carries no identifiers, so there is nothing to compare against. Discovered
while writing the test, under the owner's standing authority to adapt on
findings.

AC-0001's oracle is therefore **structural**: the section exists, carries a
normative statement that binds every step, enumerates obligations by identifier
with no duplicate, declares its judgement kinds with no overlap against the
obligation identifiers, and declares its prohibited vocabulary. Each part fails
independently, which the mutation table above demonstrates.

The obligation set's agreement with the **lint** is AC-0003's, and that is where
the real drift risk sits — the contract and its enforcement diverging. Coupling
AC-0001 to the spec's own prose would also have made a frozen spec the runtime
oracle for a living contract.

The spec's Testing Strategy entry was amended to match, and the cohort baseline
re-pinned. That re-pin is a re-approval in substance: it clears the retry
counters and the stasis baseline and re-hashes whatever is on disk.
