import numpy as np
import cv2

class CAMshift:


    def __init__(self):
        
    def track(self):
        while True:
            


    def convert_to_HSV(self, frame):
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        except:
            print "error converting frame to HSV colour space"
            return
                                                               
        return hsv;
