"""Fixture builders for the per-record quarantine and write-path suites.

Builds disposable knowledge repositories and introduces invalid committed
records the way a Git merge would: by editing committed bytes directly, beside
valid records, without going through any writer.  Standard library only; no
runner collects this file.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from knowledge_test_support import initialize_empty_v1_repo, valid_capture_request

SOURCE = "contracts/jsonschema/knowledge-captured-observation.schema.json"
TOPIC_KEY = "contracts/public-contracts"
QUERY: dict[str, Any] = {
    "task_summary": "Choose the right project-knowledge contract handoff.",
    "scope": "packs/core",
    "question": "Which contract should workflow handoff use?",
    "caller": "human",
    "risk": "routine",
}
_RECORD_LINE = re.compile(
    r'^<record reason="[a-z_]+"(?: (?:path|line|entry|ordinal|omitted)="[^"<>]*")*/>$'
)


def git(repo: Path, *args: str) -> None:
    """Run one git command in *repo*."""
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def commit(repo: Path, message: str = "test: commit") -> None:
    """Commit everything under docs/ and contracts/ (including hostile file names)."""
    git(repo, "add", "-A", "docs", "contracts")
    git(repo, "commit", "--allow-empty", "-m", message)


def knowledge_repo(base: Path, store: Any) -> Path:
    """Return an empty committed v1 repository with a source file and gate artifacts."""
    repo = initialize_empty_v1_repo(base, store)
    source = repo / SOURCE
    source.parent.mkdir(parents=True)
    source.write_text('{"schema":"v1"}\n', encoding="utf-8")
    skill = repo / "packs/core/.apm/skills/work-loop/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("capture through the public seam\n", encoding="utf-8")
    spec_dir = repo / "docs" / "specs" / "example"
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_bytes(b"# Governing spec\n")
    (spec_dir / "plan.md").write_bytes(b"# Governing plan\n")
    return repo


def request(**overrides: Any) -> dict[str, Any]:
    """Return a valid capture request observed on a fixed date."""
    body = valid_capture_request()
    body["observed_at"] = "2026-08-13T12:34:56Z"
    body.update(overrides)
    return body


def capture(repo: Path, store: Any, lesson: str, **overrides: Any) -> dict[str, Any]:
    """Capture one valid observation and return its receipt."""
    return store.capture_observation(
        repo, request(lesson=lesson, **overrides), writer_time="2026-08-13T12:40:00Z"
    )


def journal(repo: Path, partition: str) -> Path:
    """Return the journal file for *partition*."""
    return repo / "docs" / "knowledge" / partition


def append_line(repo: Path, partition: str, line: bytes) -> None:
    """Append one raw line to a partition, as a merge would."""
    path = journal(repo, partition)
    path.write_bytes(path.read_bytes() + line + b"\n")


def event_lines(repo: Path, partition: str) -> list[dict[str, Any]]:
    """Return the parsed events of a partition."""
    return [json.loads(line) for line in journal(repo, partition).read_bytes().splitlines()]


def tampered_capture(line: dict[str, Any], kind: str) -> dict[str, Any]:
    """Return a captured-event line made invalid in the named way (still typed as captured)."""
    event = json.loads(json.dumps(line))
    if kind == "extra-field":
        event["extra"] = 1
    elif kind == "privacy-lesson":
        event["request"]["lesson"] = "Write to someone@example.com for details."
    elif kind == "unknown-request-version":
        event["request"]["contract_version"] = "knowledge-captured-observation.v9"
    elif kind == "unknown-event-version":
        event["schema_version"] = "observation-event.v9"
    elif kind == "identity-mismatch":
        event["request"]["lesson"] = "tampered after identity derivation"
        event["capture_id"] = "kco-202608-" + "d" * 64
    else:
        raise AssertionError(kind)
    return event


def dumps(value: Any) -> bytes:
    """Serialize an event the way the journal does."""
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def disposition_line(
    capture_id: str, partition: str, disposition: str, **overrides: Any
) -> dict[str, Any]:
    """Return a valid terminal disposition event."""
    event: dict[str, Any] = {
        "event_type": "observation.dispositioned",
        "schema_version": "observation-event.v1",
        "capture_id": capture_id,
        "partition": partition,
        "disposition": disposition,
        "reason_code": "not_reusable",
        "recorded_at": "2026-08-13T12:41:00Z",
    }
    event.update(overrides)
    return event


def topic(store: Any, repo: Path, **overrides: Any) -> dict[str, Any]:
    """Return a valid topic owned by the fixture source file."""
    digest = store.PK.digest_bytes((repo / SOURCE).read_bytes())
    body: dict[str, Any] = {
        "schema_version": "knowledge-topic.v1",
        "topic_key": TOPIC_KEY,
        "title": "Public contracts are the durable handoff",
        "synthesis": {
            "kind": "pattern",
            "body": "Prefer the repo-owned contract before adding a local format.",
        },
        "scopes": ["packs/core"],
        "competency_facets": ["CQ-DESIGN", "CQ-VERIFY"],
        "audience": "project",
        "lifecycle": "active",
        "freshness": {"state": "fresh", "checked_at": "2026-08-13T12:40:00Z"},
        "owning_source": {"path": SOURCE, "digest": digest},
        "supporting_sources": [],
        "occurrences": [
            {
                "capture_id": "kco-202608-" + "b" * 64,
                "mutation_id": "0" * 64,
                "producer": "work-loop",
                "semantic_gate": "verified-slice",
                "source": {"path": "packs/core/.apm/skills/work-loop/SKILL.md"},
                "evidence_digest": {
                    "kind": "sha256-bytes-v1",
                    "sha256": "c" * 64,
                    "byte_length": 42,
                },
                "scope": "packs/core",
                "observed_at": "2026-08-13T12:34:56Z",
                "reviewed_disposition": "promoted",
            }
        ],
    }
    body.update(overrides)
    return body


def publish(store: Any, repo: Path, *topics: dict[str, Any]) -> None:
    """Write topics, rebuild the map, and commit them."""
    for item in topics:
        store.write_topic(repo, item)
    store.rebuild_topic_map(repo)
    commit(repo, "test: publish knowledge")


def map_path(repo: Path) -> Path:
    """Return the topic map path."""
    return repo / "docs" / "knowledge" / "topics.index.json"


def read_map(repo: Path) -> dict[str, Any]:
    """Return the parsed topic map."""
    return json.loads(map_path(repo).read_text(encoding="utf-8"))


def write_map(repo: Path, topic_map: dict[str, Any]) -> None:
    """Write the topic map in its canonical pretty form."""
    text = json.dumps(topic_map, indent=2, sort_keys=True) + "\n"
    map_path(repo).write_text(text, encoding="utf-8")


def blob(store: Any, repo: Path, raw: bytes) -> dict[str, Any]:
    """Return the git blob digest the map records for *raw*."""
    return store._git_blob_digest(raw, algorithm=store._git_object_algorithm(repo))


def replace_topic_bytes(store: Any, repo: Path, key: str, raw: bytes) -> None:
    """Replace a committed topic's bytes and keep its map entry's blob digest consistent."""
    store.topic_path_for_key(repo, key).write_bytes(raw)
    topic_map = read_map(repo)
    for entry in topic_map["entries"]:
        if entry["topic_key"] == key:
            entry["blob"] = blob(store, repo, raw)
    write_map(repo, topic_map)
    commit(repo, "test: replace topic bytes")


def map_entry(store: Any, repo: Path, relative: str, raw: bytes, key: str) -> dict[str, Any]:
    """Return a shape-valid map entry for a hand-placed topic file."""
    return {
        "topic_key": key,
        "title": "Hand placed topic",
        "path": relative,
        "scopes": ["packs/core"],
        "competency_facets": ["CQ-DESIGN"],
        "audience": "project",
        "lifecycle": "active",
        "freshness": {"state": "fresh", "checked_at": "2026-08-13T12:40:00Z"},
        "blob": blob(store, repo, raw),
    }


def promotion(store: Any, receipt: dict[str, Any], source: Path) -> dict[str, Any]:
    """Return a complete promotion proposal for *receipt*."""
    digest = store.PK.digest_bytes(source.read_bytes())
    proposal = {
        "schema_version": "knowledge-distillation-proposal.v1",
        "capture_id": receipt["capture_id"],
        "disposition": "promoted",
        "reason_code": "promoted_to_topic",
        "recorded_at": "2026-08-13T12:41:00Z",
        "candidate_topic_keys": [TOPIC_KEY],
        "named_sources": [SOURCE],
        "mutation": {
            "schema_version": "knowledge-mutation-proposal.v1",
            "capture_id": receipt["capture_id"],
            "topic_key": TOPIC_KEY,
            "title": "Public contracts are the durable handoff",
            "synthesis": {
                "kind": "pattern",
                "body": "Prefer the repo-owned contract before adding a local format.",
            },
            "scopes": ["packs/core"],
            "competency_facets": ["CQ-DESIGN", "CQ-VERIFY"],
            "owning_source": {"path": SOURCE, "digest": digest},
            "supporting_sources": [],
            "occurrence": {
                "producer": "work-loop",
                "semantic_gate": "verified-slice",
                "source": {"path": "packs/core/.apm/skills/work-loop/SKILL.md"},
                "evidence_digest": digest,
                "scope": "packs/core",
                "observed_at": "2026-08-13T12:34:56Z",
            },
            "terminal_disposition": {
                "disposition": "promoted",
                "reason_code": "promoted_to_topic",
                "recorded_at": "2026-08-13T12:41:00Z",
            },
            "expected_topic_digest": None,
        },
    }
    proposal["mutation"] = store.complete_mutation_proposal(proposal["mutation"])
    return proposal


def knowledge_files(repo: Path) -> dict[str, bytes]:
    """Return every file under docs/knowledge (except staging), keyed by relative path."""
    root = repo / "docs" / "knowledge"
    return {
        path.relative_to(repo).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".migration-stage" not in path.parts and not path.is_symlink()
    }


def evidence_part(rendered: str) -> str:
    """Return the `knowledge-evidence.v1` element of an enquiry's rendered text."""
    return rendered.split("\n<knowledge-quarantine", 1)[0]


def assert_inert_quarantine(rendered: str, entries: list[dict[str, Any]]) -> None:
    """Assert the quarantine element is one inert block after exactly one evidence element."""
    evidence, separator, tail = rendered.partition("\n<knowledge-quarantine")
    assert separator, "no quarantine element"
    assert evidence.count("<knowledge-evidence ") == 1
    assert evidence.count("</knowledge-evidence>") == 1
    assert evidence.endswith("</knowledge-evidence>")
    lines = ("<knowledge-quarantine" + tail).split("\n")
    assert lines[0] == '<knowledge-quarantine version="knowledge-quarantine.v1">'
    assert lines[1] == "Excluded records by location and reason only; no record content."
    assert lines[-1] == "</knowledge-quarantine>"
    assert len(lines) == len(entries) + 3
    assert all(_RECORD_LINE.match(line) for line in lines[2:-1]), lines
