import requests
import datetime

def main():
    server_ip = "10.70.66.2"
    port = 7001
    camera_id = "00939c0d-a6a8-9b22-1b0a-f48a6a1f7e6e" #.28
    #date = "2024-07-13T00:00:00"
    date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%s")
    dur_sec = 100
    url = f'http://{server_ip}:{port}/media/{camera_id}.mkv?pos="{date}"&duration={dur_sec}'
    print(url)

    url = f'http://{server_ip}:{port}/ec2/recordedTimePeriods?cameraId={camera_id}'
    print(url)
    response = requests.get(url)
    print(response.json())

if __name__ == "__main__":
    main()