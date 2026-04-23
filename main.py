import threading
from utils.logger import get_logger
from utils.platform_utils import get_platform_info
from core.monitor import init_db

logger = get_logger(__name__)

def main():
    logger.info("=" * 50)
    logger.info("RAM Optimizer Pro — Starting Up")
    logger.info("=" * 50)

    info = get_platform_info()
    logger.info(f"OS        : {info['os']} {info['version']}")
    logger.info(f"Processor : {info['processor']}")
    logger.info(f"Arch      : {info['architecture']}")

    init_db()

    # Launch GUI dashboard
    from ui.dashboard import launch_dashboard
    launch_dashboard()

if __name__ == '__main__':
    main()