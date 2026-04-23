import psutil
import subprocess
import os
from utils.logger import get_logger
from utils.config import SWAP_WARNING_THRESHOLD
from utils.platform_utils import is_linux, is_windows, is_mac

logger = get_logger(__name__)

def get_swap_stats() -> dict:
    # Get current swap memory statistics
    swap = psutil.swap_memory()
    return {
        'total_mb': round(swap.total / 1024**2, 2),
        'used_mb': round(swap.used / 1024**2, 2),
        'free_mb': round(swap.free / 1024**2, 2),
        'percent': swap.percent,
        'status': 'critical' if swap.percent >= SWAP_WARNING_THRESHOLD else 'healthy'
    }

def is_swap_enabled() -> bool:
    # Check if swap is currently active
    swap = psutil.swap_memory()
    return swap.total > 0

def create_swap_file(size_mb: int = 1024, path: str = '/swapfile') -> bool:
    # Create and activate a swap file on Linux
    if not is_linux():
        logger.warning("Swap file creation via this method is Linux-only.")
        return False

    if os.path.exists(path):
        logger.warning(f"Swap file already exists at {path}.")
        return False

    try:
        logger.info(f"Creating {size_mb} MB swap file at {path}...")

        # Allocate swap file
        subprocess.run(
            ['sudo', 'fallocate', '-l', f'{size_mb}M', path],
            check=True
        )

        # Set correct permissions
        subprocess.run(['sudo', 'chmod', '600', path], check=True)

        # Format as swap
        subprocess.run(['sudo', 'mkswap', path], check=True)

        # Activate swap
        subprocess.run(['sudo', 'swapon', path], check=True)

        logger.info(f"Swap file created and activated: {path} ({size_mb} MB)")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create swap file: {e}")
        return False

def remove_swap_file(path: str = '/swapfile') -> bool:
    # Deactivate and remove a swap file on Linux
    if not is_linux():
        logger.warning("Swap file removal via this method is Linux-only.")
        return False

    try:
        subprocess.run(['sudo', 'swapoff', path], check=True)
        subprocess.run(['sudo', 'rm', '-f', path], check=True)
        logger.info(f"Swap file removed: {path}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to remove swap file: {e}")
        return False

def adjust_swappiness(value: int = 10) -> bool:
    # Adjust how aggressively Linux uses swap (0=avoid swap, 100=use swap heavily)
    if not is_linux():
        logger.warning("Swappiness adjustment is Linux-only.")
        return False

    if not (0 <= value <= 100):
        logger.error("Swappiness value must be between 0 and 100.")
        return False

    try:
        subprocess.run(
            ['sudo', 'sysctl', f'vm.swappiness={value}'],
            check=True
        )
        logger.info(f"Swappiness set to {value}.")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to set swappiness: {e}")
        return False

def get_swappiness() -> int:
    # Get current swappiness value on Linux
    if not is_linux():
        return -1

    try:
        result = subprocess.run(
            ['cat', '/proc/sys/vm/swappiness'],
            capture_output=True, text=True
        )
        return int(result.stdout.strip())

    except Exception as e:
        logger.error(f"Failed to get swappiness: {e}")
        return -1

def monitor_swap_health() -> dict:
    # Check swap health and return recommendations
    stats = get_swap_stats()
    recommendations = []

    if not is_swap_enabled():
        recommendations.append("No swap is enabled. Consider adding swap for stability.")

    elif stats['percent'] >= SWAP_WARNING_THRESHOLD:
        recommendations.append(
            f"Swap usage is high at {stats['percent']}%. "
            f"System may slow down. Consider freeing RAM or increasing swap."
        )

    elif stats['percent'] >= 50:
        recommendations.append(
            f"Swap usage at {stats['percent']}%. Moderate usage — monitor closely."
        )

    else:
        recommendations.append(f"Swap is healthy at {stats['percent']}%.")

    if is_linux():
        swappiness = get_swappiness()
        if swappiness > 30:
            recommendations.append(
                f"Swappiness is {swappiness} — consider lowering it to 10 "
                f"to prefer RAM over swap."
            )

    stats['recommendations'] = recommendations
    logger.info(f"Swap health check — {stats['percent']}% used | Status: {stats['status']}")
    return stats