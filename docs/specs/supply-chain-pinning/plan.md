# Plan: supply-chain-pinning

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `.github/workflows/*.yml` (10 files), `.github/zizmor.yml`, `Makefile`,
  `workspace.toml`.

**What demonstrates done**
- The AC1 grep returns nothing; the diff is 38-for-38; `pip-audit` exits 0; and
  CI on this PR executes every pinned action.

**What I am NOT changing**
- Any workflow's logic, triggers, permissions, or job graph.
- Which actions are used — only how they are referenced.

## Security reasoning (inline — `security-reviewer` is a named skip)

- **`supply-chain`.** Tag pinning is trust-on-first-use: `@v4` is a mutable
  pointer, so a re-tagged release changes what executes with no diff anywhere in
  this repo. SHA pinning removes the mutation entirely.
- **The branch ref is the sharp edge.** `@release/v1` is not a tag at all but a
  *branch*, so it moves on every upstream merge — and it sat on the job holding a
  PyPI publishing token, where the blast radius is publishing a compromised
  artifact under our name. Its sibling workflow already pinned the same action,
  which means the exposure was an inconsistency rather than a considered choice.
- **What pinning does not buy.** A pinned SHA is immutable, not *trusted*: it
  freezes the code, it does not review it. Bumps still need reading. It also
  freezes security fixes, which is the real cost — hence AC3's tag comments, so
  the version is legible to a human and to Dependabot.
- **`config-misconfig`.** Retiring the zizmor ignore list matters as much as the
  pinning: a suppression that outlives its reason silently downgrades the audit
  for every workflow added later.

## Declined patterns

- **Tempted:** keep the zizmor ignore list "just in case a new workflow needs
  it". **Declined:** that is exactly how the list grew to 13 entries. The file
  now documents the two-line pinning recipe instead.
- **Tempted:** pin to the newest release of each action rather than the SHA the
  current tag points at. **Declined:** this change is about immutability, not
  upgrades. Bundling a version bump would make any CI failure ambiguous between
  the two.
- **Tempted:** hand-write the SHAs from the ones already present in the repo.
  **Declined:** resolved each from the GitHub API instead. That the eight
  already-pinned actions matched is a *check*, not the source.

## Anchor-test sweep

- `lint-ci-parity.py` reads `build-check.yml` step bodies; only `uses:` lines
  changed, and no step was added or removed, so its per-step roster is unaffected
  (confirmed by running it).
- `tools/test-build-check-windows-workflow.py` asserts on that workflow's shape.
- No test pins an action reference string.

## Verification log

- **AC1** grep for a non-40-hex `uses:` -> nothing.
- **AC2** `release-credbroker.yml` now matches `release-agentbundle.yml`'s pin.
- **AC4** SHAs resolved via `gh api repos/<a>/commits/<tag>`; the eight already
  pinned in-repo matched exactly.
- **AC6** `git diff --stat` -> 38 insertions, 38 deletions across 10 files.
- **AC7/AC8** `pip-audit` over cryptography + argon2-cffi + pyyaml -> "No known
  vulnerabilities found", exit 0.
- **A first attempt was reverted.** Its regex used `\s*` for the trailing gap,
  which consumed the newline and the next line's indentation and produced
  `# v4.4.0with:` — it would have broken every workflow. Caught by reading the
  diff rather than trusting the script's own success report; the rewrite is
  line-anchored. The tell was a net -40 lines on a change that should be
  one-for-one.
- **REVIEW** `adversarial-reviewer` and `security-reviewer` = named skips.
