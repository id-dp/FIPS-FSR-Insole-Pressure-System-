# main.py - Klassenbasierter FSR-Datenlogger für ESP32

import machine
import time
import os


class FSRDataLogger:
    def __init__(self, fsr_pins=[32, 33, 34, 35, 25], button_pin=23, data_file='/fsr_data.csv', sample_rate=50):
        self.fsr_pins = fsr_pins
        self.button_pin = button_pin
        self.data_file = data_file
        self.sample_rate = sample_rate
        self.interval_ms = 1000 // sample_rate

        self.adcs = self._init_adcs()
        self.button = machine.Pin(self.button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.led = machine.Pin(2, machine.Pin.OUT)
        self.led.off()

        self.recording = False
        self.last_button_state = 1
        self.last_status_ms = 0

    def _init_adcs(self):
        adcs = []
        for pin in self.fsr_pins:
            p = machine.Pin(pin)
            adc = machine.ADC(p)
            adc.atten(machine.ADC.ATTN_11DB)
            adc.width(machine.ADC.WIDTH_12BIT)
            adcs.append(adc)
        return adcs

    def start_recording(self):
        if self.recording:
            return
        print("\n>>> AUFNAHME GESTARTET <<<")
        try:
            with open(self.data_file, 'w') as f:
                header = 'timestamp,' + ','.join([f'fsr{i+1}' for i in range(len(self.fsr_pins))]) + '\n'
                f.write(header)
            self.recording = True
            self.led.on()
        except OSError:
            print("Kann Datei nicht erstellen – Speicher voll?")
            self.recording = False

    def stop_recording(self):
        if not self.recording:
            return
        try:
            size = os.stat(self.data_file)[6]
            samples = sum(1 for _ in open(self.data_file)) - 1
            duration = samples / self.sample_rate
            print(f"\n>>> AUFNAHME GESTOPPT <<<")
            print(f"    {samples} Samples · {duration:.1f} s · {size} Bytes")
        except:
            print("\n>>> AUFNAHME GESTOPPT <<<")
        self.recording = False
        self.led.off()

    def toggle_recording(self):
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def check_button(self):
        state = self.button.value()
        if state == 0 and self.last_button_state == 1:
            time.sleep_ms(50)
            if self.button.value() == 0:
                self.toggle_recording()
                while self.button.value() == 0:
                    time.sleep_ms(10)
        self.last_button_state = state

    def run(self):
        print("FSR-Datenlogger bereit – Button drücken zum Start/Stop")
        while True:
            self.check_button()

            if self.recording:
                t0 = time.ticks_ms()

                values = [adc.read() for adc in self.adcs]
                timestamp = time.time()
                line = f"{timestamp:.3f},{','.join(map(str, values))}\n"

                try:
                    with open(self.data_file, 'a') as f:
                        f.write(line)
                except OSError as e:
                    print("Speicherfehler!", e)
                    self.stop_recording()

                elapsed = time.ticks_diff(time.ticks_ms(), t0)
                if elapsed < self.interval_ms:
                    time.sleep_ms(self.interval_ms - elapsed)
            else:
                time.sleep_ms(10)

            if self.recording and time.ticks_diff(time.ticks_ms(), self.last_status_ms) > 10000:
                try:
                    size = os.stat(self.data_file)[6]
                    print(f"Aufnahme läuft… {size//1024} KB")
                except:
                    pass
                self.last_status_ms = time.ticks_ms()


# === Start ===
logger = FSRDataLogger()
logger.run()