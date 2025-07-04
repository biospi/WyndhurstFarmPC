import time

from onvif2 import ONVIFCamera
from zeep.transports import Transport
from datetime import datetime, timedelta, timezone
from zeep import xsd
from zeep.wsse.username import UsernameToken
import logging
logging.basicConfig(level=logging.DEBUG)
import configparser
config = configparser.ConfigParser()
config.read("config.cfg")

#http://10.70.66.16/onvif/recording_service

def seconds_until_midnight():
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return (tomorrow - now).total_seconds()


def main(ip, password=''):
    try:
        mycam = ONVIFCamera(ip, 80, 'admin', password, wsdl_dir='/home/onvif2/wsdl')
    except Exception as err:
        print(f"failed to set time for {ip}")

    # media2_service = mycam.create_media2_service()
    #
    # ## get the streamUri
    # profiles = media2_service.GetProfiles()
    # for profile in profiles:
    #     o = media2_service.create_type('GetStreamUri')
    #     o.ProfileToken = profile.token
    #     o.Protocol = 'RTSP'
    #     uri = media2_service.GetStreamUri(o)
    #
    #     dic = {'token': profile.token,
    #            'rtsp': uri}
    #     #print(dic)
    #
    # ## get video info , 'h265' or 'h264', 'width' 'height' 'gop' ....
    # configurations = media2_service.GetVideoEncoderConfigurations()
    #
    # for configuration in configurations:
    #     if configuration['Encoding'].lower() == 'h264' or configuration['Encoding'].lower() == 'h265':
    #         width = configuration['Resolution']['Width']
    #         height = configuration['Resolution']['Height']
    #         dic = {'token': configuration['token'],
    #                'encoding': configuration['Encoding'],
    #                'ratio': "{}*{}".format(width, height),
    #                'fps': configuration['RateControl']['FrameRateLimit'],
    #                'bitrate': configuration['RateControl']['BitrateLimit'],
    #                'gop': configuration['GovLength'],
    #                'profile': configuration['Profile'],
    #                'quality': configuration['Quality']}
    #     else:
    #         dic = {'token': configuration['Name'], 'encoding': configuration['Encoding']}
    #
    #     #print(dic)
    #
    # recording_service = mycam.create_recording_service()
    # # for item in recording_service.ws_client:
    # #     print(item)
    #
    # recording_service.ws_client.GetRecordings()
    #
    # recordings = recording_service.GetRecordings()
    # if not recordings:
    #     print("No recordings found.")
    #     return
    #
    # recording_token = recordings[0]['RecordingToken']  # First available recording
    #
    # # Find the H.264 track
    # h264_track_token = None
    # for track in recordings[0]['Tracks']['Track']:
    #     if track['Configuration']['TrackType'] == 'Video' and 'H.264' in track['Configuration']['Description']:
    #         h264_track_token = track['TrackToken']
    #         break

    # if not h264_track_token:
    #     print("No H.264 track found.")
    #     return

    # request = recording_service.create_type('ExportRecordedData')
    # now = datetime.now()
    # today = now.strftime("%Y-%m-%dT%H:%M:%SZ")  # ISO 8601 format for ONVIF
    # yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    #
    # request.StartPoint = yesterday
    # request.EndPoint = today
    # search_scope = recording_service.create_type('SearchScope')
    # search_scope.RecordingToken = recording_token
    # search_scope.TrackToken = h264_track_token
    # request.SearchScope = search_scope
    # request.FileFormat = "mp4"
    # request.StorageDestination = "file:///mnt/storage/video.mp4"

    # recording_service.ws_client.ExportRecordedData(request)

    device_service = mycam.create_devicemgmt_service()
    device_info = device_service.GetDeviceInformation()

    # print("Manufacturer:", device_info.Manufacturer)
    print("Model:", device_info.Model)
    print("Firmware Version:", device_info.FirmwareVersion)
    # print("Serial Number:", device_info.SerialNumber)
    print("Hardware ID:", device_info.HardwareId)
    print("IP:", ip)

    device_service = mycam.create_devicemgmt_service()
    capabilities = device_service.GetCapabilities()

    #print("Device Capabilities Retrieved:")
    #print(capabilities)

    recording_service = mycam.create_recording_service()


    try:
        recordings = recording_service.GetRecordings()
        #print(recordings)
    except Exception as e:
        print("Recording service not available:", e)

    recording_service = mycam.create_recording_service()
    try:
        jobs = recording_service.GetRecordingJobs()
        #print(jobs)
    except Exception as e:
        print("Recording Jobs not available:", e)

    recording_service = mycam.create_recording_service()
    try:
        capabilities = recording_service.GetServiceCapabilities()
        #print(capabilities)
    except Exception as e:
        print("Recording service capabilities not available:", e)

    recording_service = mycam.create_recording_service()
    try:
        recordings = recording_service.GetRecordings()
        # for rec in recordings:
        #     print(rec)
    except Exception as e:
        print("Could not retrieve recordings:", e)

    recording_service = mycam.create_recording_service()
    # try:
    #     options = recording_service.GetRecordingOptions("Recording-1")
    #     #print(options)
    # except Exception as e:
    #     print("Recording options not available:", e)

    recording_service = mycam.create_recording_service()
    # try:
    #     config = recording_service.GetRecordingConfiguration("Recording-1")
    #     #print(config)
    # except Exception as e:
    #     print("Recording configuration not available:", e)


    now = datetime.now(timezone.utc)
    devicemgmt_service = mycam.create_devicemgmt_service()
    current_datetime_info = devicemgmt_service.GetSystemDateAndTime()
    date = current_datetime_info.UTCDateTime
    date['Time']['Hour'] = now.hour
    date['Time']['Minute'] = now.minute
    date['Time']['Second'] = now.second
    date['Date']['Year'] = now.year
    date['Date']['Month'] = now.month
    date['Date']['Day'] = now.day
    request = device_service.create_type('SetSystemDateAndTime')
    request.DateTimeType = 'Manual'
    request.DaylightSavings = False
    # request.TimeZone = tz
    request.UTCDateTime = date
    print(request)
    try:
        device_service.SetSystemDateAndTime(request)
        print(f"Camera time successfully set to host time (UTC). {ip}")
    except Exception as e:
        print("Failed to set camera time:", e)

def update_time():
    main('10.70.66.156', password=config['AUTH']['password_hikvision'])
    main('10.70.66.139', password=config['AUTH']['password_hikvision'])
    main('10.70.66.130', password=config['AUTH']['password_hikvision'])
    main('10.70.66.33', password=config['AUTH']['password_hikvision'])
    main('10.70.66.3', password=config['AUTH']['password_hikvision'])
    main('10.70.66.1', password=config['AUTH']['password_hikvision'])
    main('10.70.66.133', password=config['AUTH']['password_hikvision'])
    main('10.70.66.128', password=config['AUTH']['password_hikvision'])
    main('10.70.66.137', password=config['AUTH']['password_hikvision'])

    main('10.70.66.127', password=config['AUTH']['password_hikvision'])
    main('10.70.66.15', password=config['AUTH']['password_hikvision'])
    main('10.70.66.34', password=config['AUTH']['password_hikvision'])
    main('10.70.66.129', password=config['AUTH']['password_hikvision'])
    main('10.70.66.138', password=config['AUTH']['password_hikvision'])

    main('10.70.66.4', password=config['AUTH']['password_hikvision'])
    main('10.70.66.9', password=config['AUTH']['password_hikvision'])
    main('10.70.66.5', password=config['AUTH']['password_hikvision'])
    main('10.70.66.132', password=config['AUTH']['password_hikvision'])
    main('10.70.66.156', password=config['AUTH']['password_hikvision'])

    main('10.70.66.126', password=config['AUTH']['password_hikvision'])
    main('10.70.66.136', password=config['AUTH']['password_hikvision'])
    main('10.70.66.131', password=config['AUTH']['password_hikvision'])
    main('10.70.66.6', password=config['AUTH']['password_hikvision'])
    main('10.70.66.125', password=config['AUTH']['password_hikvision'])
    main('10.70.66.11', password=config['AUTH']['password_hikvision'])
    main('10.70.66.8', password=config['AUTH']['password_hikvision'])

    main('10.70.66.52', config['AUTH']['password_hanwha'])
    main('10.70.66.53', config['AUTH']['password_hanwha'])
    main('10.70.66.141', config['AUTH']['password_hanwha'])
    main('10.70.66.50', config['AUTH']['password_hanwha'])
    main('10.70.66.49', config['AUTH']['password_hanwha'])
    main('10.70.66.47', config['AUTH']['password_hanwha'])
    main('10.70.66.45', config['AUTH']['password_hanwha'])
    main('10.70.66.46', config['AUTH']['password_hanwha'])
    main('10.70.66.54', config['AUTH']['password_hanwha'])
    main('10.70.66.48', config['AUTH']['password_hanwha'])

    main('10.70.66.26', config['AUTH']['password_hanwha'])
    main('10.70.66.27', config['AUTH']['password_hanwha'])
    main('10.70.66.25', config['AUTH']['password_hanwha'])
    main('10.70.66.23', config['AUTH']['password_hanwha'])
    main('10.70.66.21', config['AUTH']['password_hanwha'])
    main('10.70.66.19', config['AUTH']['password_hanwha'])
    main('10.70.66.16', config['AUTH']['password_hanwha'])
    main('10.70.66.17', config['AUTH']['password_hanwha'])
    main('10.70.66.18', config['AUTH']['password_hanwha'])
    main('10.70.66.20', config['AUTH']['password_hanwha'])
    main('10.70.66.22', config['AUTH']['password_hanwha'])
    main('10.70.66.24', config['AUTH']['password_hanwha'])

    #footbath
    main('10.70.66.28', config['AUTH']['password_hanwha'])
    main('10.70.66.29', config['AUTH']['password_hanwha'])
    main('10.70.66.30', config['AUTH']['password_hanwha'])
    main('10.70.66.31', config['AUTH']['password_hanwha'])

    ########################
    main('10.70.66.39', config['AUTH']['password_hanwha'])
    main('10.70.66.43', config['AUTH']['password_hanwha'])
    main('10.70.66.41', config['AUTH']['password_hanwha'])
    main('10.70.66.38', config['AUTH']['password_hanwha'])
    main('10.70.66.44', config['AUTH']['password_hanwha'])
    main('10.70.66.37', config['AUTH']['password_hanwha'])
    main('10.70.66.40', config['AUTH']['password_hanwha'])
    main('10.70.66.35', config['AUTH']['password_hanwha'])
    main('10.70.66.42', config['AUTH']['password_hanwha'])
    main('10.70.66.36', config['AUTH']['password_hanwha'])



if __name__ == "__main__":
    #ntp.bris.ac.uk
    while True:
        update_time()
        wait_time = seconds_until_midnight()
        print(f"Next update in {wait_time} seconds.")
        time.sleep(wait_time)