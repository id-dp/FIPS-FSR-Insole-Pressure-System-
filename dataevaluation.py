# dataevaluation_perfect_image.py - KEIN STAUCHEN MEHR! Passt sich automatisch an dein Bild an

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.widgets import Slider
import matplotlib.image as mpimg
import os

# === Konfiguration ===
CSV_FILE = 'fsr_data.csv'
FOOT_IMAGE = 'foot.png'          # Dein eigenes Bild (kann .jpg oder .png sein!)
MAX_PRESSURE = 4095
CMAP = 'hot'

# Positionen der Sensoren (in relativen Einheiten 0-1, damit sie immer passen)
# Du kannst sie später feinjustieren (z. B. 0.35 → 0.38)
rel_positions = {
    0: (0.60, 0.12),  # FSR1 - Ferse (zentral)
    1: (0.37, 0.67),  # FSR2 - Mittelfuß links
    2: (0.65, 0.655),  # FSR3 - Mittelfuß rechts
    3: (0.40, 0.83),  # FSR4 - Großzeh (leicht links vom Zentrum)
    4: (0.65, 0.79),  # FSR5 - Ringzeh (rechts neben Großzeh, etwas tiefer)
}

# === Daten laden ===
if not os.path.exists(CSV_FILE):
    print(f"Fehler: {CSV_FILE} nicht gefunden!")
    exit()

df = pd.read_csv(CSV_FILE)
print(f"Geladen: {len(df)} Samples → {len(df)/50:.1f} Sekunden")
timestamps = df['timestamp'].values
data = df[['fsr1', 'fsr2', 'fsr3', 'fsr4', 'fsr5']].values

# === Bild laden und Plot anpassen ===
fig, ax = plt.subplots(figsize=(10, 14))
plt.subplots_adjust(bottom=0.2)

if os.path.exists(FOOT_IMAGE):
    img = mpimg.imread(FOOT_IMAGE)
    img_height, img_width = img.shape[:2]
    img_aspect = img_width / img_height  # echtes Seitenverhältnis deines Bildes
    
    plot_width = 10
    plot_height = plot_width / img_aspect  # Höhe automatisch anpassen → kein Stauchen!
    
    print(f"Dein Bild hat Aspect {img_aspect:.2f} → Plot wird perfekt angepasst auf {plot_width}x{plot_height:.1f}")
    
    ax.imshow(img, extent=[0, plot_width, 0, plot_height], aspect='equal', alpha=0.95, zorder=0)
else:
    print("Bild nicht gefunden → graue Kontur")
    plot_width, plot_height = 10, 14
    foot_outline = plt.Polygon([
        (2,plot_height),(4,plot_height),(8,plot_height-1),(9,plot_height-3),(8,plot_height-7),
        (9,plot_height-10),(7,0),(5,0),(3,plot_height-10),(4,plot_height-7),(3,plot_height-3),(2,plot_height)
    ], closed=True, color='lightgray', alpha=0.3)
    ax.add_patch(foot_outline)

# Limits setzen (jetzt perfekt auf dein Bild abgestimmt)
ax.set_xlim(0, plot_width)
ax.set_ylim(0, plot_height)
ax.set_aspect('equal')
ax.axis('off')

# Sensor-Kreise (relative Positionen → skalieren automatisch mit)
circles, glows, texts = [], [], []
for i in range(5):
    rel_x, rel_y = rel_positions[i]
    abs_x = rel_x * plot_width
    abs_y = rel_y * plot_height
    
    glow = Circle((abs_x, abs_y), plot_width*0.15, ec='none', fc='yellow', alpha=0)
    ax.add_patch(glow)
    glows.append(glow)
    
    circle = Circle((abs_x, abs_y), plot_width*0.11, lw=2, ec='black', fc='blue', alpha=0.9)
    ax.add_patch(circle)
    circles.append(circle)
    
    text = ax.text(abs_x, abs_y, "0", ha='center', va='center', fontweight='bold', color='white', fontsize=11)
    texts.append(text)

ax.set_title('FSR Fußdruck-Heatmap – Perfekt auf dein Bild abgestimmt!', fontsize=16)

# === Slider ===
slider_ax = plt.axes([0.15, 0.08, 0.70, 0.03])
slider = Slider(slider_ax, 'Zeitpunkt', 0, len(df)-1, valinit=0, valstep=1)

def update(val):
    idx = int(slider.val)
    pressures = data[idx]
    norm = np.clip(pressures / MAX_PRESSURE, 0, 1)

    for i in range(5):
        intensity = norm[i]
        circles[i].set_facecolor(plt.cm.get_cmap(CMAP)(intensity))
        glows[i].set_alpha(intensity * 0.6)
        texts[i].set_text(f"{int(pressures[i])}")

    fig.suptitle(f"Zeit: {timestamps[idx]:.3f}s | Sample {idx+1}/{len(df)} | Druck: {[int(p) for p in pressures]}", fontsize=12)
    fig.canvas.draw_idle()

slider.on_changed(update)

# Autoplay
playing = False
def toggle_play(event):
    global playing
    if event.key == ' ':
        playing = not playing
        print("Autoplay " + ("AN" if playing else "AUS"))
def autoplay():
    if playing:
        curr = int(slider.val)
        slider.set_val(curr + 1 if curr < len(df)-1 else 0)
    fig.canvas.draw_idle()
    plt.pause(0.02)

fig.canvas.mpl_connect('key_press_event', toggle_play)
timer = fig.canvas.new_timer(interval=20)
timer.add_callback(autoplay)
timer.start()

update(0)
print("\nJetzt sollte dein Bild perfekt rund und unverzerrt sein!")
print("Falls Kreise nicht 100% sitzen → ändere die Werte in 'rel_positions' (0.0 bis 1.0)")
plt.show()