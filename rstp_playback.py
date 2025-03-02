import json

import requests
import xmltodict
import time
from requests.auth import HTTPDigestAuth
from datetime import datetime

# Camera details
CAMERA_IP = "10.70.66.16"
USERNAME = "admin"  # Change if needed
PASSWORD = "Ocs881212"  # Change if needed

# ONVIF URLs
SEARCH_SERVICE_URL = f"http://{CAMERA_IP}/onvif/search_service"
RECORDING_SERVICE_URL = f"http://{CAMERA_IP}/onvif/recording_service"
EXPORT_SERVICE_URL = f"http://{CAMERA_IP}/onvif/recording_service"
REPLAY_SERVICE_URL = f"http://{CAMERA_IP}/onvif/replay_service"
EVENT_SERVICE_URL = f'http://{CAMERA_IP}/onvif/event_service'


# ONVIF Headers
HEADERS = {"Content-Type": "text/xml; charset=utf-8"}

AUTH = HTTPDigestAuth(USERNAME, PASSWORD)

def send_soap_request(url, body):
    """ Sends a SOAP request and returns the parsed XML response. """
    response = requests.post(url, data=body, headers=HEADERS, auth=AUTH)
    return xmltodict.parse(response.text)


def find_recordings():
    """ Step 1: Start a search for recordings. """
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

    response = send_soap_request(SEARCH_SERVICE_URL, body)
    print(json.dumps(response, indent=4))
    if response:
        try:
            search_token = response["SOAP-ENV:Envelope"]["SOAP-ENV:Body"]["tse:FindRecordingsResponse"]["tse:SearchToken"]
            print(f"Search Token: {search_token}")
            return search_token
        except KeyError:
            print("Failed to retrieve SearchToken.")
    return None


def find_recordings():
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

    response = send_soap_request(SEARCH_SERVICE_URL, body)
    print(json.dumps(response, indent=4))
    if response:
        try:
            search_token = response["SOAP-ENV:Envelope"]["SOAP-ENV:Body"]["tse:FindRecordingsResponse"]["tse:SearchToken"]
            print(f"Search Token: {search_token}")
            return search_token
        except KeyError:
            print("Failed to retrieve SearchToken.")
    return None

def get_recording_results(search_token):
    time.sleep(3)  # Wait to ensure search is complete
    body = f"""<?xml version="1.0" encoding="utf-8"?>
    <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">
        <s:Body>
            <GetRecordingSearchResults xmlns="http://www.onvif.org/ver10/search/wsdl">
                <SearchToken>{search_token}</SearchToken>
                <WaitTime>PT50S</WaitTime>
            </GetRecordingSearchResults>
        </s:Body>
    </s:Envelope>"""

    response = send_soap_request(SEARCH_SERVICE_URL, body)
    if response:
        print(json.dumps(response, indent=4))
        try:
            recording_info = response["SOAP-ENV:Envelope"]["SOAP-ENV:Body"]["tse:GetRecordingSearchResultsResponse"]["tse:ResultList"]["tt:RecordingInformation"]
            recording_token = recording_info["tt:RecordingToken"]
            print(f"Recording Found: {recording_token}")
            return recording_token
        except KeyError:
            print("No recordings found.")
    return None

def get_recording_by_token(recording_token):
    # Request to retrieve actual recording details using the recording token
    body = f"""<?xml version="1.0" encoding="utf-8"?>
    <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">
        <s:Body>
            <GetRecordings xmlns="http://www.onvif.org/ver10/recording/wsdl">
                <RecordingToken>{recording_token}</RecordingToken>
            </GetRecordings>
        </s:Body>
    </s:Envelope>"""
    print(body)
    response = send_soap_request(RECORDING_SERVICE_URL, body)
    if response:
        print(json.dumps(response, indent=4))
        try:
            # Extract actual recording data or URI from the response
            recordings = response["SOAP-ENV:Envelope"]["SOAP-ENV:Body"]["trt:GetRecordingsResponse"]["trt:Recording"]
            for recording in recordings:
                print(f"Recording URI: {recording['trt:URI']}")
            return recordings
        except KeyError:
            print("No recordings found.")
    return None


def export_recorded_data(recording_token, track_token, time_from, time_to):
    time.sleep(3)  # Wait to ensure export request is processed
    body = f"""<?xml version="1.0" encoding="utf-8"?>
    <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">
        <s:Body>
            <ExportRecordedData xmlns="http://www.onvif.org/ver10/search/wsdl">
                <RecordingToken>{recording_token}</RecordingToken>
                <TrackToken>{track_token}</TrackToken>
                <TimeFrom>{time_from}</TimeFrom>
                <TimeTo>{time_to}</TimeTo>
            </ExportRecordedData>
        </s:Body>
    </s:Envelope>"""

    response = send_soap_request(EXPORT_SERVICE_URL, body)
    if response:
        print(json.dumps(response, indent=4))
        try:
            return response["SOAP-ENV:Body"]["ExportRecordedDataResponse"]["Uri"]
        except KeyError:
            print("Error: Export URI not found in response.")
            return None
    else:
        print("Error: No response from the camera.")
        return None


def get_recording_by_token(recording_token):
    # Construct the SOAP body for the GetRecordings request with possible other prefixes
    body = f"""<?xml version="1.0" encoding="utf-8"?>
    <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:tt="http://www.onvif.org/ver10/recording/wsdl">
        <s:Body>
            <tt:GetRecordings>
                <tt:RecordingToken>{recording_token}</tt:RecordingToken>
            </tt:GetRecordings>
        </s:Body>
    </s:Envelope>"""

    # Send the SOAP request to the recording service
    response = send_soap_request(RECORDING_SERVICE_URL, body)
    if response:
        print(json.dumps(response, indent=4))
        try:
            # Parse and process the response
            recordings = response["SOAP-ENV:Envelope"]["SOAP-ENV:Body"]["tt:GetRecordingsResponse"]["tt:Recording"]
            for recording in recordings:
                print(f"Recording URI: {recording['tt:URI']}")
            return recordings
        except KeyError:
            print("No recordings found.")
    return None


def find_events_by_time_range(search_token, start_time, end_time):
    body = f"""<?xml version="1.0" encoding="utf-8"?>
    <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">
        <s:Body xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            <FindEvents xmlns="http://www.onvif.org/ver10/search/wsdl">
                <StartPoint>{start_time}</StartPoint>
                <EndPoint>{end_time}</EndPoint>
                <Scope>
                    <IncludedRecordings xmlns="http://www.onvif.org/ver10/schema">{search_token}</IncludedRecordings>
                </Scope>
                <SearchFilter>
                    <wsnt:TopicExpression Dialect="http://www.onvif.org/ver10/tev/topicExpression/ConcreteSet"
                        xmlns:wsnt="http://docs.oasis-open.org/wsn/b-2"
                        xmlns:tns1="http://www.onvif.org/ver10/topics">
                        tns1:RecordingHistory/Track/State
                    </wsnt:TopicExpression>
                </SearchFilter>
                <IncludeStartState>true</IncludeStartState>
                <KeepAliveTime>PT60S</KeepAliveTime>
            </FindEvents>
        </s:Body>
    </s:Envelope>"""

    print(body)
    try:
        response = send_soap_request(EVENT_SERVICE_URL, body)
        print(json.dumps(response, indent=4))
    except requests.exceptions.RequestException as e:
        print(f"Error during SOAP request: {e}")

    return None


def get_replay_uri(recording_token):
    """Sends a SOAP request to retrieve the replay URI for a given recording token."""
    body = f"""<?xml version="1.0" encoding="utf-8"?>
    <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">
        <s:Body>
            <trp:GetReplayUri xmlns:trp="http://www.onvif.org/ver10/replay/wsdl">
                <trp:StreamSetup>
                    <tt:Stream xmlns:tt="http://www.onvif.org/ver10/schema">RTP-Unicast</tt:Stream>
                    <tt:Transport xmlns:tt="http://www.onvif.org/ver10/schema">
                        <tt:Protocol>RTSP</tt:Protocol>
                    </tt:Transport>
                </trp:StreamSetup>
                <trp:RecordingToken>{recording_token}</trp:RecordingToken>
            </trp:GetReplayUri>
        </s:Body>
    </s:Envelope>"""
    response = send_soap_request(REPLAY_SERVICE_URL, body)
    print(json.dumps(response, indent=4))


# def get_replay_uri(recording_token, start_time, end_time):
#     """Sends a SOAP request to retrieve the replay URI for a given recording token."""
#
#     # Ensure the times are in the correct format with "Z" indicating UTC
#     start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')  # Use 'Z' for UTC
#     end_time_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')  # Use 'Z' for UTC
#
#     # Build the SOAP body for GetReplayUri with the necessary parameters
#     body = f"""<?xml version="1.0" encoding="utf-8"?>
#     <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
#                        xmlns:trp="http://www.onvif.org/ver10/replay/wsdl"
#                        xmlns:tt="http://www.onvif.org/ver10/schema">
#         <SOAP-ENV:Body>
#             <trp:GetReplayUri>
#                 <trp:StreamSetup>
#                     <tt:Stream>RTP-Unicast</tt:Stream>
#                     <tt:Transport>
#                         <tt:Protocol>RTSP</tt:Protocol>
#                     </tt:Transport>
#                 </trp:StreamSetup>
#                 <trp:RecordingToken>{recording_token}</trp:RecordingToken>
#             </trp:GetReplayUri>
#         </SOAP-ENV:Body>
#     </SOAP-ENV:Envelope>"""
#
#     # Send the request and get the response
#     try:
#         response = send_soap_request(REPLAY_SERVICE_URL, body)
#         print(json.dumps(response, indent=4))
#         return response
#     except requests.exceptions.RequestException as e:
#         print(f"Error during SOAP request: {e}")
#         return None


def download_file(uri, filename="recording.mp4"):
    """ Step 4: Download the file from the given URI. """
    print(f"Downloading {filename} from {uri}...")
    response = requests.get(uri, stream=True, auth=(USERNAME, PASSWORD))
    if response.status_code == 200:
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        print("Download complete.")
    else:
        print(f"Failed to download: {response.status_code}")


def get_track_details(track_token):
    # Construct the SOAP body for the GetTrack request using the TrackToken
    body = f"""<?xml version="1.0" encoding="utf-8"?>
    <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">
        <s:Body>
            <GetTrack xmlns="http://www.onvif.org/ver10/recording/wsdl">
                <TrackToken>{track_token}</TrackToken>
            </GetTrack>
        </s:Body>
    </s:Envelope>"""

    # Send the SOAP request to get track details
    response = send_soap_request(RECORDING_SERVICE_URL, body)
    if response:
        print(json.dumps(response, indent=4))
        try:
            track_info = response["SOAP-ENV:Envelope"]["SOAP-ENV:Body"]["trt:GetTrackResponse"]["trt:Track"]
            print(f"Track Info: {track_info}")
            return track_info
        except KeyError:
            print("No track found.")
    return None


def search_recordings(recording_token, start_time, end_time):
    """Searches for recordings within a specified time range."""

    # Ensure the times are in the correct format with "Z" indicating UTC
    start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')  # Use 'Z' for UTC
    end_time_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')  # Use 'Z' for UTC

    # Build the SOAP body for searching recordings
    body = f"""<?xml version="1.0" encoding="utf-8"?>
    <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
                       xmlns:trp="http://www.onvif.org/ver10/recording/wsdl"
                       xmlns:tt="http://www.onvif.org/ver10/schema">
        <SOAP-ENV:Body>
            <trp:GetRecordings>
            </trp:GetRecordings>
        </SOAP-ENV:Body>
    </SOAP-ENV:Envelope>"""

    # Send the request and get the response
    try:
        response = send_soap_request(REPLAY_SERVICE_URL, body)
        print(json.dumps(response, indent=4))
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error during SOAP request: {e}")
        return None

if __name__ == "__main__":
    search_token = find_recordings()
    if search_token:
        recording_token = get_recording_results(search_token)
    else:
        print("Failed to start recording search.")


    #get_recording_by_token(recording_token)
    # recording_token = "Recording-1"
    # track_token = "VIDEO002"
    time_from = "2025-02-28T16:05:44Z"
    time_to = "2025-02-28T17:58:00Z"
    #
    # download_link = export_recorded_data(recording_token, track_token, time_from, time_to)
    # if download_link:
    #     print(f"Download video from: {download_link}")

    #
    # replay_response = get_replay_uri(recording_token, start_time, end_time)

    # search_recordings(recording_token, start_time, end_time)

    #get_replay_uri(recording_token)
    find_events_by_time_range(recording_token, time_from, time_to)
