"""Selector behaviour for phase-scoped policy delivery.

Repository-level on purpose. The selector resolves `seed:` locators against the
repository root — `seed:AGENTS.md` is a root file — so this coverage cannot live
under `packs/core/tests/`, which `pack-tests-stay-in-pack` confines to the pack.
The registry's own content is asserted pack-locally in
`packs/core/tests/skills/work-loop/test_policy_family_registry.py`.

The three `# STUB:` blocks below are the approved stubs from
`docs/specs/phase-policy-registry-and-selector/plan.md`, verbatim except for
their two root constants, which the plan wrote for a pack-test location. The
assertions — the contract the stubs pin — are unchanged.
"""

# STUB: AC6 — the emitted id sequence equals the registry's declared list
# Stored and validated in PLAN's T2 Tests: subsection. Comparing against the
# registry, not against a second run, is the whole point: a deterministically
# reversed selector satisfies "stable across runs".
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2] / "packs/core"
SELECTOR = PACK_ROOT / ".apm/skills/work-loop/scripts/select-policy-families.py"
REGISTRY = PACK_ROOT / ".apm/skills/work-loop/references/policy-families.md"
REPO_ROOT = Path(__file__).resolve().parents[2]


def test_emitted_order_equals_declared_order():
    key = "SPEC-PLAN-DRAFTING"
    proc = subprocess.run(
        [sys.executable, str(SELECTOR), "--registry", str(REGISTRY),
         "--root", str(REPO_ROOT), key],
        capture_output=True, text=True, check=False,
    )

    assert proc.returncode == 0, proc.stderr
    emitted = [f["id"] for f in json.loads(proc.stdout)["families"]]
    declared = _registry_block()["selection"][key]
    assert emitted == declared


# STUB: AC7 — each emitted entry equals its registry record plus a real digest
# Stored and validated in PLAN's T3 Tests: subsection. Comparing tier and module
# against the registry is what a presence-only assertion misses: a selector
# reporting every family as `advisory` passes the weaker form.


def test_emitted_entry_equals_registry_record_with_digest():
    record = {f["id"]: f for f in _registry_block()["families"]}
    entry = _select("CODE-IMPLEMENTATION")["families"][0]
    source = record[entry["id"]]

    assert entry["tier"] == source["tier"]
    assert entry["module"] == source["module"]
    resolved = _resolve(source["module"], REPO_ROOT)
    assert entry["module_digest"] == hashlib.sha256(resolved.read_bytes()).hexdigest()


# STUB: AC8 — an unknown selection key is refused on stderr with a non-zero exit
# Stored and validated in PLAN's T4 Tests: subsection. The prefix is asserted at
# the start of the stream, not as a bare substring: the script name appears in
# argv echoes, so a substring check can pass while the message is missing.
def test_unknown_selection_key_is_refused():
    proc = subprocess.run(
        [sys.executable, str(SELECTOR), "--registry", str(REGISTRY),
         "--root", str(REPO_ROOT), "NO-SUCH-PHASE"],
        capture_output=True, text=True, check=False,
    )

    assert proc.returncode != 0
    assert proc.stderr.startswith("select-policy-families:")


# --- EXECUTE fill: construction helpers the stubs reference -------------------
#
# --- EXECUTE fill: construction helpers the stubs reference -------------------
#
# `_resolve` deliberately re-derives the locator search order from the spec
# rather than importing the selector's own resolver. Importing it would make
# AC7's digest assertion compare the selector against a copy of itself, and the
# mutation that reverses the selector's `seed:` order would move both sides and
# stay green. An independent second statement is the oracle.

_SKILL_ROOTS = (".claude/skills", ".agents/skills", "packs/core/.apm/skills")
_SEED_ROOTS = ("", "packs/core/seeds")

REGISTRY_ARGS = ["--registry", str(REGISTRY), "--root", str(REPO_ROOT)]


def _selector_module():
    """Import the selector once for assertions whose subject is not the CLI.

    Spawning an interpreter per selection key spends the suite's time waiting
    rather than asserting, and gets worse on a loaded machine. The CLI envelope
    keeps its subprocess, because there the integration *is* the subject.

    Swap in throwaway streams across the load. The selector reconfigures both
    streams to UTF-8 at module scope, as every `.apm/` script must; run against
    pytest's captured streams that replaces their `errors="replace"` with
    `strict` for the rest of the session, so a surrogate in any later test's
    captured output would raise inside capture. Same mechanism the sibling suite
    uses for `loop-engine.py`, documented at `_loop_guards.py:613-621`.
    """
    import importlib.util
    import io

    spec = importlib.util.spec_from_file_location("_selector", SELECTOR)
    module = importlib.util.module_from_spec(spec)
    saved_out, saved_err = sys.stdout, sys.stderr
    sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    try:
        spec.loader.exec_module(module)
    finally:
        sys.stdout, sys.stderr = saved_out, saved_err
    return module


_SELECTOR = _selector_module()


def _registry_block() -> dict:
    text = REGISTRY.read_text(encoding="utf-8")
    match = re.search(r"^```json policy-registry\.v1\n(.*?)^```", text,
                      re.MULTILINE | re.DOTALL)
    assert match, "no `json policy-registry.v1` fenced block in policy-families.md"
    return json.loads(match.group(1))


def _resolve(module: str, root: Path) -> Path:
    namespace, _, remainder = module.partition(":")
    roots = _SKILL_ROOTS if namespace == "skill" else _SEED_ROOTS
    for base in roots:
        candidate = root / base / remainder if base else root / remainder
        if candidate.is_file():
            return candidate
    raise AssertionError(f"{module!r} resolves to no file under {root}")


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SELECTOR), *args],
        capture_output=True, text=True, check=False,
    )


def _select(key: str) -> dict:
    proc = _run(*REGISTRY_ARGS, key)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _write_registry(tmp_path: Path, registry: dict,
                    info: str = "json policy-registry.v1") -> Path:
    path = tmp_path / "policy-families.md"
    path.write_text(f"# fixture\n\n```{info}\n{json.dumps(registry, indent=2)}\n```\n",
                    encoding="utf-8")
    return path


def _refuse(registry_path: Path,
            key: str = "CODE-IMPLEMENTATION") -> subprocess.CompletedProcess:
    proc = _run("--registry", str(registry_path), "--root", str(REPO_ROOT), key)
    assert proc.returncode != 0, f"expected refusal, got 0:\n{proc.stdout}"
    assert proc.stderr.startswith("select-policy-families:"), proc.stderr
    return proc


def _base_registry() -> dict:
    return json.loads(json.dumps(_registry_block()))


# --- AC5: the record envelope -------------------------------------------------

def test_record_envelope_is_exact_with_a_null_assembled_digest():
    """One real subprocess proves the CLI contract; the sweep runs in-process.

    The subject of the CLI case is the integration — exit status, an empty
    stderr, and stdout parsing as one JSON object. The per-key envelope shape is
    settled by `build_record`, so it does not need 11 interpreter starts.
    """
    registry = _SELECTOR.load_registry(REGISTRY)
    keys = list(registry["selection"])

    proc = _run(*REGISTRY_ARGS, keys[0])
    assert proc.returncode == 0, proc.stderr
    # F5: this reads stderr, so say stderr.
    assert proc.stderr == "", "diagnostics leaked to stderr on the success path"
    printed = json.loads(proc.stdout)
    # AC5 claims the *printed* object's key set. Asserting only the in-process
    # return would leave a fourth top-level key added in `main` undetected.
    assert set(printed) == {"selection_key", "families", "assembled_brief_digest"}
    assert printed["selection_key"] == keys[0]
    assert printed["assembled_brief_digest"] is None

    for key in keys:
        record = _SELECTOR.build_record(registry, key, REPO_ROOT)
        assert set(record) == {"selection_key", "families", "assembled_brief_digest"}
        assert record["selection_key"] == key
        assert record["assembled_brief_digest"] is None


# --- AC7: resolution prefers the copy an acting agent reads -------------------

def test_seed_locator_prefers_the_live_root_over_the_seed_copy():
    """The one candidate pair in this tree that actually differs.

    Every `skill:` candidate here is byte-identical, so a permutation is
    invisible; root AGENTS.md and packs/core/seeds/AGENTS.md differ, which is
    what makes the preference order observable at all.
    """
    entry = next(f for f in _select("CODE-IMPLEMENTATION")["families"]
                 if f["id"] == "the-razor")
    live = hashlib.sha256((REPO_ROOT / "AGENTS.md").read_bytes()).hexdigest()
    seeded = hashlib.sha256(
        (REPO_ROOT / "packs/core/seeds/AGENTS.md").read_bytes()).hexdigest()

    assert live != seeded, "fixture assumption broke: the two copies converged"
    assert entry["module_digest"] == live


def test_skill_locator_prefers_the_first_candidate_root(tmp_path):
    """Synthetic, because the repository tree cannot answer this.

    All three `skill:` candidates here hold identical bytes, so any order yields
    the same digest. Two deliberately different files at the first and third
    candidate paths give the order an oracle.
    """
    first = tmp_path / ".claude/skills/probe/rule.md"
    third = tmp_path / "packs/core/.apm/skills/probe/rule.md"
    for path, body in ((first, "first candidate\n"), (third, "third candidate\n")):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    registry = {
        "schema_version": 1,
        "families": [{"id": "probe", "tier": "advisory",
                      "module": "skill:probe/rule.md"}],
        "selection": {"CODE-IMPLEMENTATION": ["probe"]},
    }
    proc = _run("--registry", str(_write_registry(tmp_path, registry)),
                "--root", str(tmp_path), "CODE-IMPLEMENTATION")

    assert proc.returncode == 0, proc.stderr
    digest = json.loads(proc.stdout)["families"][0]["module_digest"]
    assert digest == hashlib.sha256(first.read_bytes()).hexdigest()


def test_every_selected_entry_matches_its_registry_record():
    registry = _SELECTOR.load_registry(REGISTRY)
    by_id = {f["id"]: f for f in registry["families"]}
    for key in registry["selection"]:
        for entry in _SELECTOR.build_record(registry, key, REPO_ROOT)["families"]:
            source = by_id[entry["id"]]
            assert entry["tier"] == source["tier"]
            assert entry["module"] == source["module"]
            resolved = _resolve(source["module"], REPO_ROOT)
            assert entry["module_digest"] == hashlib.sha256(
                resolved.read_bytes()).hexdigest()
            assert re.fullmatch(r"[0-9a-f]{64}", entry["module_digest"])


# --- AC8: the refusal set -----------------------------------------------------

def test_duplicate_family_id_is_refused(tmp_path):
    registry = _base_registry()
    registry["families"].append(dict(registry["families"][0]))
    _refuse(_write_registry(tmp_path, registry))


def test_selection_naming_an_unknown_family_is_refused(tmp_path):
    registry = _base_registry()
    registry["selection"]["CODE-IMPLEMENTATION"] = ["no-such-family"]
    _refuse(_write_registry(tmp_path, registry))


def _family(registry: dict, fid: str) -> dict:
    """Address a family by id. Positional indices couple a fixture to AC2's order."""
    return next(f for f in registry["families"] if f["id"] == fid)


def test_unresolvable_module_is_refused(tmp_path):
    registry = _base_registry()
    # `the-razor` on purpose: resolution runs only for a *selected* family, and
    # CODE-IMPLEMENTATION selects it.
    _family(registry, "the-razor")["module"] = "seed:no/such/file.md"
    _refuse(_write_registry(tmp_path, registry))


def test_unknown_tier_is_refused(tmp_path):
    registry = _base_registry()
    _family(registry, "the-razor")["tier"] = "blocking"
    _refuse(_write_registry(tmp_path, registry))


def test_unknown_module_namespace_is_refused(tmp_path):
    # The remainder must RESOLVE, or this case is dominated by the resolution
    # check: a namespace-less module partitions to an empty remainder, which
    # fails to resolve and refuses for the wrong reason, leaving this case green
    # when the namespace check is deleted. `http:AGENTS.md` resolves to the root
    # file under the seed search order, so only the namespace check can refuse it.
    registry = _base_registry()
    _family(registry, "the-razor")["module"] = "http:AGENTS.md"
    _refuse(_write_registry(tmp_path, registry))


def test_selection_list_repeating_an_id_is_refused(tmp_path):
    registry = _base_registry()
    registry["selection"]["CODE-IMPLEMENTATION"] = ["the-razor", "the-razor"]
    _refuse(_write_registry(tmp_path, registry))


def test_info_string_disagreeing_with_schema_version_is_refused(tmp_path):
    # A *supported* schema_version with a mismatched info string. The obvious
    # fixture (v1 / schema_version 2) is caught by the `== 1` check once the
    # pair check is removed, so it would survive its own mutation.
    registry = _base_registry()
    _refuse(_write_registry(tmp_path, registry, info="json policy-registry.v2"))


def test_unsupported_schema_version_is_refused(tmp_path):
    # A *consistent* unsupported pair, so the pair check (which runs first) does
    # not fire and this case reaches the version check.
    registry = _base_registry()
    registry["schema_version"] = 2
    _refuse(_write_registry(tmp_path, registry, info="json policy-registry.v2"))


# --- Containment: a locator may not read outside --root ----------------------

def test_projected_file_safety_matches_the_agentbundle_canonical():
    """Cross-tree parity: the pack copy is byte-identical to the engine helper.

    The selector confines through the blessed helper rather than a local
    canonicalize-then-prefix check, so the mirror must not drift from the
    source that gets hardened.
    """
    mirror = REPO_ROOT / "packs/core/.apm/skills/work-loop/scripts/file_safety.py"
    canonical = (REPO_ROOT
                 / "packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py")

    assert mirror.read_bytes() == canonical.read_bytes()


def test_hard_link_into_root_is_refused(tmp_path):
    """A hard link is canonically inside the boundary, so resolve() cannot see it.

    `Path.resolve()` does not traverse hard links: a second link to an
    out-of-root inode has a canonical path under the root and passes any
    canonicalize-then-prefix check. The blessed helper refuses on `st_nlink > 1`,
    which is the observable that distinguishes it.
    """
    secret = tmp_path / "outside_secret.txt"
    secret.write_text("secret\n", encoding="utf-8")
    root = tmp_path / "root"
    root.mkdir()
    os.link(secret, root / "hardlink.md")

    registry = {
        "schema_version": 1,
        "families": [{"id": "probe", "tier": "advisory", "module": "seed:hardlink.md"}],
        "selection": {"CODE-IMPLEMENTATION": ["probe"]},
    }
    proc = _run("--registry", str(_write_registry(tmp_path, registry)),
                "--root", str(root), "CODE-IMPLEMENTATION")

    assert proc.returncode != 0, f"hard link was digested:\n{proc.stdout}"
    assert proc.stderr.startswith("select-policy-families:"), proc.stderr


def test_non_utf8_registry_is_refused_not_a_traceback(tmp_path):
    path = tmp_path / "policy-families.md"
    path.write_bytes(b"```json policy-registry.v1\n\xff\xfe not utf-8\n```\n")
    proc = _run("--registry", str(path), "--root", str(REPO_ROOT), "K")

    assert proc.returncode != 0
    assert proc.stderr.startswith("select-policy-families:"), proc.stderr
    assert "Traceback" not in proc.stderr


def test_control_sequences_in_a_module_cannot_repaint_the_refusal(tmp_path):
    """File-controlled bytes reaching a terminal must not carry escape authority.

    A raw ESC sequence in the candidate list can erase the line and rewrite it,
    making a non-zero refusal read as a pass to an operator or a log scraper.
    """
    root = tmp_path / "root"
    root.mkdir()
    hostile = "seed:\x1b[2K\x1b[1;32mSUCCESS: all families resolved\x1b[0m/x.md"
    registry = {
        "schema_version": 1,
        "families": [{"id": "probe", "tier": "advisory", "module": hostile}],
        "selection": {"CODE-IMPLEMENTATION": ["probe"]},
    }
    proc = _run("--registry", str(_write_registry(tmp_path, registry)),
                "--root", str(root), "CODE-IMPLEMENTATION")

    assert proc.returncode != 0
    assert "\x1b" not in proc.stderr, "raw ESC reached stderr"


def test_module_escaping_root_is_refused(tmp_path):
    """`..`, absolute, and symlink-out locators all refuse.

    `Path.__truediv__` discards the left operand when the right is absolute, so
    joining alone confines nothing; and a symlink inside the boundary can still
    point outside it, which is why containment is re-checked after resolving.
    """
    outside = tmp_path / "outside.txt"
    outside.write_text("secret\n", encoding="utf-8")
    root = tmp_path / "root"
    root.mkdir()
    link = root / "link.md"
    link.symlink_to(outside)

    for module in ("seed:../outside.txt", f"seed:{outside}",
                   f"skill:{outside}", "seed:../../outside.txt",
                   "seed:link.md"):
        registry = {
            "schema_version": 1,
            "families": [{"id": "probe", "tier": "advisory", "module": module}],
            "selection": {"CODE-IMPLEMENTATION": ["probe"]},
        }
        proc = _run("--registry", str(_write_registry(tmp_path, registry)),
                    "--root", str(root), "CODE-IMPLEMENTATION")
        assert proc.returncode != 0, f"{module!r} was not refused:\n{proc.stdout}"
        assert proc.stderr.startswith("select-policy-families:"), proc.stderr


def test_a_tampered_helper_mirror_refuses_through_the_declared_channel(tmp_path):
    """Absent, symlinked and truncated mirrors all report as refusals.

    Two of the loader's three refusals are tamper detection. A control that
    announces a detected substitution with a traceback and an empty stdout
    breaks the contract every other refusal keeps, and `json.loads` over
    stdout then raises instead of parsing.
    """
    import shutil

    source = REPO_ROOT / "packs/core/.apm/skills/work-loop/scripts"
    for label, sabotage in (
        ("absent", lambda d: (d / "file_safety.py").unlink()),
        ("symlink", lambda d: ((d / "file_safety.py").unlink(),
                               (d / "file_safety.py").symlink_to(
                                   source / "file_safety.py"))),
        ("truncated", lambda d: (d / "file_safety.py").write_text(
            "# partial\n", encoding="utf-8")),
    ):
        staged = tmp_path / label
        shutil.copytree(source, staged)
        sabotage(staged)
        proc = subprocess.run(
            [sys.executable, str(staged / "select-policy-families.py"),
             "--registry", str(REGISTRY), "--root", str(REPO_ROOT),
             "CODE-IMPLEMENTATION"],
            capture_output=True, text=True, check=False,
        )
        assert proc.returncode != 0, f"{label}: accepted a tampered mirror"
        assert proc.stderr.startswith("select-policy-families:"), (
            f"{label} reported through the wrong channel:\n{proc.stderr}")
        assert "Traceback" not in proc.stderr, f"{label} crashed:\n{proc.stderr}"


# --- Malformed shapes leave through the documented channel -------------------

def test_non_object_registry_shapes_refuse_rather_than_traceback(tmp_path):
    """Every refusal is a prefixed one-liner, never a stack trace."""
    path = tmp_path / "policy-families.md"
    for body in ("[1, 2, 3]", "null", '"a string"', "42",
                 '{"schema_version": 1, "families": [1], "selection": {}}',
                 '{"schema_version": 1, "families": [{"id": 1, "tier": "advisory",'
                 ' "module": "seed:AGENTS.md"}], "selection": {}}',
                 '{"schema_version": 1, "families": [{"id": "a", "tier": "advisory",'
                 ' "module": 7}], "selection": {}}',
                 '{"schema_version": 1, "families": [{"id": "a", "tier": "advisory",'
                 ' "module": "seed:AGENTS.md"}], "selection": {"K": "not-a-list"}}'):
        path.write_text(f"```json policy-registry.v1\n{body}\n```\n", encoding="utf-8")
        proc = _run("--registry", str(path), "--root", str(REPO_ROOT), "K")
        assert proc.returncode != 0, f"{body} was accepted"
        assert proc.stderr.startswith("select-policy-families:"), (
            f"{body} produced a traceback, not a refusal:\n{proc.stderr}")
        assert "Traceback" not in proc.stderr


def test_unterminated_fence_is_reported_as_such(tmp_path):
    path = tmp_path / "policy-families.md"
    path.write_text('```json policy-registry.v1\n{"schema_version": 1}\n',
                    encoding="utf-8")
    proc = _run("--registry", str(path), "--root", str(REPO_ROOT), "K")

    assert proc.returncode != 0
    # Assert the MESSAGE, not a substring of the whole stream. pytest derives
    # tmp_path from the test's own name, so this file's path already contains
    # "unterminated" — a bare `in proc.stderr` passes even when the selector
    # reports something else entirely. Measured: it survived its own mutation.
    message = proc.stderr.split("select-policy-families: ", 1)[1]
    assert message.startswith("unterminated fenced block"), message


def test_guide_refusal_table_quotes_what_the_selector_emits(tmp_path):
    """Every fragment the guide's refusal table quotes is driven against the emitter.

    Coverage is self-policing: the fragment list is parsed out of the guide, and
    a documented fragment with no driver fails rather than being skipped. An
    earlier version drove four of six while its docstring claimed all of them,
    which is the wording that would have stopped the next author noticing.

    The table previously quoted `resolves to no file under Z` while the selector
    emitted `confined to`. Nothing compared the two, so the row went stale
    silently and would have sent an adopter hunting for a missing file when the
    real cause was a locator reaching outside the root.
    """
    guide_path = REPO_ROOT / "guides/core/reference/phase-scoped-policy-delivery.md"
    guide = guide_path.read_text(encoding="utf-8")
    table = guide[guide.index("| What you see |"):]
    table = table[:table.index("\n\n")]
    # Every `code` span in the first column, including a cell listing two.
    documented = {frag for row in table.splitlines()[2:]
                  for frag in re.findall(r"`([^`]+)`", row.split("|")[1])}

    root = tmp_path / "root"
    root.mkdir()
    (root / "in.md").write_text("in\n", encoding="utf-8")
    ok = {"id": "p", "tier": "advisory", "module": "seed:in.md"}

    def reg(**over) -> dict:
        base = {"schema_version": 1, "families": [dict(ok)],
                "selection": {"CODE-IMPLEMENTATION": ["p"]}}
        base.update(over)
        return base

    # documented fragment -> (registry, key, info-string override or None)
    drivers = {
        "unknown selection key 'X'": (reg(), "NO-SUCH", None),
        "module 'Y' resolves to no file confined to Z": (
            reg(families=[{**ok, "module": "seed:../out.md"}]),
            "CODE-IMPLEMENTATION", None),
        "info string ... disagrees with schema_version": (
            reg(), "CODE-IMPLEMENTATION", "json policy-registry.v2"),
        "unsupported schema_version": (
            reg(schema_version=2), "CODE-IMPLEMENTATION", "json policy-registry.v2"),
        "duplicate family id": (
            reg(families=[dict(ok), dict(ok)]), "CODE-IMPLEMENTATION", None),
        "selection 'X' repeats a family id": (
            reg(selection={"CODE-IMPLEMENTATION": ["p", "p"]}),
            "CODE-IMPLEMENTATION", None),
        "family 'Y' has tier ...": (
            reg(families=[{**ok, "tier": "blocking"}]), "CODE-IMPLEMENTATION", None),
    }

    # An empty parse must fail, not empty the work list. Without this the
    # `undriven` check is vacuously satisfied and every driver below is skipped,
    # so the test goes green having never run the selector — reachable through
    # any edit that moves the first blank line after the header.
    assert documented, (
        f"parsed no refusal fragments from {guide_path.name} — the table's shape "
        f"changed; fix the parse rather than letting this test assert nothing")
    # Both directions: a documented fragment with no driver fails, and a driver
    # for a fragment the guide no longer quotes fails too.
    assert documented == set(drivers), (
        f"guide and drivers disagree — documented-only: "
        f"{sorted(documented - set(drivers))}, driver-only: "
        f"{sorted(set(drivers) - documented)}")

    # The table elides variables as `X`, `Y`, `Z` and `...`. Require EVERY
    # literal segment between those placeholders, not the leading stem: for
    # "family 'Y' has tier ..." the stem alone is "family", which matches almost
    # any message and let two emitter rewordings pass their own mutation.
    for fragment, (registry, key, info) in drivers.items():
        segments = [s.strip() for s in re.split(r"'?[XYZ]'?|\.\.\.", fragment)
                    if s.strip()]
        assert segments, f"{fragment!r} has no literal segment to match on"
        path = (_write_registry(tmp_path, registry, info) if info
                else _write_registry(tmp_path, registry))
        proc = _run("--registry", str(path), "--root", str(root), key)
        assert proc.returncode != 0, f"{fragment}: not refused"
        for segment in segments:
            assert segment in proc.stderr, (
                f"guide documents {fragment!r} (segment {segment!r} missing) but "
                f"the selector emitted:\n{proc.stderr}")


# --- T6: the guide's coverage half --------------------------------------------

def test_guide_names_every_family_and_the_reserved_token():
    guide = REPO_ROOT / "guides/core/reference/phase-scoped-policy-delivery.md"
    text = guide.read_text(encoding="utf-8")

    for family in _registry_block()["families"]:
        assert family["id"] in text, f"guide omits {family['id']}"
    assert "DIRECT-LIGHT" in text
    for heading in ("## Declaring a family", "## Classifying a family",
                    "## Troubleshooting a selection"):
        assert heading in text, f"guide omits {heading!r}"
