from enum import Enum

Direction = Enum('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')
Recognize = Enum('Presence', 'Entering Scence', 'Exiting Scene')

class Options:

    def __init__(self, end_time, start_time=0, sampling_rate=10):
        self.end_time = end_time
        self.start_time = start_time
        self.sampling_rate = sampling_rate


class HSV_Options():

    def __init__(self, direction, start_time=0, end_time=0, sampling_rate=1):
        self.end_time = end_time
        self.start_time = start_time
        self.sampling_rate = sampling_rate
        self.direction = direction

