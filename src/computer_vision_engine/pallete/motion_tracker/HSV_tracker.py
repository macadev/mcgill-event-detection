import cv2
from collections import deque
import numpy as np
from feature_extractor.HSV_extractor import *
#from computer_vision_engine.pallete.feature_extractor.HSV_extractor import HSVExtractor
#from computer_vision_engine.event_handler.event_logger import *

__author__ = 'yarden'


class Tracker:

    def __init__(self, lower=(0, 0, 0), upper=(255, 255, 255), buff=32, r=10, objects=1, drawing=True, camera=0):

        self.feature_extractor = HSVExtractor()
        self.camera = camera
        self.buff = 32
        self.pts = deque(maxlen=32)
        self.direction = ""
        self.counter = self.dX = self.dY = 0

        self.timestamps = []

        '''self.lowerHSVBound = lower
        self.upperHSVBound = upper
        self.buff = buff
        self.objects = objects
        self.minRadius = r
        self.pts = deque(maxlen=buff)
        self.counter = self.dX = self.dY = 0
        self.direction = ""
        self.drawing = True
        self.motion = Motion(init_motion=False if camera==0 else True)'''

    def set_lower_hsv_bounds(self, lower):
        self.lowerHSVBound = lower

    def set_upper_hsv_bounds(self, upper):
        self.upperHSVBound = upper

    def roi_to_mask(self, roi, frame):
        mask = np.zeros(frame.shape[:2], np.uint8)
        cv2.fillPoly(mask, [roi], (255, 255, 255))
        return mask

    def track_object(self, roi_hist, roi, timestamp):

        camera = cv2.VideoCapture(self.camera)
        fps = camera.get(cv2.cv.CV_CAP_PROP_FPS)

        #cv2.cv.SetCaptureProperty(camera, cv2.cv.CV_CAP_PROP_POS_MSEC, timestamp);
        #camera.set(cv2.cv.CV_CAP_PROP_POS_MSEC, timestamp)
        '''
        (grabbed, frame) = camera.read()
        roi_mask = self.roi_to_mask(roi, frame)
        #roi_hist = self.feature_extractor.get_histogram(frame, roi_mask)

        #roi_hist = cv2.calcHist([self.feature_extractor.convert_to_HSV(frame)],[0],roi_mask,[256],[0,256])
        roi_box = frame[600:700, 300:400]
        roi_hist = cv2.calcHist([roi_box], [0], None, [16], [0, 180])
        roi_hist = cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)


        #cv2.cv.SetCaptureProperty(camera, cv2.cv.CV_CAP_PROP_POS_MSEC, 0);
        camera.set(cv2.cv.CV_CAP_PROP_POS_MSEC, 0)
        '''
        termination = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)

        while 1:
            (grabbed, frame) = camera.read()
            #frame = cv2.flip(frame, 1)
            if not grabbed:
                print "error fetching camera."
                return self.timestamps

            #mask = self.construct_mask(frame)

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            backProj = cv2.calcBackProject([hsv], [0], roi_hist, [0, 180], 1)

            if(backProj.any()):
                (r, roi) = cv2.CamShift(backProj, roi, termination)
                pts = np.int0(cv2.cv.BoxPoints(r))
                cv2.polylines(frame, [pts], True, (255, 0, 0), 2)
                ((c_x, c_y),__, _) = r

                self.pts.appendleft(((int)(c_x), (int)(c_y)))

                #cv2.imshow("frame", frame)

            self.track_points(frame)

            if self.direction == "South-West":
                time = camera.get(cv2.cv.CV_CAP_PROP_POS_MSEC)/1000
                self.timestamps.append(time)

                #if time > 5:
                    #return self.timestamps

            self.draw_text(frame)

            self.draw_frame(frame)

            '''center, x, y, radius = self.find_max_contour(mask)

            self.draw_enclosing_circle(center, x, y, radius, frame)

            self.track_points(frame)

            self.draw_text(frame)

            self.draw_frame(frame)
            '''
            if cv2.waitKey((int)(fps)) & 0xFF == ord('q'):
                break

        camera.release()
        cv2.destroyAllWindows()

    def draw_text(self, frame):
        # show the movement deltas and the direction of movement on the frame
        cv2.putText(frame, self.direction, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 3)
        cv2.putText(frame, "dx: {}, dy: {}".format(self.dX, self.dY), (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

    def track_points(self, frame):
        # loop over the set of tracked points
        for i in np.arange(1, len(self.pts)):
            # if points are null, ignore
            if self.pts[i-1] is None or self.pts[i] is None:
                continue
            if len(self.pts) > 10:
                # check to see if enough points have been accumulated in the buffer
                if self.counter >= 10 and i == 1 and self.pts[-10] is not None:
                    # compute the difference between x and y
                    # re-initialize the direction
                    self.dX = self.pts[-10][0] - self.pts[i][0]
                    self.dY = self.pts[-10][1] - self.pts[i][1]
                    (dirX, dirY) = ("", "")

                    # ensure significant movement in both directions
                    if np.abs(self.dX) > 20:
                        dirX = "East" if np.sign(self.dX) == 1 else "West"
                    if np.abs(self.dY) > 20:
                        dirY = "North" if np.sign(self.dY) == 1 else "South"

                    # handle when both directions are non-empty
                    if dirX != "" and dirY != "":
                        self.direction = "{}-{}".format(dirY, dirX)

                    # otherwise, only one direction is empty
                    else:
                        self.direction = dirX if dirX != "" else dirY


            # otherwise compute the thickness of the line and draw connecting lines
            thickness = int(np.sqrt(self.buff / float(i+1)) * 2.5)
            cv2.line(frame, self.pts[i-1], self.pts[i], (0, 0, 255), thickness)

    def draw_frame(self, frame):
        #cv2.imshow('frame', frame)
        # if self.drawing:
        #    #easel = Drawing()
        #    cv2.setMouseCallback('frame', draw_circle, param=frame)
        self.counter += 1

    def draw_enclosing_circle(self, center, x, y, radius, frame):
        # only proceed if the radius meets a min size
        if radius > self.minRadius:
            # draw the circle and update tracked points
            if self.direction in self.motion.tracking_motion:
                cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                cv2.circle(frame, center, 5, (0, 0, 255), -1)
            self.pts.appendleft(center)

    def construct_mask(self, frame):
        # blur and convert to hsv colour space
        # TODO: check blur
        blur = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

        # construct, dialate, and erode mask
        mask = cv2.inRange(hsv, self.lowerHSVBound, self.upperHSVBound)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        return mask

    def find_max_contour(self, mask):
        contours = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
        center = x = y = radius = None

        contours_found = 0

        if len(contours) > 0:
            # while contours_found < self.objects:
                # find the largest contour
                maxContour = max(contours, key=cv2.contourArea)
                # contours.remove(maxContour)

                ((x, y), radius) = cv2.minEnclosingCircle(maxContour)

                M = cv2.moments(maxContour)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

                # contours_list.append(center, x, y, radius)

                contours_found += 1


        return center, x, y, radius


def start(video, image):
    bounding_box = cv2.imread(image, -1)
    bounding_box = cv2.cvtColor(bounding_box, cv2.COLOR_BGR2HSV)
    roi_hist = cv2.calcHist([bounding_box], [0], None, [16], [0, 180])
    roi_hist = cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)

    tracker = Tracker(camera = video)
    #roi = np.array([[450, 200], [500, 200], [500, 300], [450, 300]])
    (w, h) = bounding_box.shape[:2]

    return tracker.track_object(roi_hist, (0, 0, w, h), 1000)

if __name__ == '__main__':
    car_src = "../../../resources/image_samples/tennis_man.png"
    car = cv2.imread(car_src, -1)
    car = cv2.cvtColor(car, cv2.COLOR_BGR2HSV)
    roi_hist = cv2.calcHist([car], [0], None, [16], [0, 180])
    roi_hist = cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)
    video = "../../../resources/video_samples/sample3.mp4"
    tracker = Tracker(camera = "../../../resources/video_samples/sample3.mp4")
    print start(video, car_src)
    #roi = np.array([[450, 200], [500, 200], [500, 300], [450, 300]])
    (w, h) = car.shape[:2]

   # tracker.track_object(roi_hist, (0, 0, w, h), 1000)
