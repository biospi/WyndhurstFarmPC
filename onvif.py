from onvif2 import ONVIFCamera
from zeep.transports import Transport
from datetime import datetime, timedelta

#http://10.70.66.16/onvif/recording_service

def main():
    mycam = ONVIFCamera('10.70.66.16', 80, 'admin', 'Ocs881212', wsdl_dir='/home/onvif2/wsdl')
    media2_service = mycam.create_media2_service()

    ## get the streamUri
    profiles = media2_service.GetProfiles()
    for profile in profiles:
        o = media2_service.create_type('GetStreamUri')
        o.ProfileToken = profile.token
        o.Protocol = 'RTSP'
        uri = media2_service.GetStreamUri(o)

        dic = {'token': profile.token,
               'rtsp': uri}
        print(dic)

    ## get video info , 'h265' or 'h264', 'width' 'height' 'gop' ....
    configurations = media2_service.GetVideoEncoderConfigurations()

    for configuration in configurations:
        if configuration['Encoding'].lower() == 'h264' or configuration['Encoding'].lower() == 'h265':
            width = configuration['Resolution']['Width']
            height = configuration['Resolution']['Height']
            dic = {'token': configuration['token'],
                   'encoding': configuration['Encoding'],
                   'ratio': "{}*{}".format(width, height),
                   'fps': configuration['RateControl']['FrameRateLimit'],
                   'bitrate': configuration['RateControl']['BitrateLimit'],
                   'gop': configuration['GovLength'],
                   'profile': configuration['Profile'],
                   'quality': configuration['Quality']}
        else:
            dic = {'token': configuration['Name'], 'encoding': configuration['Encoding']}

        print(dic)

    recording_service = mycam.create_recording_service()
    for item in recording_service.ws_client:
        print(item)

    recording_service.ws_client.GetRecordings()

    recordings = recording_service.GetRecordings()
    if not recordings:
        print("No recordings found.")
        return

    recording_token = recordings[0]['RecordingToken']  # First available recording

    # Find the H.264 track
    h264_track_token = None
    for track in recordings[0]['Tracks']['Track']:
        if track['Configuration']['TrackType'] == 'Video' and 'H.264' in track['Configuration']['Description']:
            h264_track_token = track['TrackToken']
            break

    if not h264_track_token:
        print("No H.264 track found.")
        return

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

    print("Manufacturer:", device_info.Manufacturer)
    print("Model:", device_info.Model)
    print("Firmware Version:", device_info.FirmwareVersion)
    print("Serial Number:", device_info.SerialNumber)
    print("Hardware ID:", device_info.HardwareId)

    device_service = mycam.create_devicemgmt_service()
    capabilities = device_service.GetCapabilities()

    print("Device Capabilities Retrieved:")
    print(capabilities)

    recording_service = mycam.create_recording_service()


    try:
        recordings = recording_service.GetRecordings()
        print(recordings)
    except Exception as e:
        print("Recording service not available:", e)

    recording_service = mycam.create_recording_service()
    try:
        jobs = recording_service.GetRecordingJobs()
        print(jobs)
    except Exception as e:
        print("Recording Jobs not available:", e)

    recording_service = mycam.create_recording_service()
    try:
        capabilities = recording_service.GetServiceCapabilities()
        print(capabilities)
    except Exception as e:
        print("Recording service capabilities not available:", e)

    recording_service = mycam.create_recording_service()
    try:
        recordings = recording_service.GetRecordings()
        for rec in recordings:
            print(rec)
    except Exception as e:
        print("Could not retrieve recordings:", e)

    recording_service = mycam.create_recording_service()
    try:
        options = recording_service.GetRecordingOptions("Recording-1")
        print(options)
    except Exception as e:
        print("Recording options not available:", e)

    recording_service = mycam.create_recording_service()
    try:
        config = recording_service.GetRecordingConfiguration("Recording-1")
        print(config)
    except Exception as e:
        print("Recording configuration not available:", e)


if __name__ == "__main__":
    main()