"""Brief runner run-grant judge, unit level: grant format, record line, fixed detail vocabulary.

No Git and no clock: every case passes ``now`` explicitly.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
    / "brief-runner.py"
)


def _load() -> ModuleType:
    """Load the runner by path under a pack- and skill-unique name."""
    alias = "core_work_loop_brief_runner_grant_units"
    spec = importlib.util.spec_from_file_location(alias, _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


runner = _load()

NOW = datetime(2026, 1, 10, 12, 0, 0, tzinfo=UTC)
SPEC_MAP = ["alpha", "beta", "gamma"]
BASE = {
    "schema_version": "1",
    "brief": '"demo"',
    "confirmed_by": '"alice-1"',
    "confirmed_at": "2026-01-10T11:00:00Z",
    "expires_at": "2026-01-12T11:00:00Z",
    "done_when": '"all-granted-merged"',
    "slices": '["alpha", "beta"]',
    "retry_budget": "2",
    "max_slices_in_flight": "1",
    "held_actions": '["push", "open-pull-request"]',
}
VOCABULARY = {
    "no-record", "not-regular", "oversize", "not-utf8", "hidden-text", "not-toml",
    "unknown-key", "table", "expiry-order", "expiry-too-long", "confirmed-in-future",
    "record-repeated", "record-form", "record-mismatch",
} | {f"key:{k}" for k in runner.GRANT_KEYS}  # fmt: skip


def _grant(**over: str) -> bytes:
    values = {**BASE, **over}
    return "".join(f"{k} = {v}\n" for k, v in values.items()).encode()


def _judge(data: bytes, now: datetime = NOW, cap: int = 2):
    return runner.judge_grant(
        data, brief_slug="demo", spec_map=SPEC_MAP, retry_budget_cap=cap, now=now
    )


def _detail(data: bytes, **kw: object) -> str:
    with pytest.raises(runner.GrantProblem) as err:
        _judge(data, **kw)
    assert err.value.detail in VOCABULARY
    return err.value.detail


def test_valid_grant_returns_typed_values() -> None:
    grant = _judge(_grant())
    assert grant.confirmed_at == datetime(2026, 1, 10, 11, 0, tzinfo=UTC)
    assert grant.expires_at == datetime(2026, 1, 12, 11, 0, tzinfo=UTC)
    assert grant.done_when == "all-granted-merged"
    assert grant.slices == ("alpha", "beta")
    assert (grant.retry_budget, grant.max_slices_in_flight) == (2, 1)
    assert grant.held_actions == ("open-pull-request", "push")
    assert not hasattr(grant, "confirmed_by")


def test_empty_held_actions_passes() -> None:
    assert _judge(_grant(held_actions="[]")).held_actions == ()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("schema_version", "2"),
        ("schema_version", "true"),
        ("brief", '"other"'),
        ("confirmed_by", '""'),
        ("confirmed_by", '"-bad"'),
        ("confirmed_by", '"a--b"'),
        ("confirmed_by", '"' + "a" * 40 + '"'),
        ("confirmed_by", "5"),
        ("confirmed_at", "2026-01-10T11:00:00+02:00"),
        ("confirmed_at", "2026-01-10T11:00:00.5Z"),
        ("confirmed_at", "2026-01-10T11:00:00"),
        ("confirmed_at", "2026-01-10"),
        ("expires_at", "2026-01-12T11:00:00-05:00"),
        ("done_when", '"never"'),
        ("slices", "[]"),
        ("slices", '["alpha", "alpha"]'),
        ("slices", '["delta"]'),
        ("slices", '["Alpha"]'),
        ("slices", '"alpha"'),
        ("retry_budget", "true"),
        ("retry_budget", "3"),
        ("retry_budget", "-1"),
        ("retry_budget", '"1"'),
        ("max_slices_in_flight", "2"),
        ("max_slices_in_flight", "true"),
        ("held_actions", '["merge"]'),
        ("held_actions", '["push", "push"]'),
    ],
)
def test_bad_key_value_names_the_key(key: str, value: str) -> None:
    assert _detail(_grant(**{key: value})) == f"key:{key}"


def test_missing_key_names_the_key() -> None:
    data = _grant().replace(b"retry_budget = 2\n", b"")
    assert _detail(data) == "key:retry_budget"


@pytest.mark.parametrize("key", ["spend_cap", "human_only", "max_retries"])
def test_unknown_key(key: str) -> None:
    assert _detail(_grant() + f"{key} = 1\n".encode()) == "unknown-key"


def test_table_is_refused() -> None:
    assert _detail(_grant() + b"[extra]\nx = 1\n") == "table"


def test_oversize_and_boundary() -> None:
    pad = b"# " + b"x" * 100 + b"\n"
    data = _grant()
    data += pad * ((4096 - len(data)) // len(pad))
    data += b"#" * (4096 - len(data))
    assert len(data) == 4096
    _judge(data)
    assert _detail(data + b"#") == "oversize"


def test_hidden_character() -> None:
    assert _detail(_grant() + "# a​b\n".encode()) == "hidden-text"


def test_not_toml_and_duplicate_key() -> None:
    assert _detail(b"this is = = bad") == "not-toml"
    assert _detail(_grant() + b"retry_budget = 1\n") == "not-toml"


def test_not_utf8() -> None:
    assert _detail(_grant() + b"# \xff\xfe\n") == "not-utf8"


def test_expiry_rules() -> None:
    same = "2026-01-10T11:00:00Z"
    assert _detail(_grant(expires_at=same)) == "expiry-order"
    assert _detail(_grant(expires_at="2026-01-10T10:00:00Z")) == "expiry-order"
    assert _detail(_grant(expires_at="2026-01-24T11:00:01Z")) == "expiry-too-long"
    assert _judge(_grant(expires_at="2026-01-24T11:00:00Z")).expires_at.day == 24


def test_confirmed_in_future() -> None:
    at = "2026-01-10T12:06:00Z"
    assert _detail(_grant(confirmed_at=at, expires_at="2026-01-11T00:00:00Z")) == (
        "confirmed-in-future"
    )
    ok = _grant(confirmed_at="2026-01-10T12:04:00Z", expires_at="2026-01-11T00:00:00Z")
    assert _judge(ok).confirmed_at.minute == 4


def test_detail_never_carries_grant_text() -> None:
    marker = "distinctive-secret-zq"
    for data in (
        _grant(brief=f'"{marker}"'),
        _grant(done_when=f'"{marker}"'),
        _grant() + f"{marker} = 1\n".encode(),
        f"{marker} = = x".encode(),
        _grant() + f"[{marker}]\n".encode(),
    ):
        with pytest.raises(runner.GrantProblem) as err:
            _judge(data)
        assert marker not in err.value.detail
        assert marker not in str(err.value)
        assert err.value.detail in VOCABULARY


def test_human_only_list_is_pinned() -> None:
    assert runner.HUMAN_ONLY == (
        "accept-protected-class-risk",
        "approve-plan",
        "approve-spec",
        "irreversible-operation",
        "merge",
        "reapprove-after-material-change",
    )
    assert list(runner.HUMAN_ONLY) == sorted(runner.HUMAN_ONLY)


def test_grant_cannot_carry_human_only() -> None:
    assert _detail(_grant() + b'human_only = ["merge"]\n') == "unknown-key"


RECORD = "- **Run grant:** required (confirmed 2026-01-10T11:00:00Z)"


def _brief(preamble: str = RECORD, body: str = "") -> str:
    return f"# Brief: demo\n\n- **Status:** Ready\n{preamble}\n\n## Spec map\n\n{body}\n"


def _record_detail(text: str) -> str:
    with pytest.raises(runner.GrantProblem) as err:
        runner.judge_record(text)
    assert err.value.detail in VOCABULARY
    return err.value.detail


def test_record_absent_is_none() -> None:
    assert runner.judge_record(_brief(preamble="")) is None
    assert runner.record_evidence(_brief(preamble="")) is False


def test_record_parses() -> None:
    assert runner.record_evidence(_brief()) is True
    assert runner.judge_record(_brief()) == datetime(2026, 1, 10, 11, 0, tzinfo=UTC)


def test_record_repeated() -> None:
    assert _record_detail(_brief(preamble=RECORD + "\n" + RECORD)) == "record-repeated"
    assert _record_detail(_brief(body=RECORD)) == "record-repeated"


def test_record_only_in_comment_is_form() -> None:
    assert runner.record_evidence(_brief(preamble=f"<!-- {RECORD} -->")) is True
    assert _record_detail(_brief(preamble=f"<!-- {RECORD} -->")) == "record-form"


def test_record_in_body_is_form() -> None:
    assert _record_detail(_brief(preamble="", body=RECORD)) == "record-form"


@pytest.mark.parametrize(
    "line",
    [
        "- **Run grant:** required (confirmed 2026-01-10T11:00:00+00:00)",
        "- **Run grant:** required (confirmed 2026-01-10 11:00:00Z)",
        "- **Run grant:** required (confirmed 2026-13-10T11:00:00Z)",
        "- **Run grant:** optional (confirmed 2026-01-10T11:00:00Z)",
        "* **Run grant:** required (confirmed 2026-01-10T11:00:00Z)",
        RECORD + " extra",
    ],
)
def test_record_wrong_format(line: str) -> None:
    assert _record_detail(_brief(preamble=line)) == "record-form"


def test_record_mismatch() -> None:
    grant = _judge(_grant())
    runner.check_record_matches(grant, runner.judge_record(_brief()))
    other = datetime(2026, 1, 10, 11, 0, 1, tzinfo=UTC)
    with pytest.raises(runner.GrantProblem) as err:
        runner.check_record_matches(grant, other)
    assert err.value.detail == "record-mismatch"
