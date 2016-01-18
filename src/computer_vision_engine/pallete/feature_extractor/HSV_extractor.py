import numpy as np
import sys
import cv2

class HSVExtractor:

    def __init__(self, bins=(8, 12, 3)):
        self.bins = bins

    def extract_features(self, frame, mask):
        frame = convert_to_HSV(frame)
        if not frame:
            return
        return self.get_histogram(frame, mask)

    def get_histogram(self, frame, mask):
        histogram = cv2.calcHist([frame], [0, 1, 2], mask, self.bins, [0, 180, 0, 256, 0, 256])
        histogram = cv2.normalize(histogram).flatten()

        return histogram

    def convert_to_HSV(self, frame):
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        except:
            print "error converting frame to HSV colour space"
            return

        return hsv;
        
        
