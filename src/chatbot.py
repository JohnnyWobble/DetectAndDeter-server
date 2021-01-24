from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

# https://chatbotslife.com/how-to-create-an-intelligent-chatbot-in-python-c655eb39d6b1

my_bot = ChatBot(name='DetectAndDeter', read_only=True,
                 logic_adapters=['chatterbot.logic.MathematicalEvaluation',
                                 'chatterbot.logic.BestMatch'])


def train():
    corpus_trainer = ChatterBotCorpusTrainer(my_bot)
    corpus_trainer.train('chatterbot.corpus.english')


def get_response(text: str):
    text.replace(" %HESITATION", "")
    return my_bot.get_response(text)


if __name__ == '__main__':
    while True:
        print(my_bot.get_response(input("> ")))
