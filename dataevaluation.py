# dataevaluation.py - Interaktive Druck-Heatmap mit Slider
# Benötigt: Python 3, matplotlib, numpy, pandas
# Installation falls nötig: pip install matplotlib numpy pandas

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.widgets import Slider
import os

# === Konfiguration ===
CSV_FILE = 'fsr_data.csv'           # Name deiner CSV vom ESP32
MAX_PRESSURE = 4095                 # Maximaler ADC-Wert (12-Bit), anpassen falls kalibriert
CMAP = 'hot'                        # Farbskala: 'hot', 'viridis', 'plasma', 'Reds' etc.

# === Positionen der 5 FSRs auf dem Fuß (in cm oder willkürlichen Einheiten) ===
# Du kannst das an dein Foto anpassen – hier sehr gut passend zu deinem Bild:
positions = {
    0: (4.0, 13.5),   # FSR1 - Ferse links
    1: (6.5, 13.5),   # FSR2 - Ferse rechts
    2: (3.5, 8.0),    # FSR3 - Mittelfuß links
    3: (7.5, 7.5),    # FSR4 - Mittelfuß rechts / Ballen
    4: (5.5, 1.5),    # FSR5 - Großzehe / Vorfuß
}

# === Daten laden ===
if not os.path.exists(CSV_FILE):
    print(f"Fehler: {CSV_FILE} nicht gefunden!")
    print("Lege die CSV aus dem ESP32 in diesen Ordner.")
    exit()

df = pd.read_csv(CSV_FILE)
print(f"Geladen: {len(df)} Samples bei {50} Hz → {len(df)/50:.1f} Sekunden")

timestamps = df['timestamp'].values
data = df[['fsr1', 'fsr2', 'fsr3', 'fsr4', 'fsr5']].values

# === Plot vorbereiten ===
fig, ax = plt.subplots(figsize=(8, 12))
plt.subplots_adjust(bottom=0.2)  # Platz für Slider

# Fußkontur (optional schöner Hintergrund – du kannst ein Bild laden, wenn du willst)
foot_outline = plt.Polygon([
    (2,15), (4,15), (8,14), (9,12), (8,8), (9,4), (7,0), (5,0), (3,4), (4,8), (3,12), (2,15)
], closed=True, color='lightgray', alpha=0.3, linewidth=2)
ax.add_patch(foot_outline)

# Kreise für jeden Sensor
circles = []
for i in range(5):
    x, y = positions[i]
    circle = Circle((x, y), radius=1.3, linewidth=2, edgecolor='black', facecolor='blue', alpha=0.8)
    ax.add_patch(circle)
    circles.append(circle)

# Text für Druckwerte (optional)
texts = []
for i in range(5):
    x, y = positions[i]
    t = ax.text(x, y, "0", ha='center', va='center', fontweight='bold', color='white')
    texts.append(t)

ax.set_xlim(0, 10)
ax.set_ylim(-1, 16)
ax.set_aspect('equal')
ax.set_title('Live Fußdruck-Visualisierung (FSR 50 Hz)', fontsize=16)
ax.axis('off')

# === Slider ===
slider_ax = plt.axes([0.15, 0.08, 0.70, 0.03])
slider = Slider(slider_ax, 'Zeitpunkt', 0, len(df)-1, valinit=0, valstep=1)
slider.valtext.set_visible(False)

def update(val):
    idx = int(slider.val)
    pressures = data[idx]
    normalized = np.clip(pressures / MAX_PRESSURE, 0, 1)  # 0 bis 1

    for i, circle in enumerate(circles):
        intensity = normalized[i]
        # Farbe von blau (kein Druck) nach rot/gelb (stark)
        circle.set_facecolor(plt.cm.get_cmap(CMAP)(intensity))

        # Optional: Zahlen anzeigen
        texts[i].set_text(f"{pressures[i]}")

    # Zeit anzeigen
    fig.suptitle(f"Timestamp: {timestamps[idx]:.3f}s  |  Sample {idx+1}/{len(df)}  |  "
                 f"Druck: {[int(p) for p in pressures]}", fontsize=12)

    fig.canvas.draw_idle()

slider.on_changed(update)

# Startwert setzen
update(0)

# Play-Button Simulation (optional – drücke Leertaste für Autoplay)
playing = False
def toggle_play(event):
    global playing
    if event.key == ' ':
        playing = not playing
        if playing:
            print("Autoplay gestartet (Leertaste = Pause)")
        else:
            print("Pause")

def autoplay():
    if playing:
        current = int(slider.val)
        if current < len(df) - 1:
            slider.set_val(current + 1)
        else:
            slider.set_val(0)  # Loop
    fig.canvas.draw_idle()
    plt.pause(0.02)  # ca. 50 Hz

fig.canvas.mpl_connect('key_press_event', toggle_play)
timer = fig.canvas.new_timer(interval=20)  # 50 Hz
timer.add_callback(autoplay)
timer.start()

print("\nSteuerung:")
print("   ← → oder Mausrad: durch die Zeit navigieren")
print("   Leertaste: Autoplay ein/aus (50 Hz Wiedergabe)")
print("   Schließen mit Fenster-X")

plt.show()