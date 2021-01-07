from warnings import filterwarnings
import datetime

from fastai.text.all import *
# from fastai import text
# import fastai

model: TextLearner = load_learner('models/rev4-1.model')
print(TextLearner)

# filterwarnings('ignore')


class Prediction:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Prediction: {self.name}"


CATEGORIES = ["Question", "Command", "General Exchange", "Persuasion", "Information", "Information",
              "Conditional"]
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
        time_seconds = (now - datetime.now()).seconds
        print(prediction, end=' ')
        print(time_seconds, "s", sep="")
