# Falsifiability record

Every assertion this change adds or relocates, the mutation that makes it fail,
and the positive control. AC8 requires this record; it exists so the evidence is
reproducible rather than asserted.

## Python — `tools/test_guide_ledger_integrity.py`

The mutations are **encoded as a test**, not run by hand, so they re-run in CI:
`test_each_rule_is_falsifiable` applies each one to a fresh `copy.deepcopy` of
the parsed ledger and asserts the violation substring only that rule emits.

Each case asserts its own substring rather than merely that some violation came
back. An earlier revision asserted only non-emptiness, and three rules —
digest format, identity uniqueness, anchor uniqueness — were **not** killed by
it: each of their mutations also perturbs a `(path, line, content_sha256)`
tuple, so `"ledger identities drifted from the frozen baseline"` fired for them
regardless, and any of the three rules could have been deleted with the suite
still green.

| Rule | Mutation | Asserted violation |
| --- | --- | --- |
| `item` values are `1..N` in order | set row 1's `item` to `999` | `item numbers are not 1..N in order` |
| Row carries exactly the eight fields (missing) | delete row 1's `reason` | `field set is not the recorded eight` |
| Row carries exactly the eight fields (extra) | add `unexpected` to row 1 | `field set is not the recorded eight` |
| `status` is terminal | set row 1's `status` to `pending` | `is not terminal` |
| `classification` is allowed | set row 1's `classification` to `warning` | `is not allowed` |
| `reason` is non-empty | set row 1's `reason` to whitespace | `reason is empty` |
| `anchor` is non-empty | set row 1's `anchor` to `""` | `anchor is empty` |
| `content_sha256` is a digest | set row 1's to `not-a-digest` | `is not a sha256 digest` |
| Identity triples are unique | copy row 1's triple onto row 2 | `duplicate (path, line, content_sha256) identities` |
| Anchors are unique per guide | copy row 1's path and anchor onto row 2 | `anchors are not unique within a guide` |
| A row missing an identity field is a violation, not a crash | delete row 1's `path` | `field set is not the recorded eight` |
| Ledger matches the frozen baseline | set baseline row 1's digest to zeroes | `drifted from the frozen baseline` |

**Positive control:** `test_the_frozen_ledger_is_self_consistent` runs
`check_ledger` over the unmutated tracked files and asserts no violations.

**Deletion proof**, run once by hand to confirm the substring assertions close
the hole the earlier revision left. Removing each rule from `check_ledger` and
re-running:

| Rule removed | Result |
| --- | --- |
| digest format | `FAILED test_each_rule_is_falsifiable` |
| identity uniqueness | `FAILED test_each_rule_is_falsifiable` |
| anchor uniqueness | `FAILED test_each_rule_is_falsifiable` |

All three passed before the substring assertions were added. The file was
restored from a copy afterwards and `git diff` confirmed no residue.

## TypeScript — `web/src/test/rendered-output.test.ts`

Run with `npm test --prefix web` against a full build
(`python3 tools/build-site.py && npm run build --prefix web && npm run build --prefix docs-site`).
Absent that build the suite skips, and a skip is not a pass.

| Assertion | Mutation | Observed |
| --- | --- | --- |
| Built blockquotes match the source count | append `> Temporary mutation probe.` to `guides/core/tutorials/your-first-workspace.md` | `0 built blockquotes for 1 in source` |
| Built asides match the source count **per type** | change one `:::note` to `:::tip`, holding the total at its original value | `2 built note asides for 1 in source` **and** `0 built tip asides for 1 in source` |

The second mutation is why the comparison is per type. A total-only comparison
stays green through a type flip, and per-type matching is what the deleted
ledger-row test provided.

**Positive control:** with both mutations reverted, 18 files / 129 tests pass.

**Counter-factual for the aside-body skip.** `sourceCallouts` ignores quote
markers inside a `:::` aside body, because the built-side comparison filters out
blockquotes nested in an aside. To show that guard is load-bearing rather than
decorative, a quoted line was added inside an existing `:::note` body:

| Code | Result |
| --- | --- |
| with the aside-body skip | 129 passed — no false failure |
| with the skip removed | `0 built blockquotes for 1 in source` on a guide with no defect |

Both the source mutation and the code revert were undone, and `git status`
confirmed a clean tree.
