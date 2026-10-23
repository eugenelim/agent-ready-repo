---
slug: catalogue-spec-release
title: "Release 0.1 of the catalogue specification (RFC-0109 S4)"
status: Implementing
---

# Spec: Release 0.1 of the catalogue specification

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0109](../../rfc/0109-catalogue-specification-publication.md) D3 (`$id` rule, version line, path table), D7 (checks 2, 3 and 4), D8 slice S4, and its [Trust analysis](../../rfc/0109-catalogue-specification-publication.md#trust-analysis)
- **Contract:** `contracts/catalogue-spec.toml`
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

**Mode:** full. It mints permanent public identifiers, changes a published
interface, adds a tamper control, and changes the package.

Site paths below are written without the `/agent-ready-repo` base path, which
every served URL carries; the `$id` in AC 1 shows the full absolute form.

## Outcome

Release 0.1 of the agentbundle catalogue specification is published. Every
member schema's `$id` is its permanent URL under
`/docs/spec/catalogue/0.1/`, a committed snapshot freezes the released bytes,
and the site serves that version from the snapshot rather than from live
`contracts/`. Three drift checks make the release append-only and stop a CLI
from shipping a specification version the site does not serve. `agentbundle`
reports which catalogue specification version it carries.

This is a one-way door: merging it deploys URLs that are permanent.

## What Changes

- Every member JSON schema in `contracts/` gains an absolute `$id` under `0.1/` and a `$schema`; `adapter.schema.json` gains both — and so do the `_data/` copies
- A rewrite tool moves every member `$id` to a given version — `tools/catalogue/rewrite_member_ids.py`
- The first snapshot, `contracts/releases/catalogue/0.1/`, holding the 10 member files and a copy of the narrative page sources
- The first `release` row in `contracts/catalogue-spec.toml`, with the version, date, adapter contract version and a SHA-256 per member file and per page source; the manifest loader learns to parse and validate release and correction rows
- The site serves `/docs/spec/catalogue/0.1/` from the snapshot, and `/docs/spec/catalogue/latest/` as redirect pages plus byte copies of the 0.1 raw files; `index.json` lists 0.1 with its member digests
- Build a Catalogue's specification entry repoints from `draft/` to `latest/`
- D7 check 2 (version consistency) and check 3's tree half join the build-check chain; check 3's rendered half joins `pages.yml` before the Pages artifact upload; check 4 gates the tag-push run of `release-agentbundle.yml`
- `agentbundle --version` and `agentbundle catalogue contracts list` report the catalogue specification version, read from the bundled member `$id`s
- `agentbundle` 0.56.0, across the six files that move together

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Published interface | Adopters pin a permanent URL | `/docs/spec/catalogue/0.1/` and member `$id`s | eugenelim | Rendered-output check green; deployed `index` lists 0.1 | Every member is served at its `$id` |
| Released artifact | The released bytes must be frozen | `contracts/releases/catalogue/0.1/` | eugenelim | Check 3 green against the base anchor | Snapshot and release row committed |
| Tamper control | A `main` writer must not rewrite a released file | D7 check 3, in `build-check` and `pages.yml` | eugenelim | Falsification tests for both halves, run by a named gate | Both halves fail on a mutated release |
| Release control | A CLI must not ship a version the site lacks | D7 check 4, in `release-agentbundle.yml` | eugenelim | Check 4 job present and depended on | Both publish jobs need it |
| Adopter guidance | Adopters must know how to protect themselves | the 0.1 overview page | eugenelim | Rendered page carries the four options | Page states pin, record, cross-check, vendor |
| Maintainer procedure | Maintainers must know how to cut the next version | `docs/guides/how-to/cut-a-package-release.md` | eugenelim | Updated how-to | Names the rewrite tool, the release flow and a correction row |

## Agent Rules

### Always do

- Build a released version's pages and raw files from that version's snapshot and its own release row, never from live `contracts/` and never from the manifest's `member` rows.
- Derive the `draft/` member list from the manifest's `member` rows, so a member added later appears at `draft/` without a code change. This rule governs `draft/` only.
- Keep `latest/` raw files byte-identical to the newest release's raw files, so their `$id`s name the versioned path.
- Keep every member `$id` on one version, V, in `contracts/` and in `_data/`.
- Name the rewrite tool in check 2's failure message.
- Anchor check 3 outside the pushed commit, per half: the tree half anchors on the merge base with the base branch; the rendered half anchors on the fetched deployed `index` on every run it makes, pull request or `main` push.
- Fetch the deployed `index` over a hard-coded `https` scheme and host, refusing redirects, with a 30-second timeout and a read bounded at 1 MiB, and take the URL from no environment variable or workflow input.
- Fail closed everywhere: only a 200 response that parses as JSON and carries an explicitly present `releases` array may be read as an index; an unreachable base ref fails; an unreadable bundled `$id` fails the version report naming `_data/<name>`.
- Validate a release row's `version` against a literal `MAJOR.MINOR` form before using it as a path segment, and validate every release-row path before reading or writing it: relative, no `..`, no backslash, no drive letter, resolving inside that release's snapshot directory.
- Read the released version from the bundled member `$id`s only. Fetch nothing.
- Give every new check and every new test suite a named route — a gate-chain step, a Makefile suite line and its matching `build-check.yml` pytest list, or a job or step in another workflow — carrying whatever roster entry `tools/AGENTS.md` obliges for that route, which may be none.

### Ask first

- Choosing any version other than `0.1` for the release row.
- Changing a released `$id`, a released digest, or an existing release row.
- Moving a contract file on disk, or adding a top-level directory.
- Splitting the `$id` rewrite into its own pull request ahead of the release.

### Never do

- Re-serialize a JSON member when rewriting its `$id`. Splice bytes, as `draft_bytes()` does.
- Let `contracts/releases/**` be read by the CLI at runtime, or shipped inside the package.
- Cite an RFC, ADR or spec identifier in shipped package source, messages or package tests.
- Weaken check 3 so that a run with no reachable anchor passes.
- Read the deployed `index` from any path inside the checkout or the build output.
- Publish a `bundled` or `vendored` row under a released path.

## Testing Strategy

- `$id` rewrite tool (idempotence, byte-level splice, insertion when absent, `$schema` insertion, refusal on a non-member): **TDD** in `tools/test_rewrite_member_ids.py`.
- Release-row and correction-row parsing, `supersedes`-chain validation, `version`-form validation, path confinement, the shared JSON-schema-member predicate, the bundled member inventory's generation and D7 check 1's rule holding it: **TDD** in `tools/test_contract_parity.py`, the loader's and generator's existing gated test home. These are repository tools, so they are verified there and never in the package suite.
- Checks 2, 3 (both halves) and 4, each with **falsification** cases that prove it can fail — a mutated released byte, a deleted row, a dropped path, a disagreeing `$id`, a 200 carrying non-JSON, a 200 whose body has no `releases` key, a body past the 1 MiB ceiling, a missing or 404 index, an unreachable base ref, a mutation in an earlier commit of a multi-commit push, an absent or non-ancestor pre-push value, a snapshot page-source edit with no matching correction row, and a build-tree index substituted for the fetched one: **TDD** in `tools/test_check_spec_version.py`, `tools/test_check_release_immutability.py`, `tools/test_check_deployed_release_parity.py` and `tools/test_check_release_gate.py`.
- Workflow wiring: **TDD** in `tools/test-release-agentbundle-workflow.py` (new) and `tools/test-pages-workflow.py` (extended).
- Snapshot-driven site generation and `latest/`: **TDD** in `tools/test_catalogue_spec_site.py`.
- The CLI's *consumption* of the bundled inventory and its version report, including the `--format json` object envelope and the lazy `--version` action: **TDD** in `packages/agentbundle/tests/unit/`, against fixtures only.
- Navigation: **TDD** in `tools/test_build_a_catalogue_nav.py`.
- The repository-level half — the 0.56.0 pin across the six files that move together, the no-governance-identifier rule, and the `contracts/REGISTRY.md` backward row: **TDD** in `tests/roster/test_okf_catalogue_discovery.py`, `tests/roster/test_agentbundle_governance_markers.py` and `tests/roster/test_contract_backward_registry.py`, the enforced home for this half.
- The `Engine-Change-RFC: RFC-0109` commit trailer: **goal-based**, `python3 tools/lint-catalogue-curation-guard.py --root . --base origin/main` after fetching, run by every task whose edit sites touch `packages/agentbundle/`.
- The built site: **goal-based**, via `web/src/test/rendered-output.test.ts` and `tools/check-rendered-site-links.py` against the real Astro build.
- The shipped CLI: **manual QA** — run the built `agentbundle --version` and `agentbundle catalogue contracts list` and record the observed output.

## Acceptance Criteria

- [ ] A member row is a **JSON-schema member** when its `path` ends in `.json`; that predicate is computed in one place and shared, never recomputed per tool. Every JSON-schema member row carries `"$id": "https://eugenelim.github.io/agent-ready-repo/docs/spec/catalogue/0.1/<file name>"` and a `$schema` keyword, in `contracts/` and byte-identically in `_data/`. `contracts/adapter.schema.json` gains both. The two TOML members are unchanged.
- [ ] `tools/catalogue/rewrite_member_ids.py` rewrites every member JSON schema's top-level `$id` to a given version and ensures a `$schema` keyword is present, inserting either line when absent, changing no other byte, and is idempotent. Check 2 names it in its failure message.
- [ ] `contracts/releases/catalogue/0.1/` holds a byte-identical copy of each of the 10 member files and of every narrative page source under `docs-site/spec-src/catalogue/`.
- [ ] `contracts/catalogue-spec.toml`'s `release` array holds exactly one row: `version = "0.1"`, `date` recording the date the row was authored, the adapter contract version read from `contracts/adapter.toml`, and two separately keyed digest tables: `members`, holding a SHA-256 for each of the 10 member files, and `pages`, holding one for each narrative page source. The two key spaces never mix: the loader rejects a release row whose `members` and `pages` tables share a key after each is resolved by AC 5's validation — so an alias such as `./pack.schema.json` beside `pack.schema.json` is caught, since every later read uses the resolved form — so every consumer reads member digests from `members` alone. It also rejects a second release row whose `version` compares equal to another row's under that ordering — so `0.1` and `0.01` collide rather than both being admitted — naming the duplicate row — the same duplicate-key convention the loader already applies to `[[contract]]` rows. The manifest loader parses and validates release rows and rejects a malformed one with an error naming the row; `version` must match a literal `MAJOR.MINOR` form (`^[0-9]+\.[0-9]+$`) before it is used as a path segment, and a row failing that is rejected.
- [ ] The loader rejects any release-row path that is absolute, contains `..`, contains a backslash or a drive letter, or does not resolve to a regular file inside `contracts/releases/catalogue/<version>/`, with one rejection test per escape shape. Every snapshot read in the checks, and every per-release path the site generator reads or writes, uses only a `version` and a path key that passed that validation.
- [ ] A correction row carries `version`, `date`, a note, `supersedes`, and a `pages` digest table only. Its `pages` keys, resolved by AC 5's validation, must lie inside that version's release-row `pages` key set resolved the same way, so a correction row can never name a member file. It carries no `members` table, and the loader rejects one that does, one whose `pages` carries a key outside that set, one naming a version with no release row, and one whose `supersedes` link is missing, duplicated, cyclic or dangling. For each version the governing correction row is the head of that version's rooted `supersedes` chain — not its position in the array, so reordering rows changes nothing — and it governs page-source digests only; the original release row's `members` table always governs member digests. "Latest release" is the highest version with a release row, and a correction row never changes it.
- [ ] D7 check 2 fails unless all member `$id`s name one version V, where V is the latest release when the member bytes equal its snapshot and an unreleased version with no snapshot when they differ. It runs in the build-check gate chain.
- [ ] D7 check 3's tree half fails, on a pull request, when the head commit deletes or edits a release row, deletes or edits an existing correction row or its `supersedes` chain, deletes or edits a snapshot file, or changes a member digest, measured against the merge base with the base branch — so a branch cut before a later release row landed still passes. An unreachable base ref fails rather than passes. On a `push` to `main` it measures every commit in the push against the ref's pre-push value, and fails closed when that value is absent or is not an ancestor of the tip — after a force-push or a first push — so a mutation placed in any commit of a multi-commit push cannot sit inside its own anchor. When the event is absent or is not one of those three — every local `make build-check` run — it anchors on the merge base with the base branch, the same strong anchor the pull-request leg uses, with the unreachable-base rule still governing. On a `workflow_dispatch`, which carries no pre-push value, it anchors on the pushed commit's first parent; that anchor is the author's own commit, so the run is evidence only that the tree is self-consistent, never a tamper check. A snapshot page-source edit is admitted only when the edited path is a key of that version's release-row `pages` table — so the carve-out can never reach a `members` key — and that version carries a governing correction row whose `pages` digests match the new bytes; a page-source edit without one fails. A correction row may be superseded by a newer one but never deleted or edited against the anchor, so the record of which released page changed cannot be erased. A falsification test proves each of those five mutations, a deleted and an edited correction row, the unreachable-base case, the `main`-push leg and the unmatched page-source edit fails, and a stale-branch fixture proves the merge-base anchor does not false-alarm. It names, in its own output, the event it ran on and the anchor commit it measured against, and marks a first-parent-anchored run as self-consistency evidence — so which anchor produced a green result is readable rather than inferred. It runs in the build-check gate chain.
- [ ] D7 check 3's rendered half runs in `pages.yml` before `upload-pages-artifact` and compares the built site against the deployed `index`, fetched over a hard-coded `https` scheme and host with redirects refused, a 30-second timeout, a read bounded at 1 MiB, and no environment or workflow input in the URL. The opener carries no environment-reading proxy handler, so a set `https_proxy` cannot change where the request goes, and the server certificate is validated by an explicitly constructed context with verification and hostname checking on, whose trust anchor is taken from neither `SSL_CERT_FILE` nor `SSL_CERT_DIR`. The skip decision reads the event name and the ref together: the check skips only on a `workflow_dispatch` run whose ref is not `main`, saying so in its output, because that build cannot deploy. It runs — never skips — on a `pull_request` event, on a `push` to `main`, and on a `workflow_dispatch` whose ref is `main`. It never passes silently. A body exceeding the ceiling fails the check rather than being read whole. Only a 200 response that parses as JSON and carries an explicitly present `releases` array is an index; a non-200, an empty, truncated or unparsable body, an absent or non-array `releases`, or a missing or 404 response fails the deploy. A deployed `index` whose `releases` array is empty admits this first deploy and any retry of it. The check fails when a released path is missing from the build or when served member bytes differ from the digest the fetched `index` carries for that release. The digests compared come from the fetched body; no in-checkout manifest row is the anchor for this half. A falsification test proves it fails when the build-tree `index` is substituted for the fetched one.
- [ ] `tools/check-deployed-release-parity.py` and its test appear in both the `push` and `pull_request` path filters of `pages.yml`, asserted by `tools/test-pages-workflow.py`.
- [ ] D7 check 4 runs in the tag-push run of `release-agentbundle.yml`, in a job that both `publish-pypi` and `publish-artifactory` depend on. It reads V from the bundled member `$id`s and fails unless the tagged commit holds a snapshot and a release row for V, the bundled member bytes equal that snapshot, and the deployed `index` lists V with the same member digests. The member set whose bytes it compares is the key set of V's release-row `members` table — all 10 members, derivable from the row alone and never from the bundled inventory, because the build-check chain that holds that inventory to the manifest does not run in this workflow. V itself is read from the JSON-schema subset of those members, the only ones carrying an `$id`. The row's `pages` table is not compared, because the package bundles no page sources. The check additionally fails when the bundled inventory does not list exactly the JSON-schema subset of that `members` key set — compared after reducing each side to its base file name, the form `_data/` copies already use — or when either side does not reduce to that form, or is absent, unreadable or empty. Its fetch obeys the same hard-coded-host, no-redirect, 30-second-timeout, 1-MiB-bounded-read, no-proxy-handler and explicit-context certificate rules — including the trust anchor taken from neither `SSL_CERT_FILE` nor `SSL_CERT_DIR` — and the same index-acceptance predicate.
- [ ] After `python tools/build-site.py`, `/docs/spec/catalogue/0.1/` serves an overview page and one page per member of that release, and `/docs/spec/catalogue/0.1/<file name>` serves bytes byte-identical to the snapshot member file. The served file set comes from the 0.1 release row's `members` table and its snapshot, so a member added to or removed from the manifest after 0.1 changes no `0.1/` output.
- [ ] `/docs/spec/catalogue/latest/<file name>` is byte-identical to `/docs/spec/catalogue/0.1/<file name>`, so each carries the `0.1/` `$id`. `/docs/spec/catalogue/latest/` and each member page under it redirect to the matching `0.1/` page.
- [ ] The `latest/` redirect targets are generated, not hand-maintained: the site generator writes them to a generated, gitignored data file that `docs-site/astro.config.ts` reads and spreads into its existing `redirects:` block, treating an absent file as empty. Each entry follows that block's existing asymmetry — a base-relative `from` and a base-absolute `to` carrying the `/agent-ready-repo/docs/` prefix — and both sides are composed in code under the fixed `/docs/spec/catalogue/` path. Cutting a later version repoints `latest/` with no edit to `astro.config.ts`.
- [ ] `/docs/spec/catalogue/index.json` lists release 0.1 with its date, adapter contract version and a SHA-256 for every member file. It publishes the release row's `members` digests only; the `pages` table stays in the manifest, because check 4 and the rendered half both compare member bytes and nothing fetches a page source. The `/docs/spec/catalogue/` page lists 0.1 and links it, `latest/` and `draft/`.
- [ ] The 0.1 overview page describes itself as release 0.1, not as the draft: it carries no sentence calling itself the draft and none claiming no released version exists. Because one source, `docs-site/spec-src/catalogue/overview.md`, feeds both `draft/` and the snapshot, its prose must read correctly at both — status wording that is true at either path, with no claim that only holds at one. A test fails when the released page still calls itself the draft or still says no release is published.
- [ ] The 0.1 overview page tells adopters to pin a versioned URL rather than `latest/` or `draft/`, to record each digest in their own repository, to cross-check a digest against the `_data/` copy in the matching PyPI wheel or the snapshot at the matching `agentbundle-v*` tag, or to vendor the file — and says the `index` comes from the same deploy as the files.
- [ ] Build a Catalogue's "Contract and schema reference" group links the specification at `spec/catalogue/latest` instead of `spec/catalogue/draft`. The tab set and `rail.ts` are unchanged.
- [ ] Every `draft/` raw file's `$id` still names `draft/`, and `draft/` generation still reads live `contracts/`. `draft/adapter.schema.json` gains the `$id` and `$schema` lines its source gained, and its expected bytes are pinned.
- [ ] A bundled member inventory, `_data/catalogue-members.txt`, is generated by the same generator that writes `public-contracts.txt` and lists exactly the manifest's JSON-schema member rows as AC 1 defines them — the members that carry an `$id`. The two TOML members, `adapter.toml` and `target-vocab.toml`, are excluded, because AC 1 leaves them without one. The generator, the rewrite tool and check 2 all take that set from the one shared predicate, so they cannot disagree. D7 check 1 holds the file to that derived set, so a JSON member added for a later version joins it without a code change.
- [ ] `agentbundle --version` reports the catalogue specification version alongside the CLI and adapter contract versions. `agentbundle catalogue contracts list` reports it in its table output, and its `--format json` output becomes the object `{"catalogue_specification": "<version>", "contracts": [<the rows it emits today, unchanged>]}` — a breaking change to that bare array, recorded as Breaking in `CHANGELOG.md` and `README-pypi.md`. Both reports read the version from the members named in `_data/catalogue-members.txt` at the moment the report is produced — for `--version` that means the argparse action computes the string when it fires, not when the parser is built, since the parser is built on every invocation before the subcommand is known — so a malformed bundled `$id` fails those two reports and leaves working every command that does not read the affected member. Both agree, and both fail closed naming `_data/<name>` when a listed member is missing, unparsable, or carries a disagreeing or absent `$id` — and fail closed naming `_data/catalogue-members.txt` when that inventory is itself absent, unreadable, empty, or lists zero entries, so an empty member set is never a vacuous pass.
- [ ] `agentbundle` is 0.56.0 in all six files that move together, and the implementing commits carry an `Engine-Change-RFC: RFC-0109` trailer.
- [ ] No shipped package source, message or package test cites an RFC, ADR or spec identifier; `tests/roster/test_agentbundle_governance_markers.py` passes.
- [ ] Every new check script and every new test suite has a named route — a gate-chain step, a Makefile suite line together with its matching `.github/workflows/build-check.yml` pytest list, or a job or step in another workflow — carrying whatever `STEP_DISPOSITION` or `SUITE_DISPOSITION` entry `tools/AGENTS.md` obliges for that route, which is none for a gate added inside `build_gate_chain.py`. `tools/lint-ci-parity.py` and `tools/test_marketplace_envelope_parity.py` both pass.
- [ ] `contracts/REGISTRY.md` carries a backward row pointing `contracts/catalogue-spec.toml` at this spec, so `tests/roster/test_contract_backward_registry.py`'s set equality holds and `lint-spec-status.py --verbose` emits no invariant (v) warning naming this spec.
- [ ] `docs/guides/how-to/cut-a-package-release.md` documents cutting the next specification version: run the rewrite tool, add the snapshot and release row, merge and let Pages deploy, then tag — and documents applying a correction row to a released page.

## Follow-ons

- eugenelim: Wave 7 marketing links repoint at the 0.1 URLs (`catalogue-wave7-marketing-evaluator`).

## Assumptions

- Technical: `docs-site/astro.config.ts` already carries a `redirects:` block, so `latest/` redirect pages use an existing mechanism (settled by: the first real build).
- Technical: the deployed `index` returns HTTP 200 with `{"releases": []}` today, verified on 2026-10-22, so check 3's rendered half has a live anchor from its first run.
