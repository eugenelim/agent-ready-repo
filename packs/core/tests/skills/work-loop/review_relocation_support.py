"""Comparison corpus for the finding-adjudication command relocation.

The corpus is a list of cases. Each case seeds a throwaway repository with one
cohort spec directory, writes generic report files, then runs a sequence of
steps against it: a command (`cli`) or a hand edit of `state.json` (`state`).

Every `cli` step names its arguments as the `loop-cohort.py review` verbs take
them. The same arguments, without the leading `review`, are what
`review-artifact.py` takes, so one case runs through both command sets.

`fixtures/review-relocation/golden.json` holds each step's stdout, stderr, exit
code, and the review counters in `state.json` afterwards, recorded from the
`loop-cohort.py review` verbs BEFORE they delegated to `review-artifact.py`.
Regenerate it only from a pre-change tree:

    python review_relocation_support.py <pre-change-loop-cohort.py> <golden.json>

Only the standard library is used, and the module loads scripts by path under
unique names so a bare `import` never binds the wrong sibling.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "review-relocation"
GOLDEN = FIXTURES / "golden.json"

RUN_ID = "11111111-1111-4111-8111-111111111111"
OTHER_RUN_ID = "22222222-2222-4222-8222-222222222222"
SENTINEL = "Clean — ready to commit."

COUNTER_FIELDS = (
    "review_round_count",
    "review_retry_count",
    "max_review_retries",
    "finding_fingerprints",
    "previous_finding_fingerprints",
    "last_review_clean_source",
    "last_review_clean_digest",
    "last_review_record_operation_id",
    "last_review_record_payload_digest",
)


def fingerprint(location: str, line: int, title: str) -> str:
    """Re-derive a finding fingerprint the way the skill documents it."""
    return hashlib.sha256(f"{location}|{line}|{title}".encode()).hexdigest()


FP_A = fingerprint("src/example.py", 10, "**1. Missing guard**")
FP_B = fingerprint("src/other.py", 20, "**1. Unchecked input**")
FP_OLD = "d" * 40  # the 40-hex SHA-1 form a pre-2.3.0 run may still hold

_FINDING_A = "**1. Missing guard** `src/example.py:10`"
_FINDING_B = "**1. Unchecked input** `src/other.py:20`"
_SUSTAINED_A = f"{_FINDING_A}. The handler skips validation. Fix: validate the input."
_SUSTAINED_B = f"{_FINDING_B}. The loader trusts its caller. Fix: check the caller."


def _envelope(main: str, indeterminate: str = "None.") -> str:
    """Build the three-section finding-adjudicator envelope."""
    return (
        f"## Main-loop result\n{main}\n\n## Refuted audit\n\nNone.\n\n"
        f"## Indeterminate audit\n\n{indeterminate}\n"
    )


FILES: dict[str, str] = {
    "adj-clean.md": _envelope(SENTINEL),
    "adj-findings-a.md": _envelope(_SUSTAINED_A),
    "adj-findings-b.md": _envelope(_SUSTAINED_B),
    "adj-indeterminate.md": _envelope(
        SENTINEL, "ADJUDICATION-INDETERMINATE: the claim cannot be decided."
    ),
    "adj-bad-shape.md": _envelope("Everything looks fine."),
    "legacy-findings-a.md": _FINDING_A + "\n",
    "legacy-clean.md": f"Review complete.\n\n{SENTINEL}\n",
    "legacy-ship-it.md": "Review complete.\nSHIP IT\n",
    "raw-clean.md": SENTINEL + "\n",
    "raw-footer.md": f"{SENTINEL}\n\n## Not checked\n- Did not run the slow suite.\n",
    "raw-findings.md": _FINDING_A + "\n",
    "raw-noise.md": "Looks fine to me.\n",
    "exact-sentinel.txt": SENTINEL,
    "wrong-sentinel.txt": SENTINEL + "\n",
}

_REC = ["record", "{spec}"]
_RUN = ["--expect-run-id", "{run}"]


def _fp_round(*fps: str, extra: list[str] | None = None) -> list[str]:
    """Argv for a findings round carrying the given fingerprints."""
    flags: list[str] = []
    for value in fps:
        flags += ["--fingerprint", value]
    return [*_REC, *flags, *_RUN, *(extra or [])]


CASES: list[dict[str, Any]] = [
    # classify (state-free)
    {"id": "classify-clean-text", "steps": [
        ("cli", ["classify", "--report", "{f}/adj-clean.md"])]},
    {"id": "classify-clean-json", "steps": [
        ("cli", ["classify", "--report", "{f}/adj-clean.md", "--json"])]},
    {"id": "classify-findings-json", "steps": [
        ("cli", ["classify", "--report", "{f}/adj-findings-a.md", "--json"])]},
    {"id": "classify-legacy-report-refused", "steps": [
        ("cli", ["classify", "--report", "{f}/legacy-clean.md", "--json"])]},
    {"id": "classify-bad-shape-refused", "steps": [
        ("cli", ["classify", "--report", "{f}/adj-bad-shape.md"])]},
    {"id": "classify-indeterminate-refused", "steps": [
        ("cli", ["classify", "--report", "{f}/adj-indeterminate.md", "--json"])]},
    {"id": "classify-unreadable", "steps": [
        ("cli", ["classify", "--report", "{f}/absent.md", "--json"])]},
    # raw-classify (state-free)
    {"id": "raw-classify-clean-text", "steps": [
        ("cli", ["raw-classify", "--report", "{f}/raw-clean.md"])]},
    {"id": "raw-classify-clean-json", "steps": [
        ("cli", ["raw-classify", "--report", "{f}/raw-clean.md", "--json"])]},
    {"id": "raw-classify-footer-json", "steps": [
        ("cli", ["raw-classify", "--report", "{f}/raw-footer.md", "--json"])]},
    {"id": "raw-classify-findings-json", "steps": [
        ("cli", ["raw-classify", "--report", "{f}/raw-findings.md", "--json"])]},
    {"id": "raw-classify-noise-refused", "steps": [
        ("cli", ["raw-classify", "--report", "{f}/raw-noise.md"])]},
    {"id": "raw-classify-unreadable", "steps": [
        ("cli", ["raw-classify", "--report", "{f}/absent.md", "--json"])]},
    # inspect
    {"id": "inspect-adjudication-no-previous-round", "steps": [
        ("cli", ["inspect", "{spec}", "--report", "{f}/adj-findings-a.md",
                 "--adjudication", "--json"])]},
    {"id": "inspect-adjudication-previous-round-match", "steps": [
        ("cli", _fp_round(FP_A)),
        ("cli", ["inspect", "{spec}", "--report", "{f}/adj-findings-a.md",
                 "--adjudication", "--json"]),
        ("cli", ["inspect", "{spec}", "--report", "{f}/adj-findings-a.md",
                 "--adjudication"])]},
    {"id": "inspect-adjudication-previous-round-differs", "steps": [
        ("cli", _fp_round(FP_B)),
        ("cli", ["inspect", "{spec}", "--report", "{f}/adj-findings-a.md",
                 "--adjudication", "--json"])]},
    {"id": "inspect-adjudication-clean", "steps": [
        ("cli", ["inspect", "{spec}", "--report", "{f}/adj-clean.md",
                 "--adjudication", "--json"])]},
    {"id": "inspect-adjudication-legacy-refused", "steps": [
        ("cli", ["inspect", "{spec}", "--report", "{f}/legacy-clean.md",
                 "--adjudication", "--json"])]},
    {"id": "inspect-legacy-findings-match", "steps": [
        ("cli", _fp_round(FP_A)),
        ("cli", ["inspect", "{spec}", "--report", "{f}/legacy-findings-a.md",
                 "--json"])]},
    {"id": "inspect-legacy-ship-it", "steps": [
        ("cli", ["inspect", "{spec}", "--report", "{f}/legacy-ship-it.md"])]},
    # record: each form
    {"id": "record-fingerprint", "steps": [
        ("cli", _fp_round(FP_B, FP_A, FP_A)),
        ("cli", _fp_round(FP_B))]},
    {"id": "record-fingerprint-sha1-accepted", "steps": [
        ("cli", _fp_round(FP_OLD))]},
    {"id": "record-fingerprint-malformed-refused", "steps": [
        ("cli", _fp_round("NOT-HEX"))]},
    {"id": "record-direct-clean-file", "steps": [
        ("cli", [*_REC, "--direct-clean-file", "{f}/exact-sentinel.txt", *_RUN])]},
    {"id": "record-direct-clean-file-wrong-bytes-refused", "steps": [
        ("cli", [*_REC, "--direct-clean-file", "{f}/wrong-sentinel.txt", *_RUN])]},
    {"id": "record-direct-clean-file-with-adjudication-refused", "steps": [
        ("cli", [*_REC, "--direct-clean-file", "{f}/exact-sentinel.txt",
                 "--adjudication", *_RUN])]},
    {"id": "record-structural-clean-file", "steps": [
        ("cli", [*_REC, "--structural-clean-file", "{f}/raw-clean.md", *_RUN])]},
    {"id": "record-structural-clean-file-footer-refused", "steps": [
        ("cli", [*_REC, "--structural-clean-file", "{f}/raw-footer.md", *_RUN])]},
    {"id": "record-structural-clean-file-noise-refused", "steps": [
        ("cli", [*_REC, "--structural-clean-file", "{f}/raw-noise.md", *_RUN])]},
    {"id": "record-report-adjudication", "steps": [
        ("cli", [*_REC, "--report", "{f}/adj-clean.md", "--adjudication", *_RUN])]},
    {"id": "record-report-without-adjudication-refused", "steps": [
        ("cli", [*_REC, "--report", "{f}/adj-clean.md", *_RUN])]},
    {"id": "record-report-with-findings-refused", "steps": [
        ("cli", [*_REC, "--report", "{f}/adj-findings-a.md", "--adjudication",
                 *_RUN])]},
    {"id": "record-all-skipped", "steps": [
        ("cli", _fp_round(FP_A)),
        ("cli", [*_REC, "--all-skipped", *_RUN])]},
    {"id": "record-wrong-expect-run-id-refused", "steps": [
        ("cli", [*_REC, "--all-skipped", "--expect-run-id", OTHER_RUN_ID])]},
    # record: the budget
    {"id": "record-budget-reached", "steps": [
        ("state", {"max_review_retries": 2}),
        ("cli", _fp_round(FP_A)),
        ("cli", _fp_round(FP_B)),
        ("cli", _fp_round(FP_A, FP_B))]},
    {"id": "record-allow-retry-cap-override", "steps": [
        ("state", {"max_review_retries": 1}),
        ("cli", _fp_round(FP_A)),
        ("cli", _fp_round(FP_B)),
        ("cli", _fp_round(FP_B, extra=["--allow-retry-cap-override"]))]},
    {"id": "record-cap-raised-by-hand", "steps": [
        ("state", {"max_review_retries": 2}),
        ("cli", _fp_round(FP_A)),
        ("cli", _fp_round(FP_B)),
        ("cli", _fp_round(FP_A)),
        ("state", {"max_review_retries": 4}),
        ("cli", _fp_round(FP_A)),
        ("cli", _fp_round(FP_B))]},
    {"id": "record-clean-rounds-do-not-spend-budget", "steps": [
        ("state", {"max_review_retries": 1}),
        ("cli", [*_REC, "--report", "{f}/adj-clean.md", "--adjudication", *_RUN]),
        ("cli", [*_REC, "--all-skipped", *_RUN]),
        ("cli", _fp_round(FP_A)),
        ("cli", _fp_round(FP_B))]},
    # record: operation ids
    {"id": "record-operation-id-replay", "steps": [
        ("cli", _fp_round(FP_A, extra=["--operation-id", f"{RUN_ID}:1"])),
        ("cli", _fp_round(FP_A, extra=["--operation-id", f"{RUN_ID}:1"])),
        ("cli", _fp_round(FP_B, extra=["--operation-id", f"{RUN_ID}:1"])),
        ("cli", _fp_round(FP_B, extra=["--operation-id", f"{RUN_ID}:2"]))]},
    {"id": "record-operation-id-replay-clean", "steps": [
        ("cli", [*_REC, "--direct-clean-file", "{f}/exact-sentinel.txt", *_RUN,
                 "--operation-id", f"{RUN_ID}:1"]),
        ("cli", [*_REC, "--direct-clean-file", "{f}/exact-sentinel.txt", *_RUN,
                 "--operation-id", f"{RUN_ID}:1"])]},
    {"id": "record-operation-id-malformed-refused", "steps": [
        ("cli", _fp_round(FP_A, extra=["--operation-id", f"{RUN_ID}:01"])),
        ("cli", _fp_round(FP_A, extra=["--operation-id", f"{OTHER_RUN_ID}:1"]))]},
]


def load_script(name: str, path: Path) -> ModuleType:
    """Load one script by path under a unique name."""
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # a `@dataclass` resolves its module by name
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def call_main(module: ModuleType, argv: list[str]) -> tuple[int, str, str]:
    """Run `module.main(argv)` in-process; return (exit code, stdout, stderr).

    The streams are real text wrappers, not `StringIO`: a script that loads a
    sibling reconfigures `sys.stdout` while importing it, and `StringIO` has no
    `reconfigure`.
    """
    out_bytes, err_bytes = io.BytesIO(), io.BytesIO()
    out = io.TextIOWrapper(out_bytes, encoding="utf-8", newline="")
    err = io.TextIOWrapper(err_bytes, encoding="utf-8", newline="")
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = module.main(argv)
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 1
    out.flush()
    err.flush()
    return (
        int(code or 0),
        out_bytes.getvalue().decode("utf-8"),
        err_bytes.getvalue().decode("utf-8"),
    )


def seed_repo(root: Path, case: dict[str, Any], init_module: ModuleType) -> tuple[Path, Path]:
    """Create a repository with one initialised cohort spec and the case's files."""
    subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
    spec = root / "spec1"
    spec.mkdir()
    files = root / "files"
    files.mkdir()
    for name, text in FILES.items():
        (files / name).write_bytes(text.encode("utf-8"))
    with contextlib.chdir(root):
        code, _, err = call_main(init_module, ["init", str(spec), "--run-id", RUN_ID])
    assert code == 0, err
    return spec, files


def _expand(argv: list[str], spec: Path, files: Path) -> list[str]:
    return [
        part.replace("{spec}", str(spec)).replace("{f}", str(files)).replace("{run}", RUN_ID)
        for part in argv
    ]


def _scrub(text: str, spec: Path, files: Path) -> str:
    """Replace this run's throwaway paths so a diagnostic compares across runs."""
    for path, token in ((files, "<FILES>"), (spec, "<SPEC>")):
        for form in sorted({str(path), str(path.resolve())}, key=len, reverse=True):
            text = text.replace(form, token)
    return text


def read_state(spec: Path) -> dict[str, Any]:
    """Return the parsed cohort `state.json`."""
    return json.loads((spec / "state.json").read_text(encoding="utf-8"))


def patch_state(spec: Path, patch: dict[str, Any]) -> None:
    """Hand-edit `state.json` the way an operator raising a cap would."""
    state = read_state(spec)
    state.update(patch)
    (spec / "state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def run_case(
    module: ModuleType,
    case: dict[str, Any],
    spec: Path,
    files: Path,
    *,
    legacy: bool,
) -> list[dict[str, Any]]:
    """Run a case's steps in the current directory; return one record per `cli` step."""
    records: list[dict[str, Any]] = []
    for kind, payload in case["steps"]:
        if kind == "state":
            patch_state(spec, payload)
            continue
        argv = _expand(payload, spec, files)
        code, out, err = call_main(module, (["review"] if legacy else []) + argv)
        state = read_state(spec)
        records.append(
            {
                "exit_code": code,
                "stdout": _scrub(out, spec, files),
                "stderr": _scrub(err, spec, files),
                "counters": {name: state.get(name) for name in COUNTER_FIELDS},
            }
        )
    return records


def record_golden(legacy_cohort: Path, out_path: Path) -> None:
    """Record every case from a pre-change `loop-cohort.py` into `out_path`."""
    module = load_script("_review_relocation_golden_cohort", legacy_cohort)
    golden: dict[str, Any] = {}
    for case in CASES:
        with tempfile.TemporaryDirectory(prefix="review-relocation-") as tmp:
            root = Path(tmp).resolve()
            spec, files = seed_repo(root, case, module)
            with contextlib.chdir(root):
                golden[case["id"]] = run_case(module, case, spec, files, legacy=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(golden, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: review_relocation_support.py <loop-cohort.py> <golden.json>")
    record_golden(Path(sys.argv[1]), Path(sys.argv[2]))
