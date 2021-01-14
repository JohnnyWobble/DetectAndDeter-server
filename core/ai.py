import datetime

from fastai.text.all import *
from fastai.callback.all import *

model: TextLearner = load_learner('models/rev5-1.model')


class Prediction:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Prediction: {self.name}"


CATEGORIES = ["Question", "Command", "General Exchange", "Persuasion", "Information", "Conditional"]
PREDICTIONS = {c: Prediction(c) for c in CATEGORIES}


def predict_text(text: str):
    text.replace(" %HESITATION", "")
    p = model.predict(text)
    return PREDICTIONS[str(p[0])]


if __name__ == '__main__':
    while True:
        user_input = input("> ")
        now = datetime.now()
        prediction = predict_text(user_input)
        time_seconds = (datetime.now() - now).microseconds / 1000000
        print(f"{prediction} {time_seconds}s")
