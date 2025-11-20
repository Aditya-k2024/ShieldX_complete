# 🛡️ ShieldX - Smart Helmet Fleet Dashboard

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)
![Platform](https://img.shields.io/badge/Platform-ESP32%2FArduino-orange.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)

**ShieldX** is a professional-grade desktop fleet dashboard for monitoring multiple smart helmets using **Python + PySide6 (Qt for Python)**. It serves as a central command unit for industrial safety, offering real-time telemetry, advanced data visualization, and worker profile management.

## 🚀 Key Features

### 🖥️ Live Command Center
* **Real-Time Sensor Feed:** Monitors CO (Gas) levels, Temperature, Humidity, and Battery status with smooth animations.
* **Interactive Fleet Map:** Integrated **Leaflet.js** map tracking all workers.
    * **🟢 Green Markers:** Safe status.
    * **🔴 Red Markers:** High gas alert or emergency.
* **Live Alerts Panel:** Instant visual list of active hazards. **Clicking an alert** instantly switches the dashboard view to the affected worker.
* **Connection Status:** Auto-detects hardware connection state (Connected/Disconnected/Simulation).

### 📊 Graph-Intense Analysis
* **Animated Visualizations:**
    * **Bar Charts:** Real-time CO trends with growth animations.
    * **Line Charts:** Temperature and Humidity history.
    * **Fleet Histogram:** Visualizes gas level distribution across the entire workforce.
* **Context-Aware Analytics:** Toggle between individual helmet history and fleet-wide averages using the interactive dropdown.

### 👷 Worker Profiles
* **Digital ID Cards:** Displays detailed worker info (Name, ID, Role, Contact) fetched dynamically.
* **Async Image Loading:** Fetches profile pictures from URLs smoothly on a background thread to ensure the UI never freezes.

### ⚙️ Dual Operation Modes
1.  **Live Mode:** Reads JSON packets from an ESP32/Arduino via USB Serial.
2.  **Simulation Mode:** Generates realistic random data to test the UI functionality without hardware attached.

---

## 🛠️ Tech Stack

### Software (Dashboard)
* **Language:** Python 3
* **UI Framework:** PySide6 (Qt for Python)
* **Map Rendering:** Qt WebEngine + Leaflet.js
* **Communication:** PySerial (USB/UART)
* **API:** OpenWeatherMap (for environmental context)

### Hardware (Firmware)
* **Microcontroller:** ESP32 or Arduino
* **Sensors:** MQ-9 (Gas), DHT11 (Temp/Hum), Neo-6M (GPS)
* **Features:** Interrupt-based Emergency Button, ArduinoJson serialization.

---

## 📂 Project Structure

```
ShieldX/
│
├── main.py                  
├── config.py                
├── utils.py                 
├── requirements.txt         
├── runtime.txt              
├── logo.png                
│
├── workers/                
│   ├── __init__.py
│   ├── serial_worker.py     
│   └── weather_worker.py    
│
└── ui/                     
    ├── __init__.py
    ├── main_window.py       
    │
    ├── components/          
    │   ├── __init__.py
    │   ├── shared.py        
    │   ├── cards.py         
    │   ├── graphs.py        
    │   └── maps.py         
    │
    └── pages/               
        ├── __init__.py
        ├── dashboard_page.py   
        ├── analysis_page.py    
        ├── warehouse_page.py   
        ├── fleet_map_page.py   
        └── settings_page.py    
```

---

## ⚡ How It Works

1.  **Data Ingestion:** The app runs a `DataWorker` thread.
    * In **Live Mode**, it listens to a COM port for JSON packets like: `{"helmetId":"SH-001", "gas":450, "lat":22.8, ...}`
    * In **Simulation Mode**, it generates random values every 200ms.
2.  **Processing:** Data is stored in a `deque` (double-ended queue) to maintain a scrolling history of the last 50 data points.
3.  **Visualization:** The UI updates continuously (approx 10fps) using `QTimer` and `QPropertyAnimation` for smooth transitions between data points.
4.  **Alert Logic:** If Gas > Threshold (default 900 ppm), the system triggers a visual alert, logs the event in the Data Warehouse, and updates the map markers to Red.

---

## 🔧 Setup Instructions

### 1. Install Dependencies
Ensure you have Python installed, then run:
```bash
pip install PySide6 pyserial requests
```

### 2. Configuration (main.py)
Open `main.py` and adjust the top configuration block to suit your needs.

**Option A: Run a Demo (No Hardware)**
```python
# --- CONFIGURATION ---
USE_SIMULATION = True
SERIAL_PORT = "COM3"  # Ignored in simulation mode
```

**Option B: Run with Hardware**
```python
# --- CONFIGURATION ---
USE_SIMULATION = False
SERIAL_PORT = "COM3"  # Change to your device's port (e.g., /dev/ttyUSB0 on Linux)
BAUD_RATE = 115200    # Ensure your Arduino code uses Serial.begin(115200)
```

### 3. (Optional) Weather API
Replace `API_KEY` in `main.py` with your free key from **OpenWeatherMap** to get real local weather data.

### 4. Run the Dashboard
```bash
python main.py
```

---

## 📊 Future Enhancements

- [ ] Replace USB Serial with MQTT for wireless/remote monitoring over WiFi.
- [ ] Add MongoDB integration for permanent data storage and report generation.
- [ ] Add Geofencing capabilities to the map for restricted zones.
