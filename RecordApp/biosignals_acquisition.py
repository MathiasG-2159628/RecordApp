import sys
import os
import collections
import platform
import sys
from pylsl import StreamInfo, StreamOutlet, local_clock
import threading

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


osDic = {"Darwin": "MacOS",
         "Linux": "Linux64",
         "Windows": ("Win32", "Win64")}
if platform.system() != "Windows":
    sys.path.append(resource_path("PLUX-API-Python3/{}/plux.so".format(osDic[platform.system()])))
else:
    if platform.architecture()[0] == '64bit':
        sys.path.append(resource_path("PLUX-API-Python3/Win64"))
    else:
        sys.path.append(resource_path("PLUX-API-Python3/Win32"))
import plux

# initialize outlet
info = StreamInfo('python.biosignalsplux', 'biosignalsplux', 8, 2000, 'float32', 'biosignalsplux-python')

info.desc().append_child_value("manufacturer", "BioSemi")
channels = info.desc().append_child("channels")
for c in ["Ch1", "Ch2", "Ch3", "Ch4", "Ch5", "Ch6", "Ch7", "Ch8"]:
    channels.append_child("channel") \
        .append_child_value("label", c)

outlet = StreamOutlet(info, 32, 360)

shutdown = False


class NewDevice(plux.SignalsDev):

    def __init__(self, address):
        plux.MemoryDev.__init__(address)
        self.frequency = 0

    def onRawFrame(self, nSeq, data):  # onRawFrame takes three arguments
        sample = list(data)
        outlet.push_sample(sample, local_clock())
        return shutdown


def acquisition_loop(device):
    device.loop()  # calls device.onRawFrame until it returns True
    device.stop()
    device.close()


def start_acquisition(address, freq, code):  # time acquisition for each frequency
    """
    Example acquisition.

    Supported channel number codes:
    {1 channel - 0x01, 2 channels - 0x03, 3 channels - 0x07
    4 channels - 0x0F, 5 channels - 0x1F, 6 channels - 0x3F
    7 channels - 0x7F, 8 channels - 0xFF}

    Maximum acquisition frequencies for number of channels:
    1 channel - 8000, 2 channels - 5000, 3 channels - 4000
    4 channels - 3000, 5 channels - 3000, 6 channels - 2000
    7 channels - 2000, 8 channels - 2000
    """

    device = NewDevice(address)
    device.frequency = freq
    device.start(device.frequency, code, 16)
    acquisition_thread = threading.Thread(target=acquisition_loop, args=(device,))
    acquisition_thread.start()
