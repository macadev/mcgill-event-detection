from matplotlib import pyplot as plt
import numpy as np
import argparse
import sys
import cv2

class HSVExtractor:

    def __init__(self, bins=(8, 12, 3)):
        self.bins = bins

    def get_histogram(self, frame, mask):
        frame = self.convert_to_HSV(frame)
        return self.calc_hist(frame, mask)

    def display_histogram(self, frame, mask):

        masked_frame = cv2.bitwise_and(frame, frame, mask=mask)

        cv2.imshow("frame", masked_frame)

        color = ('b','g','r')
        for i,col in enumerate(color):
            histr = cv2.calcHist([self.convert_to_HSV(frame)],[i],mask,[256],[0,256])
            histr = cv2.normalize(histr).flatten()
            plt.plot(histr, color = col)
            plt.xlim([0,256])
        plt.show()

        cv2.waitKey()

    def calc_hist(self, frame, mask=None):

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

    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", help = "path to image file")
    ap.add_argument("-m", "--mask", action = 'store_true',  help = "optional mask; same dimensions as image")
    args = vars(ap.parse_args())


    if(args["image"] is not None):
        frame = cv2.imread(args["image"], 1)
    else:
        frame = cv2.imread("../../../../resources/image_samples/camera-man.png", 1)

    if(args["mask"]):
        #bounding_box = np.array([[75, 200], [150, 200], [150, 350], [75, 350]])
        bounding_box = np.array([[50, 50], [125, 50], [125, 150], [50, 150]])
        #bounding_box = np.array([[600, 300], [700, 300], [700, 400], [600, 300]])
        mask = np.zeros(frame.shape[:2], np.uint8)
        cv2.fillPoly(mask, [bounding_box], (255, 255, 255))
    else:
        mask = None

    extractor = HSVExtractor()
    histogram = extractor.get_histogram(frame, None)
    extractor.display_histogram(frame, mask)
