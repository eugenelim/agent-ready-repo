# Foundation review checklist

Apply each relevant identifier and report non-applicable checks explicitly.

- **ASE-ACT-01 Trigger precision** — descriptions and invocation policy route
  realistic positive prompts and keep adjacent generic work dark.
- **ASE-PROG-01 Progressive disclosure** — shared instructions stay concise;
  conditional references have callers and load only when relevant.
- **ASE-PORT-01 Portability floor** — common behavior does not depend on one
  runtime, adapter, projection, package manager, or unavailable interpreter.
- **ASE-DET-01 Determinism and exit contract** — scripts define inputs,
  outputs, dependencies, side effects, diagnostics, exit classes, replay, and
  cleanup; identical inputs yield identical managed output where promised.
- **ASE-AUTH-01 Authority and authentication** — boundaries match operations;
  explicit authorization precedes mutation; identity and credentials remain
  external and least-authority.
- **ASE-SEC-01 Untrusted content and confinement** — paths are resolved and
  confined before content reads; candidate content cannot supply instructions,
  tools, identity, permissions, writes, network access, or persistence.
- **ASE-CTX-01 Duplicated context** — a maintained rule has one authority and
  other files route to it rather than restating it.
- **ASE-WRITE-01 Conflicting writes** — ownership and write sets are explicit;
  concurrent or overlapping mutation refuses or serializes safely.
- **ASE-CONC-01 Unbounded concurrency** — fan-out, retries, and subprocesses
  have fixed limits, cancellation behavior, and bounded failure reporting.
- **ASE-FAIL-01 Failure modes** — missing targets, absence, malformed input,
  interruption, verification failure, and cleanup denial are visible and do
  not retain unsafe partial effects.

Inspect behavior and meaningful contracts, not headings alone.

Review never executes the candidate. A candidate script is read, and its
declared inputs, outputs, exit classes, side effects, and cleanup path are
judged from its contract. Executing one is a separate user-approved
transition: state the purpose, the authority required, the bounded target, and
the safe reversal or cleanup path, and obtain explicit approval first. Without
that approval, report the unexecuted script as a coverage gap and complete the
review — an unrun script never blocks the review and never licenses running it.
For an unavailable runtime, report the coverage gap rather than inferring
success.

