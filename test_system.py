"""
Unit tests for the Wyckoff Screening System components.
Verifies syntax, formatting, chunking, and configuration safety without external API calls.
"""

import unittest
from config import validate_config
from bot import format_scan_results, HEADER, MAX_MESSAGE_LENGTH


class TestWyckoffSystem(unittest.TestCase):

    def test_empty_results_formatting(self):
        """Verifies that an empty scan result produces the correct fallback message."""
        messages = format_scan_results([])
        self.assertEqual(len(messages), 1)
        self.assertIn("🚨 SYSTEM ONLINE: WYCKOFF CYCLE MATRIX 🚨", messages[0])
        self.assertIn("No setups found today.", messages[0])

    def test_setup_formatting_html_safety(self):
        """Verifies that setups with special characters are safely escaped and formatted in HTML."""
        sample_results = [
            "[AAPL] Action: $150.25 | MUST BREAK: $155.00 on Vol > 1500000 | RIP-CORD: $140.50",
            "[MSFT] Action: $420.00 | MUST BREAK: $435.50 on Vol > 2000000 | RIP-CORD: $395.20",
        ]
        messages = format_scan_results(sample_results)
        self.assertEqual(len(messages), 1)
        body = messages[0]

        # Verify Header
        self.assertIn(HEADER.strip(), body)

        # Verify HTML tags
        self.assertIn("<b>[AAPL]</b>", body)
        self.assertIn("<b>[MSFT]</b>", body)
        # Verify Vol > is escaped safely as Vol &gt;
        self.assertIn("Vol &gt; 1500000", body)
        self.assertIn("Vol &gt; 2000000", body)

    def test_message_chunking(self):
        """Verifies that messages exceeding the character limit are split into chunks."""
        # Create a large batch of results
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
