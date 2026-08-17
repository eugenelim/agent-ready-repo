# Resolve-vs-surface disposition record

## PLAN

- Resolve: tighten HTTPS, provenance, and strict-JSON criteria from secure-design review; these close existing boundaries without expanding scope.
- Resolve: align execution with the installed Phase-1 sequential supervisor while retaining the approved dependency wave.
- Resolve: name the shared roster harness, correct task ownership, and materialize red construction stubs before production work.
- Resolve: require discrete argv or schema-validated data files with shell execution disabled for every tracker-derived CLI value.
- Surface: none. The prerequisite contracts and selected canonical queue entry are present.

## REVIEW

- Resolve: the first adversarial pass found normalized-only fixtures. Adapter
  construction tests now start with tracker-specific raw response envelopes,
  derive trusted provenance in executable code, validate the shared contract,
  and invoke a fake `work-intake` seam.
- Resolve: Jira and Jira Align destination validation is now bound to the
  credentialed sibling-client request path. Intake mode validates the base URL
  before token access, pins the credential URL and stable public DNS identity,
  rechecks before requests, disables redirects, refuses writes, and enforces
  timeout/retry/response-byte budgets without changing legacy callers.
- Resolve: add a sixth cross-profile fixture for a claimed defect without
  durable expected-behavior evidence; it remains a Draft spec route with a
  named gap and no processor.
- Resolve: the GitHub `gh` wrapper now bounds output bytes and rejects malformed
  or non-RFC-8259 JSON before normalization.
- Resolve: every adapter now enforces the shared schema's exact sensitive
  constraint-name denylist, including API/private/access key variants, and the
  roster contract test covers `api_key` explicitly.
- Resolve: Jira and Jira Align preserve `HTTPS_PROXY`/`NO_PROXY` behavior in
  intake mode, pin the configured proxy socket, retain destination DNS checks,
  and load enterprise CA settings. Direct connections remain address-pinned.
- Resolve: all four shipped adapter scripts install the required UTF-8 stdout
  and stderr guards before producing output.
- Resolve: lifecycle checkboxes and final statuses are deferred until all gates
  and specialist reviews are clean; they are release bookkeeping, not evidence
  for the implementation review.
- Surface: the managed environment blocks legacy tests that construct a real
  TLS transport from reading the installed CA bundle, blocks `pip-audit` while
  it bootstraps isolated virtual environments, and prevents Semgrep's remote
  rulesets from creating an X509 trust store. Focused mocked boundary tests,
  Bandit, and all remaining local gates stay available; no dependency or
  environment repair is attempted.
- Accepted risk at the human gate: scanner-owned dependency-CVE and
  Semgrep injection/exception coverage is incomplete in this managed session.
  This is not a waiver for merge: no dependency changed, Bandit and the
  security review's reasoning/hybrid checks are clean, but the PR/CI gate must
  run `pip-audit` and Semgrep successfully before merge approval.
- Named skip: no `experience-reviewer` role is exposed in this session. The
  adopter-facing guide changes were checked against the six common fixtures
  and recorded in `adapter-guide-walkthrough.md`; guide/source validation
  passed, while the unavailable Astro runtime prevented a rendered link pass.
- Named skip: no `frontend-reviewer` was warranted because the diff has no
  primary HTML, CSS, or JavaScript output.
