import sys
from queue import Queue

from ibm_watson.websocket import RecognizeCallback

from ai import predict_text


class RecognizeCallback1(RecognizeCallback):
    def __init__(self, prints=False):
        self.last = ''
        self.transcript_q = Queue()
        self.prints = prints
        RecognizeCallback.__init__(self)

    def on_transcription(self, transcript):
        self.last = transcript[0]['transcript'].strip()
        self.transcript_q.put(self.last)
        if self.prints:
            print("\r--> ", self.last, "-- ",  predict_text(self.last))

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

    def on_data(self, data):
        pass

    def on_close(self):
        print("Connection closed")