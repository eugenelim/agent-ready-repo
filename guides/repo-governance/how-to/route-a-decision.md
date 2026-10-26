---
title: "Route a decision"
summary: "Ask which record a decision needs, whether it is a one-way door, and whom to consult, without writing anything."
pack: repo-governance
kind: how-to
uses: [repo-governance]
---

# Route a decision

Ask your agent which record a decision needs, and it answers in one short block. It reads your existing decisions and writes nothing.

## Ask for a route

Use this when you are unsure whether to write an ADR, propose an RFC, or skip the record:

```text
Use navigate-decisions in route mode: we want to move the build to a monorepo. Which record does this need? Consult @org/platform-team and the release managers.
```

## Read the result

The agent first checks the repository for an existing decision on the topic, then replies with this block:

```text
ROUTE:
- Route: <outcome>
- Why: <one or two sentences>
- Door: <one-way | two-way> — <reason>
- Consult: <user-supplied handles and roles, or "none supplied">
- Existing decisions checked: <record identifiers, "none found", or "not checked — <reason>">
- Next: <skill or action>
```

- **Route** is one outcome from the [RFC skill's routing](new-rfc.md), such as `skip`, `reuse`, `ADR`, `PR` or `RFC`. When the outcome is `PR`, `issue` or `spec`, no decision record is needed. Build through your normal work loop, which picks its own build mode.
- **Door** says whether the decision is hard to reverse (`one-way`) or easy to reverse (`two-way`). It is advice only and never changes the route. A one-way verdict on a `skip`, `PR`, `issue` or time-bounded trial outcome is flagged so you can check it.
- **Consult** lists only the handles (such as `@user` or `@org/team`) and roles (such as "platform maintainers") you gave in the conversation. It never holds an email address. If you gave none, it says `none supplied`, and the agent asks who is affected and who has the expertise after the block.
- **Existing decisions checked** shows what the agent found. If the check could not run, it says `not checked` and why. That is not the same as finding nothing.
- **Next** names the skill or action for you to start. The agent does not start it.

## Act on it

When the route is `ADR`, [record the decision](new-adr.md). When it is `RFC`, [propose it with an RFC](new-rfc.md).
