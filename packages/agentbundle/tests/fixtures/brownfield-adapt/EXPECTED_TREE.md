# Brownfield-adapt fixture — expected post-adaptation tree

## Repo scope

After `agentbundle adapt --values-from <repo>/.adapt-discovery.toml`
against the seeded `[markers]` (`project-name = "myproject"`,
`owner = "octocat"`, `repo-url = "https://example.com/myproject"`),
the following files should match
`packages/agentbundle/tests/fixtures/brownfield-adapt-expected/`
byte-for-byte:

  - `AGENTS.md` — markers substituted.
  - `docs/CHARTER.md` — markers substituted.

`AGENTS.upstream.md` is a class-2 companion: the CLI does not delete
or merge it (that's the skill's class-2 work, exercised in the manual
QA matrix). It remains on disk after a class-1 `adapt` run.

## User scope (synthetic)

`tests/fixtures/brownfield-adapt-user-home/.agent-ready/` plumbs the
user-scope dot-directory:

  - `state.toml` — v0.2 schema with no installed user-scope packs
    (placeholder for AC4a's *user-scope path-jail refusal* and
    *Tier-2 detection-user* rows).
  - `.adapt-discovery.toml` — canonical user-scope shape:
    `discovery-schema-version = "0.1"` plus a single
    `[[findings.declined]]` entry. **No `[markers]`** (refused at
    user scope per RFC-0004).

Used by:
  - T11: `test_class_one_end_to_end` and `test_idempotent_re_run`
    against the repo-scope tree (markers are repo-only).
  - AC4a synthetic user-scope rows: dirty-state-user, Tier-2-user,
    user-scope path-jail refusal.
