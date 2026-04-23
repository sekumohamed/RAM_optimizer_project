import unittest
from unittest.mock import patch, MagicMock
from core.optimizer import (
    get_current_ram_percent,
    kill_zombie_processes,
    run_optimization
)

class TestOptimizer(unittest.TestCase):

    def test_get_current_ram_percent_valid(self):
        # RAM percent should be between 0 and 100
        result = get_current_ram_percent()
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 100)

    def test_kill_zombie_processes_returns_list(self):
        result = kill_zombie_processes()
        self.assertIsInstance(result, list)

    def test_run_optimization_skipped_when_ram_low(self):
        # When RAM is below threshold, optimization should be skipped
        with patch('core.optimizer.get_current_ram_percent', return_value=30.0):
            result = run_optimization(force=False)
            self.assertEqual(result['status'], 'skipped')

    def test_run_optimization_forced(self):
        # When forced, optimization should attempt to run
        with patch('core.optimizer.kill_zombie_processes', return_value=[]):
            with patch('core.optimizer.reduce_process_working_set', return_value=0):
                with patch('core.optimizer.free_ram_cache', return_value={
                    'ram_before': 50.0, 'ram_after': 45.0, 'freed_percent': 5.0
                }):
                    result = run_optimization(force=True)
                    self.assertIn(result['status'], ['success', 'skipped'])

    def test_run_optimization_returns_dict(self):
        result = run_optimization(force=False)
        self.assertIsInstance(result, dict)
        self.assertIn('status', result)

if __name__ == '__main__':
    unittest.main()