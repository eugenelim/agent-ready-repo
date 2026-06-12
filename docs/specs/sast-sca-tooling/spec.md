# Spec: SAST/SCA tooling (Bandit + pip-audit + Semgrep)

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0017
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The repo has no static-analysis tooling, and an internal organisational Snyk
scan is flagging some skill/tool scripts with no output the maintainer can see.
This feature gives the repo its own SAST/SCA gate — Bandit, pip-audit, and
Semgrep — runnable locally as `make sast` and enforced in a dedicated CI
workflow, so the class of issue the org scan catches fails *our* build first.
The genuine findings the gate surfaces in shipped code are fixed in the same
change; tool-specific false positives are suppressed at the narrowest scope that
keeps the gate honest. Because Bandit has no dataflow engine, the gate also
covers **taint** (untrusted input → sink) via custom Semgrep `mode: taint` rules
and a CodeQL code-scanning workflow — the lens that caught the org scan's
`session-start` env-var → `pathlib.Path` finding, which is fixed at the source so
every adopter inherits it. Success: a contributor runs `make sast` on a clean
tree and it passes; introducing a real security regression (including a new
unsanitised env→path flow) makes it fail.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep the three scanners **dev/CI-only**. They are invoked from the Makefile
  and the CI workflow; they are installed in CI, not pinned into any shipped
  package.
- Prefer a **real code fix** over any suppression for a genuine finding — a real
  fix satisfies Bandit *and* the internal Snyk scan.
- When a finding is a tool-specific false positive, suppress with
  `# nosec <ID> — <reason>` carrying a one-line justification on the same line.
- Validate untrusted input at the boundary it crosses — sanitize env-var path
  overrides and assert URL schemes in the shipped source, so the fix ships to
  every adopter rather than each suppressing the finding.
- Edit pack **source** under `packs/<pack>/.apm/...`, then run `make build-self`
  to reproject; never edit a projected `.claude/...` copy directly.
- Keep `bandit.yaml`'s exclusions and skips minimal and justified by a comment.

### Ask first

- Adding a **runtime** dependency to any shipped package or skill to fix a
  finding (e.g. `defusedxml`) — surface the stdlib-vs-dependency tradeoff before
  taking it. (The XML finding is fixed without a new runtime dependency; see the
  plan.)
- Making the Semgrep job blocking-vs-advisory differently from the plan, or
  changing which registry rulesets it runs.
- Widening Bandit's severity/confidence floor below `medium`.

### Never do

- Never add Bandit, pip-audit, or Semgrep to a shipped package's
  `dependencies`, optional-extras, or a skill `requirements.txt`. They are not
  runtime code.
- Never silence a genuine finding with `# nosec` to make the gate green.
- Never wire the scanners into the projected `pre-pr.py` hook body (it projects
  to adopters and would misfire); SAST is a repo-owned CI workflow + `make`
  target, mirroring `build-check`.
- Never author `.snyk` Code-ignore entries with invented issue IDs; the file
  ships as a documented scaffold until real IDs are available.
- Never add scanner config or CI surface beyond the sanctioned set —
  `bandit.yaml`, `.snyk`, `tools/requirements-sast.txt`, `tools/semgrep/`
  (custom taint rules), and `.github/workflows/codeql.yml`, plus wiring edits to
  `Makefile` (the `sast` target + the `build-check` chain) and
  `.github/workflows/build-check.yml` (install the SAST tools) — without amending
  this spec. The finding-driven source fixes (`session-start.py` sanitizer,
  `sso-broker.py` scheme guard, the SHA-1 / arXiv / `# nosec` dispositions) are
  the only shipped-code edits.
- Never add the SAST scanners to `tools/hooks/pre-pr.py` (the shipped adopter
  hook — it runs on the Windows CI path at `build-check-windows.yml`, where
  Semgrep is unsupported, and it projects to adopters) **or** to
  `tools/pre-pr-catalogue.py` (the Linux `make build-check` aggregator — adding
  them there would double-run, since `make build-check` already chains
  `make sast`). The scanners live in `make sast` alone. The Windows job invokes
  neither `make` nor `make sast`, so the dogfooded gate never reaches it.

## Testing Strategy

- **Bandit / pip-audit / Semgrep gates: goal-based check.** Each is verified by
  running the tool and asserting a clean (exit 0) result on the current tree —
  the `make sast` one-liner is the contract. No test file asserts what the
  scanner already proves.
- **Code fixes (SHA-1 `usedforsecurity=False`, XML hardening): goal-based
  check**, verified by Bandit no longer reporting the finding at medium+
  severity, plus the package/skill's existing tests staying green (the digests
  and the arXiv parse remain functionally identical).
- **CI wiring: goal-based check** — `make build-check` chains `make sast`, and
  `build-check.yml` installs the SAST tools before invoking it; verified by
  running `make build-check` and observing the scanners execute.
- **Drift: goal-based check** — `make build-self` leaves the tree clean after
  the `loop-cohort.py` edit is reprojected (`git status` shows no unstaged
  projected drift).

## Acceptance Criteria

- [x] `make sast` exists and runs Bandit, pip-audit, and Semgrep in sequence;
  on a clean working tree it exits 0.
- [x] **The SAST gate is dogfooded into this repo's own development per the
  repo's gate convention:** `make build-check` (the single native gate, run
  locally per CONTRIBUTING and in the `build-check.yml` CI on every PR to `main`)
  chains `make sast`, so a new medium+ finding fails this repo's own gate — it is
  not a separate, skippable workflow. No standalone `sast.yml` is added.
- [x] A repo-root `bandit.yaml` configures Bandit to fail on **medium-or-higher
  severity at medium-or-higher confidence**, excludes test trees, and skips
  `B101`; every exclusion/skip carries a justifying comment.
- [x] `bandit -r tools packs packages -c bandit.yaml --severity-level medium
  --confidence-level medium` reports **zero** issues on the post-change tree.
- [x] The two weak-SHA-1 findings (`packages/agentbundle/agentbundle/config.py`,
  `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`) are fixed with
  `hashlib.sha1(..., usedforsecurity=False)`; the produced digests are
  byte-identical to before (existing tests stay green).
- [x] The `arxiv-retriever.py` endpoint is upgraded from `http://` to
  `https://` (a real fix for the constant-base `urlopen` / B310), and the script
  still parses a real arXiv Atom response.
- [x] The `ET.fromstring` B314 finding is dispositioned as a **stdlib pattern
  false positive** with a precise `# nosec B314 — <reason>` justification
  (stdlib ElementTree resolves no external entities or DTDs on 3.11+; arXiv is a
  constant first-party endpoint), keeping the script stdlib-only per its
  docstring. No fragile content-scanning guard and no runtime dependency.
- [x] The `yaml.load`-against-`SafeLoader`-subclass false positives
  (`tools/lint-agent-artifacts.py`, `tools/lint-skill-spec.py`) and the
  constant/operator-configured-base `urlopen` false positives carry
  `# nosec <ID> — <reason>` annotations. The `catalogue.py` tarfile extraction
  already carries its **real fix** (`extractall(filter="data")`); its stray
  `# noqa: S###` comments are dropped, and a `# nosec B202` is added *only if*
  Bandit still flags it despite the kwarg, with a reason naming the real fix in
  place — it is not re-filed as a pattern FP.
- [x] pip-audit audits `tools/requirements.txt`, `tools/requirements-sast.txt`,
  every shipped per-skill `requirements.txt`, and the `credbroker[crypto]` extra
  (`cryptography`, `argon2-cffi`) — the only third-party code either shipped
  package can pull, since both declare `dependencies = []`. It reports **zero**
  known-vulnerable versions; any accepted exception has a `.snyk` entry carrying
  a `reason` and an `expires`.
- [x] Semgrep runs against `p/python` + `p/security-audit` and reports no
  findings on the post-change tree. Four rules are excluded as duplicates of
  classes Bandit owns (sha1 → `usedforsecurity=False` + B324; urllib → B310;
  xml → B314; permissive-chmod → B103), with no coverage loss; the exclusion
  list and rationale live in the `make sast` recipe and ADR-0017 (this is the
  spec amendment the structural Boundary requires).
- [x] The Windows gate path is unaffected: `build-check-windows.yml` (which runs
  `python -m agentbundle.build check` + `python tools/hooks/pre-pr.py`, **not**
  `make build-check`) stays green, and Semgrep is never invoked on Windows.
- [x] A committed `.snyk` policy file documents the Snyk-native suppression
  vehicle (SCA ignore-by-ID; Code via Consistent Ignores) with a worked example
  and no invented IDs.
- [x] `make build-self` reprojects the `loop-cohort.py` source edit and leaves
  the tree drift-clean; `make build-check` stays green.
- [x] A custom Semgrep `mode: taint` rule (`tools/semgrep/env-path-taint.yml`,
  env-var → `pathlib.Path`, CWE-22/73) is loaded by `make sast` via
  `--config tools/semgrep/`; it reports zero findings on the post-change tree
  and still fires on a direct `Path(os.environ.get(...))` (verified by canary).
- [x] The `session-start` hook's three env→`Path` flows (`KNOWLEDGE_FILE`,
  `ADAPT_REPO_MARKER`, `ADAPT_USER_MARKER`) are routed through a **confining**
  sanitizer (`_safe_override_path`) in the **shipped** pack source: it
  `expanduser().resolve()`-normalizes then requires the result to stay within an
  allowed base (repo root for the first two, `~` for the user marker) — closing
  not just `..` traversal (CWE-22) but absolute-path and symlink escape
  (CWE-73). An out-of-bounds override is refused (warns + falls back to the
  default); a regression test asserts both an absolute out-of-bounds path and a
  `..` traversal are refused and their contents never emitted; existing
  session-start tests (Python + both shell) stay green.
- [x] `sso-broker.py`'s `test` verb rejects any resolved URL whose scheme is not
  `http`/`https` (exit 3) before `urlopen`, with a regression test; `http`/`https`
  endpoints still work. (Boundary input-validation, returns the existing error
  code — not a contract change.)
- [x] A CodeQL code-scanning workflow (`.github/workflows/codeql.yml`, Python,
  `security-extended`) runs on PRs + push to `main`; it provides the
  interprocedural-taint lens (`py/path-injection`) Bandit and OSS Semgrep cannot.
- [x] The four dev tools (Bandit, pip-audit, Semgrep, CodeQL) are recorded in
  **ADR-0017** (satisfying the "or an ADR" branch of the dependency-recording
  rule — they are dev/CI-only, not a package runtime dependency), and a
  `docs/product/changelog.md` `[Unreleased]` entry names them.

## Assumptions

- Technical: Both shipped packages declare `dependencies = []`; the SAST tools
  must stay dev/CI-only (source: `packages/*/pyproject.toml`, ADR-0017).
- Technical: The two `yaml.load` *call sites* (`lint-agent-artifacts.py:189`,
  `lint-skill-spec.py:360`) pass a `yaml.SafeLoader` **subclass** (class defs at
  `lint-agent-artifacts.py:91`, `lint-skill-spec.py:141`), so B506 is a false
  positive (source: probe 2026-06-12).
- Technical: stdlib `xml.etree.ElementTree` resolves no external entities or
  DTDs on Python 3.11+, so the `arxiv-retriever.py` B314 is a pattern false
  positive, not a genuine XXE/entity-expansion exposure; the real fix on that
  line is the `http://`→`https://` endpoint upgrade for B310 (source: probe
  2026-06-12, Python docs).
- Technical: The SHA-1 sites are non-security digests (cache-key / review
  fingerprint), so `usedforsecurity=False` is semantically correct and digest-
  preserving (source: probe — `config.py:482`, `loop-cohort.py:748`).
- Technical: `loop-cohort.py` is a projected skill script; the source of record
  is `packs/core/.apm/skills/work-loop/scripts/` (source: memory
  `feedback_self_host_projection`).
- Process: SAST is chained into `make build-check` (the repo's single native
  gate) so it is dogfooded into this repo's own development, accepting a slower
  gate; no standalone `sast.yml` (source: user direction 2026-06-12, ADR-0017).
- Product: Maintainer asked for all three tools and for Snyk-native suppression
  where relevant (source: user confirmation 2026-06-12).
