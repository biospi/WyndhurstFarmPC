import time
import json
from onvif2 import ONVIFCamera
from zeep.transports import Transport
from pathlib import Path
from datetime import datetime, timedelta
import configparser
config = configparser.ConfigParser()
config.read("config.cfg")

LOG_DIR = Path("/mnt/camera_logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

CAMERA_IPS = [
    '10.70.66.52', '10.70.66.53', '10.70.66.141', '10.70.66.50',
    '10.70.66.49', '10.70.66.47', '10.70.66.45', '10.70.66.46', '10.70.66.54',
    '10.70.66.48', '10.70.66.26', '10.70.66.27', '10.70.66.25', '10.70.66.23',
    '10.70.66.21', '10.70.66.19', '10.70.66.16', '10.70.66.17', '10.70.66.18',
    '10.70.66.20', '10.70.66.22', '10.70.66.24', '10.70.66.28', '10.70.66.29',
    '10.70.66.30', '10.70.66.31', '10.70.66.43', '10.70.66.41', '10.70.66.38',
    '10.70.66.44', '10.70.66.37', '10.70.66.40', '10.70.66.35', '10.70.66.42',
    '10.70.66.36'
]

def check_sd_recording_health(mycam):
    try:
        recording_service = mycam.create_recording_service()
        jobs = recording_service.GetRecordingJobs()
        for job in jobs:
            token = job['JobToken']
            mode = job['JobConfiguration']['Mode']
            print(f"Job {token} mode: {mode}")
            if mode != 'Active':
                return False
        return True
    except Exception as e:
        print(f"Failed to check SD recording health: {e}")
        return False

def get_recording_status(ip):
    try:
        mycam = ONVIFCamera(ip, 80, 'admin', config['AUTH']['password_hanwha'], wsdl_dir='/home/onvif2/wsdl')
        return check_sd_recording_health(mycam)
    except Exception as err:
        print(f"Failed to connect or check recording for {ip}: {err}")
        return False

def check_all_recording_status():
    status_dict = {}
    for ip in CAMERA_IPS:
        status_dict[ip] = get_recording_status(ip)

    timestamp = datetime.now().replace(microsecond=0).isoformat().replace(":", "-")
    filename = LOG_DIR / f"recording_status_{timestamp}.json"

    report = {
        "timestamp": timestamp,
        "camera_status": status_dict
    }

    # Save JSON report
    try:
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Saved status report to {filename}")
    except Exception as e:
        print(f"Failed to write JSON report: {e}")

    # Print if any camera isn't recording
    if not all(status_dict.values()):
        print("\n--- One or more cameras are NOT recording ---")
        for ip, status in status_dict.items():
            print(f"{ip}: {'Recording' if status else 'NOT Recording'}")


def main():
    while True:
        print("Checking recording status for all cameras...")
        check_all_recording_status()
        delay = 60*5
        print(f"Sleeping for {delay} seconds...\n")
        time.sleep(delay)

if __name__ == "__main__":
    main()
