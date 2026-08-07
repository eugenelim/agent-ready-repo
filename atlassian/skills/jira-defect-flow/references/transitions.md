# Jira transition names you'll see in the wild

`jira.py list-transitions <KEY>` returns the transitions actually
available from the issue's current state. The names below are common
shapes, not a contract — always confirm via `list-transitions` before
applying.

## Common defect workflows

### Simple three-state

```
Open --[Start Progress]--> In Progress --[Resolve]--> Resolved --[Close]--> Closed
                                       <--[Reopen]---
```

### Standard with review + QA

```
To Do --[Start work]--> In Progress --[Submit for review]--> In Review
                                                              |
                                  --[Approve]-----------------+
                                  v
                              Ready for QA --[Pass]--> Done
                                           --[Fail]--> In Progress (reopened)
```

### Enterprise (with explicit dev / staging gates)

```
Backlog -> In Analysis -> In Progress -> Code Review -> Ready for Dev
       -> Dev Deployed -> Ready for QA -> In QA -> Ready for UAT
       -> UAT Verified -> Ready for Prod -> Done
```

## Stage → transition mapping (defect-flow stages)

| Defect-flow stage | Transition you typically apply | Common names |
|---|---|---|
| 2 (start work) | "Start Progress" | `In Progress`, `Start Work`, `In Development` |
| 7 (PR opened) | "Move to review" | `In Review`, `Code Review`, `Ready for Review`, `In QA Review` |
| 8 (deployed to dev) | "Mark dev-deployed" | `Ready for QA`, `Dev Deployed`, `Ready for Test`, `In QA` |
| — (not in scope) | "Close" | `Done`, `Closed`, `Resolved` — leave this to QA |

## Don't hardcode

These names vary per project, per board, and sometimes per issue type
inside the same project. Always:

1. `jira.py list-transitions $KEY` to see what's available from the
   current state.
2. Pick by name from the returned list (or by `id` if names collide).
3. Confirm with the user when the name is ambiguous.

If `list-transitions` returns an empty array, the current user lacks
permission to move the ticket. Surface this — do not try to backdoor
via `update-issue`.
