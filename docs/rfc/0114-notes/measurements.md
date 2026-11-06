# RFC-0114 measurements

Facts behind the Evidence section of RFC-0114, with the method for each. Taken on 2026-11-06 in a copy of the repository or a scratch directory, so none is a committed artifact.

## RFC length

Method: whitespace-separated word count of each `docs/rfc/NNNN-*.md` file, excluding the title and the header field lines and including everything else (prose before the first section and fenced code both count).

- 112 files: 111 RFCs and `0021-greenfield-inception-research.md`, a research companion.
- Median 4,275 words. Mean 5,217. Longest 15,699 (RFC-0053). 37 files over 5,000.
- RFC-0112: 487 words before "Problem & goals".
- Current template (`assets/rfc.md`): 489 words, seven header fields. Proposed template: 435 words. Whole-file counts.

## RFC-0113 (PR #1698)

| Commit | Words | Words before the problem section |
| --- | --- | --- |
| `659002067` | 6,508 | 1,461 (765 of them a glossary) |
| `12b148b4b` | 4,820 | 1,170 |

The `659002067` text rewritten in the proposed template: 3,073 words. Two fresh-context reviewers examined the rewrite. The first, given only the rewrite, judged two of six decisions on their merits, because the rest depended on ADR and runner terms the file did not explain. The second compared the rewrite with the original and found two costs the rewrite had dropped, which were restored. Only the first tested whether a reader could decide: one reader, one document.

## `rfc.py` against the corpus

`check` over the 112 existing files: one false alarm, a research companion counted as a duplicate number and as missing its sections. Treating `NNNN-<slug>-research.md` as a companion removes it. `new` numbered the next draft 0113 because the open RFC-0113 is on an unmerged branch.

Pressure tests, each in a fresh directory, on a prototype with hand-written confinement checks (the design now uses the shared `file_safety.py`):

- A planted `argparse.py` runs when the call omits `-I` and does not run with it.
- A symlinked template is refused. Symlinked and dangling records are ignored or reported.
- Control characters in a file name are escaped in output.
- A repository whose config sets `core.fsmonitor` and `core.hooksPath` does not run its program.
- Numbers outside 1 to 9999 are refused.
- `--dir` lets a trusted copy work on another folder.
- `renumber` refuses a linked record.
- A decided RFC absent from the default branch is reported.

## Change applied to a copy of the repository

The roster, `new-rfc`, `new-adr` and `navigate-decisions` suites pass after updating:

- three tests that pin pack version 2.5.2;
- the install-snapshot file: four new seed paths in that run, and five in the current design with `docs/rfc/file_safety.py`;
- one test that pins a phrase in the old template;
- the `plugin.json` version;
- a changelog fragment.

Three tests could not run because the copy had no git history or remote. The self-host drift check failed until `GOVERNANCE.md` was added to the paths it does not project.

## Seeded files and upgrade

Scratch catalogue of `repo-governance`, installed at 2.5.2 and upgraded to 2.5.3 and 2.5.4:

| Case | Skill files | Seed files |
| --- | --- | --- |
| Untouched, changed upstream | Refreshed | Left at the old version |
| Edited, changed upstream | Kept, new version beside it as `SKILL.upstream.md` | Kept, no companion |
| Added upstream | Added | Not written |

- `upgrade --seed <path>` returned "primitive not in pack". `install --force` did not add the new seed.
- `agentbundle scaffold --pack repo-governance --packs-dir <catalogue>/packs --output <repo>` added the absent seed and wrote companions for seeds that differed.
- `guides/_shared/explanation/file-safety-contract.md` and `guides/_shared/reference/agentbundle.md` describe seed upgrades as working.
