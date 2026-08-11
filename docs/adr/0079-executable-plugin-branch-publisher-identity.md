# ADR-0079: Executable plugin branch — dedicated publisher identity

- **Status:** Accepted
- **Date:** 2026-08-10
- **Decision-makers:** eugenelim
- **Consulted:** security-reviewer, adversarial-reviewer
- **Supersedes:** none
- **Related:** [ADR-0072](0072-derived-plugin-manifest-mirrors-upstream-schema.md), [`docs/specs/claude-plugin-hook-parity/`](../specs/claude-plugin-hook-parity/)

## Decision summary

- **Decision:** Only a dedicated, repository-scoped GitHub App may update
  `claude-plugins-dist`.
- **Because:** A generic Actions-app bypass identifies the platform actor, not
  the reviewed publisher workflow.
- **Applies to:** Claude-plugin dist publication and its CI authentication
  boundary.
- **Tradeoff accepted:** Publishing gains an owner-approved environment step
  and an operational app credential.
- **Revisit if:** GitHub offers workflow-scoped ruleset bypass or the
  marketplace moves to immutable commit SHAs.

## Context

`claude-plugins-dist` serves executable plugin code from a mutable branch.
Existing force-push and deletion restrictions protect history but do not stop an
ordinary fast-forward push from replacing hook bodies.

The current publisher uses `GITHUB_TOKEN` with `contents: write`. That token
represents GitHub's repository Actions app. Allowing that app through a branch
ruleset would permit every workflow with an equivalent token to update the
executable branch.

GitHub rulesets can restrict updates to named bypass actors, protected
environments can hold credentials until approval, and GitHub Apps provide
short-lived installation tokens with repository-scoped permissions.

## Decision

We will make a dedicated publisher GitHub App the sole bypass actor for an
exact-branch ruleset protecting `refs/heads/claude-plugins-dist`.

The app is installed only on this repository and has Contents read/write with
no other write permission. Its app ID and private key live only in the
`claude-plugin-publish` environment, which accepts `main`, requires owner
approval, and disallows protection-rule bypass.

The workflow's ordinary `GITHUB_TOKEN` is read-only. Checkout persists no
credential. Every external action is pinned to a full commit SHA. A short-lived
app token is minted after environment approval and supplied only to the final
publisher step through a non-logged subprocess environment.

Desired settings and sanitized live evidence are independently represented and
checked by a pure-stdlib repository lint.

## Decision drivers

- Prevent direct or unrelated-workflow updates to executable plugin content.
- Preserve the existing machine-generated dist branch and marketplace topology.
- Avoid user-bound, long-lived credentials.
- Make configuration drift and rollout evidence mechanically reviewable.

## Consequences

**Positive:**

- Ordinary writers and unrelated workflows cannot update the executable branch.
- Each publication has an explicit approval and audit event.
- Publisher credentials are short-lived and repository-scoped.
- The existing branch name and plugin source shape remain unchanged.

**Negative:**

- The repository owner must create and maintain a GitHub App, environment, and
  ruleset.
- Every publication requires environment approval.
- The app credential remains high-value during an approved publishing job.
- The mutable ref still lacks adopter-verifiable content hashes.

**Revisit if:** GitHub offers workflow-scoped ruleset bypass or the marketplace
moves to immutable commit SHAs.

## Confirmation

- **Mode:** architecture fitness test + periodic audit
- **Signal:** workflow construction lint, desired-state/evidence comparison,
  ordinary-identity canary rejection, publisher-app canary acceptance, and
  sanitized live settings snapshots
- **Owner:** repository owner

## Alternatives considered

- **Bypass the generic GitHub Actions app.** Rejected because all workflow
  `GITHUB_TOKEN`s represent that app; it cannot distinguish one workflow.
- **Require pull requests on the generated dist branch.** Rejected because it
  replaces deterministic machine publication with a second review/merge
  lifecycle.
- **Use a personal token or deploy key.** Rejected because it is long-lived or
  user-bound and has a weaker approval boundary.
- **Pin marketplace entries to immutable SHAs.** Desirable follow-on, but the
  current marketplace/dist publishing cycle cannot know its own resulting
  commit before publication without changing topology.

## References

- [GitHub: available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
- [GitHub: deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- [GitHub: `GITHUB_TOKEN`](https://docs.github.com/en/actions/concepts/security/github_token)
- [GitHub: `actions/create-github-app-token`](https://github.com/actions/create-github-app-token/blob/main/README.md)
