# Manual QA matrix — adapt-to-project (AC4)

Each AC4a row declares its **verification method** per the amended
AC4a (see `spec.md`):

  - `(a) automation` — pinned by a mechanical test in
    `packages/agentbundle/tests/`.
  - `(b) grep` — pinned by a SKILL.md body grep in `tests/skills/`.
  - `(c) transcript` — inline transcript excerpt + before/after tree
    fragment captured against a real adopter session.

**No AC4a row uses method *(c)* in v1.** The amended AC4a mandates
that every row's artifact MUST exist in the repo; method *(c)*
artifacts that cannot be captured in v1 belong under AC4b. The
class-2/3/4 transition rows all require method *(c)* (LLM judgment
against an interactive adopter session); they are enumerated under
AC4b below with named triggers.

AC4b also covers user-scope LLM-judgment rows deferred per RFC-0004
§ *Drawbacks* (no user-scope-eligible pack ships in v1).

## AC4a — v1-shipped rows

### Cross-cutting

| # | Row | Method | Pinned at |
| - | --- | ------ | --------- |
| 1 | idempotency re-run | (a) automation | `tests/integration/test_brownfield_adapt_end_to_end.py::test_idempotent_re_run` runs the round-trip twice; asserts byte-identical files at both passes. |
| 2 | dirty-state-repo | (b) grep | `tests/skills/test_adapt_skill_body.py::test_body_names_dirty_state_command` pins `git status --porcelain` in the body. End-to-end transcript deferred to AC4b. |
| 3 | Tier-2 detection-repo | (b) grep | `tests/skills/test_adapt_skill_body.py::test_body_pre_flight_section_references_user_scope_state` pins Tier-2 reference in the Pre-flight section. End-to-end fixture deferred to AC4b. |
| 4 | cross-scope-restructure × decline | (b) grep | `tests/skills/test_adapt_skill_body.py::test_body_names_split_into_two_prompt` + `test_body_forbids_cross_scope_execution` pin the two contract phrases. End-to-end transcript deferred to AC4b. |

### User-scope plumbing rows (synthetic fixture)

Synthetic fixture: `packages/agentbundle/tests/fixtures/brownfield-adapt-user-home/.agent-ready/`.
All three are *plumbing* (no LLM judgment): the skill's pre-flight
reads the user-scope state and discovery files, and the CLI's
`safety.write_jailed` enforces the path-jail.

| # | Row | Method | Pinned at |
| - | --- | ------ | --------- |
| 5 | user-scope path-jail refusal | (a) automation | `safety.write_jailed` with `scope="user"` + `allowed_prefixes` is exercised by the existing safety tests (`tests/unit/test_safety.py`); a class-3 destination escaping `~/.claude/`/`~/.agent-ready/` raises `PathJailError`. |
| 6 | dirty-state-user | (b) grep | SKILL.md body's Pre-flight section documents the content-hash divergence check against `~/.agent-ready/state.toml`. End-to-end fixture deferred to AC4b. |
| 7 | Tier-2 detection-user | (b) grep | SKILL.md body's Pre-flight section names `~/.agent-ready/`, `state.toml`, and `Tier-2` (`test_body_pre_flight_section_references_user_scope_state`). |

## AC4b — deferred rows

Every row below is method *(c)* (inline transcript excerpt +
before/after tree fragment) deferred to a follow-up. The contract
surface (SKILL.md body, automation/grep tests) ships in v1; only
the LLM-judgment transcripts are deferred. Rows are numbered
continuously with AC4a so cross-references are unambiguous.

### Repo-scope class-2 transcript artifacts

The brownfield fixture seeds the surface (`brownfield-adapt/AGENTS.upstream.md`
next to `AGENTS.md`); only the inline transcripts are deferred.

| # | Deferred row | Trigger |
| - | ------------ | ------- |
| 8 | repo-scope class-2 × accept (transcript) | follow-up captures an adopter session against `brownfield-adapt/AGENTS.upstream.md` and attaches transcript + tree fragment inline |
| 9 | repo-scope class-2 × edit (transcript) | as above |
| 10 | repo-scope class-2 × skip (transcript) | as above |
| 11 | repo-scope class-2 × decline (transcript) | as above |

### Repo-scope class-3 transcript artifacts

Brownfield fixture does not seed a class-3 surface in v1.

| # | Deferred row | Trigger |
| - | ------------ | ------- |
| 12 | repo-scope class-3 × accept (end-to-end) | brownfield fixture seeds a class-3 surface (e.g., overlapping `DESIGN.md` + `docs/CHARTER.md`) and an adopter session is captured |
| 13 | repo-scope class-3 × edit (end-to-end) | as above |
| 14 | repo-scope class-3 × decline (end-to-end) | as above |

### Repo-scope class-4 transcript artifacts

| # | Deferred row | Trigger |
| - | ------------ | ------- |
| 15 | repo-scope class-4 × accept (end-to-end) | brownfield fixture seeds a class-4 surface (overlapping `docs/howto/` + `docs/guides/how-to/`) and an adopter session is captured |
| 16 | repo-scope class-4 × decline (end-to-end) | as above |

### Cross-cutting end-to-end transcripts

| # | Deferred row | Trigger |
| - | ------------ | ------- |
| 17 | dirty-state-repo (end-to-end transcript) | follow-up captures an interactive adopter session |
| 18 | Tier-2 detection-repo (end-to-end transcript) | as above |

### User-scope LLM-judgment rows

Deferred per RFC-0004 § *Drawbacks* + *Unresolved questions* — no
user-scope-eligible pack ships in v1 (all four shipped packs lock
`allowed-scopes = ["repo"]`).

**Trigger to unblock (rows 19–28):** first pack declaring
`allowed-scopes = ["user"]` lands.

| # | Deferred row | Trigger |
| - | ------------ | ------- |
| 19 | user-scope class-2 × accept | first user-scope-eligible pack |
| 20 | user-scope class-2 × edit | first user-scope-eligible pack |
| 21 | user-scope class-2 × skip | first user-scope-eligible pack |
| 22 | user-scope class-2 × decline | first user-scope-eligible pack |
| 23 | user-scope class-3 × accept | first user-scope-eligible pack |
| 24 | user-scope class-3 × edit | first user-scope-eligible pack |
| 25 | user-scope class-3 × decline | first user-scope-eligible pack |
| 26 | user-scope class-4 × accept | first user-scope-eligible pack |
| 27 | user-scope class-4 × decline | first user-scope-eligible pack |
| 28 | cross-scope-restructure × split-into-two (both halves end-to-end) | first user-scope-eligible pack |

## Notes

The *split-into-two* path is verified by SKILL.md body greps
(`test_body_names_split_into_two_prompt` +
`test_body_forbids_cross_scope_execution`); end-to-end exercise of
both halves is row 28 under AC4b.

Method *(b) grep* rows verify the SKILL.md body *teaches* the
contract; they don't replace end-to-end exercise. The AC4b
enumeration captures the deferred work so reviewers can spot
omissions in the follow-up.
