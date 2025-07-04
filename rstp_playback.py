import json
import sys
import time
import requests
import xmltodict
from requests.auth import HTTPDigestAuth
from datetime import datetime, timedelta
import subprocess
from pathlib import Path
from utils import run_cmd
import configparser
config = configparser.ConfigParser()
config.read("config.cfg")

MAX_ONVIF_RETRY = 5
MAX_DOWNLOAD_RETRIES = 3
EXPECTED_DURATION = 5 * 60
USERNAME = "admin"
PASSWORD = config['AUTH']['password_hanwha']

HEADERS = {"Content-Type": "text/xml; charset=utf-8"}
AUTH = HTTPDigestAuth(USERNAME, PASSWORD)

def create_output_directory(output_file: str, ip_tag: str):
    """
    Creates an output directory based on the first timestamp of the output file.

    :param output_file: The path to the output file.
    :return: The path to the created directory.
    """
    timestamp_str = output_file.split('_')[0]
    timestamp = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
    date_subfolder = timestamp.strftime('%Y%b%d')
    output_dir = Path(f'/media/fo18103/Storage/CCTV/hanwha/media/66{ip_tag[-3:]}/{date_subfolder}/videos/')
    output_dir.mkdir(parents=True, exist_ok=True)
    print(output_dir)
    return output_dir

def generate_perfect_5min_ranges(start: str, end: str) -> list:
    """Generate 5-minute aligned recording ranges from start to end timestamps."""

    # Convert input strings to datetime objects
    start_dt = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
    end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ")

    # Align start time to the nearest 5-minute mark
    aligned_start_dt = start_dt.replace(second=0, microsecond=0)
    if aligned_start_dt.minute % 5 != 0:
        aligned_start_dt += timedelta(minutes=(5 - aligned_start_dt.minute % 5))  # Move up to next 5-minute mark

    step = timedelta(minutes=5, seconds=1)
    ranges = []
    current_dt = aligned_start_dt

    while current_dt < end_dt:
        next_dt = current_dt + step
        if next_dt > end_dt:
            break  # Stop if the next step exceeds the end time
        ranges.append([current_dt.strftime('%Y%m%d%H%M%S'), next_dt.strftime('%Y%m%d%H%M%S')])
        current_dt = next_dt  # Move to the next 5-minute interval

    return ranges

def get_video_duration(file_path):
    """Get the duration of a video file in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-i", file_path, "-show_entries",
                "format=duration", "-v", "quiet", "-of", "csv=p=0"
            ],
            capture_output=True, text=True
        )
        duration = float(result.stdout.strip())
        return int(duration)
    except Exception as e:
        print(f"Failed to get duration: {e}")
        return None

def download_video(rtsp_url, output_file):
    """Download video via ffmpeg."""
    #-analyzeduration 10000000 -probesize 10000000 \
    ffmpeg_command = [
        "ffmpeg",
        "-rtsp_transport", "tcp",
        "-rtbufsize", "100M",

        # "-analyzeduration", "10000000",
        # "-probesize", "10000000",

        "-i", rtsp_url,
        "-an",
        "-c:v", "libx264",
        "-crf", "28",
        "-preset", "veryslow",
        "-f", "mp4",
        output_file.as_posix()
    ]
    ffmpeg_command = " ".join(ffmpeg_command).strip()
    print(f"FFMPEG CMD:{ffmpeg_command}")
    return run_cmd(ffmpeg_command, verbose=True)

def main(ip):
    now = datetime.now()
    earliest_recording = (now - timedelta(days=3)).strftime('%Y-%m-%dT%H:%M:%SZ')
    latest_recording = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    clips = generate_perfect_5min_ranges(earliest_recording, latest_recording)
    print(f"Found {len(clips)} recordings. First clip: [{clips[0]}] Last clip: [{clips[-1]}]")

    for i in range(len(clips)):
        clock = f"{clips[i][0]}-{clips[i][1]}"
        rtsp_url = f"rtsp://{USERNAME}:{PASSWORD}@{ip}/recording/{clock}/OverlappedID=0/backup.smp"
        #recording/20250305000000-20250305000500/OverlappedID=0/backup.smp
        filename = f"{clock}.mp4".replace("-", '_')
        out_dir = create_output_directory(filename, ip)
        output_file = out_dir / filename

        if output_file.exists():
            print(f"File {output_file} already exists. Skipping download.")
            continue

        output_file.unlink(missing_ok=True)

        for attempt in range(1, MAX_DOWNLOAD_RETRIES + 1):
            print(f"Attempt {attempt} to download {filename}")
            p_status = download_video(rtsp_url, output_file)
            print(f"Download status: {p_status}")

            if output_file.exists():
                duration = get_video_duration(output_file)
                print(f"File duration: {duration}")
                if duration >= EXPECTED_DURATION:
                    print(f"File {filename} downloaded successfully with correct duration.")
                    break
                else:
                    print(f"Duration mismatch: Expected {EXPECTED_DURATION}, got {duration}")
                    output_file.unlink()  # Remove bad file
            else:
                print("File download failed.")

            if attempt == MAX_DOWNLOAD_RETRIES:
                print(f"Failed to download {filename} with correct duration after {MAX_DOWNLOAD_RETRIES} attempts. Skipping.")

if __name__ == "__main__":
    main("10.70.66.40")
    # if len(sys.argv) > 1:
    #     ip = sys.argv[1]
    #     print("argument:", ip)
    #     main(ip)
    # else:
    #     print("No argument provided")
