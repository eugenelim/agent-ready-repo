# Brief backlink lints report canonical and legacy forms

- **Slug:** `brief-backlink-provenance-lints`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [spec/traceability-lint](../../specs/traceability-lint/spec.md)

## Outcome

Brief backlink lints resolve canonical local paths and advise authors when legacy slug form remains in use.

## Opportunity

Canonical path-form `Brief:` backlinks are classified as unresolvable cross-repository pointers, while bare-slug backlinks pass early linting without an advisory and only block dispatch during `dispatch.py` reconciliation.

## What this absorbs

### traceability-brief-path-backlink-unresolved

- `_CROSSREPO_RE` in `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py` is defined as = re.compile(r".+/.+|.+@.+|.+·.+")`, so any `<dir>/<file>.md` producer pointer is classified as cross-repository.
- A canonical local `docs/.../brief.md` back-link is reported as `unknown / not-yet-catalogued (cross-repo, unresolvable)` and loses the brief↔spec edge it should generalize. The lint is informational and exits 0, so no gate catches it.
- A mistyped path is only informational, whereas a mistyped bare slug is a fatal dangling pointer; path-form typos therefore receive less strict detection.
- Recorded fix: resolve a canonical local brief path to its brief node before endpoint classification in `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py`.
- The attempted naive alias was withdrawn because `docs/specs/traceability-lint/spec.md` makes changing a producer-pointer field Ask-first, forbids identifying a node by file path, hardcoding an artifact path, and treating a well-formed cross-repo reference as dangling. It also hard-failed on brief files under a `[traceability].briefs` override.
- Unblocked by a reviewed amendment to `docs/specs/traceability-lint/spec.md` carrying the Ask-first sign-off; no `needs` edge.

### brief-backlink-slug-form-needs-lint-note

- `packs/core/.apm/skills/author-delivery-brief/scripts/lint-brief-coverage.py` still accepts the slug, path, and `brief:<slug>` forms: `if back in (brief_slug, rel, f"brief:{brief_slug}") and slug not in mapped`.
- `lint-brief-coverage.py` and `lint-traceability.py` accept a bare-slug `Brief:` back-link, so it passes every early gate and only fails later at `dispatch.py` reconciliation, where it blocks dispatch. Their docstrings call slug form backward-compatible only, but lint-time output gives authors no warning.
- Recorded fix: have the coverage lint emit a non-fatal note naming each spec whose back-link matched by slug rather than path, in `lint-brief-coverage.py` and the `receive-brief` skill.
- The work was deferred because it adds output to a lint many repositories run in CI.
- Unblocked once the note is agreed to be non-fatal and the lint's output contract is versioned; no tracked dependency and no `needs` edge.

## Assumptions

- None.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

## Non-goals

- The new slug-form note is non-fatal; no lint gains a new failure.
- Dispatch reconciliation in `dispatch.py` is unchanged.
- No producer-pointer change beyond the owner-approved amendment to the traceability-lint spec.

**Riskiest assumption:** resolving a repository-relative brief path to its node does not break the spec's rules against identifying a node by file path or hardcoding an artifact path. Agent-only test: fixtures for a real path, a mistyped path and a `[traceability].briefs` override must all behave as the amended spec states.

## Readiness

Route: new-spec, one session. The owner has approved amending `docs/specs/traceability-lint/spec.md` for the Ask-first producer-pointer rule.

Checked 2026-11-05: `_CROSSREPO_RE` is still `.+/.+|.+@.+|.+·.+` at `lint-traceability.py` line 977, and `lint-brief-coverage.py` line 279 still accepts the slug, path and `brief:<slug>` forms. First slice: amend the spec, resolve a repository-relative path that exists locally to its brief node before the cross-repo classification, and add a non-fatal note to the coverage lint for slug-form back-links. Proof: fixture cases for a real path (resolves), a mistyped path (reported as dangling) and a slug-form back-link (note, exit 0).
