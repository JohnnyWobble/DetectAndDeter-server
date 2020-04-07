import sys

from ibm_watson.websocket import RecognizeCallback


class RecognizeCallback1(RecognizeCallback):
    def __init__(self):
        self.last = ''
        RecognizeCallback.__init__(self)

    def on_transcription(self, transcript):
        # print(transcript)
        self.last = transcript[0]['transcript'].strip()
        # pred = Process(target=predict_text, args=self.last)
        # pred.start()
        # pred.join()
        # prediction = predict_text(self.last)
        # print("Pronting")
        print("\r--> ", transcript[0]['transcript'])
        # print("\r--> ", transcript[0]['transcript'], "--",  predict_text(transcript[0]))

    def on_connected(self):
        print('Connection was successful')

    def on_error(self, error):
        print('Error received: {}'.format(error))

    def on_inactivity_timeout(self, error):
        print('Inactivity timeout: {}'.format(error))

    def on_listening(self):
        print('Service is listening')

    def on_hypothesis(self, hypothesis):
        # # print('.....')
        if hypothesis.strip() != self.last:
            print('\r', hypothesis, sep='', end='')
            sys.stdout.flush()
        # print(hypothesis)
        # pass

    def on_data(self, data):
        pass

    def on_close(self):
        print("Connection closed")