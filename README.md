#  RAM Optimizer Pro

A smart, AI-powered RAM optimization and monitoring tool for Desktop (Linux, Windows, macOS).
Built with Python, it monitors memory usage in real time, predicts future RAM consumption using
Machine Learning, and automatically optimizes your system when needed.

---

##  Features

-  **Live RAM & Swap Monitoring** — real-time stats updated every 2 seconds
-  **Top Process Tracker** — identifies the biggest memory consumers
-  **AI Prediction** — predicts RAM usage 15, 30, and 60 minutes ahead using RandomForest ML
-  **One-Click Optimization** — frees RAM cache, kills zombie processes, reduces working sets
-  **Memory Compression** — zlib-based compression and Linux zram support
-  **Swap Manager** — monitors and manages swap memory health
-  **Smart Alerts** — desktop notifications at warning (80%) and critical (90%) thresholds
-  **Live Dashboard** — beautiful dark-themed GUI built with CustomTkinter
-  **27 Unit Tests** — fully tested core modules

---

##  Tech Stack

- **Python 3.10+**
- **psutil** — system memory and process monitoring
- **CustomTkinter** — modern dark-themed GUI
- **Matplotlib** — live charts and graphs
- **scikit-learn** — RandomForest ML model for RAM prediction
- **SQLite** — local database for usage history
- **plyer** — desktop notifications
- **joblib** — model persistence
- **pytest** — unit testing

---

##  Project Structure

```
ram_optimizer_pro/
├── ai/
│   ├── predictor.py
│   └── recommender.py
├── core/
│   ├── monitor.py
│   ├── analyzer.py
│   ├── optimizer.py
│   ├── compressor.py
│   └── swap_manager.py
├── ui/
│   ├── dashboard.py
│   ├── charts.py
│   └── alerts.py
├── utils/
│   ├── logger.py
│   ├── config.py
│   └── platform_utils.py
├── tests/
├── data/
├── main.py
└── requirements.txt
```

##  Installation

```bash
# Clone the repository
git clone https://github.com/sekumohamed/RAM_optimizer_project.git
cd RAM_optimizer_project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows


# Install dependencies
pip install -r requirements.txt
```

---


##  Usage

```bash
python main.py
```

The dashboard will launch automatically.

---

##  Running Tests

```bash
python -m pytest tests/ -v
```

---

##  How It Works

1. **Monitor** — psutil collects RAM stats every 2 seconds and saves to SQLite
2. **Analyze** — analyzer detects peak usage, memory hogs, and leak suspects
3. **Predict** — RandomForest model trains on historical data and predicts future usage
4. **Optimize** — optimizer frees cache, kills zombies, and reduces process working sets
5. **Alert** — desktop notifications fire at 80% (warning) and 90% (critical) thresholds
6. **Dashboard** — all data visualized in a live dark-themed GUI

---

##  Screenshots

> Dashboard showing live RAM stats, AI predictions, top processes, and alerts.

---

##  Contributing

Pull requests are welcome. For major changes, please open an issue first.

---

##  License

MIT License