# Repository tools

## Finding-response scorer

`python3 tools/score_finding_responses.py <case-file> <transcript-file>` reads
one recorded case and transcript. Valid inputs print the arm, repair share,
counts for every disposition, baseline and answered acceptance-criteria counts
with their change, and finding dispositions. Invalid input names every
applicable offender on stderr and exits non-zero.

Transcript headers record the terminal-clause label in `Grammar`, plus the
repository-relative rendering path and its lowercase SHA-256 digest in
`Rendering` and `Rendering-sha256`. The parser validates the digest's format
without reading the rendering file, so parsing remains a pure operation over
the supplied transcript text. Frozen-corpus validation separately requires
the canonical repository-local rendering for the transcript's case and arm.
It rejects symlink renderings, verifies every finding line carries the declared
terminal-clause label, requires a non-empty, complete set of well-formed
finding records whose identifiers match the transcript responses exactly once,
and verifies that the rendering bytes match the recorded digest.

## Cognition scorer

`python3 tools/score-cognition.py FILE [FILE ...]` describes an authored reply
against the cognitive-load rule's readable effects. It reports quantities,
asserts no direction, and returns no verdict: the rule says a table is used only
when it makes a link much clearer and that exact names and paths are kept, so
neither fewer tables nor fewer technical tokens is an improvement the tool may
claim.

It exists because `check-output-readability.py` removes tables, code, links and
technical tokens before scoring, so a table-heavy reply scores well on the little
that survives. What that strip discards is kept here as separate quantities:
`scored_pct`, `table_density` and `jargon_density`.

`--pair CONTROL TREATMENT` reports each quantity's difference. `--spread SAMPLE
[...]` reports the range across same-arm samples — the floor a difference must
clear to mean anything. `ease` and `grade` are one dimension reported twice, not
two agreeing signals. Input is read through the repository's confinement helper.
