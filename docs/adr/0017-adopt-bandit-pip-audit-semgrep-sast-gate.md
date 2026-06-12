# ADR-0017: Adopt Bandit + pip-audit + Semgrep as the repo's SAST/SCA gate

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-06-12
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** the implementing spec `docs/specs/sast-sca-tooling/`; ADR-0003 (credential-broker contract — `sso-broker.py` is one of the scanned scripts)

## Context

The repo ships agent skills, tool scripts, and two Python packages, but had **no
static-analysis tooling of any kind** — no SAST, no dependency (SCA) scan, no
config, no CI job. CI (`build-check.yml`) is entirely self-hosting drift gates
plus targeted `pytest`; nothing inspects the ~76k lines of Python for the
security-relevant patterns a scanner catches.

The trigger was concrete: an **internal organisational Snyk scan** is flagging
some of the skill/tool scripts, and the maintainer has **no access to that
scan's output**. Without a local equivalent there is no way to see what Snyk
sees, reproduce it, or gate it before it reaches the org scan.

Running **Bandit** (the reference Python SAST tool, and the closest open-source
analog to Snyk Code's Python ruleset) across `tools/`, `packs/`, and
`packages/` reproduced a small, tractable set of medium/high findings in shipped
code — weak SHA-1 digests, an unsafe XML parse of network data, and a handful of
pattern false positives (a `yaml.load` against a `SafeLoader` **subclass**;
`urllib.request.urlopen` against constant `https://` bases) — under a large
low-severity tail dominated by `assert` use in test files.

Two constraints shape the decision:

- **The packages are deliberately stdlib-pure.** Both `agentbundle` and
  `credbroker` declare `dependencies = []`; `credbroker`'s only third-party code
  sits behind an optional `[crypto]` extra. This zero-runtime-dependency posture
  is a load-bearing property, not an accident — see `credbroker`'s purity gate in
  CI. Any scanner we adopt must be a **dev/CI-only** tool and must never become a
  runtime dependency of a shipped package.
- **We cannot see the Snyk findings, and `# nosec` does not reach Snyk.** Bandit
  honours `# nosec`; Snyk does not. So suppression and the real remediation are
  different levers, and the choice between them must be explicit per finding.
- **Bandit has no taint/dataflow engine.** It is an AST pattern-matcher: it
  cannot see that an *untrusted value flows into* a sink. A reported Snyk Code
  finding on the `session-start` hook — environment-variable input flowing into
  `pathlib.Path` (CWE-22/73 path injection) — is invisible to Bandit at any
  severity, and the registry Semgrep packs did not carry that source→sink rule.
  Closing the gate's gap therefore needs a *taint-capable* lens, not more Bandit
  tuning.

## Decision

**We adopt four open-source scanners as the repo's CI-only SAST/SCA gate:
Bandit (Python pattern SAST), pip-audit (Python dependency / SCA), Semgrep
(cross-cutting SAST, including custom `mode: taint` rules), and CodeQL (deep
interprocedural dataflow/taint — the open-source analogue of Snyk Code's
engine).** They run behind a `make sast` target that is **chained
into `make build-check`** — the repo's single native gate, run locally
(CONTRIBUTING lists it among the gates that run locally) and in the existing
`build-check.yml` CI on every PR — so the gate is dogfooded into this repo's own
development rather than living in a separate, skippable workflow. None of the
three is ever added to a shipped package's runtime dependencies.

Boundaries on the decision:

- **Bandit is the primary Python SAST gate.** It is configured (repo-root
  `bandit.yaml`) to **fail on medium-or-higher severity at medium-or-higher
  confidence**, excluding test trees and skipping `B101` (`assert` use) — the
  large low-severity tail is noise for an attack-surface gate, not signal. This
  keeps the gate achievable and focused on what an org scan would block on.
- **pip-audit is the SCA gate.** It audits the dependency manifests the repo
  actually owns — `tools/requirements.txt`, the two packages, and the shipped
  per-skill `requirements.txt` files (which are what adopters install) — for
  known-vulnerable versions.
- **Semgrep is the cross-cutting SAST gate**, run against curated registry
  rulesets (`p/python`, `p/security-audit`). It catches dataflow-shaped issues
  Bandit's pattern rules miss and is the lens that extends to non-Python files
  if the repo ever grows them. Because Semgrep has no Windows support, the gate
  is reached **only** through `make build-check` (which the Windows CI job does
  not invoke — `build-check-windows.yml` runs `agentbundle.build check` +
  `tools/hooks/pre-pr.py` directly); the scanners live in `make sast` alone and
  are added to neither `tools/hooks/pre-pr.py` (the shipped hook, on the Windows
  path) nor `tools/pre-pr-catalogue.py` (the Linux `make build-check`
  aggregator).
- **Custom Semgrep `mode: taint` rules live in `tools/semgrep/`** and run in
  `make sast` (`--config tools/semgrep/`). They close the dataflow gap Bandit
  cannot — the first is `env-var-into-pathlib-path` (env → `pathlib.Path`,
  CWE-22/73), the class Snyk Code flagged. OSS Semgrep taint is
  *intraprocedural*; that is sufficient for same-function flows.
- **CodeQL runs as a code-scanning workflow** (`.github/workflows/codeql.yml`,
  `security-extended`, free for this public repo) for the *interprocedural*
  taint Semgrep OSS can't do — the closest open-source match to Snyk Code.
  Alerts surface in the Security tab / PR annotations; promoting them to a merge
  blocker is a branch-protection setting, not a code change.
- **Genuine taint findings are fixed in the shipped source, not suppressed.**
  The `session-start` env → `Path` flow is sanitized once in the hook
  (`_safe_override_path` rejects traversal before the path is used), so every
  adopter inherits the fix rather than each carrying a suppression.
- **Semgrep excludes four rules that duplicate Bandit's coverage**
  (`insecure-hash-algorithm-sha1`, `dynamic-urllib-use-detected`,
  `use-defused-xml`, `insecure-file-permissions`). Each maps to a class Bandit
  owns line-precisely (sha1 → B324 + `usedforsecurity=False`; urllib → B310;
  xml → B314; permissive-chmod → B103), so excluding the Semgrep duplicates
  avoids a second inline-pragma system in shipped pack scripts with no loss of
  coverage. The exclusion list lives in the `make sast` recipe.
- **Suppression policy — three-way, real-fix-first:**
  1. **Genuine findings get a real code fix**, never a suppression — a real fix
     satisfies Bandit *and* the internal Snyk scan, which a comment cannot.
  2. **Tool-specific false positives get `# nosec <ID> — <reason>`**, scoped to
     Bandit. These are patterns Snyk's dataflow analysis already clears (a
     `SafeLoader` subclass; a constant-scheme URL), so they need no Snyk ignore.
  3. **A committed `.snyk` policy file is the Snyk-native suppression vehicle**
     for findings that must be *accepted* in Snyk itself — primarily Snyk Open
     Source (SCA) issues, ignored by issue ID with a `reason` and an `expires`.
     Snyk **Code** (SAST) findings are suppressible through the same file only
     where the org enables "Consistent Ignores"; otherwise they are managed in
     the Snyk platform. Either path needs the issue ID from an actual Snyk run,
     so the `.snyk` file ships as a documented scaffold, populated when those
     IDs are available — not authored blind.

## Consequences

**Positive:**
- A local + CI gate now mirrors the class of issue the org's Snyk scan catches,
  so findings fail *our* build first instead of surfacing in a scan we can't see.
- `make sast` gives any contributor the same reproduction locally — no Snyk
  account or token required.
- Real fixes for the genuine findings (weak hash, unsafe XML parse) harden code
  that ships to adopters, not just our own tree.
- The three tools are complementary lenses (pattern SAST / dependency CVEs /
  dataflow SAST) and all are OSS, so the gate carries no licensing or
  per-seat cost.

**Negative:**
- Three dev tools are real maintenance surface — versions to pin and bump, rule
  updates to absorb.
- **Chaining `make sast` into `make build-check` slows the repo's own gate** —
  Semgrep fetches rules from the network and scans ~76k LOC, so a `build-check`
  that was seconds now takes longer and needs connectivity. We accept this so the
  gate is actually dogfooded (the maintainer's explicit priority over inner-loop
  speed); the mitigations are running narrower targets during the inner loop and
  bumping `build-check.yml`'s `timeout-minutes`.
- **Semgrep pulls its rulesets from the registry at scan time** (network
  dependency); upstream rule changes can shift findings between runs. We accept
  this for the broader coverage; the mitigation if it becomes flaky is to pin or
  vendor a ruleset (noted as a revisit, not built now).
- The gate is tuned (medium+ severity, test trees excluded). A real low-severity
  issue in non-test code could pass; the bet is that the org scan's blocking bar
  is also medium+ and that the excluded surface is genuinely low-risk.
- We cannot prove the gate matches the org Snyk scan exactly without access to
  it — Bandit/Semgrep are a high-fidelity proxy, not the same engine.

**Neutral / to revisit:**
- Whether Semgrep should be blocking or advisory, and whether to pin/vendor its
  rules, is revisited if registry drift causes CI flakiness.
- If the slower `build-check` proves painful in the inner loop, a fast/slow split
  (Bandit in `build-check`, the network-bound legs in a separate cadence) can be
  revisited — but the default is the single dogfooded gate.
- The `.snyk` file's Code-ignore entries stay empty until the org scan's issue
  IDs are obtainable.
- **The taint coverage is layered, and only `packs/` env→path is *blocking*.**
  The Semgrep taint rule is scoped to `packs/**` (auto-running agent primitives);
  the ~13 other env→path flows in `tools/` dev-CLIs (a maintainer's own arg) and
  install-time `install-marker.py` (installer-set `HOME`/plugin paths) are
  trusted-context and covered only by CodeQL, which is **advisory** until branch
  protection requires it. A future `tools/` script that reads genuinely
  untrusted env would inherit only advisory coverage — revisit the scope if that
  happens. Promoting CodeQL to a merge blocker is a one-time branch-protection
  setting, not a code change.

## Alternatives considered

- **Snyk CLI in CI** (`snyk code test` / `snyk test`) — the closest match to the
  org scan. Rejected as the *primary* gate: it needs an authenticated Snyk
  account/token in CI and (for the Code product) a paid entitlement, which the
  OSS-published catalogue should not require of contributors. The `.snyk`
  suppression file is adopted regardless, so a future Snyk-CLI step can layer on
  top. **CodeQL is adopted instead** as the OSS deep-taint stand-in (free here).
- **CodeQL** — initially weighed only as a Snyk-CLI alternative; **adopted**
  once the taint gap surfaced. It is the only OSS option that does Snyk-Code-class
  interprocedural dataflow, and it is free for this public repo (private repos
  would need GitHub Advanced Security — an adopter caveat to document, not a
  blocker here).
- **Pysa (Meta/Pyre taint analyzer)** — also real interprocedural taint.
  Rejected: heavier setup (hand-written taint models) for no gain over CodeQL on
  a repo this size.
- **Lowering Bandit's severity floor to catch the subprocess/partial-path tail** —
  Rejected: it floods the gate with ~190 low-severity false positives (constant
  `subprocess` calls) and still would not find the taint flows, which Bandit
  cannot represent at any severity.
- **Ruff's `S` ruleset (flake8-bandit) instead of Bandit** — much faster and
  would honour the `# noqa: S###` comments already present in `catalogue.py`.
  Rejected as the primary SAST: it reimplements a *subset* of Bandit's rules, and
  the maintainer asked specifically for Bandit (the reference implementation with
  full coverage). The stray `# noqa: S###` comments are realigned to Bandit's
  `# nosec` form as part of the implementing spec.
- **Bandit only** (skip pip-audit + Semgrep) — Rejected: Bandit covers neither
  vulnerable-dependency detection (the packages are stdlib-pure but the shipped
  skills pull `httpx`, `lxml`, `markdownify`, …) nor dataflow-shaped or
  non-Python findings. The maintainer asked for all three.
- **Do nothing** — Rejected: leaves the org scan as the only gate, with no local
  reproduction and no pre-merge signal.

## References

- Implementing spec: `docs/specs/sast-sca-tooling/spec.md`.
- Bandit: <https://bandit.readthedocs.io/> — `# nosec` is the only inline
  suppression it honours.
- pip-audit: <https://pypi.org/project/pip-audit/>.
- Semgrep registry rulesets: <https://semgrep.dev/r> (`p/python`,
  `p/security-audit`).
- Snyk `.snyk` policy file + Consistent Ignores for Code:
  <https://docs.snyk.io/manage-risk/policies/the-.snyk-file>.
