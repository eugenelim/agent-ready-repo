---
name: Agent Skill Engineering
pluginInstallable: true
scope: user
tagline: "Frame, create, update, review, and optimize portable agent skills."
skills:
  - author-or-update-agent-skill
  - review-or-optimize-agent-skill
installCommand: "agentbundle install --pack agent-skill-engineering --scope user"
docsUrl: /docs/guides/
---

Frame a portable skill before writing it, create or update it under an explicit
write boundary, or review it before making a measured optimization. Framing and
review are read-only; every write, and every optimization, needs its own
explicit authorization, and an optimization needs an observed failure or a
measured baseline before it starts.

Three governed reference topics cover trigger quality, progressive disclosure,
and deterministic script and exit contracts. When a compatible knowledge
provider is available the workflows call it explicitly; when none is, they keep
their full baseline rather than guessing. Candidate files and provider replies
are treated as untrusted evidence throughout, and authentication stays outside
the model's context.
