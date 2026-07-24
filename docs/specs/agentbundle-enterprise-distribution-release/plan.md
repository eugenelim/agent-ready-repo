# Plan: agentbundle-enterprise-distribution-release

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Four mechanical file edits land in one PR; a post-merge tag push triggers the
existing release workflow. No new code is introduced. The PR touches four files:

1. `packages/agentbundle/pyproject.toml` — version field only
2. `packages/agentbundle/agentbundle/version.py` — `CLI_VERSION` constant only
3. `packages/agentbundle/CHANGELOG.md` — new `## [0.13.0]` section prepended
4. `packages/agentbundle/README.md` — new `## Enterprise distribution` section inserted

The release workflow (`.github/workflows/release-agentbundle.yml`) runs `build-and-smoke`
on the PR automatically; it asserts tag-vs-pyproject and tag-vs-CLI_VERSION parity at tag
push time, so both version files must be updated atomically. The riskiest step is the tag
push: once `agentbundle-v0.13.0` is pushed and PyPI publishes, the version is permanent.
The gate is: all M1–M6 PRs merged to main and `build-and-smoke` green on this PR.

Verification mode: goal-based check (grep assertions on the four files; CI gate) for
T0–T3; visual / manual QA for T5 (PyPI publish).

## Constraints

- RFC-0072: runtime is Python 3.11 stdlib-only; `dependencies = []` in pyproject.toml;
  no credentials, tokens, or real org endpoints in documentation; all examples use
  `example.test` hostnames.
- RFC-0031: no new runtime dependencies; no server, no daemon.
- The existing release workflow is used as-is — this spec adds no CI surface; changes
  to the workflow require their own spec.
- PyPI Trusted Publisher OIDC is the only allowed publish mechanism; no API token.
- The tag `agentbundle-v0.13.0` must point to a commit on `main`; the workflow enforces
  this with a `git merge-base --is-ancestor` check.

## Construction tests

**Integration tests:** none beyond per-task goal-based checks.

**Manual verification:** T5 — push `agentbundle-v0.13.0`, watch the `release-agentbundle`
workflow, install from PyPI in a fresh venv, confirm `agentbundle --version` → `0.13.0`
and the PyPI package page shows the updated description.

## Design (LLD)

### Design decisions

**`0.13.0` not `0.12.2`.** The three new CLI surfaces (`--format`, `--all`,
`package-catalogue`) qualify as new additive functionality under semver minor semantics.
The 0.x range per RFC-0031 allows minor bumps to be breaking; these three surfaces are
additive, so a patch bump (`0.12.2`) would be technically defensible — but minor is
more informative and matches the initiative's stated semver guidance in RFC-0072 §Change
if accepted. Traces to: AC1–AC3.

**README section placement.** `## Enterprise distribution` goes between `## More commands`
and `## Build your own catalogue` — it describes a usage pattern (enterprise deployment),
not a build-your-own-catalogue concern. Adopters scanning the README see quick start →
common commands → enterprise commands → catalogue authoring → credentials → learn more.
Traces to: AC8–AC11.

**CHANGELOG sections: `### Added` + `### Documentation`.** M1–M5a ship code; M5b and M6
ship documentation only. A separate `### Documentation` section (or equivalent) avoids
conflating code and docs additions, matching the reader's expectation about changelog
format (they look for `### Added` when upgrading to know what broke-vs-new). Traces to: AC5–AC6.

**Version files updated atomically in one PR.** The release workflow's tag-time assertion
checks both `pyproject.toml` and `version.py` before publishing; a two-PR approach would
leave a window where the tag-time check could fail on the first tag attempt. Traces to: AC1–AC2, AC15.

## Tasks

### T0: Pre-flight gate — confirm all M1-M6 PRs are merged and code is present

**Depends on:** none

**Tests:**

_Workspace cross-check_ — spec doc-completion signal only (not a code-merge signal;
workspace.toml `shipped` means "spec + plan authored; adversarial review Clean"):
- All nine spec paths present under `["ini-004".work].shipped` in `workspace.toml`;
  none remain under `active` or `queue`

_Artifact layer_ — authoritative gate; code is actually in the tree (prevent
publishing a wheel whose CHANGELOG describes features absent from the code):
- M1a: `! grep -q 'source.*=.*"agent-ready-repo"' packages/agentbundle/agentbundle/config.py`
  exits 0 (hard-coded PackState default removed; backward-compat mapping in
  `canonicalize_source` is expected and correct)
- M1b: `grep -rF "source_conflict" packages/agentbundle/agentbundle/` exits 0
  (source-conflict guard present)
- M2: `agentbundle list-installed --help | grep -F -- "--format"` exits 0
- M3: `agentbundle upgrade --help | grep -F -- "--all"` exits 0
- M4a: `grep -rF "catalogue+https" packages/agentbundle/agentbundle/` exits 0
- M4a auth: `grep -rF "AGENTBUNDLE_HTTP_BEARER_TOKEN" packages/agentbundle/agentbundle/` exits 0
- M4b: `grep -rF "organization.artifactory" packages/agentbundle/agentbundle/` exits 0
- M5a: `agentbundle package-catalogue --help` exits 0
- M5b: `test -f docs/guides/_shared/how-to/publish-to-artifactory.md` passes
- M6: `test -f docs/guides/_shared/how-to/use-an-artifactory-catalogue.md` passes

**Approach:**
1. Read `workspace.toml` and confirm all nine spec paths appear under `shipped`.
   This is a documentation cross-check, not an authoritative merge signal.
2. Run all ten artifact-layer checks above on the current `main` tree. Any check
   failing means the corresponding M1-M6 implementation is not yet merged — stop here.
3. This is a human verification step; no file change.

**Done when:** All nine workspace.toml paths in `shipped` (cross-check); all ten
artifact checks pass (authoritative gate).

---

### T1: Bump version to 0.13.0 in pyproject.toml and version.py

**Depends on:** T0

**Touches:** `packages/agentbundle/pyproject.toml`, `packages/agentbundle/agentbundle/version.py`

**Tests:**
- `grep 'version = "0.13.0"' packages/agentbundle/pyproject.toml` exits 0
- `grep 'CLI_VERSION = "0.13.0"' packages/agentbundle/agentbundle/version.py` exits 0
- `grep 'version = "0.12.1"' packages/agentbundle/pyproject.toml` exits 1 (old value
  gone)
- `grep 'CLI_VERSION = "0.12.1"' packages/agentbundle/agentbundle/version.py` exits 1
  (old value gone)
- `grep -F "dependencies = []" packages/agentbundle/pyproject.toml` exits 0 (runtime
  deps still empty — RFC-0031 / RFC-0072 constraint)

**Approach:**
1. In `packages/agentbundle/pyproject.toml`: change
   `version = "0.12.1"` → `version = "0.13.0"`. Only this one field changes; no other
   content in the file is touched.
2. In `packages/agentbundle/agentbundle/version.py`: change
   `CLI_VERSION = "0.12.1"` → `CLI_VERSION = "0.13.0"`. Only this constant changes;
   the docstring and all other code are untouched.

**Done when:** All five grep tests pass; `git diff HEAD packages/agentbundle/pyproject.toml`
and `git diff HEAD packages/agentbundle/agentbundle/version.py` each show exactly one
line changed.

---

### T2: Update CHANGELOG — add [0.13.0] entry

**Depends on:** T1

**Touches:** `packages/agentbundle/CHANGELOG.md`

**Tests:**
- `grep -m1 '^## \[' packages/agentbundle/CHANGELOG.md` outputs a line beginning with
  `## [0.13.0] —`
- All seven feature clusters from spec AC5 appear in the entry (grep each keyword
  case-insensitively: `grep -iF "packstate"`, `grep -iF "source conflict"`,
  `grep -iF "list-installed"`, `grep -F -- "upgrade --all"`,
  `grep -F "catalogue+https"`, `grep -F "organization.artifactory"`,
  `grep -F "package-catalogue"`)
- AC6 documentation section present: `grep -F "### Documentation" packages/agentbundle/CHANGELOG.md` exits 0
- M5b acknowledged: `grep -iF "publish" packages/agentbundle/CHANGELOG.md` exits 0
  (the M5b "publishing workflow" entry is present)
- M6 guide filename referenced: `grep -F "use-an-artifactory-catalogue" packages/agentbundle/CHANGELOG.md` exits 0
- `grep 'example\.test\|\.example\.' packages/agentbundle/CHANGELOG.md` confirms
  any hostnames in the entry use example.test (or the entry has no hostname examples)
- No real org names, Artifactory URLs, or tokens appear in the entry
- `test -f docs/guides/_shared/how-to/use-an-artifactory-catalogue.md` passes (the
  M6 guide must exist before T2 references it in the CHANGELOG)
- `test -f docs/guides/_shared/how-to/publish-to-artifactory.md` passes (the M5b
  guide must exist before T2 references it in the CHANGELOG)

**Approach:**

Insert the following block immediately after the prose header (the "All notable changes..."
paragraph and the "The format follows..." line) and before the existing `## [0.12.1]`
section. **Note: replace `2026-07-24` with the actual PR merge date before committing**
— the date below is a placeholder used when this plan was authored; the CHANGELOG
should reflect the date the release PR actually lands on main.

```
## [0.13.0] — 2026-07-24

### Added

- **PackState source provenance** — every installed row now records the actual
  catalogue source used at install time. The historical hard-coded `"agent-ready-repo"`
  literal is removed; source-based operations (conflict detection, upgrade routing,
  update-status) now rest on real provenance data. Implements RFC-0072 / ADR-0036.

- **Source conflict install guard** — installing the same pack name at the same scope
  from a different source is refused before any file, state, or hook is written.
  `--force` does not bypass a source mismatch. The error message identifies the
  conflicting adapters and their respective sources. Same-scope, same-source,
  multi-adapter install is unaffected.

- **`list-installed --format table|json`** — machine-readable JSON output for CI
  pipelines. New status values: `up-to-date` / `upgrade-available` / `ahead` /
  `unknown`; `ahead` is never mis-reported as `up-to-date`. Machine-readable reason
  codes for `unknown` rows (`source-unavailable`, `source-unknown`, `pack-not-found`,
  `unparseable-*-version`, `incompatible-contract`, `adapter-no-longer-supported`,
  `malformed-catalogue`). `--updates-only` filter includes upgrade-available, ahead,
  and unknown rows. Stable JSON contract (`schema_version` 1) with a `sources` array
  and per-row `status_reason` field. Credential-redacted source strings in all output.

- **`upgrade --all --scope repo|user`** — scoped bulk upgrade of all installed packs.
  Each `(pack, adapter)` pair is an independent upgrade row. Preflights all rows
  before any file is written; a blocked row (unknown source, manifest error) prevents
  all writes. Stop-on-first-failure with `completed` / `failed` / `not-attempted`
  outcome tracking. `--yes` required for non-interactive use. Stable JSON contract
  (`schema_version` 1) with per-row `outcome` field and summary. Never silently
  downgrades an ahead row.

- **`catalogue+https://` and `archive+https://` source schemes** — HTTPS-hosted
  catalogue channels for enterprise Artifactory or any static HTTPS server.
  `catalogue+https://` fetches a mutable channel descriptor pointing to an immutable
  versioned archive. `archive+https://` is a direct archive URI with a required
  `#sha256=<digest>` fragment. SHA-256 verified during streaming download before
  extraction. Bearer token auth via `AGENTBUNDLE_HTTP_BEARER_TOKEN` (never persisted,
  never printed, never forwarded across host redirects). Named safety limits:
  descriptor 1 MiB, compressed archive 256 MiB, members 20 000, expanded 1 GiB,
  finite HTTP timeout. Path traversal, absolute paths, symlinks, hard links, and
  special files rejected during extraction.

- **Organization Artifactory bootstrap** — an optional `[organization.artifactory]`
  block in the package's bundled `agentbundle/_data/install-defaults.toml` lets an
  org fork ship a pre-configured default channel. Source precedence: explicit arg →
  user config → org bootstrap → editable clone → packaged default. Fail-closed on a
  malformed `enabled = true` config — no silent fallback to the public source.

- **`agentbundle package-catalogue`** — new CLI command producing the Artifactory
  artifact layout (immutable versioned release archive + mutable channel descriptor
  JSON) from a catalogue repository directory. `--root`, `--bundle`, `--release`,
  `--channel`, `--output` required; `--source-revision`,
  `--minimum-agentbundle-version`, `--published-at`, and `SOURCE_DATE_EPOCH` honored
  as optional reproducibility inputs. Deterministic archive: sorted paths, normalized
  uid/gid/timestamps/modes, reproducible gzip, SHA-256 generated after final bytes.
  Refuses to overwrite an existing release archive by default.

### Documentation

- **Enterprise adoption guide** (`docs/guides/_shared/how-to/use-an-artifactory-catalogue.md`)
  — six documented flows: org bootstrap from a fork, repo-scope CI bulk-upgrade via
  JSON output and PR annotation, user-scope MDM upgrade, source-conflict remediation,
  fully disconnected hosts via local catalogue directory, security controls. All flows
  use `example.test` hostnames; no real credentials appear.

- **Artifactory publishing workflow** — how-to guide and disabled GitHub Actions
  template for the five-step publish sequence (validate → package-catalogue → upload
  archive → upload checksum → verify upload → upload channel JSON last); explicit
  statement that channel JSON is always uploaded last.

- Targeted updates to the existing install, list-installed, upgrade, dry-run, and
  constrained-network guides for enterprise context.
```

**Done when:** First version heading is `## [0.13.0] —`; all seven grep checks pass;
no forbidden content; file parses as valid Markdown.

---

### T3: Update PyPI README — add Enterprise distribution section

**Depends on:** T0

**Touches:** `packages/agentbundle/README.md`

**Tests:**
- `grep -F "## Enterprise distribution" packages/agentbundle/README.md` exits 0
- `grep -F "catalogue+https://" packages/agentbundle/README.md` exits 0
- `grep -F "list-installed --format json" packages/agentbundle/README.md` exits 0
- `grep -F -- "upgrade --all" packages/agentbundle/README.md` exits 0
- `grep -F "package-catalogue" packages/agentbundle/README.md` exits 0
- `grep -F "organization.artifactory" packages/agentbundle/README.md` exits 0
- `grep -F "use-an-artifactory-catalogue.md" packages/agentbundle/README.md` exits 0
- All hostname examples in the new section resolve to `example.test` subdomains (grep
  for non-example.test domains in the new section returns nothing)
- `sed -n '/## More commands/,/## Enterprise distribution/p' packages/agentbundle/README.md | grep -F "ahead"` exits 0 (the existing `## More commands` list-installed prose is updated to include `ahead`, not just the new section)
- `sed -n '/## More commands/,/## Enterprise distribution/p' packages/agentbundle/README.md | grep -F "list-installed" | grep -F -- "--format"` exits 0 (same prose updated to mention `--format json`, not just the new section)
- `test -f docs/guides/_shared/how-to/use-an-artifactory-catalogue.md` passes (the
  M6 guide must exist before T3 cross-references it in the README)

**Approach:**

1. **Update existing prose (Concern 6 fix):** In the `## More commands` section, the
   paragraph starting "`**list-installed**` reads your state files..." lists statuses
   as `up-to-date` / `upgrade-available` / `unknown`. Update it to include `ahead` and
   note `--format json` so the existing section does not contradict the new one.
   Specifically, update that paragraph to read: "...and an `up-to-date` /
   `upgrade-available` / `ahead` / `unknown` status; `--format json` emits a stable
   JSON contract (`schema_version` 1) for CI pipelines..."

2. **Insert the new section:** Insert the following block between `## More commands`
   (ending around line 71 of the current README) and the existing `## Build your own
   catalogue` section. The insertion point is after the paragraph ending "...rather than
   hang.":

```
## Enterprise distribution

For organizations running an internal Artifactory mirror or any static HTTPS server,
agentbundle's enterprise distribution capabilities handle the full adoption loop —
from org-wide channel configuration to CI-driven bulk upgrades.

**Install from an internal Artifactory channel:**

```bash
# Point agentbundle at your org's channel descriptor (one-time per machine,
# or pre-configured in your org fork — see Org bootstrap below)
agentbundle config set source catalogue+https://artifactory.example.test/agentbundle/catalogues/core/channels/stable.json

agentbundle install --pack core
```

The channel descriptor points to an immutable versioned archive; agentbundle
fetches, verifies its SHA-256 digest, and installs. Pass a bearer token via
`AGENTBUNDLE_HTTP_BEARER_TOKEN` — it is never stored in state, never printed, and
never forwarded to a different host.

**JSON output for CI pipelines:**

```bash
# See what's installed and what needs upgrading — machine-readable
agentbundle list-installed --format json
agentbundle list-installed --format json --updates-only
```

Returns a stable JSON contract (`schema_version` 1) with per-row status
(`up-to-date` / `upgrade-available` / `ahead` / `unknown`) and machine-readable
reason codes for unknown rows. Pipe into `jq` or your CI annotation step.

**Bulk upgrade in one scoped command:**

```bash
# Upgrade all installed packs in a scope — preflights before any write
agentbundle upgrade --all --scope repo --yes
agentbundle upgrade --all --scope user --format json --yes
```

Preflights all rows before writing anything; a blocked row stops the run before the
filesystem is touched. Partial failure is reported honestly — not described as a
rollback. Never silently downgrades an `ahead` row.

**Package your catalogue for Artifactory:**

```bash
agentbundle package-catalogue \
  --root /path/to/catalogue \
  --bundle my-packs \
  --release 1.0.0 \
  --channel stable \
  --output dist/
```

Produces a deterministic, reproducible gzip archive (versioned) and a mutable channel
descriptor JSON (`stable.json`), ready to upload to Artifactory. Identical inputs
produce byte-identical archives (honors `SOURCE_DATE_EPOCH`).

**Org bootstrap — ship the default channel in your fork:**

Add an `[organization.artifactory]` block to
`agentbundle/_data/install-defaults.toml` in your org's agentbundle fork:

```toml
[organization.artifactory]
enabled = true
base-url = "https://artifactory.example.test"
repository = "agentbundle"
bundle = "core"
channel = "stable"
```

Developers installing from your fork get the internal channel without a manual
`config set source` step. The block ships `enabled = false` in the public package.
A malformed `enabled = true` config fails closed — no silent fallback to the public
source.

See the full enterprise adoption guide at
`docs/guides/_shared/how-to/use-an-artifactory-catalogue.md` for all six flows
(org bootstrap, repo-scope CI upgrade, user-scope MDM, source-conflict remediation,
disconnected hosts, and security controls).
```

**Done when:** All ten grep tests pass; `twine check --strict dist/*` exits 0 after
`python -m build` from `packages/agentbundle/`; the new section appears between
`## More commands` and `## Build your own catalogue` in the file; the existing
`list-installed` prose in `## More commands` now names `ahead` and `--format json`.

---

### T4: Open PR and verify build-and-smoke

**Depends on:** T1, T2, T3

**Tests:**
- `build-and-smoke` job on the PR completes green (all steps pass)
- `python -m build` exits 0 locally in `packages/agentbundle/`
- `twine check --strict dist/*` exits 0 locally (strict mode: zero warnings)
- `python -c "from agentbundle.cli import main"` exits 0 in a fresh venv with the
  built wheel installed
- `agentbundle --version` in that same fresh venv reports `0.13.0` (covers AC3 before
  PyPI publish)

**Approach:**
1. Stage all four changed files: `pyproject.toml`, `version.py`, `CHANGELOG.md`,
   `README.md`.
2. Commit with message: `feat(agentbundle): 0.13.0 — enterprise distribution release`.
3. Open PR targeting `main`; title: "feat(agentbundle): 0.13.0 — enterprise distribution
   release". PR body must note: (a) this is the release coordination PR for ini-004;
   (b) all nine M1–M6 PRs must be merged to main before the tag is pushed; (c) the tag
   push is a separate step after merge.
4. Confirm `build-and-smoke` passes automatically on the PR.
5. Run local build verification: `cd packages/agentbundle && python -m build && twine check --strict dist/*`.

**Done when:** PR open with green `build-and-smoke`; local build and twine check exit 0;
all four changed files reviewed.

---

### T5: Post-merge tag push and PyPI publish verification

**Depends on:** T4 (PR merged to main)

**Tests:**
- `git tag -l agentbundle-v0.13.0` lists the tag after push
- `release-agentbundle` workflow `build-and-smoke` job completes green for the tag push
- `release-agentbundle` workflow `publish-pypi` job completes green
- `pip install agentbundle==0.13.0` in a fresh venv on a separate machine exits 0
- `agentbundle --version` in that venv reports `0.13.0`

**Approach:**
1. After the PR merges to main, re-run the T0 artifact-layer checks on the merged main
   tree to confirm all M1–M6 code is present.
2. Pre-tag sanity checks (prevent double-publish):
   - `git tag -l agentbundle-v0.13.0` — must be empty (tag does not yet exist)
   - `pip index versions agentbundle 2>/dev/null | grep -F "0.13.0"` or `curl -s
     https://pypi.org/pypi/agentbundle/json | python3 -c "import sys,json; v=json.load(sys.stdin)['releases']; sys.exit(0 if '0.13.0' not in v else 1)"` — 0.13.0 must
     not already be on PyPI. If 0.13.0 is already on PyPI, stop and consult the
     release owner before proceeding.
3. Push tag: `git tag agentbundle-v0.13.0 && git push origin agentbundle-v0.13.0`.
4. Monitor the `release-agentbundle` workflow run triggered by the tag push:
   - Verify `build-and-smoke` passes (tag-vs-pyproject assertion, tag-vs-CLI_VERSION
     assertion, tag-on-main ancestry assertion, wheel build, twine check, smoke install,
     `agentbundle --help`).
   - Verify `publish-pypi` completes (Trusted Publisher OIDC handshake succeeds).
   - Note: `publish-artifactory` will report `configured=false` and skip unless the
     org has configured Artifactory secrets — this is expected.
5. Install verification: from a clean Python 3.11+ venv on a different machine or in
   a fresh CI environment, run `pip install agentbundle==0.13.0` and then
   `agentbundle --version`. Expected: `0.13.0`.
6. Visit `https://pypi.org/project/agentbundle/0.13.0/` and confirm the long description
   includes the `## Enterprise distribution` section.
7. Update `workspace.toml ["ini-004".work]`: move `spec/agentbundle-enterprise-distribution-release`
   from `active` to `shipped`.

**Done when:** PyPI shows version 0.13.0 with enterprise distribution description;
`agentbundle --version` reports `0.13.0` from a clean install; workspace.toml updated.

## Rollout

- **Delivery:** four file edits in one PR, then a post-merge tag push. The tag push
  triggers `.github/workflows/release-agentbundle.yml` which publishes to PyPI via
  Trusted Publisher OIDC. Irreversible: once `agentbundle-v0.13.0` is on PyPI, the
  version is permanent in the pre-1.0 window (PyPI does not allow deletion of a version
  once it has been downloaded). Rollback path: yank `0.13.0` from PyPI (marks it
  unavailable to new installs; existing installs unaffected) if a critical defect is
  found, then issue `0.13.1` as a fix.
- **Infrastructure:** no new infrastructure. The existing GitHub Actions environment
  `pypi` with Trusted Publisher OIDC is already configured.
- **External-system integration:** PyPI Trusted Publisher OIDC must be active for
  `eugenelim/agent-ready-repo` under the `pypi` environment. No new configuration
  required.
- **Deployment sequencing:** (1) all nine M1–M6 PRs merge to main → (2) release PR
  lands (version bump + CHANGELOG + README) → (3) tag pushed → (4) workflow publishes
  to PyPI. Steps 1 and 2 are independent of each other (can merge in either order,
  but both must precede step 3). The tag in step 3 is the hard sequencing gate.

## Risks

- **M1–M6 PR not yet merged at tag time.** If any upstream PR is still open when the
  tag is pushed, the published wheel would not contain the feature its CHANGELOG entry
  describes. Mitigation: T0 and T5 step 1 are explicit human-verified gate checks
  including artifact-layer assertions; do not push the tag without running them.
- **CLI_VERSION drift.** If `version.py` is not updated alongside `pyproject.toml`,
  the release workflow's tag-time assertion will fail the entire workflow before any
  publish occurs. Mitigation: T1 updates both files atomically in the same commit.
- **README renders poorly on PyPI.** If the new section introduces Markdown that
  PyPI's renderer does not support (e.g., nested code blocks inside list items), the
  long description may render as raw Markdown. Mitigation: T3 runs `twine check --strict`
  locally; AC12 requires strict-mode zero warnings.
- **Publish-artifactory partial-credential warning.** If exactly one or two of the
  three Artifactory secrets are set (e.g., only `ARTIFACTORY_TOKEN`), the workflow
  emits `::warning::` and skips Artifactory without failing. This is intended behavior
  per the existing workflow and spec/agentbundle-wheel-release AC9; it is not a bug.

## Changelog

- 2026-07-24: initial plan.
- 2026-07-24: adversarial review pass 1 — T0 strengthened with artifact-layer CLI
  checks and guide-file existence check (Blocker 1 + Blocker 2); T2 adds guide-file
  existence test; T3 adds existing-prose update for `ahead`/`--format json` (Concern 6)
  and `twine check --strict` (Concern 3); T4 adds `agentbundle --version` assertion
  (Nit 8); T5 adds pre-tag checks for existing tag and PyPI version (Concern 4); T1
  adds `dependencies = []` assertion (Nit 7). Spec updated: AC11 pins exact guide
  path; AC12 clarifies strict-mode is local-only; AC13 adds artifact-layer checks.
- 2026-07-24: adversarial review pass 2 — T0/AC13 grep patterns fixed from
  `\-\-all`/`\-\-format` (never matches) to `grep -F -- "--all"` / `grep -F -- "--format"`
  (Blocker 1); T2 keyword grep case-insensitive for "source conflict" and "PackState"
  (Concern 3); T3 adds guide-file existence test + fixes `--format` grep pattern
  (Concern 4 + Blocker fix); AC9(a) URL aligned to include repository segment
  `/agentbundle/` matching RFC-0072 D2 (Concern 2); AC12 clarifies strict-mode is
  a local-only gate since CI uses non-strict (Concern 5); T0 approach step count
  corrected to "six" (Nit 6); AC4 verifier says "beginning with" (Nit 7).
- 2026-07-24: adversarial review pass 3 — T0 rewritten to distinguish workspace
  cross-check (doc-completion signal) from artifact layer (authoritative code-presence
  gate); M1a (PackState literal absence), M1b (source-conflict grep), M5b
  (publish-to-artifactory.md existence) added to artifact layer; AC13 rewritten to
  match (Blockers 1+2); T2 adds `### Documentation` section check and M5b/M6
  file greps (Concern 3); T3 `ahead`/`--format` greps scoped to More-commands
  region via `sed` (Concern 4); T3 `Depends on: T0` (Nit 5); CHANGELOG date
  placeholder note added (Nit 6).
- 2026-07-24: adversarial review pass 4 — T3 `--format` verifier piped through
  `grep -F "list-installed"` to avoid false-positive from unrelated `show` examples
  (Concern 1); T4 approach step 5 adds `--strict` to `twine check` (Concern 2);
  spec AC13(b) M4a split into M4a + M4a-auth bullets so count reconciles with T0
  "ten checks" (Nit 3); M1a grep-c replaced with `! grep -q` exit-code form in
  both files (Nit 4).
