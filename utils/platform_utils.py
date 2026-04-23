import platform
import os
import subprocess
from utils.logger import get_logger

logger = get_logger(__name__)

# Detect current operating system
OS_TYPE = platform.system()  # 'Windows', 'Linux', or 'Darwin' (macOS)

def get_os():
    return OS_TYPE

def is_windows():
    return OS_TYPE == 'Windows'

def is_linux():
    return OS_TYPE == 'Linux'

def is_mac():
    return OS_TYPE == 'Darwin'

def clear_ram_cache():
    # Clear RAM cache based on OS
    try:
        if is_linux():
            subprocess.run(['sudo', 'sync'], check=True)
            subprocess.run(['sudo', 'sh', '-c', 'echo 3 > /proc/sys/vm/drop_caches'], check=True)
            logger.info("Linux RAM cache cleared.")

        elif is_mac():
            subprocess.run(['sudo', 'purge'], check=True)
            logger.info("macOS RAM cache cleared.")

        elif is_windows():
            # Windows cache clearing via EmptyStandbyList tool (if available)
            subprocess.run(['EmptyStandbyList.exe', 'workingsets'], check=True)
            logger.info("Windows RAM working sets cleared.")

        else:
            logger.warning(f"Unsupported OS: {OS_TYPE}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Cache clear failed: {e}")

def kill_process(pid: int):
    # Terminate a process by PID
    try:
        if is_windows():
            subprocess.run(['taskkill', '/PID', str(pid), '/F'], check=True)
        else:
            subprocess.run(['kill', '-9', str(pid)], check=True)
        logger.info(f"Process {pid} terminated.")

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to kill process {pid}: {e}")

def get_platform_info():
    return {
        'os': OS_TYPE,
        'version': platform.version(),
        'architecture': platform.architecture()[0],
        'processor': platform.processor(),
        'machine': platform.machine()
    }