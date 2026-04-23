import unittest
import os
import sqlite3
from unittest.mock import patch, MagicMock
from core.monitor import get_ram_stats, get_top_processes, init_db, save_snapshot
from utils.config import DB_PATH

class TestMonitor(unittest.TestCase):

    def test_get_ram_stats_keys(self):
        # Verify all expected keys are present in RAM stats
        stats = get_ram_stats()
        expected_keys = ['timestamp', 'total_mb', 'used_mb', 'free_mb',
                         'percent_used', 'swap_total_mb', 'swap_used_mb', 'swap_percent']
        for key in expected_keys:
            self.assertIn(key, stats)

    def test_get_ram_stats_values(self):
        # Verify RAM values are positive and within valid range
        stats = get_ram_stats()
        self.assertGreater(stats['total_mb'], 0)
        self.assertGreaterEqual(stats['used_mb'], 0)
        self.assertGreaterEqual(stats['free_mb'], 0)
        self.assertGreaterEqual(stats['percent_used'], 0)
        self.assertLessEqual(stats['percent_used'], 100)

    def test_get_top_processes_returns_list(self):
        # Verify top processes returns a list
        processes = get_top_processes()
        self.assertIsInstance(processes, list)

    def test_get_top_processes_structure(self):
        # Verify each process has required fields
        processes = get_top_processes()
        if processes:
            proc = processes[0]
            self.assertIn('pid', proc)
            self.assertIn('name', proc)
            self.assertIn('memory_mb', proc)
            self.assertIn('cpu_percent', proc)
            self.assertIn('status', proc)

    def test_get_top_processes_sorted(self):
        # Verify processes are sorted by memory descending
        processes = get_top_processes()
        if len(processes) >= 2:
            self.assertGreaterEqual(
                processes[0]['memory_mb'],
                processes[1]['memory_mb']
            )

    def test_init_db_creates_tables(self):
        # Verify database and tables are created
        init_db()
        self.assertTrue(os.path.exists(DB_PATH))
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        self.assertIn('ram_snapshots', tables)
        self.assertIn('process_logs', tables)
        self.assertIn('optimization_events', tables)

    def test_save_snapshot(self):
        # Verify snapshot is saved to database
        init_db()
        stats = get_ram_stats()
        save_snapshot(stats)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM ram_snapshots')
        count = cursor.fetchone()[0]
        conn.close()
        self.assertGreater(count, 0)

if __name__ == '__main__':
    unittest.main()