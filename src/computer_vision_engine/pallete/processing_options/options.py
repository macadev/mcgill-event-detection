from enum import Enum

Direction = Enum('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')
Recognize = Enum('Presence', 'Entering Scence', 'Exiting Scene')

class Options:

    def __init__(self, end_time, start_time=0, sampling_rate=10):
        self.end_time = end_time;
        self.start_time = start_time;
        self.sampling_rate = sampling_rate;


class HSV_Options(Options):

    def __init__(self, end_time, start_time=0, sampling_rate=10, direction=[Direction.N]):
        super(HSV_Options).__init__(end_time, start_time, sampling_rate)
        self.direction = direction


class SURF_Options(Options):

    def __init__(self, end_time, start_time=0, sampling_rate=10, recognize=[Recognize.Presence]):
        super(SURF_Options).__init__(end_time, start_time, sampling_rate)
        self.recognize = recognize

if __name__ == '__main__':
    my_opts = SURF_Options(10)
    print(my_opts)

