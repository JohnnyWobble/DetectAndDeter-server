import logging
from queue import Queue, Full
from threading import Thread

import pyaudio
from ibm_watson import SpeechToTextV1
from ibm_watson.websocket import AudioSource
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

from watson_recognizer import RecognizeCallback as MyRecognizeCallback

# Watson websocket prints justs too many debug logs, so disable it
logging.disable(logging.CRITICAL)

# https://www.satishchandragupta.com/tech/speech-recognition-with-python.html

# Chunk and buffer size
CHUNK_SIZE = 4096
BUFFER_MAX_ELEMENT = 10

WATSON_API_KEY = 'zPJij17cD8uAVUsaWqRgZPyGt9CH5q8XuwNGurfFhtXW'
CHUNK = 1024
# Note: It will discard if the websocket client can't consume fast enough
# So, increase the max size as per your choice
BUF_MAX_SIZE = CHUNK * 10
# Buffer to store audio
q = Queue(maxsize=int(round(BUF_MAX_SIZE / CHUNK)))

# Create an instance of AudioSource
audio_source = AudioSource(q, True, True)

# instantiate pyaudio
audio = pyaudio.PyAudio()

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100


def pyaudio_callback(in_data, frame_count, time_info, status):
    try:
        q.put(in_data)
    except Full:
        pass  # discard
    return None, pyaudio.paContinue


# open stream using callback
stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK,
    stream_callback=pyaudio_callback,
    start=False
)


def watson_streaming_stt() -> Thread:
    authenticator = IAMAuthenticator(WATSON_API_KEY)
    speech_to_text = SpeechToTextV1(authenticator=authenticator)

    # Callback object
    mycallback = MyRecognizeCallback()

    # Start Speech-to-Text recognition thread
    stt_stream_thread = Thread(
        target=speech_to_text.recognize_using_websocket,
        kwargs={
            'audio': audio_source,
            'content_type': 'audio/l16; rate=44100',
            'recognize_callback': mycallback,
            'interim_results': True
        }
    )

    stream.start_stream()
    stt_stream_thread.start()
    while stt_stream_thread.is_alive():
        pass
    stt_stream_thread.join()
    return stt_stream_thread


if __name__ == '__main__':
    thread = watson_streaming_stt()
    thread.start()
    while thread.is_alive():
        pass
    thread.join()
    stream.close()
