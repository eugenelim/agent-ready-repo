# Plan: install-symlink-hardening

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `packages/agentbundle/agentbundle/render.py` — the `_collect_tree` skip.
- `packages/agentbundle/tests/unit/test_collect_tree_symlinks.py` (new).
- Version + both changelogs; `workspace.toml`.

**What demonstrates done**
- Three tests covering absolute, relative and directory links; full agentbundle
  suite; `make ci`.

**What I am NOT changing**
- Any adapter's symlink policy — see the reversal below.
- `build/main.py`'s `.apm`/`seeds` copytrees.

## Security reasoning (inline — `security-reviewer` is a named skip)

- **`path-and-file` / CWE-59 (link following), CWE-22.** The primitive is a
  symlink whose relpath is innocent while its target is not, so every
  path-confinement check upstream passes. The bytes only become a file at
  `_collect_tree`'s `read_bytes()`, which is therefore the correct choke point:
  it covers absolute links, relative traversal, and symlinked directories in one
  place, where a per-adapter filter would have to catch each shape separately.
- **`supply-chain`.** Threat actor is an untrusted catalogue, the documented
  model for the install path. First-party packs are unaffected — `find packs
  -type l` returns zero and `lint_packs.py:482` rejects any pack shipping one.
- **Failure mode.** Silently dropping a member is weaker than refusing the pack.
  That refusal is `lint_pack` gating on the install path, left as the sibling
  entry's remaining scope.

## Reversal record

The first implementation followed the backlog entry: lift the strict
skip-every-symlink helper into `direct_directory.py`, adopt it in all six
adapters. It was **reverted**, because
`tests/build_pipeline/test_adapter_codex.py::test_symlink_pass_through` failed
and led to `docs/specs/codex-native-skills/spec.md`, which states pass-through
*is* the safety invariant.

Two corrections fall out of that, both recorded rather than acted on:

1. The entry's premise is inverted. `copilot`, `gemini` and `kiro` already drop
   every symlink, so the four strict adapters are the ones diverging from the
   spec — not the two permissive ones.
2. My own earlier claim that "the full agentbundle suite is green" was wrong; the
   codex pass-through test was failing. CI caught it. The lesson is in the anchor
   sweep below.

## Anchor-test sweep — corrected

The first sweep searched for tests pinning the adapters' callbacks **by name**
and found none, and I concluded the behaviour was unpinned. It was pinned by
*behaviour*: `test_symlink_pass_through` asserts the projected artifact is a
symlink, naming no callback at all. Grep the behaviour a change alters, not only
the identifiers it renames.

## Declined patterns

- **Tempted:** update `test_symlink_pass_through` to expect the new strict
  behaviour, since I had already written the consolidation. **Declined:** that
  test encodes a stated spec invariant. Changing a security invariant because my
  patch disagreed with it is backwards; the spec decides, or it gets amended
  deliberately by someone who can rule on it.
- **Tempted:** keep the shared-helper consolidation and apply it only to the four
  already-strict adapters. **Declined:** it would freeze the divergence into a
  shared module and make the eventual ruling harder to apply.

## Verification log

- **AC1/AC3** 3 tests in `test_collect_tree_symlinks.py` green.
- **AC2** adapters and `direct_directory.py` restored to `origin/main`;
  `test_adapter_codex.py` 27 passed.
- **AC5** 0.36.0 -> 0.36.1; roster release-surface test passes.
- **REVIEW** `adversarial-reviewer` and `security-reviewer` = named skips.
  Security reasoning applied inline above.
