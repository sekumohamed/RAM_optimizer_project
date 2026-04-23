import unittest
from unittest.mock import patch
from core.analyzer import (
    get_recent_snapshots, get_peak_usage,
    get_average_usage, get_top_memory_hogs,
    detect_memory_leaks, run_analysis
)

class TestAnalyzer(unittest.TestCase):

    def test_get_recent_snapshots_returns_list(self):
        result = get_recent_snapshots(hours=24)
        self.assertIsInstance(result, list)

    def test_get_peak_usage_returns_dict(self):
        result = get_peak_usage()
        self.assertIsInstance(result, dict)

    def test_get_peak_usage_keys(self):
        result = get_peak_usage()
        if result:
            self.assertIn('timestamp', result)
            self.assertIn('used_mb', result)
            self.assertIn('percent_used', result)

    def test_get_average_usage_returns_dict(self):
        result = get_average_usage()
        self.assertIsInstance(result, dict)

    def test_get_average_usage_valid_range(self):
        result = get_average_usage()
        if result:
            self.assertGreaterEqual(result['avg_percent'], 0)
            self.assertLessEqual(result['avg_percent'], 100)

    def test_get_top_memory_hogs_returns_list(self):
        result = get_top_memory_hogs()
        self.assertIsInstance(result, list)

    def test_detect_memory_leaks_returns_list(self):
        result = detect_memory_leaks()
        self.assertIsInstance(result, list)

    def test_run_analysis_structure(self):
        result = run_analysis()
        self.assertIn('peak_usage', result)
        self.assertIn('average_usage', result)
        self.assertIn('top_memory_hogs', result)
        self.assertIn('suspected_leaks', result)

if __name__ == '__main__':
    unittest.main()