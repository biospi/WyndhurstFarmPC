import json
from datetime import datetime, timedelta
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor
from utils import run_cmd
import time


def get_log_filename():
    """Generate a log filename with the current date."""
    log_dir = Path("log")
    log_dir.mkdir(parents=True, exist_ok=True)  # Ensure the log directory exists
    current_date = datetime.now().strftime("%Y-%m-%d")
    return log_dir / f"hanwha_downloader_{current_date}.log"


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


def download_video(camera, start_time, duration):
    """Download a video for a specific camera."""
    date = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
    date_dir = date.strftime("%Y%b%d")
    ip = ".".join(camera["ip"].split('.')[-2:])
    out_dir = Path("/media/fo18103/Storage/CCTV/hanwha") / ip / date_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    end_time = date + timedelta(seconds=duration)
    end_time_format = end_time.strftime("%Y-%m-%dT%H:%M:%S")
    end_time_str = end_time.strftime("%Y%m%dT%H%M%S")
    start_time_str = date.strftime("%Y%m%dT%H%M%S")
    out_video_path = out_dir / f"{start_time_str}_{end_time_str}.mp4"
    logging.info(f"camera={camera['ip']} start_time={start_time} end_time={end_time_format}")
    cmd = (
        f"curl --insecure -X 'GET' 'https://localhost:7001/media/{camera['id']}.mp4?"
        f"pos=%22{start_time}%22&duration={duration}' "
        f"-H 'accept: */*' "
        f"-H 'x-runtime-guid: vms-6f7eeebe0025132dcf008fc07ef2c053-QWWErRBgae' "
        f"-o {out_video_path}"
    )
    if run_cmd(cmd) == 0:
        logging.info(f"downloaded video {out_video_path} from {camera['ip']}")
        return 0
    logging.info(f"failed to download video {out_video_path} from {camera['ip']}")
    if out_video_path.exists(): #file will be corrupted
        out_video_path.unlink()
    return -1


def process_camera(camera, last_end_time, duration):
    """Download videos for a single camera in continuous intervals."""
    try:
        start_time = last_end_time.strftime("%Y-%m-%dT%H:%M:%S")
        s = download_video(camera, start_time, duration)
        if s == 0:
            res = last_end_time + timedelta(seconds=duration)
        else:
            res = last_end_time
        logging.info(f"res last_end_time={res}")
        return res
    except Exception as e:
        logging.error(f"Error processing camera {camera['id']} ({camera['ip']}): {e}")
        return last_end_time  # Retain the old time if there's an error

def main():
    configure_logging()
    # Load the camera configuration
    with open("hanwha.json", "r") as json_file:
        data = json.load(json_file)

    # Initialize per-camera last_end_time
    duration = 20
    camera_states = {
        camera["id"]: datetime.now() - timedelta(hours=0, minutes=duration) for camera in data["cameras"]
    }

    current_day = datetime.now().day
    while True:
        if datetime.now().day != current_day:
            configure_logging()
            current_day = datetime.now().day
        logging.info(f"Starting download cycle for {len(data['cameras'])} cameras.")

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            for camera in data["cameras"]:
                camera_id = camera["id"]
                last_end_time = camera_states[camera_id]

                future = executor.submit(
                    process_camera,
                    camera,
                    last_end_time,
                    duration * 60
                )
                futures[future] = camera_id

            for future in futures:
                camera_id = futures[future]
                try:
                    # Update the last_end_time for the camera upon successful completion
                    camera_states[camera_id] = future.result()
                except Exception as e:
                    # Log any errors that occur during processing
                    logging.error(f"Error in thread for camera {camera_id}: {e}")


        logging.info("All cameras completed their downloads. Starting next cycle.")
        logging.info("Sleeping before the next download cycle.")
        time.sleep(duration*60)

if __name__ == "__main__":
    main()
