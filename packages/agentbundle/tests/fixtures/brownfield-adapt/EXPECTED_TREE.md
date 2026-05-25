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

`DESIGN.md` (top-level) is a class-3 surface: an off-canonical
document the skill should propose moving / merging into the canonical
`docs/CHARTER.md`. The CLI's `adapt` ignores it (no marker, not in
state); it remains on disk byte-identical after a class-1 run.
Seeded for the manual QA matrix's class-3 (rows 12–14) Claude-
simulated captures; not consumed by any automated test.

`docs/howto/getting-started.md` (adopter-original) and
`docs/guides/how-to/index.md` (diátaxis-projection) are the class-4
surface: two overlapping how-to homes the skill should propose
consolidating. Filenames deliberately differ so the consolidation
proposal doesn't require a collision-handling sub-protocol (which
SKILL.md doesn't yet specify). Neither carries a marker; both
remain byte-identical after a class-1 run. Seeded for the manual
QA matrix's class-4 (rows 15–16) Claude-simulated captures; not
consumed by any automated test.

## User scope (synthetic)

`tests/fixtures/brownfield-adapt-user-home/.agentbundle/` plumbs the
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
