# Self-coverage module — pre-mortem

Part of the [self-coverage gate](coverage-record.md). Runs at the **divergence**
stage (against each candidate shape) and again **pre-G2** (against the converged
spine).

## The move

Assume the shipped product **failed**, then work backwards to *why*. Imagine it is
a year out and the initiative was a disappointment — name the most plausible causes
before they happen, while they are still cheap to fix.

For each candidate shape and the converged spine, name:

- **The myopic-greedy failure** — the loop locked onto the first coherent framing
  and missed a higher altitude (the whole domain, not one slice) or a deeper
  sub-domain. This is the loop's *headline* failure mode; the divergence stage
  exists because of it.
- **The ungrounded-domain failure** — a load-bearing domain claim was asserted, not
  grounded (routes to [`domain-grounding`](domain-grounding.md)).
- **The over-scope failure** — a capability nobody asked for rode in past the Scope
  Boundary.
- **The unbacked-security-screen failure** — a security-sensitive surface designed
  with no threat lens (the worked example's whole ripple was a prompt-injection
  self-modification finding).
- **The converged-not-validated failure** — the brief shipped as a finished plan,
  not a connected hypothesis; a load-bearing assumption had no validation hook.

## Output

A short list of named pre-mortem causes, each routed: **resolve** (a referent
fixes it — fix it now) or **surface** (irreducible — carries to the coverage
record). A pre-mortem that produces nothing on a non-trivial discovery is a sign
the loop wasn't looking, not that there was nothing to find.
