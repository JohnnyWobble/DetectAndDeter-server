from multiprocessing import Queue, Process, Manager, Event
import audioop
import base64
from pathlib import Path
import datetime as dt
import json
import numpy as np

from TTS.utils.synthesizer import Synthesizer
from deepspeech import Model

from ai import model
from chatbot import chatbot

CONFIG = json.load(open("config.json", 'r'))


class DetectAndDeter:
    CLASSIFICATION_COUNT = 5
    TELEMARKETER_THRESH = 0.3
    VALID_CALLER_THRESH = 0.1
    IN_AUDIO_RATE = 8000
    DS_AUDIO_RATE = 16000
    MOZILLA_TTS_AUDIO_RATE = 22050
    QUIET_THRESH = 150
    QUIET_LENGTH = 3000

    def __init__(self, name):
        self.name = name  # user's name  e.g. "Bob Ross"
        self.valid_caller_event = Event()
        self.caller_audio_chunk = np.array([], dtype='int16')

        self.audio_in_queue = Queue()
        self.stt_to_classification_queue = Queue()
        self.stt_to_chatbot_queue = Queue()
        self.chatbot_to_tts_queue = Queue()
        self.audio_out_queue = Queue()

        self.manager = Manager()
        self.transcript = self.manager.list()
        self.is_telemarketer = self.manager.Value("is_telemarketer", None)

        self.deep_speech = None
        self.mozilla_tts = None

        self.final_transcript = None
        self.final_predictions = None

        self.speech_to_text_thread = Process(target=self.speech_to_text)
        self.classify_text_thread = Process(target=self.classify_text)
        self.generate_response_thread = Process(target=self.generate_responses)
        self.text_to_speech_thread = Process(target=self.text_to_speech)

        self.log = {"start": None, "end": None, "version": CONFIG['version'], "transcript": [],
                    "is_telemarketer": None, "caller": None}

    @property
    def queues(self):
        return self.audio_in_queue, self.audio_out_queue

    def start(self):
        self.speech_to_text_thread.start()
        self.classify_text_thread.start()
        self.generate_response_thread.start()
        self.text_to_speech_thread.start()

        self.log["start"] = dt.datetime.now().isoformat()

    def close(self):
        self.log["transcript"] = [value for value in self.transcript]
        self.log["is_telemarketer"] = self.is_telemarketer.value
        self.log["end"] = dt.datetime.now().isoformat()

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

    def fill_log_info(self, caller_number):
        self.log['caller'] = caller_number
        return self.log

    def classify_text(self):
        predictions = []
        while self.is_telemarketer.value is None:
            print("!!!!!!!!")
            idx = self.stt_to_classification_queue.get()
            text = self.transcript[idx]['text']

            preds = model.predict(text)
            self.transcript[idx]['analysis'] = {"prediction": str(preds[0]).lower(), "confidence": max(preds[2])}
            predictions.append(str(preds[0]).lower())

            maybe_telemarketer = predictions.count("persuasion") / len(preds)

            if len(preds) > self.CLASSIFICATION_COUNT:
                if maybe_telemarketer > self.TELEMARKETER_THRESH:
                    self.is_telemarketer.value = True
                    break
                elif maybe_telemarketer < self.VALID_CALLER_THRESH:
                    self.is_telemarketer.value = False
                    break

        if not self.is_telemarketer.value:
            self.valid_caller_event.set()

    def generate_responses(self):
        while True:
            text = self.stt_to_chatbot_queue.get()
            print("Generate Response:", text)
            response = str(chatbot.get_response(text))

            self.chatbot_to_tts_queue.put(response)

    def text_to_speech(self):
        tts_config = CONFIG['tts_config']
        models_folder = Path(tts_config['folder'])

        model_path = str(models_folder/tts_config['model'])
        model_config_path = str(models_folder/tts_config['model_config'])
        vocoder_path = str(models_folder/tts_config['vocoder'])
        vocoder_config_path = str(models_folder/tts_config['vocoder_config'])

        self.mozilla_tts = Synthesizer(model_path, model_config_path, vocoder_path, vocoder_config_path)

        while True:
            response = self.chatbot_to_tts_queue.get()
            print("TTS:", response)

            sound_arr = np.array(self.mozilla_tts.tts(response))

            sound_arr *= 2**15
            sound_arr = sound_arr.astype('int16')

            sound = bytes(sound_arr)
            sound, _ = audioop.ratecv(sound, 2, 1, self.MOZILLA_TTS_AUDIO_RATE, self.IN_AUDIO_RATE, None)

            ulaw_sound = audioop.lin2ulaw(sound, 2)

            chunk_len = 540
            chunks = len(ulaw_sound) // chunk_len
            extra = len(ulaw_sound) - (chunks * chunk_len)

            for c in range(chunks):
                chunk = ulaw_sound[c*chunk_len:c*chunk_len+chunk_len]
                self.audio_out_queue.put(base64.b64encode(chunk).decode('utf-8'))

            if extra != 0:
                chunk = ulaw_sound[-extra:]
                self.audio_out_queue.put(base64.b64encode(chunk).decode('utf-8'))

            self.transcript.append({"speaker": "self", "text": response,
                                    "datetime": dt.datetime.now().isoformat()})

    def speech_to_text(self):
        stt_config = CONFIG['stt_config']
        models_folder = Path(stt_config['folder'])
        model_path = str(models_folder/stt_config['model'])
        scorer_path = str(models_folder/stt_config['scorer'])

        self.deep_speech = Model(model_path)
        self.deep_speech.enableExternalScorer(scorer_path)

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

                    idx = len(self.transcript)  # insert to avoid race conditions with indexes
                    self.transcript.insert(idx, {"speaker": "caller", "text": text,
                                                 "datetime": dt.datetime.now().isoformat()})
                    self.stt_to_classification_queue.put(idx)

                    stream.finishStream()
                    stream = self.deep_speech.createStream()

                self.caller_audio_chunk = np.array([], dtype='int16')

    def make_greeting(self, one_party_consent):
        self.chatbot_to_tts_queue.put(f"Hi. This is {self.name} how may I help you?")

        if not one_party_consent:
            self.chatbot_to_tts_queue.put("Keep in mind, I record all calls")
