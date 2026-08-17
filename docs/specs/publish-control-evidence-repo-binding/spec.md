---
title: Bind the publish-control evidence artifact to the repository it describes
slug: publish-control-evidence-repo-binding
---

# Spec: the publish-control evidence names its subject

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** none — see § Named deviation
- **Mode:** full (security boundary — the artifact is the sole offline evidence
  that the ADR-0079 publisher App was provisioned, and `validate_sequencing`
  branches the whole publisher-identity gate on whether it exists. It is also a
  schema change to a committed contract.)
- **Constrained by:**
  [ADR-0079](../../adr/0079-executable-plugin-branch-publisher-identity.md)
  (the publication-control boundary this evidences);
  [`capture-evidence-repo-dot-segments`](../capture-evidence-repo-dot-segments/spec.md)
  (which closed one route to a wrong-subject capture and named this as the
  wider gap it did not close)
- **Contract:** none (a repo-internal desired-state/evidence pair; no published
  interface)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Named deviation from full mode

The `loop-engine` / `loop-cohort` state machine was not run, and there is no
`plan.md`. The two human approval gates it sequences — **spec-approved** and
**plan-approved** — were **granted up front by the requester**, as a standing
instruction to carry this through to merge. The merge decision itself was
explicitly retained. `adversarial-reviewer` and `security-reviewer` were run.

## Objective

`docs/specs/claude-plugin-hook-parity/publish-control-evidence.json` records
what the publication controls look like — the branch ruleset, the App
installation, the protected environment, the canary outcomes — and records
**nothing about whose controls they are**. `build_evidence` emits `version`,
`branch`, `app`, `environment`, `identities_agree`, `canary`, `observed_at`,
`observation_source`. No repository field.

So the artifact does not bind to a subject. Run
`capture-publish-control-evidence.py --repo some/other-well-configured-repo`
and the output is byte-indistinguishable from a capture against this one — and
`lint-claude-plugin-publish-control.py` would accept it, then let
`validate_sequencing` conclude that *this* repository's publisher App is
provisioned.

`capture-evidence-repo-dot-segments` closed one route to a wrong-subject capture
(a dot-segment `--repo` retargeting the API reads) and surfaced this wider gap in
its § Honest scope rather than hiding it.

## Decision 1 — `repo` is desired state as well as evidence, and the linter compares them

The file already models exactly this shape four times over. `branch`, `app`,
`environment` and `canary` each appear in the repo-authored
`.github/claude-plugin-publish-control.json` **and** in the captured evidence,
and `compare_evidence` requires equality. `repo` becomes the fifth: the desired
file declares the subject the controls are authored for; the evidence records
the subject the observations were made against; the linter refuses a mismatch.

This is an application of the existing design, not an extension of it — which
matters, because the alternative below is an extension.

## Decision 2 — `repo` is not an independent observation, and that is the point

Every other block in the evidence is read back from the GitHub API. `repo` is
not: it is the `--repo` argument the operator passed. Recording it is still
sound, and the reason is worth stating precisely rather than glossing:

> **`repo` is not one of the observations. It is the subject *of* them.** Every
> `gh api repos/{repo}/…` read in `build_evidence` is made against that value,
> so recording it is a faithful statement of what the rest of the document
> describes. A `--repo` naming a repository the operator cannot read fails at
> the first API call, long before anything is written.

What it therefore does **not** prove is that the operator captured against the
repository they committed into. It proves the artifact says which repository it
describes, and the linter proves that matches what this repository's committed
contract claims as its subject.

## Decision 3 — declined: deriving the subject from the runtime environment

The stronger-looking option is to resolve the "committing repo" at lint time
from something no committed file can forge — `GITHUB_REPOSITORY` in Actions, or
the `origin` remote locally — and compare the evidence against *that*. Declined,
for three reasons:

1. **It would make the gate behave differently locally and in CI.** With
   `GITHUB_REPOSITORY` set only in Actions, the binding would hold on the
   required check and not on `make build-check`. That is precisely the
   local/CI divergence class `tools/lint-ci-parity.py` exists to catch, imported
   into a linter to close a different hole.
2. **The `origin` fallback is not the same fact.** A contributor working from a
   fork has `origin` pointing at the fork; the gate would redden on a change
   that has nothing to do with publication controls.
3. **It would be a second, stronger trust model applied to one field only.**
   Everything else in this file rests on "an explicit, reviewable edit to the
   committed contract" — that is stated outright as the *only* legitimate route
   to running without evidence (`control_status: decommissioned`). A field that
   answered to the runtime environment while its four siblings answered to
   review would be harder to reason about, not safer.

**But the reasons are about the linter, and there is one place they do not
reach.** Security review made the point: `.github/workflows/publish-claude-plugins.yml`
**only ever runs in Actions**, so reason 1 does not apply to it, reason 2 has no
`origin` fallback to be noisy, and reason 3 is untouched because the linter's
trust model does not change. So the runtime binding goes there — see
§ Decision 5 — and the linter keeps the file-to-file comparison.

**The residual on the linter half, stated plainly:** defeating the file-to-file
comparison requires editing `.github/claude-plugin-publish-control.json` in the
same commit as the forged evidence. That is a reviewable change to the
repo-authored contract, the same anchor the decommission escape hatch rests on.
Note what that anchor is worth here: ADR-0079's 2026-08-12 erratum set
`prevent_self_review: false` *because* one person merges, so the reviewer and
the author can be the same actor. That is why § Decision 5 exists — the
publish-time check does not rest on review at all.

## Decision 5 — the runtime binding goes in the publish workflow, not the linter

Two committed files travelling together certify nothing in a **copy**. Fork this
repository, or clone-and-push it elsewhere, and both halves come along: they
still compare equal, `make build-check` is green, and `validate_sequencing`
concludes the publisher App is provisioned — for a repository whose dist-branch
ruleset, App installation scope and protected environment were never observed at
all. That is the wrong-subject failure this spec exists to close, in the one
case the file-to-file design structurally cannot see.

The linter gains an **optional `--subject`** argument, and
`publish-claude-plugins.yml` passes `"$GITHUB_REPOSITORY"` to it. When given, it
must equal the desired file's `repo`.

An earlier draft put the comparison in a shell step of its own. Review was right
that that was worse: it would have duplicated `DESIRED_PATH` and the JSON parse,
and — the load-bearing objection — the only unforgeable half of the binding
would have lived in a YAML string that no test could delete-and-verify. As an
argument it lands in the linter's existing mutation suite instead.

It costs none of § Decision 3's three reasons:

- the flag is **optional**, so `make build-check` passes none and behaves
  identically locally and in CI — no divergence;
- `github.repository` is set by the runner and no committed file can forge it;
- the desired/evidence comparison is untouched, so the file's trust model is
  unchanged.

It also refuses a fork attempting to publish, which is correct on its own terms.

Three deletions verified: removing the `--subject` comparison reddens the lint
suite; removing `--subject` from the workflow invocation reddens
`test-publish-claude-plugins.py`; removing the schema-version comparison reddens
the lint suite. Neither the flag nor its use can be dropped silently.

## Decision 4 — the version goes to 2, and the committed artifact is hand-edited

`compare_evidence` requires `evidence.version == desired.version`, so a schema
change has a version to move. Bumping to `2` makes a stale v1 artifact fail on
the version — a clearer message than "repo missing" — and makes the schema
change visible in the desired-state diff.

The committed evidence artifact cannot be re-captured here: doing so needs the
publisher App's private key. So its `repo` and `version` fields are **added by
hand**. This is worth naming rather than glossing:

- The value added is true. The artifact was captured against this repository —
  `observation_source: github-api-sanitized` and every field in it came from
  `repos/eugenelim/agent-ready-repo/…`.
- It is nonetheless the one field in that file not written by the capture tool.
  Every subsequent capture writes it from `--repo`; this one instance does not.
- The alternative — requiring `repo` and letting the committed artifact go red
  until someone re-runs the capture — would break `make build-check` on `main`
  for everyone until an operator with the key is available. Not acceptable for
  a hygiene fix.

## Acceptance Criteria

- [x] **AC1 — the capture tool records the subject.** `build_evidence` emits
      `repo` alongside `version`, and the value is the validated `--repo`
      argument every API read in that function was made against.

- [x] **AC2 — the linter admits the key and requires it.** `repo` joins
      `ALLOWED_EVIDENCE_KEYS`, and `validate_desired` rejects a desired-state
      file whose `repo` is absent, empty, or not a bare `owner/name`.

- [x] **AC3 — the shape rule is shared, not restated.** The linter reuses
      `capture-publish-control-evidence.py`'s `_validate_repo` — loaded by path,
      the way `_load_pack_scope_module` already loads `tools/pack_scope.py` —
      so the two cannot drift. A restated regex would be a second copy of a rule
      `capture-evidence-repo-dot-segments` already got wrong once.

- [x] **AC4 — a mismatch fails, and is proven to fail.** `compare_evidence`
      reports an error when `evidence["repo"]` differs from `desired["repo"]`,
      is absent, or is `None`. Each is a mutation case in
      `tools/test-lint-claude-plugin-publish-control.py` — the mutated input
      must go red, not merely the clean input stay green.

- [x] **AC5 — the version moves.** Both files carry `version: 2`;
      `validate_desired` requires `2`; a v1 evidence file fails.

- [x] **AC6 — the committed artifact carries its subject.**
      `publish-control-evidence.json` gains `repo: "eugenelim/agent-ready-repo"`
      and `version: 2`, and `lint-claude-plugin-publish-control.py
      --require-live-evidence` exits 0 against the committed pair.

- [x] **AC7 — deleting the control turns the gate red.** With the `repo`
      comparison removed from `compare_evidence`, the mutation cases added by
      AC4 fail. Verified by removing it and running the suite, not by reading
      the assertion.

- [x] **AC8 — no identifier is leaked.** `_identifier_leaks` still reports
      nothing for the committed artifact; `owner/name` is a public repository
      path, not one of the internal identifiers `FORBIDDEN_IDENTIFIER_KEYS`
      exists to keep out. The allowlist is extended by exactly one key.

- [x] **AC9 — gates pass.** `python3 tools/lint-ruff.py`, `make lint-mypy`,
      `SKIP_SAST=1 make build-check`, `make sast`, and
      `lint-spec-status.py --root . --base-ref origin/main` all exit 0.

- [x] **AC9a — the publish workflow refuses a repository the control was not
      authored for.** The linter takes an optional `--subject`;
      `publish-claude-plugins.yml` passes `"$GITHUB_REPOSITORY"`. Pinned in two
      places, because either alone is defeatable:
      `tools/test-lint-claude-plugin-publish-control.py` drives `main()` with no
      subject (accepted), the declared one (accepted), a fork's (refused) and an
      empty one (refused); `tools/test-publish-claude-plugins.py` asserts the
      workflow passes the flag **and** that the linter enforces it. Each
      verified by deleting the control.

- [x] **AC9b — the comparisons stand on their own.** `compare_evidence`'s repo
      check does not rely on `validate_desired` running first: with `repo`
      absent from **both** documents, `.get(...) != .get(...)` compares equal,
      so the check reads the desired value's type explicitly. A mutation case
      pins it. The schema-version comparison — the only thing that rejects a
      stale v1 artifact against the v2 desired file, i.e. this change's own
      migration — gains the negative control it was missing.

- [x] **AC10 — the register entry is closed.**
      `publish-control-evidence-not-repo-bound` is removed from
      `workspace.toml [backlog].open`, verified with `tomllib`.

## Boundaries

### Always do

- Always keep the desired-state and evidence halves of a field in step; a field
  in one and not the other is a field the linter cannot use.
- Always mutation-test a new comparison: delete it and confirm the suite goes
  red.

### Ask first

- Ask before binding any field of this pair to the runtime environment. See
  § Decision 3; it changes the trust model for the whole file, not one field.

### Never do

- Never restate the `owner/name` rule. One definition, loaded by path.
- Never add an internal identifier to the evidence to strengthen the binding —
  an App ID, an installation ID, a ruleset ID. `_identifier_leaks` exists to
  refuse exactly that, and `identities_agree` is the sanctioned substitute.
- Never re-capture the artifact as a way of "fixing" a mismatch. A mismatch
  means the evidence describes the wrong repository; the fix is to find out
  which.
- Never hand-author a field the capture tool writes, except as § Decision 4
  records for the one-off schema migration. The artifact's whole value is that
  a machine observed it; a hand-written field is a claim, not evidence.

## Testing Strategy

Goal-based plus mutation, in the existing harness. No new test file: both
`tools/test-lint-claude-plugin-publish-control.py` and
`tools/test-capture-publish-control-evidence.py` are already mutation-shaped and
already chained into `make build-check` via `tools/repo/build_gate_chain.py`.

| AC | How |
| --- | --- |
| AC1 | Call `build_evidence` with the three network readers stubbed; assert the returned dict's `repo`. |
| AC2, AC5 | `validate_desired` against the real desired file (clean) and against mutations dropping / emptying / malforming `repo` and moving `version` (each red). |
| AC3 | Assert the linter's validator **is** the capture tool's function object, not a lookalike. |
| AC4 | `compare_evidence` mutation cases: mismatched, absent, `None`. |
| AC6 | Run `lint-claude-plugin-publish-control.py --require-live-evidence`; assert exit 0. |
| AC7 | Delete the comparison; re-run the suite; assert it reports failures. Restore; assert green. |
| AC8 | `_identifier_leaks` on the committed artifact. |
| AC9a | `lint.main()` under four `--subject` values; plus `test-publish-claude-plugins.py`'s two assertions. Then delete each control and re-run. |
| AC9b | `compare_evidence` with `repo` absent from both documents, and with `version: 1` evidence against the v2 desired file. |
| AC9, AC10 | The gate commands; `tomllib` on `workspace.toml`. |

## What the mutation pass caught

Worth recording, because it is the reason AC7 is written as "delete the control
and confirm the suite goes red" rather than "the suite asserts X".

The first draft's *"`build_evidence` validates the subject it records"* case
passed — and kept passing when the validation was deleted. It called
`build_evidence("owner/..")` with the real network readers in place, so the
`CaptureError` it caught came from the first `gh api` call, not from the
validation. A green assertion, an absent control, and no signal. It now stubs
all three readers around the negative case, so the validation is the only thing
that can raise; deleting it turns the case red.

`tools/test-capture-publish-control-evidence.py` carries that reasoning as a
docstring on the stub helper, so the next person to touch it knows why the
stubs wrap the negative case and not just the positive one.

## Deferred

| Slug | Why not here |
| --- | --- |
| `publish-control-evidence-max-age` | `observed_at` is checked for being a non-empty string and nothing else, so the artifact never goes stale. Real, and made more visible by this change — but expiry blocks every merge until an operator with the App private key re-captures, so the operational answer (how long, who is paged, what the escape hatch is) has to be decided first. |

## Honest scope

- **Two bindings of different strength, and it matters which is where.** The
  linter's is between two committed files, so it binds the artifact to a
  *declared* subject — defeating it costs one more reviewable edit. The publish
  workflow's is against `$GITHUB_REPOSITORY`, which no committed file can forge,
  but it runs only at publication. So `make build-check` on a copy of this
  repository is still green while attesting to nothing; what that copy cannot do
  is publish. § Decisions 2, 3 and 5. Read them before concluding the artifact
  is tamper-evident — the linter half is subject-*stating*, which is a smaller
  and more useful claim.
- **One field of the committed artifact was written by hand**, while the file
  asserts `observation_source: github-api-sanitized` and nothing in the file
  itself records the exception — § Decision 4 is the only place a reader learns
  it. A one-shot `--migrate-subject <owner/name>` mode on the capture tool would
  have kept the value tool-written and the provenance claim literally true;
  declined as a mode added to an operator tool for a single migration, but it is
  the better answer if this recurs.
- **The canary outcomes remain operator-asserted.** Unchanged by this spec, and
  deliberately so — `capture-publish-control-evidence.py`'s docstring explains
  why inferring them would make the evidence self-confirming.
