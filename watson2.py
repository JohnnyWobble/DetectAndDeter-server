# You need to install pyaudio to run this example
# pip install pyaudio

# When using a microphone, the AudioSource `input` parameter would be
# initialised as a queue. The pyaudio stream would be continuosly adding
# recordings to the queue, and the websocket client would be sending the
# recordings to the speech to text service
import datetime
import sys

import pyaudio

from ibm_watson import SpeechToTextV1
from ibm_watson.websocket import AudioSource
from threading import Thread

# from multiprocessing import Process, Queue
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

from recog_callback import RecognizeCallback1
# from ai import predict_text

try:
    from Queue import Queue, Full
except ImportError:
    from queue import Queue, Full

###############################################
#### Initalize queue to store the recordings ##
###############################################
CHUNK = 1024
# Note: It will discard if the websocket client can't consume fast enough
# So, increase the max size as per your choice
BUF_MAX_SIZE = CHUNK * 10
# Buffer to store audio
q = Queue(maxsize=int(round(BUF_MAX_SIZE / CHUNK)))

# Create an instance of AudioSource
audio_source = AudioSource(q, True, True)

###############################################
#### Prepare Speech to Text Service ########
###############################################

# initialize speech to text service
authenticator = IAMAuthenticator('zPJij17cD8uAVUsaWqRgZPyGt9CH5q8XuwNGurfFhtXW')
speech_to_text = SpeechToTextV1(authenticator=authenticator)


# this function will initiate the recognize service and pass in the AudioSource


def recognize_using_weboscket(*args):
    mycallback = RecognizeCallback1()
    speech_to_text.recognize_using_websocket(audio=audio_source,
                                             content_type='audio/l16; rate=44100',
                                             recognize_callback=mycallback,
                                             interim_results=True)

###############################################
#### Prepare the for recording using Pyaudio ##
###############################################


# Variables for recording the speech
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# define callback for pyaudio to store the recording in queue


def pyaudio_callback(in_data, frame_count, time_info, status):
    # print(in_data)
    try:
        q.put(in_data)
    except Full:
        pass  # discard
    return None, pyaudio.paContinue


# instantiate pyaudio
audio = pyaudio.PyAudio()

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

#########################################################################
#### Start the recording and start service to recognize the stream ######
#########################################################################
SPEECH = True

if __name__ == '__main__':
    if SPEECH:
        print("Enter CTRL+C to end recording...")
        stream.start_stream()

        try:
            recognize_thread = Thread(target=speech_to_text.recognize_using_websocket, kwargs={
                "audio": audio_source,
                "content_type": "audio/l16; rate=44100",
                "recognize_callback": RecognizeCallback1(),
                "interim_results": True})
            recognize_thread.start()

            while recognize_thread.is_alive():
                pass

            recognize_thread.join()
        except (KeyboardInterrupt, SystemExit):
            # stop recording
            stream.stop_stream()
            stream.close()
            audio.terminate()
            audio_source.completed_recording()
            print("end")
