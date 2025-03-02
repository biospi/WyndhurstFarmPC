#import cv2
# import time
# from datetime import datetime
# from concurrent.futures import ThreadPoolExecutor
# from pathlib import Path
#
# CAMERA_LIST_FILE = Path("hanwha.txt")
# BASE_OUTPUT_DIR = Path("/media/fo18103/Storage/CCTV/hanwha")
# CHUNK_DURATION = 20 * 60
# FOURCC = cv2.VideoWriter_fourcc(*"MP4V")
# FPS = 20
#
# def get_camera_directory(rtsp_url):
#     """Generate a directory path based on the last two elements of the IP and the current date."""
#     ip_address = rtsp_url.split("@")[-1].split(":")[0]  # Extract IP address
#     ip_suffix = ".".join(ip_address.split(".")[-2:])  # Last two elements of the IP
#     date_str = datetime.now().strftime("%d%b%Y")  # Format date as 09Jan2025
#     return BASE_OUTPUT_DIR / ip_suffix / date_str
#
# def get_output_filename(output_dir):
#     """Generate a timestamped filename for the video chunk."""
#     return output_dir / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4"  # Change extension to .mp4
#
# def record_camera(rtsp_url):
#     """Record video from the IP camera in chunks."""
#     output_dir = get_camera_directory(rtsp_url)
#     output_dir.mkdir(parents=True, exist_ok=True)
#
#     cap = cv2.VideoCapture(rtsp_url)
#     if not cap.isOpened():
#         print(f"Error: Cannot open the camera stream: {rtsp_url}")
#         return
#
#     while True:
#         start_time = time.time()
#         output_file = get_output_filename(output_dir)
#         frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#         frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#         out = cv2.VideoWriter(str(output_file), FOURCC, FPS, (frame_width, frame_height))
#         print(f"Recording started: {output_file}")
#         while time.time() - start_time < CHUNK_DURATION:
#             ret, frame = cap.read()
#             if not ret:
#                 print(f"Error: Failed to read frame from the camera: {rtsp_url}")
#                 break
#             out.write(frame)
#         out.release()
#         print(f"Recording saved: {output_file}")
#     cap.release()
#
# def main():
#     """Main function to read camera list and start recording in parallel."""
#     with CAMERA_LIST_FILE.open("r") as file:
#         camera_urls = [line.strip() for line in file if line.strip()]
#
#     with ThreadPoolExecutor() as executor:
#         for rtsp_url in camera_urls:
#             executor.submit(record_camera, rtsp_url)
#
# if __name__ == "__main__":
#     try:
#         main()
#     except KeyboardInterrupt:
#         print("Recording stopped.")

#rtsp://admin:Ocs881212@10.70.66.39:554/profile2/media.smp
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess

CAMERA_LIST_FILE = Path("hanwha.txt")
BASE_OUTPUT_DIR = Path("/media/fo18103/Storage/CCTV/hanwha")
CHUNK_DURATION = 20 * 60


def get_camera_directory(rtsp_url):
    """Generate a directory path based on the last two elements of the IP and the current date."""
    ip_address = rtsp_url.split("@")[-1].split(":")[0]  # Extract IP address
    ip_suffix = ".".join(ip_address.split(".")[-2:])  # Last two elements of the IP
    date_str = datetime.now().strftime("%Y%b%d")  # Format date as 09Jan2025
    return BASE_OUTPUT_DIR / ip_suffix / date_str


def get_output_filename(output_dir, start_time):
    """Generate a filename in the format startofvideo_endofvideo.mp4."""
    end_time = start_time + timedelta(seconds=CHUNK_DURATION)
    start_str = start_time.strftime("%Y%m%dT%H%M%S")
    end_str = end_time.strftime("%Y%m%dT%H%M%S")
    return output_dir / f"{start_str}_{end_str}.mp4"


def record_camera(rtsp_url):
    """Record video from the IP camera in chunks using FFmpeg."""
    while True:
        output_dir = get_camera_directory(rtsp_url)
        output_dir.mkdir(parents=True, exist_ok=True)
        start_time = datetime.now()
        output_file = get_output_filename(output_dir, start_time)
        print(f"Recording started: {output_file}")

        # Command to record video with FFmpeg (no audio stream)
        # command = [
        #     "ffmpeg",
        #     "-y",  # Overwrite output file if it exists
        #     "-rtsp_transport", "tcp",  # Use TCP for RTSP
        #     "-i", rtsp_url,  # Input RTSP stream
        #     "-t", str(CHUNK_DURATION),  # Duration of the video chunk
        #     "-c:v", "copy",  # Copy the video stream without re-encoding
        #     "-an",  # Disable audio
        #     str(output_file)  # Output file
        # ]

        command = [
            "ffmpeg",
            "-y",  # Overwrite output file if it exists
            "-rtsp_transport", "tcp",  # Use TCP for RTSP
            "-i", rtsp_url,  # Input RTSP stream
            "-t", str(CHUNK_DURATION),  # Duration of the video chunk
            "-c:v", "libx264",  # Re-encode video using H.264
            "-preset", "fast",
            # Speed-quality tradeoff (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
            "-crf", "28",  # Constant Rate Factor (lower = better quality, higher = smaller size; 23 is default)
            "-r", "16",  # Match input FPS
            "-an",  # Disable audio
            str(output_file)  # Output file
        ]

        try:
            print(command)
            subprocess.run(command, check=True)
            print(f"Recording saved: {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error recording {rtsp_url}: {e}")
            break


def main():
    """Main function to read camera list and start recording in parallel."""
    with CAMERA_LIST_FILE.open("r") as file:
        camera_ips = [line.strip() for line in file if line.strip()]

    with ThreadPoolExecutor() as executor:
        for camera_ip in camera_ips:
            #rtsp://admin:Ocs881212@10.70.66.39:554/profile2/media.smp
            rtsp_url = f"rtsp://admin:Ocs881212@{camera_ip}:554/profile2/media.smp"
            executor.submit(record_camera, rtsp_url)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Recording stopped.")

