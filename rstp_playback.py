import json
import sys

import requests
import xmltodict
from requests.auth import HTTPDigestAuth
from datetime import datetime, timedelta
import subprocess
from pathlib import Path

from utils import run_cmd

USERNAME = "admin"
PASSWORD = "Ocs881212"

# ONVIF Headers
HEADERS = {"Content-Type": "text/xml; charset=utf-8"}

AUTH = HTTPDigestAuth(USERNAME, PASSWORD)

def send_soap_request(url, body):
    """ Sends a SOAP request and returns the parsed XML response. """
    response = requests.post(url, data=body, headers=HEADERS, auth=AUTH)
    return xmltodict.parse(response.text)

def find_recordings(ip):
    body = f"""<?xml version="1.0" encoding="utf-8"?>
    <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">
        <s:Body>
            <FindRecordings xmlns="http://www.onvif.org/ver10/search/wsdl">
                <Scope>
                    <RecordingInformationFilter xmlns="http://www.onvif.org/ver10/schema">boolean(//Track[TrackType = "Video"])</RecordingInformationFilter>
                </Scope>
                <KeepAliveTime>PT10S</KeepAliveTime>
            </FindRecordings>
        </s:Body>
    </s:Envelope>"""
    print("***************************REQUEST*********************************")
    SEARCH_SERVICE_URL = f"http://{ip}/onvif/search_service"
    print(SEARCH_SERVICE_URL)
    print(body)
    print("***************************RESPONSE*********************************")
    response = send_soap_request(SEARCH_SERVICE_URL, body)
    print(json.dumps(response["SOAP-ENV:Envelope"]["SOAP-ENV:Body"], indent=4))
    if response:
        try:
            search_token = response["SOAP-ENV:Envelope"]["SOAP-ENV:Body"]["tse:FindRecordingsResponse"]["tse:SearchToken"]
            print(f"Search Token: {search_token}")
            return search_token
        except KeyError:
            print("Failed to retrieve SearchToken.")
    return None


def get_recording_results(ip, search_token):
    #time.sleep(3)
    body = f"""<?xml version="1.0" encoding="utf-8"?>
    <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">
        <s:Body>
            <GetRecordingSearchResults xmlns="http://www.onvif.org/ver10/search/wsdl">
                <SearchToken>{search_token}</SearchToken>
                <WaitTime>PT50S</WaitTime>
            </GetRecordingSearchResults>
        </s:Body>
    </s:Envelope>"""
    print("***********************REQUEST*************************************")
    SEARCH_SERVICE_URL = f"http://{ip}/onvif/search_service"
    print(body)
    print("***********************RESPONSE*************************************")
    response = send_soap_request(SEARCH_SERVICE_URL, body)
    if response:
        print(json.dumps(response["SOAP-ENV:Envelope"]["SOAP-ENV:Body"], indent=4))
        try:
            recording_info = response["SOAP-ENV:Envelope"]["SOAP-ENV:Body"]["tse:GetRecordingSearchResultsResponse"]["tse:ResultList"]["tt:RecordingInformation"]
            earliest_recording = format_datetime(recording_info["tt:EarliestRecording"])
            latest_recording = format_datetime(recording_info["tt:LatestRecording"])
            print(f"earliest_recording: {earliest_recording} latest_recording: {latest_recording}")
            return earliest_recording, latest_recording
        except KeyError:
            return None, None
    return None, None

def format_datetime(old_datetime: str):
    """Convert datetime string from 'YYYY-MM-DDTHH:MM:SSZ' to 'YYYYMMDDHHMMSS'."""
    dt = datetime.strptime(old_datetime, "%Y-%m-%dT%H:%M:%SZ")
    return dt.strftime("%Y%m%d%H%M%S")


def generate_perfect_5min_ranges(start: str, end: str) -> list:
    """Generate 5-minute aligned recording ranges from start to end timestamps."""

    # Convert input strings to datetime objects
    start_dt = datetime.strptime(start, "%Y%m%d%H%M%S")
    end_dt = datetime.strptime(end, "%Y%m%d%H%M%S")

    # Align start time to the nearest 5-minute mark
    aligned_start_dt = start_dt.replace(second=0, microsecond=0)
    if aligned_start_dt.minute % 5 != 0:
        aligned_start_dt += timedelta(minutes=(5 - aligned_start_dt.minute % 5))  # Move up to next 5-minute mark

    step = timedelta(minutes=5)
    ranges = []
    current_dt = aligned_start_dt

    while current_dt < end_dt:
        next_dt = current_dt + step
        if next_dt > end_dt:
            break  # Stop if the next step exceeds the end time
        ranges.append([current_dt.strftime('%Y%m%d%H%M%S'), next_dt.strftime('%Y%m%d%H%M%S')])
        current_dt = next_dt  # Move to the next 5-minute interval

    return ranges

def generate_recording_ranges(start: str, end: str) -> list:
    """Generate 20-minute recording ranges between start and end timestamps."""
    start_dt = datetime.strptime(start, "%Y%m%d%H%M%S")
    end_dt = datetime.strptime(end, "%Y%m%d%H%M%S")
    step = timedelta(minutes=10)

    ranges = []
    current_dt = start_dt

    while current_dt < end_dt:
        next_dt = min(current_dt + step, end_dt)
        ranges.append([current_dt.strftime('%Y%m%d%H%M%S'), next_dt.strftime('%Y%m%d%H%M%S')])
        current_dt = next_dt

    return ranges

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


def find_all_mp4_files(root_directory= "/media/fo18103/Storage/CCTV/hanwha/media/"):
    """
    Finds all .mp4 files in the given root directory and its subdirectories.

    :param root_directory: The root directory to start searching in.
    :return: A list of Path objects pointing to each .mp4 file found.
    """
    root_path = Path(root_directory)
    mp4_files = list(root_path.rglob("*.mp4"))
    return mp4_files


def main(ip):
    search_token = find_recordings(ip)
    earliest_recording, latest_recording = get_recording_results(ip, search_token)
    clips = generate_perfect_5min_ranges(earliest_recording, latest_recording)[400:]
    print(f"Found {len(clips)} recordings. First clip: [{clips[0]}] Last clip: [{clips[-1]}]")

    for i in range(len(clips)):
        videos = find_all_mp4_files(f"/media/fo18103/Storage/CCTV/hanwha/media/66.{ip[-2:]}")
        clock = f"{clips[i][0]}-{clips[i][1]}"
        rtsp_url = f"rtsp://{USERNAME}:{PASSWORD}@{ip}/recording/{clock}/OverlappedID=0/backup.smp"
        print(rtsp_url)

        filename = f"{clock}.mp4".replace("-", '_')
        out_dir = create_output_directory(filename, ip)
        output_file = out_dir / filename
        print(f"Output file: {output_file}")

        if output_file.exists():
            print(f"File {output_file} already exists. Skipping download.")
            continue  # Skip the download if the file already exists

        output_file.unlink(missing_ok=True)

        ffmpeg_command = [
            "ffmpeg",
            "-rtsp_transport", "tcp",
            "-rtbufsize", "100M",
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
        p_status = run_cmd(ffmpeg_command, verbose=True)
        print(f"p_status={p_status}")


if __name__ == "__main__":
    # cctvs = [line.strip() for line in open("hanwha_tpen.txt").readlines()]
    # for ip in cctvs:
    if len(sys.argv) > 1:
        ip = sys.argv[1]
        print("argument:", ip)
        main(ip)
    else:
        print("No argument provided")


