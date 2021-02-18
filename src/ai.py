import datetime

from fastai.text.all import *
from fastai.callback.all import *

from utils import get_file_by_extension


model: TextLearner = load_learner(get_file_by_extension("model"))


class Prediction:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Prediction: {self.name}"


CATEGORIES = ["Question", "Command", "General Exchange", "Persuasion", "Information", "Conditional"]
PREDICTIONS = {c: Prediction(c) for c in CATEGORIES}


def predict_text(text):
    text.replace(" %HESITATION", "")
    p = model.predict(text)
    return PREDICTIONS[str(p[0])], max(p[2])


if __name__ == '__main__':
    while True:
        inp = input("> ")
        now = datetime.now()
        prediction, confidence = predict_text(inp)
        time_seconds = (datetime.now() - now).total_seconds()
        print(f"{prediction} {confidence*100:4.1f}% {time_seconds:5.3f}s")
