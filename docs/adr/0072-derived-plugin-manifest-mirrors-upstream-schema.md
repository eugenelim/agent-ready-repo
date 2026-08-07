# ADR-0072: The derived plugin manifest mirrors Claude Code's schema; the real client is the oracle

- **Status:** Accepted
- **Date:** 2026-08-06
- **Decision-makers:** eugenelim
- **Consulted:** adversarial-reviewer, security-reviewer
- **Supersedes:** none
- **Related:** `.github/workflows/publish-claude-plugins.yml`

## Decision summary

- **Decision:** `contracts/plugin-manifest.derived.schema.json` is a **mirror of
  an external contract we do not own**, not a contract we author. When it and
  Claude Code's published plugin schema disagree, the upstream schema wins and
  ours is corrected — no compatibility shim, no local extension. Concretely: the
  plugin `source` object is a `git-subdir` source (`source`, `url`, `path`, and
  `ref` / `sha` — **at least one required**; see *Named exception*). The keys `branch` and `directory` are removed; they were never
  valid.
- **Because:** a self-authored schema that gates a self-authored generator
  verifies only that we are self-consistent. Ours was self-consistent and wrong,
  and it published empty plugins to adopters while every gate stayed green.
- **Applies to:** the derived plugin manifest, the marketplace entries built from
  it, and any future artifact whose shape is dictated by a third-party runtime.

## Context

`agentbundle build` emitted plugin sources as
`{"source": "github", "repo": ..., "branch": "claude-plugins-dist", "directory": "<pack>"}`.
Claude Code's `github` plugin source accepts `repo`, `ref?`, and `sha?` only, and
has no subdirectory support at all. `branch` and `directory` were silently
dropped, so the installer cloned the repository's default branch at its root.

The failure was silent at every layer. `claude plugin validate` passed, because
it checks shape and tolerates unknown keys. `claude plugin install` reported
`✔ Successfully installed`. Only `claude plugin details` revealed the truth:
`Skills (0) Agents (0) Hooks (0)`. Every adopter who followed the documented
install path received a plugin that contained nothing.

Three artifacts agreed with each other and none agreed with reality:

1. the generator (`build/main.py:derive_projectable_subset`, and a second writer
   at `build/self_host.py:_aggregate_marketplace`),
2. regression tests that asserted `source.branch` and `source.directory` must be
   set — pinning the defect as if it were the contract,
3. `contracts/plugin-manifest.derived.schema.json`, which listed `branch` and
   `directory` in `source.required` and pinned `source.source` to
   `enum: ["github"]`.

The decisive condition, however, is a fourth: **nothing validated a marketplace
entry at all.** `build/main.py:545-546` pops `source` and `category` off the
derived manifest before `validate_derived_plugin_manifest_dict`, so the schema
has never seen a `source` object; `catalogue_tooling/verify.py:631-632` inspects
`marketplace.json` only for a stray `hooks` key. The proof is on disk: every live
entry carries `category`, which the derived schema forbids under
`additionalProperties: false` — if entries were validated, all 21 would fail
today.

This matters because it changes the remedy. It is tempting to say the schema
"ratified" the bug, but a schema that is never applied ratifies nothing. The
generator emitted an invalid shape into an unguarded channel, and
`publish-claude-plugins.yml` — which substitutes a hermetic schema check
*specifically because the `claude` binary is unavailable in CI* (workflow
comment, lines 16-20) — published it. The fix is therefore not only to correct
the schema but to make it actually run against marketplace entries.

A second, independent defect — components projected to `<pack>/.claude/` where
plugins require `skills/`, `agents/`, `commands/` at the plugin root — was
invisible until the first was fixed, and is corrected alongside it.

## Options considered

**A — extend the schema to permit both shapes.** Add `git-subdir` alongside the
existing `github`+`branch`+`directory` form, keeping old manifests valid.
Rejected: there are no valid old manifests. Every artifact the old shape produced
was an empty plugin. Permissiveness here preserves nothing and leaves the invalid
shape documented as supported, which is how the next author reintroduces it.

**B — drop `additionalProperties: false` so the schema stops blocking us.**
Rejected outright: that constraint is the only reason the schema is a gate rather
than a suggestion. The problem was that the schema asserted the wrong contract,
not that it asserted one strictly.

**C — delete the schema and rely on `claude plugin validate` in CI.** Rejected:
the binary is not available in standard CI, which is why the schema exists. It
also would not have caught this defect — `validate` passed on the broken manifest.

**D — correct the schema to mirror upstream, and make real-client verification a
merge precondition.** Chosen. The schema keeps its job as a fast hermetic gate,
but is explicitly a *mirror* rather than a source of truth, and a human runs the
real client before merging changes to the plugin pipeline.

## Consequences

**Good.** The published contract matches the runtime that consumes it. Adopters
installing from the marketplace receive actual components. The `git-subdir`
source additionally unlocks the claude.ai organization-marketplace path, which
requires a private marketplace repository but permits public plugin targets.

**Costs and risks.** The schema must now be maintained against an upstream that
can change without notice; drift is detected by a human running the real client,
not by CI. That is a deliberate trade: CI cannot run the client, so the honest
position is that this pipeline's green build is **necessary but not sufficient**.
The publish workflow already states this; this ADR elevates it from a comment to
a recorded decision.

**Named exception — one deliberate tightening beyond upstream.** The rule above
says upstream wins and we add no local extension. There is exactly one departure:
our source object requires **at least one** of `ref` or `sha`, where upstream
leaves both optional. It is expressed with the `if`/`then`/`else` trio rather
than `oneOf` — `build/validate.py:23-28` lists `oneOf`/`anyOf`/`allOf` as
"Unsupported by design", so a `oneOf` would be silently ignored by the very gate
it was meant to strengthen. `oneOf` would also have been wrong on the merits: it
is satisfied by exactly one branch, so a manifest carrying both `ref` and `sha` —
legal upstream — would have been rejected locally, making this
"one departure" claim untrue. Upstream can afford optionality because its
fallback — the
repository's default branch — is usually what a caller wants. For us it is the
precise failure this ADR exists to prevent: a `ref`-less entry silently fetches
`main` at repo root, which is the original defect wearing a valid shape. The
exception is *restrictive*, so anything we emit remains valid upstream; it can
never make a manifest that upstream would reject succeed locally. Any future
tightening must clear the same bar: restrictive only, and justified by a defect
we have actually observed.

**Accepted residual — a mutable `ref`.** The `git-subdir` source pins `ref` to
the `claude-plugins-dist` branch rather than a `sha`. Exact-commit pinning is
infeasible here: the dist commit does not exist at build time, and
`marketplace.json` lives *on* the branch it would pin. The compensating control
is therefore branch integrity, not manifest integrity — which means **branch
protection on `claude-plugins-dist` is a precondition of this decision, not an
optimisation.** It does not exist today: the protection API returns 404 for that
branch while `main` blocks force-pushes. Before this change the branch delivered
empty plugins, so the exposure was theoretical; after it, the branch delivers
skills, agents, and a `SessionStart` hook that execute on every adopter's
machine. Shipping the corrected manifest without protecting the branch converts a
latent risk into a live code-delivery channel that anyone with repo write — or
any workflow holding `contents: write` — can push to unreviewed.

**Follow-on.** A periodic or release-gated job that runs the real `claude` client
against the published marketplace would close the CI gap properly. Not in scope
here; recorded as the known weakness this ADR accepts.

## Verification

The decision is verified by the real client, not by the schema:
`claude plugin install core@<marketplace>` followed by `claude plugin details`
must report non-zero skills and agents. A schema test asserts that a
`branch`/`directory` payload is now **rejected**, so the defect cannot be
reintroduced silently.
