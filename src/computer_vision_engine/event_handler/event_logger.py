class EventLogger:


    def __init__(self):
        self.events = []

    def add_event(self, time_stamp):
        self.events.append(time_stamp)

    def print_log(self):
        print self.events
