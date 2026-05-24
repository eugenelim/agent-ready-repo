"""T12: worked example credentialed-skill (skill-secrets spec § AC29).

Closes:

- AC29 *Skill structure* — SKILL.md + scripts/cli.py + references/
  creds-schema.toml ship at the canonical landing.
- AC29 *SKILL.md frontmatter* — ``credentialed: true``,
  ``primitive-class: credentialed-cli`` pass
  ``tools/lint-agent-artifacts.py``.
- AC29 *Verbatim "Don't" block* — the body contains the three RFC-0006
  § 4 substrings the credentialed-CLI variant pins; the integration
  test diffs the skill's "Don't" block against the
  ``add-credentialed-skill`` template's ``credentialed-cli`` variant
  so a drift in either ships as a test failure.
- AC29 *cli.py imports the loader* — ``scripts/cli.py`` references
  ``agent_ready.credentials.load_credentials``.
- AC29 *cli.py refuses argv-ban flags* — invoking with ``--token=x``
  exits non-zero with the argparse-default ``unrecognized arguments``
  shape (the lint enforces the *absence* of the flag in the parser
  declaration; the runtime refusal happens at argparse-parse time).
- AC29 *schema declares one required key + one sibling* — parse via
  ``_parse_schema`` and assert the shape.
- AC29 *conventions-check clean* — ``tools/lint-credentialed-skills.sh``
  reports zero findings against this skill.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "example-credentialed-skill"
TEMPLATE_PATH = REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "add-credentialed-skill" / "assets" / "credentialed-skill-SKILL.md"


# ── AC29: structure ────────────────────────────────────────────────────


def test_skill_structure_complete():
    """AC29: the worked example ships SKILL.md, scripts/cli.py, and
    references/creds-schema.toml at the canonical landing."""
    assert (SKILL_DIR / "SKILL.md").is_file()
    assert (SKILL_DIR / "scripts" / "cli.py").is_file()
    assert (SKILL_DIR / "references" / "creds-schema.toml").is_file()


# ── AC29: SKILL.md frontmatter ────────────────────────────────────────


def _read_frontmatter(path: Path) -> dict[str, str]:
    """Single-line scalar YAML-subset parser matching the lint shape."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert lines and lines[0].strip() == "---", "missing opening ---"
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
            v = v[1:-1]
        fields[k.strip()] = v
    return fields


def test_frontmatter_declares_credentialed_cli_primitive():
    """AC29: frontmatter carries ``credentialed: true`` and
    ``primitive-class: credentialed-cli``.
    """
    fields = _read_frontmatter(SKILL_DIR / "SKILL.md")
    assert fields.get("credentialed") == "true"
    assert fields.get("primitive-class") == "credentialed-cli"
    assert fields.get("name") == "example-credentialed-skill"


def test_lint_agent_artifacts_passes():
    """AC29: ``tools/lint-agent-artifacts.py`` accepts the skill's
    frontmatter (the schema additions from T9 cover this)."""
    res = subprocess.run(
        [sys.executable, "tools/lint-agent-artifacts.py"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert res.returncode == 0, (
        f"lint-agent-artifacts.py failed:\nstdout={res.stdout}\n"
        f"stderr={res.stderr}"
    )


# ── AC29: verbatim "Don't" block + template-drift check ───────────────


REQUIRED_DONT_PHRASES = (
    "### Security rules (non-negotiable)",
    "**Never** read that file, print it, or echo the token",
    "**Never** put the token on the command line",
    "do not run it for them",
)


def _split_frontmatter_body(text: str) -> str:
    """Return the post-frontmatter body, mirroring the lint's split.

    ``lint-credentialed-skills.sh::parse_frontmatter`` returns
    ``(fields, body)`` where ``body`` is everything after the second
    ``---`` line; the section walk runs against ``body``. A description
    that quotes the heading string still triggers a naive ``in text``
    match, so the test must split the same way the lint does to stay
    faithful to what the production check enforces.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "".join(lines[i + 1:])
    return text


def test_dont_block_phrases_appear_inside_security_section():
    """AC29: the three RFC-0006 § 4 anchor phrases must appear inside
    the ``### Security rules (non-negotiable)`` section of the SKILL.md
    *body* (post-frontmatter) — not anywhere in the file. A phrase
    living only in the frontmatter description or in another section
    would satisfy a naive ``in text`` check but does not satisfy the
    lint, which walks the body's section slice."""
    import re as _re

    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    body = _split_frontmatter_body(text)
    heading = "### Security rules (non-negotiable)"
    start = body.find(heading)
    assert start != -1, f"missing heading in body: {heading}"
    terminator = _re.search(r"\n#{1,6}\s", body[start + len(heading):])
    end = (start + len(heading) + terminator.start()) if terminator else len(body)
    section = body[start:end]
    for phrase in REQUIRED_DONT_PHRASES[1:]:  # heading itself is the slice start
        assert phrase in section, (
            f"phrase {phrase!r} absent from `### Security rules` section "
            f"(found elsewhere in the file is not enough)"
        )


def test_dont_block_matches_credentialed_cli_template():
    """AC29 drift trap: the skill's "Don't" block (every line from
    ``### Security rules (non-negotiable)`` through the section's
    terminator) must appear verbatim in the worked example.

    The template at ``add-credentialed-skill/assets/credentialed-skill-SKILL.md``
    is the canonical source for the block; a future edit to either
    side without updating the other will trip this test before merge.

    The slice is anchored on the next heading line (``\\n##`` or
    deeper) rather than a paragraph-break heuristic so a template
    edit that inserts a blank line between bullets, or adds a
    sub-paragraph under a bullet, does not silently truncate the
    compared text. The lint walks the same heading-to-heading slice
    via ``HEADING_TERMINATE_RE``.
    """
    import re as _re

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    # The ``credentialed-cli`` variant ends at the next ``---`` separator
    # (the file uses ``---`` between variants).
    variant_start = template.find("### Variant: credentialed-cli")
    assert variant_start != -1, "template missing credentialed-cli variant"
    variant_end = template.find("\n---", variant_start)
    assert variant_end != -1, "template missing closing ---"
    variant = template[variant_start:variant_end]

    # Pull the fenced-code body — everything between the ```markdown
    # fence and its closing ```.
    fence_open = variant.find("```markdown")
    assert fence_open != -1, "template missing ```markdown fence"
    body_start = variant.index("\n", fence_open) + 1
    fence_close = variant.find("\n```", body_start)
    assert fence_close != -1, "template missing closing ``` fence"
    block_body = variant[body_start:fence_close]

    # Anchor on the heading + next heading line (the same shape
    # ``HEADING_TERMINATE_RE`` in ``lint-credentialed-skills.sh`` uses).
    heading = "### Security rules (non-negotiable)"
    heading_in_block = block_body.find(heading)
    assert heading_in_block != -1, (
        "template variant missing the Security rules heading"
    )
    rest = block_body[heading_in_block:]
    terminator = _re.search(r"\n#{1,6}\s", rest[len(heading):])
    template_block = (
        rest[: len(heading) + terminator.start()].rstrip()
        if terminator
        else rest.rstrip()
    )

    assert template_block in skill, (
        "Worked example's `### Security rules (non-negotiable)` block "
        "drifted from the credentialed-cli template — re-copy it "
        "verbatim from "
        "packs/core/.apm/skills/add-credentialed-skill/assets/"
        "credentialed-skill-SKILL.md or update the template in lockstep.\n"
        f"--- template ---\n{template_block!r}\n"
    )


# ── AC29: cli.py imports load_credentials + refuses argv-ban flags ────


def test_cli_imports_load_credentials():
    """AC29: ``scripts/cli.py`` imports the public-shim loader."""
    text = (SKILL_DIR / "scripts" / "cli.py").read_text(encoding="utf-8")
    assert "from agent_ready.credentials import" in text
    assert "load_credentials" in text


def _load_cli_module():
    """Import the seed-side ``cli.py`` as a module under a unique
    name so importlib doesn't re-use a cached entry across tests."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "example_credentialed_skill_cli",
        SKILL_DIR / "scripts" / "cli.py",
    )
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    return cli


def test_cli_catches_tier2_hard_fail_with_friendly_stderr(
    tmp_path, monkeypatch, capsys
):
    """Maintainability contract for the worked example: a
    ``Tier2HardFailError`` from ``load_credentials`` is caught and
    surfaces a one-line stderr instead of letting the traceback
    escape. Adopters copy this skill; the catch arm is the load-bearing
    pattern they inherit.
    """
    cli = _load_cli_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    from agent_ready.credentials import Tier2HardFailError

    def boom(*a, **kw):
        raise Tier2HardFailError("keychain locked")

    monkeypatch.setattr(cli, "load_credentials", boom)
    rc = cli.main(["call"])
    assert rc == 3
    out = capsys.readouterr()
    assert "keychain unavailable" in out.err
    assert "keychain locked" in out.err  # the underlying exception text
    # No traceback escapes — stderr should be the one-line message,
    # not a Python ``Traceback (most recent call last)`` frame.
    assert "Traceback" not in out.err


def test_cli_refuses_invalid_base_url_with_exit_three(
    tmp_path, monkeypatch, capsys
):
    """Maintainability contract: ``BASE_URL`` resolution that returns
    a non-URL value exits 3 instead of issuing a call to garbage.
    Adopters who copy the pattern inherit the validation seam."""
    cli = _load_cli_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("EXAMPLE_API_TOKEN", "x")
    monkeypatch.setenv("EXAMPLE_BASE_URL", "not-a-url")
    rc = cli.main(["call"])
    assert rc == 3
    out = capsys.readouterr()
    assert "not a valid URL" in out.err


def test_cli_call_output_does_not_leak_token_bytes_or_length(
    tmp_path, monkeypatch, capsys
):
    """The token bytes never reach stdout, and neither does
    ``len(token)`` — token-length is a small side-channel adopters
    should not normalise leaking."""
    cli = _load_cli_module()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    secret = "super-secret-token-xyz-deadbeef"
    monkeypatch.setenv("EXAMPLE_API_TOKEN", secret)
    monkeypatch.setenv("EXAMPLE_BASE_URL", "https://example.fixture.test")
    rc = cli.main(["call"])
    assert rc == 0
    out = capsys.readouterr()
    assert secret not in out.out
    assert str(len(secret)) not in out.out  # no len= field
    assert "len=" not in out.out


def test_cli_refuses_argv_borne_token_flag_in_process(tmp_path, monkeypatch, capsys):
    """AC29: invoking the primitive's ``main(["call", "--token=x"])``
    exits non-zero via argparse's ``unrecognized arguments`` path.

    Runs in-process against ``cli.main(...)`` rather than via subprocess
    so the failure mode is observable without ``PYTHONPATH`` munging
    or env-redirection plumbing. Valid Tier-1 env vars are seeded for
    both schema keys so that *without* the offending flag the call
    would succeed (verified by a control invocation below); the only
    remaining failure mode for ``--token=x`` is argparse's flag
    refusal, which is what AC29 contracts. Without this control, a
    missing-credentials exit (rc=2) would also satisfy the
    non-zero-exit assertion and the test would pass for the wrong
    reason.
    """
    # Load the cli module from the seed path (it is not on the default
    # PYTHONPATH because the skill is not a Python package).
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "example_credentialed_skill_cli",
        SKILL_DIR / "scripts" / "cli.py",
    )
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("EXAMPLE_API_TOKEN", "fixture-token")
    monkeypatch.setenv("EXAMPLE_BASE_URL", "https://example.fixture.test")

    # Control: without the offending flag, ``check`` succeeds.
    rc = cli.main(["check"])
    assert rc == 0, "control invocation should succeed (rc=0)"
    capsys.readouterr()  # drop control output

    # Argparse raises SystemExit on unknown flags; assert it surfaces.
    with pytest.raises(SystemExit) as exc:
        cli.main(["call", "--token=x"])
    assert exc.value.code != 0
    out = capsys.readouterr()
    assert "unrecognized arguments" in out.err or "--token" in out.err


# ── AC29: schema shape ────────────────────────────────────────────────


def test_schema_declares_one_required_and_one_optional_key():
    """AC29: schema declares ``API_TOKEN`` (secret) and ``BASE_URL``
    (non-secret) under the ``example`` namespace."""
    from agentbundle.creds.loader import _parse_schema, CredsSchema, KeyDef

    schema = _parse_schema(SKILL_DIR / "references" / "creds-schema.toml")
    assert isinstance(schema, CredsSchema)
    assert schema.namespace == "example"
    key_names = [k.name for k in schema.keys]
    assert key_names == ["API_TOKEN", "BASE_URL"]
    secret_map = {k.name: k.secret for k in schema.keys}
    assert secret_map["API_TOKEN"] is True
    assert secret_map["BASE_URL"] is False


# ── AC29: conventions-check clean ─────────────────────────────────────


def test_conventions_check_reports_zero_findings(tmp_path):
    """AC29: ``tools/lint-credentialed-skills.sh`` reports zero findings
    against the worked example. Runs the lint with ``LINT_ROOT`` scoped
    to a temp tree containing only this skill, so a finding from any
    other in-tree credentialed skill cannot mask a regression here.
    """
    # Copy the skill into a stand-alone tree so LINT_ROOT only sees it.
    import shutil
    target = tmp_path / "packs" / "core" / ".apm" / "skills" / "example-credentialed-skill"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SKILL_DIR, target)

    env = os.environ.copy()
    env["LINT_ROOT"] = str(tmp_path)
    res = subprocess.run(
        ["bash", str(REPO_ROOT / "tools" / "lint-credentialed-skills.sh")],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert res.returncode == 0, (
        f"lint-credentialed-skills.sh reported findings:\n"
        f"stdout={res.stdout}\nstderr={res.stderr}"
    )


def test_skill_passes_in_situ_credentialed_lint():
    """AC29 belt-and-braces: the skill must be clean under the real
    in-tree LINT_ROOT too, not only under a stand-alone temp tree.
    Confirms there is no other in-tree skill that the lint regression
    masks (and vice-versa).

    Parses each ``✖ <relpath>:`` finding line (the format emitted by
    ``lint-credentialed-skills.sh``'s ``report()``) and asserts no
    path begins with either the seed or the projected location for
    this skill — substring matching on stderr alone would fire
    spuriously if an unrelated finding's text happened to mention
    the skill name.
    """
    res = subprocess.run(
        ["bash", str(REPO_ROOT / "tools" / "lint-credentialed-skills.sh")],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    seed_prefix = "packs/core/.apm/skills/example-credentialed-skill/"
    projected_prefix = ".claude/skills/example-credentialed-skill/"
    for line in res.stderr.splitlines():
        if not line.startswith("✖ "):
            continue
        # ``✖ <relpath>: <message>``
        rest = line[2:]
        relpath = rest.split(":", 1)[0]
        assert not relpath.startswith(seed_prefix), (
            f"worked example seed flagged by in-tree lint: {line!r}"
        )
        assert not relpath.startswith(projected_prefix), (
            f"worked example projection flagged by in-tree lint: {line!r}"
        )
