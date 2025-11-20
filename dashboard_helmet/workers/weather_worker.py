import time
import requests
from PySide6.QtCore import QThread, Signal

class WeatherWorker(QThread):
    weather_updated = Signal(dict)

    def __init__(self, api_key, city):
        super().__init__()
        self.api_key = api_key
        self.city = city
        self.is_running = True

    def run(self):
        while self.is_running:
            # Skip if no valid key provided
            if not self.api_key or len(self.api_key) < 10:
                self._sleep_interruptible(1800) # Sleep 30 mins
                continue
                
            try:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={self.city}&appid={self.api_key}&units=metric"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    weather_data = {
                        "city": data['name'],
                        "temp": f"{data['main']['temp']:.1f}",
                        "condition": data['weather'][0]['description'].title(),
                        "icon_url": f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png"
                    }
                    self.weather_updated.emit(weather_data)
                else:
                    print(f"Error fetching weather: {response.status_code}")
                    
            except Exception as e:
                print(f"An error occurred in WeatherWorker: {e}")
            
            # Update every 30 minutes (1800 seconds)
            self._sleep_interruptible(1800)

    def _sleep_interruptible(self, seconds):
        """Allows the thread to stop immediately even if sleeping."""
        for _ in range(seconds):
            if not self.is_running:
                break
            time.sleep(1)

    def stop(self):
        print("Stopping Weather Worker...")
        self.is_running = False
        self.wait()