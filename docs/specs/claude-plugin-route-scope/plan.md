# Plan: Claude-plugin route — publish only user-capable packs

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

> **Cross-reference convention.** Criteria are cited by **name**, not number.
> The predecessor spec's numeric references went stale three times under
> renumbering.

## Approach

One predicate, applied at three writers, plus the docs that advertise the route.
Nothing here touches the hook pipeline — that split out to
`docs/specs/claude-plugin-hook-parity/` after five review rounds showed it
specifying a code-execution channel in prose and generating new findings each
round. Nothing in this spec depends on it.

**The predicate.** `commands/validate.py:_allowed_scopes` is the existing
resolver and is reused. Its real gate is `[pack.adapter-contract].version`, not
`[pack.install]` — verified by execution, a pack declaring
`allowed-scopes = ["repo","user"]` with no `[pack.adapter-contract]` resolves to
`["repo"]`. That surprise is why the fixtures need care and why the spec names
it rather than leaving it to be rediscovered.

**Three writers.** The recipe and `_run_aggregate` are expected. The third,
`build/self_host.py:_aggregate_marketplace`, writes the repo-root
`.claude-plugin/marketplace.json` that adopters actually add, and carries a
design note asserting the opposite intent. ADR-0072 records it as the writer
missed last time; the predecessor plan missed it again. It is listed first in
every task that touches marketplace output for that reason.

**The site.** `web/src/content/packs/*.md` are 21 hand-authored frontmatter
files with no generator — `tools/build-site.py` feeds `docs-site/`, not `web/`.
So the user-capability field is another hand-copied value, and the only thing
that keeps it honest is a test reading `pack.toml` and comparing. That test has
to run somewhere `make ci` reaches, because `web/`'s own test script is wired
into no workflow.

## Constraints

- **ADR-0002** owns the scope model. **ADR-0072** governs the marketplace shape
  and names `_aggregate_marketplace` as the previously-missed writer.
- `.claude-plugin/marketplace.json` is a `make build-check`-gated projected path.
- `agentbundle` is stdlib-only.

## Tasks

### T0 — The predicate and its three writers
**Depends on:** T1 · **Mode:** TDD

**Tests:** `stub: pending` (materialise before EXECUTE) — `packages/agentbundle/tests/unit/test_plugin_scope_filter.py`.
The predicate over an `allowed-scopes` × `adapter-contract.version` matrix
including the absent-table case; the seven named packs absent from
`dist/claude-plugins/` and from **both** `marketplace.json` files; a
user-capable pack still present. The by-name assertion carries the
tripwire comment.

**Approach:** one predicate reusing `_allowed_scopes`, applied at the recipe,
`_run_aggregate`, and `_aggregate_marketplace` — overturning that function's
"advertises every pack" note at the note. Re-pin the blast-radius tests here,
re-derived by glob first. `publish_claude_plugins.py` keeps `catalogue-curation`
for its operator-only reason, gains the derived filter beside it, and its check
becomes a fail-loud assertion so a stale `dist/` is caught rather than
republished.

**Done when:** the unit and integration tests pass and `make build-self` +
`make build-check` are green with the regenerated marketplace committed.

### T1 — Fixture scope declarations
**Depends on:** none · *(runs first — the five build fixtures carry only a `[pack]` table, so the predicate resolves them to `["repo"]` and reddens the derivation, pipeline, end-to-end and drift-gate suites the moment T0 lands)* · **Mode:** Goal-based check

**Done when:** every fixture whose tests assert claude-plugins output declares
both `[pack.adapter-contract] version` and `[pack.install] allowed-scopes`
including `"user"`, and those tests pass.

**Approach:** five fixtures under `build/tests/fixtures/packs/` lack
`[pack.adapter-contract]` and therefore resolve to `["repo"]`. `.../packs/core/`
additionally ships `.apm/hooks/` + `.apm/hook-wiring/`, so Rail B
(`build/scope_rails.py:check_hooks`) also requires
`[pack.install] user-scope-hooks = true` or `validate` refuses it. Declare, don't
rely on defaults.

### T2 — Site gating, with a consistency test
**Depends on:** T0 · **Mode:** TDD

**Tests:** `stub: pending` (materialise before EXECUTE) — a test reading each `packs/<slug>/pack.toml` and
asserting `web/src/content/packs/<slug>.md`'s user-capability field equals
`"user" in allowed-scopes`. Written under `packages/agentbundle/tests/` so
`make ci` runs it, since `npm run test --prefix web` is in no workflow.

**Approach:** add the field to `web/src/content.config.ts` and the 21 markdown
files; gate `[pack].astro` and `catalogue/index.astro` on it, **not** on `scope`
(which is `default-scope` and would hide `product-documentation`).

### T3 — Prose docs
**Depends on:** T0 · **Mode:** Goal-based check

**Done when:** a fresh grep for `plugin install` / `plugin marketplace add`
across `README.md`, `docs-site/`, `guides/`, and `web/` returns no instance
offering the route for a repo-only pack.

**Approach:** re-derive the file list by grep. State the precondition once in
`install-routes.md`'s route table; fix its marker-writer paragraph and
`docs/architecture/catalogue.md:32`; record RFC-0008's dormancy in
`docs/architecture/agentbundle.md`.

### T4 — Errata and the QA matrix
**Depends on:** T0 · **Mode:** Goal-based check

**Approach:** errata on the three frozen specs assuming `core` is
plugin-installable (bodies not edited). Re-point or retire the manual-QA-matrix
row and `test_manual_qa_matrix_shape.py:37-44`, which keeps it green while the
scenario becomes impossible.

### T5 — Changelogs
**Depends on:** T0 · **Mode:** Goal-based check

**Approach:** `[Unreleased]` in both changelogs naming the removal, the seven
packs, and `claude plugin uninstall` as step one of the remedy.

### T6 — Real client
**Depends on:** T0, T2, T3, T5 · **Mode:** Visual / manual QA

**Done when:** a dropped pack is confirmed absent from the marketplace against
`claude` 2.1.223, and an install-then-delist run records what the client does to
an installed-but-delisted plugin. Transcripts below. **Scope boundary:** one
dropped pack and one user-capable pack are exercised by hand; the other 19 are
covered by T0's assertions.

## Risks

- **Delisting is not revocation.** Adopters keep a pinned copy running. The
  changelog remedy is the only signal, and it is in a repo their client does not
  read. Accepted; recorded in the spec.
- **No compensating control ships for unrestricted pushes to
  `claude-plugins-dist`.** Force-push and deletion are denied; ordinary pushes
  are not, and the marketplace `ref` stays mutable. Deferred in the spec.
- **The `web/` field is hand-copied.** T2's consistency test is what makes that
  survivable; without it the site can advertise a repo-only pack indefinitely.

## Verification log

_(T6 transcripts land here.)_

## Changelog

- **2026-08-07** — split out of `docs/specs/claude-plugin-hook-parity/` after
  five review rounds. The scope filter and the docs fix survived rounds 4 and 5
  unchallenged and are independently shippable; the hook compiler kept
  generating new findings each round and now blocks on a spike. Carries forward
  every verified correction from those rounds: `_aggregate_marketplace` as the
  third writer, `_allowed_scopes`' real gate, the hand-authored `web/`
  frontmatter, the fail-loud publish check, and revocation-before-remedy.
