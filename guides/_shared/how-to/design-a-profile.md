---
title: "Design a profile"
summary: "Let one kind of person install exactly the packs they need in one command."
pack: _shared
kind: how-to
---

# Design a profile

Let one kind of person, such as a solution architect, install exactly the packs they use together in one command, by defining a profile.

## Write the manifest

Create `profiles/<name>.toml`. It holds one scope, a description, and the packs, with each pack listed after the packs it depends on:

```toml
scope = "user"
description = "Solution architect's portable toolkit: architecture design, desk research, and contract-driven specs."

[[packs]]
pack = "architect"

[[packs]]
pack = "desk-research"

[[packs]]
pack = "contracts"
```

Use `user` scope for tools that follow a person across repositories and `repo` for tools that write into a repository. A profile cannot mix scopes, and it should list only packs the person reaches for together, repeatedly. [Profile design tests](../reference/profile-design-tests.md) gives the four tests and worked examples.

## Lint it

Check that every pack allows the scope and the order is right:

```bash
agentbundle catalogue lint --root .
```

The output names the failing rule and the pack that caused it.

## Install it

Install the profile from your catalogue:

```bash
agentbundle install --profile solution-architect <catalogue>
```

Next, [build a pack](build-an-org-stack-pack.md) for your organization's own standards.
