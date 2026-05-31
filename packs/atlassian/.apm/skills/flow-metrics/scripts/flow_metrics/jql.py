"""JQL composition helper — the canonical iteration-order anchor.

Used identically for scope, ``--jql``, ``--cohort-jql``, ``--align-filter``,
and (in the per-team rollup) the program-scope JQL. Parenthesization is contract-tested:
``(scope) AND (user)`` whenever a user clause is present, regardless of
its internal operator precedence. ``ORDER BY key ASC`` is appended for
canonical iteration order.

Stdlib only. Python >= 3.10.
"""
from __future__ import annotations

from typing import Optional


def compose_jql(
    scope_clause: str,
    user_clause: Optional[str],
    *,
    order_by_key: bool = True,
) -> str:
    """Compose a JQL query from a scope clause and an optional user clause.

    Always wraps both clauses in parentheses before ``AND``. Appends
    ``ORDER BY key ASC`` for canonical iteration order unless suppressed.

    Used identically for ``--jql`` (Jira) and ``--align-filter`` (Jira
    Align OData) at the string-shape level — both follow the same
    parenthesization rule.
    """
    if user_clause is not None and user_clause.strip() != "":
        body = "({}) AND ({})".format(scope_clause, user_clause)
    else:
        body = scope_clause
    if order_by_key:
        return body + " ORDER BY key ASC"
    return body


__all__ = ["compose_jql"]
