# Adversarial implementation review — round 1

## Blockers

**1. Normalized validation does not enforce the contract schema.** `packs/atlassian/.apm/skills/jira-brief-intake/scripts/intake_adapter.py:78`

**2. Raw tracker envelopes do not drive normalized content.** `packs/atlassian/tests/skills/jira-brief-intake/test_jira_brief_intake.py:39`

**3. Response byte budgets are checked only after unbounded buffering.** `packs/github/.apm/skills/github-brief-intake/scripts/intake_adapter.py:144`

**4. Jira and Jira Align DNS checks are not connection-pinned.** `packs/atlassian/.apm/skills/jira/scripts/_client.py:150`

**5. Linear retry backoff ignores the profile budget.** `packs/linear/.apm/skills/linear/scripts/linear.py:267`

Each finding is accepted for implementation in the next review round.
