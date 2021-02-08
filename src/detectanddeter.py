from multiprocessing import Queue, Process, Manager, Event
from io import BytesIO
import audioop
import base64

from ibm_watson import SpeechToTextV1
from ibm_watson.websocket import AudioSource
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from gtts import gTTS
from pydub import AudioSegment

from watson_recognizer import RecognizeCallback
from ai import model
from chatbot import chatbot


class DetectAndDeter:
    CLASSIFICATION_COUNT = 5
    TELEMARKETER_THRESH = 0.3
    VALID_CALLER_THRESH = 0.1

    def __init__(self, encoding="mulaw", rate=8000):
        self.encoding = encoding
        self.rate = rate
        self.is_telemarketer = None
        self.valid_caller_event = Event()

        self.audio_in_queue = Queue()
        self.stt_to_classification_queue = Queue()
        self.stt_to_chatbot_queue = Queue()
        self.chatbot_to_tts_queue = Queue()
        self.audio_out_queue = Queue()

        self.manager = Manager()
        self.transcript = self.manager.list()
        self.predictions = self.manager.list()
        self.audio_source = AudioSource(self.audio_in_queue, True, True)

        self.final_transcript = None
        self.final_predictions = None

        # initialize speech to text service
        self.authenticator = IAMAuthenticator('zPJij17cD8uAVUsaWqRgZPyGt9CH5q8XuwNGurfFhtXW')
        self.speech_to_text = SpeechToTextV1(authenticator=self.authenticator)
        self.callback = RecognizeCallback(queues=(self.stt_to_chatbot_queue, self.stt_to_classification_queue))

        self.recognize_thread = Process(target=self.speech_to_text.recognize_using_websocket, kwargs=dict(
            audio=self.audio_source,
            content_type=f"audio/{self.encoding}; rate={self.rate}",
            model="en-US_NarrowbandModel",
            recognize_callback=self.callback,
            interim_results=True,
            profanity_filter=False,
            end_of_phrase_silence_time=0.4))

        self.classify_text_thread = Process(target=self.classify_text)
        self.generate_response_thread = Process(target=self.generate_responses)
        self.text_to_speech_thread = Process(target=self.text_to_speech)

    @property
    def queues(self):
        return self.audio_in_queue, self.audio_out_queue

    def start(self):
        self.recognize_thread.start()
        self.classify_text_thread.start()
        self.generate_response_thread.start()
        self.text_to_speech_thread.start()

    def close(self):
        self.final_predictions = [value for value in self.predictions]
        self.final_transcript = [value for value in self.transcript]

        self.recognize_thread.terminate()
        self.recognize_thread.join()
        self.recognize_thread.close()

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
            sound = sound.set_frame_rate(self.rate)

            ulaw_sound = audioop.lin2ulaw(sound.raw_data, 2)

            chunk_len = 192
            chunks = len(ulaw_sound) // chunk_len

            for c in range(chunks):
                chunk = ulaw_sound[c*chunk_len:c*chunk_len+chunk_len]
                self.audio_out_queue.put(base64.b64encode(chunk).decode('utf-8'))
