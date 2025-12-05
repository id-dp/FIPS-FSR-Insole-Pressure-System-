# main.py – Final optimierte Version (dein Code + kleine Verbesserungen)

import machine
import time
import os

# === Konfiguration ===
FSR_PINS        = [32, 33, 34, 35, 36]   # ADC1-Pins
BUTTON_PIN      = 0                      # Boot-Button geht auch, aber GPIO 0 ist ok
DATA_FILE       = '/fsr_data.csv'
SAMPLE_RATE_HZ  = 50
INTERVAL_MS     = 1000 // SAMPLE_RATE_HZ  # = 20

# === Initialisierung ===
adcs = []
for pin in FSR_PINS:
    p = machine.Pin(pin)
    adc = machine.ADC(p)
    adc.atten(machine.ADC.ATTN_11DB)      # 0–3.3 V
    adc.width(machine.ADC.WIDTH_12BIT)    # optional: volle 12-Bit Auflösung
    adcs.append(adc)

button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
led    = machine.Pin(2, machine.Pin.OUT)
led.off()

recording       = False
last_state      = 1
debounce_ms     = 50
last_status_ms  = 0

# === Funktionen ===
def start_recording():
    global recording
    if recording:
        return
    print("\n>>> AUFNAHME GESTARTET <<<")
    try:
        with open(DATA_FILE, 'w') as f:
            f.write('timestamp,fsr1,fsr2,fsr3,fsr4,fsr5\n')
        recording = True
        led.on()
    except OSError:
        print("Kann Datei nicht erstellen – SD voll?")
        recording = False

def stop_recording():
    global recording
    if not recording:
        return
    size = os.stat(DATA_FILE)[6] if DATA_FILE in os.listdir() else 0
    samples = sum(1 for _ in open(DATA_FILE)) - 1  # -1 für Header
    duration = samples / SAMPLE_RATE_HZ
    print(f"\n>>> AUFNAHME GESTOPPT <<<")
    print(f"    {samples} Samples · {duration:.1f} s · {size} Bytes")
    recording = False
    led.off()

def toggle_recording():
    global recording
    if recording:
        stop_recording()
    else:
        start_recording()

# === Button-Entprellung ===
def check_button():
    global last_state
    state = button.value()
    if state == 0 and last_state == 1:              # fallende Flanke
        time.sleep_ms(debounce_ms)
        if button.value() == 0:                     # wirklich gedrückt
            toggle_recording()
            while button.value() == 0:              # warten bis losgelassen
                time.sleep_ms(10)
    last_state = state

# === Hauptloop ===
print("FSR-Datenlogger bereit – Button drücken zum Start/Stop")

while True:
    check_button()

    if recording:
        t0 = time.ticks_ms()

        values = [adc.read() for adc in adcs]
        timestamp = time.time()

        line = f"{timestamp:.3f},{values[0]},{values[1]},{values[2]},{values[3]},{values[4]}\n"

        try:
            with open(DATA_FILE, 'a') as f:
                f.write(line)
        except OSError as e:
            print("Speicherfehler!", e)
            stop_recording()

        # präzises Timing
        elapsed = time.ticks_diff(time.ticks_ms(), t0)
        if elapsed < INTERVAL_MS:
            time.sleep_ms(INTERVAL_MS - elapsed)

    else:
        time.sleep_ms(10)  # CPU entlasten

    # Statusmeldung alle 10 Sekunden
    now = time.ticks_ms()
    if recording and time.ticks_diff(now, last_status_ms) > 10000:
        size = os.stat(DATA_FILE)[6] if DATA_FILE in os.listdir() else 0
        print(f"Aufnahme läuft… {size//1024} KB")
        last_status_ms = now