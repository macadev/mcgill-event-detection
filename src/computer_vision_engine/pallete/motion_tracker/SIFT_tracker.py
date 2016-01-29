#import the necessary packages
from feature_extractor.SIFT_extractor import RootSIFT
from motion_tracker.find_obj import filter_matches,explore_match
import cv2
import numpy as np
import sys
    

class SIFT_Tracker:

    def __init__(self, num_clusters=1):
        self.num_clusters = num_clusters

    def track_object(self, camera='0', object_src=None, min_radius=10):
        camera = cv2.VideoCapture(camera)
        fps = camera.get(cv2.cv.CV_CAP_PROP_FPS)

        object = cv2.imread(object_src)

        while True:
            (grabbed, frame) = camera.read()
            
            if not grabbed:
                print "error reading frame."
                return 

            (gray_frame, frame) = self.prepare_frame(frame) 
            (gray_object, object) = self.prepare_frame(object)

            # SIFT extractor
            extractor = RootSIFT()
            detector = cv2.FeatureDetector_create("SIFT")
            kps = detector.detect(gray_frame)
            (kps, descs) = extractor.extract_features(gray_frame, kps) 
            
            kps2 = detector.detect(gray_object)
            (kps2, descs2) = extractor.extract_features(gray_object, kps2)
            # draw features to frame
            sift_image = cv2.drawKeypoints(frame, kps)

            # FLANN
            FLANN_INDEX_KDTREE = 0
            index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
            search_params = dict(checks = 50)

            flann = cv2.FlannBasedMatcher(index_params, search_params)
            matches = flann.knnMatch(descs, descs2, k=2)

            # Brute Force
            brute_force = cv2.BFMatcher()
            matches_bf = brute_force.knnMatch(descs, descs2, k=2)
            p1, p2, kp_pairs = filter_matches(kps, kps2, matches_bf)
            explore_match('result', frame, object, kp_pairs)
            mathces_bf = sorted(matches_bf, key=lambda val: val.distance)
            

            # draw only good matches
            matchesMask = [[0,0] for i in xrange(len(matches))]

            # ratio test
            for i, (m, n) in enumerate(matches):
                if m.distance < 0.7*n.distance:
                    matchesMask[i] = [1,0]

            draw_params = dict(matchColor = (0, 255, 0), singlePointColor = (255, 0, 0), matchesMask = matchesMask, flags = 0)

            #result = drawMatches(frame, kps, object, kps2, matches), result, **draw_params)

            #cv2.imshow("result", result)
            #cv2.imshow("SIFT", sift_image)

            if cv2.waitKey(int(1)) & 0xFF == ord('q'):
                break

        camera.release()
        cv2.destroyAllWindows()
    
    def prepare_frame(self, frame):
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        return (gray, frame)

def drawMatches(img1, kp1, img2, kp2, matches):
    """
    My own implementation of cv2.drawMatches as OpenCV 2.4.9
    does not have this function available but it's supported in
    OpenCV 3.0.0

    This function takes in two images with their associated 
    keypoints, as well as a list of DMatch data structure (matches) 
    that contains which keypoints matched in which images.

    An image will be produced where a montage is shown with
    the first image followed by the second image beside it.

    Keypoints are delineated with circles, while lines are connected
    between matching keypoints.

    img1,img2 - Grayscale images
    kp1,kp2 - Detected list of keypoints through any of the OpenCV keypoint 
              detection algorithms
    matches - A list of matches of corresponding keypoints through any
              OpenCV keypoint matching algorithm
    """

    # Create a new output image that concatenates the two images together
    # (a.k.a) a montage
    rows1 = img1.shape[0]
    cols1 = img1.shape[1]
    rows2 = img2.shape[0]
    cols2 = img2.shape[1]

    out = np.zeros((max([rows1,rows2]),cols1+cols2,9), dtype='uint8')

    # Place the first image to the left
    out[:rows1,:cols1] = np.dstack([img1, img1, img1])

    # Place the next image to the right of it
    out[:rows2,cols1:] = np.dstack([img2, img2, img2])

    # For each pair of points we have between both images
    # draw circles, then connect a line between them
    for mat in matches:

        # Get the matching keypoints for each of the images
        img1_idx = mat.queryIdx
        img2_idx = mat.trainIdx

        # x - columns
        # y - rows
        (x1,y1) = kp1[img1_idx].pt
        (x2,y2) = kp2[img2_idx].pt

        # Draw a small circle at both co-ordinates
        # radius 4
        # colour blue
        # thickness = 1
        cv2.circle(out, (int(x1),int(y1)), 4, (255, 0, 0), 1)   
        cv2.circle(out, (int(x2)+cols1,int(y2)), 4, (255, 0, 0), 1)

        # Draw a line in between the two points
        # thickness = 1
        # colour blue
        cv2.line(out, (int(x1),int(y1)), (int(x2)+cols1,int(y2)), (255, 0, 0), 1)


    # Show the image
    cv2.imshow('Matched Features', out)
    cv2.waitKey(0)
    cv2.destroyWindow('Matched Features')

    # Also return the image if you'd like a copy
    return out

if __name__ == '__main__':
    tracker = SIFT_Tracker()
    tracker.track_object("../../../resources/video_samples/sample3.mp4", "../../../resources/image_samples/red_car.png")


# load the image we are going to extract descriptors from and convert
# it to grayscale
image = cv2.imread("../../../resources/image_samples/sample-1.jpg")
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
 
# detect Difference of Gaussian keypoints in the image
detector = cv2.FeatureDetector_create("SIFT")
kps = detector.detect(gray)
 
# extract normal SIFT descriptors
extractor = cv2.DescriptorExtractor_create("SIFT")
(kps, descs) = extractor.compute(gray, kps)
print "SIFT: kps=%d, descriptors=%s " % (len(kps), descs.shape)
 
sift = cv2.drawKeypoints(gray, kps)
cv2.imwrite("SIFT1.png", sift)

# extract RootSIFT descriptors
rs = RootSIFT()
(kps, descs) = rs.extract_features(gray, kps)
#print "RootSIFT: kps=%d, descriptors=%s " % (len(kps), descs.shape)

sift = cv2.drawKeypoints(gray, kps)
cv2.imwrite("SIFT2.png", sift)
