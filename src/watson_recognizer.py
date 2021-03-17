from threading import Thread
from queue import Queue, Full
import sys

from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import pyaudio
from ibm_watson import SpeechToTextV1
from ibm_watson.websocket import AudioSource
from ibm_watson.websocket import RecognizeCallback as RCallback


class WatsonRecognizer:
    # Note: It will discard if the websocket client can't consume fast enough
    # So, increase the max size as per your choice
    CHUNK = 1024
    BUF_MAX_SIZE = CHUNK * 10

    # Variables for recording the speech
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    def __init__(self, prints=False):
        # Buffer to store audio
        self.audio_q = Queue(maxsize=int(round(self.BUF_MAX_SIZE / self.CHUNK)))
        self.audio_source = AudioSource(self.audio_q, True, True)
        self.callback = RecognizeCallback(prints=prints, queues=[])

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
            self.audio_q.put(in_data)
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


class RecognizeCallback(RCallback):
    def __init__(self, queues, prints=False):
        self.last = ''
        self.queues = queues
        self.prints = prints

    def on_transcription(self, transcript):
        self.last = transcript[0]['transcript'].strip().replace(" %HESITATION", "")
        print("STT:", self.last)
        for q in self.queues:
            q.put(self.last)

        if self.prints:
            print("\r--> ", self.last)

    def on_connected(self):
        print('Connection was successful')

    def on_error(self, error):
        print('Error received: {}'.format(error))

    def on_inactivity_timeout(self, error):
        print('Inactivity timeout: {}'.format(error))

    def on_listening(self):
        print('Service is listening')

    def on_hypothesis(self, hypothesis):
        if self.prints:
            if hypothesis.strip() != self.last:
                print('\r', hypothesis, sep='', end='')
                sys.stdout.flush()

    def on_close(self):
        print("Connection closed")


if __name__ == '__main__':
    watson = WatsonRecognizer(prints=True)

    try:
        watson.start()

        while watson.thread.is_alive():
            pass
    except (KeyboardInterrupt, SystemExit):
        watson.close()
        print("end")
