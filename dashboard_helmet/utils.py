import csv
import random
from datetime import datetime
from config import CSV_FILE

def generate_sample_csv(filename=CSV_FILE, num_rows=100, num_helmets=10):
    """
    Generates dummy data for testing the dashboard when no hardware is connected.
    """
    print(f"Generating {num_rows} rows of sample data for {num_helmets} helmets in {filename}...")
    
    helmet_ids = [f"SH-{i:03d}" for i in range(1, num_helmets + 1)]
    
    
    header = [
        "timestamp",
        "helmetId",
        "gas",
        "temperature",
        "humidity", 
        "latitude",
        "longitude",
        "emergency",
        "battery", 
        "methane",
        "natural_gas"
    ]
    
    try:
        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            
            for _ in range(num_rows):
                helmet_id = random.choice(helmet_ids)
                
                # Generate random sensor values
                gas = random.uniform(901, 1200) if random.random() < 0.2 else random.uniform(300, 800)
                emergency = True if random.random() < 0.02 else False
                
                row = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "helmetId": helmet_id,
                    "gas": f"{gas:.2f}",
                    "temperature": f"{random.uniform(28.0, 35.0):.2f}",
                    "humidity": f"{random.uniform(45.0, 65.0):.2f}",
                    "latitude": f"{28.6139 + random.uniform(-0.05, 0.05):.6f}",
                    "longitude": f"{77.2090 + random.uniform(-0.05, 0.05):.6f}",
                    "emergency": emergency,
                    "battery": random.randint(5, 100),
                    "methane": random.randint(0, 15),
                    "natural_gas": random.randint(0, 10)
                }
                writer.writerow(row)
        print("Sample data generation complete.")
        
    except IOError as e:
        print(f"Error generating CSV: {e}")