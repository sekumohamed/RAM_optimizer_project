import psutil
import sqlite3
import time
from datetime import datetime
from utils.logger import get_logger
from utils.config import DB_PATH, MONITOR_INTERVAL_SECONDS, TOP_PROCESS_COUNT

logger = get_logger(__name__)

def init_db():
    # Create tables if they don't exist
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ram_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            total_mb REAL,
            used_mb REAL,
            free_mb REAL,
            percent_used REAL,
            swap_total_mb REAL,
            swap_used_mb REAL,
            swap_percent REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            pid INTEGER,
            name TEXT,
            memory_mb REAL,
            cpu_percent REAL,
            status TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS optimization_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            event_type TEXT,
            description TEXT,
            ram_before REAL,
            ram_after REAL
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("Database initialized.")

def get_ram_stats():
    # Fetch current RAM and swap stats
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_mb': round(ram.total / 1024**2, 2),
        'used_mb': round(ram.used / 1024**2, 2),
        'free_mb': round(ram.available / 1024**2, 2),
        'percent_used': ram.percent,
        'swap_total_mb': round(swap.total / 1024**2, 2),
        'swap_used_mb': round(swap.used / 1024**2, 2),
        'swap_percent': swap.percent
    }

def get_top_processes():
    # Get top memory-consuming processes
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'status']):
        try:
            mem_mb = round(proc.info['memory_info'].rss / 1024**2, 2)
            processes.append({
                'pid': proc.info['pid'],
                'name': proc.info['name'],
                'memory_mb': mem_mb,
                'cpu_percent': proc.info['cpu_percent'],
                'status': proc.info['status']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Sort by memory usage descending
    processes.sort(key=lambda x: x['memory_mb'], reverse=True)
    return processes[:TOP_PROCESS_COUNT]

def save_snapshot(stats: dict):
    # Save RAM snapshot to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ram_snapshots
        (timestamp, total_mb, used_mb, free_mb, percent_used,
         swap_total_mb, swap_used_mb, swap_percent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        stats['timestamp'], stats['total_mb'], stats['used_mb'],
        stats['free_mb'], stats['percent_used'], stats['swap_total_mb'],
        stats['swap_used_mb'], stats['swap_percent']
    ))
    conn.commit()
    conn.close()

def save_processes(processes: list):
    # Save top processes to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for proc in processes:
        cursor.execute('''
            INSERT INTO process_logs
            (timestamp, pid, name, memory_mb, cpu_percent, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            timestamp, proc['pid'], proc['name'],
            proc['memory_mb'], proc['cpu_percent'], proc['status']
        ))
    conn.commit()
    conn.close()

def start_monitoring(callback=None):
    # Continuously monitor RAM and save to DB
    logger.info("RAM monitoring started.")
    init_db()

    while True:
        stats = get_ram_stats()
        processes = get_top_processes()

        save_snapshot(stats)
        save_processes(processes)

        logger.info(
            f"RAM: {stats['used_mb']}MB / {stats['total_mb']}MB "
            f"({stats['percent_used']}%) | "
            f"Swap: {stats['swap_percent']}%"
        )

        # Send data to UI if callback provided
        if callback:
            callback(stats, processes)

        time.sleep(MONITOR_INTERVAL_SECONDS)