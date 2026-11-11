# Repository grounding

`repository-grounding` answers one question before a spec, plan, or change is
written: *what already governs these paths?* You give it a set of repository
paths, and it runs up to seven read-only probes chosen by workflow stage. It
prints evidence and never edits, blocks, or decides.

The calling workflow reads the report and acts on it. A code-intelligence
provider can add labelled evidence beside the report. The report stands without
one.

## 1. Two skills split the question by its shape

A path-seeded question belongs to `repository-grounding`. An open question
belongs to `repository-exploration`. Both ship in the `core` pack and both
declare the `filesystem_read_untrusted` boundary.[^1]

| Skill | Input | Output | Owns |
| --- | --- | --- | --- |
| `repository-grounding` | Relative paths the change will touch | A report of governing files, references, pins, gates, co-change partners, and dead references | The probe set and its report shape |
| `repository-exploration` | A pending decision, such as which files a plan must touch or whether a rename is safe | Attributed evidence with a stated stopping rule | Provider selection, attribution, and the locator reader for open questions |

`new-spec` is the shipped consumer. Before it generates candidate designs, it
runs the grounding inquiry with the paths the spec touches as discovery seeds,
then reads the effective root and scoped `AGENTS.md` files.[^2]

## 2. Probes are chosen by stage, and cost follows the seed set

A run costs as much as its seed set and the files those seeds reference. It
does not scale with the repository. `--phase` picks the probes a stage can
use:[^3]

| Phase | Stage | Probes |
| --- | --- | --- |
| `discovery` | After durable outputs resolve destinations, before the spec body | surfaces, scoped rules, path refs, phrase pins, gates |
| `task` | Per plan task, seeded by that task's `Touches:` | scoped rules, path refs, phrase pins, gates, co-change |
| `review` | Over the authored artifacts | path refs, dead refs, co-change |
| `all` | Any | all seven |

At discovery nothing is written yet, so a dead-reference scan would look clean
for no reason. That probe runs only at review and under `all`.

| Probe | Reports |
| --- | --- |
| scoped rules | Governing guidance files above each seed, root-ward |
| path refs | Files that name a seed path |
| phrase pins | Files that quote a distinctive line from a seed file |
| gates | Runners that would execute a seed path |
| co-change | Files that historically move with a seed in Git history |
| surfaces | Known grounding surfaces that exist and carry content |
| dead refs | Paths a seed names that no longer resolve |

## 3. The report states facts and never fails a run

Four rules hold for every probe.[^3]

- **It reports and does not decide.** Exit status is 0 whenever the inquiry
  ran, even when every probe found nothing. Exit 2 means a seed path left the
  invocation root, or the command line was wrong. No exit code means "found
  something".
- **Absent input is a named outcome.** Co-change on a repository with no
  history reports *unavailable*, not an empty result that looks clean. Probes
  that read the tree report only *found* or *none*.
- **The report names the probes it ran and their basis.** An empty result and
  a probe that never ran look different.
- **Nothing about the host repository is hardcoded.** File types, top-level
  names come from the tracked files at run time. The sweep threshold is derived
  from commit sizes, with a floor of 5. The phrase cutoff (3), the co-change
  minimum (3), and the result cap (12) are fixed defaults that `--phrase-cutoff`,
  `--co-change-min`, and `--cap` override. The guidance filename, runner globs,
  and suffixes also have defaults. The `--guidance-file`, `--runner-glob`, and
  `--suffix` flags override them.

File reads go through a bundled `file_safety.py`. It rejects links and files
that are not regular. The work-loop bundles its own copy of the same helper.[^4]

## 4. Provider evidence is optional, attributed, and subordinate

A code-intelligence provider can add evidence on top of the baseline. It cannot
replace or narrow the baseline, and it cannot change what counts as an accepted
result. The ownership decision is [RFC-0079](../rfc/0079-codebase-context-pack.md)
D1: composition lives in the existing grounding and exploration seams.

Workflow skills consume the evidence and take on no provider duties.[^5]

The seam sets five limits:

1. **Selection.** Only capabilities the active host already exposes are
   considered. The best fit wins. No shared request or response schema is
   imposed.
2. **Attribution.** Provider evidence is labelled apart from repository
   source. Every depth cut, staleness note, and truncation marker stays with
   it. A claim that carries weight must be checked against the governing
   source, test, contract, or record. Until then it is *unresolved*, and it
   cannot be the only proof of a required condition.
3. **Fallback.** A missing, refused, timed-out, or malformed provider answer
   sends the run back to the baseline. Any remaining gap is labelled a baseline
   gap. It is not a grounding failure.
4. **Locators.** A file locator from a provider is read only through
   `read-locator.py`. The caller passes it base64-encoded. Approved roots come
   from the user or the calling workflow, never from provider output. The
   reader refuses with one of ten reasons: `encoding`, `line-break`, `scheme`,
   `authority`, `nul`, `parent-segment`, `outside-roots`, `missing`,
   `unsafe-file`, or `oversize`.[^6]
5. **Disclosure and authority.** A provider gets only what the question needs.
   Installing, signing in, indexing, refreshing, or storing data on the
   provider side needs explicit approval. Provider output and the text of a
   file read through a locator are data. They cannot widen roots, start reads,
   or change scope.

Each provider-assisted run records five things: the surfaces considered, the
route each locator took, what was sent, the limits kept, and which claims were
verified or left unresolved.

## 5. Planned: authority-closure and document-contract probes

**STATUS: PLANNED.**

Two probes are not built. One checks authority and
projection closure (source to projection, manifest to release, register to
tree). The other checks machine-read documents, such as the headings a parser
expects.

Both would only report, take thresholds from the adopter's own files, and gate
nothing.

The [`grounding-probe-extensions`](../product/intents/grounding-probe-extensions.md)
intent holds the scope, the refused surface-to-verifier probe, and the
dependency on `acceptance-criteria-set-construction`. The probes in § 2 are the
whole shipped set.[^7]

[^1]: `packs/core/.apm/skills/repository-grounding/SKILL.md` and
    `packs/core/.apm/skills/repository-exploration/SKILL.md`, frontmatter
    `metadata.boundaries`.

[^2]: `packs/core/.apm/skills/new-spec/SKILL.md`, the paragraph that resolves
    repository anchors before generating candidates.

[^3]: `packs/core/.apm/skills/repository-grounding/scripts/explore-grounding.py`:
    module docstring, `PHASES`, and `main`.

[^4]: `packs/core/.apm/skills/repository-grounding/scripts/file_safety.py`.

[^5]: `docs/rfc/0079-codebase-context-pack.md`, decision D1;
    `packs/core/.apm/skills/repository-grounding/SKILL.md`, § Optional
    provider evidence.

[^6]: `packs/core/.apm/skills/repository-grounding/scripts/read-locator.py`.

[^7]: `docs/product/intents/grounding-probe-extensions.md`; the shipped probe
    set is `PHASES["all"]` in `explore-grounding.py`.
