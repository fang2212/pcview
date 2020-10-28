import pyaudio
from threading import Thread
import wave
import os


class Audio(Thread):

    def __init__(self, file_path, duration_time=10, is_replay=False):
        super(Audio, self).__init__()
        self.file_path = file_path
        self.is_replay = is_replay
        self.duration_time = duration_time
        if is_replay:
            self.duration_time = 1008611

    def run(self):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 2
        RATE = 16000
        RECORD_SECONDS = self.duration_time
        WAVE_OUTPUT_FILENAME = self.file_path

        p = pyaudio.PyAudio()

        if not self.is_replay:
            dir_path = os.path.dirname(os.path.abspath(WAVE_OUTPUT_FILENAME))
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

            wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)

            stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)

            print("\033[0;34m  ** recording voice at " + self.file_path + " ** \033[0m")

            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK)
                wf.writeframes(data)

            stream.stop_stream()
            stream.close()
            wf.close()
            print("\033[0;34m  ** recording done at " + self.file_path + " ** \033[0m")

        else:
            if not os.path.exists(self.file_path):
                print("\033[0;34m  ** wave " + self.file_path + " not exist ** \033[0m")
                p.terminate()
                return

            wf = wave.open(self.file_path, 'rb')
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True)

            data = wf.readframes(CHUNK)
            print("\033[0;34m  ** play wave " + self.file_path + " ** \033[0m")

            while data != b'':
                stream.write(data)
                data = wf.readframes(CHUNK)

            stream.stop_stream()
            stream.close()
            print("\033[0;34m  ** play wave " + self.file_path + " over ** \033[0m")
        p.terminate()


if __name__ == '__main__':
    a = Audio("output.wav", duration_time=3)
    a.start()
    a.join()

    b = Audio("output.wav", is_replay=True)
    b.start()
    b.join()
