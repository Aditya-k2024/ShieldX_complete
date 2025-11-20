#include <Arduino.h>
#include <DHT.h>
#include <TinyGPS++.h>

// ----------------------
// PIN DEFINITIONS
// ----------------------
#define MQ9_PIN       34
#define DHT_PIN       32
#define BUTTON_PIN    13     
#define LED_PIN       5      
#define MOTOR_PIN     14     

#define DHT_TYPE      DHT11

// REMOVED: #define GAS_THRESHOLD
// The threshold is now 100% controlled by Python.

#define GPS_RX_PIN    16
#define GPS_TX_PIN    17
#define HELMET_ID "SH-001" 

// ----------------------
DHT dht(DHT_PIN, DHT_TYPE);
TinyGPSPlus gps;
HardwareSerial gpsSerial(2);

// ----------------------
// GAS CALCULATIONS (Raw Data Pass-through)
// ----------------------
float calcCH4(int raw) { return raw * 1.0; }
float calcCO(int raw)  { return raw * 1.0; }
float calcLPG(int raw) { return raw * 1.0; }

void setup() {
  Serial.begin(115200); 

  dht.begin();
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);

  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  pinMode(MOTOR_PIN, OUTPUT);

  // Ensure off at start
  digitalWrite(LED_PIN, LOW);
  digitalWrite(MOTOR_PIN, LOW);

  Serial.println("Safety Helmet System Started - Waiting for Python Commands..."); 
}

void loop() {
  // -------------------------------------------------
  // 1. READ COMMANDS FROM PYTHON (New Logic)
  // -------------------------------------------------
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    // '1' = Turn Alert ON
    if (command == '1') {
      digitalWrite(LED_PIN, HIGH);
      digitalWrite(MOTOR_PIN, HIGH);
    } 
    // '0' = Turn Alert OFF
    else if (command == '0') {
      digitalWrite(LED_PIN, LOW);
      digitalWrite(MOTOR_PIN, LOW);
    }
  }

  // ----------------------
  // 2. SENSOR READINGS
  // ----------------------
  int gasRaw = analogRead(MQ9_PIN);
  float CH4 = calcCH4(gasRaw);
  float CO  = calcCO(gasRaw);
  float LPG = calcLPG(gasRaw);

  float temp = dht.readTemperature();
  float hum  = dht.readHumidity();

  if (isnan(temp)) temp = 0.0;
  if (isnan(hum)) hum = 0.0;

  unsigned long start = millis();
  while (millis() - start < 500) { // Reduced delay slightly for faster response
    if (gpsSerial.available()) gps.encode(gpsSerial.read());
  }

  float lat = gps.location.isValid() ? gps.location.lat() : 23.6622598;
  float lon = gps.location.isValid() ? gps.location.lng() : 86.4726765;

  bool emergency = (digitalRead(BUTTON_PIN) == LOW);

  // ----------------------
  // 3. JSON OUTPUT
  // ----------------------
  String json = "{";
  json += "\"helmetId\": \"" + String(HELMET_ID) + "\",";
  json += "\"gas\": " + String(CO) + ",";          
  json += "\"methane\": " + String(CH4) + ",";     
  json += "\"natural_gas\": " + String(LPG) + ","; 
  json += "\"temperature\": " + String(temp) + ",";
  json += "\"humidity\": " + String(hum) + ",";
  json += "\"latitude\": " + String(lat, 6) + ",";
  json += "\"longitude\": " + String(lon, 6) + ",";
  json += "\"battery\": 100,"; 
  json += "\"emergency\": " + String(emergency ? "true" : "false");
  json += "}";

  Serial.println(json);
  
  // Reduced delay so the system is more responsive to commands
  delay(500); 
}