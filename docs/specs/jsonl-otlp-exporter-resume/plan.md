# Plan: jsonl-otlp-exporter-resume

> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material: an implementer corrects them in place as the
> work teaches, without an amendment and without a review round.

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - `packages/agentbundle/agentbundle/workspace_mcp.py:447-450` — the
    offset-plus-inode pairing and its reset condition (`st_ino` changed or
    `st_size < offset`), reused rather than reinvented. Read for shape, not
    imported: the exporter must stay extractable, which the parent plan pins.
  - `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/source.py:217-220` — the
    one-shot byte budget this change has to make offset-relative.
  - `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/transport.py:341-445` —
    `send_batches`' per-batch loop, where acceptance is decided and where the
    accepted-prefix accounting belongs.
  - `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/config.py` and
    `profile.py` — the precedent for a small module owning one untrusted-input
    parse plus its own refusal exception, which `cursor.py` follows.
  - Analogous tests and their construction path:
    `packages/jsonl-otlp-exporter/tests/unit/test_source.py` (descriptor
    fixtures) and `tests/unit/test_transport.py` (the response-shape seam in
    front of the transport).
  - Named uncertainty: `send_batches` continues to the next batch after a
    non-retryable HTTP error rather than returning, so "the accepted prefix"
    cannot be a high-water mark. This is the single place the implementation is
    most likely to be quietly wrong, and it is why T3's stub asserts an accepted
    batch *after* a refused one.

## Approach

Layers ordered so each is provable before the next depends on it. The cursor's
parse and render are pure and land first; the reader's offset accounting lands
next and is provable with no network; the accepted-prefix accounting lands
against the existing response-shape seam; the CLI wires the three together and
owns the stdout channel.

The package must stay extractable: nothing here imports from this repository,
and the tests use only the package's own fixtures.

## Constraints

- Standard library only at runtime. No new dependency.
- No module may name a consumer.
- No durable write of any kind. The cursor arrives as an argument and leaves on
  stdout.
- **One reader and one batcher, not two of each.** `iter_records` gains
  `start_offset` and `on_position` and yields `(record, end_offset)` pairs;
  `batch_records` consumes those pairs and yields `(records, body, end_offset)`;
  `send_batches` consumes the three-tuple. A parallel `*_positioned` function
  beside each was drafted to spare the existing suites and produced two review
  findings on its own: the CLI had to be switched to the new name and the plan
  never said so, and the old name was left public with nothing consuming it.
  A public function nothing calls is a branch that retires silently.
- Reader churn, counted rather than estimated: `test_source.py` calls
  `iter_records` at eight sites — the `_records` helper at line 31 and seven
  direct calls at 207, 225, 240, 302, 331, 346 and 428. An earlier draft of this
  bullet claimed the helper funnelled almost all of them, which is wrong and was
  the stated reason for keeping a `*_positioned` twin. The honest number is eight
  sites, most of them a `list(...)` that becomes a comprehension, plus the ~25
  `send_batches` call sites taking a third tuple element. That is still small
  enough that one reader beats two.
- Arity changes rather than tolerating both shapes: a function accepting either
  a two-tuple or a three-tuple cannot be type-checked and hides a missed call
  site, which is the defect class `tests/wiring_sweep.py` exists to catch.

## Construction tests

Every module these tasks assert against already exists and ships, so all five
TDD tasks carry validated stub code below rather than the parent plan's
`no stub (implementation-discovered)`.

The response-shape seam in front of the transport is reused unchanged, so each
acceptance and refusal case stays a fixture rather than a live condition.

Five new cross-module keywords each need a control that fails when the keyword is
removed, because `tests/wiring_sweep.py` reports a survivor as a defect:

- `out=` on the cursor print. At least one test passes an explicit buffer and
  asserts on that buffer, so dropping the keyword writes to the real stdout and
  the assertion fails. A test that reads `capsys` alone would still pass and
  leave a survivor.
- `start_offset=` on `send_batches`. T3's AC-0006 case resumes from offset 64
  with its first batch refused and expects 64 back; dropping the keyword
  initialises the accounting at 0 and the case fails.
- `start_offset=` on `iter_records`. T2's AC-0011 case expects the
  first record skipped; dropping the keyword reads from byte 0 and yields it.
- `on_position=` on `iter_records`. T5's clean-run case expects the
  offset past two trailing unparseable lines; without the callback the CLI falls
  back to the last batch's offset and the case fails.
- `fd=` on `resolve_start_offset`. T4's AC-0030 case drives a misaligned cursor
  through the command and expects exit 1; without the descriptor the boundary
  check cannot run and the run resumes mid-record instead.

## Stub validation

Every fenced Python block below was parsed, and each block's free names resolved
against the test module it lands in, before this plan was put up for approval.
This is a recorded measurement, not a standing gate: the script lives in the
session scratchpad, and promoting it to `tools/` is named under the spec's
Follow-ons because a repository tool owes a test beside it.

The method: extract each ```python block, `ast.parse` it, collect every name
loaded but not bound inside the block, and subtract the target module's
module-level names, the names the block's own docstring says it adds, and the
helpers the `## New test helpers` section specifies. Anything left is a stub that
cannot run.

A second check runs beside the name check: for every call to a helper the
target module defines, each keyword the stub passes must be one that helper
accepts. Name existence alone let two defects through — `_records(fd)` against
`_records(path, root)`, and `_FakeResponse(body=...)` against its `payload=`.

The keyword check has one blind spot, and it is worth knowing: a helper taking
`**kwargs` accepts anything, so nothing can be checked against it. `_dest` in
`test_transport.py` is such a helper, and `_dest(endpoint="x")` passes. The
three helpers `## New test helpers` specifies take keyword-only arguments and no
`**kwargs`, so they stay checkable.

Result, 2026-09-15: 6 blocks, all parse, 0 unresolved names, 0 bad keywords. It reached that
state by failing first — on its first run it reported `mock` in T2 (a module
`test_source.py` does not import, and which `packages/AGENTS.md` steers away
from in favour of `monkeypatch`), `os` plus three undeclared helpers in T4, and
five undeclared imports in T5. The script also had to be fixed: its first
version keyed each block to a target module by list index, and silently
mis-targeted every block once a new one was inserted ahead of them, so the
target is now read from the block's own text.

## New test helpers

T4 introduces three module-level helpers in `tests/unit/test_cli.py`. They are
specified here because the stubs call them and a stub that calls an undeclared
helper is not a validated stub — three of round 4's four findings were exactly
that class, and running the stubs is what surfaces them.

```python
def _run_against_receiver(tmp_path, monkeypatch, *, out=None, stream=None,
                          sent=None, extra=(), target=None, lines=1,
                          statuses=(200,)) -> int:
    """Drive `cli.main` end to end against a recording fake receiver.

    Writes `lines` valid records to `target` (default `tmp_path/events.jsonl`)
    only when that path does not already exist, so a caller that wrote its own
    fixture keeps it. Installs a connection factory that appends each request
    body to `sent` and answers with the next status from `statuses`, repeating
    the last one. Passes `--input`, `--root`, `--profile` and an endpoint in the
    environment, then whatever `extra` adds. Returns the exit code.
    """


def _argv_for(kind, tmp_path) -> list[str]:
    """Argv for one of AC-0019's six pre-open exit reasons.

    `kind` is one of `no-endpoint`, `bad-cursor`, `bad-config`, `bad-profile`,
    `absent-input`, `bad-endpoint`. Always appends `--report-cursor`: without it
    AC-0002 already requires an empty stdout and the case proves nothing.
    """


def _env_for(kind) -> dict[str, str]:
    """The environment paired with `_argv_for(kind, ...)`.

    Empty for `no-endpoint`; otherwise an endpoint that resolves, so each case
    exits for the reason it names rather than for a missing endpoint.
    """
```

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `README-pypi.md` (public contract, compatibility) | T6 | AC-0021 green | Renders on PyPI |
| `CHANGELOG.md` (release) | T6 | Both flags named under the unreleased `## 0.1.0` entry | Tag matches `pyproject.toml` |
| `notes/decisions.md` (decision rationale) | T0 — authored at PLAN | Each decision naming its rejected alternative | File present |

## Design (LLD)

### Interfaces & contracts — the cursor

```json
{"v": 1, "offset": 4096, "device": 16777232, "inode": 8394821}
```

One line of JSON on stdout under `--report-cursor`; the same text accepted back
as the `--from-cursor` argument. `v` exists so a caller holding a cursor written
by a future version is refused loudly rather than misread; a value other than 1
is a refusal, not a reset.

### Component / module decomposition

One new module and three changed ones:

- `cursor.py` (new) — `Cursor`, `CursorRefused`, `parse_cursor`,
  `render_cursor`, `resolve_start_offset`. `parse_cursor` does no I/O at all,
  which is what lets the whole refusal group run with no file.
  `resolve_start_offset` takes the already-validated descriptor and does exactly
  one read on it — `os.pread(fd, 1, offset - 1)` for the boundary check — which
  does not move the file position.
- `source.py` — `iter_records` gains a start offset, a position callback, and a
  per-record end offset on each yield.
- `transport.py` — the batch tuple gains its end offset; `SendOutcome` gains
  `accepted_offset` and `all_accepted`.
- `cli.py` — two flags, the `out` stream, and the one place the reported offset
  is computed.

### State & control flow — how the offset is computed

Two mechanisms with two distinct jobs, because neither alone is sufficient:

1. **Per-batch end offset**, carried in the batch tuple. Needed because
   `_emit` splits an over-large batch, and its halves must carry their own
   offsets — giving both halves the parent's end offset would credit the second
   half when only the first was accepted.
2. **The reader's final consumed position**, reported through `on_position`.
   Needed because lines the reader consumed after the last record it yielded —
   trailing unparseable lines, an over-length line, a record with a bad
   timestamp — belong to no batch, and a run that leaves the offset before them
   re-reads and re-skips them on every future run.

The CLI combines them: the offset is the accepted prefix, and only when every
batch was accepted is it raised to the reader's final position. That ordering is
what makes AC-0004 and AC-0005 both true — the second mechanism can only ever
extend a clean run, never step past a failure. AC-0008 was drafted as a third
rule for the over-ceiling record and retired: stated unconditionally it
contradicted AC-0005, and as a member of AC-0004's set it is already covered.

### Failure, edge cases & resilience

A malformed cursor is a usage error and exits 1 even with no endpoint
configured, which is what `--config` and `--profile` already do. This does not
weaken off-by-default: a refused argument sends nothing, and the parent
contract's AC-0033 — amended in this change to name all three arguments — was
only ever about the exit status.

A rotation or truncation resets to byte 0 with a line on stderr. A cursor that
is merely malformed never resets — silently restarting from 0 for a caller bug
would re-send the whole history without saying so.

## Tasks

### T1: The cursor module — parse, render, reset

**Depends on:** none

**Touches:** `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/cursor.py`,
`packages/jsonl-otlp-exporter/tests/unit/test_cursor.py`

**Tests:**

Validated stub. Verification mode: TDD. Materialise unchanged, prove the red,
then fill the deferred cases.

```python
"""AC-0012, AC-0023, AC-0013, AC-0024, AC-0015, AC-0016, AC-0030 — the cursor.

A new module, tests/unit/test_cursor.py. Self-contained: it imports `io`,
`json`, `os`, `pytest` and the `cursor` module under test.
"""
import io
import json
import os

import pytest

from jsonl_otlp_exporter import cursor as cur


class TestRoundTrip:
    def test_render_parses_back_to_the_same_cursor(self):
        """The output of one run is the input of the next, or resume is a fiction."""
        text = cur.render_cursor(4096, 12, 34)
        assert json.loads(text) == {"v": 1, "offset": 4096, "device": 12, "inode": 34}
        back = cur.parse_cursor(text)
        assert (back.offset, back.device, back.inode) == (4096, 12, 34)

    def test_render_emits_exactly_one_line(self):
        """AC-0001's 'exactly one line' is decided here, not at the print."""
        assert "\n" not in cur.render_cursor(0, 1, 2)


class TestRefusal:
    @pytest.mark.parametrize(
        "text",
        [
            "not json at all",
            "[]",
            "3",
            '"a string"',
            '{"v": 1, "offset": 0, "device": 1}',                    # missing inode
            '{"v": 1, "offset": 0, "device": 1, "inode": 2, "x": 3}',  # extra key
            '{"v": 2, "offset": 0, "device": 1, "inode": 2}',        # future version
            '{"v": 1, "offset": "0", "device": 1, "inode": 2}',      # offset not an int
            '{"v": 1, "offset": 1.5, "device": 1, "inode": 2}',
            '{"v": 1, "offset": true, "device": 1, "inode": 2}',     # bool is not an int here
            '{"v": 1, "offset": -1, "device": 1, "inode": 2}',       # negative
            '{"v": 1, "offset": 0, "device": "1", "inode": 2}',
            '{"v": 1, "offset": 0, "device": 1, "inode": "2"}',
        ],
    )
    def test_a_bad_cursor_is_refused(self, text):
        """AC-0016. One predicate, every enumerated member."""
        with pytest.raises(cur.CursorRefused):
            cur.parse_cursor(text)

    def test_an_oversize_argument_is_refused_on_its_length(self):
        """AC-0015, and the fixture is the whole point of the case.

        The argument is over the byte bound and otherwise fully conforming: a
        valid member set, valid types, a non-negative integer offset. Nothing
        but the length check can refuse it, so a build that parses first and
        never measures raises nothing and this fails. A fixture padded with an
        extra member is refused on shape by that same wrong build -- which is
        how this case was first drafted, and why it was replaced.
        """
        offset = int("9" * (cur.MAX_CURSOR_BYTES + 1))
        text = json.dumps({"v": 1, "offset": offset, "device": 1, "inode": 2})
        assert len(text.encode("utf-8")) > cur.MAX_CURSOR_BYTES
        with pytest.raises(cur.CursorRefused) as excinfo:
            cur.parse_cursor(text)
        assert "too long" in str(excinfo.value)

    def test_the_length_refusal_is_distinguishable_from_a_shape_refusal(self):
        """AC-0015 states an ordering, and an ordering needs two outcomes.

        Without this, an argument that is both over-length and malformed cannot
        show which check fired, so "before it is parsed" is unobservable and the
        case above proves only that something refused.
        """
        with pytest.raises(cur.CursorRefused) as excinfo:
            cur.parse_cursor("not json at all")
        assert "too long" not in str(excinfo.value)

    def test_the_bound_is_measured_on_utf8_bytes_not_characters(self):
        """The bound's unit.

        A conforming cursor is all ASCII, so no valid-shape fixture can separate
        characters from bytes. This one is malformed too, so it asserts only that
        the LENGTH check fired -- which the case above established is a
        distinguishable reason.
        """
        text = '{"v": 1, "offset": 0, "é": "'
        text += "é" * (cur.MAX_CURSOR_BYTES // 2 + 1) + '"}'
        assert len(text) < cur.MAX_CURSOR_BYTES < len(text.encode("utf-8"))
        with pytest.raises(cur.CursorRefused) as excinfo:
            cur.parse_cursor(text)
        assert "too long" in str(excinfo.value)


class TestResolveStartOffset:
    @staticmethod
    def _info(device, inode, size):
        class _Stat:
            st_dev, st_ino, st_size = device, inode, size

        return _Stat()

    def test_a_matching_cursor_is_honoured(self):
        """AC-0011's half that needs no file."""
        stream = io.StringIO()
        offset = cur.resolve_start_offset(
            cur.Cursor(offset=10, device=1, inode=2), self._info(1, 2, 100), stream=stream
        )
        assert offset == 10
        assert stream.getvalue() == ""

    def test_an_offset_equal_to_the_size_is_honoured(self):
        """The boundary the bridge's `st_size < offset` puts on the honoured side."""
        assert cur.resolve_start_offset(
            cur.Cursor(offset=100, device=1, inode=2),
            self._info(1, 2, 100),
            stream=io.StringIO(),
        ) == 100

    @pytest.mark.parametrize(
        "info_args", [(9, 2, 100), (1, 9, 100)], ids=["device", "inode"]
    )
    def test_an_identity_change_resets_to_zero(self, info_args):
        """AC-0012. Device and inode each reset on their own."""
        assert cur.resolve_start_offset(
            cur.Cursor(offset=10, device=1, inode=2),
            self._info(*info_args),
            stream=io.StringIO(),
        ) == 0

    @pytest.mark.parametrize(
        "info_args", [(9, 2, 100), (1, 9, 100)], ids=["device", "inode"]
    )
    def test_an_identity_change_is_reported(self, info_args):
        """AC-0023, split from AC-0012: a silent reset fails only this one."""
        stream = io.StringIO()
        cur.resolve_start_offset(
            cur.Cursor(offset=10, device=1, inode=2),
            self._info(*info_args),
            stream=stream,
        )
        assert "identity" in stream.getvalue()

    def test_a_shrink_below_the_offset_resets_to_zero(self):
        """AC-0013."""
        assert cur.resolve_start_offset(
            cur.Cursor(offset=200, device=1, inode=2),
            self._info(1, 2, 100),
            stream=io.StringIO(),
        ) == 0

    def test_a_shrink_below_the_offset_is_reported(self):
        """AC-0024, split from AC-0013."""
        stream = io.StringIO()
        cur.resolve_start_offset(
            cur.Cursor(offset=200, device=1, inode=2),
            self._info(1, 2, 100),
            stream=stream,
        )
        assert "shrank" in stream.getvalue()

    def test_a_misaligned_offset_is_refused_not_reset(self, tmp_path):
        """AC-0030. A matching identity with a bad offset is not a rotation.

        Folding this into AC-0012's reset is the tempting shape and is wrong: it
        turns a corrupted or forged cursor into a silent re-send of the whole
        file. The check reads the preceding byte from the descriptor `--input`
        was opened on, so it inherits that descriptor's confinement proof rather
        than reopening the path.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(b'{"i": 0}\n{"i": 1}\n')
        fd = os.open(target, os.O_RDONLY)
        try:
            info = os.fstat(fd)
            aligned = cur.Cursor(offset=9, device=info.st_dev, inode=info.st_ino)
            assert cur.resolve_start_offset(aligned, info, stream=io.StringIO(),
                                            fd=fd) == 9
            misaligned = cur.Cursor(offset=4, device=info.st_dev,
                                    inode=info.st_ino)
            with pytest.raises(cur.CursorRefused):
                cur.resolve_start_offset(misaligned, info, stream=io.StringIO(),
                                         fd=fd)
        finally:
            os.close(fd)

    def test_a_decoder_failure_of_any_kind_becomes_a_refusal(self):
        """AC-0016's catch-all member.

        Measured 2026-09-15: neither scanner raises `RecursionError` at the ~2000
        nesting levels a 4096-byte argument admits, so this is insurance rather
        than a reproducing attack -- the recursion limit is settable by an
        embedding caller and `source.py:286` carries the same broad catch for the
        same reason. The case asserts the refusal either way, so it holds whether
        the decoder raises or simply rejects the shape.
        """
        with pytest.raises(cur.CursorRefused):
            cur.parse_cursor("[" * 2000 + "]" * 2000)

    def test_no_cursor_reads_from_zero_and_says_nothing(self):
        """AC-0014. The absent flag is not a reset and must not print one."""
        stream = io.StringIO()
        assert cur.resolve_start_offset(None, self._info(1, 2, 100), stream=stream) == 0
        assert stream.getvalue() == ""
```

- Verifies AC-0012, AC-0023, AC-0013, AC-0024, AC-0015, AC-0016, AC-0030, and
  the file-free halves of AC-0022, AC-0011 and AC-0014.

**Approach:**

- `MAX_CURSOR_BYTES = 4096`, checked on `text.encode("utf-8")` before
  `json.loads`.
- Reject `bool` explicitly: `isinstance(True, int)` is true in Python, so a
  cursor carrying `true` for an offset parses as 1 without it.
- Compare the member-name set for equality, not containment, so an extra key is
  a refusal rather than ignored.
- The length refusal's message contains `too long`; no other refusal's does.
  AC-0015 states an ordering between two checks, and an ordering is only
  observable when the two outcomes differ.
- `parse_cursor` catches `Exception`, not just `JSONDecodeError`, converting any
  decode failure to `CursorRefused`. `source.py:286` carries the same broad catch
  and states the reason: the decoder raises more than a decode error on hostile
  input. Measured 2026-09-15, the nesting a 4096-byte argument admits does not
  reach that on this interpreter, but the recursion limit is caller-settable and
  the catch costs one clause.
- `resolve_start_offset` takes the open descriptor and reads the byte before a
  non-zero offset with `os.pread`, which does not disturb the file position. It
  is the descriptor `open_input` already validated, so the check adds no path
  resolution and no new confinement window.
- The 4096-byte bound is also what keeps a digit bomb out of the parse. CPython
  refuses to convert an integer literal longer than
  `sys.get_int_max_str_digits()`, which defaults to 4300: measured 2026-09-15,
  `json.loads` of a 5000-digit integer raises `ValueError` while 4097 digits
  parses. Every argument inside the byte bound is therefore inside the digit
  limit, so the length check decides the long case and `json.loads` never meets
  one. `parse_cursor` still catches `ValueError` — it is the ordinary
  does-not-parse path — but no conforming argument reaches it that way.

**Done when:** the whole stub passes and `parse_cursor` refuses every member of
its parametrised set.

### T2: The positioned reader

**Depends on:** T1

**Touches:** `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/source.py`,
`packages/jsonl-otlp-exporter/tests/unit/test_source.py`

**Tests:**

Validated stub. Verification mode: TDD.

```python
"""AC-0009, AC-0010, AC-0011, AC-0014, AC-0017, AC-0029 — reading from an offset.

Appended to tests/unit/test_source.py, which already imports `io`, `os`,
`src` and defines `_records`. Adds no import: the budget cases use the
`monkeypatch` fixture, which `packages/AGENTS.md` names as the convention.
"""


class TestPositionedReader:
    """Appended to tests/unit/test_source.py, which owns `_records` and the fd
    fixtures this reuses."""

    @staticmethod
    def _write(tmp_path, lines):
        target = tmp_path / "events.jsonl"
        target.write_bytes(b"".join(line.encode("utf-8") + b"\n" for line in lines))
        return target

    def test_a_start_offset_skips_the_records_before_it(self, tmp_path):
        """AC-0011."""
        target = self._write(tmp_path, ['{"i": 0}', '{"i": 1}', '{"i": 2}'])
        first_line = len(b'{"i": 0}\n')
        fd = src.open_input(target, tmp_path)
        try:
            pairs = list(src.iter_records(fd, start_offset=first_line))
        finally:
            os.close(fd)
        assert [record["i"] for record, _ in pairs] == [1, 2]

    def test_each_yielded_offset_follows_a_newline(self, tmp_path):
        """AC-0009, asserted on every yield rather than sampled once."""
        target = self._write(tmp_path, ['{"i": 0}', '{"i": 1}', '{"i": 2}'])
        data = target.read_bytes()
        fd = src.open_input(target, tmp_path)
        try:
            offsets = [offset for _, offset in src.iter_records(fd)]
        finally:
            os.close(fd)
        assert offsets, "the reader yielded nothing, so the invariant was not exercised"
        for offset in offsets:
            assert data[offset - 1 : offset] == b"\n", offset

    def test_a_skipped_line_still_advances_the_position(self, tmp_path):
        """A line the reader consumed and declined belongs behind the offset, or
        every future run re-reads and re-declines it."""
        target = self._write(tmp_path, ['{"i": 0}', "not json", '{"i": 2}'])
        fd = src.open_input(target, tmp_path)
        try:
            pairs = list(src.iter_records(fd, stream=io.StringIO()))
        finally:
            os.close(fd)
        assert pairs[-1][1] == len(target.read_bytes())

    def test_a_final_line_with_no_newline_is_not_consumed(self, tmp_path):
        """AC-0010. The partial line's first byte is the ceiling on the offset."""
        target = tmp_path / "events.jsonl"
        target.write_bytes(b'{"i": 0}\n{"i": 1}')
        fd = src.open_input(target, tmp_path)
        try:
            positions = []
            pairs = list(
                src.iter_records(fd, on_position=positions.append)
            )
        finally:
            os.close(fd)
        assert [record["i"] for record, _ in pairs] == [0]
        assert max(positions) == len(b'{"i": 0}\n')

    def test_on_position_reports_past_a_trailing_skipped_line(self, tmp_path):
        """AC-0004's trailing-skip member: the last yield cannot see past itself."""
        target = self._write(tmp_path, ['{"i": 0}', "not json"])
        fd = src.open_input(target, tmp_path)
        try:
            positions = []
            list(
                src.iter_records(
                    fd, stream=io.StringIO(), on_position=positions.append
                )
            )
        finally:
            os.close(fd)
        assert max(positions) == len(target.read_bytes())

    def test_an_unterminated_over_length_final_line_is_not_consumed(self, tmp_path):
        """AC-0010 on the path a short partial line never reaches.

        The reader clears an over-length line's bytes as it reads them, so an
        accounting that advances on the clear reports a position inside a line
        with no terminator -- and a later run resumes mid-record from it. A short
        partial line stays in the buffer and never exercises the discard branch,
        which is why the first draft's single fixture could not see this.
        """
        target = tmp_path / "events.jsonl"
        head = b'{"i": 0}\n'
        target.write_bytes(head + b"x" * (src.MAX_LINE_BYTES + 10))
        fd = src.open_input(target, tmp_path)
        try:
            positions = []
            list(
                src.iter_records(
                    fd, stream=io.StringIO(), on_position=positions.append
                )
            )
        finally:
            os.close(fd)
        assert max(positions) == len(head)

    def test_the_one_shot_budget_is_measured_from_the_start_offset(
        self, tmp_path, monkeypatch
    ):
        """AC-0017. Asserted against a live writer, not against the arithmetic.

        A budget left at the whole file size lets one-shot drain an appending
        writer forever; a budget of size-minus-offset cannot. The writer appends
        on every read, so a wrong budget hangs rather than returning a wrong
        count -- which is why this has a record ceiling and not just an equality.
        """
        target = self._write(tmp_path, ['{"i": 0}', '{"i": 1}'])
        first_line = len(b'{"i": 0}\n')
        fd = src.open_input(target, tmp_path)
        appended = [0]

        def _read(descriptor, size):
            if appended[0] < 50:
                appended[0] += 1
                with open(target, "ab") as handle:
                    handle.write(b'{"i": 99}\n')
            return os.read(descriptor, size)

        try:
            monkeypatch.setattr(src.os, "read", _read)
            pairs = list(src.iter_records(fd, start_offset=first_line))
        finally:
            os.close(fd)
        assert len(pairs) == 1
        assert pairs[0][0] == {"i": 1}

    def test_the_budget_covers_the_whole_file_after_a_reset(self, tmp_path,
                                                           monkeypatch):
        """AC-0029. A reset reads from zero, so its ceiling is S, not S - N.

        Driven the same way as AC-0017 and separate from it because the two
        ceilings come from different starting offsets: a build that subtracts the
        cursor's offset unconditionally passes AC-0017 and never terminates here.
        """
        target = self._write(tmp_path, ['{"i": 0}', '{"i": 1}'])
        fd = src.open_input(target, tmp_path)
        appended = [0]

        def _read(descriptor, size):
            if appended[0] < 50:
                appended[0] += 1
                with open(target, "ab") as handle:
                    handle.write(b'{"i": 99}\n')
            return os.read(descriptor, size)

        try:
            monkeypatch.setattr(src.os, "read", _read)
            pairs = list(src.iter_records(fd, start_offset=0))
        finally:
            os.close(fd)
        assert [record["i"] for record, _ in pairs] == [0, 1]

    def test_the_modules_helper_unwraps_the_new_yield_shape(self, tmp_path):
        """`test_source.py:28`'s `_records(path, root, **kwargs)` still returns
        plain records, so cases routed through it keep their assertions.

        It takes a path and a root, not a descriptor, and opens the input itself.
        Pinned because the helper is the one site that hides the pair from a
        caller; the seven direct `iter_records` calls in that module unwrap at
        their own call site.
        """
        target = self._write(tmp_path, ['{"i": 0}', '{"i": 1}'])
        assert _records(target, tmp_path) == [{"i": 0}, {"i": 1}]
```

- Verifies AC-0009, AC-0010 on both its fixtures, AC-0011, AC-0014's reader
  half, AC-0017, AC-0029, and AC-0004's skipped-line members.

**Approach:**

- `iter_records(fd, *, start_offset=0, ..., on_position=None)` seeks
  to `start_offset`, tracks `position`, and yields `(value, position)` after each
  consumed line.
- `budget = max(0, os.fstat(fd).st_size - start_offset)` in one-shot.
- `position` advances **only** when a newline is actually consumed, and never
  when buffered bytes are cleared. The reader discards an over-length line's
  bytes as it reads them, so an accounting that advances on the discard reports a
  position inside a line that has no terminator yet — which breaks AC-0009 and
  AC-0010 and lets a later run resume mid-record. Count the discarded bytes in a
  separate tally and fold that tally into `position` when the discarded line's
  own newline arrives; if it never arrives, `position` correctly stays before the
  whole line.
- `iter_records` yields `(record, end_offset)`. Its eight call sites in
  `test_source.py` unwrap the pair: the `_records` helper absorbs it for the
  cases routed through it, and the seven direct calls take the record from the
  pair at their own site.

**Done when:** the stub passes, and every existing `test_source.py` case passes
after its call site unwraps the pair — the assertions do not change, only the
unwrapping.

### T3: The accepted prefix

**Depends on:** T2

**Touches:** `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/transport.py`,
`packages/jsonl-otlp-exporter/tests/unit/test_transport.py`

**Tests:**

Validated stub. Verification mode: TDD.

```python
"""AC-0004 through AC-0007 — which offset a run has earned."""


class TestAcceptedOffset:
    """Appended to tests/unit/test_transport.py, which owns `_dest`,
    `_factory` and `_FakeResponse`."""

    @staticmethod
    def _batches(*ends):
        return [([], b"{}", end) for end in ends]

    def test_a_fully_accepted_run_reports_the_last_batch_offset(self):
        """AC-0004's send half."""
        out = tp.send_batches(
            self._batches(100, 200, 300),
            _dest(),
            _factory([], [_FakeResponse(), _FakeResponse(), _FakeResponse()]),
            start_offset=0,
        )
        assert out.accepted_offset == 300
        assert out.all_accepted is True

    def test_an_accepted_batch_after_a_refused_one_is_not_credited(self):
        """AC-0005, and the reason this task exists.

        `send_batches` continues to the next batch after a non-retryable status,
        so a high-water mark would credit batch three and lose batch two's
        records for good. The prefix stops at the first refusal.
        """
        out = tp.send_batches(
            self._batches(100, 200, 300),
            _dest(),
            _factory([], [_FakeResponse(), _FakeResponse(status=400), _FakeResponse()]),
            start_offset=0,
        )
        assert out.accepted_offset == 100
        assert out.all_accepted is False

    def test_a_refused_first_batch_reports_the_start_offset(self):
        """AC-0006, and the control behind `start_offset=`."""
        out = tp.send_batches(
            self._batches(100, 200),
            _dest(),
            _factory([], [_FakeResponse(status=400), _FakeResponse()]),
            start_offset=64,
        )
        assert out.accepted_offset == 64
        assert out.all_accepted is False

    def test_a_run_issuing_no_batch_reports_the_start_offset(self):
        """A run the reader gave nothing.

        `all_accepted` stays true, so the CLI raises the offset to the reader's
        consumed position -- which is AC-0004, not AC-0006: AC-0006 needs a first
        batch to exist. Asserted here because the two read alike and the
        distinction is what stops a solitary over-ceiling record from stalling.
        """
        out = tp.send_batches([], _dest(), _factory([], []), start_offset=64)
        assert out.accepted_offset == 64
        assert out.all_accepted is True

    def test_a_partial_success_is_not_an_acceptance(self):
        """AC-0007. HTTP 200 with rejected records must not move the offset."""
        body = b'{"partialSuccess": {"rejectedLogRecords": 2}}'
        out = tp.send_batches(
            self._batches(100, 200),
            _dest(),
            _factory([], [_FakeResponse(), _FakeResponse(payload=body)]),
            start_offset=0,
        )
        assert out.accepted_offset == 100
        assert out.all_accepted is False

    def test_a_split_batch_credits_each_half_separately(self):
        """AC-0005 at the one place the halves could share a parent's offset."""
        records = [{"pad": "x" * 4096} for _ in range(4)]
        positioned = [(record, (index + 1) * 10) for index, record in enumerate(records)]

        def encode(batch, diagnostics=True):
            return json.dumps(list(batch)).encode("utf-8")

        batches = list(
            tp.batch_records(positioned, encode, max_bytes=8192)
        )
        assert len(batches) > 1, "the fixture did not actually split"
        assert [end for _, _, end in batches] == sorted(end for _, _, end in batches)
        assert batches[-1][2] == 40
        assert batches[0][2] < 40, "the first half must not carry the parent's offset"
```

- Verifies AC-0004's send half, AC-0005, AC-0006, AC-0007.

**Approach:**

- `SendOutcome` gains `accepted_offset: int = 0` and `all_accepted: bool = True`.
- `send_batches` gains `start_offset: int = 0`, initialises
  `out.accepted_offset` from it, and sets `all_accepted = False` at every point a
  batch is not accepted — the redirect return, the attempt-budget returns, the
  run-bound returns, the non-2xx break, and the `partialSuccess` branch.
- `accepted_offset` is only assigned while `all_accepted` is still true, so a
  batch sent after a refusal cannot advance it.
- `batch_records` takes `(record, end_offset)` pairs and yields
  `(records, body, end_offset)`; `_emit` threads each sub-batch's own last-record
  offset through the split. `batch_records` keeps its name and now yields the
  three-tuple with a zero offset for callers that do not track one.

**Done when:** the stub passes and every existing `test_transport.py` case passes
with its batch tuples widened to three elements.

### T4: CLI wiring and the stdout channel

**Depends on:** T3

**Touches:** `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/cli.py`,
`packages/jsonl-otlp-exporter/tests/unit/test_cli.py`

**Tests:**

Validated stub. Verification mode: TDD.

```python
"""AC-0001, AC-0022, AC-0002, AC-0003, AC-0011, AC-0012, AC-0018 through
AC-0030 — the flags end to end.

Appended to tests/unit/test_cli.py, which already imports `cli`, `io`,
`json` and `pytest`. Adds `import os` and the three module-level helpers
the `## New test helpers` section above specifies.
"""


class TestReportCursor:
    """Appended to tests/unit/test_cli.py, which owns the local-receiver
    fixtures and the connection-factory seam."""

    def test_the_flag_prints_exactly_one_json_object(self, tmp_path, monkeypatch):
        """AC-0001. The buffer is explicit so dropping `out=` fails this."""
        out = io.StringIO()
        code = _run_against_receiver(tmp_path, monkeypatch, out=out,
                                     extra=["--report-cursor"])
        assert code == 0
        lines = out.getvalue().splitlines()
        assert len(lines) == 1
        reported = json.loads(lines[0])              # AC-0022
        assert set(reported) == {"v", "offset", "device", "inode"}
        assert reported["v"] == 1
        assert all(type(reported[k]) is int for k in
                   ("v", "offset", "device", "inode"))

    def test_without_the_flag_stdout_stays_empty(self, tmp_path, monkeypatch):
        """AC-0002."""
        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out)
        assert out.getvalue() == ""

    def test_the_identity_is_the_descriptor_not_the_path(self, tmp_path, monkeypatch):
        """AC-0003. The path is replaced after the open; the cursor must not move."""
        target = tmp_path / "events.jsonl"
        target.write_bytes(b'{"ts": "2026-01-01T00:00:00Z", "result": "ok"}\n')
        expected = os.stat(target)
        real = cli.open_input

        def swap(path, root):
            fd = real(path, root)
            other = tmp_path / "other.jsonl"
            other.write_bytes(b'{"ts": "2026-01-01T00:00:00Z", "result": "ok"}\n')
            os.replace(other, target)
            return fd

        monkeypatch.setattr(cli, "open_input", swap)
        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out,
                              extra=["--report-cursor"], target=target)
        reported = json.loads(out.getvalue())
        assert (reported["device"], reported["inode"]) == (expected.st_dev,
                                                           expected.st_ino)

    def test_the_reported_cursor_resumes_the_next_run(self, tmp_path, monkeypatch):
        """AC-0011 end to end: the whole point, asserted as a round trip."""
        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out,
                              extra=["--report-cursor"], lines=2)
        cursor = out.getvalue().strip()
        sent = []
        second = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=second, sent=sent,
                              extra=["--report-cursor", "--from-cursor", cursor],
                              lines=2)
        assert sent == [], "a second run over an unchanged file must send nothing"
        assert json.loads(second.getvalue()) == json.loads(cursor)

    def test_an_identity_change_resends_the_new_files_records(self, tmp_path,
                                                              monkeypatch):
        """AC-0012 at the command.

        T1 proves `resolve_start_offset` returns zero on an identity change; this
        proves the zero reaches the reader. A build that computes the reset and
        then seeks to the stale offset passes T1 and sends nothing here -- or
        worse, sends from the middle of an unrelated record.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(b'{"ts": "2026-01-01T00:00:00Z", "result": "ok"}\n' * 3)
        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out,
                              extra=["--report-cursor"], target=target)
        cursor = out.getvalue().strip()
        assert json.loads(cursor)["offset"] > 0

        replacement = tmp_path / "rotated.jsonl"
        replacement.write_bytes(b'{"ts": "2026-02-02T00:00:00Z", "result": "ok"}\n')
        os.replace(replacement, target)

        sent = []
        stream = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=io.StringIO(), sent=sent,
                              stream=stream, target=target,
                              extra=["--report-cursor", "--from-cursor", cursor])
        assert len(sent) == 1, "the new file's one record must be sent"
        assert b"2026-02-02" in sent[0]
        assert "identity" in stream.getvalue()   # AC-0023 at the command

    def test_a_misaligned_cursor_is_refused_at_the_command(self, tmp_path,
                                                           monkeypatch):
        """AC-0030 at the command, and the control behind `fd=`.

        T1 proves the boundary check refuses; this proves it is wired, and that
        the run does not fall through to reading from a mid-record offset. The
        cursor is the command's own, with its offset moved one byte -- so its
        identity matches and only the alignment is wrong.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(b'{"ts": "2026-01-01T00:00:00Z", "result": "ok"}\n' * 2)
        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out, target=target,
                              extra=["--report-cursor"])
        cursor = json.loads(out.getvalue())
        cursor["offset"] -= 1

        sent = []
        code = _run_against_receiver(tmp_path, monkeypatch, sent=sent,
                                     target=target,
                                     extra=["--from-cursor", json.dumps(cursor)])
        assert code == 1
        assert sent == []

    def test_resuming_sends_exactly_the_records_appended_since(self, tmp_path,
                                                               monkeypatch):
        """AC-0032. The positive assertion the contract was missing.

        The round-trip case above resumes over an UNCHANGED file and asserts
        nothing is sent, which a build that never sends anything also satisfies.
        This appends two records after the first run, resumes, and requires
        exactly those two on the wire -- so a build that honours the cursor by
        reading nothing fails here and nowhere else.
        """
        target = tmp_path / "events.jsonl"
        first = b'{"ts": "2026-01-01T00:00:00Z", "result": "ok"}\n'
        target.write_bytes(first)
        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out, target=target,
                              extra=["--report-cursor"])
        cursor = out.getvalue().strip()

        with open(target, "ab") as handle:
            handle.write(b'{"ts": "2026-01-01T00:00:01Z", "result": "ok"}\n')
            handle.write(b'{"ts": "2026-01-01T00:00:02Z", "result": "ok"}\n')

        sent = []
        code = _run_against_receiver(
            tmp_path, monkeypatch, out=io.StringIO(), sent=sent, target=target,
            extra=["--report-cursor", "--from-cursor", cursor],
        )
        assert code == 0
        body = b"".join(sent)
        assert b"00:00:01" in body and b"00:00:02" in body
        assert b"00:00:00" not in body, "the first record must not be re-sent"

    def test_a_malformed_cursor_exits_one_and_sends_nothing(self, tmp_path,
                                                            monkeypatch):
        """AC-0016 at the CLI, with the transport seam proving nothing was sent."""
        sent = []
        code = _run_against_receiver(tmp_path, monkeypatch, sent=sent,
                                     extra=["--from-cursor", "{}"])
        assert code == 1
        assert sent == []

    @pytest.mark.parametrize("env", [{}, {"OTEL_EXPORTER_OTLP_ENDPOINT":
                                          "http://127.0.0.1:4318"}],
                             ids=["no-endpoint", "endpoint"])
    def test_a_malformed_cursor_exits_one_at_both_endpoint_states(self, env,
                                                                  tmp_path):
        """AC-0026, and the AC-0033 carve-out is what makes one status right.

        A build honouring the unamended AC-0033 returns 0 for the unconfigured
        case, so parametrising the endpoint state is the whole control.
        """
        target = tmp_path / "events.jsonl"
        target.write_text("{}\n", encoding="utf-8")
        stream = io.StringIO()
        code = cli.main(
            ["--input", str(target), "--root", str(tmp_path),
             "--from-cursor", "nonsense"],
            env=env, stream=stream, out=io.StringIO(),
        )
        assert code == 1
        assert "cursor" in stream.getvalue()   # AC-0028


class TestNoCursorWhenNothingWasRead:
    @pytest.mark.parametrize(
        "argv_kind",
        ["no-endpoint", "bad-cursor", "bad-config", "bad-profile", "absent-input",
         "bad-endpoint"],
    )
    def test_a_run_exiting_before_the_open_prints_nothing(self, argv_kind, tmp_path):
        """AC-0019, every reason, because they return from six different points.

        `_argv_for` appends `--report-cursor` to every case. Without it AC-0002
        already requires an empty stdout and none of these would prove anything.
        `bad-cursor` is here because the cursor is parsed before the endpoint is
        resolved, making it another pre-open exit -- the reason this case was
        missing from the first draft.
        """
        out = io.StringIO()
        cli.main(_argv_for(argv_kind, tmp_path), env=_env_for(argv_kind),
                 stream=io.StringIO(), out=out)
        assert out.getvalue() == ""

    def test_an_interrupted_run_prints_nothing(self, tmp_path, monkeypatch):
        """AC-0020. SIGINT arrives in the send loop, so that is where it is raised."""
        def boom(*args, **kwargs):
            raise KeyboardInterrupt

        monkeypatch.setattr(cli, "send_batches", boom)
        out = io.StringIO()
        code = _run_against_receiver(tmp_path, monkeypatch, out=out,
                                     extra=["--report-cursor"])
        assert code == 130
        assert out.getvalue() == ""


class TestNoWriteSurface:
    @staticmethod
    def _tree(root):
        """Every regular file under the root, with content and mtime.

        Names alone cannot see a file whose content was rewritten in place, and a
        single directory cannot see a checkpoint written to a subdirectory.
        """
        return {
            path.relative_to(root).as_posix(): (
                path.read_bytes(), path.stat().st_mtime_ns
            )
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    def test_no_file_under_the_root_changes_across_a_resume_sequence(
        self, tmp_path, monkeypatch
    ):
        """AC-0018. The baseline is taken before the FIRST run, not between runs.

        Snapshotting after run one puts any checkpoint run one wrote inside the
        baseline, so the comparison ratifies it. That is how this case was first
        drafted, and it could not fail.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(b'{"ts": "2026-01-01T00:00:00Z", "result": "ok"}\n')
        before = self._tree(tmp_path)
        assert before, "an empty baseline would make the comparison vacuous"

        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out, target=target,
                              extra=["--report-cursor"])
        assert self._tree(tmp_path) == before

        _run_against_receiver(tmp_path, monkeypatch, out=io.StringIO(),
                              target=target,
                              extra=["--report-cursor",
                                     "--from-cursor", out.getvalue().strip()])
        assert self._tree(tmp_path) == before
```

- Verifies AC-0001, AC-0022, AC-0002, AC-0003, AC-0011 end to end, AC-0012,
  AC-0023 and AC-0030 at the command, AC-0025, AC-0026, AC-0028, AC-0032,
  AC-0018, AC-0019, AC-0020.

**Approach:**

- Add `--from-cursor` and `--report-cursor`; add `out` to `main` and `_run`,
  defaulting to `sys.stdout`, mirroring the existing `stream` parameter.
- Parse `--from-cursor` before `resolve_endpoint`, so an argument error is
  decided before anything else and cannot be masked by the unconfigured path.
- `_run` passes `on_position` into the reader and threads the batcher's
  three-tuples into `send_batches`. The call at `cli.py:147` changes shape here;
  T5 patches `cli.batch_records`, so that name has to be the one `_run` calls.
- Compute the reported offset in exactly one place, after the reader is drained:
  `offset = outcome.accepted_offset`, raised to the reader's final position only
  when `outcome.all_accepted`.
- Print the cursor before both of `_run`'s remaining returns, so the
  no-valid-record exit reports its consumed position too.

**Done when:** the stub passes and the round-trip case sends nothing on the
second run.

### T5: The offset's whole-journey check

**Depends on:** T4

**Touches:** `packages/jsonl-otlp-exporter/tests/unit/test_cli.py`

**Tests:**

Validated stub. Verification mode: TDD.

```python
"""AC-0004, AC-0009 and AC-0031 — over the assembled command.

Also in tests/unit/test_cli.py. Adds `import ast`, `import functools`,
`import pathlib`, `import jsonl_otlp_exporter` and
`from jsonl_otlp_exporter import transport as tp` to that module, on top of
what T4 adds.
"""


class TestOffsetJourney:
    def test_a_clean_run_advances_past_trailing_skipped_lines(self, tmp_path,
                                                              monkeypatch):
        """AC-0004's skipped-line members: the offset is the reader's position,
        not the last batch's, whenever every batch was accepted."""
        target = tmp_path / "events.jsonl"
        target.write_bytes(
            b'{"ts": "2026-01-01T00:00:00Z", "result": "ok"}\n'
            b"not json\n"
            b"also not json\n"
        )
        out = io.StringIO()
        code = _run_against_receiver(tmp_path, monkeypatch, out=out,
                                     extra=["--report-cursor"], target=target)
        assert code == 0
        assert json.loads(out.getvalue())["offset"] == len(target.read_bytes())

    def test_a_clean_run_advances_past_an_over_ceiling_record(self, tmp_path,
                                                              monkeypatch):
        """AC-0004's over-ceiling member, which no other case reaches.

        The ceiling is lowered rather than an 8 MiB fixture built: the criterion
        is about the offset, not about the number 8388608, and the batcher already
        takes its ceiling as a value. Without this case a build that holds the
        cursor before an undeliverable record passes every other check and then
        re-reads and re-declines it on every future run, re-sending the whole
        tail behind it each time.
        """
        target = tmp_path / "events.jsonl"
        pad = "x" * 4096
        target.write_bytes(
            b'{"ts": "2026-01-01T00:00:00Z", "result": "ok"}\n'
            + ('{"ts": "2026-01-01T00:00:01Z", "result": "ok", "pad": "%s"}\n'
               % pad).encode("utf-8")
        )
        # The ceiling is injected through the existing `max_bytes` parameter,
        # NOT by patching `tp.MAX_BODY_BYTES`: `batch_records` binds
        # that constant as a default at definition time, so rebinding the module
        # attribute changes nothing and the 4 KiB record stays under the real
        # 8 MiB bound. Patching the CLI's imported name is the shape
        # `test_cli.py` already uses for `send_batches` and `iter_records`.
        monkeypatch.setattr(
            cli, "batch_records",
            functools.partial(tp.batch_records, max_bytes=1024),
        )
        out = io.StringIO()
        stream = io.StringIO()
        code = _run_against_receiver(tmp_path, monkeypatch, out=out, stream=stream,
                                     extra=["--report-cursor"], target=target)
        assert code == 0
        assert "cannot be split" in stream.getvalue()
        assert json.loads(out.getvalue())["offset"] == len(target.read_bytes())

    def test_the_distribution_has_no_write_or_lock_surface(self):
        """AC-0031. The surface, not one run's effect on one directory.

        AC-0018 snapshots a tree after a run, so it cannot see a write to a path
        outside it or a lock that leaves no file behind. This walks the shipped
        modules instead, so a write surface fails it whether or not any test
        exercises the branch that uses it.

        `rglob`, not `glob`: a module in a subpackage is still shipped.
        Root-qualified for the ambiguous names, because `encode.py:66` calls
        `str.replace` and a bare-name denylist fails on it -- and rooted rather
        than taking the immediate receiver, because `Path(p).unlink()` has a Call
        there. `open`'s mode is read from `mode=` as well as position, and a
        non-literal mode is an offender in itself.
        """
        package = pathlib.Path(jsonl_otlp_exporter.__file__).parent
        bare = {"write_text", "write_bytes", "mkdir", "makedirs", "touch",
                "mkstemp", "mkdtemp", "NamedTemporaryFile", "TemporaryFile",
                "TemporaryDirectory", "lockf", "flock", "locking"}
        qualified = {"write", "writelines", "pwrite", "rename", "replace",
                     "remove", "unlink", "rmdir", "truncate", "ftruncate",
                     "symlink", "link", "chmod", "dup2", "copy", "copyfile",
                     "copytree", "move"}
        receivers = {"os", "shutil", "tempfile", "pathlib", "Path"}
        modules = {"fcntl", "msvcrt", "shutil", "tempfile", "sqlite3", "dbm",
                   "shelve"}
        write_flags = {"O_WRONLY", "O_RDWR", "O_CREAT", "O_APPEND", "O_TRUNC"}
        offenders = []

        def _root(node):
            """The root name of an attribute chain, through calls and subscripts.

            `Path(p).replace(q)` roots at `Path`; `text.replace(a, b)` roots at
            `text`. Reading only the immediate receiver misses the first,
            because there the receiver is itself a Call -- which is how
            `Path(p).unlink()` passed the previous draft.
            """
            while True:
                if isinstance(node, ast.Attribute):
                    node = node.value
                elif isinstance(node, (ast.Call,)):
                    node = node.func
                elif isinstance(node, ast.Subscript):
                    node = node.value
                else:
                    return getattr(node, "id", None)

        sources = sorted(package.rglob("*.py"))
        assert sources, "an empty module set would make this vacuous"
        for module in sources:
            tree = ast.parse(module.read_text(encoding="utf-8"))
            where = f"{module.relative_to(package)}"
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in modules:
                            offenders.append((where, node.lineno, alias.name))
                elif isinstance(node, ast.ImportFrom):
                    if (node.module or "").split(".")[0] in modules:
                        offenders.append((where, node.lineno, node.module))
                elif isinstance(node, ast.Call):
                    func = node.func
                    name = getattr(func, "attr", None) or getattr(func, "id", None)
                    if name in bare:
                        offenders.append((where, node.lineno, name))
                    elif name in qualified and _root(func) in receivers:
                        offenders.append((where, node.lineno, f"{_root(func)}.{name}"))
                    elif name == "open" and _root(func) == "os":
                        # `os.open`'s second argument is FLAGS, not a mode. An
                        # earlier draft ran the mode rule here and reported every
                        # `os.open(p, os.O_RDONLY | os.O_NOFOLLOW)` in the
                        # shipped package as a computed mode -- three false
                        # positives, which would have made the guard unusable on
                        # the day it landed.
                        for arg in list(node.args[1:]) + [
                            kw.value for kw in node.keywords
                        ]:
                            for inner in ast.walk(arg):
                                flag = (inner.attr if isinstance(inner, ast.Attribute)
                                        else getattr(inner, "id", None))
                                if flag in write_flags:
                                    offenders.append(
                                        (where, node.lineno, f"os.open {flag}")
                                    )
                    elif name == "open":
                        # `open(path, mode)` puts the mode second; the method
                        # form `p.open(mode)` puts it FIRST. Reading index 1
                        # unconditionally let `Path(p).open("w")` through.
                        index = 1 if isinstance(func, ast.Name) else 0
                        mode = next(
                            (kw.value for kw in node.keywords if kw.arg == "mode"),
                            node.args[index] if len(node.args) > index else None,
                        )
                        if mode is not None:
                            try:
                                literal = ast.literal_eval(mode)
                            except ValueError:
                                # A computed mode is itself a failure: this
                                # distribution has no reason to build one, and
                                # admitting it lets `"w" + "b"` through.
                                offenders.append((where, node.lineno, "computed mode"))
                            else:
                                if any(ch in str(literal) for ch in "wax+"):
                                    offenders.append(
                                        (where, node.lineno, f"open {literal!r}")
                                    )
        assert offenders == []

    def test_every_reported_offset_lands_on_a_record_boundary(self, tmp_path,
                                                              monkeypatch):
        """AC-0009 over the assembled command, across accepted and refused runs."""
        target = tmp_path / "events.jsonl"
        data = b"".join(
            b'{"ts": "2026-01-01T00:00:0%dZ", "result": "ok"}\n' % i for i in range(5)
        )
        target.write_bytes(data)
        for statuses in ([200], [400], [200, 400], [200, 200]):
            out = io.StringIO()
            _run_against_receiver(tmp_path, monkeypatch, out=out, statuses=statuses,
                                  extra=["--report-cursor"], target=target)
            offset = json.loads(out.getvalue())["offset"]
            assert offset == 0 or data[offset - 1 : offset] == b"\n", (statuses, offset)
```

- Verifies AC-0004 — including its skipped-line and over-ceiling members —
  AC-0009 over the assembled command, and AC-0031 over the shipped modules.

**Approach:** no production change. Two things live here that the per-module
tasks cannot give: the integrated offset, computed from two mechanisms in two
modules, and AC-0031's walk over the whole shipped package rather than one
module.

AC-0031's predicate was run before this plan was approved, because a guard that
passes on day one proves nothing until you have seen it fail. Measured
2026-09-15 against the shipped package: 7 modules, 0 offenders. Against
synthetic sources it reported an offender for each of `Path(p).unlink()`,
`Path(p).replace(q)`, `open(p, "w" + "b")`, `open(p, mode="w")`,
`os.lockf(f, 1, 0)`, `import shutil`, `pathlib.Path(p).write_text("x")` and
`os.open(p, os.O_WRONLY | os.O_CREAT)` — every escape shape a reviewer named —
and stayed clean on `text.replace("a", "b")`, `stream.write("x")`,
`open(p, "rb")`, `os.open(p, os.O_RDONLY | os.O_NOFOLLOW)` and `d["k"].get("x")`.

**Done when:** all four cases pass — the two offset cases, the over-ceiling
case, and AC-0031's walk.

### T6: The published contract

**Depends on:** T5

**Touches:** `packages/jsonl-otlp-exporter/README-pypi.md`,
`packages/jsonl-otlp-exporter/CHANGELOG.md`,
`packages/jsonl-otlp-exporter/tests/unit/test_published_contract.py`

**Tests:**

- `no stub (goal-based)`. Reason: the outcome is a literal string in an authored
  file, and `test_published_contract.py` already owns exactly this check shape
  for the parent contract's AC-0030 and AC-0032. A stub would restate the
  assertion the existing module makes.
- `README-pypi.md` carries `## Resuming a run` containing `--from-cursor`,
  `--report-cursor`, `the caller stores the cursor`, and `at-least-once`.
  Verifies AC-0021.

**Approach:**

- Add `## Resuming a run` to `README-pypi.md`: the two flags, the cursor's
  opaqueness and its `v` field, the reset-to-zero behaviour, that the caller
  stores the cursor, and that concurrent callers double-send.
- Add both flags to the existing `## Options` table.
- Name both flags under the existing unreleased `## 0.1.0` entry. No version
  bump: 0.1.0 has not shipped, so this surface is part of the first release, and
  bumping to 0.2.0 would publish a 0.1.0 that never existed. This reading of
  `packages/AGENTS.md`'s bump rule is recorded in the verification ledger.

**Done when:** AC-0021's check passes and the real console script runs end to
end — a resumed second run against an unchanged file sends nothing and reports
the same cursor.

### T7: A resumed run with nothing new

**Depends on:** T4

**Touches:** `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/cli.py`,
`packages/jsonl-otlp-exporter/tests/unit/test_cli.py`

**Tests:**

Validated stub. Verification mode: TDD.

```python
"""AC-0033, AC-0034 — the steady state of a repeated run.

Appended to tests/unit/test_cli.py, which already has every name this needs.
"""


class TestNothingNewPastTheCursor:
    def test_a_resumed_run_with_nothing_new_exits_zero(self, tmp_path,
                                                       monkeypatch):
        """AC-0033. Found by manual QA of the installed wheel, not by the suite.

        This is the normal state of a polling caller, and it exited 1 because
        the parent contract's `emitted == 0` predicate reads an empty read as an
        all-invalid input. Nothing in the suite drove a second run against an
        unchanged file and checked its status -- the round-trip case that
        existed asserted only that nothing was re-sent.
        """
        out = io.StringIO()
        assert _run_against_receiver(tmp_path, monkeypatch, out=out,
                                     extra=["--report-cursor"]) == 0
        cursor = out.getvalue().strip()

        second, stream, sent = io.StringIO(), io.StringIO(), []
        code = _run_against_receiver(
            tmp_path, monkeypatch, out=second, stream=stream, sent=sent,
            extra=["--report-cursor", "--from-cursor", cursor],
        )
        assert code == 0
        assert sent == []
        assert json.loads(second.getvalue()) == json.loads(cursor)

    def test_that_run_says_no_record_lay_past_the_cursor(self, tmp_path,
                                                         monkeypatch):
        """AC-0034. Split from AC-0033: the two fail independently."""
        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out,
                              extra=["--report-cursor"])
        cursor = out.getvalue().strip()

        stream = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=io.StringIO(),
                              stream=stream,
                              extra=["--report-cursor", "--from-cursor", cursor])
        message = stream.getvalue()
        assert "past the cursor" in message
        assert "no line yielded a valid record" not in message, (
            "the old message described invalid lines when no line was read"
        )

    def test_an_all_invalid_input_still_exits_one(self, tmp_path, monkeypatch):
        """The carve-out must not widen to any empty send.

        A build that exits 0 whenever nothing was emitted passes AC-0033 and
        converts a real failure into success. This is the case that separates
        "read no line" from "read lines, emitted nothing".
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(b"not json\n" * 3)
        stream = io.StringIO()
        code = _run_against_receiver(tmp_path, monkeypatch, target=target,
                                     stream=stream, out=io.StringIO(),
                                     extra=["--report-cursor"])
        assert code == 1
        assert "no line yielded a valid record" in stream.getvalue()

    def test_a_reset_cursor_against_an_empty_file_exits_one(self, tmp_path,
                                                            monkeypatch):
        """The witness against substituting "a cursor was supplied" for the
        non-zero honoured start.

        A cursor IS supplied and `consumed == begin` holds — both are 0, because
        the identity mismatch reset the offset and the file is empty. A build
        testing `from_cursor is not None and consumed == begin and emitted == 0`
        passes every other case here and exits 0 for this one. Only the
        *honoured non-zero* reading of `begin` separates them.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(b"")
        stale = json.dumps({"v": 1, "offset": 40, "device": 1, "inode": 2})
        stream, sent = io.StringIO(), []
        code = _run_against_receiver(tmp_path, monkeypatch, target=target,
                                     stream=stream, sent=sent, out=io.StringIO(),
                                     extra=["--report-cursor",
                                            "--from-cursor", stale])
        assert code == 1
        assert sent == []
        assert "identity changed" in stream.getvalue()
        assert "no line yielded a valid record" in stream.getvalue()

    def test_an_empty_input_with_no_cursor_exits_one(self, tmp_path, monkeypatch):
        """The case that makes the non-zero-begin half load-bearing.

        Every other case here either consumes a line or resumes from a non-zero
        offset, so a build testing only `emitted == 0 and consumed == begin`
        passes all of them — and then exits 0 for an empty file with no cursor,
        where `begin` and `consumed` are both 0. The parent contract's AC-0039
        and its exit table both claim 1 for that.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(b"")
        stream, sent = io.StringIO(), []
        code = _run_against_receiver(tmp_path, monkeypatch, target=target,
                                     stream=stream, sent=sent, out=io.StringIO(),
                                     extra=["--report-cursor"])
        assert code == 1
        assert sent == []
        assert "no line yielded a valid record" in stream.getvalue()

    def test_an_honoured_cursor_followed_by_invalid_lines_exits_one(
        self, tmp_path, monkeypatch
    ):
        """The case that makes the `consumed == begin` half of the check load-bearing.

        Every other case here starts at byte 0, so a build testing only
        `begin != 0 and emitted == 0` passes all of them while converting a
        genuine all-invalid tail into success. This one resumes from an honoured
        non-zero cursor AND reads lines, so only the consumed-nothing half can
        separate it from the carve-out.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(GOOD_LINE.encode("utf-8"))
        out = io.StringIO()
        assert _run_against_receiver(tmp_path, monkeypatch, out=out, target=target,
                                     extra=["--report-cursor"]) == 0
        cursor = out.getvalue().strip()
        assert json.loads(cursor)["offset"] > 0, "the cursor must be non-zero"

        with open(target, "ab") as handle:
            handle.write(b"not json\n")

        stream, sent = io.StringIO(), []
        code = _run_against_receiver(
            tmp_path, monkeypatch, out=io.StringIO(), stream=stream, sent=sent,
            target=target, extra=["--report-cursor", "--from-cursor", cursor],
        )
        assert code == 1, "lines were read and none was valid: that is still a failure"
        assert sent == []
        assert "no line yielded a valid record" in stream.getvalue()

    def test_a_reset_that_finds_nothing_still_exits_one(self, tmp_path,
                                                        monkeypatch):
        """A reset reads from byte 0, so an empty result there is AC-0039's case.

        Distinguishes the carve-out's precondition -- an HONOURED non-zero
        cursor -- from merely having been given a cursor.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(b"not json\n")
        stale = json.dumps({"v": 1, "offset": 5, "device": 1, "inode": 2})
        stream = io.StringIO()
        code = _run_against_receiver(tmp_path, monkeypatch, target=target,
                                     stream=stream, out=io.StringIO(),
                                     extra=["--report-cursor",
                                            "--from-cursor", stale])
        assert code == 1
        assert "identity changed" in stream.getvalue()
```

- Verifies AC-0033 and AC-0034, and pins the five cases the carve-out must not
  reach. Three wrong implementations each have their own witness, and none of
  the three is caught by the others:
  - drops `consumed[0] == begin` → caught by an honoured non-zero cursor whose
    newly appended lines are all invalid;
  - drops the non-zero-`begin` requirement → caught by an empty input with no
    cursor, where `begin` and `consumed` are both 0;
  - substitutes "a cursor was supplied" for "an honoured non-zero `begin`" →
    caught by a reset cursor against an empty file, where a cursor is present
    and `consumed == begin == 0`.
  The all-invalid-from-zero and reset-consumes-an-invalid-line cases cover the
  ordinary paths.

**Approach:**

- In `_run`, the `emitted[0] == 0` branch gains one precondition: when the run
  began at a non-zero honoured offset and the reader consumed nothing
  (`consumed[0] == begin`), report that no record lay past the cursor and return
  `EXIT_OK`. Every other empty-send path keeps its message and its exit 1.
- `begin` is already the honoured offset: a reset returns 0 from
  `resolve_start_offset`, so `begin` is falsy on that path and the carve-out
  cannot apply to it. That is what makes T7's fourth case pass without a second
  flag to thread.

**Done when:** all four cases pass, and the installed console script exits 0 on
a second run against an unchanged file.

### T8: Repairs from the implementation review

**Depends on:** T7

**Touches:** `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/cli.py`,
`packages/jsonl-otlp-exporter/jsonl_otlp_exporter/source.py`,
`packages/jsonl-otlp-exporter/tests/unit/test_cli.py`,
`packages/jsonl-otlp-exporter/tests/unit/test_cursor.py`

**Tests:**

Validated stub. Verification mode: TDD.

```python
"""AC-0001's exit-1 half, AC-0035, and four controls review found missing.

Appended to tests/unit/test_cli.py and tests/unit/test_cursor.py, both of which
already have every name these need.
"""


class TestWhichRunsReportACursor:
    """tests/unit/test_cli.py. AC-0001 and AC-0035."""

    def test_a_run_that_emitted_nothing_still_reports_its_cursor(self, tmp_path,
                                                                 monkeypatch):
        """AC-0001's exit-1 half, which no case asserted.

        Only the exit-0 path was checked, and every opened-input exit-1 case
        discarded its stdout buffer — so a build printing the cursor on success
        alone passed the whole suite.
        """
        target = tmp_path / "events.jsonl"
        target.write_bytes(b"not json\n" * 2)
        out = io.StringIO()
        code = _run_against_receiver(tmp_path, monkeypatch, out=out, target=target,
                                     extra=["--report-cursor"])
        assert code == 1
        assert json.loads(out.getvalue())["offset"] == len(target.read_bytes())

    def test_a_boundary_refusal_reports_no_cursor(self, tmp_path, monkeypatch):
        """AC-0035. The refusal happens after the open, so AC-0019 cannot own it."""
        target = tmp_path / "events.jsonl"
        target.write_bytes(GOOD_LINE.encode("utf-8") * 2)
        out = io.StringIO()
        _run_against_receiver(tmp_path, monkeypatch, out=out, target=target,
                              extra=["--report-cursor"])
        cursor = json.loads(out.getvalue())
        cursor["offset"] -= 1

        second, stream = io.StringIO(), io.StringIO()
        code = _run_against_receiver(
            tmp_path, monkeypatch, out=second, stream=stream, target=target,
            extra=["--report-cursor", "--from-cursor", json.dumps(cursor)],
        )
        assert code == 1
        assert second.getvalue() == ""
        assert "not a record boundary" in stream.getvalue(), (
            "an automated caller gets exit 1 and needs to know why"
        )


class TestReviewRepairs:
    """tests/unit/test_cli.py. Controls for cases that could not fail."""

    def test_a_later_batch_refusal_still_lands_on_a_boundary(self, tmp_path,
                                                             monkeypatch):
        """The multi-status cases never consumed their second status.

        `MAX_RECORDS_PER_REQUEST` is 512, so five records were one batch and
        `[200, 400]` exercised only the 200. Batching one record per request is
        what makes the second status reachable, and with it the accepted-prefix
        path where a later batch is refused.
        """
        target = tmp_path / "events.jsonl"
        data = b"".join(
            json.dumps({"at": f"2026-01-01T00:00:0{i}Z", "result": "success",
                        "run_id": "r", "seq": i, "event": "e"}).encode("utf-8")
            + b"\n"
            for i in range(3)
        )
        target.write_bytes(data)
        monkeypatch.setattr(
            cli, "batch_records",
            functools.partial(tp.batch_records, max_records=1),
        )
        out = io.StringIO()
        # THREE batches, not four: `MAX_ATTEMPTS_PER_RUN` is 3, so a fourth
        # batch is never issued and the accepted-after-refused batch this case
        # exists to catch never happens. Proven -- with four batches the
        # high-water-mark defect survived this very test.
        code = _run_against_receiver(tmp_path, monkeypatch, out=out, target=target,
                                     statuses=[200, 400, 200],
                                     extra=["--report-cursor"])
        assert code == 1
        offset = json.loads(out.getvalue())["offset"]
        assert data[offset - 1:offset] == b"\n", offset
        assert offset < len(data), (
            "a refused third batch must not be credited, nor any batch after it"
        )
```

```python
"""tests/unit/test_cursor.py — two refusal controls review found missing."""


class TestRefusalControls:
    def test_a_decoder_exception_of_any_type_becomes_a_refusal(self, monkeypatch):
        """The broad `except` had no control that could fail.

        The deep-nesting fixture does not make either scanner raise at this byte
        bound — measured — so a build that caught only `JSONDecodeError` passed
        it by refusing on shape instead. Forcing the decoder to raise something
        else is the only way to reach the clause.
        """
        def boom(*args, **kwargs):
            raise RecursionError("forced")

        monkeypatch.setattr(cur.json, "loads", boom)
        with pytest.raises(cur.CursorRefused):
            cur.parse_cursor('{"v": 1, "offset": 0, "device": 1, "inode": 2}')

    def test_a_boolean_version_is_refused(self):
        """`True == 1` in Python, so a `raw["v"] != 1` check accepts JSON `true`.

        Bool rejection was pinned for `offset` only. The version field decides
        whether a stored cursor is readable at all, so it needs its own case.
        """
        with pytest.raises(cur.CursorRefused):
            cur.parse_cursor('{"v": true, "offset": 0, "device": 1, "inode": 2}')
```

- Verifies AC-0001's exit-1 half, AC-0035, and adds controls for the
  later-batch-refusal path, the decoder-exception clause, and the boolean
  version field.

**Approach:**

- `cli.py` passes the size it already captured into the reader, as
  `size_at_open=info.st_size`. The reader took its own `os.fstat` when the lazy
  generator first ran, which is a later instant than the CLI's: a concurrent
  append in between enlarged the budget and let a resumed one-shot run read more
  than the `S - N` bytes AC-0017 allows. The parameter defaults to `None`, in
  which case the reader fstats itself, so every existing caller and case is
  unchanged.
- No change is made to `_partial_success`. Its `AttributeError` on a 2xx body
  that is valid JSON but not an object is real and was found by this review, but
  the function is byte-identical to `HEAD` — it is a pre-existing defect on a
  shipped path, not something this change introduced, and repairing it is a
  behaviour change outside the bundled-fixes tiers. Recorded in
  `[backlog].open` instead.

**Done when:** all five cases pass, the reader reads no more than the size the
CLI observed at open, and every control has been observed failing against the
wrong implementation it guards.

**Round-2 strengthening.** A second quality pass found two of these controls
still satisfiable. The decoder case raised `RecursionError`, which an
implementation catching `(JSONDecodeError, RecursionError)` also passes; it now
raises a test-local exception type no whitelist can name. And
`test_a_skipped_line_still_advances_the_position` — introduced by T2, whose
section is not edited because that task is complete — asserted only the final
offset, which equals EOF, so a reader reporting the descriptor's own position
for every record passed it. The case now also pins the delta across the skipped
line. Both were proven to catch their implementation before being trusted.

## Risks

- **The accepted prefix is the load-bearing defect surface.** `send_batches`
  continues after a non-retryable status, so the natural implementation (a
  high-water mark) is wrong in exactly the case that loses records. T3's second
  stub case exists only to catch it, and it is the case to re-check after any
  later edit to that loop.
- **Widening the batch tuple touches ~30 existing test call sites.** Mechanical,
  and mypy plus the existing suite find every one, but it makes the diff larger
  than the behaviour change and a reviewer should read the two apart.
- **The wiring sweep must stay clean.** Five new cross-module keywords each need
  a control that fails on their removal; the Construction tests section names
  which case is each one's.

## Review-round accounting — a stated deviation

The engine's `state.json` shows `review_round_count: 0` and
`review_retry_count: 0`, and that is not what happened. Ten reviewer passes ran
against these artifacts before the spec gate: seven on the contract lens and
three on secure design. Their raw reports are persisted under
`.context/reviews/82f1e2a2-049e-4770-a215-634d011eb1a2/`, numbered in the order
they ran.

The `findings-remain` / `spec-ready` cycle was not fired between rounds, so the
engine's retry cap never engaged. The substance is recorded below instead: every
round's findings, which were sustained, and what each repair changed. Firing the
cycle retroactively would write round counts into `state.json` that were never
true at the times it stamps, which is worse than an accurate note beside an
honest zero.

What the cap exists to catch is a loop that stops converging. This one did not
stall — each round found defects the previous round's repairs introduced or
missed, the last two rounds returned clean on both lenses with 60,834 and 21,019
tokens spent, and the final two contract findings were the most serious of the
whole sequence. But the cap not running is a real gap, and the owner should read
the sequence below rather than trust a counter that says nothing happened.

## Changelog

- 2026-09-16 — second contract amendment, from the implementation review. Three
  reviewers ran against the diff on disjoint scopes; the security lens returned
  clean. AC-0001 required a cursor line after any exit of 0 or 1 from a run that
  opened its input, which the AC-0030 boundary refusal cannot satisfy — it is
  refused after the open and has no offset it could honestly report, since the
  supplied one is what was refused and byte 0 would mean re-send everything.
  AC-0001 is now conditioned on reaching the send loop, and AC-0035 owns the
  refusal. The quality lens found the same criterion untested on its exit-1
  half, which is how the over-broad wording survived.
  Four controls that could not fail were also found and are repaired in T8: the
  multi-status offset cases never consumed their second status, because 512
  records fit one batch; the decoder-exception clause had no case that made the
  decoder raise; the boolean rejection was pinned for `offset` but not for `v`,
  where `True == 1` would let a naive check through; and the command-level
  misaligned-cursor case asserted no stderr, so a silent refusal passed.
  One finding is pre-existing and deliberately not repaired: `_partial_success`
  raises `AttributeError` on a 2xx body that is valid JSON but not an object.
  Byte-identical to `HEAD`, so it ships today; recorded in `[backlog].open`.

- 2026-09-16 — review of the amendment, round 3. One finding, sustained. Both
  halves of the carve-out's condition had a witness, but a third wrong shape did
  not: substituting "a cursor was supplied" for "an honoured non-zero `begin`"
  passed all six cases, because no case combined a supplied cursor with a reset
  to zero *and* an empty read. The reset case that existed consumes an invalid
  line, so `consumed != begin` there. A seventh case supplies a
  mismatched-identity cursor against an empty file, where a cursor is present
  and `consumed == begin == 0`. The reviewer confirmed the criteria themselves
  consistent across all five cases it was asked to walk, and the deferred
  `--follow` residual accurately stated.
- 2026-09-16 — review of the amendment, round 2. Two findings, both introduced
  by round 1's own repairs. The parent AC-0039 exception omitted AC-0033's "no
  mode flag" qualifier, so it covered `--follow` while the resume criterion did
  not; the two scopes now match, and the residual — a bounded follow run that
  finds nothing new still exits 1 — is recorded under Follow-ons with its reason
  rather than widened. T7's reset case consumed an invalid line, so no case
  started at byte zero *and* consumed nothing: a build omitting the
  non-zero-`begin` half passed every test and would exit 0 for an empty file
  with no cursor. Each half of the condition now has its own witness.
- 2026-09-16 — review of the amendment itself. Two findings, both sustained.
  T7's stub could not reject a build checking only `begin != 0 and emitted == 0`
  and omitting the `consumed == begin` half: every case it carried started at
  byte 0, so the wrong build would have converted a genuine all-invalid tail
  into success. A fifth case resumes from an honoured non-zero cursor and then
  appends an invalid line. The reworded parent AC-0039 also went too far: "reads
  at least one line and finds none valid" left an empty input with no cursor
  pinned by nothing, while the exit table still claims 1 for it. It is now
  stated as an exception to the original rule rather than a rewrite of it.
- 2026-09-16 — contract amendment, authorised by the owner and recorded in
  `notes/verification-ledger.md`. Manual QA of the installed wheel found that a
  resumed run whose cursor sits at the end of its input exits 1 — the steady
  state of the polling caller this feature exists for. The cause is the parent
  contract's AC-0039, whose `emitted == 0` predicate cannot separate an
  all-invalid input from an empty read; the two were nearly the same condition
  until a run could start part-way through the file. AC-0033 and AC-0034 carve
  that case out, parent AC-0039 is reworded to match, and T7 implements it. Ten
  of the eleven QA scenarios needed no change.
  Worth naming: the suite could not have caught this. Its round-trip case
  resumed over an unchanged file and asserted only that nothing was re-sent —
  it never checked the exit status, and a wrong status passes a
  nothing-was-sent assertion.

- 2026-09-15 — drafted.
- 2026-09-15 — contract review of the previous round's own two repairs. Four
  blockers, all introduced by those repairs. AC-0001's new precondition read "was
  not interrupted", which is not an observable property; it is now an exit status
  of 0 or 1, and the sentence claiming AC-0001, AC-0019 and AC-0020 partition
  every run was simply false and is gone — a completed run without
  `--report-cursor` matches none of the three, because AC-0002 owns it. AC-0032
  was sloppy in three ways and demanded the sending of every case the contract
  deliberately does not send: an unterminated final line (AC-0010 forbids
  consuming it), a line yielding no admitted record, and a record over the
  request-body ceiling (AC-0004's set names it). It now excludes all three.
  Its one-shot scope is kept and the reason recorded under Follow-ons rather
  than widened: a time-bounded run's completeness needs a duration floor this
  spec has no basis for inventing.
- 2026-09-15 — final contract review. Two blockers, both in the original
  contract rather than in a repair. AC-0001 required exactly one stdout line
  under `--report-cursor` unconditionally, which contradicted AC-0019 for a run
  with no endpoint configured and AC-0020 for an interrupted run; it now names
  the run it describes and the three criteria partition every run between them.
  The second is the more serious and had survived four rounds: AC-0017 and
  AC-0029 bound how much a resumed run may read and nothing required it to send
  anything, so a build that seeks to the cursor, reads zero bytes and exits
  satisfied both while losing every pending record. AC-0032 is the completeness
  half. Its stub appends records after a first run and requires exactly those on
  the wire — the round-trip case that existed resumes over an unchanged file and
  asserts nothing is sent, which the same empty build also passes.
- 2026-09-15 — stub validation gained a keyword check, which immediately found
  `_FakeResponse(body=...)` in T3 where the helper's keyword is `payload=`. The
  name check could not see it, and it is the same class as round 4's
  `_records(fd)`: a helper that exists, called in a way that raises. Proven able
  to fail before being trusted — against `test_transport.py`'s real signatures
  it reports `body` for the defect and nothing for `payload=`, `status=` or a
  correct `_dest(url=...)`.
- 2026-09-15 — stub validation re-run to green: 6 blocks, 0 unresolved. See
  `## Stub validation` for the method and what it caught.
- 2026-09-15 — stub validation, applying round 4's standing correction before
  the next review round rather than after it. A script parses every fenced
  Python block in this plan and resolves each block's free names against the
  test module it is appended to. All five blocks parse. It found six unresolved
  names the reviewers had not reached: T2 used `mock`, which `test_source.py`
  does not import and which `packages/AGENTS.md` steers away from in favour of
  `monkeypatch`; T4 used `os` plus three helpers — `_run_against_receiver`,
  `_argv_for`, `_env_for` — that this plan never specified; and T5 used `ast`,
  `functools`, `pathlib`, `jsonl_otlp_exporter` and `tp` without saying they are
  added to that module. The helpers now have a `## New test helpers` section and
  every stub states the imports it adds.
- 2026-09-15 — pre-EXECUTE convergence review, round 4. Four findings, all
  sustained, all drift from round 3's own repairs. Three were in stub code rather
  than in the contract: T2 called `_records(fd)` when the module's helper takes
  `(path, root)` and opens the input itself; T2's completion statement said the
  existing cases pass unchanged when seven of them call `iter_records` directly
  and must unwrap the new pair; and T2's approach still described `iter_records`
  as a two-line delegation to a twin that no longer exists. The fourth is a real
  hole in AC-0031: `Path(p).open("w")` puts its mode at argument zero, so reading
  index one unconditionally let the method form through.
  The round also refuted a claim of this plan's own. The reader-churn bullet said
  one helper funnelled almost every case; the count is one helper plus seven
  direct calls. That claim was the stated reason for the `*_positioned` twin, so
  it is corrected in place rather than quietly dropped — keeping one reader
  survives the real number, but it no longer rests on a wrong one.
  Standing correction from this round: three of the four findings were things
  running the stub would have surfaced in seconds. Stub validation moves ahead of
  the next review round rather than after it.
- 2026-09-15 — pre-EXECUTE convergence review, round 3. Four findings, all
  sustained, three of them drift from earlier repairs. AC-0013 and AC-0024 now
  require a matching identity: without it a cursor whose identity differed *and*
  whose offset exceeded the new file's size matched both reset criteria, so the
  routing was total but not disjoint. AC-0031's walk resolves an attribute
  chain's root rather than its immediate receiver — `Path(p).unlink()` puts a
  Call there and passed — and treats a computed `open` mode as an offender, so
  `"w" + "b"` no longer slips by. Running the repaired predicate then found a
  defect the reviewer had not: it read `os.open`'s flags argument as a mode and
  reported three false positives inside the shipped package, so the two calls are
  now handled by separate rules and conjunct 2 of AC-0031 says why. T5's
  completion statement counted two cases when it had four.
  The fourth finding had a shared root cause with one of round 2's: the plan
  carried a `*_positioned` twin beside `iter_records` and `batch_records` to
  spare the existing suites, which left the CLI needing a call-site swap the plan
  never stated, and left two public functions with nothing consuming them. There
  is now one reader and one batcher. `test_source.py:31`'s `_records` helper
  absorbs most of the reader churn, which is what made the twin look necessary.
- 2026-09-15 — pre-EXECUTE secure-design review, round 2. One blocker, drift
  from round 1's own AC-0031 repair: the stub read `open`'s mode positionally
  only, globbed one directory level, and matched write primitives by bare name.
  `open(p, mode="w")`, `Path(p).write_text(...)`, `os.lockf(...)` and any module
  in a subpackage all passed it, so the control could not enforce its criterion.
  The criterion now states its four conjuncts and its closed name set, the walk
  is recursive, and the ambiguous names are receiver-qualified — `encode.py:66`
  calls `str.replace`, which a bare-name denylist would fail on. The criterion
  also names its blind spot: a write reached through an alias or a dynamic
  lookup is AC-0018's half, not this one's. The reviewer cleared AC-0030 as
  load-bearing and the reader's position rule as closed against every path
  through the shipped loop.
- 2026-09-15 — pre-EXECUTE contract review, round 2. Both findings were drift
  from round 1's own repairs. AC-0030 overlapped AC-0011 and AC-0013, so a
  matching-but-misaligned cursor was simultaneously honoured and refused; the
  four cursor routes now carry mutually exclusive preconditions instead of an
  implied precedence. The new over-ceiling case patched `tp.MAX_BODY_BYTES`,
  which `batch_records` binds as a default at definition time, so the
  case could not have failed for its stated reason — it now injects `max_bytes`
  through the CLI's imported name. The reviewer confirmed the rewritten offset
  procedure assigns exactly one offset across all five cases it was asked to
  attack.
- 2026-09-15 — pre-EXECUTE secure-design review, round 1. Two blockers
  sustained. A schema-valid cursor could seek anywhere inside a matching file,
  so AC-0030 now requires the offset to land on a record boundary and refuses
  rather than resets when it does not — the Boundaries already forbade beginning
  part-way through a record, and nothing enforced it. The reader's position rule
  was wrong in the same direction: it advanced over an over-length line's
  discarded bytes, so an unterminated over-length final line produced a
  mid-record cursor; position now advances only on a consumed newline, and
  AC-0010 gained the fixture that reaches that path. One concern was adopted with
  its premise corrected: a deep-nesting `RecursionError` does not reproduce
  within the 4096-byte bound on this interpreter (measured 2026-09-15), but
  `parse_cursor` catches `Exception` anyway, as `source.py:286` does for the same
  class. AC-0031 was added because AC-0018 can only see one run's effect on one
  directory, and the no-durable-state decision is about the surface.
- 2026-09-15 — pre-EXECUTE contract review, round 1. Five blockers and four
  concerns, eight sustained. The offset criteria were rewritten as one decision
  procedure and AC-0008 retired into AC-0004's enumerated set, because stated
  unconditionally it contradicted AC-0005 for a run with a refused batch and a
  trailing over-ceiling record. AC-0017 gained AC-0011's preconditions, which it
  needed to stop demanding a negative byte ceiling on the reset path, and AC-0029
  now owns the reset path's own bound. AC-0001, AC-0012 and AC-0013 split their
  conjunctions; AC-0027 was drafted and retired when the owner amended the parent
  contract's AC-0033 instead. Four stub cases could not fail for the reason
  claimed and were replaced: the two cursor-length fixtures, refusable on shape
  by a build that never measures; AC-0018's baseline, captured after the first
  run so it ratified anything that run wrote; and the reset cases, asserted at
  the function and never at the command. AC-0004's over-ceiling member and
  AC-0019's malformed-cursor reason had no case at all.
