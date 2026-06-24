"""Configuration-level tests that do not log in to STARS."""

import unittest

from config import ConfigurationError, StarsConfig
from helpers.index_pairs import parse_index_pairs
from stars_messages import is_page_expired_alert, is_registration_not_open_alert


class ParseIndexPairsTests(unittest.TestCase):
    def test_pairs_indexes_by_position(self):
        self.assertEqual(
            parse_index_pairs("12345, 23456", "67890,98765"),
            [("12345", "67890"), ("23456", "98765")],
        )

    def test_requires_the_same_number_of_indexes(self):
        with self.assertRaisesRegex(ConfigurationError, "same number"):
            parse_index_pairs("12345,23456", "67890")

    def test_rejects_empty_index_values(self):
        with self.assertRaisesRegex(ConfigurationError, "without empty"):
            parse_index_pairs("12345,,23456", "67890,98765,54321")

    def test_recognizes_the_closed_registration_alert(self):
        self.assertTrue(
            is_registration_not_open_alert(
                "09.You are not allowed to register for course now^ ! "
                "<Server Datetime :24-JUN-2026 15:46>"
            )
        )

    def test_recognizes_the_expired_page_alert(self):
        self.assertTrue(is_page_expired_alert(" This page has expired!"))

    def test_runtime_settings_are_loaded_from_one_config_class(self):
        config = StarsConfig.from_environment(
            {
                "STARS_WAIT_SECONDS": "4",
                "STARS_ALERT_WAIT_SECONDS": "6",
                "STARS_RETRY_DELAY_SECONDS": "1.5",
                "STARS_POLL_INTERVAL_SECONDS": "0.1",
                "MAX_REQUEST_ATTEMPTS": "20",
                "ADD_DROP_RETRY_DELAY_SECONDS": "2",
                "ADD_DROP_MAX_ATTEMPTS": "30",
                "STARS_HEADLESS": "true",
            }
        )
        self.assertEqual(config.page_timeout_seconds, 4.0)
        self.assertEqual(config.alert_timeout_seconds, 6.0)
        self.assertEqual(config.retry_delay_seconds, 1.5)
        self.assertEqual(config.poll_interval_seconds, 0.1)
        self.assertEqual(config.max_request_attempts, 20)
        self.assertEqual(config.add_drop_retry_delay_seconds, 2.0)
        self.assertEqual(config.add_drop_max_attempts, 30)
        self.assertTrue(config.headless)


if __name__ == "__main__":
    unittest.main()
