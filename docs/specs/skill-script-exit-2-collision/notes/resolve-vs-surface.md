# Resolve-vs-surface dispositions

Persistent decisions for the work-loop's resolve-vs-surface gate.

| Question | Disposition | Evidence |
| --- | --- | --- |
| Which skills and entry points are in scope? | Resolve | The approved spec's canonical roster and the repository scan agree on eight skills and nine entry points. |
| Where does the trusted installation base come from? | Resolve | The installer or harness supplies the directory containing the active `SKILL.md`; CWD, user input, environment variables, and profile paths are excluded. |
| What happens for missing, non-file, resolution-error, or escaping targets? | Resolve | Every affected skill stops before runtime launch with a bounded entry-point diagnostic and no credential or dependency routing. |
| Can a shell string be used? | Resolve | Prefer discrete argv. Platform-specific literal quoting is permitted only when the path is representable; otherwise the caller refuses. |
| Does this change exit-code meanings or SSO authority? | Resolve | Exit tables are unchanged. Jira and Confluence headed capture remains operator-only; automatic recovery remains headless. |
| Must the Linear workflow skills change behavior? | Resolve | Their bodies remain unchanged; only the complete user-triggered activation roster is added as pack hygiene. |
| Which verification cannot run in the managed workspace? | Surface | Tempfile-dependent pytest and write-producing projection/build gates require the user's shell. Read-only source, syntax, manifest, eval, and standalone exit checks run locally first. |
| Are exact-content anchor tests affected? | Resolve | No relevant hashes or snapshots were found. Existing Jira and Confluence remediation-string assertions intentionally adopt the resolved form while retaining their semantic and operator-only guards. |
| Are any implementation-review findings unresolved? | Resolve | Rounds 1-5 record each finding and its applied remediation. Round 6 returned unanimous clean results from adversarial, security, and quality reviewers. |
