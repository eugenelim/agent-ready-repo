---
title: Start a project
summary: Get a new or existing repository ready for your agent and find the first piece of work.
pack: core
uses: [core, architect]
kind: how-to
---

# Start a project

Tell your agent whether you are starting from an idea or from an existing repository.

## Start from an idea

For a new project, ask your agent to run `init-project`:

```text
Start a new project: a URL shortener service. Here is the one-paragraph idea: ...
```

The agent checks the idea is worth a repository, writes a first brief, records your stack choice as a decision record and an architecture reference, and drafts the first small spec. [Idea to a walking skeleton](../tutorials/start-a-new-project.md) walks through it.

## Bring in an existing repository

For a repository that already has code, ask your agent to check how ready it is:

```text
Run adapt-to-project and tell me what is missing for agents to work here.
```

The agent reads the repository and reports gaps in its agent guidance without changing anything. [Adapt a repository](adapt-to-project.md) covers acting on the report.

To also understand the architecture you inherited, ask:

```text
Assess the architecture of this repository and give me an action plan.
```

The `architect-assess` skill writes a current-state model, the weak spots, and an ordered action plan. [Assess a repository](../../architect/how-to/assess-a-repository.md) shows how to read it.

## Find your first piece of work

Ask your agent where the planned work stands:

```text
Show me the workspace status and help me choose my first ready work item.
```

The agent reads `workspace.toml`, the file where the repository tracks planned work, and lists what is ready to start and what is blocked and why. [Orient at the start of a session](orient-at-session-start.md) explains each part of that report.

Next, [connect your tracker](../../_shared/how-to/choose-a-tracker-integration.md) if your team plans work elsewhere.
