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

**The residual, stated plainly:** defeating this requires editing
`.github/claude-plugin-publish-control.json` in the same commit as the forged
evidence. That is a reviewable change to the repo-authored contract, which is
the same anchor the decommission escape hatch already rests on — and it is
strictly more than the change costs today, which is nothing.

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

## Honest scope

- **This binds the artifact to a declared subject, not to an unforgeable one.**
  § Decision 3 says what was declined and why; § Decision 2 says exactly what
  `repo` is and is not. Read both before concluding the artifact is now
  tamper-evident — it is subject-*stating*, which is a smaller and more useful
  claim.
- **One field of the committed artifact was written by hand.** § Decision 4.
  Every later capture writes it.
- **The canary outcomes remain operator-asserted.** Unchanged by this spec, and
  deliberately so — `capture-publish-control-evidence.py`'s docstring explains
  why inferring them would make the evidence self-confirming.
