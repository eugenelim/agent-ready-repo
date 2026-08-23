# Refresh capability walkthrough

**Date:** 2026-08-17  
**Reviewer:** work-loop supervisor  
**Boundary:** local fixtures and fake transports/runners only; no tracker
credentials, browser session, live acquisition, or live write was used.

## Shared scope

Each flow starts with an existing registered tracker-origin artifact and a
trusted `1.0` profile. The fixtures compare source revision `1` with revision
`2` across Draft, Accepted/Ready/Approved, Implementing/Executing, and Shipped
states. Tracker text is data. Local decisions use the common source-authority
policy; each remote action uses a distinct confirmation and a pending receipt
before the fake call.

## Linear

**Fixture inputs:** `linear-default/1.0`, fixed `https://api.linear.app/graphql`
destination, one normalized source-field change, and confirmed trace-link,
pull-request-link, display-status, comment, and closure actions.

**Observed route and output:** the registry selected `linear-refresh` for the
exact profile. Draft and accepted-state fixtures used the shared reviewed local
matrix; executing states refused local mutation. Fake GraphQL calls used only
`commentCreate`, `attachmentCreate`, and `issueUpdate`; every write had a
pending then succeeded/failed receipt and no automatic retry.

**Run/session boundary:** one local pytest process for the Linear skill. The
runner used fake HTTP responses and no environment credential lookup.

## GitHub

**Fixture inputs:** `github-default/1.0`, trusted host `github.com`, trusted
repository `example-org/example-repo`, issue `101`, instruction-shaped comment
text, and one confirmation per declared coordination action.

**Observed route and output:** the registry selected `github-refresh`. The
processor produced fixed-host `gh issue` argv lists with shell execution
disabled; comment and link text stayed on stdin. Tracker-selected host,
repository, Issue-body rewrite, missing confirmation, reused confirmation, and
receipt failure all recorded zero fake command calls.

**Run/session boundary:** one local pytest process with an injected command
runner. The real `gh` executable was not invoked.

## Jira

**Fixture inputs:** `jira-default/1.0`, fixed
`https://tracker.example.test`, pinned public fixture address, guarded token
client, and confirmed comment, display-status, and closure actions. A separate
fixture used SSO-cookie authentication.

**Observed route and output:** the registry selected `jira-refresh`. The token
fixtures called only `add_comment` or `transition_issue`, persisted pending and
terminal receipts, and made one attempt. SSO-cookie non-GET/HEAD fixtures,
including the existing raw-call path, refused before the fake transport
recorded a request.

**Run/session boundary:** isolated local pytest processes for the refresh,
intake-policy, and SSO client fixtures. No Jira credentials or live client were
used.

## Jira Align

**Fixture inputs:** `jira-align-default/1.0`, fixed
`https://portfolio-tracker.example.test`, pinned public fixture address, and
the same local lifecycle matrix.

**Observed route and output:** the registry selected `jira-align-refresh` for
acquisition and reviewed local comparison. The profile declared no remote
write-back actions. A requested requirement-body or comment action returned
`unsupported_capability` before payload construction and with zero fake
transport calls.

**Run/session boundary:** one isolated local pytest process. No Jira Align
credentials, generic update method, or live request were used.

## Reproduce the no-write checks

Run each command from the repository root. They use only local fixtures:

```bash
env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider packs/linear/tests/skills/linear/ tests/roster/test_linear_refresh_processor.py -q
env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests/roster/test_github_refresh_processor.py -q
env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests/roster/test_jira_refresh_processor.py packs/atlassian/tests/skills/jira/test_intake_policy.py packs/atlassian/tests/skills/jira/test_sso_client.py -q
env PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests/roster/test_jira_align_refresh_processor.py packs/atlassian/tests/skills/jira-align/test_jira_align_intake_policy.py -q
```
