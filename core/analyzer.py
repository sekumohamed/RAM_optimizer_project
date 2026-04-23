import sqlite3
from datetime import datetime, timedelta
from utils.logger import get_logger
from utils.config import DB_PATH, HISTORY_RETENTION_DAYS

logger = get_logger(__name__)

def get_recent_snapshots(hours: int = 24) -> list:
    # Fetch RAM snapshots from the last N hours
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    since = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        SELECT timestamp, used_mb, percent_used, swap_percent
        FROM ram_snapshots
        WHERE timestamp >= ?
        ORDER BY timestamp ASC
    ''', (since,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_peak_usage(hours: int = 24) -> dict:
    # Find peak RAM usage in the last N hours
    rows = get_recent_snapshots(hours)
    if not rows:
        return {}

    peak = max(rows, key=lambda x: x[2])
    return {
        'timestamp': peak[0],
        'used_mb': peak[1],
        'percent_used': peak[2],
        'swap_percent': peak[3]
    }

def get_average_usage(hours: int = 24) -> dict:
    # Calculate average RAM and swap usage
    rows = get_recent_snapshots(hours)
    if not rows:
        return {}

    avg_used = round(sum(r[1] for r in rows) / len(rows), 2)
    avg_percent = round(sum(r[2] for r in rows) / len(rows), 2)
    avg_swap = round(sum(r[3] for r in rows) / len(rows), 2)

    return {
        'avg_used_mb': avg_used,
        'avg_percent': avg_percent,
        'avg_swap_percent': avg_swap,
        'samples': len(rows)
    }

def get_top_memory_hogs(limit: int = 5) -> list:
    # Find processes that consistently use the most memory
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT name, AVG(memory_mb) as avg_mem, MAX(memory_mb) as max_mem, COUNT(*) as appearances
        FROM process_logs
        GROUP BY name
        ORDER BY avg_mem DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            'name': r[0],
            'avg_memory_mb': round(r[1], 2),
            'max_memory_mb': round(r[2], 2),
            'appearances': r[3]
        }
        for r in rows
    ]

def detect_memory_leaks() -> list:
    # Detect processes whose memory keeps growing over time
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    since = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        SELECT name, MIN(memory_mb) as min_mem, MAX(memory_mb) as max_mem,
               MAX(memory_mb) - MIN(memory_mb) as growth
        FROM process_logs
        WHERE timestamp >= ?
        GROUP BY name
        HAVING growth > 50
        ORDER BY growth DESC
    ''', (since,))
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            'name': r[0],
            'min_mb': round(r[1], 2),
            'max_mb': round(r[2], 2),
            'growth_mb': round(r[3], 2)
        }
        for r in rows
    ]

def clean_old_records():
    # Delete records older than retention period
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=HISTORY_RETENTION_DAYS)).strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('DELETE FROM ram_snapshots WHERE timestamp < ?', (cutoff,))
    cursor.execute('DELETE FROM process_logs WHERE timestamp < ?', (cutoff,))
    cursor.execute('DELETE FROM optimization_events WHERE timestamp < ?', (cutoff,))

    conn.commit()
    conn.close()
    logger.info(f"Old records cleaned up (older than {HISTORY_RETENTION_DAYS} days).")

def run_analysis() -> dict:
    # Run full analysis and return summary
    logger.info("Running system memory analysis...")

    peak = get_peak_usage()
    average = get_average_usage()
    hogs = get_top_memory_hogs()
    leaks = detect_memory_leaks()

    clean_old_records()

    summary = {
        'peak_usage': peak,
        'average_usage': average,
        'top_memory_hogs': hogs,
        'suspected_leaks': leaks
    }

    logger.info(f"Analysis complete. Peak: {peak.get('percent_used', 'N/A')}% | "
                f"Avg: {average.get('avg_percent', 'N/A')}% | "
                f"Leaks detected: {len(leaks)}")

    return summary