# Plan: spec-ac-gate-and-fixture-domains

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` + its projection.
- `packs/core/tests/skills/work-loop/test_lint_spec_status.py`.
- 18 `docs/specs/*/spec.md` headings.
- `packs/converters/tests/skills/msg-to-markdown/**` (4 files).
- `workspace.toml`.

**What demonstrates done**
- Mutation test on the matcher; full converter suite; `make ci`.

**What I am NOT changing**
- The missing-section policy (AC5 records it).
- Any spec's actual criteria — headings only.
- The parity gate's design; the oracle is regenerated, not redefined.

## Declined patterns

- **Tempted:** hand-edit `msgreader_baseline.json`, since the rename is
  obviously mechanical. **Declined:** the file's value is that a *different*
  codebase produced it. Hand-editing turns an independent cross-check into a
  restatement of our own reader's output, and nothing would have flagged that.
  Regenerated against real Node instead; the byte-identical result confirms the
  assumption rather than substituting for it.
- **Tempted:** map both `corp.com` and `x.com` to `example.com`. **Declined:**
  they are distinct in fixtures that exercise cross-domain recipients; collapsing
  them would weaken those cases invisibly.
- **Tempted:** also fail loudly on a spec with no Acceptance-Criteria section,
  since it is the same vacuous pass. **Declined:** that is a policy call about
  what a spec must contain, not a regex bug, and some specs legitimately have
  none. Split out.
- **Tempted:** skip normalising the 18 headings once the matcher was tolerant.
  **Declined:** cheap, and it stops the next author seeing two forms in the
  corpus and guessing which is wanted.

## Anchor-test sweep

- `test_lint_spec_status.py` — extended (AC3).
- `test_parity.py` reads `msgreader_baseline.json` — regenerated (AC7).
- `.claude/skills/**` projection is content-pinned by `build-self` — resynced (AC8).

## Verification log

- **AC1/AC3** mutation-verified: case-sensitive matcher fails the sentence-case and
  upper-case arms; restoring passes all 5. Full file: 31 passed.
- **AC2** measured before changing: 18 affected specs, 0 unchecked ACs among them.
- **AC4** `grep -rl '^## Acceptance criteria' docs/specs/*/spec.md` -> 0; canonical -> 323.
- **AC6/AC7** 56 replacements across 4 files; baseline regenerated with real Node
  msgreader (v26.4.0) and byte-identical to the rename; converter suite 53 passed.
- **AC8** `make build-self FORCE=1`; source and projection byte-identical.
- **REVIEW** `adversarial-reviewer` = named skip (session instruction prohibits
  subagent dispatch). Self-reviewed against the spec-less checklist.
