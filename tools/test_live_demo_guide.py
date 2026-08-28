#!/usr/bin/env python3
"""Construction checks for the canonical three-track live-demo guide."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
GUIDE_PATH = REPO_ROOT / "guides/core/how-to/run-a-live-demo.md"
WALKTHROUGHS_PATH = (
    REPO_ROOT / "docs/specs/m6-live-demo-guide/notes/walkthroughs.md"
)


def _section(text: str, heading: str) -> str:
    """Return one level-two section, excluding the next level-two heading."""
    match = re.search(
        rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"missing section: {heading}")
    return match.group("body")


class LiveDemoGuideTests(unittest.TestCase):
    """Pin the product-bearing workflow contract without checking prose style."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = GUIDE_PATH.read_text(encoding="utf-8")

    def assert_contains_all(self, text: str, values: tuple[str, ...]) -> None:
        """Report all missing contract tokens in one failure."""
        missing = [value for value in values if value not in text]
        self.assertFalse(missing, f"missing required content: {missing}")

    def test_frontmatter_and_entry_contract(self) -> None:
        self.assertTrue(self.text.startswith("---\n"))
        frontmatter = self.text.split("---", 2)[1]
        self.assert_contains_all(
            frontmatter,
            (
                'title: "How to run a 30-minute live workflow demo"',
                "pack: core",
                "kind: how-to",
            ),
        )
        opening = "\n".join(self.text.splitlines()[:24])
        self.assert_contains_all(
            opening,
            ("**Use this when:**", "**Prerequisites:**", "**Result:**"),
        )

    def test_five_timeboxes_total_thirty_minutes(self) -> None:
        frame = _section(self.text, "The five teaching beats")
        rows = re.findall(r"^\| ([^|]+) \| (\d+) min \|", frame, re.MULTILINE)
        self.assertEqual(
            rows,
            [
                ("Pre-flight", "4"),
                ("Enter", "7"),
                ("Shape or cut", "6"),
                ("Draft delivery handoff", "9"),
                ("Receipt", "4"),
            ],
        )
        self.assertEqual(sum(int(minutes) for _name, minutes in rows), 30)

    def test_track_map_pins_real_pack_paths(self) -> None:
        mapping = _section(self.text, "Choose the workflow, not the persona label")
        self.assert_contains_all(
            mapping,
            (
                "**Technical**",
                "Core at repo scope",
                "`new-spec`",
                "No brief; one Draft spec/plan pair",
                "**Enterprise**",
                "`author-delivery-brief continue` → selected slice → `new-spec`",
                "Source brief `Ready`",
                "**Non-technical**",
                "Product Engineering at user scope, then Core at repo scope",
                "`frame-intent` → `de-risk-intent` → `decompose-intent` → `new-spec`",
                "Draft intent and one Draft spec/plan pair",
                "input shape chooses the workflow",
            ),
        )
        self.assert_contains_all(
            mapping,
            ("governance-extras", "product-strategy", "Experience Design"),
        )

    def test_every_track_has_executable_beat_fields(self) -> None:
        fields = (
            "**Say:**",
            "**Reads:**",
            "**Writes:**",
            "**You see:**",
            "**You decide:**",
            "**Narrate:**",
            "**Stop if:**",
        )
        for heading in (
            "Technical — Core direct feature path",
            "Enterprise — Core structured-handoff path",
            "Non-technical — Product Engineering shaping into Core",
        ):
            with self.subTest(track=heading):
                track = _section(self.text, heading)
                self.assertEqual(track.count("### "), 5)
                for beat in (
                    "Pre-flight — 4 min maximum",
                    "Enter — 7 min maximum",
                    "Shape or cut — 6 min maximum",
                    "Draft delivery handoff — 9 min maximum",
                    "Receipt — 4 min maximum",
                ):
                    self.assertIn(f"### {beat}", track)
                for field in fields:
                    self.assertEqual(track.count(field), 5, field)

    def test_technical_contract_has_no_brief_or_discovery_gates(self) -> None:
        track = _section(self.text, "Technical — Core direct feature path")
        self.assert_contains_all(
            track,
            (
                "Use Core's new-spec skill",
                "create no brief",
                "`Brief: none`",
                "command-to-AC trace",
                "task-to-file trace",
                "renamed G0/G1.5/G2 discovery sequence",
                "ready to circulate",
            ),
        )

    def test_enterprise_contract_uses_unqueued_ready_brief(self) -> None:
        track = _section(self.text, "Enterprise — Core structured-handoff path")
        self.assert_contains_all(
            track,
            (
                "unqueued Draft brief",
                "uses `author-delivery-brief continue`",
                "Use Core's author-delivery-brief skill in continue mode",
                "Do not implement, approve, register work, edit",
                "Outcome, Appetite, at least one Rabbit",
                "Spec map",
                "policy/control → acceptance criterion → plan-evidence trace",
                "mid-market enterprise segment",
                "`workspace.toml` is explicitly excluded",
            ),
        )

    def test_nontechnical_contract_crosses_user_to_repo_scope(self) -> None:
        track = _section(
            self.text, "Non-technical — Product Engineering shaping into Core"
        )
        self.assert_contains_all(
            track,
            (
                "feature level",
                "app scale",
                "user-scoped Product Engineering",
                "repo-scoped Core",
                "repo-root `agentbundle-layout.toml`",
                "`[product] output_dir`",
                "never creates\nor edits a user-home layout file",
                "Pause at G0",
                "predeclared kill condition",
                "validation hook",
                "project it directly to a Core\nspec",
                "coordination brief's readiness",
                "`to-validate`",
                "source → corrected intent → Draft acceptance-criterion",
                "not the full 60–120 minute `discovery-loop`",
            ),
        )

    def test_receipt_separates_demo_from_approval_and_execution(self) -> None:
        receipt = _section(self.text, "Completion receipt")
        self.assert_contains_all(
            receipt,
            (
                "Track:",
                "Packs and scopes used:",
                "Skills invoked:",
                "Changed paths and statuses:",
                "Provenance links:",
                "Verified proof:",
                "Unresolved or unverified items:",
                "Human decisions recorded:",
                "Formal spec approval fired: no",
                "Formal plan approval fired: no",
                "Implementation started: no",
                "Work-intake registration performed: no",
                "External systems changed: no",
                "Next reviewer and action:",
                "Share recipient:",
                "Elapsed time:",
                "Safe stop",
            ),
        )

    def test_cold_walkthroughs_record_three_complete_bounded_paths(self) -> None:
        records = WALKTHROUGHS_PATH.read_text(encoding="utf-8")
        self.assert_contains_all(
            records,
            (
                "## Technical — Core direct `new-spec`",
                "## Enterprise — Core `receive-brief` to `new-spec`",
                "## Non-technical — Product Engineering into Core",
                "No external systems changed",
                "no work-intake",
                "repo-root\n  `agentbundle-layout.toml`",
                '`[product] output_dir = "docs/product"`',
                "/private/tmp/m6-live-demo-guide-cold-qa-20260813/demo-repo/docs/product",
                "No user-home\n  layout file was read, created, or edited.",
                "Corrective layout revalidation (2026-08-14)",
                "11:45 total",
                "Cold quality verdict: **Clean — ready to record.**",
            ),
        )
        expected_receipts = {
            "Technical — Core direct `new-spec`": (
                "Outcome: Success",
                "Track: Technical",
                "Packs and scopes used: Core at repo scope",
                "Skills invoked: new-spec",
                "Changed paths and statuses: "
                "docs/specs/demo-doc-link-proof/spec.md — Draft; "
                "docs/specs/demo-doc-link-proof/plan.md — Draft",
                "Provenance links: no brief; source guide and verification "
                "command cited directly by the Draft spec",
                "Verified proof: python3 tools/link_check.py --build-dir build "
                "exited successfully twice",
                "Unresolved or unverified items: Draft pair awaits formal "
                "review; no demo proof gaps",
                "Human decisions recorded: problem is recognizable and "
                "feature-sized; success command is trusted",
                "Formal spec approval fired: no",
                "Formal plan approval fired: no",
                "Implementation started: no",
                "Work-intake registration performed: no",
                "External systems changed: no",
                "Next reviewer and action: Example Engineer reviews accuracy "
                "and circulation readiness",
                "Share recipient: Example Engineer",
                "Elapsed time: 22:30",
            ),
            "Enterprise — Core `receive-brief` to `new-spec`": (
                "Outcome: Success",
                "Track: Enterprise",
                "Packs and scopes used: Core at repo scope",
                "Skills invoked: receive-brief, new-spec",
                "Changed paths and statuses: "
                "docs/product/briefs/demo-governed-doc-pilot.md — Ready; "
                "docs/specs/demo-rendered-link-pilot/spec.md — Draft; "
                "docs/specs/demo-rendered-link-pilot/plan.md — Draft",
                "Provenance links: policy/control source to Ready brief to "
                "selected slice to Draft spec backlink",
                "Verified proof: policy claim traces to AC1 and plan T1; "
                "residual-risk recipient is named",
                "Unresolved or unverified items: mid-market path remains "
                "uncharacterized; Draft pair awaits formal review",
                "Human decisions recorded: selected "
                "rendered-link-proof-prompt and accepted the completed Ready "
                "gate",
                "Formal spec approval fired: no",
                "Formal plan approval fired: no",
                "Implementation started: no",
                "Work-intake registration performed: no",
                "External systems changed: no",
                "Next reviewer and action: Example Risk Reviewer checks "
                "control accuracy and circulation readiness",
                "Share recipient: Example Risk Reviewer",
                "Elapsed time: 25:55",
            ),
            "Non-technical — Product Engineering into Core": (
                "Outcome: Success",
                "Track: Non-technical",
                "Packs and scopes used: Product Engineering at user scope, "
                "then Core at repo scope",
                "Skills invoked: frame-intent, de-risk-intent, "
                "decompose-intent, receive-brief, new-spec",
                "Changed paths and statuses: "
                "docs/product/intents/demo-onboarding-proof-intent.md — Draft; "
                "docs/product/briefs/demo-onboarding-proof-brief.md — Ready; "
                "docs/specs/demo-onboarding-review-evidence/spec.md — Draft; "
                "docs/specs/demo-onboarding-review-evidence/plan.md — Draft",
                "Provenance links: source guide to corrected intent to Ready "
                "Core brief to Draft spec and plan",
                "Verified proof: participant correction propagates through "
                "the intent and spec; validation hook remains visible",
                "Unresolved or unverified items: surviving assumption remains "
                "to-validate; Draft pair awaits formal review",
                "Human decisions recorded: G0 framing, kill condition, "
                "survive verdict, participant wording, and Core slice cut",
                "Formal spec approval fired: no",
                "Formal plan approval fired: no",
                "Implementation started: no",
                "Work-intake registration performed: no",
                "External systems changed: no",
                "Next reviewer and action: Example Product Owner checks "
                "meaning, authorship, and circulation readiness",
                "Share recipient: Example Product Owner",
                "Elapsed time: 28:25",
            ),
        }
        for heading, expected_receipt in expected_receipts.items():
            with self.subTest(receipt=heading):
                track = _section(records, heading)
                receipt_match = re.search(
                    r"\*\*Completion receipt\*\*\n\n```text\n"
                    r"(?P<receipt>.*?)\n```",
                    track,
                    flags=re.DOTALL,
                )
                self.assertIsNotNone(receipt_match)
                receipt = receipt_match.group("receipt").splitlines()
                self.assertEqual(tuple(receipt), expected_receipt)
        totals = re.findall(r"\| \*\*Total\*\* \| \*\*(\d+):(\d{2})\*\* \|", records)
        self.assertEqual(totals, [("22", "30"), ("25", "55"), ("28", "25")])
        self.assertTrue(all(int(minutes) < 30 for minutes, _seconds in totals))
        self.assertEqual(records.count("(`Draft`)"), 7)
        self.assertEqual(records.count("(`Ready`)"), 2)


if __name__ == "__main__":
    unittest.main()
