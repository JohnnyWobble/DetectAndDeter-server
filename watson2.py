# You need to install pyaudio to run this example
# pip install pyaudio

# When using a microphone, the AudioSource `input` parameter would be
# initialised as a queue. The pyaudio stream would be continuosly adding
# recordings to the queue, and the websocket client would be sending the
# recordings to the speech to text service

from threading import Thread
from queue import Queue, Full

from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import pyaudio
from ibm_watson import SpeechToTextV1
from ibm_watson.websocket import AudioSource

from recog_callback import RecognizeCallback1


class WatsonRecognizer:
    # Note: It will discard if the websocket client can't consume fast enough
    # So, increase the max size as per your choice
    CHUNK = 1024
    BUF_MAX_SIZE = CHUNK * 10

    # Variables for recording the speech
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    def __init__(self):
        # Buffer to store audio
        self.q = Queue(maxsize=int(round(self.BUF_MAX_SIZE / self.CHUNK)))
        self.audio_source = AudioSource(self.q, True, True)
        self.callback = RecognizeCallback1()

        # initialize speech to text service
        self.authenticator = IAMAuthenticator('zPJij17cD8uAVUsaWqRgZPyGt9CH5q8XuwNGurfFhtXW')
        self.speech_to_text = SpeechToTextV1(authenticator=self.authenticator)

        # instantiate audio
        self.audio = pyaudio.PyAudio()

        # open stream using callback
        self.stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=self.pyaudio_callback,
            start=False
        )

        # thread for the speech recognition
        self.thread = Thread(target=self.speech_to_text.recognize_using_websocket, kwargs={
            "audio": self.audio_source,
            "content_type": "audio/l16; rate=44100",
            "recognize_callback": self.callback,
            "interim_results": True})

    def pyaudio_callback(self, in_data, frame_count, time_info, status):
        try:
            self.q.put(in_data)
        except Full:
            pass  # discard
        return None, pyaudio.paContinue

    def start(self):
        self.stream.start_stream()
        self.thread.start()

    def close(self, timeout=20):
        self.thread.join(timeout=timeout)
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        self.audio_source.completed_recording()


if __name__ == '__main__':
    watson = WatsonRecognizer()

    try:
        watson.start()

        while watson.thread.is_alive():
            pass
    except (KeyboardInterrupt, SystemExit):
        watson.close()
        print("end")
