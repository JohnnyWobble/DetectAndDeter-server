import pyttsx3

from watson_recognizer import WatsonRecognizer
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
            print("MAX: %-80s" % text, predict_text(text))
            response = get_response(text)
            print("BOT:", response)
            engine.say(response)
            engine.runAndWait()

    except KeyboardInterrupt:
        recognizer.close()
