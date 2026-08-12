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

## Errata

Corrections below are Approver-signed. The body above is preserved unchanged;
errata supersede where noted. This ADR is Accepted → Frozen
(`docs/CONVENTIONS.md`). (Approver: eugenelim, 2026-08-12.)

- **2026-08-12 — the control is live; *Confirmation* is satisfied.** Every signal
  the *Confirmation* section names has been exercised. The publisher App is
  installed on this repository only, with Contents read/write as its sole write
  permission. The `claude-plugin-publish` environment admits `main` only,
  requires one reviewer, prevents self-review, and disallows admin bypass. An
  active ruleset targets exactly `refs/heads/claude-plugins-dist`, restricting
  updates and deletions and blocking force pushes, with the App as its only
  always-bypass actor. On a canary ref, an ordinary owner push was rejected
  (`GH013 … push declined due to repository rule violations`) and the same commit
  pushed with an App installation token was accepted (`Bypassed rule
  violations …`); the canary was then removed with the App identity and the
  ruleset retargeted, so the live branch was never a negative probe. The
  sanitized snapshot is committed at
  `docs/specs/claude-plugin-hook-parity/publish-control-evidence.json`.

- **2026-08-12 — the decision needed an ordering rule it did not state.** This
  ADR specified the end state but not the identity to hold *until* the App
  exists. The token-minting step consequently merged ahead of its credentials
  and every push to `main` failed at
  `[@octokit/auth-app] appId option is required` for eight consecutive commits,
  while the construction tests stayed green because they asserted the end-state
  workflow shape without asking whether the credentials it named existed.
  `docs/specs/claude-plugin-hook-parity` AC36 closes this: the workflow's
  identity must match provisioning state, read offline from whether the evidence
  file exists, and both directions fail closed — an App-token workflow without
  evidence is refused, and so is the interim publisher once evidence lands. The
  decision is unchanged; it is now sequenced.

- **2026-08-12 — `prevent_self_review` is disabled; the gate was unsatisfiable.**
  The *Decision* above specifies an environment that "requires owner approval"
  together with self-review prevention. On a repository where one person merges
  every change, that person is always the deployment's triggering actor, so
  GitHub withholds the approval control from the only account that holds it —
  and with `can_admins_bypass` false there is no override. The first real
  publication after rollout sat in `waiting` with
  `current_user_can_approve: false` and **could not be approved by anyone**.

  The canary probes did not catch this because they minted an App token directly
  rather than routing through the environment, so the approval path was never
  exercised end to end until a live publish.

  `prevent_self_review` is therefore now `false`. The reviewer requirement
  stands: every publication still waits for a human to release it deliberately,
  and `can_admins_bypass` stays `false` so the gate cannot be stepped around.
  What is lost is the second pair of eyes, which a single-maintainer repository
  could never actually supply. Restoring `true` requires a second trusted
  reviewer account, and would otherwise reintroduce the deadlock.

- **2026-08-12 — no internal identifier is recorded.** The *Confirmation*
  signal "sanitized live settings snapshots" is narrowed: the evidence artifact
  carries no App, installation, ruleset, account, or node ID. The three-way
  identity agreement between the ruleset bypass actor, the App installation, and
  the environment's App ID variable is computed against live state at capture
  time and committed as a single asserted boolean, and the repository lint walks
  the artifact to refuse any forbidden identifier key. Recorded as AC36
  clause 6. This strengthens "sanitized" rather than relaxing it.
