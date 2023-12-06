import os
import time
from datetime import datetime
from pylsl import StreamInlet, resolve_byprop
import threading
from collections import OrderedDict, deque
import csv
from bs4 import BeautifulSoup
import subprocess
from pathlib import Path
#import biosignals_acquisition
import polar_acquisition

class Stream(threading.Thread):
    def __init__(self, stream_type):
        self.type = stream_type
        self.buffer = deque()
        self.ch_labels = []
        self.stop_event = threading.Event()

        threading.Thread.__init__(self, name=stream_type)

    def run(self):
        self.read_stream(self.type)
        return

    def read_stream(self, stream_type):
        streams = []

        while len(streams) < 1:
            if self.stop_event.is_set():
                return
            streams = resolve_byprop('type', stream_type, 1, 1.0)
        inlet = StreamInlet(streams[0])

        info = BeautifulSoup(inlet.info().as_xml(), features="html.parser")
        channels = info.find_all("channel")
        for channel in channels:
            self.ch_labels.append(channel.label.text)

        # print(f"{self.type} — connected")

        last_sample_time = 0
        time_since_last_sample = 0
        while not self.stop_event.is_set() or time_since_last_sample < 100:
            time_since_last_sample = time.time() - last_sample_time
            sample, timestamp = inlet.pull_sample(timeout=1.0)
            
            if sample is None:
                continue
            last_sample_time = time.time()

            csv_sample = [timestamp] + sample
            self.buffer.append(csv_sample)

        self.debuffer()

    def debuffer(self):
        csv_file = open(f'{data_dir}/{self.type}.csv', 'w', newline='')

        with csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Timestamp"] + self.ch_labels)
            writer.writerows(self.buffer)

    def join(self, timeout=None):
        self.stop_event.set()
        threading.Thread.join(self, timeout)

    def terminate(self):
        self.stop_event.set()


data_dir = None
threads = []


def shutdown():
    print("Saving data, please wait a moment.")
    #biosignals_acquisition.shutdown = True
    polar_acquisition.disconnect.set()

    for thread in threads:
        thread.terminate()


def start(biosignalsplux_macaddress, identifier, stream_types):
    global data_dir
    # if biosignalsplux_macaddress is not None:
    #     biosignals_acquisition.start_acquisition(biosignalsplux_macaddress, 500, 0xFF)

    print("Recording started")
    #polar_macaddress = "ce:e7:a1:3a:54:4b"
    polar_macaddress = "d0:5a:12:b9:1f:22"
    polar_acquisition.disconnect.clear()
    polar_acquisition.start(polar_macaddress)

    for stream_type in stream_types:
        thread = Stream(stream_type)
        threads.append(thread)

    timestamp = datetime.now().strftime('%Y%m%d%H%M')
    data_dir = f"ExperimentData/{identifier}_{timestamp}"
    Path(data_dir).mkdir(parents=True, exist_ok=True)

    # print("press ENTER to start recording:")
    # input()

    for thread in threads:
        thread.start()

    # print("press ENTER to stop recording:")
    input()
    shutdown()


if __name__ == "__main__":
    # stream_types = ["events", "heldObjects", "booleanActions", "heart", "raw-heart", "performance", "questionnaire"]
    stream_types = ["heart", "raw-heart"]
    start(None, "Experiment1", stream_types)  # BTH00:07:80:0F:80:00
