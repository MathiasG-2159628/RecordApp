from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from functools import partial
import threading
from receive_data import *
import sys
from io import StringIO

__version__ = "1.0.3" 
class RedirectedOutput:
    def __init__(self, callback):
        self.callback = callback
        self.buffer = StringIO()

    def write(self, text):
        self.buffer.write(text)
        self.callback(self.buffer.getvalue())

    def flush(self):
        pass

class RecorderApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        self.start_stop_button = Button(text='Start Recording', on_press=self.toggle_recording)
        self.timer_label = Label(text='0:00')
        self.output_label = Label(text='')
        self.output_scroll = ScrollView(size_hint=(1, None), size=(500,500))

        self.output_scroll.add_widget(self.output_label)

        self.layout.add_widget(self.start_stop_button)
        self.layout.add_widget(self.timer_label)
        self.layout.add_widget(self.output_scroll)



        self.recording = False
        self.timer_seconds = 0

        return self.layout

    def toggle_recording(self, instance):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        sys.stdout = RedirectedOutput(callback=self.update_label)

        self.recording = True
        self.start_stop_button.text = 'Stop Recording'
        Clock.schedule_interval(self.update_timer, 1)

        stream_types = ["heart", "raw-heart"]
        
        self.thread = threading.Thread(target=partial(start, None, "Experiment1", stream_types))
        self.thread.setDaemon(True)
        self.thread.start()

    def stop_recording(self):
        self.recording = False
        self.start_stop_button.text = 'Start Recording'
        Clock.unschedule(self.update_timer)
        self.timer_seconds = 0
        shutdown()

    def update_timer(self, dt):
        self.timer_seconds += 1
        minutes = self.timer_seconds // 60
        seconds = self.timer_seconds % 60
        self.timer_label.text = f'{minutes}:{seconds:02}'

    def update_label(self, text):
        self.output_label.text = text 

if __name__ == "__main__":
    RecorderApp().run()
