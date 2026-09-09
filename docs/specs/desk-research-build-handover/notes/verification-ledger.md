# Verification ledger: desk-research-build-handover

Execution observations. `spec.md` and `plan.md` are pinned in substance from
approval; everything produced by running the work lands here
(`docs/CONVENTIONS.md` § *A spec directory freezes as a unit*).

## Execution — 2026-09-09

T1 was implemented by a scoped Codex worker under a three-file allowlist. T2
(mutation proofs) and T3 (gates) are recorded here.

### Gates

| Command | Exit | Result |
| --- | --- | --- |
| `python3 tools/build-site.py` | 0 | generated |
| `npm run build --prefix web` | 0 | 50 pages |
| `npm run build --prefix docs-site` | 0 | 238 pages |
| `npm test --prefix web` | 0 | 148 passed across 18 files |
| `python3 -m pytest` over the 7 touched `tools/` suites | 0 | 170 passed |
| `make site-link-check` | 0 | 73,081 links across 288 pages, clean |
| `git diff --check` | 0 | no whitespace errors |

The three new cases were confirmed **executed, not skipped**: a filtered run
reported `3 passed | 39 skipped`. AC2 sits outside the build-gated `describe`
deliberately — a source check that silently skips when the site has not been
built is a control that cannot fail.

### Route preservation

`comm -23` against the sibling slice's 288-route baseline returned **0 lost
routes**.

### The defect is gone at the emitted layer

`build/docs/guides/desk-research/index.html` now contains **zero** occurrences of
`blob/main/guides/desk-research`. Before this slice it carried the laundered
fallback for every unresolvable link. The link total rose 73,075 → 73,081,
consistent with one added handover link and five links that now resolve
internally rather than leaving the audit's scope.

### Mutation proofs — seven, all killing their target

| # | Invariant | Mutation | Observed |
| --- | --- | --- | --- |
| M1 | AC2 catches a plain missing `.md` | `[m1](./no-such-file.md)` in `tutorials/` | AC2 failed |
| M2 | AC2 catches a missing directory | `[m2](./no-such-dir/)` in `how-to/` | AC2 failed |
| M3 | AC2 strips fragments before resolving | `[m3](./no-such-file.md#section)` in `explanation/` | AC2 failed |
| M4 | AC2 requires a directory to hold `README.md` | `[m4](../how-to/)` in `reference/` | AC2 failed |
| M5 | AC2 **traverses** rather than reading a fixed list | created `explanation/zz-traversal-probe.md` with one broken link | AC2 failed |
| M6 | AC1 reads the article body | deleted the README handover entry | AC1 and AC3 failed |
| M7 | AC1 rejects a collapsed disclosure | same link, same text, same target, wrapped in `<details>` | AC1 and AC3 failed |

M1–M4 were placed in four different subdirectories and none in `README.md`, so
each failure is also traversal evidence: a verifier reading only `README.md`
survives none of them. M5 is the decisive one — a file that did not exist when
any verifier was written cannot be in a hard-coded list, so it kills the whole
family of selective verifiers rather than one member per round. M7 proves the
`<details>` branch that was added in review round 5; without it that branch
would have been asserted and never exercised.

All mutations were reverted by editing and by removing the probe file — never
`git checkout`, `git reset`, or `git stash`, which would also have discarded this
slice's real work, the sibling slice's uncommitted work, and a peer session's
changes in this tree. Residue check after restore: no `details>`, `zz-traversal`,
or `no-such` strings remain in the pack; the pack's Markdown file count returned
to 8.
