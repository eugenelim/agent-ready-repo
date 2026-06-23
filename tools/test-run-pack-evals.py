#!/usr/bin/env python3
"""Self-test for tools/run-pack-evals.py (pack-activation-evals, Tier A).

Pure-stdlib so it runs on Windows. The deterministic core — parse the
stream-json payload, compute trigger_rate, grade against 0.5, detect
intra-pack exclusivity, write the iteration-numbered workspace — is exercised
against fixtures and a fake (no-live-model) detector. The single live-model
surface (`claude -p`) is covered separately by the recorded manual run and the
report-only workflow, never here.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNNER = REPO_ROOT / "tools" / "run-pack-evals.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("run_pack_evals", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    # Register before exec so the @dataclass annotation lookup (string
    # annotations under `from __future__ import annotations`) can resolve
    # the module's own namespace via sys.modules.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def fail(label: str, msg: str) -> None:
    print(f"✖ {label}: {msg}", file=sys.stderr)
    sys.exit(1)


def check(label: str, cond: bool, msg: str) -> None:
    if not cond:
        fail(label, msg)


M = _load_runner()


# ── Pure functions ────────────────────────────────────────────────────────


def test_parse_activation() -> None:
    fired_stream = "\n".join(
        [
            json.dumps({"type": "system", "subtype": "init"}),
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "Skill",
                                "input": {"skill": "new-spec", "args": "x"},
                            }
                        ]
                    },
                }
            ),
            json.dumps({"type": "result", "subtype": "success", "result": "DONE"}),
        ]
    )
    res = M.parse_activation(fired_stream)
    check("parse-fired", res.fired is True, "expected fired True")
    check("parse-fired", res.skills_fired == ["new-spec"], f"got {res.skills_fired}")
    check("parse-fired", res.result == "DONE", f"got result {res.result!r}")

    quiet_stream = "\n".join(
        [
            json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "What feature?"}]}}),
            "{ this is not json",  # garbled line must be skipped, not crash
            json.dumps({"type": "result", "result": "asked a question"}),
        ]
    )
    res = M.parse_activation(quiet_stream)
    check("parse-quiet", res.fired is False, "expected fired False")
    check("parse-quiet", res.skills_fired == [], f"got {res.skills_fired}")
    print("✓ parse_activation: fired/quiet/garbled-line all handled.")


def test_trigger_rate_and_grade() -> None:
    check("rate", M.trigger_rate([True, True, False]) == 2 / 3, "2/3 expected")
    check("rate", M.trigger_rate([]) == 0.0, "empty -> 0.0")
    check("grade", M.grade(0.67, True) is True, "0.67 + should_trigger -> pass")
    check("grade", M.grade(0.33, True) is False, "0.33 + should_trigger -> fail")
    check("grade", M.grade(0.33, False) is True, "0.33 + should-not -> pass")
    check("grade", M.grade(0.67, False) is False, "0.67 + should-not -> fail")
    print("✓ trigger_rate + 0.5 grading correct.")


def test_safe_segment() -> None:
    for ok in ("core", "new-spec", "markdown-to-docx"):
        check("safe-seg", M._safe_segment("x", ok) == ok, f"{ok!r} should be accepted")
    for bad in ("../escape", "a/b", "..", ".", "", "a\\b", "/abs", M.REPORT_ERROR):
        try:
            M._safe_segment("x", bad)
        except ValueError:
            pass
        else:
            fail("safe-seg", f"{bad!r} must be rejected (path traversal)")
    print("✓ _safe_segment rejects traversal / multi-segment names.")


def test_detector_seam() -> None:
    det = M.get_detector("claude-code")
    check("seam", isinstance(det, M.ClaudeCodeDetector), "claude-code -> detector")
    for bad in ("kiro-ide", "cursor"):
        try:
            M.get_detector(bad)
        except ValueError as exc:
            check("seam", "headless" in str(exc), f"{bad}: message names headless")
        else:
            fail("seam", f"{bad} should raise (GUI-only)")
    try:
        M.get_detector("nonsense-adapter")
    except ValueError:
        pass
    else:
        fail("seam", "unknown adapter should raise, not silently run")
    print("✓ detector seam: claude-code dispatches; GUI-only + unknown rejected.")


# ── Orchestration with a fake (no-live-model) detector ────────────────────


class FakeDetector:
    adapter = "claude-code"

    def __init__(self, responses: dict[str, list[str]], errors: set[str] | None = None):
        # query text -> skills_fired list returned every run
        self.responses = responses
        self.errors = errors or set()

    def project(self, pack_path, output_root):  # pragma: no cover - not used
        raise AssertionError("project() must not be called when project_root is set")

    def run_and_parse(self, query, cwd, timeout):
        if query in self.errors:
            return M.ActivationResult(error="exit-1")
        return M.ActivationResult(
            skills_fired=list(self.responses.get(query, [])), result=f"ran: {query}"
        )


def test_run_and_parse_error_paths() -> None:
    import subprocess as sp

    det = M.ClaudeCodeDetector()
    orig = M.subprocess.run
    try:
        def _timeout(*a, **k):
            raise sp.TimeoutExpired(cmd="claude", timeout=1)
        M.subprocess.run = _timeout
        check("err", det.run_and_parse("q", pathlib.Path("."), 1).error == "timeout",
              "timeout must be flagged as a harness error")

        class _NonZero:
            returncode = 2
            stdout = '{"type":"result","result":"x"}'
        M.subprocess.run = lambda *a, **k: _NonZero()
        check("err", det.run_and_parse("q", pathlib.Path("."), 1).error == "exit-2",
              "non-zero exit must be flagged as a harness error")

        class _Ok:
            returncode = 0
            stdout = ('{"type":"assistant","message":{"content":[{"type":"tool_use",'
                      '"name":"Skill","input":{"skill":"x"}}]}}\n'
                      '{"type":"result","result":"ok"}')
        M.subprocess.run = lambda *a, **k: _Ok()
        r = det.run_and_parse("q", pathlib.Path("."), 1)
        check("err", r.error is None and r.skills_fired == ["x"],
              "a clean run must carry no error")

        def _oserror(*a, **k):
            raise OSError("claude not spawnable")
        M.subprocess.run = _oserror
        check("err", det.run_and_parse("q", pathlib.Path("."), 1).error == "spawn-error",
              "a spawn failure must be flagged as a harness error")

        class _Empty:
            returncode = 0
            stdout = ""
        M.subprocess.run = lambda *a, **k: _Empty()
        check("err", det.run_and_parse("q", pathlib.Path("."), 1).error == "no-result-event",
              "a returncode-0 empty/truncated stream must be flagged")
    finally:
        M.subprocess.run = orig
    print("✓ run_and_parse flags timeout / non-zero exit / spawn-error / "
          "no-result-event; clean run carries no error.")


def test_print_report_smoke() -> None:
    import contextlib
    import io

    summary = {
        "pack": "p", "adapter": "claude-code", "mode": "in-harness",
        "fidelity": "reported", "provenance": "operator-attested",
        "runs": None, "iteration": 1,
        "skills": {"s": {
            "queries": [{
                "query_id": "q00", "query": "x", "should_trigger": True,
                "trigger_rate": 0.0, "passed": False, "errored_runs": 2,
                "exclusivity_violations": [],
            }],
            "pass_count": 0, "total": 1, "error_count": 2,
        }},
    }
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        M._print_report(summary)
    out = buf.getvalue()
    check("report", "harness error" in out, "per-skill harness-error note must appear")
    check("report", "errored run" in out, "per-query errored-run note must appear")
    check("report", "provenance=operator-attested" in out,
          "in-harness provenance must show in the console report")
    print("✓ _print_report renders harness-error + provenance notes without crashing.")


def _build_fake_pack(repo_root: pathlib.Path) -> None:
    skills = repo_root / "packs" / "testpack" / ".apm" / "skills"
    (repo_root / "packs" / "testpack" / "pack.toml").parent.mkdir(
        parents=True, exist_ok=True
    )
    (repo_root / "packs" / "testpack" / "pack.toml").write_text(
        '[pack]\nname = "testpack"\n\n[pack.evals]\nskills = ["alpha"]\n',
        encoding="utf-8",
    )
    (skills / "alpha" / "evals").mkdir(parents=True, exist_ok=True)
    (skills / "alpha" / "evals" / "eval_queries.json").write_text(
        json.dumps(
            [
                {"query": "fire alpha", "should_trigger": True},
                {"query": "stay quiet", "should_trigger": False},
                {"query": "beta steals", "should_trigger": True},
            ]
        ),
        encoding="utf-8",
    )
    # A non-covered sibling skill so "beta" counts as intra-pack.
    (skills / "beta").mkdir(parents=True, exist_ok=True)


def test_run_eval_workspace_and_grading() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = pathlib.Path(tmp)
        _build_fake_pack(repo_root)
        detector = FakeDetector(
            {
                "fire alpha": ["alpha"],   # positive, fires -> pass
                "stay quiet": [],          # negative, quiet -> pass
                "beta steals": ["beta"],   # positive, a *different* skill fires
            }
        )
        summary = M.run_eval(
            "testpack",
            runs=3,
            detector=detector,
            repo_root=repo_root,
            project_root=repo_root,  # skip agentbundle projection
        )

        iter1 = repo_root / ".eval-workspace" / "testpack" / "iteration-1"
        check("ws", iter1.is_dir(), "iteration-1/ not created")
        check(
            "ws",
            (iter1 / "alpha" / "q00" / "with_skill" / "run-1" / "outputs" / "result.txt").is_file(),
            "per-run outputs/result.txt not captured",
        )
        check("ws", (iter1 / "summary.json").is_file(), "summary.json missing")

        # Reserved grading slots must NOT be produced by Tier A.
        for reserved in ("without_skill", "timing.json", "grading.json"):
            hits = list(iter1.rglob(reserved))
            check("reserved", not hits, f"Tier A produced reserved slot {reserved}: {hits}")
        check(
            "reserved",
            not (iter1 / "benchmark.json").exists(),
            "Tier A produced reserved benchmark.json",
        )

        # Grading.
        qs = {q["query_id"]: q for q in summary["skills"]["alpha"]["queries"]}
        check("grade", qs["q00"]["passed"] is True, "q00 positive-fires should pass")
        check("grade", qs["q00"]["trigger_rate"] == 1.0, "q00 rate 1.0")
        check("grade", qs["q01"]["passed"] is True, "q01 negative-quiet should pass")
        check("grade", qs["q02"]["passed"] is False, "q02 positive-stolen should fail")
        check(
            "exclusivity",
            qs["q02"]["exclusivity_violations"] == ["beta"],
            f"expected beta flagged, got {qs['q02']['exclusivity_violations']}",
        )
        check("count", summary["skills"]["alpha"]["pass_count"] == 2, "2 of 3 pass")
        check("mode", summary["mode"] == "headless" and summary["fidelity"] == "observed",
              "headless summary must be labelled mode=headless / fidelity=observed")
        check("err-count", summary["skills"]["alpha"]["error_count"] == 0,
              "clean detector -> 0 harness errors")

        # A detector that errors on one query surfaces error_count in the summary.
        err_det = FakeDetector(
            {"fire alpha": ["alpha"], "stay quiet": [], "beta steals": ["beta"]},
            errors={"stay quiet"},
        )
        err_summary = M.run_eval(
            "testpack", runs=2, detector=err_det,
            repo_root=repo_root, project_root=repo_root,
        )
        check("err-count", err_summary["skills"]["alpha"]["error_count"] == 2,
              f"2 errored runs expected, got {err_summary['skills']['alpha']['error_count']}")

        # Bounded summary: no secret / stderr / env leakage anywhere.
        blob = (iter1 / "summary.json").read_text(encoding="utf-8")
        for forbidden in ("ANTHROPIC_API_KEY", "stderr", "environ", "PATH="):
            check("bounded", forbidden not in blob, f"summary leaked {forbidden!r}")

        # A second pass increments the iteration number.
        M.run_eval(
            "testpack", runs=1, detector=detector,
            repo_root=repo_root, project_root=repo_root,
        )
        check(
            "iteration",
            (repo_root / ".eval-workspace" / "testpack" / "iteration-2").is_dir(),
            "second pass did not create iteration-2/",
        )
    print("✓ run_eval: workspace layout, grading, exclusivity, bounded summary, "
          "iteration bump all correct; reserved slots untouched.")


def test_grade_reports_in_harness() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = pathlib.Path(tmp)
        _build_fake_pack(repo_root)
        reports = {
            "alpha": {
                "q00": ["alpha", "alpha", "alpha"],          # positive, fires -> pass
                "q01": [None, None, None],                   # negative, quiet -> pass
                "q02": ["beta", "beta", M.REPORT_ERROR],     # positive, stolen+1 error -> fail
            }
        }
        summary = M.grade_reports("testpack", reports, repo_root=repo_root)

        check("mode", summary["mode"] == "in-harness", "mode must be in-harness")
        check("fidelity", summary["fidelity"] == "reported", "fidelity must be reported")
        qs = {q["query_id"]: q for q in summary["skills"]["alpha"]["queries"]}
        check("grade", qs["q00"]["passed"] is True and qs["q00"]["trigger_rate"] == 1.0,
              "q00 all-alpha -> pass @ 1.0")
        check("grade", qs["q01"]["passed"] is True, "q01 all-quiet negative -> pass")
        check("grade", qs["q02"]["passed"] is False, "q02 stolen -> fail")
        check("excl", qs["q02"]["exclusivity_violations"] == ["beta"], "beta flagged")
        check("err", qs["q02"]["errored_runs"] == 1, "1 errored run on q02")
        check("count", summary["skills"]["alpha"]["pass_count"] == 2, "2 of 3 pass")
        check("err-count", summary["skills"]["alpha"]["error_count"] == 1, "1 error total")

        # Bounded report capture written, contains only skill names (no model text).
        cap = (repo_root / ".eval-workspace" / "testpack" / "iteration-1"
               / "alpha" / "q02" / "in_harness" / "reports.json")
        check("capture", cap.is_file(), "in_harness reports.json not captured")
        blob = cap.read_text(encoding="utf-8")
        for forbidden in ("ANTHROPIC_API_KEY", "stderr", "environ"):
            check("capture", forbidden not in blob, f"capture leaked {forbidden!r}")
    print("✓ grade_reports: in-harness grading, mode/fidelity labels, exclusivity, "
          "errors, bounded capture.")


def test_grade_reports_validation_and_unmeasured() -> None:
    # Malformed reports must fail loud, not silently mis-grade.
    for bad in (
        ["not", "a", "dict"],
        {"alpha": "not-a-dict"},
        {"alpha": {"q00": "not-a-list"}},
        {"alpha": {"q00": [123]}},
    ):
        try:
            M._validate_reports(bad)
        except ValueError:
            pass
        else:
            fail("validate", f"{bad!r} must be rejected")
    M._validate_reports({"alpha": {"q00": ["alpha", None, M.REPORT_ERROR]}})  # valid

    # A covered query with no reports is flagged unmeasured (errored), not a miss.
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = pathlib.Path(tmp)
        _build_fake_pack(repo_root)  # alpha has q00, q01, q02
        summary = M.grade_reports(
            "testpack", {"alpha": {"q00": ["alpha"]}}, repo_root=repo_root
        )
        qs = {q["query_id"]: q for q in summary["skills"]["alpha"]["queries"]}
        check("unmeasured", qs["q01"]["errored_runs"] == 1, "q01 unmeasured -> errored")
        check("unmeasured", qs["q02"]["errored_runs"] == 1, "q02 unmeasured -> errored")
        check("unmeasured", summary["skills"]["alpha"]["error_count"] >= 2,
              "unmeasured queries surface in error_count")
        check("provenance", "operator-attested" in summary["provenance"],
              "summary records operator-attested provenance")
    print("✓ grade_reports: rejects malformed reports; flags unmeasured queries; "
          "records provenance.")


def _build_behavior_pack(repo_root: pathlib.Path) -> None:
    skills = repo_root / "packs" / "bxpack" / ".apm" / "skills"
    (repo_root / "packs" / "bxpack" / "pack.toml").parent.mkdir(parents=True, exist_ok=True)
    (repo_root / "packs" / "bxpack" / "pack.toml").write_text(
        '[pack]\nname = "bxpack"\n\n[pack.evals]\nskills = ["alpha"]\n', encoding="utf-8"
    )
    (skills / "alpha" / "evals" / "files").mkdir(parents=True, exist_ok=True)
    (skills / "alpha" / "evals" / "files" / "in.txt").write_text("fixture\n", encoding="utf-8")
    (skills / "alpha" / "evals" / "evals.json").write_text(json.dumps({
        "skill_name": "alpha",
        "evals": [
            {"id": 1, "prompt": "p1", "expected_output": "e1",
             "assertions": ["did the thing"],
             "expect": {"produces": ["out.txt"], "output_contains": ["OK"],
                        "output_excludes": ["Traceback"]}},
            {"id": 2, "prompt": "p2", "expected_output": "e2",
             "expect": {"produces": ["missing.txt"]}},
            {"id": 3, "prompt": "p3", "expected_output": "e3",
             "expect": {"produces": "out.txt"}},  # malformed: str not list
            {"id": 4, "prompt": "p4", "expected_output": "e4"},  # no expect / no assertions
        ],
    }), encoding="utf-8")


def test_seed_workspace() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = pathlib.Path(tmp)
        _build_behavior_pack(repo_root)
        skill_dir = repo_root / "packs" / "bxpack" / ".apm" / "skills" / "alpha"
        ws = M.seed_workspace(skill_dir, ["evals/files/in.txt"])
        try:
            check("seed", (ws / "in.txt").is_file(), "fixture copied into workspace")
            check("seed", str(ws).startswith(tempfile.gettempdir()),
                  "workspace lives under the OS temp root, not the repo")
        finally:
            shutil.rmtree(ws, ignore_errors=True)
        # Path-traversal fixture is refused.
        try:
            M.seed_workspace(skill_dir, ["evals/../../../../etc/hosts"])
        except ValueError:
            pass
        else:
            fail("seed", "out-of-evals fixture must be refused")
        # A symlinked fixture is refused (the guard checks the UNRESOLVED path).
        if hasattr(os, "symlink"):
            link = skill_dir / "evals" / "files" / "link.txt"
            try:
                os.symlink(skill_dir / "evals" / "files" / "in.txt", link)
            except (OSError, NotImplementedError):
                pass
            else:
                try:
                    M.seed_workspace(skill_dir, ["evals/files/link.txt"])
                except ValueError:
                    pass
                else:
                    fail("seed", "symlinked fixture must be refused")
    print("✓ seed_workspace: OS-temp dir, fixtures confined under evals/, "
          "traversal + symlink refused.")


def test_grade_behavior() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = pathlib.Path(tmp)
        _build_behavior_pack(repo_root)
        ws1 = pathlib.Path(tempfile.mkdtemp())
        ws2 = pathlib.Path(tempfile.mkdtemp())
        try:
            # eval 1: produced artifact + output file with OK, assertions attested true.
            (ws1 / "out.txt").write_text("done\n", encoding="utf-8")
            (ws1 / M.BEHAVIOR_OUTPUT_FILE).write_text("all OK here\n", encoding="utf-8")
            # eval 2: missing.txt NOT produced -> deterministic fail.
            ws3 = pathlib.Path(tempfile.mkdtemp())
            ws4 = pathlib.Path(tempfile.mkdtemp())
            results = {"alpha": {
                "1": {"assertions": [True], "errored": False},
                "2": {"assertions": [], "errored": False},
                "3": {"assertions": [], "errored": False},
                "4": {"assertions": [], "errored": False},
            }}
            summary = M.grade_behavior(
                "bxpack", results,
                workspaces={"alpha/1": str(ws1), "alpha/2": str(ws2),
                            "alpha/3": str(ws3), "alpha/4": str(ws4)},
                repo_root=repo_root,
            )
            check("bx", summary["mode"] == "in-harness" and summary["tier"] == "B-lite",
                  "labelled mode=in-harness / tier=B-lite")
            check("bx", summary["provenance"] == "operator-attested", "provenance recorded")
            evs = {e["eval_id"]: e for e in summary["skills"]["alpha"]["evals"]}
            check("bx", evs["1"]["passed"] is True, "eval 1 (artifact+output+assertion) passes")
            check("bx", evs["2"]["passed"] is False and not evs["2"]["produces_ok"],
                  "eval 2 fails on the missing artifact (re-derived by the runner)")
            check("bx", evs["3"]["errored"] and not evs["3"]["passed"],
                  "eval 3 malformed expect (str not list) fails closed")
            check("bx", evs["4"]["errored"] and not evs["4"]["passed"],
                  "eval 4 with no post-conditions fails closed (no vacuous pass)")
            check("bx", summary["skills"]["alpha"]["pass_count"] == 1, "1 of 4 pass")
            shutil.rmtree(ws3, ignore_errors=True)
            shutil.rmtree(ws4, ignore_errors=True)

            # Re-derivation is real: deleting eval-1's artifact flips it to fail,
            # regardless of any operator-claimed booleans (which we never accept).
            (ws1 / "out.txt").unlink()
            summary2 = M.grade_behavior(
                "bxpack", results,
                workspaces={"alpha/1": str(ws1), "alpha/2": str(ws2)},
                repo_root=repo_root,
            )
            ev1b = {e["eval_id"]: e for e in summary2["skills"]["alpha"]["evals"]}["1"]
            check("bx", ev1b["passed"] is False,
                  "removing the artifact flips eval 1 to fail (checks are re-derived)")

            # Fail-closed: a missing workspace grades errored, never a pass.
            summary3 = M.grade_behavior(
                "bxpack", {"alpha": {"1": {"assertions": [True], "errored": False}}},
                workspaces={}, repo_root=repo_root,
            )
            ev1c = {e["eval_id"]: e for e in summary3["skills"]["alpha"]["evals"]}["1"]
            check("bx", ev1c["errored"] and not ev1c["passed"],
                  "missing workspace fails closed")
        finally:
            shutil.rmtree(ws1, ignore_errors=True)
            shutil.rmtree(ws2, ignore_errors=True)
    print("✓ grade_behavior: re-derives deterministic checks from the workspace, "
          "attests assertions, labels B-lite, fails closed on missing workspace.")


def test_gitignored_control() -> None:
    # The real repo .gitignore must ignore a representative outputs/ path.
    rel = ".eval-workspace/core/iteration-1/new-spec/q00/with_skill/run-1/outputs/result.txt"
    proc = subprocess.run(
        ["git", "check-ignore", rel],
        cwd=str(REPO_ROOT), capture_output=True, text=True,
    )
    check("gitignore", proc.returncode == 0, f"{rel} is not gitignored")
    print("✓ .eval-workspace/ outputs path is gitignored.")


def test_help_smoke() -> None:
    proc = subprocess.run(
        [sys.executable, str(RUNNER), "--help"], capture_output=True, text=True
    )
    check("help", proc.returncode == 0, f"--help exited {proc.returncode}")
    check("help", "--pack" in proc.stdout, "--help missing --pack")
    print("✓ --help works.")


def main() -> int:
    test_parse_activation()
    test_trigger_rate_and_grade()
    test_safe_segment()
    test_run_and_parse_error_paths()
    test_print_report_smoke()
    test_detector_seam()
    test_run_eval_workspace_and_grading()
    test_grade_reports_in_harness()
    test_grade_reports_validation_and_unmeasured()
    test_seed_workspace()
    test_grade_behavior()
    test_gitignored_control()
    test_help_smoke()
    print()
    print("Self-test: passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
