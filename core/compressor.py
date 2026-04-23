import zlib
import subprocess
import platform
from utils.logger import get_logger
from utils.platform_utils import is_linux, is_windows, is_mac

logger = get_logger(__name__)

def compress_data(data: bytes, level: int = 6) -> bytes:
    # Compress raw bytes using zlib (level 1-9, higher = better compression)
    compressed = zlib.compress(data, level)
    original_size = len(data)
    compressed_size = len(compressed)
    ratio = round((1 - compressed_size / original_size) * 100, 2)
    logger.info(f"Compressed {original_size} bytes → {compressed_size} bytes ({ratio}% reduction)")
    return compressed

def decompress_data(data: bytes) -> bytes:
    # Decompress zlib-compressed bytes
    return zlib.decompress(data)

def get_zram_status() -> dict:
    # Check if zram is active on Linux
    if not is_linux():
        return {'supported': False, 'reason': 'zram is Linux-only'}

    try:
        result = subprocess.run(
            ['cat', '/sys/block/zram0/comp_algorithm'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            algorithm = result.stdout.strip()
            return {'supported': True, 'algorithm': algorithm}
        else:
            return {'supported': False, 'reason': 'zram device not found'}
    except FileNotFoundError:
        return {'supported': False, 'reason': 'zram module not loaded'}

def enable_zram(size_mb: int = 512) -> bool:
    # Enable zram swap on Linux
    if not is_linux():
        logger.warning("zram is only supported on Linux.")
        return False

    try:
        subprocess.run(['sudo', 'modprobe', 'zram'], check=True)
        subprocess.run(
            ['sudo', 'sh', '-c', f'echo {size_mb * 1024 * 1024} > /sys/block/zram0/disksize'],
            check=True
        )
        subprocess.run(['sudo', 'mkswap', '/dev/zram0'], check=True)
        subprocess.run(['sudo', 'swapon', '/dev/zram0', '-p', '10'], check=True)

        logger.info(f"zram enabled with {size_mb} MB compressed swap.")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to enable zram: {e}")
        return False

def disable_zram() -> bool:
    # Disable and reset zram on Linux
    if not is_linux():
        logger.warning("zram is only supported on Linux.")
        return False

    try:
        subprocess.run(['sudo', 'swapoff', '/dev/zram0'], check=True)
        subprocess.run(
            ['sudo', 'sh', '-c', 'echo 1 > /sys/block/zram0/reset'],
            check=True
        )
        logger.info("zram disabled and reset.")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to disable zram: {e}")
        return False

def get_compression_stats() -> dict:
    # Get zram compression statistics on Linux
    if not is_linux():
        return {}

    try:
        stats = {}
        with open('/sys/block/zram0/mm_stat', 'r') as f:
            values = f.read().split()
            stats['original_size_mb'] = round(int(values[0]) / 1024**2, 2)
            stats['compressed_size_mb'] = round(int(values[1]) / 1024**2, 2)
            stats['memory_used_mb'] = round(int(values[2]) / 1024**2, 2)
            if stats['original_size_mb'] > 0:
                stats['compression_ratio'] = round(
                    stats['original_size_mb'] / max(stats['compressed_size_mb'], 0.01), 2
                )
        return stats

    except FileNotFoundError:
        logger.warning("zram stats not available.")
        return {}

def compress_string(text: str) -> bytes:
    # Compress a string to bytes (utility for in-memory compression)
    return compress_data(text.encode('utf-8'))

def decompress_string(data: bytes) -> str:
    # Decompress bytes back to string
    return decompress_data(data).decode('utf-8')