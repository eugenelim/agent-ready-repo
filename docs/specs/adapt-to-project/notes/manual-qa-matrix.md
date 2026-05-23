# Manual QA matrix — adapt-to-project (AC4)

Each AC4a row declares its **verification method** per the amended
AC4a (see `spec.md`):

  - `(a) automation` — pinned by a mechanical test in
    `packages/agentbundle/tests/`.
  - `(b) grep` — pinned by a SKILL.md body grep in `tests/skills/`.
  - `(c) transcript` — inline transcript excerpt + before/after tree
    fragment captured against a real adopter session.

Method *(c)* is required for class-2 transition rows against the
brownfield fixture (the only exercisable LLM-judgment surface in v1
— `AGENTS.upstream.md` next to `AGENTS.md`). Class-3/4 transition
rows whose brownfield surface requires a v1.1 fixture are deferred
to AC4b under named triggers.

AC4b rows are deferred per RFC-0004 § *Drawbacks* (no user-scope-
eligible pack ships in v1).

## AC4a — exercisable rows

### Repo-scope class-2 (`.upstream.<ext>` companion merge)

Fixture: `packages/agentbundle/tests/fixtures/brownfield-adapt/AGENTS.upstream.md`
next to `AGENTS.md`. Method *(c)* required (LLM judgment surface
exists in v1).

| # | Transition | Method | Status |
| - | ---------- | ------ | ------ |
| 1 | accept     | (c) transcript | pending — captured against an interactive adopter session; transcript + tree fragment attached out-of-band with the session recording |
| 2 | edit       | (c) transcript | pending — as above |
| 3 | skip       | (c) transcript | pending — as above |
| 4 | decline    | (c) transcript | pending — as above |

These four rows are the hard *(c)*-method gate. The PR does not
attach the transcripts inline; they are recorded out-of-band with
each adopter session. **Reviewer note:** if this is unacceptable for
v1 sign-off, hold the merge and require inline capture.

### Repo-scope class-3 (discovery + restructuring)

| # | Transition | Method | Status |
| - | ---------- | ------ | ------ |
| 1 | accept     | (c) transcript — deferred to AC4b | trigger: brownfield fixture with a class-3 surface (e.g., a seeded `DESIGN.md` overlapping `docs/CHARTER.md`) lands |
| 2 | edit       | (c) transcript — deferred to AC4b | as above |
| 3 | decline    | (c) transcript — deferred to AC4b | as above |

v1 brownfield fixture does not seed a class-3 surface. The skill body
documents the contract; method *(b)* greps pin the per-finding
accept/edit/decline language under
`packages/agentbundle/tests/skills/test_adapt_skill_body.py` —
which proves the SKILL.md body teaches the contract — but the
end-to-end exercise is deferred to AC4b.

### Repo-scope class-4 (within-layout consolidation)

| # | Transition | Method | Status |
| - | ---------- | ------ | ------ |
| 1 | accept     | (c) transcript — deferred to AC4b | trigger: brownfield fixture with a class-4 surface (overlapping `docs/howto/` + `docs/guides/how-to/`) lands |
| 2 | decline    | (c) transcript — deferred to AC4b | as above |

### Cross-cutting

| # | Row | Method | Pinned at |
| - | --- | ------ | --------- |
| 1 | dirty-state-repo | (b) grep | `tests/skills/test_adapt_skill_body.py::test_body_names_dirty_state_command` pins `git status --porcelain` in the body. End-to-end transcript deferred to AC4b. |
| 2 | idempotency re-run | (a) automation | `tests/integration/test_brownfield_adapt_end_to_end.py::test_idempotent_re_run` runs the round-trip twice; asserts byte-identical files at both passes. |
| 3 | Tier-2 detection-repo | (b) grep | `tests/skills/test_adapt_skill_body.py::test_body_pre_flight_section_references_user_scope_state` pins Tier-2 reference in the Pre-flight section. End-to-end fixture deferred to AC4b. |
| 4 | cross-scope-restructure × decline | (b) grep | `tests/skills/test_adapt_skill_body.py::test_body_names_split_into_two_prompt` + `test_body_forbids_cross_scope_execution` pin the two contract phrases. End-to-end transcript deferred to AC4b. |

### User-scope plumbing rows (synthetic fixture)

Synthetic fixture: `packages/agentbundle/tests/fixtures/brownfield-adapt-user-home/.agent-ready/`.
All three are *plumbing* (no LLM judgment): the skill's pre-flight
reads the user-scope state and discovery files, and the CLI's
`safety.write_jailed` enforces the path-jail.

| # | Row | Method | Pinned at |
| - | --- | ------ | --------- |
| 1 | dirty-state-user | (b) grep | SKILL.md body's Pre-flight section documents the content-hash divergence check against `~/.agent-ready/state.toml`. End-to-end fixture deferred to AC4b. |
| 2 | Tier-2 detection-user | (b) grep | SKILL.md body's Pre-flight section names `~/.agent-ready/`, `state.toml`, and `Tier-2` (test_body_pre_flight_section_references_user_scope_state). |
| 3 | user-scope path-jail refusal | (a) automation | `safety.write_jailed` with `scope="user"` + `allowed_prefixes` is exercised by the existing safety tests (`tests/unit/test_safety.py`); a class-3 destination escaping `~/.claude/`/`~/.agent-ready/` raises `PathJailError`. |

## AC4b — deferred rows

User-scope class-2/3/4 LLM-judgment rows are deferred until a pack
declaring `allowed-scopes = ["user"]` ships (no such pack in v1; all
four shipped packs lock `allowed-scopes = ["repo"]`). Per RFC-0004 §
*Drawbacks* + *Unresolved questions* — APM/Claude-plugins adapter
parity lands later.

**Trigger to unblock:** first pack declaring `allowed-scopes =
["user"]` lands.

Additional v1 deferrals (transcript captures requiring a fixture
surface that v1 doesn't seed):

| # | Deferred row | Trigger |
| - | ------------ | ------- |
| 1–4 | user-scope class-2 × {accept, edit, skip, decline} | first user-scope-eligible pack |
| 5–7 | user-scope class-3 × {accept, edit, decline} | first user-scope-eligible pack |
| 8–9 | user-scope class-4 × {accept, decline} | first user-scope-eligible pack |
| 10 | cross-scope-restructure × split-into-two (both halves end-to-end) | first user-scope-eligible pack |
| 11–13 | repo-scope class-3 × {accept, edit, decline} (end-to-end) | brownfield fixture seeds a class-3 surface |
| 14–15 | repo-scope class-4 × {accept, decline} (end-to-end) | brownfield fixture seeds a class-4 surface |
| 16 | dirty-state-repo (end-to-end transcript) | follow-up captures an interactive adopter session |
| 17 | Tier-2 detection-repo (end-to-end transcript) | as above |
| 18–21 | repo-scope class-2 × {accept, edit, skip, decline} (transcript artifacts inline) | follow-up captures and attaches the four transcripts |

Rows 18–21 are the strict *(c)*-method requirement for class-2;
they're listed under AC4b only to track the artifact-attachment work.
The contract surface (the SKILL.md body) is fully shipped in v1.

## Notes

The *split-into-two* path (cross-cutting row 4) is verified by
SKILL.md body greps; end-to-end exercise of both halves is deferred
to AC4b (row 10) under the user-scope-pack trigger.

Method *(b) grep* rows verify the SKILL.md body *teaches* the
contract; they don't replace end-to-end exercise. The AC4b
enumeration captures the deferred work so reviewers can spot
omissions.
