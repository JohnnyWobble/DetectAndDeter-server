from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

# https://chatbotslife.com/how-to-create-an-intelligent-chatbot-in-python-c655eb39d6b1

chatbot = ChatBot(name='DetectAndDeter', read_only=True,
                       logic_adapters=['chatterbot.logic.MathematicalEvaluation',
                                       'chatterbot.logic.BestMatch'])
chatbot.get_response("This is just to make it load everything")


def train():
    corpus_trainer = ChatterBotCorpusTrainer(chatbot)
    corpus_trainer.train('chatterbot.corpus.english')


def get_response(text: str):
    return chatbot.get_response(text)


if __name__ == '__main__':
    cmd = input("[T]rain or [C]onversate: ").lower()

    if cmd == 'c':
        while True:
            print(chatbot.get_response(input("> ")))
    elif cmd == 't':
        train()
