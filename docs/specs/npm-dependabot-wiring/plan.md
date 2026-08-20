# Plan: npm-dependabot-wiring

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `.github/dependabot.yml` — new.
- `workspace.toml` — remove `npm-dependabot-wiring`; append an instance note to
  `adr-errata-convention`.
- `docs/specs/npm-dependabot-wiring/{spec.md,plan.md}` — this contract.

**What demonstrates done**
- Goal-based. The artifact is a service config; there is nothing to unit-test that
  would not just restate the file.
- `yaml.safe_load` parses it, `version == 2`, and each `directory` contains a
  `package.json` — asserted, not eyeballed.
- `lint-spec-status` clean after the slug is removed.
- `make ci` green.

**What I am NOT changing**
- No code, no gate, no workflow, no permission, no token.
- Not `tools/audit-npm.py` or the `make sast` chain.
- Not ADR-0083 or `docs/specs/npm-sca-gate/spec.md` — both frozen.

## Declined patterns

- **Tempted:** add `pip` and `github-actions` ecosystems while the file is open —
  it is four more lines and the file is new, so there is no precedent to break.
  **Declined:** `sast-requirements-not-audited` owns an explicit audit-vs-Dependabot
  decision for Python, and github-actions is its own volume call. The owner approved
  *npm* wiring; silently widening the blast radius of a volume decision is the one
  thing this item must not do.
- **Tempted:** leave the slug in `[backlog].open` as an anchor, the way
  `starlight-migration-rfc` and the branch-protection entries are retained.
  **Declined:** those are retained because a frozen spec's `(deferred: <slug>)` marker
  makes `lint-spec-status` invariant (iv) require them. Nothing requires this one —
  verified by removing it and running the lint. Retaining it would make the backlog
  claim open work that is done, which is the complaint those entries' own comments
  make about themselves.
- **Tempted:** correct ADR-0083's two references while closing the slug, so nothing
  dangles. **Declined:** the ADR body is frozen and no errata mechanism exists — that
  is `adr-errata-convention`, still open. Recorded there as a concrete instance
  instead of inventing a shape in a config PR.
- **Tempted:** daily interval and no grouping, which surfaces advisories fastest.
  **Declined:** the only stated objection to this item was weekly review volume.
  Optimising against the objection the owner raised is the point.

## Tasks

### T1 — Read ADR-0083's disposition before writing anything
- **Mode:** goal-based. `Done when:` the ADR's recorded reason for deferring is known
  and the settings answer it.
- **Tests:** no stub (goal-based).
- **Status:** done. Deferred on review volume, not technique; AC2 is the response.

### T2 — Write and validate the config
- **Mode:** goal-based. `Done when:` it parses, `version == 2`, and both directories
  contain a `package.json`.
- **Tests:** no stub — nothing in CI validates dependabot.yml; the check is the
  parse assertion recorded in AC4.
- **Touches:** `.github/dependabot.yml`.

### T3 — Close the slug; establish what depends on it
- **Mode:** goal-based. `Done when:` the slug is gone, `lint-spec-status` is clean,
  and every surviving reference to it is enumerated.
- **Tests:** no stub (goal-based).
- **Status:** done. Four prose references in two frozen documents; no lint invariant
  depends on the slug. Recorded as AC5 and appended to `adr-errata-convention`.
