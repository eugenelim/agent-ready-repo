# Phase 1A manual QA — portable Agent Plugins projection

- **Date:** 2026-08-25
- **Worktree:** `eugenelim/rfc92-followon`
- **Current base ref:** `0df3be711d4403afc2ca1d0f02ae033c79aff745`
- **Environment:** managed enterprise workspace; Python `os.rmdir` is denied,
  so deterministic rebuild evidence uses two independent approved temporary
  roots as prescribed by `pre-existing-enterprise-python-rmdir`.

## Real build

Both fresh-root invocations used the normal default recipe surface:

```text
PYTHONPATH=packages/agentbundle python3 -m agentbundle.build build \
  --packs-dir packs --output-dir <fresh-root>/dist
```

- **First artifact:** `/private/tmp/rfc92-phase1a.Dw19O1/dist`
- **Second artifact:** `/private/tmp/rfc92-phase1a.og3kbJ/dist`
- **Exit status:** `0` for both builds
- **Observed route:** `agent-plugins/<pack>/plugin.json` plus `skills/`
- **Eligible roster:** `atlassian`, `catalogue-curation`, `contracts`,
  `converters`, `figma`, `github`, `governance-extras`, `iac-terraform`,
  `linear`, `monorepo-extras`, `product-documentation`, `product-strategy`,
  `user-guide-diataxis`
- **Excluded roster:** `architect`, `core`, `credential-brokers`,
  `desk-research`, `experience-design`, `frontend-engineering`,
  `product-engineering`, `release-engineering`
- **Named exclusion observed:** `core` reported the complete sorted set
  `agent`, `command`, `hook-body`, `hook-wiring`, `kiro-ide-hook`.

The command prints the existing deprecation notice for the legacy module entry
point and directs maintainers to `agentbundle catalogue build --root .`; the
recipe behavior exercised here is the same `run_default_build` implementation.

After the first adversarial review repair, the same normal build was repeated
from the current worktree into
`/private/tmp/rfc92-phase1a-review.7C6UdQ/dist`. It exited `0`, retained the
13-pack portable roster, and emitted the same eight complete exclusion
diagnostics. This post-repair build exercises the confined discovery boundary,
immediate-skill-directory projection, and reverse-domain extension-directory
preflight added for AC6, AC8, and AC9.

After the second adversarial repair, the same fresh-root build was repeated at
`/private/tmp/rfc92-phase1a-review2.PhMxZp/dist`. It also exited `0` with the
same eligible and excluded rosters, exercising route-sanitized discovery and
the declared-extension-file refusal without changing valid catalogue output.

After the specialist security and quality repair, the normal build was repeated
at `/private/tmp/rfc92-phase1a-specialist-20260826/dist`. It exited `0` with the
same 13 eligible packs and the exact same eight exclusion diagnostics. This
build exercises the disk-backed all-pack source snapshot, traversal-time file
cap, supported-keyword gate for active extension schemas, and mode-aware render
contract without adding a build-time network dependency.

After the fourth adversarial repair, the normal build was repeated once more at
`/private/tmp/rfc92-phase1a-final-20260826/dist`. It exited `0` with the same
rosters and diagnostics. The final repair samples executable mode from the same
confined descriptor as source bytes and sanitizes missing/unreadable active
extension-schema failures.

After the final specialist adjudications, the normal build was repeated at
`/private/tmp/rfc92-phase1a-complete-20260826-b/dist`. It exited `0` with the
same rosters and diagnostics. This build includes the route-scoped metadata
confinement fix, traversal-before-serialization extension-depth enforcement,
and sanitized rejection of dangling agent-plugin output symlinks.

After the final whole-spec review repair, the normal build was repeated at
`/private/tmp/rfc92-phase1a-complete-20260826-c/dist`. It exited `0` with the
same rosters and diagnostics. This build includes sanitized handling for deeply
nested unused pack metadata and keeps the legacy `--emit-install-routes`
renderer pinned to its pre-Phase-1A Claude, APM, and marketplace recipes.

## Validation and determinism

A read-only inventory comparison covered every relative file path, SHA-256 of
its bytes, and executable/non-executable flag in both fresh route roots.

- **Inventoried files:** 404
- **Consecutive inventories:** byte- and mode-identical
- **Canonical inventory SHA-256:**
  `1a1cc5374c90bf507beb5900f54489bfaf85638b80014c66200e67078f7de566`
- **Manifest validation:** all 13 root `plugin.json` files validated against
  `contracts/vendor/agent-plugins/1.0.0/plugin.schema.json`
- **Schema source:** local vendored bytes only; no build-time network access

## Scope observed

The artifact contains portable root manifests and canonical skills. No
`mcp.json`, seeds, adaptation state, publication automation, client install, or
runtime verification was exercised or claimed. The MCP schema is present only
as the packaged, provenance-pinned Phase 1B contract input.

## Local limitation

The managed runtime's known Python `os.rmdir` denial affects the exact six
cleanup-sensitive nodes recorded by the workspace backlog:

- `test_agent_plugin_projection_is_deterministic_and_removes_stale_files`
- `test_default_build_emits_complete_agent_plugin_roster`
- `EndToEndBuildTests::test_default_build_produces_expected_shape`
- `EndToEndBuildTests::test_plain_build_does_not_invoke_self_host_recipes`
- `CheckCommandTests::test_make_build_check_on_a_clean_pre_projected_tree_exits_zero`
- `ScaffoldCommandTests::test_scaffold_copies_seeds_into_output`

The production cleanup and tests remain unchanged; CI or a supported profile
owns those exact cases. The unaffected selected suite passed locally with those
nodes explicitly deselected. A one-time mode-preserving render design probe
also confirmed that directory replacement is denied in the managed temporary
area; the implementation therefore uses an unnamed regular-file spool and does
not depend on directory replacement or cleanup.

The new direct-install regression assertion in
`test_path_jail_probe_refused` is also left to CI: its unchanged autouse
catalogue fixture reached `tests/_support.py::materialize_catalogue` and failed
at `Path.rmdir()` before the test body. A direct CLI smoke reached the corrected
legacy recipe selection and then hit the same `TemporaryDirectory` cleanup
denial before installation writes. Neither path was retried or weakened.
