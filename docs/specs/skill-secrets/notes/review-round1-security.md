# Security review — skill-secrets, round 1

**Scope.** Integrated diff `git diff 5671e2e..8e73f3f` (9 task PRs); OWASP web + LLM Apps + STRIDE lenses. User pre-flagged AC6 (token-never-on-argv; doubled-write on macOS), AC9–AC11 (Win32 matrix; only static-reviewed on Darwin), AC14 (atomic-write semantics), AC15 (POSIX shared-parent + icacls), AC26(b)+AC27 (AST-walker argv-flag detection).

No Blockers raised — see Concerns and Nits. Complements (does not replace) SAST/SCA; no scanner has run on this diff.

## Concerns

**1. macOS write sends token twice on child stdin, widening in-process exposure window.** `packages/agentbundle/agentbundle/creds/_keychain_macos.py:92-94`. `add-generic-password -w` prompt asks twice; implementer packs `token + "\n" + token + "\n"` into a single `communicate(input=...)`. Functionally correct but: (a) any token containing `\n` is silently truncated and the confirmation mismatches — `security` resolves by storing empty password and returning non-zero (handled), but a token ending in `\n` round-trips lossy (`rstrip("\n")` on read at line 67); (b) more bytes of plaintext sit in parent's Python heap. Fix: keep the doubled write but add an early guard refusing tokens containing `\n` or `\r` with a clear stderr message — Tier-3 quoting (`_quote_for_dotfile`) and macOS prompt confirmation both break on embedded newlines.

**2. AC26(b) AST walker misses real-world non-argparse credentialed CLIs (click / typer).** `tools/lint-credentialed-skills.sh:151-165`. Walker hard-codes `func.attr == "add_argument"`, so any credentialed-CLI primitive written with `click.option("--token", ...)` or `typer.Option(..., "--token")` passes the lint clean while accepting the banned flag at runtime. AC26(b) does scope to argparse, but the architectural rule (no token on argv) is library-agnostic; the lint under-enforces it. Fix: either extend the walker to recognise `click.option` / `click.argument` / `typer.Option` shapes, or add a documented limitation note in `add-credentialed-skill/SKILL.md` plus a second lint rule banning `import click` / `import typer` from `primitive-class = "credentialed-cli"` skills.

**3. `_walk_credentialed_skills` on Windows reads from `pathlib.Path.home()` but tests likely monkeypatch only `HOME`.** `packages/agentbundle/agentbundle/commands/creds.py:289`. `Path.home()` on Windows honours `USERPROFILE` before `HOMEDRIVE+HOMEPATH`; a test setting `HOME` but not `USERPROFILE` reads the developer's real `~/.agent-ready/state.toml` (AC35 violation by reads, not just writes). Fix: add a `tests/conftest.py` autouse fixture that sets *both* `HOME` and `USERPROFILE` to `tmp_path` for tests touching `loader._dotfile_path` or `_walk_credentialed_skills`.

**4. `_verify_icacls` parses English-only `icacls` output and can be bypassed by non-English Windows locales.** `packages/agentbundle/agentbundle/creds/loader.py:237-246`. Substring scan looks for `"BUILTIN\\Users"`, `"Everyone"`, `"Authenticated Users"` — these are localised on non-English Windows (`Tout le monde`, `Jeder`, `Все`). On a French Windows install the parser sees no match and silently accepts a DACL that would have been refused in English. Fix: switch from name-substring matching to **SID-based** matching by invoking `icacls <path> /findsid S-1-1-0` (Everyone) and `S-1-5-11` (Authenticated Users) — SIDs are locale-invariant. Mark as Concern because the spec's threat model assumes English Windows; either widen the model or fix the parser.

**5. `_dotfile_read` performs an unbounded `read_text` against an attacker-influenced path.** `packages/agentbundle/agentbundle/creds/loader.py:565`. `parse_env_file` calls `path.read_text(encoding="utf-8", newline="")` with no size cap. If an attacker (or buggy caller) plants a multi-GB `~/.agent-ready/credentials.env`, the loader allocates the entire file into memory at every credential resolution. Fix: add a 1 MiB ceiling on `path.stat().st_size` before reading; raise `EnvParseError` with a clear message if exceeded.

**6. `--allow-insecure-fallback` and `--allow-permissive-acl` posture-lowering flags are argv-only; document the contract so future PRs don't widen it.** `packages/agentbundle/agentbundle/commands/creds.py:144-163`. Currently the elevation-of-privilege reverse is loud (must appear in user's argv). Keep it that way. Fix: add `# SECURITY: do not add env-var or config-file alternatives — posture lowering must be visible in argv` near the flag definitions so future agents don't widen the contract.

**7. `creds rm` reads each Tier 2 entry before deleting it; `Tier2HardFailError` during the read aborts Tier-3 cleanup.** `packages/agentbundle/agentbundle/commands/creds.py:654-661`. The read-before-delete pattern is correct, but a `Tier2HardFailError` during the read aborts the entire `rm` — including the Tier-3 cleanup that would have succeeded. An operator invoking `creds rm` to react to a Tier-2 compromise cannot clean up Tier 3 without first fixing Tier 2. Fix: catch `Tier2HardFailError` per-key, log to stderr, continue with Tier 3 cleanup; non-zero exit at end so the operator knows something hard-failed.

## Nits

**8. `Credentials` has no explicit redacting `__repr__`; relies on absence of override.** `packages/agentbundle/agentbundle/creds/loader.py:86`. Docstring claims "No `__repr__` override — the default `object` repr is intentional so a misplaced `print(creds)` never echoes the token bytes." Correct *today*, but future maintainers commonly add `__repr__` for debugging. Fix: add an explicit `__repr__` that lists key names but not values, with a comment pinning the contract.

**9. `_parse_frontmatter` strips matched outer quotes but `credentialed: "true"` matches the equality check; guard against `credentialed: True` / `yes`.** `packages/agentbundle/agentbundle/commands/creds.py:286, 303`. Check `fields.get("credentialed") == "true"` only matches literal string `true`. A skill author who writes `credentialed: True` (Python-style) or `credentialed: yes` (YAML 1.1) silently *not* picked up by `setup` walker. Confusing rather than insecure. Fix: lowercase value before comparison and accept `{"true", "yes", "1"}` — or raise from `tools/lint-agent-artifacts.sh` if the value isn't canonical.

## Not checked / out of scope

- **No SAST / SCA / secret-scan was run.** Bandit would flag the `subprocess` calls; `pip-audit` and Dependabot would surface dependency posture. Recommend gating both in CI if not already.
- **No live exercise of the Windows ctypes path.** AC9–AC11 are static-review only; the spec acknowledges the missing `windows-latest` matrix. **Out of scope per the prompt — requires a precursor CI-matrix PR, not a code change to T5.** Track separately.
- **No fuzzing of `parse_env_file`.** Construction tests cover named shapes, not boundary mutation space.
- **No TLS / cert-pinning review** — no network code touched in this diff.
- **No review of build/lib checkpoint artifacts** — orthogonal to this spec.

---

**Convergence note (round 1):** seven Concerns; zero Blockers. The doubled-write decision (Concern #1) was the right call given `security`'s prompt contract, with a small reliability gap (embedded-newline tokens). icacls locale and dotfile size cap are the highest-leverage Concerns.
