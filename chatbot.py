from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

# https://chatbotslife.com/how-to-create-an-intelligent-chatbot-in-python-c655eb39d6b1

def train():
    corpus_trainer = ChatterBotCorpusTrainer(my_bot)
    corpus_trainer.train('chatterbot.corpus.english')


my_bot = ChatBot(name='DetectAndDeter', read_only=True,
                 logic_adapters=['chatterbot.logic.MathematicalEvaluation',
                                 'chatterbot.logic.BestMatch'])
while True:
    """
    DetectAndDeter
    Detect and Deter
    DaD
    D&D
    """
    print(my_bot.get_response(input("> ")))


