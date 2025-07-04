from pathlib import Path
from datetime import datetime, timedelta
import time
import logging
from concurrent.futures import ThreadPoolExecutor

from utils import run_cmd, format_curl
import configparser
config = configparser.ConfigParser()
config.read("config.cfg")

BUFFER = []
DOWNLOADED_FILES = "downloaded_files.txt"

def get_log_filename():
    """Generate a log filename with the current date."""
    log_dir = Path("log")
    log_dir.mkdir(parents=True, exist_ok=True)  # Ensure the log directory exists
    current_date = datetime.now().strftime("%Y-%m-%d")
    return log_dir / f"hikvision_downloader_{current_date}.log"

def configure_logging():
    """Configure logging to use a new file based on the current date."""
    log_file = get_log_filename()
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        filemode="a",  # Append to the file if it already exists
    )
    logging.info(f"Logging configured. Writing logs to {log_file}")

def download_media_from(ip, start_time, end_time):
    #logging.info(f"Downloading videos from {ip} ({start_time} - {end_time})")
    out = Path("/media/fo18103/Storage/CCTV/hikvision")
    out.mkdir(parents=True, exist_ok=True)
    curl_cmd_file = out / ip.replace('.', '')

    cmd = (
        f"java -jar importer.jar {ip}:80 {config['AUTH']['login']} {config['AUTH']['password_hikvision']} --from-time '{start_time}' "
        f"--to-time '{end_time}' | cut -d'|' -f5 > {curl_cmd_file}"
    )

    if ip == "10.70.66.137":
        cmd = (
            f"java -jar importer_new.jar {ip}:80 {config['AUTH']['login']} {config['AUTH']['password_hikvision']} --from-time '{start_time}' "
            f"--to-time '{end_time}' | cut -d'|' -f5 > {curl_cmd_file}"
        )

    logging.info(f"Running command: {cmd}")
    run_cmd(cmd, verbose=False)

    if not curl_cmd_file.exists():
        logging.error(f"Missing file! {curl_cmd_file}")
        return [], []

    print(curl_cmd_file)
    with open(curl_cmd_file) as file:
        curl_cmds_videos = []
        curl_cmds_photos = []
        output_dir = out / "media"

        output_dir.mkdir(parents=True, exist_ok=True)
        time_s, time_e, durs = [], [], []
        for line in file:
            #print(line)
            if "mp4" in line:
                logging.info(f"line {line}".replace('\n',''))
            cmd_, _, start, end = format_curl(
                line.rstrip(),
                output_dir,
                format_output=True,
                ip_address=ip
            )
            if "mp4" in line:
                time_s.append(start)
                time_e.append(end)
                dur = end - start
                durs.append(dur)

            if "mp4" in cmd_:
                t = dur.total_seconds() / 60
                #print(t)
                # if ip != "10.70.66.138":
                #     if t >= 20: #remove temp video
                #         curl_cmds_videos.append(cmd_)
                # else:
                #     if t >= 6.5:
                #         curl_cmds_videos.append(cmd_)
                curl_cmds_videos.append(cmd_)
                #print(cmd_)
            elif "jpeg" in cmd_:
                curl_cmds_photos.append(cmd_)
    print("curl_cmds_videos", curl_cmds_videos)
    print("curl_cmds_photos", curl_cmds_photos)
    return curl_cmds_videos, curl_cmds_photos, time_s[0], time_e[-1]

def is_file_downloaded(file_path):
    if not Path(DOWNLOADED_FILES).exists():
        print(f"Missing file {DOWNLOADED_FILES}!")
        return False

    with open(DOWNLOADED_FILES, "r") as f:
        return file_path.as_posix() in f.read().splitlines()


def is_recent_file(file_path, cutoff_date="20250330"):
    """Check if the file's start timestamp is on or after the cutoff date."""
    filename = file_path.stem  # Extract filename without extension
    start_timestamp = filename.split("_")[0]  # Get the start timestamp part

    # Convert timestamps to datetime objects for comparison
    file_date = datetime.strptime(start_timestamp, "%Y%m%dT%H%M%S")
    cutoff_datetime = datetime.strptime(cutoff_date, "%Y%m%d")

    return file_date >= cutoff_datetime


def process_camera(ip, last_iteration_data, download_images=False):
    """Process a single camera's video and photo downloads."""

    now = datetime.now()
    start_time = (now - timedelta(days=1, hours=now.hour, minutes=now.minute, seconds=now.second)).strftime('%m/%d/%y at %I:%M %p')
    end_time = now.strftime('%m/%d/%y at %I:%M %p')
    #now = datetime.now()
    if ip in last_iteration_data:
        try:
            s, e = last_iteration_data[ip].split(' ')
            s_d = datetime.strptime(s, "%Y%m%dT%H%M%S")
            e_d = datetime.strptime(e, "%Y%m%dT%H%M%S")
            start_time = e_d.strftime('%m/%d/%y at %I:%M %p')
        except Exception as e:
            print(e)

    try:

        # start_time = last_end_time.strftime("%m/%d/%y at %I:%M %p")
        # end_time = now.strftime("%m/%d/%y at %I:%M %p")
        # start_time = "12/12/24 at 12:00 AM"
        # end_time = "12/13/24 at 11:59 PM"
        logging.info(f"ip={ip} start_time={start_time} end_time={end_time}")
        print(f"ip={ip} start_time={start_time} end_time={end_time}")#for debugging todo remove
        videos, images, first_file, last_file = download_media_from(ip, start_time, end_time)
        #return f"{first_file.strftime('%Y%m%dT%H%M%S')} {last_file.strftime('%Y%m%dT%H%M%S')}"

        print(videos)
        for cmd in videos:
            logging.info(f"Downloading video for {ip} with command: {cmd}")
            print(cmd)
            filepath = Path(cmd.split("--output")[1].strip())
            if not is_recent_file(filepath):
                logging.info(f"Skipping old file {filepath}")
                continue  # Skip files older than May 24, 2025
            if filepath.exists() or is_file_downloaded(filepath):
                logging.info(f"already downloaded {filepath}")
                continue
            p_status = run_cmd(cmd, verbose=True)
            if p_status == 0:
                logging.info(f"downloaded {filepath}")
                BUFFER.append(filepath.name)
                with open(DOWNLOADED_FILES, "a") as f:
                    f.write(filepath.as_posix() + "\n")

        if ip == '10.70.66.138':
            download_images = False

        if download_images:
            for cmd in images:
                logging.info(f"Downloading image for {ip} with command: {cmd}")
                filepath = Path(cmd.split("--output")[1])
                if filepath.exists():
                    logging.info(f"already downloaded {filepath}")
                    continue
                p_status = run_cmd(cmd, verbose=True)
                if p_status == 0:
                    logging.info(f"downloaded {filepath}")
                    BUFFER.append(filepath.name)

        logging.info(f"end={last_file}")
        return last_file  # Return the new last_end_time

    except Exception as e:
        logging.error(f"Error processing IP {ip}: {e}")
        return None
#
# def main():
#
#     # mp4_files = list(Path("/media/fo18103/Storage/CCTV/hikvision/media").rglob("*.mp4"))
#     # for video in mp4_files:
#     #     with open(DOWNLOADED_FILES, "a") as f:
#     #         f.write(Path(video).as_posix() + "\n")
#     #
#     # exit()
#
#     configure_logging()
#     # duration = 20
#     # cctvs = [line.strip() for line in open("hikvision_ips.txt").readlines()]
#     # camera_states = {ip: datetime.now() - timedelta(minutes=duration) for ip in cctvs}
#
#     # current_day = datetime.now().day
#     last_iter_file = {}
#     while True:
#         cctvs = [line.strip() for line in open("hikvision_ips.txt").readlines()]
#         #camera_states = {ip: datetime.now() - timedelta(minutes=duration) for ip in cctvs}
#         # Reconfigure logging if the day changes
#         # if datetime.now().day != current_day:
#         #     configure_logging()
#         #     current_day = datetime.now().day
#
#         logging.info(f"Starting download cycle for {len(cctvs)} cameras.")
#         with ThreadPoolExecutor(max_workers=len(cctvs)) as executor:
#             futures = {
#                 executor.submit(process_camera, ip, last_iter_file): ip
#                 for ip in cctvs
#             }
#             for future in futures:
#                 ip = futures[future]
#                 try:
#                     res = future.result()
#                     last_iter_file[ip] = res
#                 except Exception as e:
#                     logging.error(f"Error in thread for IP {ip}: {e}")
#
#         # logging.info("Sleeping before the next download cycle.")
#         # time.sleep(60)
#

def daily_task():
    configure_logging()
    last_iter_file = {}
    cctvs = [line.strip() for line in open("hikvision_ips.txt").readlines()]
    logging.info(f"Starting download cycle for {len(cctvs)} cameras.")

    with ThreadPoolExecutor(max_workers=len(cctvs)) as executor:
        futures = {
            executor.submit(process_camera, ip, last_iter_file): ip
            for ip in cctvs
        }
        for future in futures:
            ip = futures[future]
            try:
                res = future.result()
                last_iter_file[ip] = res
            except Exception as e:
                logging.error(f"Error in thread for IP {ip}: {e}")

def main():
    #daily_task()
    while True:
        now = datetime.now()
        # Calculate the next midnight
        next_run = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        time_to_sleep = (next_run - now).total_seconds()
        print(f"Sleeping until next run at {next_run}")

        time.sleep(time_to_sleep)

        daily_task()

if __name__ == "__main__":
    main()