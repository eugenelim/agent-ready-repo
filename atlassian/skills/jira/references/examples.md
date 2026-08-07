# jira — extended examples

The three canonical examples (JQL search, create-issue, transition) live
in `SKILL.md`. Everything else lives here. Load this file when the user
asks for a flow that isn't on the dispatch table in the SKILL.

```bash
# Who am I?
python scripts/jira.py whoami

# One issue, just the basics
python scripts/jira.py get-issue PROJ-123 \
  --fields "summary,status,assignee,priority"

# Fetch with renderedFields and changelog expanded
python scripts/jira.py get-issue PROJ-123 \
  --expand "renderedFields,changelog,transitions"

# Partial update: change summary and add labels
python scripts/jira.py update-issue PROJ-123 \
  --field summary="Onboarding revamp v2" \
  --field 'labels=["urgent","onboarding"]'

# List the available transitions for an issue
python scripts/jira.py list-transitions PROJ-123

# Add a comment
python scripts/jira.py comment PROJ-123 --body "Pushed the fix in #4567."

# Upload a screenshot
python scripts/jira.py attach PROJ-123 --file ./screenshot.png

# Fetch a project
python scripts/jira.py get-project PROJ

# Get every project, streamed to disk
python scripts/jira.py list-projects --format jsonl --output projects.jsonl

# Look up a Cloud user by email (returns accountId)
python scripts/jira.py list-users --query ada@example.com

# Endpoint not wrapped by a subcommand (e.g. worklog on a specific issue)
python scripts/jira.py raw GET issue/PROJ-123/worklog

# Bulk JQL export for offline analysis
python scripts/jira.py search \
  "assignee = currentUser() AND resolution = Unresolved" \
  --fields "summary,status,priority,updated" \
  --format jsonl --output my-open-issues.jsonl

# Delete an issue (only after explicit user confirmation)
python scripts/jira.py delete-issue PROJ-123 --yes
```
