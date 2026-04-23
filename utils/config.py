import os

# Base project directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database path
DB_PATH = os.path.join(BASE_DIR, 'data', 'usage_history.db')

# Monitoring settings
MONITOR_INTERVAL_SECONDS = 2       # How often RAM is sampled
HISTORY_RETENTION_DAYS = 7         # Days of history to keep in DB

# RAM threshold settings (percentage)
RAM_WARNING_THRESHOLD = 80         # Show warning
RAM_CRITICAL_THRESHOLD = 90        # Trigger auto-optimization

# Swap threshold
SWAP_WARNING_THRESHOLD = 70        # Warn when swap exceeds this %

# AI Prediction settings
PREDICTION_INTERVAL_MINUTES = 10   # How often prediction runs
PREDICTION_HORIZON_MINUTES = 15    # How far ahead to predict

# Top processes to display in dashboard
TOP_PROCESS_COUNT = 10

# Auto-optimization
AUTO_OPTIMIZE_ENABLED = True       # Trigger optimizer at critical threshold