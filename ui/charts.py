import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
from utils.logger import get_logger

logger = get_logger(__name__)

# Store last 60 readings for live graph
MAX_POINTS = 60
ram_history = deque([0] * MAX_POINTS, maxlen=MAX_POINTS)
swap_history = deque([0] * MAX_POINTS, maxlen=MAX_POINTS)

def update_history(ram_percent: float, swap_percent: float):
    # Add new readings to history
    ram_history.append(ram_percent)
    swap_history.append(swap_percent)

def create_live_chart(parent_frame):
    # Create live RAM/Swap line chart embedded in tkinter frame
    fig, ax = plt.subplots(figsize=(7, 2.5), facecolor='#1e1e2e')
    ax.set_facecolor('#1e1e2e')
    ax.tick_params(colors='white')
    ax.spines['bottom'].set_color('#444')
    ax.spines['top'].set_color('#444')
    ax.spines['left'].set_color('#444')
    ax.spines['right'].set_color('#444')

    ram_line, = ax.plot([], [], color='#89b4fa', linewidth=2, label='RAM %')
    swap_line, = ax.plot([], [], color='#f38ba8', linewidth=2, label='Swap %')

    ax.set_xlim(0, MAX_POINTS)
    ax.set_ylim(0, 100)
    ax.set_ylabel('Usage %', color='white', fontsize=9)
    ax.legend(loc='upper left', fontsize=8, facecolor='#313244', labelcolor='white')
    ax.grid(True, color='#313244', linestyle='--', linewidth=0.5)

    fig.tight_layout()

    def animate(frame):
        ram_line.set_data(range(MAX_POINTS), list(ram_history))
        swap_line.set_data(range(MAX_POINTS), list(swap_history))
        return ram_line, swap_line

    ani = animation.FuncAnimation(fig, animate, interval=2000, blit=True)

    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()

    return canvas, ani

def create_process_pie(parent_frame, process_data: list):
    # Create pie chart of top process memory usage
    fig, ax = plt.subplots(figsize=(3.5, 3.5), facecolor='#1e1e2e')
    ax.set_facecolor('#1e1e2e')

    if not process_data:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', color='white')
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        return canvas

    names = [p['name'][:12] for p in process_data[:5]]
    sizes = [p['memory_mb'] for p in process_data[:5]]
    colors = ['#89b4fa', '#a6e3a1', '#f38ba8', '#fab387', '#cba6f7']

    ax.pie(sizes, labels=names, colors=colors, autopct='%1.1f%%',
           textprops={'color': 'white', 'fontsize': 8},
           wedgeprops={'edgecolor': '#1e1e2e'})

    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    return canvas