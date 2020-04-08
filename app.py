import pyttsx3

from watson2 import WatsonRecognizer
from ai import predict_text
from chatbot import get_response

recognizer = WatsonRecognizer()
transcript_q = recognizer.callback.transcript_q
engine = pyttsx3.init()
voices = engine.getProperty("voices")
engine.setProperty("rate", 180)
engine.setProperty("voice", voices[1].id)

if __name__ == '__main__':
    try:
        recognizer.start()

        while True:
            text = transcript_q.get()
            print("> " + text)
            response = get_response(text)
            print(">>", response)
            engine.say(response)
            engine.runAndWait()

    except KeyboardInterrupt:
        recognizer.close()
