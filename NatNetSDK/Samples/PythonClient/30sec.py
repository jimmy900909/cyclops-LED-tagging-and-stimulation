import csv
import atexit
import os
import time
import tkinter as tk
import serial
from NatNetClient import NatNetClient


class RigidBodyLogger:
    def __init__(self):
        # Motive client
        self.client = NatNetClient()
        self.client.new_frame_listener = self.on_frame
        self.client.rigid_body_listener = self.on_rigid_body

        # Logging
        self.logging_started = False
        self.previous_frame = None
        self.start_frame = None
        self.current_frame = 0
        self.recorded_data = []
        self.start_wall_time = None

        # LED control
        self.led_on = False
        self.last_led_time = 0
        self.led_interval = 30   # seconds between LED pulses
        self.led_duration = 1    # seconds the LED stays ON

        # Serial communication
        self.serial_port = "COM18"
        self.baudrate = 115200
        try:
            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=1)
            time.sleep(2)
        except serial.SerialException as e:
            print(f"⚠️ Serial Error: {e}")
            self.ser = None

        # CSV save path
        self.csv_path = r"C:\Users\Admin\Desktop\123\rigid_body_positions.csv"
        atexit.register(self.save_csv)

        # UI Setup
        self.root = tk.Tk()
        self.root.title("Rigid Body Logger + LED Trigger")
        self.root.geometry("300x100")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        tk.Label(self.root, text="Logging + LED triggering...\nClose to save and exit.").pack(pady=20)

    def on_frame(self, data_dict):
        self.current_frame = data_dict.get("frame_number", 0)

        if self.previous_frame is not None:
            if self.previous_frame > 100 and self.current_frame < 10 and not self.logging_started:
                self.logging_started = True
                self.start_frame = self.current_frame
                self.start_wall_time = time.time()
                self.recorded_data.clear()
                self.last_led_time = self.start_wall_time
                print("✅ Logging started at frame reset!")

        self.previous_frame = self.current_frame

    def on_rigid_body(self, rigid_body_id, position, orientation):
        if not self.logging_started:
            return

        now = time.time()

        # LED trigger every 30s
        if now - self.last_led_time >= self.led_interval:
            self.send_led_command(True)
            self.led_on = True
            self.last_led_time = now

        # LED OFF after duration
        if self.led_on and now - self.last_led_time >= self.led_duration:
            self.send_led_command(False)
            self.led_on = False

        rel_frame = self.current_frame - self.start_frame if self.start_frame is not None else 0
        rel_time = now - self.start_wall_time if self.start_wall_time is not None else 0
        row = [rel_time, rel_frame, *position, int(self.led_on)]
        self.recorded_data.append(row)

        print(f"✅ Frame {rel_frame} | Time: {rel_time:.3f}s | Pos: {position} | LED: {int(self.led_on)}")

    def send_led_command(self, state):
        if self.ser is None or not self.ser.is_open:
            print("⚠️ Serial port not available")
            return
        command = '1' if state else '0'
        try:
            self.ser.write(command.encode('utf-8'))
            print(f"💡 LED {'ON' if state else 'OFF'} command sent")
        except Exception as e:
            print(f"⚠️ Failed to send LED command: {e}")

    def save_csv(self):
        if not self.recorded_data:
            print("⚠️ No data recorded. CSV not saved.")
            return
        try:
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Time (s)", "Frame", "X", "Y", "Z", "LED State"])
                writer.writerows(self.recorded_data)
            print(f"💾 Data saved to {self.csv_path}")
        except Exception as e:
            print(f"❌ Failed to save CSV: {e}")

    def on_close(self):
        print("🛑 UI closed. Saving data...")
        self.save_csv()
        self.root.destroy()
        os._exit(0)  # Force exit since client.run() is blocking

    def run(self):
        print("🔄 Waiting for recording to start in Motive...")
        self.client.run()


if __name__ == "__main__":
    logger = RigidBodyLogger()
    logger.root.after(100, logger.run)
    logger.root.mainloop()
