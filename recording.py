import pyaudio
from pynput import keyboard
import numpy as np
import soundfile as sf
import os
import sys
import time

class Recorder:
    def __init__(
        self, chunksize=4096, format=pyaudio.paInt16, samplerate=44100, num_channel=1
    ):
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get("deviceCount")
        print("\nInput Devices;")
        for i in range(0, numdevices):
            if (
                p.get_device_info_by_host_api_device_index(0, i).get("maxInputChannels")
            ) > 0:
                print(
                    f" - id {i}: {p.get_device_info_by_host_api_device_index(0, i).get('name')}"
                )
        input_device = int(input("Select an input device id please: "))
        self.input_device = input_device
        self.format = format
        self.num_channel = num_channel
        self.samplerate = samplerate
        self.chunksize = chunksize
        self.p = p
        self.frames = []
        self.recording = False

    def callback(self, in_data, frame_count, time_info, status):
        if self.recording:
            self.frames.append(in_data)
            return (in_data, pyaudio.paContinue)
        else:
            self.frames = []
            return (in_data, pyaudio.paComplete)

    def open_stream(self):
        self.stream = self.p.open(
            format=self.format,
            channels=self.num_channel,
            rate=self.samplerate,
            input=True,
            frames_per_buffer=self.chunksize,
            input_device_index=self.input_device,
            stream_callback=self.callback,
        )

    def record_sentence(self, sentence, filename):
        def on_press(key):
            pass

        def on_release(key):
            if key == keyboard.Key.esc:
                if self.recording:
                    self.recording = False
                    self.frames = [
                        np.reshape(
                            np.frombuffer(frame, dtype=np.int16),
                            (self.chunksize, self.num_channel),
                        ) for frame in self.frames
                    ]
                    signal = np.concatenate(self.frames, axis=0)
                    signal = signal[2048:]
                    signal = signal / (np.max(abs(signal)) * 1.2)
                    sys.stdout.write("\033[K")
                    print(
                        f" >> {signal.shape[0] / self.samplerate:.3f}s recorded."
                    )

                    sf.write(filename, signal, self.samplerate)
                    print(
                        f" >> {filename} have been written."
                    )
                    self.stream.stop_stream()
                    return False
                else:
                    self.recording = True
                    self.open_stream()
                    self.stream.start_stream()
                    print(" >> Starting... Hold on...", end='\r')
                    time.sleep(1)
                    print(" >> Recording... Press esc again to stop. ", end='\r')
                    self.frames = []

        with keyboard.Listener(
            on_press=on_press, on_release=on_release, suppress=False
        ) as listener:
            print("-" * 45)
            print(f">>> READ: [ \033[94m\033[4m{sentence}\033[0m ]")
            print(" >> press esc to start...", end='\r')
            listener.join()


if __name__ == "__main__":
    user = input("Input your name: ")
    os.makedirs(os.path.join("./", user), exist_ok=True)
    try:
        r = Recorder(chunksize=2048)
        r.open_stream()
        with open("./sentences.txt", "r") as f:
            content = [item.strip().split("|  ") for item in f.readlines()]
        start = input(">>> Please input the index to start (default: 0): ")
        if not start:
            start = 0
        end = input(f">>> Please input the index of the end (default: {len(content)}): ")
        if not end:
            end = len(content)
        content = content[int(start):int(end) +1]
        for item in content:
            confirm = False
            while not confirm:
                sentence = item[1]
                filename = os.path.join("./", user, item[0] + ".wav")
                r.record_sentence(sentence, filename)
                confirm = input(" >> Confirm? (N to retry):\r")
                if confirm.lower() == "n":
                    confirm = False
                else:
                    sys.stdout.write("\033[K")
                    print(" >> Done.")
                    confirm = True
    except:
        try:
            r.stream.close()
        except:
            pass
        print("\nTerminated.")
