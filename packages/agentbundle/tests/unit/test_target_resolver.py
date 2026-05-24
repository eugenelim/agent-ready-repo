"""T4: scope-conditional `target` resolver — pure-function unit tests.

Resolves the v0.3 contract's `target` field shape (string or
`{repo, user}` scope-map) plus the `<attach-to-agent>` placeholder
substitution for `merge-into-agent-json` consumers (T5/T6). The
resolver returns a *string* template; scope-root resolution and
filesystem placement are caller concerns.

Tests cover the bullets under spec.md AC3, AC4, AC15, AC18 plus the
T4 plan's internal acceptance bullets.
"""

from __future__ import annotations

import unittest


class ResolveTargetBareStringTests(unittest.TestCase):
    """Legacy / v0.1-shape projections declare `target` as a bare string."""

    def test_bare_string_returns_unchanged_for_repo(self) -> None:
        from agentbundle.build.target_resolver import resolve_target

        projection = {"target": "tools/hooks/<name>.{sh,py}"}
        self.assertEqual(
            resolve_target(projection, scope="repo"),
            "tools/hooks/<name>.{sh,py}",
        )

    def test_bare_string_returns_unchanged_for_user(self) -> None:
        """The bare string is the entire target template — scope doesn't fork it."""
        from agentbundle.build.target_resolver import resolve_target

        projection = {"target": "tools/hooks/<name>.{sh,py}"}
        self.assertEqual(
            resolve_target(projection, scope="user"),
            "tools/hooks/<name>.{sh,py}",
        )


class ResolveTargetScopeMapTests(unittest.TestCase):
    """v0.3 scope-map declarations fork by scope."""

    def test_scope_map_returns_repo_target(self) -> None:
        from agentbundle.build.target_resolver import resolve_target

        projection = {
            "target": {
                "repo": "tools/hooks/<name>.{sh,py}",
                "user": ".claude/hooks/<name>.{sh,py}",
            }
        }
        self.assertEqual(
            resolve_target(projection, scope="repo"),
            "tools/hooks/<name>.{sh,py}",
        )

    def test_scope_map_returns_user_target(self) -> None:
        from agentbundle.build.target_resolver import resolve_target

        projection = {
            "target": {
                "repo": "tools/hooks/<name>.{sh,py}",
                "user": ".claude/hooks/<name>.{sh,py}",
            }
        }
        self.assertEqual(
            resolve_target(projection, scope="user"),
            ".claude/hooks/<name>.{sh,py}",
        )

    def test_scope_map_returns_only_declared_branch(self) -> None:
        """An asymmetric scope-map (e.g. only `repo` declared) is allowed; the
        absent scope refuses (see the missing-scope test). The declared one
        resolves cleanly."""
        from agentbundle.build.target_resolver import resolve_target

        projection = {"target": {"repo": "tools/only.json"}}
        self.assertEqual(resolve_target(projection, scope="repo"), "tools/only.json")


class ResolveTargetMissingScopeTests(unittest.TestCase):
    """Requesting a scope the projection doesn't declare is an error."""

    def test_user_scope_missing_in_scope_map_refuses(self) -> None:
        from agentbundle.build.target_resolver import resolve_target

        projection = {"target": {"repo": ".claude/settings.local.json"}}
        with self.assertRaises(ValueError) as ctx:
            resolve_target(projection, scope="user")
        # Refusal text names the missing scope so the caller can act on it.
        self.assertIn("user", str(ctx.exception))

    def test_repo_scope_missing_in_scope_map_refuses(self) -> None:
        from agentbundle.build.target_resolver import resolve_target

        projection = {"target": {"user": ".claude/settings.json"}}
        with self.assertRaises(ValueError) as ctx:
            resolve_target(projection, scope="repo")
        self.assertIn("repo", str(ctx.exception))

    def test_missing_target_field_refuses(self) -> None:
        from agentbundle.build.target_resolver import resolve_target

        with self.assertRaises(ValueError):
            resolve_target({}, scope="repo")


class ResolveTargetAttachToAgentTests(unittest.TestCase):
    """`merge-into-agent-json` targets carry the `<attach-to-agent>` placeholder;
    the resolver substitutes it when given the agent name. Other placeholders
    (`<name>`, `<pack>`) are NOT substituted — they're the pipeline's concern."""

    def test_substitutes_attach_to_agent_in_bare_string(self) -> None:
        from agentbundle.build.target_resolver import resolve_target

        projection = {"target": ".kiro/agents/<attach-to-agent>.json"}
        self.assertEqual(
            resolve_target(projection, scope="repo", attach_to_agent="reviewer"),
            ".kiro/agents/reviewer.json",
        )

    def test_substitutes_attach_to_agent_in_scope_map(self) -> None:
        from agentbundle.build.target_resolver import resolve_target

        projection = {
            "target": {
                "repo": ".kiro/agents/<attach-to-agent>.json",
                "user": ".kiro/agents/<attach-to-agent>.json",
            }
        }
        self.assertEqual(
            resolve_target(projection, scope="user", attach_to_agent="clipboard-watcher"),
            ".kiro/agents/clipboard-watcher.json",
        )

    def test_leaves_other_placeholders_untouched(self) -> None:
        """`<name>` is a separate pipeline concern; the resolver does not touch it."""
        from agentbundle.build.target_resolver import resolve_target

        projection = {"target": "tools/hooks/<name>.{sh,py}"}
        result = resolve_target(projection, scope="repo", attach_to_agent="reviewer")
        # `<name>` survives; `<attach-to-agent>` would have been substituted if present.
        self.assertEqual(result, "tools/hooks/<name>.{sh,py}")

    def test_unfilled_attach_to_agent_placeholder_refuses(self) -> None:
        """If the template requires `<attach-to-agent>` but no name is given,
        passing the unsubstituted template to a consumer would be a bug."""
        from agentbundle.build.target_resolver import resolve_target

        projection = {"target": ".kiro/agents/<attach-to-agent>.json"}
        with self.assertRaises(ValueError) as ctx:
            resolve_target(projection, scope="repo")
        self.assertIn("attach-to-agent", str(ctx.exception))

    def test_attach_to_agent_ignored_when_placeholder_absent(self) -> None:
        """Providing `attach_to_agent` when the template doesn't reference it
        is a no-op — the caller may pass it unconditionally for shape uniformity."""
        from agentbundle.build.target_resolver import resolve_target

        projection = {"target": "tools/hooks/static.json"}
        self.assertEqual(
            resolve_target(projection, scope="repo", attach_to_agent="reviewer"),
            "tools/hooks/static.json",
        )


class ResolveTargetReturnTypeTests(unittest.TestCase):
    """Resolver returns `str`, not `Path` — pipeline consumers do scope-root
    resolution against `.` or `~` themselves (the resolver is a pure
    string-shape utility, no filesystem dependency)."""

    def test_returns_str_not_path(self) -> None:
        from agentbundle.build.target_resolver import resolve_target

        result = resolve_target({"target": "tools/hooks/<name>.{sh,py}"}, scope="repo")
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main()
