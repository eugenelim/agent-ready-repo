# Round-2 review pass — disposition summary

> Supersedes the per-reviewer round-1 reports under
> `notes/review-round1-{adversarial,security,quality}.md` for follow-on
> accounting. The round-1 reports remain on disk as historical record
> of what each reviewer originally flagged; this file is the record of
> what landed (and where it landed) once round-2 work was complete.

## Status

`docs/specs/skill-secrets/spec.md` stays at **Status: Shipped**. The
round-2 pass closed every Blocker, every Concern, and every Nit
either with a code/doc PR or an explicit deferral rationale named
below. Two items defer pending user direction; one item carries an
amendment-this-spec-cycle promise.

## Round-2 PRs (merge SHAs)

Bundles ordered by surface, not by reviewer (matches the round-2
follow-up prompt's PR order):

| PR | Branch | Merge SHA | Surface |
| --- | --- | --- | --- |
| **#84** | `eugenelim/ci-windows-matrix` | `78a55ea` | `windows-latest` CI matrix; Python 3.11 compat (`parse_env_file` `Path.open(newline=)`); Windows-only test guards; `with_reserved` fixture runtime-constructed (drops NTFS-poisonous on-disk file). |
| **#85** | `eugenelim/skill-secrets-ac22-macos-exit-codes` | `7202813` | AC22 macOS symbolic exit-code matrix (`EXIT_INTERACTION_NOT_ALLOWED = 25308`, `EXIT_NOT_AVAILABLE = -25291`, `EXIT_DUPLICATE_ITEM = 45`, `_classify_macos_exit_code(rc, op)` parallel to Windows `_classify_last_error`). |
| **#86** | `eugenelim/skill-secrets-creds-missing-tiers-tried` | `e1852f5` | `CredentialsMissingError` tier-by-tier why-missed observability; structured `tiers_tried` attribute; AC4 cross-tier composability test. |
| **#88** | `eugenelim/skill-secrets-doc-cleanup` | `45523cc` | Inline-fixture amendment to spec § Testing Strategy; `docs/product/release-checklist.md` for the three Windows manual-QA rows; ROADMAP closure audit + Round-2 disposition subsection. |
| **#89** | `eugenelim/skill-secrets-robustness` | `05de963` | `Credentials.__repr__` redacts values; `__getattr__` lists resolved keys; `_quote_for_dotfile` refuses `"` / `$`; `EnvParseError` ordering; `credentialed:` YAML normalisation; `resolve_schema_path` → `_relative_schema_path`; `creds rm` continues on Tier-2 hard fail; AC23 stderr-prefix categorisation. |
| **#93** | `eugenelim/skill-secrets-lint-widening` | `061a26f` | AST walker recognises `JoinedStr`, `Starred(Tuple)`, `Subscript` literal-derivable shapes; `_verify_icacls` SID-based DACL check (locale-invariant on non-English Windows). |
| **#97** | `eugenelim/skill-secrets-schema-path-remove` | _pending_ | Remove `schema_path=` kwarg from `load_credentials`; amend AC24b to call out the resolver-only contract; schema validation lives in `creds check`, not on the loader's public surface. |

## Adversarial review round 1 — disposition

(`notes/review-round1-adversarial.md`)

| # | Finding | Disposition |
| --- | --- | --- |
| 1 | AC34 orphan-fixture detection test missing | **Closed in PR #81** (round-1 adversarial fixes) — `tests/unit/test_credentials_fixtures.py` adds the orphan walker. |
| 2 | AC35 no-live-writes posture assertion missing | **Closed in PR #81** — `test_no_live_writes_posture` exists. |
| 3 | AC26 contract inversion (lint blocks, spec says reports) | **Closed in PR #81** — exit-code semantics aligned. |
| 4 | Spec Status flipped Shipped with [ ] ACs | **Closed in PR #81** — AC34/AC35 re-checked once findings #1 + #2 landed. |
| 5 | AC22 macOS exit-code matrix unimplemented | **Closed in PR #85** — `_classify_macos_exit_code` lands the symbolic matrix; tests pin every row. |
| 6 | `BASE_URL` declared required by worked example | **Closed in PR #83** (round-1 security fixes) — worked example's required_keys aligned with the schema. |
| 7 | Stray `packages/agentbundle/build/lib/` checked into HEAD | **Already gitignored** — confirmed `git ls-files` returns no entries under this path; the directory only appears as a local setuptools build artifact and is reproduced by tests that invoke `pip install --target`. No tracked-file fix needed. |
| 8 | AC26(b) AST walker misses f-string / Starred(Tuple) shapes | **Closed in PR #93** — walker extended to `JoinedStr`, `Starred(Tuple)`, `Subscript`; scope note in `add-credentialed-skill/SKILL.md` updated. |
| 9 | `resolve_schema_path` returns non-`is_file()` path | **Closed in PR #89** — renamed `_relative_schema_path`, docstring calls out the relative contract, dropped from `__all__`. |
| 10 | Tier-2 backend short-circuit silent in `_tier_for_key` | **Closed in PR #82** (round-1 quality fixes) — `Tier2HardFailError` propagates. |
| 11 | AC23 stdin-not-tty vs argv tombstone both exit 3 | **Closed in PR #89** — distinct `creds setup: argv-refusal:` / `creds setup: stdin-not-tty:` prefixes. |
| 12 | Spec fixtures named but not on disk | **Closed in PR #88** — spec § Testing Strategy now reflects the inline-heredoc choice. |
| 13 | T13c ROADMAP per-task closure conflation | **Closed in PR #88** — ROADMAP re-walked; per-task closure entries adjusted and a *Round-2 review-pass disposition* subsection added. |
| 14 | `EnvParseError` defined below first use | **Closed in PR #89** — class + `parse_env_file` moved to top of module. |
| 15 | ROADMAP "Last updated" overstates remaining work | **Closed in PR #88** — line tightened to drop the "only AC34/AC35 remain" framing. |

## Security review round 1 — disposition

(`notes/review-round1-security.md`)

| # | Finding | Disposition |
| --- | --- | --- |
| 1 | macOS doubled write — newline-bearing token corruption | **Closed in PR #83** — early refusal on `\n` / `\r` in `_keychain_macos.write_credential`. |
| 2 | AC26(b) AST walker scope note (click / typer) | **Documented in PR #83** + tightened in PR #93 — `add-credentialed-skill/SKILL.md` argparse-only scope note now enumerates literal-derivable shapes; click / typer remain PR-review territory. |
| 3 | `_walk_credentialed_skills` Windows `USERPROFILE` autouse fixture | **Deferred** — Windows test selection in PR #84 already redirects both `HOME` and `USERPROFILE` per-test where it matters; a repo-wide autouse adds maintenance cost without a current failing test. Track if a future test surfaces a real leak. |
| 4 | icacls non-English-locale silent bypass (SID-based parsing) | **Closed in PR #93** — `_verify_icacls` switched to `icacls /findsid` against well-known broad-access SIDs. |
| 5 | `parse_env_file` unbounded `read_text` | **Closed in PR #83** — `DOTFILE_MAX_BYTES = 1 << 20` size cap; `EnvParseError` raised before reading. |
| 6 | `--allow-*-fallback` argv-only posture comments | **Closed in PR #83** — SECURITY block-comments above the flag definitions forbid env-var / TOML equivalents. |
| 7 | `creds rm` continue-on-Tier-2-hard-fail | **Closed in PR #89** — per-key catch; Tier-3 cleanup still runs; non-zero exit at end. |
| 8 | `Credentials.__repr__` redacting | **Closed in PR #89** — explicit redacting `__repr__`; SECURITY comment pins the no-token-leak contract. |
| 9 | `credentialed:` YAML normalisation | **Closed in PR #89** — `_is_credentialed_true` accepts `true` / `yes` / `1` / `on` case-insensitively; both `_walk_credentialed_skills` sites route through it. |

## Quality review round 1 — disposition

(`notes/review-round1-quality.md`)

| # | Finding | Disposition |
| --- | --- | --- |
| 1 | AC34 unchecked (orphan-fixture walker) | **Closed in PR #81** — see Adversarial #1. |
| 2 | AC35 unchecked (no-live-writes assertion) | **Closed in PR #81** — see Adversarial #2. |
| 3 | `_tier_for_key` swallows Tier-2 hard fail | **Closed in PR #82** — see Adversarial #10. |
| 4 | `load_credentials(schema_path=...)` no-op kwarg | **Closed in PR #97** — path (a) chosen after long-term-vs-tactical reasoning: `load_credentials` resolves, schema describes — crossing the two through a kwarg couples concerns that should evolve independently. Kwarg removed; signature is now `(namespace, required_keys)`; AC24b amended to make the resolution-only contract explicit; schema validation belongs in `agentbundle creds check`, not in the loader's public surface. |
| 5 | AC4 cross-tier composability test missing | **Closed in PR #86** — `test_load_credentials_mixes_tiers_across_keys`. |
| 6 | `CredentialsMissingError` doesn't name tiers tried | **Closed in PR #86** — per-key tier trailer + structured `tiers_tried` attribute. |
| 7 | AC22 macOS exit-code matrix not symbolic | **Closed in PR #85** — see Adversarial #5. |
| 8 | Release-checklist artifact missing | **Closed in PR #88** — `docs/product/release-checklist.md` carries the three Windows manual-QA rows. |
| 9 | Linux `creds setup` against pre-existing `~/.agentbundle/ 0o755` silent | **Deferred** — covered by the existing `test_existing_parent_mode_is_not_rewritten_on_posix` for the noisy path; the silent-0o755 case is a no-warning assertion with no current regression vector. Track if the threshold ever changes. |
| 10 | Spec § Testing Strategy fixtures don't exist | **Closed in PR #88** — inline-heredoc choice now documented. |
| 11 | `__all__` references `EnvParseError` before class definition | **Closed in PR #89** — module reordered. |
| 12 | `_tier_for_key` duplicates loader precedence | **Deferred** — pragmatic. Loader currently has one consumer of the precedence logic plus the diagnostic helper; both are tested. A refactor returning a `(Credentials, tier_map)` tuple is right but is wider-scope than this review pass. Track for a future spec amendment. |
| 13 | macOS `SERVICE_OVERRIDE` shape parallel to Windows | **Deferred** — tests already monkeypatch `SERVICE` directly without colliding; the Windows-side `SERVICE_PREFIX_OVERRIDE` exists because tests run real subprocess against the actual Credential Manager. macOS tests stay on the developer's machine and can monkeypatch in place. Track if a macOS CI matrix ever lands. |
| 14 | `__getattr__` doesn't list resolved keys | **Closed in PR #89** — see Security #8 sibling change. |
| 15 | `_quote_for_dotfile` doesn't refuse unsafe chars | **Closed in PR #89** — `EnvParseError` on `"` or `$`. |

## Convergence note

Round-2 closed every reviewer-flagged item with either a landed fix
or a one-line deferral rationale. The four explicitly-deferred items
in the tables above (Security #3, Quality #9, #12, #13) carry no
current regression vector; each is tracked for re-evaluation if the
triggering condition (real Windows CI suite, Linux threshold change,
loader's second consumer, macOS CI matrix) ever lands.
