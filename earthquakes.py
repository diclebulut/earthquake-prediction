import os
import multiprocessing
from time import sleep
import requests


download_path = "./data5"
start_year = 2013
end_year = 2023 # partial data will occur if the year has not yet ends

years = range(start_year, end_year + 1)
months = range(1, 13)

if not os.path.exists(download_path):
    os.mkdir(download_path)

urls = []
for y in years:
    for m in months:
        url_tpl = f"http://udim.koeri.boun.edu.tr/zeqmap/xmlt/{y}{m:02}.xml"
        urls.append(url_tpl)


def download(url: str, base_path="."):
    try:
        response = requests.get(url)

        rfile = url.split("/")[-1]
        file_name = os.path.join(base_path, rfile)
        if response.status_code != 200:
            print(f"{_url} returns {response.status_code}")
            return "Download failed"

        with open(file_name, "w") as f:
            f.write(response.text)
            f.close()
        print(f"{_url} is downloaded")
        return "Download successful"
    except Exception as e:
        print(e)


queue = multiprocessing.Queue(maxsize=5)

while True:
    if not queue.full():
        if not urls:
            print("All urls are downloaded!")
            break
        _url = urls.pop()
        print(f"{_url} is added to queue.")
        queue.put(download(_url, download_path))
    else:
        print("Queue is full, wait for 5 secs.")
        sleep(5)

    while not queue.empty():
        result = queue.get()