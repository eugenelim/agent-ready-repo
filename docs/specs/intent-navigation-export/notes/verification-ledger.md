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
