"""
Unit tests for the Wyckoff Screening System components.
Verifies syntax, custom money calculations, card formatting, and chunking.
"""

import unittest
from bot import format_scan_results, format_card, HEADER, MAX_MESSAGE_LENGTH


class TestWyckoffSystem(unittest.TestCase):

    def test_empty_results_formatting(self):
        """Verifies that an empty scan result produces the correct fallback message."""
        messages = format_scan_results([])
        self.assertEqual(len(messages), 1)
        self.assertIn("🚨 SYSTEM ONLINE: WYCKOFF CYCLE MATRIX 🚨", messages[0])
        self.assertIn("No setups found today", messages[0])

    def test_card_custom_money_calculation(self):
        """Verifies that custom money numbers, percentages, and plain-English plans are calculated correctly."""
        raw = "[V] Action: $368.42 | MUST BREAK: $385.57 on Vol > 9883988 | RIP-CORD: $353.24"
        card = format_card(raw)

        # Check ticker and company name
        self.assertIn("V — Visa", card)
        self.assertIn("$368.42", card)

        # Check custom calculated upside money number: $385.57 - $368.42 = $17.15 (+4.7%)
        self.assertIn("$385.57", card)
        self.assertIn("+$17.15", card)
        self.assertIn("+4.7%", card)
        self.assertIn("9.88M shares", card)

        # Check custom calculated downside risk money number: $368.42 - $353.24 = $15.18 (-4.1%)
        self.assertIn("$353.24", card)
        self.assertIn("-$15.18 per share", card)
        self.assertIn("-4.1%", card)

        # Check action plan
        self.assertIn("Put on watchlist", card)

    def test_message_chunking(self):
        """Verifies that messages exceeding the character limit are split into chunks."""
        mock_results = [
            f"[TEST{i}] Action: $100.00 | MUST BREAK: $110.00 on Vol > 1000000 | RIP-CORD: $90.00"
            for i in range(100)
        ]
        messages = format_scan_results(mock_results)
        self.assertGreater(len(messages), 1)
        for msg in messages:
            self.assertLessEqual(len(msg), MAX_MESSAGE_LENGTH)


if __name__ == "__main__":
    unittest.main()
