import requests
import random
import time
import uuid

API_URL = "http://localhost:8000/iot/ingest"

DEVICES = [
    {"id": "SCALE-001", "type": "weight", "unit": "kg"},
    {"id": "PH-METER-01", "type": "ph", "unit": "pH"},
    {"id": "SPECTRO-X", "type": "spectro", "unit": "nm"}
]

def generate_data():
    device = random.choice(DEVICES)
    value = 0.0
    if device["type"] == "weight":
        value = round(random.uniform(10.0, 50.0), 2)
    elif device["type"] == "ph":
        value = round(random.uniform(6.0, 8.0), 1)
    elif device["type"] == "spectro":
        value = round(random.uniform(400, 700), 0)
        
    payload = {
        "device_id": device["id"],
        "parameter": device["type"],
        "value": value,
        "unit": device["unit"],
        "timestamp": str(time.time())
    }
    return payload

def run_simulator():
    print("Starting IoT Simulator...")
    while True:
        data = generate_data()
        try:
            response = requests.post(API_URL, json=data)
            print(f"Sent: {data} | Status: {response.status_code}")
        except Exception as e:
            print(f"Error sending: {e}")
        
        time.sleep(2) # Send every 2 seconds

if __name__ == "__main__":
    run_simulator()
