## Scope

Pre-execute secure-design review of the spec/plan amendment on branch
`promotion-drain-hardening` (commits `3bcbd7f38..7b5ac5be2`), which reopens
`docs/specs/work-item-promotion-handoff` for the four sustained post-merge
findings (no-dispatch routes, unvalidated classification, closure-test
ownership, stale workspace lock). Boundaries crossed by the change:
path-and-file (lock file and acquisition temporary; superseded-citation
path resolution) and exceptional-conditions (lock recovery, retry, hold
behavior). Reviewed against `security-checklists` modules `path-and-file`
(CWE-22/CWE-73, ASVS 5.0 V12, Proactive Controls C3) and
`exceptional-conditions` (OWASP A10, ASVS 5.0 V16, Proactive Controls C10).

## Findings

None sustained.

## What was checked, and why it holds

- **Citation-path confinement (CWE-73 depth, not just CWE-22).** § D5 and
  AC-0027 resolve the cited path within the repository root with symlinks
  followed — canonicalize-then-verify, the deeper control — and refuse
  absent, non-resolving, root-escaping (`..` or absolute), and
  root-escaping-symlink citations. The refusal is stated per form and
  driven in the Testing Strategy and T21. Fail-closed: a refused citation
  holds the item.
- **Lock-path file-shape discipline.** A non-regular file at the lock path
  (symlink, FIFO, device) is alien — never probed, never removed — and the
  payload read is no-follow, non-blocking, and bounded. This closes the
  FIFO-blocking and symlink-following attacks a foreign-authored lock file
  admits.
- **Lock-stealing and race discipline.** Live-owner locks are never taken;
  removal re-verifies inode and pid payload immediately before the unlink
  and refuses when the lock changed; the both-recoverers window is
  disclosed as a bounded residual with the token-keyed alternative routed
  to the lock protocol's owner — an honest, owner-assigned disclosure, not
  a silent gap. PID reuse is disclosed and bounded by the short critical
  section; its failure mode is a conservative refusal, never an unsafe
  grant.
- **Acquisition temporary.** Per-holder unique name (pid plus random
  token) created fresh — unpredictable, no collision, no
  pre-placement attack; unlinked after publication and on link failure;
  orphans are inert and never block later acquisition; gitignored in both
  the root and the adopter seed.
- **Exceptional-conditions discipline.** Every security-relevant failure
  fails closed: no dispatch wired → hold; non-member or non-dispatchable
  classification → hold; refused citation → hold; lock states that cannot
  be proven stale → lock-busy. Retry is bounded (once). The failure-hold
  rule names the failing stage or refusing control in the run report — no
  silent swallow, no exception text (the transaction's existing contract
  already refuses to return exception values because they may carry
  untrusted data or sensitive paths).

## Not checked

- access-control, authn-session, injection, secrets-and-crypto,
  outbound-ssrf, supply-chain, config-misconfig, llm-agent, and
  agentic-skills: the amendment crosses none of these boundaries — no new
  authn surface, secret handling, outbound call, dependency, configuration
  surface, or LLM-authority change is introduced by the spec/plan text
  under review.
