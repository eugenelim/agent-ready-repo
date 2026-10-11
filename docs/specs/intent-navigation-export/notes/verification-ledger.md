# Verification ledger: intent navigation export

## T1

- The derivation reads header lines with `str.splitlines`, so a U+2028 or U+2029 inside a
  header value ends that line and the rest is dropped; neither character can reach a
  record, node, or edge value, and a spec directory named with U+2028 is not admitted as a
  spec. The committed `hostile` corpus therefore carries U+2028 and U+2029 in header text
  (the value is cut at the separator), and the data-block escaping of both characters is
  proved on a constructed payload in `test_build_html_escapes_line_separators_and_markup`.
  AC-0031's wording ("headers carry ... a U+2028 line separator") is not satisfiable
  through the derivation as written.
- `hostile` carries an `expected-outstanding.json`, so slice 1's manifest-discovery tests
  also run over it.
- `build_html`, `publish`, and `source_links` in `intent_view.py` are the minimal T1 forms:
  an unstyled document with only the data block, exclusive-create publication, and every
  source link `inert`. T2, T3, and T4 replace them.

## T2

- Gates: `python -m pytest packs/core/tests/skills/navigate-intents/ -q` gave 386 passed, 4 skipped
  (the 4 skips are in other suites; `test_export_publication.py` alone gave 40 passed, 0 skipped).
  `make lint-ruff lint-mypy` pass. `agentbundle catalogue self-host --root . --write --force`
  run twice (second run changed nothing); `agentbundle catalogue verify --root .` ok.
- AC-0016 ran, not skipped, on this macOS APFS machine (git 2.50.1): the probe
  `CaseProbe` / `caseprobe` resolved to one directory, and `Root/Inner` was refused when given
  as `root/inner`. The component-wise comparison does not catch it (macOS `realpath` keeps the
  spelling); the `samefile` check against each ancestor of the destination does.
- Observed Git behaviour pinned by the tests: for a `--separate-git-dir` main checkout and a
  submodule, `git worktree list` lists the git directory, not the checkout, and does not mark
  it `bare`. The listing therefore belongs to `--root` by the second form (the `.git` file's
  `gitdir:` target equals an entry). A linked worktree of a `--separate-git-dir` repository
  accepts its main checkout, as the accepted limit says.
- `intent_view.py` T1 source held literal U+2028 and U+2029 characters as the escape-table
  keys; they are now ` ` and ` ` escapes with the same value.
- `publish` now takes the `Destination` that `validate_destination` returns. The budget check,
  the platform-support check, and all file creation happen inside `publish`, after validation.
- A test that wraps `os.open` must also add the wrapper to `os.supports_dir_fd`, because the
  platform check compares `os.open` by identity.

## T3

- AC-0027 as written asks for a spec directory named with `?`, `#`, `%`, and a space. The
  derivation admits only slug-shaped spec directory names (such a directory yields no spec
  node), so the test puts those characters in the corpus root's directory name below the Git
  top level, which is part of every link path, and asserts `%3F`, `%23`, `%25`, `%20` in the
  commit URL. `_encode_path` is also tested directly.
- `ls-tree` is limited to the three corpus directories `docs/product/intents`,
  `docs/product/briefs`, and `docs/specs` (the only places a node path can be), passed as
  pathspecs relative to `--root`; `--full-name` makes the output paths top-level relative,
  which is how the link path is formed.
- A node file that is a symlink or a submodule entry in HEAD's tree, a failed or oversized
  read, or an unloadable `_file_safety.py` all give `latest`, never an exception.
- Gates: `python -m pytest packs/core/tests/skills/navigate-intents/ -q` passed (see commit
  report for counts); `make lint-ruff lint-mypy` pass; self-host run twice, second no diff;
  `agentbundle catalogue verify --root .` ok.

## T4

- Code commits: `9490629c5` (page, assets, empty fixture) and `0b8dd0c33` (tests). Chromium 153.0.8010.12 (Playwright, headless).
- Asset digests (SHA-256): `view.js` `93d4d39d4b9ed81e6c1a7d8817eaf10cf7a550cc1c9559bf993b7bd9696733a7`; `view.css` `823d4bf4c130075b6d75b97f9ef279a8a629391d21447aed9c85f5da719f996d`.
- Static suite: `test_export_html.py` 6 passed (CSP and both digests, element and attribute bans, hostile strings outside the data block, forbidden script tokens, `node` escape parity over every unsafe code point plus its neighbours, no motion in the stylesheet). The whole `navigate-intents` folder: 427 passed, 4 skipped (the four skips are the slice 1 whole-operation-failure corpora, unchanged).
- Browser suite `view_browser_checks.py -q -rs`: 40 tests run (35 criteria; AC-0058, AC-0059 at 320 and 1280 px, AC-0064 in four theme setups), 0 skipped, 0 failed, 8.2 s. A mutation check (escape disabled, muted text colour lightened) made AC-0034 and AC-0064 fail, so those checks bite.
- Gates: `make lint-ruff lint-mypy` pass; self-host run twice with an identical tree; `catalogue verify` ok; `catalogue lint --deep` has no `navigate-intents` finding; no `uv.lock`.
- Real export over this repository (AC-0068 preview, not the final record): `export --root .` wrote 564,451 bytes outside the repository; in Chromium the summary strip read 196 outstanding, 0 refused, 100 parentless, 168 intents, 23 briefs, 547 specs, and the Tree view listed 168 intents after expanding every subtree. Screenshot `/tmp/s4-real-repo-detail.png` (not in the repository): header and summary strip on top, view switcher and filters at the left over the tree, the selected intent's facts, "Open on GitHub" link with the "may be newer than this export" mark, and grouped edges at the right; focus ring on the detail heading is a 3 px blue outline.
- Observations: (1) No all-parented corpus exists: the derivation always leaves one root, so AC-0053 is checked on the empty corpus and on a valid export whose data block was rewritten so every record has a resolved parent. (2) The `mixed` corpus has no refused edge, so it is the no-refusal corpus and a separate fixture was not added. (3) `view.js` assembles the GitHub prefix from parts so a page for an unrecognised remote carries no host text (the slice 3 inert test asserts that). (4) The CSP blocks Playwright's string predicates, so the suite passes functions to `wait_for_function`. (5) Keyboard selection in the level filter is by type-ahead; arrow keys do not change a closed select in headless Chromium on macOS.
