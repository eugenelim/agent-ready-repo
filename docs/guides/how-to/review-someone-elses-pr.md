# Review a branch or PR you didn't write

The reviewer subagents don't care who wrote the diff. The work loop
points them at your own working tree, but you can point them at anyone's.

Prompt your agent:

> Use the work-loop to review branch `<their-branch>`.

Name whatever your agent can reach. A local branch always works; if the
agent has the tooling (`gh`, `glab`, an MCP server), point it straight at
a hosted change instead — "review GitHub PR #123", "review this GitLab MR".

It resolves the diff and runs `adversarial-reviewer` (plus
`security-reviewer` / `quality-engineer` if the diff warrants) — the same
REVIEW step described in
[Plan and execute non-trivial work](plan-and-execute-non-trivial-work.md).

Two things worth saying out loud:

- **No spec? Say so.** An in-flight branch usually has no spec, so the
  reviewer falls back to the spec-less self-review lens. If the branch
  *does* carry a `docs/specs/<feature>/spec.md`, name it — the reviewer
  then checks the diff against the spec instead.
- **It's a throwaway review.** You want the findings, not a loop run.
  Don't expect `state.json` or stasis detection; read the severity-tagged
  output and hand it to the author.

## See also

- [The core pack](../explanation/core-pack.md) — *why* the reviewers read
  the diff cold, and what each lens covers.
