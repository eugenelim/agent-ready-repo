# Spec: capture-evidence-repo-dot-segments

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** none — see § Named deviation
- **Mode:** full (security boundary — `_validate_repo` is input validation on
  an operator-supplied value that is interpolated into JWT-authenticated API
  paths)
- **Constrained by:** none. Recorded as a deferral of
  [`bandit-nosec-comment-hygiene`](../bandit-nosec-comment-hygiene/spec.md)
  § Deferred.
- **Contract:** none (an internal operator script; no published interface)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Named deviation from full mode

The `loop-engine` / `loop-cohort` state machine was not run, and there is no
`plan.md`. The two human approval gates it sequences were **granted up front by the
requester** as a standing instruction to carry this through to merge.
`adversarial-reviewer`
and `security-reviewer` were both run, and both produced findings that are
applied here.

Every AC below is met and both gates are granted, so the spec is `Shipped`. It
was held at `Implementing` until the grant rather than flipped by the author.

## Objective

`_validate_repo` in `tools/capture-publish-control-evidence.py` accepts
`[A-Za-z0-9._-]+/[A-Za-z0-9._-]+`. `.` and `..` are built entirely from that
character set, so the pattern admits RFC 3986 dot-segments, and `urllib` sends
the selector it is handed without normalising it. A `--repo` value can therefore
reach an `api.github.com` endpoint other than the one the operator named.

Success: dot-segments are rejected, legitimate dotted repository names still
work, and a test pins both directions.

## What is actually reachable — and what the register entry got wrong

The backlog entry and the originating spec both cite `--repo ../../app`. That
value is **already rejected**: it has three segments, and the pattern is
`fullmatch` over exactly two. Verified by construction.

The values that *do* get through are the two-segment ones:

| `--repo` | admitted today | resulting path | transport of that path |
| --- | --- | --- | --- |
| `../..` | yes | `repos/../../environments/…` | `gh api` |
| `owner/..` | yes | `/repos/owner/../installation` | `_app_api` (urllib) |
| `./name` | yes | `/repos/./name/installation` | `_app_api` (urllib) |
| `../name` | yes | `/repos/../name/installation` | `_app_api` (urllib) |
| `owner/.` | yes | `/repos/owner/./installation` | `_app_api` (urllib) |
| `../../app` | **no** — three segments | n/a | n/a |

Every admitted value flows through *both* legs — the column names the
transport of the example path shown, not the only one reached. Five of the six
`--repo`-interpolated reads go through `_gh_api` → `gh api`; only the
installation read goes through `_app_api`. For the urllib rows,
`urllib.request.Request("https://api.github.com/repos/../../app/installation")`
reports `selector == "/repos/../../app/installation"` — unnormalised. Whether
GitHub resolves the dot-segments or 404s on them is unverified and does not
change the point: it is not the read the operator named.

## Honest scope — this is hygiene, not a live hole

Stated plainly because the fix looks scarier than it is:

- **No privilege is gained.** Whoever passes `--repo` already holds the App
  private key the script requires; they can already read anything the App can.
- **The JWT cannot leave `api.github.com`** — but this covers only one of the
  two transports. `_app_api` (the JWT-bearing leg) hard-codes the scheme and
  host and installs `_NoRedirect`, which matters because urllib's default
  handler copies the `Authorization` header across an origin change. The other
  five reads go through `gh api`, which carries the operator's OAuth token, not
  the JWT, and whose confinement rests on `gh`'s own client and its configured
  host — nothing in this file. Say that plainly rather than letting the
  `_NoRedirect` sentence stand for both.
- **What is actually wrong** is narrower than "the artifact lies about its
  subject", and the honest version is less flattering to this fix: the evidence
  document records no repository field at all (`build_evidence` emits `version`,
  `branch`, `app`, `environment`, `identities_agree`, `canary`, `observed_at`,
  `observation_source`). So nothing binds the evidence to a subject, and
  `--repo other-org/well-configured-repo` still produces a byte-indistinguishable
  artifact. Dot-segments were one route to a wrong-subject capture; this closes
  that route and does **not** make the artifact trustworthy about its subject.
  Binding the artifact to its repository is the real fix, and is recorded as
  `publish-control-evidence-not-repo-bound`.

## Why not "each segment must start alphanumeric"

`lint-spec-status.py` guards its contract paths that way, and copying it here
would be wrong: **`owner/.github` is a real GitHub repository**, and a leading
dot is legal in a repository name. Narrowing the charset would reject a valid
target in the name of safety. The dot-segments are therefore rejected by name,
leaving every other dotted name (`.github`, `a.b`, `..x`, `x..`) working.

## Acceptance Criteria

- [x] **AC1 — dot-segments are rejected.** `../..`, `owner/..`, `./name`,
      `../name`, and `owner/.` each raise `CaptureError`.

- [x] **AC2 — legitimate dotted names still work.** `owner/.github`,
      `my-org/my.repo`, `a_b/c-d.e`, `owner/..x`, and `owner/x..` are accepted
      and returned unchanged. AC2 is the reason AC1 is implemented as a
      segment-equality check rather than a charset narrowing.

- [x] **AC3 — the existing shape checks are unchanged.** `owner`,
      `owner/name/extra`, `""`, `owner/`, `/name`, and values containing a
      space are still rejected. The new rule is additive.

- [x] **AC4 — the two failures are distinguishable.** A dot-segment value
      raises the dot-segment message, not the generic shape message, so the
      operator is not sent looking for the wrong defect.

- [x] **AC5 — the guard is on the live path.** `_validate_repo(args.repo)` runs
      in `main` before `build_evidence`, which is the only caller that reaches
      `_gh_api` / `_app_api`. Confirmed by reading the call graph, not assumed.

- [x] **AC6 — a self-test exists and is gated.**
      `tools/test-capture-publish-control-evidence.py` covers AC1–AC4 and is a
      step in `tools/repo/build_gate_chain.py`'s `build-check` chain, beside the
      linter for the artifact this script produces. The script is operator-run
      and never executes in CI, so without this the guard has no exercise at all.

- [x] **AC7 — the suppression rationale it cites stays true, pinned by
      behaviour.** The `# nosec B310` on `opener.open` gives two reasons, and
      the self-test observes both on the *production* path rather than grepping
      the source: it spies `urllib.request.Request` to assert every URL
      `_app_api` builds starts `https://api.github.com/`, and spies
      `build_opener` to assert `_app_api` passes `_NoRedirect`. Re-deriving an
      opener locally would only have tested urllib.

- [x] **AC7b — the cited control is pinned by behaviour, not by grep.**
      `_NoRedirect().redirect_request(...)` raises `CaptureError`; every one of
      `redirect_request` is defined on `_NoRedirect` itself rather than
      inherited — a `getattr` loop over `http_error_30x` would not show that,
      since the class subclasses `HTTPRedirectHandler` and every one of those is
      non-`None` by inheritance. Verified by mutation: deleting
      `redirect_request` fails the self-test, where the previous substring check
      passed green while the bearer JWT would have been forwarded across an
      origin change.

- [x] **AC7c — `gh api` cannot read a path as a flag.** The call passes `--`
      before `path`. A leading-dash owner (`-h/name`) satisfies the charset
      guard, so this is what keeps that from mattering to the five reads that
      go through `gh`. Pinned behaviourally — `subprocess.run` is spied and
      `argv[:3]` asserted — because a source substring is exactly what this
      spec's `Always do` boundary rules out. Mutation-verified.

- [x] **AC8 — gates pass.** `python3 tools/lint-ruff.py`, `make lint-mypy`,
      `SKIP_SAST=1 make build-check`, and `make sast`.

- [x] **AC9 — the register is dispositioned.** `capture-evidence-repo-dot-segments`
      is removed from `workspace.toml [backlog].open`.

## Boundaries

### Always do

- Always keep the two rejection reasons distinguishable, so an operator is not
  sent looking for the wrong defect.
- Always pin a cited control by behaviour. The `# nosec B310` rationale names
  `_NoRedirect`; a substring match on the source is not a pin.

### Ask first

- Ask before changing `_gh_api`'s transport or `_app_api`'s opener — the B310
  suppression's rationale depends on both, and this spec only guards the input.
- Ask before adding a repository field to the evidence artifact; that changes
  the schema the linter compares against.

### Never do

- Never narrow the character class to exclude a leading dot. See § Why not.
- Never change the request construction, the `_NoRedirect` opener, or the B310
  suppression. They are cited as context here; this change is the input guard
  only.
- Never make the script reachable from CI. It reads a private key and live org
  settings; only its guard is gated.

## Testing Strategy

Goal-based, against the real function:

- `python3 tools/test-capture-publish-control-evidence.py` → all cases pass.
  Counts live in the test, not here, so adding a case cannot silently drift this
  document.
- The reachability table's `admitted today` column came from running
  `re.fullmatch`; the urllib rows' selectors from
  `urllib.request.Request(...).selector`. The `gh api` row is not a urllib
  selector and is labelled as such.
- **Mutation check on the redirect control.** Deleting `redirect_request` from
  `_NoRedirect` must fail the self-test. Before review it did not: the case
  grepped the source for `build_opener(_NoRedirect)`, which survives the
  deletion, while the resulting handler would forward the bearer JWT to another
  origin. Re-run after the fix — the mutation now fails one case.
- `SKIP_SAST=1 make build-check` runs the self-test as a chain step.

## Assumptions

- GitHub normalises `..` server-side rather than 404ing on it. Not verified
  against the live API — doing so would require the App key and would issue real
  authenticated reads. The fix does not depend on it: an unnormalised selector
  that 404s is still a request for an endpoint the operator did not name.

## Declined

- **Percent-encoding the segments instead of rejecting them.** It would make
  `owner/..` a literal path segment rather than a traversal, but a repository
  named `..` does not exist, so the only thing that behaviour buys is a
  confusing 404 in place of a clear error.
- **Validating inside `_gh_api` / `_app_api` instead.** Two call sites, one
  entry point; the guard belongs where the operator's value enters, and moving
  it would leave `build_evidence`'s signature accepting an unvalidated repo.
- **Amending `bandit-nosec-comment-hygiene`'s § Deferred**, which says this
  deferral is "Recorded in `workspace.toml [backlog].open`" — a statement this
  PR makes false. That spec is **Frozen**, and `docs/CONVENTIONS.md`
  § *Superseding a frozen document* is explicit that an append is a body edit,
  however additive it reads. The forward pointer is this spec's `Constrained
  by:` line; the parent's stale sentence is the accepted residue of the freeze
  rule, not an oversight.
- **Using the return value of `_validate_repo` at the call site.** `main`
  discards it and passes `args.repo` on. Threading the return value through
  would be tidier but changes nothing — the function raises on every rejected
  value, so the guard is total either way. Left alone to keep the diff to the
  guard.
