from ai import predict_text
import pyttsx3
from watson_recognizer import WatsonRecognizer
from chatbot import get_response
"""
> how are you
Question
> i am 10 years old
Information
> hi
Formality
> will you please be my friend
Persuasion
"""


def input_(prompt=""):
    text = input(prompt)
    if text.lower() == "exit":
        raise KeyboardInterrupt
    else:
        return text


engine = pyttsx3.init()
voices = engine.getProperty("voices")
engine.setProperty("rate", 180)
engine.setProperty("voice", voices[1].id)
recognizer = WatsonRecognizer(prints=True)
transcript_q = recognizer.callback.transcript_q

modes = ['predict', 'tts', 'stt', 'chat']

if __name__ == '__main__':
    while True:
        try:
            mode = input("MODE: ").lower().strip()
            while mode not in modes:
                mode = input("MODE: ").lower().strip()

            if mode == 'stt':
                try:
                    recognizer.start()
                    while recognizer.thread.is_alive():
                        pass
                finally:
                    recognizer.close()
                    quit()

            while True:
                if mode == 'predict':
                    print(predict_text(input_("> ").lower()))
                elif mode == 'tts':
                    engine.say(input_("> "))
                    engine.runAndWait()
                elif mode == 'chat':
                    print("BOT: " + str(get_response(input_("MAX: ").lower())))
        except KeyboardInterrupt:
            pass
