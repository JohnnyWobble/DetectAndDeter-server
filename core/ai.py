from warnings import filterwarnings

from fastai import text

model: text.RNNLearner = text.load_learner('models', 'finalv1.model')

filterwarnings('ignore')


class Prediction:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Prediction: {self.name}"


CATEGORIES = ["Question", "Command", "General Exchange", "Persuasion", "Information", "Formality",
              "Information", "Conditional"]
PREDICTIONS = {c: Prediction(c) for c in CATEGORIES}


def predict_text(text: str):
    text.replace(" %HESITATION", "")
    p = model.predict(text)
    return PREDICTIONS[str(p[0])]


if __name__ == '__main__':
    while True:
        user_input = input("> ")
        timer.reset()
        prediction = predict_text(user_input)
        time_seconds = timer.get()
        print(prediction, end=' ')
        print(time_seconds, "s", sep="")
