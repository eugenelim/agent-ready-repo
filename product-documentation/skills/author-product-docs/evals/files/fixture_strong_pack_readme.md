<!-- STRONG FIXTURE: task-first pack README with correct audience routing -->
<!-- Demonstrates: outcome-led opening, natural-language starter, result preview,
     explicit read/write boundary, no skill inventory before first task, correct
     canonical sources inspected (pack.toml + skill source). -->

# Credential Brokers

Resolve credentials for your AI agent workflows without writing secrets into skill files or config — the broker intercepts at the right moment, asks once, and keeps the token in memory for the session.

## What this helps you do

- **Run credentialed skills in CI or local sessions** without hardcoding tokens
- **Rotate an expired credential** without breaking ongoing workflows
- **Audit which credentials a session has used** before it ends

## Get started

```
Set up a credential for my Jira instance
```

The agent prompts for your token once, stores it for the session, and makes it available to any skill that needs it. You can confirm at any point what credentials are active.

## How it works

The broker runs in-process. It reads the current session state and the target skill's declared requirements. It does not write your credentials anywhere on disk; they are held in memory for the session only.

Read/write boundary: reads declared skill requirements and session state. Never writes credentials to disk.

## What to do next

```
Show me which credentials this session has active
```

```
Rotate the Jira credential before running the next task
```

## Install

```bash
agentbundle install --pack credential-brokers
```

## Guides

- [How to set up a credential](../../guides/credential-brokers/how-to/set-up-a-credential.md)
- [How to rotate a credential mid-session](../../guides/credential-brokers/how-to/rotate-credential.md)
- [About the broker's in-process model](../../guides/credential-brokers/explanation/in-process-model.md)
