import requests
import datetime

cmd = f"java -jar importer.jar 10.70.66.136:80 admin ocs881212 --from-time '{start_time}' --to-time '{end_time}' | cut -d'|' -f5 > {out_cmd}"

'''
curl --insecure -X 'GET' "https://127.0.0.1:7001/media/00939c0d-a6a8-9b22-1b0a-f48a6a1f7e6e.mkv?pos=%222024-11-27T06:00:00%22&duration=100" -H 'accept: */*' -H 'x-runtime-guid: vms-6f7eeebe0025132dcf008fc07ef2c053-yjXKayqXsq' -o test.mkv
'''

'''
curl --insecure -X 'GET' 'https://127.0.0.1:7001/media/40900271-06c0-2a3a-5e0f-4bb45691cbba.mp4?pos=%222024-12-03T00:00:00%22&duration=100' -H 'accept: */*' -H 'x-runtime-guid: vms-6f7eeebe0025132dcf008fc07ef2c053-B5vOyYipyk'
'''

'''

https://localhost:7001/media/00939c0d-a6a8-9b22-1b0a-f48a6a1f7e6e.mp4?pos=%222024-12-07T18:00:00%22&duration=100

'''


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