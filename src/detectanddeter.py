from multiprocessing import Queue, Process, Manager, Event
from io import BytesIO
import audioop
import base64
import numpy as np
import datetime as dt

from gtts import gTTS
from pydub import AudioSegment
from deepspeech import Model

from ai import model
from chatbot import chatbot


class DetectAndDeter:
    CLASSIFICATION_COUNT = 5
    TELEMARKETER_THRESH = 0.3
    VALID_CALLER_THRESH = 0.1
    IN_AUDIO_RATE = 8000
    DS_AUDIO_RATE = 16000
    QUIET_THRESH = 150
    QUIET_LENGTH = 3000

    def __init__(self, name):
        self.name = name  # user's name  e.g. "Bob Ross"
        self.is_telemarketer = None
        self.valid_caller_event = Event()
        self.caller_audio_chunk = np.array([], dtype='int16')

        self.audio_in_queue = Queue()
        self.stt_to_classification_queue = Queue()
        self.stt_to_chatbot_queue = Queue()
        self.chatbot_to_tts_queue = Queue()
        self.audio_out_queue = Queue()

        self.manager = Manager()
        self.transcript = self.manager.list()
        self.predictions = self.manager.list()
        self.deep_speech = None

        self.final_transcript = None
        self.final_predictions = None

        self.speech_to_text_thread = Process(target=self.speech_to_text)
        self.classify_text_thread = Process(target=self.classify_text)
        self.generate_response_thread = Process(target=self.generate_responses)
        self.text_to_speech_thread = Process(target=self.text_to_speech)

    @property
    def queues(self):
        return self.audio_in_queue, self.audio_out_queue

    def start(self):
        self.speech_to_text_thread.start()
        self.classify_text_thread.start()
        self.generate_response_thread.start()
        self.text_to_speech_thread.start()

    def close(self):
        self.final_predictions = [value for value in self.predictions]
        self.final_transcript = [value for value in self.transcript]

        self.speech_to_text_thread.terminate()
        self.speech_to_text_thread.join()
        self.speech_to_text_thread.close()

        self.classify_text_thread.terminate()
        self.classify_text_thread.join()
        self.classify_text_thread.close()

        self.generate_response_thread.terminate()
        self.generate_response_thread.join()
        self.generate_response_thread.close()

        self.text_to_speech_thread.terminate()
        self.text_to_speech_thread.join()
        self.text_to_speech_thread.close()

    def classify_text(self):
        while self.is_telemarketer is None:
            text = self.stt_to_classification_queue.get()
            preds = model.predict(text)
            self.predictions.append({"prediction": str(preds[0]).lower(), "confidence": max(preds[2])})
            all_preds = [t["prediction"] for t in self.predictions]

            maybe_telemarketer = all_preds.count("persuasion") / len(preds)

            if len(preds) > self.CLASSIFICATION_COUNT:
                if maybe_telemarketer > self.TELEMARKETER_THRESH:
                    self.is_telemarketer = True
                    break
                elif maybe_telemarketer < self.VALID_CALLER_THRESH:
                    self.is_telemarketer = False
                    break

        if not self.is_telemarketer:
            self.valid_caller_event.set()

    def generate_responses(self):
        while True:
            text = self.stt_to_chatbot_queue.get()
            print("Generate Response:", text)
            response = str(chatbot.get_response(text))

            self.transcript.append({"speaker": "caller", "text": text})
            self.transcript.append({"speaker": "self", "text": response})

            self.chatbot_to_tts_queue.put(response)

    def text_to_speech(self):
        while True:
            response = self.chatbot_to_tts_queue.get()
            print("TTS:", response)
            mp3_fp = BytesIO()
            tts = gTTS(response, lang='en')
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)

            sound = AudioSegment.from_mp3(mp3_fp)
            sound = sound.set_channels(1)
            sound = sound.set_frame_rate(self.IN_AUDIO_RATE)

            ulaw_sound = audioop.lin2ulaw(sound.raw_data, 2)

            chunk_len = 192
            chunks = len(ulaw_sound) // chunk_len

            for c in range(chunks):
                chunk = ulaw_sound[c*chunk_len:c*chunk_len+chunk_len]
                self.audio_out_queue.put(base64.b64encode(chunk).decode('utf-8'))

    def speech_to_text(self):
        self.deep_speech = Model('models/deepspeech-0.9.3-models.pbmm')
        self.deep_speech.enableExternalScorer('models/deepspeech-0.9.3-models.scorer')

        stream = self.deep_speech.createStream()

        while True:
            speech = self.audio_in_queue.get()

            while not self.audio_in_queue.empty():
                speech += self.audio_in_queue.get()

            lin_speech = audioop.ulaw2lin(speech, 2)
            ds_speech, _ = audioop.ratecv(lin_speech, 2, 1, self.IN_AUDIO_RATE, self. DS_AUDIO_RATE, None)

            lin_speech_arr = np.frombuffer(lin_speech, np.int16)
            ds_speech_arr = np.frombuffer(ds_speech, np.int16)

            stream.feedAudioContent(ds_speech_arr)

            self.caller_audio_chunk = np.concatenate((self.caller_audio_chunk, lin_speech_arr))

            chunk_idx = max(0, len(self.caller_audio_chunk) - self.QUIET_LENGTH)
            quiet_chunk = self.caller_audio_chunk[chunk_idx:]
            if (quiet_chunk < self.QUIET_THRESH).all() and (self.caller_audio_chunk > self.QUIET_THRESH).any():
                text = stream.intermediateDecode()

                if text.strip():
                    self.stt_to_chatbot_queue.put(text)
                    self.stt_to_classification_queue.put(text)

                    stream.finishStream()
                    stream = self.deep_speech.createStream()

                self.caller_audio_chunk = np.array([], dtype='int16')

    def make_greeting(self):
        self.chatbot_to_tts_queue.put(f"Hi, this is {self.name} how may I help you?")

