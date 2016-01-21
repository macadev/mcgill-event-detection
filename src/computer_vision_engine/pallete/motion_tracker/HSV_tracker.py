import cv2
from collections import deque
import numpy as np
from UserInput.Motion import *
#from UserInput.Drawing import *

__author__ = 'yarden'


class Tracker:

    def __init__(self, lower=(0, 0, 0), upper=(255, 255, 255), buff=32, r=10, objects=1, drawing=True, camera=0):
        self.camera = camera
        self.lowerHSVBound = lower
        self.upperHSVBound = upper
        self.buff = buff
        self.objects = objects
        self.minRadius = r
        self.pts = deque(maxlen=buff)
        self.counter = self.dX = self.dY = 0
        self.direction = ""
        self.drawing = True
        self.motion = Motion(init_motion=False if camera==0 else True)

    def set_lower_hsv_bounds(self, lower):
        self.lowerHSVBound = lower

    def set_upper_hsv_bounds(self, upper):
        self.upperHSVBound = upper

    def track_object(self):
        camera = cv2.VideoCapture(0)
        #if self.camera == 'camera.avi':
        if self.camera != '0':
            camera = cv2.VideoCapture(self.camera)
        while 1:
            (grabbed, frame) = camera.read()
            frame = cv2.flip(frame, 1)
            if not grabbed:
                print "error fetching camera."
                break

            mask = self.construct_mask(frame)

            center, x, y, radius = self.find_max_contour(mask)

            self.draw_enclosing_circle(center, x, y, radius, frame)

            self.track_points(frame)

            self.draw_text(frame)

            self.draw_frame(frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
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
        cv2.imshow('frame', frame)
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
