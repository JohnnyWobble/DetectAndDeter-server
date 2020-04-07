import datetime


class Timer:
    def __init__(self):
        self.start_time = datetime.datetime.now()

    def reset(self):
        self.start_time = datetime.datetime.now()

    def get(self):
        return (datetime.datetime.now() - self.start_time).microseconds / 1000000
