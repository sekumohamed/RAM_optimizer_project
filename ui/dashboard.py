import customtkinter as ctk
import threading
import time
from datetime import datetime
from utils.logger import get_logger
from utils.config import RAM_WARNING_THRESHOLD, RAM_CRITICAL_THRESHOLD, AUTO_OPTIMIZE_ENABLED
from core.monitor import get_ram_stats, get_top_processes, init_db, start_monitoring
from core.optimizer import run_optimization
from core.swap_manager import monitor_swap_health
from ai.predictor import run_prediction_cycle
from ai.recommender import generate_recommendations
from ui.charts import create_live_chart, update_history
from ui.alerts import check_and_alert, format_alert_color, get_alert_icon

logger = get_logger(__name__)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class RAMOptimizerDashboard(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("RAM Optimizer Pro")
        self.geometry("1100x750")
        self.resizable(True, True)
        self.configure(fg_color="#1e1e2e")

        self._ram_data = {}
        self._processes = []
        self._alerts = []
        self._predictions = []
        self._monitoring = True

        init_db()
        self._build_ui()
        self._start_background_threads()

    def _build_ui(self):
        # ── Title Bar ──
        title_frame = ctk.CTkFrame(self, fg_color="#181825", corner_radius=0)
        title_frame.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(
            title_frame,
            text="🧠 RAM Optimizer Pro",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#89b4fa"
        ).pack(side="left", padx=20, pady=10)

        self.clock_label = ctk.CTkLabel(
            title_frame,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="#6c7086"
        )
        self.clock_label.pack(side="right", padx=20)

        # ── Main Layout ──
        main_frame = ctk.CTkFrame(self, fg_color="#1e1e2e")
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=0)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # ── Stats Panel (top left) ──
        stats_frame = ctk.CTkFrame(main_frame, fg_color="#181825", corner_radius=12)
        stats_frame.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")
        self._build_stats_panel(stats_frame)

        # ── Optimize Button Panel (top right) ──
        action_frame = ctk.CTkFrame(main_frame, fg_color="#181825", corner_radius=12)
        action_frame.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="nsew")
        self._build_action_panel(action_frame)

        # ── Live Chart (middle left) ──
        chart_frame = ctk.CTkFrame(main_frame, fg_color="#181825", corner_radius=12)
        chart_frame.grid(row=1, column=0, padx=(0, 5), pady=5, sticky="nsew")
        self._build_chart_panel(chart_frame)

        # ── Predictions Panel (middle right) ──
        pred_frame = ctk.CTkFrame(main_frame, fg_color="#181825", corner_radius=12)
        pred_frame.grid(row=1, column=1, padx=(5, 0), pady=5, sticky="nsew")
        self._build_prediction_panel(pred_frame)

        # ── Process Table (bottom left) ──
        proc_frame = ctk.CTkFrame(main_frame, fg_color="#181825", corner_radius=12)
        proc_frame.grid(row=2, column=0, padx=(0, 5), pady=5, sticky="nsew")
        self._build_process_panel(proc_frame)

        # ── Alerts Panel (bottom right) ──
        alert_frame = ctk.CTkFrame(main_frame, fg_color="#181825", corner_radius=12)
        alert_frame.grid(row=2, column=1, padx=(5, 0), pady=5, sticky="nsew")
        self._build_alerts_panel(alert_frame)

    def _build_stats_panel(self, parent):
        ctk.CTkLabel(
            parent, text="📊 Live Memory Stats",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#cdd6f4"
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # RAM progress bar
        self.ram_label = ctk.CTkLabel(parent, text="RAM: -- MB / -- MB (--%) ",
                                       text_color="#89b4fa", font=ctk.CTkFont(size=12))
        self.ram_label.pack(anchor="w", padx=15)

        self.ram_bar = ctk.CTkProgressBar(parent, width=400, height=18,
                                           progress_color="#89b4fa", fg_color="#313244")
        self.ram_bar.set(0)
        self.ram_bar.pack(anchor="w", padx=15, pady=(2, 8))

        # Swap progress bar
        self.swap_label = ctk.CTkLabel(parent, text="Swap: -- MB / -- MB (--%) ",
                                        text_color="#f38ba8", font=ctk.CTkFont(size=12))
        self.swap_label.pack(anchor="w", padx=15)

        self.swap_bar = ctk.CTkProgressBar(parent, width=400, height=18,
                                            progress_color="#f38ba8", fg_color="#313244")
        self.swap_bar.set(0)
        self.swap_bar.pack(anchor="w", padx=15, pady=(2, 10))

    def _build_action_panel(self, parent):
        ctk.CTkLabel(
            parent, text="⚙️ Actions",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#cdd6f4"
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.optimize_btn = ctk.CTkButton(
            parent,
            text="🚀 Optimize RAM Now",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#89b4fa",
            text_color="#1e1e2e",
            hover_color="#74c7ec",
            corner_radius=10,
            height=40,
            command=self._on_optimize_click
        )
        self.optimize_btn.pack(padx=15, pady=5, fill="x")

        self.optimize_status = ctk.CTkLabel(
            parent, text="",
            font=ctk.CTkFont(size=11),
            text_color="#a6e3a1"
        )
        self.optimize_status.pack(padx=15)

        ctk.CTkButton(
            parent,
            text="🔍 Run Analysis",
            font=ctk.CTkFont(size=12),
            fg_color="#313244",
            text_color="#cdd6f4",
            hover_color="#45475a",
            corner_radius=10,
            height=35,
            command=self._on_analysis_click
        ).pack(padx=15, pady=5, fill="x")

        ctk.CTkButton(
            parent,
            text="🤖 Refresh Predictions",
            font=ctk.CTkFont(size=12),
            fg_color="#313244",
            text_color="#cdd6f4",
            hover_color="#45475a",
            corner_radius=10,
            height=35,
            command=self._on_predict_click
        ).pack(padx=15, pady=5, fill="x")

    def _build_chart_panel(self, parent):
        ctk.CTkLabel(
            parent, text="📈 Live RAM & Swap Usage",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#cdd6f4"
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.chart_canvas, self.chart_ani = create_live_chart(parent)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)

    def _build_prediction_panel(self, parent):
        ctk.CTkLabel(
            parent, text="🤖 AI Predictions",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#cdd6f4"
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.pred_labels = []
        for horizon in ['15 min', '30 min', '60 min']:
            row = ctk.CTkFrame(parent, fg_color="#313244", corner_radius=8)
            row.pack(fill="x", padx=15, pady=3)
            ctk.CTkLabel(row, text=f"In {horizon}:",
                         text_color="#6c7086", font=ctk.CTkFont(size=12)).pack(side="left", padx=10, pady=6)
            val = ctk.CTkLabel(row, text="--% | --",
                               text_color="#a6e3a1", font=ctk.CTkFont(size=12, weight="bold"))
            val.pack(side="right", padx=10)
            self.pred_labels.append(val)

    def _build_process_panel(self, parent):
        ctk.CTkLabel(
            parent, text="🔥 Top Memory Consumers",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#cdd6f4"
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Header row
        header = ctk.CTkFrame(parent, fg_color="#313244", corner_radius=6)
        header.pack(fill="x", padx=15, pady=(0, 3))
        for col, width in [("Process", 200), ("PID", 70), ("RAM (MB)", 90), ("CPU %", 70)]:
            ctk.CTkLabel(header, text=col, width=width,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#6c7086").pack(side="left", padx=5, pady=4)

        # Process rows
        self.proc_rows = []
        for _ in range(8):
            row = ctk.CTkFrame(parent, fg_color="#1e1e2e", corner_radius=4)
            row.pack(fill="x", padx=15, pady=1)
            labels = []
            for width in [200, 70, 90, 70]:
                lbl = ctk.CTkLabel(row, text="--", width=width,
                                   font=ctk.CTkFont(size=11), text_color="#cdd6f4")
                lbl.pack(side="left", padx=5, pady=3)
                labels.append(lbl)
            self.proc_rows.append(labels)

    def _build_alerts_panel(self, parent):
        ctk.CTkLabel(
            parent, text="🔔 Alerts & Recommendations",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#cdd6f4"
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.alerts_box = ctk.CTkScrollableFrame(parent, fg_color="#1e1e2e", corner_radius=8)
        self.alerts_box.pack(fill="both", expand=True, padx=15, pady=5)

        self.alert_message_label = ctk.CTkLabel(
            self.alerts_box,
            text="✅ System is healthy. Monitoring...",
            text_color="#a6e3a1",
            font=ctk.CTkFont(size=11),
            wraplength=280,
            justify="left"
        )
        self.alert_message_label.pack(anchor="w", padx=5, pady=5)

    # ── Background Threads ──

    def _start_background_threads(self):
        threading.Thread(target=self._monitor_loop, daemon=True).start()
        threading.Thread(target=self._prediction_loop, daemon=True).start()
        threading.Thread(target=self._clock_loop, daemon=True).start()

    def _monitor_loop(self):
        while self._monitoring:
            try:
                stats = get_ram_stats()
                processes = get_top_processes()
                self._ram_data = stats
                self._processes = processes

                update_history(stats['percent_used'], stats['swap_percent'])
                alerts = check_and_alert(stats['percent_used'], stats['swap_percent'])

                # Auto-optimize if critical
                if stats['percent_used'] >= RAM_CRITICAL_THRESHOLD and AUTO_OPTIMIZE_ENABLED:
                    run_optimization()

                self.after(0, self._update_stats_ui, stats, processes, alerts)
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
            time.sleep(2)

    def _prediction_loop(self):
        while self._monitoring:
            try:
                predictions = run_prediction_cycle()
                self._predictions = predictions
                self.after(0, self._update_predictions_ui, predictions)
            except Exception as e:
                logger.error(f"Prediction loop error: {e}")
            time.sleep(600)

    def _clock_loop(self):
        while self._monitoring:
            now = datetime.now().strftime("%A, %d %b %Y  %H:%M:%S")
            self.after(0, self.clock_label.configure, {"text": now})
            time.sleep(1)

    # ── UI Update Methods ──

    def _update_stats_ui(self, stats, processes, alerts):
        # Update RAM bar
        ram_pct = stats['percent_used'] / 100
        color = "#f38ba8" if stats['percent_used'] >= RAM_CRITICAL_THRESHOLD else \
                "#fab387" if stats['percent_used'] >= RAM_WARNING_THRESHOLD else "#89b4fa"

        self.ram_bar.configure(progress_color=color)
        self.ram_bar.set(ram_pct)
        self.ram_label.configure(
            text=f"RAM: {stats['used_mb']} MB / {stats['total_mb']} MB ({stats['percent_used']}%)"
        )

        # Update Swap bar
        swap_pct = stats['swap_percent'] / 100 if stats['swap_total_mb'] > 0 else 0
        self.swap_bar.set(swap_pct)
        self.swap_label.configure(
            text=f"Swap: {stats['swap_used_mb']} MB / {stats['swap_total_mb']} MB ({stats['swap_percent']}%)"
        )

        # Update process table
        for i, labels in enumerate(self.proc_rows):
            if i < len(processes):
                p = processes[i]
                labels[0].configure(text=p['name'][:25])
                labels[1].configure(text=str(p['pid']))
                labels[2].configure(text=str(p['memory_mb']))
                labels[3].configure(text=str(p['cpu_percent']))
            else:
                for lbl in labels:
                    lbl.configure(text="--")

        # Update alerts
        if alerts:
            alert_text = "\n".join(
                [f"{get_alert_icon(a['level'])} {a['message']}" for a in alerts]
            )
            self.alert_message_label.configure(
                text=alert_text,
                text_color=format_alert_color(alerts[0]['level'])
            )
        else:
            self.alert_message_label.configure(
                text="✅ System is healthy. Monitoring...",
                text_color="#a6e3a1"
            )

    def _update_predictions_ui(self, predictions):
        risk_colors = {
            'HEALTHY': '#a6e3a1',
            'MODERATE': '#fab387',
            'WARNING': '#f9e2af',
            'CRITICAL': '#f38ba8'
        }
        for i, pred in enumerate(predictions):
            if i < len(self.pred_labels) and pred.get('status') == 'success':
                color = risk_colors.get(pred['risk_level'], '#cdd6f4')
                self.pred_labels[i].configure(
                    text=f"{pred['predicted_percent']}% | {pred['risk_level']}",
                    text_color=color
                )

    # ── Button Handlers ──

    def _on_optimize_click(self):
        self.optimize_status.configure(text="⏳ Optimizing...", text_color="#f9e2af")
        self.optimize_btn.configure(state="disabled")

        def _run():
            result = run_optimization(force=True)
            status = (
                f"✅ Freed {result.get('freed_percent', 0)}%"
                if result.get('status') == 'success'
                else "ℹ️ Optimization skipped"
            )
            self.after(0, self.optimize_status.configure, {"text": status, "text_color": "#a6e3a1"})
            self.after(0, self.optimize_btn.configure, {"state": "normal"})

        threading.Thread(target=_run, daemon=True).start()

    def _on_analysis_click(self):
        def _run():
            from ai.recommender import generate_recommendations
            recs = generate_recommendations()
            text = "\n".join([f"{get_alert_icon(r['level'])} {r['message']}" for r in recs])
            self.after(0, self.alert_message_label.configure, {"text": text, "text_color": "#cdd6f4"})

        threading.Thread(target=_run, daemon=True).start()

    def _on_predict_click(self):
        def _run():
            predictions = run_prediction_cycle()
            self.after(0, self._update_predictions_ui, predictions)

        threading.Thread(target=_run, daemon=True).start()

    def on_closing(self):
        self._monitoring = False
        self.destroy()


def launch_dashboard():
    app = RAMOptimizerDashboard()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()