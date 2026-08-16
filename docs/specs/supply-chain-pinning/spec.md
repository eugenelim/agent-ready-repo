# Spec: supply-chain-pinning

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none. CI configuration and one SCA invocation.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. Risk trigger: security boundary (supply chain — what third-party
code CI executes, and what gets audited). `security-reviewer` is a NAMED SKIP
under this session's no-subagent instruction; reasoning is inline in the plan. -->

## Objective

Make what CI executes immutable, and audit the one third-party dependency that
was slipping past the SCA gate.

## Acceptance Criteria

- [x] **AC1 — every `uses:` is pinned to a 40-character commit SHA.** 38 pins
  across 10 workflows, plus 2 CodeQL subpath actions. Verification:
  `grep -rhoE "uses:\s*\S+@\S+" .github/workflows/*.yml | grep -vE "@[0-9a-f]{40}$"`
  returns nothing.

- [x] **AC2 — the one mutable *branch* ref is gone.**
  `release-credbroker.yml` used `pypa/gh-action-pypi-publish@release/v1` — a
  branch, not a tag, on a job that holds a PyPI publishing token. Its sibling
  `release-agentbundle.yml` already pinned the same action to a SHA; both now
  agree on `dc37677…` (v1.14.2).

- [x] **AC3 — every pin carries its tag in a trailing comment.** A bare SHA is
  unmaintainable: neither Dependabot nor a human can tell which version it is.

- [x] **AC4 — the pins are correct, not merely present.** Each SHA was resolved
  from the tag through the GitHub API at pin time, and the eight actions already
  pinned elsewhere in the repo resolved to exactly the SHAs those files carry.

- [x] **AC5 — the zizmor suppression is retired, not widened.** The
  `unpinned-uses` ignore list named 13 workflows. With nothing left to suppress
  it is deleted, and the file now documents how to pin a newly-added action
  instead of how to add another exemption.

- [x] **AC6 — no workflow line other than a `uses:` line changed.** 38
  insertions, 38 deletions — one for one.

- [x] **AC7 — `pyyaml` reaches the SCA gate.** `packages/agentbundle`'s `[lint]`
  extra is `pyyaml>=6.0`, genuinely third-party and audited by nothing: the
  Makefile audited `tools/requirements-sast.txt` and credbroker's `[crypto]`
  extra, and both packages declare `dependencies = []`, so the extra was the one
  thing that was not nothing. It joins the explicit audit line.

- [x] **AC8 — the audit still passes.** `pip-audit` over the extended set
  reports no known vulnerabilities.

- [x] **AC9 — both backlog entries removed.**

## Boundaries

### Never do

- Never re-add an `unpinned-uses` suppression. Pin the action instead; AC5's
  file says how.
- Never pin without the tag comment.

## Testing Strategy

- **Goal-based**: the AC1 grep, the AC6 diff shape, and `pip-audit`'s exit code.
  Workflow correctness is proven by CI running on this very PR — every pinned
  action executes here.
