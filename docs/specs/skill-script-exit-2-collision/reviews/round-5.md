# Implementation review round 5

## Blockers

**1. Markdown-to-HTML dependency examples still teach shell-unsafe path substitution.** `packs/converters/.apm/skills/markdown-to-html/SKILL.md:60`
The dependency commands put the resolved `<skill-dir>` inside POSIX double
quotes, where `$()`, backticks, and variable-shaped text still expand. The
source contract currently blesses that exact form. Fix: use the installed
entry-point contract's single-quoted POSIX/PowerShell literal form, retain its
refusal rule for unrepresentable paths, and reject double-quoted dependency
prefix examples.

**2. Markdown-to-HTML evals still positively require bare npm install.** `packs/converters/.apm/skills/markdown-to-html/evals/evals.json:9`
The success eval says to run bare `npm install` from the skill directory, while
the source-contract regex only rejects a line beginning with that command.
Fix: require the resolved-prefix dependency check and install in the eval,
remove other bare-command spellings from shipped surfaces, and reject bare
`npm install` wherever it appears rather than only at line start.

## Concerns

None after deduplication; the quality finding is covered by blocker 2.

## Nits

None.

## Security review limit

SAST/SCA and live eval execution were not run in the reviewer pass. Source,
tests, documentation, and scanner/gate wiring were reviewed.

## Remediation disposition

Both blockers were in-scope and were applied.

1. All dependency examples now use the entry-point contract's single-quoted
   POSIX/PowerShell literal form and explicitly carry its single-quote refusal
   rule. The source contract rejects double-quoted dependency-prefix examples.
2. The success eval now requires both the resolved-prefix dependency check and
   consent-gated resolved-prefix install. Remaining prose no longer spells a
   bare install command, and the source contract rejects that command wherever
   it occurs rather than only at the beginning of a line.
