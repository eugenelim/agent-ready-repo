# Verification ledger — layout-install-sections

Execution observations. The spec and plan are pinned; this is where what was
actually run and seen is recorded.

## Probes that settled a spec assumption

**2026-09-11 — an occupied top-level name does not produce invalid TOML.**
Executing the real `_append_layout_section` against `research = 1` and against
`[[research]]\nx = 1`, with `pack_layout={"repo": {"parent": ".context/research"}}`:
both returned `["research"]\nparent = ".context/research"\n`, which parses
cleanly. The occupant was silently dropped by the off-schema branch. An earlier
draft asserted the opposite — that appending beside a scalar produced a
redeclaration error — reasoning from hand-written TOML rather than the
function's output. The real defect there is data loss, not invalid TOML; the
invalid-TOML hazard belongs to the *proposed* append design, which is why the
refusal is specified as a property of the new design rather than a repair.

**2026-09-11 — a non-UTF-8 file is absorbed by the malformed branch today.**
A layout file containing `# caf\xe9` came back byte-identical with a warning,
because `read_text` sits inside the `try`. This is why the decode stays inside
the refusal boundary: moving it out turns a warning into an uncaught traceback.

**2026-09-11 — `read_text` folds lone CR.** `b'[a]\rparent = "x"\r'` parsed and
was appended to under the shipped text-mode read. Under the byte-preserving
read it is unparseable and refused. That narrowing is reported, not silent, and
is recorded in the changelog.

## Mutation checks

Each control was verified to fail when the thing it guards is removed.

| Control | Mutation | Result |
| --- | --- | --- |
| AC10 value emitter | `_emit_basic_string` replaced with raw interpolation | 3 red (quote, newline, backslash) |
| AC13 mode preservation | `mode=existing_mode` → `mode=None` | 1 red |
| AC14 symlink probe | `is_symlink()` gated behind `exists()` | 1 red (dangling link) |
| AC14 confinement | root check disabled | 1 red (`~/.ssh`) |
| AC15 section class | class guard disabled | 1 red (`-lead`) |
| AC5 silence | table-occupied case made to report | 1 red |
| AC4 reporting | read failure made silent | 1 red |
| AC9 schema pattern | `pattern` dropped from both copies | 6 red |
| AC7 anchoring | reverted to CWD resolution | 3 red |
| AC7 user-scope half | both scopes anchored to repo root | 2 red |
| AC6 pair matching | `product-engineering` section crossed to `discovery` | 1 red |
| AC6 pair matching | `architect` base reverted without its docs | 1 red |

The AC7 user-scope mutation is the one the criterion was written for: a single
undifferentiated fix passes the repo-scope case and fails the user-scope one.

## Suites

- `packages/agentbundle/tests/unit` — 1077 passed, 1 skipped, 1 xfailed
  (with integration and conformance, 260s)
- `tests/conformance/test_pack_layout_declared_section.py` — 7 passed
- `packages/agentbundle/tests/unit/test_append_layout_section.py` — 35 passed
- `tools/test_build_site_routing.py` — 93 passed, 1 skipped

## Notes for a later reader

`agentbundle catalogue lint` reported five schema errors during T3 until the
invocation was pinned to the local package. A bare `python3 -m agentbundle`
resolves to the stale `site-packages` install, which validates against an older
schema copy. A lint verdict here means nothing unless the invocation is pinned.

## Shipping record — 2026-09-11

Every acceptance criterion ticked against a named observer that exists and
runs. 83 cases across six files; the mapping was verified mechanically rather
than by reading, and no criterion is discharged by a test that does not exist.

| AC | Observer |
| --- | --- |
| AC1 | unit append case + the end-to-end install case |
| AC2 | three preservation cases (extra key, nested table, top-level scalar) |
| AC3 | five line-ending cases including CRLF-without-terminator |
| AC4 | nine reporting rows, exercised individually |
| AC5 | three silent rows plus two ordering cases |
| AC6 | conformance pair rule + its synthetic discrimination proof + roster floor |
| AC7 | five anchoring cases across both scopes |
| AC8 | every reference doc agrees with its pack's declared base |
| AC9 | schema admission, refusal, and the character-class pattern |
| AC10 | four injection payloads that reach the emitter |
| AC11 | reporting state leaves exit status intact; marker failure still fatal |
| AC12 | mode preserved, asserted with the bytes so a no-op cannot pass |
| AC13 | symlink refused and left a link; dangling link reports |
| AC14 | out-of-root, out-of-prefix, prefix sibling, home root, in-prefix |
| AC15 | five rejected section values including the empty string |

### Remote CI, final round

All three green on the shipping head: `build-check`, `test-corpus`,
`test-roster`. Eight rounds were needed. Every failure was a real repository
rule about *membership* — publication, portability, projection, admitted
backlog kinds, pinned release surfaces — rather than the behaviour, which the
unit and mutation work had covered before the first dispatch.

### Review rounds

Contract: five rounds. Code: three. The code rounds found 4, then 11, then 1
(a nit). Round 1's severe finding was a security control this spec specified
correctly and the implementation did not honour: user-scope confinement was
the whole home rather than the adapter's write prefixes. Round 2's most
valuable finding was repair-origin — round 1 moved empty-string `section` to
the report row and left the identical clause on `output_dir` silent.

Two reported blockers were dismissed rather than repaired, each after the
premise failed under execution: that an occupied top-level name produces
invalid TOML (the occupant is silently dropped and the output parses), and
that a glob in `output_dir` collapses `git_commit` scope to the worktree (it
fails closed, matching nothing).

### What is not covered

- Concurrent installs racing on one layout file can lose the earlier append.
  Accepted, recorded in the plan and the function's docstring.
- The atomic replace carries the file's mode and nothing else: group
  ownership, ACLs, extended attributes and hard links are not preserved.
- Adopter layout files cannot be observed, so nothing here can tell whether a
  section name exists in the wild that no pack declares.
