"""Contract suite for the read-only delivery fact feed (Slice 3, task T1).

Covers AC-0001, AC-0002, AC-0010, AC-0012 of delivery-knowledge-projection:
complete and paged scans, torn and corrupt frames, supersession, snapshot
refusal, and log byte-identity.  Fixtures are built with the shipped Slice 1
and Slice 2 writers, in temporary repositories.

Mode: TDD through contract and integration tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType
from typing import Any

import delivery_feed_support as dfs
import pytest

ENABLED = {"WORK_LOOP_SHADOW_SERVICES": "1"}
FINGERPRINT_PREFIX = "acceptance-fp-"


@pytest.fixture(scope="module")
def feed() -> ModuleType:
    """The feed module, loaded by path under a unique name."""
    return dfs.load_script("dfp_contract_feed", "_delivery_feed.py")


@pytest.fixture
def repo(tmp_path: Path) -> dfs.FeedRepo:
    """A temporary repository with the shipped writers loaded."""
    return dfs.FeedRepo(tmp_path)


def scan(feed: ModuleType, root: Path, **kwargs: Any) -> tuple[list[dict], list[dict]]:
    """Follow every continuation; return (pages, entries)."""
    pages: list[dict] = []
    token: str | None = None
    while True:
        page = feed.feed_page(root, continuation=token, environ=ENABLED, **kwargs)
        pages.append(page)
        token = page["continuation"]
        if token is None:
            break
    return pages, [entry for page in pages for entry in page["entries"]]


def observations(entries: list[dict]) -> list[dict]:
    """Return the observations among *entries*."""
    return [e["observation"] for e in entries if e["entry_kind"] == "fact" and e["observation"]]


def none_reasons(entries: list[dict]) -> list[str]:
    """Return the none reasons among *entries*, in order."""
    return [e["none_reason"] for e in entries if e["entry_kind"] == "fact" and e["none_reason"]]


# ── AC-0001 / AC-0002: complete scan and projection ──────────────────────────


def test_complete_scan_projects_each_current_review_failure_receipt(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    """One gotcha per receipt, carrying both fingerprints; everything else is an explicit none."""
    store = repo.open_store("alpha")
    repo.add_engine_transition("alpha", store)
    receipt_ids = repo.add_review_failure("alpha", store, "one", criteria=("AC-0014", "AC-0015"))
    _, entries = scan(feed, repo.root)

    found = observations(entries)
    assert [o["source"]["receipt_id"] for o in found] == receipt_ids
    for obs in found:
        assert obs["kind"] == "gotcha"
        assert obs["source"]["spec_path"] == "docs/specs/alpha"
        assert obs["source"]["acceptance_fingerprint"] == FINGERPRINT_PREFIX + "alpha"
        assert obs["source"]["review_policy_fingerprint"] == "review-policy-one"
        assert obs["source"]["report_id"] == "report-one"
        assert obs["observed"]["field_path"] == "observed"
        assert obs["scope_paths"] == ["packs/core/example/module.py"]
    reasons = none_reasons(entries)
    assert "ineligible-receipt" in reasons  # the engine-transition receipt
    assert "ineligible-record-kind" in reasons  # report, assessment, subject records
    assert [e["ordinal"] for e in entries] == list(range(len(entries)))


def test_torn_final_frame_is_invisible_and_left_unrepaired(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    """AC-0001: a torn tail exposes no record, is not a refusal, and is not truncated."""
    store = repo.open_store("alpha")
    receipt_ids = repo.add_review_failure("alpha", store, "one")
    _, before = scan(feed, repo.root)
    with repo.log_path("alpha").open("ab") as handle:
        handle.write(b'{"tx":{"schema_version":1,"transaction_id":"tx-torn"')
    torn_bytes = repo.log_bytes("alpha")

    _, after = scan(feed, repo.root)

    assert [e for e in after if e["entry_kind"] == "unread-source"] == []
    assert after == [dict(e) for e in before]
    assert [o["source"]["receipt_id"] for o in observations(after)] == receipt_ids
    assert repo.log_bytes("alpha") == torn_bytes


def test_superseded_review_failure_receipt_yields_no_candidate(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    """AC-0002 and AC-0010: a receipt a supersession names is an explicit none."""
    store = repo.open_store("alpha")
    repo.add_review_failure("alpha", store, "gone")
    kept = repo.add_review_failure("alpha", store, "kept")
    repo.supersede_by_assessment("alpha", store, "gone")

    _, entries = scan(feed, repo.root)

    assert [o["source"]["receipt_id"] for o in observations(entries)] == kept
    assert none_reasons(entries).count("superseded") == 1


def test_subject_changed_but_unsuperseded_receipt_stays_eligible(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    """The feed never judges freshness: a later report on another subject hides nothing."""
    store = repo.open_store("alpha")
    first = repo.add_review_failure("alpha", store, "old", policy_fingerprint="review-policy-v1")
    second = repo.add_review_failure("alpha", store, "new", policy_fingerprint="review-policy-v2")

    _, entries = scan(feed, repo.root)

    found = {o["source"]["receipt_id"]: o for o in observations(entries)}
    assert set(found) == set(first) | set(second)
    assert found[first[0]]["source"]["review_policy_fingerprint"] == "review-policy-v1"
    assert found[second[0]]["source"]["review_policy_fingerprint"] == "review-policy-v2"
    assert found[first[0]]["source"]["acceptance_fingerprint"] == FINGERPRINT_PREFIX + "alpha"


@pytest.mark.parametrize("how", ["report", "invalidation"])
def test_report_replacement_and_source_invalidation_supersede_the_receipt(
    feed: ModuleType, repo: dfs.FeedRepo, how: str
) -> None:
    """AC-0010: once Slice 2 supersedes the receipt, the next scan presents no candidate."""
    store = repo.open_store("alpha")
    repo.add_review_failure("alpha", store, "gone")
    _, before = scan(feed, repo.root)
    assert len(observations(before)) == 1

    if how == "report":
        repo.supersede_by_report_replacement("alpha", store, "gone")
    else:
        repo.supersede_by_source_invalidation("alpha", store, "gone")

    _, after = scan(feed, repo.root)
    assert observations(after) == []
    assert none_reasons(after).count("superseded") == 1


def test_identity_is_one_candidate_per_source_and_stable_across_rescans(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    """AC-0010: the same facts yield the same identities and bytes on every scan."""
    store = repo.open_store("alpha")
    repo.add_review_failure("alpha", store, "one", criteria=("AC-0014", "AC-0015"))
    first = scan(feed, repo.root)[1]
    second = scan(feed, repo.root)[1]
    assert first == second
    ids = [o["observation_id"] for o in observations(first)]
    assert len(ids) == len(set(ids)) == 2


def test_absent_log_and_disabled_shadow_dir_contribute_nothing(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    """AC-0010: a source without a log yields no entry and no candidate."""
    repo.spec_dir("no-shadow")
    repo.ensure_shadow("marker-only")
    pages, entries = scan(feed, repo.root)
    assert entries == []
    assert pages[0]["continuation"] is None


def test_unset_shadow_flag_returns_complete_empty_snapshot_without_listing(
    feed: ModuleType, repo: dfs.FeedRepo, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-0012: flag unset means an empty snapshot and no listing or read."""
    store = repo.open_store("alpha")
    repo.add_review_failure("alpha", store, "one")
    fs = feed._file_safety()
    for name in ("list_confined_directories", "validate_confined_directory",
                 "read_confined_regular_file"):
        monkeypatch.setattr(fs, name, lambda *a, **k: pytest.fail("filesystem touched"))
    for env in ({}, {"WORK_LOOP_SHADOW_SERVICES": ""}, {"WORK_LOOP_SHADOW_SERVICES": "0"},
                {"WORK_LOOP_SHADOW_SERVICES": "true"}):
        page = feed.feed_page(repo.root / "does-not-exist", environ=env)
        assert page["entries"] == [] and page["continuation"] is None
        assert page["shadow_services"] == "disabled"


def test_flag_semantics_match_the_shadow_facade(feed: ModuleType) -> None:
    """The feed reads the same opt-in the facade writes under."""
    facade = dfs.load_script("dfp_contract_facade", "_compat_facade.py")
    assert feed.SHADOW_ENV_VAR == facade.SHADOW_ENV_VAR
    assert feed._MARKER_BYTES == b"*\n"
    assert feed._SHADOW_SUBDIR == facade.SHADOW_SUBDIR
    assert feed._EVIDENCE_LOG == facade._EVIDENCE_LOG


# ── AC-0001: bounds, paging, snapshot ────────────────────────────────────────


def test_pages_end_before_the_entry_that_would_exceed_the_entry_bound(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    """More than 1,000 facts page at exactly 1,000 with nothing dropped or repeated."""
    store = repo.open_store("alpha")
    for _ in range(1005):
        repo.add_engine_transition("alpha", store)
    pages, entries = scan(feed, repo.root)
    assert [len(p["entries"]) for p in pages] == [1000, 5]
    assert [e["ordinal"] for e in entries] == list(range(1005))
    assert pages[1]["first_ordinal"] == 1000
    assert pages[0]["snapshot_id"] == pages[1]["snapshot_id"]


def test_pages_end_before_the_entry_that_would_exceed_the_byte_bound(
    feed: ModuleType, repo: dfs.FeedRepo, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The page byte bound is exact: one byte less moves the last entry to the next page."""
    store = repo.open_store("alpha")
    for _ in range(6):
        repo.add_engine_transition("alpha", store)
    monkeypatch.setattr(feed, "MAX_ENTRIES", 3)
    sizes = [len(feed.render_page(p)) for p in scan(feed, repo.root)[0]]
    assert len(sizes) == 2
    exact = sizes[0]
    monkeypatch.setattr(feed, "MAX_PAGE_BYTES", exact)
    pages, entries = scan(feed, repo.root)
    assert [len(p["entries"]) for p in pages] == [3, 3]
    assert all(len(feed.render_page(p)) <= exact for p in pages)
    monkeypatch.setattr(feed, "MAX_PAGE_BYTES", exact - 1)
    pages, entries = scan(feed, repo.root)
    assert [len(p["entries"]) for p in pages][0] == 2
    assert all(len(feed.render_page(p)) <= exact - 1 for p in pages)
    assert [e["ordinal"] for e in entries] == list(range(6))


def _two_page_repo(feed: ModuleType, repo: dfs.FeedRepo) -> dict:
    """Two specs, three facts each, so a 2-entry page leaves later logs unread."""
    for slug in ("alpha", "beta"):
        store = repo.open_store(slug)
        for _ in range(3):
            repo.add_engine_transition(slug, store)
    return {}


def _first_page(feed: ModuleType, repo: dfs.FeedRepo, monkeypatch: pytest.MonkeyPatch) -> dict:
    monkeypatch.setattr(feed, "MAX_ENTRIES", 2)
    page = feed.feed_page(repo.root, environ=ENABLED)
    assert page["continuation"] is not None
    return page


@pytest.mark.parametrize(
    "mutate",
    ["append-unread-log", "append-read-log", "add-spec", "remove-spec", "flip-read-prefix"],
)
def test_continuation_refuses_a_changed_snapshot_without_a_partial_result(
    feed: ModuleType, repo: dfs.FeedRepo, monkeypatch: pytest.MonkeyPatch, mutate: str
) -> None:
    """AC-0001: any difference refuses the continuation; no page is returned."""
    _two_page_repo(feed, repo)
    page = _first_page(feed, repo, monkeypatch)
    if mutate == "append-unread-log":
        repo.add_engine_transition("beta", repo.open_store("beta"))
    elif mutate == "append-read-log":
        repo.add_engine_transition("alpha", repo.open_store("alpha"))
    elif mutate == "add-spec":
        repo.spec_dir("gamma")
    elif mutate == "remove-spec":
        (repo.log_path("beta")).unlink()
        (repo.shadow_dir("beta") / ".gitignore").unlink()
        repo.shadow_dir("beta").rmdir()
        repo.spec_dir("beta").rmdir()
    else:
        data = bytearray(repo.log_bytes("alpha"))
        data[40] ^= 0x01  # same length, different prefix
        repo.log_path("alpha").write_bytes(bytes(data))
    with pytest.raises(feed.ScanRefused) as caught:
        feed.feed_page(repo.root, continuation=page["continuation"], environ=ENABLED)
    assert caught.value.code == "snapshot-changed"


def test_completing_a_torn_frame_between_pages_changes_the_snapshot(
    feed: ModuleType, repo: dfs.FeedRepo, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The digest covers the torn tail, so a writer finishing it refuses the continuation."""
    _two_page_repo(feed, repo)
    with repo.log_path("beta").open("ab") as handle:
        handle.write(b'{"tx":')
    page = _first_page(feed, repo, monkeypatch)
    with repo.log_path("beta").open("ab") as handle:
        handle.write(b'"x"}}\n')
    with pytest.raises(feed.ScanRefused) as caught:
        feed.feed_page(repo.root, continuation=page["continuation"], environ=ENABLED)
    assert caught.value.code == "snapshot-changed"


@pytest.mark.parametrize(
    "token",
    ["", "dff1", "dff1." + "0" * 64, "dff1." + "0" * 64 + ".x", "dff2." + "0" * 64 + ".1",
     "dff1." + "0" * 64 + ".1\n", "dff1." + "A" * 64 + ".1", "dff1." + "0" * 64 + ".1" + "0" * 10],
)
def test_malformed_continuation_tokens_are_refused(
    feed: ModuleType, repo: dfs.FeedRepo, token: str
) -> None:
    """The token grammar is strict, including a trailing newline."""
    repo.open_store("alpha")
    with pytest.raises(feed.ScanRefused) as caught:
        feed.feed_page(repo.root, continuation=token, environ=ENABLED)
    assert caught.value.code == "token-invalid"


def test_forged_position_in_a_valid_snapshot_is_refused(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    """A token for the right snapshot but a position past the end is refused."""
    store = repo.open_store("alpha")
    repo.add_engine_transition("alpha", store)
    snapshot = feed.feed_page(repo.root, environ=ENABLED)["snapshot_id"].rsplit("-", 1)[1]
    with pytest.raises(feed.ScanRefused) as caught:
        feed.feed_page(repo.root, continuation=f"dff1.{snapshot}.5", environ=ENABLED)
    assert caught.value.code == "token-invalid"


# ── Admission parity with the store's replay ─────────────────────────────────


def _frames(raw: bytes) -> list[bytes]:
    return [line + b"\n" for line in raw.split(b"\n") if line]


def test_a_frame_reusing_an_admitted_identity_is_skipped_first_wins(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    """The feed admits what the store's replay admits: a repeated frame adds nothing."""
    store = repo.open_store("alpha")
    receipt_ids = repo.add_review_failure("alpha", store, "one")
    _, once = scan(feed, repo.root)
    raw = repo.log_bytes("alpha")
    repo.log_path("alpha").write_bytes(raw + _frames(raw)[-1] + _frames(raw)[0])
    _, twice = scan(feed, repo.root)
    assert twice == once
    assert [o["source"]["receipt_id"] for o in observations(twice)] == receipt_ids


def test_feed_admission_matches_the_stores_own_open(
    feed: ModuleType, repo: dfs.FeedRepo, tmp_path: Path
) -> None:
    """Cross-check: records the feed lists equal the records a reopened store indexes."""
    store = repo.open_store("alpha")
    repo.add_engine_transition("alpha", store)
    repo.add_review_failure("alpha", store, "one", criteria=("AC-0014", "AC-0015"))
    repo.add_review_failure("alpha", store, "two")
    repo.supersede_by_assessment("alpha", store, "two")
    reopened = repo.es.EvidenceStore(repo.log_path("alpha"))
    reopened.open()
    _, entries = scan(feed, repo.root)
    listed_receipts = {
        e["source"]["record_id"] for e in entries
        if e["entry_kind"] == "fact" and e["source"]["record_kind"] == "evidence-receipt.v1"
    }
    active = {r["receipt_id"] for r in reopened.get_all_active_receipts()}
    eligible = {o["source"]["receipt_id"] for o in observations(entries)}
    assert eligible <= active
    assert len(listed_receipts) == reopened.receipt_count
    # Every active bridge receipt is a candidate; every engine receipt is an explicit none.
    assert len(eligible) == 2
    assert len(active) - len(eligible) == 1


def _recompute_checksum(es: ModuleType, frame: dict) -> dict:
    tx = {k: v for k, v in frame["tx"].items() if k != "checksum"}
    frame["tx"]["checksum"] = es._compute_frame_checksum(tx, frame["records"])
    return frame


def test_checksum_invalid_log_is_an_unread_source_and_other_logs_still_read(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    """AC-0013: a bad frame makes the whole log unread, with a closed reason."""
    bad = repo.open_store("alpha")
    repo.add_review_failure("alpha", bad, "one")
    good = repo.open_store("beta")
    kept = repo.add_review_failure("beta", good, "two")
    frames = _frames(repo.log_bytes("alpha"))
    frame = json.loads(frames[-1])
    frame["tx"]["checksum"] = "sha256:" + "0" * 64
    frames[-1] = (json.dumps(frame, sort_keys=True, separators=(",", ":")) + "\n").encode()
    repo.log_path("alpha").write_bytes(b"".join(frames))

    _, entries = scan(feed, repo.root)

    unread = [e for e in entries if e["entry_kind"] == "unread-source"]
    assert [(u["spec_path"], u["reason_code"]) for u in unread] == [
        ("docs/specs/alpha", "log-corrupt")
    ]
    assert [o["source"]["receipt_id"] for o in observations(entries)] == kept
    assert all(e["source"]["spec_path"] == "docs/specs/beta"
               for e in entries if e["entry_kind"] == "fact")


def test_unknown_transaction_version_makes_the_log_unread(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    """An unknown major is inadmissible even behind a recomputed checksum."""
    store = repo.open_store("alpha")
    repo.add_engine_transition("alpha", store)
    frame = json.loads(_frames(repo.log_bytes("alpha"))[0])
    frame["tx"]["schema_version"] = 2
    frame = _recompute_checksum(repo.es, frame)
    repo.log_path("alpha").write_bytes(
        (repo.es._canonical_json(frame) + "\n").encode("utf-8")
    )
    _, entries = scan(feed, repo.root)
    assert [e["reason_code"] for e in entries] == ["log-corrupt"]


def test_frame_with_a_record_kind_outside_the_registry_makes_the_log_unread(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    """Reviewed-envelope, plan, and task records are never admitted from a log."""
    store = repo.open_store("alpha")
    repo.add_engine_transition("alpha", store)
    frame = json.loads(_frames(repo.log_bytes("alpha"))[0])
    frame["records"] = [{"schema_version": 1, "envelope_fingerprint": "x", "refs": {}}]
    frame["tx"]["ordered_record_ids"] = ["x"]
    frame = _recompute_checksum(repo.es, frame)
    repo.log_path("alpha").write_bytes((repo.es._canonical_json(frame) + "\n").encode("utf-8"))
    _, entries = scan(feed, repo.root)
    assert [e["reason_code"] for e in entries] == ["log-corrupt"]


# ── Identifiers the feed cannot hold stay per record ─────────────────────────


def test_unrepresentable_identifiers_do_not_hide_the_logs_other_facts(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    """A finding id with a space or over the length limit costs only its own fact."""
    import hashlib
    import re
    import subprocess
    import sys

    store = repo.open_store("alpha")
    repo.add_engine_transition("alpha", store)
    repo.add_review_failure("alpha", store, "has space")
    repo.add_review_failure("alpha", store, "x" * 150)
    good = repo.add_review_failure("alpha", store, "good")

    _, entries = scan(feed, repo.root)

    assert not [e for e in entries if e["entry_kind"] == "unread-source"]
    assert [o["source"]["receipt_id"] for o in observations(entries)] == good
    identifier = re.compile(feed._projection().PATTERNS["identifier"])
    stand_ins = [
        e["source"]["record_id"]
        for e in entries
        if e["source"]["record_id"].startswith("digest-sha256:")
    ]
    assert len(stand_ins) >= 2
    # The records that carry a stand-in id are the report and assessment records, which
    # are never candidates; the two receipts built on the unrepresentable finding ids
    # are explicit `unrepresentable` nones, and only the good receipt is a candidate.
    standing_in = [
        e for e in entries if e["source"]["record_id"].startswith("digest-sha256:")
    ]
    assert standing_in
    assert {e["none_reason"] for e in standing_in} == {"ineligible-record-kind"}
    receipts = [e for e in entries if e["source"]["record_kind"] == "evidence-receipt.v1"]
    assert [e["none_reason"] for e in receipts if e["observation"] is None].count(
        "unrepresentable"
    ) == 2
    for entry in entries:
        assert identifier.search(entry["source"]["record_id"])
        assert identifier.search(entry["source"]["transaction_id"])
    # The stand-in is the SHA-256 of the UTF-8 id, so it is the same in any process.
    shown = {e["source"]["record_id"] for e in entries}
    for raw in _raw_ids(repo, "alpha", identifier):
        assert "digest-sha256:" + hashlib.sha256(raw).hexdigest() in shown
    script = Path(feed.__file__).with_name("delivery-fact-feed.py")
    outputs = [
        subprocess.run(
            [sys.executable, "-I", str(script), "--root", str(repo.root)],
            env={"WORK_LOOP_SHADOW_SERVICES": "1"},
            capture_output=True,
            check=True,
        ).stdout
        for _ in range(2)
    ]
    assert outputs[0] == outputs[1]
    assert json.loads(outputs[0])["entries"] == scan(feed, repo.root)[1]


def _raw_ids(repo: dfs.FeedRepo, slug: str, pattern: Any) -> list[bytes]:
    """Return the UTF-8 bytes of every record id in the log that *pattern* (the projector's) refuses."""
    found: list[bytes] = []
    for line in repo.log_bytes(slug).splitlines():
        frame = json.loads(line)
        for record in frame["records"]:
            record_id = repo.es._semantic_record_id(record)
            if not pattern.search(record_id):
                found.append(record_id.encode("utf-8"))
    return found


# ── An unexpected fault is a stage diagnostic, not a data fault ──────────────


def test_an_unexpected_replay_fault_is_not_reported_as_a_corrupt_log(
    feed: ModuleType, repo: dfs.FeedRepo, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only the store's own admission error makes a log unread; a code defect surfaces."""
    store = repo.open_store("alpha")
    repo.add_engine_transition("alpha", store)

    def defective(_raw: bytes) -> Any:
        raise RuntimeError("defect")

    monkeypatch.setattr(feed._evidence_store(), "replay_admitted_frames", defective)
    with pytest.raises(RuntimeError):
        feed.feed_page(repo.root, environ=ENABLED)


def test_the_command_names_the_stage_and_exception_class_of_an_unexpected_fault(
    repo: dfs.FeedRepo, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The closed refusal line is unchanged; a second line adds stage and class, no content."""
    cli = dfs.load_script("dfp_feed_cli", "delivery-fact-feed.py")

    class Stub:
        class ScanRefused(Exception):
            code = "unused"

        @staticmethod
        def feed_page(*_args: Any, **_kwargs: Any) -> Any:
            raise KeyError("secret-record-content")

    monkeypatch.setattr(cli, "_load_feed", lambda: Stub)

    assert cli.main(["--root", str(repo.root)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.splitlines() == [
        "delivery-fact-feed: refused: scan-failed",
        "delivery-fact-feed: scan-failed: scan: KeyError",
    ]
    assert "secret-record-content" not in captured.err


# ── Projection refusals reached through real logs ────────────────────────────


def test_oversized_and_unsafe_text_yield_explicit_nones(
    feed: ModuleType, repo: dfs.FeedRepo
) -> None:
    """AC-0002: an oversized, refused, or unrepresentable fact yields no observation."""
    store = repo.open_store("alpha")
    repo.add_review_failure("alpha", store, "long", finding_text={"observation": "x " * 400})
    repo.add_review_failure("alpha", store, "many", evidence_refs=tuple(
        f"packs/core/example/{'d' * 180}/{i}.py" for i in range(10)
    ), finding_text={
        "observation": "a" * 590, "reachable_path": "b" * 590, "actual_failure": "c" * 590,
    })
    repo.add_review_failure("alpha", store, "bidi", finding_text={"observation": "evil ‮ text"})
    repo.add_review_failure("alpha", store, "ok", finding_text={"observation": "line one\n\tline two"})

    _, entries = scan(feed, repo.root)

    reasons = none_reasons(entries)
    assert reasons.count("oversized") == 2
    assert reasons.count("unrepresentable") == 1  # bidi override
    found = observations(entries)
    assert [o["source"]["report_id"] for o in found] == ["report-ok"]
    assert found[0]["observed"]["value"] == "line one line two"
    assert all(len(json.dumps(o, separators=(",", ":"))) <= 4096 for o in found)


def test_content_policy_refusal_yields_an_explicit_none(
    feed: ModuleType, repo: dfs.FeedRepo, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The knowledge-observation profile runs before a candidate leaves the feed."""
    store = repo.open_store("alpha")
    repo.add_review_failure("alpha", store, "one")
    profiles = feed._projection()._content_safety().BOUNDARY_PROFILES
    monkeypatch.setitem(profiles, "knowledge-observation", {"max_bytes": 40})
    _, entries = scan(feed, repo.root)
    assert observations(entries) == []
    assert none_reasons(entries).count("content-refused") == 1


# ── Byte identity and the read-only contract ─────────────────────────────────


def test_a_scan_leaves_every_log_byte_identical_and_never_opens_the_store(
    feed: ModuleType, repo: dfs.FeedRepo, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-0001: logs, torn tails, markers, and timestamps are unchanged by a scan."""
    store = repo.open_store("alpha")
    repo.add_review_failure("alpha", store, "one")
    repo.add_engine_transition("alpha", store)
    other = repo.open_store("beta")
    repo.add_engine_transition("beta", other)
    with repo.log_path("beta").open("ab") as handle:
        handle.write(b'{"torn":')
    before = repo.tree_state()
    es = feed._evidence_store()
    monkeypatch.setattr(es.EvidenceStore, "open", lambda *a, **k: pytest.fail("open() called"))
    scan(feed, repo.root)
    scan(feed, repo.root)
    assert repo.tree_state() == before


def test_the_feed_opens_no_file_under_contracts_and_writes_no_file(
    feed: ModuleType, repo: dfs.FeedRepo, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-0011: no schema is read at runtime and nothing is opened for writing."""
    import builtins
    import os

    store = repo.open_store("alpha")
    repo.add_review_failure("alpha", store, "one")
    seen: list[tuple[str, str]] = []
    real_open = builtins.open
    real_os_open = os.open

    def spy_open(file: Any, mode: str = "r", *a: Any, **k: Any) -> Any:
        seen.append((str(file), mode))
        return real_open(file, mode, *a, **k)

    def spy_os_open(path: Any, flags: int, *a: Any, **k: Any) -> Any:
        seen.append((str(path), "w" if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT) else "r"))
        return real_os_open(path, flags, *a, **k)

    monkeypatch.setattr(builtins, "open", spy_open)
    monkeypatch.setattr(os, "open", spy_os_open)
    scan(feed, repo.root)
    monkeypatch.undo()
    assert not [p for p, _ in seen if "contracts" in p]
    assert not [(p, m) for p, m in seen if m not in {"r", "rb"}]
