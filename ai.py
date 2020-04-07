import warnings
import datetime

# import fastai
from fastai import text

from timer import Timer

model: text.RNNLearner = text.load_learner('models', 'finalv1.model')

timer = Timer()

warnings.filterwarnings('ignore')


def predict_text(text: str):
    return str(model.predict(text)[0])


if __name__ == '__main__':
    while True:
        user_input = input("> ")
        timer.reset()
        prediction = predict_text(user_input)
        time_seconds = timer.get()
        print(prediction, end=' ')
        print(time_seconds, "s", sep="")
