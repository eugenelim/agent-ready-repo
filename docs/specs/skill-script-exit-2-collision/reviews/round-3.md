# Implementation review round 3

## Blockers

**1. Dependency remediation still shell-interpolates the resolved install path.** `packs/converters/.apm/skills/markdown-to-html/scripts/render.js:64`
The missing-dependency diagnostic inserts the installed skill directory inside
raw double quotes. A directory containing a double quote, `$()`, or backticks
can therefore change how a copied remediation command is parsed. Fix: render an
argument-vector-shaped npm command through the same platform-specific safe
renderer, with bounded non-command guidance when the path is not representable.

## Concerns

**1. Windows renderer safe-path tests assert quote shape instead of argv preservation.** `packs/atlassian/tests/skills/jira/test_invocation_contract.py:86`
The affected Python and Node tests count quote characters for the safe path,
which would still pass if the renderer reordered, rewrote, or dropped an
argument. Fix: assert the exact rendered command naming the original executable
and entry path while retaining the unsafe-character refusal table.

## Nits

None.

## Specialist results

Security reviewer: Clean — ready to commit.

## Remediation disposition

Both findings were in-scope and mechanical, so both were accepted for this
patch.

1. Markdown-to-HTML now renders `npm --prefix <installed-skill-dir> install`
   through the same platform-specific command renderer as its runtime entry
   point. POSIX paths are single-quote escaped; unsafe Windows paths fall back
   to bounded prose rather than producing a copyable shell command. A pure
   helper regression covers double quotes, `$()`, and backticks in the path.
2. All seven Python renderer tests and the Node renderer test now assert the
   exact safe command, preserving the executable and entry-point arguments.
   Their unsafe-character refusal tables remain intact.
