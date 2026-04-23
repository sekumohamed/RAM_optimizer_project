import psutil
import sqlite3
from datetime import datetime
from utils.logger import get_logger
from utils.config import DB_PATH, RAM_CRITICAL_THRESHOLD
from utils.platform_utils import clear_ram_cache

logger = get_logger(__name__)

def log_optimization_event(event_type: str, description: str, ram_before: float, ram_after: float):
    # Save optimization event to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO optimization_events
        (timestamp, event_type, description, ram_before, ram_after)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        event_type, description, ram_before, ram_after
    ))
    conn.commit()
    conn.close()

def get_current_ram_percent() -> float:
    return psutil.virtual_memory().percent

def reduce_process_working_set(exclude_names: list = None) -> int:
    # Reduce memory footprint of background/idle processes
    if exclude_names is None:
        exclude_names = ['python3', 'python', 'code', 'bash', 'systemd']

    freed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'status', 'memory_info']):
        try:
            name = proc.info['name']
            status = proc.info['status']
            mem_mb = proc.info['memory_info'].rss / 1024**2

            # Skip protected and small processes
            if name in exclude_names or mem_mb < 50:
                continue

            # Suspend and resume idle processes to flush working set
            if status == psutil.STATUS_SLEEPING and mem_mb > 100:
                proc.suspend()
                proc.resume()
                freed_count += 1
                logger.info(f"Reduced working set of: {name} ({round(mem_mb, 2)} MB)")

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return freed_count

def kill_zombie_processes() -> list:
    # Kill zombie and defunct processes
    killed = []
    for proc in psutil.process_iter(['pid', 'name', 'status']):
        try:
            if proc.info['status'] == psutil.STATUS_ZOMBIE:
                proc.kill()
                killed.append(proc.info['name'])
                logger.info(f"Killed zombie process: {proc.info['name']} (PID {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return killed

def free_ram_cache() -> dict:
    # Clear OS-level RAM cache and measure result
    ram_before = psutil.virtual_memory().percent
    logger.info(f"RAM before cache clear: {ram_before}%")

    clear_ram_cache()

    ram_after = psutil.virtual_memory().percent
    freed = round(ram_before - ram_after, 2)
    logger.info(f"RAM after cache clear: {ram_after}% (freed {freed}%)")

    log_optimization_event(
        event_type='CACHE_CLEAR',
        description='OS RAM cache cleared',
        ram_before=ram_before,
        ram_after=ram_after
    )

    return {
        'ram_before': ram_before,
        'ram_after': ram_after,
        'freed_percent': freed
    }

def run_optimization(force: bool = False) -> dict:
    # Full optimization routine
    ram_percent = get_current_ram_percent()

    if not force and ram_percent < RAM_CRITICAL_THRESHOLD:
        logger.info(f"RAM at {ram_percent}% — optimization not needed yet.")
        return {'status': 'skipped', 'ram_percent': ram_percent}

    logger.info(f"Starting optimization — RAM at {ram_percent}%")
    ram_before = ram_percent

    # Step 1 — Kill zombies
    killed = kill_zombie_processes()
    logger.info(f"Zombie processes killed: {len(killed)}")

    # Step 2 — Reduce working sets
    reduced = reduce_process_working_set()
    logger.info(f"Working sets reduced: {reduced} processes")

    # Step 3 — Clear RAM cache
    cache_result = free_ram_cache()

    ram_after = get_current_ram_percent()
    freed = round(ram_before - ram_after, 2)

    log_optimization_event(
        event_type='FULL_OPTIMIZATION',
        description=f"Killed {len(killed)} zombies, reduced {reduced} processes, cleared cache",
        ram_before=ram_before,
        ram_after=ram_after
    )

    logger.info(f"Optimization complete — RAM: {ram_before}% → {ram_after}% (freed {freed}%)")

    return {
        'status': 'success',
        'ram_before': ram_before,
        'ram_after': ram_after,
        'freed_percent': freed,
        'zombies_killed': len(killed),
        'processes_reduced': reduced
    }