"""Every client the run reaches issues read methods only.

The boundary is the source-derived invocation set, not the set of skills
the pack ships and not the set the manifest declares. Checking Jira verbs
alone would leave a Confluence or a Jira Align write reachable -- this pack
ships a Confluence publisher -- so "no Jira write verb" does not by itself
make the view read-only.

Each client is exercised against a recording transport standing in for its
CLI, so what the run asked for is observed at the process boundary rather
than inferred from the caller's intent. A client in the derived set that
this run does not happen to reach is exercised directly, because a boundary
with an unexercised member on it is a boundary nobody checked.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

import atlassian_jira_epic_outcome_view_guarantees as guarantees
import pytest

#: The read verbs each client's CLI exposes. Held as an allowlist rather
#: than as a denylist of write verbs: a verb added to a client later is
#: refused here until someone considers it, which is the safe direction for
#: a guarantee that cannot be re-checked at run time.
READ_VERBS = {
    "jira": {"check", "whoami", "get-issue", "search", "get-project"},
    "jira-align": set(),
}

#: The only safe HTTP method on the escape hatch every client exposes.
READ_HTTP_METHOD = "GET"

#: Named so a failure says what was issued, not merely that something was.
WRITE_VERB_SHAPES = (
    "transition", "comment", "create", "update", "delete", "assign",
    "attach", "link", "label", "worklog", "publish", "post", "put", "patch",
)


def _positional(argv: list[str]) -> list[str]:
    """Drop flags and their values, leaving the verb and its operands."""
    rest: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if token in {"--format", "--output", "--fields", "--expand", "--page-size", "--param"}:
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        rest.append(token)
        index += 1
    return rest


def assert_read_only(client: str, argv: list[str]) -> None:
    """One recorded invocation, held to its client's read allowlist."""
    rest = _positional(argv)
    assert rest, f"{client} was invoked with no verb at all: {argv}"
    verb = rest[0]
    if verb == "raw":
        method = rest[1] if len(rest) > 1 else ""
        assert method == READ_HTTP_METHOD, (
            f"{client} was asked for a raw {method}, which is not a read"
        )
        return
    assert verb in READ_VERBS[client], (
        f"{client} was asked for {verb!r}, which is not in its read allowlist"
    )
    assert not any(shape in verb for shape in WRITE_VERB_SHAPES), (
        f"{client} was asked for a write-shaped verb {verb!r}"
    )


@pytest.fixture
def transport(tmp_path):
    return guarantees.build_recording_transport(tmp_path)


@pytest.fixture
def completed_run(monkeypatch, load_module, transport, tmp_path, capsys):
    """One whole run, with every client behind the recording transport."""
    cli = load_module("")
    guarantees.apply_environment(monkeypatch, guarantees.view_environment(transport))
    working_dir = tmp_path / "team-working-directory"
    working_dir.mkdir()
    monkeypatch.chdir(working_dir)

    exit_code = cli.main(list(guarantees.VIEW_ARGV))
    stdout = capsys.readouterr().out
    assert exit_code == 0, f"the view did not complete: {stdout}"
    guarantees.assert_answer_is_correct_and_non_empty(
        guarantees.parse_stdout_document(stdout)
    )
    return transport


def test_the_run_really_reached_its_clients(completed_run) -> None:
    """Liveness. "Issued no write" is trivially true of a run that issued
    nothing, so the recorded traffic is asserted before its shape is."""
    calls = completed_run.client_calls()

    assert len(calls) >= 3, f"only {len(calls)} client invocations were recorded"
    verbs = {_positional(call["argv"])[0] for call in calls}
    assert "search" in verbs, "the run never searched, so it read nothing"


def test_every_recorded_invocation_is_a_read(completed_run) -> None:
    """The guarantee, over every client the run reached -- the view's own
    Jira reads and the ones the flow skill made inside its own process."""
    for call in completed_run.client_calls():
        assert_read_only(call["client"], call["argv"])


def test_no_jira_write_verb_of_any_kind_is_issued(completed_run) -> None:
    """Stated separately because it is its own criterion: no comment, no
    label, no transition, no field edit."""
    for call in completed_run.client_calls():
        verb = _positional(call["argv"])[0]
        assert verb not in {"transition", "comment", "create-issue", "update-issue"}
        if verb == "raw":
            assert _positional(call["argv"])[1] == READ_HTTP_METHOD


def test_a_write_verb_is_refused_before_any_process_starts(load_module) -> None:
    """The refusal is structural rather than a promise about what a caller
    passes: the allowlist is consulted ahead of the spawn, so a write verb
    never reaches a client at all."""
    jira_read = load_module("jira_read")

    def never(*_args, **_kwargs):  # pragma: no cover - reaching this is the failure
        raise AssertionError("a subprocess started for a write verb")

    for verb in ("transition", "comment", "create-issue"):
        with pytest.raises(jira_read.WriteVerbRefused):
            jira_read.run_jira(script=Path("unused"), verb=verb, runner=never)
    with pytest.raises(jira_read.WriteVerbRefused):
        jira_read.run_jira(
            script=Path("unused"), verb="raw", args=["POST", "issue"], runner=never
        )


# ---------------------------------------------------------------------------
# The client the view's own run does not reach
# ---------------------------------------------------------------------------
def _load_flow_metrics_upstream():
    """Load the flow skill's client module under a qualified name.

    Never by putting a `scripts/` directory on `sys.path`: skills are
    independent and several packs ship a module of the same bare name.
    """
    name = "atlassian_flow_metrics"
    package_dir = guarantees.SKILLS_ROOT / "flow-metrics" / "scripts" / "flow_metrics"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            name, package_dir / "__init__.py",
            submodule_search_locations=[str(package_dir)],
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return importlib.import_module(f"{name}.upstream")


def test_the_jira_align_client_in_the_derived_set_issues_reads_only(
    monkeypatch, transport
) -> None:
    """Jira Align sits in the transitive derived set but this view's own run
    never reaches it, so it is exercised directly. Leaving it unexercised
    would make the boundary one client short of the one the criteria name --
    which is the gap "no Jira write verb" leaves open on its own.
    """
    upstream = _load_flow_metrics_upstream()
    monkeypatch.setenv("ATLASSIAN_RECORDER_LOG", str(transport.log))
    monkeypatch.setenv("ATLASSIAN_RECORDER_CLIENT", "jira-align")
    client = upstream.JiraAlignClient(transport.jira_align_script)

    client.raw_get("programs/42")

    calls = transport.client_calls()
    assert calls, "the Jira Align client was never exercised"
    for call in calls:
        assert_read_only("jira-align", call["argv"])


def test_the_jira_align_client_refuses_anything_but_a_read(transport) -> None:
    """The control for the assertion above: the recording transport would
    have recorded a write just as happily, so the refusal is what stops one."""
    upstream = _load_flow_metrics_upstream()
    client = upstream.JiraAlignClient(transport.jira_align_script)

    with pytest.raises(upstream.AllowlistError):
        client.raw_get("programs/42/features/1/update")

    assert not transport.client_calls(), "a refused call still reached the client"
