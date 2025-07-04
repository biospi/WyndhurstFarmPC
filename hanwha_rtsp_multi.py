import rstp_playback
import concurrent.futures
import queue


def process_cctv(ip):
    print(ip)
    rstp_playback.main(ip)


if __name__ == "__main__":
    cctvs = [line.strip() for line in open("hanwha_tpen.txt").readlines()]
    # process_cctv(cctvs[0])

    cctv_queue = queue.Queue()
    for ip in cctvs:
        cctv_queue.put(ip)

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        while not cctv_queue.empty():
            ip = cctv_queue.get()
            executor.submit(process_cctv, ip)
