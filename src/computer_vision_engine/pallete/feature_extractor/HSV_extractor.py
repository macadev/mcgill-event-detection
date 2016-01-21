from matplotlib import pyplot as plt
import numpy as np
import sys
import cv2

class HSVExtractor:

    def __init__(self, bins=(8, 12, 3)):
        self.bins = bins

    def extract_histogram(self, frame, mask):
        frame = self.convert_to_HSV(frame)
        return self.get_histogram(frame, mask)

    def extract_range(self, frame, mask):
        cv2.imshow("img", frame)
        cv2.waitKey()
        hist = self.extract_histogram(frame, mask)
        plt.plot(hist)
        plt.show() 
        cv2.waitKey()
        #(min, max, _, _) = cv2.cv.GetMinMaxHistValue(hist)



        #return (lower, upper)



    def get_histogram(self, frame, mask=None):
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
        
if __name__ == '__main__':
    extractor = HSVExtractor()
    extractor.extract_range(cv2.imread("../../../resources/image_samples/camera-man.png", -1), None)
