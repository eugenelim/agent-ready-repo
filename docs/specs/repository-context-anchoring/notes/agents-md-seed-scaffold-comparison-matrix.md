# AGENTS.md seed and scaffold comparison matrix

> Discipline: applied (practitioner-pattern survey)

## Decision question

Which parts of the core `AGENTS.md` seed are useful repository instructions,
which parts merely reproduce this catalogue's own information architecture,
and which conventional headings should a brownfield scaffold use?

## Evidence base

External evidence combines four independent surfaces:

1. The official [AGENTS.md format](https://agents.md/) names project overview,
   build and test commands, code style, testing, and security as popular topics;
   it defines nested `AGENTS.md` precedence and deliberately requires no schema.
2. The [50-project instruction-file study](https://github.com/willhama/md-file-study/blob/main/ANALYSIS.md)
   measures 511 files: exact build/run commands 94%, test commands 92%,
   lint/format commands 86%, nested instructions 74%, and file-tree maps 44%.
3. The MSR study, [Context Engineering for AI Agents in Open-Source
   Software](https://arxiv.org/abs/2510.21413), analyzes 466 projects and finds
   no established content structure.
4. [Evaluating AGENTS.md](https://arxiv.org/abs/2602.11988) evaluates 138 tasks
   from 12 repositories plus SWE-bench. Context files increased exploration and
   cost by more than 20% without a significant overall accuracy gain; agents did
   strongly follow named repository tools. Its authors recommend minimal,
   human-owned requirements rather than generated overview prose.

The smaller [efficiency study](https://arxiv.org/abs/2601.20404) reports the
opposite cost direction over 124 pull requests in 10 repositories: 28.64% lower
median runtime and 16.58% fewer output tokens with `AGENTS.md`. This supports
having repository instructions but does not establish which headings or content
caused the improvement. [moderate; conflicting outcome studies]

## Current core seed bundle

| Seed | Lines | Pressure-test result |
| --- | ---: | --- |
| `AGENTS.md` | 79 | Useful behaviors are mixed with catalogue-specific headings and a mandatory-looking document taxonomy. |
| `docs/CONVENTIONS.md` | 1,482 | Not a neutral coding-conventions starter: it specifies the catalogue's ADR/RFC/spec hierarchy, pack sources, AgentBundle projection, work-loop state, credential brokers, and scaling profiles. |
| `docs/architecture/overview.md` | 81 | Prefills a monorepo tree (`apps/`, `packages/`, `.claude/`) before an adopter has supplied real boundaries. |
| `docs/CHARTER.md` | 78 | Optional greenfield governance template, but it assumes RFC/ADR and the rest of the seeded document hierarchy. |
| `docs/product/changelog.md` | 68 | Contains the core pack's real `1.0.0` Phase-1 changelog, not just adopter placeholders. |
| Product, knowledge, spec, and workspace seeds | 544 | Opinionated work-loop scaffolding; potentially useful when chosen, but not evidence of the adopter's existing conventions. |

The catalogue seed lint does not detect this portability problem. Its blocklist
is empty, `AGENTS.md` requires only `<project-name>`, and a unit test explicitly
permits a repository-specific name in a "portable" seed
(`catalogue_tooling/lint.py:351-372` and
`test_catalogue_tooling_lint.py:1249-1259`). [high; direct local evidence]

## Current AGENTS.md section verdicts

| Current seed section | Keep the behavior? | Conventional replacement | Reason |
| --- | --- | --- | --- |
| `What this repo is` | Yes | `Project overview` | Officially recommended and ordinary repository language. |
| `Keeping changes minimal` | Partly | `Coding conventions` or `Contribution guidelines` | Keep only action-changing repository rules; generic style maxims add cost and may conflict with adopter practice. |
| `Source of truth` | No as a default section | `Documentation`, only when several real sources need routing | The header is not an established AGENTS.md convention, and the current table elevates the catalogue's document hierarchy over adopter equivalents. |
| `How we work` | Yes | `Development workflow` | The work-loop activation is mechanically important; the heading need not use pack vocabulary. |
| `Commands you'll need` | Yes | `Build and test commands` | Exact commands are the strongest convergent content and measurably change agent tool use. |
| `Check before acting` | Partly | Fold into `Coding conventions` | Keep concrete repository prohibitions; remove assumptions that every repo uses ADRs or the catalogue decision process. |
| `Security and privacy` | Yes when applicable | `Security considerations` | Officially recommended; the core loop also reads the declared external quality gate and blessed helpers. |
| `Scoped instructions` | Yes | `Scoped instructions` | Nested precedence is part of the official format and is observed in 37/50 leading projects. |
| `When this file is wrong` | Keep one sentence | Fold into the owning section | Stale/conflicting guidance should surface, but a dedicated scaffold heading is not justified. |

## Folder-map verdict

A raw folder map is not a default requirement. The 50-project study finds one in
22/50 primary instruction files, which proves prevalence rather than task
benefit. In the task benchmark, 8/12 developer context files had a codebase
overview and four enumerated directories, yet context files did not reduce time
to the first patch-relevant file. [moderate]

This repository's map illustrates the maintenance hazard:

- `docs/architecture/overview.md:48` says to edit seeds under `.apm/`, while
  `packs/AGENTS.md` and `packs/core/AGENTS.md` correctly treat `seeds/**` and
  `.apm/**` as sibling sources.
- `docs/architecture/overview.md:118-124` calls RFC-0008 and RFC-0010 the most
  recent accepted RFCs even though the repository is now beyond RFC-0090.
- The useful part is not the tree at lines 8-36; it is the non-obvious generated
  projection warning at lines 38-49 and the subsystem pointers at lines 51-92.

Therefore an existing architecture or structure document may be linked when it
contains real ownership and change boundaries. The doctor should offer a new
structure section or scoped `AGENTS.md` only when those boundaries would change
an agent's actions. It should not generate a generic directory tree. [high for
the local contradiction; moderate for general effectiveness]

## Recommended scaffold vocabulary

Use ordinary headings and omit any section with no verified content:

```markdown
# AGENTS.md

## Project overview

## Documentation

## Development workflow

## Build and test commands

## Coding conventions

## Security considerations

## Scoped instructions
```

`Documentation` is conditional: one source is linked in the relevant prose;
several authoritative sources may use a short topic/source table. `Security
considerations` and `Scoped instructions` are also conditional. A minimal
brownfield result therefore remains roughly 15-25 lines rather than filling
seven empty headings.

For a repository with no `CONTRIBUTING.md`, the doctor first looks for the
actual contributor entry point referenced by the README, CI, or existing docs.
It may separately suggest the conventional root, `.github/`, or `docs/`
`CONTRIBUTING.md` for human-facing contribution guidance. It does not invent
nested contribution files or make that document a prerequisite for AGENTS.md.

## Implementation implications

1. Separate the catalogue's rich root `AGENTS.md` from the portable seed. They
   may share concepts but should not be kept structurally identical by default.
2. Remove the seed's `Source of truth` contract and replace it with contextual
   links under conventional headings.
3. Preserve this repository's richer documentation routing only where it helps
   its own build loop; call the section `Documentation` and keep mechanically
   authoritative code/skill rules in their owning workflow sections.
4. Make `adapt-to-project` discover adopter sources before pack defaults and
   propose a populated scaffold rather than copying a fixed map.
5. Do not treat the generic architecture-overview tree as repository evidence.
   Rewrite it as optional enrichment or stop offering it by default; any change
   to seed delivery mechanics must be sequenced with the independently owned
   installation work.
6. Treat the non-portable `CONVENTIONS.md` and real core changelog content as a
   separate seed-bundle finding. Fixing their delivery/classification is larger
   than the repository-anchoring surface and must not be hidden inside a header
   rename.

## Known unknowns

- **Known-unknown:** Which individual sections improve task success for this
  catalogue's agents. An A/B fixture eval over structural and non-structural
  tasks would close it; prevalence alone cannot.
- **Known-unknown:** Whether core's non-AGENTS seed documents are always
  explicitly accepted before appearing in a brownfield repository. This belongs
  to the parallel installation-handoff work.
- **Known-unknown:** Whether a compact `Documentation` table outperforms inline
  links. Retrieval-oriented fixture evals can compare them.
- **Unknowable from current evidence:** A universally correct future AGENTS.md
  header schema; the standard intentionally permits arbitrary Markdown.
