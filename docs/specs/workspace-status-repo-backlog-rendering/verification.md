# Verification: workspace-status repo backlog rendering

## Projected-backend manual QA

The projected `.agents` backend was invoked in both modes against the mixed
behavior-eval fixture:

```text
python3 .agents/skills/workspace-status/scripts/workspace_status.py status --root packs/core/.apm/skills/workspace-status/evals/files
python3 .agents/skills/workspace-status/scripts/workspace_status.py reconcile --root packs/core/.apm/skills/workspace-status/evals/files
```

Both commands exited successfully and returned the same ordered display
projection:

```json
{
  "repo_backlog": {
    "open": [
      {
        "needs": ["backlog:prerequisite"],
        "room": "build",
        "slug": "example-build",
        "source": "spec/example",
        "summary": "Implement the example"
      },
      {
        "entry_type": "research",
        "needs": ["backlog:example-build"],
        "room": "shape",
        "slug": "example-shape",
        "source": {"mode": "repo-origin"},
        "summary": "Research the example"
      }
    ]
  }
}
```

The corresponding rendered section is:

```text
Backlog — 2 open item(s):
- [build] example-build — Implement the example
- [shape] example-shape — Research the example
```

The projected backend was also invoked against this worktree. At verification
time, the checkout contained 135 supported open repository-backlog records;
all 135 appeared in `repo_backlog.open` in source order, while the intentionally
typed-only `shaping.top_level_backlog` remained empty. This is an observation,
not a count pinned by a test or renderer rule.

## Automated verification

- Initial focused contract reproduction: five expected `KeyError:
  'repo_backlog'` failures before production changes.
- Focused repository-backlog and renderer-wiring tests: passed after the fix.
- Full workspace-status target suite: passed.
- `make lint-ruff`: passed.
- `make lint-mypy`: passed.
- `make test`: passed.
- `make build-check`: passed, including its required policy and SAST/SCA legs.
- `FORCE=1 make build-self`: passed; `.agents` and `.claude` projections match
  the `.apm` source.

## Review routing

- Adversarial implementation review: `Clean — ready to commit.`
- Whole-spec quality review: `Clean — ready to commit.`
- Security review: not triggered. The change adds a display-only projection of
  data already parsed by the existing TOML boundary. It adds no file or network
  access, mutation path, dependency, authentication, authorization, secret,
  or executable-data handling.
- Experience review: named skip because no matching reviewer role is installed;
  manual projected-output QA above covers the user-visible text contract.
