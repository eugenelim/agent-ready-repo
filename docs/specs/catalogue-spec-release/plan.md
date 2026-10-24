# Plan: Release 0.1 of the catalogue specification

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `tools/catalogue_spec_site.py` (`draft_bytes` byte splice, `page_name`, `generate`) and `tools/test_catalogue_spec_site.py`; `tools/catalogue/sync_contract_inventory.py:46-63` (`_check_path`, the stdlib path-confinement routine to reuse) with `load_manifest`, `ContractRow`, `ManifestError`, and their existing gated tests in `tools/test_contract_parity.py:124-187`; `tools/catalogue/check_contract_parity.py:25-41` (path-loading that loader); `tools/repo/build_gate_chain.py:246-249` (`check-contract-parity` as `_script_step`) and `:632-633` (`test-codeql-workflow` as the hyphenated-workflow-test precedent); `Makefile:607` (`test-pages-workflow.py` invocation) and `Makefile:698-718` (the hand-enumerated `run-test-suite` line anchored at `tools/test_contract_parity.py`); `tools/test_marketplace_envelope_parity.py:731-746` (`_assert_gate_wiring` — that Makefile group and `.github/workflows/build-check.yml:915-934` must be the same set) and `tools/test_local_ci_shared_test_deduplication.py:324-404,1059-1064` (`FINAL_TOOL_BATCH` and the two approved plan digests, which any addition to that line moves); `tools/capture-publish-control-evidence.py:282-313` (`_NoRedirect` opener, literal host, `timeout=30`, documented bandit suppression — the stdlib outbound-HTTP shape); `.github/workflows/pages.yml` and `tools/test-pages-workflow.py:361-369`; `.github/workflows/release-agentbundle.yml:132-135,343-362`; `packages/agentbundle/agentbundle/version.py` and `cli.py:156`; `docs/guides/how-to/cut-a-package-release.md`

## Approach

The slice lands in one pull request. RFC-0109 § How a release flows does
describe the `$id` rewrite and the release as separate pull requests, and the
checks admit that split — check 2 accepts an unreleased version with no
snapshot, and check 3's rendered half accepts a deployed `index` with zero
releases. So the unit is divisible, and T1 is a two-way-door change that could
ship first. It is kept together here because the owner is reviewing one
one-way-door change and the rewrite has no value on its own; the spec's
`Ask first` records the split as the owner's call.

The order is: mint the identifiers, freeze them, check them, serve them, then
report them. T1 rewrites the `$id`s. T2 writes the snapshot and the release
row, teaches the loader to read and confine it, and adds the bundled member
inventory with its check-1 rule. T3 and T4 add the two checks that run inside
the repository tree. T5 serves the version from the snapshot. T6 adds check 3's
rendered half. T8 changes the package, and T7 then adds check 4, which reads
what T8 bundles. T9 writes the how-to so the next version is cuttable without
re-reading this plan, and T10 routes every suite this slice created.

The riskiest parts are check 3's two halves: they are the tamper control, and a
control that cannot fail is not a control. Each half carries falsification
tests that mutate a released artifact and assert the check goes red, and each
test runs from a named gate rather than by hand.

## Constraints

- RFC-0109 D3: a released `$id` never changes; `latest/` files are byte copies, not rewrites; the CLI version line stays independent of the specification version.
- RFC-0109 D7: check 3's reference is anchored outside the pushed commit, and fails closed.
- `tools/AGENTS.md`: new `tools/` additions are pure-stdlib `.py`. A hyphenated `tools/test-*.py` is a standalone entry point a directory sweep does not collect.
- `tools/AGENTS.md` roster obligations, both directions: a new `build-check.yml` step needs a `STEP_DISPOSITION` entry on both axes; a new target on a Makefile `run-test-suite` line needs a `SUITE_DISPOSITION` entry per target. A gate added *inside* `build_gate_chain.py` adds no workflow step and needs no `STEP_DISPOSITION`; confirm by running `tools/lint-ci-parity.py`, not by assuming.
- Root `AGENTS.md`: no blessed outbound-HTTP helper exists, so this slice sets the convention; it must not cut trust-boundary validation. The exemplar at `tools/capture-publish-control-evidence.py:282-313` demonstrates the `_NoRedirect` opener, the literal host and `timeout=30` — but it reads its body unbounded, so the 1 MiB ceiling is the part this slice adds rather than copies. `tools/AGENTS.md`'s pure-stdlib rule makes `_check_path` — not `agentbundle.catalogue_tooling.file_safety` — the reusable confinement form in `tools/`.
- `packages/AGENTS.md`: bump `version.py` and `pyproject.toml` together; package tests must not read repository paths.
- Root `AGENTS.md`: shipped package source, messages and package tests cite no RFC/ADR/spec identifiers.
- `docs-site/AGENTS.md`: edit sources, never generated content; `web/` builds before `docs-site/`.
- Adding a module to the `run-test-suite` line anchored at `tools/test_contract_parity.py` obliges three further edits: the matching pytest list in `.github/workflows/build-check.yml:915-934` (set-equality, enforced by `tools/test_marketplace_envelope_parity.py`), and `FINAL_TOOL_BATCH` plus both approved plan digests in `tools/test_local_ci_shared_test_deduplication.py`, whose comment block requires a recorded sole-cause and prior-pins-were-current disposition with the re-pin.
- `web/src/test/rendered-output.test.ts` carries a `DOCS_PAGE_BUDGET`; 0.1 and `latest/` add roughly 22 pages.

## Construction tests

T6's rendered half and T8's manual QA span earlier tasks, because each reads a
real build rather than a fixture.

## Durable-output map

| Spec durable output | Task |
| --- | --- |
| Published interface (`0.1/` URLs and `$id`s) | T1, T5 |
| Released artifact (snapshot and release row) | T2 |
| Tamper control (check 3, both halves) | T4, T6 |
| Release control (check 4) | T7 |
| Adopter guidance (0.1 overview) | T5 |
| Maintainer procedure (how-to) | T9 |
| Gate routing for every new check and suite | T3, T4, T6, T7, T10 |
| Bundled member inventory the CLI reads | T2 (generated), T8 (consumed) |

## Design (LLD)

### Component / module decomposition

**Shared JSON-schema-member predicate.** *Owned by: T1*, because T1's rewrite
tool is its first consumer and AC 1 forbids a second copy anywhere.
`sync_contract_inventory` gains one exported helper returning the manifest's
member rows whose `path` ends in `.json`. The rewrite tool (T1), the inventory
generator (T2) and check 2 (T3) all call that one helper by the existing
path-load route — `check_contract_parity.py:26-43` already loads
`sync_contract_inventory` by `spec_from_file_location`, so a new tool or check
reaches it the same way — so the three cannot drift apart when a member is added. Today
`.json`, `.schema.json` and "parses as JSON" all yield the same 8, which is
exactly why a disagreement would stay invisible without a single source.

**`tools/catalogue/rewrite_member_ids.py`** (new, stdlib). *Owned by: T1.*
Reuses the byte-splice approach `catalogue_spec_site.draft_bytes` proves: find
the top-level `$id` line, replace the value span, or insert the line after the
opening brace; same for `$schema`. Re-parses and asserts the result to refuse a
bad splice. Takes `--version`, writes `contracts/` and the `_data/` copies, and
is idempotent. It is the tool check 2 names.

**`contracts/catalogue-spec.toml` release rows.** *Owned by: T2.* A release
row carries `version`, `date`, `adapter_contract`, and **two separately keyed
digest tables** — `members` (the 10 member files) and `pages` (the narrative
page sources), each mapping a snapshot-relative path to its SHA-256. Two tables
rather than one flat map, because AC 6, AC 11, AC 12 and AC 15 each need to tell
a member digest from a page-source digest, and the manifest's `member` rows are
explicitly ruled out as that discriminator (a member added after 0.1 must change
no `0.1/` output). A correction row carries `version`, `date`, `note`,
`supersedes`, and a `pages` table only — never a `members` table. The governing
correction row for a version is the head of its rooted `supersedes` chain, so
row order is inert. `load_manifest` grows
`ReleaseRow` and `CorrectionRow` dataclasses and validation raising
`ManifestError`; every path key passes `_check_path` rooted at that release's
snapshot directory before any read. That routine currently hard-codes its error
label as `contract row {index}` (`sync_contract_inventory.py:47`), so it takes a
caller-supplied label here, letting a rejected release path name the release row
and its version as AC 4 requires. It keeps rejecting a non-list `release`.

**`tools/catalogue/check_spec_version.py`** (new). *Owned by: T3.* Check 2.
Reads member `$id`s, asserts one version V, compares member bytes to the latest
snapshot, and requires V to be the latest release on a match and an unreleased
version with no snapshot otherwise. Its failure message names
`rewrite_member_ids.py`.

**`tools/catalogue/check_release_immutability.py`** (new). *Owned by: T4.*
Check 3's tree half. It picks its anchor by event, reading the event name from
`GITHUB_EVENT_NAME` and the pre-push value from the event payload's `before`:
on a `pull_request`, the merge base with the base branch — the
`f"{base}...HEAD"` form `tools/lint-catalogue-curation-guard.py:199` uses; on a
`push` to `main`, the ref's pre-push value, measuring every commit in the push;
on a `workflow_dispatch`, which carries no pre-push value, the pushed commit's
first parent; and with no event name at all — every local `make build-check` —
the merge-base form. It then reads the anchor manifest and snapshots via
`git show`, and requires every released row, correction row, path and member
digest to survive unchanged in the head tree. It names the event and the anchor
commit in its own output, marking a first-parent-anchored run as
self-consistency evidence. Fails closed when the anchor is unavailable, or when
a pre-push value is not an ancestor of the tip.

**`tools/check-deployed-release-parity.py`** (new). *Owned by: T6.* Check 3's
rendered half. Builds a `_NoRedirect` opener against a literal
`https://eugenelim.github.io` host, with a 30-second timeout and a 1 MiB
bounded read, and no environment or workflow input in the URL. The opener is
built without the default environment-reading `ProxyHandler` — `build_opener`
installs one that honours `https_proxy`, which would let a workflow-level
environment variable move the anchor without touching this script — and the
server certificate is validated by an explicitly constructed context with
verification and hostname checking on, whose trust anchor comes from neither
`SSL_CERT_FILE` nor `SSL_CERT_DIR`. Verified on this worktree's Python 3.13.13:
a non-existent `SSL_CERT_FILE` makes `ssl.create_default_context()` load zero
CAs, so the variable does reach the trust root. `PYTHONHTTPSVERIFY=0` did not
weaken the context there and is not part of this control. No third-party CA
bundle is available, per `tools/AGENTS.md`'s pure-stdlib rule. Accepts a body only when
it is a 200 that parses as JSON and carries an explicitly present `releases`
array; every other outcome fails. For every release it lists, requires the
built site to carry each released path with bytes matching the digest that
fetched entry carries for that release; no in-checkout manifest row supplies a
comparison digest. It reads no path inside the checkout or the build output as the anchor. On a
`workflow_dispatch` run whose ref is not `main` it skips explicitly and prints
the skip, per RFC-0109 D7 check 3 — that build cannot deploy, so there is
nothing for the live anchor to govern, and a fail-closed run there would red
every feature-branch dispatch.

**`tools/catalogue/check_release_gate.py`** (new, stdlib). *Owned by: T7.* Check
4. Reads V from the `$id`s of the bundled JSON-schema members, then compares
bytes over the key set of V's release-row `members` table — all 10 members,
derivable from the row alone, never from the bundled inventory, because the
build-check chain that holds that inventory to the manifest does not run in this
workflow. The row's `pages` table is not compared: the package bundles no page
sources. It requires a snapshot and release row for V in the tagged commit,
requires the bundled member bytes to equal that snapshot, requires the bundled
inventory to list exactly the JSON-schema subset of that `members` key set, and requires the fetched deployed
`index` to list V with the same member digests. Shares the opener, ceiling and
index-acceptance predicate with check 3's rendered half.

**Bundled member inventory.** *Owned by: T2.* `sync_contract_inventory` gains
a second generated output, `_data/catalogue-members.txt`, listing the manifest's
`member` rows whose file is a JSON schema — today 8 of the 10, excluding
`adapter.toml` and `target-vocab.toml`, which AC 1 leaves without an `$id`.
`check_contract_parity.py` gains a rule holding that file to the same derived
set, beside its existing `public-contracts.txt` rule. Both are repository tools,
so both are verified in `tools/test_contract_parity.py`; the package side only
consumes the file.

**Site generation.** *Owned by: T5.* `catalogue_spec_site.generate` gains a
released-version pass driven by the manifest's release rows. For each release
it reads that release's snapshot and the key set of that release row's
`members` table — not `contracts/`, not the manifest's `member` rows, and not
the row's `pages` table, which drives no raw file and no index entry — and writes pages, raw files and the
index entry. `latest/` copies the newest release's raw bytes verbatim. Its redirect
targets are generated rather than hand-maintained: the generator writes
`docs-site/src/generated/spec-latest-redirects.json` (generated, gitignored),
and `docs-site/astro.config.ts` reads that file once and spreads it into its
existing `redirects:` block, treating an absent file as empty. The file is a
flat object matching that block's existing asymmetry: a base-relative key
(`/spec/catalogue/latest/pack-schema-json/`) mapping to a base-absolute value
(`/agent-ready-repo/docs/spec/catalogue/0.1/pack-schema-json/`). Writing both
sides alike would build green and resolve nowhere, so the generator composes
each side separately. That keeps the
config a hand-written source file, as `docs-site/AGENTS.md` requires, while the
generator owns the data — so a later release repoints `latest/` with no config
edit. `draft/` keeps reading live `contracts/`.

**CLI version report.** *Owned by: T8.* `version.py` gains
`catalogue_spec_version()`, a function rather than an import-time constant —
but that alone is not enough. `cli.py:186-189` registers `--version` as
`action="version", version=_version_string()`, which argparse evaluates while
`_build_parser()` runs, on every invocation and before the subcommand is known;
a function behind an eagerly evaluated argument is still eager. So `--version`
moves to a small `argparse.Action` subclass that computes the string when the
flag fires. Only then does a malformed bundled `$id` fail just the two reports
and leave every other command working, and only a test driving the real CLI
entry point can show it. It reads the members named in
`_data/catalogue-members.txt` through the same `importlib.resources` route
`SPEC_VERSION` uses, failing closed and naming that file when it is absent,
unreadable, empty or zero-entry, and `catalogue contracts list --format json` gains the
`{"catalogue_specification": ..., "contracts": [...]}` envelope — a documented
breaking change to that output, the owner's decision on 2026-10-22.

### Interfaces & contracts

- `rewrite_member_ids.py --version <MAJOR.MINOR>` → exit 0, tree rewritten; re-running changes nothing.
- Each check script → exit 0 ok / 1 fail, failures on stderr, matching `check_contract_parity.py`'s shape.
- `agentbundle --version` → `agentbundle 0.56.0 (spec <adapter>, catalogue specification 0.1)`.

### Gate routing

Every new artifact gets a named route, because an ungated falsification test
proves nothing:

| Artifact | Route | Disposition entry |
| --- | --- | --- |
| `check_spec_version.py` | `_script_step` in `build_gate_chain.py` | none — adds no workflow step |
| `check_release_immutability.py` | `_script_step` in `build_gate_chain.py` | none — adds no workflow step |
| `tools/test_rewrite_member_ids.py`, `test_check_spec_version.py`, `test_check_release_immutability.py`, `test_check_deployed_release_parity.py`, `test_check_release_gate.py` | added to **both** the `Makefile:698-718` `run-test-suite` line and the matching `.github/workflows/build-check.yml:915-934` pytest list, which must stay the same set; plus the `FINAL_TOOL_BATCH` and two plan-digest re-pins in `tools/test_local_ci_shared_test_deduplication.py` | `SUITE_DISPOSITION` per target, and the re-pin's sole-cause and prior-pins-current disposition |
| `tools/test-release-agentbundle-workflow.py` | `_script_step`, as `test-codeql-workflow` is wired; asserted in T7's `Done when` by running the chain | none — adds no workflow step |
| `check-deployed-release-parity.py` | a `pages.yml` step before `upload-pages-artifact`, plus both `paths:` filters | not a `build-check.yml` step |
| `tools/catalogue/check_release_gate.py` | a gate job in `release-agentbundle.yml` that both publish jobs need | not a `build-check.yml` step |

## Tasks

Every suite this slice creates is registered once, in T10, after all of them
exist — so the batch-digest re-pin has a single recorded cause rather than five.
Until T10 lands, each task's suite is run directly; T10 is what makes AC 23 true.

### T1: Absolute `$id`s, the rewrite tool, and the registry row

**Depends on:** none

**Edit sites:** `contracts/*.schema.json` and their `_data/` copies, `tools/catalogue/rewrite_member_ids.py` (new), `tools/catalogue/sync_contract_inventory.py` (the shared JSON-schema-member predicate only), and `contracts/REGISTRY.md`.

The registry row lands here, first, not in T9. `tests/roster/test_contract_backward_registry.py` derives its pair set by globbing `docs/specs/*/spec.md` on disk, so creating this spec already turned that suite red — verified on this worktree, reporting `('contracts/catalogue-spec.toml', 'docs/specs/catalogue-spec-release')`. `gate-main` collects every roster module on every pull request, so leaving the one-line row until the ninth task keeps the branch's gate red through T1-T8 for a cause unrelated to any of them.

**Tests:** `tools/test_rewrite_member_ids.py` (new):
- A schema with a top-level `$id` has only its value span replaced; every other byte is equal (AC 2).
- A schema without one gains exactly the `$id` line after the opening brace; a schema without `$schema` gains exactly that line; every other byte is equal (AC 2).
- Running twice produces the same bytes as running once (AC 2).
- A non-member file, and a file the splice would not re-parse, are refused.
- The shared JSON-schema-member predicate returns exactly the `.json` member rows, and the rewrite tool resolves its set from that helper rather than its own copy (AC 1).
- On the real tree: all 8 JSON members carry the `0.1/` `$id` and a `$schema`; the 2 TOML members are byte-unchanged (AC 1).

**Done when:** the suite passes, `python3 tools/catalogue/check_contract_parity.py` exits 0, `./.venv/bin/python -m pytest tests/roster/test_contract_backward_registry.py -q` passes (AC 24), and — since this task's edit sites touch `packages/agentbundle/_data/` — `python3 tools/lint-catalogue-curation-guard.py --root . --base origin/main` passes after a fetch, proving the `Engine-Change-RFC: RFC-0109` trailer is present (AC 21).

### T2: Snapshot, release row, correction row and loader confinement

**Depends on:** T1

**Edit sites:** `docs-site/spec-src/catalogue/overview.md` (**first** — see below), `contracts/catalogue-spec.toml`, `contracts/releases/catalogue/0.1/`, `tools/catalogue/sync_contract_inventory.py` (second generated output), `tools/catalogue/check_contract_parity.py` (the rule holding it), and the regenerated `_data/` copies.

The released page sources reach their final bytes **here, before the snapshot is taken**. `docs-site/spec-src/catalogue/` holds one file, `overview.md`, it is the prose the generator reads, and today it carries no adopter guidance and still says "No released version is published yet." AC 16's four adopter options and the same-deploy warning must therefore land in it *before* T2 copies it into `contracts/releases/catalogue/0.1/` and digests it. Editing it after the snapshot would either strand a stale copy — which the Agent Rule requiring released pages to build from the snapshot then serves — or red T2's digest assertion with no task owning the re-stamp, and changing a released digest is an `Ask first` item. T5 therefore edits no page source; it asserts the generated page.

**Tests:** `tools/test_contract_parity.py` (extend — the loader's and the generator's existing gated test home):
- Update the real-tree `release = []` assertion at line 147 to the post-release manifest shape. The `release = []` fixture prefixes elsewhere in that module stay valid and do not move (AC 4).
- A well-formed release row parses with its version, date, adapter contract version, and its `members` and `pages` tables kept as separate key spaces (AC 4).
- The inventory generator resolves its member set from T1's shared predicate rather than its own copy (AC 1, AC 19).
- A row missing a member digest, carrying an unknown path, a non-string digest, or a `version` not matching `^[0-9]+\.[0-9]+$` raises `ManifestError` naming the row (AC 4).
- One rejection case per escape shape — absolute, `..`, backslash, drive letter, non-regular file, outside the snapshot root — for both path keys and the `version` segment (AC 5).
- A second release row whose `version` compares numerically equal to another's is rejected, naming the duplicate row — `0.1` against `0.01` — and `0.10` sorts above `0.9` rather than below it (AC 4, AC 6).
- A release row whose `members` and `pages` tables share a key after AC 5 resolution is rejected, including the alias form `./pack.schema.json` beside `pack.schema.json` (AC 4).
- A correction row carrying a `members` table is rejected; one whose `pages` carries a key outside that version's release-row `pages` key set is rejected; one carrying only in-set `pages` keys is accepted; one naming a version with no release row is rejected; a missing, duplicated, cyclic or dangling `supersedes` link is rejected; the governing row is the chain head, so reordering two correction rows changes nothing; "latest release" ignores correction rows (AC 6).
- Before the snapshot is taken, `overview.md` carries AC 16's four adopter options and the same-deploy warning, and no longer calls itself the draft or says no release is published — asserted here, so an incomplete edit surfaces before the digest is frozen rather than in T5 (AC 16).
- `_data/catalogue-members.txt` is generated with exactly the manifest's JSON-schema member rows; `adapter.toml` and `target-vocab.toml` are absent from it; a JSON member added to a fixture manifest appears with no code change (AC 19).
- Check 1 fails when that file drifts from the derived set — an added, dropped or reordered entry (AC 19).
- On the real tree: every snapshot file's SHA-256 equals its release-row digest, and the snapshot holds all 10 members plus every page source (AC 3, AC 4).

**Done when:** `tools/test_contract_parity.py` passes through its existing route, `python3 tools/catalogue/check_contract_parity.py` exits 0, and `python3 tools/lint-catalogue-curation-guard.py --root . --base origin/main` passes after a fetch — this task regenerates the `_data/` copies (AC 21).

### T3: Check 2 — version consistency

**Depends on:** T2

**Tests:** `tools/test_check_spec_version.py` (new):
- The real tree passes: all `$id`s name 0.1, member bytes equal the 0.1 snapshot, 0.1 is the latest release (AC 7).
- **Falsification:** one member `$id` moved to another version fails; member bytes differing from the snapshot while `$id`s still name the latest release fails; member bytes differing with `$id`s naming an unreleased version that has no snapshot passes (AC 7).
- The failure message contains `rewrite_member_ids.py` (AC 2).
- All three consumers — the rewrite tool, the inventory generator and this check — resolve the same member set from T1's single shared predicate; this is the first task in which all three exist (AC 1).

**Done when:** the suite passes, the `_script_step` runs it in the gate chain, and `make lint-ruff lint-mypy` is green.

### T4: Check 3, tree half — append-only snapshots

**Depends on:** T2

**Tests:** `tools/test_check_release_immutability.py` (new), against fixture git trees:
- Head equal to base passes; head adding a new release row and snapshot passes (AC 8).
- **Falsification, one case each:** a deleted release row, an edited release row (a changed `date`, `adapter_contract` or `pages` key), an edited member digest, an edited snapshot member file, and a deleted snapshot file each fail — five cases for AC 8's five mutations (AC 8).
- An unavailable base ref fails rather than passes (AC 8).
- A `main`-push fixture measures every commit in the push against the ref's pre-push value: a mutation in the tip commit fails, and so does one in an earlier commit of the same multi-commit push — the case a first-parent anchor would have passed (AC 8).
- A push whose pre-push value is absent, or is not an ancestor of the tip, fails closed (AC 8).
- A `workflow_dispatch` fixture, which carries no pre-push value, takes the first-parent anchor (AC 8).
- The check's output names the event and the anchor commit it measured, and marks a first-parent-anchored run as self-consistency evidence — asserted on that output, so the claim has something that can fail (AC 8).
- A snapshot page-source edit with a matching correction row passes; the same edit without one fails (AC 8).
- A deleted correction row fails; an edited correction row fails; appending a newer correction row that supersedes an existing one passes (AC 8).
- A stale-branch fixture — a branch cut before a later release row landed on the base branch — passes, proving the merge-base anchor does not false-alarm (AC 8).

**Done when:** the suite passes and the `_script_step` runs it in the gate chain.

### T5: Serve 0.1 and latest/, repoint navigation, adopter guidance

**Depends on:** T2

**Edit sites:** `tools/catalogue_spec_site.py`, `docs-site/astro.config.ts` (read-and-spread of the generated map), `docs-site/.gitignore` (add `src/generated/`), and `docs-site/src/build-a-catalogue-nav.json`.

**Tests:** `tools/test_catalogue_spec_site.py` (extend):
- Each `0.1/` raw file is byte-identical to its snapshot member file, so its `$id` names `0.1/` (AC 12).
- The 0.1 output is driven by the release row, not the manifest: in a fixture, adding a `member` row and mutating live `contracts/` changes no `0.1/` output (AC 12).
- Each `latest/` raw file is byte-identical to the matching `0.1/` raw file (AC 13).
- The generator writes `docs-site/src/generated/spec-latest-redirects.json` with one entry per `latest/` page; each key is base-relative and each value base-absolute under `/agent-ready-repo/docs/`, asserted on both sides rather than by entry count; a second release in a fixture repoints every entry with no config edit (AC 14).
- `index.json` lists 0.1 with its date, adapter contract version and member digests, and carries no page-source digest (AC 15).
- `draft/` still reads live `contracts/`, every `draft/` `$id` still names `draft/`, and `draft/adapter.schema.json`'s new expected bytes are pinned (AC 18).
- `tools/test_build_a_catalogue_nav.py` (extend): the specification entry links `spec/catalogue/latest`; the tab set is unchanged (AC 17).
- The generated 0.1 overview page carries the four adopter options and the same-deploy warning (AC 16).

**Done when:** those suites pass, and `python3 tools/build-site.py` then `npm ci && npm run build` in `web/` then `docs-site/` then `tools/check-rendered-site-links.py --build-dir build` and `npm test --prefix web` all succeed, with `latest/` observed redirecting to `0.1/` in the real build (AC 13).

### T6: Check 3, rendered half — deployed-index parity

**Depends on:** T5

**Tests:** `tools/test_check_deployed_release_parity.py` (new), against a stub HTTP server and a fake build tree:
- An index listing 0.1 with digests matching the build passes (AC 9).
- **Falsification:** a released path missing from the build fails; a served member byte differing from the fetched index's digest fails; a missing, unfetchable and 404 index each fail; a 200 carrying non-JSON fails; a 200 whose JSON has no `releases` key fails; a 200 whose `releases` is not an array fails; a body past the 1 MiB ceiling fails rather than being read whole (AC 9).
- A redirect is refused; the 30-second timeout is set; the URL is a literal no environment variable changes; a set `https_proxy` does not change the fetch destination; a set `SSL_CERT_FILE` and a set `SSL_CERT_DIR` each leave the trust anchor unchanged rather than redirecting it (AC 9).
- On a `workflow_dispatch` run whose ref is not `main`, the check skips explicitly and prints the skip rather than failing closed or passing silently (AC 9).
- **It runs rather than skips** on a `pull_request` event, on a `push` to `main`, and on a `workflow_dispatch` whose ref is `main` — one case per leg, so a skip predicate reading the ref alone goes red instead of silently disabling the control on every pull request (AC 9).
- An index whose `releases` array is empty passes, admitting the first deploy (AC 9).
- Substituting the build-tree `index.json` for the fetched anchor fails (AC 9).
- `tools/test-pages-workflow.py` (extend): the step exists in the build job, precedes `upload-pages-artifact`, and the script and its test appear in both `paths:` filters (AC 9, AC 10).

**Done when:** both suites pass, and `tools/lint-ci-parity.py`'s `pages.yml` reason has been read and now names this second hard gate — a goal-based check on the text, since that roster is presence-checked, not truth-checked, and the lint is green either way.

### T7: Check 4 — the release gate

**Depends on:** T2, T8

**Tests:**
- `tools/test-release-agentbundle-workflow.py` (new): a gate job exists, is conditional on `github.ref_type == 'tag'`, and both `publish-pypi` and `publish-artifactory` list it in `needs` (AC 11).
- `tools/test_check_release_gate.py` (new): V read from the `$id`s of the bundled JSON-schema members; the compared byte set is the key set of V's release-row `members` table — all 10 members — taken from the row alone and never from the inventory; the row's `pages` table is not compared (AC 11).
- **Falsification:** no snapshot for V, bundled bytes differing from the snapshot, a deployed index not listing V, a non-200 or unparsable index, a bundled inventory not listing exactly the release row's set, and an absent, unreadable or empty inventory each fail; the fetch refuses redirects, carries the timeout and ceiling, ignores `https_proxy`, and takes its trust anchor from neither `SSL_CERT_FILE` nor `SSL_CERT_DIR` (AC 11).

**Done when:** both suites pass, the gate chain run shows the `_script_step` executing `tools/test-release-agentbundle-workflow.py`, and `tools/lint-ci-parity.py`'s `release-agentbundle.yml` reason now names this second hard gate, on the same goal-based basis as T6.

### T8: CLI version report and the package bump

**Depends on:** T1, T2 — T2 generates `_data/catalogue-members.txt`, which both reports read and which AC 20 makes a fail-closed input, so the manual-QA leg can only record a real version string after T2

**Edit sites:** `version.py`, `pyproject.toml`, `CHANGELOG.md`, `README-pypi.md`, `docs/product/changelog.d/<uuid>.md` (written with `tools/changelog.py new`), `tests/roster/test_okf_catalogue_discovery.py`, and `commands/catalogue_contracts.py`.

**Tests:** `packages/agentbundle/tests/unit/` (extend), fixtures only, no repository paths and no spec identifiers — the generator and check-1 halves belong to T2:
- `catalogue_spec_version()` equals the version in the `$id`s of the members the bundled inventory names (AC 20).
- A fixture inventory listing a member whose bundled copy has no `$id` fails both reports closed, naming `_data/<name>` (AC 20).
- An absent, unreadable, empty or zero-entry inventory fails both reports naming `_data/catalogue-members.txt` (AC 20).
- Driven through the real CLI entry point, not a direct reader call: with a malformed bundled `$id`, `--version` and `catalogue contracts list` fail while `agentbundle adapt --help` still succeeds — which only holds once `--version` uses the lazy action, since argparse evaluates an eager `version=` on every invocation (AC 20).
- A listed member missing, unparsable, lacking an `$id`, or carrying a disagreeing one raises naming `_data/<name>` — and importing `agentbundle` and running a command that does not read that member still works (AC 20).
- `--version` carries the version; `catalogue contracts list` table output carries it; `--format json` emits `{"catalogue_specification": ..., "contracts": [...]}` with the rows unchanged, and `test_catalogue_wave3_contracts_cli.py:88`'s bare-array assertion is updated to the new envelope (AC 20).
- `tests/roster/test_okf_catalogue_discovery.py` pins 0.56.0 (AC 21).
- `CHANGELOG.md` and `README-pypi.md` record the `--format json` change as Breaking (AC 20).
- `tests/roster/test_agentbundle_governance_markers.py` passes (AC 22).

**Done when:** `./.venv/bin/python -m pytest packages/agentbundle/tests tests/roster/test_okf_catalogue_discovery.py tests/roster/test_agentbundle_governance_markers.py -q` passes, `python3 tools/lint-catalogue-curation-guard.py --root . --base origin/main` passes after a fetch (AC 21), and the built CLI's `--version` and `catalogue contracts list` (both formats) are run and their output recorded (manual QA).

### T9: Maintainer how-to

**Depends on:** T5

**Edit sites:** `docs/guides/how-to/cut-a-package-release.md`. The `contracts/REGISTRY.md` row belongs to T1 and must not be added again here — a second row for the same spec breaks the set equality T1 restored.

**Tests:** goal-based. `Done when:` the how-to names `rewrite_member_ids.py`, the snapshot path, the release-row fields, the merge-deploy-then-tag order, and how to apply a correction row; `./.venv/bin/python -m pytest tests/roster/test_contract_backward_registry.py -q` still passes, as a regression re-run of the row T1 added; and `lint-spec-status.py --root . --verbose` emits no warning naming this spec — read from its output, not from its exit code, which is 0 either way (AC 24, AC 25).

### T10: Register every new suite and re-pin the batch digests

**Depends on:** T1, T3, T4, T6, T7

**Tests:** goal-based, and the existing gates are the check:
- Add the five new `tools/test_*.py` suites to **both** the `Makefile:698-718` `run-test-suite` line and the matching `.github/workflows/build-check.yml:915-934` pytest list, keeping the two sets equal.
- Add a `SUITE_DISPOSITION` entry per new target in `tools/lint-ci-parity.py`, naming the build-check step that actually gates it.
- Re-pin `FINAL_TOOL_BATCH` and both approved plan digests in `tools/test_local_ci_shared_test_deduplication.py`, recording the two-way disposition its comment block requires: that this slice's five suites are the sole cause, and that the prior pins were current before the change.

**Done when:** `./.venv/bin/python -m pytest tools/test_marketplace_envelope_parity.py tools/test_local_ci_shared_test_deduplication.py -q` passes and `python3 tools/lint-ci-parity.py` exits 0 (AC 23).

## Rollout

One pull request, left unmerged at the human gate. Merging deploys permanent
URLs, so the owner presses that button. After the deploy succeeds, the
`agentbundle-v0.56.0` tag can be pushed; a tag pushed before the deploy fails
check 4, which is the intended safe failure.

The release row's `date` records when the row was authored, not when it merges.
If the merge slips well past that date, re-stamp the row and its digests stay
untouched — the date is not digested.

Reversal before merge is free. After merge, the `0.1/` URLs are permanent;
a mistake is corrected by a new version or, for a released page only, by a
correction row.

## Risks

- A released byte and its digest can be changed together inside one commit. Check 3 anchors outside the commit precisely for this, and the two halves cover the two reachable anchors; a `main` writer who also edits `pages.yml` defeats it. RFC-0109 § Trust analysis accepts that residual.
- A version merged but not yet deployed is unprotected until its deploy lands, because a later push is checked against the older anchor. RFC-0109 § Trust analysis records and accepts this second residual; the merge-to-deploy window is the exposure.
- A released *page source* has no anchor on the `main`-push path: `index.json` carries member digests only, so the rendered half compares member bytes, and the tree half's `main`-push leg anchors on the ref's pre-push value — which catches a page-source edit anywhere in that push but not one landed in an earlier push and deployed later. This is a third residual beside the two RFC-0109 § Trust analysis records, and it is accepted on the same basis: released bytes are only as safe as write access to `main`.
- Adding roughly 22 pages may exceed `DOCS_PAGE_BUDGET` or the rendered-output heap. T5 raises the budget and heap together, and only if the real build needs it.
- The deployed-index fetch adds a network dependency to the Pages build and the release gate. It fails closed, so a GitHub Pages outage blocks the deploy or the tag rather than publishing unchecked.

## Changelog

- 2026-10-23: spec approved by eugenelim
- 2026-10-23: plan approved by eugenelim
- 2026-10-22: spec and plan drafted
- 2026-10-22: revised from pre-EXECUTE review round 1 — 19 sustained findings across adversarial and security adjudication
- 2026-10-22: revised from round 2 — 19 further sustained findings; owner settled the `--format json` envelope (wrap, documented breaking) and kept the slice as one pull request
- 2026-10-22: revised from round 3 — 13 further sustained findings, including a self-contradiction where the member inventory listed two TOML members that can never carry an `$id`
- 2026-10-23: revised from round 7 — 11 sustained findings across both reviewers. T8 now depends on T2, which generates the inventory its manual-QA leg reads; the rendered-half design sentence names the fetched index entry (a round-6 edit that silently did not apply); the released overview must no longer call itself the draft, which would otherwise have been frozen into a permanent URL; the tree-half design covers all four anchor legs; version ordering is numeric and key disjointness compares resolved paths. Awaiting owner approval
- 2026-10-23: revised from round 6 — 7 sustained findings. The released page sources now reach final bytes in T2 before the snapshot is taken, closing a freeze-then-edit ordering defect; the push leg anchors on the ref's pre-push value rather than the tip's first parent, which measured only the last commit of a multi-commit push; a release row's `version` is now unique and the shared-key rule sits on the release row; the tree half names its event and anchor in its own output so the dispatch carve-out has an observable.
- 2026-10-23: revised from round 5 — 10 sustained findings. The generator's stale flat-`digests` reference and the shared predicate's task ownership were both round-4 restructure drift; AC 9's failure clause now names the fetched index, and the rendered half's skip now reads event and ref together. The gate-chain routing finding was refuted: the curation guard defaults `--base origin/main`, so a zero-arg `_script_step` already fails closed
- 2026-10-23: revised from round 4 — 12 sustained findings. The release row gains separate `members` and `pages` digest tables, which three criteria needed and none had; `--version` moves to a lazy argparse action, since a function behind an eager `version=` is still eager; the registry row moves to T1 because the roster suite is already red. One security adjudication returned indeterminate on a TLS question and was re-adjudicated under owner steer with interpreter evidence
