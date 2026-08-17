# Adversarial implementation review — round 2

## Blockers

**1. Adapter validators still accept schema-forbidden secret or payload constraint names.** `contracts/jsonschema/normalized-intake.schema.json:149`

## Concerns

**2. Jira and Jira Align intake HTTP mode disables enterprise proxy handling.** `packs/atlassian/.apm/skills/jira/scripts/_client.py:477`

**3. New shipped adapter scripts omit the required UTF-8 stream guard.** `packs/AGENTS.md:125`

Each finding is accepted for implementation in the next review round.
