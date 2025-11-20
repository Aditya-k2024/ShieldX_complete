import serial
import serial.tools.list_ports
import json
import time
from PySide6.QtCore import QThread, Signal

# Import Config
from config import DEFAULT_BAUD_RATE, DEFAULT_PORT_FALLBACK

class SerialWorker(QThread):
    # Signal to send data back to the Main Window
    data_received = Signal(dict)

    def __init__(self, baud_rate=DEFAULT_BAUD_RATE):
        super().__init__()
        self.baud_rate = baud_rate
        self.is_running = True
        self.port = self.find_esp32_port() # Auto-detect port

    def find_esp32_port(self):
        """Attempts to auto-detect a port with a connected device."""
        ports = serial.tools.list_ports.comports()
        for p in ports:
            # Common descriptions for ESP32/Arduino drivers
            if "USB" in p.description or "CP210" in p.description or "CH340" in p.description:
                print(f"Auto-detected Port: {p.device}")
                return p.device
        
        print(f"⚠️ No ESP32 found. Defaulting to {DEFAULT_PORT_FALLBACK}.")
        return DEFAULT_PORT_FALLBACK

    def send_command(self, command_char):
        """
        Sends a single character command to the ESP32.
        '1' = Turn Alarm ON
        '0' = Turn Alarm OFF
        """
        if hasattr(self, 'serial_conn') and self.serial_conn.is_open:
            try:
                self.serial_conn.write(command_char.encode())
            except Exception as e:
                print(f"❌ Send Error: {e}")

    def run(self):
        if not self.port:
            print("❌ No Port Selected.")
            return

        try:
            self.serial_conn = serial.Serial(self.port, self.baud_rate, timeout=1)
            print(f"✅ Connected to {self.port}")
            time.sleep(2) # Wait for connection to stabilize
        except Exception as e:
            print(f"❌ Serial Connection Error: {e}")
            self.is_running = False
            return

        while self.is_running:
            try:
                if self.serial_conn.in_waiting:
                    # Read line from ESP32
                    line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    
                    # Check if it looks like JSON
                    if line.startswith('{') and line.endswith('}'):
                        try:
                            data = json.loads(line)
                            self.data_received.emit(data)
                        except json.JSONDecodeError:
                            print(f"⚠️ Malformed JSON: {line}")
            except Exception as e:
                print(f"❌ Serial Loop Error: {e}")
                break
            
            self.msleep(10) # Prevent CPU hogging

    def stop(self):
        self.is_running = False
        if hasattr(self, 'serial_conn') and self.serial_conn.is_open:
            self.serial_conn.close()
        self.wait()