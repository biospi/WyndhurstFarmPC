import base64
import hashlib
import subprocess
import socket
import configparser
config = configparser.ConfigParser()
config.read("config.cfg")

m_Vars = {
    "bufLen" : 1024,
    "defaultServerPort" : 554,
    "defaultUserAgent" : "RTSP Client",
    "defaultTestUri" : "/recording/play.smp",
    "defaultUsername" : "admin",
    "defaultPassword" : config['AUTH']['password_hanwha']
}

def genmsg_OPTIONS(url,seq,userAgent,sessionId,authSeq):
    msgRet = "OPTIONS " + url + " RTSP/1.0\r\n"
    msgRet += "CSeq: " + str(seq) + "\r\n"
    msgRet += "User-Agent: " + userAgent + "\r\n"
    msgRet += "Session: " + sessionId + "\r\n"
    msgRet += "\r\n"
    return msgRet

def decodeSession(strContent):
    mapRetInf = {}
    messageStrings = strContent.split("\n")
    for element in messageStrings:
        if "Session" in element:
            a = element.find(":")
            b = element.find(";")
            mapRetInf = element[a+2:b]
    return mapRetInf

def decodeControl(strContent):
    mapRetInf = {}
    messageStrings = strContent.split("\n")
    for element in messageStrings:
        a = element.find("rtsp")
        if a >= 0:
            mapRetInf = element[a:]
    return mapRetInf.replace('\r','')

def genmsg_SETUP(url,seq,userAgent,authSeq):
    msgRet = "SETUP " + url + " RTSP/1.0\r\n"
    msgRet += "CSeq: " + str(seq) + "\r\n"
    msgRet += "Authorization: " + authSeq + "\r\n"
    msgRet += "User-Agent: " + userAgent + "\r\n"
    msgRet += "Blocksize: 65535\r\n"
    msgRet += "Transport: RTP/AVP/TCP;unicast\r\n"
    msgRet += "\r\n"
    return msgRet


def genmsg_PLAY(url,seq,userAgent,sessionId,authSeq,clock):
    msgRet = "PLAY " + url + " RTSP/1.0\r\n"
    msgRet += "CSeq: " + str(seq) + "\r\n"
    msgRet += "Authorization: " + authSeq + "\r\n"
    msgRet += "User-Agent: " + userAgent + "\r\n"
    msgRet += "Session: " + sessionId + "\r\n"
    msgRet += "Require: " + "onvif-replay" + "\r\n"
    msgRet += "Range: clock="+clock+"\r\n"
    msgRet += "Rate-Control: no\r\n"
    msgRet += "\r\n"
    return msgRet


def download_video(ip, start, end, out):
    rtsp_url = f"rtsp://admin:{config['AUTH']['password_hanwha']}@{ip}:554/recording/{start}-{end}/play.smp"
    command = ["ffmpeg", "-i", rtsp_url, "-c", "copy", "-f", "mp4", out]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(e.output)


def genmsg_DESCRIBE(url, seq, userAgent, authSeq):
    msgRet = "DESCRIBE " + url + " RTSP/1.0\r\n"
    msgRet += "CSeq: " + str(seq) + "\r\n"
    msgRet += "Authorization: " + authSeq + "\r\n"
    msgRet += "User-Agent: " + userAgent + "\r\n"
    msgRet += "Accept: application/sdp\r\n"
    msgRet += "\r\n"
    return msgRet


def generateAuthString(username,password,realm,method,uri,nonce):
    mapRetInf = {}
    m1 = hashlib.md5((username + ":" + realm + ":" + password).encode("ascii")).hexdigest()
    m2 = hashlib.md5((method + ":" + uri).encode("ascii")).hexdigest()
    response = hashlib.md5((m1 + ":" + nonce + ":" + m2).encode("ascii")).hexdigest()

    mapRetInf = "Digest "
    mapRetInf += "username=\"" + m_Vars["defaultUsername"] + "\", "
    mapRetInf += "realm=\"" + realm + "\", "
    mapRetInf += "algorithm=\"MD5\", "
    mapRetInf += "nonce=\"" + nonce + "\", "
    mapRetInf += "uri=\"" + uri + "\", "
    mapRetInf += "response=\"" + response + "\""
    return mapRetInf


def download_video(trackid, control, output_file, clock, duration="00:05:00"):
    rtsp_url = f"rtsp://admin:{m_Vars['defaultPassword']}@{ip}/recording/play.smp/trackID={trackid}?clock={clock}"
    rtsp_url = f"rtsp://admin:{config['AUTH']['password_hanwha']}@10.70.66.16/recording/play.smp?Range=clock=20250302T224900Z-20250302T225000Z"
    rtsp_url = f"rtsp://admin:{config['AUTH']['password_hanwha']}@10.70.66.16/recording/20250303000000-20250303000500/OverlappedID=0/backup.smp"
    command = [
        "ffplay ",
        # "loglevel", "debug",
        "-rtsp_transport", "tcp",  # Use TCP for RTSP transport
        "-i", rtsp_url,           # RTSP URL with track ID
        # "-c", "copy",             # Copy codec to avoid re-encoding
        "-y",                     # Overwrite output file if it exists
        # "-t", duration,           # Duration of the video
        #output_file               # Output file path
    ]
    print(command)

    try:
        subprocess.run(command, check=True)
        print(f"Video downloaded successfully to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error during video download: {e}")


def bprint(byte_string):
    # Decode the byte string to a regular string
    decoded_string = byte_string.decode('utf-8')

    # Split by newlines to get each header and its value
    lines = decoded_string.split('\r\n')

    # Print each line
    print("**************")
    for line in lines:
        print(line)

if __name__ == "__main__":
    ip="10.70.66.16"
    # start = "20250123000000"
    # end = "20250123000500"
    # out = "test.mp4"
    # download_video(ip, start, end, out)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, 554))
    seq = 1

    authSeq = base64.b64encode(("admin" + ":" + config['AUTH']['password_hanwha']).encode("ascii"))
    authSeq = "Basic " + authSeq.decode("utf-8")

    url = "rtsp://10.70.66.16/recording/play.smp"
    #url = "rtsp://10.70.66.16/ProfileG/Recording-1/recording/play.smp"
    url = "rtsp://10.70.66.16/recording/20250303000000-20250303000500/OverlappedID=0/backup.smp"
    msg_describe = genmsg_DESCRIBE(url, seq, m_Vars["defaultUserAgent"], authSeq)
    msg_describe = msg_describe.encode("ascii")
    bprint(msg_describe)
    s.send(msg_describe)
    out_describe = s.recv(4096)
    bprint(out_describe)
    print("***********************************")
    seq = seq + 1
    out_describe = out_describe.decode("utf-8")
    if out_describe.find("Unauthorized") > 1:
        isDigest = True

        # New DESCRIBE with digest authentication
        start = out_describe.find("realm")
        begin = out_describe.find("\"", start)
        end = out_describe.find("\"", begin + 1)
        realm = out_describe[begin + 1:end]

        start = out_describe.find("nonce")
        begin = out_describe.find("\"", start)
        end = out_describe.find("\"", begin + 1)
        nonce = out_describe[begin + 1:end]

        authSeq = generateAuthString(m_Vars["defaultUsername"], m_Vars["defaultPassword"], realm, "DESCRIBE",
                                     m_Vars["defaultTestUri"], nonce)

        msg_describe = genmsg_DESCRIBE(url, seq, m_Vars["defaultUserAgent"], authSeq).encode("ascii")
        bprint(msg_describe)
        s.send(msg_describe)
        out_describe = s.recv(m_Vars["bufLen"]).decode("utf-8")
        print(out_describe)
    print("***********************************")

    control = decodeControl(out_describe)
    print(f"control={control}")

    authSeq = generateAuthString(m_Vars["defaultUsername"], m_Vars["defaultPassword"], realm, "SETUP",
                                 m_Vars["defaultTestUri"], nonce)

    print(f"authSeq={authSeq}")
    msg_setup = genmsg_SETUP(control, seq, m_Vars["defaultUserAgent"], authSeq)
    sessionId = msg_setup.split("response=")[1].split('\r')[0].replace('\"', '')
    print(f"sessionId={sessionId}")
    msg_setup = msg_setup.encode("ascii")
    bprint(msg_setup)
    s.send(msg_setup)
    out_setup = s.recv(m_Vars["bufLen"])
    bprint(out_setup)
    print("***********************************")
    seq = seq + 1
    #sessionId = decodeSession(msg1.decode("utf-8"))


    # msg_options = genmsg_OPTIONS(url, seq, m_Vars["defaultUserAgent"], sessionId, authSeq)
    # print(msg_options)
    # msg_options = msg_options.encode("ascii")
    # s.send(msg_options)
    # msg1 = s.recv(m_Vars["bufLen"])
    # print(msg1)
    # seq = seq + 1

    range = "20250302T225000.440Z-20250302T224900Z"
    msg_play = genmsg_PLAY(control + "/", seq, m_Vars["defaultUserAgent"], sessionId, authSeq, range)
    msg_play = msg_play.encode("ascii")
    bprint(msg_play)
    s.send(msg_play)
    out_play = s.recv(m_Vars["bufLen"])
    bprint(out_play)
    seq = seq + 1

    print("**************************************************")

    download_video("G726-16", control, "video.mp4", range,"00:05:00")
    #TODO video download to video.mp4

