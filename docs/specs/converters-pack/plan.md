# Plan: converters-pack

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this document is allowed to change as you learn. When it changes substantially (a different approach, not just a re-ordering), note why in the changelog at the bottom.

## Approach

One PR, seven tasks. The work is mostly file copying + content scrub + thin metadata authoring + a single integration test + new pytest CI surface; the riskiest step is the scrub (T2) because net-new content authored during T3 (plugin.json description text, render.js comment rewrite) could introduce new attribution leaks the audit didn't see. T3 includes a re-run of the scrub grep against its own authored content to catch that.

Order is strictly serial — the dependency chain prevents parallelism. T1 (import) → T2 (scrub) → T3 (pack metadata) → T4a (pytest test, requires pack.toml from T3) → T4b (pytest CI invocation, requires T4a green locally) → T5 (CI greps + seed-side architecture overview edit) → T6 (SHA pin). Earlier drafts of this plan suggested T3/T4 could run in parallel — they cannot: T4a's `agentbundle install converters --scope user` reads pack.toml authored in T3.

The implementation is deliberately thin on cleverness: no helper extraction, no shared scaffolding across the three skills, no abstraction over the carry-over logic. Three skill directories, three independent contents, one shared scrub rule.

## Constraints

- [RFC-0007](../../rfc/0007-user-scope-converter-pack.md) (Accepted 2026-05-24) — pack shape, runtime-dep disposition, scrub rules, eight Acceptance Criteria.
- [RFC-0004](../../rfc/0004-install-scope-per-pack.md) — user-scope dimension; the three refusal rails (seeds, hooks, markers); state-file v0.2 shape.
- [ADR-0002](../../adr/0002-install-scope-per-pack-default-and-allowance.md) — install-scope precedence rules.
- [`docs/specs/distribution-adapters/spec.md`](../distribution-adapters/spec.md) — recipe set; build-pipeline auto-emission of APM + Claude-plugins per pack (no per-pack opt-in needed).
- [`docs/specs/self-hosting/spec.md`](../self-hosting/spec.md) — projected-path drift detection; this plan edits `packs/core/seeds/docs/architecture/overview.md` directly (seed) and regenerates the projected `docs/architecture/overview.md` via `make build-self`.
- AGENTS.md root file — Conventional Commits format; commit identity per memory `git_identity.md`.

## Construction tests

Most construction tests live under the per-task `Tests:` subsections below. Cross-cutting:

- **Integration:** the pytest fixture-`$HOME` install/uninstall test from T4a is the single integration test that crosses task boundaries (exercises pack.toml from T3, the imported files from T1–T2, and the build-pipeline projection from T3).
- **Manual verification:** none — every AC has an automated check.

## Tasks

### T1: Import source files into `packs/converters/.apm/skills/`; pin source SHA

**Depends on:** none

**Mode:** Goal-based check.

**Tests:**
- Directory inventory matches the *pre-scrub* state: three skill directories carrying their source contents inclusive of the 3 × `manifest.json` files and the dropkit-attributed render.js comment (T2 removes these).
- `git ls-files packs/converters/.apm/skills/` lists every file the source carries under `skills/converters/`, with the directory prefix rewritten to `.apm/skills/`.
- `docs/specs/converters-pack/notes/source-sha.txt` exists, contains exactly one 40-hex-char SHA line, and is committed (not gitignored).

**Approach:**
- Clone the source catalogue (HEAD of `main`) to a temp directory outside the repo.
- Record `git rev-parse HEAD` from the temp clone and write it to `docs/specs/converters-pack/notes/source-sha.txt` (single line, newline-terminated). This artifact is the durable cross-task pin used by T6.
- Copy `skills/converters/file-to-markdown/`, `skills/converters/markdown-to-html/`, `skills/converters/msg-to-markdown/` into `packs/converters/.apm/skills/{file-to-markdown,markdown-to-html,msg-to-markdown}/` respectively.
- Commit raw (one commit including the SHA file) so T2's scrub diff is reviewable in isolation.

**Done when:** Three skill directories present under `packs/converters/.apm/skills/`; `notes/source-sha.txt` committed with the SHA; file inventory matches the pre-scrub expectation.

---

### T2: Scrub source-catalogue attribution

**Depends on:** T1

**Mode:** Goal-based check.

**Tests:**
- `rg -i --hidden '\bdropkit\b' packs/converters/` exits non-zero (= zero hits). Run locally; the same check lands in CI in T5. (`-iE` from earlier drafts is broken on ripgrep 15+ — `-E` maps to `--encoding=NAME`; the AC2 amendment dropped it and added `--hidden` because the imported skills live under `.apm/`.)
- The four named hits from RFC-0007 § Source-attribution scrub are each addressed (verifiable by `git diff T1..T2 -- packs/converters/`): 3 × `manifest.json` deletions + 1 × `render.js:30` comment rewrite.

**Approach:**
- Run the scrub grep first as a shell one-liner (`rg -i --hidden 'dropkit' packs/converters/`); confirm 4 hits (the audit baseline).
- Delete `packs/converters/.apm/skills/file-to-markdown/manifest.json`.
- Delete `packs/converters/.apm/skills/markdown-to-html/manifest.json`.
- Delete `packs/converters/.apm/skills/msg-to-markdown/manifest.json`.
- Edit `packs/converters/.apm/skills/markdown-to-html/scripts/render.js:30` — rewrite the comment from `// dropkit/skills/... or copied into ~/.claude/skills/markdown-to-html/).` to `// either at the skill directory or copied into ~/.claude/skills/markdown-to-html/).`.
- Re-run the scrub grep; confirm zero hits.

**Done when:** scrub grep exits non-zero (zero hits); the four documented dispositions are visible in the diff.

---

### T3: Author `pack.toml` + `.claude-plugin/plugin.json`; close AC7 + AC7a

**Depends on:** T2

**Mode:** Goal-based check.

**Tests:**
- **pack.toml shape:** `agentbundle validate packs/converters/` exits zero; `pack.toml` content matches [RFC-0007 § `pack.toml`](../../rfc/0007-user-scope-converter-pack.md#packtoml) verbatim (modulo cosmetic whitespace).
- **plugin.json shape:** `packs/converters/.claude-plugin/plugin.json` structurally matches `packs/governance-extras/.claude-plugin/plugin.json` (same fields; substituted name and description).
- **Build emission:** `make build PACKS_DIR=packs` emits `dist/claude-plugins/converters/` and `dist/apm/converters/` and aggregates the converters entry into `dist/claude-plugins/marketplace.json`.
- **Scrub re-check (catches T3-authored attribution leaks):** `rg -i --hidden '\bdropkit\b' packs/converters/` still exits non-zero after T3.
- **AC7 disposition:** `markdown-to-html/package.json` exists (carried from source) and pins `marked` + `highlight.js`; SKILL.md text greps for the runtime install commands per AC7.
- **AC7a gitignore note:** `grep -F 'node_modules' packs/converters/.apm/skills/markdown-to-html/SKILL.md` returns the `.gitignore` recommendation (note: T3 *adds* this note to SKILL.md if absent in the source; the source's SKILL.md does not currently carry it).

**Approach:**
- Write `packs/converters/pack.toml` from the RFC-0007 § `pack.toml` block verbatim.
- Write `packs/converters/.claude-plugin/plugin.json` modeled on the existing `governance-extras` plugin.json shape. Description avoids naming the source catalogue.
- Add the one-line `.gitignore` recommendation to `markdown-to-html/SKILL.md` (close to the `npm install` step). Wording: `> Note: at repo scope, add \`.claude/skills/*/node_modules/\` to your project's \`.gitignore\` to avoid committing the npm install artifacts.`
- Run `agentbundle validate packs/converters/` locally — must exit zero.
- Run `make build PACKS_DIR=packs` — confirm dist artifacts.
- Re-run the scrub grep against the now-larger surface.

**Done when:** `agentbundle validate` exits zero; dist artifacts emit cleanly; AC7 + AC7a greps pass; scrub re-check stays clean.

---

### T4a: pytest fixture-`$HOME` install/uninstall test (local)

**Depends on:** T3

**Mode:** TDD.

**Tests:**
- The test file `packages/agentbundle/tests/integration/test_install_converters_user_scope.py` runs and passes via `pytest packages/agentbundle/tests/integration/test_install_converters_user_scope.py`.
- The test's first invocation (against an empty test file) fails because no test is defined — the natural TDD red. Subsequent invocations after writing the test pass.
- The test asserts: temp `$HOME` → install at user scope → state.toml exists with schema-version matching `STATE_SCHEMA_VERSION` (currently `"0.3"`) and `converters` entry at `scope = "user"` → projected primitives at `~/.claude/skills/<each>/` → uninstall → state.toml has no `converters` entry → projected primitives gone.

**Approach:**
- Read `packages/agentbundle/tests/integration/test_install_user_hooks.py` (verified: closest existing idiom — user-scope install fixture, lines 27–113). The canonical shape is **in-process** `install.run(args_namespace)` via `from agentbundle.commands import install`, using `unittest.TestCase` (pytest discovers unittest classes via `tool.pytest.ini_options.testpaths`).
- Create the test file with a placeholder `class ConvertersUserScopeInstallTests(unittest.TestCase): def test_placeholder(self): self.fail("not yet implemented")`. Run `pytest <path>` to confirm the failing-first red.
- Write the test:
  - `class ConvertersUserScopeInstallTests(unittest.TestCase)` with `setUp` mirroring `_UserScopeInstallBase` in `test_install_user_hooks.py:57-73`: `self.tmp = Path(tempfile.mkdtemp())`, `self.home = self.tmp / "home"`, `self.repo = self.tmp / "repo"`, `self.cat = self.tmp / "catalogue"`, all `mkdir`'d; `patch.dict(os.environ, {"HOME": str(self.home)})` started + cleanup registered.
  - Copy the local `packs/converters/` (i.e. `REPO_ROOT / "packs" / "converters"`) into `self.cat / "packs" / "converters"` via `shutil.copytree` (mirroring `_copy_fixture`).
  - Build args: `argparse.Namespace(pack="converters", catalogue=str(self.cat), output=str(self.repo), scope="user", force=False, force_merge=False)`.
  - Call `install.run(args)` with stdout/stderr captured via `contextlib.redirect_stdout/redirect_stderr` and assert `rc == 0`.
  - **HOME-resolution guard:** before any state-file assertion, assert `(self.home / ".agent-ready").exists()` — if HOME didn't propagate, the state directory lands at the developer's real home instead and this assertion fails with a clear message.
  - Use `agentbundle.config.load_state` (per `test_install_user_hooks.py:107-113`) to read `self.home / ".agent-ready" / "state.toml"`; assert schema-version equals `agentbundle.config.STATE_SCHEMA_VERSION` (`"0.3"` at import time) and `state.packs["converters"].scope == "user"`.
  - Assert three `(self.home / ".claude" / "skills" / name).is_dir()` checks.
  - Build uninstall args: `argparse.Namespace(pack="converters", root=str(self.repo), scope="user")` — mirroring `test_uninstall_user_hooks.py` `_uninstall_args` shape; the uninstall surface is narrower than install (no `catalogue`, no `force*`, uses `root` not `output`). Call `uninstall.run(args)`; assert state has no `converters` entry and `.claude/skills/<name>/` dirs are absent.
- Run; confirm green.

**Done when:** test green locally; the test file is committed.

---

### T4b: Wire pytest CI invocation

**Depends on:** T4a

**Mode:** Goal-based check.

**Tests:**
- A new GitHub Actions job named (e.g.) `pytest converters install` exists in `build-check.yml` or `docs.yml`.
- The job runs `pytest packages/agentbundle/tests/integration/test_install_converters_user_scope.py` on every PR targeting `main`.
- The job surfaces as a distinct check name in the PR's checks list.
- This branch's CI run shows the check passing.

**Approach:**
- Verified from `packages/agentbundle/pyproject.toml`: the package declares `[project.scripts] agentbundle = "agentbundle.cli:main"` (editable install exposes the console script) and `[tool.pytest.ini_options] testpaths = ["tests", "agentbundle/build/tests"]` (pytest discovers from the package root). The CI install + run shape is therefore: `pip install -e packages/agentbundle/` then `cd packages/agentbundle && pytest tests/integration/test_install_converters_user_scope.py -q`.
- Add a new job (or a step in `build-check` job) to `.github/workflows/build-check.yml` — same workflow already does `actions/setup-python@v5` so it's the natural host:
  - Step 1: `pip install -e packages/agentbundle/`.
  - Step 2: `cd packages/agentbundle && pytest tests/integration/test_install_converters_user_scope.py -q` (the `-q` matches `addopts` from pyproject.toml).
- Push branch; confirm the new check name appears and passes in the PR UI.
- If `pip install -e` surfaces editable-install issues on CI (rare with `setuptools>=61`), fall back to `pip install packages/agentbundle/` (non-editable); update the step in place.

**Done when:** CI run on this branch surfaces a green check for the new pytest job; subsequent PRs targeting `main` invoke the same check.

---

### T5: Add scrub + Rail C greps to CI; update architecture overview (via seed)

**Depends on:** T2, T3

**Mode:** Goal-based check.

**Tests:**
- GitHub Actions workflow runs `rg -i --hidden '\bdropkit\b' packs/converters/` as a step; exits non-zero (zero hits) on this branch.
- Same workflow runs `rg --hidden '<adapt:[A-Z_][A-Z0-9_]*>|<adapt:[a-z][a-z0-9-]*>' packs/converters/`; exits non-zero (zero hits).
- Same workflow runs JSON-validity + canonical-keys check for AC4a on each carried `evals.json`.
- `packs/core/seeds/docs/architecture/overview.md` names `converters` as the fifth pack in whichever section enumerates the catalogue's packs.
- After `make build-self`, `docs/architecture/overview.md` matches the seed (no drift); `make build-check` exits zero.
- `grep -n converters docs/architecture/overview.md` returns at least one hit naming the pack.

**Approach:**
- **Edit-order against T4b:** T4b lands first and adds the pytest install+run step to `build-check.yml`. T5 appends its three CI steps after T4b's; if both tasks ran in parallel they would collide on the same workflow file, but the `Depends on:` chain serialises them.
- Edit `packs/core/seeds/docs/architecture/overview.md` (the seed; verified source-of-truth — projected to `docs/architecture/overview.md` via the build pipeline). Find the section enumerating packs; add `converters` with a one-line description matching RFC-0007 wording.
- Run `make build-self` to regenerate the projected path.
- Run `make build-check` to confirm zero drift.
- Add three CI steps to `build-check.yml` (preferred — same workflow context):
  - Scrub: `! rg -i --hidden '\bdropkit\b' packs/converters/` (inverted; success = zero hits).
  - Rail C: `! rg --hidden '<adapt:[A-Z_][A-Z0-9_]*>|<adapt:[a-z][a-z0-9-]*>' packs/converters/`.
  - AC4a: `for f in packs/converters/.apm/skills/*/evals/evals.json; do python -c "import json,sys; p=sys.argv[1]; d=json.load(open(p)); assert 'skill_name' in d and 'evals' in d, f'{p} missing canonical keys'" "$f"; done` (single parse + assertion; path passed via `sys.argv` so quoting in filenames doesn't break the step).
- Verify locally that all three greps + the JSON check exit zero against the pack.

**Done when:** all three CI checks land and pass on this branch; the seed edit propagates cleanly through `make build-self`; overview.md grep returns the converters mention.

---

### T6: Pin source commit SHA in spec Changelog

**Depends on:** T1

**Mode:** Goal-based check.

**Tests:**
- `docs/specs/converters-pack/spec.md` Changelog has a dated entry matching the anchored grep: `grep -E '^- [0-9]{4}-[0-9]{2}-[0-9]{2}: initial import from source commit [a-f0-9]{40}$' docs/specs/converters-pack/spec.md` returns the entry.
- The SHA in the spec entry equals the SHA in `notes/source-sha.txt` (committed by T1): `diff <(grep -oE '[a-f0-9]{40}$' docs/specs/converters-pack/spec.md) docs/specs/converters-pack/notes/source-sha.txt` returns no difference.

**Approach:**
- Read the SHA from `docs/specs/converters-pack/notes/source-sha.txt`.
- Append to the spec's Changelog section, exact format: `- 2026-05-24: initial import from source commit <sha>`. SHA-only is the canonical form — the AC5 anchored grep is right-anchored to `[a-f0-9]{40}$`, and the spec § Never-do governance-text carve-out permits naming the source in spec prose but not in this Changelog line shape. If a future maintainer wants the human-readable source name as a breadcrumb, the spec's prose body can carry it; the Changelog line stays SHA-only.

**Done when:** anchored Changelog grep returns the entry; SHA matches `notes/source-sha.txt`.

---

## Rollout

The pack lands on `main` via a single squash-merged PR. No feature flag, no gradual rollout, no migration. Adopters opt in by running `agentbundle install converters` after the PR ships. Reversibility: revert the PR commit; the pack disappears from `packs/`, the build pipeline stops emitting its dist artifacts, the catalogue's marketplace.json regenerates without the entry; the new pytest CI job stops running (no dependent jobs).

## Risks

- **CI grep idiom may not invert exit codes cleanly across runners.** GitHub Actions' `bash` shell: `! rg ...` and `rg ... && exit 1 || exit 0` both work. T5's Approach uses `! rg ...` (verified — no existing inverted-grep precedent in `build-check.yml` today, so this PR establishes the idiom). *Mitigation:* if CI surfaces a shell-level quirk, fall back to `rg ... && exit 1 || exit 0`.
- **`Path.home()` cache busts via `patch.dict` re-entrancy.** The in-process `install.run()` resolves HOME afresh on each call, but if any code path caches the resolved home at module-import time, `patch.dict(os.environ, {"HOME": ...})` won't affect that cache. The HOME-resolution guard in AC6a (`(self.home / ".agent-ready").exists()` before state-file assertions) catches this — if a cached home is wrong, the guard fires before the test reaches the shape assertions. *Mitigation:* the guard is the test contract.
- **New pytest CI job's runner setup may diverge from existing tests' local-run invocation.** Reading `packages/agentbundle/pyproject.toml` confirmed the install idiom (`pip install -e packages/agentbundle/`) and the pytest invocation (`pytest tests/integration/...` with `addopts = "-q"`). The CI step pins these. *Mitigation:* T4b's commit message documents the chosen idiom for future maintainers.
- **`make build-self` projects user-scope packs into the catalogue's `<repo>/.claude/skills/` and `AGENTS.md` regardless of `default-scope`.** Observed during T5: `make build-self FORCE=1` writes the three converter skills under the catalogue's own `.claude/skills/`, advertises them in `AGENTS.md`, and adds the converters entry to `.claude-plugin/marketplace.json`. The self-hosting spec is silent on user-scope packs. For now this PR accepts the projection as intentional dog-fooding — the catalogue is itself a project consuming the pack at repo-scope (`allowed-scopes = ["user", "repo"]` permits this) — but the AGENTS.md skill list now interleaves domain skills with governance skills. *Mitigation:* none in this PR; a follow-on RFC should decide whether `make build-self` should skip user-scope-default packs or whether AGENTS.md should split workflow-skills from shipped-skills. Filed as a follow-on note in this plan; no ROADMAP entry yet (the dust settles after the first user-scope pack ships).

## Changelog

- 2026-05-24: initial plan, drafted alongside spec.md.
- 2026-05-24: revised per adversarial review (B1–B5, C6–C12, N13–N15). Split T4 into T4a (write test, run locally) and T4b (wire pytest CI invocation) after confirming no pytest CI exists today. Changed T5 Approach to edit the seed (`packs/core/seeds/docs/architecture/overview.md`) directly. Added `notes/source-sha.txt` as T1's durable artifact bridging to T6. Relabelled T2 from TDD to Goal-based check. Split T3 Tests into named blocks; added scrub re-check + AC7a coverage. Removed the "deliberate-defect inversion" claim from T4 (the TDD red is the test file's non-existence). Tightened T6 grep to anchored Changelog-line shape.
- 2026-05-24: revised per second-pass adversarial review. Rewrote T4a Approach to mirror the actual `test_install_user_hooks.py` idiom (in-process `install.run(args_namespace)`, `unittest.TestCase` + `patch.dict(os.environ, {"HOME": ...})`, catalogue layout `<tmp>/catalogue/packs/converters/`); dropped the fictitious `--from` flag and the subprocess shell-out. Pinned T4b CI invocation against verified `pyproject.toml` shape (`pip install -e packages/agentbundle/` + `pytest tests/integration/...`). Added HOME-resolution guard to AC6a (assert before state-file shape). Clarified AC3 covers prose/code blocks. Dropped T6's parenthetical-permission hedge (SHA-only canonical). Added explicit T4b → T5 edit-order note in T5 Approach.
- 2026-05-24: revised during implementation. Spec AC2/AC3 and matching plan T2/T3/T5 grep idioms updated: removed `-E` (maps to `--encoding=NAME` on ripgrep 15+ and aborts with `unknown encoding`); added `--hidden` (the imported skills live under `.apm/`, which ripgrep treats as hidden by default — without `--hidden` the scrub vacuously passes without searching the imported files). Verified locally against ripgrep 15.1.0 with the four-hit audit baseline pre-scrub and zero hits post-scrub.
- 2026-05-24: revised during T4a implementation. State-file schema version moved from a hard-coded `"0.2"` to the runtime constant `agentbundle.config.STATE_SCHEMA_VERSION` (currently `"0.3"`); RFC-0005 bumped the schema after the spec was drafted. The test asserts against the constant rather than a literal so a future bump doesn't silently invalidate this AC.
- 2026-05-24: revised during T5 implementation. (a) `file-to-markdown/SKILL.md` frontmatter `description` field collapsed from a folded YAML scalar (`description: >`) to a single-line string — the AGENTS.md generator pulls the literal `>` instead of parsing the folded form, and every other SKILL.md in the catalogue uses the single-line shape. Body text unchanged. (b) `make build-self FORCE=1` was needed because the working tree is dirty during implementation; the projected paths under `.claude/skills/` and the bumped `AGENTS.md` + `.claude-plugin/marketplace.json` are part of this PR's diff. (c) CI grep idiom shipped as `if rg …; then exit 1; fi` rather than the plan's literal `! rg …` — both forms are documented-equivalent in the plan's Risks section; the chosen form surfaces a `::error::` annotation when it fires.
- 2026-05-24: revised per adversarial review (2 Blockers + 7 Concerns + 4 Nits). (a) **B1**: `metadata:` blocks stripped from all three SKILL.md files — `tools/lint-agent-artifacts.sh` allows only `{name, description, dependencies}` and aborts on nested mappings; the `version:` field was a source-catalogue convention, not part of the agentskills.io canonical layout. (b) **B2**: rewrote the `cd skills/converters/markdown-to-html` instruction in `markdown-to-html/SKILL.md` in path-neutral terms — same shape of source-layout leak that `render.js:30` carried (the scrub's `\bdropkit\b` target missed layout strings by construction; spec § Always do should grow a broader audit on the next user-scope import). (c) **C4**: integration test now reads the raw TOML for `schema-version` rather than comparing `state.schema_version` to `STATE_SCHEMA_VERSION` — `load_state` defaults a missing key to the constant, so the prior assertion was a tautology that wouldn't fail on a regression where install never wrote the field. (d) **C5**: CI scrub/Rail-C steps now distinguish rg's exit codes (0 = hit/fail, 1 = clean, ≥2 = error/fail) so an invalid-pattern or missing-path failure can't masquerade as a no-match pass. (e) **C6**: the AC4a CI step now enumerates the spec's three-skill disposition (file-to-markdown + markdown-to-html carry `evals.json`, msg-to-markdown must not) rather than glob-iterating with a count floor. (f) **N10**: added a `setUp` comment naming the LIFO cleanup-order dependency between `env.stop` and `shutil.rmtree`. (g) **C3/C7**: filed as a follow-on Risk — `make build-self` projecting user-scope packs into the catalogue's own working tree is intentional dog-fooding for this PR, but warrants a follow-on RFC.
