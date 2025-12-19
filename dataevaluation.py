# dataevaluation.py - Klassenbasierte Fußdruck-Visualisierung

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.widgets import Slider
import matplotlib.image as mpimg
import os


class FootPressureVisualizer:
    def __init__(self, csv_file='fsr_data.csv', foot_image='foot.png', max_pressure=4095, cmap='hot'):
        self.csv_file = csv_file
        self.foot_image = foot_image
        self.max_pressure = max_pressure
        self.cmap = cmap

        # Relative Sensorpositionen (0.0 bis 1.0) – leicht angepasst an deine letzte Version
        self.rel_positions = {
            0: (0.60, 0.12),   # Ferse zentral
            1: (0.37, 0.67),   # Mittelfuß links
            2: (0.65, 0.655),  # Mittelfuß rechts
            3: (0.40, 0.83),   # Großzeh
            4: (0.65, 0.79),   # Ringzeh
        }

        self.df = None
        self.timestamps = None
        self.data = None
        self.fig = None
        self.ax = None
        self.slider = None
        self.circles = []
        self.glows = []
        self.texts = []
        self.playing = False

        self._load_data()
        self._setup_plot()
        self._setup_interaction()

    def _load_data(self):
        if not os.path.exists(self.csv_file):
            raise FileNotFoundError(f"CSV-Datei '{self.csv_file}' nicht gefunden!")
        
        self.df = pd.read_csv(self.csv_file)
        print(f"Geladen: {len(self.df)} Samples → {len(self.df)/50:.1f} Sekunden")
        
        self.timestamps = self.df['timestamp'].values
        self.data = self.df[['fsr1', 'fsr2', 'fsr3', 'fsr4', 'fsr5']].values

    def _setup_plot(self):
        self.fig, self.ax = plt.subplots(figsize=(10, 14))
        plt.subplots_adjust(bottom=0.2)

        plot_width = 10
        plot_height = 14

        # Bild laden und Aspect Ratio anpassen
        if os.path.exists(self.foot_image):
            img = mpimg.imread(self.foot_image)
            img_height, img_width = img.shape[:2]
            img_aspect = img_width / img_height
            plot_height = plot_width / img_aspect
            print(f"Bild-Aspect: {img_aspect:.2f} → Plot: {plot_width} x {plot_height:.1f}")

            self.ax.imshow(img, extent=[0, plot_width, 0, plot_height], aspect='equal', alpha=0.95, zorder=0)
        else:
            print("Bild nicht gefunden → Fallback-Kontur")
            foot_outline = plt.Polygon([
                (2, plot_height), (4, plot_height), (8, plot_height-1), (9, plot_height-3),
                (8, plot_height-7), (9, plot_height-10), (7, 0), (5, 0),
                (3, plot_height-10), (4, plot_height-7), (3, plot_height-3), (2, plot_height)
            ], closed=True, color='lightgray', alpha=0.3)
            self.ax.add_patch(foot_outline)

        self.ax.set_xlim(0, plot_width)
        self.ax.set_ylim(0, plot_height)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.ax.set_title('FSR Fußdruck-Heatmap', fontsize=16)

        # Sensoren zeichnen
        for i in range(5):
            rel_x, rel_y = self.rel_positions[i]
            x = rel_x * plot_width
            y = rel_y * plot_height

            glow = Circle((x, y), plot_width * 0.15, ec='none', fc='yellow', alpha=0)
            self.ax.add_patch(glow)
            self.glows.append(glow)

            circle = Circle((x, y), plot_width * 0.11, lw=2, ec='black', fc='blue', alpha=0.9)
            self.ax.add_patch(circle)
            self.circles.append(circle)

            text = self.ax.text(x, y, "0", ha='center', va='center', fontweight='bold',
                                color='white', fontsize=11)
            self.texts.append(text)

    def _setup_interaction(self):
        # Slider
        slider_ax = plt.axes([0.15, 0.08, 0.70, 0.03])
        self.slider = Slider(slider_ax, 'Zeitpunkt', 0, len(self.df)-1, valinit=0, valstep=1)
        self.slider.on_changed(self._update)

        # Autoplay mit Leertaste
        self.fig.canvas.mpl_connect('key_press_event', self._toggle_play)
        timer = self.fig.canvas.new_timer(interval=20)
        timer.add_callback(self._autoplay)
        timer.start()

        self._update(0)

    def _update(self, val):
        idx = int(self.slider.val)
        pressures = self.data[idx]
        norm = np.clip(pressures / self.max_pressure, 0, 1)

        for i in range(5):
            intensity = norm[i]
            self.circles[i].set_facecolor(plt.cm.get_cmap(self.cmap)(intensity))
            self.glows[i].set_alpha(intensity * 0.6)
            self.texts[i].set_text(f"{int(pressures[i])}")

        rel_time = self.timestamps[idx] - self.timestamps[0]
        self.fig.suptitle(f"Zeit: {rel_time:.3f} s | Sample {idx+1}/{len(self.df)} | "
                          f"Druck: {[int(p) for p in pressures]}", fontsize=12)
        self.fig.canvas.draw_idle()

    def _toggle_play(self, event):
        if event.key == ' ':
            self.playing = not self.playing
            print("Autoplay " + ("AN" if self.playing else "AUS"))

    def _autoplay(self):
        if self.playing:
            curr = int(self.slider.val)
            new_val = curr + 1 if curr < len(self.df) - 1 else 0
            self.slider.set_val(new_val)

    def show(self):
        plt.show()


# === Start ===
if __name__ == "__main__":
    viz = FootPressureVisualizer(csv_file='fsr_data.csv', foot_image='foot.png')
    viz.show()