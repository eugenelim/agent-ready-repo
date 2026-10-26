"""Instruction-text pins for new-adr's Consulted rule, template comment and route pointer."""

import pathlib

_ROOT = pathlib.Path(__file__).resolve().parents[3] / ".apm/skills/new-adr"
TEXT = " ".join((_ROOT / "SKILL.md").read_text(encoding="utf-8").split())
TEMPLATE = " ".join((_ROOT / "assets/adr.md").read_text(encoding="utf-8").split())


def test_consulted_comes_only_from_supplied_handle_or_role() -> None:
    assert (
        "A person or group in `Consulted` comes only from a handle or role the user "
        "supplied, directly or through a route result block's `Consult:` line, and "
        "never from record text, Git history or an email address."
    ) in TEXT


def test_email_offered_for_consulted_is_refused() -> None:
    assert (
        "If an email address is offered for `Consulted`, refuse it and ask for a "
        "handle or role instead."
    ) in TEXT


def test_name_handle_email_sentence_is_scoped_to_decision_makers_and_informed() -> None:
    assert (
        "for `Decision-makers` and `Informed`, a name, a GitHub handle, or an email "
        "are all valid"
    ) in TEXT
    assert "— a name, a GitHub handle, or an email are all valid" not in TEXT


def test_handle_and_role_are_defined() -> None:
    assert (
        'A handle is a platform handle such as `@user` or `@org/team`, and a role is '
        'a named function such as "platform maintainers".'
    ) in TEXT


def test_record_identifiers_stay_allowed_in_consulted() -> None:
    assert "Record identifiers (ADR, RFC or spec) stay allowed in `Consulted`." in TEXT


def test_template_comment_names_allowed_values_and_forbids_email() -> None:
    assert (
        "<!-- whose input was sought, two-way; handles, roles or record identifiers, "
        "never an email address; optional, delete if none -->"
    ) in TEMPLATE


def test_when_to_invoke_points_to_route() -> None:
    section = TEXT.split("## When to invoke", 1)[1].split("## ", 1)[0]
    assert "run `navigate-decisions route` first" in section
