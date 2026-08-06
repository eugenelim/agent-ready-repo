# Spec: check-base-freshness-guidance-fixes

Mode: light (no risk trigger fired)

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Constrained by:** none
- **Contract:** none

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Risk assessment: familiar territory; single-person; three independent
one-site fixes in one file plus their tests; no new dependency; no structural
change; no public-interface change (exit codes and the JSON keys are
untouched); nothing destructive. The script emits guidance text, it does not
execute git mutations, so no security boundary is crossed — the shell-quoting
policy (`_quote_for_shell`, Windows returns None) is deliberately out of scope
and unmodified. -->

## Objective

`check-base-freshness.py` is the first thing the work-loop runs. When it is
wrong, it is wrong at the moment the agent has the least context to notice.
Three defects make it wrong in the *silent* direction — it hands the agent a
confident instruction that sends it down the wrong path:

1. A fetch that failed for any reason whose stderr happens to mention "remote
   ref" is reported as **"branch not found on remote"**. The agent then goes
   hunting for a wrong branch name when the real cause was auth or network.
2. A dirty tree is told to `git stash`. The stash stack lives in the shared ref
   store (`refs/stash` is not a per-worktree ref), so in a multi-worktree setup
   a stash pushed in one workspace is visible — and poppable — in every other
   one. Recommending it invites cross-workspace work loss.
3. An unparseable commit count from `git rev-list --count` falls back to `0`,
   which the very next line reads as **"head is current"** — the one answer
   this script exists to avoid getting wrong by accident.

## Acceptance Criteria

- [x] **AC1 — Fetch-error classification is narrow.** The "branch not found on
  remote" message is emitted only when git's own not-found wording
  (`couldn't find remote ref`, case-insensitively) is present in the fetch
  stderr. The strictly-broader `"remote ref" in err_lower` clause — the one
  that actually over-fired, and that made its narrow partner redundant — is
  removed. Every other fetch failure falls through to the generic
  `check network/auth` message.

- [x] **AC2 — Message matching is locale-deterministic.** Because AC1 leaves a
  single English msgid as the sole selector, `_build_git_env()` sets `LC_ALL=C`
  for every git subprocess, so a git build with translation catalogues
  installed cannot silently defeat the classification.

- [x] **AC3 — A dirty tree is told to commit, not stash.** When the branch is
  behind the target and the working tree has uncommitted changes (with or
  without untracked files), the surfaced message recommends committing the work
  on the current branch, names why stash is not the recommendation (the stash
  stack is shared across the repository's worktrees), and names the unwind
  (`git reset --soft HEAD~1` after the rebase). The string `git stash` no
  longer appears as a recommended command anywhere in the script's output. The
  untracked/tracked-only distinction is retained — it still selects between
  `git add -A` + commit and `git commit -a`. The commit subject is
  Conventional-Commits-clean (`chore: wip`) so it survives a `commit-msg` hook
  in an adopter repo.

- [x] **AC4 — The unmerged-files branch stays truthful.** That branch must not
  imply committing is simply unavailable: `git stash` refuses an unmerged
  index, but `git commit -a` — the command AC3 recommends one branch over —
  stages and commits the conflict markers. The message says both.

- [x] **AC5 — An unparseable commit count fails closed.** When
  `git rev-list --count` exits 0 but its stdout is not a non-negative decimal
  integer, the script Surfaces (exit 1) instead of returning `head is current`.
  The predicate is `str.isdecimal`, not `str.isdigit` — `"²".isdigit()` is
  `True` but `int("²")` raises, which would trade a wrong answer for a
  traceback and no JSON on stdout.

- [x] **AC6 — Regression tests.** `test-check-base-freshness.py` gains four
  cases across three functions. Three fail against the pre-fix script:
  - a fetch that fails for a transport reason whose stderr contains the
    substring `remote ref` (a remote URL carrying that phrase) → message says
    `check network/auth` and does **not** claim the branch is missing;
  - a branch behind its target with a dirty tree, tracked-only and untracked
    variants → message recommends a commit, contains no `git stash`, and the
    `git add -A` discriminator is asserted present *and* absent respectively;
  - a branch behind its target with a real `UU` file → message names both
    `git commit -a` and the conflict markers.

  The fourth is a non-regression guard that holds on both sides: a fetch for a
  branch the remote does not have still reports the branch as missing after the
  narrowing (pre-fix, the narrow disjunct matched first, so the message was
  identical). AC2 and AC5 are covered by inspection, not by a test — see the
  declined-pattern register.

  The suite runs green end-to-end (it is executed by
  `packs/core/tests/skills/work-loop/test-loop-cohort.sh`, which the `docs`
  workflow runs in CI).

- [x] **AC7 — The rest of the pack stops prescribing `git stash`.** The three
  remaining prescriptions are replaced, so the pack gives one answer rather
  than two:
  - `work-loop/references/pre-flight-failures.md` — the **stash-check**
    (`git stash -u && <gate> && git stash pop`) becomes a **worktree-check**
    (`git worktree add --detach`, run the gate there, remove it), with the
    dependency caveat named and the shared-stack hazard stated. Its two other
    references to "stash-check" are renamed with it.
  - `work-loop/SKILL.md` § Pre-existing failure triage — "stash-and-rerun"
    becomes "a worktree-check", with the reason in-line.
  - `adapt-to-project/SKILL.md` § Dirty-state escalation — "stash or commit"
    becomes "commit", with the reason in-line.

  Verified by sweeping `grep -rn stash packs/`: no remaining recommendation to
  stash anywhere in the pack tree or its projections.

- [x] **AC8 — Release hygiene.** The `core` pack patch version is bumped in all
  three places that carry it (`packs/core/pack.toml`,
  `packs/core/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` —
  `build-self` does not sync the latter two) and the projected copies
  (`.claude/`, `.agents/`) are regenerated with `FORCE=1 make build-self` so
  `make build-check` is drift-clean. `docs/product/changelog.md` records the
  user-visible fixes under a `[core]` entry.

## Grounding

Four factual claims the fix rests on, each verified rather than assumed:

- **git's not-found wording.** `git fetch <remote> +refs/heads/nope:...` against
  a remote lacking the branch prints `fatal: couldn't find remote ref
  refs/heads/nope` (verified on git 2.50.1; older releases capitalise it, which
  the case-insensitive match covers).
- **that wording is a gettext msgid.** git wraps the string in `_()`, so a build
  with translation catalogues installed prints it in the user's language and the
  match would silently never fire. Not reproducible on Apple Git 2.50.1, which
  ships no catalogues — hence AC2's `LC_ALL=C`, which is the cheap way to make
  the question moot rather than to bet on it.
- **stash is shared across worktrees.** `refs/stash` is not in git's
  per-worktree ref set (`HEAD`, `refs/bisect/*`, `refs/worktree/*`,
  `refs/rewritten/*`). Verified directly: a `git stash push` in a repository's
  main worktree is listed by `git stash list` in a linked worktree of the same
  repository. This is general git behaviour, not tool-specific, so the message
  says "worktrees" rather than naming any particular workspace manager.
- **`git commit -a` commits conflict markers.** Verified on git 2.50.1 against a
  `UU` file: `git stash` fails with `f.txt: needs merge`, plain `git commit`
  refuses with `Committing is not possible because you have unmerged files`, and
  `git commit -a` succeeds, committing the file with `<<<<<<<` intact. This is
  why AC4 exists at all — AC3 puts `git commit -a` in the agent's hands one
  branch away.

## Tasks

1. Narrow the fetch-error classification (AC1) and pin the locale (AC2).
2. Replace the stash guidance with commit guidance, and make the unmerged-files
   branch truthful about both escapes (AC3, AC4).
3. Fail closed on an unparseable commit count (AC5).
4. Add the regression cases (AC6).
5. Sweep the pack's remaining `git stash` prescriptions (AC7).
6. Bump `core` in all three files, run `FORCE=1 make build-self`, add the
   changelog entry (AC8).

## Assumptions

- The stdout JSON is read by an agent, not parsed by a program: no consumer
  matches on `message` substrings, so rewording it is not a breaking change.
  (Verified: the only consumer is the `work-loop` SKILL.md prose instruction to
  read `message` and Surface it.)
- AC5 is defensive. With a real git binary, `rev-list --count` returning exit 0
  and non-decimal stdout is not reachable; the change is justified by the
  direction of the fallback, not by a reproducible failure. It is therefore
  covered by inspection, not by a test — see the declined-pattern register.
- **The commit command is emitted on Windows too, unlike the rebase command.**
  `_quote_for_shell` returns `None` on Windows because the *ref name* it would
  interpolate is attacker-shaped data with no quoting strategy that is safe in
  cmd.exe, PowerShell and Git Bash at once. `git commit -a -m "chore: wip"` and
  `git add -A` interpolate nothing and are valid verbatim in all three shells,
  so the policy does not reach them. Emitting them unconditionally preserves
  the pre-fix behaviour, where `stash_cmd` was likewise unconditional.

## Declined

- **A `_classify_fetch_error()` helper.** One call site. Inline per AGENTS.md.
- **A full fetch-error taxonomy** (auth vs DNS vs proxy vs shallow-clone). The
  generic message already names both plausible causes; more branches means more
  ways to be confidently wrong, which is the defect being fixed.
- **A PATH-shim `git` to reach the AC5 branch in a test.** The shim would have
  to pass every other git call through; the test would then mostly exercise the
  shim. Recorded as an inspection-only change instead.
- **A test for AC2's `LC_ALL=C`.** Reproducing it needs a git build with
  translation catalogues installed, which no CI runner here guarantees. A test
  that asserts the env dict contains the key would pin the implementation, not
  the behaviour.
- **A configurable WIP commit message.** No second caller needs to differ.
- **Wiring the test file into `docs.yml` as its own step.** Grepped first: it
  is already invoked by `test-loop-cohort.sh`, which that workflow runs.
- **Touching `_quote_for_shell` / the Windows no-command policy.** Untouched by
  this change and out of scope — see the third Assumption for why the commit
  command does not fall under it.
- **Deferring the rest of the pack's stash prescriptions.** Initially deferred
  as `work-loop-no-stash-guidance-sweep`, on the grounds that the other files
  sit outside this change's directory and so fall outside the bundled-fixes
  carve-out. Pulled back in at the author's direction — leaving the pack
  telling the agent "commit, don't stash" in one file and "stash" in three
  others is a worse outcome than a slightly wider diff. Now AC7; the backlog
  entry was removed rather than left dangling.
- **Replacing the stash-check with "commit, then compare against HEAD~1".**
  That reads the parent commit, not the pre-change working tree, so it answers
  a different question once any of the session's work is already committed.
  The worktree-check preserves the original semantics; the commit-first route
  is named only as the fallback for gates that need installed dependencies.

## Resolve-vs-surface disposition

| Item | Disposition | Note |
|---|---|---|
| git's exact not-found wording | resolved | Reproduced locally against git 2.50.1. |
| Is that wording translatable? | resolved | It is a gettext msgid; pinned `LC_ALL=C` rather than betting on the runner's locale. |
| Is the stash stack really shared? | resolved | Reproduced with a linked worktree. |
| Does `git commit -a` dodge the unmerged guard? | resolved | Reproduced against a `UU` file; it commits the markers, so AC4 exists. |
| Is AC5 reachable? | resolved | Concluded not reachable with a real git; changed anyway for direction, flagged as inspection-only. |
| Does the test file actually run in CI? | resolved | Grepped: invoked by `test-loop-cohort.sh` in the `docs` workflow. |
| Does any program parse `message`? | resolved | Grepped every reference; the only consumer is skill prose. |
| Does `build-self` sync the pack version? | resolved | It does not; `plugin.json` and `marketplace.json` are hand-bumped, per the precedent in commit `a509e1db`. |
| The other stash prescriptions in the pack | surfaced, then resolved | Out of the carve-out's reach, so surfaced as a deferral; the author pulled it into this change. Now AC7. |
| Is `git reset --soft HEAD~1` the right unwind? | resolved | No — `--soft` restores untracked files as staged. Mixed `git reset HEAD~1` is the exact inverse of both variants. |
