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
