#!/usr/bin/env python3
"""Self-test for tools/lint-knowledge-freshness.py.

Pure-stdlib Python so the suite runs on Windows without an MSYS shell.
Pattern: build a fixture repository in a tempdir holding `docs/knowledge/topics/`
and the files its pins cite, run the linter with `--root <fixture>`, and assert
the exit code plus a diagnostic substring on the failure cases. The linter is
driven as a subprocess rather than imported, so every case exercises the real
entry point and the real exit status. The case sweep and the pass/fail
protocol come from the shared `tools/selftest_harness.py`, which
`tools/AGENTS.md` names as their owner; `run_cases` is the runner that reports
how many cases ran, so a run that silently stopped executing them cannot read
the same as a full one.

Cases pin each refusal to the failure mode it exists to catch:

  A — every pin matches its cited file. Must exit 0.
  B — the cited file's bytes changed, same length. Must fail naming the topic.
      This is the mutation proof: it is the drift the checker exists for, and
      case A's green means nothing without it.
  C — the cited file's length changed. Must fail.
  D — a drifted `supporting_sources` pin with a matching `owning_source`. Must
      fail. The shipped `read_freshness_source` cannot see this one, so it is
      the case that justifies the checker covering more than `owning_source`.
  E — stale count within `--max-stale`. Must exit 0.
  F — stale count above `--max-stale`. Must fail.
  G — a pin citing a file that is not there. Must fail even under
      `--max-stale 99`: a baseline is a statement about known drift, and a
      missing file is not drift.
  H — a corpus with no pins at all. Must fail rather than report clean, so a
      wrong --root or an emptied corpus cannot read as green.
  I — a topic with `owning_source: null` and no supporting sources, beside one
      sound pin. Must exit 0 — an unpinned topic is not a finding.
  J — a malformed topic file. Must fail with a parse diagnostic, not a
      traceback.
  K — a digest kind the schema does not admit. Must fail as malformed.
  L — a schema-valid `git-blob-v1` pin. Must fail as unresolved under its own
      reason, never labelled unknown or unreadable.
  M — a source with no `digest` key, beside a sound pin. Must fail as
      malformed; before this case existed the pin was skipped and the run
      exited 0.
  N — a digest written as a string. Must fail as malformed.
  O — `supporting_sources` written as an object. Must fail as malformed.
  P — a null `byte_length`. Must fail as malformed, not with a traceback.
  Q — a malformed pin under `--json`. Must exit 1 and still emit a JSON
      object naming the error.
  R — a source carrying a key beyond `path` and `digest`. Must fail as
      malformed; the writer refuses it.
  S — a non-canonical `./` source path. Must fail as malformed; pathlib folds
      it away before the read, so only the writer's path rule can catch it.
  T — a `git-blob-v1` digest whose `algorithm` is a list. The writer's own
      validator crashes on it with `TypeError`; the checker must still report
      a malformed topic and, under `--json`, emit the JSON error object.
  U — a `bool` `byte_length`, which the writer accepts. Must NOT be refused as
      malformed: the checker holds topics to the writer's schema, not a
      stricter private one.

  V — a stale pin that sits only in a nested topic (`topics/area/nested.json`),
      beside a sound top-level pin. Must fail: the store's reader walks nested
      topic keys, and a top-level-only listing would exit 0 here.
  W — a topic whose `topic_key` does not match its file path. Must fail as
      malformed and name the file; the store's reader refuses it.
  X — a topic file with a duplicated JSON key. Must fail as malformed; the
      store's reader refuses duplicate keys where `json.loads` keeps the last.

Every fixture topic is a full, writer-valid topic, because the checker reads
the corpus only through the store's own reader.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

import selftest_harness

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LINTER = REPO_ROOT / "tools" / "lint-knowledge-freshness.py"

_LABEL = "lint-knowledge-freshness self-test"


def _digest(data: bytes) -> dict[str, object]:
    """Return the `sha256-bytes-v1` pin the store's writer would record for *data*."""
    return {
        "kind": "sha256-bytes-v1",
        "byte_length": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _topic(
    key: str,
    *,
    owning: dict[str, object] | None = None,
    supporting: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """A writer-valid v1 topic: it passes `validate_topic` unless a case breaks it."""
    return {
        "schema_version": "knowledge-topic.v1",
        "topic_key": key,
        "title": key.replace("-", " "),
        "synthesis": {"kind": "pattern", "body": "fixture body"},
        "scopes": ["."],
        "competency_facets": ["CQ-ORIENT"],
        "audience": "project",
        "lifecycle": "active",
        "freshness": {"state": "fresh", "checked_at": "1970-01-01T00:00:00Z"},
        "owning_source": owning,
        "supporting_sources": supporting or [],
        "occurrences": [
            {
                "capture_id": "kco-197001-" + "0" * 64,
                "mutation_id": "0" * 64,
                "producer": "fixture",
                "semantic_gate": "fixture",
                "source": {"path": "docs/fixture.md"},
                "scope": ".",
                "observed_at": "1970-01-01T00:00:00Z",
                "reviewed_disposition": "promoted",
            }
        ],
    }


def _write_topic(root: pathlib.Path, topic: dict[str, object]) -> None:
    """Write *topic* at the path its key maps to, creating nested folders."""
    target = root / "docs" / "knowledge" / "topics" / f"{topic['topic_key']}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(topic, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _write_source(root: pathlib.Path, relative: str, data: bytes) -> bytes:
    """Write a cited source file into the fixture repository and return its bytes."""
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return data


def _run(root: pathlib.Path, *extra: str) -> subprocess.CompletedProcess[str]:
    """Run the real linter entry point against the fixture repository at *root*."""
    return subprocess.run(
        [sys.executable, str(LINTER), "--root", str(root), *extra],
        capture_output=True,
        text=True,
        check=False,
    )


def _check(*, got: int, want: int, output: str, needle: str = "") -> None:
    """Assert the exit status, then the diagnostic that status is meant to explain."""
    assert got == want, f"exit {got}, expected {want}\n{output}"
    if needle:
        assert needle in output, f"diagnostic missing {needle!r}\n{output}"


def test_a_all_fresh() -> None:
    """A: every pin matches its cited file, so the run passes."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        data = _write_source(root, "docs/one.md", b"original bytes\n")
        _write_topic(root, _topic("fresh-topic", owning={"path": "docs/one.md", "digest": _digest(data)}))
        result = _run(root)
        _check(
            got=result.returncode,
            want=0,
            output=result.stdout + result.stderr,
            needle="1 pinned source(s) across 1 topic(s)",
        )


def test_b_content_drift() -> None:
    """B: equal-length byte drift is reported; the mutation proof for case A."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        pinned = _digest(b"original bytes\n")
        # Same length, different bytes — a length-only comparison would pass.
        _write_source(root, "docs/one.md", b"mutated bytes!\n")
        _write_topic(root, _topic("drifted-topic", owning={"path": "docs/one.md", "digest": pinned}))
        result = _run(root)
        _check(
            got=result.returncode,
            want=1,
            output=result.stdout + result.stderr,
            needle="drifted-topic owning_source pin is stale",
        )


def test_c_length_drift() -> None:
    """C: a change in byte length is reported as stale."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        pinned = _digest(b"short\n")
        _write_source(root, "docs/one.md", b"a considerably longer body\n")
        _write_topic(root, _topic("grown-topic", owning={"path": "docs/one.md", "digest": pinned}))
        result = _run(root)
        _check(
            got=result.returncode,
            want=1,
            output=result.stdout + result.stderr,
            needle="grown-topic owning_source pin is stale",
        )


def test_d_supporting_drift() -> None:
    """D: a drifted supporting pin is caught beside a sound owning pin."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        owning = _write_source(root, "docs/owning.md", b"owning body\n")
        supporting_pin = _digest(b"supporting body\n")
        _write_source(root, "docs/supporting.md", b"supporting body, edited\n")
        _write_topic(
            root,
            _topic(
                "supporting-drift",
                owning={"path": "docs/owning.md", "digest": _digest(owning)},
                supporting=[{"path": "docs/supporting.md", "digest": supporting_pin}],
            ),
        )
        result = _run(root)
        _check(
            got=result.returncode,
            want=1,
            output=result.stdout + result.stderr,
            needle="supporting-drift supporting_sources[0] pin is stale",
        )


def test_e_within_baseline() -> None:
    """E: a stale count within --max-stale passes."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        pinned = _digest(b"original bytes\n")
        _write_source(root, "docs/one.md", b"mutated bytes!\n")
        _write_topic(root, _topic("drifted-topic", owning={"path": "docs/one.md", "digest": pinned}))
        result = _run(root, "--max-stale", "1")
        _check(
            got=result.returncode,
            want=0,
            output=result.stdout + result.stderr,
            needle="1 stale, within --max-stale 1",
        )


def test_f_above_baseline() -> None:
    """F: a stale count above --max-stale fails."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        for name in ("one", "two"):
            pinned = _digest(b"original bytes\n")
            _write_source(root, f"docs/{name}.md", b"mutated bytes!\n")
            _write_topic(
                root,
                _topic(f"drifted-{name}", owning={"path": f"docs/{name}.md", "digest": pinned}),
            )
        result = _run(root, "--max-stale", "1")
        _check(
            got=result.returncode,
            want=1,
            output=result.stdout + result.stderr,
            needle="2 stale pin(s) of 2 examined",
        )


def test_g_unresolved_ignores_baseline() -> None:
    """G: a missing cited file fails whatever --max-stale says."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        _write_topic(
            root,
            _topic(
                "absent-source",
                owning={"path": "docs/gone.md", "digest": _digest(b"anything\n")},
            ),
        )
        result = _run(root, "--max-stale", "99")
        _check(
            got=result.returncode,
            want=1,
            output=result.stdout + result.stderr,
            needle="--max-stale does not cover an unresolved pin",
        )


def test_h_zero_pins_refuses() -> None:
    """H: a run that examined no pins refuses rather than reporting clean."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        _write_topic(root, _topic("unpinned-topic"))
        result = _run(root, "--max-stale", "99")
        _check(
            got=result.returncode,
            want=1,
            output=result.stdout + result.stderr,
            needle="examined 0 pinned sources",
        )


def test_i_unpinned_topic_is_not_a_finding() -> None:
    """I: an unpinned topic beside a sound pin is not a finding."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        data = _write_source(root, "docs/one.md", b"original bytes\n")
        _write_topic(root, _topic("fresh-topic", owning={"path": "docs/one.md", "digest": _digest(data)}))
        _write_topic(root, _topic("unpinned-topic"))
        result = _run(root)
        _check(
            got=result.returncode,
            want=0,
            output=result.stdout + result.stderr,
            needle="1 pinned source(s) across 2 topic(s)",
        )


def test_j_malformed_topic() -> None:
    """J: an unparseable topic file fails with a named diagnostic."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        topics = root / "docs" / "knowledge" / "topics"
        topics.mkdir(parents=True, exist_ok=True)
        (topics / "broken.json").write_text("{ not json", encoding="utf-8")
        result = _run(root)
        _check(
            got=result.returncode,
            want=1,
            output=result.stdout + result.stderr,
            needle="malformed topic corpus — refused by the store's reader at broken.json",
        )


def test_k_unknown_digest_kind() -> None:
    """K: a digest kind no schema admits fails as malformed."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        data = _write_source(root, "docs/one.md", b"original bytes\n")
        sound = _digest(data)
        foreign = dict(sound)
        foreign["kind"] = "md5-bytes-v0"  # admitted by no schema version
        _write_topic(
            root,
            _topic(
                "foreign-kind",
                owning={"path": "docs/one.md", "digest": foreign},
                supporting=[{"path": "docs/one.md", "digest": sound}],
            ),
        )
        result = _run(root)
        _check(
            got=result.returncode,
            want=1,
            output=result.stdout + result.stderr,
            needle="malformed topic",
        )


def _malformed_case(source: dict[str, object] | None, *, supporting: object = None) -> None:
    """Assert a topic carrying *source* fails as malformed beside one sound pin.

    The sound pin matters: without it the zero-pin refusal would also exit 1,
    and the case would pass for a reason that has nothing to do with the
    malformed source.
    """
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        data = _write_source(root, "docs/sound.md", b"sound bytes\n")
        _write_topic(
            root, _topic("sound-topic", owning={"path": "docs/sound.md", "digest": _digest(data)})
        )
        broken = _topic("broken-topic", owning=source)
        if supporting is not None:
            broken["supporting_sources"] = supporting
        _write_topic(root, broken)
        result = _run(root, "--max-stale", "99")
        _check(
            got=result.returncode,
            want=1,
            output=result.stdout + result.stderr,
            needle="broken-topic.json",
        )
        assert "Traceback" not in result.stderr, f"crashed instead of refusing\n{result.stderr}"


def test_l_git_blob_kind_is_named_not_unknown() -> None:
    """L: a schema-valid git-blob-v1 pin is unresolved under its own named reason."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        data = _write_source(root, "docs/one.md", b"original bytes\n")
        blob = {"kind": "git-blob-v1", "algorithm": "sha1", "object_id": "a" * 40}
        _write_topic(
            root,
            _topic(
                "blob-pinned",
                owning={"path": "docs/one.md", "digest": blob},
                supporting=[{"path": "docs/one.md", "digest": _digest(data)}],
            ),
        )
        result = _run(root, "--max-stale", "99")
        output = result.stdout + result.stderr
        _check(got=result.returncode, want=1, output=output, needle="is schema-valid but")
        assert "unknown" not in output, f"git-blob-v1 labelled unknown\n{output}"


def test_m_missing_digest_is_malformed() -> None:
    """M: a source with no digest key fails instead of being skipped."""
    _malformed_case({"path": "docs/sound.md"})


def test_n_string_digest_is_malformed() -> None:
    """N: a digest written as a string fails as malformed."""
    _malformed_case({"path": "docs/sound.md", "digest": "deadbeef"})


def test_o_supporting_sources_object_is_malformed() -> None:
    """O: supporting_sources written as an object fails as malformed."""
    _malformed_case(None, supporting={"path": "docs/sound.md"})


def test_p_null_byte_length_is_malformed() -> None:
    """P: a null byte_length fails as malformed rather than tracebacking."""
    digest = _digest(b"sound bytes\n")
    digest["byte_length"] = None
    _malformed_case({"path": "docs/sound.md", "digest": digest})


def test_q_malformed_under_json_still_emits_json() -> None:
    """Q: --json exits 1 on a malformed pin and still emits a JSON error object."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        _write_topic(root, _topic("broken-topic", owning={"path": "docs/x.md", "digest": "x"}))
        result = _run(root, "--json")
        assert result.returncode == 1, f"exit {result.returncode}\n{result.stderr}"
        payload = json.loads(result.stdout)
        assert payload.get("exit_code") == 1, payload
        assert "broken-topic.json" in payload.get("error", ""), payload


def test_r_extra_source_key_is_malformed() -> None:
    """R: a source carrying a key beyond path and digest fails as malformed."""
    digest = _digest(b"sound bytes\n")
    _malformed_case({"path": "docs/sound.md", "digest": digest, "extra": 1})


def test_s_dot_segment_path_is_malformed() -> None:
    """S: a non-canonical ./ path fails as malformed rather than being folded away."""
    _malformed_case({"path": "./docs/sound.md", "digest": _digest(b"sound bytes\n")})


def test_t_validator_crash_still_reports_malformed() -> None:
    """T: a shape the writer's validator crashes on is still a named malformed topic."""
    blob = {"kind": "git-blob-v1", "algorithm": [], "object_id": "x"}
    _malformed_case({"path": "docs/sound.md", "digest": blob})
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        _write_topic(root, _topic("broken-topic", owning={"path": "docs/x.md", "digest": blob}))
        result = _run(root, "--json")
        assert result.returncode == 1, f"exit {result.returncode}\n{result.stderr}"
        assert "Traceback" not in result.stderr, f"crashed\n{result.stderr}"
        payload = json.loads(result.stdout)
        assert "malformed topic" in payload.get("error", ""), payload


def test_u_bool_byte_length_matches_the_writer() -> None:
    """U: a bool byte_length the writer accepts is not refused as malformed."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        _write_source(root, "docs/one.md", b"original bytes\n")
        digest = _digest(b"original bytes\n")
        digest["byte_length"] = True
        _write_topic(root, _topic("bool-length", owning={"path": "docs/one.md", "digest": digest}))
        result = _run(root, "--max-stale", "99")
        output = result.stdout + result.stderr
        _check(got=result.returncode, want=0, output=output, needle="1 stale, within")
        assert "malformed" not in output, f"stricter than the writer\n{output}"


def test_v_nested_topic_pin_is_checked() -> None:
    """V: a stale pin only in a nested topic fails the run."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        data = _write_source(root, "docs/sound.md", b"sound bytes\n")
        _write_topic(
            root, _topic("sound-topic", owning={"path": "docs/sound.md", "digest": _digest(data)})
        )
        _write_source(root, "docs/nested.md", b"edited after pinning\n")
        _write_topic(
            root,
            _topic(
                "area/nested",
                owning={"path": "docs/nested.md", "digest": _digest(b"as pinned\n")},
            ),
        )
        result = _run(root)
        _check(
            got=result.returncode,
            want=1,
            output=result.stdout + result.stderr,
            needle="area/nested owning_source pin is stale",
        )


def test_w_key_path_mismatch_is_malformed() -> None:
    """W: a topic_key that does not match its file path fails and names the file."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        data = _write_source(root, "docs/sound.md", b"sound bytes\n")
        topic = _topic("other-key", owning={"path": "docs/sound.md", "digest": _digest(data)})
        target = root / "docs" / "knowledge" / "topics" / "misplaced.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(topic, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result = _run(root, "--max-stale", "99")
        _check(
            got=result.returncode,
            want=1,
            output=result.stdout + result.stderr,
            needle="misplaced.json (topic_key does not match its path)",
        )


def test_x_duplicate_json_key_is_malformed() -> None:
    """X: a duplicated JSON key fails as malformed instead of last-key-wins."""
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw).resolve()
        data = _write_source(root, "docs/sound.md", b"sound bytes\n")
        topic = _topic("dup-key", owning={"path": "docs/sound.md", "digest": _digest(data)})
        body = json.dumps(topic, indent=2, sort_keys=True)
        # A second "title" after the first: json.loads would keep this one silently.
        body = body.replace('"title":', '"title": "shadowed",\n  "title":', 1)
        target = root / "docs" / "knowledge" / "topics" / "dup-key.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body + "\n", encoding="utf-8")
        result = _run(root, "--max-stale", "99")
        _check(
            got=result.returncode,
            want=1,
            output=result.stdout + result.stderr,
            needle="refused by the store's reader at dup-key.json",
        )


def main() -> int:
    """Run every case through the shared harness and return its exit status."""
    cases = (
        test_a_all_fresh,
        test_b_content_drift,
        test_c_length_drift,
        test_d_supporting_drift,
        test_e_within_baseline,
        test_f_above_baseline,
        test_g_unresolved_ignores_baseline,
        test_h_zero_pins_refuses,
        test_i_unpinned_topic_is_not_a_finding,
        test_j_malformed_topic,
        test_k_unknown_digest_kind,
        test_l_git_blob_kind_is_named_not_unknown,
        test_m_missing_digest_is_malformed,
        test_n_string_digest_is_malformed,
        test_o_supporting_sources_object_is_malformed,
        test_p_null_byte_length_is_malformed,
        test_q_malformed_under_json_still_emits_json,
        test_r_extra_source_key_is_malformed,
        test_s_dot_segment_path_is_malformed,
        test_t_validator_crash_still_reports_malformed,
        test_u_bool_byte_length_matches_the_writer,
        test_v_nested_topic_pin_is_checked,
        test_w_key_path_mismatch_is_malformed,
        test_x_duplicate_json_key_is_malformed,
    )
    return selftest_harness.run_cases(
        {case.__name__: case for case in cases}, _LABEL
    )


if __name__ == "__main__":
    sys.exit(main())
