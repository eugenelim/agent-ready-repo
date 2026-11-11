# Verification ledger: ux-writing-to-experience-design

## 2026-10-14 — upgrade-order spike (before approval)

Throwaway scratch repositories, `claude-code` adapter, repo scope, isolated
`AGENTBUNDLE_USER_ROOT`, and the worktree's `agentbundle`. The old catalogue is
`3216c5b40`. The new one is a scratch copy with `ux-writing` moved, a one-line body
edit, product-engineering 2.0.0, and experience-design 4.2.0. Both packs at the
old versions were installed first. "PE" is product-engineering, "XD" is
experience-design.

| Run | Steps | `ux-writing/SKILL.md` after | State rows claiming it |
| --- | --- | --- | --- |
| A | PE upgrade → PE uninstall + install → XD upgrade | XD copy | 1 |
| B | PE upgrade → delete the folder by hand → XD upgrade | XD copy | 2 (PE 2.0.0 still claims it) |
| C | XD upgrade → PE upgrade → PE uninstall + install | XD copy | 1 |
| D | B, then PE uninstall | XD copy, kept as shared | 1 |
| E | XD upgrade → PE upgrade → XD uninstall | left behind by the stale PE claim | 1 |

- In C, the PE upgrade prints "1 installed file(s) have local edits", because XD
  rewrote a file PE still claims. No `.upstream` file is written.
- `upgrade` does not run direct install's "already owned by" refusal, so two packs
  can claim one path.
- Conclusion: the order of the two upgrades does not matter. A PE uninstall and
  install afterwards clears the stale claim. Deleting by hand does not.

## 2026-10-14 — spike, second pass (before approval)

Same setup as above. Runs F and G start from product-engineering 1.0.5 alone.

| Run | Steps | `ux-writing/SKILL.md` after | State rows claiming it |
| --- | --- | --- | --- |
| F | PE upgrade → XD install | PE 1.0.5 copy; the install exits 1, "refusing — these paths are already owned" | 1 (PE) |
| G | PE upgrade → PE uninstall + install → XD install | XD copy | 1 |
| H | both packs: PE upgrade → XD upgrade → PE uninstall + install | XD copy | 1 |

- A product-engineering-only adopter must run the uninstall and install step before
  installing experience-design.
- H is the product-engineering-first order with the step last, which run A did not
  cover.

## 2026-10-14 — local edits through the step (before approval)

Run I starts from product-engineering 1.0.5 alone, with one line appended to the
installed `.claude/skills/intent/SKILL.md`.

- The upgrade to 2.0.0 keeps the edit and writes `SKILL.upstream.md` beside it.
- `agentbundle uninstall --pack product-engineering` prints "keeping adopter-edited
  file: .claude/skills/intent/SKILL.md" and "87 removed, 1 kept".
- The edited file survives the step.

## 2026-10-14 — T5 install-then-upgrade observation (AC-0015)

The old catalogue is commit 3216c5b40 (product-engineering 1.0.5, experience-design
4.1.6). The new catalogue is this change (product-engineering 2.0.0, experience-design
4.2.0). Each run uses a fresh scratch git repo, `--scope repo --adapter claude-code`,
and its own `AGENTBUNDLE_USER_ROOT`, so the real user scope is untouched. Every
command exits 0.

| Run | Steps | State rows for `.claude/skills/ux-writing/SKILL.md` | File vs. source |
| --- | --- | --- | --- |
| PE-first | install PE + XD (old) → upgrade PE → upgrade XD → uninstall PE → install PE (new) | 1, XD 4.2.0 | identical |
| XD-first | install PE + XD (old) → upgrade XD → upgrade PE → uninstall PE → install PE (new) | 1, XD 4.2.0 | identical |
| PE-only | install PE (old) → upgrade PE → uninstall PE → install PE (new) → install XD (new) | 1, XD 4.2.0 | identical |

- The file is compared with `packs/experience-design/.apm/skills/ux-writing/SKILL.md`
  directly with `cmp`; the claude-code projection does not transform it.
- Key lines in the two-pack runs: "upgraded: product-engineering @ repo 1.0.5 ->
  2.0.0", "upgraded: experience-design @ repo 4.1.6 -> 4.2.0", and "uninstall: 80
  removed, 0 kept, 8 kept (shared)".
- Key lines in the PE-only run: "upgraded: product-engineering @ repo 1.0.5 -> 2.0.0",
  "uninstall: 88 removed, 0 kept", and both installs end with their usual "Next:" line.
- AC-0015 holds: every run ends with one state row for the path, at experience-design
  4.2.0, and the installed file equals the experience-design copy.

## 2026-10-19 — rebase onto `cf919e2b3`

- `main` gained 15 commits that rewrote the guides and pack READMEs. Two pages this change edited are gone on `main`: `guides/product-engineering/how-to/hand-it-to-build.md` and `guides/experience-design/how-to/review-independently.md`. The plan's T3 bullets about the walkthrough's rung comments and pointer, and the review-step rungs, no longer have a target.
- Each pack README and both guide READMEs now take `main`'s text. On top of it, `ux-writing` leaves product-engineering's skill list and joins experience-design's, and the microcopy how-to's index entry moves to the experience-design guides.
- After the rebase, every gate passes again:
  - journeys regenerated;
  - self-host;
  - `catalogue lint --deep` and `catalogue verify`;
  - guide, site-parity, and journey lints;
  - changelog validation;
  - `make site-link-check` (35,716 links across 612 pages, clean);
  - 240 tests;
  - `make lint-ruff lint-mypy`.
- `tests/roster/test_plugin_install_doc_drift.py` passes alone (4 passed). It fails to collect only when run beside the other suites, from a test-module name clash in files this change does not touch.
- After the rebase, product-engineering's README carries one `ux-writing` line: the `docs/product/voice/` folder line naming Experience Design's `ux-writing` as its writer. That line satisfies AC-0010 and the plan's Rationale decision.

## 2026-10-19 — contract amendment authorized (AC-0010 wording)

- **Owner ruling (eugenelim, 2026-10-19):** amend AC-0010 and the plan's Rationale decision through controlled amendment, rather than adding a folder tree back to `main`'s README.
- **Reason:** after the rebase onto `cf919e2b3`, product-engineering's README has no folder tree. Its one `ux-writing` line is the `docs/product/voice/` sentence under "Where are the files saved?". AC-0010 still names "the `README.md` `voice/` tree line", and the plan Rationale still says "Its `README.md` tree keeps `voice/`".
- **Scope:** the wording of AC-0010 and the plan's Rationale decision only. The only-line rule stays as it is.
- **T3 stays as approved:** completed task sections cannot be edited. These T3 bullets have no target after the rebase, and this entry records them as deviations:
  - the `<!-- rung: -->` comments in the deleted `hand-it-to-build.md`;
  - the `guides/product-engineering/README.md` "line 57" walk sentence, since `main`'s rewritten README has no walk paragraph, no skill count, and no `ux-writing` line. AC-0018's "no `thirteen`" check on that file still holds.

## 2026-10-19 — T5 re-run after rebase (AC-0015)

The same three runs, repeated against the working tree rebased onto `cf919e2b3` as the
new catalogue (product-engineering 2.0.0, experience-design 4.2.0). The old catalogue is a
fresh `git archive` of 3216c5b40 (product-engineering 1.0.5, experience-design 4.1.6).
Each run uses a fresh scratch git repo, `--scope repo --adapter claude-code`, and its own
`AGENTBUNDLE_USER_ROOT`. Every command exits 0.

| Run | Steps | State rows for `.claude/skills/ux-writing/SKILL.md` | File vs. source |
| --- | --- | --- | --- |
| PE-first | install PE + XD (old) → upgrade PE → upgrade XD → uninstall PE → install PE (new) | 1, XD 4.2.0 | identical |
| XD-first | install PE + XD (old) → upgrade XD → upgrade PE → uninstall PE → install PE (new) | 1, XD 4.2.0 | identical |
| PE-only | install PE (old) → upgrade PE → uninstall PE → install PE (new) → install XD (new) | 1, XD 4.2.0 | identical |

- The file is compared with `packs/experience-design/.apm/skills/ux-writing/SKILL.md`
  directly with `cmp`.
- Key lines match the earlier entry: "upgraded: product-engineering @ repo 1.0.5 -> 2.0.0",
  "upgraded: experience-design @ repo 4.1.6 -> 4.2.0", "uninstall: 80 removed, 0 kept, 8 kept
  (shared)" in the two-pack runs, and "uninstall: 88 removed, 0 kept" in PE-only.
- New in the XD-first run: the PE upgrade prints "1 installed file(s) have local edits;
  your edits are preserved as .upstream companions". This is the `ux-writing` file that XD
  4.2.0 had already put at the path. No `.upstream` file remains after the uninstall, and the
  end state is unchanged.
- AC-0015 holds on the rebased tree.
- Checked separately: right after the product-engineering upgrade in the experience-design-first order, no `*upstream*` file exists under `.claude/`. The CLI notice says "where the file still ships", and `ux-writing` no longer ships in product-engineering, so none is written.
