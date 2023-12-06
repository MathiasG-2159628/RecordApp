import asyncio
import collections
import threading
import matplotlib.pyplot as plt
import pyhrv.tools as tools
import pyhrv.time_domain as td
import pyhrv.frequency_domain as fd
from pylsl import StreamInfo, StreamOutlet, local_clock

from bleak import BleakClient

address = "ce:e7:a1:3a:54:4b"
MODEL_NBR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
# 00002a24-0000-1000-8000-00805f9b34fb
HR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
# 00002a37-0000-1000-8000-00805f9b34fb
rri_buffer = collections.deque([], 10)
heart_outlet = None
raw_heart_outlet = None
disconnect = threading.Event()
disconnect.set()


def callback(sender: int, data: bytearray):
    # print(f"{sender}: {data}")
    hr = data[1]
    print(hr)
    
    # print("hr:", hr)
    for x in range(2, len(data), 2):
        rri = data[x] + 256 * data[x + 1]
        raw_heart_outlet.push_sample([rri], local_clock())
        rri_buffer.append(rri)
        # print("rri:", rri)

    if len(rri_buffer) == 10:
        rmssd = td.rmssd(rri_buffer)[0]
        # result = fd.welch_psd(rri_buffer)
        # plt.show()
        heart_outlet.push_sample([hr, rmssd], local_clock())


async def run(address):
    global rri_buffer, heart_outlet, raw_heart_outlet

    async with BleakClient(address) as client:
        model_number = await client.read_gatt_char(MODEL_NBR_UUID)
        print("Model connected: {0}".format("".join(map(chr, model_number))))

        await client.start_notify(HR_UUID, callback)

        while not disconnect.isSet():
            await asyncio.sleep(1)

        print("disconnecting polar")
        await client.stop_notify(HR_UUID)
        rri_buffer.clear()
        heart_outlet = None
        raw_heart_outlet = None


def initialize_outlets():
    global heart_outlet, raw_heart_outlet
    # processed heart outlet
    info = StreamInfo('python.polar.heart', 'heart', 2, 0, 'float32', 'heart-python')
    channels = info.desc().append_child("channels")
    for c in ["HR", "HRV"]:
        channels.append_child("channel") \
            .append_child_value("label", c)
    heart_outlet = StreamOutlet(info)

    # raw heart outlet
    info = StreamInfo('python.polar.raw-heart', 'raw-heart', 1, 0, 'float32', 'raw-heart-python')
    channels = info.desc().append_child("channels")
    for c in ["RRI"]:
        channels.append_child("channel") \
            .append_child_value("label", c)
    raw_heart_outlet = StreamOutlet(info)


def start(address):
    disconnect.clear()
    initialize_outlets()
    thread = threading.Thread(target=asyncio.run, args=(run(address),))
    thread.start()

# loop = asyncio.get_event_loop()
# loop.run_until_complete(run(address))
