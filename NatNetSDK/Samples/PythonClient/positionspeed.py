import sys
import time
import numpy as np
import serial
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from NatNetClient import NatNetClient


def decode_timecode(timecode, subframe):
    hour = (timecode >> 24) & 255
    minute = (timecode >> 16) & 255
    second = (timecode >> 8) & 255
    frame = timecode & 255
    # Assuming 120 fps
    return hour * 3600 + minute * 60 + second + frame / 120 + subframe / 120.0


class PositionTracker(QThread):
    position_signal = pyqtSignal(int, tuple, float, int, bool)  # position, motive_time, frame, recording

    def __init__(self):
        super().__init__()
        self.streaming_client = NatNetClient()
        self.latest_timestamp = None
        self.latest_frame = None
        self.is_recording = False

        self.streaming_client.rigid_body_listener = self.receive_rigid_body_frame
        self.streaming_client.new_frame_listener = self.receive_frame_data

    def receive_frame_data(self, data_dict):
        self.latest_timestamp = decode_timecode(
            data_dict.get("timecode", 0),
            data_dict.get("timecode_sub", 0)
        )
        self.latest_frame = data_dict.get("frame_number", 0)
        self.is_recording = data_dict.get("is_recording", False)

    def receive_rigid_body_frame(self, rigid_body_id, position, orientation):
        if position and self.latest_timestamp is not None:
            self.position_signal.emit(
                rigid_body_id,
                position,
                self.latest_timestamp,
                self.latest_frame,
                self.is_recording
            )

    def run(self):
        print("✅ Listening for rigid body position updates...")
        self.streaming_client.run()


class PositionDisplay(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Real-Time Position & LED Control (Synced with Motive)")
        self.setGeometry(100, 100, 400, 300)

        self.layout = QVBoxLayout()

        self.label = QLabel("Waiting for position data...")
        self.label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.layout.addWidget(self.label)

        self.led_status_label = QLabel("LED Status: OFF")
        self.led_status_label.setStyleSheet("font-size: 16px; color: red;")
        self.layout.addWidget(self.led_status_label)

        self.speed_label = QLabel("Speed: 0.00 m/s")
        self.speed_label.setStyleSheet("font-size: 16px;")
        self.layout.addWidget(self.speed_label)

        self.motive_time_label = QLabel("Motive Time: 0.000 s")
        self.motive_time_label.setStyleSheet("font-size: 16px;")
        self.layout.addWidget(self.motive_time_label)

        self.setLayout(self.layout)

        self.serial_port = "COM18"
        self.baudrate = 115200
        try:
            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=1)
            time.sleep(2)
        except serial.SerialException as e:
            print(f"⚠️ Serial Error: {e}")
            self.ser = None

        self.tracker = PositionTracker()
        self.tracker.position_signal.connect(self.update_position)
        self.tracker.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_label)
        self.timer.start(100)

        self.current_position = np.array([0.0, 0.0, 0.0])
        self.previous_position = None
        self.previous_time = None
        self.current_speed = 0.0
        self.led_on = False

        # Parameters
        self.target_position = np.array([-0.01, 0.0, 0.62])
        self.distance_threshold = 0.6
        self.speed_threshold = 0.0008
        self.required_hold_time = 0.02
        self.led_grace_time = 0.2

        self.speed_hold_start_time = None
        self.led_last_on_time = None

    def update_position(self, rigid_body_id, position, motive_time, frame_number, is_recording):
        self.motive_time_label.setText(f"Motive Time: {motive_time:.3f} s")

        if not is_recording:
            print(f"⏸ Motive not recording | Frame: {frame_number}")
            return

        current_time = time.time()
        position_array = np.array(position)

        if self.previous_position is not None and self.previous_time is not None:
            dt = current_time - self.previous_time
            frame_distance = np.linalg.norm(position_array - self.previous_position)

            if dt > 0:
                if frame_distance < 0.0024:
                    raw_speed = 0.0
                elif frame_distance < 0.0025:
                    raw_speed = (frame_distance / dt) * 0.3
                else:
                    raw_speed = frame_distance / dt

                self.current_speed = raw_speed
                print(f"🎬 Frame: {frame_number} | ⏱ Motive Time: {motive_time:.6f} | 🚀 Speed: {self.current_speed:.4f} m/s | 📍 Distance: {frame_distance:.4f} m")

        self.previous_position = position_array
        self.previous_time = current_time
        self.current_position = position_array

        self.check_led_condition()

    def check_led_condition(self):
        now = time.time()
        distance = np.linalg.norm(self.current_position - self.target_position)

        if distance <= self.distance_threshold and self.current_speed >= self.speed_threshold:
            if self.speed_hold_start_time is None:
                self.speed_hold_start_time = now
            elif now - self.speed_hold_start_time >= self.required_hold_time:
                if not self.led_on:
                    self.send_led_command(True)
                    self.led_on = True
                self.led_last_on_time = now
        else:
            self.speed_hold_start_time = None
            if self.led_on and self.led_last_on_time is not None:
                if now - self.led_last_on_time > self.led_grace_time:
                    self.send_led_command(False)
                    self.led_on = False

    def send_led_command(self, state):
        if self.ser is None or not self.ser.is_open:
            print("⚠️ Serial port is not open.")
            return

        command = '1' if state else '0'
        try:
            self.ser.write(command.encode('utf-8'))
            print(f"💡 LED {'ON' if state else 'OFF'} command sent.")
            self.led_status_label.setText(f"LED Status: {'ON' if state else 'OFF'}")
            self.led_status_label.setStyleSheet("font-size: 16px; color: green;" if state else "font-size: 16px; color: red;")
        except Exception as e:
            print(f"⚠️ Failed to send LED command: {e}")

    def update_label(self):
        x, y, z = self.current_position
        self.label.setText(f"Rigid Body Position:\nX: {x:.2f}, Y: {y:.2f}, Z: {z:.2f}")
        self.speed_label.setText(f"Speed: {self.current_speed:.4f} m/s")

    def closeEvent(self, event):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.tracker.terminate()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PositionDisplay()
    window.show()
    sys.exit(app.exec_())
