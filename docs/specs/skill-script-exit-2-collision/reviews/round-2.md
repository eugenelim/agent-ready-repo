# Implementation review round 2

## Blockers

None.

## Concerns

**1. Windows command renderers admit PowerShell expansion syntax.** `packs/atlassian/.apm/skills/jira/scripts/_client.py:77`
The copied Windows renderers reject cmd metacharacters but still emit paths
containing PowerShell-sensitive `$()`, backticks, `$env:` text, or single
quotes. Fix: use a conservative Windows-safe allowlist or refuse textual
commands, apply it to every affected Python and Node renderer, and add
helper-level regressions for spaces, both quotes, `$()`, backticks, `$env:`,
`%...%`, and `!...!`.

**2. The byte-identical setup helper still emits Jira-specific guidance.** `packs/atlassian/.apm/skills/confluence-crawler/scripts/setup_sso.py:103`
Although the helper docstring is now neutral, its runtime success preamble
still calls Jira's `check --register` the attested capture path. Fix: replace
the sentence in both parity-governed copies with neutral active-skill wording
and extend the Crawler regression to reject `jira.py`, `jira skill`, and
`check --register` in shipped Crawler surfaces or setup output.

## Nits

None.

## Accepted disposition

`credbroker-refresh-stderr-bounding` remains a valid out-of-scope broker
follow-up for this four-pack caller-contract change. Reviewers did not require
the private broker boundary to change in this patch.

## Remediation disposition

1. Every Python renderer now routes Windows output through the same
   conservative ASCII allowlist and refuses paths containing either quote,
   `$()`, backticks, `$env:` text, `%...%`, `!...!`, or any other punctuation
   outside the inert path set. The Node renderer uses the equivalent allowlist.
   Pack-local helper-level tests extract and execute each shipped Python helper;
   the Node test requires and exercises the exported pure helper.
2. Both parity-governed setup helpers now emit neutral active-skill guidance.
   Their byte-identical tests reject `jira.py`, `jira skill`, and
   `check --register` in runtime stderr; the Crawler surface test rejects the
   same stale forms across the shipped skill.
