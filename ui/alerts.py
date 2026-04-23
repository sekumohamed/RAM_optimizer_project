import threading
from plyer import notification
from utils.logger import get_logger
from utils.config import RAM_WARNING_THRESHOLD, RAM_CRITICAL_THRESHOLD, SWAP_WARNING_THRESHOLD

logger = get_logger(__name__)

# Track last alert to avoid spamming
_last_alert = {'ram': None, 'swap': None}

def send_desktop_notification(title: str, message: str, timeout: int = 8):
    # Send a desktop notification in a separate thread
    def _notify():
        try:
            notification.notify(
                title=title,
                message=message,
                app_name='RAM Optimizer Pro',
                timeout=timeout
            )
        except Exception as e:
            logger.warning(f"Desktop notification failed: {e}")

    threading.Thread(target=_notify, daemon=True).start()

def check_and_alert(ram_percent: float, swap_percent: float) -> list:
    # Check thresholds and fire alerts if needed
    alerts = []

    # RAM alerts
    if ram_percent >= RAM_CRITICAL_THRESHOLD:
        if _last_alert['ram'] != 'critical':
            _last_alert['ram'] = 'critical'
            msg = f"RAM usage is at {ram_percent}%! Auto-optimization triggered."
            logger.warning(f"[ALERT - CRITICAL] {msg}")
            send_desktop_notification("🔴 RAM Critical!", msg)
            alerts.append({'level': 'CRITICAL', 'message': msg})

    elif ram_percent >= RAM_WARNING_THRESHOLD:
        if _last_alert['ram'] != 'warning':
            _last_alert['ram'] = 'warning'
            msg = f"RAM usage is at {ram_percent}%. Consider closing unused apps."
            logger.warning(f"[ALERT - WARNING] {msg}")
            send_desktop_notification("⚠️ RAM Warning", msg)
            alerts.append({'level': 'WARNING', 'message': msg})

    else:
        # Reset alert state when RAM is healthy
        _last_alert['ram'] = None

    # Swap alerts
    if swap_percent >= SWAP_WARNING_THRESHOLD:
        if _last_alert['swap'] != 'warning':
            _last_alert['swap'] = 'warning'
            msg = f"Swap usage is high at {swap_percent}%. System may slow down."
            logger.warning(f"[ALERT - SWAP] {msg}")
            send_desktop_notification("⚠️ Swap Warning", msg)
            alerts.append({'level': 'WARNING', 'message': msg})
    else:
        _last_alert['swap'] = None

    return alerts

def format_alert_color(level: str) -> str:
    # Return color code for alert level
    colors = {
        'CRITICAL': '#f38ba8',
        'WARNING': '#fab387',
        'INFO': '#a6e3a1'
    }
    return colors.get(level, '#cdd6f4')

def get_alert_icon(level: str) -> str:
    icons = {
        'CRITICAL': '🔴',
        'WARNING': '⚠️',
        'INFO': '✅'
    }
    return icons.get(level, 'ℹ️')